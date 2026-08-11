"""M8 -- can the Hoy et al. method reach satellites of young close-in giants?

**The idea.** Hoy et al. work because the reflex velocity scales as ``M_host^(-2/3)``: a
light host wobbles hard. Push that further -- a 1 M_Jup planet is 37x lighter than
CD-35 2722 B, so an *Earth-mass* satellite of a hot Jupiter gives K ~ 70 m/s, and a
10 M_Earth one gives ~700 m/s. Both are larger than the 246 m/s Hoy et al. actually
detected. On signal strength alone the close-in case is not merely feasible, it is easier.

Three things then have to be true, and this module tests each against real targets.

**1. The satellite must exist.** A close-in giant's Hill sphere is tiny -- a few R_Jup --
so the whole stable zone spans satellite periods of hours, and it sits deep inside the
planet's tidal reach. Whether anything survives there is decided by the planet's *spin*,
via ``satellites.survival_window``: a planet tidally locked to its star has its corotation
radius outside the Hill-stability limit, so every stable satellite is inside corotation and
spirals in. Young planets have not been despun yet. That is why "early formation" is the
right instinct and not a detail -- it is the entire mechanism.

**2. The planet must be observable.** This is where the method has to change. Hot Jupiters
cannot be spatially resolved, so the slit trick that isolates CD-35 2722 B is unavailable.
The substitute is high-resolution cross-correlation spectroscopy, which separates planet
from star in *velocity* instead of in *position* -- and that requires the planet's
line-of-sight velocity to sweep 30-60 km/s during one observation
(``satellites.hrccs_velocity_swing_kms``).

**3. The signal must be separable from the planet itself.** A satellite whose period is
hours has to be told apart from a planet whose rotation is also hours
(``satellites.activity_confusion``). For CD-35 2722 B that ratio is 260. Here it is ~1.

Requirements 1 and 2 pull in opposite directions in the same variable, and the trade is a
clean power law: ``tau_spin_down ~ M_star t_obs^3 / Delta_v^3``. Whether they overlap at
all comes down to the planetary tidal quality factor Q, which is the least-constrained
number in the problem -- hence ``q_planet`` is an explicit argument, not a constant.

Prior art, read into ``papers/`` and none of it previously in this project:

- **Tokadjian & Piro 2023** (arXiv:2302.04646) -- the closest published analogue. Derives
  exomoon "stability niches" for hundreds of innermost exoplanets and finds a moon of ~1%
  of the planet's mass can synchronise the planet *to itself*, overpowering the star. Of
  their sample only **26 systems have any niche, and 5 a niche wider than 1 R_p**. They
  also state the conclusion this module's naive tidal clock gets backwards: **massive moons
  are more likely to survive.**
- **Martinez, Stone & Munoz 2020** (arXiv:2008.13778) -- moons do not survive
  high-eccentricity (ZLK) migration, and massive moons prevent it outright. So a satellite
  around a hot Jupiter is a **migration-channel discriminant**: finding one argues the
  planet arrived by disc migration, not by high-eccentricity migration.
- **arXiv:2509.13263 (2025)** -- after *disc* migration both prograde and retrograde moons
  can survive, retrograde 5x more often; under coplanar secular excitation only massive
  (>10 M_Earth) retrograde moons make it.

The scientific prize is therefore not the moon. It is that a **detection or a clean upper
limit around a young hot Jupiter distinguishes how that hot Jupiter got there** -- and RV
is most sensitive to exactly the massive satellites those papers say are the survivors.
"""

from __future__ import annotations

import warnings
from typing import Any

from .satellites import (
    HRCCS_MIN_SWING_KMS,
    activity_confusion,
    hrccs_velocity_swing_kms,
    min_detectable_sat_mearth,
    moon_can_synchronise_planet,
    satellite_period_d,
    survival_window,
)

NEA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP"

QUERY = """
SELECT pl_name, hostname, st_age, pl_orbsmax, pl_orbper, pl_bmassj, pl_radj,
       st_mass, sy_dist, sy_kmag
FROM pscomppars
WHERE st_age IS NOT NULL AND st_age < {max_age_gyr}
  AND pl_orbsmax IS NOT NULL AND pl_orbsmax < 2.0
  AND pl_bmassj IS NOT NULL AND pl_radj IS NOT NULL AND st_mass IS NOT NULL
  AND (pl_bmassj > 0.05 OR pl_radj > 0.4)
ORDER BY pl_orbsmax DESC
"""

HRCCS_RV_PRECISION_MS = 1000.0
"""Per-epoch precision assumed for a planet velocity from cross-correlation, m/s.

Deliberately crude and deliberately optimistic. HRCCS quotes K_p to ~1-3 km/s; this takes
the good end. It is a *placeholder with a stated value* rather than a hidden assumption,
because M8's conclusion does not turn on it -- requirement 1 or 2 fails first for every
real target. If a target ever passes both, this number becomes the thing to measure.
"""


def run_closein(
    max_age_myr: float = 200.0,
    t_obs_hr: float = 8.0,
    q_planet: float = 1e5,
    p_spin_primordial_hr: float = 10.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Test survival and observability against every known young close-in giant."""
    import pyvo

    warnings.filterwarnings("ignore")
    svc = pyvo.dal.TAPService(NEA_TAP)
    table = svc.search(QUERY.format(max_age_gyr=max_age_myr / 1000.0)).to_table()

    rows: list[dict[str, Any]] = []
    for rec in table:
        try:
            m_p = float(rec["pl_bmassj"])
            r_p = float(rec["pl_radj"])
            m_s = float(rec["st_mass"])
            a = float(rec["pl_orbsmax"])
            age = float(rec["st_age"]) * 1000.0
            p_orb = float(rec["pl_orbper"]) if rec["pl_orbper"] else None
        except (TypeError, ValueError):
            continue

        win = survival_window(
            m_p, r_p, m_s, a, age,
            p_spin_primordial_d=p_spin_primordial_hr / 24.0,
            p_orbit_d=p_orb, q_planet=q_planet,
        )
        swing = hrccs_velocity_swing_kms(a, m_s, t_obs_hr)
        survivable = win.is_open
        observable = swing >= HRCCS_MIN_SWING_KMS

        if survivable:
            p_out = satellite_period_d(win.a_out_au, m_p)
            m_min = min_detectable_sat_mearth(m_p, win.a_out_au, HRCCS_RV_PRECISION_MS)
            confusion = activity_confusion(p_out, win.p_spin_d)
        else:
            p_out, m_min, confusion = float("nan"), float("nan"), float("nan")

        if survivable and observable:
            verdict = "BOTH - real candidate"
        elif survivable:
            verdict = f"survivable, not observable (dv {swing:.0f} < {HRCCS_MIN_SWING_KMS:.0f} km/s)"
        elif observable:
            verdict = "observable, but no satellite survives"
        else:
            verdict = "neither"

        rows.append({
            "name": str(rec["pl_name"]),
            "age_myr": age,
            "sma_au": a,
            "orbital_period_d": p_orb,
            "m_planet_mjup": m_p,
            "r_planet_rjup": r_p,
            "m_star_msun": m_s,
            "distance_pc": float(rec["sy_dist"]) if rec["sy_dist"] else None,
            "k_mag": float(rec["sy_kmag"]) if rec["sy_kmag"] else None,
            "synchronised": win.synchronised,
            "spin_down_myr": win.spin_down_yr / 1e6,
            "p_spin_d": win.p_spin_d,
            "corotation_au": win.corotation_au,
            "roche_au": win.roche_au,
            "stability_au": win.stability_au,
            "window_dex": win.decades,
            "sat_period_outer_d": p_out,
            "activity_confusion": confusion,
            "moon_could_sync_planet": moon_can_synchronise_planet(win.p_spin_d, p_orb or 1e9),
            "swing_kms": swing,
            "min_sat_mearth": m_min,
            "survivable": survivable,
            "observable": observable,
            "verdict": verdict,
        })

    rows.sort(key=lambda r: (-r["survivable"], -r["swing_kms"]))
    n_both = sum(r["survivable"] and r["observable"] for r in rows)
    meta = {
        "max_age_myr": max_age_myr,
        "t_obs_hr": t_obs_hr,
        "q_planet": q_planet,
        "hrccs_min_swing_kms": HRCCS_MIN_SWING_KMS,
        "n_targets": len(rows),
        "n_survivable": sum(r["survivable"] for r in rows),
        "n_observable": sum(r["observable"] for r in rows),
        "n_both": n_both,
        "conclusion": _conclusion(rows, q_planet, n_both),
    }
    return rows, meta


def _conclusion(rows: list[dict[str, Any]], q_planet: float, n_both: int) -> list[str]:
    if n_both:
        names = ", ".join(r["name"] for r in rows if r["survivable"] and r["observable"])
        return [
            f"{n_both} target(s) satisfy both requirements at Q_p = {q_planet:.0e}: {names}.",
            ("Q_p is the least-constrained parameter here; rerun across 1e5-1e7 before"
             " trusting this list."),
        ]
    return [
        "No target satisfies both requirements at this Q_p.",
        ("Survival needs a large orbit, cross-correlation needs a small one, and the trade"
         " is tau_spin_down ~ M_star t^3 / dv^3 -- a factor 2 in observability costs 8 in"
         " survival time. Raising Q_p moves the survival boundary in; try --q-planet 1e6."),
    ]
