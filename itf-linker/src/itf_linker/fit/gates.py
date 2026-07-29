"""The MPC's *published* post-fit acceptance criteria, and nothing more.

From ``minorplanetcenter.net/mpcops/submissions/identifications/additional/`` (quoted in
``DISCOVERY/itf-linker.md``), an ITF-to-ITF link is auto-rejected if:

* **before fitting** -- fewer than 3 distinct nights; arc < 3 days; exactly 3 nights with
  arc > 15 days; or the arc both starts *and* ends with a single-detection tracklet.
  Implemented in :func:`itf_linker.verify.mpec.acceptance_summary`.
* **after fitting** -- residual RMS > 0.25", or non-convergence.
* **three-night links only** -- additionally sigma(a) < 0.05 AU, sigma(q) < 0.05 AU,
  sigma(i) < 0.5 deg, sigma(e) < 0.05.

Passing these gates means "the MPC's automatic filter would not reject this on sight". It
does **not** mean the object is new, unreported, or a discovery: an ITF trkSub that fits
cleanly is most often a known object under a survey's internal tracking name. Establishing
otherwise needs the catalogue cross-match (MPChecker / SkyBoT / SBIDENT), which is M2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .findorb import FitResult

#: Post-fit thresholds, exactly as published. Named so a diff shows any drift.
MAX_RMS_ARCSEC = 0.25
THREE_NIGHT_SIGMA_A_AU = 0.05
THREE_NIGHT_SIGMA_Q_AU = 0.05
THREE_NIGHT_SIGMA_I_DEG = 0.5
THREE_NIGHT_SIGMA_E = 0.05


@dataclass(slots=True)
class GateResult:
    desig: str
    passes: bool
    reasons: list[str] = field(default_factory=list)
    n_nights: int | None = None
    rms_residual: float | None = None
    tight_sigmas_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "desig": self.desig,
            "passes": self.passes,
            "reasons": self.reasons,
            "n_nights": self.n_nights,
            "rms_residual": self.rms_residual,
            "tight_sigmas_required": self.tight_sigmas_required,
        }


def post_fit_gate(fit: FitResult, n_nights: int | None = None) -> GateResult:
    """Apply the published post-fit criteria to one solution.

    ``n_nights`` selects whether the tighter three-night sigma limits apply. It is the
    caller's count of *distinct local nights*, not anything Find_Orb reports.
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
            (fit.sigma_a, THREE_NIGHT_SIGMA_A_AU, "sigma(a)", " AU"),
            (fit.sigma_q, THREE_NIGHT_SIGMA_Q_AU, "sigma(q)", " AU"),
            (fit.sigma_i, THREE_NIGHT_SIGMA_I_DEG, "sigma(i)", " deg"),
            (fit.sigma_e, THREE_NIGHT_SIGMA_E, "sigma(e)", ""),
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
    )
