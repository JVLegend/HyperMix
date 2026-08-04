"""Testes do leitor ENVI, todos sintéticos e independentes do cubo de 629 MB."""

import numpy as np
import pytest

from hypermix.envi import (
    envi_nodata_mask,
    open_envi_cube,
    parse_envi_header,
)


def _write_cube(tmp_path, data, interleave, *, dtype="<f4", offset=0, extra=""):
    """Grava um par .hdr/binário sintético no interleave pedido."""
    lines, samples, bands = data.shape
    order = {
        "bsq": (2, 0, 1),
        "bil": (0, 2, 1),
        "bip": (0, 1, 2),
    }[interleave]
    payload = np.ascontiguousarray(data.transpose(order), dtype=dtype)
    binary = tmp_path / "scene"
    binary.write_bytes(b"\x00" * offset + payload.tobytes())
    header = tmp_path / "scene.hdr"
    header.write_text(
        "ENVI\n"
        f"samples = {samples}\n"
        f"lines = {lines}\n"
        f"bands = {bands}\n"
        f"header offset = {offset}\n"
        "file type = ENVI Standard\n"
        "data type = 4\n"
        f"interleave = {interleave}\n"
        f"byte order = {0 if dtype.startswith('<') else 1}\n"
        + extra,
        encoding="utf-8",
    )
    return header


@pytest.mark.parametrize("interleave", ["bsq", "bil", "bip"])
def test_open_envi_cube_roundtrips_every_interleave(tmp_path, interleave):
    rng = np.random.default_rng(0)
    data = rng.normal(size=(5, 4, 3)).astype("<f4")

    header_path = _write_cube(tmp_path, data, interleave)
    cube, header = open_envi_cube(header_path)

    assert header.interleave == interleave
    assert header.shape == (5, 4, 3)
    assert cube.shape == (5, 4, 3)
    np.testing.assert_array_equal(np.asarray(cube), data)


def test_open_envi_cube_preserves_radiometric_scale(tmp_path):
    """O loader antigo normalizava; este devolve os valores medidos."""
    data = np.full((3, 2, 2), 0.25, dtype="<f4")
    data[0, 0, 0] = 0.9

    cube, _ = open_envi_cube(_write_cube(tmp_path, data, "bsq"))

    assert float(np.asarray(cube).min()) == pytest.approx(0.25)
    assert float(np.asarray(cube).max()) == pytest.approx(0.9)


def test_parse_envi_header_reads_wavelengths_units_and_comments(tmp_path):
    extra = (
        "wavelength units = nm\n"
        "description = {HEADWALL Hyperspec III,RADIANCE,REFLECTANCE}\n"
        "wavelength = {\n398.411\n,400.632\n,402.852\n}\n"
        ";Units = mW/(cm2*sr*um)\n"
        ";Exposure (ms) = 6.994\n"
    )
    header_path = _write_cube(
        tmp_path, np.zeros((2, 2, 3), dtype="<f4"), "bsq", extra=extra
    )

    header = parse_envi_header(header_path)

    assert header.wavelength_units == "nm"
    assert header.wavelengths is not None
    np.testing.assert_allclose(header.wavelengths, [398.411, 400.632, 402.852])
    assert "RADIANCE" in (header.description or "")
    # A unidade declarada pela Headwall vive num comentário, não numa chave ENVI.
    assert header.comments["units"] == "mW/(cm2*sr*um)"
    assert header.comments["exposure (ms)"] == "6.994"


def test_parse_envi_header_rejects_wavelength_count_mismatch(tmp_path):
    header_path = _write_cube(
        tmp_path,
        np.zeros((2, 2, 3), dtype="<f4"),
        "bsq",
        extra="wavelength = {400, 500}\n",
    )

    with pytest.raises(ValueError, match="wavelength count"):
        parse_envi_header(header_path)


def test_header_reports_dtype_and_expected_size(tmp_path):
    header = parse_envi_header(
        _write_cube(tmp_path, np.zeros((5, 4, 3), dtype="<f4"), "bsq")
    )

    assert header.dtype == np.dtype("<f4")
    assert header.expected_size == 5 * 4 * 3 * 4


def test_open_envi_cube_honours_header_offset(tmp_path):
    rng = np.random.default_rng(1)
    data = rng.normal(size=(3, 3, 2)).astype("<f4")

    cube, header = open_envi_cube(_write_cube(tmp_path, data, "bsq", offset=64))

    assert header.header_offset == 64
    np.testing.assert_array_equal(np.asarray(cube), data)


def test_open_envi_cube_rejects_truncated_binary(tmp_path):
    header_path = _write_cube(tmp_path, np.zeros((4, 4, 3), dtype="<f4"), "bsq")
    binary = tmp_path / "scene"
    binary.write_bytes(binary.read_bytes()[:-16])

    with pytest.raises(ValueError, match="expected at least"):
        open_envi_cube(header_path)


def test_open_envi_cube_flags_trailing_bytes_unless_allowed(tmp_path):
    header_path = _write_cube(tmp_path, np.zeros((4, 4, 3), dtype="<f4"), "bsq")
    binary = tmp_path / "scene"
    binary.write_bytes(binary.read_bytes() + b"\x00" * 32)

    with pytest.raises(ValueError, match="expected exactly"):
        open_envi_cube(header_path)

    cube, _ = open_envi_cube(header_path, strict_size=False)
    assert cube.shape == (4, 4, 3)


def test_open_envi_cube_requires_a_paired_binary(tmp_path):
    header_path = _write_cube(tmp_path, np.zeros((2, 2, 2), dtype="<f4"), "bsq")
    (tmp_path / "scene").unlink()

    with pytest.raises(FileNotFoundError, match="no ENVI binary paired"):
        open_envi_cube(header_path)


def test_parse_envi_header_rejects_a_non_envi_file(tmp_path):
    path = tmp_path / "other.hdr"
    path.write_text("samples = 2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not an ENVI header"):
        parse_envi_header(path)


def test_envi_nodata_mask_marks_only_all_band_fill():
    cube = np.ones((2, 3, 4), dtype=np.float32)
    cube[0, 0, :] = 0.0          # preenchimento da ortorretificação
    cube[1, 2, 0] = 0.0          # zero em uma banda apenas, é medida

    mask = envi_nodata_mask(cube)

    assert mask.shape == (2, 3)
    assert bool(mask[0, 0]) is True
    assert bool(mask[1, 2]) is False
    assert mask.sum() == 1
