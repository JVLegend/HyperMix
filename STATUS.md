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

## Later: Milestone 2 — the detector

- [ ] Physics-informed forward-model layer.
- [ ] Self-supervised (Noise2Noise / Noise2Self) joint detection + unmixing (PyTorch).
      Note: PyTorch wheels for Python 3.14 unconfirmed; pin a supported interpreter
      (3.11/3.12) in a separate training env when this starts.
- [ ] Semi-blind handling of unknown background / missing references.
- [ ] Calibrated per-pixel uncertainty.

## Grant / admin (tracked in the vault, not here)

Approved for US$ 2,500. Funds release only after the Experiment.com campaign
launches (needs endorsement -> DocuSign -> launch). Building proceeds now on free
compute regardless.
