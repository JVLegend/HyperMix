# STATUS — HyperMix

Source of progress truth for the repo. Read before starting a phase, update at the end.

## Agora: endurecimento de validade científica, Fase A - 2026-07-18

- [x] A1: adicionado `smoothed_matched_filter`, com blur gaussiano fixo de
      `sigma=1,5` pixel, ao benchmark e ao leaderboard.
- [x] A2: o ruído agora é calibrado pela contribuição do alvo, não pelo RMS da
      cena. Target SNR = `20 log10(RMS do alvo / RMS do ruído)`, com RMS do alvo
      calculado nos pixels cuja abundância excede o limiar de detecção.
- [ ] A3: medir robustez a mismatch espectral.
- [ ] A4: substituir Pearson r em todos os pixels por correlação nos pixels de
      alvo e MAE de abundância.

Números atuais, re-medidos com 3 seeds, três fundos reais e target SNR de 20,
10, 5 e 0 dB:

- MF espacial: AUC média 0,990; AUC a 0 dB 0,982.
- Detector aprendido: AUC média 0,987; AUC a 0 dB 0,972.
- MF por pixel: AUC média 0,943; AUC a 0 dB 0,908.

Conclusão atual: o detector aprendido não supera o comparador espacial. O ganho
anterior sobre o MF por pixel confundia informação espectral com o prior espacial
dos blobs. A troca de fundos simulados por fundos reais testa robustez ao fundo,
não generalização completa: treino e teste ainda compartilham repórter sintético,
blobs gaussianos e mistura linear. Os resultados históricos abaixo descrevem o
estado anterior à correção de target SNR e não devem ser citados como atuais.

## Histórico: Phase 0 shipped (Milestone 0) - 2026-07-16

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

## Histórico: Milestone 1 - real backgrounds + benchmark (2026-07-16)

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

## Histórico: Milestone 2 - learned detector (2026-07-16)

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

## Histórico: Milestone 3 - public release

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
- [x] Unmixing head (`AbundanceUnmixer`): estimates fractional abundance, not
      just detection. Pearson r vs true abundance at 10 dB (real scenes):
      Indian Pines 0.922, Salinas 0.859, Pavia 0.302 (matched filter proxy:
      0.435 / 0.236 / 0.089). `scripts/train_unmixer.py`. Delivers the
      "detection + unmixing" promise. 10 tests passing.
- [x] `RELEASE.md`: step-by-step PyPI + Zenodo instructions for the author.
- [ ] PyPI publish: author runs `twine upload dist/*` with their token (see RELEASE.md).
- [ ] DOI: connect the GitHub repo to Zenodo and cut a release (see RELEASE.md).

## Grant / admin (tracked in the vault, not here)

Approved for US$ 2,500. Funds release only after the Experiment.com campaign
launches (needs endorsement -> DocuSign -> launch). Building proceeds now on free
compute regardless.
