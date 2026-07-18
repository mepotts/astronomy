"""EXTERNAL acceptance test — reproduce Nilipour et al. (2023) SN 1987A crossing epochs.

This is the project's M1 acceptance gate turned from *self-consistent* into *externally
validated*: the ellipsoid math must reproduce the published SETI-Ellipsoid crossing times
of Nilipour, Davenport, Croft & Siemion (2023), "Signal Synchronization Strategies and
Time Domain SETI with Gaia DR3", AJ 166, 79 (DOI 10.3847/1538-3881/acde79, arXiv:2308.00066).

Ground truth is the paper's published machine-readable Table 2 (the SN='1987A',
Seto='False' subset), shipped verbatim as tests/data/nilipour2023_sn1987a_ellipsoid.csv
(see that file's header for provenance). For each target we feed the authors' own
Bailer-Jones (2021) distance and Gaia position into our ellipsoid solver and require the
crossing epoch to match their XTime (converted BJD -> decimal year).

Their crossing-time definition (from the paper's ``ellipsoid.py``: ``etime = d1 + d2 - 2c``
with ``c = d_SN/2`` and reference epoch 1987-02-23) is identical to ours, and they adopt the
same SN 1987A distance (51.4 kpc), so agreement should be tight (observed max residual
~5e-4 yr over all 217 targets); the tolerance below is deliberately looser to stay robust
to sub-arcsecond coordinate/epoch bookkeeping while still catching any real geometry regression.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

from seti_ellipsoid_broker import ellipsoid as E
from seti_ellipsoid_broker import pipeline, ranking
from seti_ellipsoid_broker.models import Alert
from seti_ellipsoid_broker.pipeline import GaiaFields

FIXTURE = Path(__file__).resolve().parent / "data" / "nilipour2023_sn1987a_ellipsoid.csv"

# Tolerance on |ours - theirs| (decimal years). Observed max ~0.0005 yr; 0.01 yr = 20x margin.
CROSSING_EPOCH_TOL_YR = 0.01


def _load_targets() -> list[dict]:
    rows: list[dict] = []
    with FIXTURE.open(encoding="utf-8") as f:
        header = None
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if header is None:
                header = line.split(",")
                continue
            vals = line.split(",")
            rec = dict(zip(header, vals))
            rows.append(rec)
    return rows


@pytest.fixture(scope="module")
def nilipour_targets() -> list[dict]:
    assert FIXTURE.exists(), f"missing Nilipour fixture: {FIXTURE}"
    rows = _load_targets()
    assert rows, "Nilipour fixture is empty"
    return rows


def _their_year(rec: dict) -> float:
    return float(Time(float(rec["xtime_bjd"]), format="jd").jyear)


def _sep_deg(rec: dict) -> float:
    coord = SkyCoord(ra=float(rec["ra_deg"]) * u.deg, dec=float(rec["dec_deg"]) * u.deg, frame="icrs")
    return float(E.separation_from_sn_deg(coord))


def test_fixture_is_the_sn1987a_ellipsoid_subset(nilipour_targets):
    # The published SN 1987A SETI-Ellipsoid subset of Table 2.
    assert len(nilipour_targets) == 217
    # Crossing epochs all fall inside the Gaia DR3 epoch-photometry window (mid-2014..mid-2017).
    years = [_their_year(r) for r in nilipour_targets]
    assert all(2014.0 <= y <= 2018.0 for y in years)


def test_crossing_epochs_match_nilipour_within_tolerance(nilipour_targets):
    """Core external validation: ours vs. their XTime for every SN 1987A ellipsoid target."""
    residuals = []
    for rec in nilipour_targets:
        dist_pc = float(rec["dist_pc"])
        mine = float(E.crossing_epoch(dist_pc, _sep_deg(rec)))
        theirs = _their_year(rec)
        residuals.append(abs(mine - theirs))
    worst = max(residuals)
    assert worst < CROSSING_EPOCH_TOL_YR, f"max crossing-epoch residual {worst:.5f} yr too large"
    # And typically far tighter than the tolerance.
    residuals.sort()
    median = residuals[len(residuals) // 2]
    assert median < 0.005


def test_crossing_epochs_within_authors_own_uncertainty(nilipour_targets):
    """Our epoch sits well inside each target's published 1-sigma crossing-time error."""
    for rec in nilipour_targets:
        mine = float(E.crossing_epoch(float(rec["dist_pc"]), _sep_deg(rec)))
        theirs = _their_year(rec)
        assert abs(mine - theirs) <= float(rec["xtime_err_yr"]) + 1e-6


def test_pipeline_reproduces_nilipour_epochs(nilipour_targets):
    """Feed a sample of Nilipour targets through the REAL staging+ranking path (not just the
    bare solver) and confirm the ranked crossing epochs still match the published values."""
    sample = nilipour_targets[:20]
    fields_by_ref: dict[str, GaiaFields] = {}
    alerts: list[Alert] = []
    for i, rec in enumerate(sample):
        ref = f"NIL{i:03d}"
        alerts.append(Alert(ref, "NILIPOUR", float(rec["ra_deg"]), float(rec["dec_deg"]), 0.0))
        fields_by_ref[ref] = GaiaFields(
            gaia_source_id=int(rec["gaia_source_id"]),
            parallax_mas=1000.0 / float(rec["dist_pc"]),  # invert their distance
            parallax_over_error=20.0,  # comfortably passes the quality cut
            ruwe=1.0,
            neighbor_count=50,
        )
    conn = pipeline.open_staging(":memory:")
    try:
        pipeline.stage_alerts(conn, alerts, crossmatch=lambda a: fields_by_ref[a.source_ref])
        ranked = pipeline.rank_staged(conn, now_jyear=ranking.DEFAULT_NOW_JYEAR)
    finally:
        conn.close()
    assert len(ranked) == len(sample)
    by_ref = {t.source_ref: t for t in ranked}
    for i, rec in enumerate(sample):
        t = by_ref[f"NIL{i:03d}"]
        assert abs(t.crossing_epoch_jyear - _their_year(rec)) < CROSSING_EPOCH_TOL_YR
