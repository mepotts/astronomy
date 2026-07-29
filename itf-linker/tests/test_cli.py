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
