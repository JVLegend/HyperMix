"""Self-supervised background modeling for target detection.

The spectral autoencoder is fitted transductively on unlabeled pixels from the
scene being evaluated. Its training path receives neither target signatures nor
ground-truth masks. The final target-aware score combines reconstruction
surprise with a matched-filter score only after background training is complete.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata

from .baselines import spectral_matched_filter

__all__ = ["background_detector", "smoothed_background_detector"]


def _validate_cube(cube: np.ndarray) -> np.ndarray:
    values = np.asarray(cube)
    if values.ndim != 3:
        raise ValueError("cube must have shape (height, width, bands)")
    if values.shape[0] * values.shape[1] < 2 or values.shape[2] < 2:
        raise ValueError("cube must contain at least two pixels and two bands")
    if not np.all(np.isfinite(values)):
        raise ValueError("cube must contain only finite values")
    return values.astype(np.float32, copy=False)


def _background_reconstruction_error(
    cube: np.ndarray,
    *,
    latent_dim: int | None,
    epochs: int,
    sample_size: int,
    batch_size: int,
    seed: int,
) -> np.ndarray:
    """Fit a shallow spectral autoencoder without labels or target input."""
    if epochs < 1:
        raise ValueError("epochs must be positive")
    if sample_size < 2 or batch_size < 1:
        raise ValueError("sample_size and batch_size must be positive")

    try:
        import torch
        from torch import nn
    except ImportError as exc:  # pragma: no cover - exercised without train extra
        raise ImportError(
            "background_detector requires the optional train dependency"
        ) from exc

    height, width, bands = cube.shape
    pixels = cube.reshape(-1, bands)
    generator = np.random.default_rng(seed)
    count = min(sample_size, pixels.shape[0])
    indices = generator.choice(pixels.shape[0], size=count, replace=False)
    training = pixels[indices].astype(np.float32, copy=True)

    median = np.median(training, axis=0)
    mad = np.median(np.abs(training - median), axis=0)
    scale = np.maximum(1.4826 * mad, 1e-4)
    training = np.clip((training - median) / scale, -8.0, 8.0)

    if latent_dim is None:
        latent_dim = min(32, max(4, bands // 6))
    if not 1 <= latent_dim < bands:
        raise ValueError("latent_dim must lie between 1 and bands - 1")

    torch.manual_seed(seed)
    model = nn.Sequential(
        nn.Linear(bands, latent_dim),
        nn.GELU(),
        nn.Linear(latent_dim, bands),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    loss_function = nn.MSELoss()
    tensor = torch.from_numpy(training)
    shuffle_generator = torch.Generator().manual_seed(seed)

    model.train()
    for _ in range(epochs):
        order = torch.randperm(tensor.shape[0], generator=shuffle_generator)
        for start in range(0, tensor.shape[0], batch_size):
            batch = tensor[order[start : start + batch_size]]
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(batch), batch)
            loss.backward()
            optimizer.step()

    model.eval()
    errors = np.empty(pixels.shape[0], dtype=np.float32)
    with torch.no_grad():
        for start in range(0, pixels.shape[0], batch_size):
            batch_values = pixels[start : start + batch_size]
            standardized = np.clip(
                (batch_values - median) / scale, -8.0, 8.0
            ).astype(np.float32, copy=False)
            batch = torch.from_numpy(standardized)
            residual = model(batch) - batch
            errors[start : start + batch.shape[0]] = (
                residual.square().mean(dim=1).cpu().numpy()
            )
    return errors.reshape(height, width)


def _empirical_quantiles(values: np.ndarray) -> np.ndarray:
    flat = np.asarray(values, dtype=np.float64).ravel()
    quantiles = rankdata(flat, method="average") / (flat.size + 1.0)
    return quantiles.reshape(values.shape)


def background_detector(
    cube: np.ndarray,
    target: np.ndarray,
    *,
    latent_dim: int | None = None,
    epochs: int = 15,
    sample_size: int = 12_000,
    batch_size: int = 512,
    anomaly_weight: float = 0.5,
    seed: int = 0,
    matched_filter_score: np.ndarray | None = None,
) -> np.ndarray:
    """Target score gated by a self-supervised background anomaly score.

    A shallow bottleneck autoencoder first learns the spectral background from
    unlabeled pixels of ``cube``. The target is not supplied during this step.
    Reconstruction error and matched-filter response are then converted to
    empirical quantiles. The returned score is

    ``MF_quantile * ((1 - w) + w * reconstruction_quantile)``.

    ``anomaly_weight`` is fixed before evaluation and must lie in ``[0, 1]``.
    The optional ``matched_filter_score`` avoids recomputing an already available
    MF map; it does not enter autoencoder training.
    """
    values = _validate_cube(cube)
    signature = np.asarray(target)
    if signature.shape != (values.shape[2],):
        raise ValueError("target must have shape (bands,)")
    if not 0.0 <= anomaly_weight <= 1.0:
        raise ValueError("anomaly_weight must lie in [0, 1]")

    reconstruction = _background_reconstruction_error(
        values,
        latent_dim=latent_dim,
        epochs=epochs,
        sample_size=sample_size,
        batch_size=batch_size,
        seed=seed,
    )
    if matched_filter_score is None:
        matched = spectral_matched_filter(values, signature)
    else:
        matched = np.asarray(matched_filter_score, dtype=np.float64)
        if matched.shape != values.shape[:2]:
            raise ValueError("matched_filter_score must match cube spatial shape")
    target_quantile = _empirical_quantiles(matched)
    anomaly_quantile = _empirical_quantiles(reconstruction)
    gate = (1.0 - anomaly_weight) + anomaly_weight * anomaly_quantile
    return (target_quantile * gate).astype(np.float64)


def smoothed_background_detector(
    cube: np.ndarray,
    target: np.ndarray,
    sigma: float = 1.5,
    **kwargs,
) -> np.ndarray:
    """Background-model score followed by fixed Gaussian smoothing."""
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    score = background_detector(cube, target, **kwargs)
    if sigma == 0:
        return score
    return gaussian_filter(score, sigma=float(sigma), mode="reflect")
