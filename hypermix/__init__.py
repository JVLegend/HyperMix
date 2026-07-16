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
    reporter_signature,
    simulate_scene,
)
from .baselines import ace, spectral_matched_filter
from .metrics import roc_auc, roc_curve

__version__ = "0.1.0"

__all__ = [
    "SceneResult",
    "simulate_scene",
    "endmember_library",
    "reporter_signature",
    "false_color",
    "spectral_matched_filter",
    "ace",
    "roc_auc",
    "roc_curve",
    "__version__",
]
