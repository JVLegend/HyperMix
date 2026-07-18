"""Build the HyperMix detection leaderboard across all real scenes.

    python scripts/make_leaderboard.py

Reads matched-filter / ACE / learned results from results/detector_eval.json
(one entry per real scene), computes the Spectral Angle Mapper baseline fresh,
aggregates across every real cube in ./data and the SNR sweep, and writes a
ranked results/leaderboard.md with a per-scene breakdown.
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
    spectral_angle_mapper,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNRS = (20.0, 10.0, 5.0, 0.0)
SEEDS = (0, 1, 2)
PRETTY = {
    "matched_filter": "Matched filter",
    "matched_filter_spatial": "Matched filter (spatial)",
    "ace": "ACE",
    "spectral_angle_mapper": "Spectral Angle Mapper",
    "learned": "Learned detector (HyperMix)",
}


def _fresh_rows(cube, target, detector):
    out = {}
    for snr in SNRS:
        aucs = []
        for s in SEEDS:
            rng = np.random.default_rng(9000 + s)
            scene, gt, _, tgt = implant_target(cube, rng, target=target, snr_db=snr)
            aucs.append(roc_auc(detector(scene, tgt), gt))
        out[snr] = float(np.mean(aucs))
    return out


def main() -> None:
    eval_path = os.path.join(HERE, "results", "detector_eval.json")
    if not os.path.exists(eval_path):
        raise SystemExit("Run scripts/train_detector.py first.")
    data = json.load(open(eval_path))
    scenes = data.get("scenes", {})
    if not scenes:
        raise SystemExit("No real scenes in detector_eval.json.")

    # method -> scene -> {snr: auc}
    per = {m: {} for m in PRETTY}
    for name, rows in scenes.items():
        for r in rows:
            per[r["detector"]].setdefault(name, {})[r["snr_db"]] = r["auc_mean"]
        cube = load_mat_cube(os.path.join(HERE, "data", f"{name}.mat"))
        target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        per["spectral_angle_mapper"][name] = _fresh_rows(
            cube, target, spectral_angle_mapper
        )
        per["matched_filter_spatial"][name] = _fresh_rows(
            cube, target, smoothed_matched_filter
        )

    scene_names = list(scenes)

    def mean_all(method):
        vals = [per[method][s][snr] for s in scene_names for snr in SNRS]
        return float(np.mean(vals))

    def mean_at0(method):
        return float(np.mean([per[method][s][0.0] for s in scene_names]))

    board = sorted(PRETTY, key=mean_all, reverse=True)

    lines = [
        "# HyperMix detection leaderboard",
        "",
        f"Detection AUC across **{len(scene_names)} real hyperspectral scenes** "
        f"({', '.join(scene_names)}) with an implanted bacteriochlorophyll-a target,",
        "averaged over 3 seeds. Different sensors and band counts. The spatial matched",
        "filter applies a fixed Gaussian blur with sigma = 1.5 pixels. `Mean AUC` averages",
        "over all scenes and SNR = 20, 10, 5, 0 dB. The learned detector is trained",
        "**only on simulation**. Reproduce: `python scripts/make_leaderboard.py`.",
        "",
        "| Rank | Method | Mean AUC | AUC @ 0 dB |",
        "|-----:|--------|:--------:|:----------:|",
    ]
    for i, m in enumerate(board, 1):
        star = " 🧠" if m == "learned" else ""
        lines.append(f"| {i} | {PRETTY[m]}{star} | {mean_all(m):.3f} | {mean_at0(m):.3f} |")

    lines += ["", "## Per-scene AUC @ 0 dB (hardest case)", "",
              "| Method | " + " | ".join(scene_names) + " |",
              "|--------|" + "|".join([":---:"] * len(scene_names)) + "|"]
    for m in board:
        cells = " | ".join(f"{per[m][s][0.0]:.3f}" for s in scene_names)
        star = " 🧠" if m == "learned" else ""
        lines.append(f"| {PRETTY[m]}{star} | {cells} |")
    lines.append("")

    out = os.path.join(HERE, "results", "leaderboard.md")
    with open(out, "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
