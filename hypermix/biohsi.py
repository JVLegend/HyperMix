"""Rastreabilidade e aquisição dos cubos bioHSI publicados por Chemla et al.

Os arquivos grandes ficam em ``data/biohsi`` e nunca são incluídos no pacote.
O manifesto pequeno e versionado preserva DOI, versão, licença, tamanho e
checksum dos subconjuntos que compõem a Fase C do HyperMix.
"""

from __future__ import annotations

import hashlib
from importlib.resources import files
import json
from pathlib import Path
from typing import Any, Callable, Mapping, NamedTuple
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "biohsi"
MANIFEST_RESOURCE = files("hypermix.data").joinpath("biohsi_manifest.json")

__all__ = [
    "DEFAULT_DATA_DIR",
    "BioHSIArchiveMember",
    "available_biohsi_files",
    "fetch_biohsi_file",
    "inspect_biohsi_archive",
    "load_biohsi_manifest",
    "verify_biohsi_file",
]


class BioHSIArchiveMember(NamedTuple):
    """Metadados de um membro do ZIP, sem extrair seu conteúdo."""

    name: str
    size: int
    compressed_size: int


def load_biohsi_manifest() -> dict[str, Any]:
    """Carrega o manifesto curado empacotado com o HyperMix."""
    with MANIFEST_RESOURCE.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema_version") != 1 or not manifest.get("files"):
        raise ValueError("invalid bioHSI manifest")
    return manifest


def available_biohsi_files(
    manifest: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Retorna os arquivos curados em ordem alfabética."""
    source = manifest or load_biohsi_manifest()
    return tuple(sorted(source["files"]))


def _entry(name: str, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    if Path(name).name != name:
        raise ValueError("bioHSI file name must not contain a path")
    try:
        return manifest["files"][name]
    except KeyError as exc:
        choices = ", ".join(available_biohsi_files(manifest))
        raise KeyError(f"unknown bioHSI file {name!r}; choose one of: {choices}") from exc


def _checksum(path: Path, specification: str) -> tuple[str, str]:
    algorithm, expected = specification.split(":", 1)
    if algorithm not in {"md5", "sha256"}:
        raise ValueError(f"unsupported checksum algorithm: {algorithm}")
    digest = hashlib.new(algorithm, usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"{algorithm}:{digest.hexdigest()}", expected


def verify_biohsi_file(path: str | Path, entry: Mapping[str, Any]) -> Path:
    """Valida tamanho e checksum, levantando erro em qualquer divergência."""
    candidate = Path(path)
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    expected_size = int(entry["size"])
    actual_size = candidate.stat().st_size
    if actual_size != expected_size:
        raise ValueError(
            f"size mismatch for {candidate}: expected {expected_size}, got {actual_size}"
        )
    actual_checksum, expected_digest = _checksum(candidate, entry["checksum"])
    if actual_checksum.split(":", 1)[1] != expected_digest:
        raise ValueError(
            f"checksum mismatch for {candidate}: expected {entry['checksum']}, "
            f"got {actual_checksum}"
        )
    return candidate


def inspect_biohsi_archive(path: str | Path) -> tuple[BioHSIArchiveMember, ...]:
    """Inventaria um ZIP validado sem extrair nem executar seu conteúdo."""
    archive = Path(path)
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with zipfile.ZipFile(archive) as handle:
        corrupt = handle.testzip()
        if corrupt is not None:
            raise ValueError(f"corrupt ZIP member: {corrupt}")
        return tuple(
            BioHSIArchiveMember(info.filename, info.file_size, info.compress_size)
            for info in handle.infolist()
            if not info.is_dir()
        )


def fetch_biohsi_file(
    name: str,
    destination: str | Path = DEFAULT_DATA_DIR,
    *,
    manifest: Mapping[str, Any] | None = None,
    force: bool = False,
    chunk_size: int = 4 * 1024 * 1024,
    progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Baixa um arquivo curado com retomada HTTP e verificação obrigatória."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    source = manifest or load_biohsi_manifest()
    entry = _entry(name, source)
    output_dir = Path(destination)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / name
    partial = output.with_name(f"{output.name}.part")

    if output.exists():
        try:
            return verify_biohsi_file(output, entry)
        except ValueError:
            if not force:
                raise
            output.unlink()

    expected_size = int(entry["size"])
    if partial.exists() and partial.stat().st_size > expected_size:
        partial.unlink()
    if partial.exists() and partial.stat().st_size == expected_size:
        try:
            verify_biohsi_file(partial, entry)
        except ValueError:
            if not force:
                raise
            partial.unlink()
        else:
            partial.replace(output)
            if progress is not None:
                progress(expected_size, expected_size)
            return output
    offset = partial.stat().st_size if partial.exists() else 0
    if progress is not None:
        progress(offset, expected_size)
    headers = {"User-Agent": "HyperMix/0.4 (+https://github.com/JVLegend/HyperMix)"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(entry["download_url"], headers=headers)

    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        status = getattr(response, "status", None)
        append = bool(offset and status == 206)
        mode = "ab" if append else "wb"
        with partial.open(mode) as handle:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                handle.write(chunk)
                offset = handle.tell()
                if progress is not None:
                    progress(offset, expected_size)

    verify_biohsi_file(partial, entry)
    partial.replace(output)
    return output
