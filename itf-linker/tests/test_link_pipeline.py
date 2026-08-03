"""Windowing, merging and ranking -- plus the end-to-end path on the real snapshot."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from itf_linker.link.arrows import build_arrows
from itf_linker.link.heliolinc import HypothesisGrid, LinkCandidate
from itf_linker.link.pipeline import (
    link_arrows,
    merge_links,
    rank_links,
    yield_summary,
)

SITES = {"F51": (203.74409, 0.936241, 0.351543), "G96": (249.21128, 0.845107, 0.533611)}


def _cand(ids, spread=1e-4, found=1, window=0):
    return LinkCandidate(
        arrow_ids=tuple(ids), n_nights=3, n_obscodes=1, obscodes=("F51",),
        desigs=("a",), n_obs=9, arc_days=6.0, mjd_first=60000.0, mjd_last=60006.0,
        first_trk_n_obs=3, last_trk_n_obs=3, min_trk_n_obs=3,
        r_au=2.5, rdot=0.0, pos_spread_au=spread, vel_spread_au_per_day=1e-5,
        n_hypotheses_found=found, window=window,
    )


def test_the_same_link_found_in_two_windows_is_counted_once():
    merged = merge_links([_cand([1, 2, 3], spread=1e-3, window=0),
                          _cand([1, 2, 3], spread=1e-4, window=1)])
    assert len(merged) == 1
    assert merged[0].pos_spread_au == 1e-4          # the tighter proposal is kept
    assert merged[0].n_hypotheses_found == 2        # but both sightings are counted


def test_merging_still_drops_subsets():
    merged = merge_links([_cand([1, 2, 3]), _cand([1, 2, 3, 4])])
    assert len(merged) == 1
    assert len(merged[0].arrow_ids) == 4


def test_ranking_is_stable_and_puts_more_nights_before_tighter_spread():
    a = _cand([1, 2, 3], spread=1e-9)
    b = _cand([4, 5, 6], spread=1e-3)
    b.n_nights = 5
    assert rank_links([a, b])[0] is b


def test_empty_arrow_set_produces_nothing_rather_than_failing():
    empty = build_arrows(
        pl.DataFrame(
            schema={
                "desig": pl.String, "obscode": pl.String, "mjd": pl.Float64,
                "ra_deg": pl.Float64, "dec_deg": pl.Float64, "mag": pl.Float64,
                "note2": pl.String, "night": pl.Int32,
            }
        ),
        SITES,
    )
    links, report = link_arrows(empty)
    assert links == []
    assert report["arrows"] == 0


def test_yield_summary_of_nothing_is_zero_not_an_error():
    out = yield_summary([])
    assert out["total"] == 0
    assert out["cross_observatory"] == 0


# --- end to end, on the real snapshot ---------------------------------------------

@pytest.mark.slow
def test_linker_rediscovers_trksub_groupings_on_a_real_slice(itf_snapshot):
    """A miniature of the M3 validation: hide the linkage, see if it comes back.

    Restricted to one two-week slice of the ITF so it runs in seconds, and scored the same
    way the full run is: a designation is recovered when some produced link is exactly its
    set of tracklets.
    """
    from itf_linker.fit.candidates import bad_data_filter
    from itf_linker.index.tracklets import add_night
    from itf_linker.ingest.fetch import fetch_obscodes, fetch_obscodes_full
    from itf_linker.link.validate import ground_truth_groups, score_links

    filtered, _ = bad_data_filter(itf_snapshot.lazy())
    try:
        lon = fetch_obscodes()
        full = fetch_obscodes_full()
    except Exception:  # noqa: BLE001 - no network and no cache: nothing to test against
        pytest.skip("observatory table unavailable")

    nighted = add_night(filtered, lon).collect()
    # A two-week slice chosen because it carries ~16 trkSub groupings to score against;
    # most fortnights of the ITF carry none, which is exactly why the file exists.
    arrows = build_arrows(nighted, full, mjd_min=60900.0, mjd_max=60914.0)
    truth = ground_truth_groups(arrows.table, min_nights=3, max_arc_days=14.0)
    if len(truth) < 5:
        pytest.skip("this snapshot slice holds too little ground truth to score")

    links, _ = link_arrows(
        arrows, grid=HypothesisGrid.build(), window_days=14.0, window_step_days=14.0
    )
    score = score_links(links, truth)
    assert score["recall_touched"] >= 0.5, score
    assert score["recovered_exact"] >= 1, score


@pytest.mark.slow
def test_geometry_reproduces_find_orbs_own_solutions(itf_snapshot):
    """Cross-check the linker's geometry against M1's differential-correction fits.

    Nothing about this path is shared with Find_Orb: the observer, the distance solve, the
    velocity solve, the propagation and the element conversion are all this repo's numpy.
    Scanning ``(r, rdot)`` for the hypothesis that makes a designation's own tracklets agree
    best and converting the result to elements must land near a DE-440 least-squares
    solution, or the proposals the linker makes are not about the sky.
    """
    import json

    from itf_linker.fit.candidates import bad_data_filter
    from itf_linker.index.tracklets import add_night
    from itf_linker.ingest.fetch import fetch_obscodes, fetch_obscodes_full
    from itf_linker.link.arrows import arrow_arrays
    from itf_linker.link.geometry import (
        C_AU_PER_DAY,
        propagate_kepler,
        state_from_hypothesis,
        state_to_elements,
    )

    try:
        with open("m1-report.json", encoding="utf-8") as fh:
            ranked = json.load(fh)["fits"]["ranked"][:6]
    except (OSError, KeyError):
        pytest.skip("no m1-report.json to cross-check against")
    try:
        lon, full = fetch_obscodes(), fetch_obscodes_full()
    except Exception:  # noqa: BLE001
        pytest.skip("observatory table unavailable")

    filtered, _ = bad_data_filter(itf_snapshot.lazy())
    nighted = add_night(filtered, lon).collect()
    wanted = {r["desig"] for r in ranked}
    arrows = build_arrows(nighted.filter(pl.col("desig").is_in(wanted)), full)

    errors: list[float] = []
    for row in ranked:
        table = arrows.table.filter(pl.col("desig") == row["desig"]).sort("mjd")
        if table.height < 3:
            continue
        a = arrow_arrays(table)
        t_ref = float(np.mean(a["mjd"]))
        best = None
        for r_hyp, rdot in HypothesisGrid.build(r_step=0.02):
            rv, vv, rho, valid = state_from_hypothesis(
                a["obs_pos"], a["obs_vel"], a["rho_hat"], a["rho_hat_dot"],
                np.full(table.height, r_hyp), np.full(table.height, rdot),
            )
            if not valid.all():
                continue
            p, _, ok = propagate_kepler(rv, vv, t_ref - (a["mjd"] - rho / C_AU_PER_DAY))
            if not ok.all():
                continue
            spread = float(np.linalg.norm(p - p.mean(axis=0), axis=1).max())
            if best is None or spread < best[0]:
                best = (spread, rv, vv)
        assert best is not None, row["desig"]
        el = state_to_elements(best[1], best[2])
        rel = abs(float(np.mean(el["a"])) - row["a"]) / row["a"]
        # An assumed-distance proposal is not a least-squares fit, so the bar is "the same
        # regime", not "the same number". The tight bound is on the *median*: a systematic
        # error in the observer or the propagation would move every designation, not one.
        assert rel < 0.15, (row["desig"], rel)
        errors.append(rel)
    assert len(errors) >= 3, "too few M1 designations were still present to cross-check"
    assert float(np.median(errors)) < 0.05, errors


@pytest.mark.slow
def test_observer_positions_are_consistent_across_sites_on_a_real_night(itf_snapshot):
    """Two observatories on one night must sit within an Earth diameter of each other."""
    from itf_linker.ingest.fetch import fetch_obscodes_full
    from itf_linker.link.geometry import R_EARTH_AU, observer_heliocentric

    try:
        full = fetch_obscodes_full()
    except Exception:  # noqa: BLE001
        pytest.skip("observatory table unavailable")
    codes = ["F51", "G96", "W84", "F52"]
    mjd = np.full(len(codes), 61100.3)
    lon = np.array([full[c][0] for c in codes])
    rc = np.array([full[c][1] for c in codes])
    rs = np.array([full[c][2] for c in codes])
    pos, _ = observer_heliocentric(mjd, lon, rc, rs)
    spread = np.linalg.norm(pos - pos.mean(axis=0), axis=1).max()
    assert spread < 2 * R_EARTH_AU


def test_survivors_are_presented_cross_observatory_first():
    """Conflicts resolve on fit quality; the surviving list is *ordered* by strategy."""
    from itf_linker.fit.findorb import FitResult
    from itf_linker.fit.pipeline import FitOutcome
    from itf_linker.link.run import rank_survivors

    def outcome(desig, codes, rms):
        fit = FitResult(desig=desig, converged=True, status="converged", rms_residual=rms)
        return FitOutcome(desig=desig, fit=fit, n_nights=3, n_obs_submitted=9,
                          prefit_arc_days=6.0, obscodes=codes, gate_passes=True,
                          gate_reasons=[])

    meta = {
        "same": {"source_desigs": ["a", "b"]},
        "cross": {"source_desigs": ["c", "d"]},
        "rederived": {"source_desigs": ["e"]},
    }
    ordered = rank_survivors(
        [
            outcome("same", ["F51"], 0.01),          # best fit, but one observatory
            outcome("rederived", ["F51", "G96"], 0.20),
            outcome("cross", ["F51", "G96"], 0.15),
        ],
        meta,
    )
    assert [o.desig for o in ordered] == ["cross", "rederived", "same"]
