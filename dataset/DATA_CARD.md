# HyperMix open spectral library

A small, open spectral library for hyperspectral biosignature detection:
natural background endmembers and the two engineered reporters from the
founding paper, on a canonical wavelength grid.

## Files
- `hypermix_spectral_library.csv` — one row per wavelength; columns are the
  spectra.
- `hypermix_spectral_library.npz` — same data as NumPy arrays keyed by name.

## Grid
- 61 bands, 400-1000 nm, 10 nm steps (`wavelength_nm` column).

## Spectra (reflectance, 0-1)
| Name | Type | Provenance |
|---|---|---|
| `vegetation` | background endmember | stylized (green bump + red edge + NIR plateau) |
| `soil` | background endmember | stylized (smooth rise) |
| `dry_vegetation` | background endmember | stylized |
| `water` | background endmember | stylized (NIR absorption) |
| `bacteriochlorophyll_a` | engineered reporter | modeled from published absorption maxima (Qx ~600 nm, Qy ~770 nm) |
| `biliverdin_ixalpha` | engineered reporter | modeled from published absorption maxima (~670 nm band) |

## Important honesty notes
- The **background endmembers are stylized**, not measured, standing in for
  soil/vegetation/water until measured libraries (USGS, ECOSTRESS) are wired in.
- The **reporter signatures are modeled** from the reported absorption maxima of
  the two molecules Chemla et al. (*Nature Biotechnology*, 2026) selected,
  biliverdin IXα and bacteriochlorophyll a. They are approximate placeholders
  for the measured spectra; drop measured spectra in when available.

## Reproduce
```bash
python scripts/export_dataset.py
```

## License
Released under MIT together with the HyperMix repository. Attribution
appreciated: HyperMix (github.com/JVLegend/HyperMix). Reporter molecule choices
follow Chemla et al., *Nature Biotechnology*, 2026.
