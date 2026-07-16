"""Classical detection baselines: the floor HyperMix must beat.

These are the standard tools the field uses today. The physics-informed,
self-supervised detector (Milestone 2) is measured against them.
"""

from __future__ import annotations

import numpy as np

__all__ = ["spectral_matched_filter", "ace"]


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


def ace(cube: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Adaptive Cosine Estimator score map, shape (H, W), in [0, 1]."""
    h, w, xc, cinv, t = _prepare(cube, target)
    ct = cinv @ t
    num = (xc @ ct) ** 2
    tct = float(t @ ct) + 1e-12
    xcx = np.einsum("nb,nb->n", xc @ cinv, xc) + 1e-12
    return (num / (tct * xcx)).reshape(h, w)
