"""Phase 0 demo: simulate scenes, run the matched-filter baseline, report AUC.

    python examples/run_demo.py

Prints detection AUC as SNR degrades and saves a figure to assets/.
"""

from __future__ import annotations

import os

import numpy as np

from hypermix import (
    false_color,
    roc_auc,
    simulate_scene,
    spectral_matched_filter,
)


def main() -> None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(here, "assets")
    os.makedirs(assets, exist_ok=True)

    print("HyperMix Phase 0 - matched-filter detection vs target SNR")
    print(f"{'target SNR (dB)':>15} | {'AUC':>6}")
    print("-" * 20)
    for snr in (30.0, 20.0, 10.0, 5.0, 0.0):
        scene = simulate_scene(snr_db=snr, seed=0)
        score = spectral_matched_filter(scene.cube, scene.reporter)
        auc = roc_auc(score, scene.detection_gt)
        print(f"{snr:>15.0f} | {auc:>6.3f}")

    # Figure at a deliberately hard SNR.
    scene = simulate_scene(snr_db=5.0, seed=0)
    score = spectral_matched_filter(scene.cube, scene.reporter)
    auc = roc_auc(score, scene.detection_gt)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 3, figsize=(12, 4))
        ax[0].imshow(false_color(scene.cube))
        ax[0].set_title(f"Simulated cube (target SNR {scene.snr_db:.0f} dB)")
        ax[1].imshow(scene.detection_gt, cmap="magma")
        ax[1].set_title("Ground truth: reporter present")
        im = ax[2].imshow(score, cmap="magma")
        ax[2].set_title(f"Matched filter (AUC {auc:.3f})")
        for a in ax:
            a.axis("off")
        fig.colorbar(im, ax=ax[2], fraction=0.046)
        fig.tight_layout()
        out = os.path.join(assets, "demo_detection.png")
        fig.savefig(out, dpi=130)
        print(f"\nFigure saved to {out}")
    except Exception as exc:  # noqa: BLE001
        print(f"\n(Plot skipped: {exc})")


if __name__ == "__main__":
    main()
