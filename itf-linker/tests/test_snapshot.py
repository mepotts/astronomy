"""The snapshot archive: observation keys, delta chain, pruning, and diffing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import polars as pl
import pytest

from itf_linker import snapshot as snap

OBS_SCHEMA = {
    "desig": pl.String, "obscode": pl.String, "mjd": pl.Float64,
    "ra_deg": pl.Float64, "dec_deg": pl.Float64,
}
TRK_SCHEMA = {
    "desig": pl.String, "obscode": pl.String, "night": pl.Int32, "n_obs": pl.UInt32,
}


def _obs(rows):
    return pl.DataFrame(rows, schema=OBS_SCHEMA, orient="row")


def _trk(desigs):
    return pl.DataFrame(
        [(d, "F51", 60000, 3) for d in desigs], schema=TRK_SCHEMA, orient="row"
    )


def _prov(last_modified: str):
    return {"last_modified": last_modified, "url": "x", "size_bytes": 1}


# ----------------------------------------------------------------------------------
# The observation key
# ----------------------------------------------------------------------------------

def test_scalar_and_vectorised_keys_agree():
    """Two implementations of one definition, the way the 80-column parsers are."""
    rows = [
        ("a1", "F51", 60000.123456, 10.5, -5.25),
        ("b2", "G96", 59000.000001, 359.9999999, 89.9),
        ("", "  ", 0.0, 0.0, 0.0),
        ("long-desig", "X05", 61000.5, 180.0, -0.0000001),
    ]
    frame = _obs(rows)
    vector = snap.obs_keys(frame)
    for i, row in enumerate(rows):
        assert int(vector[i]) == snap.obs_key(*row), row


def test_key_is_stable_across_runs():
    """A literal, so a change to the digest cannot slip through and break old snapshots."""
    assert snap.obs_key("RL00adt", "X05", 60875.296948, 343.481392, -9.334283) == snap.obs_key(
        "RL00adt", "X05", 60875.296948, 343.481392, -9.334283
    )
    assert snap.string_digest("F51") == snap.string_digest(" F51 ")


def test_key_changes_with_every_field():
    base = ("a", "F51", 60000.5, 10.0, 5.0)
    keys = {snap.obs_key(*base)}
    for i, changed in enumerate(
        [("b", "F51", 60000.5, 10.0, 5.0),
         ("a", "G96", 60000.5, 10.0, 5.0),
         ("a", "F51", 60000.500001, 10.0, 5.0),
         ("a", "F51", 60000.5, 10.0000001, 5.0),
         ("a", "F51", 60000.5, 10.0, 5.0000001)]
    ):
        keys.add(snap.obs_key(*changed))
        assert len(keys) == i + 2


def test_key_ignores_differences_below_the_recorded_precision():
    """A re-reduced magnitude must not read as "vanished and replaced"."""
    a = snap.obs_key("a", "F51", 60000.5, 10.0, 5.0)
    b = snap.obs_key("a", "F51", 60000.50000001, 10.000000001, 5.0)
    assert a == b


def test_keys_are_64_bit():
    assert 0 <= snap.obs_key("a", "F51", 60000.5, 10.0, 5.0) < 2**64


# ----------------------------------------------------------------------------------
# Snapshot identity
# ----------------------------------------------------------------------------------

def test_snapshot_is_named_after_the_files_last_modified():
    """The ITF is regenerated continuously; naming by fetch date would collide."""
    assert snap.snapshot_id_for(_prov("Wed, 29 Jul 2026 05:26:45 GMT")) == "20260729T052645Z"


def test_snapshot_id_falls_back_to_fetch_time():
    got = snap.snapshot_id_for({"fetched_at_utc": "2026-07-29T05:30:09+00:00"})
    assert got.startswith("20260729T053009")


def test_snapshot_id_survives_missing_provenance():
    assert len(snap.snapshot_id_for(None)) == len("20260729T052645Z")


def test_snapshot_id_rejects_future_server_and_fetch_timestamps():
    future = datetime.now(UTC) + timedelta(hours=1)
    last_modified = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    with pytest.raises(RuntimeError, match="future HTTP Last-Modified"):
        snap.snapshot_id_for(_prov(last_modified))
    with pytest.raises(RuntimeError, match="future fetch timestamp"):
        snap.snapshot_id_for({"fetched_at_utc": future.isoformat()})


# ----------------------------------------------------------------------------------
# Building, diffing, pruning
# ----------------------------------------------------------------------------------

def _build(root, when, rows, **kw):
    return snap.build_snapshot(_obs(rows), _trk({r[0] for r in rows}), _prov(when),
                               root=root, **kw)


A_ROWS = [
    ("keep1", "F51", 60000.5, 10.0, 5.0),
    ("keep2", "F51", 60000.6, 11.0, 5.0),
    ("gone1", "G96", 60001.5, 12.0, 5.0),
    ("gone2", "G96", 60001.6, 13.0, 5.0),
]
B_ROWS = [
    ("keep1", "F51", 60000.5, 10.0, 5.0),
    ("keep2", "F51", 60000.6, 11.0, 5.0),
    ("new1", "X05", 60002.5, 14.0, 5.0),
]


def test_first_snapshot_is_a_baseline(tmp_path):
    m = _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    assert m["is_baseline"] and m["parent_snapshot"] is None
    assert m["observations"] == 4
    assert m["delta"] == {"appeared": 0, "disappeared": 0}


def test_duplicate_records_are_counted_not_hidden(tmp_path):
    rows = A_ROWS + [A_ROWS[0], A_ROWS[0]]
    m = _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", rows)
    assert m["observations"] == 6
    assert m["distinct_obs_keys"] == 4
    assert m["duplicate_observations"] == 2


def test_second_snapshot_records_what_disappeared(tmp_path):
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    m = _build(tmp_path, "Thu, 30 Jul 2026 05:26:45 GMT", B_ROWS)
    assert not m["is_baseline"]
    assert m["parent_snapshot"] == "20260729T052645Z"
    assert m["delta"] == {"disappeared": 2, "appeared": 1}


def test_diff_names_the_designations_that_left(tmp_path):
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    _build(tmp_path, "Thu, 30 Jul 2026 05:26:45 GMT", B_ROWS)
    a, b = snap.list_snapshots(tmp_path)
    d = snap.diff(a, b, root=tmp_path)
    assert d["method"] == "full-key-set"
    assert d["disappeared_observations"] == 2
    assert d["appeared_observations"] == 1
    assert d["net_change"] == -1
    assert {r["desig"] for r in d["top_disappeared"]} == {"gone1", "gone2"}
    assert {r["desig"] for r in d["top_appeared"]} == {"new1"}


def test_delta_chain_answers_the_same_question_after_pruning(tmp_path):
    """The whole point of the archive: old pairs stay comparable from kilobytes."""
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    _build(tmp_path, "Thu, 30 Jul 2026 05:26:45 GMT", B_ROWS)
    a, b = snap.list_snapshots(tmp_path)
    full = snap.diff(a, b, root=tmp_path)

    snap.prune(tmp_path, raw_keep=0, full_keep=0)
    a, b = snap.list_snapshots(tmp_path)
    assert not a.has_full and not b.has_full
    chained = snap.diff(a, b, root=tmp_path)

    assert chained["method"] == "delta-chain"
    assert chained["disappeared_observations"] == full["disappeared_observations"]
    assert chained["appeared_observations"] == full["appeared_observations"]
    assert {r["desig"] for r in chained["top_disappeared"]} == {"gone1", "gone2"}


def test_an_observation_that_returns_nets_out_of_the_chain(tmp_path):
    """Asked "what is gone at B", not "what was ever touched between A and B"."""
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    _build(tmp_path, "Thu, 30 Jul 2026 05:26:45 GMT", B_ROWS)          # gone1/2 leave
    _build(tmp_path, "Fri, 31 Jul 2026 05:26:45 GMT", A_ROWS)          # they come back
    snap.prune(tmp_path, raw_keep=0, full_keep=0)
    first, _, last = snap.list_snapshots(tmp_path)
    d = snap.diff(first, last, root=tmp_path)
    assert d["method"] == "delta-chain"
    assert d["disappeared_observations"] == 0
    assert d["appeared_observations"] == 0


def test_pruning_never_removes_the_permanent_record(tmp_path):
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    _build(tmp_path, "Thu, 30 Jul 2026 05:26:45 GMT", B_ROWS)
    snap.prune(tmp_path, raw_keep=0, full_keep=0)
    for s in snap.list_snapshots(tmp_path):
        assert (s.path / snap.MANIFEST_FILE).exists()
        assert (s.path / snap.DELTA_FILE).exists()
        assert not (s.path / snap.OBS_FILE).exists()


def test_rebuilding_the_same_snapshot_is_a_no_op(tmp_path):
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    again = _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", B_ROWS)
    assert again.get("already_present")
    assert again["observations"] == 4          # untouched, not overwritten by B


def test_snapshots_are_listed_oldest_first(tmp_path):
    _build(tmp_path, "Thu, 30 Jul 2026 05:26:45 GMT", B_ROWS)
    _build(tmp_path, "Wed, 29 Jul 2026 05:26:45 GMT", A_ROWS)
    ids = [s.snapshot_id for s in snap.list_snapshots(tmp_path)]
    assert ids == sorted(ids)


def test_no_snapshots_is_not_an_error(tmp_path):
    assert snap.list_snapshots(tmp_path / "nothing") == []


@pytest.mark.parametrize("keep", [0, 1, 2])
def test_raw_retention_window(tmp_path, keep):
    for day, rows in ((29, A_ROWS), (30, B_ROWS), (31, A_ROWS)):
        _build(tmp_path, f"Wed, {day} Jul 2026 05:26:45 GMT", rows, raw_keep=3, full_keep=3)
    for s in snap.list_snapshots(tmp_path):
        (s.path / snap.RAW_FILE).write_bytes(b"x")
    snap.prune(tmp_path, raw_keep=keep, full_keep=3)
    assert sum(s.has_raw for s in snap.list_snapshots(tmp_path)) == keep
