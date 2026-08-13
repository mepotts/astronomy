"""Model comparison on the paper's published RVs -- the reproduction of its conclusion.

Fast checks on the data and the machinery; the full fit is exercised by `exosat-rv orbits`
and marked `slow` here because it runs hundreds of optimiser restarts.
"""

import pytest

from exosat_rv.analysis.orbits import (
    delta_logz_proxy,
    fit_fixed_periods,
    load_published,
)
from exosat_rv.config import PUBLISHED as P


def test_nature_table_is_complete_and_correctly_parsed():
    """Self-verifying: the mean of the error column must land on the paper's stated 57.68
    m/s. Nothing feeds that number in, so agreement means the digitisation is right."""
    d = load_published()  # nature is the default since M13
    assert len(d.rv) == P.pub_n_epochs
    assert d.erv.mean() == pytest.approx(P.pub_rv_err_nodding_ms, abs=0.05)
    assert d.baseline_d == pytest.approx(851, abs=2)


def test_v1_table_is_complete_and_correctly_parsed():
    """The superseded arXiv v1 table stays available and still self-verifies at 31.44."""
    d = load_published(version="v1")
    assert len(d.rv) == P.n_epochs_used
    assert d.erv.mean() == pytest.approx(P.rv_err_nodding_ms, abs=0.05)
    assert d.baseline_d == pytest.approx(465, abs=2)


def test_published_rv_range_is_consistent_with_the_published_amplitude():
    d = load_published()
    span = d.rv.max() - d.rv.min()
    assert span == pytest.approx(2 * P.pub_sat1_amplitude_ms, rel=0.25)


def test_published_errors_lie_in_the_quoted_range():
    """v1 quotes per-epoch errors of 18-54 m/s; the Nature table runs 42-87."""
    v1 = load_published(version="v1")
    assert v1.erv.min() >= 18.0
    assert v1.erv.max() <= 54.0
    d = load_published()
    assert d.erv.min() >= 40.0
    assert d.erv.max() <= 90.0


def test_delta_logz_proxy_sign_convention():
    class F:
        def __init__(self, bic):
            self.bic = bic

    assert delta_logz_proxy(F(100.0), F(110.0)) == pytest.approx(5.0)   # a better -> positive
    assert delta_logz_proxy(F(110.0), F(100.0)) == pytest.approx(-5.0)


@pytest.mark.slow
def test_the_second_period_reproduces_at_88_days_on_v1():
    """M6's headline: 88 d beats every other alias candidate on the v1 RVs."""
    d = load_published(version="v1")
    fits = {p2: fit_fixed_periods(d, (P.sat1_period_d, p2), n_starts=120)
            for p2 in P.alias_periods_d}
    best = min(fits.values(), key=lambda f: f.bic)
    assert best.periods[1] == 88.0
    assert best.amplitudes[1] == pytest.approx(P.sat2_amplitude_ms, rel=0.15)
    assert delta_logz_proxy(best, fits[115.0]) > 0.5


@pytest.mark.slow
def test_the_second_period_choice_reproduces_on_the_nature_table():
    """M13 SS5: 87.349 d still beats the 115 d alias on the published Nature RVs."""
    d = load_published()
    two = fit_fixed_periods(d, (P.pub_sat1_period_d, P.pub_sat2_period_d), n_starts=120)
    alias = fit_fixed_periods(d, (P.pub_sat1_period_d, 115.0), n_starts=120)
    assert delta_logz_proxy(two, alias) > 0.5


@pytest.mark.slow
def test_two_satellites_beat_the_eccentric_single_only_on_v1():
    """M6 found two satellites preferred on v1; M13 SS5 found the preference does NOT
    survive the authors' own revised table. Both directions are claims; test both."""
    v1 = load_published(version="v1")
    one = fit_fixed_periods(v1, (P.sat1_period_d,), eccentric=True, n_starts=120)
    two = fit_fixed_periods(v1, (P.sat1_period_d, 88.0), n_starts=120)
    assert delta_logz_proxy(two, one) > 0        # same direction as the paper's dlogZ = 6.9
    assert one.ecc > 0.2                         # the 2:1 MMR degeneracy signature

    nat = load_published()
    one_n = fit_fixed_periods(nat, (P.pub_one_sat_period_d,), eccentric=True, n_starts=120)
    two_n = fit_fixed_periods(nat, (P.pub_sat1_period_d, P.pub_sat2_period_d), n_starts=120)
    assert delta_logz_proxy(two_n, one_n) < 1.0  # the paper claims +2.62; we measure -0.51
