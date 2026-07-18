"""Reproducible detection benchmark: baselines vs SNR, synthetic and real.

Runs every baseline over an SNR sweep and multiple seeds on:
  - fully synthetic scenes (hypermix.simulate), and
  - a real background cube with an implanted target (hypermix.datasets),

logging mean/std AUC to a JSON results table. Run:

    python -m hypermix.benchmark
"""

from __future__ import annotations

import json
import os

import numpy as np

from .baselines import ace, smoothed_matched_filter, spectral_matched_filter
from .datasets import implant_target, load_mat_cube
from .metrics import roc_auc
from .simulate import false_color, simulate_scene

SNRS = (30.0, 20.0, 10.0, 5.0, 0.0)
DETECTORS = {
    "matched_filter": spectral_matched_filter,
    "matched_filter_spatial": smoothed_matched_filter,
    "ace": ace,
}


def run_synthetic(seeds=(0, 1, 2), snrs=SNRS) -> list[dict]:
    rows = []
    for snr in snrs:
        for name, fn in DETECTORS.items():
            aucs = []
            for s in seeds:
                sc = simulate_scene(snr_db=snr, seed=s)
                aucs.append(roc_auc(fn(sc.cube, sc.reporter), sc.detection_gt))
            rows.append({"dataset": "synthetic", "detector": name,
                         "target_snr_db": snr,
                         "auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs))})
    return rows


def run_real(cube_path: str, seeds=(0, 1, 2), snrs=SNRS) -> list[dict]:
    cube = load_mat_cube(cube_path)
    rows = []
    for snr in snrs:
        for name, fn in DETECTORS.items():
            aucs = []
            for s in seeds:
                rng = np.random.default_rng(s)
                scene, gt, _, tgt = implant_target(cube, rng, snr_db=snr)
                aucs.append(roc_auc(fn(scene, tgt), gt))
            rows.append({"dataset": "indian_pines (real bg)", "detector": name,
                         "target_snr_db": snr, "auc_mean": float(np.mean(aucs)),
                         "auc_std": float(np.std(aucs))})
    return rows


def _print_table(rows: list[dict]) -> None:
    print(f"{'dataset':<24} {'detector':<24} {'target SNR':>10} {'AUC':>7} {'±std':>6}")
    print("-" * 70)
    for r in rows:
        print(f"{r['dataset']:<24} {r['detector']:<24} {r['target_snr_db']:>10.0f} "
              f"{r['auc_mean']:>7.3f} {r['auc_std']:>6.3f}")


def _figure_real(cube_path: str, out: str) -> None:
    cube = load_mat_cube(cube_path)
    rng = np.random.default_rng(0)
    scene, gt, _, tgt = implant_target(cube, rng, snr_db=5.0)
    score = spectral_matched_filter(scene, tgt)
    auc = roc_auc(score, gt)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 3, figsize=(12, 4))
        ax[0].imshow(false_color(scene)); ax[0].set_title("Real background + implanted target (target SNR 5 dB)")
        ax[1].imshow(gt, cmap="magma"); ax[1].set_title("Ground truth")
        im = ax[2].imshow(score, cmap="magma"); ax[2].set_title(f"Matched filter (AUC {auc:.3f})")
        for a in ax:
            a.axis("off")
        fig.colorbar(im, ax=ax[2], fraction=0.046)
        fig.tight_layout(); fig.savefig(out, dpi=130)
        print(f"Figure saved to {out}")
    except Exception as exc:  # noqa: BLE001
        print(f"(Plot skipped: {exc})")


def main() -> None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(here, "results")
    assets = os.path.join(here, "assets")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(assets, exist_ok=True)

    rows = run_synthetic()
    cube_path = os.path.join(here, "data", "indian_pines.mat")
    if os.path.exists(cube_path):
        rows += run_real(cube_path)
        _figure_real(cube_path, os.path.join(assets, "benchmark_real.png"))
    else:
        print(f"(Real cube not found at {cube_path}; run scripts/fetch_data.py. "
              "Synthetic-only benchmark below.)")

    _print_table(rows)
    with open(os.path.join(results_dir, "benchmark.json"), "w") as fh:
        json.dump(rows, fh, indent=2)
    print(f"\nResults written to {os.path.join(results_dir, 'benchmark.json')}")


if __name__ == "__main__":
    main()
