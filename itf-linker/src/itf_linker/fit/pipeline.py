"""The M1 pipeline: from a parsed ITF snapshot to a ranked list of orbit fits.

    observations
      -> bad-data filter            candidates.bad_data_filter
      -> tracklets, per designation index.tracklets + candidates.per_designation
      -> keep 3+ nights
      -> MPC published pre-fit gate  candidates.prefit_gate
      -> trkSub collision screen     collide.screen
      -> original 80-column lines    extract.extract_lines
      -> Find_Orb                    findorb.run_fo_batched
      -> MPC published post-fit gate gates.post_fit_gate + collide.post_fit_collision_check

**What comes out of this is a list of designations with acceptable orbit fits. It is not a
list of discoveries.** A trkSub that fits cleanly is, most often, a known object under a
survey's internal tracking name. Deciding otherwise requires a catalogue cross-match
against MPChecker / SkyBoT / JPL SBIDENT, which is M2 and is deliberately not done here.
Nothing in this module -- or anywhere in this package -- submits anything anywhere.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from ..index.tracklets import add_night, build_tracklets
from . import collide
from .candidates import bad_data_filter, gate_summary, per_designation, prefit_gate
from .extract import extract_lines
from .findorb import FitResult, run_fo_batched
from .gates import post_fit_gate
from .wsl import Shell, default_shell


@dataclass
class CandidateSet:
    """The designations selected for fitting, and the funnel that produced them."""

    table: pl.DataFrame                       # one row per surviving designation
    screened: pl.DataFrame                    # every 3+-night designation, with flags
    report: dict[str, Any] = field(default_factory=dict)

    @property
    def designations(self) -> list[str]:
        return self.table["desig"].to_list()


def select_candidates(
    observations: pl.DataFrame,
    obscode_lon: dict[str, float] | None = None,
    *,
    min_nights: int = 3,
) -> CandidateSet:
    """Run the whole pre-fit funnel and return both the survivors and the audit trail."""
    filtered, filter_stats = bad_data_filter(observations.lazy())
    with_night = add_night(filtered, obscode_lon or {})
    tracklets = build_tracklets(with_night).collect()

    per_desig = per_designation(tracklets)
    multi = per_desig.filter(pl.col("n_nights") >= min_nights)
    gated = prefit_gate(multi)
    passing = gated.filter(pl.col("prefit_pass"))

    motion = collide.tracklet_motion(tracklets.filter(pl.col("desig").is_in(set(multi["desig"]))))
    screened = collide.screen(gated, motion)
    survivors = screened.filter(pl.col("prefit_pass") & ~pl.col("collision_suspect"))

    report = {
        "bad_data_filter": filter_stats,
        "tracklets": tracklets.height,
        "designations": per_desig.height,
        "designations_by_nights": {
            "1": int((per_desig["n_nights"] == 1).sum()),
            "2": int((per_desig["n_nights"] == 2).sum()),
            "3+": int((per_desig["n_nights"] >= 3).sum()),
        },
        "prefit_gate": gate_summary(gated),
        "collision_screen": collide.screen_summary(
            screened.filter(pl.col("prefit_pass"))
        ),
        "collision_screen_all_multinight": collide.screen_summary(screened),
        "candidates": survivors.height,
        "funnel": {
            "designations_3plus_nights": multi.height,
            "after_prefit_gate": passing.height,
            "after_collision_screen": survivors.height,
        },
    }
    return CandidateSet(table=survivors, screened=screened, report=report)


@dataclass
class FitOutcome:
    """One designation's fit plus every gate applied to it."""

    desig: str
    fit: FitResult
    n_nights: int
    n_obs_submitted: int
    prefit_arc_days: float
    obscodes: list[str]
    gate_passes: bool
    gate_reasons: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "desig": self.desig,
            "n_nights": self.n_nights,
            "n_obs_submitted": self.n_obs_submitted,
            "prefit_arc_days": self.prefit_arc_days,
            "obscodes": self.obscodes,
            "gate_passes": self.gate_passes,
            "gate_reasons": self.gate_reasons,
            **{k: v for k, v in self.fit.as_dict().items() if k != "desig"},
        }


def _used_nights(fit: FitResult) -> int | None:
    """Distinct UTC dates among the observations Find_Orb actually kept.

    Deliberately UTC dates and not local nights: this is a *floor* on the night count of
    the used subset, and a floor is what the collision guard needs.
    """
    if not fit.residuals:
        return None
    dates = {
        str(r.get("iso date", ""))[:10]
        for r in fit.residuals
        if r.get("incl", 1) and r.get("iso date")
    }
    return len(dates) or None


def fit_candidates(
    candidates: CandidateSet,
    workroot: Path,
    *,
    src_gz: Path | None = None,
    shell: Shell | None = None,
    workers: int = 8,
    chunk_size: int = 48,
    limit: int | None = None,
    progress: Callable[[int, int, Any], None] | None = None,
) -> dict[str, Any]:
    """Extract each candidate's original astrometry, fit it, and gate the result."""
    shell = shell or default_shell()
    table = candidates.table.head(limit) if limit else candidates.table
    desigs = table["desig"].to_list()

    groups, extract_stats = extract_lines(desigs, src=src_gz)
    fittable = {d: lines for d, lines in groups.items() if lines}
    missing = sorted(set(desigs) - set(fittable))

    diagnostics: list[dict[str, Any]] = []
    results = run_fo_batched(
        fittable, workroot, shell=shell, workers=workers,
        chunk_size=chunk_size, progress=progress, diagnostics=diagnostics,
    )
    # Designations Find_Orb returned under a name that could not be mapped back. Reported
    # rather than dropped: a silent renaming would look identical to a failed fit.
    unmatched = sorted(set(results) - set(desigs))

    meta = {r["desig"]: r for r in table.to_dicts()}
    outcomes: list[FitOutcome] = []
    for desig in desigs:
        fit = results.get(desig) or FitResult(desig=desig, status="not_extracted")
        info = meta[desig]
        gate = post_fit_gate(fit, n_nights=int(info["n_nights"]))
        ok, reasons = collide.post_fit_collision_check(
            fit.n_obs, fit.n_used, used_nights=_used_nights(fit)
        )
        outcomes.append(
            FitOutcome(
                desig=desig,
                fit=fit,
                n_nights=int(info["n_nights"]),
                n_obs_submitted=len(fittable.get(desig, [])),
                prefit_arc_days=float(info["arc_days"]),
                obscodes=list(info["obscodes"]),
                gate_passes=gate.passes and ok,
                gate_reasons=gate.reasons + reasons,
            )
        )

    converged = [o for o in outcomes if o.fit.converged]
    passed = [o for o in outcomes if o.gate_passes]
    rms_ok = [o for o in converged if (o.fit.rms_residual or 9e9) <= 0.25]

    def _count(pred: Callable[[FitOutcome], bool]) -> int:
        return sum(1 for o in outcomes if pred(o))

    return {
        "extraction": extract_stats,
        "designations_submitted": len(desigs),
        "designations_without_astrometry": missing,
        "fo_invocation_failures": diagnostics,
        "results_not_matched_to_a_designation": unmatched,
        "converged": len(converged),
        "not_converged": len(outcomes) - len(converged),
        "not_converged_reasons": _status_histogram(outcomes),
        "rms_le_0.25": len(rms_ok),
        "rms_gt_0.25": len(converged) - len(rms_ok),
        "failed_subset_guard": _count(
            lambda o: o.fit.converged
            and not collide.post_fit_collision_check(
                o.fit.n_obs, o.fit.n_used, _used_nights(o.fit)
            )[0]
        ),
        "three_night_sigma_gate": _sigma_gate_counts(outcomes),
        "passed_all_gates": len(passed),
        "ranked": [o.as_dict() for o in rank(passed)],
        "outcomes": [o.as_dict() for o in outcomes],
    }


def rank(outcomes: list[FitOutcome]) -> list[FitOutcome]:
    """Order surviving fits best-first: lowest RMS, then tightest sigma(a), then longest arc.

    Ranking is *not* a second gate. In particular the MPC's sigma limits apply only to
    three-night links, so a four-night fit with sigma(a) = 784 AU passes the published
    criteria untouched; it sorts to the bottom here rather than being quietly dropped,
    because the criteria are the MPC's and the ordering is ours.
    """
    return sorted(
        outcomes,
        key=lambda o: (
            o.fit.rms_residual if o.fit.rms_residual is not None else 9e9,
            o.fit.sigma_a if o.fit.sigma_a is not None else 9e9,
            -(o.fit.arc_days or 0.0),
        ),
    )


def _status_histogram(outcomes: list[FitOutcome]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for o in outcomes:
        if not o.fit.converged:
            hist[o.fit.status] = hist.get(o.fit.status, 0) + 1
    return dict(sorted(hist.items(), key=lambda kv: -kv[1]))


def _sigma_gate_counts(outcomes: list[FitOutcome]) -> dict[str, int]:
    """How the tighter three-night sigma limits behave, separately from everything else."""
    three = [o for o in outcomes if o.n_nights == 3 and o.fit.converged]
    from .gates import (
        THREE_NIGHT_SIGMA_A_AU,
        THREE_NIGHT_SIGMA_E,
        THREE_NIGHT_SIGMA_I_DEG,
        THREE_NIGHT_SIGMA_Q_AU,
    )

    def ok(value: float | None, limit: float) -> bool:
        return value is not None and value < limit

    return {
        "three_night_converged": len(three),
        "sigma_a_ok": sum(1 for o in three if ok(o.fit.sigma_a, THREE_NIGHT_SIGMA_A_AU)),
        "sigma_q_ok": sum(1 for o in three if ok(o.fit.sigma_q, THREE_NIGHT_SIGMA_Q_AU)),
        "sigma_i_ok": sum(1 for o in three if ok(o.fit.sigma_i, THREE_NIGHT_SIGMA_I_DEG)),
        "sigma_e_ok": sum(1 for o in three if ok(o.fit.sigma_e, THREE_NIGHT_SIGMA_E)),
        "all_four_ok": sum(
            1
            for o in three
            if ok(o.fit.sigma_a, THREE_NIGHT_SIGMA_A_AU)
            and ok(o.fit.sigma_q, THREE_NIGHT_SIGMA_Q_AU)
            and ok(o.fit.sigma_i, THREE_NIGHT_SIGMA_I_DEG)
            and ok(o.fit.sigma_e, THREE_NIGHT_SIGMA_E)
        ),
        "more_than_three_nights": sum(1 for o in outcomes if o.n_nights > 3),
    }
