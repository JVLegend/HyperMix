import json
from pathlib import Path

import pytest

from hypermix.evidence import EvidenceManifestError, sha256_file, verify_evidence_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _manifest(tmp_path: Path, artifact_path: str, digest: str) -> Path:
    (tmp_path / "generator.py").write_text("pass\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "entries": [
            {
                "id": "test-claim",
                "status": "supported",
                "claim": "A test claim.",
                "command": "python generator.py",
                "artifacts": [{"path": artifact_path, "sha256": digest}],
                "limitations": ["Synthetic fixture only."],
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_repository_evidence_manifest_is_valid():
    summary = verify_evidence_manifest(REPO_ROOT)
    assert summary == {"claims": 8, "files": 16}


def test_checksum_mismatch_fails_closed(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("first", encoding="utf-8")
    manifest = _manifest(tmp_path, "artifact.txt", sha256_file(artifact))
    artifact.write_text("changed", encoding="utf-8")

    with pytest.raises(EvidenceManifestError, match="checksum mismatch"):
        verify_evidence_manifest(tmp_path, manifest)


def test_parent_path_is_rejected(tmp_path):
    manifest = _manifest(tmp_path, "../outside.txt", "0" * 64)

    with pytest.raises(EvidenceManifestError, match="escapes the repository"):
        verify_evidence_manifest(tmp_path, manifest)


def test_duplicate_claim_ids_are_rejected(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("fixture", encoding="utf-8")
    manifest = _manifest(tmp_path, "artifact.txt", sha256_file(artifact))
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["entries"].append(dict(payload["entries"][0]))
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidenceManifestError, match="duplicate evidence id"):
        verify_evidence_manifest(tmp_path, manifest)
