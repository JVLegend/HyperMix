import importlib.util
from pathlib import Path
from shutil import copy2

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_release", ROOT / "scripts" / "check_release.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECK_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_RELEASE)
validate_release = CHECK_RELEASE.validate_release

RELEASE_FILES = (
    "pyproject.toml",
    "CITATION.cff",
    "CHANGELOG.md",
    ".github/workflows/publish-pypi.yml",
    "docs/releases/v0.5.0.md",
)


def _release_fixture(tmp_path: Path) -> Path:
    for relative in RELEASE_FILES:
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source, destination)
    return tmp_path


def test_current_release_contract_is_consistent():
    assert validate_release(ROOT, tag="v0.5.0") == []


def test_release_gate_rejects_a_tag_version_mismatch(tmp_path):
    root = _release_fixture(tmp_path)

    errors = validate_release(root, tag="v0.5.1")

    assert any("diverge da versão do pacote" in error for error in errors)


def test_release_gate_rejects_citation_drift(tmp_path):
    root = _release_fixture(tmp_path)
    citation = root / "CITATION.cff"
    citation.write_text(
        citation.read_text(encoding="utf-8").replace("version: 0.5.0", "version: 9.9.9"),
        encoding="utf-8",
    )

    errors = validate_release(root, tag="v0.5.0")

    assert any("CITATION.cff declara" in error for error in errors)


def test_release_gate_rejects_unpinned_actions(tmp_path):
    root = _release_fixture(tmp_path)
    workflow = root / ".github/workflows/publish-pypi.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33",
            "pypa/gh-action-pypi-publish@release/v1",
        ),
        encoding="utf-8",
    )

    errors = validate_release(root, tag="v0.5.0")

    assert any("SHA de 40 caracteres" in error for error in errors)
