"""Evaluate self-supervised background modeling on real spectral clutter.

The autoencoder is fitted independently on unlabeled pixels from each implanted
test scene. It receives neither labels nor the target signature during fitting.
The experiment compares spatial matched filtering, global RX, and the background
model with and without the same fixed spatial smoothing.

    .venv-train/bin/python scripts/background_experiment.py

Writes ``results/background.json`` and ``results/background.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from hypermix import (
    background_detector,
    implant_target,
    load_mat_cube,
    pd_at_far,
    reporter_library,
    roc_auc,
    rx_detector,
    spectral_matched_filter,
)


ROOT = Path(__file__).resolve().parents[1]
SCENES = ("indian_pines", "salinas", "paviaU")
SNRS = (5.0, 0.0)
EVAL_SEEDS = (0, 1, 2, 3)
METHODS = ("mf_spatial", "rx", "background", "background_spatial")
METHOD_LABELS = {
    "mf_spatial": "MF espacial",
    "rx": "RX global",
    "background": "Autoencoder de fundo",
    "background_spatial": "Autoencoder de fundo espacial",
}
FAR = 1e-3
SPATIAL_SIGMA = 1.5
AE_EPOCHS = 15
AE_SAMPLE_SIZE = 12_000
AE_BATCH_SIZE = 512
AE_ANOMALY_WEIGHT = 0.5
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 20260718


def _case_seed(scene_index: int, seed: int) -> int:
    return 70_000 + 1_000 * scene_index + seed


def _evaluate() -> list[dict]:
    rows = []
    for scene_index, scene_name in enumerate(SCENES):
        cube = load_mat_cube(str(ROOT / "data" / f"{scene_name}.mat"))
        target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
        print(f"{scene_name}: {cube.shape}")
        for snr_index, snr in enumerate(SNRS):
            for seed in EVAL_SEEDS:
                implantation_seed = _case_seed(scene_index, seed)
                scene, ground_truth, _, target_used = implant_target(
                    cube,
                    np.random.default_rng(implantation_seed),
                    target=target,
                    snr_db=snr,
                )
                mf = spectral_matched_filter(scene, target_used)
                maps = {
                    "mf_spatial": gaussian_filter(
                        mf, sigma=SPATIAL_SIGMA, mode="reflect"
                    ),
                    "rx": rx_detector(scene),
                }
                background = background_detector(
                    scene,
                    target_used,
                    epochs=AE_EPOCHS,
                    sample_size=AE_SAMPLE_SIZE,
                    batch_size=AE_BATCH_SIZE,
                    anomaly_weight=AE_ANOMALY_WEIGHT,
                    seed=(10_000 * scene_index + 100 * snr_index + seed),
                    matched_filter_score=mf,
                )
                maps["background"] = background
                maps["background_spatial"] = gaussian_filter(
                    background, sigma=SPATIAL_SIGMA, mode="reflect"
                )
                for method, score in maps.items():
                    row = {
                        "scene": scene_name,
                        "target_snr_db": snr,
                        "seed": seed,
                        "implantation_seed": implantation_seed,
                        "method": method,
                        "auc": roc_auc(score, ground_truth),
                        "pd_at_far": pd_at_far(score, ground_truth, FAR),
                        "positive_pixels": int(ground_truth.sum()),
                        "negative_pixels": int((~ground_truth).sum()),
                    }
                    rows.append(row)
                    print(
                        f"  SNR {snr:>3.0f} seed {seed} {method:<20} "
                        f"AUC {row['auc']:.4f} Pd {row['pd_at_far']:.4f}"
                    )
    return rows


def _case_matrix(rows: list[dict]) -> tuple[list[dict], dict[str, np.ndarray]]:
    keys = sorted({
        (row["scene"], row["target_snr_db"], row["seed"])
        for row in rows
    })
    cases = [
        {"scene": scene, "target_snr_db": snr, "seed": seed}
        for scene, snr, seed in keys
    ]
    lookup = {
        (row["scene"], row["target_snr_db"], row["seed"], row["method"]): row
        for row in rows
    }
    values = {}
    for metric in ("auc", "pd_at_far"):
        for method in METHODS:
            values[f"{method}:{metric}"] = np.array([
                lookup[(case["scene"], case["target_snr_db"], case["seed"], method)][metric]
                for case in cases
            ])
    return cases, values


def _hierarchical_resamples(
    cases: list[dict],
    replicates: int,
    seed: int,
) -> list[np.ndarray]:
    """Resample scenes, then seeds within every selected scene/SNR stratum."""
    rng = np.random.default_rng(seed)
    scene_names = sorted({case["scene"] for case in cases})
    snr_values = sorted({case["target_snr_db"] for case in cases})
    resamples = []
    for _ in range(replicates):
        sampled = []
        for scene_name in rng.choice(
            scene_names, size=len(scene_names), replace=True
        ):
            for snr in snr_values:
                candidates = np.array([
                    index
                    for index, case in enumerate(cases)
                    if case["scene"] == scene_name
                    and case["target_snr_db"] == snr
                ])
                sampled.extend(
                    rng.choice(candidates, size=len(candidates), replace=True)
                )
        resamples.append(np.asarray(sampled, dtype=int))
    return resamples


def _interval(values: np.ndarray, resamples: list[np.ndarray]) -> dict:
    bootstrapped = np.array([
        float(np.mean(values[indices])) for indices in resamples
    ])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrapped, 0.025)),
        "ci_high": float(np.quantile(bootstrapped, 0.975)),
    }


def _summaries(rows: list[dict]) -> tuple[dict, dict, dict]:
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

    by_snr = {}
    for snr_index, snr in enumerate(SNRS):
        selected_cases = [
            case for case in cases if case["target_snr_db"] == snr
        ]
        selected_indices = np.array([
            index for index, case in enumerate(cases)
            if case["target_snr_db"] == snr
        ])
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

    difference = {}
    for metric in ("auc", "pd_at_far"):
        paired = (
            values[f"background_spatial:{metric}"]
            - values[f"mf_spatial:{metric}"]
        )
        difference[metric] = _interval(paired, resamples)
    difference["significant_advantage"] = bool(
        difference["auc"]["ci_low"] > 0.0
        and difference["pd_at_far"]["ci_low"] > 0.0
    )
    return overall, by_snr, difference


def _format_interval(summary: dict) -> str:
    return (
        f"{summary['mean']:.3f} "
        f"[{summary['ci_low']:.3f}, {summary['ci_high']:.3f}]"
    )


def _write_markdown(results: dict) -> str:
    overall = results["summary"]["overall"]
    by_snr = results["summary"]["by_snr"]
    difference = results["comparison"]
    advantage = difference["significant_advantage"]
    lines = [
        "# T7a: modelo auto-supervisionado do fundo",
        "",
        "Avaliação transdutiva em Indian Pines, Salinas e Pavia University,",
        "com alvo implantado, target SNR de 5 e 0 dB e 4 seeds por ponto.",
        "O autoencoder espectral raso é treinado separadamente nos pixels não",
        "rotulados de cada cena de teste. Ele não recebe máscara nem assinatura",
        "do alvo durante o treino. Como os pixels são não rotulados, uma pequena",
        "contaminação por alvos implantados pode estar presente na amostra.",
        "",
        f"Pd é medido em FAR = {FAR:.0e}. Intervalos de 95% usam "
        f"{BOOTSTRAP_REPLICATES} réplicas hierárquicas: cenas são reamostradas e,",
        "dentro de cada cena e SNR, seeds são reamostradas. Com apenas três cenas,",
        "os intervalos descrevem este benchmark e não uma população ampla de sensores.",
        "",
        "## Resultado agregado",
        "",
        "| Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |",
        "|---|:---:|:---:|",
    ]
    for method in METHODS:
        lines.append(
            f"| {METHOD_LABELS[method]} | "
            f"{_format_interval(overall[method]['auc'])} | "
            f"{_format_interval(overall[method]['pd_at_far'])} |"
        )
    lines += ["", "## Resultado por target SNR", ""]
    lines += [
        "| SNR | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |",
        "|---:|---|:---:|:---:|",
    ]
    for snr in SNRS:
        snr_summary = by_snr[str(int(snr))]
        for method in METHODS:
            lines.append(
                f"| {snr:.0f} dB | {METHOD_LABELS[method]} | "
                f"{_format_interval(snr_summary[method]['auc'])} | "
                f"{_format_interval(snr_summary[method]['pd_at_far'])} |"
            )
    lines += [
        "",
        "## Comparação causal pré-especificada",
        "",
        "Diferença do autoencoder espacial menos o MF espacial:",
        "",
        f"- AUC: {_format_interval(difference['auc'])}",
        f"- Pd@FAR 1e-3: {_format_interval(difference['pd_at_far'])}",
        "",
    ]
    if advantage:
        lines += [
            "Os dois intervalos da diferença ficaram acima de zero. Neste protocolo,",
            "o modelo de fundo obteve a primeira vantagem causal robusta do aprendizado",
            "sobre o comparador espacial pré-especificado.",
        ]
    else:
        lines += [
            "O critério de vantagem robusta não foi satisfeito: os intervalos de AUC",
            "e Pd@FAR não ficaram ambos acima de zero. Este autoencoder simples não",
            "sustenta uma vantagem causal do aprendizado sobre o MF espacial.",
        ]
    lines += [
        "",
        "O RX é alvo-agnóstico. O score do autoencoder combina o quantil do MF com",
        "um gate fixo baseado no quantil do erro de reconstrução, com peso 0,5.",
        "Nenhum hiperparâmetro foi escolhido usando rótulos deste experimento.",
        "Isto continua sendo alvo implantado em fundos reais, não detecção remota de",
        "expressão biológica naturalmente observada.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    rows = _evaluate()
    overall, by_snr, difference = _summaries(rows)
    results = {
        "protocol": {
            "scenes": list(SCENES),
            "target_snrs_db": list(SNRS),
            "eval_seeds": list(EVAL_SEEDS),
            "far": FAR,
            "spatial_sigma_pixels": SPATIAL_SIGMA,
            "autoencoder": {
                "architecture": "bands -> min(32, max(4, bands // 6)) -> bands",
                "epochs": AE_EPOCHS,
                "sample_size": AE_SAMPLE_SIZE,
                "batch_size": AE_BATCH_SIZE,
                "anomaly_weight": AE_ANOMALY_WEIGHT,
                "uses_labels": False,
                "uses_target_during_training": False,
            },
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "scheme": "resample scenes, then seeds within scene/SNR",
            },
            "significance_rule": (
                "both 95% CIs for background_spatial - mf_spatial "
                "must be above zero"
            ),
        },
        "rows": rows,
        "summary": {"overall": overall, "by_snr": by_snr},
        "comparison": difference,
    }
    output_json = ROOT / "results" / "background.json"
    output_md = ROOT / "results" / "background.md"
    output_json.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _write_markdown(results)
    output_md.write_text(markdown, encoding="utf-8")
    print("\n" + markdown)
    print(f"\nWrote {output_json} and {output_md}")


if __name__ == "__main__":
    main()
