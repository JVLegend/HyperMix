"""Calibrate detector probabilities without leaking evaluation labels.

For every real scene and target SNR, two implanted realizations form the
calibration split and four disjoint realizations form the evaluation split.
Classical scores receive Platt scaling. Learned logits receive temperature
scaling with an intercept correction, both for one network and a three-member
deep ensemble trained only on simulated backgrounds.

    .venv-train/bin/python scripts/uncertainty_experiment.py

Writes ``results/uncertainty.json``, ``results/uncertainty.md`` and
``assets/reliability_uncertainty.png``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.special import expit, logit

from hypermix import (
    binary_nll,
    brier_score,
    expected_calibration_error,
    implant_target,
    load_mat_cube,
    pd_at_far,
    reliability_curve,
    reporter_library,
    roc_auc,
    spectral_matched_filter,
)
from hypermix.calibration import PlattCalibrator, TemperatureCalibrator
from hypermix.detector import SpectralDetector, make_training_set, pixel_features


ROOT = Path(__file__).resolve().parents[1]
SCENES = ("indian_pines", "salinas", "paviaU")
SNRS = (5.0, 0.0)
CALIBRATION_SEEDS = (100, 101)
EVALUATION_SEEDS = (0, 1, 2, 3)
METHODS = (
    "mf_platt",
    "mf_spatial_platt",
    "learned_temperature",
    "learned_ensemble_temperature",
)
METHOD_LABELS = {
    "mf_platt": "MF + Platt",
    "mf_spatial_platt": "MF espacial + Platt",
    "learned_temperature": "Aprendido + temperatura",
    "learned_ensemble_temperature": "Ensemble aprendido + temperatura",
}
SPATIAL_SIGMA = 1.5
FAR = 1e-3
ECE_BINS = 15
ENSEMBLE_SEEDS = (0, 1, 2)
TRAINING_SCENES = 28
TRAINING_HW = 96
TRAINING_EPOCHS = 30
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 20260719
METRICS = ("nll", "brier", "ece", "auc", "pd_at_far")


def _implantation_seed(scene_index: int, snr_index: int, seed: int) -> int:
    return 90_000 + 10_000 * scene_index + 1_000 * snr_index + seed


def _train_ensemble() -> list[SpectralDetector]:
    target = reporter_library(200)["bacteriochlorophyll_a"]
    print("Construindo o treino simulado compartilhado pelo ensemble...")
    features, labels = make_training_set(
        target,
        n_scenes=TRAINING_SCENES,
        hw=TRAINING_HW,
    )
    print(
        f"  {features.shape[0]:,} pixels, {int(labels.sum()):,} positivos, "
        f"{features.shape[1]} features"
    )
    ensemble = []
    for seed in ENSEMBLE_SEEDS:
        print(f"Treinando membro {seed + 1}/{len(ENSEMBLE_SEEDS)}...")
        detector = SpectralDetector(features.shape[1], seed=seed)
        detector.fit(features, labels, epochs=TRAINING_EPOCHS)
        ensemble.append(detector)
    return ensemble


def _raw_outputs(
    scene: np.ndarray,
    target: np.ndarray,
    ensemble: list[SpectralDetector],
) -> dict[str, np.ndarray]:
    mf = spectral_matched_filter(scene, target)
    mf_spatial = gaussian_filter(mf, sigma=SPATIAL_SIGMA, mode="reflect")
    features = pixel_features(scene, target)
    logits = np.stack([
        detector.predict_logits(features) for detector in ensemble
    ])
    member_probability = expit(logits[0])
    ensemble_probability = np.mean(expit(logits), axis=0)
    ensemble_logit = logit(np.clip(ensemble_probability, 1e-7, 1.0 - 1e-7))
    return {
        "mf_platt": mf.ravel(),
        "mf_spatial_platt": mf_spatial.ravel(),
        "learned_temperature": logits[0],
        "learned_ensemble_temperature": ensemble_logit,
        "learned_probability": member_probability,
        "learned_ensemble_probability": ensemble_probability,
    }


def _fit_calibrators(raw: dict[str, list[np.ndarray]], labels: list[np.ndarray]):
    calibration_labels = np.concatenate(labels)
    calibrators = {}
    for method in METHODS:
        values = np.concatenate(raw[method])
        if method.startswith("mf"):
            calibrator = PlattCalibrator().fit(values, calibration_labels)
        else:
            calibrator = TemperatureCalibrator().fit(values, calibration_labels)
        calibrators[method] = calibrator
    return calibrators


def _calibrator_record(calibrator) -> dict:
    if isinstance(calibrator, PlattCalibrator):
        return {
            "kind": "platt",
            "slope": calibrator.slope_,
            "intercept": calibrator.intercept_,
        }
    return {
        "kind": "temperature_with_bias",
        "temperature": calibrator.temperature_,
        "bias": calibrator.bias_,
    }


def _evaluate(ensemble: list[SpectralDetector]):
    rows = []
    parameters = []
    reliability_inputs = {
        str(int(snr)): {method: [[], []] for method in METHODS} for snr in SNRS
    }
    for scene_index, scene_name in enumerate(SCENES):
        cube = load_mat_cube(str(ROOT / "data" / f"{scene_name}.mat"))
        target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        print(f"{scene_name}: {cube.shape}")
        for snr_index, snr in enumerate(SNRS):
            calibration_raw = {method: [] for method in METHODS}
            calibration_labels = []
            for seed in CALIBRATION_SEEDS:
                implantation_seed = _implantation_seed(
                    scene_index, snr_index, seed
                )
                scene, ground_truth, _, target_used = implant_target(
                    cube,
                    np.random.default_rng(implantation_seed),
                    target=target,
                    snr_db=snr,
                )
                outputs = _raw_outputs(scene, target_used, ensemble)
                for method in METHODS:
                    calibration_raw[method].append(outputs[method])
                calibration_labels.append(ground_truth.ravel())
            calibrators = _fit_calibrators(
                calibration_raw, calibration_labels
            )
            parameters.append({
                "scene": scene_name,
                "target_snr_db": snr,
                "calibrators": {
                    method: _calibrator_record(calibrators[method])
                    for method in METHODS
                },
            })

            for seed in EVALUATION_SEEDS:
                implantation_seed = _implantation_seed(
                    scene_index, snr_index, seed
                )
                scene, ground_truth, _, target_used = implant_target(
                    cube,
                    np.random.default_rng(implantation_seed),
                    target=target,
                    snr_db=snr,
                )
                outputs = _raw_outputs(scene, target_used, ensemble)
                truth = ground_truth.ravel()
                for method in METHODS:
                    raw_score = outputs[method]
                    probability = calibrators[method].predict_proba(raw_score)
                    row = {
                        "scene": scene_name,
                        "target_snr_db": snr,
                        "seed": seed,
                        "implantation_seed": implantation_seed,
                        "method": method,
                        "nll": binary_nll(probability, truth),
                        "brier": brier_score(probability, truth),
                        "ece": expected_calibration_error(
                            probability, truth, n_bins=ECE_BINS
                        ),
                        "auc": roc_auc(raw_score, truth),
                        "pd_at_far": pd_at_far(raw_score, truth, FAR),
                        "positive_pixels": int(truth.sum()),
                        "negative_pixels": int((~truth).sum()),
                    }
                    rows.append(row)
                    reliability_inputs[str(int(snr))][method][0].append(
                        probability
                    )
                    reliability_inputs[str(int(snr))][method][1].append(truth)
                    print(
                        f"  SNR {snr:>3.0f} seed {seed} {method:<32} "
                        f"NLL {row['nll']:.5f} ECE {row['ece']:.5f} "
                        f"AUC {row['auc']:.4f}"
                    )
    return rows, parameters, reliability_inputs


def _cases_and_values(rows: list[dict]):
    keys = sorted({
        (row["scene"], row["target_snr_db"], row["seed"]) for row in rows
    })
    cases = [
        {"scene": scene, "target_snr_db": snr, "seed": seed}
        for scene, snr, seed in keys
    ]
    lookup = {
        (row["scene"], row["target_snr_db"], row["seed"], row["method"]): row
        for row in rows
    }
    values = {
        f"{method}:{metric}": np.array([
            lookup[(case["scene"], case["target_snr_db"], case["seed"], method)][metric]
            for case in cases
        ])
        for method in METHODS
        for metric in METRICS
    }
    return cases, values


def _hierarchical_resamples(cases: list[dict], replicates: int, seed: int):
    rng = np.random.default_rng(seed)
    scenes = sorted({case["scene"] for case in cases})
    snrs = sorted({case["target_snr_db"] for case in cases})
    resamples = []
    for _ in range(replicates):
        selected = []
        for scene in rng.choice(scenes, size=len(scenes), replace=True):
            for snr in snrs:
                candidates = np.array([
                    index for index, case in enumerate(cases)
                    if case["scene"] == scene and case["target_snr_db"] == snr
                ])
                selected.extend(
                    rng.choice(candidates, size=len(candidates), replace=True)
                )
        resamples.append(np.asarray(selected, dtype=int))
    return resamples


def _interval(values: np.ndarray, resamples: list[np.ndarray]) -> dict:
    bootstrap = np.array([np.mean(values[index]) for index in resamples])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
    }


def _summaries(rows: list[dict]):
    cases, values = _cases_and_values(rows)
    resamples = _hierarchical_resamples(
        cases, BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED
    )
    overall = {
        method: {
            metric: _interval(values[f"{method}:{metric}"], resamples)
            for metric in METRICS
        }
        for method in METHODS
    }
    by_snr = {}
    for snr_index, snr in enumerate(SNRS):
        selected_indices = np.array([
            index for index, case in enumerate(cases)
            if case["target_snr_db"] == snr
        ])
        local_cases = [cases[index] for index in selected_indices]
        local_resamples = _hierarchical_resamples(
            local_cases,
            BOOTSTRAP_REPLICATES,
            BOOTSTRAP_SEED + snr_index + 1,
        )
        by_snr[str(int(snr))] = {
            method: {
                metric: _interval(
                    values[f"{method}:{metric}"][selected_indices],
                    local_resamples,
                )
                for metric in METRICS
            }
            for method in METHODS
        }
    learned = "learned_ensemble_temperature"
    classical = "mf_spatial_platt"
    difference = {
        metric: _interval(
            values[f"{learned}:{metric}"] - values[f"{classical}:{metric}"],
            resamples,
        )
        for metric in METRICS
    }
    difference["significant_calibration_advantage"] = bool(
        difference["nll"]["ci_high"] < 0.0
        and difference["ece"]["ci_high"] < 0.0
    )
    return overall, by_snr, difference


def _serialize_reliability(reliability_inputs):
    output = {}
    for snr, methods in reliability_inputs.items():
        output[snr] = {}
        for method, (probabilities, labels) in methods.items():
            curve = reliability_curve(
                np.concatenate(probabilities),
                np.concatenate(labels),
                n_bins=ECE_BINS,
            )
            output[snr][method] = {
                "bin_edges": curve["bin_edges"].tolist(),
                "counts": curve["counts"].tolist(),
                "mean_probability": [
                    None if np.isnan(value) else float(value)
                    for value in curve["mean_probability"]
                ],
                "event_rate": [
                    None if np.isnan(value) else float(value)
                    for value in curve["event_rate"]
                ],
            }
    return output


def _format_interval(summary: dict, digits: int = 5) -> str:
    return (
        f"{summary['mean']:.{digits}f} "
        f"[{summary['ci_low']:.{digits}f}, {summary['ci_high']:.{digits}f}]"
    )


def _write_markdown(results: dict) -> str:
    overall = results["summary"]["overall"]
    by_snr = results["summary"]["by_snr"]
    comparison = results["comparison"]
    won = comparison["significant_calibration_advantage"]
    lines = [
        "# T7b: incerteza calibrada",
        "",
        "O experimento separa calibração e avaliação por implante. Em cada cena e",
        "target SNR, os seeds 100 e 101 ajustam os calibradores; os seeds 0 a 3",
        "são usados apenas nas métricas. O treino do detector continua restrito a",
        "fundos simulados. Nenhum rótulo de avaliação ajusta rede ou calibrador.",
        "",
        "NLL e Brier são médias pixel-wise sem balanceamento em cada caso; o",
        "agregado dá o mesmo peso a cada combinação de cena, SNR e seed. A ECE usa",
        f"{ECE_BINS} bins uniformes fixos. Os IC 95% usam "
        f"{BOOTSTRAP_REPLICATES} réplicas hierárquicas sobre cenas e seeds.",
        "AUC e Pd@FAR são referências de detecção calculadas nos scores antes da",
        "calibração. Com apenas três cenas, os IC descrevem este benchmark.",
        "",
        "## Resultado agregado",
        "",
        "| Método | NLL [IC 95%] | Brier [IC 95%] | ECE [IC 95%] | AUC [IC 95%] | Pd@FAR 1e-3 [IC 95%] |",
        "|---|:---:|:---:|:---:|:---:|:---:|",
    ]
    for method in METHODS:
        summary = overall[method]
        lines.append(
            f"| {METHOD_LABELS[method]} | "
            f"{_format_interval(summary['nll'])} | "
            f"{_format_interval(summary['brier'])} | "
            f"{_format_interval(summary['ece'])} | "
            f"{_format_interval(summary['auc'], 3)} | "
            f"{_format_interval(summary['pd_at_far'], 3)} |"
        )
    lines += ["", "## Resultado por target SNR", ""]
    lines += [
        "| SNR | Método | NLL [IC 95%] | Brier [IC 95%] | ECE [IC 95%] |",
        "|---:|---|:---:|:---:|:---:|",
    ]
    for snr in SNRS:
        for method in METHODS:
            summary = by_snr[str(int(snr))][method]
            lines.append(
                f"| {snr:.0f} dB | {METHOD_LABELS[method]} | "
                f"{_format_interval(summary['nll'])} | "
                f"{_format_interval(summary['brier'])} | "
                f"{_format_interval(summary['ece'])} |"
            )
    lines += [
        "",
        "## Critério pré-especificado",
        "",
        "Diferença pareada do ensemble aprendido menos MF espacial, ambos calibrados:",
        "",
        f"- NLL: {_format_interval(comparison['nll'])}",
        f"- Brier: {_format_interval(comparison['brier'])}",
        f"- ECE: {_format_interval(comparison['ece'])}",
        f"- AUC: {_format_interval(comparison['auc'], 3)}",
        f"- Pd@FAR 1e-3: {_format_interval(comparison['pd_at_far'], 3)}",
        "",
    ]
    if won:
        lines += [
            "Os limites superiores dos IC de NLL e ECE ficaram abaixo de zero.",
            "Neste protocolo, o ensemble aprendido obteve a primeira vantagem",
            "robusta do aprendizado em incerteza calibrada, sem reivindicar vantagem",
            "em detecção.",
        ]
    else:
        lines += [
            "O critério não foi satisfeito: NLL e ECE não tiveram simultaneamente",
            "IC favoráveis ao ensemble. O aprendizado não demonstrou vantagem robusta",
            "de incerteza calibrada neste protocolo.",
        ]
    lines += [
        "",
        "Platt e temperature scaling têm dois parâmetros de calibração. A correção",
        "de intercepto no temperature scaling é necessária porque a rede foi treinada",
        "com perda ponderada, cujo intercepto bruto não representa a prevalência de",
        "implantação. Os diagramas estão em `assets/reliability_uncertainty.png`.",
        "",
        "A motivação de Ariel vem da Gaussian Log-Likelihood do desafio, mas este",
        "experimento binário não reproduz a tarefa de recuperação de parâmetros",
        "atmosféricos do Ariel Data Challenge.",
        "",
        "Referência: [Ariel Data Challenge: exoplanet atmospheric spectra",
        "reconstruction](https://arxiv.org/abs/2505.08940).",
        "",
    ]
    return "\n".join(lines)


def _plot_reliability(reliability: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {
        "mf_platt": "#4078c0",
        "mf_spatial_platt": "#143d66",
        "learned_temperature": "#c56b2d",
        "learned_ensemble_temperature": "#8b2f24",
    }
    fig, axes = plt.subplots(1, len(SNRS), figsize=(12, 5), sharex=True, sharey=True)
    for axis, snr in zip(axes, SNRS):
        axis.plot([0, 1], [0, 1], color="#888888", linestyle="--", linewidth=1)
        for method in METHODS:
            curve = reliability[str(int(snr))][method]
            x = np.array([
                np.nan if value is None else value
                for value in curve["mean_probability"]
            ])
            y = np.array([
                np.nan if value is None else value for value in curve["event_rate"]
            ])
            occupied = np.isfinite(x) & np.isfinite(y)
            axis.plot(
                x[occupied], y[occupied], marker="o", linewidth=1.8,
                markersize=4, color=colors[method], label=METHOD_LABELS[method],
            )
        axis.set_title(f"Target SNR {snr:.0f} dB")
        axis.set_xlabel("Probabilidade prevista")
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("Frequência observada")
    axes[-1].legend(fontsize=8, loc="upper left")
    fig.suptitle("Curvas de confiabilidade em pixels de avaliação")
    fig.tight_layout()
    fig.savefig(ROOT / "assets" / "reliability_uncertainty.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ensemble = _train_ensemble()
    rows, parameters, reliability_inputs = _evaluate(ensemble)
    overall, by_snr, comparison = _summaries(rows)
    reliability = _serialize_reliability(reliability_inputs)
    results = {
        "protocol": {
            "scenes": list(SCENES),
            "target_snrs_db": list(SNRS),
            "calibration_seeds": list(CALIBRATION_SEEDS),
            "evaluation_seeds": list(EVALUATION_SEEDS),
            "split_unit": "independent target implantation",
            "far": FAR,
            "ece_uniform_bins": ECE_BINS,
            "spatial_sigma_pixels": SPATIAL_SIGMA,
            "ensemble_seeds": list(ENSEMBLE_SEEDS),
            "training": {
                "background": "physics-simulated only",
                "scenes": TRAINING_SCENES,
                "height_width": TRAINING_HW,
                "epochs": TRAINING_EPOCHS,
                "class_weighted_detector_loss": True,
            },
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "scheme": "resample scenes, then seeds within scene/SNR",
            },
            "significance_rule": (
                "upper 95% CI bounds for learned ensemble minus calibrated "
                "spatial MF must be below zero for both NLL and ECE"
            ),
            "evaluation_labels_used_for_fitting": False,
        },
        "calibration_parameters": parameters,
        "rows": rows,
        "summary": {"overall": overall, "by_snr": by_snr},
        "comparison": comparison,
        "reliability": reliability,
    }
    output_json = ROOT / "results" / "uncertainty.json"
    output_md = ROOT / "results" / "uncertainty.md"
    output_json.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _write_markdown(results)
    output_md.write_text(markdown, encoding="utf-8")
    _plot_reliability(reliability)
    print("\n" + markdown)
    print(f"\nArquivos: {output_json}, {output_md}")


if __name__ == "__main__":
    main()
