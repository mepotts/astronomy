"""The published system is the fixture.

Every number Hoy et al. print that this module can compute independently is asserted here.
If these fail, the M7/M8 target rankings built on top are worthless -- which is the same
discipline ``test_feasibility.py`` applies to the RV amplitude.
"""

from __future__ import annotations

import math

import pytest

from exosat_rv.analysis.satellites import (
    HRCCS_MIN_SWING_KMS,
    activity_amplitude_ms,
    activity_confusion,
    corotation_radius_au,
    hoy_calibrated_threshold_ms,
    hrccs_velocity_swing_kms,
    lazzoni_threshold_ms,
    mean_density_cgs,
    min_detectable_sat_mearth,
    moon_can_synchronise_planet,
    moon_inspiral_yr,
    roche_limit_au,
    satellite_period_d,
    satellite_sma_au,
    survival_window,
    tidal_spin_down_yr,
)
from exosat_rv.config import PUBLISHED

R_JUP_AU = 7.1492e7 / 1.495978707e11


# --- reproducing the paper -------------------------------------------------------------


def test_reproduces_the_published_roche_limit() -> None:
    """Paper: 8.4 R_host, from a 1.2 R_Jup / 37 M_Jup host and a Saturn-density satellite.

    Host density must be *derived*. Defaulting it to Jupiter's 1.33 g/cm^3 gives 3.1
    R_host and looks perfectly plausible -- the failure is silent, which is why this is
    pinned rather than trusted.
    """
    limit_au = roche_limit_au(37.0, 1.2, rho_sat_cgs=0.687)
    assert limit_au / R_JUP_AU / 1.2 == pytest.approx(PUBLISHED.roche_limit_rbd, rel=0.02)


def test_host_mean_density_is_that_of_a_brown_dwarf_not_a_planet() -> None:
    """37 M_Jup in 1.2 R_Jup is ~27 g/cm^3; the paper quotes 29."""
    assert mean_density_cgs(37.0, 1.2) == pytest.approx(29.0, rel=0.10)
    # 1.24, NOT Jupiter's quoted 1.326. R_JUP_M here is the *equatorial* radius
    # (71,492 km), the usual astronomical unit; the 1.326 figure uses the *volumetric
    # mean* radius (69,911 km). A 2.3% radius difference is a 7% density difference,
    # and it propagates into the Roche limit as its cube root.
    assert mean_density_cgs(1.0, 1.0) == pytest.approx(1.24, rel=0.02)


def test_reproduces_the_published_satellite_semi_major_axes() -> None:
    """Kepler's third law about the *companion*, not about the star."""
    assert satellite_sma_au(PUBLISHED.sat1_period_d, PUBLISHED.bd_mass_mjup) == pytest.approx(
        PUBLISHED.sat1_sma_au, rel=0.02
    )
    assert satellite_sma_au(PUBLISHED.sat2_period_d, PUBLISHED.bd_mass_mjup) == pytest.approx(
        PUBLISHED.sat2_sma_au, rel=0.02
    )


def test_period_and_sma_round_trip() -> None:
    for period in (0.5, 12.1, 87.46, 169.45, 3650.0):
        a = satellite_sma_au(period, 37.0)
        assert satellite_period_d(a, 37.0) == pytest.approx(period, rel=1e-9)


def test_hoy_threshold_is_anchored_on_the_achieved_precision() -> None:
    """At CD-35 2722 B's own K = 12.01 the 1-sigma value must be the paper's 31.44 m/s."""
    assert hoy_calibrated_threshold_ms(12.01, snr=1.0) == pytest.approx(
        PUBLISHED.rv_err_nodding_ms, rel=1e-6
    )


def test_the_real_instrument_beat_the_published_forecast() -> None:
    """Lazzoni et al. 2022 predicted ~50 m/s at K = 12.01; the campaign reached 31.44.

    Anchoring target selection on the forecast rather than the achievement would
    under-admit targets by a factor of 1.6 in precision.
    """
    assert lazzoni_threshold_ms(12.01) == pytest.approx(50.3, rel=0.02)
    assert hoy_calibrated_threshold_ms(12.01, snr=1.0) < lazzoni_threshold_ms(12.01)


def test_detected_satellite_sits_above_the_threshold_it_was_found_with() -> None:
    """Sanity: the method must be able to find what it did find."""
    m_min = min_detectable_sat_mearth(
        PUBLISHED.bd_mass_mjup, PUBLISHED.sat1_sma_au, hoy_calibrated_threshold_ms(12.01)
    )
    detected = PUBLISHED.sat1_msini_mjup * 317.828
    assert m_min < detected


def test_rotation_cannot_be_confused_with_the_published_signals() -> None:
    """The paper's own rotation argument, as a number.

    v sin i = 9.58 km/s gives P_rot <= 0.65 d against satellite periods of 87 and 169 d.
    A few per cent of spot coverage on such a fast rotator produces ~190 m/s -- comparable
    to the 246 m/s detection -- so *amplitude* does not clear the target. Only the 130x
    period separation does.
    """
    assert activity_amplitude_ms(PUBLISHED.bd_vsini_kms) > 100.0
    for period in (PUBLISHED.sat1_period_d, PUBLISHED.sat2_period_d):
        assert activity_confusion(period, PUBLISHED.bd_max_prot_days) > 10.0


# --- the close-in physics --------------------------------------------------------------


def test_old_hot_jupiter_has_no_satellite_survival_window() -> None:
    """A synchronised close-in giant puts corotation outside the stability limit.

    This is the Barnes & O'Brien (2002) result and the reason the naive version of the
    "apply it to hot Jupiters" idea fails: every dynamically stable orbit is inside
    corotation, so every satellite inspirals.
    """
    win = survival_window(1.0, 1.2, 1.0, 0.05, age_myr=1000.0)
    assert win.synchronised
    assert win.corotation_au > win.stability_au
    assert not win.is_open


def test_young_close_in_giant_can_have_a_window() -> None:
    """The same planet, young enough not to have been despun, keeps a window open."""
    win = survival_window(1.0, 1.2, 1.0, 0.1, age_myr=10.0)
    assert not win.synchronised
    assert win.is_open


def test_spin_down_time_scales_as_the_sixth_power_of_separation() -> None:
    """a^6 is why the answer flips over a factor of ~3 in orbital distance."""
    near = tidal_spin_down_yr(1.0, 1.2, 1.0, 0.05, 10.0 / 24.0)
    far = tidal_spin_down_yr(1.0, 1.2, 1.0, 0.10, 10.0 / 24.0)
    assert far / near == pytest.approx(2.0**6, rel=1e-6)


def test_massive_moons_inspiral_fastest_under_stellar_tides_alone() -> None:
    """...and Tokadjian & Piro 2023 say the opposite once the moon torques back.

    Both are recorded because the module reports both regimes rather than choosing. This
    pins only the direction of the naive clock, so that a future change that silently
    flips it is caught.
    """
    light = moon_inspiral_yr(0.1, 1.0, 1.2, 3.0 * R_JUP_AU)
    heavy = moon_inspiral_yr(10.0, 1.0, 1.2, 3.0 * R_JUP_AU)
    assert heavy < light
    # Tokadjian & Piro eq. 9: a moon-synchronised state needs P_spin < P_orb / 5.05.
    assert moon_can_synchronise_planet(p_spin_d=0.4, p_orbit_d=6.0)
    assert not moon_can_synchronise_planet(p_spin_d=3.0, p_orbit_d=6.0)


def test_corotation_radius_is_where_satellite_period_equals_spin_period() -> None:
    a = corotation_radius_au(1.0, 0.5)
    assert satellite_period_d(a, 1.0) == pytest.approx(0.5, rel=1e-9)


def test_hrccs_needs_a_close_orbit_and_survival_needs_a_wide_one() -> None:
    """The structural tension of M8, as an assertion.

    Cross-correlation requires the planet's velocity to sweep >= 30 km/s in a night, which
    only close orbits do; satellite survival requires a wide enough orbit that the star has
    not despun the planet. The trade is tau ~ 1/dv^3.
    """
    close = hrccs_velocity_swing_kms(0.05, 1.0, 8.0)
    wide = hrccs_velocity_swing_kms(0.30, 1.0, 8.0)
    assert close > HRCCS_MIN_SWING_KMS > wide

    t_close = tidal_spin_down_yr(1.0, 1.2, 1.0, 0.05, 10.0 / 24.0)
    t_wide = tidal_spin_down_yr(1.0, 1.2, 1.0, 0.30, 10.0 / 24.0)
    assert t_wide > t_close


def test_the_survival_observability_trade_is_an_inverse_cube() -> None:
    """tau_spin_down ~ M_star t^3 / dv^3: doubling observability costs 8x in survival."""
    a1, a2 = 0.05, 0.05 * math.sqrt(2.0)  # dv ~ 1/a^2, so this halves dv
    dv_ratio = hrccs_velocity_swing_kms(a1, 1.0, 8.0) / hrccs_velocity_swing_kms(a2, 1.0, 8.0)
    tau_ratio = tidal_spin_down_yr(1.0, 1.2, 1.0, a2, 0.4) / tidal_spin_down_yr(
        1.0, 1.2, 1.0, a1, 0.4
    )
    assert dv_ratio == pytest.approx(2.0, rel=0.02)
    assert tau_ratio == pytest.approx(dv_ratio**3, rel=0.05)


def test_close_in_satellite_periods_collide_with_the_planet_rotation() -> None:
    """Why the close-in case is hard even where it is possible.

    A close-in giant's whole stable zone spans satellite periods of hours, and the planet
    spins in hours too -- so ``activity_confusion`` lands near the danger zone, where
    CD-35 2722 B's is 260. The inner edge of the survival window *is* corotation, where
    the two periods are equal by construction.
    """
    win = survival_window(1.0, 1.2, 1.0, 0.1, age_myr=10.0)
    assert win.is_open
    p_inner = satellite_period_d(win.a_in_au, 1.0)
    assert activity_confusion(p_inner, win.p_spin_d) < 0.1
