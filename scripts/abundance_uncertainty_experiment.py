"""Calibrate abundance estimates and grouped prediction intervals without leakage.

The unmixer is trained on simulated backgrounds. Separate target implants are
used for affine scale calibration, conformal residual calibration and final
evaluation. Scene-seed cases, rather than pixels, are the bootstrap units.

    .venv-train/bin/python scripts/abundance_uncertainty_experiment.py

Writes ``results/abundance_uncertainty.json``, ``.md`` and ``.png``.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hypermix import (
    CaseBalancedAffineCalibrator,
    GroupedConformalInterval,
    implant_target,
    interval_coverage,
    load_mat_cube,
    mean_absolute_error,
    mean_bias,
    mean_interval_width,
    pearson_r,
    reporter_library,
    spectral_matched_filter,
)
from hypermix.detector import AbundanceUnmixer, make_training_set


ROOT = Path(__file__).resolve().parents[1]
SCENES = ("indian_pines", "salinas", "paviaU")
SNRS = (10.0, 5.0)
SCALE_CALIBRATION_SEEDS = (100, 101)
INTERVAL_CALIBRATION_SEEDS = (200, 201)
EVALUATION_SEEDS = (0, 1, 2, 3)
METHODS = ("matched_filter", "unmixer")
METHOD_LABELS = {
    "matched_filter": "MF calibrado",
    "unmixer": "Unmixer calibrado",
}
TARGET_THRESHOLD = 0.02
INTERVAL_ALPHA = 0.10
TRAINING_SCENES = 28
TRAINING_HW = 96
TRAINING_EPOCHS = 30
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 20260807
METRICS = ("mae", "bias", "abs_bias", "pearson_r", "coverage", "width")


def _implantation_seed(
    split_index: int,
    scene_index: int,
    snr_index: int,
    seed: int,
) -> int:
    return (
        500_000
        + 100_000 * split_index
        + 10_000 * scene_index
        + 1_000 * snr_index
        + seed
    )


def _train_unmixer() -> AbundanceUnmixer:
    target = reporter_library(200)["bacteriochlorophyll_a"]
    print("Construindo treino simulado do unmixer...")
    features, _, abundance = make_training_set(
        target,
        n_scenes=TRAINING_SCENES,
        hw=TRAINING_HW,
        with_abundance=True,
    )
    print(f"  {features.shape[0]:,} pixels, {features.shape[1]} features")
    print("Treinando unmixer...")
    return AbundanceUnmixer(features.shape[1], seed=0).fit(
        features,
        abundance,
        epochs=TRAINING_EPOCHS,
    )


def _raw_predictions(
    scene: np.ndarray,
    target: np.ndarray,
    unmixer: AbundanceUnmixer,
) -> dict[str, np.ndarray]:
    return {
        "matched_filter": spectral_matched_filter(scene, target),
        "unmixer": unmixer.predict_map(scene, target),
    }


def _collect_split(
    unmixer: AbundanceUnmixer,
    seeds: tuple[int, ...],
    split_index: int,
) -> list[dict]:
    cases = []
    for scene_index, scene_name in enumerate(SCENES):
        cube = load_mat_cube(str(ROOT / "data" / f"{scene_name}.mat"))
        target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        print(f"{scene_name}: {cube.shape}")
        for snr_index, snr in enumerate(SNRS):
            for seed in seeds:
                implantation_seed = _implantation_seed(
                    split_index, scene_index, snr_index, seed
                )
                scene, _, abundance, target_used = implant_target(
                    cube,
                    np.random.default_rng(implantation_seed),
                    target=target,
                    snr_db=snr,
                    detection_threshold=TARGET_THRESHOLD,
                )
                mask = abundance > TARGET_THRESHOLD
                raw = _raw_predictions(scene, target_used, unmixer)
                case_id = f"{scene_name}|{snr:g}|{seed}"
                cases.append({
                    "case_id": case_id,
                    "scene": scene_name,
                    "target_snr_db": snr,
                    "seed": seed,
                    "implantation_seed": implantation_seed,
                    "truth": abundance[mask].astype(np.float64),
                    "raw": {
                        method: values[mask].astype(np.float64)
                        for method, values in raw.items()
                    },
                })
    return cases


def _fit_scale_calibrators(cases: list[dict]) -> dict:
    calibrators = {}
    for method in METHODS:
        predicted = np.concatenate([case["raw"][method] for case in cases])
        truth = np.concatenate([case["truth"] for case in cases])
        case_ids = np.concatenate([
            np.full(case["truth"].size, index, dtype=np.int64)
            for index, case in enumerate(cases)
        ])
        calibrators[method] = CaseBalancedAffineCalibrator().fit(
            predicted, truth, case_ids
        )
    return calibrators


def _fit_intervals(cases: list[dict], calibrators: dict) -> dict:
    intervals = {}
    for method in METHODS:
        predicted = np.concatenate([
            calibrators[method].predict(case["raw"][method]) for case in cases
        ])
        truth = np.concatenate([case["truth"] for case in cases])
        case_ids = np.concatenate([
            np.full(case["truth"].size, index, dtype=np.int64)
            for index, case in enumerate(cases)
        ])
        intervals[method] = GroupedConformalInterval(
            alpha=INTERVAL_ALPHA
        ).fit(predicted, truth, case_ids)
    return intervals


def _evaluate(
    cases: list[dict],
    calibrators: dict,
    intervals: dict,
) -> list[dict]:
    rows = []
    for case in cases:
        truth = case["truth"]
        for method in METHODS:
            predicted = calibrators[method].predict(case["raw"][method])
            lower, upper = intervals[method].predict(predicted)
            bias = mean_bias(predicted, truth)
            rows.append({
                "case_id": case["case_id"],
                "scene": case["scene"],
                "target_snr_db": case["target_snr_db"],
                "seed": case["seed"],
                "implantation_seed": case["implantation_seed"],
                "method": method,
                "mae": mean_absolute_error(predicted, truth),
                "bias": bias,
                "abs_bias": abs(bias),
                "pearson_r": pearson_r(predicted, truth),
                "coverage": interval_coverage(lower, upper, truth),
                "width": mean_interval_width(lower, upper),
                "target_pixels": int(truth.size),
            })
    return rows


def _bootstrap_indices(count: int) -> list[np.ndarray]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    return [rng.integers(0, count, size=count) for _ in range(BOOTSTRAP_REPLICATES)]


def _interval(values: np.ndarray, resamples: list[np.ndarray]) -> dict:
    bootstrap = np.asarray([np.mean(values[index]) for index in resamples])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
    }


def _summaries(rows: list[dict]) -> tuple[dict, dict, dict]:
    case_ids = sorted({row["case_id"] for row in rows})
    resamples = _bootstrap_indices(len(case_ids))
    by_key = {(row["case_id"], row["method"]): row for row in rows}
    aggregate = {}
    for method in METHODS:
        aggregate[method] = {}
        for metric in METRICS:
            values = np.asarray([by_key[(case, method)][metric] for case in case_ids])
            aggregate[method][metric] = _interval(values, resamples)

    differences = {}
    for metric in ("mae", "abs_bias", "coverage", "width"):
        values = np.asarray([
            by_key[(case, "unmixer")][metric]
            - by_key[(case, "matched_filter")][metric]
            for case in case_ids
        ])
        differences[metric] = _interval(values, resamples)

    by_scene = {}
    for scene in SCENES:
        scene_cases = [
            case for case in case_ids
            if by_key[(case, "matched_filter")]["scene"] == scene
        ]
        scene_resamples = _bootstrap_indices(len(scene_cases))
        by_scene[scene] = {}
        for method in METHODS:
            by_scene[scene][method] = {}
            for metric in ("mae", "bias", "coverage", "width"):
                values = np.asarray([
                    by_key[(case, method)][metric] for case in scene_cases
                ])
                by_scene[scene][method][metric] = _interval(
                    values, scene_resamples
                )
    return aggregate, differences, by_scene


def _verdict(aggregate: dict, differences: dict) -> dict:
    point_win = differences["mae"]["ci_high"] < 0.0
    coverage_valid = all(
        aggregate[method]["coverage"]["mean"] >= 1.0 - INTERVAL_ALPHA
        for method in METHODS
    )
    interval_win = coverage_valid and differences["width"]["ci_high"] < 0.0
    if point_win and interval_win:
        conclusion = "unmixer_wins_point_and_interval_efficiency"
    elif point_win:
        conclusion = "unmixer_wins_mae_only"
    elif interval_win:
        conclusion = "unmixer_wins_interval_efficiency_only"
    else:
        conclusion = "no_calibrated_abundance_advantage"
    return {
        "conclusion": conclusion,
        "point_win": point_win,
        "interval_win": interval_win,
        "coverage_target_met_by_both": coverage_valid,
        "pre_specified_rule": (
            "Vitória pontual exige que o IC bootstrap pareado de 95% para MAE "
            "do unmixer menos MF fique abaixo de zero. Vitória em eficiência "
            "dos intervalos exige também cobertura média de pelo menos 0,90 "
            "nos dois métodos e IC de 95% da diferença de largura abaixo de zero."
        ),
    }


def _format_interval(summary: dict, digits: int = 4) -> str:
    return (
        f"{summary['mean']:.{digits}f} "
        f"[{summary['ci_low']:.{digits}f}, {summary['ci_high']:.{digits}f}]"
    )


def _markdown(result: dict) -> str:
    lines = [
        "# T12: abundância calibrada e intervalos",
        "",
        "O unmixer é treinado em simulação. A escala afim, o raio conformal e a",
        "avaliação usam implantes e seeds disjuntos. Cada cena-seed tem peso igual",
        "na calibração e é a unidade do bootstrap. A análise é condicional aos",
        f"pixels com abundância maior que {TARGET_THRESHOLD:.2f}.",
        "",
        "## Resultado agregado",
        "",
        "| Método | MAE [IC 95%] | Viés [IC 95%] | Cobertura 90% [IC 95%] | Largura [IC 95%] |",
        "|---|:---:|:---:|:---:|:---:|",
    ]
    for method in METHODS:
        summary = result["aggregate"][method]
        lines.append(
            f"| {METHOD_LABELS[method]} | {_format_interval(summary['mae'])} | "
            f"{_format_interval(summary['bias'])} | "
            f"{_format_interval(summary['coverage'], 3)} | "
            f"{_format_interval(summary['width'])} |"
        )
    lines += [
        "",
        "## Diferença pareada, unmixer menos MF",
        "",
        "| Métrica | Diferença [IC 95%] |",
        "|---|:---:|",
    ]
    labels = {
        "mae": "MAE",
        "abs_bias": "Viés absoluto",
        "coverage": "Cobertura",
        "width": "Largura",
    }
    for metric, label in labels.items():
        digits = 3 if metric == "coverage" else 4
        lines.append(
            f"| {label} | {_format_interval(result['differences'][metric], digits)} |"
        )
    lines += [
        "",
        "## Por cena",
        "",
        "| Cena | Método | MAE | Viés | Cobertura | Largura |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for scene in SCENES:
        for method in METHODS:
            summary = result["by_scene"][scene][method]
            lines.append(
                f"| {scene} | {METHOD_LABELS[method]} | "
                f"{summary['mae']['mean']:.4f} | {summary['bias']['mean']:.4f} | "
                f"{summary['coverage']['mean']:.3f} | {summary['width']['mean']:.4f} |"
            )
    verdict = result["verdict"]
    lines += [
        "",
        "## Critério pré-especificado",
        "",
        verdict["pre_specified_rule"],
        "",
        f"Resultado codificado: `{verdict['conclusion']}`.",
        "",
        "## Limitações",
        "",
        "- Os intervalos são condicionais a pixels já declarados como alvo. Isto",
        "  não inclui a incerteza de errar a detecção.",
        "- Calibração e avaliação usam implantes diferentes nos mesmos três fundos",
        "  reais. Não há validação em uma nova população de sensores.",
        "- A abundância é fração do simulador, não concentração biológica.",
        "- O raio é constante e deliberadamente conservador. Pixels dentro de uma",
        "  cena são correlacionados, por isso a calibração ocorre em dois níveis:",
        "  quantil dentro do caso e quantil entre casos.",
        "- O unmixer usa features derivados de MF e ACE. Uma vantagem quantitativa",
        "  não altera o veredito de detecção do benchmark.",
    ]
    return "\n".join(lines) + "\n"


def _plot(result: dict, output: Path) -> None:
    colors = {"matched_filter": "#167c80", "unmixer": "#d5933b"}
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    x = np.arange(len(SCENES))
    width = 0.36
    for offset, method in enumerate(METHODS):
        means = [result["by_scene"][scene][method]["mae"]["mean"] for scene in SCENES]
        lows = [result["by_scene"][scene][method]["mae"]["ci_low"] for scene in SCENES]
        highs = [result["by_scene"][scene][method]["mae"]["ci_high"] for scene in SCENES]
        axes[0].bar(
            x + (offset - 0.5) * width,
            means,
            width,
            color=colors[method],
            label=METHOD_LABELS[method],
            yerr=[np.asarray(means) - lows, np.asarray(highs) - means],
            capsize=3,
        )
    axes[0].set_xticks(x, SCENES)
    axes[0].set_ylabel("MAE nos pixels de alvo")
    axes[0].set_title("Erro de abundância calibrada")
    axes[0].legend(frameon=False)
    for method in METHODS:
        coverage = result["aggregate"][method]["coverage"]
        interval_width = result["aggregate"][method]["width"]
        axes[1].errorbar(
            coverage["mean"],
            interval_width["mean"],
            xerr=[[coverage["mean"] - coverage["ci_low"]], [coverage["ci_high"] - coverage["mean"]]],
            yerr=[[interval_width["mean"] - interval_width["ci_low"]], [interval_width["ci_high"] - interval_width["mean"]]],
            fmt="o",
            markersize=8,
            capsize=3,
            color=colors[method],
            label=METHOD_LABELS[method],
        )
    axes[1].axvline(0.90, color="#555", linestyle="--", linewidth=1)
    axes[1].set_xlabel("Cobertura empírica")
    axes[1].set_ylabel("Largura média do intervalo")
    axes[1].set_title("Intervalos conformais agrupados de 90%")
    axes[1].legend(frameon=False)
    figure.suptitle("HyperMix T12: abundância calibrada", fontweight="bold")
    figure.tight_layout()
    figure.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    unmixer = _train_unmixer()
    print("\nSplit 1/3: calibração da escala...")
    scale_cases = _collect_split(unmixer, SCALE_CALIBRATION_SEEDS, split_index=1)
    calibrators = _fit_scale_calibrators(scale_cases)
    print("\nSplit 2/3: calibração dos resíduos...")
    interval_cases = _collect_split(
        unmixer, INTERVAL_CALIBRATION_SEEDS, split_index=2
    )
    intervals = _fit_intervals(interval_cases, calibrators)
    print("\nSplit 3/3: avaliação final...")
    evaluation_cases = _collect_split(unmixer, EVALUATION_SEEDS, split_index=3)
    rows = _evaluate(evaluation_cases, calibrators, intervals)
    aggregate, differences, by_scene = _summaries(rows)
    result = {
        "protocol": {
            "target": "bacteriochlorophyll_a",
            "target_threshold": TARGET_THRESHOLD,
            "target_snr_db": list(SNRS),
            "scenes": list(SCENES),
            "training": {
                "simulated_scenes": TRAINING_SCENES,
                "height_width": TRAINING_HW,
                "epochs": TRAINING_EPOCHS,
            },
            "scale_calibration_seeds": list(SCALE_CALIBRATION_SEEDS),
            "interval_calibration_seeds": list(INTERVAL_CALIBRATION_SEEDS),
            "evaluation_seeds": list(EVALUATION_SEEDS),
            "interval_alpha": INTERVAL_ALPHA,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_unit": "scene-SNR-seed case, paired by method",
        },
        "calibrators": {
            method: {
                "slope": calibrators[method].slope_,
                "intercept": calibrators[method].intercept_,
                "interval_radius": intervals[method].radius_,
                "case_radii": intervals[method].case_radii_.tolist(),
            }
            for method in METHODS
        },
        "aggregate": aggregate,
        "differences": differences,
        "by_scene": by_scene,
        "verdict": _verdict(aggregate, differences),
        "rows": rows,
    }
    output_json = ROOT / "results" / "abundance_uncertainty.json"
    output_md = ROOT / "results" / "abundance_uncertainty.md"
    output_png = ROOT / "results" / "abundance_uncertainty.png"
    output_json.write_text(json.dumps(result, indent=2) + "\n")
    output_md.write_text(_markdown(result))
    _plot(result, output_png)
    print(f"\nResultado: {result['verdict']['conclusion']}")
    for method in METHODS:
        summary = aggregate[method]
        print(
            f"{METHOD_LABELS[method]}: MAE {_format_interval(summary['mae'])}, "
            f"coverage {_format_interval(summary['coverage'], 3)}, "
            f"width {_format_interval(summary['width'])}"
        )
    print(f"Artefatos: {output_json}, {output_md}, {output_png}")


if __name__ == "__main__":
    main()
