"""Classical target detectors used as transparent comparison points.

These established methods are useful reference baselines, but this small set is
not presented as an exhaustive comparison with the state of the art.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "spectral_matched_filter",
    "smoothed_matched_filter",
    "matched_subspace_detector",
    "smoothed_matched_subspace_detector",
    "rx_detector",
    "ace",
    "spectral_angle_mapper",
]


def _prepare(cube: np.ndarray, target: np.ndarray):
    h, w, b = cube.shape
    x = cube.reshape(-1, b).astype(np.float64)
    mu = x.mean(axis=0)
    xc = x - mu
    cov = (xc.T @ xc) / xc.shape[0]
    cov += 1e-6 * np.trace(cov) / b * np.eye(b)   # ridge for stability
    cinv = np.linalg.inv(cov)
    t = target.astype(np.float64) - mu
    return h, w, xc, cinv, t


def spectral_matched_filter(cube: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Constrained matched filter score map, shape (H, W).

    score(x) = (x - mu)^T C^-1 (t - mu) / ((t - mu)^T C^-1 (t - mu))
    """
    h, w, xc, cinv, t = _prepare(cube, target)
    num = xc @ (cinv @ t)
    den = float(t @ (cinv @ t)) + 1e-12
    return (num / den).reshape(h, w)


def smoothed_matched_filter(
    cube: np.ndarray,
    target: np.ndarray,
    sigma: float = 1.5,
) -> np.ndarray:
    """Matched-filter score followed by spatial Gaussian smoothing.

    This baseline receives the same kind of spatial prior available to the
    learned detector. ``sigma`` is measured in pixels and must be non-negative;
    zero recovers the ordinary per-pixel matched filter.
    """
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    score = spectral_matched_filter(cube, target)
    if sigma == 0:
        return score

    from scipy.ndimage import gaussian_filter

    return gaussian_filter(score, sigma=float(sigma), mode="reflect")


def matched_subspace_detector(
    cube: np.ndarray,
    targets: np.ndarray,
    rank: int | None = None,
) -> np.ndarray:
    """Whitened target-subspace projection score, shape ``(H, W)``.

    ``targets`` is a matrix of plausible target signatures with shape
    ``(n_targets, n_bands)``. The detector estimates background covariance from
    the scene, whitens pixels and signatures, then measures the fraction of
    whitened pixel energy captured by the target subspace. With one signature,
    this reduces numerically to ACE. The optional ``rank`` caps the number of
    target directions retained after SVD.

    This is the classical comparison designed for target variability. It is
    not presented as a novel HyperMix detector.
    """
    values = np.asarray(targets, dtype=np.float64)
    if values.ndim == 1:
        values = values[None, :]
    if values.ndim != 2 or values.shape[1] != cube.shape[2]:
        raise ValueError("targets must have shape (n_targets, n_bands)")
    if values.shape[0] < 1:
        raise ValueError("at least one target signature is required")
    if rank is not None and (rank < 1 or rank > min(values.shape)):
        raise ValueError("rank must be between 1 and min(targets.shape)")

    h, w, bands = cube.shape
    pixels = cube.reshape(-1, bands).astype(np.float64)
    mean = pixels.mean(axis=0)
    centered = pixels - mean
    covariance = (centered.T @ centered) / centered.shape[0]
    ridge = max(1e-12, 1e-6 * float(np.trace(covariance)) / bands)
    eigenvalues, eigenvectors = np.linalg.eigh(
        covariance + ridge * np.eye(bands)
    )
    whitening = (
        eigenvectors
        * (1.0 / np.sqrt(np.maximum(eigenvalues, ridge)))[None, :]
    ) @ eigenvectors.T
    whitened_pixels = centered @ whitening
    whitened_targets = (values - mean) @ whitening

    _, singular_values, right_vectors = np.linalg.svd(
        whitened_targets, full_matrices=False
    )
    if rank is None:
        tolerance = max(whitened_targets.shape) * np.finfo(float).eps
        tolerance *= singular_values[0] if singular_values.size else 1.0
        retained = max(1, int(np.sum(singular_values > tolerance)))
    else:
        retained = rank
    basis = right_vectors[:retained].T
    projected = whitened_pixels @ basis
    numerator = np.einsum("nr,nr->n", projected, projected)
    denominator = np.einsum(
        "nb,nb->n", whitened_pixels, whitened_pixels
    ) + 1e-12
    return (numerator / denominator).reshape(h, w)


def smoothed_matched_subspace_detector(
    cube: np.ndarray,
    targets: np.ndarray,
    sigma: float = 1.5,
    rank: int | None = None,
) -> np.ndarray:
    """Matched-subspace score followed by fixed Gaussian smoothing."""
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    score = matched_subspace_detector(cube, targets, rank=rank)
    if sigma == 0:
        return score
    from scipy.ndimage import gaussian_filter

    return gaussian_filter(score, sigma=float(sigma), mode="reflect")


def rx_detector(cube: np.ndarray) -> np.ndarray:
    """Global Reed-Xiaoli anomaly score, shape ``(H, W)``.

    RX estimates one Gaussian background model from every unlabeled pixel in
    the scene and returns the squared Mahalanobis distance
    ``(x - mu)^T C^-1 (x - mu)``. It is target-agnostic and therefore complements
    target-aware matched filtering in the background-model experiment.
    """
    values = np.asarray(cube)
    if values.ndim != 3:
        raise ValueError("cube must have shape (height, width, bands)")
    h, w, bands = values.shape
    pixels = values.reshape(-1, bands).astype(np.float64)
    if pixels.shape[0] < 2:
        raise ValueError("cube must contain at least two pixels")
    centered = pixels - pixels.mean(axis=0)
    covariance = (centered.T @ centered) / pixels.shape[0]
    ridge = max(1e-12, 1e-6 * float(np.trace(covariance)) / bands)
    inverse = np.linalg.pinv(
        covariance + ridge * np.eye(bands), hermitian=True
    )
    score = np.einsum("nb,nb->n", centered @ inverse, centered)
    return score.reshape(h, w)


def ace(cube: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Adaptive Cosine Estimator score map, shape (H, W), in [0, 1]."""
    h, w, xc, cinv, t = _prepare(cube, target)
    ct = cinv @ t
    num = (xc @ ct) ** 2
    tct = float(t @ ct) + 1e-12
    xcx = np.einsum("nb,nb->n", xc @ cinv, xc) + 1e-12
    return (num / (tct * xcx)).reshape(h, w)


def spectral_angle_mapper(cube: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Spectral Angle Mapper score map (cosine similarity), shape (H, W).

    Background-agnostic per-pixel baseline: the cosine of the spectral angle
    between each pixel and the target. Higher means more target-like. Simple
    and standard, but blind to background statistics (unlike the matched
    filter), so it is a useful lower rung on the leaderboard.
    """
    h, w, b = cube.shape
    x = cube.reshape(-1, b).astype(np.float64)
    t = target.astype(np.float64)
    xn = np.linalg.norm(x, axis=1) + 1e-12
    tn = float(np.linalg.norm(t)) + 1e-12
    return ((x @ t) / (xn * tn)).reshape(h, w)
