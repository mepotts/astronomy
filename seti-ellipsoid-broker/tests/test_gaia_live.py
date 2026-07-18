"""LIVE Gaia DR3 smoke test — SKIPPED unless SETI_GAIA_LIVE=1 (keeps the suite offline).

Run explicitly with, e.g.:

    SETI_GAIA_LIVE=1 python -m pytest tests/test_gaia_live.py -q

It hits the anonymous ESA Gaia TAP service (no account/token) and asserts that a known
bright LMC-direction source resolves with the columns the pipeline and the zero-point
correction need. This is the only test that touches the network.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("SETI_GAIA_LIVE") != "1",
    reason="live Gaia TAP smoke test; set SETI_GAIA_LIVE=1 to enable",
)


def test_live_gaia_cone_returns_needed_columns():
    from seti_ellipsoid_broker import gaia

    # A field near SN 1987A; anonymous cone query, real network.
    src = gaia.crossmatch_cone(83.86658, -69.26961, radius_arcsec=30.0)
    assert src is not None
    assert src.source_id is not None and src.source_id > 0
    # The zero-point input columns must be present for correctable solutions.
    assert src.astrometric_params_solved in (3, 31, 95)
    if src.astrometric_params_solved in (31, 95):
        assert src.ecl_lat is not None
        assert src.phot_g_mean_mag is not None


def test_live_gaia_by_source_id_roundtrips():
    from seti_ellipsoid_broker import gaia

    # Vela-region bright star Gaia DR3 id (stable public catalogue entry).
    known = 5853498713190525696  # Proxima Centauri (Gaia DR3)
    out = gaia.crossmatch_by_source_id([known])
    assert known in out
    assert out[known].parallax is not None
    assert out[known].parallax > 700  # Proxima parallax ~768 mas
