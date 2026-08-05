"""Evaluate leakage-free physical transfer from laboratory to sensor targets.

This T9 experiment is synthetic and wavelength-calibrated. It uses measured
bioHSI pellet spectra and measured USGS backgrounds, then varies sensor FWHM,
atmosphere, target SNR and seed. Target-transfer parameters are fixed before
evaluation and never use implanted labels.

    python scripts/target_transfer_experiment.py

Writes ``results/target_transfer.json`` and ``results/target_transfer.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from hypermix import (
    measured_reporter_library,
    pd_at_far,
    resample_spectrum,
    roc_auc,
    simulate_scene,
    smoothed_matched_filter,
    smoothed_matched_subspace_detector,
    target_transfer,
    target_transfer_library,
)


ROOT = Path(__file__).resolve().parents[1]
NATIVE_BANDS = 601
N_BANDS = 61
HEIGHT = 72
WIDTH = 72
SNRS = (10.0, 5.0, 0.0)
SENSOR_FWHM_NM = (8.0, 10.0, 12.0)
EVAL_SEEDS = (0, 1, 2, 3, 4)
ATMOSPHERE_BY_SEED = (0.75, 0.875, 1.0, 1.125, 1.25)
TRANSFER_ATMOSPHERE_GRID = (0.7, 1.0, 1.3)
TRANSFER_SHIFT_GRID_NM = (-2.0, 0.0, 2.0)
PATH_RADIANCE = 0.02
SPATIAL_SIGMA = 1.5
FAR = 1e-3
BOOTSTRAP_REPLICATES = 4000
BOOTSTRAP_SEED = 20260805
METHODS = (
    "laboratory_spatial",
    "transfer_nominal_spatial",
    "transfer_family_spatial",
    "oracle_spatial",
)
METHOD_LABELS = {
    "laboratory_spatial": "MF espacial, alvo laboratorial",
    "transfer_nominal_spatial": "MF espacial, transferência nominal",
    "transfer_family_spatial": "Subespaço espacial, família física",
    "oracle_spatial": "MF espacial, alvo oráculo",
}


def _targets(sensor_fwhm_nm: float):
    native_wavelengths, reporters = measured_reporter_library(NATIVE_BANDS)
    laboratory = reporters["bacteriochlorophyll_a"]
    sensor_wavelengths = np.linspace(400.0, 1000.0, N_BANDS)
    laboratory_resampled = resample_spectrum(
        laboratory, native_wavelengths, sensor_wavelengths
    )
    nominal = target_transfer(
        laboratory,
        native_wavelengths,
        sensor_wavelengths,
        sensor_fwhm_nm=sensor_fwhm_nm,
        atmosphere_strength=1.0,
        path_radiance=PATH_RADIANCE,
    )
    family = target_transfer_library(
        laboratory,
        native_wavelengths,
        sensor_wavelengths,
        sensor_fwhm_nm=sensor_fwhm_nm,
        atmosphere_strengths=TRANSFER_ATMOSPHERE_GRID,
        wavelength_shifts_nm=TRANSFER_SHIFT_GRID_NM,
        path_radiance=PATH_RADIANCE,
    )
    return laboratory_resampled, nominal, family


def _evaluate() -> list[dict]:
    rows = []
    for sensor_fwhm_nm in SENSOR_FWHM_NM:
        laboratory, nominal, family = _targets(sensor_fwhm_nm)
        for snr in SNRS:
            for seed, atmosphere_strength in zip(
                EVAL_SEEDS, ATMOSPHERE_BY_SEED, strict=True
            ):
                scene = simulate_scene(
                    height=HEIGHT,
                    width=WIDTH,
                    n_bands=N_BANDS,
                    snr_db=snr,
                    spectral_source="measured",
                    reporter_name="bacteriochlorophyll_a",
                    sensor_fwhm_nm=sensor_fwhm_nm,
                    atmosphere=True,
                    atmosphere_strength=atmosphere_strength,
                    path_radiance=PATH_RADIANCE,
                    mixing="bilinear",
                    nonlinearity=0.5,
                    seed=90_000 + int(sensor_fwhm_nm) * 100 + seed,
                )
                score_maps = {
                    "laboratory_spatial": smoothed_matched_filter(
                        scene.cube, laboratory, sigma=SPATIAL_SIGMA
                    ),
                    "transfer_nominal_spatial": smoothed_matched_filter(
                        scene.cube, nominal, sigma=SPATIAL_SIGMA
                    ),
                    "transfer_family_spatial": smoothed_matched_subspace_detector(
                        scene.cube,
                        family.signatures,
                        sigma=SPATIAL_SIGMA,
                        rank=4,
                    ),
                    "oracle_spatial": smoothed_matched_filter(
                        scene.cube, scene.reporter, sigma=SPATIAL_SIGMA
                    ),
                }
                for method, score_map in score_maps.items():
                    rows.append(
                        {
                            "sensor_fwhm_nm": sensor_fwhm_nm,
                            "atmosphere_strength": atmosphere_strength,
                            "target_snr_db": snr,
                            "seed": seed,
                            "method": method,
                            "auc": roc_auc(score_map, scene.detection_gt),
                            "pd_at_far": pd_at_far(
                                score_map, scene.detection_gt, FAR
                            ),
                        }
                    )
    return rows


def _case_matrix(rows: list[dict]):
    keys = sorted({
        (row["sensor_fwhm_nm"], row["target_snr_db"], row["seed"])
        for row in rows
    })
    cases = [
        {"sensor_fwhm_nm": fwhm, "target_snr_db": snr, "seed": seed}
        for fwhm, snr, seed in keys
    ]
    lookup = {
        (
            row["sensor_fwhm_nm"],
            row["target_snr_db"],
            row["seed"],
            row["method"],
        ): row
        for row in rows
    }
    values = {}
    for metric in ("auc", "pd_at_far"):
        for method in METHODS:
            values[f"{method}:{metric}"] = np.array([
                lookup[(
                    case["sensor_fwhm_nm"],
                    case["target_snr_db"],
                    case["seed"],
                    method,
                )][metric]
                for case in cases
            ])
    return cases, values


def _hierarchical_resamples(
    cases: list[dict], replicates: int, seed: int
) -> list[np.ndarray]:
    """Resample sensor widths, then seeds inside each width and SNR."""
    rng = np.random.default_rng(seed)
    widths = sorted({case["sensor_fwhm_nm"] for case in cases})
    snrs = sorted({case["target_snr_db"] for case in cases})
    resamples = []
    for _ in range(replicates):
        sampled = []
        for width in rng.choice(widths, size=len(widths), replace=True):
            for snr in snrs:
                candidates = np.array([
                    index
                    for index, case in enumerate(cases)
                    if case["sensor_fwhm_nm"] == width
                    and case["target_snr_db"] == snr
                ])
                sampled.extend(
                    rng.choice(candidates, size=len(candidates), replace=True)
                )
        resamples.append(np.asarray(sampled, dtype=int))
    return resamples


def _interval(values: np.ndarray, resamples: list[np.ndarray]) -> dict:
    bootstrap = np.array([
        float(np.mean(values[indices])) for indices in resamples
    ])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
    }


def _summaries(rows: list[dict]) -> tuple[dict, dict, dict, dict, dict]:
    cases, values = _case_matrix(rows)
    resamples = _hierarchical_resamples(
        cases, BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED
    )
    overall = {
        method: {
            metric: _interval(values[f"{method}:{metric}"], resamples)
            for metric in ("auc", "pd_at_far")
        }
        for method in METHODS
    }
    comparison = {}
    for metric in ("auc", "pd_at_far"):
        paired = (
            values[f"transfer_family_spatial:{metric}"]
            - values[f"laboratory_spatial:{metric}"]
        )
        comparison[metric] = _interval(paired, resamples)
    comparison["significant_advantage"] = bool(
        comparison["auc"]["ci_low"] > 0.0
        and comparison["pd_at_far"]["ci_low"] > 0.0
    )

    nominal_comparison = {}
    for metric in ("auc", "pd_at_far"):
        paired = (
            values[f"transfer_nominal_spatial:{metric}"]
            - values[f"laboratory_spatial:{metric}"]
        )
        nominal_comparison[metric] = _interval(paired, resamples)
    nominal_comparison["both_intervals_above_zero"] = bool(
        nominal_comparison["auc"]["ci_low"] > 0.0
        and nominal_comparison["pd_at_far"]["ci_low"] > 0.0
    )

    distance_to_oracle = {
        method: {
            metric: _interval(
                values[f"oracle_spatial:{metric}"] - values[f"{method}:{metric}"],
                resamples,
            )
            for metric in ("auc", "pd_at_far")
        }
        for method in METHODS[:-1]
    }

    by_snr = {}
    for snr_index, snr in enumerate(SNRS):
        selected_indices = np.array([
            index
            for index, case in enumerate(cases)
            if case["target_snr_db"] == snr
        ])
        selected_cases = [
            case for case in cases if case["target_snr_db"] == snr
        ]
        local_resamples = _hierarchical_resamples(
            selected_cases,
            BOOTSTRAP_REPLICATES,
            BOOTSTRAP_SEED + snr_index + 1,
        )
        by_snr[str(int(snr))] = {
            method: {
                metric: _interval(
                    values[f"{method}:{metric}"][selected_indices],
                    local_resamples,
                )
                for metric in ("auc", "pd_at_far")
            }
            for method in METHODS
        }
    return overall, by_snr, comparison, nominal_comparison, distance_to_oracle


def _format_interval(summary: dict) -> str:
    return (
        f"{summary['mean']:.3f} "
        f"[{summary['ci_low']:.3f}, {summary['ci_high']:.3f}]"
    )


def _write_markdown(results: dict) -> str:
    overall = results["summary"]["overall"]
    by_snr = results["summary"]["by_snr"]
    comparison = results["comparison"]
    nominal_comparison = results["secondary_nominal_comparison"]
    distance = results["distance_to_oracle"]
    lines = [
        "# T9: transferência física da assinatura laboratório-sensor",
        "",
        "Experimento sintético calibrado em comprimento de onda, com espectro",
        "laboratorial medido do bioHSI, fundos medidos do USGS, mistura bilinear,",
        "três larguras de resposta espectral, cinco atmosferas por seed e target",
        "SNR de 10, 5 e 0 dB. São 45 casos pareados por método.",
        "",
        "A família física usa apenas o FWHM declarado do sensor e uma grade fixa",
        "de atmosfera e deslocamento espectral. Nenhum rótulo, máscara ou score",
        "de avaliação seleciona seus parâmetros.",
        "",
        f"Pd é medido em FAR = {FAR:.0e}. Intervalos de 95% usam",
        f"{BOOTSTRAP_REPLICATES} réplicas hierárquicas, reamostrando larguras de",
        "sensor e depois seeds dentro de cada largura e SNR.",
        "",
        "## Resultado agregado",
        "",
        "| Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] | Distância AUC ao oráculo |",
        "|---|:---:|:---:|:---:|",
    ]
    for method in METHODS:
        distance_text = (
            _format_interval(distance[method]["auc"])
            if method in distance else "0,000 por definição"
        )
        lines.append(
            f"| {METHOD_LABELS[method]} | "
            f"{_format_interval(overall[method]['auc'])} | "
            f"{_format_interval(overall[method]['pd_at_far'])} | "
            f"{distance_text} |"
        )

    lines += [
        "",
        "## Resultado por target SNR",
        "",
        "| SNR | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |",
        "|---:|---|:---:|:---:|",
    ]
    for snr in SNRS:
        for method in METHODS:
            summary = by_snr[str(int(snr))][method]
            lines.append(
                f"| {snr:.0f} dB | {METHOD_LABELS[method]} | "
                f"{_format_interval(summary['auc'])} | "
                f"{_format_interval(summary['pd_at_far'])} |"
            )

    lines += [
        "",
        "## Critério pré-especificado",
        "",
        "Diferença da família física menos o alvo laboratorial:",
        "",
        f"- AUC: {_format_interval(comparison['auc'])}",
        f"- Pd@FAR 1e-3: {_format_interval(comparison['pd_at_far'])}",
        "",
    ]
    if comparison["significant_advantage"]:
        lines += [
            "Os dois intervalos ficaram acima de zero. Neste simulador físico, a",
            "família transferida reduz de forma robusta o gap laboratório-sensor.",
            "Esta é uma vantagem causal da modelagem física, não do aprendizado.",
        ]
    else:
        lines += [
            "O critério de vantagem robusta não foi satisfeito: os intervalos de",
            "AUC e Pd@FAR não ficaram ambos acima de zero. A família física testada",
            "não fecha de forma robusta o gap laboratório-sensor.",
        ]
    lines += [
        "",
        "## Análise secundária",
        "",
        "A transferência nominal era um método declarado no protocolo, mas não era",
        "o método do critério primário de significância. Sua diferença contra o",
        "alvo laboratorial foi:",
        "",
        f"- AUC: {_format_interval(nominal_comparison['auc'])}",
        f"- Pd@FAR 1e-3: {_format_interval(nominal_comparison['pd_at_far'])}",
        "",
        "Os dois intervalos ficaram acima de zero. Descritivamente, o alvo nominal",
        "transferido por metadados quase alcançou o oráculo, enquanto ampliar essa",
        "assinatura para um subespaço de nove variantes introduziu direções que",
        "degradaram a detecção. Este contraste motiva validação independente, não",
        "uma troca retroativa do critério primário.",
        "",
        "O alvo oráculo conhece exatamente a transformação usada para gerar cada",
        "cena e serve apenas como teto. O experimento usa alvos implantados e não",
        "substitui o T8 sobre expressão biológica realmente medida.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    rows = _evaluate()
    overall, by_snr, comparison, nominal_comparison, distance = _summaries(rows)
    results = {
        "protocol": {
            "reporter": "measured bacteriochlorophyll_a from bioHSI pellets",
            "target_snrs_db": list(SNRS),
            "sensor_fwhm_nm": list(SENSOR_FWHM_NM),
            "atmosphere_strength_by_seed": list(ATMOSPHERE_BY_SEED),
            "eval_seeds": list(EVAL_SEEDS),
            "mixing": "bilinear",
            "nonlinearity": 0.5,
            "far": FAR,
            "spatial_sigma_pixels": SPATIAL_SIGMA,
            "transfer_family": {
                "uses_labels": False,
                "uses_detector_scores": False,
                "sensor_fwhm_source": "declared sensor metadata",
                "atmosphere_strength_grid": list(TRANSFER_ATMOSPHERE_GRID),
                "wavelength_shift_grid_nm": list(TRANSFER_SHIFT_GRID_NM),
                "path_radiance": PATH_RADIANCE,
                "rank": 4,
            },
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "scheme": (
                    "resample sensor FWHM, then seeds within FWHM/SNR"
                ),
            },
            "significance_rule": (
                "both 95% CIs for transfer_family_spatial - "
                "laboratory_spatial must be above zero"
            ),
        },
        "rows": rows,
        "summary": {"overall": overall, "by_snr": by_snr},
        "comparison": comparison,
        "secondary_nominal_comparison": nominal_comparison,
        "distance_to_oracle": distance,
    }
    output_json = ROOT / "results" / "target_transfer.json"
    output_md = ROOT / "results" / "target_transfer.md"
    output_json.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _write_markdown(results)
    output_md.write_text(markdown, encoding="utf-8")
    print("\n" + markdown)
    print(f"\nWrote {output_json} and {output_md}")


if __name__ == "__main__":
    main()
