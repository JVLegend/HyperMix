"""Reprodução auditável do classificador publicado com o conjunto bioHSI.

O artigo de Chemla et al. acompanha uma implementação MIT chamada
``HierarchicalKMeansUnmixer``. Este módulo reimplementa somente o caminho usado
na Figura 4g, fixando inclusive os defaults históricos que mudaram entre
versões do scikit-learn. Ele não é apresentado como um método novo do HyperMix.

Fonte primária: ``VoigtLab/bioHSI``, tag ``v.1.0.0``, commit
``935e501cf24e28fd77b40c9d111f8e827bd1812c``.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Callable

import numpy as np
from scipy.ndimage import uniform_filter


YF10_RESOURCE = files("hypermix.data").joinpath("biohsi_yf10_absorbance.csv")

__all__ = [
    "PublishedHKMResult",
    "load_published_yf10_absorbance",
    "published_hkm_ucls",
    "smooth_spectral_cube",
    "ucls_abundances",
]


@dataclass(frozen=True)
class PublishedHKMResult:
    """Mapa e diagnóstico mínimo da reprodução HKM mais UCLS."""

    score_map: np.ndarray
    endmembers: np.ndarray
    valid_mask: np.ndarray
    initial_clusters: int
    retained_clusters: int
    final_clusters: int


def load_published_yf10_absorbance(wavelengths_nm: np.ndarray) -> np.ndarray:
    """Interpola a absorbância YF10 original para o sensor da cena.

    O CSV empacotado preserva os 371 pares do arquivo NPY oficial. ``np.interp``
    também reproduz a extrapolação constante usada pela classe ``Spectrum``.
    Nenhuma correção de linha de base ou normalização é aplicada.
    """
    wavelengths = np.asarray(wavelengths_nm, dtype=np.float64)
    if wavelengths.ndim != 1 or wavelengths.size < 2:
        raise ValueError("wavelengths_nm must be a one-dimensional grid")
    if not np.all(np.isfinite(wavelengths)) or np.any(np.diff(wavelengths) <= 0):
        raise ValueError("wavelengths_nm must be finite and strictly increasing")
    with YF10_RESOURCE.open("rb") as handle:
        source = np.genfromtxt(handle, delimiter=",", names=True, dtype=np.float64)
    return np.interp(
        wavelengths,
        source["wavelength_nm"],
        source["absorbance"],
    )


def smooth_spectral_cube(cube: np.ndarray, window_size: int = 11) -> np.ndarray:
    """Aplica a média móvel espectral usada pelo código bioHSI oficial."""
    array = np.asarray(cube)
    if array.ndim != 3:
        raise ValueError("cube must have shape (lines, samples, bands)")
    if not isinstance(window_size, (int, np.integer)) or not 0 < window_size <= array.shape[2]:
        raise ValueError("window_size must be a positive integer no larger than bands")
    return uniform_filter(array, size=(1, 1, int(window_size)), mode="nearest")


def ucls_abundances(pixels: np.ndarray, endmembers: np.ndarray) -> np.ndarray:
    """Unconstrained least squares, com a mesma orientação do código oficial."""
    matrix = np.asarray(pixels, dtype=np.float64)
    basis = np.asarray(endmembers, dtype=np.float64)
    if matrix.ndim != 2 or basis.ndim != 2:
        raise ValueError("pixels and endmembers must be two-dimensional")
    if matrix.shape[1] != basis.shape[1]:
        raise ValueError("pixels and endmembers must have the same band count")
    return (np.linalg.pinv(basis.T) @ matrix.T).T


def _normalized_valid_pixels(
    cube: np.ndarray,
    valid_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    flattened = np.asarray(cube).reshape(-1, cube.shape[-1])
    maxima = np.nanmax(flattened, axis=1)
    automatic = np.all(np.isfinite(flattened), axis=1) & np.isfinite(maxima) & (maxima != 0)
    if valid_mask is not None:
        supplied = np.asarray(valid_mask, dtype=bool)
        if supplied.shape != cube.shape[:2]:
            raise ValueError("valid_mask must match the spatial cube shape")
        automatic &= supplied.ravel()
    pixels = flattened[automatic]
    if pixels.shape[0] == 0:
        raise ValueError("cube has no valid spectra")
    pixels = pixels / maxima[automatic, None]
    return np.asarray(pixels, dtype=np.float32), automatic.reshape(cube.shape[:2])


def _reference_filter(endmembers: np.ndarray, reference: np.ndarray, threshold: float) -> np.ndarray:
    normalized = endmembers / np.nanmax(endmembers, axis=1, keepdims=True)
    projections = normalized @ reference
    gram = normalized @ normalized.T
    squared_norms = np.diag(gram)
    distances = np.sqrt(
        np.maximum(squared_norms[:, None] + squared_norms[None, :] - 2.0 * gram, 0.0)
    )
    numerator = projections[:, None] - projections[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        similarity = numerator / (np.linalg.norm(reference) * distances)
    np.fill_diagonal(similarity, 0.0)
    return np.nanmax(similarity, axis=0) <= threshold


def published_hkm_ucls(
    cube: np.ndarray,
    reference_absorbance: np.ndarray,
    *,
    valid_mask: np.ndarray | None = None,
    reduced_dims: int = 3,
    n_init_clusters: int = 1000,
    filter_threshold: float = 0.9,
    distance_threshold: float = 0.005,
    random_state: int = 1,
    progress: Callable[[str], None] | None = None,
) -> PublishedHKMResult:
    """Executa o caminho HKM mais UCLS da Figura 4g.

    O cubo recebido já deve conter a suavização espectral. A configuração
    default reproduz os parâmetros da tag oficial. ``n_init=3`` é explicitado
    porque era o comportamento efetivo do scikit-learn 1.3 e virou ``auto`` em
    versões posteriores.
    """
    try:
        from sklearn.cluster import AgglomerativeClustering, MiniBatchKMeans
        from sklearn.decomposition import PCA
    except ImportError as exc:  # pragma: no cover, exercised by core-only installs
        raise ImportError(
            "published_hkm_ucls requires `pip install hypermix[reproduce]`"
        ) from exc

    array = np.asarray(cube)
    reference = np.asarray(reference_absorbance, dtype=np.float64).ravel()
    if array.ndim != 3:
        raise ValueError("cube must have shape (lines, samples, bands)")
    if reference.shape != (array.shape[2],) or not np.all(np.isfinite(reference)):
        raise ValueError("reference_absorbance must be finite and match cube bands")
    if not 1 <= reduced_dims <= array.shape[2]:
        raise ValueError("reduced_dims must lie between 1 and the band count")
    if not isinstance(n_init_clusters, (int, np.integer)) or n_init_clusters < 2:
        raise ValueError("n_init_clusters must be at least 2")
    if not 0.0 <= filter_threshold <= 1.0:
        raise ValueError("filter_threshold must lie in [0, 1]")
    if distance_threshold <= 0:
        raise ValueError("distance_threshold must be positive")

    emit = progress or (lambda _message: None)
    emit("normalizando pixels válidos")
    pixels, spatial_valid = _normalized_valid_pixels(array, valid_mask)
    if pixels.shape[0] < n_init_clusters:
        raise ValueError("n_init_clusters exceeds the number of valid pixels")

    emit("reduzindo a dimensionalidade com PCA")
    reduced = PCA(
        n_components=int(reduced_dims),
        random_state=int(random_state),
        svd_solver="full",
    ).fit_transform(pixels)

    emit("ajustando MiniBatchKMeans")
    initial_labels = MiniBatchKMeans(
        n_clusters=int(n_init_clusters),
        random_state=int(random_state),
        n_init=3,
    ).fit_predict(reduced)
    initial_endmembers = np.vstack(
        [pixels[initial_labels == label].mean(axis=0) for label in range(n_init_clusters)]
    )

    emit("filtrando clusters semelhantes ao alvo")
    retained = _reference_filter(initial_endmembers, reference, filter_threshold)
    if int(retained.sum()) < 2:
        raise ValueError("reference filtering retained fewer than two clusters")
    filtered_endmembers = initial_endmembers[retained]

    emit("fundindo endmembers por clusterização aglomerativa")
    merged = AgglomerativeClustering(
        n_clusters=None,
        metric="cosine",
        linkage="average",
        distance_threshold=float(distance_threshold),
    ).fit_predict(filtered_endmembers)
    initial_to_final = np.full(int(n_init_clusters), -1, dtype=np.int32)
    initial_to_final[np.flatnonzero(retained)] = merged
    final_labels = initial_to_final[initial_labels]
    final_count = int(merged.max()) + 1
    final_endmembers = np.vstack(
        [pixels[final_labels == label].mean(axis=0) for label in range(final_count)]
    )

    emit("calculando abundância UCLS")
    basis = np.vstack([-reference, final_endmembers])
    target_scores = ucls_abundances(pixels, basis)[:, 0]
    target_scores[target_scores < 0.0] = 0.0
    score_map = np.full(array.shape[:2], np.nan, dtype=np.float64)
    score_map[spatial_valid] = target_scores
    return PublishedHKMResult(
        score_map=score_map,
        endmembers=final_endmembers,
        valid_mask=spatial_valid,
        initial_clusters=int(n_init_clusters),
        retained_clusters=int(retained.sum()),
        final_clusters=final_count,
    )
