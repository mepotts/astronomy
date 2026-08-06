"""The fitting order, and the arithmetic underneath it.

M5's claim is that its queue puts survivors first and M4's did not. That is a measurable
statement about a ranking rule, so it is measured here on synthetic outcomes with a known
answer rather than asserted from the production run.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from itf_linker.link.priority import (
    FEATURES,
    SURVIVAL_MODEL,
    capture_curve,
    design_matrix,
    fit_survival_model,
    logistic_fit,
    rank_for_fitting,
    survival_score,
    tier_summary,
)


def _links(n: int, seed: int = 0) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    return pl.DataFrame(
        {
            "desig": [f"lnk{i:04d}" for i in range(n)],
            "band": rng.choice(["belt", "neo", "outer"], n).tolist(),
            "pos_spread_au": rng.uniform(1e-5, 2e-3, n),
            "n_hypotheses_found": rng.integers(1, 400, n),
            "n_obscodes": rng.integers(1, 5, n),
            "min_trk_n_obs": rng.integers(2, 6, n),
            "arc_days": rng.uniform(3.0, 14.0, n),
            "cross_observatory": rng.random(n) < 0.3,
        }
    )


def test_the_design_matrix_is_finite_even_for_a_degenerate_link():
    """A perfectly tight cluster has pos_spread 0, and log10(0) is not a rank key."""
    frame = _links(4).with_columns(
        pl.lit(0.0).alias("pos_spread_au"), pl.lit(0).alias("n_hypotheses_found")
    )
    x = design_matrix(frame)
    assert x.shape == (4, len(FEATURES))
    assert np.isfinite(x).all()


def test_the_score_moves_the_way_the_measured_marginals_do():
    """Each coefficient's sign is a claim about M4's outcomes; hold it to that claim."""
    base = pl.DataFrame(
        {
            "desig": ["a"], "band": ["neo"], "pos_spread_au": [5e-4],
            "n_hypotheses_found": [4], "n_obscodes": [2], "min_trk_n_obs": [3],
            "arc_days": [6.0], "cross_observatory": [True],
        }
    )
    ref = survival_score(base)[0]
    assert survival_score(base.with_columns(pl.lit("belt").alias("band")))[0] > ref
    assert survival_score(base.with_columns(pl.lit(1e-4).alias("pos_spread_au")))[0] > ref
    assert survival_score(base.with_columns(pl.lit(200).alias("n_hypotheses_found")))[0] > ref
    assert survival_score(base.with_columns(pl.lit(12.0).alias("arc_days")))[0] > ref
    assert survival_score(base.with_columns(pl.lit(4).alias("n_obscodes")))[0] < ref


def test_cross_observatory_links_are_fitted_first_whatever_they_score():
    """The tier is a value judgement and outranks the yield model by construction."""
    frame = _links(200, seed=3)
    ranked = rank_for_fitting(frame)
    tiers = ranked["fit_tier"].to_list()
    assert tiers == sorted(tiers)
    cross = ranked.filter(pl.col("fit_tier") == 0)
    assert cross["cross_observatory"].all()
    # the very worst-scoring cross-observatory link still precedes the best same-observatory one
    assert cross["survival_score"].min() <= ranked.filter(pl.col("fit_tier") == 1)[
        "survival_score"
    ].max()
    assert ranked.filter(pl.col("fit_tier") == 0)["desig"].to_list() == cross["desig"].to_list()


def test_within_a_tier_the_order_is_the_score_descending_and_total():
    frame = _links(300, seed=5)
    ranked = rank_for_fitting(frame)
    for tier in (0, 1):
        scores = ranked.filter(pl.col("fit_tier") == tier)["survival_score"].to_list()
        assert scores == sorted(scores, reverse=True)
    # Total: re-ranking the same frame in a different input order gives the same queue.
    shuffled = rank_for_fitting(frame.sample(fraction=1.0, shuffle=True, seed=11))
    assert shuffled["desig"].to_list() == ranked["desig"].to_list()


def test_an_empty_queue_still_carries_the_columns_the_batcher_reads():
    empty = _links(0)
    ranked = rank_for_fitting(empty)
    assert {"fit_tier", "survival_score"} <= set(ranked.columns)
    assert ranked.height == 0
    assert tier_summary(ranked) == {"links": 0}


def test_logistic_fit_recovers_a_planted_coefficient():
    rng = np.random.default_rng(1)
    x = np.column_stack([np.ones(4000), rng.normal(size=4000), rng.normal(size=4000)])
    truth = np.array([-1.0, 2.0, -1.5])
    y = (rng.random(4000) < 1.0 / (1.0 + np.exp(-(x @ truth)))).astype(float)
    assert np.allclose(logistic_fit(x, y, l2=1e-6), truth, atol=0.2)


def test_the_ridge_keeps_a_separating_feature_finite():
    """No six-night link passed anything in M4, which without a ridge is an infinite weight."""
    x = np.column_stack([np.ones(60), np.repeat([0.0, 1.0], 30)])
    y = np.repeat([1.0, 0.0], 30)
    assert np.isfinite(logistic_fit(x, y)).all()


def test_a_ranking_built_from_outcomes_beats_shuffling_those_outcomes():
    """The whole justification for the module, on data where the answer is known."""
    frame = _links(3000, seed=9)
    x = design_matrix(frame)
    truth = np.array([SURVIVAL_MODEL[name] for name in FEATURES])
    rng = np.random.default_rng(4)
    passed = rng.random(frame.height) < 1.0 / (1.0 + np.exp(-(x @ truth)))
    refit = fit_survival_model(frame, passed)
    assert set(refit) == set(FEATURES)

    ordered = np.argsort(-survival_score(frame, refit))
    shuffled = rng.permutation(frame.height)
    by_score = capture_curve(ordered, passed)
    by_luck = capture_curve(shuffled, passed)
    assert by_score["top25%"] > by_luck["top25%"] + 0.2
    assert by_score["top10%"] > by_luck["top10%"]


def test_capture_curve_is_a_fraction_of_the_survivors_and_survives_having_none():
    passed = np.array([1.0, 0.0, 0.0, 1.0])
    assert capture_curve(np.array([0, 3, 1, 2]), passed)["top50%"] == 1.0
    assert capture_curve(np.array([1, 2, 0, 3]), passed)["top50%"] == 0.0
    assert capture_curve(np.array([0, 1]), np.zeros(2))["top50%"] == 0.0
