"""Export the HyperMix open spectral library to ./dataset (CSV + NPZ).

    python scripts/export_dataset.py

Writes a small, citable open dataset: measured USGS background endmembers,
measured bioHSI reporter absorbance, and documented reflectance-like reporter
surrogates on a canonical 400-1000 nm grid, plus a data card.
"""

from __future__ import annotations

import os

import numpy as np

from hypermix import (
    measured_endmember_library,
    measured_reporter_absorbance_library,
    measured_reporter_library,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "dataset")
N_BANDS = 61  # 400-1000 nm at 10 nm steps


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    wl, endmembers = measured_endmember_library(N_BANDS)
    _, all_reporters = measured_reporter_library(wavelengths=wl)
    reporters = {
        "bacteriochlorophyll_a_reflectance_surrogate": (
            all_reporters["bacteriochlorophyll_a"]
        ),
        "biliverdin_ixalpha_reflectance_surrogate": (
            all_reporters["biliverdin_ixalpha"]
        ),
    }
    _, absorbance = measured_reporter_absorbance_library(
        wavelengths=wl, baseline_correct=False
    )

    columns = {"wavelength_nm": wl}
    columns.update(endmembers)
    columns.update(reporters)
    columns.update(absorbance)
    names = list(columns)

    # CSV
    csv_path = os.path.join(OUT, "hypermix_spectral_library.csv")
    rows = np.column_stack([columns[n] for n in names])
    header = ",".join(names)
    np.savetxt(csv_path, rows, delimiter=",", header=header, comments="",
               fmt="%.6f")

    # NPZ
    npz_path = os.path.join(OUT, "hypermix_spectral_library.npz")
    np.savez(npz_path, **columns)

    print(f"Wrote {csv_path}")
    print(f"Wrote {npz_path}")
    print(f"  {N_BANDS} bands, {len(names) - 1} spectra: "
          f"{', '.join(n for n in names if n != 'wavelength_nm')}")


if __name__ == "__main__":
    main()
