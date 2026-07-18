"""Measured reference spectra with explicit provenance.

Natural endmembers come from USGS Spectral Library Version 7. Reporter
curves are inferred pellet absorbance arrays published with the official
bioHSI code for Chemla et al. They are measurements, but the conversion from
absorbance to a reflectance-like target remains a documented model choice.
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np

__all__ = [
    "measured_endmember_library",
    "measured_reporter_absorbance_library",
    "measured_reporter_library",
]


_ENDMEMBER_COLUMNS = {
    "vegetation": "usgs_aspen_green_reflectance",
    "dry_vegetation": "usgs_dry_grass_reflectance",
    "soil": "usgs_sand_reflectance",
    "water": "usgs_seawater_reflectance",
}
_REPORTER_COLUMNS = {
    "bacteriochlorophyll_a_yf10": "chemla_bchl_a_yf10_absorbance",
    "smurfp_biliverdin_ecoli": "chemla_smurfp_biliverdin_ecoli_absorbance",
    "smurfp_biliverdin_pputida": "chemla_smurfp_biliverdin_pputida_absorbance",
}


def _reference_table() -> np.ndarray:
    resource = files("hypermix").joinpath("data/reference_spectra.csv")
    with resource.open("rb") as handle:
        return np.genfromtxt(handle, delimiter=",", names=True, dtype=np.float64)


def _output_grid(n_bands: int, wavelengths: np.ndarray | None) -> np.ndarray:
    if wavelengths is None:
        if n_bands < 2:
            raise ValueError("n_bands must be at least 2")
        return np.linspace(400.0, 1000.0, n_bands)
    grid = np.asarray(wavelengths, dtype=np.float64)
    if grid.ndim != 1 or grid.size < 2 or np.any(np.diff(grid) <= 0):
        raise ValueError("wavelengths must be a strictly increasing 1-D array")
    if grid[0] < 400.0 or grid[-1] > 1000.0:
        raise ValueError("measured spectra cover 400-1000 nm")
    return grid


def measured_endmember_library(
    n_bands: int = 60,
    *,
    wavelengths: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return measured USGS surface-reflectance endmembers.

    The four selected samples are green aspen, golden dry grass, sand and
    open-ocean seawater. Spectra are linearly interpolated from their native
    USGS sampling grid and clipped only to the physical reflectance interval.
    """
    table = _reference_table()
    grid = _output_grid(n_bands, wavelengths)
    native = table["wavelength_nm"]
    library = {
        name: np.clip(np.interp(grid, native, table[column]), 0.0, 1.0)
        for name, column in _ENDMEMBER_COLUMNS.items()
    }
    return grid, library


def measured_reporter_absorbance_library(
    n_bands: int = 60,
    *,
    wavelengths: np.ndarray | None = None,
    baseline_correct: bool = True,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return the measured reporter pellet absorbance curves from bioHSI.

    With ``baseline_correct=True``, each spectrum's fifth percentile is
    subtracted and negative residuals are clipped to zero. Values remain in
    absorbance units and are not peak-normalized.
    """
    table = _reference_table()
    grid = _output_grid(n_bands, wavelengths)
    native = table["wavelength_nm"]
    library = {}
    for name, column in _REPORTER_COLUMNS.items():
        curve = np.interp(grid, native, table[column])
        if baseline_correct:
            curve = np.clip(curve - np.percentile(curve, 5), 0.0, None)
        library[name] = curve
    return grid, library


def measured_reporter_library(
    n_bands: int = 60,
    *,
    wavelengths: np.ndarray | None = None,
    baseline: float = 0.45,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Convert measured absorbance shapes to reflectance-like targets.

    The bioHSI arrays are inferred pellet absorbance, not absolute surface
    reflectance. HyperMix applies the Beer-Lambert transmittance relation
    ``baseline * 10**(-absorbance)``. This preserves the measured band shape
    and magnitude while making the modeling boundary explicit.

    The canonical biliverdin curve is the mean of the E. coli and P. putida
    measurements. Host-specific curves are also returned for sensitivity
    analysis.
    """
    if not 0.0 < baseline <= 1.0:
        raise ValueError("baseline must lie in (0, 1]")
    grid, absorbance = measured_reporter_absorbance_library(
        n_bands, wavelengths=wavelengths, baseline_correct=True
    )
    bchl = absorbance["bacteriochlorophyll_a_yf10"]
    ecoli = absorbance["smurfp_biliverdin_ecoli"]
    pputida = absorbance["smurfp_biliverdin_pputida"]
    canonical = {
        "bacteriochlorophyll_a": baseline * np.power(10.0, -bchl),
        "biliverdin_ixalpha": baseline * np.power(10.0, -0.5 * (ecoli + pputida)),
        "biliverdin_ixalpha_ecoli": baseline * np.power(10.0, -ecoli),
        "biliverdin_ixalpha_pputida": baseline * np.power(10.0, -pputida),
    }
    return grid, canonical
