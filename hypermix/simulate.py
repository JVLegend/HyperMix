"""Physics-based hyperspectral scene simulator for remote biosignature detection.

The forward model mirrors the HyperMix proposal:

    cube = illumination * blur( (1 - r) * sum_k b_k * E_k  +  r * R ) + noise

where E_k are natural background endmembers (soil, vegetation, dry
vegetation, water), b_k are per-pixel background fractions that sum to 1,
R is the engineered reporter signature, r is the reporter abundance, the
blur is the instrument point-spread function, illumination is a smooth
multiplicative gain, and noise is set to hit a target SNR.

Everything is deterministic given ``seed`` and depends only on NumPy, so a
scene can be reproduced anywhere with no external data. Real reporter
spectra can later replace the synthetic signature without touching the API.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .spectra import measured_endmember_library, measured_reporter_library

__all__ = [
    "SceneResult",
    "endmember_library",
    "reporter_signature",
    "reporter_library",
    "gaussian_srf",
    "atmospheric_transmittance",
    "apply_atmosphere",
    "apply_srf",
    "simulate_scene",
    "false_color",
]


# --------------------------------------------------------------------------- #
# Spectra
# --------------------------------------------------------------------------- #
def _wavelengths(n_bands: int, lo: float = 400.0, hi: float = 1000.0) -> np.ndarray:
    return np.linspace(lo, hi, n_bands)


def endmember_library(n_bands: int = 60) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return (wavelengths, {name: reflectance}) for natural backgrounds.

    Shapes are stylised but spectrally distinct, standing in for soil,
    vegetation, dry vegetation and water until measured libraries (USGS,
    ECOSTRESS) are wired in.
    """
    wl = _wavelengths(n_bands)
    t = (wl - wl[0]) / (wl[-1] - wl[0])  # normalised 0..1

    vegetation = (
        0.04
        + 0.16 * np.exp(-(((t - 0.25) / 0.06) ** 2))   # green bump ~550 nm
        + 0.55 / (1.0 + np.exp(-(t - 0.52) / 0.03))     # red edge -> NIR plateau
    )
    soil = 0.15 + 0.45 * t ** 0.8
    dry_veg = 0.10 + 0.38 * t + 0.06 * np.exp(-(((t - 0.28) / 0.08) ** 2))
    water = 0.25 * np.exp(-3.0 * t) + 0.02

    lib = {
        "vegetation": np.clip(vegetation, 0.0, 1.0),
        "soil": np.clip(soil, 0.0, 1.0),
        "dry_vegetation": np.clip(dry_veg, 0.0, 1.0),
        "water": np.clip(water, 0.0, 1.0),
    }
    return wl, lib


def reporter_signature(
    n_bands: int = 60,
    center_nm: float = 790.0,
    width_nm: float = 12.0,
    depth: float = 0.35,
    baseline: float = 0.45,
) -> np.ndarray:
    """Synthetic engineered-reporter reflectance: a sharp, localized absorption.

    A narrow spectral feature is exactly what makes an engineered pigment
    detectable against smooth natural backgrounds, and exactly what low SNR
    and blur threaten to wash out.
    """
    wl = _wavelengths(n_bands)
    dip = depth * np.exp(-(((wl - center_nm) / width_nm) ** 2))
    return np.clip(baseline - dip, 0.0, 1.0)


# Absorption features (approximate peak positions, nm) of the two reporters
# selected by Chemla et al., Nature Biotechnology 2026. Modeled from
# published absorption maxima; replace with the measured spectra when the
# supplementary data is available. Each entry: list of (center_nm, width_nm,
# depth) absorption bands within the 400-1000 nm window.
_KNOWN_REPORTERS = {
    # bacteriochlorophyll a: Qx ~600 nm, Qy ~770 nm (Soret ~360 nm is out of range)
    "bacteriochlorophyll_a": [(600.0, 20.0, 0.18), (770.0, 16.0, 0.38)],
    # biliverdin IXalpha: broad red band ~670 nm (Soret ~377 nm mostly out of range)
    "biliverdin_ixalpha": [(670.0, 45.0, 0.34), (400.0, 25.0, 0.15)],
}


def reporter_library(n_bands: int = 60, baseline: float = 0.45) -> dict[str, np.ndarray]:
    """Reflectance signatures for the reporters used by Chemla et al. (2026).

    Grounded on the reported absorption maxima of biliverdin IXalpha and
    bacteriochlorophyll a (approximate, pending measured spectra). Useful as
    realistic detection targets instead of an arbitrary synthetic feature.
    """
    wl = _wavelengths(n_bands)
    lib = {}
    for name, bands in _KNOWN_REPORTERS.items():
        refl = np.full(n_bands, baseline, dtype=np.float64)
        for center, width, depth in bands:
            refl -= depth * np.exp(-(((wl - center) / width) ** 2))
        lib[name] = np.clip(refl, 0.0, 1.0)
    return lib


# --------------------------------------------------------------------------- #
# Sensor and atmosphere (Phase B realism, opt-in)
# --------------------------------------------------------------------------- #
# Approximate atmospheric absorption bands within 400-1000 nm: O2 at 760 nm and
# water vapour near 720, 820 and 940 nm. Centres/depths are illustrative, not a
# radiative-transfer model; the point is spectrally structured transmittance.
_ATMOSPHERE_BANDS = [(720.0, 12.0, 0.15), (760.0, 6.0, 0.35),
                     (820.0, 15.0, 0.20), (940.0, 25.0, 0.55)]


def atmospheric_transmittance(
    n_bands: int = 60,
    *,
    wavelengths: np.ndarray | None = None,
    strength: float = 1.0,
) -> np.ndarray:
    """Simple structured atmospheric transmittance for 400-1000 nm.

    This is a sensitivity model, not line-by-line radiative transfer. A value
    of zero for ``strength`` gives a transparent atmosphere; one gives the
    documented default O2 and water-vapour bands.
    """
    if strength < 0:
        raise ValueError("atmospheric strength must be non-negative")
    wl = _wavelengths(n_bands) if wavelengths is None else np.asarray(wavelengths)
    if wl.ndim != 1:
        raise ValueError("wavelengths must be one-dimensional")
    tau = np.ones(wl.size)
    for center, width, depth in _ATMOSPHERE_BANDS:
        tau -= strength * depth * np.exp(-(((wl - center) / width) ** 2))
    return np.clip(tau, 0.05, 1.0)


def apply_atmosphere(
    spectra: np.ndarray,
    transmittance: np.ndarray,
    path_radiance: float = 0.02,
) -> np.ndarray:
    """Apply a one-layer atmosphere with a spectrally flat path term."""
    values = np.asarray(spectra)
    tau = np.asarray(transmittance, dtype=np.float64)
    if tau.ndim != 1 or tau.size != values.shape[-1]:
        raise ValueError("transmittance must match the last spectral dimension")
    if path_radiance < 0:
        raise ValueError("path_radiance must be non-negative")
    return values * tau + path_radiance * (1.0 - tau)


def gaussian_srf(
    wavelengths: np.ndarray,
    centers_nm: np.ndarray,
    fwhm_nm: float | np.ndarray,
) -> np.ndarray:
    """Return normalized Gaussian spectral-response weights.

    Rows correspond to output sensor bands and columns to input wavelengths.
    AVIRIS response functions are commonly represented from measured centers
    and FWHM values with this Gaussian approximation.
    """
    wl = np.asarray(wavelengths, dtype=np.float64)
    centers = np.atleast_1d(np.asarray(centers_nm, dtype=np.float64))
    fwhm = np.broadcast_to(np.asarray(fwhm_nm, dtype=np.float64), centers.shape)
    if wl.ndim != 1 or centers.ndim != 1 or np.any(np.diff(wl) <= 0):
        raise ValueError("wavelengths and centers must be one-dimensional")
    if np.any(fwhm <= 0):
        raise ValueError("FWHM values must be positive")
    sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    response = np.exp(-0.5 * ((wl[None, :] - centers[:, None]) / sigma[:, None]) ** 2)
    normalizer = response.sum(axis=1, keepdims=True)
    if np.any(normalizer == 0):
        raise ValueError("sensor response does not overlap the input wavelengths")
    return response / normalizer


def apply_srf(
    spectra: np.ndarray,
    fwhm_bands: float = 1.5,
    *,
    wavelengths: np.ndarray | None = None,
    centers_nm: np.ndarray | None = None,
    fwhm_nm: float | np.ndarray | None = None,
) -> np.ndarray:
    """Apply a Gaussian sensor spectral response along the last axis.

    For a physical response, pass input ``wavelengths``, output ``centers_nm``
    and ``fwhm_nm``. The older ``fwhm_bands`` interface remains available for
    same-grid smoothing and preserves the Phase A API.
    """
    values = np.asarray(spectra)
    if wavelengths is not None or centers_nm is not None or fwhm_nm is not None:
        if wavelengths is None or fwhm_nm is None:
            raise ValueError("physical SRF requires wavelengths and fwhm_nm")
        wl = np.asarray(wavelengths, dtype=np.float64)
        centers = wl if centers_nm is None else np.asarray(centers_nm, dtype=np.float64)
        if values.shape[-1] != wl.size:
            raise ValueError("input wavelengths must match the last dimension")
        response = gaussian_srf(wl, centers, fwhm_nm)
        return np.tensordot(values, response, axes=([-1], [1]))

    if fwhm_bands <= 0:
        return values
    sigma = fwhm_bands / 2.3548
    radius = max(1, int(np.ceil(3 * sigma)))
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= kernel.sum()
    pad = [(0, 0)] * (values.ndim - 1) + [(radius, radius)]
    padded = np.pad(values, pad, mode="edge")
    return np.apply_along_axis(
        lambda m: np.convolve(m, kernel, mode="valid"), -1, padded)


# --------------------------------------------------------------------------- #
# Spatial helpers (NumPy only)
# --------------------------------------------------------------------------- #
def _smooth_field(h: int, w: int, scale: float, rng: np.random.Generator) -> np.ndarray:
    """A smooth random field in [0, 1] via low-pass filtered white noise."""
    noise = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    lp = np.exp(-0.5 * (fy ** 2 + fx ** 2) * (scale ** 2))
    field = np.real(np.fft.ifft2(np.fft.fft2(noise) * lp))
    field -= field.min()
    denom = field.max() or 1.0
    return field / denom


def _gaussian_blur(cube: np.ndarray, sigma: float) -> np.ndarray:
    """Spatial Gaussian PSF applied band-by-band (FFT domain)."""
    if sigma <= 0:
        return cube
    h, w, _ = cube.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    otf = np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * (fy ** 2 + fx ** 2))
    out = np.empty_like(cube)
    for b in range(cube.shape[2]):
        out[:, :, b] = np.real(np.fft.ifft2(np.fft.fft2(cube[:, :, b]) * otf))
    return out


# --------------------------------------------------------------------------- #
# Scene
# --------------------------------------------------------------------------- #
@dataclass
class SceneResult:
    """One simulated hyperspectral scene with full ground truth."""

    cube: np.ndarray              # (H, W, B) reflectance-like radiance
    detection_gt: np.ndarray      # (H, W) bool, reporter present
    abundance_gt: np.ndarray      # (H, W) reporter fractional abundance
    wavelengths: np.ndarray       # (B,)
    reporter: np.ndarray          # (B,) reporter signature (target vector)
    endmembers: dict[str, np.ndarray]
    snr_db: float                 # target-contribution SNR, retained for API compatibility

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.cube.shape


def simulate_scene(
    height: int = 96,
    width: int = 96,
    n_bands: int = 60,
    snr_db: float = 10.0,
    psf_sigma: float = 1.2,
    n_reporter_blobs: int = 5,
    reporter_max_abundance: float = 0.30,
    detection_threshold: float = 0.03,
    atmosphere: bool = False,
    srf_fwhm: float = 0.0,
    spectral_source: str = "stylized",
    reporter_name: str = "bacteriochlorophyll_a",
    sensor_fwhm_nm: float = 0.0,
    atmosphere_strength: float = 1.0,
    path_radiance: float = 0.02,
    mixing: str = "linear",
    nonlinearity: float = 0.5,
    seed: int = 0,
) -> SceneResult:
    """Simulate a remote hyperspectral scene with a faint engineered reporter.

    Parameters mirror the physical knobs the detector must be robust to:
    ``snr_db`` (target-contribution SNR for cheap/distant sensors),
    ``psf_sigma`` (optical blur), ``reporter_max_abundance`` (how faint the
    target is). Target SNR is the RMS reporter contribution over positive
    target pixels divided by the additive-noise RMS.
    """
    if spectral_source not in {"stylized", "measured"}:
        raise ValueError("spectral_source must be 'stylized' or 'measured'")
    if mixing not in {"linear", "bilinear"}:
        raise ValueError("mixing must be 'linear' or 'bilinear'")
    if not 0.0 <= nonlinearity <= 1.0:
        raise ValueError("nonlinearity must lie in [0, 1]")
    if srf_fwhm > 0 and sensor_fwhm_nm > 0:
        raise ValueError("choose srf_fwhm or sensor_fwhm_nm, not both")

    rng = np.random.default_rng(seed)
    wl = _wavelengths(n_bands)
    if sensor_fwhm_nm > 0:
        native_wl = _wavelengths(601)
        if spectral_source == "measured":
            _, native_lib = measured_endmember_library(wavelengths=native_wl)
            _, reporters = measured_reporter_library(wavelengths=native_wl)
            if reporter_name not in reporters:
                raise ValueError(f"unknown measured reporter: {reporter_name!r}")
            native_reporter = reporters[reporter_name]
        else:
            _, native_lib = endmember_library(601)
            native_reporter = reporter_signature(601)
        names = list(native_lib)
        native_endmembers = np.stack([native_lib[name] for name in names], axis=0)
        E = apply_srf(
            native_endmembers,
            wavelengths=native_wl,
            centers_nm=wl,
            fwhm_nm=sensor_fwhm_nm,
        )
        R = apply_srf(
            native_reporter,
            wavelengths=native_wl,
            centers_nm=wl,
            fwhm_nm=sensor_fwhm_nm,
        )
    elif spectral_source == "measured":
        _, lib = measured_endmember_library(n_bands)
        _, reporters = measured_reporter_library(n_bands)
        if reporter_name not in reporters:
            raise ValueError(f"unknown measured reporter: {reporter_name!r}")
        names = list(lib)
        E = np.stack([lib[name] for name in names], axis=0)
        R = reporters[reporter_name]
    else:
        _, lib = endmember_library(n_bands)
        names = list(lib)
        E = np.stack([lib[name] for name in names], axis=0)
        R = reporter_signature(n_bands)


    # Background fractions: smooth fields -> softmax so they sum to 1 per pixel.
    fields = np.stack(
        [_smooth_field(height, width, scale=max(height, width) / 6.0, rng=rng)
         for _ in names],
        axis=0,
    )  # (K, H, W)
    fields *= rng.uniform(0.6, 1.4, size=(len(names), 1, 1))
    frac = np.exp(fields - fields.max(axis=0, keepdims=True))
    frac /= frac.sum(axis=0, keepdims=True)          # (K, H, W), sums to 1

    # Reporter abundance: a few Gaussian blobs.
    yy, xx = np.mgrid[0:height, 0:width]
    reporter_ab = np.zeros((height, width))
    for _ in range(n_reporter_blobs):
        cy = rng.uniform(0, height)
        cx = rng.uniform(0, width)
        rad = rng.uniform(min(height, width) * 0.04, min(height, width) * 0.10)
        amp = rng.uniform(0.4, 1.0) * reporter_max_abundance
        reporter_ab += amp * np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * rad ** 2)))
    reporter_ab = np.clip(reporter_ab, 0.0, reporter_max_abundance)

    # Optional Phase-B realism: finite spectral resolution then atmosphere,
    # applied to both endmembers and reporter so the target vector stays
    # consistent with what a detector would see.
    if srf_fwhm > 0:
        E = apply_srf(E, srf_fwhm)
        R = apply_srf(R, srf_fwhm)
    if atmosphere:
        tau = atmospheric_transmittance(
            n_bands, wavelengths=wl, strength=atmosphere_strength
        )
        E = apply_atmosphere(E, tau, path_radiance=path_radiance)
        R = apply_atmosphere(R, tau, path_radiance=path_radiance)

    # Linear mixing: convex combination of background + reporter.
    bg = np.einsum("khw,kb->hwb", frac, E)           # (H, W, B)

    # Smooth illumination gain and optical blur. Keeping background and target
    # contribution separate makes the requested SNR scientifically explicit.
    illum = 0.75 + 0.5 * _smooth_field(height, width, scale=max(height, width) / 4.0, rng=rng)
    bg_observed = _gaussian_blur(bg * illum[..., None], psf_sigma)
    target_signal = reporter_ab[..., None] * (R[None, None, :] - bg)
    if mixing == "bilinear":
        target_signal += (
            nonlinearity
            * (reporter_ab * (1.0 - reporter_ab))[..., None]
            * bg
            * R[None, None, :]
        )
    target_signal = _gaussian_blur(target_signal * illum[..., None], psf_sigma)
    cube = bg_observed + target_signal

    # Additive sensor noise scaled to target-contribution SNR, not scene SNR.
    detection_gt = reporter_ab > detection_threshold
    noise_std = _target_noise_std(target_signal, detection_gt, snr_db)
    cube = cube + rng.normal(0.0, noise_std, size=cube.shape)

    return SceneResult(
        cube=cube.astype(np.float32),
        detection_gt=detection_gt,
        abundance_gt=reporter_ab.astype(np.float32),
        wavelengths=wl,
        reporter=R.astype(np.float32),
        endmembers={name: E[index].astype(np.float32) for index, name in enumerate(names)},
        snr_db=snr_db,
    )


def _target_noise_std(
    target_signal: np.ndarray,
    target_mask: np.ndarray,
    target_snr_db: float,
) -> float:
    """Noise standard deviation for a requested target-contribution SNR."""
    if not np.isfinite(target_snr_db) and not np.isposinf(target_snr_db):
        raise ValueError("target SNR must be finite or positive infinity")
    if not np.any(target_mask):
        return 0.0
    target_rms = float(np.sqrt(np.mean(np.asarray(target_signal)[target_mask] ** 2)))
    if np.isposinf(target_snr_db):
        return 0.0
    return target_rms / (10.0 ** (target_snr_db / 20.0))


def false_color(cube: np.ndarray) -> np.ndarray:
    """Cheap RGB preview: pick three bands and stretch to [0, 1]."""
    b = cube.shape[2]
    idx = [int(b * 0.7), int(b * 0.45), int(b * 0.2)]  # NIR, red, blue-ish
    rgb = cube[:, :, idx].astype(np.float32)
    lo = np.percentile(rgb, 2)
    hi = np.percentile(rgb, 98)
    return np.clip((rgb - lo) / (hi - lo + 1e-9), 0.0, 1.0)
