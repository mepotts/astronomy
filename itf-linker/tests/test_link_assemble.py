"""Gating a link, and turning it into astrometry Find_Orb will treat as one object."""

from __future__ import annotations

import gzip

import polars as pl
import pytest

from itf_linker.link.assemble import (
    MIN_OBS_PER_NIGHT,
    _relabel,
    gate_links,
    link_astrometry,
    link_id,
    link_key,
    links_frame,
    tracklet_line_index,
)
from itf_linker.link.heliolinc import LinkCandidate
from itf_linker.link.run import resolve_conflicts

LINE = "     RL00adt  C2025 09 14.35678 01 02 03.45 +04 05 06.7          21.5 rV     X05"


def _link(
    ids=(0, 1, 2), nights=3, codes=("F51",), arc=6.0, first=3, last=3, low=3,
    desigs=("a", "b", "c"),
):
    return LinkCandidate(
        arrow_ids=tuple(ids), n_nights=nights, n_obscodes=len(set(codes)),
        obscodes=tuple(sorted(set(codes))), desigs=tuple(desigs),
        n_obs=first + last + low, arc_days=arc,
        mjd_first=60000.0, mjd_last=60000.0 + arc,
        first_trk_n_obs=first, last_trk_n_obs=last, min_trk_n_obs=low,
        r_au=2.5, rdot=0.0, pos_spread_au=1e-4, vel_spread_au_per_day=1e-5,
    )


# --- identifiers -------------------------------------------------------------------

def test_link_ids_are_seven_characters_and_unique():
    ids = [link_id(i) for i in (0, 1, 35, 36, 1000, 36**4 - 1)]
    assert all(len(x) == 7 for x in ids)
    assert len(set(ids)) == len(ids)
    assert ids[0] == "lnk0000"
    assert ids[2] == "lnk000z"
    assert ids[3] == "lnk0010"


def test_link_id_refuses_to_overflow_silently():
    with pytest.raises(ValueError):
        link_id(36**4)


# --- link_key: the one that survives a re-run --------------------------------------

def _arrows(rows):
    """(arrow_id, desig, obscode, night) -- the four columns link_key is built from."""
    return pl.DataFrame(
        rows, schema={"arrow_id": pl.Int64, "desig": pl.String,
                      "obscode": pl.String, "night": pl.Int32},
        orient="row",
    )


TRK = [(0, "A", "F51", 60000), (1, "B", "G96", 60004), (2, "C", "W84", 60008)]


def test_link_key_does_not_depend_on_member_order():
    a = link_key([("A", "F51", 60000), ("B", "G96", 60004)])
    b = link_key([("B", "G96", 60004), ("A", "F51", 60000)])
    assert a == b


def test_link_key_does_not_depend_on_arrow_numbering():
    """The whole point: arrow ids are positional, tracklets are not.

    The same three tracklets renumbered must produce the same key, or the id is no more
    stable than the counter it replaces.
    """
    one = links_frame([_link(ids=(0, 1, 2))], _arrows(TRK))
    renumbered = _arrows([(70, "A", "F51", 60000), (71, "B", "G96", 60004),
                          (72, "C", "W84", 60008)])
    two = links_frame([_link(ids=(70, 71, 72))], renumbered)
    assert one["desig"][0] == two["desig"][0] == "lnk0000"      # the counter says nothing
    assert one["link_key"][0] == two["link_key"][0]             # the key says everything


def test_link_key_separates_links_that_every_summary_field_agrees_on():
    """`lnk0018` and `lnk001e` in link-candidates.parquet differ in one arrow of six.

    Same trkSubs, same observatory codes, same MJD bounds, same observation and tracklet
    counts. Any key built from summary columns merges them; 197 such pairs exist in that
    one table.
    """
    arrows = _arrows(TRK + [(3, "C", "W84", 60009)])
    a = links_frame([_link(ids=(0, 1, 2))], arrows)["link_key"][0]
    b = links_frame([_link(ids=(0, 1, 3))], arrows)["link_key"][0]
    assert a != b


def test_link_key_is_null_without_arrows_rather_than_wrong():
    frame = links_frame([_link(ids=(0, 1, 2))])
    assert "link_key" in frame.columns
    assert frame["link_key"][0] is None


def test_a_link_whose_members_are_not_all_resolvable_gets_no_key():
    """A key from a partial member set is another link's key, which is worse than none."""
    partial = _arrows(TRK[:2])
    assert links_frame([_link(ids=(0, 1, 2))], partial)["link_key"][0] is None


def test_gate_links_carries_the_key_through():
    gated, _ = gate_links([_link(ids=(0, 1, 2))], _arrows(TRK))
    assert gated["link_key"][0] == link_key([t[1:] for t in TRK])


def test_relabel_replaces_only_columns_1_to_12():
    out = _relabel(LINE, "lnk0007")
    assert out[:5] == "     "
    assert out[5:12] == "lnk0007"
    assert out[12:] == LINE[12:]
    assert len(out) == 80


# --- the gate ----------------------------------------------------------------------

def test_gate_applies_the_published_pre_fit_criteria():
    links = [
        _link(ids=(0, 1, 2), nights=3, arc=6.0),                       # passes
        _link(ids=(3, 4, 5), nights=3, arc=2.0),                       # arc < 3 d
        _link(ids=(6, 7, 8), nights=3, arc=40.0),                      # 3 nights, arc > 15 d
        _link(ids=(9, 10, 11), nights=3, arc=6.0, first=1, last=1),    # singleton-ended
        _link(ids=(12, 13, 14), nights=3, arc=6.0, low=1),             # a one-detection night
    ]
    gated, summary = gate_links(links)
    assert gated["link_pass"].to_list() == [True, False, False, False, False]
    assert summary["reject_reasons"]["arc_lt_3_days"] == 1
    assert summary["reject_reasons"]["exactly_3_nights_arc_gt_15_days"] == 1
    assert summary["reject_reasons"]["singleton_tracklet_at_both_ends"] == 1
    assert summary["reject_reasons"]["fewer_than_2_obs_on_some_night"] == 1
    assert summary["link_pass"] == 1


def test_four_nights_may_exceed_fifteen_days():
    """The 15-day rule is scoped to *exactly* three nights, as published."""
    gated, _ = gate_links([_link(nights=4, arc=40.0)])
    assert gated["link_pass"][0]


def test_min_obs_per_night_threshold_is_the_mpc_rule():
    assert MIN_OBS_PER_NIGHT == 2


def test_gate_reports_cross_and_same_observatory_separately():
    links = [
        _link(ids=(0, 1, 2), codes=("F51", "G96")),
        _link(ids=(3, 4, 5), codes=("F51",)),
    ]
    _, summary = gate_links(links)
    assert summary["link_pass_cross_observatory"] == 1
    assert summary["link_pass_same_observatory"] == 1


def test_empty_input_does_not_explode():
    frame = links_frame([])
    assert frame.height == 0
    gated, summary = gate_links([])
    assert gated.height == 0
    assert summary["prefit_pass"] == 0


# --- astrometry assembly -----------------------------------------------------------

@pytest.fixture()
def tiny_itf(tmp_path):
    """A two-object, three-night gzipped ITF fragment in real 80-column format."""
    rows = []
    for desig, code, days in (("aaa0001", "F51", (14, 18, 22)), ("bbb0002", "G96", (15,))):
        for day in days:
            for k in range(2):
                rows.append(
                    f"     {desig}  C2025 09 {day + 0.30 + k * 0.01:08.5f} "
                    f"01 02 03.45 +04 05 06.7          21.5 rV     {code}"
                )
    path = tmp_path / "itf.txt.gz"
    with gzip.open(path, "wt", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(r.ljust(80) for r in rows) + "\n")
    return path


def test_line_index_keys_on_trksub_observatory_and_night(tiny_itf):
    index, stats = tracklet_line_index(
        ["aaa0001", "bbb0002"], {"F51": 203.7, "G96": 249.2}, src=tiny_itf
    )
    assert stats["tracklets_indexed"] == 4
    assert all(len(v) == 2 for v in index.values())
    assert {k[0] for k in index} == {"aaa0001", "bbb0002"}


def test_link_astrometry_relabels_every_line_to_one_identifier(tiny_itf):
    lon = {"F51": 203.7, "G96": 249.2}
    index, _ = tracklet_line_index(["aaa0001", "bbb0002"], lon, src=tiny_itf)
    keys = sorted(k for k in index if k[0] == "aaa0001")
    arrows = pl.DataFrame(
        {
            "arrow_id": list(range(len(keys))),
            "desig": [k[0] for k in keys],
            "obscode": [k[1] for k in keys],
            "night": [k[2] for k in keys],
        }
    )
    gated = pl.DataFrame({"desig": ["lnk0000"], "arrow_ids": [list(range(len(keys)))]})
    groups, stats = link_astrometry(gated, arrows, lon, src=tiny_itf)
    assert stats["links_with_astrometry"] == 1
    lines = groups["lnk0000"]
    assert len(lines) == 6
    assert {ln[5:12] for ln in lines} == {"lnk0000"}
    assert {ln[77:80] for ln in lines} == {"F51"}


def test_a_link_whose_astrometry_is_missing_is_counted_not_dropped_silently(tiny_itf):
    lon = {"F51": 203.7}
    arrows = pl.DataFrame(
        {"arrow_id": [0], "desig": ["missing"], "obscode": ["F51"], "night": [60932]}
    )
    gated = pl.DataFrame({"desig": ["lnk0000"], "arrow_ids": [[0]]})
    groups, stats = link_astrometry(gated, arrows, lon, src=tiny_itf)
    assert groups == {}
    assert stats["links_without_astrometry"] == 1


# --- conflict resolution -----------------------------------------------------------

def _outcome(desig, rms, arc=6.0):
    from itf_linker.fit.findorb import FitResult
    from itf_linker.fit.pipeline import FitOutcome

    fit = FitResult(desig=desig, converged=True, status="converged", rms_residual=rms,
                    first_jd=0.0, last_jd=arc)
    return FitOutcome(desig=desig, fit=fit, n_nights=3, n_obs_submitted=9,
                      prefit_arc_days=arc, obscodes=["F51"], gate_passes=True,
                      gate_reasons=[])


def test_conflicting_links_are_resolved_in_favour_of_the_better_fit():
    """A tracklet belongs to one object; two links sharing one cannot both be right."""
    a = _outcome("lnk0000", 0.05)
    b = _outcome("lnk0001", 0.20)
    c = _outcome("lnk0002", 0.10)
    kept, dropped = resolve_conflicts(
        [a, b, c],
        {"lnk0000": [1, 2, 3], "lnk0001": [3, 4, 5], "lnk0002": [6, 7, 8]},
    )
    assert [o.desig for o in kept] == ["lnk0000", "lnk0002"]
    assert [o.desig for o in dropped] == ["lnk0001"]
