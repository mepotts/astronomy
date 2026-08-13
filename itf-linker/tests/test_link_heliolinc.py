"""The linker, exercised on synthetic objects whose orbits are known exactly.

A synthetic object is generated the honest way -- propagate a real Keplerian orbit,
observe it from a real observatory at real epochs, and hand the linker nothing but
directions, rates and times. If the geometry, the hypothesis grid or the clustering is
wrong, the object is not recovered; if the structural rules are wrong, unrelated objects
are merged.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from itf_linker.link.arrows import build_arrows
from itf_linker.link.geometry import (
    C_AU_PER_DAY,
    GM_SUN,
    observer_heliocentric,
    propagate_kepler,
)
from itf_linker.link.heliolinc import (
    MAX_SLOT_CANDIDATES,
    HypothesisGrid,
    _pack_cells,
    _split_colliding,
    cluster_states,
    drop_subsets,
    isolated_groups,
    link_window,
)
from itf_linker.link.pipeline import rank_links, yield_summary

# --- the spatial hash collides, and the cap is the one place that matters ------------

def test_the_cell_hash_is_not_injective():
    """Found by brute force over a 120x120 index scan. The fix below depends on it."""
    a = np.array([[-1, 59, 0]], dtype=np.int64)
    b = np.array([[1, -59, 0]], dtype=np.int64)
    assert _pack_cells(a)[0] == _pack_cells(b)[0]


def test_a_hash_collision_cannot_discard_a_cell_through_the_overflow_cap():
    """Collisions only *add* candidates to an exact test -- except where size decides.

    Two colliding cells of 3 merge into a group of 6. Against a cap of 4 the whole group
    used to be discarded, silently destroying every genuine cluster in both and inflating
    `overflowed_cells`, which is meant to be measuring real crowding.
    """
    cell_idx = np.array([[-1, 59, 0]] * 3 + [[1, -59, 0]] * 3, dtype=np.int64)
    out = list(_split_colliding([np.arange(6)], cell_idx, max_cell_members=4))
    assert [g.tolist() for g in out] == [[0, 1, 2], [3, 4, 5]]


def test_a_genuinely_crowded_cell_still_overflows():
    """The cap is doing real work; splitting must not become a way to evade it."""
    cell_idx = np.array([[7, 7, 7]] * 6, dtype=np.int64)
    out = list(_split_colliding([np.arange(6)], cell_idx, max_cell_members=4))
    assert len(out) == 1 and len(out[0]) == 6      # still over the cap, still dropped


def test_groups_under_the_cap_are_passed_through_untouched():
    """The fast path: no lexsort for the ~99.9% of groups that never collide."""
    cell_idx = np.array([[-1, 59, 0]] * 2 + [[1, -59, 0]] * 2, dtype=np.int64)
    out = list(_split_colliding([np.arange(4)], cell_idx, max_cell_members=400))
    assert [g.tolist() for g in out] == [[0, 1, 2, 3]]


SITES = {
    "F51": (203.74409, 0.936241, 0.351543),
    "G96": (249.21128, 0.845107, 0.533611),
    "W84": (289.19358, 0.865572, -0.499793),
}


def _synthetic_observations(
    desig: str,
    a: float,
    e: float,
    inc_deg: float,
    phase: float,
    epochs: list[tuple[float, str]],
    *,
    t0: float = 60000.0,
    per_night: int = 3,
    cadence_days: float = 0.02,
) -> list[dict]:
    """Real astrometry of a real Kepler orbit, seen from real observatories.

    The state is built at perihelion, rotated by ``inc_deg`` and advanced by ``phase``
    days, then propagated to each requested epoch and reduced to topocentric RA/Dec with
    light-time applied -- the same physical chain the ITF's own records went through.
    """
    q = a * (1 - e)
    speed = np.sqrt(GM_SUN * (2.0 / q - 1.0 / a))
    inc = np.radians(inc_deg)
    r0 = np.array([[q, 0.0, 0.0]])
    v0 = np.array([[0.0, speed * np.cos(inc), speed * np.sin(inc)]])
    r0, v0, _ = propagate_kepler(r0, v0, np.array([phase]))

    rows: list[dict] = []
    for mjd, code in epochs:
        for k in range(per_night):
            t = mjd + k * cadence_days
            lon, rc, rs = SITES[code]
            obs_pos, _ = observer_heliocentric(
                np.array([t]), np.array([lon]), np.array([rc]), np.array([rs])
            )
            # One light-time iteration is plenty at these distances.
            dt = t - t0
            for _ in range(2):
                r, _, _ = propagate_kepler(r0, v0, np.array([dt]))
                delta = r - obs_pos
                dt = t - t0 - float(np.linalg.norm(delta)) / C_AU_PER_DAY
            direction = delta[0] / np.linalg.norm(delta)
            dec = np.degrees(np.arcsin(direction[2]))
            ra = np.degrees(np.arctan2(direction[1], direction[0])) % 360.0
            rows.append(
                {"desig": desig, "obscode": code, "mjd": t, "ra_deg": ra,
                 "dec_deg": dec, "mag": 21.0, "note2": "C",
                 "night": int(np.floor(t + lon / 360.0 + 0.5))}
            )
    return rows


def _arrows(rows: list[dict]):
    frame = pl.DataFrame(rows).with_columns(pl.col("night").cast(pl.Int32))
    return build_arrows(frame, SITES)


THREE_NIGHTS_ONE_SITE = [(60000.0, "F51"), (60004.0, "F51"), (60008.0, "F51")]
THREE_NIGHTS_THREE_SITES = [(60000.0, "F51"), (60004.0, "G96"), (60008.0, "W84")]


def test_a_synthetic_main_belt_object_is_recovered():
    rows = _synthetic_observations("SYN1", 2.6, 0.12, 8.0, 120.0, THREE_NIGHTS_ONE_SITE)
    arrows = _arrows(rows)
    assert len(arrows) == 3
    links, stats = link_window(arrows.table, HypothesisGrid.build())
    assert stats["candidates"] >= 1
    assert links[0].key == {0, 1, 2}
    assert links[0].n_nights == 3
    assert links[0].a_au == pytest.approx(2.6, rel=0.25)


def test_a_cross_observatory_object_is_recovered_and_flagged():
    rows = _synthetic_observations("SYN2", 2.9, 0.08, 4.0, 30.0, THREE_NIGHTS_THREE_SITES)
    arrows = _arrows(rows)
    links, _ = link_window(arrows.table, HypothesisGrid.build())
    assert links, "cross-observatory link not recovered"
    best = links[0]
    assert best.key == {0, 1, 2}
    assert best.cross_observatory
    assert best.n_obscodes == 3
    assert not best.cross_designation      # one synthetic trkSub, so not a new association


def test_two_unrelated_objects_are_not_merged():
    """Different orbits, same sky region: the linker must keep them apart."""
    rows = _synthetic_observations("SYN3", 2.4, 0.10, 5.0, 60.0, THREE_NIGHTS_ONE_SITE)
    rows += _synthetic_observations("SYN4", 3.2, 0.22, 19.0, 300.0, THREE_NIGHTS_ONE_SITE)
    arrows = _arrows(rows)
    links, _ = link_window(arrows.table, HypothesisGrid.build())
    by_desig = {frozenset(arrows.table["desig"][i] for i in link.key) for link in links}
    assert all(len(d) == 1 for d in by_desig), by_desig


def test_two_nights_is_never_enough():
    rows = _synthetic_observations(
        "SYN5", 2.5, 0.1, 6.0, 10.0, [(60000.0, "F51"), (60005.0, "F51")]
    )
    links, stats = link_window(_arrows(rows).table, HypothesisGrid.build())
    assert links == []
    assert stats["candidates"] == 0


def test_a_hypothesis_grid_that_excludes_the_object_finds_nothing():
    """Recall is bounded by the grid; a distance never guessed is never found."""
    rows = _synthetic_observations("SYN6", 2.6, 0.12, 8.0, 120.0, THREE_NIGHTS_ONE_SITE)
    narrow = HypothesisGrid.build(r_min=5.0, r_max=5.4, r_step=0.1)
    links, _ = link_window(_arrows(rows).table, narrow)
    assert links == []


# --- the structural rules that replaced single-linkage ----------------------------

def _grid_states(n: int, spread: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(3)
    pos = np.tile(np.array([2.0, 0.0, 0.0]), (n, 1)) + rng.normal(scale=spread, size=(n, 3))
    vel = np.zeros((n, 3))
    return pos, vel


def test_a_crowded_neighbourhood_yields_no_link():
    """The linker declines rather than guessing -- and the global check is what enforces it.

    The per-cell guard alone is evadable: a lattice boundary slices the crowd into
    sub-cells that each look uncontested, which is exactly the case constructed here.
    """
    n = 3 * (MAX_SLOT_CANDIDATES + 2)
    pos, vel = _grid_states(n, spread=1e-5)
    night = np.repeat([1, 2, 3], MAX_SLOT_CANDIDATES + 2)
    slot = night.astype(np.int64)          # one observatory: slot == night
    groups, counters = cluster_states(
        pos, vel, night, slot, radius_au=0.0025, vel_scale_days=5.0, min_nights=3
    )
    assert groups, "the cell-local guard is expected to leak here"
    assert counters["ambiguous_neighbourhoods"] > 0

    state6 = np.concatenate([pos, vel * 5.0], axis=1)
    kept, rejected = isolated_groups(groups, state6, night, slot, radius_au=0.0025)
    assert kept == []
    assert rejected == len(groups)


def test_isolation_check_keeps_a_group_with_nothing_else_nearby():
    pos = np.array([[2.0, 0.0, 0.0], [2.0001, 0.0, 0.0], [1.9999, 0.0, 0.0],
                    [3.0, 0.0, 0.0]])
    vel = np.zeros((4, 3))
    night = np.array([1, 2, 3, 1])
    slot = night.astype(np.int64)
    kept, rejected = isolated_groups(
        [np.array([0, 1, 2])], np.concatenate([pos, vel], axis=1), night, slot,
        radius_au=0.0025,
    )
    assert rejected == 0
    assert len(kept) == 1


def test_clustering_keeps_one_tracklet_per_observatory_night():
    pos, vel = _grid_states(6, spread=1e-6)
    night = np.array([1, 1, 2, 2, 3, 3])
    slot = night.astype(np.int64)          # two competitors per slot, under the cap
    groups, _ = cluster_states(
        pos, vel, night, slot, radius_au=0.0025, vel_scale_days=5.0, min_nights=3
    )
    assert groups
    assert all(len(g) == 3 for g in groups)


def test_clustering_enforces_a_diameter_not_a_radius():
    """Two members 2r apart both sit inside a seed's ball but are not one object."""
    pos = np.array([[2.0, 0.0, 0.0], [2.002, 0.0, 0.0], [1.998, 0.0, 0.0]])
    vel = np.zeros((3, 3))
    night = np.array([1, 2, 3])
    slot = night.astype(np.int64)
    groups, _ = cluster_states(
        pos, vel, night, slot, radius_au=0.0025, vel_scale_days=5.0, min_nights=3
    )
    assert groups == []          # diameter is 0.004 > 0.0025


def test_velocity_separates_states_that_share_a_position():
    pos = np.tile(np.array([2.0, 0.0, 0.0]), (3, 1))
    vel = np.array([[0.0, 0.010, 0.0], [0.0, 0.0105, 0.0], [0.0, 0.011, 0.0]])
    night = np.array([1, 2, 3])
    slot = night.astype(np.int64)
    groups, _ = cluster_states(
        pos, vel, night, slot, radius_au=0.0025, vel_scale_days=5.0, min_nights=3
    )
    assert groups == []          # 0.0005 AU/day * 5 d * 2 = 0.005 AU apart


# --- bookkeeping ------------------------------------------------------------------

def _fake(ids, codes, nights=3, spread=1e-4, desigs=("a",)):
    from itf_linker.link.heliolinc import LinkCandidate

    return LinkCandidate(
        arrow_ids=tuple(ids), n_nights=nights, n_obscodes=len(set(codes)),
        obscodes=tuple(sorted(set(codes))), desigs=tuple(desigs), n_obs=3 * len(ids),
        arc_days=6.0, mjd_first=60000.0, mjd_last=60006.0,
        first_trk_n_obs=3, last_trk_n_obs=3, min_trk_n_obs=3,
        r_au=2.5, rdot=0.0, pos_spread_au=spread, vel_spread_au_per_day=1e-5,
    )


def test_subsets_are_dropped():
    big = _fake([1, 2, 3, 4], ["F51"])
    small = _fake([1, 2, 3], ["F51"])
    other = _fake([5, 6, 7], ["F51"])
    kept = drop_subsets([small, big, other])
    assert {c.key for c in kept} == {big.key, other.key}


def test_the_indexed_subset_drop_agrees_with_the_pairwise_one_it_replaced():
    """The tracklet index is an optimisation, so it has to give the same answer.

    Randomised against a deliberately naive reference: overlapping links, nested links,
    equal-size links and disjoint links, which is the mix the merge step actually sees.
    """
    import random

    rng = random.Random(20260803)
    for _ in range(30):
        cands = []
        for _ in range(rng.randint(2, 40)):
            size = rng.randint(3, 6)
            ids = rng.sample(range(14), size)
            cands.append(_fake(ids, ["F51"]))
        ordered = sorted(cands, key=lambda c: -len(c.arrow_ids))
        reference: list = []
        for cand in ordered:
            if not any(cand.key < k.key for k in reference):
                reference.append(cand)
        assert {c.key for c in drop_subsets(cands)} == {c.key for c in reference}


def test_ranking_puts_cross_observatory_first():
    same = _fake([1, 2, 3], ["F51"], spread=1e-9)
    cross = _fake([4, 5, 6], ["F51", "G96"], spread=1e-3)
    assert rank_links([same, cross])[0] is cross


def test_yield_summary_separates_cross_and_same_observatory():
    out = yield_summary(
        [
            _fake([1, 2, 3], ["F51"], desigs=("a",)),
            _fake([4, 5, 6], ["F51", "G96"], desigs=("a", "b")),
        ]
    )
    assert out["cross_observatory"] == 1
    assert out["same_observatory"] == 1
    assert out["joins_more_than_one_trksub"] == 1
    assert out["top_observatory_combinations"] == {"F51+G96": 1}
