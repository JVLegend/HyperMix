"""Lista, baixa e verifica os subconjuntos bioHSI usados na Fase C.

Listar sem baixar:
    python scripts/fetch_biohsi.py --list

Baixar o primeiro conjunto real de 54 m:
    python scripts/fetch_biohsi.py --dataset rg_on_sand_induction_54m.zip
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hypermix.biohsi import (
    DEFAULT_DATA_DIR,
    available_biohsi_files,
    fetch_biohsi_file,
    inspect_biohsi_archive,
    load_biohsi_manifest,
    verify_biohsi_file,
)


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024.0 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    raise AssertionError("unreachable")


def _list(manifest: dict) -> None:
    record = manifest["record"]
    print(f"bioHSI {record['version']} | DOI {record['doi']} | {record['license']}")
    for name in available_biohsi_files(manifest):
        entry = manifest["files"][name]
        print(f"{name:<42} {_human_size(entry['size']):>10}  {entry['role']}")


def _progress_reporter(name: str):
    last_bucket = -1

    def report(downloaded: int, total: int) -> None:
        nonlocal last_bucket
        bucket = min(20, int(downloaded / total * 20)) if total else 20
        if bucket != last_bucket:
            percent = min(100.0, downloaded / total * 100) if total else 100.0
            print(
                f"  {name}: {_human_size(downloaded)} / {_human_size(total)} "
                f"({percent:.1f}%)"
            )
            last_bucket = bucket

    return report


def _inspect(path: Path) -> None:
    members = inspect_biohsi_archive(path)
    print(f"inventário: {len(members)} arquivos em {path.name}")
    for member in members:
        print(f"  {member.name:<64} {_human_size(member.size):>10}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="lista o manifesto curado")
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        metavar="NAME",
        help="arquivo do manifesto; pode ser informado mais de uma vez",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--force", action="store_true", help="substitui arquivo inválido")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="não baixa; apenas verifica os arquivos solicitados",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="após verificar, lista o conteúdo de cada ZIP sem extrair",
    )
    args = parser.parse_args()
    manifest = load_biohsi_manifest()

    if args.list or not args.dataset:
        _list(manifest)
    if not args.dataset:
        return

    for name in args.dataset:
        if name not in manifest["files"]:
            parser.error(f"arquivo não está no manifesto: {name}")
        entry = manifest["files"][name]
        output = args.output_dir / name
        if args.verify_only:
            verified = verify_biohsi_file(output, entry)
        else:
            print(f"{name}: {_human_size(entry['size'])} de {manifest['record']['doi']}")
            verified = fetch_biohsi_file(
                name,
                args.output_dir,
                manifest=manifest,
                force=args.force,
                progress=_progress_reporter(name),
            )
        print(f"ok: {verified}")
        if args.inspect:
            if verified.suffix.lower() != ".zip":
                parser.error(f"--inspect requer um ZIP: {verified.name}")
            _inspect(verified)


if __name__ == "__main__":
    main()
