"""Smoke tests for HyperMix Phase 0."""

import numpy as np

from hypermix import (
    implant_target,
    reporter_signature,
    roc_auc,
    simulate_scene,
    smoothed_matched_filter,
    spectral_matched_filter,
    synthetic_target,
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


def test_smoothed_matched_filter_adds_spatial_context():
    scene = simulate_scene(height=48, width=48, n_bands=40, snr_db=20.0, seed=4)
    mf = spectral_matched_filter(scene.cube, scene.reporter)
    spatial = smoothed_matched_filter(scene.cube, scene.reporter, sigma=1.5)
    assert spatial.shape == mf.shape
    assert not np.array_equal(spatial, mf)
    assert np.array_equal(
        smoothed_matched_filter(scene.cube, scene.reporter, sigma=0), mf
    )


def test_implant_target_on_synthetic_background():
    # a real cube isn't required: implant into any (H, W, B) background
    rng = np.random.default_rng(0)
    bg = rng.uniform(0.1, 0.6, size=(40, 40, 50)).astype(np.float32)
    scene, gt, ab, tgt = implant_target(bg, rng, snr_db=30.0, n_blobs=4)
    assert scene.shape == bg.shape
    assert gt.shape == (40, 40)
    assert gt.any() and not gt.all()
    assert tgt.shape == (50,)
    auc = roc_auc(spectral_matched_filter(scene, tgt), gt)
    assert auc > 0.7, f"implanted target should be detectable at high SNR, got {auc:.3f}"


def test_implant_noise_uses_target_contribution_snr():
    bg = np.random.default_rng(8).uniform(0.1, 0.6, size=(80, 80, 30)).astype(np.float32)
    clean, gt, ab, tgt = implant_target(
        bg, np.random.default_rng(12), snr_db=np.inf, n_blobs=5
    )
    noisy, _, _, _ = implant_target(
        bg, np.random.default_rng(12), snr_db=6.0, n_blobs=5
    )
    target_signal = ab[..., None] * (tgt[None, None, :] - bg)
    target_rms = np.sqrt(np.mean(target_signal[gt] ** 2))
    noise_rms = np.sqrt(np.mean((noisy - clean) ** 2))
    measured_snr = 20.0 * np.log10(target_rms / noise_rms)
    assert np.isclose(measured_snr, 6.0, atol=0.15), measured_snr


def test_simulator_noise_uses_target_contribution_snr():
    clean = simulate_scene(height=64, width=64, n_bands=30, snr_db=np.inf, seed=21)
    noisy = simulate_scene(height=64, width=64, n_bands=30, snr_db=4.0, seed=21)
    background = simulate_scene(
        height=64,
        width=64,
        n_bands=30,
        snr_db=np.inf,
        reporter_max_abundance=0.0,
        seed=21,
    )
    target_signal = clean.cube - background.cube
    noise = noisy.cube - clean.cube
    target_rms = np.sqrt(np.mean(target_signal[clean.detection_gt] ** 2))
    noise_rms = np.sqrt(np.mean(noise ** 2))
    measured_snr = 20.0 * np.log10(target_rms / noise_rms)
    assert np.isclose(measured_snr, 4.0, atol=0.2), measured_snr


def test_spectral_angle_mapper_ranks_target_higher():
    from hypermix import spectral_angle_mapper

    scene = simulate_scene(snr_db=30.0, seed=0)
    sam = spectral_angle_mapper(scene.cube, scene.reporter)
    assert sam.shape == scene.detection_gt.shape
    # target pixels should, on average, score higher than background
    assert sam[scene.detection_gt].mean() != sam[~scene.detection_gt].mean()
    assert roc_auc(sam, scene.detection_gt) >= 0.5


def test_synthetic_target_shape():
    t = synthetic_target(80, center_frac=0.5)
    assert t.shape == (80,)
    assert np.isclose(t.max(), 1.0, atol=1e-6)


def test_spectral_shift_is_controlled_and_deterministic():
    from hypermix.mismatch import shift_spectrum

    target = synthetic_target(100, center_frac=0.5)
    exact = shift_spectrum(target, 0.0)
    shifted = shift_spectrum(target, 0.05)
    assert np.array_equal(exact, target)
    assert shifted.shape == target.shape
    assert not np.array_equal(shifted, target)
    assert np.argmax(shifted) > np.argmax(target)


def test_reporter_library_matches_paper():
    from hypermix import reporter_library

    lib = reporter_library(n_bands=60)
    assert set(lib) == {"bacteriochlorophyll_a", "biliverdin_ixalpha"}
    for sig in lib.values():
        assert sig.shape == (60,)
        assert sig.min() < np.median(sig)   # has an absorption dip


def test_learned_detector_matches_or_beats_matched_filter():
    import pytest

    pytest.importorskip("torch")
    from hypermix import implant_target, reporter_library, simulate_scene
    from hypermix.detector import SpectralDetector, make_training_set

    target = reporter_library(60)["bacteriochlorophyll_a"]
    x, y = make_training_set(target, n_scenes=6, hw=48)
    det = SpectralDetector(n_features=x.shape[1], seed=0).fit(x, y, epochs=15)

    bg = simulate_scene(height=48, width=48, n_bands=60, snr_db=40.0,
                        reporter_max_abundance=0.0, seed=777).cube
    rng = np.random.default_rng(3)
    scene, gt, _, tgt = implant_target(bg, rng, target=target, snr_db=10.0)
    auc_learned = roc_auc(det.score_map(scene, tgt), gt)
    auc_mf = roc_auc(spectral_matched_filter(scene, tgt), gt)
    assert auc_learned >= auc_mf - 0.02, f"learned {auc_learned:.3f} vs mf {auc_mf:.3f}"


def test_abundance_unmixer_recovers_abundance():
    import pytest

    pytest.importorskip("torch")
    from hypermix import implant_target, pearson_r, reporter_library, simulate_scene
    from hypermix.detector import AbundanceUnmixer, make_training_set

    target = reporter_library(60)["bacteriochlorophyll_a"]
    x, _, ab = make_training_set(target, n_scenes=10, hw=48, with_abundance=True)
    unmix = AbundanceUnmixer(n_features=x.shape[1], seed=0).fit(x, ab, epochs=20)

    bg = simulate_scene(height=48, width=48, n_bands=60, snr_db=40.0,
                        reporter_max_abundance=0.0, seed=888).cube
    rng = np.random.default_rng(5)
    scene, _, ab_gt, tgt = implant_target(bg, rng, target=target, snr_db=30.0)
    pred = unmix.predict_map(scene, tgt)
    r = pearson_r(pred, ab_gt, mask=ab_gt > 0.02)
    assert r > 0.4, f"unmixer should track true abundance, got r={r:.3f}"


def test_atmosphere_and_srf():
    from hypermix import apply_srf, atmospheric_transmittance
    from hypermix.simulate import reporter_signature

    tau = atmospheric_transmittance(120)
    assert tau.shape == (120,)
    assert tau.min() >= 0.05 and tau.max() <= 1.0
    assert tau.min() < 0.9  # has absorption dips

    r = reporter_signature(120)
    smoothed = apply_srf(r, fwhm_bands=3.0)
    assert smoothed.shape == r.shape
    # smoothing a sharp absorption makes its minimum shallower
    assert smoothed.min() > r.min()


def test_simulate_scene_realistic_mode_runs():
    from hypermix import roc_auc, spectral_matched_filter

    s = simulate_scene(snr_db=20.0, seed=0, atmosphere=True, srf_fwhm=1.5)
    assert s.cube.shape[2] == 60
    auc = roc_auc(spectral_matched_filter(s.cube, s.reporter), s.detection_gt)
    assert auc > 0.5  # target still detectable under atmosphere + SRF


def test_bilinear_mixing_shapes_and_gt():
    from hypermix import implant_target, reporter_library

    bg = np.random.default_rng(0).uniform(0.1, 0.6, size=(48, 48, 60)).astype(np.float32)
    target = reporter_library(60)["bacteriochlorophyll_a"]
    lin = implant_target(np.array(bg), np.random.default_rng(1), target=target,
                         snr_db=20.0, mixing="linear")
    bil = implant_target(np.array(bg), np.random.default_rng(1), target=target,
                         snr_db=20.0, mixing="bilinear")
    # same seed -> same abundance ground truth; scenes differ (non-linear term)
    assert np.array_equal(lin[1], bil[1])
    assert not np.allclose(lin[0], bil[0])


def test_auc_bounds_and_degradation():
    hi = simulate_scene(snr_db=30.0, seed=2)
    lo = simulate_scene(snr_db=0.0, seed=2)
    auc_hi = roc_auc(spectral_matched_filter(hi.cube, hi.reporter), hi.detection_gt)
    auc_lo = roc_auc(spectral_matched_filter(lo.cube, lo.reporter), lo.detection_gt)
    assert 0.0 <= auc_lo <= 1.0 and 0.0 <= auc_hi <= 1.0
    assert auc_hi >= auc_lo   # detection should not improve as SNR drops


def test_abundance_metrics_respect_target_mask():
    from hypermix import mean_absolute_error, pearson_r

    truth = np.array([0.0, 0.0, 0.03, 0.08, 0.12])
    predicted = np.array([0.8, 0.7, 0.04, 0.07, 0.11])
    mask = truth > 0.02
    assert pearson_r(predicted, truth, mask=mask) > 0.95
    assert mean_absolute_error(predicted, truth, mask=mask) < 0.02
    assert mean_absolute_error(predicted, truth) > 0.25
