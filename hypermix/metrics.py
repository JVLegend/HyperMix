"""Detection metrics (NumPy only)."""

from __future__ import annotations

import numpy as np

__all__ = [
    "roc_auc",
    "roc_curve",
    "pd_at_far",
    "binary_nll",
    "negative_log_likelihood",
    "brier_score",
    "expected_calibration_error",
    "reliability_curve",
    "pearson_r",
    "mean_absolute_error",
]


def _probability_inputs(
    probabilities: np.ndarray,
    labels: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    probabilities = np.asarray(probabilities, dtype=np.float64).ravel()
    labels = np.asarray(labels).ravel()
    if probabilities.shape != labels.shape:
        raise ValueError("probabilities and labels must have the same size")
    if probabilities.size == 0:
        raise ValueError("probability metrics require at least one example")
    if not np.all(np.isfinite(probabilities)):
        raise ValueError("probabilities must be finite")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("probabilities must lie in [0, 1]")
    if not np.all(np.isin(labels, (0, 1, False, True))):
        raise ValueError("labels must be binary")
    return probabilities, labels.astype(np.float64)


def binary_nll(
    probabilities: np.ndarray,
    labels: np.ndarray,
    eps: float = 1e-12,
) -> float:
    """Mean binary negative log-likelihood for calibrated probabilities."""
    if not 0.0 < eps < 0.5:
        raise ValueError("eps must lie in (0, 0.5)")
    probabilities, labels = _probability_inputs(probabilities, labels)
    clipped = np.clip(probabilities, eps, 1.0 - eps)
    return float(-np.mean(
        labels * np.log(clipped) + (1.0 - labels) * np.log1p(-clipped)
    ))


def negative_log_likelihood(
    probabilities: np.ndarray,
    labels: np.ndarray,
    eps: float = 1e-12,
) -> float:
    """Descriptive alias for :func:`binary_nll`."""
    return binary_nll(probabilities, labels, eps=eps)


def brier_score(probabilities: np.ndarray, labels: np.ndarray) -> float:
    """Mean squared probability error for a binary event."""
    probabilities, labels = _probability_inputs(probabilities, labels)
    return float(np.mean((probabilities - labels) ** 2))


def reliability_curve(
    probabilities: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15,
) -> dict[str, np.ndarray]:
    """Uniform-bin reliability data, including empty-bin counts.

    The returned dictionary contains ``bin_edges``, ``counts``,
    ``mean_probability`` and ``event_rate``. Means are NaN for empty bins.
    A probability of exactly one belongs to the final bin.
    """
    if not isinstance(n_bins, (int, np.integer)) or n_bins < 1:
        raise ValueError("n_bins must be a positive integer")
    probabilities, labels = _probability_inputs(probabilities, labels)
    edges = np.linspace(0.0, 1.0, int(n_bins) + 1)
    bin_index = np.minimum(
        np.searchsorted(edges, probabilities, side="right") - 1,
        int(n_bins) - 1,
    )
    counts = np.bincount(bin_index, minlength=int(n_bins)).astype(np.int64)
    probability_sum = np.bincount(
        bin_index, weights=probabilities, minlength=int(n_bins)
    )
    label_sum = np.bincount(
        bin_index, weights=labels, minlength=int(n_bins)
    )
    mean_probability = np.full(int(n_bins), np.nan, dtype=np.float64)
    event_rate = np.full(int(n_bins), np.nan, dtype=np.float64)
    occupied = counts > 0
    mean_probability[occupied] = probability_sum[occupied] / counts[occupied]
    event_rate[occupied] = label_sum[occupied] / counts[occupied]
    return {
        "bin_edges": edges,
        "counts": counts,
        "mean_probability": mean_probability,
        "event_rate": event_rate,
    }


def expected_calibration_error(
    probabilities: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15,
) -> float:
    """Expected calibration error with fixed, uniform probability bins."""
    probabilities, labels = _probability_inputs(probabilities, labels)
    curve = reliability_curve(probabilities, labels, n_bins=n_bins)
    occupied = curve["counts"] > 0
    gaps = np.abs(
        curve["mean_probability"][occupied] - curve["event_rate"][occupied]
    )
    weights = curve["counts"][occupied] / probabilities.size
    return float(np.sum(weights * gaps))


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Area under the ROC curve via the Mann-Whitney U statistic.

    Ties count as 0.5. Returns 0.5 when a class is absent.
    """
    scores = np.asarray(scores, dtype=np.float64).ravel()
    labels = np.asarray(labels).ravel().astype(bool)
    n_pos = int(labels.sum())
    n_neg = labels.size - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, scores.size + 1)
    # average ranks over tied score groups
    _, inv, counts = np.unique(scores, return_inverse=True, return_counts=True)
    sums = np.zeros(counts.size)
    np.add.at(sums, inv, ranks)
    ranks = (sums / counts)[inv]
    rank_pos = ranks[labels].sum()
    return float((rank_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def roc_curve(scores: np.ndarray, labels: np.ndarray):
    """Return (fpr, tpr) arrays for plotting."""
    scores = np.asarray(scores, dtype=np.float64).ravel()
    labels = np.asarray(labels).ravel().astype(bool)
    order = np.argsort(-scores, kind="mergesort")
    y = labels[order]
    tp = np.cumsum(y)
    fp = np.cumsum(~y)
    tpr = np.concatenate([[0.0], tp / max(tp[-1], 1)])
    fpr = np.concatenate([[0.0], fp / max(fp[-1], 1)])
    return fpr, tpr


def pd_at_far(
    scores: np.ndarray,
    labels: np.ndarray,
    far: float,
) -> float:
    """Probability of detection at a fixed empirical false-alarm rate.

    The threshold is selected only from negative examples. Scores must exceed
    the threshold strictly, which makes the achieved empirical FAR conservative
    when scores are tied. ``far`` must lie in ``[0, 1)``. Both classes must be
    present because a fixed-FAR operating point is undefined otherwise.
    """
    if not 0.0 <= far < 1.0:
        raise ValueError("far must lie in [0, 1)")
    values = np.asarray(scores, dtype=np.float64).ravel()
    truth = np.asarray(labels).ravel().astype(bool)
    if values.shape != truth.shape:
        raise ValueError("scores and labels must have the same size")
    positives = values[truth]
    negatives = values[~truth]
    if positives.size == 0 or negatives.size == 0:
        raise ValueError("pd_at_far requires positive and negative examples")
    allowed_false_alarms = int(np.floor(far * negatives.size))
    ordered_negatives = np.sort(negatives)
    threshold = ordered_negatives[-(allowed_false_alarms + 1)]
    return float(np.mean(positives > threshold))


def _selected_pair(
    predicted: np.ndarray,
    truth: np.ndarray,
    mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    predicted = np.asarray(predicted, dtype=np.float64)
    truth = np.asarray(truth, dtype=np.float64)
    if predicted.shape != truth.shape:
        raise ValueError("predicted and truth must have the same shape")
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != truth.shape:
            raise ValueError("mask and truth must have the same shape")
        predicted, truth = predicted[mask], truth[mask]
    else:
        predicted, truth = predicted.ravel(), truth.ravel()
    if predicted.size == 0:
        raise ValueError("metric selection must contain at least one value")
    return predicted, truth


def pearson_r(
    predicted: np.ndarray,
    truth: np.ndarray,
    mask: np.ndarray | None = None,
) -> float:
    """Pearson correlation, optionally restricted to a declared mask."""
    predicted, truth = _selected_pair(predicted, truth, mask)
    if predicted.std() < 1e-9 or truth.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(predicted, truth)[0, 1])


def mean_absolute_error(
    predicted: np.ndarray,
    truth: np.ndarray,
    mask: np.ndarray | None = None,
) -> float:
    """Mean absolute error, optionally restricted to a declared mask."""
    predicted, truth = _selected_pair(predicted, truth, mask)
    return float(np.mean(np.abs(predicted - truth)))
