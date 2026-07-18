"""Tests for the M1 ranking layer: quality cuts, density binning, scoring, ordering."""

from __future__ import annotations

import pytest

from seti_ellipsoid_broker import ranking
from seti_ellipsoid_broker.models import RankedTarget


# --- quality cuts -------------------------------------------------------------------

def test_quality_cuts_thresholds():
    # On the right side of both thresholds -> pass.
    assert ranking.passes_quality_cuts(parallax_over_error=11.0, ruwe=1.0)
    # RUWE at/above 1.4 -> fail.
    assert not ranking.passes_quality_cuts(parallax_over_error=11.0, ruwe=1.4)
    assert not ranking.passes_quality_cuts(parallax_over_error=11.0, ruwe=1.55)
    # parallax_over_error at/below 5 -> fail.
    assert not ranking.passes_quality_cuts(parallax_over_error=5.0, ruwe=1.0)
    assert not ranking.passes_quality_cuts(parallax_over_error=4.9, ruwe=1.0)


def test_quality_cut_thresholds_match_constants():
    assert ranking.ellipsoid.RUWE_MAX == pytest.approx(1.4)
    assert ranking.ellipsoid.PARALLAX_OVER_ERROR_MIN == pytest.approx(5.0)


# --- density binning ----------------------------------------------------------------

def test_density_bin_monotonic_and_bounded():
    bins = [ranking.density_bin(n) for n in (0, 1, 2, 5, 10, 25, 50, 100, 250, 500, 5000)]
    assert bins[0] >= 1
    assert all(1 <= b <= 10 for b in bins)
    assert bins == sorted(bins)          # non-decreasing in neighbour count
    assert ranking.density_bin(5000) == 10  # saturates at the top bin
    assert ranking.density_bin(140) > ranking.density_bin(12)  # denser field, higher bin


def test_density_bin_rejects_negative():
    with pytest.raises(ValueError):
        ranking.density_bin(-1)


# --- proximity weighting ------------------------------------------------------------

def test_proximity_weight_peaks_at_now_and_decays():
    now = 2026.5
    w_now = ranking.proximity_weight(now, now_jyear=now)
    w_near = ranking.proximity_weight(now + 1.0, now_jyear=now)
    w_far = ranking.proximity_weight(now + 10.0, now_jyear=now)
    assert w_now == pytest.approx(1.0)
    assert 0.0 < w_far < w_near < w_now <= 1.0
    # Symmetric: a crossing equally far in the past is weighted the same.
    assert ranking.proximity_weight(now - 3.0, now) == pytest.approx(
        ranking.proximity_weight(now + 3.0, now)
    )


# --- score --------------------------------------------------------------------------

def test_score_rewards_density_proximity_and_tight_window():
    now = 2026.5
    base = ranking.score(2.0, 5, crossing_epoch_jyear=now, now_jyear=now)
    # Denser field -> higher.
    assert ranking.score(2.0, 9, crossing_epoch_jyear=now, now_jyear=now) > base
    # Tighter window -> higher.
    assert ranking.score(0.5, 5, crossing_epoch_jyear=now, now_jyear=now) > base
    # Crossing far from now -> lower (proximity penalty).
    assert ranking.score(2.0, 5, crossing_epoch_jyear=now + 20.0, now_jyear=now) < base


def test_score_legacy_two_arg_call_still_works():
    """The CLI's mock path calls score(window, bin) with no epoch; must not raise."""
    val = ranking.score(1.4, 7)
    assert val == pytest.approx(7.0 / 1.4)


def test_score_handles_zero_window_without_dividing_by_zero():
    val = ranking.score(0.0, 5, crossing_epoch_jyear=2026.5, now_jyear=2026.5)
    assert val > 0.0 and val == pytest.approx(5.0 / 1e-3)


# --- ordering -----------------------------------------------------------------------

def _t(ref: str, score: float) -> RankedTarget:
    return RankedTarget(
        source_ref=ref, gaia_source_id=1, ra_deg=0.0, dec_deg=0.0, distance_pc=100.0,
        parallax_over_error=10.0, ruwe=1.0, crossing_epoch_jyear=2027.0,
        crossing_window_yr=1.0, density_bin=5, score=score,
    )


def test_rank_sorts_descending_by_score():
    out = ranking.rank([_t("a", 1.0), _t("b", 3.0), _t("c", 2.0)])
    assert [t.source_ref for t in out] == ["b", "c", "a"]
