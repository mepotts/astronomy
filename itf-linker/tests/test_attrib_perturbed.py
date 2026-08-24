"""The perturbed backend (M8): planet model, integrator, dense output, encounter flag.

The recorded Horizons truth rows are astrometric geocentric places captured during the
M7/M8 calibration runs (CENTER='500', QUANTITIES='1', EXTRA_PREC) -- nothing in them
comes from the code under test, the M1 self-test's standard. The orbit fixtures are the
same stripped get-orb responses ``test_attrib_core.py`` uses.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from itf_linker.attrib import perturbed as pt
from itf_linker.attrib.core import parse_mpc_orb, predict, separation_deg
from itf_linker.attrib.perturbed import integrate_dense, predict_dense
from itf_linker.attrib.planets import (
    GM_PLANETS,
    MEAN_ELEMENTS,
    PLANET_NAMES,
    planet_positions,
)
from itf_linker.link.geometry import earth_heliocentric_posvel, propagate_kepler

DATA = Path(__file__).parent / "data" / "attrib"


def load_orbit(desig: str):
    doc = json.loads((DATA / f"mpc_orb_{desig}.json").read_text(encoding="utf-8"))
    orbit = parse_mpc_orb(doc, requested_desig=desig)
    assert orbit is not None
    return orbit


# ----------------------------------------------------------------------------------
# Planet model
# ----------------------------------------------------------------------------------

def test_emb_matches_astropy_earth() -> None:
    """The mean-element EMB and astropy's Earth agree to the model's stated accuracy.

    Two independent routes to the same body: JPL mean elements (this module) vs ERFA's
    analytic Earth ephemeris (the linker's observer machinery). Earth vs EMB differ by
    <= 3.2e-5 AU, and JPL quotes tens-of-arcsec element accuracy, so 3e-4 AU covers
    both without hiding a frame or time-argument mistake (which would be ~0.4 AU).
    """
    mjd = np.array([51544.5, 55000.0, 60000.0, 61000.0])
    emb = planet_positions(mjd)[:, PLANET_NAMES.index("emb"), :]
    earth, _ = earth_heliocentric_posvel(mjd)  # UTC vs TT: 69 s * 0.017 AU/d ~ 1e-5 AU
    assert np.max(np.linalg.norm(emb - earth, axis=1)) < 3e-4


def test_planet_radii_within_conic_bounds() -> None:
    mjd = np.linspace(48622.0, 61500.0, 40)  # 1992-2027
    pos = planet_positions(mjd)
    r = np.linalg.norm(pos, axis=2)
    a = MEAN_ELEMENTS[:, 0]
    e = MEAN_ELEMENTS[:, 2]
    assert np.all(r >= a[None, :] * (1 - e[None, :]) - 0.01)
    assert np.all(r <= a[None, :] * (1 + e[None, :]) + 0.01)


def test_planet_positions_refuse_outside_validity() -> None:
    with pytest.raises(ValueError, match="1800-2050"):
        planet_positions(np.array([100000.0]))


def test_equatorial_rotation_applied() -> None:
    """Jupiter's equatorial z must reflect the obliquity, not the ~1.3 deg ecliptic i."""
    pos = planet_positions(np.linspace(59000.0, 61165.0, 12))
    z_over_r = np.abs(pos[:, 4, 2]) / np.linalg.norm(pos[:, 4], axis=1)
    assert float(z_over_r.max()) > 0.25  # sin(23.4 deg) ~ 0.40; ecliptic-only ~ 0.02


# ----------------------------------------------------------------------------------
# Integrator
# ----------------------------------------------------------------------------------

def test_zero_mass_planets_reduce_to_two_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the perturbers switched off, RK4+Hermite must equal the Kepler propagator.

    Two tolerances on purpose: nodes every step isolate the *integrator* (~1e-11 AU),
    the production 8-day node spacing adds the cubic-Hermite *interpolation* budget
    (h^4/384 * a * n^4 ~ 1.2e-8 AU for Iris) -- both are measured here so a regression
    in either shows up as itself.
    """
    monkeypatch.setattr(pt, "GM_PLANETS", np.zeros_like(GM_PLANETS))
    orbit = load_orbit("7")
    t_eval = orbit.epoch_mjd_tt - np.array([17.3, 111.9, 250.0, 399.0])
    r_kep, v_kep, conv = propagate_kepler(
        np.broadcast_to(orbit.r0, (4, 3)).copy(),
        np.broadcast_to(orbit.v0, (4, 3)).copy(),
        t_eval - orbit.epoch_mjd_tt,
    )
    assert np.all(conv)

    exact_nodes = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        orbit.epoch_mjd_tt - 400.0, orbit.epoch_mjd_tt, dense_every=1,
    )
    r_d, v_d = exact_nodes.state_at(t_eval, np.zeros(4, dtype=int))
    assert np.max(np.linalg.norm(r_d - r_kep, axis=1)) < 2e-9    # integrator itself
    assert np.max(np.linalg.norm(v_d - v_kep, axis=1)) < 1e-10

    production = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        orbit.epoch_mjd_tt - 400.0, orbit.epoch_mjd_tt,  # dense_every=8 default
    )
    r_p, _ = production.state_at(t_eval, np.zeros(4, dtype=int))
    assert np.max(np.linalg.norm(r_p - r_kep, axis=1)) < 5e-8    # + interpolation


def test_round_trip_symmetry() -> None:
    """Back 8 years then forward 8 years lands on the initial state."""
    orbit = load_orbit("153")
    span = 2922.0
    back = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        orbit.epoch_mjd_tt - span, orbit.epoch_mjd_tt,
    )
    r_end, v_end = back.state_at(
        np.array([orbit.epoch_mjd_tt - span]), np.array([0])
    )
    fwd = integrate_dense(
        r_end, v_end, orbit.epoch_mjd_tt - span,
        orbit.epoch_mjd_tt - span, orbit.epoch_mjd_tt,
    )
    r_back, _ = fwd.state_at(np.array([orbit.epoch_mjd_tt]), np.array([0]))
    assert float(np.linalg.norm(r_back[0] - orbit.r0)) < 1e-8


def test_state_at_refuses_outside_span() -> None:
    orbit = load_orbit("7")
    traj = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        orbit.epoch_mjd_tt - 100.0, orbit.epoch_mjd_tt,
    )
    with pytest.raises(ValueError, match="outside integrated span"):
        traj.state_at(np.array([orbit.epoch_mjd_tt - 500.0]), np.array([0]))


def test_encounter_flag_trips_inside_hill_sphere() -> None:
    """An orbit built to sit 0.2 AU from Jupiter (Hill radius 0.34) must be flagged."""
    t0 = 60000.0
    jup = planet_positions(np.array([t0]))[0, 4]
    r0 = jup * (1.0 - 0.2 / float(np.linalg.norm(jup)))  # 0.2 AU sunward of Jupiter
    # near-circular velocity perpendicular to r0, in the x-y sense
    from itf_linker.link.geometry import GM_SUN

    rn = float(np.linalg.norm(r0))
    v_circ = np.sqrt(GM_SUN / rn)
    v0 = np.cross([0.0, 0.0, 1.0], r0 / rn) * v_circ
    traj = integrate_dense(r0[None, :], v0[None, :], t0, t0 - 30.0, t0)
    assert bool(traj.encounter[0])
    assert float(traj.min_planet_dist_au[0, 4]) < 0.34
    # A plain main-belt orbit must NOT be flagged over the same machinery.
    orbit = load_orbit("170")
    quiet = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        orbit.epoch_mjd_tt - 3652.5, orbit.epoch_mjd_tt,
    )
    assert not bool(quiet.encounter[0])


# ----------------------------------------------------------------------------------
# Prediction against recorded Horizons truth
# ----------------------------------------------------------------------------------

#: (7) Iris, astrometric geocentric, recorded 2026-08-16 (M7/M8 calibration cache).
#: Instants are epoch - lookback with epoch_mjd_tt = 61200.0.
IRIS_DEEP_TRUTH = [
    # (mjd_utc, ra_deg, dec_deg, perturbed_tol_arcsec, twobody_min_err_arcsec)
    (61200.0 - 3652.5, 244.027640369, -22.690107617, 15.0, 1000.0),   # 10 y back
    (61200.0 - 5478.75, 140.719963929, 10.243417055, 15.0, 1500.0),   # 15 y back
]


@pytest.mark.parametrize("mjd,ra,dec,tol,two_body_min", IRIS_DEEP_TRUTH)
def test_perturbed_beats_two_body_at_depth(
    mjd: float, ra: float, dec: float, tol: float, two_body_min: float
) -> None:
    """The backend swap in one assertion pair: perturbed lands, two-body cannot."""
    orbit = load_orbit("7")
    traj = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        mjd - 3.0, orbit.epoch_mjd_tt,
    )
    pred = predict_dense(traj, np.array([0]), np.array([mjd]),
                         h_mag=orbit.h_mag, g_slope=orbit.g_slope)
    sep = 3600.0 * float(
        separation_deg(pred["ra_deg"], pred["dec_deg"],
                       np.array([ra]), np.array([dec]))[0]
    )
    assert sep < tol
    two_body = predict(orbit, np.array([mjd]))
    sep2 = 3600.0 * float(
        separation_deg(two_body["ra_deg"], two_body["dec_deg"],
                       np.array([ra]), np.array([dec]))[0]
    )
    assert sep2 > two_body_min  # the measured M7 wall this module exists to pass


def test_predict_dense_matches_predict_shapes_and_photometry() -> None:
    """Same observable contract as core.predict, including NaN-H photometry."""
    orbit = load_orbit("24")
    t = orbit.epoch_mjd_tt - np.array([40.0, 90.0])
    traj = integrate_dense(
        orbit.r0[None, :], orbit.v0[None, :], orbit.epoch_mjd_tt,
        float(t.min() - 3.0), orbit.epoch_mjd_tt,
    )
    pred = predict_dense(traj, np.zeros(2, dtype=int), t,
                         h_mag=orbit.h_mag, g_slope=orbit.g_slope)
    ref = predict(orbit, t)
    # Two backends, same object, short lookback: sub-arcsecond agreement expected.
    sep = 3600.0 * separation_deg(pred["ra_deg"], pred["dec_deg"],
                                  ref["ra_deg"], ref["dec_deg"])
    assert float(sep.max()) < 12.0  # two-body's own short-lookback error bounds this
    assert abs(float(pred["v_pred"][0]) - float(ref["v_pred"][0])) < 0.05
    nan_pred = predict_dense(traj, np.zeros(2, dtype=int), t, h_mag=np.nan)
    assert np.all(np.isnan(nan_pred["v_pred"]))
    assert "encounter" in pred and pred["encounter"].shape == (2,)
