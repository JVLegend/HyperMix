from pathlib import Path

import pytest

from hypermix.publication import (
    BLOCK_END,
    BLOCK_START,
    PublicationAssetError,
    build_publication_assets,
    collect_publication_data,
    render_svg,
    render_table,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repository_publication_assets_are_current():
    summary = build_publication_assets(REPO_ROOT, check=True)
    assert summary == {"rows": 8, "contrasts": 10, "files": 4}


def test_generated_table_preserves_blocked_and_inconclusive_states():
    rows, _, _ = collect_publication_data(REPO_ROOT)
    table = render_table(rows)
    assert "| Alvo real, T8 |" in table
    assert "| porta bloqueada |" in table
    assert "MAE inconclusiva; intervalo pior" in table
    assert "vantagem aprendida" not in table


def test_oriented_figure_discloses_independent_scales():
    _, plot_rows, _ = collect_publication_data(REPO_ROOT)
    svg = render_svg(plot_rows)
    assert "Each row has its own scale" in svg
    assert "Intervals are not standardized" in svg
    assert svg.count("class=\"ci\"") == 10


def test_check_fails_when_generated_asset_is_missing(tmp_path):
    for relative in (
        "results",
        "publication",
    ):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    for source in (
        "background.json",
        "uncertainty.json",
        "band_sparsity.json",
        "real_target_reproduction.json",
        "target_transfer.json",
        "blind.json",
        "lod.json",
        "abundance_uncertainty.json",
    ):
        (tmp_path / "results" / source).write_bytes(
            (REPO_ROOT / "results" / source).read_bytes()
        )
    (tmp_path / "publication" / "MANUSCRIPT_DRAFT_PTBR.md").write_text(
        f"before\n{BLOCK_START}\nstale\n{BLOCK_END}\nafter\n",
        encoding="utf-8",
    )

    with pytest.raises(PublicationAssetError, match="stale publication assets"):
        build_publication_assets(tmp_path, check=True)
