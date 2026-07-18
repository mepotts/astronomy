"""Tests for the Gaia DR3 parallax zero-point correction (Lindegren et al. 2021, A&A 649 A4).

Uses the official ``gaiadr3-zeropoint`` package (offline: no network). The regression
anchors below are the package's own outputs for fixed inputs, so they pin BOTH our wiring
and the correction direction (corrected parallax = catalogue - Z, Z typically negative).
"""

from __future__ import annotations

import numpy as np
import pytest

from seti_ellipsoid_broker import zeropoint as Z


# --- known-value regression anchors -------------------------------------------------

def test_zeropoint_known_value_5param():
    """5-parameter source (astrometric_params_solved=31): Z from the official tables."""
    z = Z.parallax_zeropoint(
        phot_g_mean_mag=17.0,
        nu_eff_used_in_astrometry=1.5,
        pseudocolour=1.4,
        ecl_lat=-20.0,
        astrometric_params_solved=31,
    )
    assert z == pytest.approx(-0.031318, abs=1e-6)


def test_zeropoint_known_value_6param():
    """6-parameter source (astrometric_params_solved=95): uses pseudocolour, not nu_eff."""
    z = Z.parallax_zeropoint(
        phot_g_mean_mag=17.0,
        nu_eff_used_in_astrometry=1.5,
        pseudocolour=1.4,
        ecl_lat=-20.0,
        astrometric_params_solved=95,
    )
    assert z == pytest.approx(-0.032914, abs=1e-6)


def test_apply_correction_direction_and_value():
    """corrected = parallax - Z; Z<0 so the corrected parallax is larger (star closer)."""
    p = 1.0
    corrected = Z.apply_parallax_zeropoint(
        parallax_mas=p,
        phot_g_mean_mag=17.0,
        nu_eff_used_in_astrometry=1.5,
        pseudocolour=1.4,
        ecl_lat=-20.0,
        astrometric_params_solved=31,
    )
    assert corrected == pytest.approx(1.0 - (-0.031318), abs=1e-6)
    assert corrected > p  # DR3 bias makes stars look too far; correction pulls them closer


def test_mean_offset_constant_is_documented():
    assert Z.GAIA_DR3_MEAN_ZEROPOINT_MAS == pytest.approx(-0.017, abs=1e-6)


# --- solution-type handling ---------------------------------------------------------

def test_2param_solution_is_uncorrectable_nan():
    """2-parameter solutions (solved=3) have no defined zero-point -> NaN offset."""
    z = Z.parallax_zeropoint(18.0, 1.5, np.nan, -30.0, 3)
    assert np.isnan(z)


def test_apply_falls_back_to_uncorrected_when_undefined():
    """A 2p source keeps its raw parallax (fallback) rather than becoming NaN."""
    corrected = Z.apply_parallax_zeropoint(2.5, 18.0, 1.5, np.nan, -30.0, 3)
    assert corrected == pytest.approx(2.5)
    # ...unless the caller explicitly asks for NaN.
    nan_out = Z.apply_parallax_zeropoint(
        2.5, 18.0, 1.5, np.nan, -30.0, 3, fallback_to_uncorrected=False
    )
    assert np.isnan(nan_out)


def test_5param_source_with_nan_pseudocolour_still_corrects():
    """5p sources normally have NaN pseudocolour; the correction must not choke on it."""
    z = Z.parallax_zeropoint(18.5, 1.6, np.nan, -66.0, 31)
    assert np.isfinite(z)
    assert z == pytest.approx(-0.028661, abs=1e-6)


# --- vectorised path ----------------------------------------------------------------

def test_vectorised_mixed_solution_types():
    z = Z.parallax_zeropoint(
        phot_g_mean_mag=np.array([17.0, 17.0, 18.0]),
        nu_eff_used_in_astrometry=np.array([1.5, 1.5, 1.5]),
        pseudocolour=np.array([1.4, 1.4, np.nan]),
        ecl_lat=np.array([-20.0, -20.0, -30.0]),
        astrometric_params_solved=np.array([31, 95, 3]),  # 5p, 6p, 2p
    )
    assert isinstance(z, np.ndarray)
    assert z[0] == pytest.approx(-0.031318, abs=1e-6)
    assert z[1] == pytest.approx(-0.032914, abs=1e-6)
    assert np.isnan(z[2])  # 2p uncorrectable


def test_out_of_range_magnitude_is_nan():
    """Faint source outside 6<G<21 -> undefined -> NaN offset."""
    z = Z.parallax_zeropoint(22.5, 1.5, 1.4, -20.0, 31)
    assert np.isnan(z)


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        Z.parallax_zeropoint(
            np.array([17.0, 18.0]), 1.5, 1.4, -20.0, np.array([31, 95, 31])
        )
