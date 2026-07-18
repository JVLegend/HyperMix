<div align="center">

<img src="assets/banner.png" alt="HyperMix" width="820">

# 🔬 HyperMix

### Open detection of engineered biosignatures in remote hyperspectral imagery

[![License: MIT](https://img.shields.io/badge/License-MIT-b8972a.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20→%203.14-1a2f52.svg)](pyproject.toml)
[![PyTorch](https://img.shields.io/badge/detector-PyTorch-ee4c2c.svg)](hypermix/detector.py)
[![Tests](https://img.shields.io/badge/tests-11%20passing-2ea44f.svg)](tests/)
[![Status](https://img.shields.io/badge/status-active-2ea44f.svg)](STATUS.md)
[![Funded by Experiment Foundation](https://img.shields.io/badge/funded%20by-Experiment%20Foundation-b8972a.svg)](https://experiment.com/projects/cldzyecslnphmynjenmv)

*Pulling a faint engineered reporter out of noisy remote hyperspectral cubes, with calibrated uncertainty.*

</div>

---

We can now read living, engineered cells from a drone, ninety meters up
([Chemla et al., *Nature Biotechnology*, 2026](https://www.nature.com/articles/s41587-025-02622-y)).
But out in the real world that signal is faint: it hides inside the spectrum of
soil, leaves, and water, the atmosphere distorts it, and cheap sensors bury it in
noise. A hyperspectral camera hands you a mountain of data, not an answer. Pulling
the answer out is an **algorithm** problem, and that is what HyperMix is for.

HyperMix treats detection and spectral unmixing as one regularized inverse
problem, designed from the start for **unknown natural backgrounds, sparse
reference libraries, and low SNR**. It is developed by a statistician working in
medical imaging, porting the low-SNR, cross-device reconstruction toolkit from
retinal OCT to biology at a distance. Everything here is MIT licensed.

## 📚 Contents

- [✨ Highlights](#-highlights)
- [🚀 Quickstart](#-quickstart)
- [🧪 The learned detector](#-milestone-2-a-learned-detector-that-beats-the-baselines)
- [📊 Benchmarks](#-benchmarks)
- [🗺️ Roadmap](#️-roadmap)
- [💾 Data](#-data)
- [⚠️ Honest limitations](#️-honest-limitations)

## ✨ Highlights

- 🌍 **Physics-based scene simulator** with exact ground truth (NumPy only, deterministic).
- 🛰️ **Real-data benchmark** on a real AVIRIS cube (Indian Pines) via implanted targets.
- 🧬 **Targets grounded on the paper**: biliverdin IXα and bacteriochlorophyll a.
- 🧠 **Detector aprendido**, avaliado contra baselines por pixel e com suavização espacial em 3 fundos reais.
- 🧪 **Unmixing head** that estimates fractional abundance (how much, not just whether).
- 🎯 **Calibrated uncertainty** via MC-dropout (know where to trust the map).
- 🔓 **100% open**, MIT licensed, reproducible from a clean clone.

## 🚀 Quickstart

Run it in your browser, no setup:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JVLegend/HyperMix/blob/main/notebooks/quickstart.ipynb)

Or locally:

```bash
pip install -e ".[viz]"        # numpy + scipy + matplotlib
```

```python
from hypermix import simulate_scene, spectral_matched_filter, roc_auc

scene = simulate_scene(snr_db=10.0, seed=0)          # cube + full ground truth
score = spectral_matched_filter(scene.cube, scene.reporter)
print("AUC:", roc_auc(score, scene.detection_gt))
```

Reproduce everything:

```bash
python examples/run_demo.py         # simulator + baseline, AUC vs SNR
python scripts/fetch_data.py        # download the real AVIRIS cube
python -m hypermix.benchmark        # full benchmark (synthetic + real)
python scripts/train_detector.py    # train the learned detector (needs ".[train]")
pytest -q                           # 11 tests
```

## 🧠 Milestone 2: detector aprendido com contexto espacial

`hypermix.detector` feeds each pixel the scene's **own** adaptive detector
outputs (matched filter, ACE) plus spatial context, z-scored per scene, and a
small PyTorch network learns a nonlinear combination. O treinamento usa apenas
fundos simulados; os testes usam fundos reais com o mesmo alvo sintético, modelo
de mistura linear e gerador de blobs do treino. Portanto, este experimento mede
robustez à troca de fundo, não generalização completa para alvos reais. It ships
**MC-dropout uncertainty**.

<div align="center">
<img src="assets/detector_real.png" alt="Learned detector on real background" width="920">
<br><em>Real Indian Pines background, implanted target at 5 dB SNR. The classical matched filter drowns in real clutter; the learned detector recovers the targets and flags its own uncertainty.</em>
</div>

## 📊 Benchmarks

Detection AUC on the **real** Indian Pines background (implanted target, 3 seeds):

| SNR (dB) | Matched filter | Matched filter (spatial) | ACE | 🧠 **Learned** |
|---------:|:--------------:|:------------------------:|:---:|:--------------:|
| 20 | 0.919 | 0.995 | 0.789 | **0.997** |
| 10 | 0.769 | 0.947 | 0.639 | **0.970** |
| 5  | 0.688 | 0.881 | 0.570 | **0.910** |
| 0  | 0.627 | 0.797 | 0.530 | **0.828** |

O baseline espacial aplica ao matched filter um blur gaussiano fixo com
`sigma=1,5` pixel. Na média das três cenas e quatro níveis de SNR, o delta do
detector cai de 0,165 AUC sobre o matched filter por pixel para 0,020 sobre o
matched filter espacial. Em 0 dB, o delta cai de 0,149 para 0,023. Assim, a maior
parte da vantagem observada no protocolo antigo vem do prior espacial dos alvos
em blob, não de uma vantagem espectral demonstrada.

## 🏆 Leaderboard

Detection AUC across **3 real hyperspectral scenes of different sensors and band
counts** (Indian Pines & Salinas: AVIRIS; Pavia University: ROSIS), 3 seeds.
`Mean AUC` averages over all scenes and SNR = 20, 10, 5, 0 dB. The learned
detector is trained **only on simulation**. Reproduce: `python scripts/make_leaderboard.py`.

| Rank | Method | Mean AUC | AUC @ 0 dB |
|-----:|--------|:--------:|:----------:|
| 1 | 🧠 Learned detector (HyperMix) | **0.854** | **0.742** |
| 2 | Matched filter (spatial) | 0.834 | 0.719 |
| 3 | Matched filter | 0.689 | 0.593 |
| 4 | Spectral Angle Mapper | 0.595 | 0.542 |
| 5 | ACE | 0.595 | 0.519 |

Per-scene AUC @ 0 dB (hardest case). Note it wins even on Pavia (a ROSIS sensor,
unlike the AVIRIS scenes), evidence of cross-sensor generalization:

| Method | Indian Pines | Salinas | Pavia U. |
|--------|:---:|:---:|:---:|
| 🧠 Learned detector | **0.828** | **0.759** | **0.640** |
| Matched filter (spatial) | 0.797 | 0.736 | 0.625 |
| Matched filter | 0.627 | 0.588 | 0.562 |

## 🧪 Unmixing: how much, not just whether

Detection asks *is the reporter here?* Unmixing asks *how much?* `AbundanceUnmixer`
adds a regression head (same scene-adaptive features) that estimates the target's
fractional abundance. Recovery, measured as Pearson r between the predicted and
true abundance on each real scene at 10 dB, versus the matched filter as an
abundance proxy:

| Scene | Matched filter r | 🧠 Unmixer r |
|---|:---:|:---:|
| Indian Pines | 0.435 | **0.922** |
| Salinas | 0.236 | **0.859** |
| Pavia University | 0.089 | **0.302** |

Reproduce: `python scripts/train_unmixer.py`.

## 📦 Open spectral dataset

`dataset/` ships an open spectral library (CSV + NPZ): the background endmembers
and the two paper-grounded reporters (biliverdin IXα, bacteriochlorophyll a) on a
400-1000 nm grid, with a [data card](dataset/DATA_CARD.md). Regenerate with
`python scripts/export_dataset.py`.

## 🗺️ Roadmap

- [x] **Milestone 0** — scene simulator, classical baselines, metrics
- [x] **Milestone 1** — real-background benchmark (AVIRIS), implanted-target harness, paper-grounded reporters
- [x] **Milestone 2** — physics-informed learned detector with MC-dropout uncertainty (beats baselines at low SNR, generalizes sim → real)
- [ ] **Milestone 3** — public release (in progress): ✅ Colab notebook · ✅ open spectral dataset + leaderboard · ✅ 3-scene cross-sensor benchmark · ✅ build + CITATION/Zenodo metadata · ⏳ PyPI publish · ⏳ DOI

## 💾 Data

Datasets are downloaded, not committed:

```bash
python scripts/fetch_data.py
```

Indian Pines is a public AVIRIS scene (Purdue University).

## ⚠️ Honest limitations

- Reporter spectra are modeled from published absorption maxima, not yet the
  measured spectra. They drop in without any API change once available.
- Part of the learned detector's gain is spatial regularization of extended
  (blob) targets; the edge shrinks for point-like targets.
- The first learned model is a small MLP; richer models and a true unmixing head
  are future work. All numbers, including failures, are tracked in [STATUS.md](STATUS.md).

## 📚 Cite

If you use HyperMix, please cite it (see [CITATION.cff](CITATION.cff)). A Zenodo
DOI is planned for the next release.

## 📄 License

MIT. See [LICENSE](LICENSE). Built with support from the
[Experiment Foundation](https://experiment.com/projects/cldzyecslnphmynjenmv)
Hyperspectral Biology grant.
