"""Does the learned detector earn its keep under non-linear mixing?

    python scripts/nonlinear_experiment.py

The matched filter assumes linear additive mixing. Under a two-endmember
generalized bilinear model that assumption breaks, so this is the regime where a learned detector,
trained in-domain, could beat the fair spatial matched-filter baseline. For
each mixing model we train the detector on that model and compare, on the real
scenes, the learned detector to the spatial matched filter. Honest either way:
if the learned detector still does not separate, the value is the open
benchmark, not the detector. Writes results/nonlinear.json and .md.
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
)
from hypermix.detector import SpectralDetector, make_training_set

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_BANDS = 200
SNRS = (5.0, 0.0)
SEEDS = (0, 1, 2)
REAL_CUBES = ("indian_pines.mat", "salinas.mat", "paviaU.mat")
MIXINGS = ("linear", "bilinear")


def _eval(detector, cubes, mixing):
    mf, learned = [], []
    for cube, target in cubes:
        for snr in SNRS:
            for s in SEEDS:
                rng = np.random.default_rng(9000 + s)
                scene, gt, _, tgt = implant_target(
                    cube, rng, target=target, snr_db=snr, mixing=mixing)
                mf.append(roc_auc(smoothed_matched_filter(scene, tgt), gt))
                learned.append(roc_auc(detector.score_map(scene, tgt), gt))
    return float(np.mean(mf)), float(np.mean(learned))


def main() -> None:
    cubes = []
    for fname in REAL_CUBES:
        path = os.path.join(HERE, "data", fname)
        if os.path.exists(path):
            cube = load_mat_cube(path)
            target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
            cubes.append((cube, target))
    if not cubes:
        raise SystemExit("No real cubes. Run scripts/fetch_data.py")

    target200 = reporter_library(N_BANDS)["bacteriochlorophyll_a"]
    results = {}
    print(f"{'mixing':<10} | {'spatial MF':>11} | {'learned':>8} | winner")
    print("-" * 46)
    for mixing in MIXINGS:
        X, y = make_training_set(target200, n_scenes=28, hw=96, mixing=mixing)
        det = SpectralDetector(n_features=X.shape[1], seed=0).fit(X, y, epochs=30)
        mf_auc, learned_auc = _eval(det, cubes, mixing)
        winner = "learned" if learned_auc > mf_auc + 0.005 else (
            "spatial MF" if mf_auc > learned_auc + 0.005 else "tie")
        results[mixing] = {"spatial_mf": mf_auc, "learned": learned_auc,
                           "winner": winner}
        print(f"{mixing:<10} | {mf_auc:>11.3f} | {learned_auc:>8.3f} | {winner}")

    out = os.path.join(HERE, "results", "nonlinear.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)

    lines = [
        "# Detector aprendido vs matched filter espacial sob mistura não-linear",
        "",
        "AUC de detecção média em 3 cenas reais, target SNR de 5 e 0 dB, 3 seeds.",
        "O detector é treinado no mesmo modelo de mistura em que é avaliado.",
        "A mistura bilinear usa gamma = 0,5. Os arquivos MAT não contêm centros de",
        "banda, então este teste mantém o alvo aproximado por índice espectral e não",
        "é o benchmark calibrado em comprimento de onda de `realism.md`.",
        "",
        "| Mistura | MF espacial | Detector aprendido | Vencedor |",
        "|---------|:-----------:|:------------------:|----------|",
    ]
    for mixing, r in results.items():
        lines.append(f"| {mixing} | {r['spatial_mf']:.3f} | "
                     f"{r['learned']:.3f} | {r['winner']} |")
    lines.append("")
    with open(os.path.join(HERE, "results", "nonlinear.md"), "w") as fh:
        fh.write("\n".join(lines))
    print(f"\nWrote {out} and results/nonlinear.md")


if __name__ == "__main__":
    main()
