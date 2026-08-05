"""Geometria candidata das regiões bioHSI de 54 m.

O JSON do arquivo de dados fornece coordenadas em recortes rotacionados, não
diretamente no cubo ENVI. Este módulo torna a transformação explícita e
reproduzível. A primeira porta de reprodução mostrou que ainda não há evidência
de que elas sejam as caixas manuais da Figura 4g. Scores publicados nunca são
entradas para mover ou selecionar uma região.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.ndimage import rotate


PROTOCOL_RESOURCE = files("hypermix.data").joinpath("biohsi_54m_protocol.json")

__all__ = [
    "BioHSI54mProtocol",
    "BioHSIRoi",
    "extract_rotated_crop",
    "load_biohsi_54m_protocol",
    "roi_polygon_in_scene",
    "rotated_points_to_scene",
    "scene_points_to_rotated",
]


@dataclass(frozen=True)
class BioHSIRoi:
    """Uma região retangular no referencial do recorte rotacionado."""

    index: int
    top_left_yx: tuple[int, int]
    bottom_right_yx: tuple[int, int]
    concentration_um: float
    published_classification_score: float

    @property
    def slices(self) -> tuple[slice, slice]:
        return (
            slice(self.top_left_yx[0], self.bottom_right_yx[0]),
            slice(self.top_left_yx[1], self.bottom_right_yx[1]),
        )

    @property
    def is_positive(self) -> bool:
        """Limiar pré-especificado no protocolo oficial da Figura 4."""
        return self.concentration_um >= 5.0


@dataclass(frozen=True)
class BioHSI54mProtocol:
    """Protocolo primário e sua geometria, carregados do artefato curado."""

    sample_name: str
    crop_yx: tuple[tuple[int, int], tuple[int, int]]
    rotation_degrees: float
    positive_threshold_um: float
    rois: tuple[BioHSIRoi, ...]
    source: Mapping[str, Any]

    @property
    def crop_shape(self) -> tuple[int, int]:
        (y0, y1), (x0, x1) = self.crop_yx
        return y1 - y0, x1 - x0


def load_biohsi_54m_protocol() -> BioHSI54mProtocol:
    """Carrega e valida o protocolo candidato versionado para a Figura 4g."""
    with PROTOCOL_RESOURCE.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported bioHSI 54 m protocol schema")
    primary = raw["primary_analysis"]
    rois = tuple(
        BioHSIRoi(
            index=int(item["index"]),
            top_left_yx=tuple(item["top_left_yx"]),
            bottom_right_yx=tuple(item["bottom_right_yx"]),
            concentration_um=float(item["concentration_um"]),
            published_classification_score=float(
                item["published_classification_score"]
            ),
        )
        for item in primary["rois"]
    )
    if [roi.index for roi in rois] != list(range(len(rois))):
        raise ValueError("bioHSI ROI indices must be contiguous and ordered")
    threshold = float(primary["positive_threshold_um"])
    protocol = BioHSI54mProtocol(
        sample_name=primary["sample_name"],
        crop_yx=tuple(tuple(pair) for pair in primary["crop_yx"]),
        rotation_degrees=float(primary["rotation_degrees"]),
        positive_threshold_um=threshold,
        rois=rois,
        source=raw["sources"],
    )
    height, width = protocol.crop_shape
    for roi in rois:
        y0, x0 = roi.top_left_yx
        y1, x1 = roi.bottom_right_yx
        if not (0 <= y0 < y1 <= height and 0 <= x0 < x1 <= width):
            raise ValueError(f"ROI {roi.index} lies outside the rotated crop")
        if roi.is_positive != (roi.concentration_um >= threshold):
            raise ValueError("ROI threshold differs from the protocol threshold")
    return protocol


def extract_rotated_crop(
    data: np.ndarray,
    protocol: BioHSI54mProtocol | None = None,
    *,
    order: int = 1,
) -> np.ndarray:
    """Recorta e rotaciona dados 2D ou 3D para o referencial publicado.

    A rotação usa ``reshape=False`` e mantém os eixos adicionais intactos. O
    preenchimento é NaN para nunca se tornar uma medição de fundo válida.
    """
    source = protocol or load_biohsi_54m_protocol()
    array = np.asarray(data)
    if array.ndim not in {2, 3}:
        raise ValueError("data must be (lines, samples) or (lines, samples, bands)")
    (y0, y1), (x0, x1) = source.crop_yx
    if y1 > array.shape[0] or x1 > array.shape[1]:
        raise ValueError("bioHSI crop lies outside the supplied data")
    cropped = np.asarray(array[y0:y1, x0:x1], dtype=np.float64)
    axes = (0, 1)
    return rotate(
        cropped,
        source.rotation_degrees,
        axes=axes,
        reshape=False,
        order=order,
        mode="constant",
        cval=np.nan,
        prefilter=order > 1,
    )


def _rotation_mapping(
    shape: tuple[int, int], angle_degrees: float
) -> tuple[np.ndarray, np.ndarray]:
    radians = np.deg2rad(angle_degrees)
    cosine, sine = np.cos(radians), np.sin(radians)
    matrix = np.array([[cosine, sine], [-sine, cosine]], dtype=np.float64)
    center = (np.asarray(shape, dtype=np.float64) - 1.0) / 2.0
    offset = center - matrix @ center
    return matrix, offset


def rotated_points_to_scene(
    points_yx: Sequence[Sequence[float]],
    protocol: BioHSI54mProtocol | None = None,
) -> np.ndarray:
    """Converte centros de pixels rotacionados para coordenadas do cubo."""
    source = protocol or load_biohsi_54m_protocol()
    points = np.asarray(points_yx, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("points_yx must be an (n, 2) array")
    matrix, offset = _rotation_mapping(source.crop_shape, source.rotation_degrees)
    crop_points = points @ matrix.T + offset
    origin = np.array([source.crop_yx[0][0], source.crop_yx[1][0]])
    return crop_points + origin


def scene_points_to_rotated(
    points_yx: Sequence[Sequence[float]],
    protocol: BioHSI54mProtocol | None = None,
) -> np.ndarray:
    """Converte coordenadas do cubo para o recorte rotacionado."""
    source = protocol or load_biohsi_54m_protocol()
    points = np.asarray(points_yx, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("points_yx must be an (n, 2) array")
    matrix, offset = _rotation_mapping(source.crop_shape, source.rotation_degrees)
    origin = np.array([source.crop_yx[0][0], source.crop_yx[1][0]])
    return (points - origin - offset) @ np.linalg.inv(matrix).T


def roi_polygon_in_scene(
    roi: BioHSIRoi,
    protocol: BioHSI54mProtocol | None = None,
) -> np.ndarray:
    """Retorna os quatro centros de canto de uma ROI no cubo completo."""
    y0, x0 = roi.top_left_yx
    y1, x1 = roi.bottom_right_yx
    corners = np.array(
        [[y0, x0], [y0, x1 - 1], [y1 - 1, x1 - 1], [y1 - 1, x0]],
        dtype=np.float64,
    )
    return rotated_points_to_scene(corners, protocol)
