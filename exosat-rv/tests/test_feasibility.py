"""The published CD-35 2722 B system is the fixture: if the physics does not reproduce it,
nothing built on top of it can be trusted.

Since M1 the fixture is strong -- Table 1 of the preprint gives *fitted RV semi-amplitudes*,
so `rv_semi_amplitude` is checked against a measured quantity rather than a rough estimate.
"""

import math

import pytest

from exosat_rv.config import PUBLISHED as P
from exosat_rv.targets.feasibility import (
    MEARTH_PER_MJUP,
    domingos_stability_limit_au,
    harmonic_offset_sigma,
    hill_radius_au,
    min_detectable_msini,
    photon_limited_precision,
    rv_semi_amplitude,
    semi_major_axis_au,
)


def _companion_sma() -> float:
    return semi_major_axis_au(P.bd_period_yr, P.star_mass_msun + P.bd_mass_mjup / 1047.5673)


# --- reproducing the published fit ------------------------------------------------------


def test_reproduces_published_amplitude_of_satellite_1():
    """Table 1: 246.45 m/s. Ours should agree to a few percent; the residual is the
    difference between the quoted 37 M_Jup and whatever mass the fit actually used."""
    k = rv_semi_amplitude(P.sat1_msini_mjup, P.bd_mass_mjup, P.sat1_period_d, P.sat1_ecc)
    assert k == pytest.approx(P.sat1_amplitude_ms, rel=0.03)


def test_reproduces_published_amplitude_of_satellite_2():
    k = rv_semi_amplitude(P.sat2_msini_mjup, P.bd_mass_mjup, P.sat2_period_d, P.sat2_ecc)
    assert k == pytest.approx(P.sat2_amplitude_ms, rel=0.04)


def test_published_signal_dwarfs_the_published_errors():
    """The detection is easy per-epoch -- that is why 20 epochs sufficed."""
    assert P.sat1_amplitude_ms / P.rv_err_nodding_ms > 5


def test_the_favoured_extraction_beats_the_combined_one():
    """The paper's ~10% precision gain from using individual nodding frames. M2 inherits
    the combined-spectrum penalty if it works from ESO's archived products."""
    assert P.rv_err_nodding_ms < P.rv_err_combined_ms


# --- the scaling that motivates the project ---------------------------------------------


def test_lighter_host_gives_larger_wobble():
    """K ~ M_host^(-2/3). The project's central premise; assert the sign and the size."""
    heavy = rv_semi_amplitude(0.5, 37, 100)
    light = rv_semi_amplitude(0.5, 5, 100)
    assert light > heavy
    # Ratio is set by *total* mass, satellite included.
    assert light / heavy == pytest.approx((37.5 / 5.5) ** (2 / 3), rel=1e-6)


def test_min_detectable_mass_inverts_semi_amplitude():
    m = min_detectable_msini(m_host_mjup=37, period_d=169.45, rv_precision_ms=30, snr=3.0)
    assert rv_semi_amplitude(m, 37, 169.45) == pytest.approx(90.0, rel=1e-3)


def test_sub_neptune_reachable_around_a_young_giant():
    """The Project-B claim, stated as a test so it cannot quietly rot."""
    m = min_detectable_msini(m_host_mjup=5, period_d=100, rv_precision_ms=P.rv_err_nodding_ms)
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


# --- dynamics, and the M0 retraction ----------------------------------------------------


def test_companion_semi_major_axis_far_exceeds_projected_separation():
    """A ~5000 yr orbit puts the companion at ~222 au, not the ~63 au it appears at.

    This is the error that produced M0's false disproof: taking the projected separation
    for the semi-major axis. Pinned so the mistake cannot be made silently again.
    """
    projected = P.bd_projected_sep_arcsec * (1000.0 / P.parallax_mas)
    assert projected == pytest.approx(63, abs=2)
    assert _companion_sma() > 3 * projected


def test_reproduces_the_published_stability_limit():
    """The paper's 1.07 au is a Domingos+2006 stability limit, and it is correct.

    It falls out at e_host ~ 0.93-0.94, comfortably inside the published ">0.9". M0 called
    this value impossible by treating it as a Hill radius on a circular orbit; both halves
    of that were wrong. See M1-RESULTS.md section 1.1.
    """
    a = _companion_sma()
    limits = [
        domingos_stability_limit_au(P.bd_mass_mjup, P.star_mass_msun, a, e, P.sat2_ecc)
        for e in (0.90, 0.95)
    ]
    assert min(limits) < P.stability_limit_au < max(limits)


def test_both_satellites_sit_inside_the_published_stability_limit():
    assert P.sat1_sma_au < P.stability_limit_au
    assert P.sat2_sma_au < P.stability_limit_au


def test_high_host_eccentricity_is_what_tightens_the_limit():
    """Sanity on the mechanism: the same system on a circular orbit would allow ~9 au."""
    a = _companion_sma()
    circular = domingos_stability_limit_au(P.bd_mass_mjup, P.star_mass_msun, a, 0.0, 0.0)
    eccentric = domingos_stability_limit_au(P.bd_mass_mjup, P.star_mass_msun, a, 0.93, 0.01)
    assert circular > 8.0
    assert eccentric / circular < 0.2


def test_hill_radius_is_not_the_stability_limit():
    """They differ by more than an order of magnitude here. Conflating them is precisely
    what M0 did."""
    a = _companion_sma()
    assert hill_radius_au(P.bd_mass_mjup, P.star_mass_msun, a) > 10 * P.stability_limit_au


# --- the second signal ------------------------------------------------------------------


def test_second_period_is_an_alias_not_primarily_a_harmonic():
    """The paper's stated concern is aliasing, not harmonic leakage.

    87.46 d does sit ~4.3 sigma from 169.45/2 = 84.7 d, so harmonic leakage is not absurd
    on its face. But the preprint identifies 14, 70, 88 and 115 d as aliases of one another
    induced by two observing seasons almost exactly a year apart -- and it separately fits
    and rejects the eccentric single-satellite model. M4 must test the alias structure, not
    a harmonic the authors already addressed.
    """
    sigma = harmonic_offset_sigma(P.sat1_period_d, P.sat2_period_d, P.sat2_period_err_d)
    assert 3 < sigma < 6
    assert 88.0 in P.alias_periods_d
    assert len(P.alias_periods_d) == 4


def test_two_satellite_model_is_favoured_over_the_eccentric_single():
    """The alternative M4 was originally aimed at is one the paper already fitted."""
    assert P.one_sat_ecc > 0.25          # the 2:1 MMR degeneracy signature
    assert P.two_sat_logz > P.one_sat_logz
    assert P.delta_logz_two_vs_one > P.delta_logz_88_vs_115


def test_table1_logz_difference_does_not_match_the_quoted_delta():
    """A real internal inconsistency in the preprint, pinned rather than smoothed over:
    Table 1's logZ values differ by 6.641, but the text quotes 6.9."""
    assert P.two_sat_logz - P.one_sat_logz == pytest.approx(6.641, abs=0.001)
    assert P.delta_logz_two_vs_one == 6.9
