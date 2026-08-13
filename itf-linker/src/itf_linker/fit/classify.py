"""Which dynamical population a fitted orbit belongs to, and how NEO-like it is.

M3 searched 1.4-5.6 AU and every survivor was, unsurprisingly, a main-belt orbit. M4
widens the hypothesis grid to 0.55-50 AU, which only means anything if the output is
**reported by population** -- a Centaur-distance link and a 2.7 AU link are the same row in
a table and completely different results.

Two things are computed here, and they are not the same thing:

**Classification** is a lookup on the fitted elements, using the IAU/MPC boundaries. It
says what the orbit *is*, assuming the orbit is right.

**The NEO score** is a statement about whether the orbit is *known well enough* to say it
is an NEO. The formal criterion is ``q < 1.3 AU``; Find_Orb reports ``sigma(q)`` alongside
``q``, so the score is the Gaussian probability that the true ``q`` is inside 1.3 AU given
the fitted value and its uncertainty. On a two-week arc ``sigma(q)`` is routinely a
substantial fraction of ``q``, so a link with ``q = 1.1 +/- 0.4`` is a much weaker NEO
claim than one with ``q = 1.1 +/- 0.02``, and a bare ``q < 1.3`` count hides that.

.. warning::

   **This is not digest2.** digest2 is the MPC's own NEO-likelihood scorer and it works
   from the *astrometry* -- it integrates over the orbits compatible with a short arc
   against a population model, and it does not require a converged fit. The score here
   works from a converged Find_Orb solution and its covariance, so it cannot say anything
   about a link that did not converge, and it has no population prior: a score of 0.9 means
   "the fitted orbit says NEO and the covariance does not overturn that", not "9 in 10
   objects like this are NEOs". Where digest2 is available it should replace this.
"""

from __future__ import annotations

import math
from typing import Any

#: The formal NEO criterion: perihelion distance under 1.3 AU.
NEO_PERIHELION_AU = 1.3

#: Earth's aphelion and perihelion, the Aten/Apollo/Amor boundaries.
EARTH_APHELION_AU = 1.0167
EARTH_PERIHELION_AU = 0.9833

#: Above this semimajor axis an object is trans-Neptunian by convention (Neptune's ``a``).
NEPTUNE_A_AU = 30.1

#: Population labels, in the order they are reported.
POPULATIONS = (
    "atira", "aten", "apollo", "amor",
    "mars_crosser", "hungaria", "inner_belt", "middle_belt", "outer_belt",
    "cybele_hilda", "jupiter_trojan", "centaur", "tno",
    "other_bound", "unbound", "unknown",
)

#: Populations that satisfy ``q < 1.3 AU``.
NEO_POPULATIONS = frozenset({"atira", "aten", "apollo", "amor"})


def classify_orbit(
    a: float | None, e: float | None, q: float | None = None, incl: float | None = None
) -> str:
    """Dynamical class of an osculating orbit, by the standard element boundaries.

    **Above the belt this is a semimajor-axis classification, not a distance one.** Once the
    NEO cut (``q < 1.3 AU``) has been passed, ``centaur`` and ``tno`` are decided by ``a``
    alone with no perihelion condition -- the JPL SBDB ``CEN``/``TNO`` convention. On the
    short arcs this project fits, that admits very eccentric solutions: M5's ``lnk2gkr`` is
    labelled ``tno`` with ``a`` = 98.5 AU and ``q`` = 1.59 AU, and three ``centaur`` labels
    have perihelia inside the asteroid belt. The label is correct by the convention and is
    *not* a claim that the object is far away. Anything selecting "distant objects" should
    test ``q`` as well -- see :func:`dynamically_distant`.

    ``q`` is taken from the fit when given and derived as ``a(1-e)`` otherwise, because
    Find_Orb reports both and they can differ in the last digits.
    """
    if a is None or e is None or not math.isfinite(a) or not math.isfinite(e):
        return "unknown"
    if e >= 1.0 or a <= 0.0:
        return "unbound"
    peri = q if q is not None and math.isfinite(q) else a * (1.0 - e)
    aph = a * (1.0 + e)

    if peri < NEO_PERIHELION_AU:
        if a < 1.0:
            return "atira" if aph < EARTH_PERIHELION_AU else "aten"
        return "apollo" if peri < EARTH_APHELION_AU else "amor"
    if a > NEPTUNE_A_AU:
        return "tno"
    if a > 5.5:
        return "centaur"
    if 5.05 <= a <= 5.35 and e < 0.3:
        return "jupiter_trojan"
    if 3.3 <= a <= 4.6:
        return "cybele_hilda"
    # Hungaria BEFORE mars-crosser (fixed 2026-08-07). Real Hungaria eccentricities are
    # 0.07-0.12 at a ~ 1.9, which puts perihelion either side of 1.666 AU -- so testing
    # mars-crosser first shadowed part of the Hungaria population and under-counted it
    # systematically. A high-inclination body at a = 1.87, e = 0.14 is a Hungaria that also
    # happens to cross Mars, not a Mars-crosser. M5: one survivor of 3,190 changes label.
    if 1.78 <= a < 2.0 and e < 0.18 and (incl is None or incl > 12.0):
        return "hungaria"
    if peri < 1.666 and a < 3.2:
        return "mars_crosser"
    if 2.0 <= a < 2.5:
        return "inner_belt"
    if 2.5 <= a < 2.82:
        return "middle_belt"
    if 2.82 <= a <= 3.3:
        return "outer_belt"
    return "other_bound"


#: Perihelion above which an orbit is outside the main belt at *every* point of it. Jupiter
#: sits at 5.2 AU; a body that never comes closer than this is dynamically distant in a way
#: a semimajor axis alone cannot establish.
DISTANT_PERIHELION_AU = 5.2


def dynamically_distant(a: float | None, e: float | None, q: float | None = None) -> bool:
    """Is this orbit distant *throughout*, not merely distant on average?

    :func:`classify_orbit` calls anything with ``a > 5.5`` a Centaur and ``a > 30.1`` a TNO,
    following JPL SBDB, with no condition on perihelion. On short arcs that admits solutions
    that spend most of their orbit far away and the rest of it inside the asteroid belt --
    M5's ``lnk2gkr`` is ``a`` = 98.5 AU with ``q`` = 1.59 AU. Selecting distant objects on
    the label alone therefore selects eccentric garbage too.

    This requires both: beyond the belt *and* a perihelion that never re-enters it.
    """
    if a is None or e is None or not math.isfinite(a) or not math.isfinite(e):
        return False
    if e >= 1.0 or a <= 0.0:
        return False
    peri = q if q is not None and math.isfinite(q) else a * (1.0 - e)
    return a > 5.5 and peri > DISTANT_PERIHELION_AU


def neo_score(q: float | None, sigma_q: float | None) -> float | None:
    """P(perihelion < 1.3 AU) for a Gaussian ``q`` -- a proxy, **not** digest2.

    Returns ``None`` when there is no perihelion distance to score. A missing or
    non-positive ``sigma_q`` degrades to the hard criterion (1.0 or 0.0), which is the
    honest reading of "the fit reported no uncertainty".
    """
    if q is None or not math.isfinite(q):
        return None
    if sigma_q is None or not math.isfinite(sigma_q) or sigma_q <= 0.0:
        return 1.0 if q < NEO_PERIHELION_AU else 0.0
    z = (NEO_PERIHELION_AU - q) / sigma_q
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def describe(fit: Any) -> dict[str, Any]:
    """Population, NEO score and the elements they were derived from, for one fit.

    ``fit`` is a :class:`~itf_linker.fit.findorb.FitResult` or anything carrying the same
    ``a``/``e``/``q``/``incl``/``sigma_q`` attributes.
    """
    a, e = getattr(fit, "a", None), getattr(fit, "e", None)
    q, incl = getattr(fit, "q", None), getattr(fit, "incl", None)
    sigma_q = getattr(fit, "sigma_q", None)
    population = classify_orbit(a, e, q, incl)
    score = neo_score(q, sigma_q)
    return {
        "population": population,
        "is_neo_by_q": population in NEO_POPULATIONS,
        "neo_score_proxy": None if score is None else round(score, 4),
        "a_au": a,
        "e": e,
        "q_au": q,
        "sigma_q_au": sigma_q,
        "incl_deg": incl,
    }


def population_histogram(rows: list[dict[str, Any]], key: str = "population") -> dict[str, int]:
    """Counts per population, in :data:`POPULATIONS` order, omitting empty classes."""
    counts: dict[str, int] = {}
    for row in rows:
        name = str(row.get(key) or "unknown")
        counts[name] = counts.get(name, 0) + 1
    ordered = {p: counts[p] for p in POPULATIONS if p in counts}
    ordered.update({k: v for k, v in counts.items() if k not in ordered})
    return ordered
