"""Gera a auditoria visual das nove ROIs candidatas do bioHSI de 54 m.

Uso:
    python scripts/biohsi_roi_overlay.py

O script não calcula scores de detecção. Ele mostra a geometria registrada no
JSON do conjunto, cuja ligação com a Figura 4g ainda não foi validada.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from hypermix.biohsi_roi import (
    extract_rotated_crop,
    load_biohsi_54m_protocol,
    roi_polygon_in_scene,
)
from hypermix.envi import envi_nodata_mask, open_envi_cube


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HEADER = (
    ROOT
    / "data"
    / "biohsi"
    / "rg_on_sand_induction_54m"
    / "raw_0_rd_rf_or.hdr"
)
DEFAULT_OUTPUT = ROOT / "assets" / "biohsi_54m_rois.png"


def _rgb(cube: np.ndarray, wavelengths: np.ndarray) -> np.ndarray:
    indices = [int(np.argmin(np.abs(wavelengths - value))) for value in (650, 550, 450)]
    selected = np.asarray(cube[:, :, indices], dtype=np.float32)
    valid = ~envi_nodata_mask(selected)
    rgb = np.zeros_like(selected)
    for channel in range(3):
        values = selected[:, :, channel][valid]
        lower, upper = np.percentile(values, [1, 99])
        rgb[:, :, channel] = np.clip(
            (selected[:, :, channel] - lower) / max(upper - lower, 1e-9),
            0.0,
            1.0,
        )
    rgb[~valid] = 0.0
    return np.power(rgb, 0.8)


def make_overlay(header_path: Path, output: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    cube, header = open_envi_cube(header_path)
    if header.wavelengths is None:
        raise ValueError("bioHSI overlay requires wavelengths in the ENVI header")
    protocol = load_biohsi_54m_protocol()
    rgb = _rgb(cube, header.wavelengths)
    rotated = extract_rotated_crop(rgb, protocol, order=1)

    polygons = [roi_polygon_in_scene(roi, protocol) for roi in protocol.rois]
    all_points = np.concatenate(polygons)
    margin = 14
    y0 = max(0, int(np.floor(all_points[:, 0].min())) - margin)
    y1 = min(rgb.shape[0], int(np.ceil(all_points[:, 0].max())) + margin)
    x0 = max(0, int(np.floor(all_points[:, 1].min())) - margin)
    x1 = min(rgb.shape[1], int(np.ceil(all_points[:, 1].max())) + margin)

    figure = plt.figure(figsize=(8.2, 7.0), dpi=180, facecolor="#071316")
    grid = figure.add_gridspec(1, 2, width_ratios=(1.15, 0.85), wspace=0.2)
    scene_ax = figure.add_subplot(grid[0, 0])
    frame_ax = figure.add_subplot(grid[0, 1])

    scene_ax.imshow(rgb[y0:y1, x0:x1])
    for roi, polygon in zip(protocol.rois, polygons):
        xy = np.column_stack((polygon[:, 1] - x0, polygon[:, 0] - y0))
        scene_ax.add_patch(
            Polygon(xy, closed=True, fill=False, edgecolor="#ffcc66", linewidth=1.4)
        )
        center = xy.mean(axis=0)
        scene_ax.text(
            center[0],
            center[1],
            str(roi.index),
            color="#071316",
            fontsize=6,
            ha="center",
            va="center",
            bbox={"boxstyle": "circle,pad=0.18", "fc": "#ffcc66", "ec": "none"},
        )
    scene_ax.set_title("Scene coordinates", color="white", fontsize=11, pad=10)
    scene_ax.set_axis_off()

    frame_ax.imshow(rotated)
    for roi in protocol.rois:
        top, left = roi.top_left_yx
        bottom, right = roi.bottom_right_yx
        frame_ax.add_patch(
            Rectangle(
                (left, top),
                right - left,
                bottom - top,
                fill=False,
                edgecolor="#ffcc66",
                linewidth=1.2,
            )
        )
        frame_ax.text(
            9.0,
            (top + bottom) / 2,
            f"{roi.index}   {roi.concentration_um:g} µM",
            color="white",
            fontsize=7,
            ha="left",
            va="center",
        )
    frame_ax.set_xlim(-0.5, 25)
    frame_ax.set_ylim(rotated.shape[0] - 0.5, -0.5)
    frame_ax.set_title("Archived parameter frame", color="white", fontsize=11, pad=10)
    frame_ax.set_axis_off()

    figure.suptitle(
        "bioHSI 54 m: candidate regions from the data parameters",
        color="white",
        fontsize=15,
        fontweight="bold",
        y=0.97,
    )
    figure.text(
        0.5,
        0.025,
        "Candidate mapping only. The reproduction gate failed, so these boxes are not confirmed as the Figure 4g regions.",
        color="#b6c8c8",
        fontsize=7.5,
        ha="center",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(make_overlay(args.header, args.output))


if __name__ == "__main__":
    main()
