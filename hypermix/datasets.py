"""Real hyperspectral data: loaders and the implanted-target benchmark.

The honest bridge from synthetic to real. Instead of a fully synthetic
background, we take a real hyperspectral cube (real spectral clutter and
sensor statistics) and *implant* a known target signature at controlled,
often sub-pixel, abundance. This is the standard methodology in the
target-detection literature and gives us real backgrounds with exact
ground truth for the target we are trying to find.

Loaders are intentionally light: `.mat` via SciPy, ENVI via the optional
`spectral` package.
"""

from __future__ import annotations

import numpy as np

from .simulate import _target_noise_std

__all__ = ["load_mat_cube", "load_envi_cube", "synthetic_target", "implant_target"]


def _normalize(cube: np.ndarray) -> np.ndarray:
    cube = np.asarray(cube, dtype=np.float64)
    cube = cube - cube.min()
    peak = cube.max() or 1.0
    return (cube / peak).astype(np.float32)


def load_mat_cube(path: str, key: str | None = None) -> np.ndarray:
    """Load a 3D (H, W, B) hyperspectral cube from a MATLAB .mat file."""
    from scipy.io import loadmat

    data = loadmat(path)
    if key is None:
        cands = [k for k in data
                 if not k.startswith("__") and getattr(data[k], "ndim", 0) == 3]
        if not cands:
            raise ValueError(f"No 3D array found in {path}")
        key = cands[0]
    return _normalize(data[key])


def load_envi_cube(path: str) -> np.ndarray:
    """Load an ENVI cube (.hdr/.img) via the optional `spectral` package."""
    import spectral  # noqa: F401

    return _normalize(spectral.open_image(path).load())


def synthetic_target(n_bands: int, center_frac: float = 0.62,
                     width_frac: float = 0.025) -> np.ndarray:
    """A narrow, spectrally localized target feature (unit peak).

    Placeholder for a measured engineered-reporter spectrum; a sharp,
    localized feature is what makes a reporter stand out and what low SNR
    threatens. Drop in a real spectrum here without touching the API.
    """
    idx = np.arange(n_bands)
    center = center_frac * (n_bands - 1)
    width = max(width_frac * n_bands, 1.0)
    feat = np.exp(-(((idx - center) / width) ** 2))
    return feat / (feat.max() or 1.0)   # unit peak


def implant_target(
    cube: np.ndarray,
    rng: np.random.Generator,
    target: np.ndarray | None = None,
    n_blobs: int = 6,
    max_abundance: float = 0.15,
    snr_db: float = 10.0,
    detection_threshold: float = 0.02,
    mixing: str = "linear",
    nonlinearity: float = 0.5,
):
    """Implant a known target into a real background cube.

    Returns (scene, detection_gt, abundance_gt, target_used). The target is
    scaled to the background's mean magnitude so detection depends on
    spectral *shape*, not brightness (the honest, hard case). ``snr_db`` is
    target-relative: RMS of the target contribution over positive target pixels
    divided by additive-noise RMS. It is not scene-versus-noise SNR.

    ``mixing`` is "linear" (convex combination) or "bilinear", which uses the
    two-endmember generalized bilinear model with interaction coefficient
    ``nonlinearity``. The latter breaks the matched filter's linear-additive
    assumption and is intended for controlled sensitivity analysis.
    """
    h, w, b = cube.shape
    if mixing not in {"linear", "bilinear"}:
        raise ValueError(f"unknown mixing: {mixing!r}")
    if not 0.0 <= nonlinearity <= 1.0:
        raise ValueError("nonlinearity must lie in [0, 1]")
    if target is None:
        target = synthetic_target(b)
    tgt = np.asarray(target, dtype=np.float64)
    tgt = tgt / (tgt.max() or 1.0) * float(cube.reshape(-1, b).mean())

    yy, xx = np.mgrid[0:h, 0:w]
    ab = np.zeros((h, w))
    for _ in range(n_blobs):
        cy = rng.uniform(0, h)
        cx = rng.uniform(0, w)
        rad = rng.uniform(min(h, w) * 0.03, min(h, w) * 0.07)
        amp = rng.uniform(0.5, 1.0) * max_abundance
        ab += amp * np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * rad ** 2)))
    ab = np.clip(ab, 0.0, max_abundance)

    target_signal = ab[..., None] * (tgt[None, None, :] - cube)
    if mixing == "bilinear":
        interaction = (nonlinearity * (ab * (1.0 - ab))[..., None]
                       * cube * tgt[None, None, :])
        target_signal = target_signal + interaction
    scene = cube + target_signal

    gt = ab > detection_threshold
    noise_std = _target_noise_std(target_signal, gt, snr_db)
    scene = scene + rng.normal(0.0, noise_std, size=scene.shape)

    return (scene.astype(np.float32), gt,
            ab.astype(np.float32), tgt.astype(np.float32))
