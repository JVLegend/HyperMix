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
    mean_absolute_error,
    negative_log_likelihood,
    pd_at_far,
    pearson_r,
    reliability_curve,
    roc_auc,
    roc_curve,
)
from .background import background_detector, smoothed_background_detector
from .datasets import implant_target, load_mat_cube, load_envi_cube, synthetic_target

__version__ = "0.4.0"

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
    "mean_absolute_error",
    "background_detector",
    "smoothed_background_detector",
    "load_mat_cube",
    "load_envi_cube",
    "synthetic_target",
    "implant_target",
    "__version__",
]
