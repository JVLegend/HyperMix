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

## Next: Milestone 1 — data + benchmark

- [ ] Wire in real open HSI (AVIRIS scenes; USGS / ECOSTRESS endmember libraries).
- [ ] Chase the Chemla et al. 2026 supplementary for real reporter absorption spectra;
      until then keep the synthetic signature.
- [ ] Benchmark harness: fixed scene suite + seeds, run all baselines, log AUC/ROC.
- [ ] Add linear unmixing / NNLS abundance baseline.

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
