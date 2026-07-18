"""Train the abundance unmixer and evaluate it on the real scenes.

    python scripts/train_unmixer.py

Detection tells you *whether* the reporter is present; unmixing tells you *how
much*. This trains a regression head (on the same scene-adaptive features) on
simulated abundance, then reports target-pixel Pearson correlation and target
MAE on each real scene, versus the matched filter used as an abundance proxy.
All-pixel MAE is retained as a secondary background-error diagnostic. Writes
results/unmix_eval.json and results/unmix_eval.md.
"""

from __future__ import annotations

import json
import os

import numpy as np

from hypermix import (
    implant_target,
    load_mat_cube,
    mean_absolute_error,
    pearson_r,
    reporter_library,
    simulate_scene,
    spectral_matched_filter,
)
from hypermix.detector import AbundanceUnmixer, make_training_set

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_BANDS = 200
SNR = 10.0
TARGET_THRESHOLD = 0.02
SEEDS = (0, 1, 2)
REAL_CUBES = ("indian_pines.mat", "salinas.mat", "paviaU.mat")


def _abundance_metrics(predicted, truth, target_mask):
    predicted = np.clip(predicted, 0.0, 1.0)
    return {
        "target_pearson_r": pearson_r(predicted, truth, mask=target_mask),
        "target_mae": mean_absolute_error(predicted, truth, mask=target_mask),
        "all_pixel_mae": mean_absolute_error(predicted, truth),
    }


def main() -> None:
    print("Building abundance training set...")
    target200 = reporter_library(N_BANDS)["bacteriochlorophyll_a"]
    X, _, ab = make_training_set(target200, n_scenes=28, hw=96, with_abundance=True)
    print(f"  {X.shape[0]:,} pixels, mean abundance {ab.mean():.3f}")

    print("Training unmixer...")
    unmix = AbundanceUnmixer(n_features=X.shape[1], seed=0).fit(X, ab, epochs=30)
    os.makedirs(os.path.join(HERE, "models"), exist_ok=True)
    unmix.net  # noqa: B018

    results = {
        "target": "bacteriochlorophyll_a",
        "target_snr_db": SNR,
        "target_threshold": TARGET_THRESHOLD,
        "scenes": {},
    }
    print(f"\nAbundance recovery at target SNR {SNR:.0f} dB:")
    print(f"{'scene':<16} | {'MF target r':>11} | {'unmix r':>8} | "
          f"{'MF target MAE':>13} | {'unmix MAE':>10}")
    print("-" * 70)
    for fname in REAL_CUBES:
        path = os.path.join(HERE, "data", fname)
        if not os.path.exists(path):
            continue
        cube = load_mat_cube(path)
        target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        values = {"matched_filter": [], "unmixer": []}
        for s in SEEDS:
            rng = np.random.default_rng(4000 + s)
            scene, _, ab_gt, tgt = implant_target(
                cube,
                rng,
                target=target,
                snr_db=SNR,
                detection_threshold=TARGET_THRESHOLD,
            )
            target_mask = ab_gt > TARGET_THRESHOLD
            values["matched_filter"].append(
                _abundance_metrics(
                    spectral_matched_filter(scene, tgt), ab_gt, target_mask
                )
            )
            values["unmixer"].append(
                _abundance_metrics(unmix.predict_map(scene, tgt), ab_gt, target_mask)
            )
        name = fname.replace(".mat", "")
        results["scenes"][name] = {
            method: {
                metric: float(np.mean([row[metric] for row in rows]))
                for metric in rows[0]
            }
            for method, rows in values.items()
        }
        mf = results["scenes"][name]["matched_filter"]
        learned = results["scenes"][name]["unmixer"]
        print(f"{name:<16} | {mf['target_pearson_r']:>11.3f} | "
              f"{learned['target_pearson_r']:>8.3f} | {mf['target_mae']:>13.4f} | "
              f"{learned['target_mae']:>10.4f}")

    out = os.path.join(HERE, "results", "unmix_eval.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    report = _markdown(results)
    report_path = os.path.join(HERE, "results", "unmix_eval.md")
    with open(report_path, "w") as fh:
        fh.write(report)
    print(f"\nResults written to {out} and {report_path}")


def _markdown(results):
    lines = [
        "# Avaliação de abundância",
        "",
        f"Target SNR de {results['target_snr_db']:.0f} dB, média de 3 seeds. "
        f"Pixels de alvo usam abundância > {results['target_threshold']:.2f}.",
        "Predições são limitadas ao intervalo físico [0, 1] antes da MAE.",
        "",
        "| Cena | MF target r | Unmixer target r | MF target MAE | Unmixer target MAE | Unmixer MAE, todos os pixels |",
        "|------|:-----------:|:----------------:|:-------------:|:------------------:|:-----------------------------:|",
    ]
    for scene, methods in results["scenes"].items():
        mf, unmix = methods["matched_filter"], methods["unmixer"]
        lines.append(
            f"| {scene} | {mf['target_pearson_r']:.3f} | "
            f"{unmix['target_pearson_r']:.3f} | {mf['target_mae']:.4f} | "
            f"{unmix['target_mae']:.4f} | {unmix['all_pixel_mae']:.4f} |"
        )
    lines += [
        "",
        "Pearson r e target MAE excluem os zeros de fundo. A MAE em todos os pixels",
        "é apresentada apenas como diagnóstico secundário.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
