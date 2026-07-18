"""Export the HyperMix open spectral library to ./dataset (CSV + NPZ).

    python scripts/export_dataset.py

Writes a small, citable open dataset: the background endmembers and the two
paper-grounded reporter signatures on a canonical 400-1000 nm grid, plus a
data card. This is the seed of the open spectral dataset (Milestone 3).
"""

from __future__ import annotations

import os

import numpy as np

from hypermix import endmember_library, reporter_library
from hypermix.simulate import _wavelengths

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "dataset")
N_BANDS = 61  # 400-1000 nm at 10 nm steps


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    wl = _wavelengths(N_BANDS)
    _, endmembers = endmember_library(N_BANDS)
    reporters = reporter_library(N_BANDS)

    columns = {"wavelength_nm": wl}
    columns.update(endmembers)
    columns.update(reporters)
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
