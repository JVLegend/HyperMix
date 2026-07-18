# STATUS — HyperMix

Source of progress truth for the repo. Read before starting a phase, update at the end.

## Now: Phase 0 shipped (Milestone 0) — 2026-07-16

Working, tested, reproducible on Python 3.10+ (built on 3.14.6, numpy 2.5.1).

- `hypermix/simulate.py` — physics-based scene simulator (`simulate_scene`) with
  full ground truth: linear background mixing, reporter blobs, illumination gain,
  FFT PSF blur, SNR-scaled noise. Deterministic per seed, NumPy only.
- `hypermix/baselines.py` — `spectral_matched_filter`, `ace`.
- `hypermix/metrics.py` — `roc_auc` (Mann-Whitney), `roc_curve`.
- `examples/run_demo.py` — AUC-vs-SNR table + `assets/demo_detection.png`.
- `tests/test_core.py` — 4 tests, all passing (`pytest -q`).

Baseline result (matched filter, seed 0): AUC 0.947 @ 30 dB down to 0.626 @ 0 dB.
The low-SNR collapse is the motivation for Milestone 2.

## Done: Milestone 1 — real backgrounds + benchmark (2026-07-16)

- [x] Real HSI loader (`datasets.load_mat_cube`) + implanted-target adapter
      (`datasets.implant_target`) on a real AVIRIS cube (Indian Pines).
- [x] `scripts/fetch_data.py` downloads/validates the cube (data/ gitignored).
- [x] Benchmark harness (`hypermix.benchmark`, `python -m hypermix.benchmark`):
      all baselines over SNR sweep + seeds, synthetic + real, logs
      `results/benchmark.json`, saves `assets/benchmark_real.png`.
- [x] Reporters grounded on Chemla et al. 2026: `reporter_library()` models
      biliverdin IXα + bacteriochlorophyll a from published absorption maxima
      (approximate; swap for measured spectra when available).
- [x] 7 tests passing.

Real-background result (matched filter, Indian Pines, 3 seeds):
AUC 0.920 @ 30 dB → 0.630 @ 0 dB.

Still open for later polish: ENVI/USGS/ECOSTRESS loaders exist but untested on
real files; add linear-unmixing / NNLS abundance baseline; more scenes.

## Done: Milestone 2 — learned detector (2026-07-16)

- [x] `hypermix/detector.py`: physics-informed learned detector (PyTorch, lazy
      import). Features per pixel = scene-adaptive detector outputs (matched
      filter, ACE) + spatial context, z-scored per scene. `SpectralDetector`
      (MLP + dropout), `make_training_set`, MC-dropout uncertainty.
- [x] `scripts/train_detector.py`: train on simulated backgrounds, evaluate on
      held-out synthetic AND real Indian Pines; writes results/detector_eval.json
      + assets/detector_real.png (with uncertainty map).
- [x] Trained purely on simulation, generalizes to real background.
      Real Indian Pines AUC (learned vs matched filter): 0.997/0.919 @20dB,
      0.910/0.688 @5dB, 0.828/0.627 @0dB. Biggest gain at low SNR.
- [x] MC-dropout uncertainty map shipped.
- [x] 8 tests passing (torch test skips when torch absent).

Training env: Python 3.11 (`.venv-train`) with `torch` — torch has no 3.14
wheels yet. The core package (M0/M1) still runs on 3.14 without torch.

### Honest caveats / next
- Part of the gain over the per-pixel matched filter is spatial regularization
  (targets are extended blobs). For point targets the spatial edge shrinks.
- First learned model is a small MLP over 5 features. Next: richer model,
  a true forward-model / unmixing head, and self-supervised adaptation on the
  test scene's own unlabeled pixels.
- Reporter spectra still approximate (paper maxima); wire in measured spectra.

## In progress: Milestone 3 — public release

- [x] Colab quickstart notebook (`notebooks/quickstart.ipynb`): simulate ->
      matched filter -> AUC-vs-SNR -> train learned detector, all in-browser.
      "Open in Colab" badge in the README.
- [x] SAM baseline (`spectral_angle_mapper`) added; now 3 classical baselines.
- [x] Open spectral library exported to `dataset/` (CSV + NPZ + DATA_CARD),
      `scripts/export_dataset.py`.
- [x] Leaderboard: `scripts/make_leaderboard.py` -> `results/leaderboard.md`.
      Learned 0.926 mean AUC > matched filter 0.751 > SAM 0.642 > ACE 0.632 (real bg).
- [x] Multi-scene real evaluation: learned detector beats baselines on 3 real
      cubes (Indian Pines, Salinas = AVIRIS; Pavia U. = ROSIS), i.e. cross-sensor
      and cross-band-count generalization, trained only on simulation.
      Leaderboard mean AUC: learned 0.854 > matched filter 0.689 > SAM/ACE 0.595.
- [x] Packaging: `python -m build` produces a clean sdist + wheel (PyPI-ready).
- [x] CITATION.cff + .zenodo.json added (DOI-ready).
- [ ] PyPI publish: author runs `twine upload dist/*` with their token.
- [ ] DOI: connect the GitHub repo to Zenodo and cut a release (or upload dist).

## Grant / admin (tracked in the vault, not here)

Approved for US$ 2,500. Funds release only after the Experiment.com campaign
launches (needs endorsement -> DocuSign -> launch). Building proceeds now on free
compute regardless.
