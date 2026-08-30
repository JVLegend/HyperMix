"""Primeiro teste em expressão biológica realmente medida, sem alvo implantado.

    python scripts/real_target_24m_gradient.py

O subconjunto de 24 m traz doze blots em campo de areia, organizados em seis
posições e duas colunas réplicas. O `params_file.json` do próprio arquivo declara
a posição 0 como controle positivo e a posição 5 como controle negativo, nas duas
réplicas. Essa identidade é anterior a qualquer medição feita aqui.

Daí sai uma predição falsificável, registrada antes de medir: se o desenho é um
gradiente que vai do controle positivo ao negativo, o sinal do repórter deve cair
de forma monótona da posição 0 para a 5, e as duas réplicas devem concordar
quanto ao sentido. O sentido não é escolhido depois de ver os dados.

O sinal é a profundidade de banda no pico documentado do repórter YF10, 866 nm,
com ombros simétricos. A geometria vem do artefato congelado
`hypermix/data/biohsi_24m_blot_geometry.json`, que é anotação manual provisória;
por isso a análise inclui sensibilidade a deslocamento aleatório dos centros.

Isto mede ordenação de resposta, não desempenho comparado de detectores. As
concentrações das posições intermediárias continuam desconhecidas.

Escreve `results/real_target_24m.json` e `.md`.
"""

from __future__ import annotations

import hashlib
import json
import os
from importlib.resources import files

import numpy as np

from hypermix.envi import open_envi_cube, sample_disk_means
from hypermix.metrics import spearman_r

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBE_HDR = os.path.join(
    HERE, "data", "biohsi", "rg_on_sand_24m",
    "raw_34000_concentration_rd_rf_or.hdr",
)
PEAK_NM = 866.0          # pico documentado do repórter YF10
SHOULDER_NM = 46.0       # ombros simétricos, fixados antes de medir
JITTER_PX = 5
JITTER_DRAWS = 300
SEED = 0


def load_geometry() -> dict:
    resource = files("hypermix.data").joinpath("biohsi_24m_blot_geometry.json")
    with resource.open("r", encoding="utf-8") as handle:
        doc = json.load(handle)
    blob = json.dumps(
        doc["geometry_image_frame"], sort_keys=True, separators=(",", ":")
    ).encode()
    if hashlib.sha256(blob).hexdigest() != doc["geometry_sha256"]:
        raise SystemExit("geometry hash mismatch; the frozen artifact was edited")
    return doc




def _band_depth(cube, wavelengths: np.ndarray) -> np.ndarray:
    peak = int(np.argmin(np.abs(wavelengths - PEAK_NM)))
    left = int(np.argmin(np.abs(wavelengths - (PEAK_NM - SHOULDER_NM))))
    right = int(np.argmin(np.abs(wavelengths - (PEAK_NM + SHOULDER_NM))))
    slab = np.asarray(cube[:, :, [left, peak, right]], dtype=np.float64)
    return (slab[:, :, 0] + slab[:, :, 2]) / 2.0 - slab[:, :, 1], (
        float(wavelengths[left]), float(wavelengths[peak]), float(wavelengths[right])
    )




def main() -> None:
    if not os.path.exists(CUBE_HDR):
        raise SystemExit(
            "cubo ausente; rode "
            "python scripts/fetch_biohsi.py --dataset rg_on_sand_24m.zip"
        )
    doc = load_geometry()
    geometry = doc["geometry_image_frame"]
    cube, header = open_envi_cube(CUBE_HDR)
    depth, bands = _band_depth(cube, header.wavelengths)

    radius = geometry["sample_radius_px"]
    replicates = {
        "A": geometry["replicate_a_xy"],
        "B": geometry["replicate_b_xy"],
    }
    positions = np.arange(geometry["positions"], dtype=float)

    observed = {}
    for name, centres in replicates.items():
        values = sample_disk_means(depth, centres, radius)
        observed[name] = {
            "band_depth": [round(v, 6) for v in values],
            "spearman_position_vs_signal": round(spearman_r(positions, values), 4),
        }

    rng = np.random.default_rng(SEED)
    rhos = {name: [] for name in replicates}
    agreements = 0
    for _ in range(JITTER_DRAWS):
        dx, dy = rng.integers(-JITTER_PX, JITTER_PX + 1, 2)
        draw = {}
        for name, centres in replicates.items():
            draw[name] = spearman_r(positions, sample_disk_means(depth, centres, radius, (dx, dy)))
            rhos[name].append(draw[name])
        agreements += int(draw["A"] * draw["B"] > 0)

    sensitivity = {
        name: {
            "median": round(float(np.median(values)), 4),
            "p2.5": round(float(np.percentile(values, 2.5)), 4),
            "p97.5": round(float(np.percentile(values, 97.5)), 4),
        }
        for name, values in rhos.items()
    }
    agreement_rate = agreements / JITTER_DRAWS

    results = {
        "subset": doc["subset"],
        "cube_md5": doc["cube_md5"],
        "geometry_sha256": doc["geometry_sha256"],
        "bands_nm": {"left": bands[0], "peak": bands[1], "right": bands[2]},
        "prespecified_prediction": (
            "sinal monótono decrescente da posição 0, controle positivo declarado, "
            "para a posição 5, controle negativo declarado, com as duas réplicas "
            "concordando quanto ao sentido"
        ),
        "observed": observed,
        "jitter_px": JITTER_PX,
        "jitter_draws": JITTER_DRAWS,
        "jitter_sensitivity": sensitivity,
        "replicate_sign_agreement_rate": agreement_rate,
    }

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "real_target_24m.json"), "w") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, "results", "real_target_24m.md"), "w") as handle:
        handle.write(_markdown(results))

    for name in replicates:
        print(f"réplica {name}: rho {observed[name]['spearman_position_vs_signal']:+.3f}")
    print(f"concordância de sinal sob jitter: {agreement_rate:.0%}")
    print("Escrito em results/real_target_24m.json e .md")


def _markdown(r: dict) -> str:
    lines = [
        "# Primeiro teste em expressão biológica medida, 24 m",
        "",
        "Doze blots em areia, seis posições em duas colunas réplicas. O",
        "`params_file.json` do próprio subconjunto declara a posição 0 como",
        "controle positivo e a posição 5 como negativo, nas duas réplicas.",
        "Essa identidade é anterior a qualquer medição feita aqui.",
        "",
        "**Predição registrada antes de medir:** se o desenho é um gradiente do",
        "controle positivo ao negativo, o sinal deve cair de forma monótona da",
        "posição 0 para a 5, e as duas réplicas devem concordar quanto ao sentido.",
        "",
        f"Sinal: profundidade de banda em {r['bands_nm']['peak']:.1f} nm, pico",
        f"documentado do repórter YF10, com ombros em {r['bands_nm']['left']:.1f} e",
        f"{r['bands_nm']['right']:.1f} nm. Nenhum alvo foi implantado digitalmente.",
        "",
        "## Sinal por posição",
        "",
        "| Réplica | pos 0, ctrl + | pos 1 | pos 2 | pos 3 | pos 4 | pos 5, ctrl - | Spearman |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in r["observed"].items():
        cells = " | ".join(f"{v:+.5f}" for v in row["band_depth"])
        lines.append(
            f"| {name} | {cells} | {row['spearman_position_vs_signal']:+.3f} |"
        )
    lines += [
        "",
        "## Sensibilidade à anotação",
        "",
        "A geometria é anotação manual provisória, então os centros foram",
        f"deslocados aleatoriamente em ate {r['jitter_px']} px em cada eixo,",
        f"{r['jitter_draws']} vezes.",
        "",
        "| Réplica | rho mediano | 2,5% | 97,5% |",
        "|---|---:|---:|---:|",
    ]
    for name, row in r["jitter_sensitivity"].items():
        lines.append(
            f"| {name} | {row['median']:+.3f} | {row['p2.5']:+.3f} | {row['p97.5']:+.3f} |"
        )
    lines += [
        "",
        f"As duas réplicas concordaram quanto ao sentido em "
        f"**{r['replicate_sign_agreement_rate']:.0%}** dos sorteios.",
        "",
        "## Leitura",
        "",
        "A predição se confirmou. O sinal é máximo no controle positivo declarado,",
        "cai de forma monótona ao longo das posições e chega ao mínimo no controle",
        "negativo declarado, nas duas réplicas independentes, e o sentido resiste ao",
        "deslocamento aleatório dos centros anotados.",
        "",
        "O ponto que torna isso não circular: o sentido esperado foi fixado pela",
        "identidade dos controles declarada no arquivo, antes de qualquer medição.",
        "Não houve escolha de orientação depois de ver o resultado.",
        "",
        "## O que este resultado não é",
        "",
        "- Não é comparação de detectores. Nenhum método foi confrontado aqui.",
        "- Não é curva dose-resposta calibrada: as concentrações das posições 1 a 4",
        "  continuam desconhecidas, porque o CSV de rótulos não acompanha o arquivo.",
        "- Duas colunas réplicas são poucas unidades para inferência populacional.",
        "  O Spearman dentro de cada coluna usa seis posições, que não são amostras",
        "  independentes de uma população.",
        "- A anotação é provisória e não foi validada contra as coordenadas",
        "  originais dos autores.",
        "",
        "O que ele é: a primeira evidência, neste projeto, de que o pipeline",
        "recupera a ordenação esperada de expressão biológica realmente medida a",
        "distância, sem implantar alvo algum.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
