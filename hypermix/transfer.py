"""Physics-constrained transfer from laboratory spectra to sensor targets.

The functions in this module use only laboratory spectra, sensor metadata and
pre-specified atmospheric ranges. They do not inspect target labels or detector
scores. This makes the resulting signatures suitable for leakage-free target
transfer experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np

from .simulate import apply_atmosphere, apply_srf, atmospheric_transmittance

__all__ = [
    "TargetTransferLibrary",
    "resample_spectrum",
    "target_transfer",
    "target_transfer_library",
]


@dataclass(frozen=True)
class TargetTransferLibrary:
    """A reproducible family of plausible at-sensor target signatures."""

    signatures: np.ndarray
    wavelengths: np.ndarray
    parameters: tuple[dict[str, float], ...]

    def __post_init__(self) -> None:
        signatures = np.asarray(self.signatures, dtype=np.float64)
        wavelengths = np.asarray(self.wavelengths, dtype=np.float64)
        if signatures.ndim != 2:
            raise ValueError("signatures must have shape (n_targets, n_bands)")
        if wavelengths.ndim != 1 or signatures.shape[1] != wavelengths.size:
            raise ValueError("wavelengths must match the signature band count")
        if signatures.shape[0] != len(self.parameters):
            raise ValueError("parameters must describe every signature")
        object.__setattr__(self, "signatures", signatures)
        object.__setattr__(self, "wavelengths", wavelengths)


def _validated_grid(values: np.ndarray, name: str) -> np.ndarray:
    grid = np.asarray(values, dtype=np.float64)
    if (
        grid.ndim != 1
        or grid.size < 2
        or not np.all(np.isfinite(grid))
        or np.any(np.diff(grid) <= 0.0)
    ):
        raise ValueError(f"{name} must be a finite, strictly increasing 1-D array")
    return grid


def _validated_spectrum(
    spectrum: np.ndarray,
    wavelengths: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    grid = _validated_grid(wavelengths, "laboratory_wavelengths")
    values = np.asarray(spectrum, dtype=np.float64)
    if values.ndim != 1 or values.size != grid.size:
        raise ValueError("laboratory_spectrum must match laboratory_wavelengths")
    if not np.all(np.isfinite(values)):
        raise ValueError("laboratory_spectrum must be finite")
    return values, grid


def resample_spectrum(
    laboratory_spectrum: np.ndarray,
    laboratory_wavelengths: np.ndarray,
    sensor_wavelengths: np.ndarray,
) -> np.ndarray:
    """Linearly resample a laboratory spectrum without extrapolation."""
    values, source = _validated_spectrum(
        laboratory_spectrum, laboratory_wavelengths
    )
    sensor = _validated_grid(sensor_wavelengths, "sensor_wavelengths")
    tolerance = 1e-9
    if sensor[0] < source[0] - tolerance or sensor[-1] > source[-1] + tolerance:
        raise ValueError("sensor wavelengths must lie inside laboratory coverage")
    return np.interp(sensor, source, values)


def target_transfer(
    laboratory_spectrum: np.ndarray,
    laboratory_wavelengths: np.ndarray,
    sensor_wavelengths: np.ndarray,
    *,
    sensor_fwhm_nm: float = 0.0,
    atmosphere_strength: float = 0.0,
    path_radiance: float = 0.02,
    wavelength_shift_nm: float = 0.0,
    illumination_gain: float = 1.0,
) -> np.ndarray:
    """Transfer one laboratory spectrum into a declared sensor domain.

    A positive ``wavelength_shift_nm`` moves laboratory features toward longer
    wavelengths. The shift, sensor response, atmosphere and illumination are
    applied in that order. All parameters must come from metadata or a family
    fixed before evaluation; this function never consumes labels.
    """
    values, source = _validated_spectrum(
        laboratory_spectrum, laboratory_wavelengths
    )
    sensor = _validated_grid(sensor_wavelengths, "sensor_wavelengths")
    if not np.isfinite(sensor_fwhm_nm) or sensor_fwhm_nm < 0.0:
        raise ValueError("sensor_fwhm_nm must be finite and non-negative")
    if not np.isfinite(atmosphere_strength) or atmosphere_strength < 0.0:
        raise ValueError("atmosphere_strength must be finite and non-negative")
    if not np.isfinite(path_radiance) or path_radiance < 0.0:
        raise ValueError("path_radiance must be finite and non-negative")
    if not np.isfinite(wavelength_shift_nm):
        raise ValueError("wavelength_shift_nm must be finite")
    if not np.isfinite(illumination_gain) or illumination_gain <= 0.0:
        raise ValueError("illumination_gain must be finite and positive")

    shifted_coordinates = source - float(wavelength_shift_nm)
    shifted = np.interp(
        shifted_coordinates,
        source,
        values,
        left=float(values[0]),
        right=float(values[-1]),
    )
    if sensor_fwhm_nm > 0.0:
        observed = apply_srf(
            shifted,
            wavelengths=source,
            centers_nm=sensor,
            fwhm_nm=float(sensor_fwhm_nm),
        )
    else:
        observed = resample_spectrum(shifted, source, sensor)

    if atmosphere_strength > 0.0:
        transmittance = atmospheric_transmittance(
            wavelengths=sensor,
            strength=float(atmosphere_strength),
        )
        observed = apply_atmosphere(
            observed,
            transmittance,
            path_radiance=float(path_radiance),
        )
    return np.asarray(observed * float(illumination_gain), dtype=np.float64)


def target_transfer_library(
    laboratory_spectrum: np.ndarray,
    laboratory_wavelengths: np.ndarray,
    sensor_wavelengths: np.ndarray,
    *,
    sensor_fwhm_nm: float | tuple[float, ...] = 0.0,
    atmosphere_strengths: tuple[float, ...] = (0.0,),
    wavelength_shifts_nm: tuple[float, ...] = (0.0,),
    illumination_gains: tuple[float, ...] = (1.0,),
    path_radiance: float = 0.02,
) -> TargetTransferLibrary:
    """Build a Cartesian family of physically plausible target signatures."""
    fwhm_values = (
        (float(sensor_fwhm_nm),)
        if np.isscalar(sensor_fwhm_nm)
        else tuple(float(value) for value in sensor_fwhm_nm)
    )
    atmosphere_values = tuple(float(value) for value in atmosphere_strengths)
    shift_values = tuple(float(value) for value in wavelength_shifts_nm)
    gain_values = tuple(float(value) for value in illumination_gains)
    if not fwhm_values or not atmosphere_values or not shift_values or not gain_values:
        raise ValueError("transfer parameter families must not be empty")

    signatures = []
    parameters = []
    for fwhm, atmosphere, shift, gain in product(
        fwhm_values, atmosphere_values, shift_values, gain_values
    ):
        signatures.append(
            target_transfer(
                laboratory_spectrum,
                laboratory_wavelengths,
                sensor_wavelengths,
                sensor_fwhm_nm=fwhm,
                atmosphere_strength=atmosphere,
                path_radiance=path_radiance,
                wavelength_shift_nm=shift,
                illumination_gain=gain,
            )
        )
        parameters.append(
            {
                "sensor_fwhm_nm": fwhm,
                "atmosphere_strength": atmosphere,
                "path_radiance": float(path_radiance),
                "wavelength_shift_nm": shift,
                "illumination_gain": gain,
            }
        )
    return TargetTransferLibrary(
        signatures=np.stack(signatures),
        wavelengths=np.asarray(sensor_wavelengths, dtype=np.float64),
        parameters=tuple(parameters),
    )
