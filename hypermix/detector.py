"""Milestone 2: a physics-informed, learned detector with uncertainty.

Design principle: don't throw away the physics. Each pixel is described by
its mean-removed spectrum plus the classical matched-filter score, and a
small network learns a nonlinear correction on top. Because the matched
filter is an input feature, the network can always recover it, so it should
match or beat the classical baseline, and it can exploit non-Gaussian real
background structure that the matched filter cannot.

Uncertainty comes from MC-dropout: keep dropout active at inference, run T
stochastic passes, report mean (detection) and std (confidence).

Trained purely on physics-simulated backgrounds, evaluated on real ones.
PyTorch is imported lazily so the rest of the package works without it.
"""

from __future__ import annotations

import numpy as np

from .baselines import ace, spectral_matched_filter
from .simulate import _gaussian_blur

__all__ = ["pixel_features", "SpectralDetector", "AbundanceUnmixer",
           "make_training_set"]


def _blur2d(m: np.ndarray, sigma: float) -> np.ndarray:
    return _gaussian_blur(m[:, :, None], sigma)[:, :, 0]


def pixel_features(cube: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Scene-adaptive, spatial-spectral features (per-pixel).

    All features derive from the scene's OWN adaptive detectors (matched
    filter, ACE) plus spatial context, then are z-scored within the scene.
    This is what lets a model trained on simulated backgrounds transfer to
    real ones: nothing here encodes simulator-specific absolute spectra, and
    the spatial context exploits the extended (blob) structure of targets
    that a per-pixel matched filter ignores.
    """
    mf = spectral_matched_filter(cube, target)
    a = ace(cube, target)
    feats = np.stack([
        mf, a,
        _blur2d(mf, 1.0), _blur2d(mf, 2.5),
        _blur2d(a, 1.5),
    ], axis=-1).reshape(-1, 5).astype(np.float32)
    feats = (feats - feats.mean(axis=0, keepdims=True)) / (feats.std(axis=0, keepdims=True) + 1e-6)
    return feats


class SpectralDetector:
    """Small MLP detector over pixel features, with MC-dropout uncertainty."""

    def __init__(self, n_features: int, hidden: int = 128,
                 dropout: float = 0.25, seed: int = 0):
        import torch
        import torch.nn as nn

        torch.manual_seed(seed)
        self._torch = torch
        self.net = nn.Sequential(
            nn.Linear(n_features, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )
        self.mean_ = None
        self.std_ = None

    def _scale(self, x: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mean_ = x.mean(axis=0, keepdims=True)
            self.std_ = x.std(axis=0, keepdims=True) + 1e-6
        return ((x - self.mean_) / self.std_).astype(np.float32)

    def fit(self, features: np.ndarray, labels: np.ndarray,
            epochs: int = 30, batch: int = 8192, lr: float = 1e-3,
            verbose: bool = False) -> "SpectralDetector":
        torch = self._torch
        xs = torch.from_numpy(self._scale(features, fit=True))
        ys = torch.from_numpy(labels.astype(np.float32).reshape(-1, 1))
        pos = float(labels.sum())
        pos_weight = torch.tensor([(len(labels) - pos) / max(pos, 1.0)],
                                  dtype=torch.float32)
        lossfn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        n = len(labels)
        self.net.train()
        for ep in range(epochs):
            perm = torch.randperm(n)
            total = 0.0
            for i in range(0, n, batch):
                idx = perm[i:i + batch]
                opt.zero_grad()
                loss = lossfn(self.net(xs[idx]), ys[idx])
                loss.backward()
                opt.step()
                total += float(loss.detach()) * len(idx)
            if verbose:
                print(f"  epoch {ep + 1:>2}/{epochs}  loss {total / n:.4f}")
        return self

    def score_map(self, cube: np.ndarray, target: np.ndarray, mc: int = 0):
        """Detection score map (H, W). If mc>1, returns (mean, std)."""
        torch = self._torch
        h, w, _ = cube.shape
        xs = torch.from_numpy(self._scale(pixel_features(cube, target)))
        if mc and mc > 1:
            self.net.train()  # keep dropout ON for MC sampling
            preds = []
            with torch.no_grad():
                for _ in range(mc):
                    preds.append(torch.sigmoid(self.net(xs)).numpy().reshape(h, w))
            preds = np.stack(preds, axis=0)
            return preds.mean(axis=0), preds.std(axis=0)
        self.net.eval()
        with torch.no_grad():
            return torch.sigmoid(self.net(xs)).numpy().reshape(h, w)

    def save(self, path: str) -> None:
        self._torch.save(
            {"state": self.net.state_dict(), "mean": self.mean_, "std": self.std_},
            path,
        )

    def load(self, path: str) -> "SpectralDetector":
        ckpt = self._torch.load(path, weights_only=False)
        self.net.load_state_dict(ckpt["state"])
        self.mean_, self.std_ = ckpt["mean"], ckpt["std"]
        return self


def make_training_set(target: np.ndarray, n_scenes: int = 24, hw: int = 96,
                      snrs=(0.0, 5.0, 10.0, 20.0), seed0: int = 100,
                      with_abundance: bool = False):
    """Build training data by implanting the target into simulated backgrounds.

    Returns (features, detection_labels), or (features, detection_labels,
    abundance) when ``with_abundance`` is True (for the unmixing head).
    """
    from .datasets import implant_target
    from .simulate import simulate_scene

    b = int(target.shape[0])
    feats, labs, abund = [], [], []
    for k in range(n_scenes):
        snr = snrs[k % len(snrs)]
        bg = simulate_scene(height=hw, width=hw, n_bands=b, snr_db=40.0,
                            reporter_max_abundance=0.0, seed=seed0 + k).cube
        rng = np.random.default_rng(1000 + k)
        scene, gt, ab, tgt = implant_target(bg, rng, target=target, snr_db=snr)
        feats.append(pixel_features(scene, tgt))
        labs.append(gt.reshape(-1))
        abund.append(ab.reshape(-1))
    if with_abundance:
        return np.concatenate(feats), np.concatenate(labs), np.concatenate(abund)
    return np.concatenate(feats), np.concatenate(labs)


class AbundanceUnmixer:
    """Estimate *how much* target is present per pixel, not just whether.

    Same scene-adaptive spatial-spectral features as the detector, but a
    regression head trained on the known implanted abundance. This is the
    unmixing side of the toolkit: an abundance map, not only a detection map.
    """

    def __init__(self, n_features: int, hidden: int = 128,
                 dropout: float = 0.2, seed: int = 0):
        import torch
        import torch.nn as nn

        torch.manual_seed(seed)
        self._torch = torch
        self.net = nn.Sequential(
            nn.Linear(n_features, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )
        self.mean_ = None
        self.std_ = None

    def _scale(self, x, fit=False):
        if fit:
            self.mean_ = x.mean(axis=0, keepdims=True)
            self.std_ = x.std(axis=0, keepdims=True) + 1e-6
        return ((x - self.mean_) / self.std_).astype(np.float32)

    def fit(self, features, abundance, epochs: int = 30, batch: int = 8192,
            lr: float = 1e-3) -> "AbundanceUnmixer":
        torch = self._torch
        xs = torch.from_numpy(self._scale(features, fit=True))
        ys = torch.from_numpy(abundance.astype(np.float32).reshape(-1, 1))
        lossfn = torch.nn.MSELoss()
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        n = len(abundance)
        self.net.train()
        for _ in range(epochs):
            perm = torch.randperm(n)
            for i in range(0, n, batch):
                idx = perm[i:i + batch]
                opt.zero_grad()
                lossfn(self.net(xs[idx]), ys[idx]).backward()
                opt.step()
        return self

    def predict_map(self, cube, target):
        torch = self._torch
        h, w, _ = cube.shape
        xs = torch.from_numpy(self._scale(pixel_features(cube, target)))
        self.net.eval()
        with torch.no_grad():
            return self.net(xs).numpy().reshape(h, w)
