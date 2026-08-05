import numpy as np
import pytest

from hypermix.abundance import (
    CaseBalancedAffineCalibrator,
    GroupedConformalInterval,
    finite_sample_quantile,
)
from hypermix.metrics import interval_coverage, mean_bias, mean_interval_width


def test_affine_calibrator_recovers_scale_and_offset():
    truth = np.linspace(0.02, 0.20, 50)
    raw = (truth - 0.03) / 1.8
    case_ids = np.repeat(np.arange(5), 10)
    calibrated = CaseBalancedAffineCalibrator().fit(raw, truth, case_ids)
    np.testing.assert_allclose(calibrated.predict(raw), truth, atol=1e-10)
    assert calibrated.slope_ == pytest.approx(1.8)
    assert calibrated.intercept_ == pytest.approx(0.03)


def test_affine_calibrator_weights_cases_equally():
    raw = np.zeros(101)
    truth = np.concatenate([np.zeros(100), np.ones(1)])
    cases = np.concatenate([np.zeros(100, dtype=int), np.ones(1, dtype=int)])
    calibrated = CaseBalancedAffineCalibrator().fit(raw, truth, cases)
    assert calibrated.predict(np.array([0.0]))[0] == pytest.approx(0.5)


def test_affine_calibrator_requires_fit_and_valid_truth():
    with pytest.raises(RuntimeError, match="fitted"):
        CaseBalancedAffineCalibrator().predict(np.array([0.1]))
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        CaseBalancedAffineCalibrator().fit(np.array([0.1]), np.array([1.1]))


def test_finite_sample_quantile_is_conservative():
    values = np.arange(1.0, 11.0)
    assert finite_sample_quantile(values, alpha=0.2) == 9.0
    assert finite_sample_quantile(values, alpha=0.1) == 10.0


def test_grouped_conformal_uses_case_level_quantiles():
    truth = np.tile(np.linspace(0.05, 0.15, 20), 5)
    cases = np.repeat(np.arange(5), 20)
    residual_by_case = np.repeat([0.01, 0.02, 0.03, 0.04, 0.05], 20)
    predicted = truth + residual_by_case
    interval = GroupedConformalInterval(alpha=0.2).fit(predicted, truth, cases)
    assert interval.radius_ == pytest.approx(0.05)
    lower, upper = interval.predict(np.array([0.10]))
    np.testing.assert_allclose(lower, [0.05])
    np.testing.assert_allclose(upper, [0.15])


def test_grouped_conformal_clips_physical_bounds():
    interval = GroupedConformalInterval(alpha=0.2).fit(
        np.array([0.10, 0.20, 0.30, 0.40]),
        np.array([0.05, 0.15, 0.25, 0.35]),
        np.arange(4),
    )
    lower, upper = interval.predict(np.array([0.01, 0.99]))
    assert lower[0] == 0.0
    assert upper[1] == 1.0


def test_abundance_interval_metrics():
    truth = np.array([0.02, 0.08, 0.12])
    predicted = np.array([0.03, 0.07, 0.15])
    lower = np.array([0.00, 0.05, 0.13])
    upper = np.array([0.04, 0.09, 0.17])
    assert mean_bias(predicted, truth) == pytest.approx(0.01)
    assert interval_coverage(lower, upper, truth) == pytest.approx(2 / 3)
    assert mean_interval_width(lower, upper) == pytest.approx(0.04)
    mask = np.array([False, True, True])
    assert interval_coverage(lower, upper, truth, mask=mask) == pytest.approx(0.5)
    assert mean_interval_width(lower, upper, mask=mask) == pytest.approx(0.04)


def test_interval_metrics_reject_invalid_bounds():
    with pytest.raises(ValueError, match="must not exceed"):
        interval_coverage(np.array([0.2]), np.array([0.1]), np.array([0.15]))
    with pytest.raises(ValueError, match="same shape"):
        mean_interval_width(np.array([0.0]), np.array([0.1, 0.2]))
