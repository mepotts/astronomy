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
#: main-belt-dominated ITF; above 100 AU a two-week arc cannot tell a distant object from
#: a diverging solution, and admitting them floods the output with unbound noise. Combined
#: with the requirement that the orbital energy be negative, this is the only physics
#: applied inside the sweep -- an unbound state is overwhelmingly the signature of a wrong
#: distance hypothesis rather than of an interstellar object.
MIN_PLAUSIBLE_A_AU = 0.4
MAX_PLAUSIBLE_A_AU = 100.0


@dataclass(frozen=True, slots=True)
class HypothesisGrid:
    """The ``(r, rdot)`` guesses swept over one window.

    ``rdot`` is sampled as a fraction of the local escape speed rather than on a fixed
    grid in AU/day, because the physically reachable radial velocity shrinks as ``r``
    grows: ``|rdot| < sqrt(2 GM / r)``. A fixed grid would waste most of its samples on
    unbound states at large ``r`` and under-sample the reachable range at small ``r``.
    """

    r_au: tuple[float, ...]
    rdot_fractions: tuple[float, ...]

    @classmethod
    def build(
        cls,
        r_min: float = 1.4,
        r_max: float = 5.6,
        r_step: float = 0.10,
        n_rdot: int = 9,
        max_rdot_fraction: float = 0.55,
    ) -> HypothesisGrid:
        """A grid over heliocentric distance and radial velocity.

        Doubling the distance resolution (0.10 -> 0.05 AU) moved measured recall by
        0.06 percentage points, so the default is not a compromise -- the grid is not
        what limits this linker.
        """
        r = tuple(float(x) for x in np.arange(r_min, r_max + 1e-9, r_step))
        frac = tuple(float(x) for x in np.linspace(-max_rdot_fraction, max_rdot_fraction, n_rdot))
        return cls(r_au=r, rdot_fractions=frac)

    def __iter__(self):
        for r in self.r_au:
            v_esc = np.sqrt(2.0 * GM_SUN / r)
            for f in self.rdot_fractions:
                yield r, f * v_esc

    def __len__(self) -> int:
        return len(self.r_au) * len(self.rdot_fractions)

    def as_dict(self) -> dict[str, Any]:
        """JSON-able description of the grid, for the run report."""
        return {
            "r_au_min": self.r_au[0],
            "r_au_max": self.r_au[-1],
            "r_steps": len(self.r_au),
            "r_step_au": round(self.r_au[1] - self.r_au[0], 4) if len(self.r_au) > 1 else None,
            "rdot_samples": len(self.rdot_fractions),
            "rdot_max_fraction_of_escape": max(self.rdot_fractions),
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

    It is affordable because it runs once per *group*, not once per seed: the states are
    already computed for the hypothesis in hand, so the whole check is a ``(groups x
    arrows)`` distance array.

    That array is built **in batches**, which is not premature optimisation. Built whole it
    is ``groups x arrows x 6`` doubles -- 167 MB for 151 groups against a 23,000-arrow
    window -- and with two dozen worker processes doing that at once the run dies with a
    ``MemoryError`` while asking for only 26 MB. Batching bounds it to a few tens of
    megabytes per worker however dense the window is.
    """
    if not groups:
        return [], 0
    centroids = np.stack([state6[g].mean(axis=0) for g in groups])
    kept: list[np.ndarray] = []
    rejected = 0
    for start in range(0, len(groups), CENTROID_BATCH):
        block = centroids[start : start + CENTROID_BATCH]
        inside = np.linalg.norm(block[:, None, :] - state6[None, :, :], axis=-1) <= radius_au
        for offset, group in enumerate(groups[start : start + CENTROID_BATCH]):
            near = np.flatnonzero(inside[offset])
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

    for r_hyp, rdot_hyp in grid:
        # r(t) is modelled linearly across the window; the window length is chosen so the
        # neglected curvature stays under the clustering radius (see pipeline docstring).
        r_at_t = r_hyp + rdot_hyp * (mjd - t_ref)
        if np.any(r_at_t <= 0.05):
            continue
        r_vec, v_vec, rho, valid = state_from_hypothesis(
            a["obs_pos"], a["obs_vel"], a["rho_hat"], a["rho_hat_dot"],
            r_at_t, np.full(n, rdot_hyp),
        )
        if not valid.any():
            continue
        light_time = rho / C_AU_PER_DAY

        r_norm = np.linalg.norm(r_vec, axis=1)
        v2 = np.einsum("ij,ij->i", v_vec, v_vec)
        energy = v2 / 2.0 - GM_SUN / np.maximum(r_norm, 1e-9)
        with np.errstate(divide="ignore", invalid="ignore"):
            a_sma = -GM_SUN / (2.0 * energy)
        bound = valid & (energy < 0) & (a_sma > MIN_PLAUSIBLE_A_AU) & (a_sma < MAX_PLAUSIBLE_A_AU)
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
                    _refresh(existing, r_hyp, rdot_hyp, spread_p, spread_v, pos[g], vel[g])
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
    spread_p: float,
    spread_v: float,
    pos: np.ndarray,
    vel: np.ndarray,
) -> None:
    el = _elements(pos.mean(axis=0), vel.mean(axis=0))
    cand.r_au = float(r_hyp)
    cand.rdot = float(rdot_hyp)
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
    """
    ordered = sorted(candidates, key=lambda c: -len(c.arrow_ids))
    kept: list[LinkCandidate] = []
    for cand in ordered:
        if any(cand.key < k.key for k in kept):
            continue
        kept.append(cand)
    return kept
