"""Tests for the offline, deterministic broker pipeline (M1 core).

Covers: SQLite staging, the synthetic ingest+crossmatch stand-ins, quality-cut filtering,
crossings landing in the documented live window, end-to-end artifact generation,
determinism, and that the *live* legs remain clean stubs naming the Lasair-token blocker.
"""

from __future__ import annotations

import pytest

from seti_ellipsoid_broker import pipeline
from seti_ellipsoid_broker.models import Alert


# --- staging ------------------------------------------------------------------------

def test_staging_creates_table_and_inserts():
    conn = pipeline.open_staging(":memory:")
    try:
        n = pipeline.stage_alerts(conn, pipeline.synthetic_alerts())
        assert n == 6
        count = conn.execute("SELECT COUNT(*) FROM alerts_staging").fetchone()[0]
        assert count == 6
        # The alert with no Gaia counterpart (modelled) keeps NULL Gaia columns.
        rows = conn.execute(
            "SELECT gaia_source_id FROM alerts_staging"
        ).fetchall()
        assert all(r[0] is None or isinstance(r[0], int) for r in rows)
    finally:
        conn.close()


def test_staging_is_idempotent_on_key():
    conn = pipeline.open_staging(":memory:")
    try:
        pipeline.stage_alerts(conn, pipeline.synthetic_alerts())
        pipeline.stage_alerts(conn, pipeline.synthetic_alerts())  # re-stage same batch
        count = conn.execute("SELECT COUNT(*) FROM alerts_staging").fetchone()[0]
        assert count == 6  # INSERT OR REPLACE -> no duplicates
    finally:
        conn.close()


def test_no_gaia_counterpart_is_staged_but_not_ranked():
    """An alert whose crossmatch returns None is staged (Gaia NULL) and dropped from ranking."""
    alerts = [Alert("NOMATCH", "ZTF", 10.0, 10.0, 60800.0, 18.0)]
    conn = pipeline.open_staging(":memory:")
    try:
        # crossmatch that always returns None
        pipeline.stage_alerts(conn, alerts, crossmatch=lambda a: None)
        assert conn.execute("SELECT COUNT(*) FROM alerts_staging").fetchone()[0] == 1
        ranked = pipeline.rank_staged(conn)
        assert ranked == []
    finally:
        conn.close()


# --- quality cuts in the pipeline ---------------------------------------------------

def test_pipeline_applies_quality_cuts():
    """The synthetic batch has one RUWE-failing star; it must be cut (6 staged -> 5 ranked)."""
    conn = pipeline.open_staging(":memory:")
    try:
        pipeline.stage_alerts(conn, pipeline.synthetic_alerts())
        ranked = pipeline.rank_staged(conn)
        assert len(ranked) == 5
        refs = {t.source_ref for t in ranked}
        assert "ZTF26aaaaaae" not in refs  # RUWE 1.55 star excluded
        assert all(t.ruwe < 1.4 and t.parallax_over_error > 5 for t in ranked)
    finally:
        conn.close()


# --- science: crossings land in the live window -------------------------------------

def test_crossings_land_in_live_window():
    conn = pipeline.open_staging(":memory:")
    try:
        pipeline.stage_alerts(conn, pipeline.synthetic_alerts())
        ranked = pipeline.rank_staged(conn)
        years = [t.crossing_epoch_jyear for t in ranked]
        # All synthetic survivors cross within the documented ~2024-2030 live window.
        assert all(2023.0 <= y <= 2030.0 for y in years), years
        # And the spread actually exercises the window (not all identical).
        assert max(years) - min(years) > 1.0
    finally:
        conn.close()


def test_ranked_sorted_by_descending_score():
    conn = pipeline.open_staging(":memory:")
    try:
        pipeline.stage_alerts(conn, pipeline.synthetic_alerts())
        ranked = pipeline.rank_staged(conn)
        scores = [t.score for t in ranked]
        assert scores == sorted(scores, reverse=True)
    finally:
        conn.close()


# --- end-to-end ---------------------------------------------------------------------

def test_run_offline_writes_artifacts(tmp_path):
    res = pipeline.run_offline(out_dir=tmp_path, datestamp="20260615")
    assert res.n_staged == 6
    assert res.n_ranked == 5
    assert set(res.artifacts) == {"csv", "tgt", "md"}
    for p in res.artifacts.values():
        assert p.exists() and p.stat().st_size > 0


def test_run_offline_is_deterministic(tmp_path):
    r1 = pipeline.run_offline(out_dir=tmp_path / "a", datestamp="20260615")
    r2 = pipeline.run_offline(out_dir=tmp_path / "b", datestamp="20260615")
    for kind in ("csv", "tgt", "md"):
        assert r1.artifacts[kind].read_bytes() == r2.artifacts[kind].read_bytes()


def test_run_offline_with_sqlite_file(tmp_path):
    """The staging DB can be a real on-disk SQLite file, not just in-memory."""
    db = tmp_path / "staging.sqlite"
    res = pipeline.run_offline(out_dir=tmp_path, datestamp="20260615", db_path=db)
    assert db.exists()
    assert res.n_ranked == 5


# --- live legs remain clean, named stubs --------------------------------------------

def test_live_lasair_stub_names_token():
    from seti_ellipsoid_broker.ingest import lasair

    with pytest.raises(NotImplementedError, match="LASAIR_TOKEN"):
        list(lasair.fetch_recent_alerts(60800.0, token=None))


def test_live_gaia_stub_is_not_implemented():
    from seti_ellipsoid_broker import gaia

    with pytest.raises(NotImplementedError, match="offline M1 core"):
        list(gaia.crossmatch([]))


def test_predictor_stub_is_not_implemented():
    from seti_ellipsoid_broker import predictor

    with pytest.raises(NotImplementedError, match="M3"):
        list(predictor.upcoming_crossings())
