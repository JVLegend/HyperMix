"""Testes offline do artefato e das estatísticas do gradiente de 24 m."""

import hashlib
import json
from importlib.resources import files

import numpy as np

from scripts.real_target_24m_gradient import _sample, _spearman

ARTIFACT = files("hypermix.data").joinpath("biohsi_24m_blot_geometry.json")


def _load():
    with ARTIFACT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_artifact_hash_matches_its_geometry():
    doc = _load()
    blob = json.dumps(
        doc["geometry_image_frame"], sort_keys=True, separators=(",", ":")
    ).encode()
    assert hashlib.sha256(blob).hexdigest() == doc["geometry_sha256"]


def test_geometry_has_six_positions_in_two_replicates():
    geom = _load()["geometry_image_frame"]
    assert len(geom["replicate_a_xy"]) == 6
    assert len(geom["replicate_b_xy"]) == 6
    assert geom["position_0_role"] == "positive_control"
    assert geom["position_5_role"] == "negative_control"


def test_annotation_declares_its_provisional_nature():
    doc = _load()
    assert "provis" in doc["annotation_method"].lower()
    # A identidade dos controles precede a medição; isso sustenta a predição.
    assert "anterior a qualquer medicao" in doc["control_identity_source"]
    assert len(doc["unresolved"]) >= 3


def test_spearman_is_minus_one_for_a_strictly_decreasing_sequence():
    positions = np.arange(6, dtype=float)
    decreasing = np.array([5.0, 4.0, 3.0, 2.0, 1.0, 0.0])

    assert _spearman(positions, decreasing) == -1.0
    assert _spearman(positions, positions) == 1.0


def test_sample_averages_a_disk_around_each_centre():
    depth = np.zeros((40, 40))
    depth[20, 10] = 1.0
    depth[20, 30] = 2.0

    values = _sample(depth, [(10, 20), (30, 20)], radius=3)

    assert values[1] > values[0] > 0.0
    # média sobre o disco, não o valor do pixel central
    assert values[0] < 1.0
