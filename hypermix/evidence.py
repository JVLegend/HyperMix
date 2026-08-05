"""Validation helpers for the HyperMix publication evidence bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
from typing import Any


class EvidenceManifestError(ValueError):
    """Raised when an evidence manifest is malformed or fails verification."""


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest of *path* without loading it all in memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_path(repo_root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidenceManifestError("artifact path must be a non-empty string")

    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvidenceManifestError(f"artifact path escapes the repository: {value}")

    candidate = (repo_root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise EvidenceManifestError(
            f"artifact path escapes the repository: {value}"
        ) from exc
    return candidate


def verify_evidence_manifest(
    repo_root: str | Path,
    manifest_path: str | Path = "publication/evidence_manifest.json",
) -> dict[str, int]:
    """Validate the publication manifest and verify every artifact checksum."""

    root = Path(repo_root).resolve()
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = root / manifest

    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceManifestError(f"cannot read evidence manifest: {exc}") from exc

    if payload.get("schema_version") != 1:
        raise EvidenceManifestError("unsupported evidence manifest schema")

    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise EvidenceManifestError("manifest entries must be a non-empty list")

    seen_ids: set[str] = set()
    file_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise EvidenceManifestError("every evidence entry must be an object")

        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            raise EvidenceManifestError("every evidence entry needs an id")
        if entry_id in seen_ids:
            raise EvidenceManifestError(f"duplicate evidence id: {entry_id}")
        seen_ids.add(entry_id)

        if entry.get("status") not in {"supported", "blocked", "inconclusive"}:
            raise EvidenceManifestError(f"invalid status for {entry_id}")
        if not isinstance(entry.get("claim"), str) or not entry["claim"]:
            raise EvidenceManifestError(f"missing claim for {entry_id}")
        command = entry.get("command")
        if not isinstance(command, str) or not command:
            raise EvidenceManifestError(f"missing command for {entry_id}")
        command_parts = shlex.split(command)
        if len(command_parts) < 2 or command_parts[0] not in {"python", "python3"}:
            raise EvidenceManifestError(f"invalid command for {entry_id}")
        script_path = _artifact_path(root, command_parts[1])
        if not script_path.is_file():
            raise EvidenceManifestError(f"missing generator script: {script_path}")
        limitations = entry.get("limitations")
        if not isinstance(limitations, list) or not limitations or not all(
            isinstance(item, str) and item for item in limitations
        ):
            raise EvidenceManifestError(f"missing limitations for {entry_id}")

        artifacts = entry.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise EvidenceManifestError(f"missing artifacts for {entry_id}")

        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise EvidenceManifestError(f"invalid artifact for {entry_id}")
            path = _artifact_path(root, artifact.get("path"))
            expected = artifact.get("sha256")
            if (
                not isinstance(expected, str)
                or len(expected) != 64
                or any(character not in "0123456789abcdef" for character in expected)
            ):
                raise EvidenceManifestError(f"invalid SHA-256 for {path}")
            if not path.is_file():
                raise EvidenceManifestError(f"missing artifact: {path}")
            actual = sha256_file(path)
            if actual != expected:
                raise EvidenceManifestError(
                    f"checksum mismatch for {artifact['path']}: {actual} != {expected}"
                )
            file_count += 1

    return {"claims": len(entries), "files": file_count}
