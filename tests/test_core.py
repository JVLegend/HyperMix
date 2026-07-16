"""Smoke tests for HyperMix Phase 0."""

import numpy as np

from hypermix import (
    reporter_signature,
    roc_auc,
    simulate_scene,
    spectral_matched_filter,
)


def test_scene_shapes_and_determinism():
    a = simulate_scene(height=48, width=48, n_bands=40, seed=1)
    b = simulate_scene(height=48, width=48, n_bands=40, seed=1)
    assert a.cube.shape == (48, 48, 40)
    assert a.detection_gt.shape == (48, 48)
    assert np.array_equal(a.cube, b.cube)          # deterministic given seed
    assert a.detection_gt.any()                    # some reporter present
    assert not a.detection_gt.all()                # and some background


def test_reporter_has_localized_feature():
    r = reporter_signature(n_bands=60)
    assert r.shape == (60,)
    # the absorption dip means the min is well below the median
    assert r.min() < np.median(r) - 0.1


def test_matched_filter_separates_at_high_snr():
    scene = simulate_scene(snr_db=30.0, seed=0)
    score = spectral_matched_filter(scene.cube, scene.reporter)
    auc = roc_auc(score, scene.detection_gt)
    assert auc > 0.85, f"expected strong detection at high SNR, got AUC={auc:.3f}"


def test_auc_bounds_and_degradation():
    hi = simulate_scene(snr_db=30.0, seed=2)
    lo = simulate_scene(snr_db=0.0, seed=2)
    auc_hi = roc_auc(spectral_matched_filter(hi.cube, hi.reporter), hi.detection_gt)
    auc_lo = roc_auc(spectral_matched_filter(lo.cube, lo.reporter), lo.detection_gt)
    assert 0.0 <= auc_lo <= 1.0 and 0.0 <= auc_hi <= 1.0
    assert auc_hi >= auc_lo   # detection should not improve as SNR drops
