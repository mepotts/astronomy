"""M12: the series walk's arithmetic and the cross-walk's two ordering traps.

M12's claims rest on two pieces of machinery, and both of them failed silently the first
time they ran. These are the tests that would have caught them:

* **the delta walk transports distinct keys, not rows.** ``obs_key`` is a content hash and
  the ITF ships ~1,130 exactly duplicated records, so a walk reproduces
  ``distinct_obs_keys`` and can never reproduce ``observations``. The first verification
  compared a walk against a file's row count and failed by exactly the duplicate count on
  all four checks -- an off-by-a-constant that looks like a broken walk and is not one.
* **the prefilter must hand its survivors on sorted.** The refine stage keeps only the
  first ``REFINE_KEEP`` candidates. When the prefilter returned them in catalogue order,
  every tracklet with more survivors than the cap was refined against an arbitrary subset;
  the pilot confirmed 1 of 10 and the one that worked was the only one under the cap.
* **light time is part of the integration span, not padding on it.** A 3-degree prefilter
  over 1.56M orbits admits distant objects, and ``predict_dense`` asks the trajectory for
  ``t - tau``. The first full run died 2,389 AU and twenty minutes in, having written
  nothing -- which is why a checkpoint has to be marked ``partial`` and a refine failure
  has to cost one tracklet rather than the sample.

Plus the re-designation confound the whole M12 story depends on: ``obs_key`` folds
``desig``, so a relabelled observation leaves under one key and arrives under another. If
that were common, "the file is draining" would be "the file is churning" and every number
in M12 section 1 would mean something else.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def series():
    return pytest.importorskip("m12_series")


@pytest.fixture(scope="module")
def crosswalk():
    return pytest.importorskip("m12_crosswalk")


def _delta(pl, rows):
    """rows: (obs_key, change, desig, obscode, mjd)."""
    return pl.DataFrame(
        {
            "obs_key": [r[0] for r in rows],
            "change": [r[1] for r in rows],
            "desig": [r[2] for r in rows],
            "obscode": [r[3] for r in rows],
            "mjd": [r[4] for r in rows],
        },
        schema={"obs_key": pl.UInt64, "change": pl.Int8, "desig": pl.Utf8,
                "obscode": pl.Utf8, "mjd": pl.Float64},
    )


# ----------------------------------------------------------------------------------
# The re-designation confound
# ----------------------------------------------------------------------------------

def test_a_relabelled_observation_is_counted_as_a_redesignation(series):
    """Same station, same instant, new trksub: one departure and one arrival, one object."""
    pl = pytest.importorskip("polars")
    d = _delta(pl, [
        (1, -1, "P10aaaa", "F51", 58000.5),   # leaves under the old label...
        (2, +1, "P10zzzz", "F51", 58000.5),   # ...and arrives under the new one
    ])
    assert series.redesignations(d) == 1


def test_a_genuine_departure_is_not_counted_as_a_redesignation(series):
    """Nothing arrives at that station and instant, so the observation actually left."""
    pl = pytest.importorskip("polars")
    d = _delta(pl, [
        (1, -1, "P10aaaa", "F51", 58000.5),
        (2, +1, "P10zzzz", "F51", 59000.5),   # a different night entirely
    ])
    assert series.redesignations(d) == 0


def test_redesignation_needs_both_sides(series):
    pl = pytest.importorskip("polars")
    assert series.redesignations(_delta(pl, [(1, -1, "A", "F51", 58000.5)])) == 0
    assert series.redesignations(_delta(pl, [(1, +1, "A", "F51", 58000.5)])) == 0


# ----------------------------------------------------------------------------------
# Whole vs partial departure -- the distinction the linkage reading rests on
# ----------------------------------------------------------------------------------

def test_a_designation_losing_everything_is_whole_not_partial(series):
    pl = pytest.importorskip("polars")
    parent = pl.DataFrame({
        "obs_key": pl.Series([1, 2, 3, 4], dtype=pl.UInt64),
        "desig": ["A", "A", "B", "B"],
        "obscode": ["F51"] * 4,
        "mjd": [58000.5, 58000.51, 58000.5, 58000.51],
    })
    # A loses both of its observations; B loses one of two.
    d = _delta(pl, [(1, -1, "A", "F51", 58000.5), (2, -1, "A", "F51", 58000.51),
                    (3, -1, "B", "F51", 58000.5)])
    st = series.step_stats(parent, d)
    assert st["desigs_gone_whole"] == 1
    assert st["desigs_gone_partial"] == 1
    assert st["obs_from_whole_desigs"] == 2
    assert st["obs_from_partial_desigs"] == 1
    # A designation that lost something but is missing from the parent means the walk is
    # wrong; it must be counted, never silently dropped.
    assert st["unmatched_desigs"] == 0


def test_a_departure_from_outside_the_parent_key_set_is_flagged(series):
    """The walk is wrong if a designation loses observations it never had."""
    pl = pytest.importorskip("polars")
    parent = pl.DataFrame({
        "obs_key": pl.Series([1], dtype=pl.UInt64), "desig": ["A"],
        "obscode": ["F51"], "mjd": [58000.5],
    })
    st = series.step_stats(parent, _delta(pl, [(9, -1, "GHOST", "F51", 58000.5)]))
    assert st["unmatched_desigs"] == 1


# ----------------------------------------------------------------------------------
# Distinct keys, not rows
# ----------------------------------------------------------------------------------

def test_distinct_keys_collapses_the_files_duplicate_records(series):
    """The ITF's ~1,130 duplicated records are why a walk cannot reproduce a row count."""
    pl = pytest.importorskip("polars")
    frame = pl.DataFrame({"obs_key": pl.Series([7, 7, 3], dtype=pl.UInt64)})
    out = series.distinct_keys(frame)
    assert out.height == 2
    assert out["obs_key"].to_list() == [3, 7]  # sorted, so two walks compare directly


# ----------------------------------------------------------------------------------
# Segmentation: an uncomputable delta must break the chain
# ----------------------------------------------------------------------------------

def test_an_uncomputable_delta_starts_a_new_segment(series, tmp_path, monkeypatch):
    """2026-08-13 carries parent_snapshot: null. A walk must not cross it."""
    def write(sid, **kw):
        d = tmp_path / sid
        d.mkdir()
        (d / "manifest.json").write_text(json.dumps(kw), encoding="utf-8")

    write("20260101T000000Z", is_baseline=True, delta_status={"computed": False})
    write("20260102T000000Z", is_baseline=False,
          delta_status={"computed": True, "against": "20260101T000000Z"})
    # the hole: the key set was pruned before the diff could run
    write("20260103T000000Z", is_baseline=False,
          delta_status={"computed": False, "against": None})
    write("20260104T000000Z", is_baseline=False,
          delta_status={"computed": True, "against": "20260103T000000Z"})
    monkeypatch.setattr(series, "SNAP_DIR", tmp_path)
    segs = series.segments(series.snapshot_ids())
    assert segs == [
        ["20260101T000000Z", "20260102T000000Z"],
        ["20260103T000000Z", "20260104T000000Z"],
    ]


def test_pre_delta_status_manifests_still_segment(series, tmp_path, monkeypatch):
    """Manifests written before 2026-08-06 have no delta_status at all."""
    def write(sid, **kw):
        d = tmp_path / sid
        d.mkdir()
        (d / "manifest.json").write_text(json.dumps(kw), encoding="utf-8")

    write("20260101T000000Z", is_baseline=True, parent_snapshot=None)
    write("20260102T000000Z", is_baseline=False, parent_snapshot="20260101T000000Z")
    monkeypatch.setattr(series, "SNAP_DIR", tmp_path)
    assert series.segments(series.snapshot_ids()) == [
        ["20260101T000000Z", "20260102T000000Z"]
    ]


# ----------------------------------------------------------------------------------
# The cross-walk's ordering trap
# ----------------------------------------------------------------------------------

def test_prefilter_returns_candidates_sorted_nearest_first(crosswalk):
    """The refine cap takes a prefix, so an unsorted prefilter throws away the answer.

    Three orbits are placed on one circular orbit at different mean anomalies, so their
    sky positions at a fixed epoch differ. Whatever the geometry works out to, the
    returned indices must be in increasing separation -- that is the contract the refine
    stage depends on.
    """
    np = pytest.importorskip("numpy")
    from itf_linker.attrib.bulk import elements_to_state
    from itf_linker.attrib.core import observables_from_states, separation_deg
    from itf_linker.link.geometry import TT_MINUS_UTC_DAYS, earth_heliocentric_posvel

    epoch = 61000.0
    states = [elements_to_state(2.5, 0.1, 5.0, 30.0, 40.0, m) for m in (10.0, 60.0, 200.0)]
    arr = {
        "primary": np.array(["a", "b", "c"]),
        "epoch": np.full(3, epoch),
        "r0": np.array([s[0] for s in states]),
        "v0": np.array([s[1] for s in states]),
        "h": np.full(3, 15.0),
        "g": np.full(3, 0.15),
    }
    # Aim at the first orbit's own position, so it must come back first.
    mjd = epoch - TT_MINUS_UTC_DAYS
    e_pos, e_vel = earth_heliocentric_posvel(np.array([mjd]))
    obs = observables_from_states(arr["r0"], arr["v0"],
                                  np.broadcast_to(e_pos, (3, 3)),
                                  np.broadcast_to(e_vel, (3, 3)), arr["h"], arr["g"])
    ra, dec = float(obs["ra_deg"][0]), float(obs["dec_deg"][0])

    monkey = crosswalk.PREFILTER_DEG
    try:
        crosswalk.PREFILTER_DEG = 180.0  # keep everything, so only the ORDER is tested
        idx = crosswalk.prefilter(arr, mjd, ra, dec)
    finally:
        crosswalk.PREFILTER_DEG = monkey

    assert idx.size == 3
    assert idx[0] == 0  # the orbit we aimed at
    seps = separation_deg(obs["ra_deg"][idx], obs["dec_deg"][idx],
                          np.full(3, ra), np.full(3, dec))
    assert list(seps) == sorted(seps), "prefilter must return nearest-first"


def test_prefilter_radius_actually_excludes(crosswalk):
    """The loose radius is loose, not infinite."""
    np = pytest.importorskip("numpy")
    from itf_linker.attrib.bulk import elements_to_state
    from itf_linker.attrib.core import observables_from_states
    from itf_linker.link.geometry import TT_MINUS_UTC_DAYS, earth_heliocentric_posvel

    epoch = 61000.0
    states = [elements_to_state(2.5, 0.1, 5.0, 30.0, 40.0, m) for m in (10.0, 200.0)]
    arr = {
        "primary": np.array(["a", "b"]),
        "epoch": np.full(2, epoch),
        "r0": np.array([s[0] for s in states]),
        "v0": np.array([s[1] for s in states]),
        "h": np.full(2, 15.0), "g": np.full(2, 0.15),
    }
    mjd = epoch - TT_MINUS_UTC_DAYS
    e_pos, e_vel = earth_heliocentric_posvel(np.array([mjd]))
    obs = observables_from_states(arr["r0"], arr["v0"],
                                  np.broadcast_to(e_pos, (2, 3)),
                                  np.broadcast_to(e_vel, (2, 3)), arr["h"], arr["g"])
    idx = crosswalk.prefilter(arr, mjd, float(obs["ra_deg"][0]), float(obs["dec_deg"][0]))
    assert 0 in idx
    assert 1 not in idx  # 190 degrees of mean anomaly away is not within 3 degrees


# ----------------------------------------------------------------------------------
# The confirmation rule is M9's, both halves
# ----------------------------------------------------------------------------------

# Lifted verbatim from the MPC's published record for (3517) Tatianicheva, fetched from
# get-obs while building M12's cross-walk. Hand-assembling an 80-column line gets the
# columns subtly wrong and the parser rejects it, which proves nothing about the matching
# rule -- two attempts at that preceded this constant.
OBS80_REAL = (
    "03517         C2010 09 24.53563305 28 03.561+20 22 53.40"
    "         17.50zL~0QusF51"
)


def test_confirmation_needs_both_time_and_position(crosswalk, tmp_path, monkeypatch):
    """A published row at the same instant but elsewhere on the sky is not the same
    observation -- that is the pointed-field confound M10 had to screen for."""
    pl = pytest.importorskip("polars")
    from itf_linker.mpc80 import parse_line

    line = OBS80_REAL
    rec = parse_line(line)
    assert rec is not None, "fixture line must parse, or the test proves nothing"

    cache = tmp_path / "obs80"
    cache.mkdir()
    (cache / "TARGET.obs80").write_text(line + "\n", encoding="utf-8")
    monkeypatch.setattr(crosswalk, "get_obs80",
                        lambda desig, c: [line] if desig == "TARGET" else [])

    def dep(ra, dec, dmjd=0.0):
        return pl.DataFrame({"obscode": ["F51"], "mjd": [rec.mjd + dmjd],
                             "ra_deg": [ra], "dec_deg": [dec]})

    # same instant, same place -> matched
    assert crosswalk.confirm(dep(rec.ra_deg, rec.dec_deg), "TARGET", cache)["matched"] == 1
    # same instant, 10 arcsec away -> not this observation
    assert crosswalk.confirm(dep(rec.ra_deg + 10 / 3600.0, rec.dec_deg),
                             "TARGET", cache)["matched"] == 0
    # same place, an hour later -> not this observation either
    assert crosswalk.confirm(dep(rec.ra_deg, rec.dec_deg, dmjd=1 / 24.0),
                             "TARGET", cache)["matched"] == 0
    # a different station at the same instant and place -> not this observation
    other = dep(rec.ra_deg, rec.dec_deg).with_columns(pl.lit("G96").alias("obscode"))
    assert crosswalk.confirm(other, "TARGET", cache)["matched"] == 0


def test_an_object_with_no_published_record_confirms_nothing(crosswalk, tmp_path,
                                                             monkeypatch):
    pl = pytest.importorskip("polars")
    monkeypatch.setattr(crosswalk, "get_obs80", lambda desig, c: [])
    dep = pl.DataFrame({"obscode": ["F51"], "mjd": [58000.5],
                        "ra_deg": [10.0], "dec_deg": [5.0]})
    out = crosswalk.confirm(dep, "NOTHING", tmp_path)
    assert out == {"published_rows": 0, "matched": 0, "of": 1}


# ----------------------------------------------------------------------------------
# Light time is not padding, and one bad tracklet is not a failed run
# ----------------------------------------------------------------------------------

def test_refine_survives_an_orbit_whose_light_time_exceeds_a_naive_span(crosswalk):
    """A 3-degree prefilter over 1.56M orbits will sometimes admit something far out.

    ``predict_dense`` asks the trajectory for ``t - tau``, and tau is the light time to
    the object: at 500 AU that is 2.9 days, which falls outside the 2-day margin the
    first version used. The full run died on exactly this, 2,389 AU and twenty minutes
    in. ``SPAN_MARGIN_DAYS`` is what makes it safe.
    """
    np = pytest.importorskip("numpy")
    from itf_linker.attrib.bulk import elements_to_state

    epoch = 61200.0                       # the MPCORB standard epoch
    mjd = epoch - 3650.0                  # a ten-year lookback, as the departures are
    far = elements_to_state(500.0, 0.05, 10.0, 100.0, 20.0, 45.0)   # tau ~ 2.9 d
    near = elements_to_state(2.5, 0.1, 5.0, 30.0, 40.0, 45.0)
    arr = {
        "primary": np.array(["distant", "mainbelt"]),
        "epoch": np.full(2, epoch),
        "r0": np.array([far[0], near[0]]),
        "v0": np.array([far[1], near[1]]),
        "h": np.full(2, 10.0), "g": np.full(2, 0.15),
    }
    assert crosswalk.SPAN_MARGIN_DAYS >= 30.0, "margin must cover deep light times"
    out = crosswalk.refine(arr, np.array([0, 1]), mjd, 0.0, 0.0)
    assert len(out) == 2
    assert {c["primary"] for c in out} == {"distant", "mainbelt"}
    # sorted nearest first, same contract as the prefilter
    assert out[0]["sep_arcsec"] <= out[1]["sep_arcsec"]
    # the distant one really is distant -- otherwise the test is not testing light time
    far_row = next(c for c in out if c["primary"] == "distant")
    assert far_row["delta_au"] > 100.0


def test_checkpoints_are_marked_partial(crosswalk, tmp_path):
    """A half-finished file must never be readable as a finished one."""
    import types

    args = types.SimpleNamespace(out=tmp_path / "cw.json",
                                 mpcorb=tmp_path / "nope.json.gz")
    rows = [{"desig": "A", "confirmed": True, "refine_error": None},
            {"desig": "B", "confirmed": False, "refine_error": "ValueError: boom"}]
    mid = crosswalk.write_doc(args, ["A", "B", "C"], ["A", "B", "C", "D"], rows,
                              partial=True)
    assert mid["partial"] is True
    assert mid["sample_done"] == 2 and mid["sample_requested"] == 3
    assert mid["confirmed"] == 1
    assert mid["refine_errors"] == 1
    # the fraction is over what was actually done, not over what was asked for
    assert mid["confirmed_fraction"] == pytest.approx(0.5)
    on_disk = json.loads(args.out.read_text(encoding="utf-8"))
    assert on_disk["partial"] is True

    final = crosswalk.write_doc(args, ["A", "B", "C"], ["A", "B", "C", "D"], rows,
                                partial=False)
    assert final["partial"] is False
