"""Tracklets with a rate -- the unit HelioLinC actually consumes.

M0's tracklet table carries a mean position and a time span. That is enough to *count*
tracklets but not to link them: HelioLinC needs a state vector, and a state vector needs a
velocity, which on the sky means the tracklet's apparent motion. A tracklet plus its
sky-plane rate is conventionally called an **arrow**, and this module builds them.

The rate comes from an ordinary least-squares line through the tracklet's own detections,
in a gnomonic-ish local frame anchored on the first detection::

    x = wrap(alpha - alpha_0) * cos(delta_0)      y = delta - delta_0

with the RA difference wrapped to (-180, +180] so a tracklet straddling RA = 0 does not
acquire a 360 deg/day rate. ``x`` is a great-circle offset, so the fitted ``dx/dt`` is
already ``mu_alpha * cos(delta)`` -- the quantity
:func:`itf_linker.link.geometry.unit_vector_rates` expects.

**Three populations are excluded, each for a stated reason:**

*Single-detection tracklets* have no rate at all. 6,377 of the ITF's 2.63M tracklets
(0.24%) are singletons, so this costs almost nothing. They are *not* unusable in
principle -- the MPC only rejects a link whose arc both starts and ends with one -- but a
rateless tracklet cannot be promoted to a state vector, so it cannot participate in the
clustering step.

*Zero-baseline tracklets*, whose detections share one timestamp, would divide by zero.

*Space-based tracklets* (note-2 ``S``) are dropped: the observer is a spacecraft whose
position is on the following ``s`` line, in the RA/Dec columns. Treating one as
geocentric misplaces the observer by up to ~0.01 AU, far more than any clustering
radius, and would fabricate links rather than find them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl

#: Tracklets whose detections span longer than this are not one short arc of one object.
#: The ITF's median tracklet span is 0.64 h and its p99 is 4.56 h; the 1,901 tracklets
#: beyond 12 h are almost all C51/NEOWISE, i.e. a satellite for which "night" has no
#: meaning. A linear rate over half a day is not a rate.
MAX_TRACKLET_SPAN_HOURS = 12.0

#: Sky-plane rates beyond this are not a solar-system object seen from the ground; they
#: are a mis-associated tracklet. Even a fast NEO at closest approach rarely exceeds a few
#: degrees per day, and the fitted rate on a 30-minute baseline is noisy, so this is set
#: permissively -- it exists to bound the hypothesis geometry, not to classify.
MAX_RATE_DEG_PER_DAY = 20.0


@dataclass(slots=True)
class Arrows:
    """A set of rate-bearing tracklets, ready for the linker.

    Columns are held as a polars frame rather than as objects: every downstream step is a
    vectorised numpy operation over all of them at once.
    """

    table: pl.DataFrame
    stats: dict[str, Any]

    def __len__(self) -> int:
        return self.table.height

    def slice_window(self, mjd_lo: float, mjd_hi: float) -> pl.DataFrame:
        """Arrows whose mean epoch falls in ``[mjd_lo, mjd_hi)``.

        :func:`build_arrows` leaves the table sorted by ``mjd``, so this is a binary search
        and a zero-copy slice rather than a scan. That is not a micro-optimisation. A
        filter costs one pass over the whole table per window, and the number of windows
        grows with the *span* of the slice while the table grows with its *size*: the
        MJD > 60000 slice is 359 windows over 511k arrows (cheap either way), while the
        pre-60000 slice with the 5-day NEO window is ~19,000 windows over 2.1M arrows --
        4 x 10^10 rows scanned to build slices that mostly hold a few hundred arrows.
        """
        mjd = self.table["mjd"]
        lo = int(mjd.search_sorted(mjd_lo, side="left"))
        hi = int(mjd.search_sorted(mjd_hi, side="left"))
        return self.table.slice(lo, max(hi - lo, 0))


def fit_rates(observations: pl.DataFrame) -> pl.DataFrame:
    """One row per ``(desig, obscode, night)`` with a position, a time and a fitted rate.

    ``observations`` must already carry the ``night`` column from
    :func:`itf_linker.index.tracklets.add_night`.
    """
    ref = ["desig", "obscode", "night"]
    prepared = observations.sort(ref + ["mjd"]).with_columns(
        pl.col("ra_deg").first().over(ref).alias("_ra0"),
        pl.col("dec_deg").first().over(ref).alias("_dec0"),
    )
    prepared = prepared.with_columns(
        (
            ((pl.col("ra_deg") - pl.col("_ra0") + 180.0) % 360.0 - 180.0)
            * (pl.col("_dec0") * np.pi / 180.0).cos()
        ).alias("_x"),
        (pl.col("dec_deg") - pl.col("_dec0")).alias("_y"),
    )
    agg = (
        prepared.group_by(ref, maintain_order=True)
        .agg(
            pl.len().alias("n_obs"),
            pl.col("mjd").mean().alias("mjd"),
            pl.col("mjd").min().alias("mjd_min"),
            pl.col("mjd").max().alias("mjd_max"),
            pl.col("_ra0").first().alias("_ra0"),
            pl.col("_dec0").first().alias("_dec0"),
            pl.col("_x").mean().alias("_xbar"),
            pl.col("_y").mean().alias("_ybar"),
            pl.cov("mjd", "_x").alias("_cxt"),
            pl.cov("mjd", "_y").alias("_cyt"),
            pl.col("mjd").var().alias("_vt"),
            pl.col("mag").mean().alias("mag"),
        )
        .with_columns(
            (pl.col("_ra0") + pl.col("_xbar") / (pl.col("_dec0") * np.pi / 180.0).cos())
            .alias("ra_deg"),
            (pl.col("_dec0") + pl.col("_ybar")).alias("dec_deg"),
            (pl.col("_cxt") / pl.col("_vt")).alias("ra_rate"),
            (pl.col("_cyt") / pl.col("_vt")).alias("dec_rate"),
            ((pl.col("mjd_max") - pl.col("mjd_min")) * 24.0).alias("span_hours"),
        )
    )
    return agg.drop([c for c in agg.columns if c.startswith("_")])


def build_arrows(
    observations: pl.DataFrame,
    obscodes: dict[str, tuple[float, float, float]],
    *,
    mjd_min: float | None = None,
    mjd_max: float | None = None,
) -> Arrows:
    """Build rate-bearing tracklets, attach observer geometry, and report the exclusions.

    ``observations`` is the bad-data-filtered, night-indexed observation frame.
    ``obscodes`` maps observatory code to ``(east longitude, rho cos phi', rho sin phi')``.

    The returned table carries, per arrow: ``desig``, ``obscode``, ``night``, ``n_obs``,
    ``mjd`` (mean epoch, UTC), ``ra_deg``/``dec_deg`` at that epoch, ``ra_rate``
    (great-circle) and ``dec_rate`` in deg/day, and the observer's heliocentric position
    and velocity in AU and AU/day.
    """
    stats: dict[str, Any] = {"observations_in": observations.height}

    obs = observations
    if mjd_min is not None:
        obs = obs.filter(pl.col("mjd") >= mjd_min)
    if mjd_max is not None:
        obs = obs.filter(pl.col("mjd") < mjd_max)
    stats["observations_in_window"] = obs.height

    space_based = obs.filter(pl.col("note2") == "S").height
    obs = obs.filter(pl.col("note2") != "S")
    stats["dropped_space_based_observations"] = space_based

    known = set(obscodes)
    unknown_site = obs.filter(~pl.col("obscode").is_in(known)).height
    obs = obs.filter(pl.col("obscode").is_in(known))
    stats["dropped_observations_without_parallax_constants"] = unknown_site

    table = fit_rates(obs)
    stats["tracklets"] = table.height

    n_single = table.filter(pl.col("n_obs") < 2).height
    table = table.filter(pl.col("n_obs") >= 2)
    stats["dropped_single_detection_tracklets"] = n_single

    n_zero_baseline = table.filter(
        pl.col("ra_rate").is_null() | pl.col("dec_rate").is_null()
    ).height
    table = table.filter(pl.col("ra_rate").is_not_null() & pl.col("dec_rate").is_not_null())
    stats["dropped_zero_baseline_tracklets"] = n_zero_baseline

    n_long = table.filter(pl.col("span_hours") > MAX_TRACKLET_SPAN_HOURS).height
    table = table.filter(pl.col("span_hours") <= MAX_TRACKLET_SPAN_HOURS)
    stats["dropped_long_span_tracklets"] = n_long

    rate = (pl.col("ra_rate") ** 2 + pl.col("dec_rate") ** 2).sqrt()
    n_fast = table.filter(rate > MAX_RATE_DEG_PER_DAY).height
    table = table.filter(rate <= MAX_RATE_DEG_PER_DAY)
    stats["dropped_implausible_rate_tracklets"] = n_fast

    table = table.sort("mjd").with_row_index("arrow_id")
    table = _attach_observer(table, obscodes)
    stats["arrows"] = table.height
    return Arrows(table=table, stats=stats)


def _attach_observer(
    table: pl.DataFrame, obscodes: dict[str, tuple[float, float, float]]
) -> pl.DataFrame:
    """Add heliocentric observer position/velocity columns to an arrow table."""
    from .geometry import observer_heliocentric

    if table.height == 0:
        empty = np.zeros((0, 3))
        return table.with_columns(
            [pl.Series(f"obs_{k}", empty[:, i]) for i, k in enumerate("xyz")]
            + [pl.Series(f"obs_v{k}", empty[:, i]) for i, k in enumerate("xyz")]
        )

    codes = table["obscode"].to_list()
    lon = np.array([obscodes[c][0] for c in codes])
    rc = np.array([obscodes[c][1] for c in codes])
    rs = np.array([obscodes[c][2] for c in codes])
    pos, vel = observer_heliocentric(table["mjd"].to_numpy(), lon, rc, rs)
    return table.with_columns(
        [pl.Series(f"obs_{k}", pos[:, i]) for i, k in enumerate("xyz")]
        + [pl.Series(f"obs_v{k}", vel[:, i]) for i, k in enumerate("xyz")]
    )


def arrow_arrays(table: pl.DataFrame) -> dict[str, np.ndarray]:
    """Unpack an arrow table into the numpy arrays the linker works on."""
    from .geometry import unit_vector_rates, unit_vectors

    ra = table["ra_deg"].to_numpy()
    dec = table["dec_deg"].to_numpy()
    return {
        "mjd": table["mjd"].to_numpy(),
        "rho_hat": unit_vectors(ra, dec),
        "rho_hat_dot": unit_vector_rates(
            ra, dec, table["ra_rate"].to_numpy(), table["dec_rate"].to_numpy()
        ),
        "obs_pos": np.column_stack(
            [table["obs_x"].to_numpy(), table["obs_y"].to_numpy(), table["obs_z"].to_numpy()]
        ),
        "obs_vel": np.column_stack(
            [table["obs_vx"].to_numpy(), table["obs_vy"].to_numpy(), table["obs_vz"].to_numpy()]
        ),
        "night": table["night"].to_numpy(),
        "arrow_id": table["arrow_id"].to_numpy(),
    }
