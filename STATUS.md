# STATUS - HyperMix

Source of progress truth for the repo. Read before starting a phase, update at the end.

## T7a concluído: modelo auto-supervisionado do fundo - 2026-07-18

Foi implementado um autoencoder espectral raso que aprende apenas com os pixels
não rotulados da própria cena de teste. O ajuste não recebe máscara, rótulos nem
a assinatura do alvo. Depois do treino, o score combina o quantil do erro de
reconstrução com o quantil do matched filter por uma regra fixa. Também foram
adicionados o baseline RX global e a métrica Pd@FAR.

O protocolo usa Indian Pines, Salinas e Pavia University, target SNR de 5 e 0
dB, 4 seeds por ponto e 5000 réplicas de bootstrap hierárquico sobre cenas e
seeds. Resultados agregados:

| Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |
|---|:---:|:---:|
| MF espacial | 0,987 [0,968, 0,997] | 0,650 [0,227, 0,872] |
| RX global | 0,539 [0,494, 0,593] | 0,001 [0,001, 0,002] |
| Autoencoder de fundo | 0,869 [0,776, 0,923] | 0,108 [0,003, 0,203] |
| Autoencoder de fundo espacial | 0,976 [0,945, 0,994] | 0,324 [0,087, 0,544] |

Na comparação pareada pré-especificada, autoencoder espacial menos MF
espacial, a diferença foi -0,011 [-0,023, -0,003] em AUC e -0,325 [-0,517,
-0,142] em Pd@FAR. Os dois intervalos ficaram abaixo de zero.

Conclusão: **o modelo de fundo simples não produziu a primeira vantagem causal
legítima do aprendizado**. Neste protocolo, ele foi significativamente inferior
ao MF espacial nas duas métricas. Isso fecha a instanciação pré-especificada do
autoencoder raso, mas não prova que todo estimador possível de fundo falhará. A
contribuição continua sendo o benchmark aberto, os baselines reproduzíveis e o
registro de resultados negativos sem seleção por rótulos.

Artefatos: `scripts/background_experiment.py`, `results/background.json` e
`results/background.md`. O SHA-256 do JSON foi
`3e77d71fba3ff6d575c10cb74586df876f6c0ec318f2a27ac9b68741d423fa51` em duas
execuções independentes. A documentação pública e o observatório não foram
alterados porque o critério de vantagem não foi satisfeito. 29 testes passando.

## Observatório web publicado - 2026-07-18

O benchmark agora possui uma interface web interativa em
https://hypermix-observatory.vercel.app, publicada na Vercel. O painel reúne a
fotografia auditada do leaderboard, target SNR, mismatch espectral, realismo
físico, variabilidade T1, unmixing e limitações.

A interface agora usa inglês como idioma inicial e inclui um seletor 🇺🇸/🇧🇷 no
topo. A troca atualiza todo o conteúdo e o idioma acessível do documento sem
alterar a rota ou a âncora ativa.

Redesign editorial publicado com navegação flutuante, hierarquia mais clara e
cards responsivos. O novo Map Studio aceita PNG, JPEG e WebP de até 12 MB,
processa o arquivo localmente e permite variar o limiar de visualização. O
brilho do pixel é tratado como score. Isso não é inferência sobre RGB e não
substitui o pipeline hiperespectral.

O site preserva a conclusão atual: neste protocolo, o matched filter espacial
lidera ou empata com o detector aprendido. Ele não executa inferência no
navegador e não se apresenta como leaderboard sincronizado automaticamente.
Os valores curados devem ser atualizados em `webapp/app/page.tsx` quando os
artefatos científicos em `results/` mudarem.

Implementação em `webapp/`, com preview local via vinext e build Next.js nativo
para a Vercel. Verificação da interface: build vinext, testes de renderização,
build Vercel e lint. Instruções de desenvolvimento e deploy em
`webapp/README.md`.

## Agora: T1 concluído, variabilidade do alvo medido - 2026-07-18

Novo baseline clássico `matched_subspace_detector`, com projeção no subespaço
alvo após whitening pela covariância da cena, e versão espacial comparável. Com
uma única assinatura, o score reduz numericamente ao ACE. Referência conceitual:
Scharf e Friedlander, *Matched Subspace Detectors*, IEEE TSP 1994.

Experimento determinístico em `scripts/target_variability_experiment.py`, com
endmembers USGS, grade calibrada de 400-1000 nm, target SNR de 20, 10, 5 e 0 dB
e 6 seeds estratificadas por ponto:

| Track | MF espacial nominal | Subespaço espacial | Aprendido | Oráculo |
|---|:---:|:---:|:---:|:---:|
| Hospedeiro SmURFP/biliverdina | 0,996 | 0,967 | 0,997 | 0,997 |
| Hospedeiro + sensor + atmosfera | 0,993 | 0,910 | 0,996 | 0,995 |
| Qualquer repórter, BChl ou biliverdina | 0,907 | 0,948 | 0,928 | 0,996 |

Nos dois tracks intra-SmURFP, o aprendido empata com o MF espacial nominal pela
margem de 0,005. No track de qualquer repórter, o subespaço espacial supera o
aprendido por 0,020 AUC. Esse terceiro track combina classes químicas e não é
variabilidade intra-repórter. A abundância aleatória representa nível de
expressão; o track de sensor sorteia FWHM de 6-14 nm e força atmosférica de
0,7-1,3.

Conclusão: **a variabilidade medida também não produz vantagem robusta para o
detector aprendido atual**. As features do MLP continuam sendo MF, ACE e suas
versões suavizadas com o alvo nominal; o modelo não vê sinal espectral que esses
métodos descartam. Um método aprendido só terá teste causal legítimo quando
consumir cubo bruto ou estatística de fundo adicional.

Artefatos: `results/target_variability.json` e
`results/target_variability.md`. Hash do JSON foi idêntico em duas execuções.
25 testes passando.

## Fase B concluída, realismo físico opt-in - 2026-07-18

Implementação opt-in, sem alterar os defaults nem os números auditados da Fase A:

- quatro endmembers medidos do USGS Spectral Library Version 7;
- absorbância inferida de pellets YF10 e bpHO-smURFP em dois hospedeiros, obtida
  do arquivo oficial bioHSI de Chemla et al.;
- conversão explícita de absorbância para alvo semelhante a reflectância por
  Beer-Lambert, sem apresentar a curva resultante como reflectância medida;
- SRF gaussiana física com centros e FWHM em nanômetros, além da interface antiga
  em número de bandas;
- atmosfera simples com bandas estruturadas e path radiance, declarada como
  análise de sensibilidade e não radiative transfer completo;
- mistura generalizada bilinear em `simulate_scene` e `implant_target`.

Reconstrução rastreável em `scripts/fetch_reference_spectra.py`, com SHA-256 das
fontes. Biblioteca compacta em `hypermix/data/reference_spectra.csv` e exportação
aberta em `dataset/`. Picos medidos na grade de 1 nm: YF10 em 866 nm,
SmURFP/biliverdina em 641 nm para *E. coli* e 642 nm para *P. putida*.

Experimento físico (`results/realism.md`), AUC média sobre target SNR 20, 10, 5
e 0 dB, 5 seeds:

- controle estilizado linear: MF espacial 0,983;
- espectros medidos lineares: 0,995;
- medidos + SRF de 10 nm: 0,994;
- medidos + SRF + atmosfera: MF espacial oráculo 0,994, alvo laboratorial 0,913;
- cenário completo bilinear: MF espacial oráculo 0,983, alvo laboratorial 0,906.

O alvo oráculo já inclui sensor e atmosfera. A queda com o alvo laboratorial
mostra que conhecimento do espectro no sensor é uma premissa forte. O experimento
usa uma grade simulada calibrada; os MAT reais atuais não trazem centros de banda.

Experimento não linear em três fundos reais (`scripts/nonlinear_experiment.py`),
target SNR 5 e 0 dB, 3 seeds:

- mistura linear: MF espacial 0,986 vs aprendido 0,980, MF espacial vence;
- mistura bilinear: MF espacial 0,989 vs aprendido 0,992, empate dentro de 0,005.

Conclusão honesta: em nenhum regime testado o detector aprendido supera de forma
robusta o matched filter espacial bem calibrado. **A contribuição científica do
HyperMix não é um detector superior; é o benchmark físico aberto e reprodutível,
o simulador, e a avaliação honesta que mostra que, aqui, métodos clássicos bastam.**
Não perseguir um regime artificial só para fabricar uma vitória.
Artefatos: `results/nonlinear.json`, `results/nonlinear.md`,
`results/realism.json` e `results/realism.md`. 23 testes passando.

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

- `hypermix/simulate.py` - physics-based scene simulator (`simulate_scene`) with
  full ground truth: linear background mixing, reporter blobs, illumination gain,
  FFT PSF blur, SNR-scaled noise. Deterministic per seed, NumPy only.
- `hypermix/baselines.py` - `spectral_matched_filter`, `ace`.
- `hypermix/metrics.py` - `roc_auc` (Mann-Whitney), `roc_curve`.
- `examples/run_demo.py` - AUC-vs-SNR table + `assets/demo_detection.png`.
- `tests/test_core.py` - 4 tests, all passing (`pytest -q`).

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
      (aproximação histórica; a Fase B adicionou as curvas medidas separadamente).
- [x] 7 tests passing.

Real-background result (matched filter, Indian Pines, 3 seeds):
AUC 0.920 @ 30 dB → 0.630 @ 0 dB.

Ainda aberto: testar o loader ENVI com arquivos rastreáveis, ampliar a biblioteca
medida além das quatro amostras USGS atuais, adicionar baseline NNLS e mais cenas.

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

Training env: Python 3.11 (`.venv-train`) with `torch` - torch has no 3.14
wheels yet. The core package (M0/M1) still runs on 3.14 without torch.

### Honest caveats / next
- Part of the gain over the per-pixel matched filter is spatial regularization
  (targets are extended blobs). For point targets the spatial edge shrinks.
- First learned model is a small MLP over 5 features. Next: richer model,
  a true forward-model / unmixing head, and self-supervised adaptation on the
  test scene's own unlabeled pixels.
- Item histórico superado na Fase B: espectros medidos foram incorporados, mas
  continuam sendo absorbâncias de pellets e não reflectância remota absoluta.

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
