"""Fetch primary spectral libraries and build HyperMix's compact reference CSV.

The generated table contains 400-1000 nm spectra at 1 nm spacing from:

* USGS Spectral Library Version 7, measured surface reflectance;
* the official bioHSI code archive for Chemla et al., inferred pellet
  absorbance for the two experimentally demonstrated reporters.

Large upstream archives are not committed. Their checksums are verified and
only the seven required spectra are interpolated into the package data file.

    python scripts/fetch_reference_spectra.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path
import tempfile
import urllib.request
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "hypermix" / "data" / "reference_spectra.csv"

USGS_URL = (
    "https://www.sciencebase.gov/catalog/file/get/586e8c88e4b0f5ce109fccae"
    "?f=__disk__a7%2F4f%2F91%2Fa74f913e0b7d1b8123ad059e52506a02b75a2832"
)
USGS_SHA256 = "d232645740869a82aafcad5839448c50b1dc72965ce042d1374f29b7a798a91c"
BIOHSI_URL = "https://zenodo.org/api/records/14827801/files/VoigtLab/bioHSI-v.1.0.0.zip/content"
BIOHSI_SHA256 = "3dfc176aa40c2c3740cef9b798116eb018f1a20137acc5c82872a4c58f0cedd8"

USGS_ROOT = "ASCIIdata_splib07a"
USGS_MEMBERS = {
    "usgs_aspen_green_reflectance": (
        "ASD",
        f"{USGS_ROOT}/ChapterV_Vegetation/"
        "splib07a_Aspen_Aspen-1_green-top_ASDFRa_AREF.txt",
    ),
    "usgs_dry_grass_reflectance": (
        "ASD",
        f"{USGS_ROOT}/ChapterV_Vegetation/"
        "splib07a_Grass_Golden_Dry_GDS480_ASDFRa_AREF.txt",
    ),
    "usgs_sand_reflectance": (
        "ASD",
        f"{USGS_ROOT}/ChapterS_SoilsAndMixtures/"
        "splib07a_Sand_DWO-3-DEL2ar1_no_oil_ASDFRa_AREF.txt",
    ),
    "usgs_seawater_reflectance": (
        "BECK",
        f"{USGS_ROOT}/ChapterL_Liquids/"
        "splib07a_Seawater_Open_Ocean_SW2_lwch_BECKa_AREF.txt",
    ),
}
USGS_WAVELENGTHS = {
    "ASD": f"{USGS_ROOT}/splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt",
    "BECK": f"{USGS_ROOT}/splib07a_Wavelengths_BECK_Beckman_0.2-3.0_microns.txt",
}

BIOHSI_ROOT = "VoigtLab-bioHSI-935e501/04_image_processing/00_data/absorbance_data"
BIOHSI_MEMBERS = {
    "chemla_bchl_a_yf10_absorbance": (
        f"{BIOHSI_ROOT}/YF10_infered_absorbance_from_pellets_09Jul2024.npy"
    ),
    "chemla_smurfp_biliverdin_ecoli_absorbance": (
        f"{BIOHSI_ROOT}/bpHO-smURFP_infered_absorbance_from_ecoli_pellets_10Jul2024.npy"
    ),
    "chemla_smurfp_biliverdin_pputida_absorbance": (
        f"{BIOHSI_ROOT}/bpHO-smURFP_infered_absorbance_from_pputida_pellets_10Jul2024.npy"
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, path: Path, expected_sha256: str) -> Path:
    if not path.exists():
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, path)
    actual = _sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"checksum mismatch for {path}: {actual}")
    return path


def _ascii_values(archive: zipfile.ZipFile, member: str) -> np.ndarray:
    lines = archive.read(member).decode("ascii").splitlines()[1:]
    return np.asarray([float(line) for line in lines], dtype=np.float64)


def _interpolate_valid(wavelengths: np.ndarray, values: np.ndarray,
                       output_wavelengths: np.ndarray) -> np.ndarray:
    valid = np.isfinite(values) & (values > -1e20)
    if valid.sum() < 2:
        raise ValueError("spectrum has fewer than two valid samples")
    return np.interp(output_wavelengths, wavelengths[valid], values[valid])


def build_reference_csv(usgs_zip: Path, biohsi_zip: Path, output: Path) -> None:
    output_wavelengths = np.arange(400.0, 1001.0, 1.0)
    columns: dict[str, np.ndarray] = {}

    with zipfile.ZipFile(usgs_zip) as archive:
        grids = {
            sensor: 1000.0 * _ascii_values(archive, member)
            for sensor, member in USGS_WAVELENGTHS.items()
        }
        for name, (sensor, member) in USGS_MEMBERS.items():
            values = _ascii_values(archive, member)
            columns[name] = _interpolate_valid(
                grids[sensor], values, output_wavelengths
            )

    with zipfile.ZipFile(biohsi_zip) as archive:
        for name, member in BIOHSI_MEMBERS.items():
            array = np.load(io.BytesIO(archive.read(member)), allow_pickle=False)
            if array.shape[0] != 2:
                raise ValueError(f"unexpected bioHSI array shape for {member}: {array.shape}")
            columns[name] = np.interp(output_wavelengths, array[0], array[1])

    output.parent.mkdir(parents=True, exist_ok=True)
    names = list(columns)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["wavelength_nm", *names])
        for index, wavelength in enumerate(output_wavelengths):
            writer.writerow(
                [f"{wavelength:.1f}", *(f"{columns[name][index]:.9g}" for name in names)]
            )
    print(f"Wrote {output} ({len(output_wavelengths)} wavelengths)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usgs-zip", type=Path)
    parser.add_argument("--biohsi-zip", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="hypermix-spectra-") as tmp:
        tmpdir = Path(tmp)
        usgs = args.usgs_zip or tmpdir / "usgs_splib07a.zip"
        biohsi = args.biohsi_zip or tmpdir / "biohsi.zip"
        _download(USGS_URL, usgs, USGS_SHA256)
        _download(BIOHSI_URL, biohsi, BIOHSI_SHA256)
        build_reference_csv(usgs, biohsi, args.output)


if __name__ == "__main__":
    main()
