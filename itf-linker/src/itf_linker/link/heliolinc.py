"""HelioLinC: link tracklets by clustering, never by enumerating triplets.

The idea (Holman, Payne, Blankley et al. 2018; Heinze, Eggl et al. 2022) is that
*angles-only astrometry plus one assumed heliocentric distance is a full state vector*.
Assume a distance ``r`` and a radial velocity ``rdot`` at a reference epoch; every tracklet
in the window then becomes a position and a velocity, which two-body propagation carries
to one common epoch. Tracklets of the same object land on the same point of the six
dimensional phase space; everything else scatters. Linking becomes clustering.

Why this and not pair enumeration
---------------------------------
M0 measured the wall directly: at nside=64 x 3 days the ITF yields 1.5e7 candidate pairs
but **7.5e8 triplets**, and coarser partitions reach 1e11 -- while the MPC auto-rejects
any link with fewer than three nights, so triplets are what the project needs. HelioLinC
costs ``O(tracklets x hypotheses)`` and produces clusters of *any* size in one pass. A
five-night link costs exactly what a three-night link costs, and no three-way loop exists
anywhere in this module.

What a cluster is and is not
----------------------------
A cluster is a **proposal**. It says "under some assumed distance these tracklets share a
state vector to within the clustering radius". It is not an orbit: there is no least
squares here, no perturbations, and the assumed distance is one of a few hundred guesses.
Every cluster must survive an actual Find_Orb fit and the MPC's gates before it is worth
looking at, and catalogue vetting before it is worth mentioning.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import polars as pl

from .arrows import arrow_arrays
from .geometry import C_AU_PER_DAY, GM_SUN, propagate_kepler, state_from_hypothesis

#: Semimajor axes a cluster is allowed to imply. Below ~0.4 AU nothing survives in the
#: main-belt-dominated ITF; above the ceiling a two-week arc cannot tell a distant object
#: from a diverging solution, and admitting them floods the output with unbound noise.
#: Combined with the requirement that the orbital energy be negative, this is the only
#: physics applied inside the sweep -- an unbound state is overwhelmingly the signature of
#: a wrong distance hypothesis rather than of an interstellar object.
#:
#: The ceiling is a *grid* property rather than a module constant because it has to move
#: with the distance band: 100 AU is generous for a 1.4-5.6 AU hypothesis and is a hard
#: rejection of every scattered-disc object for a 40 AU one.
MIN_PLAUSIBLE_A_AU = 0.4
MAX_PLAUSIBLE_A_AU = 100.0

#: Heliocentric distance below which the *near* root of the line-of-sight/sphere
#: intersection is also a physical position -- see :func:`~itf_linker.link.geometry.solve_rho`.
#: Earth's own heliocentric distance runs 0.983-1.017 AU over the year, so anything below
#: 1.02 AU can put the observer outside the hypothesised sphere at some epoch.
NEAR_BRANCH_MAX_R_AU = 1.02


@dataclass(frozen=True, slots=True)
class HypothesisGrid:
    """The ``(r, rdot)`` guesses swept over one window.

    ``rdot`` is sampled as a fraction of the local escape speed rather than on a fixed
    grid in AU/day, because the physically reachable radial velocity shrinks as ``r``
    grows: ``|rdot| < sqrt(2 GM / r)``. A fixed grid would waste most of its samples on
    unbound states at large ``r`` and under-sample the reachable range at small ``r``.

    Iterating yields ``(r, rdot, near)``. ``near`` selects the near root of the
    line-of-sight/sphere intersection, which exists only where the observer is *outside*
    the hypothesised sphere -- i.e. only inside about 1 AU. It is swept there and nowhere
    else, because outside 1 AU it is guaranteed to produce nothing.
    """

    r_au: tuple[float, ...]
    rdot_fractions: tuple[float, ...]
    max_a_au: float = MAX_PLAUSIBLE_A_AU
    label: str = "grid"

    @classmethod
    def build(
        cls,
        r_min: float = 1.4,
        r_max: float = 5.6,
        r_step: float = 0.10,
        n_rdot: int = 9,
        max_rdot_fraction: float = 0.55,
        max_a_au: float = MAX_PLAUSIBLE_A_AU,
        label: str = "grid",
    ) -> HypothesisGrid:
        """A uniformly spaced grid over heliocentric distance and radial velocity.

        Doubling the distance resolution (0.10 -> 0.05 AU) moved measured recall by
        0.06 percentage points, so the default is not a compromise -- the grid is not
        what limits this linker **inside the main belt**. It is a poor rule once the grid
        spans a decade in distance: see :meth:`geometric`.
        """
        r = tuple(float(x) for x in np.arange(r_min, r_max + 1e-9, r_step))
        frac = tuple(float(x) for x in np.linspace(-max_rdot_fraction, max_rdot_fraction, n_rdot))
        return cls(r_au=r, rdot_fractions=frac, max_a_au=max_a_au, label=label)

    @classmethod
    def geometric(
        cls,
        r_min: float,
        r_max: float,
        *,
        fractional_step: float = 0.04,
        n_rdot: int = 9,
        max_rdot_fraction: float = 0.55,
        max_a_au: float = MAX_PLAUSIBLE_A_AU,
        label: str = "grid",
    ) -> HypothesisGrid:
        """Distance samples spaced by a constant *fraction* of the distance.

        A uniform step is the wrong rule for a grid spanning 0.5-50 AU, and the reason is
        the quantity that actually decides whether a wrong hypothesis breaks a cluster.
        An error ``dr`` in the assumed heliocentric distance perturbs the topocentric
        distance by about the same amount, which mis-scales the implied transverse velocity
        by ``dr * mu`` (``mu`` = the tracklet's sky-plane rate) and therefore displaces the
        propagated state by ``dr * mu * dt``. Requiring that to stay under the clustering
        radius gives ``dr < radius / (mu * dt)``: **the admissible step scales as 1 / mu.**

        At opposition ``mu ~ v_earth (1 - r^-1/2) / (r - 1)``, so ``dr`` grows very nearly
        linearly with ``r``. Evaluated at the production radius (0.0025 AU) and ``dt`` = 7
        days, ``dr / r`` is 0.039 at 1.4 AU, 0.034 at 2.5, 0.029 at 5.6, 0.027 at 10, 0.025
        at 30 and 0.024 at 50 -- constant to 25% across two decades, which is exactly the
        statement that the natural grid is geometric. A uniform 0.10 AU step over 0.5-50 AU
        would be 500 samples, most of them redundant beyond 10 AU and too coarse inside 1.
        """
        if not 0.0 < fractional_step < 1.0:
            raise ValueError(f"fractional_step must be in (0, 1), got {fractional_step}")
        values: list[float] = []
        r = float(r_min)
        while r <= r_max * (1.0 + 1e-9):
            values.append(r)
            r *= 1.0 + fractional_step
        frac = tuple(float(x) for x in np.linspace(-max_rdot_fraction, max_rdot_fraction, n_rdot))
        return cls(
            r_au=tuple(values), rdot_fractions=frac, max_a_au=max_a_au, label=label
        )

    @property
    def n_near(self) -> int:
        """Distance samples for which the near root is also swept."""
        return sum(1 for r in self.r_au if r < NEAR_BRANCH_MAX_R_AU)

    def __iter__(self):
        for r in self.r_au:
            v_esc = np.sqrt(2.0 * GM_SUN / r)
            branches = (False, True) if r < NEAR_BRANCH_MAX_R_AU else (False,)
            for near in branches:
                for f in self.rdot_fractions:
                    yield r, f * v_esc, near

    def __len__(self) -> int:
        return (len(self.r_au) + self.n_near) * len(self.rdot_fractions)

    def as_dict(self) -> dict[str, Any]:
        """JSON-able description of the grid, for the run report."""
        steps = np.diff(np.asarray(self.r_au)) if len(self.r_au) > 1 else np.array([])
        return {
            "label": self.label,
            "r_au_min": self.r_au[0],
            "r_au_max": self.r_au[-1],
            "r_steps": len(self.r_au),
            "r_step_au": round(float(steps[0]), 4) if steps.size else None,
            "r_step_au_max": round(float(steps.max()), 4) if steps.size else None,
            "r_samples_with_near_branch": self.n_near,
            "rdot_samples": len(self.rdot_fractions),
            "rdot_max_fraction_of_escape": max(self.rdot_fractions),
            "max_a_au": self.max_a_au,
            "hypotheses": len(self),
        }


@dataclass(slots=True)
class LinkCandidate:
    """One proposed link: a set of arrows, the hypothesis that found them, and its quality."""

    arrow_ids: tuple[int, ...]
    n_nights: int
    n_obscodes: int
    obscodes: tuple[str, ...]
    desigs: tuple[str, ...]
    n_obs: int
    arc_days: float
    mjd_first: float
    mjd_last: float
    #: Detection counts of the earliest and latest tracklets, and the smallest anywhere in
    #: the link -- what the MPC's "arc starts and ends with a single-detection tracklet"
    #: rule and the ">= 2 observations per object per night" rule are tested against.
    first_trk_n_obs: int
    last_trk_n_obs: int
    min_trk_n_obs: int
    r_au: float
    rdot: float
    pos_spread_au: float
    vel_spread_au_per_day: float
    #: True when the hypothesis that found this link used the *near* root of the
    #: line-of-sight/sphere intersection -- only possible interior to about 1 AU.
    near_branch: bool = False
    a_au: float | None = None
    e: float | None = None
    incl_deg: float | None = None
    n_hypotheses_found: int = 1
    window: int = -1
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> frozenset[int]:
        """Identity of a link: the set of tracklets it joins, order-independent."""
        return frozenset(self.arrow_ids)

    @property
    def cross_observatory(self) -> bool:
        """Does this link span observatories no single survey could link between?"""
        return self.n_obscodes > 1

    @property
    def cross_designation(self) -> bool:
        """Does this link actually join tracklets nobody had already associated?"""
        return len(set(self.desigs)) > 1

    def as_dict(self) -> dict[str, Any]:
        """JSON-able record of the link and the hypothesis that found it."""
        return {
            "arrow_ids": list(self.arrow_ids),
            "desigs": list(self.desigs),
            "obscodes": list(self.obscodes),
            "n_tracklets": len(self.arrow_ids),
            "n_nights": self.n_nights,
            "n_obscodes": self.n_obscodes,
            "n_obs": self.n_obs,
            "arc_days": self.arc_days,
            "mjd_first": self.mjd_first,
            "mjd_last": self.mjd_last,
            "first_trk_n_obs": self.first_trk_n_obs,
            "last_trk_n_obs": self.last_trk_n_obs,
            "min_trk_n_obs": self.min_trk_n_obs,
            "cross_observatory": self.cross_observatory,
            "cross_designation": self.cross_designation,
            "r_au": self.r_au,
            "rdot": self.rdot,
            "near_branch": self.near_branch,
            "pos_spread_au": self.pos_spread_au,
            "vel_spread_au_per_day": self.vel_spread_au_per_day,
            "a_au": self.a_au,
            "e": self.e,
            "incl_deg": self.incl_deg,
            "n_hypotheses_found": self.n_hypotheses_found,
            "window": self.window,
            **self.extra,
        }


def _cell_keys(points: np.ndarray, cell: float, shift: tuple[float, ...]) -> np.ndarray:
    """Pack a lattice cell index into one int64 per point.

    Two points closer than ``cell / 2`` in every coordinate are guaranteed to share a cell
    in at least one of the ``2**d`` lattices offset by half a cell, which is why the caller
    sweeps :func:`itertools.product` over the shifts rather than inspecting neighbours.
    """
    idx = np.floor(points / cell + np.asarray(shift)).astype(np.int64)
    key = idx[:, 0] * np.int64(73856093)
    key ^= idx[:, 1] * np.int64(19349663)
    key ^= idx[:, 2] * np.int64(83492791)
    return key


def _groups_by_key(keys: np.ndarray) -> list[np.ndarray]:
    """Indices grouped by equal key, only for keys occurring more than once."""
    order = np.argsort(keys, kind="stable")
    sorted_keys = keys[order]
    boundaries = np.flatnonzero(np.r_[True, sorted_keys[1:] != sorted_keys[:-1]])
    ends = np.r_[boundaries[1:], len(sorted_keys)] if len(boundaries) else np.array([], dtype=int)
    return [order[s:e] for s, e in zip(boundaries, ends) if e - s > 1]


#: Most tracklets a seed's neighbourhood may hold before the neighbourhood is declared
#: non-discriminating. A genuine link has one tracklet per site per night, so eight is
#: already generous; a ball of forty is a crowded field, not an object.
MAX_BALL_MEMBERS = 16

#: Most tracklets that may compete for one ``(observatory, night)`` slot inside a seed's
#: neighbourhood. One is the physical expectation, and the tracklet key ``(trkSub,
#: observatory, night)`` guarantees a *real* object contributes exactly one. Two or three
#: competitors are resolved by taking the nearest to the seed; beyond that the choice is
#: arbitrary and the link is declined and counted rather than guessed.
MAX_SLOT_CANDIDATES = 3

#: Clusters whose isolation is checked against the whole window in one array. Bounds the
#: peak allocation to ``CENTROID_BATCH x arrows x 6`` doubles per worker.
CENTROID_BATCH = 32


def _prune_to_diameter(
    members: list[int], state6: np.ndarray, seed: int, radius: float, min_size: int
) -> list[int]:
    """Shrink a seed ball until its *diameter* fits inside ``radius``.

    A ball of radius ``r`` about a seed can hold two members ``2r`` apart, which is not
    the same object. The calibration in ``M3-RESULTS.md`` measured the **maximum pairwise**
    separation of known-good groups, so that is the quantity enforced here. Members are
    dropped farthest-from-seed first, which is the only ordering that cannot discard the
    seed itself.
    """
    cur = list(members)
    while True:
        s = state6[cur]
        d = np.linalg.norm(s[:, None, :] - s[None, :, :], axis=-1)
        if d.max() <= radius:
            return cur
        if len(cur) <= min_size:
            return []
        far = int(np.argmax(np.linalg.norm(s - state6[seed], axis=-1)))
        cur.pop(far)


def cluster_states(
    pos: np.ndarray,
    vel: np.ndarray,
    night: np.ndarray,
    slot: np.ndarray,
    *,
    radius_au: float,
    vel_scale_days: float,
    min_nights: int,
    max_cell_members: int = 400,
    max_ball_members: int = MAX_BALL_MEMBERS,
    max_slot_candidates: int = MAX_SLOT_CANDIDATES,
) -> tuple[list[np.ndarray], dict[str, int]]:
    """Cluster propagated states into groups that could physically be one object.

    Hashing is on **position only**, with velocity applied afterwards as an exact test
    inside each cell. That keeps the lattice sweep at ``2**3`` shifts rather than ``2**6``:
    the guarantee that near-neighbours share a cell needs one offset lattice per dimension,
    and paying for six would multiply the cost by eight for no gain -- a cell that is loose
    in velocity simply hands a few extra pairs to the exact test.

    Extraction is **seed-ball**, not single-linkage. Single linkage was tried first and
    fails badly on real data: in a Pan-STARRS/DECam deep field at RA 349, Dec -3 it chained
    24,076 arrows into clusters of *fifty* tracklets carrying fifty different trkSubs,
    because a crowded main-belt field near opposition really does put hundreds of objects
    within 0.07 deg of each other moving at the same rate. Chaining turns that into one
    absurd object. Three rules replace it, and each is structural rather than tuned:

    * **one tracklet per (observatory, night)** -- the tracklet key is
      ``(trkSub, observatory, night)``, so a genuine object contributes exactly one per
      slot and this costs no recall on the ground truth by construction;
    * **diameter, not radius** -- the group's maximum pairwise separation must fit inside
      ``radius_au``, which is the quantity the calibration measured;
    * **decline when ambiguous** -- a neighbourhood with too many members, or too many
      competitors for one slot, yields no link at all and is counted. In the deepest
      survey fields this linker reports that it cannot link rather than guessing.

    Returns ``(groups, counters)``.
    """
    counters = {"overflowed_cells": 0, "ambiguous_neighbourhoods": 0}
    if len(pos) < 2:
        return [], counters
    cell = 2.0 * radius_au
    state6 = np.concatenate([pos, vel * vel_scale_days], axis=1)
    night_l = night.tolist()
    slot_l = slot.tolist()
    found: dict[tuple[int, ...], np.ndarray] = {}

    for shift in itertools.product((0.0, 0.5), repeat=3):
        keys = _cell_keys(pos, cell, shift)
        for idx in _groups_by_key(keys):
            if len(idx) > max_cell_members:
                counters["overflowed_cells"] += 1
                continue
            cell_members = idx.tolist()
            if len({night_l[i] for i in cell_members}) < min_nights:
                continue
            s = state6[idx]
            d = np.linalg.norm(s[:, None, :] - s[None, :, :], axis=-1)
            ball = d <= radius_au
            sizes = ball.sum(axis=1)
            ball_l = ball.tolist()
            for si in np.flatnonzero(sizes >= min_nights).tolist():
                if sizes[si] > max_ball_members:
                    counters["ambiguous_neighbourhoods"] += 1
                    continue
                mask = ball_l[si]
                members = [m for m, keep in zip(cell_members, mask) if keep]
                if len({night_l[m] for m in members}) < min_nights:
                    continue
                dist = d[si][ball[si]].tolist()
                chosen = _one_per_slot(members, slot_l, dist, max_slot_candidates)
                if chosen is None:
                    counters["ambiguous_neighbourhoods"] += 1
                    continue
                if len({night_l[m] for m in chosen}) < min_nights:
                    continue
                chosen = _prune_to_diameter(
                    chosen, state6, cell_members[si], radius_au, min_nights
                )
                if len(chosen) < min_nights or len({night_l[m] for m in chosen}) < min_nights:
                    continue
                key = tuple(chosen)
                found.setdefault(key, np.array(key))
    return list(found.values()), counters


def isolated_groups(
    groups: list[np.ndarray],
    state6: np.ndarray,
    night: np.ndarray,
    slot: np.ndarray,
    *,
    radius_au: float,
    max_ball_members: int = MAX_BALL_MEMBERS,
    max_slot_candidates: int = MAX_SLOT_CANDIDATES,
) -> tuple[list[np.ndarray], int]:
    """Keep only groups whose neighbourhood is *globally* uncrowded.

    The per-cell guard inside :func:`cluster_states` is approximate, and approximate in a
    way that matters: a lattice boundary can slice a crowded blob into sub-cells that each
    look uncontested, so the guard is evaded exactly where it is needed. This check is
    exact and lattice-independent -- for each surviving group it measures the distance from
    the group's centroid to **every** state in the window under the same hypothesis, and
    discards the group if too many tracklets, or too many tracklets competing for one
    ``(observatory, night)`` slot, lie inside the clustering radius.

    It runs once per *group*, not once per seed, and the neighbours are found through a
    **spatial hash rather than a scan over every state**. M3 built the full
    ``groups x arrows x 6`` distance array in batches, which is correct and is fine at
    M3's scale: its densest window held 23,000 arrows and produced ~1,200 groups per
    hypothesis.

    It does not survive the pre-60000 slice. There the deep-drilling archival fields put
    **41,068 arrows** in one window and thousands of groups per hypothesis, and
    ``groups x arrows`` becomes ~10⁸ six-dimensional distances *per hypothesis* -- measured
    at roughly an hour for a single window against 387 hypotheses, which is not a slow run
    but an unfinishable one.

    The hash gives the identical answer. Every state within ``radius_au`` of a centroid in
    six dimensions is also within ``radius_au`` of it in the three position dimensions, so
    with a cell edge of ``radius_au`` it must lie in one of the 27 cells around the
    centroid's own. Those candidates are then tested exactly, in full six dimensions, so
    nothing is approximated: the hash only decides which distances are worth computing.
    Hash collisions (three cell indices are folded into one int64) can only *add* candidates
    to the exact test, never remove them.
    """
    if not groups:
        return [], 0
    centroids = np.stack([state6[g].mean(axis=0) for g in groups])
    near_by_group = _neighbours_within(centroids, state6, radius_au)
    kept: list[np.ndarray] = []
    rejected = 0
    for start in range(0, len(groups), CENTROID_BATCH):
        for offset, group in enumerate(groups[start : start + CENTROID_BATCH]):
            near = near_by_group[start + offset]
            if len(near) > max_ball_members:
                rejected += 1
                continue
            _, counts = np.unique(slot[near], return_counts=True)
            if counts.size and counts.max() > max_slot_candidates:
                rejected += 1
                continue
            if len(np.unique(night[group])) < 3:
                rejected += 1
                continue
            kept.append(group)
    return kept, rejected


def _pack_cells(idx: np.ndarray) -> np.ndarray:
    """Fold integer cell indices into one int64 per row, as :func:`_cell_keys` does."""
    key = idx[:, 0] * np.int64(73856093)
    key ^= idx[:, 1] * np.int64(19349663)
    key ^= idx[:, 2] * np.int64(83492791)
    return key


#: Offsets of the 27 cells that can hold a point within one cell edge of a given cell.
_NEIGHBOUR_OFFSETS = np.array(
    list(itertools.product((-1, 0, 1), repeat=3)), dtype=np.int64
)


def _neighbours_within(
    centroids: np.ndarray, state6: np.ndarray, radius: float
) -> list[np.ndarray]:
    """Indices of every state within ``radius`` of each centroid, in six dimensions.

    Exact. The spatial hash only narrows what is measured; every candidate it produces is
    then tested with the true six-dimensional distance, and no true neighbour can be
    missed because a cell edge of ``radius`` puts all of them inside the 27-cell block
    around the centroid's own cell.
    """
    pos = state6[:, :3]
    cells = np.floor(pos / radius).astype(np.int64)
    keys = _pack_cells(cells)
    order = np.argsort(keys, kind="stable")
    sorted_keys = keys[order]

    c_cells = np.floor(centroids[:, :3] / radius).astype(np.int64)
    out: list[np.ndarray] = []
    for i in range(len(centroids)):
        probe = _pack_cells(c_cells[i] + _NEIGHBOUR_OFFSETS)
        lo = np.searchsorted(sorted_keys, probe, side="left")
        hi = np.searchsorted(sorted_keys, probe, side="right")
        take = [order[a:b] for a, b in zip(lo, hi) if b > a]
        if not take:
            out.append(np.empty(0, dtype=np.int64))
            continue
        cand = np.concatenate(take)
        d = np.linalg.norm(state6[cand] - centroids[i], axis=1)
        out.append(np.sort(cand[d <= radius]))
    return out


def _one_per_slot(
    members: list[int], slot: list[int], dist: list[float], max_candidates: int
) -> list[int] | None:
    """Keep the member nearest the seed in each ``(observatory, night)`` slot.

    Returns ``None`` when any slot is contested by more than ``max_candidates`` tracklets,
    which means the neighbourhood cannot distinguish them.
    """
    keep: dict[int, tuple[float, int]] = {}
    counts: dict[int, int] = {}
    for m, dd in zip(members, dist):
        s = slot[m]
        counts[s] = counts.get(s, 0) + 1
        if counts[s] > max_candidates:
            return None
        best = keep.get(s)
        if best is None or dd < best[0]:
            keep[s] = (dd, m)
    return sorted(v[1] for v in keep.values())


def link_window(
    table: pl.DataFrame,
    grid: HypothesisGrid,
    *,
    t_ref: float | None = None,
    radius_au: float = 0.0025,
    vel_scale_days: float = 5.0,
    min_nights: int = 3,
    window_index: int = -1,
    max_cell_members: int = 400,
) -> tuple[list[LinkCandidate], dict[str, Any]]:
    """Sweep the hypothesis grid over one time window and return deduplicated links."""
    stats: dict[str, Any] = {
        "window": window_index,
        "arrows": table.height,
        "hypotheses": len(grid),
        "clusters_before_dedupe": 0,
        "overflowed_cells": 0,
        "ambiguous_neighbourhoods": 0,
        "rejected_not_isolated": 0,
        "states_valid_mean": 0.0,
    }
    if table.height < min_nights:
        stats["candidates"] = 0
        return [], stats

    a = arrow_arrays(table)
    mjd = a["mjd"]
    t_ref = float(np.median(mjd)) if t_ref is None else t_ref
    n = len(mjd)
    desigs = table["desig"].to_list()
    obscodes = table["obscode"].to_list()
    n_obs_col = table["n_obs"].to_numpy()
    mjd_lo = table["mjd_min"].to_numpy()
    mjd_hi = table["mjd_max"].to_numpy()
    # One integer per (observatory, night): the slot a genuine object fills exactly once.
    code_id = {c: i for i, c in enumerate(sorted(set(obscodes)))}
    slot = np.array(
        [code_id[c] * 1_000_000 + int(nt) for c, nt in zip(obscodes, a["night"])],
        dtype=np.int64,
    )

    merged: dict[frozenset[int], LinkCandidate] = {}
    valid_total = 0

    for r_hyp, rdot_hyp, near in grid:
        # r(t) is modelled linearly across the window; the window length is chosen so the
        # neglected curvature stays under the clustering radius (see pipeline docstring).
        r_at_t = r_hyp + rdot_hyp * (mjd - t_ref)
        # Arrows the linear model carries inside the Sun are dropped **individually**. M3
        # skipped the whole hypothesis if any single arrow did, which costs nothing on a
        # 1.4-5.6 AU grid (nothing reaches 0.05 AU there) but would throw away entire NEO
        # hypotheses over one arrow at the edge of a window.
        in_range = r_at_t > 0.05
        if not in_range.any():
            continue
        r_vec, v_vec, rho, valid = state_from_hypothesis(
            a["obs_pos"], a["obs_vel"], a["rho_hat"], a["rho_hat_dot"],
            np.where(in_range, r_at_t, 1.0), np.full(n, rdot_hyp), near=near,
        )
        valid &= in_range
        if not valid.any():
            continue
        light_time = rho / C_AU_PER_DAY

        r_norm = np.linalg.norm(r_vec, axis=1)
        v2 = np.einsum("ij,ij->i", v_vec, v_vec)
        energy = v2 / 2.0 - GM_SUN / np.maximum(r_norm, 1e-9)
        with np.errstate(divide="ignore", invalid="ignore"):
            a_sma = -GM_SUN / (2.0 * energy)
        bound = valid & (energy < 0) & (a_sma > MIN_PLAUSIBLE_A_AU) & (a_sma < grid.max_a_au)
        if bound.sum() < min_nights:
            continue
        valid_total += int(bound.sum())

        sel = np.flatnonzero(bound)
        dt = t_ref - (mjd[sel] - light_time[sel])
        pos, vel, ok = propagate_kepler(r_vec[sel], v_vec[sel], dt)
        sel = sel[ok]
        if len(sel) < min_nights:
            continue
        pos, vel = pos[ok], vel[ok]

        groups, counters = cluster_states(
            pos, vel, a["night"][sel], slot[sel],
            radius_au=radius_au, vel_scale_days=vel_scale_days,
            min_nights=min_nights, max_cell_members=max_cell_members,
        )
        stats["overflowed_cells"] += counters["overflowed_cells"]
        stats["ambiguous_neighbourhoods"] += counters["ambiguous_neighbourhoods"]
        stats["clusters_before_dedupe"] += len(groups)

        state6 = np.concatenate([pos, vel * vel_scale_days], axis=1)
        groups, crowded = isolated_groups(
            groups, state6, a["night"][sel], slot[sel], radius_au=radius_au
        )
        stats["rejected_not_isolated"] += crowded

        for g in groups:
            rows = sel[g]
            key = frozenset(int(a["arrow_id"][i]) for i in rows)
            existing = merged.get(key)
            spread_p = float(np.linalg.norm(pos[g] - pos[g].mean(axis=0), axis=1).max())
            spread_v = float(np.linalg.norm(vel[g] - vel[g].mean(axis=0), axis=1).max())
            if existing is not None:
                existing.n_hypotheses_found += 1
                if spread_p + vel_scale_days * spread_v < (
                    existing.pos_spread_au + vel_scale_days * existing.vel_spread_au_per_day
                ):
                    _refresh(existing, r_hyp, rdot_hyp, near, spread_p, spread_v, pos[g], vel[g])
                continue
            mean_pos = pos[g].mean(axis=0)
            mean_vel = vel[g].mean(axis=0)
            el = _elements(mean_pos, mean_vel)
            order = rows[np.argsort(mjd[rows])]
            merged[key] = LinkCandidate(
                arrow_ids=tuple(int(a["arrow_id"][i]) for i in rows),
                n_nights=len(np.unique(a["night"][rows])),
                n_obscodes=len({obscodes[i] for i in rows}),
                obscodes=tuple(sorted({obscodes[i] for i in rows})),
                desigs=tuple(sorted({desigs[i] for i in rows})),
                n_obs=int(n_obs_col[rows].sum()),
                arc_days=float(mjd_hi[rows].max() - mjd_lo[rows].min()),
                mjd_first=float(mjd_lo[rows].min()),
                mjd_last=float(mjd_hi[rows].max()),
                first_trk_n_obs=int(n_obs_col[order[0]]),
                last_trk_n_obs=int(n_obs_col[order[-1]]),
                min_trk_n_obs=int(n_obs_col[rows].min()),
                r_au=float(r_hyp),
                rdot=float(rdot_hyp),
                near_branch=bool(near),
                pos_spread_au=spread_p,
                vel_spread_au_per_day=spread_v,
                a_au=el["a"], e=el["e"], incl_deg=el["incl"],
                window=window_index,
            )

    candidates = drop_subsets(list(merged.values()))
    stats["candidates"] = len(candidates)
    stats["states_valid_mean"] = round(valid_total / max(len(grid), 1), 1)
    return candidates, stats


def _refresh(
    cand: LinkCandidate,
    r_hyp: float,
    rdot_hyp: float,
    near: bool,
    spread_p: float,
    spread_v: float,
    pos: np.ndarray,
    vel: np.ndarray,
) -> None:
    el = _elements(pos.mean(axis=0), vel.mean(axis=0))
    cand.r_au = float(r_hyp)
    cand.rdot = float(rdot_hyp)
    cand.near_branch = bool(near)
    cand.pos_spread_au = spread_p
    cand.vel_spread_au_per_day = spread_v
    cand.a_au, cand.e, cand.incl_deg = el["a"], el["e"], el["incl"]


def _elements(pos: np.ndarray, vel: np.ndarray) -> dict[str, float | None]:
    from .geometry import ecliptic_obliquity_matrix, state_to_elements

    rot = ecliptic_obliquity_matrix()
    el = state_to_elements(pos[None, :] @ rot.T, vel[None, :] @ rot.T)
    out: dict[str, float | None] = {}
    for k in ("a", "e", "incl"):
        v = float(el[k][0])
        out[k] = v if np.isfinite(v) else None
    return out


def drop_subsets(candidates: list[LinkCandidate]) -> list[LinkCandidate]:
    """Remove links that are proper subsets of another link found in the same sweep.

    Neighbouring hypotheses routinely recover the same object with one tracklet more or
    less; keeping both would double-count the yield and would send Find_Orb the same
    astrometry twice.

    **Indexed by tracklet, not compared pairwise.** The obvious implementation tests every
    candidate against every candidate already kept, which is fine at M3's 17,060 links and
    is not fine at M4's: the NEO band alone proposes ~60,000 before merging, and a
    quadratic scan there is 2e9 set comparisons. A proper superset must contain *every* one
    of a candidate's tracklets, so it is enough to compare against the links sharing one
    arbitrary tracklet -- a list of a few dozen, not of tens of thousands.
    """
    ordered = sorted(candidates, key=lambda c: -len(c.arrow_ids))
    kept: list[LinkCandidate] = []
    by_arrow: dict[int, list[int]] = {}
    for cand in ordered:
        key = cand.key
        probe = next(iter(key))
        if any(key < kept[i].key for i in by_arrow.get(probe, ())):
            continue
        index = len(kept)
        kept.append(cand)
        for arrow_id in key:
            by_arrow.setdefault(arrow_id, []).append(index)
    return kept
