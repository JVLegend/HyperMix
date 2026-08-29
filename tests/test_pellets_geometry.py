"""Testes do artefato congelado de geometria da placa de pellets.

Offline: validam apenas o artefato versionado, nunca o cubo de 1,8 GB.
"""

import hashlib
import json
from importlib.resources import files

ARTIFACT = files("hypermix.data").joinpath("biohsi_pellets_plate_geometry.json")


def _load():
    with ARTIFACT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_geometry_describes_a_full_96_well_plate():
    doc = _load()
    geom = doc["geometry_image_frame"]
    assert geom["n_wells"] == 96
    assert len(geom["rows_y"]) == 8
    assert len(geom["cols_x"]) == 12
    assert geom["row_labels"] == list("ABCDEFGH")


def test_grid_pitch_is_uniform_on_both_axes():
    geom = _load()["geometry_image_frame"]
    rows, cols = geom["rows_y"], geom["cols_x"]
    assert {b - a for a, b in zip(rows, rows[1:])} == {geom["row_pitch_px"]}
    assert {b - a for a, b in zip(cols, cols[1:])} == {geom["col_pitch_px"]}


def test_geometry_hash_matches_its_own_content():
    doc = _load()
    blob = json.dumps(
        doc["geometry_image_frame"], sort_keys=True, separators=(",", ":")
    ).encode()
    assert hashlib.sha256(blob).hexdigest() == doc["geometry_sha256"]


def test_artifact_records_provenance_and_open_questions():
    doc = _load()
    assert doc["zenodo_doi"] == "10.5281/zenodo.14756889"
    assert doc["cube_interleave"] == "bil"
    assert doc["cube_shape_lines_samples_bands"] == [754, 1600, 371]
    # A geometria nao autoriza comparacao de metodos por si so.
    assert "NAO autoriza" in doc["usage_rule"]
    assert len(doc["unresolved"]) >= 3
