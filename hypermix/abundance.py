"""Leakage-resistant abundance calibration and grouped prediction intervals."""

from __future__ import annotations

import numpy as np

__all__ = [
    "CaseBalancedAffineCalibrator",
    "GroupedConformalInterval",
    "finite_sample_quantile",
]


def _regression_inputs(
    predicted: np.ndarray,
    truth: np.ndarray,
    case_ids: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    predicted = np.asarray(predicted, dtype=np.float64).ravel()
    truth = np.asarray(truth, dtype=np.float64).ravel()
    if predicted.shape != truth.shape or predicted.size == 0:
        raise ValueError("predicted and truth must have the same non-zero size")
    if not np.all(np.isfinite(predicted)) or not np.all(np.isfinite(truth)):
        raise ValueError("predicted and truth must be finite")
    if np.any((truth < 0.0) | (truth > 1.0)):
        raise ValueError("truth must lie in [0, 1]")
    if case_ids is None:
        case_ids = np.zeros(predicted.size, dtype=np.int64)
    else:
        case_ids = np.asarray(case_ids).ravel()
        if case_ids.shape != predicted.shape:
            raise ValueError("case_ids must have the same size as predicted")
    return predicted, truth, case_ids


def finite_sample_quantile(values: np.ndarray, alpha: float) -> float:
    """Conformal upper quantile with the finite-sample rank correction."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    values = np.asarray(values, dtype=np.float64).ravel()
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("values must be non-empty and finite")
    rank = int(np.ceil((values.size + 1) * (1.0 - alpha)))
    rank = min(max(rank, 1), values.size)
    return float(np.partition(values, rank - 1)[rank - 1])


class CaseBalancedAffineCalibrator:
    """Fit a non-decreasing affine abundance scale with equal case weight.

    Each scene-seed case contributes total weight one, regardless of how many
    selected pixels it contains. Predictions are clipped to the physical
    abundance range only after applying the fitted affine transformation.
    """

    def __init__(self) -> None:
        self.slope_: float | None = None
        self.intercept_: float | None = None

    def fit(
        self,
        predicted: np.ndarray,
        truth: np.ndarray,
        case_ids: np.ndarray | None = None,
    ) -> "CaseBalancedAffineCalibrator":
        predicted, truth, case_ids = _regression_inputs(predicted, truth, case_ids)
        _, inverse, counts = np.unique(case_ids, return_inverse=True, return_counts=True)
        weights = 1.0 / counts[inverse]
        weights /= weights.sum()
        design = np.column_stack([predicted, np.ones(predicted.size)])
        root_weights = np.sqrt(weights)
        parameters, *_ = np.linalg.lstsq(
            design * root_weights[:, None],
            truth * root_weights,
            rcond=None,
        )
        slope, intercept = (float(parameters[0]), float(parameters[1]))
        if slope < 0.0:
            slope = 0.0
            intercept = float(np.sum(weights * truth))
        self.slope_ = slope
        self.intercept_ = intercept
        return self

    def predict(self, predicted: np.ndarray) -> np.ndarray:
        if self.slope_ is None or self.intercept_ is None:
            raise RuntimeError("calibrator must be fitted before prediction")
        predicted = np.asarray(predicted, dtype=np.float64)
        if not np.all(np.isfinite(predicted)):
            raise ValueError("predicted must be finite")
        return np.clip(self.slope_ * predicted + self.intercept_, 0.0, 1.0)


class GroupedConformalInterval:
    """Constant-width split-conformal intervals calibrated by independent cases.

    The residual quantile is first computed within each scene-seed case. A
    second finite-sample quantile across cases determines the shared radius.
    This avoids presenting correlated pixels as independent calibration units.
    """

    def __init__(self, alpha: float = 0.10) -> None:
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        self.alpha = float(alpha)
        self.radius_: float | None = None
        self.case_radii_: np.ndarray | None = None

    def fit(
        self,
        predicted: np.ndarray,
        truth: np.ndarray,
        case_ids: np.ndarray,
    ) -> "GroupedConformalInterval":
        predicted, truth, case_ids = _regression_inputs(predicted, truth, case_ids)
        residuals = np.abs(predicted - truth)
        radii = []
        for case in np.unique(case_ids):
            radii.append(finite_sample_quantile(residuals[case_ids == case], self.alpha))
        self.case_radii_ = np.asarray(radii, dtype=np.float64)
        self.radius_ = finite_sample_quantile(self.case_radii_, self.alpha)
        return self

    def predict(self, predicted: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.radius_ is None:
            raise RuntimeError("interval calibrator must be fitted before prediction")
        predicted = np.asarray(predicted, dtype=np.float64)
        if not np.all(np.isfinite(predicted)):
            raise ValueError("predicted must be finite")
        lower = np.clip(predicted - self.radius_, 0.0, 1.0)
        upper = np.clip(predicted + self.radius_, 0.0, 1.0)
        return lower, upper
