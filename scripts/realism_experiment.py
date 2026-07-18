"""Measure the effect of each opt-in Phase B realism component.

The experiment stays on a wavelength-calibrated synthetic grid, because the
three downloaded benchmark MAT files do not carry per-band wavelengths. It
compares four classical detectors with the exact at-sensor target and also
measures a practical mismatch: spatial matched filtering with the laboratory
reporter before sensor and atmospheric transformation.

    python scripts/realism_experiment.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from hypermix import (
    ace,
    measured_reporter_library,
    reporter_signature,
    roc_auc,
    simulate_scene,
    smoothed_matched_filter,
    spectral_angle_mapper,
    spectral_matched_filter,
)


ROOT = Path(__file__).resolve().parents[1]
SNRS = (20.0, 10.0, 5.0, 0.0)
SEEDS = (0, 1, 2, 3, 4)
N_BANDS = 61
METHODS = {
    "matched_filter": spectral_matched_filter,
    "matched_filter_spatial": smoothed_matched_filter,
    "ace": ace,
    "spectral_angle_mapper": spectral_angle_mapper,
}
SCENARIOS = {
    "stylized_control": {},
    "measured_linear": {"spectral_source": "measured"},
    "measured_srf_10nm": {"spectral_source": "measured", "sensor_fwhm_nm": 10.0},
    "measured_srf_atmosphere": {
        "spectral_source": "measured",
        "sensor_fwhm_nm": 10.0,
        "atmosphere": True,
    },
    "measured_full_bilinear": {
        "spectral_source": "measured",
        "sensor_fwhm_nm": 10.0,
        "atmosphere": True,
        "mixing": "bilinear",
        "nonlinearity": 0.5,
    },
}


def _laboratory_target(spectral_source: str) -> np.ndarray:
    if spectral_source == "measured":
        return measured_reporter_library(N_BANDS)[1]["bacteriochlorophyll_a"]
    return reporter_signature(N_BANDS)


def main() -> None:
    rows = []
    for scenario, options in SCENARIOS.items():
        source = options.get("spectral_source", "stylized")
        lab_target = _laboratory_target(source)
        for snr in SNRS:
            exact_scores = {name: [] for name in METHODS}
            laboratory_scores = []
            for seed in SEEDS:
                scene = simulate_scene(
                    height=80,
                    width=80,
                    n_bands=N_BANDS,
                    snr_db=snr,
                    seed=seed,
                    **options,
                )
                for name, detector in METHODS.items():
                    score = detector(scene.cube, scene.reporter)
                    exact_scores[name].append(roc_auc(score, scene.detection_gt))
                lab_score = smoothed_matched_filter(scene.cube, lab_target)
                laboratory_scores.append(roc_auc(lab_score, scene.detection_gt))

            for method, aucs in exact_scores.items():
                rows.append(
                    {
                        "scenario": scenario,
                        "target": "at_sensor_oracle",
                        "method": method,
                        "target_snr_db": snr,
                        "seeds": len(SEEDS),
                        "auc_mean": float(np.mean(aucs)),
                        "auc_std": float(np.std(aucs)),
                    }
                )
            rows.append(
                {
                    "scenario": scenario,
                    "target": "laboratory_untransformed",
                    "method": "matched_filter_spatial",
                    "target_snr_db": snr,
                    "seeds": len(SEEDS),
                    "auc_mean": float(np.mean(laboratory_scores)),
                    "auc_std": float(np.std(laboratory_scores)),
                }
            )

    output_json = ROOT / "results" / "realism.json"
    output_json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    def aggregate(scenario: str, target: str, method: str) -> tuple[float, float]:
        selected = [
            row for row in rows
            if row["scenario"] == scenario
            and row["target"] == target
            and row["method"] == method
        ]
        mean_all = float(np.mean([row["auc_mean"] for row in selected]))
        at_zero = next(row["auc_mean"] for row in selected if row["target_snr_db"] == 0.0)
        return mean_all, at_zero

    labels = {
        "stylized_control": "Controle estilizado, linear",
        "measured_linear": "Espectros medidos, linear",
        "measured_srf_10nm": "Medidos + SRF 10 nm",
        "measured_srf_atmosphere": "Medidos + SRF + atmosfera",
        "measured_full_bilinear": "Medidos + SRF + atmosfera + bilinear",
    }
    lines = [
        "# Sensibilidade aos componentes de realismo da Fase B",
        "",
        "AUC média em target SNR de 20, 10, 5 e 0 dB, com 5 seeds por ponto.",
        "O alvo oráculo é o espectro exato observado pelo sensor. O alvo laboratorial",
        "é a curva antes da SRF e da atmosfera, portanto mede mismatch de implantação.",
        "O benchmark usa uma grade simulada calibrada em comprimento de onda; os MAT",
        "reais atuais não incluem os centros de banda necessários para esta transformação.",
        "",
        "| Cenário | MF | MF espacial | ACE | SAM | MF espacial lab | MF espacial a 0 dB |",
        "|---------|:--:|:-----------:|:---:|:---:|:----------------:|:-------------------:|",
    ]
    for scenario in SCENARIOS:
        mf = aggregate(scenario, "at_sensor_oracle", "matched_filter")[0]
        spatial, spatial_zero = aggregate(
            scenario, "at_sensor_oracle", "matched_filter_spatial"
        )
        ace_auc = aggregate(scenario, "at_sensor_oracle", "ace")[0]
        sam = aggregate(scenario, "at_sensor_oracle", "spectral_angle_mapper")[0]
        lab = aggregate(scenario, "laboratory_untransformed", "matched_filter_spatial")[0]
        lines.append(
            f"| {labels[scenario]} | {mf:.3f} | {spatial:.3f} | {ace_auc:.3f} | "
            f"{sam:.3f} | {lab:.3f} | {spatial_zero:.3f} |"
        )
    lines += [
        "",
        "Interpretação: esta é uma análise de sensibilidade com alvo implantado, não",
        "evidência de generalização para um biossinal remoto naturalmente observado.",
        "",
    ]
    output_md = ROOT / "results" / "realism.md"
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Wrote {output_json} and {output_md}")


if __name__ == "__main__":
    main()
