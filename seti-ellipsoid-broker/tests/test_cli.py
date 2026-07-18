"""CLI tests (typer.testing.CliRunner). The --transients-csv Gaia leg is monkeypatched,
so every test here is fully OFFLINE."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from seti_ellipsoid_broker import cli, gaia
from seti_ellipsoid_broker.cli import app

runner = CliRunner()
EXAMPLE_CSV = Path(__file__).resolve().parents[1] / "examples" / "transients_example.csv"


def test_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "seti-ellipsoid-broker" in res.stdout


def test_offline_run_writes_artifacts_and_shows_now(tmp_path):
    res = runner.invoke(app, ["run", "--now", "2026.5", "-o", str(tmp_path)])
    assert res.exit_code == 0
    assert "now=2026.500" in res.stdout
    assert "crossing_now" in res.stdout
    assert list(tmp_path.glob("ellipsoid_targets_*.csv"))


def test_run_now_default_is_clock_coupled():
    """With no --now, the CLI uses the current time (not the frozen DEFAULT_NOW_JYEAR)."""
    from astropy.time import Time

    now = cli._now_jyear()
    assert now > 2026.0
    assert now == __import__("pytest").approx(Time.now().jyear, abs=0.01)


def test_live_flag_exits_2_and_points_to_csv():
    res = runner.invoke(app, ["run", "--live"])
    assert res.exit_code == 2
    assert "ACCOUNT-GATED" in res.stderr
    assert "--transients-csv" in res.stderr


def test_transients_csv_path_runs_offline_with_mocked_gaia(tmp_path, monkeypatch):
    # Return a canned Gaia counterpart for two of the example rows; no network.
    def fake_crossmatch(alerts, radius_arcsec=5.0, *, launch=None):
        out = {}
        for a in alerts:
            if a.source_ref in ("ZTF-example-01", "SN2026xyz"):
                out[a.source_ref] = gaia.GaiaSource(
                    source_id=a.gaia_source_id or 4657700000000000000,
                    ra=a.ra_deg, dec=a.dec_deg, parallax=1.1, parallax_error=0.05,
                    parallax_over_error=22.0, pmra=0.0, pmdec=0.0, ruwe=1.0,
                    phot_g_mean_mag=17.5, nu_eff_used_in_astrometry=1.5,
                    pseudocolour=None, ecl_lat=-85.0, astrometric_params_solved=31,
                )
        return out

    monkeypatch.setattr(gaia, "crossmatch", fake_crossmatch)
    res = runner.invoke(
        app,
        ["run", "--transients-csv", str(EXAMPLE_CSV), "--now", "2026.5", "-o", str(tmp_path)],
    )
    assert res.exit_code == 0, res.stdout
    assert "LIVE, account-free" in res.stdout
    assert "zero-point ON" in res.stdout
    assert list(tmp_path.glob("ellipsoid_targets_*.csv"))


def test_transients_csv_no_zeropoint_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(gaia, "crossmatch", lambda alerts, radius_arcsec=5.0, *, launch=None: {})
    res = runner.invoke(
        app,
        ["run", "--transients-csv", str(EXAMPLE_CSV), "--no-zeropoint", "-o", str(tmp_path)],
    )
    assert res.exit_code == 0, res.stdout
    assert "zero-point OFF" in res.stdout
