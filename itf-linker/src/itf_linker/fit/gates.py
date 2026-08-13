"""Two post-fit acceptance gates: ours, and the MPC's published one.

They are **not** the same rule, and until 2026-08-07 this module claimed they were. What
the MPC publishes, at
``minorplanetcenter.net/mpcops/documentation/identifications/additional/`` (the
``/submissions/`` path this module used to cite 404s), is that an ITF-to-ITF identification
is auto-rejected if:

* **before fitting** -- the format is wrong; fewer than 3 distinct nights; arc < 3 days;
  exactly 3 nights with arc > 15 days; a two-apparition linkage whose second apparition is
  a single tracklet; or the arc both starts *and* ends with a single-detection tracklet.
  Implemented in :func:`itf_linker.verify.mpec.acceptance_summary`.
* **after fitting** -- any of these three bullets:

  1. exactly 3 nights **and** arc < 15 d **and** RMS > 0.25" **and** orbit quality not sufficient
  2. more than 3 nights **and** arc < 10 d **and** RMS > 0.25" **and** orbit quality not sufficient
  3. the orbit fit did not converge

  where *orbit quality is sufficient* means sigma(a) < 0.05 AU, sigma(q) < 0.05 AU,
  sigma(i) < 0.5 deg, sigma(e) < 0.05, **and e < 0.5**.

Three things follow, and all three contradict what this file used to say:

* The first two bullets are **conjunctive**. There is no standalone RMS rule -- a converged
  fit with RMS = 3" and a long arc is not rejected by any published bullet.
* There are **five** quality conditions, not four. ``e < 0.5`` is published and was
  implemented nowhere in this project.
* The quality block is **not** scoped to exactly-three-night links. Bullet 2 is a rule for
  *more than* 3 nights. The "four-night fits are judged on RMS alone, by scope" claim that
  several write-ups build an argument on does not exist in the source.

So this module now exposes both rules and keeps them clearly separated:

:func:`post_fit_gate`
    **Ours, and the primary gate.** Deliberately stricter than published: a hard RMS
    ceiling applied unconditionally, plus the quality sigmas on three-night links. Every
    survivor count in M1-M5 is against this. Its behaviour is unchanged -- it is pinned by
    tests precisely so those published numbers stay reproducible.

:func:`mpc_published_gate`
    **Theirs, verbatim.** The conjunctive rule above, including ``e < 0.5``. Strictly more
    permissive than ours, so it is reported alongside rather than replacing: a link that
    fails our gate but passes theirs is one the MPC's filter would not reject on sight.

Passing either gate means "the MPC's automatic filter would not reject this on sight". It
does **not** mean the object is new, unreported, or a discovery: an ITF trkSub that fits
cleanly is most often a known object under a survey's internal tracking name. Establishing
otherwise needs the catalogue cross-match (MPChecker / SkyBoT / SBIDENT), which is M2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .findorb import FitResult

#: Residual ceiling. Published, but published only as one conjunct of bullets 1 and 2 --
#: :func:`post_fit_gate` applies it unconditionally, which is ours, not theirs.
MAX_RMS_ARCSEC = 0.25

#: The published "orbit quality is sufficient" test. Named for what it is: these apply to
#: any link the quality test reaches, not to three-night links specifically. The old
#: ``THREE_NIGHT_*`` names encoded the misreading described above.
QUALITY_SIGMA_A_AU = 0.05
QUALITY_SIGMA_Q_AU = 0.05
QUALITY_SIGMA_I_DEG = 0.5
QUALITY_SIGMA_E = 0.05

#: The fifth published quality condition, on the eccentricity itself rather than its
#: uncertainty. Absent from this project entirely before 2026-08-07.
MAX_ECCENTRICITY = 0.5

#: Arc ceilings from the two post-fit bullets, in days.
THREE_NIGHT_MAX_ARC_DAYS = 15.0
MANY_NIGHT_MAX_ARC_DAYS = 10.0


@dataclass(slots=True)
class GateResult:
    desig: str
    passes: bool
    reasons: list[str] = field(default_factory=list)
    n_nights: int | None = None
    rms_residual: float | None = None
    tight_sigmas_required: bool = False
    #: Which rule produced this result: ``"strict"`` (ours) or ``"mpc_published"``.
    rule: str = "strict"

    def as_dict(self) -> dict[str, Any]:
        return {
            "desig": self.desig,
            "passes": self.passes,
            "reasons": self.reasons,
            "n_nights": self.n_nights,
            "rms_residual": self.rms_residual,
            "tight_sigmas_required": self.tight_sigmas_required,
            "rule": self.rule,
        }


def orbit_quality_reasons(fit: FitResult) -> list[str]:
    """Every published quality condition this fit fails; empty means quality is sufficient.

    All five conditions, including the ``e < 0.5`` one. A missing value counts as a
    failure: an unreported uncertainty is not evidence of a small one.
    """
    reasons: list[str] = []
    for value, limit, name, unit in (
        (fit.sigma_a, QUALITY_SIGMA_A_AU, "sigma(a)", " AU"),
        (fit.sigma_q, QUALITY_SIGMA_Q_AU, "sigma(q)", " AU"),
        (fit.sigma_i, QUALITY_SIGMA_I_DEG, "sigma(i)", " deg"),
        (fit.sigma_e, QUALITY_SIGMA_E, "sigma(e)", ""),
        (fit.e, MAX_ECCENTRICITY, "e", ""),
    ):
        if value is None:
            reasons.append(f"{name} not reported")
        elif value >= limit:
            reasons.append(f"{name} {value:.4g}{unit} >= {limit}{unit}")
    return reasons


def orbit_quality_sufficient(fit: FitResult) -> bool:
    """The MPC's "orbit quality is sufficient" test, all five conditions."""
    return not orbit_quality_reasons(fit)


def post_fit_gate(fit: FitResult, n_nights: int | None = None) -> GateResult:
    """**Our** gate -- deliberately stricter than the MPC's published rule.

    Rejects on ``not converged`` OR ``RMS > 0.25"`` OR (exactly 3 nights AND any of the
    four quality sigmas fails). That differs from the published rule in three ways: the RMS
    ceiling is unconditional where the MPC applies it only as one conjunct; the sigma block
    is scoped to three-night links where the MPC scopes it by arc length; and ``e < 0.5``
    is not applied at all. See :func:`mpc_published_gate` for the published rule.

    The net direction is conservative -- this rejects a superset of what the MPC would --
    so nothing was ever wrongly promoted by it. **Behaviour is intentionally frozen**: every
    pass rate in M1-M5 is against this rule, and changing it would silently invalidate them.

    ``n_nights`` selects whether the tighter sigma limits apply. It is the caller's count of
    *distinct local nights*, not anything Find_Orb reports.
    """
    reasons: list[str] = []
    tight = n_nights == 3

    if not fit.converged:
        reasons.append(f"non-convergence ({fit.status})")

    if fit.rms_residual is None:
        reasons.append("no residual RMS reported")
    elif fit.rms_residual > MAX_RMS_ARCSEC:
        reasons.append(f'RMS {fit.rms_residual:.3f}" > {MAX_RMS_ARCSEC}"')

    if tight:
        for value, limit, name, unit in (
            (fit.sigma_a, QUALITY_SIGMA_A_AU, "sigma(a)", " AU"),
            (fit.sigma_q, QUALITY_SIGMA_Q_AU, "sigma(q)", " AU"),
            (fit.sigma_i, QUALITY_SIGMA_I_DEG, "sigma(i)", " deg"),
            (fit.sigma_e, QUALITY_SIGMA_E, "sigma(e)", ""),
        ):
            if value is None:
                reasons.append(f"{name} not reported (3-night link)")
            elif value >= limit:
                reasons.append(f"{name} {value:.4g}{unit} >= {limit}{unit} (3-night link)")

    return GateResult(
        desig=fit.desig,
        passes=not reasons,
        reasons=reasons,
        n_nights=n_nights,
        rms_residual=fit.rms_residual,
        tight_sigmas_required=tight,
        rule="strict",
    )


def mpc_published_gate(
    fit: FitResult, n_nights: int | None = None, arc_days: float | None = None
) -> GateResult:
    """The MPC's published post-fit rule, verbatim and conjunctive.

    Rejects only if the fit did not converge, or if *every* conjunct of the applicable
    arc-length bullet holds. A converged fit with RMS <= 0.25" is never quality-tested at
    all, and neither is one whose arc exceeds the bullet's ceiling.

    ``arc_days`` is the arc covered by the *tracklets* -- the caller's submitted arc, not
    the fitted arc, since that is what the MPC's pre-fit checks measure. When it is unknown
    the arc conjunct cannot be evaluated; rather than assume it, the bullet is treated as
    applicable (the conservative direction) and the reason says so.
    """
    if not fit.converged:
        return GateResult(
            desig=fit.desig,
            passes=False,
            reasons=[f"non-convergence ({fit.status})"],
            n_nights=n_nights,
            rms_residual=fit.rms_residual,
            rule="mpc_published",
        )

    if n_nights is None or n_nights < 3:
        # Fewer than 3 nights never reaches a post-fit bullet; it is a pre-fit reject.
        max_arc = THREE_NIGHT_MAX_ARC_DAYS
    else:
        max_arc = THREE_NIGHT_MAX_ARC_DAYS if n_nights == 3 else MANY_NIGHT_MAX_ARC_DAYS

    arc_unknown = arc_days is None
    arc_within = arc_unknown or arc_days < max_arc
    rms_high = fit.rms_residual is None or fit.rms_residual > MAX_RMS_ARCSEC
    quality_reasons = orbit_quality_reasons(fit)

    if arc_within and rms_high and quality_reasons:
        detail = "arc unknown" if arc_unknown else f"arc {arc_days:.3g} d < {max_arc} d"
        rms_detail = (
            "no residual RMS reported"
            if fit.rms_residual is None
            else f'RMS {fit.rms_residual:.3f}" > {MAX_RMS_ARCSEC}"'
        )
        nights_detail = "3 nights" if n_nights == 3 else f"{n_nights} nights"
        return GateResult(
            desig=fit.desig,
            passes=False,
            reasons=[
                (
                    f"{nights_detail} and {detail} and {rms_detail} and "
                    f"orbit quality not sufficient ({'; '.join(quality_reasons)})"
                )
            ],
            n_nights=n_nights,
            rms_residual=fit.rms_residual,
            rule="mpc_published",
        )

    return GateResult(
        desig=fit.desig,
        passes=True,
        reasons=[],
        n_nights=n_nights,
        rms_residual=fit.rms_residual,
        rule="mpc_published",
    )
