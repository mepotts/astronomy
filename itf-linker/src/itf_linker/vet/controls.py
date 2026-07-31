"""Controls: objects whose identity is already known, pushed through the identical path.

A cross-match layer fails silently. If the query is malformed, the epoch is off by a day,
the coordinates are swapped, or a name is mangled on the way to the resolver, every
candidate comes back ``unmatched`` -- which reads exactly like a field full of discoveries.
That failure mode has to be excluded *before* any real verdict is quoted, and the only way
to exclude it is to feed in things whose answer is known in advance and check that they come
back right.

Two controls, deliberately different in kind.

**The natural control: ``0073P-C``.** M1 submitted 979 ITF designations to Find_Orb and one
came back under the name ``73P-C`` -- comet 73P/Schwassmann-Wachmann 3, fragment C, which
Find_Orb recognised from the packed designation in the record itself. It is a known object
sitting in the ITF under its own name, discovered by a completely independent route (an
orbit solver reading a designation, not a catalogue query), and it is therefore the one
candidate in the whole population whose right answer was known before this module existed.
The vetting layer must flag it. If it does not, the layer is broken.

It is also the *hardest* realistic case, which makes it a good calibrator rather than a
formality: the ITF's astrometry is from April-May 2006, during 73P's disintegration, and it
drifts from the catalogue ephemeris across the arc. That measured drift is what sets
:data:`itf_linker.vet.verdict.CONSIDER_ARCSEC`.

**The synthetic control: numbered minor planets.** Three objects spanning dynamical classes,
their positions taken from JPL Horizons and written as if they were candidates. These test
the opposite corner: an ordinary, perfectly-known orbit must resolve to *itself*, at
arcsecond separations, through the same classifier. Where 73P-C proves the layer can find a
hard object, these prove it does not merely find *something* and call it a match.

Nothing here is special-cased. Controls are :class:`~itf_linker.vet.types.VetCandidate`
values and go through :func:`~itf_linker.vet.pipeline.vet_candidate` unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache import CachedSession
from .pipeline import Resolver, vet_candidate
from .sources import from_mpc80_lines, horizons_control
from .types import VetCandidate, VetVerdict

#: The ITF designation M1 found to be a known comet, and what it must resolve to.
ITF_COMET_CONTROL = ("0073P-C", "73P-C")

#: Numbered minor planets, one per dynamical class, with the Horizons target specifier and
#: the SBDB designation the vetting layer must return. The trailing ``;`` is not optional:
#: ``COMMAND='7'`` resolves to *Uranus*.
NUMBERED_CONTROLS: tuple[tuple[str, str, str], ...] = (
    ("433;", "433", "(433) Eros [NEO]"),
    ("7;", "7", "(7) Iris [inner main belt]"),
    ("588;", "588", "(588) Achilles [Jupiter Trojan]"),
)

#: Controls run from the observatories the *candidate population* actually uses, at the
#: epochs it actually spans.
#:
#: This is the control that matters most for M2's headline, and it was missing from the
#: first version. 100 of M1's 128 candidates are Rubin (X05) alone, all from 2025-2026. If
#: SkyBoT or MPChecker silently mishandled ``X05`` -- an observatory code only minted in
#: 2025 -- every one of those candidates would come back ``unmatched``, and a systematic
#: query bug would be indistinguishable from a field full of discoveries. Nothing in the
#: comet control (084, 2006) or the numbered controls (568, 2024) touches that path.
#:
#: ``(obscode, start_date, horizons_command, expected, label)``.
SITE_CONTROLS: tuple[tuple[str, str, str, str, str], ...] = (
    ("X05", "2025-07-15", "7;", "7", "(7) Iris from X05 Rubin, 2025 -- the candidate path"),
    ("W84", "2025-07-15", "433;", "433", "(433) Eros from W84 DECam, 2025"),
    ("O18", "2025-07-15", "588;", "588", "(588) Achilles from O18, 2025"),
)

#: Where and when the synthetic controls are "observed". 568 is Mauna Kea.
#:
#: **Not 703**, which is what M1's Find_Orb self-test uses. MPChecker answers ``403
#: Forbidden`` to any query carrying ``oc=703``, with an otherwise byte-identical request:
#: X05, O18, W84, 568, 269, T09, 304, 807, G37, 691, F51, 500 and 084 all return 200 and
#: the same 3,886-byte page, and 703 alone returns a nine-byte "Forbidden". Leaving the
#: control on 703 locked MPChecker out of three controls in a row, which then spent the
#: circuit breaker's failure budget and disabled the service for the rest of the run --
#: a control that silently switches off one of the services it is meant to be testing.
CONTROL_OBSCODE = "568"
CONTROL_START = "2024-01-05"
CONTROL_SEARCH_DAYS = 150


@dataclass(slots=True)
class ControlOutcome:
    label: str
    desig: str
    expected: str
    verdict: VetVerdict | None
    passed: bool
    failures: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "desig": self.desig,
            "expected": self.expected,
            "passed": self.passed,
            "failures": self.failures,
            "verdict": self.verdict.as_dict() if self.verdict else None,
        }


def _normalise(name: str) -> str:
    return name.replace(" ", "").replace("/", "").replace("-", "").upper()


def _same_object(got: str | None, expected: str) -> bool:
    """Loose string identity: SBDB may answer ``73P-C`` where a service said ``73P/C``."""
    return bool(got) and _normalise(got) == _normalise(expected)


def judge(outcome_verdict: VetVerdict, expected: str) -> list[str]:
    """Why this control did or did not pass. Empty list means it passed."""
    failures: list[str] = []
    if outcome_verdict.category != "known":
        failures.append(
            f"category is {outcome_verdict.category!r}, expected 'known' "
            f"({'; '.join(outcome_verdict.reasons) or 'no reason recorded'})"
        )
    if not _same_object(outcome_verdict.identified_as, expected):
        failures.append(
            f"identified as {outcome_verdict.identified_as!r}, expected {expected!r}"
        )
    return failures


def comet_control(
    session: CachedSession,
    resolver: Resolver,
    astrometry_path: Path,
    **kwargs: Any,
) -> ControlOutcome:
    """Vet the ITF's own ``0073P-C`` and require it to come back as comet 73P-C."""
    desig, expected = ITF_COMET_CONTROL
    lines = json.loads(Path(astrometry_path).read_text(encoding="utf-8"))["lines"].get(desig)
    if not lines:
        return ControlOutcome(
            label=f"{desig} (ITF designation Find_Orb identified as comet {expected})",
            desig=desig, expected=expected, verdict=None, passed=False,
            failures=[f"{desig} not present in {astrometry_path}; run `itf-linker vet-extract`"],
        )
    candidate = from_mpc80_lines(
        desig, lines, origin="positive control: known comet inside the ITF"
    )
    verdict = vet_candidate(session, candidate, resolver, force_sbident=True, **kwargs)
    failures = judge(verdict, expected)
    return ControlOutcome(
        label=f"{desig} (ITF designation Find_Orb identified as comet {expected})",
        desig=desig, expected=expected, verdict=verdict,
        passed=not failures, failures=failures,
    )


def _horizons_control(
    session: CachedSession,
    resolver: Resolver,
    *,
    command: str,
    expected: str,
    label: str,
    obscode: str,
    start: str,
    tag: str,
    **kwargs: Any,
) -> ControlOutcome:
    """One synthetic control: known object, real site, real epoch, same classifier."""
    from ..fit.verify import HorizonsError, horizons_astrometry

    try:
        rows = horizons_astrometry(
            command, obscode, start=start,
            stop=_add_days(start, CONTROL_SEARCH_DAYS), step="30m",
        )
    except (HorizonsError, OSError) as exc:
        return ControlOutcome(
            label=label, desig=expected, expected=expected, verdict=None,
            passed=False, failures=[f"Horizons unavailable: {exc}"],
        )
    if not rows:
        return ControlOutcome(
            label=label, desig=expected, expected=expected, verdict=None, passed=False,
            failures=[f"Horizons returned no observable epochs from {obscode} after {start}"],
        )
    candidate: VetCandidate = horizons_control(
        f"CTRL{tag}", rows, obscode,
        origin=f"positive control: {label}, positions from JPL Horizons",
    )
    verdict = vet_candidate(session, candidate, resolver, force_sbident=False, **kwargs)
    failures = judge(verdict, expected)
    return ControlOutcome(
        label=label, desig=candidate.desig, expected=expected, verdict=verdict,
        passed=not failures, failures=failures,
    )


def numbered_controls(
    session: CachedSession, resolver: Resolver, **kwargs: Any
) -> list[ControlOutcome]:
    """Synthesise candidates for known numbered minor planets and require self-resolution."""
    return [
        _horizons_control(
            session, resolver, command=command, expected=expected, label=label,
            obscode=CONTROL_OBSCODE, start=CONTROL_START, tag=expected, **kwargs,
        )
        for command, expected, label in NUMBERED_CONTROLS
    ]


def site_controls(
    session: CachedSession, resolver: Resolver, **kwargs: Any
) -> list[ControlOutcome]:
    """Repeat the exercise from the observatories and epochs the candidates come from.

    Without this, a query bug specific to a new observatory code -- ``X05`` was minted in
    2025 and covers 100 of M1's 128 candidates -- reads as a field full of discoveries.
    """
    return [
        _horizons_control(
            session, resolver, command=command, expected=expected, label=label,
            obscode=obscode, start=start, tag=f"{expected}{obscode}", **kwargs,
        )
        for obscode, start, command, expected, label in SITE_CONTROLS
    ]


def run_controls(
    session: CachedSession,
    *,
    astrometry_path: Path,
    include_numbered: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run every control and return a JSON-able report.

    ``all_passed`` is the gate the rest of M2 hangs off: if it is false, no verdict from
    this run should be quoted as evidence about anything.
    """
    resolver = Resolver(session)
    outcomes = [comet_control(session, resolver, astrometry_path, **kwargs)]
    if include_numbered:
        outcomes.extend(numbered_controls(session, resolver, **kwargs))
        outcomes.extend(site_controls(session, resolver, **kwargs))
    n_pass = sum(1 for o in outcomes if o.passed)
    return {
        "summary": {
            "n_controls": len(outcomes),
            "n_passed": n_pass,
            "all_passed": bool(outcomes) and n_pass == len(outcomes),
            "outcomes": [
                {
                    "label": o.label,
                    "expected": o.expected,
                    "identified_as": o.verdict.identified_as if o.verdict else None,
                    "category": o.verdict.category if o.verdict else None,
                    "best_sep_arcsec": o.verdict.best_sep_arcsec if o.verdict else None,
                    "worst_sep_arcsec": o.verdict.worst_sep_arcsec if o.verdict else None,
                    "passed": o.passed,
                    "failures": o.failures,
                }
                for o in outcomes
            ],
        },
        "http": session.summary(),
        "controls": [o.as_dict() for o in outcomes],
    }


def _add_days(iso: str, days: int) -> str:
    from datetime import date, timedelta

    y, m, d = (int(x) for x in iso.split("-"))
    return (date(y, m, d) + timedelta(days=days)).isoformat()
