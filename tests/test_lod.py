import numpy as np
import pytest

from hypermix.lod import (
    detection_probability_at_threshold,
    grid_detection_limit,
    robust_standardize_scores,
    threshold_at_far,
)


def test_robust_standardize_scores_centers_the_median():
    scores = np.array([[1.0, 2.0], [3.0, 100.0]])
    standardized = robust_standardize_scores(scores)
    assert standardized.shape == scores.shape
    assert np.isclose(np.median(standardized), 0.0)
    assert np.all(np.isfinite(standardized))


def test_threshold_at_far_is_conservative():
    scores = np.arange(1000, dtype=float)
    threshold = threshold_at_far(scores, 1e-2)
    assert np.mean(scores > threshold) <= 1e-2
    assert np.sum(scores > threshold) == 10


def test_detection_probability_uses_external_threshold():
    scores = np.array([0.1, 0.8, 0.2, 0.9])
    labels = np.array([0, 1, 0, 1])
    pd, far = detection_probability_at_threshold(scores, labels, 0.5)
    assert pd == 1.0
    assert far == 0.0


def test_grid_detection_limit_requires_sustained_crossing():
    abundances = np.array([0.01, 0.02, 0.05, 0.10])
    pd = np.array([0.2, 0.85, 0.7, 0.95])
    assert grid_detection_limit(abundances, pd, target_pd=0.8) == 0.10


def test_grid_detection_limit_returns_none_above_range():
    assert grid_detection_limit(
        np.array([0.01, 0.02]), np.array([0.4, 0.7]), target_pd=0.8
    ) is None


@pytest.mark.parametrize(
    "call",
    [
        lambda: robust_standardize_scores(np.array([])),
        lambda: threshold_at_far(np.ones(3), 1.0),
        lambda: detection_probability_at_threshold(
            np.ones(3), np.ones(3), 0.5
        ),
        lambda: grid_detection_limit(
            np.array([0.2, 0.1]), np.array([0.8, 0.9])
        ),
    ],
)
def test_lod_helpers_validate_inputs(call):
    with pytest.raises(ValueError):
        call()
