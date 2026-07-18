# STATUS — HyperMix

Source of progress truth for the repo. Read before starting a phase, update at the end.

## Agora: Fase B, realismo físico e a pergunta decisiva - 2026-07-18

Adicionada física opt-in ao forward model (não invalida os números da Fase A,
que usam os defaults antigos):
- `atmospheric_transmittance` (transmitância espectral com bandas de absorção de
  O2/vapor de água) e `apply_srf` (resolução espectral finita via suavização no
  eixo de bandas), plugáveis em `simulate_scene(atmosphere=, srf_fwhm=)`.
- `implant_target(mixing="bilinear")`: termo de interação Fan (fundo x alvo), que
  quebra a premissa linear-aditiva do matched filter. É o regime onde um detector
  aprendido poderia justificar sua existência.

Experimento decisivo (`scripts/nonlinear_experiment.py`), MF espacial vs detector
aprendido treinado no mesmo modelo de mistura, 3 cenas reais, target SNR 5 e 0 dB:
- Mistura linear: MF espacial 0,986 vs aprendido 0,980 (MF espacial vence).
- Mistura bilinear: MF espacial 0,990 vs aprendido 0,994 (empate, dentro de 0,005).

Conclusão honesta: em nenhum regime testado o detector aprendido supera de forma
robusta o matched filter espacial bem calibrado. **A contribuição científica do
HyperMix não é um detector superior; é o benchmark físico aberto e reprodutível,
o simulador, e a avaliação honesta que mostra que, aqui, métodos clássicos bastam.**
Isso é field-building legítimo e não deve ser vendido como "nosso modelo vence".
Não perseguir um regime artificial só para fabricar uma vitória (benchmark-hacking).
Artefatos: `results/nonlinear.json` e `results/nonlinear.md`. 18 testes passando.

## Fase A: endurecimento de validade científica - 2026-07-18

- [x] A1: adicionado `smoothed_matched_filter`, com blur gaussiano fixo de
      `sigma=1,5` pixel, ao benchmark e ao leaderboard.
- [x] A2: o ruído agora é calibrado pela contribuição do alvo, não pelo RMS da
      cena. Target SNR = `20 log10(RMS do alvo / RMS do ruído)`, com RMS do alvo
      calculado nos pixels cuja abundância excede o limiar de detecção.
- [x] A3: mismatch espectral medido por deslocamento controlado da assinatura.
- [x] A4: Pearson r e MAE calculados nos pixels de alvo (`ab_gt > 0,02`), com
      MAE em todos os pixels mantida apenas como diagnóstico secundário.

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

Mismatch a target SNR de 5 dB, média de 3 cenas e 3 seeds:

- Deslocamento de 1%: queda de AUC de 0,041 no MF, 0,007 no MF espacial e
  0,014 no detector aprendido.
- Deslocamento de 2,5%: quedas de 0,159, 0,070 e 0,080, respectivamente.
- Deslocamento de 5%: quedas de 0,293, 0,260 e 0,277, respectivamente.

O MF espacial permaneceu acima do detector aprendido em todos os níveis. O
deslocamento usa a faixa normalizada de índices porque as cenas têm grades
espectrais diferentes. Artefatos: `results/mismatch.json` e
`results/mismatch.md`.

Unmixing a target SNR de 10 dB, média de 3 seeds:

- Indian Pines: target r 0,982 no unmixer e 0,966 no MF; target MAE 0,0081 e
  0,0142, respectivamente.
- Salinas: target r 0,988 no unmixer e 0,979 no MF; target MAE 0,0237 e 0,0073.
  A correlação favorece o unmixer, mas a MAE mostra viés de escala e favorece o
  MF nesta cena.
- Pavia U.: target r 0,938 no unmixer e 0,796 no MF; target MAE 0,0093 e 0,0177.

Artefatos: `results/unmix_eval.json` e `results/unmix_eval.md`.

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
- [x] Avaliação original treinou em fundo simulado e testou em fundo real. A
      auditoria de 18/07 mostrou que isso mede robustez ao fundo e que o ganho
      publicado contra o MF por pixel não sobrevive ao MF espacial.
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
- [x] Leaderboard criado em `results/leaderboard.md`; números originais foram
      substituídos após correção de target SNR e inclusão do MF espacial.
- [x] Avaliação multi-cena cobre Indian Pines e Salinas (AVIRIS) e Pavia U.
      (ROSIS). A troca de sensor não remove a circularidade do alvo implantado.
- [x] Packaging: `python -m build` produces a clean sdist + wheel (PyPI-ready).
- [x] CITATION.cff + .zenodo.json added (DOI-ready).
- [x] Unmixing head (`AbundanceUnmixer`) estima abundância fracionária. A métrica
      original em todos os pixels foi substituída por target r e target MAE;
      valores atuais estão na seção de Fase A e em `results/unmix_eval.md`.
- [x] `RELEASE.md`: step-by-step PyPI + Zenodo instructions for the author.
- [ ] PyPI publish: author runs `twine upload dist/*` with their token (see RELEASE.md).
- [ ] DOI: connect the GitHub repo to Zenodo and cut a release (see RELEASE.md).

## Grant / admin (tracked in the vault, not here)

Approved for US$ 2,500. Funds release only after the Experiment.com campaign
launches (needs endorsement -> DocuSign -> launch). Building proceeds now on free
compute regardless.
