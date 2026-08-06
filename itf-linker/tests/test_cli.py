"""CLI smoke tests. Nothing here touches the network or the full snapshot."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from itf_linker import __version__
from itf_linker.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_help_lists_the_m0_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("fetch", "parse", "counts", "tracklets", "killcheck", "partition", "m0"):
        assert cmd in result.stdout


def test_counts_without_a_snapshot_fails_cleanly(tmp_path, monkeypatch):
    """Missing data must produce an actionable message, not a stack trace."""
    from itf_linker import config

    monkeypatch.setattr(config, "ITF_PARQUET", tmp_path / "absent.parquet")
    from itf_linker import cli

    monkeypatch.setattr(cli.config, "ITF_PARQUET", tmp_path / "absent.parquet")
    result = runner.invoke(app, ["counts"])
    assert result.exit_code != 0
    assert "itf-linker fetch" in result.output


def test_provenance_roundtrip(tmp_path):
    """Provenance is what makes a count reproducible; it must survive a write/read."""
    from itf_linker.ingest.fetch import load_provenance

    payload = {"url": "x", "size_bytes": 1, "last_modified": "Wed, 29 Jul 2026 05:26:45 GMT"}
    p = tmp_path / "prov.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    assert load_provenance(p) == payload
    assert load_provenance(tmp_path / "missing.json") is None


def test_obscode_table_parsing():
    """Fixed-width ObsCodes rows -> {code: east longitude}."""
    from itf_linker.ingest.fetch import parse_obscodes

    text = (
        "Code  Long.       cos        sin    Name\n"
        "F51 203.744090 0.936239 +0.348656 Pan-STARRS 1, Haleakala\n"
        "M21  16.361440 0.848764 -0.527700 Schiaparelli Southern Observatory, Hakos\n"
        "C51                               WISE\n"
    )
    codes = parse_obscodes(text)
    assert codes["F51"] == 203.744090
    assert codes["M21"] == 16.361440
    assert "C51" not in codes  # space telescope: no longitude, must not be invented


def test_help_lists_the_m2_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("vet-extract", "vet-control", "vet", "m2"):
        assert cmd in result.stdout


def test_vet_without_extracted_astrometry_fails_cleanly(tmp_path):
    """Missing inputs must name the command that produces them, not raise from three
    frames down inside a JSON load."""
    report = tmp_path / "m1-report.json"
    report.write_text('{"fits": {"ranked": []}}', encoding="utf-8")
    result = runner.invoke(
        app,
        ["vet", "--report", str(report), "--astrometry", str(tmp_path / "absent.json"),
         "--cache", str(tmp_path / "cache"), "--offline"],
    )
    assert result.exit_code != 0
    assert "vet-extract" in result.output


def test_vet_without_an_m1_report_fails_cleanly(tmp_path):
    result = runner.invoke(
        app,
        ["vet", "--report", str(tmp_path / "absent.json"),
         "--astrometry", str(tmp_path / "also-absent.json"),
         "--cache", str(tmp_path / "cache"), "--offline"],
    )
    assert result.exit_code != 0
    assert "itf-linker m1" in result.output


def test_help_lists_the_m5_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("link-fit-all", "link-vet-extract"):
        assert cmd in result.stdout


def test_link_fit_all_without_a_link_table_fails_cleanly(tmp_path):
    result = runner.invoke(
        app, ["link-fit-all", "--links", str(tmp_path / "absent.parquet"), "--plan-only"]
    )
    assert result.exit_code != 0
    assert "itf-linker m3" in result.output


def test_link_fit_all_plans_a_queue_without_running_anything(tmp_path):
    """`--plan-only` must be answerable from the link table alone: no snapshot, no fo."""
    import polars as pl

    links = tmp_path / "links.parquet"
    pl.DataFrame(
        {
            "desig": ["lnk0000", "lnk0001", "lnk0002"],
            "link_pass": [True, True, False],
            "band": ["belt", "neo", "belt"],
            "pos_spread_au": [1e-4, 9e-4, 1e-4],
            "n_hypotheses_found": [80, 2, 5],
            "n_obscodes": [2, 1, 2],
            "min_trk_n_obs": [3, 2, 3],
            "arc_days": [7.0, 4.0, 6.0],
            "cross_observatory": [True, False, True],
            "arrow_ids": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        }
    ).write_parquet(links)
    result = runner.invoke(
        app,
        ["link-fit-all", "--links", str(links), "--plan-only",
         "--seed-workroot", str(tmp_path / "no-such-seed")],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["queue"]["links"] == 2                      # the gate rejection is excluded
    assert payload["queue"]["tiers"] == {"cross_observatory": 1, "same_observatory": 1}
    assert payload["seeded"] == 0
