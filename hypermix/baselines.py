"""Classical detection baselines: the floor HyperMix must beat.

These are the standard tools the field uses today. The physics-informed,
self-supervised detector (Milestone 2) is measured against them.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "spectral_matched_filter",
    "smoothed_matched_filter",
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
