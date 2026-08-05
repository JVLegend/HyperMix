#!/usr/bin/env python3
"""Executa a tag oficial bioHSI sobre as regiões candidatas do protocolo.

Este diagnóstico exige um clone separado de ``VoigtLab/bioHSI`` na tag
``v.1.0.0``. Nenhum arquivo desse clone é copiado para o HyperMix.

    python scripts/audit_official_biohsi_source.py \
      --official-root /path/to/bioHSI/04_image_processing
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HEADER = (
    ROOT / "data" / "biohsi" / "rg_on_sand_induction_54m" / "raw_0_rd_rf_or.hdr"
)
DEFAULT_OUTPUT = ROOT / "results" / "real_target_official_source_audit.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    official_root = args.official_root.resolve()
    reference_path = (
        official_root
        / "00_data"
        / "absorbance_data"
        / "YF10_infered_absorbance_from_pellets_09Jul2024.npy"
    )
    if not (official_root / "hsi_detect" / "classifier.py").is_file():
        raise FileNotFoundError("official-root must contain hsi_detect/classifier.py")
    if not reference_path.is_file():
        raise FileNotFoundError(reference_path)

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(official_root))
    from hsi_detect.classifier import HierarchicalKMeansUnmixer
    from hsi_detect.image import HyperspectralImage
    from hsi_detect.spectrum import Spectrum
    import scipy
    import sklearn
    import spectral

    from hypermix.biohsi_roi import extract_rotated_crop, load_biohsi_54m_protocol
    from hypermix.metrics import mean_absolute_error, pearson_r

    print("carregando o cubo pelo código oficial", flush=True)
    image = HyperspectralImage(str(args.header), smoothing_window=11)
    reference = Spectrum(str(reference_path))
    reference.interpolate_spectrum(image.centers)
    print("executando HierarchicalKMeansUnmixer oficial", flush=True)
    classifier = HierarchicalKMeansUnmixer()
    classifier.fit(image, reference)
    score_map = classifier.classify(reference)

    protocol = load_biohsi_54m_protocol()
    rotated = extract_rotated_crop(score_map, order=1)
    reproduced = np.asarray(
        [float(np.nanmean(rotated[roi.slices])) for roi in protocol.rois]
    )
    published = np.asarray(
        [roi.published_classification_score for roi in protocol.rois]
    )
    payload = {
        "schema_version": 1,
        "official_repository": "https://github.com/VoigtLab/bioHSI",
        "official_tag": "v.1.0.0",
        "official_commit": "935e501cf24e28fd77b40c9d111f8e827bd1812c",
        "candidate_geometry": "hypermix/data/biohsi_54m_protocol.json",
        "scores": reproduced.tolist(),
        "mae": mean_absolute_error(reproduced, published),
        "pearson_r": pearson_r(reproduced, published),
        "final_clusters": len(classifier.em_ls[0]),
        "map_min": float(np.nanmin(score_map)),
        "map_max": float(np.nanmax(score_map)),
        "map_mean": float(np.nanmean(score_map)),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "spectral": spectral.__version__,
        },
        "interpretation": (
            "This audit tests the candidate coordinate bridge with the source "
            "implementation. It does not recreate the authors' historical environment."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
