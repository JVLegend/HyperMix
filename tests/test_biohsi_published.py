import numpy as np
import pytest

from hypermix.biohsi_published import (
    load_published_yf10_absorbance,
    published_hkm_ucls,
    smooth_spectral_cube,
    ucls_abundances,
)


def test_published_yf10_preserves_raw_baseline_and_interpolates():
    wavelengths = np.array([399.59, 865.618, 1002.49])
    spectrum = load_published_yf10_absorbance(wavelengths)

    assert spectrum.shape == wavelengths.shape
    assert spectrum[0] == pytest.approx(-0.021080408864303846)
    assert spectrum[-1] == pytest.approx(-0.010155903829613067)
    assert spectrum[1] == pytest.approx(0.5729762938546077)


def test_spectral_smoothing_matches_nearest_moving_average():
    cube = np.arange(5, dtype=np.float32).reshape(1, 1, 5)
    smoothed = smooth_spectral_cube(cube, window_size=3)

    np.testing.assert_allclose(smoothed[0, 0], [1 / 3, 1, 2, 3, 11 / 3])
    with pytest.raises(ValueError):
        smooth_spectral_cube(cube, window_size=6)


def test_ucls_recovers_linear_coefficients():
    endmembers = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    pixels = np.array([[0.25, 0.75, 0.0], [0.8, 0.2, 0.0]])

    np.testing.assert_allclose(ucls_abundances(pixels, endmembers), pixels[:, :2])


def test_published_hkm_ucls_is_deterministic_and_masks_zero_fill():
    pytest.importorskip("sklearn")
    rng = np.random.default_rng(7)
    prototypes = np.array(
        [
            [0.9, 0.7, 0.5, 0.4, 0.3],
            [0.3, 0.4, 0.6, 0.8, 0.9],
            [0.7, 0.3, 0.8, 0.4, 0.6],
            [0.4, 0.8, 0.3, 0.7, 0.5],
        ],
        dtype=np.float32,
    )
    labels = np.arange(64).reshape(8, 8) % 4
    cube = prototypes[labels] + rng.normal(0, 0.005, size=(8, 8, 5))
    cube = np.asarray(cube, dtype=np.float32)
    cube[0, 0] = 0.0
    reference = np.array([-0.1, 0.2, 0.7, 0.2, -0.1])

    kwargs = dict(
        reduced_dims=3,
        n_init_clusters=4,
        filter_threshold=1.0,
        distance_threshold=1e-6,
    )
    first = published_hkm_ucls(cube, reference, **kwargs)
    second = published_hkm_ucls(cube, reference, **kwargs)

    assert first.score_map.shape == cube.shape[:2]
    assert np.isnan(first.score_map[0, 0])
    assert np.nanmin(first.score_map) >= 0.0
    assert first.initial_clusters == 4
    assert 2 <= first.retained_clusters <= 4
    assert first.final_clusters >= 2
    np.testing.assert_allclose(first.score_map, second.score_map, equal_nan=True)


def test_published_hkm_validates_reference_and_cluster_count():
    pytest.importorskip("sklearn")
    cube = np.ones((2, 2, 3), dtype=np.float32)

    with pytest.raises(ValueError, match="match cube bands"):
        published_hkm_ucls(cube, np.ones(2), n_init_clusters=2)
    with pytest.raises(ValueError, match="exceeds"):
        published_hkm_ucls(cube, np.ones(3), n_init_clusters=5)
