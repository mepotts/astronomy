"""Tests for the LIVE, account-free path: --transients-csv -> Gaia crossmatch + zero-point.

The Gaia leg is mocked (an injected ``launch`` returning a canned astropy Table), so the
whole account-free pipeline runs OFFLINE. Covers the CSV reader schema, the end-to-end
run, and that the zero-point correction actually moves the inferred distance.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.table import MaskedColumn, Table

from seti_ellipsoid_broker import gaia, pipeline
from seti_ellipsoid_broker.ingest import transients

EXAMPLE_CSV = Path(__file__).resolve().parents[1] / "examples" / "transients_example.csv"


# --- canned Gaia table + routing launcher -------------------------------------------

def _canned_table(rows: list[dict]) -> Table:
    t = Table(masked=True)
    int_cols = {"source_id", "astrometric_params_solved"}
    for name in gaia.GAIA_COLUMNS:
        raw = [r.get(name) for r in rows]
        mask = [v is None for v in raw]
        if name in int_cols:
            data = [0 if v is None else int(v) for v in raw]
            t[name] = MaskedColumn(np.array(data, dtype=np.int64), mask=mask)
        else:
            data = [np.nan if v is None else float(v) for v in raw]
            t[name] = MaskedColumn(np.array(data, dtype=float), mask=mask)
    return t


def _source(source_id, ra, dec, parallax, *, g=17.0, nu=1.5, solved=31, poe=24.0, ruwe=1.0):
    return {
        "source_id": source_id, "ra": ra, "dec": dec,
        "parallax": parallax, "parallax_error": parallax / poe, "parallax_over_error": poe,
        "pmra": 0.0, "pmdec": 0.0, "ruwe": ruwe, "phot_g_mean_mag": g,
        "nu_eff_used_in_astrometry": nu, "pseudocolour": None,
        "ecl_lat": -85.0, "astrometric_params_solved": solved,
    }


class _RoutingLaunch:
    """Return the id-table for id queries and the cone-table for cone queries."""

    def __init__(self, id_table: Table, cone_table: Table):
        self.id_table = id_table
        self.cone_table = cone_table
        self.calls: list[str] = []

    def __call__(self, adql: str) -> Table:
        self.calls.append(adql)
        return self.id_table if "source_id IN" in adql else self.cone_table


# --- CSV reader ---------------------------------------------------------------------

def test_read_transients_csv_parses_schema(tmp_path):
    p = tmp_path / "alerts.csv"
    p.write_text(
        "name,ra,dec,gaia_source_id,discovery_date,survey,mag\n"
        "A1,83.9,-69.1,,2026-05-03,ZTF,18.2\n"
        "A2,84.2,-69.4,4657701054736643840,2026-05-04,TNS,16.9\n",
        encoding="utf-8",
    )
    alerts = transients.read_transients_csv(p)
    assert [a.source_ref for a in alerts] == ["A1", "A2"]
    assert alerts[0].gaia_source_id is None
    assert alerts[1].gaia_source_id == 4657701054736643840
    assert alerts[1].survey == "TNS"
    # discovery_date -> mjd (2026-05-04 ~ MJD 61164)
    assert alerts[1].mjd == pytest.approx(61164.0, abs=1.0)


def test_read_transients_csv_accepts_aliases_and_bare_positions(tmp_path):
    p = tmp_path / "alerts.csv"
    p.write_text("objectId,ramean,decmean\nZTFxx,83.5,-69.0\n", encoding="utf-8")
    alerts = transients.read_transients_csv(p)
    assert alerts[0].source_ref == "ZTFxx"
    assert alerts[0].ra_deg == pytest.approx(83.5)
    assert alerts[0].mjd == 0.0  # no mjd/date column -> harmless placeholder


def test_read_transients_csv_missing_required_raises(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("name,ra\nA1,83.9\n", encoding="utf-8")  # no dec
    with pytest.raises(ValueError, match="dec"):
        transients.read_transients_csv(p)


def test_shipped_example_csv_reads():
    alerts = transients.read_transients_csv(EXAMPLE_CSV)
    assert len(alerts) == 5
    assert sum(1 for a in alerts if a.gaia_source_id is not None) == 1


# --- zero-point applied in the staging conversion -----------------------------------

def test_gaia_fields_zeropoint_moves_parallax():
    src = gaia.GaiaSource(
        source_id=123, ra=83.9, dec=-69.1, parallax=1.0, parallax_error=0.04,
        parallax_over_error=25.0, pmra=0.0, pmdec=0.0, ruwe=1.0, phot_g_mean_mag=17.0,
        nu_eff_used_in_astrometry=1.5, pseudocolour=None, ecl_lat=-20.0,
        astrometric_params_solved=31,
    )
    with_zp = pipeline.gaia_fields_from_source(src, apply_zeropoint=True)
    without_zp = pipeline.gaia_fields_from_source(src, apply_zeropoint=False)
    # Z = -0.031318 mas -> corrected parallax = 1.031318 (larger -> star closer)
    assert with_zp.parallax_mas == pytest.approx(1.031318, abs=1e-6)
    assert without_zp.parallax_mas == pytest.approx(1.0, abs=1e-9)
    assert with_zp.parallax_mas > without_zp.parallax_mas


def test_gaia_fields_none_without_parallax():
    src = gaia.GaiaSource(
        source_id=1, ra=0, dec=0, parallax=None, parallax_error=None,
        parallax_over_error=None, pmra=None, pmdec=None, ruwe=1.0, phot_g_mean_mag=17.0,
        nu_eff_used_in_astrometry=1.5, pseudocolour=None, ecl_lat=0.0,
        astrometric_params_solved=31,
    )
    assert pipeline.gaia_fields_from_source(src) is None


# --- end-to-end account-free run (mocked Gaia leg) ----------------------------------

def _write_two_alert_csv(tmp_path) -> Path:
    p = tmp_path / "alerts.csv"
    # one id-resolved alert, one cone-resolved alert (both near SN 1987A so they cross soon)
    p.write_text(
        "name,ra,dec,gaia_source_id\n"
        "IDER,83.90,-69.10,4657701054736643840\n"
        "CONER,84.05,-69.40,\n",
        encoding="utf-8",
    )
    return p


def test_run_live_csv_end_to_end_mocked(tmp_path):
    csv = _write_two_alert_csv(tmp_path)
    id_table = _canned_table([_source(4657701054736643840, 83.90, -69.10, 1.2)])
    cone_table = _canned_table([_source(4657690012345678976, 84.05, -69.40, 1.8)])
    launch = _RoutingLaunch(id_table, cone_table)

    result = pipeline.run_live_csv(
        csv, out_dir=tmp_path / "out", datestamp="20260718", launch=launch, now_jyear=2026.5
    )
    assert result.n_staged == 2
    assert result.n_ranked == 2
    refs = {t.source_ref for t in result.targets}
    assert refs == {"IDER", "CONER"}
    for p in result.artifacts.values():
        assert p.exists() and p.stat().st_size > 0
    # Both queries were exercised (id + cone).
    assert any("source_id IN" in c for c in launch.calls)
    assert any("CONTAINS" in c for c in launch.calls)


def test_run_live_csv_zeropoint_changes_distance(tmp_path):
    csv = _write_two_alert_csv(tmp_path)

    def make_launch():
        id_table = _canned_table([_source(4657701054736643840, 83.90, -69.10, 1.0)])
        cone_table = _canned_table([_source(4657690012345678976, 84.05, -69.40, 1.0)])
        return _RoutingLaunch(id_table, cone_table)

    with_zp = pipeline.run_live_csv(
        csv, out_dir=tmp_path / "a", datestamp="20260718",
        launch=make_launch(), apply_zeropoint=True, now_jyear=2026.5,
    )
    without_zp = pipeline.run_live_csv(
        csv, out_dir=tmp_path / "b", datestamp="20260718",
        launch=make_launch(), apply_zeropoint=False, now_jyear=2026.5,
    )
    d_with = {t.source_ref: t.distance_pc for t in with_zp.targets}
    d_without = {t.source_ref: t.distance_pc for t in without_zp.targets}
    # Correction raises parallax -> reduces distance for every source.
    for ref in d_with:
        assert d_with[ref] < d_without[ref]
