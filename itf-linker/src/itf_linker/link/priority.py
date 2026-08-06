"""In what order should gated links be fitted, when there is not time to fit them all?

M4 gated **412,929** links on the pre-60000 slice and fitted 4,461 of them (1.08%). The
order it fitted them in came from :func:`itf_linker.link.run.prioritise_bands` plus M3's
ranking: distance band first (NEO ahead of the belt), then cross-observatory, then *more*
nights, then a tighter cluster. That order was argued from value -- an NEO matters more
than another main-belt rock -- and never measured against outcomes.

It can be measured now, because M4 fitted 4,461 links and 118 of them passed every gate.
Replaying each candidate order over that sample and asking *what fraction of the eventual
survivors is in the first X% of the queue* gives:

===========================  ======  ======  ======  ======
order                        top 10%  top 25%  top 50%  top 75%
===========================  ======  ======  ======  ======
M4's own                      0.000    0.017    0.110    0.407
a random shuffle              0.127    0.271    0.517    0.771
this module (5-fold CV)       0.585    0.797    0.932    0.983
===========================  ======  ======  ======  ======

**M4's ranking was worse than shuffling the queue**, and the reason is legible in the
marginals it was built without:

* the ``neo`` band passed **0.3%** (6 of 2,000) against the ``belt`` band's **5.1%**
  (102 of 2,000) -- and M4 fitted the NEO band *first*;
* **more nights is worse, not better**: 3-night links passed 6.7%, four-night 1.8%,
  five-night 0.65%, six- and seven-night none. M4 sorted nights descending. A longer
  chain has more ways to contain one wrong tracklet, and M1's supplementary guard --
  which rejected half of everything that converged here -- fails the whole link when it
  does;
* **exactly two observatory codes** beat three or more: 3.5% against 0.9% and 0.6%;
* the two strongest signals were not in M4's sort at all: ``pos_spread_au`` (23% at
  <1e-4 AU falling to under 1% past 1e-3) and ``n_hypotheses_found`` (9.0% for links
  recovered by 50+ independent distance hypotheses against 0.55% for links seen once).

So the ordering here is a **logistic regression fitted to those outcomes**, not a hand
weighting. :data:`SURVIVAL_MODEL` holds its coefficients; :func:`fit_survival_model`
re-derives them from any report with the same shape.

Two things this ordering is deliberately *not*:

**It is not a filter.** Nothing is excluded by a low score. The score decides only what
gets fitted first, so that an interrupted run leaves behind the part that mattered. A
link the model scores at the very bottom is fitted with exactly the same gates as one at
the top, if the run reaches it.

**It is not applied across the cross-observatory boundary.** Cross-observatory links are
fitted first as a whole tier, ahead of every same-observatory link regardless of score,
because that is a judgement about *value* rather than yield: 100 of M4's 106 older-slice
survivors span two or more observatories, and a same-observatory link is mostly one
survey's own unlinked tracking, which that survey will link itself. The survival evidence
for the tier is weak in either direction (M4's sample was 90% cross-observatory), and it
is not what the tier rests on.

The honest caveat on the coefficients: they were fitted to a sample that M4 selected as
its own best-ranked, so it is 90% cross-observatory and contains no ``neo``-band link with
fewer than four nights. Scoring the other 99% of the population is extrapolation. Because
the score only ever orders a queue, the cost of that extrapolation is efficiency and never
correctness.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import polars as pl

#: Design-matrix columns, in order. Every one is available *before* Find_Orb runs.
FEATURES: tuple[str, ...] = (
    "intercept",
    "band_belt",
    "band_outer",
    "log10_pos_spread_au",
    "log10_n_hypotheses_found",
    "obscodes_over_2",
    "min_trk_n_obs",
    "prefit_arc_days",
)

#: Fitted on M4's 4,461 older-slice outcomes (``m4-old.json``, 118 passing), ridge
#: lambda = 1.0. Signs, all reproduced by the marginal tables in this module's docstring:
#: the belt band beats the NEO band; a tighter cluster is better; being recovered by more
#: independent hypotheses is better; a third observatory code is worse; thicker tracklets
#: are worse (they belong to the crowded archival fields, where agreement is cheap); a
#: longer arc is better.
SURVIVAL_MODEL: dict[str, float] = {
    "intercept": -9.818841,
    "band_belt": 1.122386,
    "band_outer": 0.456085,
    "log10_pos_spread_au": -1.305895,
    "log10_n_hypotheses_found": 0.961228,
    "obscodes_over_2": -0.765693,
    "min_trk_n_obs": -0.660361,
    "prefit_arc_days": 0.291591,
}


def design_matrix(frame: pl.DataFrame) -> np.ndarray:
    """``(n_links, len(FEATURES))`` of pre-fit predictors, in :data:`FEATURES` order."""
    n = frame.height
    band = frame["band"].to_numpy() if "band" in frame.columns else np.full(n, "belt")
    cols = {
        "intercept": np.ones(n),
        "band_belt": (band == "belt").astype(float),
        "band_outer": (band == "outer").astype(float),
        "log10_pos_spread_au": np.log10(
            np.clip(frame["pos_spread_au"].to_numpy().astype(float), 1e-6, None)
        ),
        "log10_n_hypotheses_found": np.log10(
            np.clip(frame["n_hypotheses_found"].to_numpy().astype(float), 1.0, None)
        ),
        "obscodes_over_2": np.clip(
            frame["n_obscodes"].to_numpy().astype(float) - 2.0, 0.0, None
        ),
        "min_trk_n_obs": frame["min_trk_n_obs"].to_numpy().astype(float),
        "prefit_arc_days": frame["arc_days"].to_numpy().astype(float),
    }
    return np.column_stack([cols[name] for name in FEATURES])


def survival_score(
    frame: pl.DataFrame, coefficients: dict[str, float] | None = None
) -> np.ndarray:
    """Predicted log-odds that a link will pass every published and supplementary gate."""
    w = coefficients or SURVIVAL_MODEL
    return design_matrix(frame) @ np.array([w[name] for name in FEATURES])


def logistic_fit(
    x: np.ndarray, y: np.ndarray, *, l2: float = 1.0, iters: int = 200
) -> np.ndarray:
    """Newton-IRLS logistic regression with an L2 ridge on every column but the intercept.

    Written out rather than pulled in because the project's dependency list is four
    libraries and this is fifteen lines. The ridge is what keeps a separating feature
    (there are several here -- no six-night link passed anything) from sending a
    coefficient to infinity.
    """
    w = np.zeros(x.shape[1])
    ridge = l2 * np.eye(x.shape[1])
    ridge[0, 0] = 0.0  # never penalise the intercept
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(x @ w)))
        grad = x.T @ (y - p) - ridge @ w
        weights = np.clip(p * (1.0 - p), 1e-6, None)
        hess = -(x.T * weights) @ x - ridge
        step = np.linalg.solve(hess, grad)
        w = w - step
        if np.max(np.abs(step)) < 1e-9:
            break
    return w


def fit_survival_model(
    frame: pl.DataFrame, passed: Sequence[bool] | np.ndarray, *, l2: float = 1.0
) -> dict[str, float]:
    """Re-derive :data:`SURVIVAL_MODEL` from a frame of links and their gate outcomes."""
    y = np.asarray(passed, dtype=float)
    return dict(zip(FEATURES, logistic_fit(design_matrix(frame), y, l2=l2)))


def capture_curve(
    order: np.ndarray, passed: Sequence[bool] | np.ndarray, at: Sequence[float] = (0.1, 0.25, 0.5, 0.75)
) -> dict[str, float]:
    """Fraction of the eventual survivors sitting in the first X% of ``order``.

    This is the only number that decides whether one fitting order is better than
    another, because the run *will* be cut short and what it already has is the result.
    """
    y = np.asarray(passed, dtype=float)[order]
    total = float(y.sum())
    if total == 0:
        return {f"top{int(p * 100)}%": 0.0 for p in at}
    return {
        f"top{int(p * 100)}%": round(float(y[: int(len(y) * p)].sum() / total), 3) for p in at
    }


def rank_for_fitting(
    gated: pl.DataFrame, coefficients: dict[str, float] | None = None
) -> pl.DataFrame:
    """Order gated links for fitting: cross-observatory tier first, survival score within.

    Adds ``fit_tier`` (0 cross-observatory, 1 same-observatory) and ``survival_score``,
    and returns the frame sorted. Ties broken by ``desig`` so the order is total and two
    runs of the same command chunk the queue identically -- which is what makes
    ``--resume`` exact rather than hopeful.
    """
    if gated.height == 0:
        return gated.with_columns(
            pl.lit(0, dtype=pl.Int32).alias("fit_tier"),
            pl.lit(0.0, dtype=pl.Float64).alias("survival_score"),
        )
    scored = gated.with_columns(
        pl.when(pl.col("cross_observatory")).then(0).otherwise(1).cast(pl.Int32).alias("fit_tier"),
        pl.Series("survival_score", survival_score(gated, coefficients)),
    )
    return scored.sort(
        ["fit_tier", "survival_score", "desig"], descending=[False, True, False]
    )


def tier_summary(ranked: pl.DataFrame) -> dict[str, Any]:
    """Per-tier and per-band counts of a ranked queue, for the report's coverage table."""
    out: dict[str, Any] = {"links": ranked.height}
    if not ranked.height:
        return out
    out["tiers"] = {
        ("cross_observatory" if r["fit_tier"] == 0 else "same_observatory"): int(r["n"])
        for r in ranked.group_by("fit_tier").agg(pl.len().alias("n")).sort("fit_tier").to_dicts()
    }
    if "band" in ranked.columns:
        out["bands"] = {
            str(r["band"]): int(r["n"])
            for r in ranked.group_by("band")
            .agg(pl.len().alias("n"))
            .sort("n", descending=True)
            .to_dicts()
        }
    out["survival_score"] = {
        "max": round(float(ranked["survival_score"].max()), 3),
        "median": round(float(ranked["survival_score"].median()), 3),
        "min": round(float(ranked["survival_score"].min()), 3),
    }
    return out
