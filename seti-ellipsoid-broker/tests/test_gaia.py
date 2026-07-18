"""Tests for the live Gaia DR3 crossmatch (gaia.py) — fully OFFLINE via an injected launcher.

The network-touching part of ``gaia`` is isolated behind a ``launch(adql) -> Table``
callable. Here we pass a fake that returns a small canned astropy Table (with masked
columns for the usual NULLs), so no query ever leaves the process.
"""

from __future__ import annotations

import numpy as np
import pytest
from astropy.table import MaskedColumn, Table

from seti_ellipsoid_broker import gaia
from seti_ellipsoid_broker.models import Alert


# --- a small canned Gaia table ------------------------------------------------------

def _canned_table(rows: list[dict]) -> Table:
    """Build a masked astropy Table over GAIA_COLUMNS from a list of dicts (None -> masked)."""
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


class _FakeLaunch:
    """Records the ADQL it was asked to run and returns a preset table."""

    def __init__(self, table: Table):
        self.table = table
        self.calls: list[str] = []

    def __call__(self, adql: str) -> Table:
        self.calls.append(adql)
        return self.table


# A 5-parameter and a 6-parameter source, with the complementary colour column masked.
_ROW_5P = {
    "source_id": 4657701054736643840,  # 19-digit id must survive without float mangling
    "ra": 83.8, "dec": -69.3,
    "parallax": 1.23, "parallax_error": 0.05, "parallax_over_error": 24.6,
    "pmra": 1.1, "pmdec": -2.2, "ruwe": 1.03, "phot_g_mean_mag": 17.0,
    "nu_eff_used_in_astrometry": 1.5, "pseudocolour": None,  # 5p -> pseudocolour NULL
    "ecl_lat": -85.5, "astrometric_params_solved": 31,
}
_ROW_6P = {
    "source_id": 4657690012345678976,
    "ra": 84.0, "dec": -69.4,
    "parallax": 2.0, "parallax_error": 0.08, "parallax_over_error": 25.0,
    "pmra": 0.5, "pmdec": -1.0, "ruwe": 0.98, "phot_g_mean_mag": 18.2,
    "nu_eff_used_in_astrometry": None, "pseudocolour": 1.5,  # 6p -> nu_eff NULL
    "ecl_lat": -85.0, "astrometric_params_solved": 95,
}


# --- ADQL builders ------------------------------------------------------------------

def test_source_id_adql_lists_ids_and_columns():
    adql = gaia.build_source_id_adql([111, 222])
    assert "source_id IN (111, 222)" in adql
    for col in gaia.GAIA_COLUMNS:
        assert col in adql
    assert "gaiadr3.gaia_source" in adql


def test_source_id_adql_rejects_empty():
    with pytest.raises(ValueError):
        gaia.build_source_id_adql([])


def test_cone_adql_uses_contains_and_radius():
    adql = gaia.build_cone_adql(83.8, -69.3, 5.0)
    assert "CONTAINS(POINT('ICRS', ra, dec)" in adql
    assert "CIRCLE('ICRS'" in adql
    # 5 arcsec -> ~0.00139 deg
    assert "0.0013888" in adql


# --- table parsing ------------------------------------------------------------------

def test_table_to_sources_preserves_19_digit_id_and_masks():
    table = _canned_table([_ROW_5P, _ROW_6P])
    sources = gaia._table_to_sources(table)
    assert sources[0].source_id == 4657701054736643840  # exact, not a float
    assert sources[0].nu_eff_used_in_astrometry == pytest.approx(1.5)
    assert sources[0].pseudocolour is None            # masked -> None
    assert sources[1].nu_eff_used_in_astrometry is None
    assert sources[1].pseudocolour == pytest.approx(1.5)
    assert sources[1].astrometric_params_solved == 95


# --- crossmatch dispatch ------------------------------------------------------------

def test_crossmatch_by_source_id_path():
    alert = Alert("ZTFxx", "ZTF", 83.8, -69.3, 60800.0, 17.0, gaia_source_id=4657701054736643840)
    fake = _FakeLaunch(_canned_table([_ROW_5P]))
    out = gaia.crossmatch([alert], launch=fake)
    assert set(out) == {"ZTFxx"}
    assert out["ZTFxx"].source_id == 4657701054736643840
    # The id path issues an id query (not a cone query).
    assert any("source_id IN" in c for c in fake.calls)
    assert not any("CONTAINS" in c for c in fake.calls)


def test_crossmatch_cone_path_picks_nearest():
    # Two sources in the cone; the alert sits essentially on _ROW_5P, so it must win.
    far = dict(_ROW_6P, ra=83.95, dec=-69.35)
    fake = _FakeLaunch(_canned_table([far, _ROW_5P]))
    alert = Alert("CONEonly", "CSV", 83.8001, -69.3001, 60800.0, 17.0)  # no gaia id
    out = gaia.crossmatch([alert], launch=fake)
    assert out["CONEonly"].source_id == _ROW_5P["source_id"]  # nearest chosen
    assert any("CONTAINS" in c for c in fake.calls)


def test_crossmatch_empty_makes_no_calls():
    fake = _FakeLaunch(_canned_table([_ROW_5P]))
    assert gaia.crossmatch([], launch=fake) == {}
    assert fake.calls == []


def test_crossmatch_absent_when_no_counterpart():
    fake = _FakeLaunch(_canned_table([]))  # empty result -> no match
    alert = Alert("NOPE", "CSV", 10.0, 10.0, 60800.0, 18.0)
    assert gaia.crossmatch([alert], launch=fake) == {}
