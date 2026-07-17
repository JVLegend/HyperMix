"""Train the Milestone 2 detector and benchmark it against the baselines.

    python scripts/train_detector.py

Trains purely on physics-simulated backgrounds, then evaluates on held-out
synthetic backgrounds AND the real Indian Pines cube, across an SNR sweep,
comparing the learned detector to the matched filter and ACE. Writes
results/detector_eval.json and (if a real cube is present) a figure with an
uncertainty map.
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
    simulate_scene,
    spectral_matched_filter,
)
from hypermix.detector import SpectralDetector, make_training_set

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_BANDS = 200
SNRS = (20.0, 10.0, 5.0, 0.0)
EVAL_SEEDS = (0, 1, 2)


def synthetic_bg(seed: int) -> np.ndarray:
    return simulate_scene(height=96, width=96, n_bands=N_BANDS, snr_db=40.0,
                          reporter_max_abundance=0.0, seed=seed).cube


def evaluate(detector, target, bg_fn, seed_offset=0):
    rows = []
    for snr in SNRS:
        auc = {"matched_filter": [], "ace": [], "learned": []}
        for s in EVAL_SEEDS:
            cube = bg_fn(s)
            rng = np.random.default_rng(9000 + seed_offset + s)
            scene, gt, _, tgt = implant_target(cube, rng, target=target, snr_db=snr)
            auc["matched_filter"].append(roc_auc(spectral_matched_filter(scene, tgt), gt))
            auc["ace"].append(roc_auc(ace(scene, tgt), gt))
            auc["learned"].append(roc_auc(detector.score_map(scene, tgt), gt))
        for det, vals in auc.items():
            rows.append({"detector": det, "snr_db": snr,
                         "auc_mean": float(np.mean(vals)),
                         "auc_std": float(np.std(vals))})
    return rows


def main() -> None:
    target = reporter_library(N_BANDS)["bacteriochlorophyll_a"]

    print("Building training set from simulated backgrounds...")
    X, y = make_training_set(target, n_scenes=28, hw=96)
    print(f"  {X.shape[0]:,} pixels, {int(y.sum()):,} positive, {X.shape[1]} features")

    print("Training detector...")
    det = SpectralDetector(n_features=X.shape[1], seed=0)
    det.fit(X, y, epochs=30, verbose=False)

    models = os.path.join(HERE, "models")
    os.makedirs(models, exist_ok=True)
    det.save(os.path.join(models, "detector.pt"))

    results = {"target": "bacteriochlorophyll_a", "n_bands": N_BANDS}
    print("\nEvaluating on held-out SYNTHETIC backgrounds...")
    results["synthetic"] = evaluate(det, target, synthetic_bg, seed_offset=500)

    real_path = os.path.join(HERE, "data", "indian_pines.mat")
    if os.path.exists(real_path):
        cube = load_mat_cube(real_path)
        print("Evaluating on REAL Indian Pines background...")
        results["real"] = evaluate(det, target, lambda s: cube, seed_offset=0)
        _figure(det, target, cube)

    _print(results)
    out = os.path.join(HERE, "results", "detector_eval.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults written to {out}")


def _print(results: dict) -> None:
    for split in ("synthetic", "real"):
        if split not in results:
            continue
        print(f"\n=== {split.upper()} background ===")
        print(f"{'SNR':>5} | {'matched_filter':>14} | {'ace':>8} | {'learned':>8} | best")
        print("-" * 56)
        by_snr = {}
        for r in results[split]:
            by_snr.setdefault(r["snr_db"], {})[r["detector"]] = r["auc_mean"]
        for snr in sorted(by_snr, reverse=True):
            d = by_snr[snr]
            best = max(d, key=d.get)
            print(f"{snr:>5.0f} | {d['matched_filter']:>14.3f} | {d['ace']:>8.3f} "
                  f"| {d['learned']:>8.3f} | {best}")


def _figure(det, target, cube) -> None:
    rng = np.random.default_rng(0)
    scene, gt, _, tgt = implant_target(cube, rng, target=target, snr_db=5.0)
    mf = spectral_matched_filter(scene, tgt)
    mean, std = det.score_map(scene, tgt, mc=25)
    auc_mf = roc_auc(mf, gt)
    auc_le = roc_auc(mean, gt)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 4, figsize=(16, 4))
        ax[0].imshow(gt, cmap="magma"); ax[0].set_title("Ground truth")
        ax[1].imshow(mf, cmap="magma"); ax[1].set_title(f"Matched filter (AUC {auc_mf:.3f})")
        ax[2].imshow(mean, cmap="magma"); ax[2].set_title(f"Learned detector (AUC {auc_le:.3f})")
        im = ax[3].imshow(std, cmap="viridis"); ax[3].set_title("Uncertainty (MC-dropout std)")
        for a in ax:
            a.axis("off")
        fig.colorbar(im, ax=ax[3], fraction=0.046)
        fig.tight_layout()
        out = os.path.join(HERE, "assets", "detector_real.png")
        fig.savefig(out, dpi=130)
        print(f"Figure saved to {out}")
    except Exception as exc:  # noqa: BLE001
        print(f"(Plot skipped: {exc})")


if __name__ == "__main__":
    main()
