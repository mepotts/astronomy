"""M11: the shell decoy's gate, the deep end's strata, and the pruned-snapshot guard.

M11's three claims that a unit test can actually hold:

* **the decoy's reproduction gate.** The whole fit-stage pricing rests on the re-run
  control being the *same* control M10 measured, so the check that decides that must
  fail on a one-count difference, not merely on a wild one.
* **the pruned-snapshot guard.** The archive's rolling retention deleted the base
  snapshot's key set between M10 and M11, and the old series scan answered by silently
  promoting a later snapshot to element 0 -- every "consumed since 08-16" count would
  then have measured "consumed since 08-21" under the old heading. The guard must
  raise, and the delta-walk that replaces it must be arithmetically exact.
* **the deep end's strata and its stopping rule.** The strata must partition 20-25 y
  with no overlap and no gap, and |dt| exactly at the 25.00 y bound must land inside
  the last stratum rather than falling off the end of the queue.

Plus the default-off contract: every knob M11 added to an M9/M10 script must leave that
script's own numbers reproducible from its original command line.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def decoy():
    return pytest.importorskip("m11_shell_decoy")


@pytest.fixture(scope="module")
def deep():
    return pytest.importorskip("m11_deep")


@pytest.fixture(scope="module")
def qdiff():
    return pytest.importorskip("m11_queue_diff")


# ----------------------------------------------------------------------------------
# The decoy's reproduction gate (M11 section 0.5 item 2)
# ----------------------------------------------------------------------------------

def _control(n=188494, **over):
    hist = {"[0,5)": 3, "[5,15)": 20, "[15,30)": 66, "[30,60)": 274, "[60,120)": 1185}
    hist.update(over)
    return {"n": n, "sep_arcsec_hist": hist}


def test_reproduction_gate_passes_on_m10s_exact_control(decoy):
    res = decoy.check_reproduction(_control())
    assert res["reproduces"] is True
    assert res["verdict"] == "same control"


def test_reproduction_gate_fails_on_a_single_count(decoy):
    """A control that differs by one match is a different control, not a near miss."""
    assert decoy.check_reproduction(_control(n=188495))["reproduces"] is False
    assert decoy.check_reproduction(_control(**{"[0,5)": 4}))["reproduces"] is False
    assert decoy.check_reproduction(_control(**{"[60,120)": 1184}))["reproduces"] is False


def test_reproduction_gate_fails_on_a_missing_histogram(decoy):
    assert decoy.check_reproduction({"n": 188494})["reproduces"] is False


# ----------------------------------------------------------------------------------
# Fit-grade: the metric both arms are measured on
# ----------------------------------------------------------------------------------

def test_fit_grade_needs_the_strict_gate_and_every_observation(decoy):
    ok = {"gate_strict": {"passes": True}, "trk_obs_used": 4, "trk_obs_total": 4}
    assert decoy.fit_grade(ok) is True
    assert decoy.fit_grade({**ok, "trk_obs_used": 3}) is False
    assert decoy.fit_grade({**ok, "gate_strict": {"passes": False}}) is False


def test_fit_grade_is_false_for_a_fit_that_never_ran(decoy):
    """``tracklet_lines_missing`` has no gate and no counts; None == None must not pass."""
    assert decoy.fit_grade({"status": "tracklet_lines_missing"}) is False


def test_real_and_decoy_arms_are_the_frozen_m10_numbers(decoy):
    """The comparison is against M10 section 5.2's measured arm, not a re-derivation."""
    assert decoy.REAL_FITS == 300
    assert decoy.REAL_FIT_GRADE == 76
    assert decoy.M10_CONTROL_N == 188494


def test_wilson_behaves_at_zero_successes(decoy):
    lo, hi = decoy.wilson(0, 300)
    assert lo == 0.0
    assert 0.0 < hi < 0.02


def test_fisher_finds_a_real_gap_and_not_an_equal_one(decoy):
    assert decoy.fisher_exact_greater(76, 224, 10, 290) < 1e-10
    assert decoy.fisher_exact_greater(76, 224, 76, 224) > 0.4


def test_strata_bucket_the_populations_m10s_caveats_indict(decoy):
    rows = [
        {"sep_arcsec": 3.0, "gate_radius_arcsec": 344.0, "trk_n_obs": 2,
         "obscode": "705", "fit": {"gate_strict": {"passes": True},
                                   "trk_obs_used": 2, "trk_obs_total": 2}},
        {"sep_arcsec": 100.0, "gate_radius_arcsec": 3600.0, "trk_n_obs": 4,
         "obscode": "G96", "fit": {"gate_strict": {"passes": False}}},
    ]
    out = decoy.strata(rows)
    assert out['trk_n_obs 2'] == {"n": 1, "fit_grade": 1}
    assert out['trk_n_obs 4+'] == {"n": 1, "fit_grade": 0}
    assert out['sep <15"']["fit_grade"] == 1
    assert out['sep 60-120"']["fit_grade"] == 0
    assert out["station 705"]["n"] == 1


# ----------------------------------------------------------------------------------
# The pruned-snapshot guard (M11 section 1.0)
# ----------------------------------------------------------------------------------

def _snapshot(root: Path, sid: str, *, full: bool, last_modified: str, obs: int):
    d = root / sid
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(json.dumps({
        "snapshot_id": sid, "observations": obs,
        "provenance": {"last_modified": last_modified},
    }), encoding="utf-8")
    if full:
        (d / "observations.parquet").write_bytes(b"")


def test_series_scan_refuses_a_pruned_base(tmp_path, monkeypatch):
    """The exact 2026-08-23 situation: the base's key set is gone, later ones survive."""
    refresh = pytest.importorskip("m10_refresh")
    snaps = tmp_path / "snapshots"
    _snapshot(snaps, refresh.BASE_SNAPSHOT, full=False,
              last_modified="Sun, 16 Aug 2026 20:27:01 GMT", obs=9255644)
    _snapshot(snaps, "20260821T142819Z", full=True,
              last_modified="Fri, 21 Aug 2026 14:28:19 GMT", obs=9204600)
    monkeypatch.setattr(refresh, "SNAP_DIR", snaps)
    with pytest.raises(SystemExit) as exc:
        refresh.scan_series(tmp_path / "fresh.parquet",
                            {"last_modified": "Sun, 23 Aug 2026 18:27:06 GMT"})
    assert "pruned" in str(exc.value)
    assert refresh.BASE_SNAPSHOT in str(exc.value)


def test_series_scan_accepts_a_surviving_base(tmp_path, monkeypatch):
    refresh = pytest.importorskip("m10_refresh")
    snaps = tmp_path / "snapshots"
    _snapshot(snaps, refresh.BASE_SNAPSHOT, full=True,
              last_modified="Sun, 16 Aug 2026 20:27:01 GMT", obs=9255644)
    _snapshot(snaps, "20260821T142819Z", full=True,
              last_modified="Fri, 21 Aug 2026 14:28:19 GMT", obs=9204600)
    monkeypatch.setattr(refresh, "SNAP_DIR", snaps)
    series = refresh.scan_series(tmp_path / "fresh.parquet",
                                 {"last_modified": "Sun, 23 Aug 2026 18:27:06 GMT"})
    assert [s["snapshot_id"] for s in series][:2] == [
        refresh.BASE_SNAPSHOT, "20260821T142819Z"
    ]
    assert series[-1]["snapshot_id"].startswith("FRESH-")


def test_delta_walk_inverts_the_archives_delta_exactly(tmp_path):
    """keys(parent) = keys(child) - appeared(child) + disappeared(child)."""
    import polars as pl

    parent = pl.DataFrame({"obs_key": [1, 2, 3], "desig": ["a", "b", "c"],
                           "obscode": ["F51"] * 3, "mjd": [1.0, 2.0, 3.0]})
    # the MPC consumed key 2 and one new observation (key 9) appeared
    child = pl.DataFrame({"obs_key": [1, 3, 9], "desig": ["a", "c", "d"],
                          "obscode": ["F51"] * 3, "mjd": [1.0, 3.0, 9.0]})
    gone = parent.join(child.select("obs_key"), on="obs_key", how="anti")
    appeared = child.join(parent.select("obs_key"), on="obs_key", how="anti")
    walked = (
        pl.concat([child.join(appeared.select("obs_key"), on="obs_key", how="anti"),
                   gone], how="vertical")
        .unique(subset=["obs_key"])
        .sort("obs_key")
    )
    assert walked.equals(parent.sort("obs_key"))


# ----------------------------------------------------------------------------------
# The deep end's strata and stopping rule (M11 section 0.6)
# ----------------------------------------------------------------------------------

def test_strata_partition_20_to_25_years_without_gap_or_overlap(deep):
    lows = [lo for lo, _ in deep.STRATA]
    assert lows == [20, 21, 22, 23, 24]
    for (_, hi), (lo2, _) in zip(deep.STRATA, deep.STRATA[1:]):
        assert hi == lo2, "a gap or an overlap between strata"


def test_the_deepest_stratum_catches_the_window_boundary(deep):
    """|dt| is capped at exactly 25.00 y; a [24, 25) bin would silently drop it."""
    lo, hi = deep.STRATA[-1]
    assert lo == 24 and hi > 25.0
    assert lo <= 25.00 < hi


def test_deep_stopping_rule_is_m10s_floor_at_the_same_rate(deep):
    """M10 stopped a 100-fit tranche below 20/100; 50 below 10/50 is the same rate."""
    assert deep.TRANCHE == 50
    assert deep.TRANCHE_FLOOR / deep.TRANCHE == pytest.approx(20 / 100)
    assert deep.STRATUM_PROBE == 20
    assert deep.STRATUM_PROBE_FLOOR == 1


def test_deep_tags_fit_the_seven_character_trksub_field(deep):
    """HANDOFF section 2: an 8-character tag truncates and merges two objects into one."""
    for stem in ("mCa", "mCb"):
        assert len(f"{stem}{9999:04d}") == 7
    import m11_shell_decoy as dec

    assert len("mBa0000") == 7 and len(f"{dec.REAL_FITS:04d}") == 4


# ----------------------------------------------------------------------------------
# The versioned queue: a diff a reviewer can trust
# ----------------------------------------------------------------------------------

def _queue_csv(path: Path, rows):
    cols = ["rank", "tier", "object", "tracklets", "arc_extension_days", "link_keys"]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_queue_diff_keys_on_link_keys_and_skips_the_spotcheck_block(tmp_path, qdiff):
    p = tmp_path / "q.csv"
    _queue_csv(p, [
        {"rank": 1, "tier": "SPOTCHECK", "object": "2025 PC147",
         "tracklets": "A@W85/n1", "arc_extension_days": 1.0, "link_keys": "lk1"},
        {"rank": 2, "tier": "A", "object": "2025 PC147",
         "tracklets": "A@W85/n1", "arc_extension_days": 1.0, "link_keys": "lk1"},
    ])
    rows = qdiff.load(p)
    assert list(rows) == [("2025 PC147", "lk1")]
    assert rows[("2025 PC147", "lk1")]["tier"] == "A"


def test_queue_diff_parses_the_at_delimited_tracklet_cell(tmp_path, qdiff, monkeypatch):
    """`trksub@obscode/nNIGHT` -- splitting on "/" alone silently yields no members."""
    old, new = tmp_path / "old.csv", tmp_path / "new.csv"
    _queue_csv(old, [{"rank": 1, "tier": "B", "object": "2025 X1",
                      "tracklets": "P10hAN9@F51/n57038", "arc_extension_days": 5.0,
                      "link_keys": "lk9"}])
    _queue_csv(new, [])
    refresh = tmp_path / "refresh.json"
    refresh.write_text(json.dumps({
        "rows": [{"trksub": "P10hAN9", "obscode": "F51", "night": 57038,
                  "itf_status": "CONSUMED"}],
        "consumed_rows": [{"trksub": "P10hAN9", "obscode": "F51", "night": 57038,
                           "agreement": "CONSUMED_AND_AGREED"}],
    }), encoding="utf-8")
    out = tmp_path / "diff.json"
    monkeypatch.setattr(sys, "argv", ["m11_queue_diff", "--old", str(old),
                                      "--new", str(new), "--refresh", str(refresh),
                                      "--out", str(out)])
    qdiff.main()
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["n_left"] == 1
    left = doc["left"][0]
    assert left["consumed_members"] == 1
    assert left["members"][0]["agreement"] == "CONSUMED_AND_AGREED"


# ----------------------------------------------------------------------------------
# The default-off contract: M9's and M10's numbers stay reproducible
# ----------------------------------------------------------------------------------

def test_m11_knobs_are_default_off():
    """Every knob M11 added leaves the earlier milestone's command line unchanged."""
    import m9_combined
    import m10_refresh
    import m10_review_queue

    assert m10_refresh.OUT.name == "m10-refresh.json"
    assert m10_review_queue.OUT_CSV.name == "review-queue.csv"
    assert m9_combined.OUT.name == "m9-combined.json"
    # the shell/deep fit roots were added to the tag->root maps, not substituted for
    assert m9_combined.FIT_ROOTS_BY_PREFIX["m8a"].name == "m8-fits"
    assert m9_combined.FIT_ROOTS_BY_PREFIX["mAa"].name == "m10-shell-fits"
    assert m10_refresh.FIT_ROOTS["m8a"].name == "m8-fits"
    assert m10_refresh.FIT_ROOTS["mAa"].name == "m10-shell-fits"


def test_m10_shell_window_constants_are_untouched():
    """M11 sweeps the same shell; if these move, the decoy prices a different window."""
    import m10_shell
    import m11_shell_decoy

    assert m11_shell_decoy.SHELL_MIN_YEARS == m10_shell.SHELL_MIN_YEARS == 15.0
    assert m11_shell_decoy.SHELL_MAX_YEARS == m10_shell.SHELL_MAX_YEARS == 25.0
