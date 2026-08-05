"""Testes do protocolo e da geometria bioHSI, sem depender do cubo real."""

from dataclasses import replace

import numpy as np
import pytest

from hypermix.biohsi_roi import (
    extract_rotated_crop,
    load_biohsi_54m_protocol,
    roi_polygon_in_scene,
    rotated_points_to_scene,
    scene_points_to_rotated,
)


def test_protocol_pins_the_nine_published_figure_4g_regions():
    protocol = load_biohsi_54m_protocol()

    assert protocol.sample_name == "high_flight_day_1_left_img0"
    assert protocol.crop_shape == (107, 9)
    assert len(protocol.rois) == 9
    assert [roi.concentration_um for roi in protocol.rois] == [
        250.0,
        100.0,
        50.0,
        25.0,
        10.0,
        5.0,
        1.0,
        0.1,
        0.0,
    ]
    assert sum(roi.is_positive for roi in protocol.rois) == 6


def test_protocol_pins_source_data_provenance():
    protocol = load_biohsi_54m_protocol()
    source_data = protocol.source["source_data"]

    assert source_data["sheet"] == "4G"
    assert source_data["range"] == "A1:B10"
    assert source_data["sha256"].startswith("8cb9bb5420e5")


def test_extract_rotated_crop_preserves_shape_and_uses_nan_fill():
    protocol = load_biohsi_54m_protocol()
    data = np.ones((900, 400, 2), dtype=np.float32)

    crop = extract_rotated_crop(data, protocol, order=0)

    assert crop.shape == (107, 9, 2)
    assert np.isnan(crop).any()
    assert np.nanmean(crop) == pytest.approx(1.0)


def test_extract_rotated_crop_rejects_incompatible_data():
    protocol = load_biohsi_54m_protocol()
    with pytest.raises(ValueError, match="outside"):
        extract_rotated_crop(np.zeros((100, 100)), protocol)
    with pytest.raises(ValueError, match="data must"):
        extract_rotated_crop(np.zeros((900, 400, 2, 1)), protocol)


def test_scene_and_rotated_coordinate_transforms_roundtrip():
    protocol = load_biohsi_54m_protocol()
    points = np.array([[3.0, 3.0], [50.0, 4.0], [103.0, 5.0]])

    scene = rotated_points_to_scene(points, protocol)
    recovered = scene_points_to_rotated(scene, protocol)

    np.testing.assert_allclose(recovered, points, atol=1e-10)


def test_roi_polygons_remain_inside_the_scene_crop_neighbourhood():
    protocol = load_biohsi_54m_protocol()
    polygons = [roi_polygon_in_scene(roi, protocol) for roi in protocol.rois]
    stacked = np.concatenate(polygons)

    # A rotação de um recorte estreito consulta alguns centros poucos pixels
    # além da caixa original; ndimage os preenche com NaN no frame de análise.
    margin = 5
    assert stacked[:, 0].min() >= protocol.crop_yx[0][0] - margin
    assert stacked[:, 0].max() <= protocol.crop_yx[0][1] + margin
    assert stacked[:, 1].min() >= protocol.crop_yx[1][0] - margin
    assert stacked[:, 1].max() <= protocol.crop_yx[1][1] + margin


def test_zero_rotation_reduces_to_crop_offset():
    protocol = replace(load_biohsi_54m_protocol(), rotation_degrees=0.0)
    points = np.array([[0.0, 0.0], [10.0, 4.0]])
    expected = points + np.array([729.0, 332.0])

    np.testing.assert_allclose(rotated_points_to_scene(points, protocol), expected)
