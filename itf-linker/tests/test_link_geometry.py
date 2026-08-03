"""Pin the geometry M3's linker rests on.

The tests that matter here are the ones with an *external* reference: a Kepler propagation
that conserves the constants of motion, an ephemeris that agrees with astropy's own
``SkyCoord`` machinery, and a round trip through the distance/velocity solve that returns
the state it started from. A linker whose geometry is subtly wrong does not fail loudly --
it just finds nothing, or finds nonsense, and both look like "the ITF is hard".
"""

from __future__ import annotations

import numpy as np
import pytest

from itf_linker.link.geometry import (
    GM_SUN,
    MIN_TOPOCENTRIC_DISTANCE_AU,
    R_EARTH_AU,
    earth_heliocentric_posvel,
    propagate_kepler,
    solve_rho,
    state_from_hypothesis,
    state_to_elements,
    stumpff,
    topocentric_offset,
    unit_vector_rates,
    unit_vectors,
)

# --- directions -------------------------------------------------------------------

def test_unit_vectors_are_unit_and_point_the_right_way():
    v = unit_vectors(np.array([0.0, 90.0, 0.0]), np.array([0.0, 0.0, 90.0]))
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0)
    assert np.allclose(v[0], [1, 0, 0], atol=1e-12)
    assert np.allclose(v[1], [0, 1, 0], atol=1e-12)
    assert np.allclose(v[2], [0, 0, 1], atol=1e-12)


def test_unit_vector_rate_matches_a_finite_difference():
    """The analytic d(rho_hat)/dt must equal a numerical derivative of rho_hat."""
    ra, dec = 123.456, -17.25
    mu_a, mu_d = 0.31, -0.12          # deg/day, great-circle in RA
    dt = 1e-5
    got = unit_vector_rates(np.array([ra]), np.array([dec]), np.array([mu_a]), np.array([mu_d]))
    nxt = unit_vectors(
        np.array([ra + mu_a / np.cos(np.radians(dec)) * dt]), np.array([dec + mu_d * dt])
    )
    cur = unit_vectors(np.array([ra]), np.array([dec]))
    assert np.allclose(got[0], (nxt[0] - cur[0]) / dt, rtol=1e-4, atol=1e-9)


def test_rate_is_great_circle_not_coordinate():
    """A cos(dec) factor dropped here would inflate every high-declination rate."""
    fast = unit_vector_rates(
        np.array([0.0]), np.array([80.0]), np.array([0.5]), np.array([0.0])
    )
    slow = unit_vector_rates(
        np.array([0.0]), np.array([0.0]), np.array([0.5]), np.array([0.0])
    )
    assert np.linalg.norm(fast[0]) == pytest.approx(np.linalg.norm(slow[0]), rel=1e-12)


# --- observers --------------------------------------------------------------------

def test_earth_is_about_one_au_from_the_sun_and_moving_at_the_right_speed():
    pos, vel = earth_heliocentric_posvel(np.array([60000.0, 60100.0, 60200.0]))
    r = np.linalg.norm(pos, axis=1)
    assert np.all((r > 0.98) & (r < 1.02))
    speed = np.linalg.norm(vel, axis=1)
    assert np.all((speed > 0.0165) & (speed < 0.0175))   # ~2*pi/365 AU/day


def test_earth_position_agrees_with_astropys_own_ephemeris_path():
    from astropy.coordinates import get_body_barycentric
    from astropy.time import Time

    t = Time([60000.0], format="mjd", scale="utc")
    pos, _ = earth_heliocentric_posvel(np.array([60000.0]))
    expect = (
        get_body_barycentric("earth", t.tdb) - get_body_barycentric("sun", t.tdb)
    ).xyz.to("AU").value.T
    assert np.allclose(pos, expect, atol=1e-9)


def test_topocentric_offset_has_the_right_magnitude_and_rotates():
    mjd = np.array([60000.0, 60000.25])
    pos, vel = topocentric_offset(mjd, np.array([203.744, 203.744]),
                                  np.array([0.936241, 0.936241]),
                                  np.array([0.351543, 0.351543]))
    assert np.allclose(np.linalg.norm(pos, axis=1), R_EARTH_AU, rtol=1e-3)
    # Six hours apart the site has swung round by ~90 degrees.
    cos_angle = np.dot(pos[0], pos[1]) / (np.linalg.norm(pos[0]) * np.linalg.norm(pos[1]))
    assert -0.2 < cos_angle < 0.4
    assert np.linalg.norm(vel[0]) == pytest.approx(2 * np.pi * R_EARTH_AU * 0.936241, rel=0.02)


def test_geocentric_site_has_no_offset():
    pos, vel = topocentric_offset(np.array([60000.0]), np.array([0.0]),
                                  np.array([0.0]), np.array([0.0]))
    assert np.allclose(pos, 0.0)
    assert np.allclose(vel, 0.0)


# --- the distance hypothesis ------------------------------------------------------

def test_solve_rho_lands_exactly_on_the_hypothesised_sphere():
    obs = np.array([[1.0, 0.0, 0.0]])
    direction = unit_vectors(np.array([30.0]), np.array([10.0]))
    rho, valid = solve_rho(obs, direction, np.array([2.5]))
    assert valid[0]
    assert np.linalg.norm(obs[0] + rho[0] * direction[0]) == pytest.approx(2.5, abs=1e-12)


def test_solve_rho_takes_the_far_root():
    """Looking back towards the Sun, the near intersection is behind us."""
    obs = np.array([[2.0, 0.0, 0.0]])
    direction = np.array([[-1.0, 0.0, 0.0]])
    rho, valid = solve_rho(obs, direction, np.array([1.0]))
    assert valid[0]
    assert rho[0] == pytest.approx(3.0)      # not 1.0


def test_hypothesis_closer_than_the_line_of_sight_can_reach_is_invalid():
    obs = np.array([[1.0, 0.0, 0.0]])
    direction = np.array([[0.0, 1.0, 0.0]])       # perpendicular: min distance is 1 AU
    _, valid = solve_rho(obs, direction, np.array([0.5]))
    assert not valid[0]


def test_grazing_hypothesis_is_rejected_by_the_degeneracy_guard():
    """r ~= |R_observer| collapses every tracklet onto the observer -- see the guard."""
    obs = np.array([[1.0, 0.0, 0.0]])
    direction = np.array([[0.0, 1.0, 0.0]])
    rho, _ = solve_rho(obs, direction, np.array([1.0 + 1e-6]))
    assert rho[0] < MIN_TOPOCENTRIC_DISTANCE_AU
    _, _, _, ok = state_from_hypothesis(
        obs, np.zeros((1, 3)), direction, np.zeros((1, 3)),
        np.array([1.0 + 1e-6]), np.array([0.0]),
    )
    assert not ok[0]


def test_state_from_hypothesis_reproduces_the_state_it_was_built_from():
    """Round trip: make a state, observe it, solve it back."""
    r_vec = np.array([[1.8, 1.2, 0.3]])
    v_vec = np.array([[-0.006, 0.008, 0.0005]])
    obs_pos = np.array([[0.9, -0.4, 0.0]])
    obs_vel = np.array([[0.007, 0.015, 0.0]])

    delta = r_vec - obs_pos
    rho = np.linalg.norm(delta, axis=1)
    rho_hat = delta / rho[:, None]
    rel_v = v_vec - obs_vel
    rho_dot = np.einsum("ij,ij->i", rel_v, rho_hat)
    rho_hat_dot = (rel_v - rho_dot[:, None] * rho_hat) / rho[:, None]

    r = np.linalg.norm(r_vec, axis=1)
    rdot = np.einsum("ij,ij->i", r_vec, v_vec) / r

    got_r, got_v, got_rho, valid = state_from_hypothesis(
        obs_pos, obs_vel, rho_hat, rho_hat_dot, r, rdot
    )
    assert valid[0]
    assert np.allclose(got_r, r_vec, atol=1e-12)
    assert np.allclose(got_v, v_vec, atol=1e-12)
    assert got_rho[0] == pytest.approx(rho[0], abs=1e-12)


# --- propagation ------------------------------------------------------------------

def test_stumpff_series_and_closed_forms_agree_across_the_switch():
    psi = np.array([-1e-3, -1e-7, 0.0, 1e-7, 1e-3])
    c2, c3 = stumpff(psi)
    assert np.allclose(c2, 0.5 - psi / 24.0 + psi**2 / 720.0, rtol=1e-10)
    assert np.allclose(c3, 1 / 6 - psi / 120.0 + psi**2 / 5040.0, rtol=1e-10)


def test_propagation_conserves_energy_and_angular_momentum():
    rng = np.random.default_rng(7)
    r_vec = rng.normal(size=(50, 3)) * 1.5 + np.array([2.5, 0.0, 0.0])
    v_vec = rng.normal(size=(50, 3)) * 0.002 + np.array([0.0, 0.011, 0.0])
    r2, v2, ok = propagate_kepler(r_vec, v_vec, np.full(50, 30.0))
    assert ok.all()

    def energy(r, v):
        return 0.5 * np.einsum("ij,ij->i", v, v) - GM_SUN / np.linalg.norm(r, axis=1)

    assert np.allclose(energy(r_vec, v_vec), energy(r2, v2), rtol=1e-9)
    assert np.allclose(np.cross(r_vec, v_vec), np.cross(r2, v2), rtol=1e-8, atol=1e-12)


def test_propagation_is_reversible():
    r_vec = np.array([[2.5, 0.3, -0.1]])
    v_vec = np.array([[-0.001, 0.0105, 0.0004]])
    fwd_r, fwd_v, _ = propagate_kepler(r_vec, v_vec, np.array([45.0]))
    back_r, back_v, _ = propagate_kepler(fwd_r, fwd_v, np.array([-45.0]))
    assert np.allclose(back_r, r_vec, atol=1e-11)
    assert np.allclose(back_v, v_vec, atol=1e-13)


def test_circular_orbit_returns_to_its_start_after_one_period():
    a = 2.5
    period = 2 * np.pi * np.sqrt(a**3 / GM_SUN)
    r_vec = np.array([[a, 0.0, 0.0]])
    v_vec = np.array([[0.0, np.sqrt(GM_SUN / a), 0.0]])
    r2, _, _ = propagate_kepler(r_vec, v_vec, np.array([period]))
    assert np.allclose(r2, r_vec, atol=1e-9)


def test_hyperbolic_state_propagates_without_blowing_up():
    """A wrong distance hypothesis routinely produces an unbound state."""
    r_vec = np.array([[1.0, 0.0, 0.0]])
    v_vec = np.array([[0.0, 0.04, 0.0]])          # well above escape at 1 AU
    r2, v2, ok = propagate_kepler(r_vec, v_vec, np.array([10.0]))
    assert ok.all()
    assert np.all(np.isfinite(r2)) and np.all(np.isfinite(v2))
    assert np.linalg.norm(r2) > np.linalg.norm(r_vec)


# --- elements ---------------------------------------------------------------------

def test_elements_of_a_known_circular_orbit():
    a = 3.0
    r_vec = np.array([[a, 0.0, 0.0]])
    v_vec = np.array([[0.0, np.sqrt(GM_SUN / a), 0.0]])
    el = state_to_elements(r_vec, v_vec)
    assert el["a"][0] == pytest.approx(a, rel=1e-12)
    assert el["e"][0] == pytest.approx(0.0, abs=1e-12)
    assert el["incl"][0] == pytest.approx(0.0, abs=1e-9)
    assert el["q"][0] == pytest.approx(a, rel=1e-12)


def test_elements_recover_eccentricity_and_inclination():
    a, e = 2.5, 0.3
    q = a * (1 - e)
    speed = np.sqrt(GM_SUN * (2.0 / q - 1.0 / a))
    inc = np.radians(20.0)
    r_vec = np.array([[q, 0.0, 0.0]])
    v_vec = np.array([[0.0, speed * np.cos(inc), speed * np.sin(inc)]])
    el = state_to_elements(r_vec, v_vec)
    assert el["a"][0] == pytest.approx(a, rel=1e-10)
    assert el["e"][0] == pytest.approx(e, rel=1e-10)
    assert el["incl"][0] == pytest.approx(20.0, rel=1e-9)
    assert el["q"][0] == pytest.approx(q, rel=1e-9)
