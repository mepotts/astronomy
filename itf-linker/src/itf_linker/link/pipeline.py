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
from typing import Any

import numpy as np
import polars as pl

from .arrows import Arrows, build_arrows
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


def merge_links(candidates: Iterable[LinkCandidate]) -> list[LinkCandidate]:
    """Collapse links proposed by more than one window or hypothesis into one each."""
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
    return drop_subsets(list(merged.values()))


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
