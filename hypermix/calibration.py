"""Probability calibration for detector scores and binary logits.

Calibration is deliberately separated from detector fitting. Callers must fit
these calibrators on a labeled calibration split and reserve evaluation labels
for metrics only.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from .metrics import binary_nll

__all__ = ["PlattCalibrator", "TemperatureCalibrator"]


def _binary_fit_inputs(values: np.ndarray, labels: np.ndarray):
    values = np.asarray(values, dtype=np.float64).ravel()
    labels = np.asarray(labels).ravel()
    if values.shape != labels.shape or values.size == 0:
        raise ValueError("values and labels must have the same non-zero size")
    if not np.all(np.isfinite(values)):
        raise ValueError("values must be finite")
    if not np.all(np.isin(labels, (0, 1, False, True))):
        raise ValueError("labels must be binary")
    labels = labels.astype(np.float64)
    if labels.min() == labels.max():
        raise ValueError("calibration requires both classes")
    return values, labels


class PlattCalibrator:
    """Fit ``sigmoid(slope * score + intercept)`` by unweighted NLL."""

    def __init__(self):
        self.slope_: float | None = None
        self.intercept_: float | None = None

    def fit(self, scores: np.ndarray, labels: np.ndarray) -> "PlattCalibrator":
        scores, labels = _binary_fit_inputs(scores, labels)
        scale = float(np.std(scores)) or 1.0
        center = float(np.mean(scores))
        normalized = (scores - center) / scale
        prevalence = np.clip(labels.mean(), 1e-9, 1.0 - 1e-9)
        initial = np.array([1.0, np.log(prevalence / (1.0 - prevalence))])

        def objective(parameters):
            probabilities = expit(parameters[0] * normalized + parameters[1])
            return binary_nll(probabilities, labels)

        result = minimize(objective, initial, method="BFGS")
        if not result.success and not np.isfinite(result.fun):
            raise RuntimeError(f"Platt calibration failed: {result.message}")
        self.slope_ = float(result.x[0] / scale)
        self.intercept_ = float(result.x[1] - result.x[0] * center / scale)
        return self

    def predict_proba(self, scores: np.ndarray) -> np.ndarray:
        if self.slope_ is None or self.intercept_ is None:
            raise RuntimeError("calibrator must be fitted before prediction")
        scores = np.asarray(scores, dtype=np.float64)
        if not np.all(np.isfinite(scores)):
            raise ValueError("scores must be finite")
        return expit(self.slope_ * scores + self.intercept_)


class TemperatureCalibrator:
    """Binary temperature scaling with an intercept correction.

    ``p = sigmoid(logit / temperature + bias)`` uses the same two calibration
    degrees of freedom as Platt scaling while constraining the logit slope to
    be positive. The bias is needed for detectors trained with class-weighted
    loss, whose raw intercept does not encode the deployment prevalence.
    """

    def __init__(self):
        self.temperature_: float | None = None
        self.bias_: float | None = None

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> "TemperatureCalibrator":
        logits, labels = _binary_fit_inputs(logits, labels)
        prevalence = np.clip(labels.mean(), 1e-9, 1.0 - 1e-9)
        initial = np.array([0.0, np.log(prevalence / (1.0 - prevalence))])

        def objective(parameters):
            temperature = np.exp(np.clip(parameters[0], -10.0, 10.0))
            probabilities = expit(logits / temperature + parameters[1])
            return binary_nll(probabilities, labels)

        result = minimize(objective, initial, method="BFGS")
        if not result.success and not np.isfinite(result.fun):
            raise RuntimeError(f"temperature calibration failed: {result.message}")
        self.temperature_ = float(np.exp(np.clip(result.x[0], -10.0, 10.0)))
        self.bias_ = float(result.x[1])
        return self

    def predict_proba(self, logits: np.ndarray) -> np.ndarray:
        if self.temperature_ is None or self.bias_ is None:
            raise RuntimeError("calibrator must be fitted before prediction")
        logits = np.asarray(logits, dtype=np.float64)
        if not np.all(np.isfinite(logits)):
            raise ValueError("logits must be finite")
        return expit(logits / self.temperature_ + self.bias_)
