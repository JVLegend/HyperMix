"""Build the HyperMix detection leaderboard.

    python scripts/make_leaderboard.py

Runs the classical baselines on the real Indian Pines implanted-target
benchmark, folds in the learned detector's numbers from
results/detector_eval.json (if present), ranks everyone by mean AUC, and
writes results/leaderboard.md.
"""

from __future__ import annotations

import json
import os

import numpy as np

from hypermix import (
    ace,
    implant_target,
    load_mat_cube,
    reporter_library,
    roc_auc,
    spectral_angle_mapper,
    spectral_matched_filter,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNRS = (20.0, 10.0, 5.0, 0.0)
SEEDS = (0, 1, 2)
CLASSICAL = {
    "Matched filter": spectral_matched_filter,
    "ACE": ace,
    "Spectral Angle Mapper": spectral_angle_mapper,
}


def _eval_real(fn, cube, target):
    per_snr = {}
    for snr in SNRS:
        aucs = []
        for s in SEEDS:
            rng = np.random.default_rng(9000 + s)
            scene, gt, _, tgt = implant_target(cube, rng, target=target, snr_db=snr)
            aucs.append(roc_auc(fn(scene, tgt), gt))
        per_snr[snr] = float(np.mean(aucs))
    return per_snr


def main() -> None:
    real_path = os.path.join(HERE, "data", "indian_pines.mat")
    if not os.path.exists(real_path):
        raise SystemExit("Real cube missing. Run: python scripts/fetch_data.py")
    cube = load_mat_cube(real_path)
    target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]

    board = []  # (name, mean_auc, auc0, learned?)
    for name, fn in CLASSICAL.items():
        per = _eval_real(fn, cube, target)
        board.append((name, float(np.mean(list(per.values()))), per[0.0], False))

    # Fold in the learned detector from its saved evaluation.
    eval_path = os.path.join(HERE, "results", "detector_eval.json")
    if os.path.exists(eval_path):
        data = json.load(open(eval_path))
        real = [r for r in data.get("real", []) if r["detector"] == "learned"]
        if real:
            by_snr = {r["snr_db"]: r["auc_mean"] for r in real}
            mean = float(np.mean([by_snr[s] for s in SNRS if s in by_snr]))
            board.append(("Learned detector (HyperMix)", mean,
                          by_snr.get(0.0, float("nan")), True))

    board.sort(key=lambda r: r[1], reverse=True)

    lines = [
        "# HyperMix detection leaderboard",
        "",
        "Detection AUC on the **real Indian Pines** background (AVIRIS) with an",
        "implanted bacteriochlorophyll-a target, averaged over 3 seeds.",
        "`Mean AUC` averages over SNR = 20, 10, 5, 0 dB; `AUC @ 0 dB` is the",
        "hardest, low-SNR case. Reproduce with `python scripts/make_leaderboard.py`.",
        "",
        "| Rank | Method | Mean AUC | AUC @ 0 dB |",
        "|-----:|--------|:--------:|:----------:|",
    ]
    for i, (name, mean, auc0, learned) in enumerate(board, 1):
        star = " 🧠" if learned else ""
        lines.append(f"| {i} | {name}{star} | {mean:.3f} | {auc0:.3f} |")
    lines.append("")

    out = os.path.join(HERE, "results", "leaderboard.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
