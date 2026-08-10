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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from ..fit import classify, collide, gates
from ..fit.findorb import FitResult, run_fo_batched
from ..fit.gates import post_fit_gate
from ..fit.pipeline import FitOutcome, used_nights
from ..fit.wsl import Shell, default_shell
from .assemble import LineIndex, gate_links, link_astrometry
from .heliolinc import HypothesisGrid, LinkCandidate
from .pipeline import Band, link_arrows, link_bands, yield_summary
from .priority import rank_for_fitting


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
    line_index: LineIndex | None = None,
    scratch_root: str | None = None,
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
    groups, extract_stats = link_astrometry(
        table, arrows, obscode_lon, src=src_gz, line_index=line_index
    )
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
        completed_only=completed_only, scratch_root=scratch_root,
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


# ----------------------------------------------------------------------------------
# Fitting a queue too long to finish in one sitting
# ----------------------------------------------------------------------------------
#
# M4 fitted 1.08% of the older slice's gated links and said so. Finishing that job means
# hundreds of thousands of `fo` invocations, which will be interrupted -- so the run has to
# be built out of pieces that are individually complete and individually reported.
#
# Two granularities do that, and both already existed in part:
#
# * the **chunk** (40 links, one `fo` invocation) is the unit `--resume` re-reads. Nothing
#   a chunk finished is ever recomputed, including the 4,461 links M4 fitted;
# * the **batch** (a few thousand links) is the unit a JSON checkpoint is written for, the
#   moment it finishes. M3 lost 150 chunks to a timeout because its report was written only
#   at the end; a batch checkpoint means the worst case is losing the batch in flight.
#
# Conflict resolution and ranking are then re-done **globally** over the union of the
# checkpoints, because "a tracklet belongs to one object" is not a per-batch statement.


def resolve_conflicts_rows(rows: Sequence[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    """:func:`resolve_conflicts` over serialised outcome rows rather than objects.

    The batched path re-reads its survivors from JSON checkpoints, so the global pass over
    them cannot use :class:`~itf_linker.fit.pipeline.FitOutcome`. A test pins this against
    :func:`resolve_conflicts` on the same input, because two implementations of one rule is
    exactly how the rule drifts.
    """
    ordered = sorted(
        rows,
        key=lambda r: (
            r.get("rms_residual") if r.get("rms_residual") is not None else 9e9,
            r.get("sigma_a") if r.get("sigma_a") is not None else 9e9,
            -(r.get("arc_days") or 0.0),
        ),
    )
    taken: set[int] = set()
    kept: list[dict] = []
    dropped: list[dict] = []
    for row in ordered:
        ids = {int(i) for i in row.get("arrow_ids") or ()}
        if ids & taken:
            dropped.append(row)
            continue
        taken |= ids
        kept.append(row)
    return kept, dropped


def rank_survivor_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """:func:`rank_survivors` over serialised outcome rows: cross-observatory first."""
    return sorted(
        rows,
        key=lambda r: (
            len(set(r.get("obscodes") or ())) <= 1,
            len(set(r.get("source_desigs") or ("x",))) <= 1,
            r.get("rms_residual") if r.get("rms_residual") is not None else 9e9,
            r.get("sigma_a") if r.get("sigma_a") is not None else 9e9,
        ),
    )


@dataclass(frozen=True, slots=True)
class FitBatch:
    """One checkpointable unit of fitting: a slice of the queue and where ``fo`` runs it."""

    name: str
    table: pl.DataFrame
    workroot: Path


def plan_batches(
    ranked: pl.DataFrame,
    workroot: Path,
    *,
    batch_size: int,
    seed: Sequence[FitBatch] = (),
) -> list[FitBatch]:
    """Cut a ranked queue into batches, after any ``seed`` batches already fitted elsewhere.

    ``seed`` carries work a previous milestone completed in its own directory -- M4's 4,461
    links, whose chunk layout lives under ``data/m4-fits-old``. Those links are removed from
    the queue here rather than refitted, which is the whole point of ``--fit-resume``.
    """
    done = {d for batch in seed for d in batch.table["desig"].to_list()}
    todo = ranked.filter(~pl.col("desig").is_in(done)) if done else ranked
    batches = list(seed)
    for i in range(0, todo.height, batch_size):
        batches.append(
            FitBatch(
                name=f"b{i // batch_size:04d}",
                table=todo.slice(i, batch_size),
                workroot=workroot / f"b{i // batch_size:04d}",
            )
        )
    return batches


#: What a batch checkpoint keeps. Everything else in a `fit_links` report is either a
#: counter (aggregated on merge) or a row for a link that failed a gate -- and 400,000 of
#: those is a gigabyte of JSON nobody reads.
_CHECKPOINT_COUNTERS = (
    "links_submitted", "links_fitted", "converged", "not_converged", "rms_le_0.25",
    "failed_subset_guard", "passed_all_gates", "elapsed_s",
)
_CHECKPOINT_HISTOGRAMS = (
    "not_converged_reasons", "converged_by_population", "submitted_by_band",
)


def checkpoint_payload(report: dict[str, Any], name: str) -> dict[str, Any]:
    """Trim a :func:`fit_links` report to what the global merge needs."""
    payload = {k: report.get(k) for k in _CHECKPOINT_COUNTERS}
    payload["batch"] = name
    for key in _CHECKPOINT_HISTOGRAMS:
        payload[key] = report.get(key, {})
    payload["extraction"] = report.get("extraction", {})
    payload["fo_invocation_failures"] = report.get("fo_invocation_failures", [])
    # Every link that passed every gate, before conflict resolution -- the merge redoes
    # that globally, so a batch's own kept/dropped split is not authoritative.
    payload["passed"] = list(report.get("ranked", [])) + list(report.get("conflicted", []))
    return payload


def fit_links_batched(
    batches: Sequence[FitBatch],
    arrows: pl.DataFrame,
    obscode_lon: dict[str, float],
    checkpoint_dir: Path,
    *,
    shell: Shell | None = None,
    workers: int = 8,
    chunk_size: int = 40,
    src_gz: Path | None = None,
    line_index: LineIndex | None = None,
    scratch_root: str | None = None,
    resume: bool = True,
    batch_progress: Callable[[int, int, dict[str, Any]], None] | None = None,
    progress: Callable[[int, int, Any], None] | None = None,
) -> list[dict[str, Any]]:
    """Fit each batch, writing its checkpoint the moment it finishes.

    A batch whose checkpoint already exists is skipped entirely when ``resume`` is set --
    so re-running the command after an interruption costs one JSON read per finished batch
    and picks up where it stopped. Inside a batch, ``fo`` chunk directories are reused by
    the same mechanism, so even the interrupted batch loses only the chunks in flight.
    """
    shell = shell or default_shell()
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    payloads: list[dict[str, Any]] = []
    for i, batch in enumerate(batches):
        path = checkpoint_dir / f"{batch.name}.json"
        if resume and path.exists():
            try:
                payloads.append(json.loads(path.read_text(encoding="utf-8")))
                if batch_progress:
                    batch_progress(i, len(batches), {"batch": batch.name, "cached": True})
                continue
            except json.JSONDecodeError:
                pass  # a half-written checkpoint is refitted, not trusted
        report = fit_links(
            batch.table, arrows, obscode_lon, batch.workroot,
            src_gz=src_gz, shell=shell, workers=workers, chunk_size=chunk_size,
            resume=True, line_index=line_index, scratch_root=scratch_root,
            progress=progress,
        )
        payload = checkpoint_payload(report, batch.name)
        path.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
        payloads.append(payload)
        if batch_progress:
            batch_progress(i, len(batches), payload)
    return payloads


def merge_checkpoints(
    payloads: Sequence[dict[str, Any]], *, gated_total: int
) -> dict[str, Any]:
    """Aggregate batch checkpoints into one funnel, resolving conflicts globally."""
    merged: dict[str, Any] = {"batches": len(payloads), "gated_total": gated_total}
    for key in _CHECKPOINT_COUNTERS:
        merged[key] = round(sum(float(p.get(key) or 0) for p in payloads), 1)
        if key != "elapsed_s":
            merged[key] = int(merged[key])
    for key in _CHECKPOINT_HISTOGRAMS:
        hist: dict[str, int] = {}
        for p in payloads:
            for k, v in (p.get(key) or {}).items():
                hist[k] = hist.get(k, 0) + int(v)
        merged[key] = dict(sorted(hist.items(), key=lambda kv: -kv[1]))
    merged["fo_invocation_failures"] = [
        f for p in payloads for f in (p.get("fo_invocation_failures") or [])
    ]
    merged["coverage_fraction"] = (
        round(merged["links_fitted"] / gated_total, 6) if gated_total else 0.0
    )
    # A link whose tracklets could not be reassembled is neither submitted nor a failure,
    # and would otherwise vanish from the funnel entirely.
    merged["links_without_astrometry"] = sum(
        int((p.get("extraction") or {}).get("links_without_astrometry") or 0) for p in payloads
    )
    merged["links_unfitted"] = max(gated_total - merged["links_fitted"], 0)

    passed = [row for p in payloads for row in (p.get("passed") or [])]
    kept, dropped = resolve_conflicts_rows(passed)
    kept = rank_survivor_rows(kept)
    merged["dropped_by_conflict_resolution"] = len(dropped)
    merged["survivors"] = len(kept)
    merged["survivors_cross_observatory"] = sum(
        1 for r in kept if len(set(r.get("obscodes") or ())) > 1
    )
    merged["survivors_same_observatory"] = merged["survivors"] - merged[
        "survivors_cross_observatory"
    ]
    merged["survivors_new_association"] = sum(
        1 for r in kept if len(set(r.get("source_desigs") or ())) > 1
    )
    merged["survivors_new_association_cross_observatory"] = sum(
        1
        for r in kept
        if len(set(r.get("source_desigs") or ())) > 1 and len(set(r.get("obscodes") or ())) > 1
    )
    merged["survivors_by_population"] = _histogram(r.get("population", "?") for r in kept)
    merged["survivors_by_band"] = _histogram(r.get("band", "?") for r in kept)
    merged["survivors_by_nights"] = _histogram(r.get("n_nights", "?") for r in kept)
    merged["survivors_neo_by_q"] = sum(1 for r in kept if r.get("is_neo_by_q"))
    merged["survivors_meeting_published_quality"] = sum(
        1 for r in kept if meets_published_quality_limits(r)
    )
    merged["ranked"] = kept
    merged["conflicted"] = dropped
    return merged


#: The MPC's published "orbit quality is sufficient" test, taken from
#: :mod:`itf_linker.fit.gates` rather than restated, and compared with the same ``>=`` the
#: gate itself uses. **Five** conditions, not four: ``e < 0.5`` is published alongside the
#: four uncertainties and was missing from this project until 2026-08-07.
#:
#: Applied to every survivor here regardless of night count. Our own gate scopes the sigmas
#: to exactly-three-night links, but that scoping is ours -- the MPC's published rule has a
#: separate bullet for links with more than 3 nights -- so a five-night link with
#: sigma(a) = 96 AU should be visible in this column rather than escape it.
QUALITY_LIMITS: dict[str, float] = {
    "sigma_a": gates.QUALITY_SIGMA_A_AU,
    "sigma_e": gates.QUALITY_SIGMA_E,
    "sigma_i": gates.QUALITY_SIGMA_I_DEG,
    "sigma_q": gates.QUALITY_SIGMA_Q_AU,
    "e": gates.MAX_ECCENTRICITY,
}


def meets_published_quality_limits(row: dict[str, Any]) -> bool:
    """Does this fit meet all five published quality conditions, whatever its night count?"""
    for key, limit in QUALITY_LIMITS.items():
        value = row.get(key)
        if value is None or value >= limit:
            return False
    return True


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
    gated, gate_report = gate_links(links, arrows.table)
    passing = gated.filter(pl.col("link_pass")) if gated.height else gated
    # Cross-observatory first: that ordering is what decides which links get fitted at all
    # when a limit is applied, and it is M3's whole strategic point.
    #
    # Changed 2026-08-07 (audit B3). This used to sort by
    # ``[band_priority, cross_observatory, cross_designation, n_nights, pos_spread_au]``
    # with nights *descending* -- M4's order. M5 section 2 measured that order as **worse
    # than a random shuffle at every depth** (0.000 against 0.127 capture in the top 10%),
    # because more nights is worse rather than better: 3-night links survived 6.7% and
    # six-night links none. ``link-fit-all`` had already moved to the fitted survival model
    # while ``m3``/``m4`` were still running the discredited order by default.
    #
    # Ordering cannot change the result of a *complete* run -- every link gets the same
    # gates whenever it is reached -- so this only affects which part of a partial run
    # exists, which is exactly what it should affect. ``fit_order``, when a caller asks for
    # it explicitly, still puts whole distance bands first; the survival model now orders
    # within them instead of the nights-descending sort.
    if passing.height:
        passing = rank_for_fitting(passing)
        if fit_order:
            passing = prioritise_bands(passing, fit_order).sort(
                ["band_priority", "fit_tier", "survival_score", "desig"],
                descending=[False, False, True, False],
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
