"""The published CD-35 2722 B system is the fixture: if the physics does not reproduce it,
nothing built on top of it can be trusted."""

import math

import pytest

from exosat_rv.config import PUBLISHED as P
from exosat_rv.targets.feasibility import (
    MEARTH_PER_MJUP,
    harmonic_offset_sigma,
    hill_radius_au,
    max_stable_sma_au,
    min_detectable_msini,
    photon_limited_precision,
    rv_semi_amplitude,
)


def test_reproduces_published_semi_amplitude():
    """Paper's Methods quote a signal of order 500 m/s peak-to-peak for satellite 1."""
    k = rv_semi_amplitude(P.sat1_msini_mjup, P.bd_mass_mjup, P.sat1_period_d)
    assert 2 * k == pytest.approx(500, rel=0.05)


def test_published_signal_dwarfs_the_published_errors():
    """The detection is easy per-epoch -- that is why 20 epochs sufficed."""
    k = rv_semi_amplitude(P.sat1_msini_mjup, P.bd_mass_mjup, P.sat1_period_d)
    assert k / P.rv_err_mean_ms > 5


def test_lighter_host_gives_larger_wobble():
    """K ~ M_host^(-2/3). The project's central premise; assert the sign of the effect."""
    heavy = rv_semi_amplitude(0.5, 37, 100)
    light = rv_semi_amplitude(0.5, 5, 100)
    assert light > heavy
    # Ratio is set by *total* mass, satellite included -- (37.5/5.5)^(2/3), not (37/5)^(2/3).
    assert light / heavy == pytest.approx((37.5 / 5.5) ** (2 / 3), rel=1e-6)


def test_min_detectable_mass_inverts_semi_amplitude():
    m = min_detectable_msini(m_host_mjup=37, period_d=169.45, rv_precision_ms=30, snr=3.0)
    assert rv_semi_amplitude(m, 37, 169.45) == pytest.approx(90.0, rel=1e-3)


def test_sub_neptune_reachable_around_a_young_giant():
    """The Project-B claim, stated as a test so it cannot quietly rot."""
    m = min_detectable_msini(m_host_mjup=5, period_d=100, rv_precision_ms=30)
    assert m * MEARTH_PER_MJUP < 25


def test_eccentricity_raises_amplitude():
    circ = rv_semi_amplitude(1.0, 37, 100, ecc=0.0)
    ecc = rv_semi_amplitude(1.0, 37, 100, ecc=0.6)
    assert ecc == pytest.approx(circ / math.sqrt(1 - 0.36), rel=1e-9)


@pytest.mark.parametrize("bad", [-0.1, 1.0, 1.5])
def test_rejects_unphysical_eccentricity(bad):
    with pytest.raises(ValueError):
        rv_semi_amplitude(1.0, 37, 100, ecc=bad)


def test_photon_scaling_is_1_585_per_magnitude():
    assert photon_limited_precision(15.0, 14.0, 30.0) == pytest.approx(30 * 10**0.2, rel=1e-9)
    assert photon_limited_precision(14.0, 14.0, 30.0) == pytest.approx(30.0)


def test_published_orbits_are_dynamically_stable():
    """Both satellite orbits sit far inside the companion's Hill sphere.

    Asserted self-consistently, NOT against the 1.07 au that ``PUBLISHED.hill_radius_au``
    carries: that value is a [SUMM] artifact and M0 disproved it. At the imaged separation
    of 2.8" = 62.6 au the Hill radius is ~18 au, and 1.07 au would require the companion to
    orbit at 3.7 au. See M0-RESULTS.md.
    """
    sep_au = 2.8 * (1000.0 / P.parallax_mas)  # arcsec x pc = au
    r_h = hill_radius_au(m_host_mjup=P.bd_mass_mjup, m_star_msun=0.5, sma_au=sep_au)
    assert r_h > 10.0
    for a in (P.sat1_sma_au, P.sat2_sma_au):
        assert a < max_stable_sma_au(P.bd_mass_mjup, 0.5, sep_au)


def test_published_hill_radius_is_internally_inconsistent():
    """Pin the M0 finding so it cannot be quietly 'fixed' back into the config.

    If someone later reads the PDF and 1.07 au turns out to be real, this test fails and
    forces the contradiction to be resolved in the open rather than papered over.
    """
    sep_au = 2.8 * (1000.0 / P.parallax_mas)
    r_h = hill_radius_au(m_host_mjup=P.bd_mass_mjup, m_star_msun=0.5, sma_au=sep_au)
    assert r_h / P.hill_radius_au > 10


def test_second_satellite_sits_near_the_first_harmonic():
    """M4 in one assertion: 87.46 d is only ~4 sigma off 169.45/2, close enough that
    harmonic leakage from an eccentric single Keplerian has to be excluded explicitly."""
    sigma = harmonic_offset_sigma(P.sat1_period_d, P.sat2_period_d, P.sat2_period_err_d)
    assert sigma < 6
    assert sigma > 0
