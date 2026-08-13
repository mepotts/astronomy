"""M9's result, pinned -- including the two screens that failed the control.

The negative results matter more than the positive one here. A future agent looking at
`data/viper/full1.rvo.dat` will rediscover that empirical weighting more than halves the
scatter on CD-35 2722 B, and will adopt it unless something says loudly that it works by
deleting the signal.
"""

from __future__ import annotations

import numpy as np
import pytest

from exosat_rv.analysis.orders import (
    PATHOLOGICAL_ORDERS,
    SCREEN_RESULTS,
    combination_ceiling_ms,
    combine,
    order_stats,
    read_rvo,
)
from exosat_rv.config import DATA, PUBLISHED

RVO = DATA / "viper" / "full1.rvo.dat"
PAR = DATA / "viper" / "full1.par.dat"
pytestmark = pytest.mark.skipif(not RVO.exists(), reason="viper outputs not present")


def test_reproduces_m2_headline_scatter() -> None:
    """A plain mean over all 10 orders must return M2's published 823 m/s run."""
    _, rv, er, orders = read_rvo(RVO)
    combined = combine(rv, er, orders, drop=(), weighting="equal")
    assert np.nanstd(combined) == pytest.approx(823.0, rel=0.02)


def test_formal_errors_are_actively_harmful_not_merely_useless() -> None:
    """Inverse-variance weighting is *worse* than a plain mean, by 3x.

    Order 8 has the largest scatter (4130 m/s) and the smallest formal error (101 m/s), so
    it dominates a formally-weighted mean. M2 found the errors untrustworthy; this measures
    the cost of trusting them anyway.
    """
    _, rv, er, orders = read_rvo(RVO)
    plain = np.nanstd(combine(rv, er, orders, drop=(), weighting="equal"))
    formal = np.nanstd(combine(rv, er, orders, drop=(), weighting="formal"))
    assert formal > 2.5 * plain


def test_dropping_the_pathological_order_helps() -> None:
    _, rv, er, orders = read_rvo(RVO)
    before = np.nanstd(combine(rv, er, orders, drop=(), weighting="equal"))
    after = np.nanstd(combine(rv, er, orders, weighting="equal"))
    assert after < before
    assert PATHOLOGICAL_ORDERS == (8,)


def test_order_8_is_the_outlier_on_independent_diagnostics() -> None:
    """It is dropped on evidence, not because it is the worst-scattering order."""
    stats = {s.order: s for s in order_stats(RVO, PAR)}
    worst = stats[8]
    others = [s for o, s in stats.items() if o != 8]
    assert worst.median_fit_rms > 3 * max(s.median_fit_rms for s in others)
    assert worst.median_formal_err_ms < min(s.median_formal_err_ms for s in others)
    assert worst.error_ratio > 30


def test_no_recombination_scheme_comes_close_to_the_published_precision() -> None:
    """M9's actual result: the ceiling is 683 m/s against a 31.44 m/s target.

    If this ever fails because the ceiling improved, M9's conclusion -- that the shortfall
    is per-order and not fixable by combination -- needs revisiting.
    """
    validated = min(rms for rms, dchi2, _ in SCREEN_RESULTS.values() if dchi2 >= 40)
    assert validated == combination_ceiling_ms()
    assert validated / PUBLISHED.rv_err_nodding_ms > 20
    # The unvalidated minimum is lower and must never be quoted as the ceiling.
    assert min(rms for rms, _, _ in SCREEN_RESULTS.values()) < validated


def test_every_screen_is_scored_on_the_control_as_well_as_the_target() -> None:
    for label, entry in SCREEN_RESULTS.items():
        assert len(entry) == 3, f"{label} has no control result"


def test_empirical_weighting_looks_best_on_target_and_destroys_the_control() -> None:
    """The trap. Same combined scatter as the accepted screen; control collapses.

    delta-chi2 65.0 -> 5.8 and K 5731 -> 1797 m/s on GJ 229 B, whose 12.1-day binary is not
    in dispute. Weighting by inverse per-order scatter downweights the orders carrying the
    signal, because for a real detection the scatter *is* the signal.
    """
    target_rms, dchi2, amp = SCREEN_RESULTS["drop order 8, empirical weights"]
    accepted_rms, accepted_dchi2, accepted_amp = SCREEN_RESULTS["drop order 8, equal"]

    assert target_rms < accepted_rms           # it looks BETTER on the science target
    assert dchi2 < 0.2 * accepted_dchi2        # and it has thrown the signal away
    assert amp < 0.4 * accepted_amp


def test_the_accepted_screen_improves_the_control_rather_than_weakening_it() -> None:
    _, base_dchi2, base_amp = SCREEN_RESULTS["all orders, equal (viper as-run)"]
    _, dchi2, amp = SCREEN_RESULTS["drop order 8, equal"]
    assert dchi2 > base_dchi2
    assert amp == pytest.approx(base_amp, rel=0.05)


def test_the_papers_own_telluric_rule_does_not_transfer_to_this_data() -> None:
    """Keeping only telluric-constrained orders makes the target worse and weakens control."""
    rms, dchi2, _ = SCREEN_RESULTS["telluric-constrained orders only"]
    baseline_rms, baseline_dchi2, _ = SCREEN_RESULTS["all orders, equal (viper as-run)"]
    assert rms > baseline_rms
    assert dchi2 < baseline_dchi2


def test_self_templating_suppresses_a_known_signal() -> None:
    """M11: the published template recipe halves the control's recovered amplitude.

    The damage arrives with the FIRST iteration and does not recover, so "iterate more" is
    not a fix. Meanwhile CD-35 2722 B looks better -- which is what suppression looks like
    on a target with no detected signal.
    """
    from exosat_rv.analysis.orders import TEMPLATE_RESULTS

    base_rms, _, base_k = TEMPLATE_RESULTS[
        "0 iterations, tpl_wave=initial (M2/M3 baseline)"
    ]
    _, one_dchi2, one_k = TEMPLATE_RESULTS["1 iteration, tpl_wave=tell"]
    two_rms, two_dchi2, two_k = TEMPLATE_RESULTS[
        "2 iterations, tpl_wave=tell (the published recipe)"
    ]

    assert one_k < 0.5 * base_k          # halved by a single iteration
    assert two_k < 0.5 * base_k          # and it does not recover
    assert one_dchi2 < 40 and two_dchi2 < 40
    assert two_rms < base_rms            # while the target appears to improve


def test_no_template_variant_beats_the_baseline_on_the_control() -> None:
    from exosat_rv.analysis.orders import TEMPLATE_RESULTS

    baseline = TEMPLATE_RESULTS["0 iterations, tpl_wave=initial (M2/M3 baseline)"]
    assert baseline[1] == max(d for _, d, _ in TEMPLATE_RESULTS.values())
