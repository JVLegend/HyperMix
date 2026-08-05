"""Evaluate leakage-resistant family-aware and target-blind detection.

The exact held-out reporter is used only for implantation and the oracle
ceiling.  Family methods receive the other host-specific biliverdin spectrum
plus fixed physical perturbations.  Unknown-target methods receive no target
spectrum at train or test time.

    .venv-train/bin/python scripts/blind_target_experiment.py

Writes ``results/blind.json`` and ``results/blind.md``.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from hypermix import (
    blind_anomaly_features,
    family_detection_features,
    implant_target,
    load_mat_cube,
    matched_subspace_detector,
    measured_reporter_library,
    pd_at_far,
    roc_auc,
    rx_detector,
    scale_target_library,
    simulate_scene,
    spectral_matched_filter,
)
from hypermix.detector import SpectralDetector


ROOT = Path(__file__).resolve().parents[1]
SCENES = ("indian_pines", "salinas", "paviaU")
HELD_OUT_TARGETS = (
    "biliverdin_ixalpha_ecoli",
    "biliverdin_ixalpha_pputida",
)
OTHER_HOST = {
    "biliverdin_ixalpha_ecoli": "biliverdin_ixalpha_pputida",
    "biliverdin_ixalpha_pputida": "biliverdin_ixalpha_ecoli",
}
SNRS = (5.0, 0.0)
EVAL_SEEDS = (0, 1, 2, 3)
TRAIN_BANDS = 61
TRAIN_SCENES = 12
TRAIN_SIZE = 48
TRAIN_EPOCHS = 16
SPATIAL_SIGMA = 1.5
MAX_SPATIAL_SAMPLES = 96
FAR = 1e-3
BOOTSTRAP_REPLICATES = 5_000
BOOTSTRAP_SEED = 20260805
METHODS = (
    "oracle_spatial",
    "family_centroid_spatial",
    "family_subspace_spatial",
    "learned_family",
    "rx_spatial",
    "learned_blind",
)
METHOD_LABELS = {
    "oracle_spatial": "MF espacial, alvo exato, teto oracle",
    "family_centroid_spatial": "MF espacial, centroide da família",
    "family_subspace_spatial": "Subespaço espacial da família",
    "learned_family": "MLP, família sem alvo retido",
    "rx_spatial": "RX espacial, sem alvo",
    "learned_blind": "MLP cego, sem alvo",
}
TRACKS = {
    "oracle_spatial": "oracle",
    "family_centroid_spatial": "family",
    "family_subspace_spatial": "family",
    "learned_family": "family",
    "rx_spatial": "unknown",
    "learned_blind": "unknown",
}


def _physical_family(signature: np.ndarray) -> np.ndarray:
    """Fixed shift/tilt family derived only from an allowed signature."""

    curve = np.asarray(signature, dtype=np.float64)
    grid = np.linspace(-1.0, 1.0, curve.size)
    variants = []
    for shift in (-1.0, 0.0, 1.0):
        shifted = np.interp(
            np.arange(curve.size) - shift,
            np.arange(curve.size),
            curve,
            left=curve[0],
            right=curve[-1],
        )
        for tilt in (-0.03, 0.0, 0.03):
            variants.append(np.clip(shifted * (1.0 + tilt * grid), 0.0, None))
    return np.asarray(variants)


def _spatial_sample(cube: np.ndarray) -> tuple[np.ndarray, int]:
    """Bound runtime with a fixed whole-scene lattice, chosen without labels."""

    stride = max(1, math.ceil(max(cube.shape[:2]) / MAX_SPATIAL_SAMPLES))
    return cube[::stride, ::stride], stride


def _training_models(held_out: str) -> tuple[SpectralDetector, SpectralDetector]:
    _, reporters = measured_reporter_library(TRAIN_BANDS)
    allowed = _physical_family(reporters[OTHER_HOST[held_out]])
    unrelated = _physical_family(reporters["bacteriochlorophyll_a"])
    family_features = []
    family_labels = []
    blind_features = []
    blind_labels = []

    for index in range(TRAIN_SCENES):
        background = simulate_scene(
            height=TRAIN_SIZE,
            width=TRAIN_SIZE,
            n_bands=TRAIN_BANDS,
            snr_db=40.0,
            reporter_max_abundance=0.0,
            spectral_source="measured",
            seed=130_000 + 1_000 * HELD_OUT_TARGETS.index(held_out) + index,
        ).cube
        family = scale_target_library(allowed, background)
        target = family[index % len(family)]
        family_scene, family_gt, _, _ = implant_target(
            background,
            np.random.default_rng(140_000 + index),
            target=target,
            snr_db=SNRS[index % len(SNRS)],
        )
        family_rx = rx_detector(family_scene)
        family_features.append(
            family_detection_features(
                family_scene,
                family,
                rank=3,
                rx_score=family_rx,
            )
        )
        family_labels.append(family_gt.reshape(-1))

        blind_library = np.vstack((allowed, unrelated))
        blind_target = scale_target_library(blind_library, background)[
            index % len(blind_library)
        ]
        blind_scene, blind_gt, _, _ = implant_target(
            background,
            np.random.default_rng(150_000 + index),
            target=blind_target,
            snr_db=SNRS[index % len(SNRS)],
        )
        blind_rx = rx_detector(blind_scene)
        blind_features.append(
            blind_anomaly_features(blind_scene, rx_score=blind_rx)
        )
        blind_labels.append(blind_gt.reshape(-1))

    family_model = SpectralDetector(6, hidden=48, dropout=0.20, seed=210)
    family_model.fit(
        np.concatenate(family_features),
        np.concatenate(family_labels),
        epochs=TRAIN_EPOCHS,
        batch=4096,
    )
    blind_model = SpectralDetector(6, hidden=48, dropout=0.20, seed=220)
    blind_model.fit(
        np.concatenate(blind_features),
        np.concatenate(blind_labels),
        epochs=TRAIN_EPOCHS,
        batch=4096,
    )
    return family_model, blind_model


def _evaluate() -> tuple[list[dict], dict[str, int]]:
    models = {
        held_out: _training_models(held_out) for held_out in HELD_OUT_TARGETS
    }
    rows = []
    strides = {}
    for scene_index, scene_name in enumerate(SCENES):
        full_cube = load_mat_cube(str(ROOT / "data" / f"{scene_name}.mat"))
        cube, stride = _spatial_sample(full_cube)
        strides[scene_name] = stride
        _, reporters = measured_reporter_library(cube.shape[-1])
        print(f"{scene_name}: {full_cube.shape} -> {cube.shape}, stride {stride}")

        for target_index, held_out in enumerate(HELD_OUT_TARGETS):
            family_model, blind_model = models[held_out]
            allowed_unscaled = _physical_family(reporters[OTHER_HOST[held_out]])
            family = scale_target_library(allowed_unscaled, cube)
            for snr in SNRS:
                for seed in EVAL_SEEDS:
                    implantation_seed = (
                        160_000 + 10_000 * scene_index + 1_000 * target_index + seed
                    )
                    scene, ground_truth, _, exact_target = implant_target(
                        cube,
                        np.random.default_rng(implantation_seed),
                        target=reporters[held_out],
                        snr_db=snr,
                    )
                    oracle = spectral_matched_filter(scene, exact_target)
                    rx = rx_detector(scene)
                    centroid = spectral_matched_filter(scene, family.mean(axis=0))
                    subspace = matched_subspace_detector(scene, family, rank=3)
                    family_input = family_detection_features(
                        scene,
                        family,
                        rank=3,
                        rx_score=rx,
                        centroid_score=centroid,
                        subspace_score=subspace,
                    )
                    blind_input = blind_anomaly_features(scene, rx_score=rx)
                    score_maps = {
                        "oracle_spatial": gaussian_filter(
                            oracle, sigma=SPATIAL_SIGMA, mode="reflect"
                        ),
                        "family_centroid_spatial": gaussian_filter(
                            centroid, sigma=SPATIAL_SIGMA, mode="reflect"
                        ),
                        "family_subspace_spatial": gaussian_filter(
                            subspace, sigma=SPATIAL_SIGMA, mode="reflect"
                        ),
                        "learned_family": family_model.predict_proba(
                            family_input
                        ).reshape(scene.shape[:2]),
                        "rx_spatial": gaussian_filter(
                            rx, sigma=SPATIAL_SIGMA, mode="reflect"
                        ),
                        "learned_blind": blind_model.predict_proba(
                            blind_input
                        ).reshape(scene.shape[:2]),
                    }
                    for method, score in score_maps.items():
                        row = {
                            "scene": scene_name,
                            "held_out_target": held_out,
                            "allowed_family_source": OTHER_HOST[held_out],
                            "target_snr_db": snr,
                            "seed": seed,
                            "implantation_seed": implantation_seed,
                            "track": TRACKS[method],
                            "method": method,
                            "auc": roc_auc(score, ground_truth),
                            "pd_at_far": pd_at_far(score, ground_truth, FAR),
                            "positive_pixels": int(ground_truth.sum()),
                            "negative_pixels": int((~ground_truth).sum()),
                        }
                        rows.append(row)
                        print(
                            f"  {held_out:<30} SNR {snr:>3.0f} seed {seed} "
                            f"{method:<27} AUC {row['auc']:.4f} "
                            f"Pd {row['pd_at_far']:.4f}"
                        )
    return rows, strides


def _case_matrix(rows: list[dict]) -> tuple[list[dict], dict[str, np.ndarray]]:
    keys = sorted({
        (row["scene"], row["held_out_target"], row["target_snr_db"], row["seed"])
        for row in rows
    })
    cases = [
        {"scene": scene, "held_out_target": target, "target_snr_db": snr, "seed": seed}
        for scene, target, snr, seed in keys
    ]
    lookup = {
        (
            row["scene"],
            row["held_out_target"],
            row["target_snr_db"],
            row["seed"],
            row["method"],
        ): row
        for row in rows
    }
    values = {}
    for metric in ("auc", "pd_at_far"):
        for method in METHODS:
            values[f"{method}:{metric}"] = np.asarray([
                lookup[
                    (
                        case["scene"],
                        case["held_out_target"],
                        case["target_snr_db"],
                        case["seed"],
                        method,
                    )
                ][metric]
                for case in cases
            ])
    return cases, values


def _hierarchical_resamples(
    cases: list[dict], replicates: int, seed: int
) -> list[np.ndarray]:
    """Resample scenes, held-out targets, then seeds within each SNR."""

    rng = np.random.default_rng(seed)
    scenes = sorted({case["scene"] for case in cases})
    targets = sorted({case["held_out_target"] for case in cases})
    snrs = sorted({case["target_snr_db"] for case in cases})
    resamples = []
    for _ in range(replicates):
        sampled = []
        for scene in rng.choice(scenes, size=len(scenes), replace=True):
            for target in rng.choice(targets, size=len(targets), replace=True):
                for snr in snrs:
                    candidates = np.asarray([
                        index
                        for index, case in enumerate(cases)
                        if case["scene"] == scene
                        and case["held_out_target"] == target
                        and case["target_snr_db"] == snr
                    ])
                    sampled.extend(
                        rng.choice(candidates, size=len(candidates), replace=True)
                    )
        resamples.append(np.asarray(sampled, dtype=int))
    return resamples


def _interval(values: np.ndarray, resamples: list[np.ndarray]) -> dict:
    bootstrap = np.asarray([
        float(np.mean(values[indices])) for indices in resamples
    ])
    return {
        "mean": float(np.mean(values)),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
    }


def _summaries(rows: list[dict]) -> tuple[dict, dict, dict, dict]:
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
    distance_to_oracle = {
        method: {
            metric: _interval(
                values[f"oracle_spatial:{metric}"] - values[f"{method}:{metric}"],
                resamples,
            )
            for metric in ("auc", "pd_at_far")
        }
        for method in METHODS
        if method != "oracle_spatial"
    }
    comparisons = {}
    for learned, comparator in (
        ("learned_family", "family_centroid_spatial"),
        ("learned_family", "family_subspace_spatial"),
        ("learned_blind", "rx_spatial"),
    ):
        key = f"{learned}_minus_{comparator}"
        comparisons[key] = {
            metric: _interval(
                values[f"{learned}:{metric}"] - values[f"{comparator}:{metric}"],
                resamples,
            )
            for metric in ("auc", "pd_at_far")
        }
        comparisons[key]["significant_advantage"] = bool(
            comparisons[key]["auc"]["ci_low"] > 0.0
            and comparisons[key]["pd_at_far"]["ci_low"] > 0.0
        )

    by_snr = {}
    for snr_index, snr in enumerate(SNRS):
        selected = np.asarray([
            index for index, case in enumerate(cases) if case["target_snr_db"] == snr
        ])
        local_cases = [case for case in cases if case["target_snr_db"] == snr]
        local_resamples = _hierarchical_resamples(
            local_cases, BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED + snr_index + 1
        )
        by_snr[str(int(snr))] = {
            method: {
                metric: _interval(
                    values[f"{method}:{metric}"][selected], local_resamples
                )
                for metric in ("auc", "pd_at_far")
            }
            for method in METHODS
        }
    return overall, by_snr, comparisons, distance_to_oracle


def _format_interval(summary: dict) -> str:
    return (
        f"{summary['mean']:.3f} "
        f"[{summary['ci_low']:.3f}, {summary['ci_high']:.3f}]"
    )


def _write_markdown(results: dict) -> str:
    overall = results["summary"]["overall"]
    by_snr = results["summary"]["by_snr"]
    comparisons = results["comparisons"]
    distance = results["distance_to_oracle"]
    family_cmp = comparisons[
        "learned_family_minus_family_centroid_spatial"
    ]
    subspace_diagnostic = comparisons[
        "learned_family_minus_family_subspace_spatial"
    ]
    blind_cmp = comparisons["learned_blind_minus_rx_spatial"]
    any_advantage = (
        family_cmp["significant_advantage"]
        or blind_cmp["significant_advantage"]
    )
    lines = [
        "# T10: detecção sem assinatura exata do alvo",
        "",
        "Avaliação leave-one-host-out nas três cenas reais do benchmark com alvo",
        "implantado. E. coli é avaliado usando somente P. putida como família",
        "permitida, e vice-versa. O alvo retido aparece apenas na implantação e",
        "no teto oracle. A curva biliverdina canônica não é usada porque contém a",
        "média dos dois hosts e vazaria informação do alvo retido.",
        "",
        "A família permitida contém nove perturbações fixas do outro host: três",
        "deslocamentos de uma banda combinados com três inclinações de 3%. O método",
        "cego não recebe alvo nem família. Os MLPs são treinados só em simulação",
        "com fundos medidos do USGS. A avaliação usa target SNR 5 e 0 dB, quatro",
        "seeds e amostragem espacial em lattice fixo de até 96 pontos por eixo,",
        "definida sem consultar rótulos.",
        "",
        f"Pd é medido em FAR = {FAR:.0e}. Intervalos de 95% usam",
        f"{BOOTSTRAP_REPLICATES} réplicas hierárquicas, reamostrando cenas, alvos",
        "retidos e seeds dentro de cada SNR. Há somente dois espectros medidos da",
        "família biliverdina, portanto este é um teste pequeno, não uma estimativa",
        "ampla de generalização entre famílias químicas.",
        "Os arquivos MAT não incluem centros de banda. Como nos experimentos",
        "implantados anteriores, as curvas medidas usam a grade de conveniência",
        "linear de 400 a 1000 nm; isto não é calibração espectral do sensor.",
        "",
        "## Resultado agregado",
        "",
        "| Regime | Método | AUC média [IC 95%] | Pd@FAR 1e-3 [IC 95%] |",
        "|---|---|:---:|:---:|",
    ]
    for method in METHODS:
        lines.append(
            f"| {TRACKS[method]} | {METHOD_LABELS[method]} | "
            f"{_format_interval(overall[method]['auc'])} | "
            f"{_format_interval(overall[method]['pd_at_far'])} |"
        )
    lines += [
        "",
        "## Distância ao teto oracle",
        "",
        "Valores positivos indicam quanto desempenho foi perdido ao retirar o",
        "espectro exato. O oracle não participa da seleção de método.",
        "",
        "| Método operável | Oracle menos método, AUC [IC 95%] | Oracle menos método, Pd [IC 95%] |",
        "|---|:---:|:---:|",
    ]
    for method in METHODS[1:]:
        lines.append(
            f"| {METHOD_LABELS[method]} | "
            f"{_format_interval(distance[method]['auc'])} | "
            f"{_format_interval(distance[method]['pd_at_far'])} |"
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
        "## Critério causal congelado para o artefato final",
        "",
        "A primeira execução funcionou como auditoria piloto e mostrou que o MF",
        "do centroide era mais forte que o subespaço. Antes de congelar o JSON",
        "final, o critério foi endurecido para usar esse melhor baseline clássico.",
        "A comparação com subespaço foi mantida apenas como diagnóstico.",
        "",
        "Cada modelo aprendido é comparado somente ao baseline clássico com a",
        "mesma informação. Vantagem exige que os ICs de AUC e Pd estejam ambos",
        "acima de zero.",
        "",
        "MLP família menos MF do centroide da família:",
        "",
        f"- AUC: {_format_interval(family_cmp['auc'])}",
        f"- Pd@FAR 1e-3: {_format_interval(family_cmp['pd_at_far'])}",
        "",
        "Diagnóstico secundário, MLP família menos subespaço da família:",
        "",
        f"- AUC: {_format_interval(subspace_diagnostic['auc'])}",
        f"- Pd@FAR 1e-3: {_format_interval(subspace_diagnostic['pd_at_far'])}",
        "",
        "MLP cego menos RX espacial:",
        "",
        f"- AUC: {_format_interval(blind_cmp['auc'])}",
        f"- Pd@FAR 1e-3: {_format_interval(blind_cmp['pd_at_far'])}",
        "",
    ]
    if any_advantage:
        lines += [
            "Ao menos um regime aprendido satisfez o critério nos dois desfechos.",
            "A interpretação fica restrita ao seu comparador de mesma informação e",
            "a este pequeno leave-one-host-out com alvos implantados.",
        ]
    else:
        lines += [
            "Nenhum regime aprendido satisfez o critério nos dois desfechos. Este",
            "teste não estabelece vantagem causal do aprendizado quando a assinatura",
            "exata é retirada.",
        ]
    lines += [
        "",
        "O oracle não participa do teste de superioridade. Ele apenas quantifica o",
        "custo de não conhecer a assinatura exata. Alvos implantados em fundos reais",
        "não equivalem à detecção remota de expressão biológica naturalmente observada.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    rows, strides = _evaluate()
    overall, by_snr, comparisons, distance_to_oracle = _summaries(rows)
    results = {
        "protocol": {
            "scenes": list(SCENES),
            "held_out_targets": list(HELD_OUT_TARGETS),
            "leave_one_host_out": dict(OTHER_HOST),
            "target_snrs_db": list(SNRS),
            "eval_seeds": list(EVAL_SEEDS),
            "far": FAR,
            "spatial_sigma_pixels_after_sampling": SPATIAL_SIGMA,
            "whole_scene_lattice_max_samples_per_axis": MAX_SPATIAL_SAMPLES,
            "spatial_strides": strides,
            "wavelength_assumption": (
                "MAT cubes have no band centers; measured targets use the "
                "linear 400-1000 nm convenience grid"
            ),
            "family_perturbations": {
                "source": "other host-specific measured biliverdin spectrum",
                "band_shifts": [-1.0, 0.0, 1.0],
                "multiplicative_tilts": [-0.03, 0.0, 0.03],
                "uses_held_out_target": False,
            },
            "learned_models": {
                "training_scenes_per_holdout": TRAIN_SCENES,
                "training_scene_shape": [TRAIN_SIZE, TRAIN_SIZE, TRAIN_BANDS],
                "epochs": TRAIN_EPOCHS,
                "hidden_units": 48,
                "dropout": 0.20,
            },
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "scheme": "resample scenes, held-out targets, then seeds within SNR",
            },
            "significance_rule": (
                "both 95% CIs must be above zero for learned_family minus "
                "family_centroid_spatial and learned_blind minus rx_spatial; "
                "the subspace comparison is diagnostic"
            ),
        },
        "rows": rows,
        "summary": {"overall": overall, "by_snr": by_snr},
        "comparisons": comparisons,
        "distance_to_oracle": distance_to_oracle,
    }
    output_json = ROOT / "results" / "blind.json"
    output_md = ROOT / "results" / "blind.md"
    output_json.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _write_markdown(results)
    output_md.write_text(markdown, encoding="utf-8")
    print("\n" + markdown)
    print(f"\nWrote {output_json} and {output_md}")


if __name__ == "__main__":
    main()
