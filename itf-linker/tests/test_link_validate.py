"""The ground-truth harness: what counts as recovered, and what precision really means."""

from __future__ import annotations

import polars as pl

from itf_linker.link.heliolinc import LinkCandidate
from itf_linker.link.validate import ground_truth_groups, score_links


def _arrows(rows: list[tuple]) -> pl.DataFrame:
    """rows: ``(arrow_id, desig, night, mjd)``."""
    return pl.DataFrame(
        [(r[0], r[1], r[2], r[3], "F51", 10.0, 5.0) for r in rows],
        schema={
            "arrow_id": pl.Int64, "desig": pl.String, "night": pl.Int32,
            "mjd": pl.Float64, "obscode": pl.String, "ra_deg": pl.Float64,
            "dec_deg": pl.Float64,
        },
        orient="row",
    )


def _link(ids):
    return LinkCandidate(
        arrow_ids=tuple(ids), n_nights=3, n_obscodes=1, obscodes=("F51",),
        desigs=("x",), n_obs=9, arc_days=6.0, mjd_first=60000.0, mjd_last=60006.0,
        first_trk_n_obs=3, last_trk_n_obs=3, min_trk_n_obs=3,
        r_au=2.5, rdot=0.0, pos_spread_au=1e-4, vel_spread_au_per_day=1e-5,
    )


def test_ground_truth_needs_three_distinct_nights():
    arrows = _arrows(
        [(0, "A", 1, 60001.0), (1, "A", 2, 60002.0), (2, "A", 3, 60003.0),
         (3, "B", 1, 60001.0), (4, "B", 1, 60001.1)]
    )
    truth = ground_truth_groups(arrows)
    assert set(truth) == {"A"}
    assert truth["A"] == frozenset({0, 1, 2})


def test_ground_truth_can_exclude_groups_a_window_cannot_reach():
    arrows = _arrows(
        [(0, "A", 1, 60001.0), (1, "A", 2, 60002.0), (2, "A", 3, 60003.0),
         (3, "C", 1, 60001.0), (4, "C", 2, 60002.0), (5, "C", 900, 60900.0)]
    )
    assert set(ground_truth_groups(arrows)) == {"A", "C"}
    assert set(ground_truth_groups(arrows, max_arc_days=14.0)) == {"A"}


def test_exact_recovery_partial_recovery_contamination_and_misses():
    truth = {
        "A": frozenset({0, 1, 2}),        # recovered exactly
        "B": frozenset({3, 4, 5, 6}),     # recovered in part, cleanly
        "C": frozenset({7, 8, 9}),        # only ever seen mixed with a stranger
        "D": frozenset({10, 11, 12}),     # never touched
    }
    links = [
        _link([0, 1, 2]),
        _link([3, 4, 5]),
        _link([7, 8, 99]),
        _link([100, 101, 102]),
    ]
    out = score_links(links, truth)
    assert out["recovered_exact"] == 1
    assert out["recovered_pure_partial"] == 1
    assert out["contaminated_only"] == 1
    assert out["missed_entirely"] == 1
    assert out["recall_exact"] == 0.25
    assert out["recall_pure"] == 0.5
    assert out["links_pure_single_trksub"] == 2
    assert out["links_mixing_a_truth_group_with_others"] == 1
    assert out["links_touching_no_truth_group"] == 1
    assert out["precision_lower_bound"] == 0.5


def test_a_link_joining_two_truth_groups_counts_as_mixed_not_pure():
    """Joining two trkSubs may be a real discovery -- which is why precision is a bound."""
    truth = {"A": frozenset({0, 1, 2}), "B": frozenset({3, 4, 5})}
    out = score_links([_link([0, 1, 3])], truth)
    assert out["links_pure_single_trksub"] == 0
    assert out["links_mixing_a_truth_group_with_others"] == 1
    assert out["recovered_exact"] == 0
    assert out["contaminated_only"] == 2


def test_empty_output_scores_zero_recall_without_dividing_by_zero():
    out = score_links([], {"A": frozenset({0, 1, 2})})
    assert out["recall_exact"] == 0.0
    assert out["links_total"] == 0
    assert out["precision_lower_bound"] == 0.0
