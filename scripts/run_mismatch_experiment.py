"""Measure detection robustness when the assumed target spectrum is shifted.

The implanted target remains the unmodified bacteriochlorophyll-a signature.
Only the signature supplied to each detector is shifted. This isolates oracle
target sensitivity while keeping scenes, seeds, abundance maps and noise fixed.

    python scripts/run_mismatch_experiment.py

Requires ``models/detector.pt`` from ``python scripts/train_detector.py``.
Writes ``results/mismatch.json`` and ``results/mismatch.md``.
"""

from __future__ import annotations

import json
import os

import numpy as np

from hypermix import (
    implant_target,
    load_mat_cube,
    reporter_library,
    roc_auc,
    smoothed_matched_filter,
    spectral_matched_filter,
)
from hypermix.detector import SpectralDetector
from hypermix.mismatch import shift_spectrum

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_SNR_DB = 5.0
SHIFT_FRACTIONS = (0.0, 0.01, 0.025, 0.05)
SEEDS = (0, 1, 2)
REAL_CUBES = ("indian_pines.mat", "salinas.mat", "paviaU.mat")
PRETTY = {
    "matched_filter": "Matched filter",
    "matched_filter_spatial": "Matched filter (spatial)",
    "learned": "Detector aprendido (HyperMix)",
}


def _evaluate(detector: SpectralDetector) -> tuple[list[dict], list[dict]]:
    rows = []
    pooled: dict[tuple[str, float], list[float]] = {}
    for fname in REAL_CUBES:
        path = os.path.join(HERE, "data", fname)
        if not os.path.exists(path):
            continue
        name = fname.removesuffix(".mat")
        cube = load_mat_cube(path)
        true_target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        for shift in SHIFT_FRACTIONS:
            aucs = {method: [] for method in PRETTY}
            for seed in SEEDS:
                scene, gt, _, planted_target = implant_target(
                    cube,
                    np.random.default_rng(9000 + seed),
                    target=true_target,
                    snr_db=TARGET_SNR_DB,
                )
                assumed_target = shift_spectrum(planted_target, shift)
                scores = {
                    "matched_filter": spectral_matched_filter(scene, assumed_target),
                    "matched_filter_spatial": smoothed_matched_filter(
                        scene, assumed_target
                    ),
                    "learned": detector.score_map(scene, assumed_target),
                }
                for method, score in scores.items():
                    value = roc_auc(score, gt)
                    aucs[method].append(value)
                    pooled.setdefault((method, shift), []).append(value)
            for method, values in aucs.items():
                rows.append(
                    {
                        "scene": name,
                        "detector": method,
                        "shift_fraction": shift,
                        "target_snr_db": TARGET_SNR_DB,
                        "auc_mean": float(np.mean(values)),
                        "auc_std": float(np.std(values)),
                    }
                )

    summary = []
    for method in PRETTY:
        exact = float(np.mean(pooled[(method, 0.0)]))
        for shift in SHIFT_FRACTIONS:
            mean = float(np.mean(pooled[(method, shift)]))
            summary.append(
                {
                    "detector": method,
                    "shift_fraction": shift,
                    "auc_mean": mean,
                    "auc_drop": exact - mean,
                }
            )
    return rows, summary


def _markdown(summary: list[dict]) -> str:
    lookup = {
        (row["detector"], row["shift_fraction"]): row for row in summary
    }
    lines = [
        "# Robustez a mismatch espectral",
        "",
        "A assinatura implantada é mantida fixa. Apenas a assinatura fornecida ao",
        "detector é deslocada no eixo normalizado de índices de bandas. Resultados",
        f"com target SNR de {TARGET_SNR_DB:.0f} dB, 3 cenas reais e 3 seeds por cena.",
        "A queda de AUC é relativa ao alvo exato do mesmo método.",
        "",
        "| Método | Deslocamento | AUC média | Queda de AUC |",
        "|--------|-------------:|:---------:|:------------:|",
    ]
    for shift in SHIFT_FRACTIONS:
        for method, pretty in PRETTY.items():
            row = lookup[(method, shift)]
            lines.append(
                f"| {pretty} | {100 * shift:.1f}% | {row['auc_mean']:.3f} | "
                f"{row['auc_drop']:.3f} |"
            )
    lines += [
        "",
        "O deslocamento é expresso como fração da faixa de índices, não em",
        "nanômetros, porque os cubos não compartilham a mesma grade espectral.",
        "Reproduza com `python scripts/run_mismatch_experiment.py`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    model_path = os.path.join(HERE, "models", "detector.pt")
    if not os.path.exists(model_path):
        raise SystemExit("Run scripts/train_detector.py first.")
    detector = SpectralDetector(n_features=5, seed=0).load(model_path)
    rows, summary = _evaluate(detector)
    payload = {
        "target": "bacteriochlorophyll_a",
        "target_snr_db": TARGET_SNR_DB,
        "seeds": list(SEEDS),
        "shift_fractions": list(SHIFT_FRACTIONS),
        "rows": rows,
        "summary": summary,
    }
    results_dir = os.path.join(HERE, "results")
    os.makedirs(results_dir, exist_ok=True)
    with open(os.path.join(results_dir, "mismatch.json"), "w") as fh:
        json.dump(payload, fh, indent=2)
    report = _markdown(summary)
    with open(os.path.join(results_dir, "mismatch.md"), "w") as fh:
        fh.write(report)
    print(report)


if __name__ == "__main__":
    main()
