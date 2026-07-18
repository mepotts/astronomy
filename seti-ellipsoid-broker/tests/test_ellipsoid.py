"""TDD spec for the SN 1987A SETI Ellipsoid crossing math (BUILD-PLAN.md task 5).

Written BEFORE the real `ellipsoid.py` body (the M0 module ships placeholders). These
tests pin the SN 1987A constants and define the *required* behaviour of `signed_offset`
S(t) and `crossing_epoch`:

  * A synthetic star at a known geometry near the SN 1987A line of sight must yield a
    crossing epoch inside the documented ~2026-2028 peak window (DATA-SOURCES.md S5,
    SPEC.md kill-criteria "scientific sunset").
  * `signed_offset` must be NEGATIVE inside the shell, POSITIVE outside, ~0 on it, and
    must change sign exactly at the crossing epoch.
  * Edge cases: a star exactly on the SN line of sight (theta=0) crosses at the reference
    epoch; monotonicity in distance and angle; input guards.

The geometry (DATA-SOURCES.md S5):
    foci = {Earth, SN 1987A};  d = Earth->SN baseline.
    d2 = sqrt(r_E^2 + d^2 - 2 r_E d cos theta)   (law of cosines, SN->star)
    shell:  r_E + d2 = d + c * t      (t = elapsed years since the 1987-02-23 observation)
    S(t)  = (d + c * t) - (r_E + d2)   (>0 once the shell has passed the star; grows at +c)
    t_cross solves S = 0  ->  crossing_year = ref_year + (r_E + d2 - d)/c
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

from seti_ellipsoid_broker import ellipsoid as E


# --------------------------------------------------------------------------------------
# Constants are REAL and load-bearing (DATA-SOURCES.md S5). Pin them so a silent edit to
# the SN 1987A geometry breaks a test rather than the science.
# --------------------------------------------------------------------------------------

def test_sn1987a_constants_pinned():
    assert E.SN1987A_RA_DEG == pytest.approx(83.86658, abs=1e-4)
    assert E.SN1987A_DEC_DEG == pytest.approx(-69.26961, abs=1e-4)
    assert E.SN1987A_DISTANCE_KPC == pytest.approx(51.4, abs=0.05)
    assert E.REFERENCE_EPOCH == "1987-02-23"
    # Semi-major axis grows at c/2 (half a light-year per calendar year).
    assert E.SEMI_MAJOR_AXIS_GROWTH_LY_PER_YR == pytest.approx(0.5)


def test_reference_epoch_decimal_year():
    """The reference epoch helper must agree with astropy's decimal year for 1987-02-23."""
    expected = Time("1987-02-23", format="iso", scale="utc").jyear
    assert E.reference_epoch_jyear() == pytest.approx(expected, abs=1e-3)
    # And it is early 1987.
    assert 1987.1 < E.reference_epoch_jyear() < 1987.2


# --------------------------------------------------------------------------------------
# Helper: independent reference implementation of the documented closed form, used to
# cross-check the package against the math written in DATA-SOURCES.md S5. Distances in
# light-years, time in years (so c = 1 ly/yr).
# --------------------------------------------------------------------------------------

_KPC_TO_LY = (1.0 * u.kpc).to_value(u.lyr)
_PC_TO_LY = (1.0 * u.pc).to_value(u.lyr)


def _ref_crossing_year(distance_pc: float, sep_deg: float) -> float:
    d_ly = E.SN1987A_DISTANCE_KPC * _KPC_TO_LY
    r_ly = distance_pc * _PC_TO_LY
    theta = math.radians(sep_deg)
    d2 = math.sqrt(r_ly**2 + d_ly**2 - 2.0 * r_ly * d_ly * math.cos(theta))
    delta_years = (r_ly + d2 - d_ly)  # c = 1 ly/yr
    return E.reference_epoch_jyear() + delta_years


def _sep_from_sn(distance_pc: float, sep_deg: float):
    """Build a SkyCoord at angular separation `sep_deg` from SN 1987A (offset in dec)."""
    return SkyCoord(
        ra=E.SN1987A_RA_DEG * u.deg,
        dec=(E.SN1987A_DEC_DEG + sep_deg) * u.deg,
        distance=distance_pc * u.pc,
        frame="icrs",
    )


# --------------------------------------------------------------------------------------
# Core acceptance test: a synthetic star near the SN line of sight crosses in ~2026-2028.
# --------------------------------------------------------------------------------------

def test_synthetic_star_crosses_in_peak_window():
    """A star whose r_E*(1-cos theta) ~ 40 ly must cross in the 2026-2028 peak window.

    Solve for the distance that puts the crossing near 'now' at a chosen small angle, then
    assert the package agrees and the epoch lands inside the documented window.
    """
    sep_deg = 8.0
    theta = math.radians(sep_deg)
    # Want delta ~ (2027 - 1987.15) = ~39.85 ly of ellipsoid depth.
    # delta ~ r_ly * (1 - cos theta)  ->  r_ly = delta / (1 - cos theta)
    target_delta_ly = 2027.0 - E.reference_epoch_jyear()
    r_ly = target_delta_ly / (1.0 - math.cos(theta))
    distance_pc = r_ly / _PC_TO_LY

    t_cross = E.crossing_epoch(distance_pc, sep_deg)

    # Lands in the documented peak window.
    assert 2026.0 <= t_cross <= 2028.0
    # Agrees with the independent closed-form reference to within a few days.
    assert t_cross == pytest.approx(_ref_crossing_year(distance_pc, sep_deg), abs=0.02)


def test_crossing_epoch_accepts_skycoord():
    """crossing_epoch must also accept a SkyCoord (carrying distance) for convenience."""
    sep_deg = 8.0
    theta = math.radians(sep_deg)
    target_delta_ly = 2027.0 - E.reference_epoch_jyear()
    distance_pc = (target_delta_ly / (1.0 - math.cos(theta))) / _PC_TO_LY
    coord = _sep_from_sn(distance_pc, sep_deg)

    t_from_coord = E.crossing_epoch(coord)
    t_from_scalars = E.crossing_epoch(distance_pc, sep_deg)
    assert t_from_coord == pytest.approx(t_from_scalars, abs=0.01)


# --------------------------------------------------------------------------------------
# signed_offset sign behaviour.
# --------------------------------------------------------------------------------------

def test_signed_offset_sign_changes_at_crossing():
    """S(t) < 0 inside the shell (before crossing), > 0 after, ~0 at the crossing epoch."""
    distance_pc = 400.0
    sep_deg = 12.0
    t_cross = E.crossing_epoch(distance_pc, sep_deg)

    s_before = E.signed_offset(distance_pc, sep_deg, t_cross - 5.0)
    s_at = E.signed_offset(distance_pc, sep_deg, t_cross)
    s_after = E.signed_offset(distance_pc, sep_deg, t_cross + 5.0)

    assert s_before < 0.0          # shell hasn't reached the star yet -> star "inside"
    assert s_at == pytest.approx(0.0, abs=1e-6)
    assert s_after > 0.0           # shell has passed the star -> star "outside"
    assert s_before < s_at < s_after  # monotonic increasing in time


def test_signed_offset_units_are_light_years_and_grow_at_c():
    """S decreases by ~c*dt (one ly per year) as the shell expands; check the slope."""
    distance_pc = 400.0
    sep_deg = 12.0
    s0 = E.signed_offset(distance_pc, sep_deg, 2026.0)
    s1 = E.signed_offset(distance_pc, sep_deg, 2027.0)
    # One calendar year advances the shell by c*1yr = 1 ly, so S rises by ~1 ly.
    assert (s1 - s0) == pytest.approx(1.0, abs=1e-3)


# --------------------------------------------------------------------------------------
# Edge cases.
# --------------------------------------------------------------------------------------

def test_star_on_line_of_sight_crosses_at_reference_epoch():
    """theta=0: d2 = d - r_E, so r_E + d2 - d = 0 -> crossing == reference epoch.

    (A star directly between us and the SN sees the flash at the same instant its light
    reaching us was emitted; its re-broadcast arrives exactly when the SN light did.)
    """
    t_cross = E.crossing_epoch(500.0, 0.0)
    assert t_cross == pytest.approx(E.reference_epoch_jyear(), abs=1e-3)


def test_farther_star_at_fixed_angle_crosses_later():
    """At fixed angle, crossing epoch increases monotonically with distance."""
    sep_deg = 10.0
    t_near = E.crossing_epoch(300.0, sep_deg)
    t_mid = E.crossing_epoch(600.0, sep_deg)
    t_far = E.crossing_epoch(900.0, sep_deg)
    assert t_near < t_mid < t_far


def test_wider_angle_at_fixed_distance_crosses_later():
    """At fixed distance, a larger angle off the SN line of sight crosses later."""
    distance_pc = 600.0
    t_small = E.crossing_epoch(distance_pc, 4.0)
    t_large = E.crossing_epoch(distance_pc, 16.0)
    assert t_small < t_large


def test_crossing_window_from_parallax_error():
    """The +/- crossing uncertainty must scale with fractional distance error.

    A 10% distance error should give a ~10%-of-depth window (symmetric, in years).
    """
    distance_pc = 400.0
    sep_deg = 12.0
    parallax_over_error = 10.0  # -> 10% fractional distance error
    window = E.crossing_window_years(distance_pc, sep_deg, parallax_over_error)
    assert window > 0.0
    # Tighter parallax (smaller error) => tighter window.
    tighter = E.crossing_window_years(distance_pc, sep_deg, 50.0)
    assert tighter < window


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        E.crossing_epoch(-1.0, 5.0)
    with pytest.raises(ValueError):
        E.crossing_epoch(100.0, -5.0)


def test_vectorized_inputs_supported():
    """crossing_epoch should accept array-like distance/sep and return an array."""
    distances = np.array([300.0, 600.0, 900.0])
    seps = np.array([10.0, 10.0, 10.0])
    out = E.crossing_epoch(distances, seps)
    out = np.asarray(out)
    assert out.shape == (3,)
    assert out[0] < out[1] < out[2]
