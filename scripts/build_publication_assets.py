#!/usr/bin/env python3
"""Build or verify manuscript tables, figures, and source provenance."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "hypermix" / "publication.py"
SPEC = importlib.util.spec_from_file_location("_hypermix_publication", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load publication builder from {MODULE_PATH}")
PUBLICATION_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PUBLICATION_MODULE
SPEC.loader.exec_module(PUBLICATION_MODULE)
PublicationAssetError = PUBLICATION_MODULE.PublicationAssetError
build_publication_assets = PUBLICATION_MODULE.build_publication_assets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing if committed assets are stale",
    )
    args = parser.parse_args()

    try:
        summary = build_publication_assets(REPO_ROOT, check=args.check)
    except PublicationAssetError as exc:
        parser.error(str(exc))

    action = "verified" if args.check else "generated"
    print(
        f"Publication assets {action}: {summary['rows']} rows, "
        f"{summary['contrasts']} contrasts, {summary['files']} synchronized files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
