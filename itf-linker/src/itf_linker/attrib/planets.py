"""Approximate planetary positions for the perturbed propagator.

Two ingredients, both from primary sources and both chosen for what the consumer
actually needs -- the *perturbing acceleration* on an asteroid, not the planet's own
ephemeris:

* **Mean Keplerian elements + rates** from JPL's "Approximate Positions of the Major
  Planets", Table 1 (valid 1800 AD - 2050 AD), fetched and transcribed verbatim from
  https://ssd.jpl.nasa.gov/planets/approx_pos.html on 2026-08-16. Earth appears as the
  Earth-Moon barycentre ("EM Bary"), which is the right body for perturbing a
  main-belt asteroid. JPL quotes worst-case position errors of tens of arcseconds over
  1800-2050 -- for a perturber at >= 1 AU from the target that is a fractional error of
  order 1e-3 in the perturbing term, which is itself a ~1e-3 correction, so the induced
  target error is ~arcseconds over 15 years. That error is not assumed small: it is
  *measured* against JPL Horizons in ``scripts/m8_calibration.py`` and absorbed into the
  frozen gate envelope.
* **GM values** from DE440 (Park, Folkner, Williams & Boggs 2021, AJ 161, 105,
  Table 2), expressed as ratios to the DE440 solar GM and scaled by this project's own
  ``GM_SUN`` (Gauss's constant squared) so the Sun term and the perturber terms share
  one unit system. Pluto is omitted: GM ~ 1e-9 of the Sun's at 30+ AU changes a
  main-belt position by far less than the mean-element error already does.

The frame is heliocentric ICRS-equatorial (the table's J2000-ecliptic output rotated by
the same obliquity matrix the rest of ``attrib`` uses), and the time argument is TT
(the table wants Teph; TT-TDB < 2 ms, which is 9 orders below the element accuracy).
"""

from __future__ import annotations

import numpy as np

from ..link.geometry import GM_SUN
from .core import ECL_TO_EQ

#: DE440 GM values, km^3/s^2 (Park et al. 2021, Table 2). "emb" is Earth + Moon.
GM_SUN_KM3_S2 = 132712440041.279419
GM_KM3_S2 = {
    "mercury": 22031.868551,
    "venus": 324858.592000,
    "emb": 398600.435507 + 4902.800118,
    "mars": 42828.375816,
    "jupiter": 126712764.100000,
    "saturn": 37940584.841800,
    "uranus": 5794556.400000,
    "neptune": 6836527.100580,
}

PLANET_NAMES = tuple(GM_KM3_S2)

#: Perturber GMs in this project's units (AU^3/day^2), via the DE440 mass ratios.
GM_PLANETS = np.array([GM_SUN * v / GM_SUN_KM3_S2 for v in GM_KM3_S2.values()])

#: JPL approximate mean elements, Table 1 (1800 AD - 2050 AD). Columns:
#: a (AU), da/dCy, e, de/dCy, I (deg), dI/dCy, L (deg), dL/dCy,
#: long.peri (deg), rate, long.node (deg), rate. Rows follow :data:`PLANET_NAMES`.
MEAN_ELEMENTS = np.array([
    [0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749,
     252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081],
    [0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890,
     181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418],
    [1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668,
     100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0],
    [1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131,
     -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343],
    [5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714,
     34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106],
    [9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609,
     49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794],
    [19.18916464, -0.00196176, 0.04725744, -0.00004397, 0.77263783, -0.00242939,
     313.23810451, 428.48202785, 170.95427630, 0.40805281, 74.01692503, 0.04240589],
    [30.06992276, 0.00026291, 0.00859048, 0.00005105, 1.77004347, 0.00035372,
     -55.12002969, 218.45945325, 44.96476227, -0.32241464, 131.78422574, -0.00508664],
])

#: The table's validity window, MJD(TT). 1800-01-01 and 2050-01-01. Integrating outside
#: it would silently degrade; the propagator refuses instead.
VALID_MJD_TT = (-21504.0, 88069.0)


def planet_positions(mjd_tt: np.ndarray) -> np.ndarray:
    """Heliocentric ICRS-equatorial perturber positions, AU, shape ``(n_t, 8, 3)``.

    Vectorised over time only -- the eight planets are computed together per instant.
    Kepler's equation is solved by Newton iteration from the standard ``M + e sin M``
    start; eight iterations leave the residual below 1e-14 rad for every planetary
    eccentricity in the table (e <= 0.21).
    """
    t = np.atleast_1d(np.asarray(mjd_tt, dtype=float))
    if t.size and (t.min() < VALID_MJD_TT[0] or t.max() > VALID_MJD_TT[1]):
        raise ValueError(
            f"epoch outside the 1800-2050 validity of the JPL mean elements: "
            f"[{t.min():.1f}, {t.max():.1f}] MJD(TT)"
        )
    T = (t + 2400000.5 - 2451545.0) / 36525.0  # centuries past J2000.0

    el = MEAN_ELEMENTS
    a = el[:, 0] + el[:, 1] * T[:, None]
    e = el[:, 2] + el[:, 3] * T[:, None]
    inc = np.radians(el[:, 4] + el[:, 5] * T[:, None])
    L = el[:, 6] + el[:, 7] * T[:, None]
    varpi = el[:, 8] + el[:, 9] * T[:, None]
    node = np.radians(el[:, 10] + el[:, 11] * T[:, None])
    omega = np.radians(varpi) - node

    M = np.radians(((L - varpi + 180.0) % 360.0) - 180.0)
    E = M + e * np.sin(M)
    for _ in range(8):
        E = E - (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))

    xp = a * (np.cos(E) - e)
    yp = a * np.sqrt(1.0 - e * e) * np.sin(E)
    co, so = np.cos(omega), np.sin(omega)
    cn, sn = np.cos(node), np.sin(node)
    ci, si = np.cos(inc), np.sin(inc)
    x_ecl = (co * cn - so * sn * ci) * xp + (-so * cn - co * sn * ci) * yp
    y_ecl = (co * sn + so * cn * ci) * xp + (-so * sn + co * cn * ci) * yp
    z_ecl = (so * si) * xp + (co * si) * yp
    ecl = np.stack([x_ecl, y_ecl, z_ecl], axis=-1)
    return np.einsum("ij,tpj->tpi", ECL_TO_EQ, ecl)
