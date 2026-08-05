"""Dynamical classification and the NEO score.

The boundaries are the IAU's, so these tests are mostly a spelling check on them -- but the
NEO score is *not* digest2 and the tests say so where it matters: a link whose perihelion
is nominally inside 1.3 AU but whose ``sigma(q)`` is half an AU is not an NEO claim, and
the score has to reflect that or it is worse than useless.
"""

from __future__ import annotations

import pytest

from itf_linker.fit.classify import (
    NEO_POPULATIONS,
    classify_orbit,
    describe,
    neo_score,
    population_histogram,
)


class _Fit:
    def __init__(self, **kw):
        for k in ("a", "e", "q", "incl", "sigma_q"):
            setattr(self, k, kw.get(k))


@pytest.mark.parametrize(
    ("a", "e", "expected"),
    [
        (0.74, 0.32, "atira"),        # (163693) Atira: aphelion inside Earth's perihelion
        (0.967, 0.183, "aten"),       # (2062) Aten
        (1.470, 0.560, "apollo"),     # (1862) Apollo
        (1.458, 0.223, "amor"),       # (433) Eros, q = 1.13
        (2.386, 0.231, "inner_belt"), # (7) Iris
        (2.681, 0.339, "middle_belt"),# (324) Bamberga
        (3.14, 0.08, "outer_belt"),
        (3.97, 0.14, "cybele_hilda"), # (153) Hilda
        (5.20, 0.147, "jupiter_trojan"),   # (588) Achilles
        (13.65, 0.383, "centaur"),    # (2060) Chiron
        (43.7, 0.039, "tno"),         # (50000) Quaoar
        (2.2, 0.45, "mars_crosser"),  # q = 1.21 -> NEO by q, actually
    ],
)
def test_known_objects_land_in_their_own_class(a, e, expected):
    got = classify_orbit(a, e, incl=15.0)
    if expected == "mars_crosser":
        # q = 1.21 < 1.3, so the formal NEO criterion wins -- as it must, because that is
        # the criterion the MPC applies and it is a perihelion test, not an `a` test.
        assert got == "amor"
    else:
        assert got == expected


def test_a_hyperbolic_or_missing_solution_is_not_silently_classified():
    assert classify_orbit(None, None) == "unknown"
    assert classify_orbit(2.5, None) == "unknown"
    assert classify_orbit(-3.0, 1.4) == "unbound"
    assert classify_orbit(float("nan"), 0.1) == "unknown"


def test_the_neo_classes_are_exactly_the_ones_inside_1_3_au():
    for a, e in [(0.74, 0.32), (0.967, 0.183), (1.470, 0.560), (1.458, 0.223)]:
        assert classify_orbit(a, e) in NEO_POPULATIONS
        assert a * (1 - e) < 1.3
    for a, e in [(2.386, 0.231), (43.7, 0.039)]:
        assert classify_orbit(a, e) not in NEO_POPULATIONS


def test_the_neo_score_reflects_how_badly_the_perihelion_is_known():
    """Same nominal q, wildly different claims."""
    tight = neo_score(1.10, 0.02)
    loose = neo_score(1.10, 0.50)
    assert tight > 0.99
    assert 0.5 < loose < 0.75
    assert neo_score(1.60, 0.02) < 0.01


def test_a_missing_sigma_degrades_to_the_hard_criterion_rather_than_guessing():
    assert neo_score(1.1, None) == 1.0
    assert neo_score(1.4, None) == 0.0
    assert neo_score(1.1, float("nan")) == 1.0
    assert neo_score(None, 0.1) is None


def test_describe_carries_the_elements_the_verdict_rests_on():
    row = describe(_Fit(a=1.458, e=0.223, q=1.133, incl=10.83, sigma_q=0.004))
    assert row["population"] == "amor"
    assert row["is_neo_by_q"] is True
    assert row["neo_score_proxy"] == 1.0
    assert row["q_au"] == 1.133
    assert row["sigma_q_au"] == 0.004


def test_the_fitted_q_is_preferred_over_a_times_one_minus_e():
    """Find_Orb reports both and they can disagree in the last digits."""
    assert classify_orbit(2.0, 0.35, q=1.29) in NEO_POPULATIONS
    assert classify_orbit(2.0, 0.35, q=1.31) not in NEO_POPULATIONS


def test_the_histogram_orders_populations_and_keeps_strangers():
    rows = [
        {"population": "tno"}, {"population": "amor"}, {"population": "amor"},
        {"population": "made_up"},
    ]
    hist = population_histogram(rows)
    assert list(hist) == ["amor", "tno", "made_up"]
    assert hist["amor"] == 2
