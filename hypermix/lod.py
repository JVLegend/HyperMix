"""Operational detection-limit helpers with calibration/evaluation separation."""

from __future__ import annotations

import numpy as np

__all__ = [
    "detection_probability_at_threshold",
    "grid_detection_limit",
    "robust_standardize_scores",
    "threshold_at_far",
]


def robust_standardize_scores(scores: np.ndarray) -> np.ndarray:
    """Standardize a score map using its unlabeled median and robust scale."""

    values = np.asarray(scores, dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("scores must be a non-empty finite array")
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = max(1.4826 * mad, 1e-12)
    return (values - median) / scale


def threshold_at_far(background_scores: np.ndarray, far: float) -> float:
    """Choose a conservative threshold from target-free calibration scores."""

    if not 0.0 <= far < 1.0:
        raise ValueError("far must lie in [0, 1)")
    values = np.asarray(background_scores, dtype=np.float64).ravel()
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("background_scores must be non-empty and finite")
    allowed = int(np.floor(far * values.size))
    ordered = np.sort(values)
    return float(ordered[-(allowed + 1)])


def detection_probability_at_threshold(
    scores: np.ndarray,
    labels: np.ndarray,
    threshold: float,
) -> tuple[float, float]:
    """Return Pd and realized FAR at a threshold fixed outside evaluation."""

    values = np.asarray(scores, dtype=np.float64).ravel()
    truth = np.asarray(labels).ravel()
    if values.shape != truth.shape:
        raise ValueError("scores and labels must have the same size")
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("scores must be non-empty and finite")
    if not np.isfinite(threshold):
        raise ValueError("threshold must be finite")
    if not np.all(np.isin(truth, (0, 1, False, True))):
        raise ValueError("labels must be binary")
    truth = truth.astype(bool)
    if not np.any(truth) or np.all(truth):
        raise ValueError("both positive and negative labels are required")
    detections = values > float(threshold)
    return float(np.mean(detections[truth])), float(np.mean(detections[~truth]))


def grid_detection_limit(
    abundances: np.ndarray,
    detection_probabilities: np.ndarray,
    target_pd: float = 0.8,
) -> float | None:
    """Return the first tested abundance with a sustained target Pd.

    A crossing is sustained only when every higher tested abundance also meets
    ``target_pd``.  Returning a tested grid point avoids false interpolation
    precision.  ``None`` means the limit lies above the evaluated range.
    """

    levels = np.asarray(abundances, dtype=np.float64)
    probabilities = np.asarray(detection_probabilities, dtype=np.float64)
    if levels.ndim != 1 or probabilities.ndim != 1 or levels.shape != probabilities.shape:
        raise ValueError("abundances and detection_probabilities must be equal 1-D arrays")
    if levels.size == 0 or not np.all(np.isfinite(levels)):
        raise ValueError("abundances must be non-empty and finite")
    if np.any(levels <= 0.0) or np.any(np.diff(levels) <= 0.0):
        raise ValueError("abundances must be positive and strictly increasing")
    if not np.all(np.isfinite(probabilities)) or np.any(
        (probabilities < 0.0) | (probabilities > 1.0)
    ):
        raise ValueError("detection probabilities must lie in [0, 1]")
    if not 0.0 < target_pd <= 1.0:
        raise ValueError("target_pd must lie in (0, 1]")

    meets = probabilities >= float(target_pd)
    sustained = np.logical_and.accumulate(meets[::-1])[::-1]
    candidates = np.flatnonzero(sustained)
    return float(levels[candidates[0]]) if candidates.size else None
