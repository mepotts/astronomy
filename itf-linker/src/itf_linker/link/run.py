"""The M3 chain end to end: link, gate, fit, gate again, resolve conflicts, rank.

    arrows -> HelioLinC clusters        link.pipeline.link_slice
           -> MPC published pre-fit gate + >= 2 obs/night   link.assemble.gate_links
           -> original 80-column astrometry, relabelled     link.assemble.link_astrometry
           -> Find_Orb                                      fit.findorb.run_fo_batched
           -> MPC published post-fit gate                   fit.gates.post_fit_gate
           -> "one orbit fits all of it" guard              fit.collide
           -> conflict resolution                           resolve_conflicts
           -> ranked output, cross-observatory first

Every stage after the linker is **M1's code, unchanged**. That is deliberate: the gates
are the MPC's and the supplementary checks are M1's, and a second implementation for links
would let the two drift. What M3 adds is the proposal step and one thing M1 never needed --
**conflict resolution**. A tracklet belongs to one object, so two surviving links that
share a tracklet cannot both be right, and the linker routinely proposes such pairs because
neighbouring distance hypotheses recover the same object with one member swapped.

The output is a list of **linked candidates surviving gates**. It is not a list of new
objects, and no stage of this module claims otherwise. Catalogue vetting (M2) runs after
this, and even a vetted survivor is only "not ruled out".
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from ..fit import classify, collide
from ..fit.findorb import FitResult, run_fo_batched
from ..fit.gates import post_fit_gate
from ..fit.pipeline import FitOutcome, used_nights
from ..fit.wsl import Shell, default_shell
from .assemble import gate_links, link_astrometry
from .heliolinc import HypothesisGrid, LinkCandidate
from .pipeline import Band, link_arrows, link_bands, yield_summary


def resolve_conflicts(outcomes: Sequence[FitOutcome], arrows_by_link: dict[str, list[int]]):
    """Greedy: a tracklet may belong to exactly one accepted link.

    Ordered by the same criteria as M1's ranking -- lowest RMS, then tightest sigma(a),
    then longest arc -- and a link is accepted only if none of its tracklets is already
    spoken for. Both the raw survivor list and the conflict-free subset are reported,
    because the difference between them is a real measure of how ambiguous the linking was.
    """
    ordered = sorted(
        outcomes,
        key=lambda o: (
            o.fit.rms_residual if o.fit.rms_residual is not None else 9e9,
            o.fit.sigma_a if o.fit.sigma_a is not None else 9e9,
            -(o.fit.arc_days or 0.0),
        ),
    )
    taken: set[int] = set()
    kept: list[FitOutcome] = []
    dropped: list[FitOutcome] = []
    for outcome in ordered:
        ids = set(arrows_by_link.get(outcome.desig, ()))
        if ids & taken:
            dropped.append(outcome)
            continue
        taken |= ids
        kept.append(outcome)
    return kept, dropped


def prioritise_bands(
    gated: pl.DataFrame, order: Sequence[str] | None = None
) -> pl.DataFrame:
    """Add a ``band_priority`` column ranking whole distance bands against each other.

    Fitting is the expensive stage -- 13,618 links cost 55 minutes of wall clock in M3 --
    so when a limit binds, *which* links get fitted is a real decision rather than
    bookkeeping. Bands not named in ``order`` sort after every band that is.
    """
    if "band" not in gated.columns:
        return gated.with_columns(pl.lit(0, dtype=pl.Int32).alias("band_priority"))
    ranks = {name: i for i, (name) in enumerate(order or ())}
    fallback = len(ranks)
    return gated.with_columns(
        pl.col("band")
        .replace_strict(ranks, default=fallback, return_dtype=pl.Int32)
        .alias("band_priority")
    )


def fit_links(
    gated: pl.DataFrame,
    arrows: pl.DataFrame,
    obscode_lon: dict[str, float],
    workroot: Path,
    *,
    src_gz: Path | None = None,
    shell: Shell | None = None,
    workers: int = 8,
    chunk_size: int = 40,
    limit: int | None = None,
    resume: bool = False,
    completed_only: bool = False,
    astrometry_out: Path | None = None,
    progress: Callable[[int, int, Any], None] | None = None,
) -> dict[str, Any]:
    """Fit gated links with Find_Orb and apply every post-fit gate M1 defined.

    ``completed_only`` reports on the chunks a previous run finished and runs nothing --
    see :func:`~itf_linker.fit.findorb.run_fo_batched`. Links with no result are dropped
    from the funnel rather than counted as failures, and ``links_fitted`` /
    ``links_submitted`` record the sampling fraction.
    """
    shell = shell or default_shell()
    table = gated.head(limit) if limit else gated
    groups, extract_stats = link_astrometry(table, arrows, obscode_lon, src=src_gz)
    if astrometry_out is not None:
        astrometry_out.parent.mkdir(parents=True, exist_ok=True)
        astrometry_out.write_text(
            json.dumps({"stats": extract_stats, "lines": groups}, indent=1), encoding="utf-8"
        )

    diagnostics: list[dict[str, Any]] = []
    started = time.monotonic()
    results = run_fo_batched(
        groups, workroot, shell=shell, workers=workers, chunk_size=chunk_size,
        progress=progress, diagnostics=diagnostics, resume=resume,
        completed_only=completed_only,
    )
    meta = {r["desig"]: r for r in table.to_dicts()}
    fitted = [d for d in groups if not completed_only or d in results]

    outcomes: list[FitOutcome] = []
    for desig in fitted:
        fit = results.get(desig) or FitResult(desig=desig, status="not_extracted")
        info = meta[desig]
        gate = post_fit_gate(fit, n_nights=int(info["n_nights"]))
        ok, reasons = collide.post_fit_collision_check(
            fit.n_obs, fit.n_used, used_nights=used_nights(fit)
        )
        outcomes.append(
            FitOutcome(
                desig=desig,
                fit=fit,
                n_nights=int(info["n_nights"]),
                n_obs_submitted=len(groups[desig]),
                prefit_arc_days=float(info["arc_days"]),
                obscodes=list(info["obscodes"]),
                gate_passes=gate.passes and ok,
                gate_reasons=gate.reasons + reasons,
            )
        )

    arrows_by_link = {r["desig"]: list(r["arrow_ids"]) for r in table.to_dicts()}
    passed = [o for o in outcomes if o.gate_passes]
    kept, dropped = resolve_conflicts(passed, arrows_by_link)
    band_of = {r["desig"]: r.get("band", "belt") for r in table.to_dicts()}
    # Conflicts are *resolved* by fit quality -- the better orbit wins a contested tracklet
    # -- but the surviving list is *presented* cross-observatory first, because that is
    # what M3 exists to produce and what a rate-limited vetting pass should see first.
    kept = rank_survivors(kept, meta)

    converged = [o for o in outcomes if o.fit.converged]
    return {
        "extraction": extract_stats,
        "links_submitted": len(groups),
        "links_fitted": len(fitted),
        "completed_only": completed_only,
        "fo_invocation_failures": diagnostics,
        "elapsed_s": round(time.monotonic() - started, 1),
        "converged": len(converged),
        "not_converged": len(outcomes) - len(converged),
        "rms_le_0.25": sum(1 for o in converged if (o.fit.rms_residual or 9e9) <= 0.25),
        "failed_subset_guard": sum(
            1
            for o in converged
            if not collide.post_fit_collision_check(
                o.fit.n_obs, o.fit.n_used, used_nights(o.fit)
            )[0]
        ),
        "not_converged_reasons": _status_histogram(outcomes),
        "passed_all_gates": len(passed),
        "dropped_by_conflict_resolution": len(dropped),
        "survivors": len(kept),
        "survivors_cross_observatory": sum(1 for o in kept if len(set(o.obscodes)) > 1),
        "survivors_same_observatory": sum(1 for o in kept if len(set(o.obscodes)) == 1),
        # The milestone's actual target: an association nobody had made, across
        # observatories no single survey could link between.
        "survivors_new_association": sum(
            1 for o in kept if len(set(meta[o.desig]["source_desigs"])) > 1
        ),
        "survivors_new_association_cross_observatory": sum(
            1
            for o in kept
            if len(set(meta[o.desig]["source_desigs"])) > 1 and len(set(o.obscodes)) > 1
        ),
        # Reported by population and by band, because "we widened the grid" is only a
        # result if the widened part of it produced something distinguishable.
        "survivors_by_population": classify.population_histogram(
            [classify.describe(o.fit) for o in kept]
        ),
        "survivors_by_band": _histogram(band_of.get(o.desig, "?") for o in kept),
        "survivors_neo_by_q": sum(
            1 for o in kept if classify.describe(o.fit)["is_neo_by_q"]
        ),
        "converged_by_population": classify.population_histogram(
            [classify.describe(o.fit) for o in converged]
        ),
        "submitted_by_band": _histogram(band_of.get(o.desig, "?") for o in outcomes),
        "ranked": [_row(o, meta) for o in kept],
        "conflicted": [_row(o, meta) for o in dropped],
        "outcomes": [_row(o, meta) for o in outcomes],
    }


def _histogram(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def rank_survivors(
    outcomes: Sequence[FitOutcome], meta: dict[str, dict[str, Any]]
) -> list[FitOutcome]:
    """Order surviving links: cross-observatory first, new associations next, then best fit.

    Individual surveys already link their own data, so a same-observatory link mostly
    reconstructs what that survey's own pipeline will find. A link spanning two or more
    observatory codes is the part nobody else is positioned to do, and M2 measured why it
    matters: 91 of M1's 128 candidates carried one survey's naming family.
    """
    return sorted(
        outcomes,
        key=lambda o: (
            len(set(o.obscodes)) <= 1,
            len(set(meta.get(o.desig, {}).get("source_desigs", ["x"]))) <= 1,
            o.fit.rms_residual if o.fit.rms_residual is not None else 9e9,
            o.fit.sigma_a if o.fit.sigma_a is not None else 9e9,
        ),
    )


def _status_histogram(outcomes: Sequence[FitOutcome]) -> dict[str, int]:
    """Why the non-converging fits did not converge, commonest first."""
    hist: dict[str, int] = {}
    for o in outcomes:
        if not o.fit.converged:
            hist[o.fit.status] = hist.get(o.fit.status, 0) + 1
    return dict(sorted(hist.items(), key=lambda kv: -kv[1]))


def _row(outcome: FitOutcome, meta: dict[str, dict[str, Any]]) -> dict[str, Any]:
    info = meta.get(outcome.desig, {})
    row = outcome.as_dict()
    # Which population the fitted orbit lands in, and how strongly it claims to be an NEO.
    # M4 widened the hypothesis grid specifically to reach populations M3 could not, so a
    # survivor that is not labelled by population does not answer the question that was
    # asked.
    row.update(classify.describe(outcome.fit))
    for key in (
        "arrow_ids", "source_desigs", "cross_observatory", "cross_designation",
        "pos_spread_au", "r_au", "n_hypotheses_found", "n_tracklets",
        "band", "near_branch",
    ):
        if key in info:
            row[key] = info[key]
    return row


def run_m3(
    observations: pl.DataFrame,
    obscode_lon: dict[str, float],
    obscodes_full: dict[str, tuple[float, float, float]],
    *,
    workroot: Path,
    mjd_min: float | None = 60000.0,
    mjd_max: float | None = None,
    grid: HypothesisGrid | None = None,
    bands: Sequence[Band] | None = None,
    shell: Shell | None = None,
    fit_limit: int | None = None,
    fit_resume: bool = False,
    astrometry_out: Path | None = None,
    links_out: Path | None = None,
    link_progress: Callable[[int, int, dict[str, Any]], None] | None = None,
    band_progress: Callable[[str, dict[str, Any]], None] | None = None,
    fit_progress: Callable[[int, int, Any], None] | None = None,
    src_gz: Path | None = None,
    workers: int = 8,
    fit_order: Sequence[str] | None = None,
    **link_kwargs: Any,
) -> tuple[dict[str, Any], list[LinkCandidate]]:
    """Link, gate, fit and rank -- one JSON-able report plus the raw link list.

    ``bands`` sweeps several distance bands, each with its own window length; ``grid``
    sweeps one. Passing both is an error, because the window would then belong to two
    owners.
    """
    from .arrows import build_arrows

    if bands is not None and grid is not None:
        raise ValueError("pass either `grid` (one band) or `bands` (several), not both")

    arrows = build_arrows(observations, obscodes_full, mjd_min=mjd_min, mjd_max=mjd_max)
    if bands is not None:
        links, link_report = link_bands(
            arrows, bands, progress=link_progress, band_progress=band_progress,
            **{k: v for k, v in link_kwargs.items()
               if k not in ("window_days", "window_step_days")},
        )
    else:
        links, link_report = link_arrows(
            arrows, grid=grid, progress=link_progress, **link_kwargs
        )
    link_report["arrow_build"] = arrows.stats
    link_report["slice"] = {"mjd_min": mjd_min, "mjd_max": mjd_max}
    gated, gate_report = gate_links(links)
    passing = gated.filter(pl.col("link_pass")) if gated.height else gated
    # Cross-observatory first: that ordering is what decides which links get fitted at all
    # when a limit is applied, and it is M3's whole strategic point. ``fit_order`` puts
    # whole distance bands ahead of that, which is M4's: a main-belt link is a population
    # every survey re-detects constantly, and an NEO- or TNO-distance link is not.
    if passing.height:
        passing = prioritise_bands(passing, fit_order).sort(
            ["band_priority", "cross_observatory", "cross_designation",
             "n_nights", "pos_spread_au"],
            descending=[False, True, True, True, False],
        )

    if links_out is not None and gated.height:
        # Written before fitting starts. Linking is ~30 minutes and fitting is hours, so a
        # fit interrupted or re-run with a different worker count must not have to repeat
        # the linking; ``itf-linker link-fit`` picks this up directly.
        links_out.parent.mkdir(parents=True, exist_ok=True)
        gated.write_parquet(links_out)

    report: dict[str, Any] = {
        "linking": link_report,
        "link_gate": gate_report,
        "gated_yield": yield_summary(
            [c for c, keep in zip(links, gated["link_pass"].to_list())if keep]
        ) if gated.height else {},
    }
    shell = shell or default_shell()
    if not shell.available():
        report["fits"] = {"skipped": f"Find_Orb not reachable at {shell.fo_path}"}
        return report, links

    report["find_orb"] = shell.version()
    report["fits"] = fit_links(
        passing, arrows.table, obscode_lon, workroot,
        src_gz=src_gz, shell=shell, workers=workers, limit=fit_limit,
        resume=fit_resume, astrometry_out=astrometry_out, progress=fit_progress,
    )
    return report, links
