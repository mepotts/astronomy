"""A delta that could not be computed must never look like a delta of zero.

On 2026-08-06 the archive recorded ``{appeared: 0, disappeared: 0}`` across a step where
21,627 observations had in fact left the ITF. The parent snapshot's full key set was not
present -- snapshots built on a CI runner commit only ``manifest.json`` and
``delta.parquet``, so their key sets exist solely as a single overwritten release asset --
and ``build_snapshot`` fell back to an empty delta while recording nothing about why.

Zero-because-nothing-changed is a real and common result here (2026-07-29 was one).
Zero-because-nothing-could-be-measured is a hole in the one dataset in this project that
cannot be regenerated. The two must be distinguishable from the manifest alone.
"""

from __future__ import annotations

import polars as pl
import pytest

from itf_linker import snapshot as snap


def _obs(keys: list[int]) -> pl.DataFrame:
    """Minimal observation frame; only the columns build_snapshot consumes."""
    return pl.DataFrame(
        {
            "desig": [f"d{k:04d}" for k in keys],
            "obscode": ["F51"] * len(keys),
            "mjd": [60000.0 + k for k in keys],
            "ra_deg": [10.0 + k for k in keys],
            "dec_deg": [5.0 + k for k in keys],
        }
    )


def _trk(keys: list[int]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "desig": [f"d{k:04d}" for k in keys],
            "night": [60000 + k for k in keys],
            "obscode": ["F51"] * len(keys),
            "n_obs": [2] * len(keys),
        }
    )


def _prov(stamp: str) -> dict:
    return {"last_modified": stamp, "etag": stamp, "size_bytes": 1}


def _build(root, keys, stamp):
    return snap.build_snapshot(_obs(keys), _trk(keys), _prov(stamp), root=root)


def test_baseline_says_so_rather_than_reporting_a_zero_delta(tmp_path):
    m = _build(tmp_path, [1, 2, 3], "Mon, 01 Jan 2029 00:00:00 GMT")
    assert m["delta_status"]["computed"] is False
    assert m["is_baseline"] is True
    assert "baseline" in m["delta_status"]["reason"]


def test_normal_step_records_which_ancestor_it_measured_against(tmp_path):
    a = _build(tmp_path, [1, 2, 3], "Mon, 01 Jan 2029 00:00:00 GMT")
    b = _build(tmp_path, [2, 3, 4], "Tue, 02 Jan 2029 00:00:00 GMT")
    assert b["delta_status"] == {
        "computed": True,
        "against": a["snapshot_id"],
        "skipped_pruned_ancestors": [],
    }
    assert b["delta"] == {"appeared": 1, "disappeared": 1}


def test_a_genuine_no_change_is_computed_and_zero(tmp_path):
    """The case that must stay distinguishable from an unmeasurable one."""
    _build(tmp_path, [1, 2, 3], "Mon, 01 Jan 2029 00:00:00 GMT")
    b = _build(tmp_path, [1, 2, 3], "Tue, 02 Jan 2029 00:00:00 GMT")
    assert b["delta"] == {"appeared": 0, "disappeared": 0}
    assert b["delta_status"]["computed"] is True


def test_walks_back_past_a_pruned_parent_to_the_newest_usable_ancestor(tmp_path):
    a = _build(tmp_path, [1, 2, 3], "Mon, 01 Jan 2029 00:00:00 GMT")
    b = _build(tmp_path, [2, 3, 4], "Tue, 02 Jan 2029 00:00:00 GMT")
    # b is what a CI-built snapshot looks like once it reaches another machine: the
    # permanent record survives, the key set does not.
    (tmp_path / b["snapshot_id"] / snap.OBS_FILE).unlink()

    c = _build(tmp_path, [3, 4, 5], "Wed, 03 Jan 2029 00:00:00 GMT")

    assert c["delta_status"]["computed"] is True
    assert c["delta_status"]["against"] == a["snapshot_id"]
    assert c["delta_status"]["skipped_pruned_ancestors"] == [b["snapshot_id"]]
    # Measured across the widened interval a->c, not the unmeasurable b->c.
    assert c["delta"] == {"appeared": 2, "disappeared": 2}
    # The immediate predecessor is still recorded, so the gap is visible.
    assert c["immediate_predecessor"] == b["snapshot_id"]
    assert c["parent_snapshot"] == a["snapshot_id"]


def test_no_usable_ancestor_is_reported_as_unmeasured_not_as_zero(tmp_path):
    """The exact 2026-08-06 failure: every ancestor key set gone."""
    a = _build(tmp_path, [1, 2, 3], "Mon, 01 Jan 2029 00:00:00 GMT")
    (tmp_path / a["snapshot_id"] / snap.OBS_FILE).unlink()

    b = _build(tmp_path, [9, 9, 9], "Tue, 02 Jan 2029 00:00:00 GMT")

    assert b["delta_status"]["computed"] is False
    assert b["is_baseline"] is False, "an unmeasurable step is not a baseline"
    assert b["immediate_predecessor"] == a["snapshot_id"]
    assert "could NOT be computed" in b["delta_status"]["reason"]
    # The counts are still zero -- that is unavoidable -- but the manifest now says the
    # zero is absence of measurement, which is the whole point.
    assert b["delta"] == {"appeared": 0, "disappeared": 0}


@pytest.mark.parametrize("full_keep", [1, 3])
def test_retention_always_leaves_an_ancestor_the_next_delta_can_use(tmp_path, full_keep):
    for i, day in enumerate(("01", "02", "03", "04"), start=1):
        snap.build_snapshot(
            _obs(list(range(i, i + 3))),
            _trk(list(range(i, i + 3))),
            _prov(f"Mon, {day} Jan 2029 00:00:00 GMT"),
            root=tmp_path,
            full_keep=full_keep,
        )
    kept = [s for s in snap.list_snapshots(tmp_path) if s.has_full]
    assert kept, "pruning must never remove every key set"
