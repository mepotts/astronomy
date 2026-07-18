"""End-to-end smoke tests for the CLI and pipeline wiring.

Kept deliberately small and offline (the detailed rule coverage lives in ``test_m1_linter.py``).
These run the real Typer CLI against the bundled Gaia fixture by forcing the fixture path through
a monkeypatched ``schema.load_schema`` so no network or on-disk cache is touched.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from adql_copilot import cli, schema
from adql_copilot.schema import load_fixture_schema

runner = CliRunner()


@pytest.fixture(autouse=True)
def _force_fixture_schema(monkeypatch):
    """Make the CLI resolve schemas from the offline fixture only (deterministic, no network)."""
    def _fixture_only(endpoint_key: str, *, refresh: bool = False):
        return load_fixture_schema(endpoint_key)

    monkeypatch.setattr(schema, "load_schema", _fixture_only)
    # the CLI imported the module object, so patching the attribute above is sufficient


def test_cli_clean_query_exits_zero():
    result = runner.invoke(
        cli.app,
        [
            "lint",
            "--endpoint",
            "gaia",
            "SELECT TOP 10 source_id, ra, dec FROM gaiadr3.gaia_source "
            "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1",
        ],
    )
    assert result.exit_code == 0
    assert "OK (no errors)" in result.stdout


def test_cli_broken_query_exits_one_and_reports_unknown_column():
    result = runner.invoke(
        cli.app,
        ["lint", "--endpoint", "gaia", "SELECT parallx FROM gaiadr3.gaia_source WHERE ruwe < 1.4"],
    )
    assert result.exit_code == 1
    assert "UNKNOWN_COLUMN" in result.stdout
    assert "NO_SPATIAL_CONSTRAINT" in result.stdout


def test_cli_json_mode_emits_report():
    result = runner.invoke(
        cli.app,
        ["lint", "--json", "SELECT TOP 5 source_id, ra, dec FROM gaiadr3.gaia_source "
         "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1"],
    )
    assert result.exit_code == 0
    assert '"endpoint_key": "gaia"' in result.stdout
    assert '"diagnostics"' in result.stdout


def test_cli_rejects_unknown_endpoint():
    result = runner.invoke(cli.app, ["lint", "--endpoint", "nope", "SELECT 1 FROM x"])
    assert result.exit_code != 0


def test_cli_endpoints_lists_gaia():
    result = runner.invoke(cli.app, ["endpoints"])
    assert result.exit_code == 0
    assert "gaia" in result.stdout
