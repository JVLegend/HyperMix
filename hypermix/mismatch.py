"""Controlled spectral mismatch utilities for target-detection experiments."""

from __future__ import annotations

import numpy as np

__all__ = ["shift_spectrum"]


def shift_spectrum(target: np.ndarray, shift_fraction: float) -> np.ndarray:
    """Shift a target signature along its normalized band-index axis.

    ``shift_fraction`` is a fraction of the full band-index range. For example,
    0.01 moves the signature by about two bands in a 200-band cube. Edge values
    are extended rather than wrapped, so no feature reappears at the other end.
    """
    target = np.asarray(target, dtype=np.float64)
    if target.ndim != 1 or target.size < 2:
        raise ValueError("target must be a one-dimensional spectrum")
    if not np.isfinite(shift_fraction) or abs(shift_fraction) >= 1.0:
        raise ValueError("shift_fraction must be finite and have magnitude < 1")
    if shift_fraction == 0:
        return target.copy()

    axis = np.linspace(0.0, 1.0, target.size)
    shifted = np.interp(
        axis - float(shift_fraction),
        axis,
        target,
        left=float(target[0]),
        right=float(target[-1]),
    )
    return shifted
