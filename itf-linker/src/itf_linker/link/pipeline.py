"""Windowing, orchestration and ranking for the M3 linker.

The linker runs over **overlapping time windows** rather than the whole slice at once, for
one reason: the ``(r, rdot)`` hypothesis models an object's heliocentric distance as
linear in time, and that model degrades with window length. A main-belt object's radial
acceleration is bounded by ``GM/r^2`` -- 4.7e-5 AU/day^2 at 2.5 AU -- so the curvature a
straight line cannot follow over a window of ``W`` days is about ``GM W^2 / (8 r^2)``:
0.001 AU at 13 days, 0.005 AU at 29 days. The clustering radius is a few thousandths of an
AU, so **two weeks is where the approximation stops being free**, and that is the default.

Windows overlap so that a link is not lost merely because its tracklets straddle a
boundary. **The step is a quarter of the window, not a half, and that is a measured
choice**: at a half-window step a group whose arc lies between 7 and 14 days can straddle
every boundary, and 682 of the ground-truth groups have arcs longer than 3.5 days.
Stepping by 7 days recovers 81.9% of the in-file ground truth exactly; stepping by 3.5
recovers 87.2%. Each arrow is therefore visited four times, and the duplicate proposals
collapse in :func:`merge_links`.

Ranking puts **cross-observatory links first**, deliberately. Individual surveys link
their own data before it ever reaches the ITF, and M2 measured the consequence: 91 of
M1's 128 candidates carried the Rubin ``RL`` prefix, so a Rubin-to-Rubin link mostly
reconstructs what Rubin's own pipeline will find anyway. A link that joins F51 to G96, or
W84 to F52, is work nobody else is positioned to do, and it is ranked accordingly.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl

from .arrows import Arrows, build_arrows
from .geometry import GM_SUN
from .heliolinc import HypothesisGrid, LinkCandidate, drop_subsets, link_window

#: Window length in days, and the step between window starts. See the module docstring for
#: why 14 days is where the linear-``r(t)`` model stops being free, and why the step is a
#: quarter of the window rather than a half.
DEFAULT_WINDOW_DAYS = 14.0
DEFAULT_WINDOW_STEP_DAYS = 3.5

#: Six-dimensional clustering radius, in AU, with velocity multiplied by
#: :data:`DEFAULT_VEL_SCALE_DAYS` first. Calibrated on in-file ground truth -- see
#: ``M3-RESULTS.md`` and :mod:`itf_linker.link.validate`.
DEFAULT_RADIUS_AU = 0.0025
DEFAULT_VEL_SCALE_DAYS = 5.0


def curvature_window_days(r_au: float, radius_au: float = DEFAULT_RADIUS_AU) -> float:
    """Longest window over which a straight line in ``r(t)`` stays inside the radius.

    The hypothesis models the heliocentric distance as linear in time. The neglected term
    is the radial acceleration ``GM / r^2``, which over a window ``W`` accumulates to
    ``GM W^2 / (8 r^2)``. Setting that equal to the clustering radius and solving for ``W``
    gives the value returned here.

    This is the rule that fixed M3's 14 days at 1.4-5.6 AU, and it is also why the widened
    grid **cannot** use one window length: the limit is 46 days at 5.6 AU, 11.5 days at
    1.4, 8.2 days at 1.0 and 4.1 days at 0.5. Sweeping NEO hypotheses in a 14-day window
    would put the model error at 7e-3 AU, three times the clustering radius, and the
    tracklets of a real object would simply not land on each other.
    """
    return float(np.sqrt(8.0 * radius_au * r_au * r_au / GM_SUN))


@dataclass(frozen=True, slots=True)
class Band:
    """One hypothesis grid swept with the window length that grid's distances allow.

    Bands are swept independently and their links merged. A band is *not* a tuning knob:
    the window follows from :func:`curvature_window_days` at the band's inner edge, and the
    distance spacing from the ``1 / mu`` argument in :meth:`HypothesisGrid.geometric`.
    """

    grid: HypothesisGrid
    window_days: float
    window_step_days: float
    label: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "window_days": self.window_days,
            "window_step_days": self.window_step_days,
            "curvature_limit_days_at_inner_edge": round(
                curvature_window_days(self.grid.r_au[0]), 1
            ),
            "grid": self.grid.as_dict(),
        }


#: Minimum window length. The MPC rejects any link with an arc under 3 days, so a window
#: that cannot hold a 3-day arc plus a night at each end cannot produce a submittable link
#: however good the geometry is. This floors the innermost band at a curvature error of
#: ~1.5x the clustering radius, which is a real and reported cost of searching there.
MIN_WINDOW_DAYS = 5.0

#: Radial-velocity range for the NEO bands, as a fraction of the local escape speed, and
#: the number of samples across it.
#:
#: M3's +/-0.55 is right for the main belt and **measurably wrong inside 1.5 AU**. The
#: reachable fraction for an orbit ``(a, e)`` observed at ``r`` is
#: ``e sqrt(r / (2 a (1 - e^2)))``, which for a low-eccentricity belt object stays well
#: under a half and for an eccentric NEO does not: (3200) Phaethon at 0.84 AU
#: (``a`` = 1.271, ``e`` = 0.890) sits at **0.715**, outside M3's range entirely. It was
#: the one target the first widened run failed to recover, and this is why. The sample
#: count rises with the range so the *resolution* is unchanged at 0.14 of escape speed.
NEO_MAX_RDOT_FRACTION = 0.85
NEO_RDOT_SAMPLES = 13


def belt_band(r_step: float = 0.10, n_rdot: int = 9) -> Band:
    """M3's grid and window, unchanged, so the main-belt result stays reproducible."""
    return Band(
        grid=HypothesisGrid.build(1.4, 5.6, r_step=r_step, n_rdot=n_rdot, label="belt"),
        window_days=DEFAULT_WINDOW_DAYS,
        window_step_days=DEFAULT_WINDOW_STEP_DAYS,
        label="belt",
    )


#: Distance spacing inside 0.95 AU, where the ``1 / mu`` rule is not the whole story.
#:
#: The rule assumes an error ``dr`` moves the topocentric distance by about ``dr``. That
#: holds at opposition and fails badly for an object *interior* to the Earth: there
#: ``d(rho)/dr = r / (r_vec . rho_hat)``, and the denominator is the square root in
#: ``solve_rho``, which shrinks towards the grazing ray. At the geometry that recovers
#: (163693) Atira it is 0.32 AU, so a distance error is amplified threefold before it
#: reaches the transverse velocity.
#:
#: Measured, on Horizons astrometry of four real NEOs, as the tightest cluster diameter any
#: hypothesis in a 0.5-1.5 AU grid achieves (the production radius is 0.0025 AU):
#:
#:     object                 rate      f=0.03    f=0.02    f=0.01    f=0.002
#:     (3200) Phaethon    3.0 deg/d    0.0103    0.0052    0.0020    0.0021
#:     (163693) Atira     1.1 deg/d    0.0011    0.0009    0.0009    0.0009
#:     (2062) Aten        1.1 deg/d    0.0001    0.0002    0.0001    0.0001
#:     (433) Eros         0.9 deg/d    0.0005    0.0005    0.0005    0.0005
#:
#: Below about 1 deg/day the step does not matter at all. At 3 deg/day a 3% step misses by
#: fourfold and a 1% step just fits -- and going finer stops helping, because ~0.002 AU is
#: the *irreducible* spread the linear ``r(t)`` model leaves over a 5-day window at that
#: speed. So 1% is where the grid stops being the limit, and the band is cheap enough
#: (6 s over the whole production slice at 3%) that there is no reason not to pay it.
INNER_FRACTIONAL_STEP = 0.01


def wide_bands(
    *,
    r_step: float = 0.10,
    n_rdot: int = 9,
    fractional_step: float = 0.03,
    inner_fractional_step: float = INNER_FRACTIONAL_STEP,
    outer_fractional_step: float = 0.04,
    outer_r_max: float = 50.0,
    inner_r_min: float = 0.55,
    radius_au: float = DEFAULT_RADIUS_AU,
    include_inner: bool = True,
    include_neo: bool = True,
    include_belt: bool = True,
    include_outer: bool = True,
) -> list[Band]:
    """The M4 production bands: NEO, main belt, Centaur/TNO.

    M3's grid ran 1.4-5.6 AU, which excludes every NEO and everything beyond Jupiter.
    These four bands span 0.55-50 AU. Each carries the window its own distances permit,
    and the main-belt band is byte-for-byte M3's, so widening cannot silently move the
    number M3 reported.
    """

    def window(r_inner: float, cap: float) -> tuple[float, float]:
        w = min(cap, max(MIN_WINDOW_DAYS, curvature_window_days(r_inner, radius_au)))
        w = round(w * 4.0) / 4.0
        return w, w / 4.0

    neo_rdot: dict[str, Any] = {
        "n_rdot": NEO_RDOT_SAMPLES, "max_rdot_fraction": NEO_MAX_RDOT_FRACTION
    }
    bands: list[Band] = []
    if include_inner:
        w, s = window(inner_r_min, 14.0)
        bands.append(
            Band(
                grid=HypothesisGrid.geometric(
                    inner_r_min, 0.95, fractional_step=inner_fractional_step,
                    label="inner", **neo_rdot,
                ),
                window_days=w, window_step_days=s, label="inner",
            )
        )
    if include_neo:
        w, s = window(0.95, 14.0)
        bands.append(
            Band(
                grid=HypothesisGrid.geometric(
                    0.95, 1.45, fractional_step=fractional_step, label="neo", **neo_rdot
                ),
                window_days=w, window_step_days=s, label="neo",
            )
        )
    if include_belt:
        bands.append(belt_band(r_step=r_step, n_rdot=n_rdot))
    if include_outer:
        # 5.6 AU permits 46 days; 21 is used instead because a longer window packs more
        # unrelated tracklets into each neighbourhood, and the isolation guard then
        # declines them. 21 days keeps the model error at 5e-4 AU, a fifth of the radius.
        bands.append(
            Band(
                grid=HypothesisGrid.geometric(
                    5.6, outer_r_max, fractional_step=outer_fractional_step,
                    n_rdot=n_rdot, max_a_au=1000.0, label="outer",
                ),
                window_days=21.0, window_step_days=5.25, label="outer",
            )
        )
    return bands


def merge_links(
    candidates: Iterable[LinkCandidate], *, drop_subset_links: bool = True
) -> list[LinkCandidate]:
    """Collapse links proposed by more than one window or hypothesis into one each.

    ``drop_subset_links`` additionally removes any link that is a *proper subset* of
    another. That is right **within** a band, where neighbouring hypotheses recover the same
    object with one tracklet more or less, and it is wrong **across** bands -- see
    :func:`link_bands`.
    """
    merged: dict[frozenset[int], LinkCandidate] = {}
    for cand in candidates:
        prev = merged.get(cand.key)
        if prev is None:
            merged[cand.key] = cand
            continue
        prev.n_hypotheses_found += cand.n_hypotheses_found
        if cand.pos_spread_au < prev.pos_spread_au:
            merged[cand.key] = cand
            cand.n_hypotheses_found = prev.n_hypotheses_found
    out = list(merged.values())
    return drop_subsets(out) if drop_subset_links else out


def rank_links(candidates: Iterable[LinkCandidate]) -> list[LinkCandidate]:
    """Best first: cross-observatory, then cross-designation, then more nights, then tighter.

    Ranking is not a gate -- nothing is dropped here. It decides what a human, or a
    rate-limited vetting service, looks at first.
    """
    return sorted(
        candidates,
        key=lambda c: (
            not c.cross_observatory,
            not c.cross_designation,
            -c.n_nights,
            -c.n_obscodes,
            c.pos_spread_au,
        ),
    )


def _window_job(job: tuple[int, float, pl.DataFrame, HypothesisGrid, dict[str, Any]]):
    """One window, as a picklable unit of work. Module level so ``spawn`` can import it."""
    index, start, table, grid, kwargs = job
    cands, stats = link_window(table, grid, window_index=index, **kwargs)
    stats["mjd_start"] = float(start)
    return cands, stats


def link_arrows(
    arrows: Arrows,
    *,
    grid: HypothesisGrid | None = None,
    window_days: float = DEFAULT_WINDOW_DAYS,
    window_step_days: float = DEFAULT_WINDOW_STEP_DAYS,
    radius_au: float = DEFAULT_RADIUS_AU,
    vel_scale_days: float = DEFAULT_VEL_SCALE_DAYS,
    min_nights: int = 3,
    max_cell_members: int = 400,
    link_workers: int = 1,
    progress: Callable[[int, int, dict[str, Any]], None] | None = None,
) -> tuple[list[LinkCandidate], dict[str, Any]]:
    """Sweep overlapping windows across an arrow set and return merged, ranked links.

    Windows are independent by construction, so ``link_workers > 1`` farms them out to
    separate processes. Processes rather than threads because the clustering step is
    dominated by small-array bookkeeping that holds the GIL; the per-window payload is one
    slice of the arrow table, a few megabytes at the busiest epochs.
    """
    grid = grid or HypothesisGrid.build()
    table = arrows.table
    if table.height == 0:
        return [], {"windows": 0, "arrows": 0}

    mjd = table["mjd"].to_numpy()
    lo, hi = float(mjd.min()), float(mjd.max())
    starts = np.arange(lo - window_days / 2.0, hi + 1e-9, window_step_days)
    kwargs = {
        "radius_au": radius_au,
        "vel_scale_days": vel_scale_days,
        "min_nights": min_nights,
        "max_cell_members": max_cell_members,
    }
    jobs = []
    for i, start in enumerate(starts):
        sub = arrows.slice_window(start, start + window_days)
        if sub.height >= min_nights:
            jobs.append((i, float(start), sub, grid, kwargs))

    started = time.monotonic()
    all_candidates: list[LinkCandidate] = []
    window_stats: list[dict[str, Any]] = []

    def absorb(done: int, result) -> None:
        """Fold one finished window into the running totals."""
        cands, stats = result
        window_stats.append(stats)
        all_candidates.extend(cands)
        if progress is not None:
            progress(done, len(jobs), stats)

    if link_workers > 1 and len(jobs) > 1:
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(
            max_workers=link_workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            for done, result in enumerate(pool.map(_window_job, jobs, chunksize=1)):
                absorb(done, result)
    else:
        for done, job in enumerate(jobs):
            absorb(done, _window_job(job))

    merged = merge_links(all_candidates)
    ranked = rank_links(merged)
    report = {
        "arrows": table.height,
        "mjd_range": [lo, hi],
        "window_days": window_days,
        "window_step_days": window_step_days,
        "windows_total": len(starts),
        "windows_run": len(window_stats),
        "link_workers": link_workers,
        "grid": grid.as_dict(),
        "radius_au": radius_au,
        "vel_scale_days": vel_scale_days,
        "min_nights": min_nights,
        "clusters_before_dedupe": sum(s["clusters_before_dedupe"] for s in window_stats),
        "overflowed_cells": sum(s["overflowed_cells"] for s in window_stats),
        "ambiguous_neighbourhoods": sum(s["ambiguous_neighbourhoods"] for s in window_stats),
        "rejected_not_isolated": sum(s["rejected_not_isolated"] for s in window_stats),
        "candidates_per_window": sum(s["candidates"] for s in window_stats),
        "candidates_merged": len(merged),
        "elapsed_s": round(time.monotonic() - started, 1),
        "yield": yield_summary(ranked),
        "busiest_windows": sorted(
            window_stats, key=lambda s: -s["candidates"]
        )[:5],
    }
    return ranked, report


def link_bands(
    arrows: Arrows,
    bands: Iterable[Band],
    *,
    progress: Callable[[int, int, dict[str, Any]], None] | None = None,
    band_progress: Callable[[str, dict[str, Any]], None] | None = None,
    **kwargs: Any,
) -> tuple[list[LinkCandidate], dict[str, Any]]:
    """Sweep several distance bands, each with its own window, and merge the links.

    Bands are swept sequentially rather than fused into one grid because they do not share
    a window length, and the window is not free: see :func:`curvature_window_days`.

    **The cross-band merge deduplicates identical links but does not drop subsets**, and
    that is a measured decision rather than a stylistic one. Dropping subsets is right
    inside a band, where neighbouring hypotheses recover the same object with one tracklet
    more or less. Across bands it is destructive: a NEO-band proposal that happens to be
    the true main-belt group *plus one neighbour* is a proper superset of the correct
    belt-band link, so the correct link is deleted and the contaminated one kept. Measured
    on M3's own ground truth, exact recall fell **0.874 -> 0.677** with cross-band subset
    dropping enabled, with "only ever seen mixed with a stranger" rising from 81 groups to
    462 while "touched at all" *rose* to 0.982 -- the signature of suppression, not of a
    failure to find. M3 saw the same mechanism from the other side in its section 5.3, where
    removing contaminated supersets *improved* recall.

    Competing distance hypotheses for overlapping tracklet sets are exactly what the orbit
    fit and the conflict resolver exist to adjudicate. Deciding it with a set-inclusion rule
    before any orbit has been computed throws away the better candidate about as often as
    the worse one.
    """
    bands = list(bands)
    all_candidates: list[LinkCandidate] = []
    per_band: list[dict[str, Any]] = []
    started = time.monotonic()
    for band in bands:
        links, report = link_arrows(
            arrows,
            grid=band.grid,
            window_days=band.window_days,
            window_step_days=band.window_step_days,
            progress=progress,
            **kwargs,
        )
        for cand in links:
            cand.extra["band"] = band.label
        all_candidates.extend(links)
        entry = {"band": band.as_dict(), **{k: v for k, v in report.items() if k != "yield"}}
        entry["candidates_this_band"] = len(links)
        per_band.append(entry)
        if band_progress is not None:
            band_progress(band.label, entry)

    merged = merge_links(all_candidates, drop_subset_links=len(bands) == 1)
    ranked = rank_links(merged)
    report = {
        "arrows": arrows.table.height,
        "cross_band_subset_drop": len(bands) == 1,
        "bands": per_band,
        "hypotheses_total": sum(len(b.grid) for b in bands),
        "candidates_before_band_merge": len(all_candidates),
        "candidates_merged": len(ranked),
        "candidates_by_band": _band_histogram(ranked),
        "elapsed_s": round(time.monotonic() - started, 1),
        "yield": yield_summary(ranked),
    }
    return ranked, report


def _band_histogram(candidates: Iterable[LinkCandidate]) -> dict[str, int]:
    """Which band's hypothesis ended up owning each surviving link."""
    out: dict[str, int] = {}
    for c in candidates:
        label = str(c.extra.get("band", "?"))
        out[label] = out.get(label, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def yield_summary(candidates: Iterable[LinkCandidate]) -> dict[str, Any]:
    """Cross-observatory and same-observatory yields, reported separately."""
    cands = list(candidates)
    cross = [c for c in cands if c.cross_observatory]
    same = [c for c in cands if not c.cross_observatory]
    new_assoc = [c for c in cands if c.cross_designation]

    def by_nights(group: list[LinkCandidate]) -> dict[int, int]:
        """Histogram of nights per link."""
        out: dict[int, int] = {}
        for c in group:
            out[c.n_nights] = out.get(c.n_nights, 0) + 1
        return dict(sorted(out.items()))

    codes: dict[str, int] = {}
    for c in cross:
        codes["+".join(c.obscodes)] = codes.get("+".join(c.obscodes), 0) + 1

    return {
        "total": len(cands),
        "cross_observatory": len(cross),
        "same_observatory": len(same),
        "joins_more_than_one_trksub": len(new_assoc),
        "reconstructs_one_trksub": len(cands) - len(new_assoc),
        # The intersection is the milestone's actual target: an association nobody had
        # made, spanning observatories no single survey could link across.
        "cross_observatory_and_new_association": sum(
            1 for c in cands if c.cross_observatory and c.cross_designation
        ),
        "nights_histogram_cross_observatory": by_nights(cross),
        "nights_histogram_same_observatory": by_nights(same),
        "top_observatory_combinations": dict(
            sorted(codes.items(), key=lambda kv: -kv[1])[:12]
        ),
    }


def link_slice(
    observations: pl.DataFrame,
    obscodes: dict[str, tuple[float, float, float]],
    *,
    mjd_min: float | None = 60000.0,
    mjd_max: float | None = None,
    grid: HypothesisGrid | None = None,
    **kwargs: Any,
) -> tuple[list[LinkCandidate], dict[str, Any]]:
    """Build arrows over a time slice of the ITF and link them.

    ``mjd_min = 60000`` is M0's recommended sandbox: 512,106 tracklets from 2023-02
    onward, where follow-up is still physically possible.
    """
    arrows = build_arrows(observations, obscodes, mjd_min=mjd_min, mjd_max=mjd_max)
    ranked, report = link_arrows(arrows, grid=grid, **kwargs)
    report["arrow_build"] = arrows.stats
    report["slice"] = {"mjd_min": mjd_min, "mjd_max": mjd_max}
    return ranked, report
