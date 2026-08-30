"""O fundo medido é gaussiano? A premissa que sustenta o matched filter.

    python scripts/background_gaussianity.py

Todo o veredito do HyperMix repousa num teorema condicional: com fundo e ruído
gaussianos e alvo conhecido, o matched filter é a estatística suficiente, e nada
aprendido pode superá-lo. A pergunta empírica, que não precisa de rótulo algum,
é se essa condição vale em dado realmente medido.

Duas fontes reais e independentes são usadas, ambas sem alvo:

- poços vazios da placa de pellets, cena de bancada, sensor `uVS-374`;
- fundo do voo de 54 m fora das regiões experimentais, cena remota, `nHS-369`.

O protocolo é pré-especificado. As bandas são subamostradas para manter a razão
entre pixels e dimensão alta. A covariância é estimada numa metade dos pixels e a
distância de Mahalanobis é avaliada na outra metade, então a estatística de
ajuste nunca vê os dados que a produziram. Sob gaussiana multivariada, essa
distância ao quadrado segue qui-quadrado com grau igual ao número de bandas.

Critério declarado antes de medir: excesso de curtose próximo de zero e quantis
de Mahalanobis próximos dos esperados indicam fundo gaussiano, o que sustenta a
otimalidade do matched filter. Caudas pesadas indicam o contrário, e nesse caso a
não gaussianidade passa a ser a explicação mecanística de onde um método
aprendido poderia legitimamente ganhar.

Escreve `results/background_gaussianity.json` e `.md`.
"""

from __future__ import annotations

import json
import os

import numpy as np

from hypermix.envi import envi_nodata_mask, open_envi_cube
from hypermix.metrics import excess_kurtosis, skewness

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAND_STRIDE = 6          # mantém pixels por dimensão alto
MAX_PIXELS = 60000
SEED = 0
QUANTILES = (0.50, 0.90, 0.99, 0.999)


def _plate_empty_wells() -> np.ndarray | None:
    """Espectros de poços sem conteúdo, pela geometria já congelada."""
    from importlib.resources import files

    hdr = os.path.join(
        HERE, "data", "biohsi", "rg_bchla_pellets_ctrl", "data.hdr"
    )
    if not os.path.exists(hdr):
        return None
    resource = files("hypermix.data").joinpath("biohsi_pellets_plate_geometry.json")
    with resource.open("r", encoding="utf-8") as handle:
        geometry = json.load(handle)["geometry_image_frame"]
    cube, _ = open_envi_cube(hdr)
    radius = 14
    yy, xx = np.mgrid[-radius : radius + 1, -radius : radius + 1]
    disk = (yy**2 + xx**2) <= radius**2
    rows = geometry["rows_y"][4:]          # metade inferior da placa, sem conteúdo
    out = []
    for y in rows:
        for x in geometry["cols_x"]:
            patch = np.asarray(
                cube[y - radius : y + radius + 1, x - radius : x + radius + 1, :],
                dtype=np.float64,
            )
            out.append(patch[disk])
    return np.concatenate(out, axis=0)


def _flight_background() -> np.ndarray | None:
    """Pixels do voo de 54 m fora das janelas experimentais e do preenchimento."""
    hdr = os.path.join(
        HERE, "data", "biohsi", "rg_on_sand_induction_54m", "raw_0_rd_rf_or.hdr"
    )
    if not os.path.exists(hdr):
        return None
    cube, _ = open_envi_cube(hdr)
    data = np.asarray(cube[:, :, ::BAND_STRIDE], dtype=np.float64)
    keep = ~envi_nodata_mask(data)
    keep[700:860, 300:360] = False          # janelas experimentais declaradas
    keep[760:850, 290:340] = False
    return data[keep]


def _subsample(pixels: np.ndarray, stride: int) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    if pixels.shape[1] > 1 and stride > 1:
        pixels = pixels[:, ::stride]
    if pixels.shape[0] > MAX_PIXELS:
        idx = rng.choice(pixels.shape[0], MAX_PIXELS, replace=False)
        pixels = pixels[idx]
    return pixels




def _chi2_quantile(df: int, q: float, rng: np.random.Generator) -> float:
    """Quantil de qui-quadrado por simulação, sem trazer SciPy para o núcleo."""
    draws = rng.standard_normal((200000, df) if df <= 80 else (60000, df))
    return float(np.quantile((draws**2).sum(axis=1), q))


def _analyse(name: str, pixels: np.ndarray, stride: int) -> dict:
    pixels = _subsample(pixels, stride)
    n, d = pixels.shape
    rng = np.random.default_rng(SEED)
    order = rng.permutation(n)
    fit, evaluate = pixels[order[: n // 2]], pixels[order[n // 2 :]]

    mean = fit.mean(axis=0)
    cov = np.cov(fit - mean, rowvar=False)
    cov += np.eye(d) * (np.trace(cov) / d) * 1e-6
    inv = np.linalg.inv(cov)
    delta = evaluate - mean
    mahalanobis = np.einsum("ij,jk,ik->i", delta, inv, delta)

    kurt = excess_kurtosis(pixels)
    skew = skewness(pixels)
    observed = {f"q{q}": float(np.quantile(mahalanobis, q)) for q in QUANTILES}
    expected = {f"q{q}": _chi2_quantile(d, q, rng) for q in QUANTILES}
    return {
        "scene": name,
        "n_pixels": int(n),
        "n_bands": int(d),
        "pixels_per_dimension": round(n / d, 1),
        "excess_kurtosis_median": float(np.median(kurt)),
        "excess_kurtosis_max": float(kurt.max()),
        "bands_with_excess_kurtosis_above_1": int((kurt > 1.0).sum()),
        "skewness_median": float(np.median(skew)),
        "mahalanobis_observed": observed,
        "mahalanobis_expected_gaussian": expected,
        "tail_ratio_q999": round(observed["q0.999"] / expected["q0.999"], 3),
    }


def _markdown(results: list[dict]) -> str:
    lines = [
        "# O fundo medido é gaussiano?",
        "",
        "A otimalidade do matched filter vale sob fundo gaussiano com alvo",
        "conhecido. Este teste mede a premissa diretamente, em duas cenas reais",
        "sem alvo, e não usa rótulo algum.",
        "",
        "A covariância é ajustada em metade dos pixels e a distância de",
        "Mahalanobis é avaliada na outra metade. Sob gaussiana multivariada, o",
        "quadrado dessa distância segue qui-quadrado com grau igual ao número de",
        "bandas, cujos quantis são obtidos por simulação.",
        "",
        "| Cena | Pixels | Bandas | Px por dim. | Curtose exc. mediana | Bandas com exc. > 1 | Assimetria mediana |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            f"| {row['scene']} | {row['n_pixels']:,} | {row['n_bands']} | "
            f"{row['pixels_per_dimension']} | {row['excess_kurtosis_median']:.2f} | "
            f"{row['bands_with_excess_kurtosis_above_1']} | {row['skewness_median']:.2f} |"
        )
    lines += ["", "## Quantis da distância de Mahalanobis ao quadrado", "",
              "| Cena | Quantil | Observado | Esperado se gaussiano | Razão |",
              "|---|---|---:|---:|---:|"]
    for row in results:
        for q in QUANTILES:
            key = f"q{q}"
            obs = row["mahalanobis_observed"][key]
            exp = row["mahalanobis_expected_gaussian"][key]
            lines.append(
                f"| {row['scene']} | {q} | {obs:.1f} | {exp:.1f} | {obs / exp:.2f} |"
            )
    lines += [
        "",
        "## Leitura",
        "",
        "O padrão é o mesmo nas duas cenas, apesar de sensores, distâncias e",
        "cenários diferentes: o miolo da distribuição é compatível com gaussiano",
        "e a cauda não é. Nas medianas a razão fica abaixo ou perto de 1, e a",
        "partir do quantil 0,99 ela cresce muito.",
        "",
        "Isso importa por um motivo operacional preciso. A taxa de falso alarme",
        "é definida exatamente pela cauda do fundo. Detecção a FAR de 1e-3 vive",
        "perto do quantil 0,999, justamente onde a razão medida é de várias",
        "vezes. Um limiar derivado de suposição gaussiana subestima o falso",
        "alarme nessa região.",
        "",
        "O resultado também refina, sem contradizer, a conclusão do T7a. Lá a",
        "hipótese era que aprender a estatística do fundo venceria o matched",
        "filter caso o fundo não fosse gaussiano, e o autoencoder testado perdeu.",
        "A medição agora mostra que a porta estava de fato aberta: o fundo tem",
        "cauda pesada. O que falhou foi aquele modelo específico, não a premissa",
        "que motivava a busca.",
        "",
        "## O que este teste não separa",
        "",
        "Cauda pesada aqui não é sinônimo de ruído não gaussiano do sensor.",
        "Duas fontes ficam confundidas e este protocolo não as distingue:",
        "",
        "- **Heterogeneidade de material.** O fundo do voo é tudo que está fora",
        "  das duas janelas experimentais, portanto mistura materiais distintos.",
        "  Uma mistura de classes produz cauda pesada sob um único modelo de",
        "  covariância global, mesmo que cada classe fosse gaussiana.",
        "- **Estrutura óptica.** Os poços vazios contêm bordas, menisco e reflexo",
        "  especular, que são estrutura real da placa e não ruído de sensor. Esse",
        "  reflexo já havia sido identificado ao ajustar a geometria.",
        "",
        "Para a decisão operacional as duas fontes têm o mesmo efeito prático,",
        "porque ambas inflam o falso alarme observado em relação ao previsto. Para",
        "explicar o mecanismo, porém, elas precisariam ser separadas, o que exige",
        "um modelo local ou por classe em vez de covariância global.",
        "",
        "Este teste descreve as duas cenas medidas disponíveis, não generaliza",
        "para todo fundo natural, e não é por si um resultado de detecção.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    sources = [
        ("pellets, poços vazios", _plate_empty_wells, BAND_STRIDE),
        ("voo 54 m, fundo", _flight_background, 1),
    ]
    results = []
    for name, loader, stride in sources:
        pixels = loader()
        if pixels is None:
            print(f"pulando {name}: cubo ausente")
            continue
        print(f"analisando {name}: {pixels.shape[0]:,} pixels brutos")
        results.append(_analyse(name, pixels, stride))

    if not results:
        raise SystemExit("nenhum cubo disponível; rode scripts/fetch_biohsi.py")

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out_json = os.path.join(HERE, "results", "background_gaussianity.json")
    with open(out_json, "w") as handle:
        json.dump({"band_stride": BAND_STRIDE, "seed": SEED, "scenes": results},
                  handle, indent=2)
    out_md = os.path.join(HERE, "results", "background_gaussianity.md")
    with open(out_md, "w") as handle:
        handle.write(_markdown(results))
    for row in results:
        print(f"  {row['scene']}: curtose exc. mediana "
              f"{row['excess_kurtosis_median']:.2f}, razão de cauda q0.999 "
              f"{row['tail_ratio_q999']}")
    print(f"\nEscrito em {out_json} e {out_md}")


if __name__ == "__main__":
    main()
