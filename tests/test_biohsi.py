"""Testes offline do manifesto e downloader bioHSI."""

import base64
import hashlib
import zipfile

import pytest

from hypermix.biohsi import (
    available_biohsi_files,
    fetch_biohsi_file,
    inspect_biohsi_archive,
    load_biohsi_manifest,
    verify_biohsi_file,
)


def test_biohsi_manifest_pins_primary_54m_file():
    manifest = load_biohsi_manifest()
    assert manifest["record"]["doi"] == "10.5281/zenodo.14756889"
    assert manifest["record"]["license"] == "CC-BY-4.0"
    entry = manifest["files"]["rg_on_sand_induction_54m.zip"]
    assert entry["size"] == 628789375
    assert entry["checksum"] == "md5:a5e553d8f0634896b02750086e7eb4a1"
    assert "rg_on_sand_induction_54m.zip" in available_biohsi_files(manifest)


def test_verify_biohsi_file_checks_size_and_digest(tmp_path):
    payload = b"measured hyperspectral target"
    path = tmp_path / "sample.bin"
    path.write_bytes(payload)
    entry = {
        "size": len(payload),
        "checksum": f"md5:{hashlib.md5(payload, usedforsecurity=False).hexdigest()}",
    }
    assert verify_biohsi_file(path, entry) == path
    path.write_bytes(payload + b"!")
    with pytest.raises(ValueError, match="size mismatch"):
        verify_biohsi_file(path, entry)


def test_fetch_biohsi_file_streams_and_verifies_without_network(tmp_path):
    payload = b"biohsi-test-payload" * 32
    encoded = base64.b64encode(payload).decode("ascii")
    name = "sample.bin"
    manifest = {
        "files": {
            name: {
                "size": len(payload),
                "checksum": (
                    "md5:"
                    + hashlib.md5(payload, usedforsecurity=False).hexdigest()
                ),
                "download_url": f"data:application/octet-stream;base64,{encoded}",
                "role": "test",
            }
        }
    }
    progress = []
    output = fetch_biohsi_file(
        name,
        tmp_path,
        manifest=manifest,
        chunk_size=17,
        progress=lambda downloaded, total: progress.append((downloaded, total)),
    )
    assert output.read_bytes() == payload
    assert not (tmp_path / f"{name}.part").exists()
    assert progress[0] == (0, len(payload))
    assert progress[-1] == (len(payload), len(payload))


def test_inspect_biohsi_archive_lists_members_without_extracting(tmp_path):
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("scene/raw.hdr", "ENVI\nsamples = 2")
        handle.writestr("scene/labels.csv", "0\n5\n")

    members = inspect_biohsi_archive(archive)

    assert [member.name for member in members] == [
        "scene/raw.hdr",
        "scene/labels.csv",
    ]
    assert members[0].size == len("ENVI\nsamples = 2")
    assert not (tmp_path / "scene").exists()


def test_fetch_promotes_a_complete_verified_partial_without_network(tmp_path):
    payload = b"complete resumable download"
    name = "sample.zip"
    partial = tmp_path / f"{name}.part"
    partial.write_bytes(payload)
    manifest = {
        "files": {
            name: {
                "size": len(payload),
                "checksum": (
                    "md5:"
                    + hashlib.md5(payload, usedforsecurity=False).hexdigest()
                ),
                "download_url": "https://invalid.example/not-requested",
                "role": "test",
            }
        }
    }

    output = fetch_biohsi_file(name, tmp_path, manifest=manifest)

    assert output.read_bytes() == payload
    assert not partial.exists()
