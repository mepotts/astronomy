"""Turn a pile of service replies into one identification decision, conservatively.

The whole design rests on one idea, borrowed from the guard that M1 found actually worked:
**one explanation must cover the whole arc.** M1 credited an orbit only if Find_Orb used
>=80% of the observations and the used subset still spanned three nights, because a name
collision can otherwise produce a perfectly respectable RMS on a subset. The same failure
mode exists here in a different costume: in a Rubin field there are roughly three catalogued
objects brighter than V=25 within 5 arcminutes, so a *single-epoch* coincidence at tens of
arcseconds is an ordinary event, not evidence.

So an identification is credited when one catalogue object sits near the candidate **at two
or more separate epochs**. A known asteroid that happens to be 40" away on one night is
somewhere else entirely a week later; the same object being 40" away on three nights spread
over eleven days means the two are moving together, and there is only one reason for that.

The asymmetry in the other direction is deliberate and is the point of the module:

* a match is only ever "known", never "confirmed new";
* a non-match is **never** upgraded to "new object". It is ``unmatched``, and
  :attr:`VetVerdict.unmatched_reason` records which of the three innocent explanations --
  epoch outside the service's coverage, an orbit too loose to have been matched, or a
  genuine absence from the catalogues -- could be established. A candidate that survives
  everything is a candidate for further work.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .types import (
    ElementComparison,
    ServiceMatch,
    ServiceReport,
    VetCandidate,
    VetVerdict,
)

#: How close a catalogue object has to be to *identify* an ordinary minor planet.
#:
#: Calibrated on the controls, where the right answer was known in advance. Three numbered
#: minor planets, positions from JPL Horizons, vetted through this same classifier:
#:
#:     (588) Achilles   0.26"  0.40"  1.06"   (MPChecker)   2.09"  2.19"  2.21"  (SkyBoT)
#:     (7)   Iris       0.89"  1.47"  1.63"                 2.53"  2.53"  2.53"
#:     (433) Eros       1.99"  2.10"  2.58"                 3.26"  3.27"  3.28"
#:
#: A real identification lands inside 3.5" and stays there. 30" is therefore very generous
#: -- about ten times the observed scale -- which is deliberate: a recently-discovered
#: object with a one-opposition orbit has a much worse ephemeris than these four-plus
#: opposition standards.
MATCH_ARCSEC = 30.0

#: The same question for a comet, where the answer is genuinely different.
#:
#: The ITF's own ``0073P-C`` -- M1's positive control -- sits **32.8", 75.2" and 118.3"**
#: from catalogue 73P-C on three nights across 27 days. That is not sloppiness: comets
#: carry non-gravitational accelerations that a gravity-only ephemeris does not model, and
#: 73P was actively disintegrating in April-May 2006, when this astrometry was taken. A
#: 30" radius reports a known comet as unmatched. The widened radius is applied only to
#: objects the SBDB calls a comet (``kind`` starting with ``c``), never by default.
COMET_MATCH_ARCSEC = 150.0

#: Matches are *recorded* out to here, whether or not they are credited, so the evidence
#: trail shows what was nearby. Set equal to the comet radius: nothing beyond it can be
#: credited under any rule, so recording further costs SBDB lookups for no benefit.
CONSIDER_ARCSEC = 150.0

#: One epoch this close is not an identification, but it *is* worth a human's attention:
#: the candidate lands where a catalogue object also is, and only the other nights say
#: otherwise. These become ``ambiguous``.
NEAR_MISS_ARCSEC = 30.0

#: When a candidate has only one epoch to offer, this alone credits it. At 5" the
#: coincidence rate in the densest field this project sees is ~0.08%.
SINGLE_EPOCH_ARCSEC = 5.0

#: Epochs that must independently agree before an identification is credited.
MIN_EPOCHS_FOR_MATCH = 2


def considered(match: ServiceMatch) -> bool:
    """Is this match close enough to be recorded as evidence at all?

    There is deliberately **no** widening by the service's own quoted ephemeris
    uncertainty. An earlier version accepted anything inside three times SkyBoT's ``Err``
    column, on the reasoning that a badly-determined catalogue orbit should not be allowed
    to hide its own object. Measured against the real population, that reasoning is wrong
    in the only way that matters: it admitted ``2022 QB161`` at **273"** as a three-epoch
    "match" for ``RL00iMW``, purely because the quoted error was large. A catalogue object
    four arcminutes away is not the candidate whatever its error bar says.
    """
    return match.sep_arcsec is not None and match.sep_arcsec <= CONSIDER_ARCSEC


def match_radius(kind: str | None) -> float:
    """The identification radius appropriate to an object's class."""
    return COMET_MATCH_ARCSEC if (kind or "").lower().startswith("c") else MATCH_ARCSEC


def _identity_table(services: dict[str, ServiceReport]) -> dict[str, dict[str, Any]]:
    """Collapse every considered match into one row per catalogue identity."""
    table: dict[str, dict[str, Any]] = {}
    for report in services.values():
        for match in report.matches:
            if not considered(match):
                continue
            row = table.setdefault(
                match.identity,
                {
                    "identity": match.identity,
                    "resolved_des": match.resolved_des,
                    "fullname": match.fullname,
                    "kind": match.kind,
                    "orbit_class": match.orbit_class,
                    "epochs": set(),
                    "services": set(),
                    "seps": [],
                    "by_epoch": [],       # (obs_index, sep) so the two stay paired
                },
            )
            row["epochs"].add(match.obs_index)
            row["services"].add(match.service)
            row["seps"].append(match.sep_arcsec)
            row["by_epoch"].append((match.obs_index, match.sep_arcsec))
            row["resolved_des"] = row["resolved_des"] or match.resolved_des
            row["fullname"] = row["fullname"] or match.fullname
            row["kind"] = row["kind"] or match.kind
    # Epochs where the object was actually *at* the candidate, as opposed to merely in the
    # same part of the sky. This is what the multi-epoch rule counts, and the distinction
    # is the whole lesson of the first pass: a main-belt neighbour moves at nearly the
    # candidate's own rate, so it stays inside a couple of arcminutes for days on end.
    # ``2018 EC25`` tracked ``RL00adt`` at 16" and then 80" two nights later -- present at
    # two epochs, at the candidate's position at neither.
    for row in table.values():
        row["radius"] = match_radius(row["kind"])
        row["matched_epochs"] = {i for i, sep in row["by_epoch"] if sep <= row["radius"]}
    return table


def _rank_key(row: dict[str, Any]) -> tuple[int, int, int, float]:
    return (
        len(row["matched_epochs"]),
        len(row["epochs"]),
        len(row["services"]),
        -min(row["seps"]),
    )


def classify(
    candidate: VetCandidate,
    services: dict[str, ServiceReport],
    *,
    element_comparison: ElementComparison | None = None,
    coverage_notes: dict[str, str] | None = None,
) -> VetVerdict:
    """Decide one candidate's category from the evidence collected for it."""
    coverage_notes = coverage_notes or {}
    epochs_queried = sorted(
        {i for r in services.values() for i in r.epochs_queried}
    )
    answering = [r for r in services.values() if r.ok]

    verdict = VetVerdict(
        desig=candidate.desig,
        category="service_failed",
        origin=candidate.origin,
        n_epochs_queried=len(epochs_queried),
        services=services,
    )

    if not answering:
        verdict.reasons.append(
            "no vetting service returned a usable answer; identification not attempted"
        )
        for name, report in services.items():
            if report.skipped:
                verdict.reasons.append(f"{name}: skipped ({report.skipped})")
            for err in report.errors[:2]:
                verdict.reasons.append(f"{name}: {err}")
        return verdict

    table = _identity_table(services)
    verdict.candidates_considered = sorted(
        (
            {
                "identity": row["identity"],
                "resolved_des": row["resolved_des"],
                "fullname": row["fullname"],
                "kind": row["kind"],
                "epochs_seen": len(row["epochs"]),
                "epochs_matched": len(row["matched_epochs"]),
                "match_radius_arcsec": row["radius"],
                "services": sorted(row["services"]),
                "min_sep_arcsec": round(min(row["seps"]), 3),
                "max_sep_arcsec": round(max(row["seps"]), 3),
            }
            for row in table.values()
        ),
        key=lambda r: (-r["epochs_matched"], r["min_sep_arcsec"]),
    )

    if not table:
        verdict.category = "unmatched"
        verdict.unmatched_reason, why = _why_unmatched(candidate, services, coverage_notes)
        verdict.reasons.append(why)
        verdict.reasons.append(
            f"no catalogue object within {CONSIDER_ARCSEC:.0f}\" at any of "
            f"{len(epochs_queried)} queried epoch(s), from "
            f"{', '.join(sorted(r.service for r in answering))}"
        )
        return verdict

    ranked = sorted(table.values(), key=_rank_key, reverse=True)
    single_epoch_run = len(epochs_queried) <= 1

    # Credited: one catalogue object was *at* the candidate on two separate nights (or, when
    # only one night existed, was very close on it). Near miss: it was at the candidate on
    # one night only -- suggestive, and a human should see it, but the other nights say no.
    credited = [
        r for r in ranked
        if len(r["matched_epochs"]) >= MIN_EPOCHS_FOR_MATCH
        or (single_epoch_run and min(r["seps"]) <= SINGLE_EPOCH_ARCSEC)
    ]
    near_misses = [
        r for r in ranked if r not in credited and min(r["seps"]) <= NEAR_MISS_ARCSEC
    ]

    if not credited and not near_misses:
        verdict.category = "unmatched"
        verdict.unmatched_reason, why = _why_unmatched(candidate, services, coverage_notes)
        verdict.reasons.append(why)
        closest = min(ranked, key=lambda r: min(r["seps"]))
        verdict.reasons.append(
            f"closest catalogue object was {closest['identity']} at "
            f"{min(closest['seps']):.1f}\", outside the {NEAR_MISS_ARCSEC:.0f}\" near-miss "
            "radius -- a neighbour at that distance is what an empty field looks like in a "
            "crowded survey, not an identification"
        )
        return verdict

    best = (credited or near_misses)[0]
    verdict.identified_as = best["resolved_des"] or best["identity"]
    verdict.identified_fullname = best["fullname"]
    verdict.n_services_agreeing = len(best["services"])
    verdict.n_epochs_matched = len(best["matched_epochs"])
    verdict.best_sep_arcsec = round(min(best["seps"]), 3)
    verdict.worst_sep_arcsec = round(max(best["seps"]), 3)
    verdict.element_comparison = element_comparison

    if len(credited) >= 2:
        verdict.category = "ambiguous"
        verdict.reasons.append(
            f"{len(credited)} catalogue objects each explain the arc: "
            + ", ".join(r["identity"] for r in credited)
        )
    elif len(credited) == 1 and not single_epoch_run:
        verdict.category = "known"
        verdict.reasons.append(
            f"{verdict.identified_as} is within {best['radius']:.0f}\" of the candidate at "
            f"{verdict.n_epochs_matched} of {len(epochs_queried)} epochs "
            f"({verdict.best_sep_arcsec}\"-{verdict.worst_sep_arcsec}\"; services: "
            f"{', '.join(sorted(best['services']))})"
        )
    elif len(credited) == 1:
        verdict.category = "known"
        verdict.reasons.append(
            f"{verdict.identified_as} matches the only queried epoch at "
            f"{verdict.best_sep_arcsec}\", inside the {SINGLE_EPOCH_ARCSEC}\" single-epoch limit"
        )
    else:
        verdict.category = "ambiguous"
        verdict.reasons.append(
            f"{verdict.identified_as} is {verdict.best_sep_arcsec}\" away at "
            f"{verdict.n_epochs_matched} of {len(epochs_queried)} epochs and further at the "
            f"rest (out to {verdict.worst_sep_arcsec}\") -- close enough to need a human "
            f"look, not enough to identify (needs {MIN_EPOCHS_FOR_MATCH} epochs inside "
            f"{best['radius']:.0f}\")"
        )

    if best["resolved_des"] is None:
        verdict.reasons.append(
            f"identity {best['identity']!r} could not be resolved in the SBDB; "
            "reported as the service named it"
        )
    if element_comparison is not None and element_comparison.consistent is False:
        verdict.reasons.append(
            "positional match but the fitted and catalogue orbits differ by more than "
            f"tolerance ({element_comparison.note})"
        )
        if verdict.category == "known":
            verdict.category = "ambiguous"
    return verdict


def _why_unmatched(
    candidate: VetCandidate,
    services: dict[str, ServiceReport],
    coverage_notes: dict[str, str],
) -> tuple[str, str]:
    """Pick the weakest claim the evidence supports, not the most exciting one."""
    if coverage_notes:
        joined = "; ".join(f"{k}: {v}" for k, v in sorted(coverage_notes.items()))
        answering = {name for name, r in services.items() if r.ok}
        if answering and answering <= set(coverage_notes):
            return "epoch_outside_service_coverage", (
                "every service that answered has a known coverage gap at this epoch -- "
                f"{joined}"
            )
    if candidate.elements is not None and not candidate.elements.well_constrained:
        sig = candidate.elements.sigma_a
        return "orbit_too_poorly_constrained", (
            f"the fitted orbit's scale is undetermined (sigma(a) = {sig}); a non-match "
            "carries no information about whether the object is known"
        )
    return "no_catalogue_object_near_astrometry", (
        "no catalogue object near the astrometry, at any queried epoch, from any service "
        "that answered -- this means unmatched, NOT new"
    )


def tally(verdicts: list[VetVerdict]) -> dict[str, Any]:
    """Counts by category, plus the breakdown of *why* the unmatched were unmatched."""
    by_category: dict[str, int] = defaultdict(int)
    by_reason: dict[str, int] = defaultdict(int)
    for v in verdicts:
        by_category[v.category] += 1
        if v.category == "unmatched" and v.unmatched_reason:
            by_reason[v.unmatched_reason] += 1
    return {
        "n": len(verdicts),
        "by_category": dict(sorted(by_category.items())),
        "unmatched_reasons": dict(sorted(by_reason.items())),
    }
