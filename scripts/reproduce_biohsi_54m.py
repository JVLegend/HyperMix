#!/usr/bin/env python3
"""Reproduz os nove scores publicados para a cena bioHSI de 54 m.

Uso:
    . .venv-train/bin/activate
    python scripts/reproduce_biohsi_54m.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hypermix.biohsi_published import (  # noqa: E402
    load_published_yf10_absorbance,
    published_hkm_ucls,
    smooth_spectral_cube,
)
from hypermix.biohsi_roi import extract_rotated_crop, load_biohsi_54m_protocol  # noqa: E402
from hypermix.envi import open_envi_cube  # noqa: E402
from hypermix.metrics import mean_absolute_error, pearson_r, roc_auc  # noqa: E402


DEFAULT_HEADER = (
    ROOT
    / "data"
    / "biohsi"
    / "rg_on_sand_induction_54m"
    / "raw_0_rd_rf_or.hdr"
)
DEFAULT_JSON = ROOT / "results" / "real_target_reproduction.json"
DEFAULT_MARKDOWN = ROOT / "results" / "real_target_reproduction.md"
DEFAULT_FIGURE = ROOT / "assets" / "biohsi_54m_reproduction.png"
MAE_LIMIT = 0.01
PEARSON_LIMIT = 0.99


def _region_scores(rotated_scores: np.ndarray) -> np.ndarray:
    protocol = load_biohsi_54m_protocol()
    values = [float(np.nanmean(rotated_scores[roi.slices])) for roi in protocol.rois]
    scores = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(scores)):
        raise ValueError("one or more bioHSI regions has no finite score")
    return scores


def _figure(
    rotated_scores: np.ndarray,
    concentrations: np.ndarray,
    reproduced: np.ndarray,
    published: np.ndarray,
    output: Path,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)
    image = axes[0].imshow(rotated_scores, cmap="inferno", vmin=0)
    protocol = load_biohsi_54m_protocol()
    for roi in protocol.rois:
        y0, x0 = roi.top_left_yx
        y1, x1 = roi.bottom_right_yx
        axes[0].add_patch(
            plt.Rectangle(
                (x0, y0), x1 - x0, y1 - y0,
                fill=False, edgecolor="white", linewidth=1.2,
            )
        )
        axes[0].text(x1 + 0.2, (y0 + y1) / 2, f"{roi.concentration_um:g}",
                     color="white", fontsize=8, va="center")
    axes[0].set_title("HKM + UCLS score in the rotated 54 m crop")
    axes[0].set_xlabel("column")
    axes[0].set_ylabel("row")
    figure.colorbar(image, ax=axes[0], fraction=0.046, label="classification score")

    order = np.argsort(concentrations)
    index = np.arange(concentrations.size)
    axes[1].plot(index, published[order], "o-", label="published source data")
    axes[1].plot(index, reproduced[order], "s--", label="HyperMix reproduction")
    axes[1].set_xticks(index, [f"{value:g}" for value in concentrations[order]], rotation=45)
    axes[1].set_xlabel("YF10 induction concentration (µM)")
    axes[1].set_ylabel("mean regional score")
    axes[1].set_title("Nine pre-specified regions, no rescaling")
    axes[1].legend(frameon=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _markdown(payload: dict) -> str:
    metrics = payload["reproduction_metrics"]
    gate = payload["gate"]
    rows = "\n".join(
        "| {index} | {concentration_um:g} | {published_score:.9f} | "
        "{reproduced_score:.9f} | {absolute_error:.9f} |".format(**row)
        for row in payload["regions"]
    )
    verdict = "satisfeita" if gate["passed"] else "não satisfeita"
    implication = (
        "A reprodução cruzou a porta pré-especificada. O confronto T8c pode avançar."
        if gate["passed"]
        else "A reprodução não cruzou a porta pré-especificada. O confronto T8c permanece pausado até a divergência ser explicada."
    )
    return f"""# Reprodução bioHSI de 54 m

Gerada pelo script versionado. Esta é uma reprodução do método publicado, não
um resultado de superioridade do HyperMix.

## Veredito

A porta de reprodução foi **{verdict}**: MAE {metrics['mae']:.6f}
(limite ≤ {gate['mae_limit']:.2f}) e Pearson {metrics['pearson_r']:.6f}
(limite ≥ {gate['pearson_limit']:.2f}). {implication}

## Scores regionais

| ROI | Concentração, µM | Publicado | Reproduzido | Erro absoluto |
|---:|---:|---:|---:|---:|
{rows}

## Diagnósticos

- Spearman reproduzido versus publicado: {metrics['spearman_vs_published']:.6f}
- AUC regional reproduzida no limiar ≥ 5 µM: {metrics['region_auc']:.6f}
- Spearman entre score reproduzido e concentração: {metrics['spearman_vs_concentration']:.6f}
- Contraste médio positivo menos negativo: {metrics['positive_negative_contrast']:.6f}
- Clusters iniciais, retidos e finais: {payload['clusters']['initial']}, {payload['clusters']['retained']} e {payload['clusters']['final']}

## Limites de reprodução

O código oficial fixa scikit-learn 1.3.0 e SciPy 1.8.0. Essas versões não são
compatíveis com o NumPy 2 do ambiente atual. A implementação HyperMix fixa
explicitamente o comportamento histórico do MiniBatchKMeans (`n_init=3`) e
registra abaixo as versões modernas efetivamente usadas. Uma divergência não
deve ser explicada automaticamente por essa diferença sem teste adicional.

As nove caixas são unidades regionais. Não há máscara pixel a pixel nem réplica
biológica por concentração, portanto este arquivo não reporta Pd@FAR nem
intervalo de confiança populacional.

## Ambiente

- Python: {payload['environment']['python']}
- NumPy: {payload['environment']['numpy']}
- SciPy: {payload['environment']['scipy']}
- scikit-learn: {payload['environment']['scikit_learn']}
- Plataforma: {payload['environment']['platform']}
- Código oficial de referência: tag `v.1.0.0`, commit `935e501cf24e28fd77b40c9d111f8e827bd1812c`
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    parser.add_argument("--clusters", type=int, default=1000)
    args = parser.parse_args()

    import sklearn

    cube, header = open_envi_cube(args.header)
    if header.wavelengths is None:
        raise ValueError("the bioHSI header must declare wavelengths")
    reference = load_published_yf10_absorbance(header.wavelengths)
    print("[1/5] suavização espectral, janela 11", flush=True)
    smoothed = smooth_spectral_cube(cube, window_size=11)
    print("[2/5] HKM + UCLS publicado", flush=True)
    result = published_hkm_ucls(
        smoothed,
        reference,
        n_init_clusters=args.clusters,
        progress=lambda message: print(f"      {message}", flush=True),
    )
    del smoothed

    print("[3/5] agregação nas nove regiões congeladas", flush=True)
    rotated = extract_rotated_crop(result.score_map, order=1)
    reproduced = _region_scores(rotated)
    protocol = load_biohsi_54m_protocol()
    concentrations = np.asarray([roi.concentration_um for roi in protocol.rois])
    published = np.asarray([roi.published_classification_score for roi in protocol.rois])
    labels = concentrations >= protocol.positive_threshold_um
    mae = mean_absolute_error(reproduced, published)
    correlation = pearson_r(reproduced, published)
    metrics = {
        "mae": mae,
        "pearson_r": correlation,
        "spearman_vs_published": float(spearmanr(reproduced, published).statistic),
        "region_auc": roc_auc(reproduced, labels),
        "spearman_vs_concentration": float(spearmanr(reproduced, concentrations).statistic),
        "positive_negative_contrast": float(reproduced[labels].mean() - reproduced[~labels].mean()),
    }
    payload = {
        "schema_version": 1,
        "method": "published HierarchicalKMeansUnmixer plus UCLS",
        "dataset": "bioHSI rg_on_sand_induction_54m",
        "protocol": "hypermix/data/biohsi_54m_protocol.json",
        "regions": [
            {
                "index": roi.index,
                "concentration_um": roi.concentration_um,
                "published_score": roi.published_classification_score,
                "reproduced_score": float(reproduced[roi.index]),
                "absolute_error": float(abs(reproduced[roi.index] - roi.published_classification_score)),
            }
            for roi in protocol.rois
        ],
        "reproduction_metrics": metrics,
        "gate": {
            "mae_limit": MAE_LIMIT,
            "pearson_limit": PEARSON_LIMIT,
            "passed": bool(mae <= MAE_LIMIT and correlation >= PEARSON_LIMIT),
        },
        "clusters": {
            "initial": result.initial_clusters,
            "retained": result.retained_clusters,
            "final": result.final_clusters,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "platform": platform.platform(),
        },
    }

    print("[4/5] gravando resultados e figura", flush=True)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown.write_text(_markdown(payload), encoding="utf-8")
    _figure(rotated, concentrations, reproduced, published, args.figure)
    print("[5/5] concluído", flush=True)
    print(json.dumps({"gate": payload["gate"], "metrics": metrics}, indent=2), flush=True)


if __name__ == "__main__":
    main()
