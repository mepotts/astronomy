"""Reconstruct tracklets from parsed ITF observations.

A **tracklet** is the atomic unit of the ITF: a short run of detections of one moving
object, from one observatory, on one night, that some pipeline already associated but
never linked to an orbit. Definition used here::

    tracklet = (designation / trkSub, observatory code, local night)

*Local* night matters. ``floor(mjd)`` cuts in half any night that straddles UTC midnight
-- for an observatory near Greenwich (M21 Hakos, lon 16.4 deg E) that is *every* night.
The night index is therefore

    night = floor(mjd + lon_signed_deg/360 + 0.5)

which puts the boundary at local noon, so a whole night carries one index.

``lon_signed`` is east longitude wrapped to (-180, +180], **not** the 0-360 range the MPC
publishes. Both wrappings group a night correctly, but only the signed one makes the index
equal the UTC date the night is conventionally labelled with. Unwrapped, Mauna Kea
(F51, 203.7 deg E) lands a whole day late and no longer lines up with the dates printed in
an MPEC. Observatories with no longitude on file (space telescopes, roving observers) fall
back to lon = 0 -- see the note on space-based tracklets below.

For a satellite in low Earth orbit (C51/NEOWISE and friends) "night" has no meaning at
all; those tracklets can legitimately span a full 24 h and are reported separately rather
than being forced into a ground-based model.

The ITF also contains records with a *blank* designation field. Those cannot be grouped
by designation at all; they are counted and reported separately rather than being
silently merged into one giant pseudo-object.
"""

from __future__ import annotations

from typing import Any

import polars as pl

BLANK_DESIG = ""


def signed_longitude(lon_east_deg: float) -> float:
    """Wrap an MPC east longitude from [0, 360) to (-180, +180]."""
    return lon_east_deg - 360.0 if lon_east_deg > 180.0 else lon_east_deg


def add_night(
    lf: pl.LazyFrame, obscode_lon: dict[str, float] | None = None
) -> pl.LazyFrame:
    """Add a local-night index (and the signed longitude used) to a parsed-observation frame."""
    if obscode_lon:
        lon_df = pl.LazyFrame(
            {
                "obscode": list(obscode_lon.keys()),
                "lon_deg": [signed_longitude(v) for v in obscode_lon.values()],
            },
            schema={"obscode": pl.String, "lon_deg": pl.Float64},
        )
        lf = lf.join(lon_df, on="obscode", how="left")
    else:
        lf = lf.with_columns(pl.lit(0.0, dtype=pl.Float64).alias("lon_deg"))

    lon = pl.col("lon_deg").fill_null(0.0)
    return lf.with_columns(
        lon.alias("lon_deg"),
        (pl.col("mjd") + lon / 360.0 + 0.5).floor().cast(pl.Int32).alias("night"),
    )


def build_tracklets(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Group observations into tracklets. Expects the ``night`` column from :func:`add_night`."""
    return (
        lf.group_by(["desig", "obscode", "night"])
        .agg(
            pl.len().alias("n_obs"),
            pl.col("mjd").min().alias("mjd_min"),
            pl.col("mjd").max().alias("mjd_max"),
            pl.col("ra_deg").mean().alias("ra_deg"),
            pl.col("dec_deg").mean().alias("dec_deg"),
            pl.col("mag").mean().alias("mag_mean"),
            pl.col("discovery").any().alias("has_discovery"),
        )
        .with_columns(
            ((pl.col("mjd_max") - pl.col("mjd_min")) * 24.0).alias("span_hours"),
            ((pl.col("mjd_min") + pl.col("mjd_max")) / 2.0).alias("mjd_mid"),
        )
    )


def _quantiles(df: pl.DataFrame, col: str, qs: tuple[float, ...]) -> dict[str, float]:
    return {f"p{int(q * 100)}": float(df[col].quantile(q)) for q in qs}


def tracklet_stats(tracklets: pl.DataFrame, observations: pl.DataFrame) -> dict[str, Any]:
    """Summarise the tracklet population: counts, obs-per-tracklet, nights, arcs."""
    n_trk = tracklets.height
    n_obs = observations.height

    per_obs = tracklets["n_obs"]
    obs_hist = (
        tracklets.group_by("n_obs")
        .agg(pl.len().alias("tracklets"))
        .sort("n_obs")
    )

    # Per-designation view: how many tracklets / distinct nights does each object have?
    # This is what decides linkability -- the MPC auto-rejects links with <3 nights.
    per_desig = (
        tracklets.group_by("desig")
        .agg(
            pl.len().alias("n_tracklets"),
            pl.col("night").n_unique().alias("n_nights"),
            pl.col("obscode").n_unique().alias("n_obscodes"),
            pl.col("mjd_min").min().alias("first_mjd"),
            pl.col("mjd_max").max().alias("last_mjd"),
        )
        .with_columns((pl.col("last_mjd") - pl.col("first_mjd")).alias("arc_days"))
    )

    nights = tracklets["night"]
    blank = tracklets.filter(pl.col("desig") == BLANK_DESIG)

    return {
        "n_observations": n_obs,
        "n_tracklets": n_trk,
        "mean_obs_per_tracklet": round(n_obs / n_trk, 3) if n_trk else 0.0,
        "obs_per_tracklet": {
            "min": int(per_obs.min()),
            "max": int(per_obs.max()),
            "mean": round(float(per_obs.mean()), 3),
            "median": float(per_obs.median()),
            **_quantiles(tracklets, "n_obs", (0.5, 0.9, 0.99)),
        },
        "obs_per_tracklet_histogram": {
            int(r["n_obs"]): int(r["tracklets"]) for r in obs_hist.head(12).to_dicts()
        },
        "singleton_tracklets": int((per_obs == 1).sum()),
        "tracklets_ge2_obs": int((per_obs >= 2).sum()),
        "distinct_nights": int(nights.n_unique()),
        "night_mjd_min": int(nights.min()),
        "night_mjd_max": int(nights.max()),
        "distinct_designations": int(tracklets["desig"].n_unique()),
        "blank_desig_tracklets": blank.height,
        "blank_desig_observations": int(blank["n_obs"].sum()) if blank.height else 0,
        "designations": {
            "total": per_desig.height,
            "with_1_night": int((per_desig["n_nights"] == 1).sum()),
            "with_2_nights": int((per_desig["n_nights"] == 2).sum()),
            "with_3plus_nights": int((per_desig["n_nights"] >= 3).sum()),
            "multi_obscode": int((per_desig["n_obscodes"] >= 2).sum()),
        },
        "span_hours": {
            "median": float(tracklets["span_hours"].median()),
            **_quantiles(tracklets, "span_hours", (0.9, 0.99)),
            "max": float(tracklets["span_hours"].max()),
        },
    }
