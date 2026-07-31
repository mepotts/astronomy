"""JPL Small-Body Database lookup -- turn a name a service returned into a definite object.

A positional service answers with whatever string it likes: SkyBoT says ``73P-C``, SBIDENT
says ``887872 (2007 TO134)``, MPChecker says ``(130535)``. None of those is an
identification on its own, because none of them is guaranteed to denote the same object as
the others. :func:`lookup` resolves a name against the SBDB and returns the primary
designation, so that "two services agree" is a statement about objects rather than about
strings.

The same call returns the object's catalogue orbit, which is what makes the *element*
comparison possible: having matched positionally, we can ask whether the catalogue orbit
and our fitted orbit are the same orbit, and say by how much they differ rather than just
"yes".

``full-prec=true`` is not optional. Without it the API rounds elements to three significant
figures -- ``"a": "3.06"`` for 73P-C -- which is coarser than the disagreement any
comparison here is trying to measure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .cache import CachedResponse, CachedSession, ServiceUnavailable
from .types import ElementComparison, OrbitElements

SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
SERVICE = "sbdb"

#: Each service names objects its own way, and the shapes barely overlap:
#:
#:   MPChecker  ``(130536) 2000 QV208``   ``2018 EC25``
#:   SBIDENT    ``887872 (2007 TO134)``   ``(2018 EC25)``   ``8 Flora (A847 UA)``
#:   SkyBoT     ``73P-C``                 ``2018 EC25``
#:
#: The rules below are ordered and deliberately conservative: anything not recognised is
#: passed to SBDB **unchanged**. An earlier version peeled a leading integer off any name,
#: which turned the comet ``73P-C`` into ``73`` and resolved it to minor planet
#: *(73) Klytia* -- a confident, completely wrong identification. The positive control is
#: what caught it, which is the entire argument for having one.
_NUM_IN_PARENS = re.compile(r"^\((\d+)\)")           # (130536) 2000 QV208
_NUM_THEN_PARENS = re.compile(r"^(\d+)\s+\(")        # 887872 (2007 TO134)
_NUM_THEN_NAME = re.compile(r"^(\d+)\s+[A-Z][a-z]")  # 8 Flora (A847 UA)
_WRAPPED = re.compile(r"^\((.+)\)$")                 # (2018 EC25)
_BARE_NUMBER = re.compile(r"^\d+$")


def name_to_sstr(raw_name: str) -> str:
    """Reduce a service's display name to something SBDB's ``sstr`` accepts.

    A minor-planet *number* is the least ambiguous handle there is, so it wins whenever one
    is unambiguously present. Everything else -- provisional designations, comet
    designations with their fragment suffixes -- goes through untouched, because SBDB
    resolves those directly and any cleverness here can only lose information.
    """
    name = raw_name.strip()
    if not name:
        return name
    for pattern in (_NUM_IN_PARENS, _NUM_THEN_PARENS, _NUM_THEN_NAME):
        m = pattern.match(name)
        if m:
            return m.group(1)
    if _BARE_NUMBER.match(name):
        return name
    m = _WRAPPED.match(name)
    if m:
        return m.group(1).strip()
    return name


@dataclass(slots=True)
class SbdbObject:
    des: str
    fullname: str | None
    kind: str | None
    orbit_class: str | None
    elements: OrbitElements
    n_obs_used: int | None = None
    data_arc_days: float | None = None
    condition_code: str | None = None
    first_obs: str | None = None
    last_obs: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "des": self.des, "fullname": self.fullname, "kind": self.kind,
            "orbit_class": self.orbit_class, "n_obs_used": self.n_obs_used,
            "data_arc_days": self.data_arc_days, "condition_code": self.condition_code,
            "first_obs": self.first_obs, "last_obs": self.last_obs,
            "elements": self.elements.as_dict(),
        }


def _f(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_sbdb(payload: dict[str, Any]) -> SbdbObject | None:
    """Turn one ``sbdb.api`` reply into an :class:`SbdbObject`, or ``None`` if unresolved."""
    obj = payload.get("object")
    if not obj:
        return None
    orbit = payload.get("orbit") or {}
    by_name = {e.get("name"): e for e in (orbit.get("elements") or []) if isinstance(e, dict)}

    def el(name: str) -> float | None:
        entry = by_name.get(name)
        return _f(entry.get("value")) if entry else None

    orbit_class = (obj.get("orbit_class") or {}).get("name")
    return SbdbObject(
        des=str(obj.get("des") or obj.get("fullname") or "").strip(),
        fullname=obj.get("fullname"),
        kind=obj.get("kind"),
        orbit_class=orbit_class,
        n_obs_used=int(orbit["n_obs_used"]) if _f(orbit.get("n_obs_used")) else None,
        data_arc_days=_f(orbit.get("data_arc")),
        condition_code=orbit.get("condition_code"),
        first_obs=orbit.get("first_obs"),
        last_obs=orbit.get("last_obs"),
        elements=OrbitElements(
            epoch_jd=_f(orbit.get("epoch")),
            a=el("a"), e=el("e"), incl=el("i"), q=el("q"),
            asc_node=el("om"), arg_per=el("w"), mean_anom=el("ma"),
            source="JPL SBDB",
        ),
    )


def lookup(session: CachedSession, raw_name: str) -> tuple[SbdbObject | None, str | None]:
    """Resolve one name. Returns ``(object, error)``; both ``None`` means "not found"."""
    sstr = name_to_sstr(raw_name)
    if not sstr:
        return None, "empty name"
    params = {"sstr": sstr, "full-prec": "true", "discovery": "0"}
    try:
        resp: CachedResponse = session.get(SERVICE, SBDB_URL, params)
    except ServiceUnavailable as exc:
        return None, str(exc)
    try:
        payload = resp.json()
    except ValueError:
        return None, f"unparseable SBDB reply for {sstr!r}"
    if payload.get("code") or payload.get("message"):
        # SBDB answers ambiguity/no-match with a message rather than an error status.
        return None, f"{payload.get('message', 'no match')} ({sstr})"
    return parse_sbdb(payload), None


#: How many of the *fitted orbit's own* sigmas two orbits may differ by and still be
#: called the same orbit.
#:
#: Sigmas, not fixed fractions. An earlier version used fixed tolerances (5% in ``a``, 5%
#: in ``q``, 2 degrees in ``i``) and got the answer wrong on a case where the positional
#: evidence was as good as it ever gets: ``/21TB2S`` sits **0.6"-3.2" from 2021 TS112 at
#: all three epochs, on both services** -- the same scale as the numbered-object controls
#: -- yet its fitted ``a`` differs by 0.68 AU, which is 31%. The fixed tolerance called
#: that a contradiction and downgraded a certain identification to ``ambiguous``.
#:
#: It is not a contradiction. M1 measured exactly why: a short ITF arc pins an orbit's
#: *direction* well and its *scale* badly, and this fit's own sigma(a) is 0.97 AU. The
#: difference is 0.70 sigma. Judging a short-arc fit against a fixed fraction measures the
#: length of the arc, not the identity of the object.
MAX_ELEMENT_SIGMA = 3.0

#: Fallback for orbits that carry no sigmas at all, where a scale-free comparison is
#: impossible and something has to be assumed.
ELEMENT_TOL = {"a_rel": 0.05, "e_abs": 0.05, "i_deg": 2.0, "q_rel": 0.05}


def compare_elements(
    fit: OrbitElements | None, cat: OrbitElements, des: str, *, max_sigma: float = MAX_ELEMENT_SIGMA
) -> ElementComparison:
    """How far apart are a fitted orbit and a catalogue orbit, in absolute and sigma terms.

    ``consistent`` can only ever *downgrade* a positional match, never create one, so it is
    deliberately permissive: when the fitted orbit is too loose to contradict anything the
    answer is "consistent", and :attr:`ElementComparison.note` says the test had no power
    rather than implying it passed something.
    """
    cmp = ElementComparison(des=des)
    if fit is None:
        cmp.note = "candidate has no fitted orbit; positional match only"
        return cmp

    def diff(x: float | None, y: float | None) -> float | None:
        return None if x is None or y is None else x - y

    cmp.d_a_au = diff(fit.a, cat.a)
    cmp.d_e = diff(fit.e, cat.e)
    cmp.d_i_deg = diff(fit.incl, cat.incl)
    cmp.d_q_au = diff(fit.q, cat.q)

    for attr, sigma, target in (
        ("n_sigma_a", fit.sigma_a, cmp.d_a_au),
        ("n_sigma_q", fit.sigma_q, cmp.d_q_au),
        ("n_sigma_i", fit.sigma_i, cmp.d_i_deg),
        ("n_sigma_e", fit.sigma_e, cmp.d_e),
    ):
        if sigma and target is not None:
            setattr(cmp, attr, abs(target) / sigma)

    sigmas = [
        n for n in (cmp.n_sigma_a, cmp.n_sigma_q, cmp.n_sigma_i, cmp.n_sigma_e)
        if n is not None
    ]
    if sigmas:
        worst = max(sigmas)
        cmp.consistent = worst <= max_sigma
        cmp.note = (
            f"agrees to {worst:.1f} sigma of the fitted orbit"
            if cmp.consistent
            else f"differs by {worst:.1f} sigma of the fitted orbit"
        )
        # A fit whose scale is undetermined cannot contradict anything; say so rather
        # than let a vacuous pass read as corroboration.
        if cmp.consistent and not fit.well_constrained:
            cmp.note += " -- but the fitted orbit is too loose for this to discriminate"
        return cmp

    checks: list[bool] = []
    if cmp.d_a_au is not None and cat.a:
        checks.append(abs(cmp.d_a_au) <= ELEMENT_TOL["a_rel"] * abs(cat.a))
    if cmp.d_e is not None:
        checks.append(abs(cmp.d_e) <= ELEMENT_TOL["e_abs"])
    if cmp.d_i_deg is not None:
        checks.append(abs(cmp.d_i_deg) <= ELEMENT_TOL["i_deg"])
    if cmp.d_q_au is not None and cat.q:
        checks.append(abs(cmp.d_q_au) <= ELEMENT_TOL["q_rel"] * abs(cat.q))
    if checks:
        cmp.consistent = all(checks)
        cmp.note = (
            "within fixed tolerance (no sigmas available)" if cmp.consistent
            else "outside fixed tolerance (no sigmas available)"
        )
    else:
        cmp.note = "no comparable elements"
    return cmp
