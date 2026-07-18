# STATUS - HyperMix

Source of progress truth for the repo. Read before starting a phase, update at the end.

## T7b concluído: incerteza calibrada - 2026-07-18

A hipótese nova foi testada com split explícito entre calibração e avaliação.
Em cada uma das três cenas reais e em target SNR de 5 e 0 dB, os implantes de
seeds 100 e 101 ajustam os calibradores; os implantes de seeds 0 a 3 são usados
somente nas métricas. O MF e o MF espacial recebem Platt scaling. O detector
recebe temperature scaling com correção de intercepto, sozinho e como ensemble
de três redes treinadas apenas em fundos simulados.

NLL e Brier são calculados sem balanceamento de classe em cada caso. A ECE usa
15 bins uniformes. O agregado dá o mesmo peso a cada combinação de cena, SNR e
seed. IC 95% usam 5000 réplicas de bootstrap hierárquico sobre cenas e seeds.

| Método | NLL [IC 95%] | Brier [IC 95%] | ECE [IC 95%] | AUC [IC 95%] |
|---|:---:|:---:|:---:|:---:|
| MF + Platt | 0,12953 [0,05716, 0,23007] | 0,03477 [0,01424, 0,06252] | 0,01581 [0,00950, 0,02486] | 0,926 [0,818, 0,984] |
| MF espacial + Platt | 0,05766 [0,01935, 0,12004] | 0,01540 [0,00517, 0,03152] | 0,00896 [0,00441, 0,01532] | 0,986 [0,963, 0,999] |
| Aprendido + temperatura | 0,07169 [0,02790, 0,14910] | 0,01968 [0,00770, 0,04008] | 0,01291 [0,00909, 0,01814] | 0,977 [0,936, 0,999] |
| Ensemble aprendido + temperatura | 0,06792 [0,02710, 0,13866] | 0,01940 [0,00760, 0,03944] | 0,01293 [0,00906, 0,01837] | 0,980 [0,946, 0,999] |

O critério pré-especificado exigia que os limites superiores dos IC para a
diferença ensemble menos MF espacial fossem negativos em NLL e ECE. O resultado
foi o oposto: +0,01026 [0,00448, 0,01778] em NLL e +0,00397 [0,00208, 0,00560]
em ECE. Brier também piorou em +0,00401 [0,00166, 0,00766].

Conclusão: **o aprendizado não venceu em incerteza calibrada neste protocolo**.
O MF espacial calibrado foi significativamente melhor nas três métricas próprias
de probabilidade. Isto não reproduz a tarefa de recuperação atmosférica do Ariel
Data Challenge; testa a pergunta binária correspondente no benchmark HyperMix.

Artefatos: `hypermix/calibration.py`, `scripts/uncertainty_experiment.py`,
`results/uncertainty.json`, `results/uncertainty.md` e
`assets/reliability_uncertainty.png`. O SHA-256 do JSON foi
`5cd0b6129d5109db5cadbf14ad8c4ba7ce986584ad8a8ba11f2fabab887f3052`
em duas execuções completas independentes.

## T7c concluído: esparsidade de banda - 2026-07-18

As bandas foram ordenadas separadamente em cada cubo real não implantado pelo
coeficiente absoluto do matched filter completo, `|C^-1 (t - mu)|`. A seleção
conhece a assinatura do alvo e as estatísticas não rotuladas da cena, mas não
usa máscara, AUC ou rótulos implantados. O MF foi recalculado nas top-k bandas
com k igual a 1, 2, 3, 5, 10, 20, 40, 80 e todas.

| Top-k | AUC do MF espacial [IC 95%] |
|---:|:---:|
| 1 | 0,838 [0,566, 0,984] |
| 2 | 0,949 [0,867, 0,993] |
| 3 | 0,948 [0,870, 0,993] |
| 5 | 0,963 [0,903, 0,997] |
| 10 | 0,969 [0,921, 0,999] |
| 20 | 0,983 [0,954, 0,999] |
| 40 | 0,986 [0,963, 0,999] |
| 80 | 0,987 [0,964, 0,999] |
| Todas | 0,984 [0,964, 0,997] |

Top-3 menos todas as bandas foi -0,036 [-0,092, -0,000] em AUC espacial.
As top-3 concentraram apenas 0,098, 0,134 e 0,161 do peso absoluto em Indian
Pines, Salinas e Pavia University. O menor k cuja média ficou a até 0,005 do MF
completo foi 20, uma leitura descritiva e não prova de equivalência.

Conclusão: **menos de três bandas não bastaram neste benchmark de detecção**.
O estudo `One Channel Is All You Need` avalia classificação de culturas na
competição ICPR 2024 e foi publicado posteriormente nos anais do ICAISC. Ele
motiva a ablação, mas não transfere automaticamente para alvo hiperespectral
implantado e seleção target-aware.

Artefatos: `scripts/band_sparsity_experiment.py`,
`results/band_sparsity.json`, `results/band_sparsity.md` e
`assets/band_sparsity.png`. O SHA-256 do JSON foi
`227273f2aba5cd7ba7683bbe7a97314250de16beeb38470d8e93e69bac77c781`
em duas execuções completas independentes. A suíte tem 33 testes passando.

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

O storytelling agora possui sete capítulos. Depois do experimento de fundo,
novos painéis apresentam T7b, com NLL, Brier, ECE, curva de confiabilidade e o
split de calibração, e T7c, com AUC do MF espacial versus top-k bandas. Os
valores são curados diretamente de `results/uncertainty.json` e
`results/band_sparsity.json`. A versão publicada preserva inglês como idioma
inicial e registra explicitamente que o aprendizado perdeu também em calibração
e que três bandas não bastaram neste benchmark. Build vinext, renderização,
tipos, lint, build Next.js e deploy Vercel foram verificados.

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

O storytelling vertical agora apresenta o benchmark como um dossiê causal em
cinco capítulos: baixo sinal, realismo físico, variabilidade, aprendizado do
fundo e unmixing. Cada capítulo encerra com a pergunta que abre o próximo. O Map
Studio foi movido para depois das evidências, antes dos limites finais.

A experiência por scroll adiciona barra de progresso, trilho do capítulo ativo,
parallax leve no hero e reveals de elementos-chave. O scroll natural não é
interceptado. Parallax e trilho são removidos em telas compactas, e
`prefers-reduced-motion` desativa as transformações decorativas sem ocultar
conteúdo.

Os valores curados também incluem T7a. MF espacial obteve AUC 0,987 [0,968,
0,997] e Pd@FAR 0,650 [0,227, 0,872]; o autoencoder espacial obteve 0,976
[0,945, 0,994] e 0,324 [0,087, 0,544]. A interface registra que os intervalos
das diferenças ficaram abaixo de zero e não generaliza essa falha para todo
estimador possível de fundo.

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
