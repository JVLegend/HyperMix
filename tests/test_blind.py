import numpy as np
import pytest

from hypermix.blind import (
    BLIND_TRACKS,
    blind_anomaly_features,
    family_detection_features,
    scale_target_library,
)


def _scene(seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mixing = rng.normal(size=(18, 16, 4))
    spectra = rng.uniform(0.1, 1.0, size=(4, 21))
    return mixing @ spectra + rng.normal(0.0, 0.02, size=(18, 16, 21))


def test_blind_tracks_keep_exact_target_outside_non_oracle_tracks():
    tracks = {track.name: track for track in BLIND_TRACKS}
    assert set(tracks) == {"oracle", "family", "unknown"}
    assert tracks["oracle"].exact_target_available
    assert not tracks["family"].exact_target_available
    assert tracks["family"].target_family_available
    assert not tracks["unknown"].exact_target_available
    assert not tracks["unknown"].target_family_available


def test_scale_target_library_matches_scene_scale():
    cube = _scene()
    library = np.vstack((np.linspace(0.1, 1.0, 21), np.linspace(1.0, 0.2, 21)))
    scaled = scale_target_library(library, cube)
    assert scaled.shape == library.shape
    assert np.allclose(np.max(np.abs(scaled), axis=1), np.mean(np.abs(cube)))


def test_blind_anomaly_features_are_finite_and_standardized():
    cube = _scene()
    features = blind_anomaly_features(cube)
    assert features.shape == (18 * 16, 6)
    assert np.all(np.isfinite(features))
    assert np.allclose(features.mean(axis=0), 0.0, atol=1e-5)


def test_family_features_accept_single_related_signature():
    cube = _scene()
    signature = np.linspace(0.1, 1.0, cube.shape[-1])
    features = family_detection_features(cube, signature)
    assert features.shape == (18 * 16, 6)
    assert np.all(np.isfinite(features))


def test_blind_feature_validation_rejects_invalid_inputs():
    cube = _scene()
    with pytest.raises(ValueError):
        blind_anomaly_features(cube[..., 0])
    with pytest.raises(ValueError):
        family_detection_features(cube, np.ones((2, 20)))
    with pytest.raises(ValueError):
        family_detection_features(cube, np.ones((2, 21)), rank=3)
    with pytest.raises(ValueError):
        blind_anomaly_features(cube, rx_score=np.ones((2, 2)))
