"""Alias-comb arithmetic, window function, and the Keplerian/GLS machinery M4 rests on.

All offline: M4's whole point is that it needs the observing *times*, not the velocities.
"""

import numpy as np
import pytest

from exosat_rv.analysis.aliases import (
    YEAR_D,
    alias_frequencies,
    fit_and_remove_sinusoid,
    gls,
    keplerian_rv,
    match_alias_comb,
    season_separation_d,
    season_split,
    window_function,
)
from exosat_rv.config import PUBLISHED as P


def two_season_cadence(n_per=10, season_len=150.0, gap=365.25, t0=0.0):
    rng = np.random.default_rng(7)
    s1 = t0 + np.sort(rng.uniform(0, season_len, n_per))
    s2 = t0 + gap + np.sort(rng.uniform(0, season_len, n_per))
    return np.concatenate([s1, s2])


# --- the alias comb ---------------------------------------------------------------------


def test_all_four_candidate_periods_lie_on_a_one_year_comb():
    """M4's central claim, as a test.

    14, 70, 88 and 115 d are all yearly aliases of the 169.45 d primary. Each implied
    sampling period must land within a few days of a year.
    """
    for m in match_alias_comb(list(P.alias_periods_d), P.sat1_period_d, 1 / YEAR_D):
        assert m.order != 0
        assert abs(m.implied_sampling_period_d - YEAR_D) < 10, m
        assert m.period_error_d < 1.0, m


def test_the_comb_orders_are_the_expected_small_integers():
    got = {m.period_d: m.order
           for m in match_alias_comb(list(P.alias_periods_d), P.sat1_period_d, 1 / YEAR_D)}
    assert got == {115.0: 1, 88.0: 2, 70.0: 3, 14.0: 24}


def test_the_fitted_second_period_is_also_on_the_comb():
    """87.46 d, not just the 88 d periodogram peak, sits within its own error of the tooth."""
    m = match_alias_comb([P.sat2_period_d], P.sat1_period_d, 1 / YEAR_D)[0]
    assert m.order == 2
    assert m.period_error_d < P.sat2_period_err_d


def test_unrelated_period_is_not_matched_by_a_small_order():
    """A period genuinely off the comb should need an implausible order or miss badly."""
    m = match_alias_comb([43.7], P.sat1_period_d, 1 / YEAR_D)[0]
    assert m.period_error_d > 0.2


def test_alias_frequencies_are_positive_and_sorted():
    f = alias_frequencies(1 / 169.45, 1 / YEAR_D, orders=10)
    assert np.all(f > 0) and np.all(np.diff(f) > 0)


# --- window function and seasons ---------------------------------------------------------


def test_window_function_peaks_at_the_sampling_period():
    t = two_season_cadence()
    freqs = np.linspace(1 / 800, 1 / 100, 4000)
    w = window_function(t, freqs)
    assert 1 / abs(freqs[np.argmax(w)]) == pytest.approx(YEAR_D, rel=0.15)


def test_window_function_is_unity_at_zero_frequency():
    assert window_function(two_season_cadence(), np.array([0.0]))[0] == pytest.approx(1.0)


def test_season_split_and_separation():
    t = two_season_cadence(gap=365.25)
    seasons = season_split(t)
    assert [len(s) for s in seasons] == [10, 10]
    assert season_separation_d(t) == pytest.approx(365.25, abs=40)


def test_single_season_has_no_separation():
    assert season_separation_d(np.linspace(0, 50, 10)) is None


# --- Keplerian and GLS -------------------------------------------------------------------


def test_circular_keplerian_is_a_cosine():
    t = np.linspace(0, 100, 50)
    assert keplerian_rv(t, 30.0, 100.0) == pytest.approx(100 * np.cos(2 * np.pi * t / 30))


def test_eccentric_keplerian_is_periodic_and_bounded():
    t = np.linspace(0, 200, 500)
    rv = keplerian_rv(t, 50.0, 100.0, ecc=0.6, omega=0.9)
    assert np.allclose(rv, keplerian_rv(t + 50.0, 50.0, 100.0, ecc=0.6, omega=0.9), atol=1e-6)
    assert np.abs(rv).max() < 100 * (1 + 0.6) + 1e-6


def test_sinusoid_removal_kills_an_injected_signal():
    t = two_season_cadence()
    dy = np.full(t.size, 10.0)
    y = keplerian_rv(t, 169.45, 250.0)
    assert np.std(fit_and_remove_sinusoid(t, y, dy, 169.45)) < 1e-6


def test_gls_recovers_a_clean_injected_period():
    t = np.sort(np.random.default_rng(3).uniform(0, 400, 60))
    dy = np.full(t.size, 5.0)
    y = keplerian_rv(t, 60.0, 100.0) + np.random.default_rng(4).normal(0, 5.0, t.size)
    freqs = np.linspace(1 / 300, 1 / 20, 6000)
    assert 1 / freqs[np.argmax(gls(t, y, dy, freqs))] == pytest.approx(60.0, rel=0.02)
