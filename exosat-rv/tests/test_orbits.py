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


def test_published_table_is_complete_and_correctly_parsed():
    """Self-verifying: the mean of the error column must land on the paper's stated 31.44
    m/s. Nothing feeds that number in, so agreement means the digitisation is right."""
    d = load_published()
    assert len(d.rv) == P.n_epochs_used
    assert d.erv.mean() == pytest.approx(P.rv_err_nodding_ms, abs=0.05)
    assert d.baseline_d == pytest.approx(465, abs=2)


def test_published_rv_range_is_consistent_with_the_published_amplitude():
    d = load_published()
    span = d.rv.max() - d.rv.min()
    assert span == pytest.approx(2 * P.sat1_amplitude_ms, rel=0.25)


def test_published_errors_lie_in_the_quoted_range():
    """The paper quotes per-epoch errors of 18-54 m/s."""
    d = load_published()
    assert d.erv.min() >= 18.0
    assert d.erv.max() <= 54.0


def test_delta_logz_proxy_sign_convention():
    class F:
        def __init__(self, bic):
            self.bic = bic

    assert delta_logz_proxy(F(100.0), F(110.0)) == pytest.approx(5.0)   # a better -> positive
    assert delta_logz_proxy(F(110.0), F(100.0)) == pytest.approx(-5.0)


@pytest.mark.slow
def test_the_second_period_reproduces_at_88_days():
    """M6's headline: 88 d beats every other alias candidate on the published RVs."""
    d = load_published()
    fits = {p2: fit_fixed_periods(d, (P.sat1_period_d, p2), n_starts=120)
            for p2 in P.alias_periods_d}
    best = min(fits.values(), key=lambda f: f.bic)
    assert best.periods[1] == 88.0
    assert best.amplitudes[1] == pytest.approx(P.sat2_amplitude_ms, rel=0.15)
    assert delta_logz_proxy(best, fits[115.0]) > 0.5


@pytest.mark.slow
def test_two_satellites_beat_the_eccentric_single():
    d = load_published()
    one = fit_fixed_periods(d, (P.sat1_period_d,), eccentric=True, n_starts=120)
    two = fit_fixed_periods(d, (P.sat1_period_d, 88.0), n_starts=120)
    assert delta_logz_proxy(two, one) > 0        # same direction as the paper's dlogZ = 6.9
    assert one.ecc > 0.2                         # the 2:1 MMR degeneracy signature
