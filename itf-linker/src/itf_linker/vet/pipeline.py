"""Orchestration: which service is asked what, in what order, and how little.

The query plan is not uniform across services, and the asymmetry is a load decision made
from measurements rather than a guess:

============  ==========  =========================================================
service       cost/query  used for
============  ==========  =========================================================
SkyBoT        ~1-2 s      **every** selected epoch of every candidate -- the sweep
MPChecker     ~5 s        **every** selected epoch -- the MPC's own catalogue
SBIDENT       ~35-240 s   **escalation only**: candidates the first two leave
                          unresolved, plus every control
SBDB          <1 s        each distinct identity, once, memoised across the run
============  ==========  =========================================================

Running SBIDENT over everything would mean 100+ CPU-minutes of numerical integration on
JPL's hardware to re-confirm answers two other services already agreed on. Running it on
exactly the cases that are still open costs a fraction of that and is where its independent
opinion is actually worth something.

Epochs are chosen one per night, spread across the arc, capped at
:data:`DEFAULT_MAX_EPOCHS`. One per night is the right unit because the multi-epoch test in
:mod:`itf_linker.vet.verdict` is only meaningful across nights -- two detections half an
hour apart are not independent evidence that a catalogue object is moving with the
candidate.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import Any

from . import mpchecker, sbdb, sbident, skybot
from .cache import CachedSession, ServiceUnavailable
from .sbdb import SbdbObject
from .types import (
    ServiceMatch,
    ServiceReport,
    VetCandidate,
    VetObservation,
    VetVerdict,
)
from .verdict import classify, tally

#: Nights sampled per candidate. Three is the smallest number that lets the multi-epoch
#: rule fail informatively (2 of 3 matched is a different statement from 2 of 2).
DEFAULT_MAX_EPOCHS = 3
#: Cone radius, shared by all three positional services so their answers are comparable.
SEARCH_RADIUS_ARCSEC = 300.0
#: Faint limit for MPChecker. Rubin reaches V~24.5; the MPC's own advice is to set the
#: limit at least a magnitude fainter than the telescope's.
MPCHECKER_LIMIT_MAG = 25.0


def select_epochs(
    candidate: VetCandidate, max_epochs: int = DEFAULT_MAX_EPOCHS
) -> list[tuple[int, VetObservation]]:
    """One observation per night, spread evenly over the arc, at most ``max_epochs``."""
    by_night: dict[int, tuple[int, VetObservation]] = {}
    for idx, obs in enumerate(candidate.observations):
        night = obs.night if obs.night is not None else int(obs.mjd_utc)
        if night not in by_night or obs.mjd_utc < by_night[night][1].mjd_utc:
            by_night[night] = (idx, obs)
    nights = sorted(by_night)
    if len(nights) <= max_epochs:
        picked = nights
    else:
        # First and last always; the rest spread evenly between them.
        step = (len(nights) - 1) / (max_epochs - 1)
        picked = sorted({nights[round(i * step)] for i in range(max_epochs)})
    return [by_night[n] for n in picked]


def _run_positional(
    session: CachedSession,
    service: str,
    epochs: Sequence[tuple[int, VetObservation]],
    runner: Callable[[int, VetObservation], tuple[list[ServiceMatch], str | None]],
) -> ServiceReport:
    report = ServiceReport(service=service)
    if service in session.disabled:
        report.skipped = session.disabled[service]
        return report
    for idx, obs in epochs:
        report.epochs_queried.append(idx)
        report.queries += 1
        try:
            matches, error = runner(idx, obs)
        except ServiceUnavailable as exc:
            report.errors.append(str(exc))
            break
        if error:
            report.errors.append(f"mjd {obs.mjd_utc:.5f}: {error}")
            continue
        report.epochs_answered.append(idx)
        report.matches.extend(matches)
    return report


def _skybot_report(
    session: CachedSession, epochs: Sequence[tuple[int, VetObservation]]
) -> ServiceReport:
    def run(idx: int, obs: VetObservation) -> tuple[list[ServiceMatch], str | None]:
        if not skybot.covers(obs.jd_utc):
            return [], "epoch outside SkyBoT's 1889-2060 coverage"
        return skybot.cone_search(
            session,
            ra_deg=obs.ra_deg, dec_deg=obs.dec_deg, jd_utc=obs.jd_utc,
            obscode=obs.obscode, radius_deg=SEARCH_RADIUS_ARCSEC / 3600.0,
            obs_index=idx, mjd_utc=obs.mjd_utc,
        )

    return _run_positional(session, skybot.SERVICE, epochs, run)


def _mpchecker_report(
    session: CachedSession, epochs: Sequence[tuple[int, VetObservation]]
) -> tuple[ServiceReport, dict[str, str]]:
    coverage: dict[str, str] = {}

    def run(idx: int, obs: VetObservation) -> tuple[list[ServiceMatch], str | None]:
        year, month, day = _calendar(obs.mjd_utc)
        gap = mpchecker.coverage_gap(year)
        if gap:
            coverage[mpchecker.SERVICE] = gap
        return mpchecker.check_position(
            session,
            year=year, month=month, day=day,
            ra_deg=obs.ra_deg, dec_deg=obs.dec_deg, obscode=obs.obscode,
            radius_arcmin=SEARCH_RADIUS_ARCSEC / 60.0,
            limit_mag=MPCHECKER_LIMIT_MAG,
            obs_index=idx, mjd_utc=obs.mjd_utc,
        )

    return _run_positional(session, mpchecker.SERVICE, epochs, run), coverage


def _sbident_report(
    session: CachedSession,
    epochs: Sequence[tuple[int, VetObservation]],
    *,
    timeout: float,
) -> ServiceReport:
    first_pass_counts: list[int] = []

    def run(idx: int, obs: VetObservation) -> tuple[list[ServiceMatch], str | None]:
        stale = sbident.too_old(obs.jd_utc)
        if stale:
            return [], stale
        matches, error, n_first = sbident.identify(
            session,
            ra_deg=obs.ra_deg, dec_deg=obs.dec_deg, jd_utc=obs.jd_utc,
            obscode=obs.obscode, hwidth_deg=SEARCH_RADIUS_ARCSEC / 3600.0,
            obs_index=idx, mjd_utc=obs.mjd_utc, timeout=timeout,
        )
        if n_first is not None:
            first_pass_counts.append(n_first)
        return matches, error

    report = _run_positional(session, sbident.SERVICE, epochs, run)
    if first_pass_counts:
        report.errors.extend(
            f"first pass returned {n} rows (budget {sbident.FIRST_PASS_BUDGET})"
            for n in first_pass_counts
            if n > sbident.FIRST_PASS_BUDGET
        )
    return report


def _calendar(mjd: float) -> tuple[int, int, float]:
    """MJD -> (year, month, fractional day), inverting ``mpc80.gregorian_to_mjd``."""
    jd = mjd + 2400000.5
    z = int(jd + 0.5)
    frac = (jd + 0.5) - z
    alpha = int((z - 1867216.25) / 36524.25)
    a = z + 1 + alpha - alpha // 4 if z >= 2299161 else z
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e) + frac
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return year, month, day


class Resolver:
    """Memoised SBDB name resolution, shared across a whole run."""

    def __init__(self, session: CachedSession) -> None:
        self.session = session
        self.cache: dict[str, tuple[SbdbObject | None, str | None]] = {}

    def resolve(self, raw_name: str) -> tuple[SbdbObject | None, str | None]:
        if raw_name not in self.cache:
            self.cache[raw_name] = sbdb.lookup(self.session, raw_name)
        return self.cache[raw_name]

    def annotate(self, reports: dict[str, ServiceReport]) -> list[str]:
        """Attach resolved identities to every match worth considering."""
        from .verdict import considered

        errors: list[str] = []
        for report in reports.values():
            for match in report.matches:
                if match.resolved_des is not None or not considered(match):
                    continue
                obj, err = self.resolve(match.raw_name)
                if obj is not None:
                    match.resolved_des = obj.des
                    match.fullname = obj.fullname
                    match.kind = obj.kind
                    if not match.orbit_class or report.service != mpchecker.SERVICE:
                        match.orbit_class = obj.orbit_class or match.orbit_class
                elif err:
                    errors.append(f"{match.raw_name}: {err}")
        return errors


def vet_candidate(
    session: CachedSession,
    candidate: VetCandidate,
    resolver: Resolver,
    *,
    max_epochs: int = DEFAULT_MAX_EPOCHS,
    use_sbident: bool = True,
    force_sbident: bool = False,
    sbident_max_epochs: int = 2,
    sbident_timeout: float = 240.0,
) -> VetVerdict:
    """Identify one candidate. Cheap services first; SBIDENT only if the answer is still open."""
    epochs = select_epochs(candidate, max_epochs)
    if not epochs:
        verdict = VetVerdict(desig=candidate.desig, category="service_failed", origin=candidate.origin)
        verdict.reasons.append("candidate carries no usable astrometry")
        return verdict

    reports: dict[str, ServiceReport] = {}
    reports[skybot.SERVICE] = _skybot_report(session, epochs)
    reports[mpchecker.SERVICE], coverage = _mpchecker_report(session, epochs)
    resolver.annotate(reports)
    verdict = classify(candidate, reports, coverage_notes=coverage)

    escalate = force_sbident or verdict.category != "known"
    if use_sbident and escalate:
        reports[sbident.SERVICE] = _sbident_report(
            session, epochs[:sbident_max_epochs], timeout=sbident_timeout
        )
        resolver.annotate(reports)
        verdict = classify(candidate, reports, coverage_notes=coverage)

    if verdict.identified_as:
        obj, _ = resolver.resolve(verdict.identified_as)
        if obj is not None:
            verdict.element_comparison = sbdb.compare_elements(
                candidate.elements, obj.elements, obj.des
            )
            verdict.identified_fullname = verdict.identified_fullname or obj.fullname
            # Re-run so an element disagreement can downgrade a positional "known".
            verdict = classify(
                candidate, reports,
                element_comparison=verdict.element_comparison,
                coverage_notes=coverage,
            )
    return verdict


def vet_candidates(
    session: CachedSession,
    candidates: Sequence[VetCandidate],
    *,
    max_epochs: int = DEFAULT_MAX_EPOCHS,
    use_sbident: bool = True,
    force_sbident: bool = False,
    sbident_max_epochs: int = 2,
    sbident_timeout: float = 240.0,
    progress: Callable[[int, int, VetVerdict], None] | None = None,
) -> dict[str, Any]:
    """Vet a whole set and return a JSON-able report. No concurrency, by design."""
    resolver = Resolver(session)
    verdicts: list[VetVerdict] = []
    started = time.monotonic()
    for i, cand in enumerate(candidates, start=1):
        verdict = vet_candidate(
            session, cand, resolver,
            max_epochs=max_epochs, use_sbident=use_sbident, force_sbident=force_sbident,
            sbident_max_epochs=sbident_max_epochs, sbident_timeout=sbident_timeout,
        )
        verdicts.append(verdict)
        if progress:
            progress(i, len(candidates), verdict)
    return {
        "settings": {
            "max_epochs": max_epochs,
            "search_radius_arcsec": SEARCH_RADIUS_ARCSEC,
            "mpchecker_limit_mag": MPCHECKER_LIMIT_MAG,
            "sbident": "escalation only" if not force_sbident else "always",
            "sbident_max_epochs": sbident_max_epochs,
        },
        "http": session.summary(),
        "elapsed_s": round(time.monotonic() - started, 1),
        "tally": tally(verdicts),
        "resolved_objects": {
            name: obj.as_dict() for name, (obj, _) in resolver.cache.items() if obj
        },
        "unresolved_names": sorted(
            name for name, (obj, err) in resolver.cache.items() if obj is None and err
        ),
        "verdicts": [v.as_dict() for v in verdicts],
    }
