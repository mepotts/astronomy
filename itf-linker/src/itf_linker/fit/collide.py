"""Detect trkSub name collisions: one designation, more than one object.

A trkSub is a **survey's internal tracking identifier**, assigned by that survey's own
pipeline during one processing run. It is not an IAU designation and carries no
global-uniqueness guarantee. Two surveys -- or one survey whose counter wrapped -- can
issue the same string for unrelated objects, and the ITF then shows a single "designation"
spanning years. M0 named two: ``des278`` (17 nights over 1,154 d) and ``soho183``
(12 nights over 3,555 d).

Why the obvious heuristic is not enough
---------------------------------------
"Implausible sky motion" is the natural first idea and it **fails on the very example it
is meant to catch**. Measured on this snapshot, ``des278``'s largest apparent rate between
consecutive tracklets is **0.021 deg/day** -- slower than a typical main-belt asteroid.
The reason is geometric: the great-circle separation between any two sky positions is
capped at 180 deg, so over a 713-day gap even two *random* directions imply only
~0.25 deg/day. Rate screening is sharp for short gaps and asymptotically blind for long
ones, which is exactly the regime name reuse lives in. (It does catch ``soho183``, at
4.6 deg/day.)

The three screens used here are chosen to be independent, and each is stated with what it
can and cannot do:

**1. Arc implausibility** -- the workhorse, and the only one that catches ``des278``.
An ITF trkSub covers one survey processing run. It cannot span apparitions, because
recognising that two apparitions belong to one object *is the linking problem the ITF
exists because nobody solved*. A survey that could span years under one name would have
submitted an orbit and the observations would not be in the ITF at all. The measured arc
distribution of the 3+-night designations backs this: a dense mode below 15 days
(1,878 of 2,515), a near-empty valley from 15 to 200 days (119 designations spread over
185 days, ~0.6/day, against ~125/day inside the mode), then a second population running
out to 4,945 days. The threshold is placed in that valley.

**2. Impossible sustained sky motion** -- deliberately permissive. Set well above any
plausible sustained rate rather than at the edge of one, so a flag means "no bound
solar-system object could do this", not "this looks unusual".

**3. Same-night, cross-site geometric impossibility** -- the only airtight screen, with no
tunable threshold. Two ground observatories see the same object displaced by at most
~2 R_earth / delta; even at a geocentric distance of 0.01 AU that is about 5 degrees. A
larger same-night separation between two sites is two objects, full stop. It is also rare:
in this snapshot only 11 (designation, night) cells have more than one tracklet at all.

None of this is the final defence. The decisive test is that **a single bound orbit must
fit every observation**, which the fit itself supplies -- see
:func:`itf_linker.fit.collide.post_fit_collision_check`.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

#: Longest arc credited to one genuine ITF trkSub, in days. Placed in the measured valley
#: between the single-run mode (< 15 d) and the name-reuse population (> 200 d).
MAX_TRKSUB_ARC_DAYS = 200.0

#: Largest sustained apparent rate, deg/day, between consecutive tracklets. A fast NEO can
#: exceed this for hours during a close approach, so the screen only applies to gaps of at
#: least :data:`MIN_RATE_GAP_DAYS`.
MAX_SUSTAINED_RATE_DEG_PER_DAY = 5.0
MIN_RATE_GAP_DAYS = 0.5

#: Largest same-night separation between two observatories viewing one object, in degrees.
#: Topocentric parallax is ~2 R_earth / delta; 5 deg corresponds to delta ~ 0.01 AU, closer
#: than essentially anything in the ITF.
MAX_SAME_NIGHT_CROSS_SITE_SEP_DEG = 5.0

#: Below this, a fit that dropped observations is treated as having fitted a *subset* --
#: the way a collision passes an RMS gate while describing only one of the objects in it.
MIN_USED_FRACTION = 0.8


def _unit_vectors(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra, dec = np.radians(ra_deg), np.radians(dec_deg)
    return np.column_stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])


def _great_circle_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.degrees(np.arccos(np.clip(np.sum(a * b, axis=1), -1.0, 1.0)))


def tracklet_motion(tracklets: pl.DataFrame) -> pl.DataFrame:
    """Per designation: consecutive-tracklet separations, gaps, and implied rates.

    Also reports the worst same-night separation between two tracklets of the same
    designation, which is the geometric-impossibility screen's input.
    """
    grouped = (
        tracklets.sort(["desig", "mjd_mid"])
        .group_by("desig", maintain_order=True)
        .agg(
            pl.col("ra_deg"),
            pl.col("dec_deg"),
            pl.col("mjd_mid"),
            pl.col("night"),
            pl.col("obscode"),
        )
    )
    rows: list[dict[str, Any]] = []
    for rec in grouped.iter_rows(named=True):
        vec = _unit_vectors(np.asarray(rec["ra_deg"]), np.asarray(rec["dec_deg"]))
        t = np.asarray(rec["mjd_mid"], dtype=float)
        nights = np.asarray(rec["night"])
        sep = _great_circle_deg(vec[:-1], vec[1:]) if len(t) > 1 else np.zeros(0)
        gap = np.diff(t) if len(t) > 1 else np.zeros(0)

        usable = gap >= MIN_RATE_GAP_DAYS
        rate = sep[usable] / gap[usable] if usable.any() else np.zeros(0)

        # Worst separation between two tracklets sharing a night (i.e. different sites).
        worst_same_night = 0.0
        for night in np.unique(nights):
            idx = np.flatnonzero(nights == night)
            if idx.size < 2:
                continue
            block = vec[idx]
            for i in range(len(idx)):
                d = _great_circle_deg(np.repeat(block[i : i + 1], len(idx) - i - 1, axis=0),
                                      block[i + 1 :])
                if d.size:
                    worst_same_night = max(worst_same_night, float(d.max()))

        rows.append(
            {
                "desig": rec["desig"],
                "max_sep_deg": float(sep.max()) if sep.size else 0.0,
                "max_gap_days": float(gap.max()) if gap.size else 0.0,
                "min_gap_days": float(gap.min()) if gap.size else 0.0,
                "max_rate_deg_per_day": float(rate.max()) if rate.size else 0.0,
                "max_same_night_sep_deg": worst_same_night,
            }
        )
    schema = {
        "desig": pl.String,
        "max_sep_deg": pl.Float64,
        "max_gap_days": pl.Float64,
        "min_gap_days": pl.Float64,
        "max_rate_deg_per_day": pl.Float64,
        "max_same_night_sep_deg": pl.Float64,
    }
    return pl.DataFrame(rows, schema=schema)


def screen(per_desig: pl.DataFrame, motion: pl.DataFrame) -> pl.DataFrame:
    """Join the motion statistics onto the per-designation table and flag collisions."""
    joined = per_desig.join(motion, on="desig", how="left")
    long_arc = pl.col("arc_days") > MAX_TRKSUB_ARC_DAYS
    fast = pl.col("max_rate_deg_per_day") > MAX_SUSTAINED_RATE_DEG_PER_DAY
    split_sky = pl.col("max_same_night_sep_deg") > MAX_SAME_NIGHT_CROSS_SITE_SEP_DEG
    return joined.with_columns(
        long_arc.fill_null(False).alias("collision_long_arc"),
        fast.fill_null(False).alias("collision_fast_motion"),
        split_sky.fill_null(False).alias("collision_same_night_split"),
        (
            long_arc.fill_null(False)
            | fast.fill_null(False)
            | split_sky.fill_null(False)
        ).alias("collision_suspect"),
    )


def screen_summary(screened: pl.DataFrame) -> dict[str, Any]:
    suspect = screened.filter(pl.col("collision_suspect"))
    return {
        "designations_screened": screened.height,
        "collision_suspects": suspect.height,
        "clean": screened.height - suspect.height,
        "thresholds": {
            "max_arc_days": MAX_TRKSUB_ARC_DAYS,
            "max_rate_deg_per_day": MAX_SUSTAINED_RATE_DEG_PER_DAY,
            "min_rate_gap_days": MIN_RATE_GAP_DAYS,
            "max_same_night_cross_site_sep_deg": MAX_SAME_NIGHT_CROSS_SITE_SEP_DEG,
        },
        "flagged_by": {
            "arc_too_long": int(screened["collision_long_arc"].sum()),
            "impossible_sustained_motion": int(screened["collision_fast_motion"].sum()),
            "same_night_cross_site_split": int(screened["collision_same_night_split"].sum()),
        },
        "flagged_by_only": {
            "arc_only": int(
                screened.filter(
                    pl.col("collision_long_arc")
                    & ~pl.col("collision_fast_motion")
                    & ~pl.col("collision_same_night_split")
                ).height
            ),
            "motion_only": int(
                screened.filter(
                    pl.col("collision_fast_motion")
                    & ~pl.col("collision_long_arc")
                    & ~pl.col("collision_same_night_split")
                ).height
            ),
            "same_night_only": int(
                screened.filter(
                    pl.col("collision_same_night_split")
                    & ~pl.col("collision_long_arc")
                    & ~pl.col("collision_fast_motion")
                ).height
            ),
        },
    }


def post_fit_collision_check(
    n_obs: int | None, n_used: int | None, used_nights: int | None = None
) -> tuple[bool, list[str]]:
    """The decisive test: did **one** orbit fit **all** of it?

    A name collision does not merely raise the residuals -- Find_Orb can converge on the
    subset belonging to one of the objects, discard the rest, and report a perfectly
    respectable RMS. The build self-test reproduced exactly that shape on a hard NEO arc:
    ``6 / 24 obs``, RMS 0.225", elements wrong by a factor of nine in ``a``. An RMS gate
    alone would have passed it.

    So a solution is only credited if it used essentially every observation
    (:data:`MIN_USED_FRACTION`) and -- when known -- the observations it used still span
    three nights. Returns ``(ok, reasons)``.
    """
    reasons: list[str] = []
    if not n_obs or n_used is None:
        return False, ["observation counts unavailable"]
    frac = n_used / n_obs
    if frac < MIN_USED_FRACTION:
        reasons.append(
            f"fit used only {n_used}/{n_obs} observations ({frac:.0%} < {MIN_USED_FRACTION:.0%})"
        )
    if used_nights is not None and used_nights < 3:
        reasons.append(f"observations actually used span {used_nights} nights (< 3)")
    return not reasons, reasons
