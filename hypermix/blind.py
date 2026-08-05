"""Leakage-resistant features for family-aware and target-blind detection.

The functions in this module deliberately separate the information regimes used
by the blind-target benchmark.  In particular, neither feature constructor
accepts the exact held-out target spectrum.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter

from .baselines import matched_subspace_detector, rx_detector, spectral_matched_filter

__all__ = [
    "BlindTrack",
    "BLIND_TRACKS",
    "blind_anomaly_features",
    "family_detection_features",
    "scale_target_library",
]


@dataclass(frozen=True)
class BlindTrack:
    """Information contract for one blind-target evaluation track."""

    name: str
    exact_target_available: bool
    target_family_available: bool
    description: str


BLIND_TRACKS = (
    BlindTrack(
        "oracle",
        exact_target_available=True,
        target_family_available=True,
        description="teto que conhece o espectro exato do alvo",
    ),
    BlindTrack(
        "family",
        exact_target_available=False,
        target_family_available=True,
        description="conhece apenas espectros relacionados, nunca o alvo retido",
    ),
    BlindTrack(
        "unknown",
        exact_target_available=False,
        target_family_available=False,
        description="não recebe alvo nem família espectral",
    ),
)


def _validate_cube(cube: np.ndarray) -> np.ndarray:
    arr = np.asarray(cube, dtype=np.float64)
    if arr.ndim != 3 or min(arr.shape) == 0:
        raise ValueError("cube must have shape (height, width, bands)")
    if not np.all(np.isfinite(arr)):
        raise ValueError("cube must contain only finite values")
    return arr


def _validate_library(signatures: np.ndarray, bands: int) -> np.ndarray:
    library = np.asarray(signatures, dtype=np.float64)
    if library.ndim == 1:
        library = library[None, :]
    if library.ndim != 2 or library.shape[0] == 0 or library.shape[1] != bands:
        raise ValueError("signatures must have shape (n_signatures, bands)")
    if not np.all(np.isfinite(library)):
        raise ValueError("signatures must contain only finite values")
    if np.any(np.linalg.norm(library, axis=1) <= 1e-12):
        raise ValueError("signatures must be non-zero")
    return library


def _standardize(features: np.ndarray) -> np.ndarray:
    mean = features.mean(axis=0, keepdims=True)
    scale = features.std(axis=0, keepdims=True)
    scale = np.where(scale > 1e-8, scale, 1.0)
    return ((features - mean) / scale).astype(np.float32)


def scale_target_library(signatures: np.ndarray, cube: np.ndarray) -> np.ndarray:
    """Scale unitless family spectra to the mean radiance of a scene."""

    arr = _validate_cube(cube)
    library = _validate_library(signatures, arr.shape[-1])
    scene_scale = max(float(np.mean(np.abs(arr))), 1e-8)
    signature_scale = np.max(np.abs(library), axis=1, keepdims=True)
    return library / signature_scale * scene_scale


def blind_anomaly_features(
    cube: np.ndarray,
    *,
    rx_score: np.ndarray | None = None,
) -> np.ndarray:
    """Build target-free anomaly features from the test scene itself.

    The output has one row per pixel.  It contains global RX, two spatial RX
    scales, a robust diagonal spectral distance, its smoothed version, and a
    local RX contrast.  No target spectrum is accepted by this API.
    """

    arr = _validate_cube(cube)
    height, width, bands = arr.shape
    if rx_score is None:
        rx = rx_detector(arr)
    else:
        rx = np.asarray(rx_score, dtype=np.float64)
        if rx.shape != (height, width) or not np.all(np.isfinite(rx)):
            raise ValueError("rx_score must be a finite map matching cube spatial shape")

    pixels = arr.reshape(-1, bands)
    median = np.median(pixels, axis=0)
    mad = np.median(np.abs(pixels - median), axis=0)
    robust_scale = np.maximum(1.4826 * mad, 1e-6)
    robust = np.mean(((pixels - median) / robust_scale) ** 2, axis=1).reshape(height, width)

    rx_15 = gaussian_filter(rx, sigma=1.5)
    rx_30 = gaussian_filter(rx, sigma=3.0)
    robust_15 = gaussian_filter(robust, sigma=1.5)
    local_contrast = rx - rx_30
    features = np.stack((rx, rx_15, rx_30, robust, robust_15, local_contrast), axis=-1)
    return _standardize(features.reshape(-1, features.shape[-1]))


def family_detection_features(
    cube: np.ndarray,
    family_signatures: np.ndarray,
    *,
    rank: int | None = None,
    rx_score: np.ndarray | None = None,
    centroid_score: np.ndarray | None = None,
    subspace_score: np.ndarray | None = None,
) -> np.ndarray:
    """Build features using only a related, non-held-out target family."""

    arr = _validate_cube(cube)
    height, width, bands = arr.shape
    library = _validate_library(family_signatures, bands)
    if rank is None:
        rank = min(3, library.shape[0])
    if not isinstance(rank, (int, np.integer)) or rank < 1 or rank > library.shape[0]:
        raise ValueError("rank must be between 1 and the number of signatures")

    centroid = library.mean(axis=0)
    if centroid_score is None:
        centroid_mf = spectral_matched_filter(arr, centroid)
    else:
        centroid_mf = np.asarray(centroid_score, dtype=np.float64)
        if centroid_mf.shape != (height, width) or not np.all(np.isfinite(centroid_mf)):
            raise ValueError(
                "centroid_score must be a finite map matching cube spatial shape"
            )
    if subspace_score is None:
        subspace = matched_subspace_detector(arr, library, rank=int(rank))
    else:
        subspace = np.asarray(subspace_score, dtype=np.float64)
        if subspace.shape != (height, width) or not np.all(np.isfinite(subspace)):
            raise ValueError(
                "subspace_score must be a finite map matching cube spatial shape"
            )
    if rx_score is None:
        rx = rx_detector(arr)
    else:
        rx = np.asarray(rx_score, dtype=np.float64)
        if rx.shape != (height, width) or not np.all(np.isfinite(rx)):
            raise ValueError("rx_score must be a finite map matching cube spatial shape")

    features = np.stack(
        (
            centroid_mf,
            gaussian_filter(centroid_mf, sigma=1.5),
            subspace,
            gaussian_filter(subspace, sigma=1.5),
            rx,
            gaussian_filter(rx, sigma=1.5),
        ),
        axis=-1,
    )
    return _standardize(features.reshape(-1, features.shape[-1]))
