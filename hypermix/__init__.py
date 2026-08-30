"""HyperMix: open detection of engineered biosignatures in remote hyperspectral imagery.

Implemented toolkit components include:
  - physics-based remote-scene simulator with full ground truth
  - classical detection baselines (matched filter, ACE, RX)
  - self-supervised spectral background detector
  - detection metrics and an open benchmark
"""

from .simulate import (
    SceneResult,
    apply_atmosphere,
    apply_srf,
    atmospheric_transmittance,
    endmember_library,
    false_color,
    gaussian_srf,
    reporter_library,
    reporter_signature,
    simulate_scene,
)
from .spectra import (
    measured_endmember_library,
    measured_reporter_absorbance_library,
    measured_reporter_library,
)
from .baselines import (
    ace,
    matched_subspace_detector,
    rx_detector,
    smoothed_matched_filter,
    smoothed_matched_subspace_detector,
    spectral_angle_mapper,
    spectral_matched_filter,
)
from .metrics import (
    binary_nll,
    brier_score,
    expected_calibration_error,
    interval_coverage,
    mean_absolute_error,
    mean_bias,
    mean_interval_width,
    negative_log_likelihood,
    pd_at_far,
    pearson_r,
    reliability_curve,
    roc_auc,
    roc_curve,
    spearman_r,
    excess_kurtosis,
    skewness,
)
from .background import background_detector, smoothed_background_detector
from .blind import (
    BLIND_TRACKS,
    BlindTrack,
    blind_anomaly_features,
    family_detection_features,
    scale_target_library,
)
from .lod import (
    detection_probability_at_threshold,
    grid_detection_limit,
    robust_standardize_scores,
    threshold_at_far,
)
from .abundance import (
    CaseBalancedAffineCalibrator,
    GroupedConformalInterval,
    finite_sample_quantile,
)
from .transfer import (
    TargetTransferLibrary,
    resample_spectrum,
    target_transfer,
    target_transfer_library,
)
from .datasets import implant_target, load_mat_cube, load_envi_cube, synthetic_target
from .envi import (
    EnviHeader,
    envi_nodata_mask,
    open_envi_cube,
    parse_envi_header,
    sample_disk_means,
)
from .biohsi_roi import (
    BioHSI54mProtocol,
    BioHSIRoi,
    extract_rotated_crop,
    load_biohsi_54m_protocol,
    roi_polygon_in_scene,
)
from .biohsi_published import (
    PublishedHKMResult,
    load_published_yf10_absorbance,
    published_hkm_ucls,
    smooth_spectral_cube,
    ucls_abundances,
)

__version__ = "0.5.0"

__all__ = [
    "SceneResult",
    "simulate_scene",
    "endmember_library",
    "reporter_signature",
    "reporter_library",
    "measured_endmember_library",
    "measured_reporter_absorbance_library",
    "measured_reporter_library",
    "gaussian_srf",
    "atmospheric_transmittance",
    "apply_atmosphere",
    "apply_srf",
    "false_color",
    "spectral_matched_filter",
    "smoothed_matched_filter",
    "matched_subspace_detector",
    "smoothed_matched_subspace_detector",
    "rx_detector",
    "ace",
    "spectral_angle_mapper",
    "roc_auc",
    "roc_curve",
    "pd_at_far",
    "binary_nll",
    "negative_log_likelihood",
    "brier_score",
    "expected_calibration_error",
    "reliability_curve",
    "pearson_r",
    "spearman_r",
    "excess_kurtosis",
    "skewness",
    "mean_absolute_error",
    "mean_bias",
    "interval_coverage",
    "mean_interval_width",
    "background_detector",
    "smoothed_background_detector",
    "BlindTrack",
    "BLIND_TRACKS",
    "blind_anomaly_features",
    "family_detection_features",
    "scale_target_library",
    "detection_probability_at_threshold",
    "grid_detection_limit",
    "robust_standardize_scores",
    "threshold_at_far",
    "CaseBalancedAffineCalibrator",
    "GroupedConformalInterval",
    "finite_sample_quantile",
    "TargetTransferLibrary",
    "resample_spectrum",
    "target_transfer",
    "target_transfer_library",
    "load_mat_cube",
    "load_envi_cube",
    "EnviHeader",
    "parse_envi_header",
    "open_envi_cube",
    "envi_nodata_mask",
    "sample_disk_means",
    "BioHSI54mProtocol",
    "BioHSIRoi",
    "load_biohsi_54m_protocol",
    "extract_rotated_crop",
    "roi_polygon_in_scene",
    "PublishedHKMResult",
    "load_published_yf10_absorbance",
    "published_hkm_ucls",
    "smooth_spectral_cube",
    "ucls_abundances",
    "synthetic_target",
    "implant_target",
    "__version__",
]
