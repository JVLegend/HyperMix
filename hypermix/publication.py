"""Deterministic publication assets derived from versioned result JSON files.

This module intentionally uses only the Python standard library so the
publication drift check can run before scientific dependencies are installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


SOURCE_FILES = (
    "results/background.json",
    "results/uncertainty.json",
    "results/band_sparsity.json",
    "results/real_target_reproduction.json",
    "results/target_transfer.json",
    "results/blind.json",
    "results/lod.json",
    "results/abundance_uncertainty.json",
)

GENERATED_DIR = Path("publication/generated")
TABLE_PATH = GENERATED_DIR / "main_results_table.md"
FIGURE_PATH = GENERATED_DIR / "main_contrasts.svg"
PROVENANCE_PATH = GENERATED_DIR / "source_provenance.json"
MANUSCRIPT_PATH = Path("publication/MANUSCRIPT_DRAFT_PTBR.md")
BLOCK_START = "<!-- BEGIN GENERATED MAIN RESULTS -->"
BLOCK_END = "<!-- END GENERATED MAIN RESULTS -->"


class PublicationAssetError(ValueError):
    """Raised when publication inputs or committed generated assets diverge."""


@dataclass(frozen=True)
class Interval:
    mean: float
    low: float
    high: float

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], context: str) -> "Interval":
        try:
            result = cls(
                mean=float(value["mean"]),
                low=float(value["ci_low"]),
                high=float(value["ci_high"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PublicationAssetError(f"invalid interval at {context}") from exc
        if result.low > result.high:
            raise PublicationAssetError(f"reversed interval at {context}")
        return result

    def oriented(self, higher_is_better: bool) -> "Interval":
        if higher_is_better:
            return self
        return Interval(-self.mean, -self.high, -self.low)


@dataclass(frozen=True)
class TableRow:
    axis: str
    contrast: str
    result: str
    verdict: str


@dataclass(frozen=True)
class PlotRow:
    label: str
    interval: Interval
    digits: int


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicationAssetError(f"cannot read {relative}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PublicationAssetError(f"expected object in {relative}")
    return payload


def _nested(payload: Mapping[str, Any], path: Sequence[str], context: str) -> Any:
    current: Any = payload
    try:
        for key in path:
            current = current[key]
    except (KeyError, TypeError) as exc:
        joined = ".".join(path)
        raise PublicationAssetError(f"missing {joined} in {context}") from exc
    return current


def _interval(payload: Mapping[str, Any], path: Sequence[str], context: str) -> Interval:
    value = _nested(payload, path, context)
    if not isinstance(value, Mapping):
        raise PublicationAssetError(f"expected interval at {context}:{'.'.join(path)}")
    return Interval.from_mapping(value, f"{context}:{'.'.join(path)}")


def _decimal(value: float, digits: int, signed: bool = False) -> str:
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{value:.{digits}f}".replace(".", ",")


def _format_interval(value: Interval, digits: int) -> str:
    return (
        f"{_decimal(value.mean, digits, signed=True)} "
        f"[{_decimal(value.low, digits)}, {_decimal(value.high, digits)}]"
    )


def _crosses_zero(value: Interval) -> bool:
    return value.low <= 0.0 <= value.high


def _verdict_from_advantage(value: Interval) -> str:
    if value.low > 0.0:
        return "vantagem aprendida"
    if value.high < 0.0:
        return "aprendizado pior"
    return "inconclusivo"


def collect_publication_data(root: str | Path) -> tuple[list[TableRow], list[PlotRow], dict[str, Any]]:
    """Extract the manuscript table and oriented contrasts from result JSONs."""

    root_path = Path(root).resolve()
    data = {relative: _read_json(root_path, relative) for relative in SOURCE_FILES}

    background = data["results/background.json"]
    background_auc = _interval(background, ("comparison", "auc"), "background")
    background_pd = _interval(background, ("comparison", "pd_at_far"), "background")

    uncertainty = data["results/uncertainty.json"]
    uncertainty_nll = _interval(uncertainty, ("comparison", "nll"), "uncertainty")
    uncertainty_ece = _interval(uncertainty, ("comparison", "ece"), "uncertainty")

    bands = data["results/band_sparsity.json"]
    bands_auc = _interval(
        bands,
        ("comparison", "top_3_minus_all", "auc_mf_spatial"),
        "band_sparsity",
    )
    smallest_k = str(
        _nested(
            bands,
            ("comparison", "smallest_k_within_0_005_of_full_mean"),
            "band_sparsity",
        )
    )

    real_target = data["results/real_target_reproduction.json"]
    gate_passed = bool(_nested(real_target, ("gate", "passed"), "real_target"))
    gate_mae = float(
        _nested(real_target, ("reproduction_metrics", "mae"), "real_target")
    )
    gate_pearson = float(
        _nested(real_target, ("reproduction_metrics", "pearson_r"), "real_target")
    )

    transfer = data["results/target_transfer.json"]
    transfer_auc = _interval(transfer, ("comparison", "auc"), "target_transfer")
    transfer_pd = _interval(transfer, ("comparison", "pd_at_far"), "target_transfer")
    nominal_auc = _interval(
        transfer,
        ("secondary_nominal_comparison", "auc"),
        "target_transfer",
    )
    nominal_pd = _interval(
        transfer,
        ("secondary_nominal_comparison", "pd_at_far"),
        "target_transfer",
    )

    blind = data["results/blind.json"]
    blind_auc = _interval(
        blind,
        ("comparisons", "learned_family_minus_family_centroid_spatial", "auc"),
        "blind",
    )
    blind_pd = _interval(
        blind,
        (
            "comparisons",
            "learned_family_minus_family_centroid_spatial",
            "pd_at_far",
        ),
        "blind",
    )

    lod = data["results/lod.json"]
    limits = _nested(lod, ("summary", "limits"), "lod")
    if not isinstance(limits, Mapping) or not limits:
        raise PublicationAssetError("missing sensor limits in lod")
    nominal_lods: list[float] = []
    far_1e3_crossings: list[float | None] = []
    for sensor, sensor_limits in limits.items():
        try:
            nominal = sensor_limits["1e-02"]["nominal_lod"]
            far_1e3 = sensor_limits["1e-03"]["nominal_lod"]
        except (KeyError, TypeError) as exc:
            raise PublicationAssetError(f"invalid LOD limits for sensor {sensor}") from exc
        if nominal is not None:
            nominal_lods.append(float(nominal))
        far_1e3_crossings.append(None if far_1e3 is None else float(far_1e3))
    if not nominal_lods:
        raise PublicationAssetError("no nominal LOD crossing at FAR 1e-2")
    lod_min = min(nominal_lods)
    lod_max = max(nominal_lods)
    lod_1e3_text = (
        ">20%"
        if all(value is None for value in far_1e3_crossings)
        else "cruzamento observado"
    )

    abundance = data["results/abundance_uncertainty.json"]
    abundance_mae = _interval(abundance, ("differences", "mae"), "abundance")
    abundance_width = _interval(abundance, ("differences", "width"), "abundance")

    rows = [
        TableRow(
            "Fundo auto-supervisionado, T7a",
            "autoencoder espacial menos MF espacial",
            f"AUC {_format_interval(background_auc, 3)}; Pd {_format_interval(background_pd, 3)}",
            _verdict_from_advantage(background_auc),
        ),
        TableRow(
            "Incerteza, T7b",
            "ensemble menos MF espacial calibrado",
            f"NLL {_format_interval(uncertainty_nll, 5)}; ECE {_format_interval(uncertainty_ece, 5)}",
            _verdict_from_advantage(uncertainty_nll.oriented(False)),
        ),
        TableRow(
            "Bandas, T7c",
            "top-3 menos todas as bandas",
            f"AUC espacial {_format_interval(bands_auc, 4)}; menor k descritivo {smallest_k}",
            "três bandas não bastaram" if bands_auc.high < 0.0 else "inconclusivo",
        ),
        TableRow(
            "Alvo real, T8",
            "reprodução da Figura 4g nas caixas candidatas",
            f"MAE {_decimal(gate_mae, 6)}; Pearson {_decimal(gate_pearson, 6)}",
            "porta passou" if gate_passed else "porta bloqueada",
        ),
        TableRow(
            "Transferência, T9",
            "família física menos alvo laboratorial",
            f"AUC {_format_interval(transfer_auc, 3)}; Pd {_format_interval(transfer_pd, 3)}",
            _verdict_from_advantage(transfer_auc),
        ),
        TableRow(
            "Alvo retido, T10",
            "MLP familiar menos MF familiar",
            f"AUC {_format_interval(blind_auc, 4)}; Pd {_format_interval(blind_pd, 4)}",
            _verdict_from_advantage(blind_auc),
        ),
        TableRow(
            "Limite, T11",
            "LOD em FAR 1e-2 e referência em FAR 1e-3",
            (
                f"nominal {_decimal(100 * lod_min, 0)}% a {_decimal(100 * lod_max, 0)}% "
                f"em FAR 1e-2; {lod_1e3_text} em FAR 1e-3"
            ),
            "resultado do simulador",
        ),
        TableRow(
            "Abundância, T12",
            "unmixer menos MF",
            f"MAE {_format_interval(abundance_mae, 4)}; largura {_format_interval(abundance_width, 4)}",
            (
                "MAE inconclusiva; intervalo pior"
                if _crosses_zero(abundance_mae) and abundance_width.low > 0.0
                else "reavaliar veredito"
            ),
        ),
    ]

    plot_rows = [
        PlotRow("T7a · AUC", background_auc.oriented(True), 3),
        PlotRow("T7a · Pd@FAR", background_pd.oriented(True), 3),
        PlotRow("T7b · NLL, sinal invertido", uncertainty_nll.oriented(False), 5),
        PlotRow("T7b · ECE, sinal invertido", uncertainty_ece.oriented(False), 5),
        PlotRow("T9 · AUC", transfer_auc.oriented(True), 3),
        PlotRow("T9 · Pd@FAR", transfer_pd.oriented(True), 3),
        PlotRow("T10 · AUC", blind_auc.oriented(True), 4),
        PlotRow("T10 · Pd@FAR", blind_pd.oriented(True), 4),
        PlotRow("T12 · MAE, sinal invertido", abundance_mae.oriented(False), 4),
        PlotRow("T12 · largura, sinal invertido", abundance_width.oriented(False), 4),
    ]

    provenance = {
        "schema_version": 1,
        "generator": "scripts/build_publication_assets.py",
        "interpretation": (
            "Contrastes da figura são orientados para que valores positivos "
            "favoreçam o método aprendido. Cada linha usa escala própria."
        ),
        "sources": {
            relative: sha256((root_path / relative).read_bytes()).hexdigest()
            for relative in SOURCE_FILES
        },
        "secondary_transfer": {
            "nominal_auc": nominal_auc.__dict__,
            "nominal_pd_at_far": nominal_pd.__dict__,
        },
        "table": [row.__dict__ for row in rows],
        "plot": [
            {"label": row.label, "interval": row.interval.__dict__}
            for row in plot_rows
        ],
    }
    return rows, plot_rows, provenance


def render_table(rows: Sequence[TableRow]) -> str:
    """Render the main manuscript results table in pt-BR Markdown."""

    lines = [
        "| Eixo | Contraste principal | Resultado com IC 95% | Veredito |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {row.axis} | {row.contrast} | {row.result} | {row.verdict} |"
        for row in rows
    )
    return "\n".join(lines) + "\n"


def render_svg(rows: Sequence[PlotRow]) -> str:
    """Render a dependency-free SVG of oriented paired contrasts."""

    width = 1500
    row_height = 62
    top = 128
    height = top + len(rows) * row_height + 112
    axis_left = 530
    axis_right = 1010
    axis_middle = (axis_left + axis_right) / 2
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>HyperMix: paired contrasts oriented toward learned advantage</title>",
        "<desc>Each row has an independent scale. Positive values favor learning; negative values favor the matched-filter baseline.</desc>",
        '<rect width="100%" height="100%" fill="#071316"/>',
        '<style>text{font-family:Inter,Arial,sans-serif}.title{fill:#f3f7f5;font-size:28px;font-weight:700}.subtitle{fill:#9eb5ad;font-size:16px}.label{fill:#dce8e3;font-size:16px}.value{fill:#dce8e3;font-size:15px;font-variant-numeric:tabular-nums}.verdict{font-size:14px;font-weight:700}.grid{stroke:#345149;stroke-width:1}.zero{stroke:#c6d4cf;stroke-width:2}.ci{stroke-width:5;stroke-linecap:round}.dot{stroke:#071316;stroke-width:2}</style>',
        '<text x="36" y="44" class="title">Paired evidence, oriented toward learned advantage</text>',
        '<text x="36" y="76" class="subtitle">Positive favors learning; negative favors the matched-filter baseline. Each row has its own scale.</text>',
        f'<text x="{axis_left}" y="108" class="subtitle" text-anchor="start">classical baseline</text>',
        f'<text x="{axis_middle}" y="108" class="subtitle" text-anchor="middle">0</text>',
        f'<text x="{axis_right}" y="108" class="subtitle" text-anchor="end">learned method</text>',
    ]

    for index, row in enumerate(rows):
        y = top + index * row_height
        scale = max(abs(row.interval.low), abs(row.interval.high), 1e-12) * 1.2

        def x_position(value: float) -> float:
            return axis_middle + (value / scale) * ((axis_right - axis_left) / 2)

        low_x = x_position(row.interval.low)
        high_x = x_position(row.interval.high)
        mean_x = x_position(row.interval.mean)
        color = (
            "#55d69e"
            if row.interval.low > 0.0
            else "#ff7b72"
            if row.interval.high < 0.0
            else "#e6b85c"
        )
        verdict = (
            "learned advantage"
            if row.interval.low > 0.0
            else "classical advantage"
            if row.interval.high < 0.0
            else "inconclusive"
        )
        value_text = _format_interval(row.interval, row.digits).replace(",", ".")
        output.extend(
            [
                f'<line x1="{axis_left}" y1="{y}" x2="{axis_right}" y2="{y}" class="grid"/>',
                f'<line x1="{axis_middle}" y1="{y - 21}" x2="{axis_middle}" y2="{y + 21}" class="zero"/>',
                f'<text x="36" y="{y + 6}" class="label">{escape(row.label)}</text>',
                f'<line x1="{low_x:.2f}" y1="{y}" x2="{high_x:.2f}" y2="{y}" class="ci" stroke="{color}"/>',
                f'<circle cx="{mean_x:.2f}" cy="{y}" r="7" class="dot" fill="{color}"/>',
                f'<text x="1045" y="{y + 6}" class="value">{escape(value_text)}</text>',
                f'<text x="1280" y="{y + 6}" class="verdict" fill="{color}">{escape(verdict)}</text>',
            ]
        )

    caption_y = top + len(rows) * row_height + 32
    output.extend(
        [
            f'<text x="36" y="{caption_y}" class="subtitle">Intervals are not standardized. Compare direction and zero crossing row by row, not line length across metrics.</text>',
            f'<text x="36" y="{caption_y + 30}" class="subtitle">T7b and T12 loss/error contrasts are sign-inverted only for this directional display.</text>',
            "</svg>",
        ]
    )
    return "\n".join(output) + "\n"


def _replace_manuscript_block(manuscript: str, table: str) -> str:
    start_count = manuscript.count(BLOCK_START)
    end_count = manuscript.count(BLOCK_END)
    if start_count != 1 or end_count != 1:
        raise PublicationAssetError(
            "manuscript must contain exactly one generated main-results block"
        )
    before, remainder = manuscript.split(BLOCK_START, 1)
    _, after = remainder.split(BLOCK_END, 1)
    return f"{before}{BLOCK_START}\n{table.rstrip()}\n{BLOCK_END}{after}"


def build_publication_assets(root: str | Path, check: bool = False) -> dict[str, int]:
    """Write or verify generated manuscript assets and the manuscript table block."""

    root_path = Path(root).resolve()
    rows, plot_rows, provenance = collect_publication_data(root_path)
    table = render_table(rows)
    outputs = {
        TABLE_PATH: (
            "# Tabela principal gerada\n\n"
            "Não edite manualmente. Execute `python scripts/build_publication_assets.py`.\n\n"
            + table
        ),
        FIGURE_PATH: render_svg(plot_rows),
        PROVENANCE_PATH: json.dumps(
            provenance,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
    }

    manuscript_file = root_path / MANUSCRIPT_PATH
    try:
        manuscript = manuscript_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise PublicationAssetError(f"cannot read manuscript: {exc}") from exc
    outputs[MANUSCRIPT_PATH] = _replace_manuscript_block(manuscript, table)

    stale: list[str] = []
    for relative, content in outputs.items():
        path = root_path / relative
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if check:
            stale.append(relative.as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if stale:
        joined = ", ".join(stale)
        raise PublicationAssetError(
            f"stale publication assets: {joined}; run scripts/build_publication_assets.py"
        )
    return {"rows": len(rows), "contrasts": len(plot_rows), "files": len(outputs)}


__all__ = [
    "BLOCK_END",
    "BLOCK_START",
    "FIGURE_PATH",
    "MANUSCRIPT_PATH",
    "PROVENANCE_PATH",
    "PublicationAssetError",
    "SOURCE_FILES",
    "TABLE_PATH",
    "build_publication_assets",
    "collect_publication_data",
    "render_svg",
    "render_table",
]
