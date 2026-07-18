"""Train the abundance unmixer and evaluate it on the real scenes.

    python scripts/train_unmixer.py

Detection tells you *whether* the reporter is present; unmixing tells you *how
much*. This trains a regression head (on the same scene-adaptive features) on
simulated abundance, then measures how well the predicted abundance map
correlates with the true abundance on each real scene, versus the matched
filter used as an abundance proxy. Writes results/unmix_eval.json.
"""

from __future__ import annotations

import json
import os

import numpy as np

from hypermix import (
    implant_target,
    load_mat_cube,
    reporter_library,
    simulate_scene,
    spectral_matched_filter,
)
from hypermix.detector import AbundanceUnmixer, make_training_set

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_BANDS = 200
SNR = 10.0
SEEDS = (0, 1, 2)
REAL_CUBES = ("indian_pines.mat", "salinas.mat", "paviaU.mat")


def _pearson(a, b):
    a = a.ravel().astype(np.float64)
    b = b.ravel().astype(np.float64)
    if a.std() < 1e-9 or b.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def main() -> None:
    print("Building abundance training set...")
    target200 = reporter_library(N_BANDS)["bacteriochlorophyll_a"]
    X, _, ab = make_training_set(target200, n_scenes=28, hw=96, with_abundance=True)
    print(f"  {X.shape[0]:,} pixels, mean abundance {ab.mean():.3f}")

    print("Training unmixer...")
    unmix = AbundanceUnmixer(n_features=X.shape[1], seed=0).fit(X, ab, epochs=30)
    os.makedirs(os.path.join(HERE, "models"), exist_ok=True)
    unmix.net  # noqa: B018

    results = {"target": "bacteriochlorophyll_a", "snr_db": SNR, "scenes": {}}
    print(f"\nAbundance recovery (Pearson r vs true abundance) at {SNR:.0f} dB:")
    print(f"{'scene':<16} | {'matched filter':>14} | {'unmixer':>8}")
    print("-" * 44)
    for fname in REAL_CUBES:
        path = os.path.join(HERE, "data", fname)
        if not os.path.exists(path):
            continue
        cube = load_mat_cube(path)
        target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        r_mf, r_un = [], []
        for s in SEEDS:
            rng = np.random.default_rng(4000 + s)
            scene, _, ab_gt, tgt = implant_target(cube, rng, target=target, snr_db=SNR)
            r_mf.append(_pearson(spectral_matched_filter(scene, tgt), ab_gt))
            r_un.append(_pearson(unmix.predict_map(scene, tgt), ab_gt))
        name = fname.replace(".mat", "")
        results["scenes"][name] = {"matched_filter_r": float(np.mean(r_mf)),
                                   "unmixer_r": float(np.mean(r_un))}
        print(f"{name:<16} | {np.mean(r_mf):>14.3f} | {np.mean(r_un):>8.3f}")

    out = os.path.join(HERE, "results", "unmix_eval.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults written to {out}")


if __name__ == "__main__":
    main()
