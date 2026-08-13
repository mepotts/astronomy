"""Select which ITF designations are worth fitting, and why.

M0's central finding was that **2,515 designations already span 3+ nights inside the ITF
under a single trkSub**. Those need orbit *fitting*, not linking -- the combinatorial step
was done by the surveys, for free. This module turns that observation into a concrete,
auditable candidate list:

    all observations
      -> drop known-bad records                         (bad_data_filter)
      -> group into tracklets, keep 3+ distinct nights   (per_designation)
      -> apply the MPC's published pre-fit gate          (prefit_gate)
      -> screen for trkSub name collisions               (fit.collide)
      -> fit                                             (fit.findorb)

Every stage reports what it removed, so the funnel adds up.

The pre-fit gate is deliberately a *second implementation* of
:func:`itf_linker.verify.mpec.acceptance_summary` -- vectorised over 2.6M designations
rather than looping over one MPEC's tracklets. The two are pinned against each other in
``tests/test_candidates.py``, the same way the scalar and vectorised 80-column parsers are.

**Arc is the true observation arc**, ``last_mjd - first_mjd``. The MPEC-driven gate uses
night midnights instead, because an MPEC's residual table prints dates and not times and
there is nothing better available there; here the exact epochs are in hand, so the
approximation is unnecessary. It also matters: measured on this snapshot, the night-index
arc admits 1,293 designations and the true observation arc 1,120, because rounding each
end to a night boundary can add up to a day at each end and lift a 2.6-day arc over the
3-day threshold. The stricter, more accurate quantity is the one used.
"""

from __future__ import annotations

from typing import Any

import polars as pl

#: Sentinel epochs. M0 found 4 observations dated before 1900, three of them within
#: 0.0003 d of MJD 0 (1858-11-17), from observatory 705 -- a modern CCD survey. They are
#: corrupt, not 19th-century astrometry.
MIN_PLAUSIBLE_MJD = 15020.0  # 1900-01-01

#: What makes two records the same observation rather than two measurements.
DUPLICATE_KEY = ["desig", "obscode", "mjd", "ra_deg", "dec_deg"]

#: MPC published pre-fit criteria for an ITF-to-ITF link.
MIN_NIGHTS = 3
MIN_ARC_DAYS = 3.0
THREE_NIGHT_MAX_ARC_DAYS = 15.0


def bad_data_filter(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, dict[str, int]]:
    """Drop the records M0 identified as unusable, and report how many each rule removed.

    * **pre-1900 epochs** -- sentinel/corrupt dates.
    * **blank designations** -- cannot be grouped; must not be merged into one pseudo-object.
    * **exact duplicate records** -- the ITF contains byte-identical repeats. On the
      2026-07-29 snapshot, 476 (designation, observatory, epoch, RA, Dec) groups repeat,
      mostly 6 times each and almost all from W84/DECam, for 1,161 redundant rows. Six
      copies of one detection are not six measurements: left in, they multiply that
      epoch's weight in the least-squares fit and let a one-detection night masquerade as
      satisfying the MPC's "2 observations per night" rule.
    * **unpaired space-based ``S`` observations** -- cannot be reduced without the
      spacecraft position, which lives on the following ``s`` line. Those are dropped at
      *extraction* time rather than here (see :mod:`itf_linker.fit.extract`), because the
      pairing only exists in the original file; the count is surfaced there.

    The one malformed record (observatory 947, declination seconds ``39 8``) never reaches
    this function: the parser rejects it, which is pinned by a test in ``test_mpc80.py``.
    """
    frame = lf.collect() if isinstance(lf, pl.LazyFrame) else lf
    n0 = frame.height
    pre1900 = frame.filter(pl.col("mjd") < MIN_PLAUSIBLE_MJD).height
    blank = frame.filter(pl.col("desig").str.strip_chars() == "").height
    kept = frame.filter(
        (pl.col("mjd") >= MIN_PLAUSIBLE_MJD) & (pl.col("desig").str.strip_chars() != "")
    )
    before_dedupe = kept.height
    kept = kept.unique(subset=DUPLICATE_KEY, keep="first", maintain_order=True)
    return kept.lazy(), {
        "input": n0,
        "dropped_pre_1900_epoch": pre1900,
        "dropped_blank_designation": blank,
        "dropped_duplicate_records": before_dedupe - kept.height,
        "kept": kept.height,
    }


def per_designation(tracklets: pl.DataFrame) -> pl.DataFrame:
    """Collapse tracklets to one row per designation, in time order.

    ``first_trk_n_obs`` / ``last_trk_n_obs`` are the detection counts of the *earliest* and
    *latest* tracklets, which is what the MPC's "arc both starts and ends with a
    single-detection tracklet" rule needs.
    """
    return (
        tracklets.sort(["desig", "mjd_mid"])
        .group_by("desig", maintain_order=True)
        .agg(
            pl.len().alias("n_tracklets"),
            pl.col("night").n_unique().alias("n_nights"),
            pl.col("obscode").n_unique().alias("n_obscodes"),
            pl.col("obscode").unique().sort().alias("obscodes"),
            pl.col("n_obs").sum().alias("n_obs"),
            pl.col("night").min().alias("first_night"),
            pl.col("night").max().alias("last_night"),
            pl.col("mjd_min").min().alias("first_mjd"),
            pl.col("mjd_max").max().alias("last_mjd"),
            pl.col("n_obs").first().alias("first_trk_n_obs"),
            pl.col("n_obs").last().alias("last_trk_n_obs"),
            pl.col("n_obs").min().alias("min_trk_n_obs"),
        )
        .with_columns(
            (pl.col("last_mjd") - pl.col("first_mjd")).alias("arc_days"),
            # The coarser quantity verify.mpec.acceptance_summary is forced to use.
            (pl.col("last_night") - pl.col("first_night")).cast(pl.Float64).alias("arc_days_night"),
        )
    )


def prefit_gate(per_desig: pl.DataFrame) -> pl.DataFrame:
    """Add the MPC's published pre-fit accept/reject decision and its reasons.

    Auto-reject if: fewer than 3 distinct nights; arc < 3 days; exactly 3 nights with arc
    > 15 days; or the arc both starts *and* ends with a single-detection tracklet.

    **Four of the MPC's five substantive pre-fit conditions.** The omitted one is "a
    two-apparition linkage whose second apparition is represented only by a single
    tracklet". It is unreachable here: the linker's windows are at most 21 days and cannot
    span two apparitions, so no candidate this gate sees can trip it. Implement it before
    any linker with a multi-apparition window uses this function. (A sixth published
    condition, "the submission format is incorrect", is not a property of a candidate.)
    """
    too_few = pl.col("n_nights") < MIN_NIGHTS
    short = pl.col("arc_days") < MIN_ARC_DAYS
    three_wide = (pl.col("n_nights") == MIN_NIGHTS) & (
        pl.col("arc_days") > THREE_NIGHT_MAX_ARC_DAYS
    )
    singleton_ends = (pl.col("first_trk_n_obs") == 1) & (pl.col("last_trk_n_obs") == 1)
    return per_desig.with_columns(
        too_few.alias("reject_too_few_nights"),
        short.alias("reject_short_arc"),
        three_wide.alias("reject_three_nights_wide_arc"),
        singleton_ends.alias("reject_singleton_ends"),
        (~(too_few | short | three_wide | singleton_ends)).alias("prefit_pass"),
    )


def gate_summary(gated: pl.DataFrame) -> dict[str, Any]:
    """Funnel counts for the pre-fit gate. Reasons overlap, so they do not sum to the total."""
    passing = gated.filter(pl.col("prefit_pass"))
    return {
        "designations_considered": gated.height,
        "prefit_pass": passing.height,
        "prefit_reject": gated.height - passing.height,
        "reject_reasons": {
            "fewer_than_3_nights": int(gated["reject_too_few_nights"].sum()),
            "arc_lt_3_days": int(gated["reject_short_arc"].sum()),
            "exactly_3_nights_arc_gt_15_days": int(gated["reject_three_nights_wide_arc"].sum()),
            "singleton_tracklet_at_both_ends": int(gated["reject_singleton_ends"].sum()),
        },
        "passing": {
            "single_observatory": int((passing["n_obscodes"] == 1).sum()),
            "median_arc_days": float(passing["arc_days"].median()) if passing.height else None,
            "median_n_obs": float(passing["n_obs"].median()) if passing.height else None,
            "nights_histogram": {
                int(r["n_nights"]): int(r["n"])
                for r in passing.group_by("n_nights")
                .agg(pl.len().alias("n"))
                .sort("n_nights")
                .to_dicts()
            },
        },
    }
