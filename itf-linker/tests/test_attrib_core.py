"""Attribution geometry (M7): mpc_orb parsing, prediction, and the phase-shifted control.

The fixtures under ``tests/data/attrib/`` are real get-orb responses for four numbered
asteroids, captured by ``scripts/m7_calibration.py``. The truth values pinned here are
JPL Horizons astrometric geocentric positions recorded during that calibration -- nothing
in them comes from the code under test, which is the M1 self-test's standard.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from itf_linker.attrib.core import (
    AttribOrbit,
    control_orbit,
    parse_mpc_orb,
    predict,
    separation_deg,
)
from itf_linker.link.geometry import state_to_elements

DATA = Path(__file__).parent / "data" / "attrib"


def load_orbit(desig: str) -> AttribOrbit:
    doc = json.loads((DATA / f"mpc_orb_{desig}.json").read_text(encoding="utf-8"))
    orbit = parse_mpc_orb(doc, requested_desig=desig)
    assert orbit is not None
    return orbit


# ----------------------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------------------

def test_parse_iris_fields() -> None:
    orbit = load_orbit("7")
    assert orbit.epoch_mjd_tt == 61200.0
    # (7) Iris: a = 2.386 AU. The state is rotated ecliptic -> equatorial; a rotation
    # must not change the orbit it represents.
    assert orbit.a_au == pytest.approx(2.386, abs=0.005)
    assert orbit.h_mag is not None and 5.0 < orbit.h_mag < 7.0
    assert orbit.period_days == pytest.approx(1346.0, rel=0.01)


def test_rotation_preserves_radius() -> None:
    doc = json.loads((DATA / "mpc_orb_7.json").read_text(encoding="utf-8"))
    orbit = parse_mpc_orb(doc, "7")
    raw = doc["mpc_orb"][0]["CAR"]["coefficient_values"]
    assert float(np.linalg.norm(orbit.r0)) == pytest.approx(
        float(np.linalg.norm(np.asarray(raw[:3]))), rel=1e-12
    )
    # The z-component must change under an obliquity rotation (ecliptic != equatorial):
    # a parser that forgets the rotation entirely would pass the radius check above.
    assert abs(orbit.r0[2] - raw[2]) > 1e-3


def test_parse_rejects_unknown_frame() -> None:
    doc = json.loads((DATA / "mpc_orb_7.json").read_text(encoding="utf-8"))
    doc["mpc_orb"][0]["system_data"]["refsys"] = "Equatorial"
    with pytest.raises(ValueError, match="unsupported mpc_orb frame"):
        parse_mpc_orb(doc, "7")


def test_parse_rejects_unknown_epoch_convention() -> None:
    doc = json.loads((DATA / "mpc_orb_7.json").read_text(encoding="utf-8"))
    doc["mpc_orb"][0]["epoch_data"]["timesystem"] = "UTC"
    with pytest.raises(ValueError, match="unsupported epoch convention"):
        parse_mpc_orb(doc, "7")


def test_parse_empty_document_is_none() -> None:
    assert parse_mpc_orb([], "x") is None
    assert parse_mpc_orb([{"mpc_orb": []}], "x") is None


# ----------------------------------------------------------------------------------
# Prediction against recorded Horizons truth
# ----------------------------------------------------------------------------------

#: Horizons astrometric geocentric places for (7) Iris (CENTER='500', QUANTITIES='1',
#: EXTRA_PREC), recorded 2026-08-16 during the M7 calibration run.
IRIS_TRUTH = [
    # (mjd_utc, ra_deg, dec_deg, tolerance_arcsec)
    (61200.0, 158.691036855, 3.039418096, 0.5),   # at the orbit epoch: geometry only
    (60834.75, 73.613300921, 22.969086974, 15.0), # 1 year back: two-body error, measured 3.5"
]


@pytest.mark.parametrize("mjd,ra,dec,tol", IRIS_TRUTH)
def test_predict_matches_horizons(mjd: float, ra: float, dec: float, tol: float) -> None:
    orbit = load_orbit("7")
    pred = predict(orbit, np.array([mjd]))
    sep_arcsec = 3600.0 * float(
        separation_deg(
            pred["ra_deg"], pred["dec_deg"], np.array([ra]), np.array([dec])
        )[0]
    )
    assert bool(pred["kepler_ok"][0])
    assert sep_arcsec < tol


def test_predict_reports_sane_photometry_and_rates() -> None:
    orbit = load_orbit("24")  # (24) Themis, H ~ 7
    pred = predict(orbit, np.array([orbit.epoch_mjd_tt - 30.0]))
    assert 8.0 < float(pred["v_pred"][0]) < 15.0
    # A main-belt object's apparent rate is a fraction of a degree per day.
    rate = float(
        np.hypot(pred["rate_ra_cosdec_deg_day"][0], pred["rate_dec_deg_day"][0])
    )
    assert 0.01 < rate < 1.0
    assert 1.0 < float(pred["delta_au"][0]) < 6.0


# ----------------------------------------------------------------------------------
# The amplitude-matched control
# ----------------------------------------------------------------------------------

def test_control_orbit_same_elements_different_place() -> None:
    orbit = load_orbit("153")
    ctrl = control_orbit(orbit)
    real = state_to_elements(orbit.r0[None, :], orbit.v0[None, :])
    fake = state_to_elements(ctrl.r0[None, :], ctrl.v0[None, :])
    for key in ("a", "e", "incl"):
        assert float(fake[key][0]) == pytest.approx(float(real[key][0]), rel=1e-9)
    # Half a period away on the same ellipse: physically elsewhere.
    assert float(np.linalg.norm(ctrl.r0 - orbit.r0)) > 0.5
    assert ctrl.primary_desig.endswith("[CONTROL]")


# ----------------------------------------------------------------------------------
# Separation
# ----------------------------------------------------------------------------------

def test_separation_basics() -> None:
    z = np.array([0.0])
    assert float(separation_deg(z, z, z, z)[0]) == pytest.approx(0.0, abs=1e-12)
    assert float(separation_deg(z, z, np.array([90.0]), z)[0]) == pytest.approx(90.0)
    # Wrap-around: 359 deg to 1 deg is 2 deg, not 358.
    assert float(
        separation_deg(np.array([359.0]), z, np.array([1.0]), z)[0]
    ) == pytest.approx(2.0)
