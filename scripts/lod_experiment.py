"""Estimate sensor-specific detection limits with fixed FAR calibration.

Thresholds are fitted only on target-free calibration scenes.  Evaluation uses
different seeds and a sensor-specific absolute noise floor fixed at a reference
abundance, so lowering abundance does not also lower the simulated noise.

    .venv/bin/python scripts/lod_experiment.py

Writes ``results/lod.json``, ``results/lod.md`` and ``results/lod_curves.png``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from hypermix import (
    detection_probability_at_threshold,
    grid_detection_limit,
    robust_standardize_scores,
    roc_auc,
    simulate_scene,
    spectral_matched_filter,
    threshold_at_far,
)


ROOT = Path(__file__).resolve().parents[1]
SENSOR_FWHM_NM = (8.0, 12.0, 20.0)
ABUNDANCES = np.array((0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20))
FAR_BUDGETS = (1e-2, 1e-3)
CALIBRATION_SEEDS = tuple(range(100, 108))
EVALUATION_SEEDS = tuple(range(12))
REFERENCE_ABUNDANCE = 0.15
REFERENCE_TARGET_SNR_DB = 5.0
TARGET_PD = 0.80
RELATIVE_DETECTION_THRESHOLD = 0.20
HEIGHT = 72
WIDTH = 72
N_BANDS = 61
SPATIAL_SIGMA = 1.5
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 20260806


def _clean_scene(sensor_fwhm_nm: float, abundance: float, seed: int):
    threshold = RELATIVE_DETECTION_THRESHOLD * abundance
    return simulate_scene(
        height=HEIGHT,
        width=WIDTH,
        n_bands=N_BANDS,
        snr_db=np.inf,
        reporter_max_abundance=abundance,
        detection_threshold=threshold,
        spectral_source="measured",
        reporter_name="bacteriochlorophyll_a",
        sensor_fwhm_nm=sensor_fwhm_nm,
        atmosphere=True,
        atmosphere_strength=1.0,
        path_radiance=0.02,
        mixing="linear",
        seed=seed,
    )


def _sensor_noise_std(sensor_fwhm_nm: float) -> float:
    reference_rms = []
    for seed in CALIBRATION_SEEDS:
        background = _clean_scene(sensor_fwhm_nm, 0.0, seed)
        reference = _clean_scene(
            sensor_fwhm_nm, REFERENCE_ABUNDANCE, seed
        )
        signal = reference.cube.astype(np.float64) - background.cube
        reference_rms.append(
            float(np.sqrt(np.mean(signal[reference.detection_gt] ** 2)))
        )
    return float(np.mean(reference_rms)) / (
        10.0 ** (REFERENCE_TARGET_SNR_DB / 20.0)
    )


def _score(cube: np.ndarray, target: np.ndarray) -> np.ndarray:
    raw = spectral_matched_filter(cube, target)
    spatial = gaussian_filter(raw, sigma=SPATIAL_SIGMA, mode="reflect")
    return robust_standardize_scores(spatial)


def _noise(sensor_index: int, seed: int, noise_std: float) -> np.ndarray:
    rng = np.random.default_rng(300_000 + 10_000 * sensor_index + seed)
    return rng.normal(0.0, noise_std, size=(HEIGHT, WIDTH, N_BANDS))


def _calibrate_thresholds(
    sensor_index: int,
    sensor_fwhm_nm: float,
    noise_std: float,
) -> dict[float, float]:
    background_scores = []
    for seed in CALIBRATION_SEEDS:
        scene = _clean_scene(sensor_fwhm_nm, 0.0, seed)
        noise = _noise(sensor_index, seed + 1_000, noise_std)
        background_scores.append(_score(scene.cube + noise, scene.reporter).ravel())
    return {
        far: max(threshold_at_far(scores, far) for scores in background_scores)
        for far in FAR_BUDGETS
    }


def _evaluate() -> tuple[list[dict], list[dict], dict]:
    rows = []
    far_rows = []
    sensor_settings = {}
    for sensor_index, sensor_fwhm_nm in enumerate(SENSOR_FWHM_NM):
        noise_std = _sensor_noise_std(sensor_fwhm_nm)
        thresholds = _calibrate_thresholds(
            sensor_index, sensor_fwhm_nm, noise_std
        )
        sensor_settings[str(int(sensor_fwhm_nm))] = {
            "absolute_noise_std": noise_std,
            "thresholds": {str(far): value for far, value in thresholds.items()},
        }
        print(
            f"FWHM {sensor_fwhm_nm:.0f} nm: noise {noise_std:.6f}, "
            + ", ".join(
                f"threshold@{far:.0e} {thresholds[far]:.3f}"
                for far in FAR_BUDGETS
            )
        )

        for seed in EVALUATION_SEEDS:
            background = _clean_scene(sensor_fwhm_nm, 0.0, seed)
            noise = _noise(sensor_index, seed, noise_std)
            background_score = _score(
                background.cube + noise, background.reporter
            )
            for far, threshold in thresholds.items():
                far_rows.append(
                    {
                        "sensor_fwhm_nm": sensor_fwhm_nm,
                        "far_budget": far,
                        "seed": seed,
                        "realized_far": float(
                            np.mean(background_score > threshold)
                        ),
                    }
                )

            for abundance in ABUNDANCES:
                scene = _clean_scene(sensor_fwhm_nm, float(abundance), seed)
                score = _score(scene.cube + noise, scene.reporter)
                auc = roc_auc(score, scene.detection_gt)
                for far, threshold in thresholds.items():
                    pd, _ = detection_probability_at_threshold(
                        score, scene.detection_gt, threshold
                    )
                    rows.append(
                        {
                            "sensor_fwhm_nm": sensor_fwhm_nm,
                            "max_abundance": float(abundance),
                            "far_budget": far,
                            "seed": seed,
                            "pd": pd,
                            "auc": auc,
                            "positive_pixels": int(scene.detection_gt.sum()),
                        }
                    )
    return rows, far_rows, sensor_settings


def _bootstrap_indices(replicates: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    count = len(EVALUATION_SEEDS)
    return [rng.integers(0, count, size=count) for _ in range(replicates)]


def _interval(values: np.ndarray, resamples: list[np.ndarray]) -> dict:
    bootstrap = np.asarray([
        float(np.mean(values[indices])) for indices in resamples
    ])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
    }


def _summaries(rows: list[dict], far_rows: list[dict]) -> dict:
    resamples = _bootstrap_indices(BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED)
    curves = {}
    limits = {}
    far_validation = {}
    for sensor_fwhm_nm in SENSOR_FWHM_NM:
        sensor_key = str(int(sensor_fwhm_nm))
        curves[sensor_key] = {}
        limits[sensor_key] = {}
        far_validation[sensor_key] = {}
        for far in FAR_BUDGETS:
            far_key = f"{far:.0e}"
            point_summaries = []
            for abundance in ABUNDANCES:
                selected = sorted(
                    (
                        row for row in rows
                        if row["sensor_fwhm_nm"] == sensor_fwhm_nm
                        and row["far_budget"] == far
                        and row["max_abundance"] == float(abundance)
                    ),
                    key=lambda row: row["seed"],
                )
                point_summaries.append(
                    {
                        "max_abundance": float(abundance),
                        "pd": _interval(
                            np.asarray([row["pd"] for row in selected]),
                            resamples,
                        ),
                        "auc": _interval(
                            np.asarray([row["auc"] for row in selected]),
                            resamples,
                        ),
                    }
                )
            curves[sensor_key][far_key] = point_summaries

            validation_rows = sorted(
                (
                    row for row in far_rows
                    if row["sensor_fwhm_nm"] == sensor_fwhm_nm
                    and row["far_budget"] == far
                ),
                key=lambda row: row["seed"],
            )
            far_summary = _interval(
                np.asarray([row["realized_far"] for row in validation_rows]),
                resamples,
            )
            budget_valid = bool(far_summary["mean"] <= far)
            far_validation[sensor_key][far_key] = {
                **far_summary,
                "budget_valid_on_mean": budget_valid,
            }

            means = np.asarray([point["pd"]["mean"] for point in point_summaries])
            lower = np.asarray([point["pd"]["ci_low"] for point in point_summaries])
            nominal = grid_detection_limit(ABUNDANCES, means, TARGET_PD)
            conservative = grid_detection_limit(ABUNDANCES, lower, TARGET_PD)
            limits[sensor_key][far_key] = {
                "nominal_lod": nominal if budget_valid else None,
                "conservative_lod": conservative if budget_valid else None,
                "pd_target": TARGET_PD,
                "far_budget_valid": budget_valid,
                "unqualified_nominal_crossing": nominal,
                "unqualified_conservative_crossing": conservative,
            }
    return {
        "curves": curves,
        "limits": limits,
        "far_validation": far_validation,
    }


def _format_interval(summary: dict, digits: int = 3) -> str:
    return (
        f"{summary['mean']:.{digits}f} "
        f"[{summary['ci_low']:.{digits}f}, {summary['ci_high']:.{digits}f}]"
    )


def _lod_text(value: float | None) -> str:
    if value is None:
        return f"> {100 * ABUNDANCES[-1]:.1f}% ou não validado"
    return f"{100 * value:.1f}%"


def _write_markdown(results: dict) -> str:
    summary = results["summary"]
    lines = [
        "# T11: limite operacional de detecção",
        "",
        "Este experimento estima a menor abundância máxima testada que mantém",
        f"Pd maior ou igual a {TARGET_PD:.2f} em todos os níveis superiores.",
        "O LOD nominal usa a média de 12 seeds. O LOD conservador exige que o",
        "limite inferior do IC de 95% também alcance a meta. Não há interpolação",
        "entre pontos da grade.",
        "",
        "O ruído é absoluto e fixo por sensor. Ele é calibrado para target SNR",
        f"{REFERENCE_TARGET_SNR_DB:.0f} dB em {100 * REFERENCE_ABUNDANCE:.0f}% de",
        "abundância e não diminui quando a abundância do teste cai. Thresholds",
        "são ajustados em oito cenas sem alvo e avaliados em 12 seeds diferentes.",
        "A regra final usa o maior threshold entre as cenas de calibração, não o",
        "quantil agrupado. Uma auditoria piloto rejeitou o quantil agrupado porque",
        "ele excedeu o FAR em cinco dos seis cenários de validação.",
        "O MF espacial recebe o alvo exato no sensor; portanto os LODs são um teto",
        "algorítmico condicionado a este detector, não garantia de campo.",
        "",
        "## LOD por sensor e orçamento de falso-alarme",
        "",
        "| FWHM | FAR alvo | FAR obtido [IC 95%] | Budget válido | LOD nominal | LOD conservador |",
        "|---:|---:|:---:|:---:|:---:|:---:|",
    ]
    for sensor_fwhm_nm in SENSOR_FWHM_NM:
        sensor_key = str(int(sensor_fwhm_nm))
        for far in FAR_BUDGETS:
            far_key = f"{far:.0e}"
            validation = summary["far_validation"][sensor_key][far_key]
            limit = summary["limits"][sensor_key][far_key]
            lines.append(
                f"| {sensor_fwhm_nm:.0f} nm | {far:.0e} | "
                f"{_format_interval(validation, digits=5)} | "
                f"{'sim' if limit['far_budget_valid'] else 'não'} | "
                f"{_lod_text(limit['nominal_lod'])} | "
                f"{_lod_text(limit['conservative_lod'])} |"
            )

    lines += [
        "",
        "## Curvas de Pd",
        "",
        "| FWHM | FAR | Abundância | Pd média [IC 95%] | AUC [IC 95%] |",
        "|---:|---:|---:|:---:|:---:|",
    ]
    for sensor_fwhm_nm in SENSOR_FWHM_NM:
        sensor_key = str(int(sensor_fwhm_nm))
        for far in FAR_BUDGETS:
            far_key = f"{far:.0e}"
            for point in summary["curves"][sensor_key][far_key]:
                lines.append(
                    f"| {sensor_fwhm_nm:.0f} nm | {far:.0e} | "
                    f"{100 * point['max_abundance']:.1f}% | "
                    f"{_format_interval(point['pd'])} | "
                    f"{_format_interval(point['auc'])} |"
                )

    lines += [
        "",
        "## Limites de interpretação",
        "",
        "- O resultado usa espectros medidos, fundos USGS simulados, atmosfera",
        "  simples, mistura linear e alvos implantados como blobs.",
        "- A abundância máxima do blob é um parâmetro do simulador, não uma",
        "  concentração biológica diretamente mensurada.",
        "- FWHM isolado não representa todos os efeitos de um sensor. Ruído, PSF,",
        "  amostragem e calibração também afetam o LOD real.",
        "- Se o FAR médio de validação exceder o orçamento, o LOD correspondente",
        "  é reportado como não validado mesmo que a curva de Pd cruze 0,80.",
        "",
    ]
    return "\n".join(lines)


def _plot(results: dict, path: Path) -> None:
    import matplotlib.pyplot as plt

    summary = results["summary"]
    figure, axes = plt.subplots(1, len(FAR_BUDGETS), figsize=(11, 4.2), sharey=True)
    colors = ("#355c4d", "#e36b3d", "#355c8a")
    x = 100 * ABUNDANCES
    for axis, far in zip(axes, FAR_BUDGETS, strict=True):
        far_key = f"{far:.0e}"
        for color, sensor_fwhm_nm in zip(colors, SENSOR_FWHM_NM, strict=True):
            points = summary["curves"][str(int(sensor_fwhm_nm))][far_key]
            mean = np.asarray([point["pd"]["mean"] for point in points])
            low = np.asarray([point["pd"]["ci_low"] for point in points])
            high = np.asarray([point["pd"]["ci_high"] for point in points])
            axis.plot(x, mean, marker="o", color=color, label=f"{sensor_fwhm_nm:.0f} nm")
            axis.fill_between(x, low, high, color=color, alpha=0.14)
        axis.axhline(TARGET_PD, color="#222222", linestyle="--", linewidth=1)
        axis.set_title(f"FAR alvo {far:.0e}")
        axis.set_xlabel("Abundância máxima (%)")
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("Probabilidade de detecção")
    axes[-1].legend(title="FWHM do sensor", frameon=False)
    figure.suptitle("HyperMix: curvas operacionais de limite de detecção")
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    rows, far_rows, sensor_settings = _evaluate()
    summary = _summaries(rows, far_rows)
    results = {
        "protocol": {
            "sensor_fwhm_nm": list(SENSOR_FWHM_NM),
            "abundance_grid": ABUNDANCES.tolist(),
            "far_budgets": list(FAR_BUDGETS),
            "calibration_seeds": list(CALIBRATION_SEEDS),
            "evaluation_seeds": list(EVALUATION_SEEDS),
            "reference_abundance": REFERENCE_ABUNDANCE,
            "reference_target_snr_db": REFERENCE_TARGET_SNR_DB,
            "target_pd": TARGET_PD,
            "relative_detection_threshold": RELATIVE_DETECTION_THRESHOLD,
            "spatial_sigma_pixels": SPATIAL_SIGMA,
            "target": "measured bacteriochlorophyll_a at sensor",
            "threshold_source": "independent target-free calibration scenes",
            "threshold_aggregation": (
                "maximum of per-calibration-scene thresholds; pooled quantile "
                "was rejected in a protocol pilot after FAR transfer failure"
            ),
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "unit": "evaluation seed, paired across abundance",
            },
        },
        "sensor_settings": sensor_settings,
        "rows": rows,
        "far_validation_rows": far_rows,
        "summary": summary,
    }
    output_json = ROOT / "results" / "lod.json"
    output_md = ROOT / "results" / "lod.md"
    output_plot = ROOT / "results" / "lod_curves.png"
    output_json.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _write_markdown(results)
    output_md.write_text(markdown, encoding="utf-8")
    _plot(results, output_plot)
    print("\n" + markdown)
    print(f"\nWrote {output_json}, {output_md} and {output_plot}")


if __name__ == "__main__":
    main()
