"""Measure how many target-aware bands preserve matched-filter detection.

Bands are ranked once per unimplanted real cube by the absolute coefficient of
the full-scene matched-filter direction ``C^-1 (t - mu)``. No implanted labels
are used for ranking. The experiment then recomputes the matched filter using
only the top-k bands on disjoint implanted evaluation cases.

    .venv-train/bin/python scripts/band_sparsity_experiment.py

Writes ``results/band_sparsity.json``, ``results/band_sparsity.md`` and
``assets/band_sparsity.png``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from hypermix import (
    implant_target,
    load_mat_cube,
    reporter_library,
    roc_auc,
    spectral_matched_filter,
)


ROOT = Path(__file__).resolve().parents[1]
SCENES = ("indian_pines", "salinas", "paviaU")
SNRS = (5.0, 0.0)
EVALUATION_SEEDS = (0, 1, 2, 3)
K_VALUES = (1, 2, 3, 5, 10, 20, 40, 80, "all")
SPATIAL_SIGMA = 1.5
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 20260720


def _implantation_seed(scene_index: int, snr_index: int, seed: int) -> int:
    return 120_000 + 10_000 * scene_index + 1_000 * snr_index + seed


def _target_for_cube(cube: np.ndarray) -> np.ndarray:
    target = reporter_library(cube.shape[2])["bacteriochlorophyll_a"]
    return (
        target.astype(np.float64)
        / (float(np.max(target)) or 1.0)
        * float(cube.reshape(-1, cube.shape[2]).mean())
    )


def _band_ranking(cube: np.ndarray, target: np.ndarray):
    pixels = cube.reshape(-1, cube.shape[2]).astype(np.float64)
    mean = pixels.mean(axis=0)
    centered = pixels - mean
    covariance = (centered.T @ centered) / centered.shape[0]
    ridge = max(
        1e-12, 1e-6 * float(np.trace(covariance)) / covariance.shape[0]
    )
    direction = np.linalg.solve(
        covariance + ridge * np.eye(covariance.shape[0]),
        target - mean,
    )
    magnitude = np.abs(direction)
    order = np.argsort(-magnitude, kind="mergesort")
    cumulative = np.cumsum(magnitude[order]) / max(float(magnitude.sum()), 1e-12)
    concentration = {
        str(percent): int(np.searchsorted(cumulative, percent / 100.0) + 1)
        for percent in (50, 80, 90)
    }
    return order, magnitude, cumulative, concentration


def _evaluate():
    rows = []
    rankings = []
    for scene_index, scene_name in enumerate(SCENES):
        cube = load_mat_cube(str(ROOT / "data" / f"{scene_name}.mat"))
        scaled_target = _target_for_cube(cube)
        order, magnitude, cumulative, concentration = _band_ranking(
            cube, scaled_target
        )
        rankings.append({
            "scene": scene_name,
            "bands": cube.shape[2],
            "top_band_indices_zero_based": order[:10].tolist(),
            "top_band_absolute_coefficients": magnitude[order[:10]].tolist(),
            "bands_for_absolute_weight_percent": concentration,
            "cumulative_absolute_weight_top_3": float(cumulative[2]),
        })
        print(
            f"{scene_name}: {cube.shape}, bandas para 80% do peso = "
            f"{concentration['80']}"
        )
        selections = {
            str(k): np.sort(order[: cube.shape[2] if k == "all" else int(k)])
            for k in K_VALUES
        }
        for snr_index, snr in enumerate(SNRS):
            for seed in EVALUATION_SEEDS:
                implantation_seed = _implantation_seed(
                    scene_index, snr_index, seed
                )
                scene, ground_truth, _, target_used = implant_target(
                    cube,
                    np.random.default_rng(implantation_seed),
                    target=reporter_library(cube.shape[2])["bacteriochlorophyll_a"],
                    snr_db=snr,
                )
                for k in K_VALUES:
                    key = str(k)
                    selected = selections[key]
                    score = spectral_matched_filter(
                        scene[:, :, selected], target_used[selected]
                    )
                    spatial = gaussian_filter(
                        score, sigma=SPATIAL_SIGMA, mode="reflect"
                    )
                    row = {
                        "scene": scene_name,
                        "target_snr_db": snr,
                        "seed": seed,
                        "implantation_seed": implantation_seed,
                        "k": key,
                        "actual_bands": int(selected.size),
                        "auc_mf": roc_auc(score, ground_truth),
                        "auc_mf_spatial": roc_auc(spatial, ground_truth),
                    }
                    rows.append(row)
                print(f"  SNR {snr:>3.0f} seed {seed} concluído")
    return rows, rankings


def _cases(rows: list[dict]):
    keys = sorted({
        (row["scene"], row["target_snr_db"], row["seed"]) for row in rows
    })
    return [
        {"scene": scene, "target_snr_db": snr, "seed": seed}
        for scene, snr, seed in keys
    ]


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


def _interval(values: np.ndarray, resamples: list[np.ndarray]):
    bootstrap = np.array([np.mean(values[index]) for index in resamples])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
    }


def _summaries(rows: list[dict]):
    cases = _cases(rows)
    lookup = {
        (row["scene"], row["target_snr_db"], row["seed"], row["k"]): row
        for row in rows
    }
    values = {
        f"{k}:{metric}": np.array([
            lookup[(case["scene"], case["target_snr_db"], case["seed"], str(k))][metric]
            for case in cases
        ])
        for k in K_VALUES
        for metric in ("auc_mf", "auc_mf_spatial")
    }
    resamples = _hierarchical_resamples(
        cases, BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED
    )
    overall = {
        str(k): {
            metric: _interval(values[f"{k}:{metric}"], resamples)
            for metric in ("auc_mf", "auc_mf_spatial")
        }
        for k in K_VALUES
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
            str(k): {
                metric: _interval(
                    values[f"{k}:{metric}"][selected_indices], local_resamples
                )
                for metric in ("auc_mf", "auc_mf_spatial")
            }
            for k in K_VALUES
        }
    difference_top3_all = {
        metric: _interval(
            values[f"3:{metric}"] - values[f"all:{metric}"], resamples
        )
        for metric in ("auc_mf", "auc_mf_spatial")
    }
    full_auc = overall["all"]["auc_mf_spatial"]["mean"]
    within_point005 = [
        k for k in K_VALUES
        if overall[str(k)]["auc_mf_spatial"]["mean"] >= full_auc - 0.005
    ]
    smallest_within = str(within_point005[0]) if within_point005 else None
    return overall, by_snr, difference_top3_all, smallest_within


def _format_interval(summary: dict) -> str:
    return (
        f"{summary['mean']:.3f} "
        f"[{summary['ci_low']:.3f}, {summary['ci_high']:.3f}]"
    )


def _write_markdown(results: dict) -> str:
    overall = results["summary"]["overall"]
    by_snr = results["summary"]["by_snr"]
    difference = results["comparison"]["top_3_minus_all"]
    smallest = results["comparison"]["smallest_k_within_0_005_of_full_mean"]
    lines = [
        "# T7c: esparsidade de banda",
        "",
        "As bandas são ordenadas separadamente em cada cubo real não implantado",
        "pelo valor absoluto do vetor do matched filter completo,",
        "`|C^-1 (t - mu)|`. A ordem usa o alvo conhecido e estatísticas não rotuladas",
        "da cena, mas não usa máscaras implantadas nem AUC. Para cada k, o MF é",
        "recalculado apenas nas bandas selecionadas.",
        "",
        "O protocolo usa Indian Pines, Salinas e Pavia University, target SNR de",
        "5 e 0 dB e 4 seeds por ponto. Os IC 95% usam 5000 réplicas hierárquicas",
        "sobre cenas e seeds. O MF espacial com sigma 1,5 é a análise primária.",
        "",
        "## AUC versus número de bandas",
        "",
        "| Top-k | MF espectral [IC 95%] | MF espacial [IC 95%] |",
        "|---:|:---:|:---:|",
    ]
    for k in K_VALUES:
        lines.append(
            f"| {k} | {_format_interval(overall[str(k)]['auc_mf'])} | "
            f"{_format_interval(overall[str(k)]['auc_mf_spatial'])} |"
        )
    lines += ["", "## MF espacial por target SNR", ""]
    lines += [
        "| Top-k | 5 dB [IC 95%] | 0 dB [IC 95%] |",
        "|---:|:---:|:---:|",
    ]
    for k in K_VALUES:
        lines.append(
            f"| {k} | "
            f"{_format_interval(by_snr['5'][str(k)]['auc_mf_spatial'])} | "
            f"{_format_interval(by_snr['0'][str(k)]['auc_mf_spatial'])} |"
        )
    lines += [
        "",
        "## Concentração dos coeficientes",
        "",
        "| Cena | Bandas totais | k para 50% | k para 80% | k para 90% | Peso absoluto nas top-3 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for ranking in results["rankings"]:
        concentration = ranking["bands_for_absolute_weight_percent"]
        lines.append(
            f"| {ranking['scene']} | {ranking['bands']} | "
            f"{concentration['50']} | {concentration['80']} | "
            f"{concentration['90']} | "
            f"{ranking['cumulative_absolute_weight_top_3']:.3f} |"
        )
    lines += [
        "",
        "## Leitura",
        "",
        "Diferença pareada top-3 menos todas as bandas:",
        "",
        f"- MF espectral: {_format_interval(difference['auc_mf'])}",
        f"- MF espacial: {_format_interval(difference['auc_mf_spatial'])}",
        "",
        f"O menor k cuja AUC espacial média ficou a até 0,005 do MF completo foi `{smallest}`.",
        "Esse limiar é descritivo e não substitui o IC da diferença top-3 menos all.",
        "",
        "O estudo `One Channel Is All You Need` motiva a pergunta, mas avalia",
        "classificação de culturas na competição ICPR 2024. Ele foi publicado nos",
        "anais do ICAISC e não estabelece que três bandas bastem para a detecção",
        "de alvos implantados do HyperMix. Os resultados aqui são específicos a",
        "bacterioclorofila-a sintética e a esta regra target-aware de seleção.",
        "",
        "Referência: [One Channel Is All You Need](https://doi.org/10.1007/978-3-032-03705-3_4),",
        "estudo baseado na competição ICPR 2024 e publicado nos anais do ICAISC.",
        "",
    ]
    return "\n".join(lines)


def _plot(overall: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    numeric_x = np.arange(len(K_VALUES))
    labels = [str(k) for k in K_VALUES[:-1]] + ["all"]
    spectral = np.array([overall[str(k)]["auc_mf"]["mean"] for k in K_VALUES])
    spatial = np.array([
        overall[str(k)]["auc_mf_spatial"]["mean"] for k in K_VALUES
    ])
    spectral_low = spectral - np.array([
        overall[str(k)]["auc_mf"]["ci_low"] for k in K_VALUES
    ])
    spectral_high = np.array([
        overall[str(k)]["auc_mf"]["ci_high"] for k in K_VALUES
    ]) - spectral
    spatial_low = spatial - np.array([
        overall[str(k)]["auc_mf_spatial"]["ci_low"] for k in K_VALUES
    ])
    spatial_high = np.array([
        overall[str(k)]["auc_mf_spatial"]["ci_high"] for k in K_VALUES
    ]) - spatial
    fig, axis = plt.subplots(figsize=(9, 5))
    axis.errorbar(
        numeric_x, spectral, yerr=[spectral_low, spectral_high], marker="o",
        capsize=3, label="MF espectral", color="#567a9f",
    )
    axis.errorbar(
        numeric_x, spatial, yerr=[spatial_low, spatial_high], marker="o",
        capsize=3, label="MF espacial", color="#b85c38",
    )
    axis.set_xticks(numeric_x, labels)
    axis.set_xlabel("Número de bandas target-aware")
    axis.set_ylabel("AUC média")
    axis.set_title("AUC do matched filter versus top-k bandas")
    axis.grid(alpha=0.2)
    axis.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "assets" / "band_sparsity.png", dpi=160)
    plt.close(fig)


def main() -> None:
    rows, rankings = _evaluate()
    overall, by_snr, difference, smallest = _summaries(rows)
    results = {
        "protocol": {
            "scenes": list(SCENES),
            "target_snrs_db": list(SNRS),
            "evaluation_seeds": list(EVALUATION_SEEDS),
            "k_values": list(K_VALUES),
            "ranking": "absolute full-scene C^-1 (target - mean) coefficient",
            "ranking_uses_implanted_labels": False,
            "spatial_sigma_pixels": SPATIAL_SIGMA,
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "scheme": "resample scenes, then seeds within scene/SNR",
            },
        },
        "rankings": rankings,
        "rows": rows,
        "summary": {"overall": overall, "by_snr": by_snr},
        "comparison": {
            "top_3_minus_all": difference,
            "smallest_k_within_0_005_of_full_mean": smallest,
        },
    }
    output_json = ROOT / "results" / "band_sparsity.json"
    output_md = ROOT / "results" / "band_sparsity.md"
    output_json.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _write_markdown(results)
    output_md.write_text(markdown, encoding="utf-8")
    _plot(overall)
    print("\n" + markdown)
    print(f"\nArquivos: {output_json}, {output_md}")


if __name__ == "__main__":
    main()
