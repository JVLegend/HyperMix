"""Test fixed-target, subspace and learned detectors under target variability.

This is a wavelength-calibrated implanted-target sensitivity experiment. It
uses measured USGS backgrounds and measured bioHSI reporter curves, but it is
not validation on a naturally expressed remote target.

    python scripts/target_variability_experiment.py

Writes ``results/target_variability.json`` and ``results/target_variability.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from hypermix import (
    apply_atmosphere,
    apply_srf,
    atmospheric_transmittance,
    implant_target,
    matched_subspace_detector,
    measured_reporter_library,
    roc_auc,
    simulate_scene,
    smoothed_matched_filter,
    smoothed_matched_subspace_detector,
    spectral_matched_filter,
)
from hypermix.detector import SpectralDetector, pixel_features


ROOT = Path(__file__).resolve().parents[1]
N_BANDS = 61
TRAIN_SCENES = 24
TRAIN_HW = 72
EVAL_HW = 80
SNRS = (20.0, 10.0, 5.0, 0.0)
EVAL_SEEDS = (0, 1, 2, 3, 4, 5)
WIN_MARGIN = 0.005

METHODS = (
    "matched_filter_nominal",
    "matched_filter_spatial_nominal",
    "matched_subspace",
    "matched_subspace_spatial",
    "learned_nominal_features",
    "matched_filter_spatial_oracle",
)


def _native_reporters() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    return measured_reporter_library(601)


def _observe_target(
    target: np.ndarray,
    native_wavelengths: np.ndarray,
    fwhm_nm: float,
    atmosphere_strength: float,
) -> np.ndarray:
    centers = np.linspace(400.0, 1000.0, N_BANDS)
    observed = apply_srf(
        target,
        wavelengths=native_wavelengths,
        centers_nm=centers,
        fwhm_nm=fwhm_nm,
    )
    tau = atmospheric_transmittance(
        wavelengths=centers, strength=atmosphere_strength
    )
    return apply_atmosphere(observed, tau, path_radiance=0.02)


def _track_definition(name: str) -> dict:
    native_wavelengths, native = _native_reporters()
    host_native = [
        native["biliverdin_ixalpha_ecoli"],
        native["biliverdin_ixalpha_pputida"],
    ]
    if name == "host_variation":
        _, reporters = measured_reporter_library(N_BANDS)
        library = np.stack([
            reporters["biliverdin_ixalpha_ecoli"],
            reporters["biliverdin_ixalpha_pputida"],
        ])
        return {"library": library, "rank": 2, "sensor": False}
    if name == "host_sensor_variation":
        variants = []
        for target in host_native:
            for fwhm in (6.0, 10.0, 14.0):
                for atmosphere_strength in (0.7, 1.0, 1.3):
                    variants.append(
                        _observe_target(
                            target, native_wavelengths, fwhm, atmosphere_strength
                        )
                    )
        return {"library": np.stack(variants), "rank": 4, "sensor": True}
    if name == "reporter_family":
        _, reporters = measured_reporter_library(N_BANDS)
        library = np.stack([
            reporters["bacteriochlorophyll_a"],
            reporters["biliverdin_ixalpha_ecoli"],
            reporters["biliverdin_ixalpha_pputida"],
        ])
        return {"library": library, "rank": 3, "sensor": False}
    raise ValueError(f"unknown variability track: {name!r}")


def _scale_signatures(signatures: np.ndarray, cube: np.ndarray) -> np.ndarray:
    values = np.atleast_2d(np.asarray(signatures, dtype=np.float64))
    scene_mean = float(cube.reshape(-1, cube.shape[2]).mean())
    maxima = np.max(values, axis=1, keepdims=True)
    maxima = np.where(maxima == 0.0, 1.0, maxima)
    return values / maxima * scene_mean


def _sample_scene(track: dict, seed: int, snr: float, hw: int):
    rng = np.random.default_rng(seed)
    native_wavelengths, native = _native_reporters()
    sensor_options = {}
    if track["sensor"]:
        fwhm = rng.uniform(6.0, 14.0)
        atmosphere_strength = rng.uniform(0.7, 1.3)
        host = [
            "biliverdin_ixalpha_ecoli",
            "biliverdin_ixalpha_pputida",
        ][seed % 2]
        actual = _observe_target(
            native[host], native_wavelengths, fwhm, atmosphere_strength
        )
        sensor_options = {
            "sensor_fwhm_nm": fwhm,
            "atmosphere": True,
            "atmosphere_strength": atmosphere_strength,
        }
    else:
        index = seed % track["library"].shape[0]
        actual = track["library"][index]

    background = simulate_scene(
        height=hw,
        width=hw,
        n_bands=N_BANDS,
        snr_db=40.0,
        reporter_max_abundance=0.0,
        spectral_source="measured",
        seed=seed + 50_000,
        **sensor_options,
    ).cube
    scene, ground_truth, _, actual_scaled = implant_target(
        background,
        rng,
        target=actual,
        snr_db=snr,
    )
    nominal = _scale_signatures(track["library"].mean(axis=0), background)[0]
    target_subspace = _scale_signatures(track["library"], background)
    return scene, ground_truth, actual_scaled, nominal, target_subspace


def _training_set(track: dict) -> tuple[np.ndarray, np.ndarray]:
    features, labels = [], []
    for index in range(TRAIN_SCENES):
        snr = SNRS[index % len(SNRS)]
        scene, ground_truth, _, nominal, _ = _sample_scene(
            track, seed=10_000 + index, snr=snr, hw=TRAIN_HW
        )
        features.append(pixel_features(scene, nominal))
        labels.append(ground_truth.reshape(-1))
    return np.concatenate(features), np.concatenate(labels)


def _evaluate(track: dict, detector: SpectralDetector) -> list[dict]:
    rows = []
    for snr in SNRS:
        scores = {method: [] for method in METHODS}
        for seed in EVAL_SEEDS:
            scene, ground_truth, actual, nominal, subspace = _sample_scene(
                track, seed=90_000 + seed, snr=snr, hw=EVAL_HW
            )
            maps = {
                "matched_filter_nominal": spectral_matched_filter(scene, nominal),
                "matched_filter_spatial_nominal": smoothed_matched_filter(
                    scene, nominal
                ),
                "matched_subspace": matched_subspace_detector(
                    scene, subspace, rank=track["rank"]
                ),
                "matched_subspace_spatial": smoothed_matched_subspace_detector(
                    scene, subspace, rank=track["rank"]
                ),
                "learned_nominal_features": detector.score_map(scene, nominal),
                "matched_filter_spatial_oracle": smoothed_matched_filter(
                    scene, actual
                ),
            }
            for method, score in maps.items():
                scores[method].append(roc_auc(score, ground_truth))
        for method, values in scores.items():
            rows.append({
                "method": method,
                "target_snr_db": snr,
                "seeds": len(EVAL_SEEDS),
                "auc_mean": float(np.mean(values)),
                "auc_std": float(np.std(values)),
                "auc_by_seed": [float(value) for value in values],
            })
    return rows


def _aggregate(rows: list[dict], method: str) -> tuple[float, float]:
    selected = [row for row in rows if row["method"] == method]
    overall = float(np.mean([row["auc_mean"] for row in selected]))
    at_zero = next(
        row["auc_mean"] for row in selected if row["target_snr_db"] == 0.0
    )
    return overall, at_zero


def _winner(rows: list[dict]) -> str:
    learned = _aggregate(rows, "learned_nominal_features")[0]
    classical_methods = (
        "matched_filter_nominal",
        "matched_filter_spatial_nominal",
        "matched_subspace",
        "matched_subspace_spatial",
    )
    best_method = max(
        classical_methods, key=lambda method: _aggregate(rows, method)[0]
    )
    best = _aggregate(rows, best_method)[0]
    if learned > best + WIN_MARGIN:
        return "aprendido"
    if best > learned + WIN_MARGIN:
        return best_method
    return "empate"


def main() -> None:
    track_names = (
        "host_variation",
        "host_sensor_variation",
        "reporter_family",
    )
    results = {
        "protocol": {
            "n_bands": N_BANDS,
            "wavelength_range_nm": [400.0, 1000.0],
            "target_snrs_db": list(SNRS),
            "eval_seeds": list(EVAL_SEEDS),
            "training_scenes": TRAIN_SCENES,
            "win_margin_auc": WIN_MARGIN,
        },
        "tracks": {},
    }
    for track_name in track_names:
        print(f"Building variable-target training set: {track_name}")
        track = _track_definition(track_name)
        features, labels = _training_set(track)
        print(
            f"  {features.shape[0]:,} pixels, {int(labels.sum()):,} positive"
        )
        detector = SpectralDetector(n_features=features.shape[1], seed=0)
        detector.fit(features, labels, epochs=30)
        rows = _evaluate(track, detector)
        results["tracks"][track_name] = {
            "target_library_size": int(track["library"].shape[0]),
            "subspace_rank": track["rank"],
            "rows": rows,
            "winner": _winner(rows),
        }

    output_json = ROOT / "results" / "target_variability.json"
    output_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    labels = {
        "host_variation": "Hospedeiro, SmURFP/biliverdina",
        "host_sensor_variation": "Hospedeiro + sensor + atmosfera",
        "reporter_family": "Qualquer repórter, BChl ou biliverdina",
    }
    method_labels = {
        "matched_filter_nominal": "MF nominal",
        "matched_filter_spatial_nominal": "MF espacial nominal",
        "matched_subspace": "Subespaço",
        "matched_subspace_spatial": "Subespaço espacial",
        "learned_nominal_features": "Aprendido",
        "matched_filter_spatial_oracle": "MF espacial oráculo",
    }
    lines = [
        "# Variabilidade do alvo medido",
        "",
        "AUC média em target SNR de 20, 10, 5 e 0 dB, 6 seeds por ponto.",
        "As cenas usam endmembers USGS medidos em um forward model calibrado de",
        "400-1000 nm. O MF nominal recebe a média fixa da biblioteca; o oráculo",
        "recebe a assinatura efetivamente implantada. O detector aprendido é",
        "treinado sobre a variação, mas conserva as cinco features derivadas do",
        "alvo nominal da arquitetura atual.",
        "",
        "| Track | MF nominal | MF espacial nominal | Subespaço | Subespaço espacial | Aprendido | Oráculo | Vencedor não-oráculo |",
        "|-------|:----------:|:-------------------:|:---------:|:------------------:|:---------:|:-------:|---------------------|",
    ]
    for track_name, result in results["tracks"].items():
        values = {
            method: _aggregate(result["rows"], method)[0] for method in METHODS
        }
        lines.append(
            f"| {labels[track_name]} | {values['matched_filter_nominal']:.3f} | "
            f"{values['matched_filter_spatial_nominal']:.3f} | "
            f"{values['matched_subspace']:.3f} | "
            f"{values['matched_subspace_spatial']:.3f} | "
            f"{values['learned_nominal_features']:.3f} | "
            f"{values['matched_filter_spatial_oracle']:.3f} | "
            f"{method_labels.get(result['winner'], result['winner'])} |"
        )
    lines += [
        "",
        "## AUC a target SNR de 0 dB",
        "",
        "| Track | MF nominal | MF espacial nominal | Subespaço | Subespaço espacial | Aprendido | Oráculo |",
        "|-------|:----------:|:-------------------:|:---------:|:------------------:|:---------:|:-------:|",
    ]
    for track_name, result in results["tracks"].items():
        values = {
            method: _aggregate(result["rows"], method)[1] for method in METHODS
        }
        lines.append(
            f"| {labels[track_name]} | {values['matched_filter_nominal']:.3f} | "
            f"{values['matched_filter_spatial_nominal']:.3f} | "
            f"{values['matched_subspace']:.3f} | "
            f"{values['matched_subspace_spatial']:.3f} | "
            f"{values['learned_nominal_features']:.3f} | "
            f"{values['matched_filter_spatial_oracle']:.3f} |"
        )
    lines += [
        "",
        "O track de família pergunta se qualquer um dos repórteres foi detectado;",
        "não deve ser descrito como variabilidade intra-repórter. O nível de",
        "expressão é representado pela abundância aleatória do implante. O track",
        "de sensor sorteia FWHM entre 6-14 nm e força atmosférica entre 0,7-1,3.",
        "As assinaturas são estratificadas: três cenas por hospedeiro nos tracks",
        "SmURFP e duas por repórter no track de família, em cada nível de SNR.",
        "",
        "Este é um benchmark de alvo implantado. Não demonstra detecção remota de",
        "expressão biológica naturalmente observada e ainda não inclui intervalos",
        "de confiança sobre a população de cenas.",
        "",
    ]
    output_md = ROOT / "results" / "target_variability.md"
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Wrote {output_json} and {output_md}")


if __name__ == "__main__":
    main()
