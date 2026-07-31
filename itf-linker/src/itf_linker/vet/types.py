"""The vocabulary of the vetting stage: what goes in, what comes out.

Nothing here knows about the ITF, about Find_Orb, or about the 128 designations M1
happened to produce. A :class:`VetCandidate` is *"a thing someone believes might be an
object, with astrometry and optionally a fitted orbit"* -- which is equally true of an ITF
trkSub, a DAD tracklet, a linked triplet, or a synthetic control. That is deliberate: the
identification question is the same in every case, and the answer should be produced by
one code path so that a control and a real candidate are provably judged alike.

The verdict vocabulary is four-valued, and the fourth value is the important one:

``known``
    A catalogue object explains the astrometry.
``unmatched``
    No catalogue object was returned near the astrometry by any service that answered.
    **This is not "new".** It can equally mean the arc is too poor to match, or that the
    service's catalogue does not cover the epoch. :attr:`VetVerdict.unmatched_reason`
    carries whichever of those could be determined.
``ambiguous``
    Services disagree, or an object matches some epochs and not others.
``service_failed``
    Nothing usable came back. Recorded rather than silently folded into ``unmatched``,
    because "we did not look" and "we looked and saw nothing" are different claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

Category = Literal["known", "unmatched", "ambiguous", "service_failed"]

#: Reasons a non-match may not mean "unknown object". Ordered weakest claim first.
UnmatchedReason = Literal[
    "epoch_outside_service_coverage",
    "object_class_outside_service_coverage",
    "orbit_too_poorly_constrained",
    "no_catalogue_object_near_astrometry",
]

#: Beyond this a "semimajor axis" is a symptom, not a measurement. The ITF's longest fitted
#: arcs are weeks; nothing observed over weeks can be shown to orbit past the inner Oort
#: cloud, so a larger value means the least-squares solution ran away.
MAX_PLAUSIBLE_A_AU = 1000.0


@dataclass(frozen=True, slots=True)
class VetObservation:
    """One astrometric detection -- everything a positional service needs and no more."""

    mjd_utc: float
    ra_deg: float
    dec_deg: float
    obscode: str
    mag: float | None = None
    band: str | None = None
    #: Local-night index, when the caller knows it. Used only to spread queries across
    #: nights rather than wasting three of them on one night's tracklet.
    night: int | None = None

    @property
    def jd_utc(self) -> float:
        return self.mjd_utc + 2400000.5


@dataclass(frozen=True, slots=True)
class OrbitElements:
    """A fitted heliocentric osculating orbit, with whatever sigmas came with it.

    Field names follow ``fit.findorb.FitResult`` so an M1 fit converts without a
    translation table, and the units are the ones every service also uses: AU and degrees.
    """

    epoch_jd: float | None = None
    a: float | None = None
    e: float | None = None
    incl: float | None = None
    q: float | None = None
    asc_node: float | None = None
    arg_per: float | None = None
    mean_anom: float | None = None
    sigma_a: float | None = None
    sigma_e: float | None = None
    sigma_i: float | None = None
    sigma_q: float | None = None
    source: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "epoch_jd": self.epoch_jd, "a": self.a, "e": self.e, "incl": self.incl,
            "q": self.q, "asc_node": self.asc_node, "arg_per": self.arg_per,
            "mean_anom": self.mean_anom, "sigma_a": self.sigma_a, "sigma_e": self.sigma_e,
            "sigma_i": self.sigma_i, "sigma_q": self.sigma_q, "source": self.source,
        }

    @property
    def well_constrained(self) -> bool:
        """Is the orbit's *scale* determined at all?

        M1 measured that a short ITF arc pins an orbit's direction well and its scale
        badly, and that the MPC's published sigma limits are scoped to exactly-three-night
        links -- so a five-night fit with sigma(a) = 8,173 AU passes them untouched. When
        an orbit is that loose the designation is not a usable candidate whatever the
        catalogues say, and the verdict must record that rather than let a non-match read
        as a discovery.

        The absolute cap on ``a`` is not decoration. A purely relative test
        (``sigma_a < 5% of a``) calls M1's worst fit -- ``t75502b``, a = 1.09e11 AU with
        sigma(a) = 8,173 AU -- *well constrained*, because 8,173 really is a tiny fraction
        of 1.09e11. It is of course nothing of the kind. Nothing observed over a two-month
        arc can have a semimajor axis past the inner Oort cloud, so a value there is a
        statement that the fit did not converge on anything physical.
        """
        if self.sigma_a is None or self.a is None:
            return False
        if not math.isfinite(self.sigma_a) or not math.isfinite(self.a):
            return False
        if abs(self.a) > MAX_PLAUSIBLE_A_AU:
            return False
        return self.sigma_a < max(0.05, 0.05 * abs(self.a))


@dataclass(frozen=True, slots=True)
class VetCandidate:
    """Something to be identified: a name, its astrometry, and optionally a fitted orbit."""

    desig: str
    observations: tuple[VetObservation, ...]
    elements: OrbitElements | None = None
    #: Free-text provenance, e.g. ``"itf-linker M1 ranked"`` or ``"positive control"``.
    origin: str = ""
    #: Original 80-column records, when the caller has them. MPChecker can consume these
    #: directly, which lets the MPC do its own parsing rather than trusting ours.
    mpc80_lines: tuple[str, ...] = ()

    @property
    def obscodes(self) -> list[str]:
        return sorted({o.obscode for o in self.observations})

    @property
    def n_nights(self) -> int:
        if any(o.night is not None for o in self.observations):
            return len({o.night for o in self.observations if o.night is not None})
        return len({int(o.mjd_utc) for o in self.observations})


@dataclass(slots=True)
class ServiceMatch:
    """One catalogue object a service put near one of the candidate's detections."""

    service: str
    raw_name: str
    #: SBDB-resolved primary designation. ``None`` means SBDB could not resolve the name,
    #: which is itself worth recording -- an unresolvable name is not an identification.
    resolved_des: str | None = None
    fullname: str | None = None
    kind: str | None = None                    # SBDB "kind": an/au/cn/cu ...
    orbit_class: str | None = None
    sep_arcsec: float | None = None
    ephem_err_arcsec: float | None = None
    v_mag: float | None = None
    obs_index: int = -1                        # which VetObservation produced this
    mjd_utc: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "service": self.service, "raw_name": self.raw_name,
            "resolved_des": self.resolved_des, "fullname": self.fullname,
            "kind": self.kind, "orbit_class": self.orbit_class,
            "sep_arcsec": self.sep_arcsec, "ephem_err_arcsec": self.ephem_err_arcsec,
            "v_mag": self.v_mag, "obs_index": self.obs_index, "mjd_utc": self.mjd_utc,
        }

    @property
    def identity(self) -> str:
        """The key two services must agree on to be counted as agreeing."""
        return self.resolved_des or self.raw_name


@dataclass(slots=True)
class ServiceReport:
    """What one service did for one candidate: queries, answers, failures."""

    service: str
    queries: int = 0
    from_cache: int = 0
    matches: list[ServiceMatch] = field(default_factory=list)
    #: Epochs the service answered for, so partial coverage is visible.
    epochs_queried: list[float] = field(default_factory=list)
    epochs_answered: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: str | None = None

    @property
    def ok(self) -> bool:
        return self.skipped is None and bool(self.epochs_answered)

    def as_dict(self) -> dict[str, Any]:
        return {
            "service": self.service, "queries": self.queries, "from_cache": self.from_cache,
            "epochs_queried": len(self.epochs_queried),
            "epochs_answered": len(self.epochs_answered),
            "n_matches": len(self.matches),
            "matches": [m.as_dict() for m in self.matches],
            "errors": self.errors, "skipped": self.skipped, "ok": self.ok,
        }


@dataclass(slots=True)
class ElementComparison:
    """How far the candidate's fitted orbit is from a matched object's catalogue orbit."""

    des: str
    d_a_au: float | None = None
    d_e: float | None = None
    d_i_deg: float | None = None
    d_q_au: float | None = None
    n_sigma_a: float | None = None
    n_sigma_q: float | None = None
    n_sigma_i: float | None = None
    n_sigma_e: float | None = None
    consistent: bool | None = None
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "des": self.des, "d_a_au": self.d_a_au, "d_e": self.d_e,
            "d_i_deg": self.d_i_deg, "d_q_au": self.d_q_au,
            "n_sigma_a": self.n_sigma_a, "n_sigma_q": self.n_sigma_q,
            "n_sigma_i": self.n_sigma_i, "n_sigma_e": self.n_sigma_e,
            "consistent": self.consistent, "note": self.note,
        }


@dataclass(slots=True)
class VetVerdict:
    """The identification decision for one candidate, with its whole evidence trail."""

    desig: str
    category: Category
    identified_as: str | None = None
    identified_fullname: str | None = None
    n_services_agreeing: int = 0
    n_epochs_queried: int = 0
    n_epochs_matched: int = 0
    best_sep_arcsec: float | None = None
    worst_sep_arcsec: float | None = None
    element_comparison: ElementComparison | None = None
    unmatched_reason: str | None = None
    reasons: list[str] = field(default_factory=list)
    services: dict[str, ServiceReport] = field(default_factory=dict)
    #: Every distinct identity any service proposed, with how many epochs it covered.
    candidates_considered: list[dict[str, Any]] = field(default_factory=list)
    origin: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "desig": self.desig,
            "origin": self.origin,
            "category": self.category,
            "identified_as": self.identified_as,
            "identified_fullname": self.identified_fullname,
            "n_services_agreeing": self.n_services_agreeing,
            "n_epochs_queried": self.n_epochs_queried,
            "n_epochs_matched": self.n_epochs_matched,
            "best_sep_arcsec": self.best_sep_arcsec,
            "worst_sep_arcsec": self.worst_sep_arcsec,
            "element_comparison": (
                self.element_comparison.as_dict() if self.element_comparison else None
            ),
            "unmatched_reason": self.unmatched_reason,
            "reasons": self.reasons,
            "candidates_considered": self.candidates_considered,
            "services": {k: v.as_dict() for k, v in self.services.items()},
        }


def angular_sep_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Great-circle separation in arcseconds, via the Vincenty formula.

    Not ``acos(sin sin + cos cos cos)``: that form loses all precision below about 1
    arcsecond, which is precisely the regime an identification lives in.
    """
    p1, p2 = math.radians(dec1), math.radians(dec2)
    dl = math.radians(ra2 - ra1)
    sin_dl, cos_dl = math.sin(dl), math.cos(dl)
    num = math.hypot(
        math.cos(p2) * sin_dl,
        math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * cos_dl,
    )
    den = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * cos_dl
    return math.degrees(math.atan2(num, den)) * 3600.0
