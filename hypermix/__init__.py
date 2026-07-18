"""HyperMix: open detection of engineered biosignatures in remote hyperspectral imagery.

Phase 0 (this release):
  - physics-based remote-scene simulator with full ground truth
  - classical detection baselines (matched filter, ACE)
  - detection metrics (ROC AUC)

Planned:
  - physics-informed, self-supervised detector + uncertainty (Milestone 2)
  - open spectral dataset + public benchmark (Milestone 3)
"""

from .simulate import (
    SceneResult,
    endmember_library,
    false_color,
    reporter_library,
    reporter_signature,
    simulate_scene,
)
from .baselines import (
    ace,
    smoothed_matched_filter,
    spectral_angle_mapper,
    spectral_matched_filter,
)
from .metrics import mean_absolute_error, pearson_r, roc_auc, roc_curve
from .datasets import implant_target, load_mat_cube, load_envi_cube, synthetic_target

__version__ = "0.4.0"

__all__ = [
    "SceneResult",
    "simulate_scene",
    "endmember_library",
    "reporter_signature",
    "reporter_library",
    "false_color",
    "spectral_matched_filter",
    "smoothed_matched_filter",
    "ace",
    "spectral_angle_mapper",
    "roc_auc",
    "roc_curve",
    "pearson_r",
    "mean_absolute_error",
    "load_mat_cube",
    "load_envi_cube",
    "synthetic_target",
    "implant_target",
    "__version__",
]
