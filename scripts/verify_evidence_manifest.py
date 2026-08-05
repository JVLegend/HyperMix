#!/usr/bin/env python3
"""Verify the checksummed evidence bundle used by the HyperMix publication."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "hypermix" / "evidence.py"
SPEC = importlib.util.spec_from_file_location("_hypermix_evidence", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load evidence verifier from {MODULE_PATH}")
EVIDENCE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE_MODULE)
EvidenceManifestError = EVIDENCE_MODULE.EvidenceManifestError
verify_evidence_manifest = EVIDENCE_MODULE.verify_evidence_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="publication/evidence_manifest.json",
        help="manifest path relative to the repository root",
    )
    args = parser.parse_args()

    try:
        summary = verify_evidence_manifest(REPO_ROOT, args.manifest)
    except EvidenceManifestError as exc:
        parser.error(str(exc))

    print(
        "Evidence bundle verified: "
        f"{summary['claims']} claims, {summary['files']} files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
