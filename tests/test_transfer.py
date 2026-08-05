import numpy as np
import pytest

from hypermix import (
    measured_reporter_library,
    resample_spectrum,
    simulate_scene,
    target_transfer,
    target_transfer_library,
)


def test_resample_spectrum_preserves_linear_curve():
    source = np.linspace(400.0, 1000.0, 601)
    spectrum = 0.1 + source / 2000.0
    sensor = np.linspace(400.0, 1000.0, 61)

    observed = resample_spectrum(spectrum, source, sensor)

    assert np.allclose(observed, 0.1 + sensor / 2000.0)


def test_transfer_matches_simulator_target_for_declared_physics():
    native_wavelengths, reporters = measured_reporter_library(601)
    sensor_wavelengths = np.linspace(400.0, 1000.0, 61)
    transferred = target_transfer(
        reporters["bacteriochlorophyll_a"],
        native_wavelengths,
        sensor_wavelengths,
        sensor_fwhm_nm=10.0,
        atmosphere_strength=1.2,
        path_radiance=0.02,
    )
    scene = simulate_scene(
        height=20,
        width=20,
        n_bands=61,
        snr_db=10.0,
        spectral_source="measured",
        reporter_name="bacteriochlorophyll_a",
        sensor_fwhm_nm=10.0,
        atmosphere=True,
        atmosphere_strength=1.2,
        path_radiance=0.02,
        seed=4,
    )

    assert np.allclose(transferred, scene.reporter, atol=1e-7)


def test_positive_shift_moves_absorption_feature_redward():
    wavelengths = np.linspace(400.0, 1000.0, 601)
    spectrum = 0.5 - 0.3 * np.exp(-((wavelengths - 700.0) / 5.0) ** 2)
    shifted = target_transfer(
        spectrum,
        wavelengths,
        wavelengths,
        wavelength_shift_nm=8.0,
    )

    assert wavelengths[np.argmin(shifted)] == pytest.approx(708.0, abs=1.0)


def test_transfer_library_is_deterministic_and_tracks_parameters():
    wavelengths, reporters = measured_reporter_library(61)
    kwargs = dict(
        sensor_fwhm_nm=(8.0, 12.0),
        atmosphere_strengths=(0.7, 1.0, 1.3),
        wavelength_shifts_nm=(-2.0, 0.0, 2.0),
    )
    first = target_transfer_library(
        reporters["bacteriochlorophyll_a"], wavelengths, wavelengths, **kwargs
    )
    second = target_transfer_library(
        reporters["bacteriochlorophyll_a"], wavelengths, wavelengths, **kwargs
    )

    assert first.signatures.shape == (18, 61)
    assert len(first.parameters) == 18
    assert np.array_equal(first.signatures, second.signatures)
    assert first.parameters == second.parameters


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sensor_fwhm_nm": -1.0},
        {"atmosphere_strength": -0.1},
        {"path_radiance": -0.1},
        {"illumination_gain": 0.0},
    ],
)
def test_target_transfer_rejects_nonphysical_parameters(kwargs):
    wavelengths = np.linspace(400.0, 1000.0, 61)
    with pytest.raises(ValueError):
        target_transfer(
            np.full(61, 0.4), wavelengths, wavelengths, **kwargs
        )


def test_resample_rejects_extrapolation():
    wavelengths = np.linspace(450.0, 900.0, 46)
    with pytest.raises(ValueError, match="inside laboratory coverage"):
        resample_spectrum(
            np.full(wavelengths.size, 0.4),
            wavelengths,
            np.linspace(400.0, 1000.0, 61),
        )
