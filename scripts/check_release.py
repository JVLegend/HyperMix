"""Fail closed when release metadata or automation drift apart."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


PROJECT_VERSION_RE = re.compile(
    r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)"
)
FIELD_RE_TEMPLATE = r"(?m)^{field}:\s*[\"']?([^\"'\s]+)"
CHANGELOG_RE_TEMPLATE = r"(?m)^##\s+{version}\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})\s*$"
PINNED_ACTION_RE = re.compile(r"(?m)^\s*uses:\s*([^@\s]+)@([0-9a-f]{40})\s*(?:#.*)?$")


def _read(root: Path, relative: str, errors: list[str]) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"arquivo obrigatório ausente: {relative}")
        return ""


def _project_version(pyproject: str) -> str | None:
    project = PROJECT_VERSION_RE.search(pyproject)
    if not project:
        return None
    version = re.search(r'(?m)^version\s*=\s*["\']([^"\']+)["\']\s*$', project.group(1))
    return version.group(1) if version else None


def _citation_field(citation: str, field: str) -> str | None:
    match = re.search(FIELD_RE_TEMPLATE.format(field=re.escape(field)), citation)
    return match.group(1) if match else None


def validate_release(root: Path, *, tag: str | None = None) -> list[str]:
    """Return every release-contract violation found under ``root``."""

    root = root.resolve()
    errors: list[str] = []
    pyproject = _read(root, "pyproject.toml", errors)
    package_init = _read(root, "hypermix/__init__.py", errors)
    citation = _read(root, "CITATION.cff", errors)
    changelog = _read(root, "CHANGELOG.md", errors)
    workflow = _read(root, ".github/workflows/publish-pypi.yml", errors)

    version = _project_version(pyproject)
    if not version:
        errors.append("versão ausente em [project] de pyproject.toml")
        return errors

    expected_tag = f"v{version}"
    if tag is not None and tag != expected_tag:
        errors.append(f"tag {tag!r} diverge da versão do pacote; esperado {expected_tag!r}")

    package_version_match = re.search(
        r'(?m)^__version__\s*=\s*["\']([^"\']+)["\']\s*$', package_init
    )
    package_version = (
        package_version_match.group(1) if package_version_match else None
    )
    if package_version != version:
        errors.append(
            "hypermix.__version__ declara "
            f"{package_version!r}; pyproject.toml declara {version!r}"
        )

    citation_version = _citation_field(citation, "version")
    if citation_version != version:
        errors.append(
            f"CITATION.cff declara {citation_version!r}; pyproject.toml declara {version!r}"
        )

    changelog_match = re.search(
        CHANGELOG_RE_TEMPLATE.format(version=re.escape(version)), changelog
    )
    if not changelog_match:
        errors.append(f"CHANGELOG.md não contém uma seção datada para {version}")
    else:
        changelog_date = changelog_match.group(1)
        try:
            date.fromisoformat(changelog_date)
        except ValueError:
            errors.append(f"data inválida no changelog: {changelog_date!r}")
        citation_date = _citation_field(citation, "date-released")
        if citation_date != changelog_date:
            errors.append(
                "date-released de CITATION.cff diverge da data da versão no changelog: "
                f"{citation_date!r} != {changelog_date!r}"
            )

    notes_path = root / "docs" / "releases" / f"v{version}.md"
    if not notes_path.is_file():
        errors.append(f"notas da release ausentes: {notes_path.relative_to(root)}")
    else:
        heading = f"# HyperMix v{version}"
        if heading not in notes_path.read_text(encoding="utf-8"):
            errors.append(f"notas da release não contêm o título {heading!r}")

    workflow_checks = {
        "gatilho release published": r"(?s)release:\s*\n\s*types:\s*\[published\]",
        "environment pypi": r"(?m)^\s*name:\s*pypi\s*$",
        "permissão id-token": r"(?m)^\s*id-token:\s*write\s*$",
        "publicador PyPI": r"(?m)^\s*uses:\s*pypa/gh-action-pypi-publish@",
    }
    for description, pattern in workflow_checks.items():
        if not re.search(pattern, workflow):
            errors.append(f"workflow de publicação sem {description}")

    action_lines = [line for line in workflow.splitlines() if "uses:" in line]
    pinned_actions = PINNED_ACTION_RE.findall(workflow)
    if len(pinned_actions) != len(action_lines):
        errors.append("todas as actions do workflow de publicação devem usar SHA de 40 caracteres")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tag", help="tag que será publicada, por exemplo v0.5.0")
    args = parser.parse_args()

    errors = validate_release(args.root, tag=args.tag)
    if errors:
        print("Gate de release reprovado:")
        for error in errors:
            print(f"- {error}")
        return 1

    version = _project_version((args.root / "pyproject.toml").read_text(encoding="utf-8"))
    print(f"Gate de release aprovado para HyperMix v{version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
