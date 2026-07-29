"""Spatial (HEALPix) x temporal partitioning, and the combinatorics that follow from it.

Linking is a pair-finding problem before it is an orbit-fitting problem: you must first
propose which tracklets *might* belong to the same object. Brute force is
``C(N, 2) ~ 3e12`` for N ~ 2.5M tracklets -- hopeless. Partitioning replaces it with

    for each HEALPix pixel:
        for each pair of tracklets in that pixel within W days:
            propose

The two knobs are ``nside`` (pixel scale, which must be >= the distance an object can
move in W days) and ``W`` (the temporal window). :func:`candidate_combinatorics` measures
the *exact* resulting pair count rather than assuming a uniform sky -- the ITF is very far
from uniform, being dominated by a handful of survey footprints near the ecliptic.
"""

from __future__ import annotations

from typing import Any

import astropy.units as u
import numpy as np
import polars as pl
from astropy_healpix import HEALPix

#: Rough apparent sky motion, degrees/day, for the populations of interest.
#: A main-belt asteroid near opposition tracks at ~0.2-0.3 deg/day; NEOs run far faster.
TYPICAL_MOTION_DEG_PER_DAY = {
    "main_belt": 0.30,
    "neo_slow": 1.0,
    "neo_fast": 5.0,
}


def add_healpix(df: pl.DataFrame, nside: int, order: str = "nested") -> pl.DataFrame:
    """Attach a HEALPix pixel index computed from ``ra_deg`` / ``dec_deg``."""
    hp = HEALPix(nside=nside, order=order)
    pix = hp.lonlat_to_healpix(
        df["ra_deg"].to_numpy() * u.deg,
        df["dec_deg"].to_numpy() * u.deg,
    )
    return df.with_columns(pl.Series(f"hpx{nside}", np.asarray(pix, dtype=np.int64)))


def healpix_resolution_deg(nside: int) -> float:
    """Approximate linear pixel size in degrees (sqrt of the pixel solid angle)."""
    n_pix = 12 * nside * nside
    sq_deg = 41252.96124941928 / n_pix
    return float(np.sqrt(sq_deg))


def count_pairs_within_window(
    df: pl.DataFrame,
    pixel_col: str,
    window_days: float,
    time_col: str = "mjd_mid",
    min_gap_days: float = 0.5,
) -> tuple[int, int]:
    """Exact same-pixel candidate counts within ``window_days``.

    Returns ``(pairs, triplets)``. Both exclude partners closer than ``min_gap_days``,
    which drops same-night pairs -- those are either the same tracklet or two objects
    that a single night can never distinguish, and are useless for linking.

    ``triplets`` counts, for each tracklet, the pairs of *later* partners inside its
    window, i.e. triplets keyed on their earliest member. That is the quantity that
    matters, because the MPC auto-rejects any link with fewer than three distinct nights.

    Sorted scan + binary search per pixel: O(N log N), no candidate is ever enumerated.
    """
    sub = df.select([pixel_col, time_col]).sort([pixel_col, time_col])
    pix = sub[pixel_col].to_numpy()
    tim = sub[time_col].to_numpy()
    if len(pix) == 0:
        return 0, 0
    starts = np.flatnonzero(np.r_[True, pix[1:] != pix[:-1]])
    ends = np.r_[starts[1:], len(pix)]
    pairs = 0
    triplets = 0
    for s, e in zip(starts, ends):
        m = tim[s:e]
        if len(m) < 2:
            continue
        lo = np.searchsorted(m, m + min_gap_days, side="left")
        hi = np.searchsorted(m, m + window_days, side="right")
        k = np.maximum(hi - lo, 0)  # partners in (t+min_gap, t+window]
        pairs += int(k.sum())
        triplets += int((k * (k - 1) // 2).sum())
    return pairs, triplets


def partition_stats(df: pl.DataFrame, nside: int) -> dict[str, Any]:
    """Occupancy statistics for a HEALPix partition of the tracklet population."""
    col = f"hpx{nside}"
    if col not in df.columns:
        df = add_healpix(df, nside)
    occ = df.group_by(col).agg(pl.len().alias("n")).sort("n", descending=True)
    counts = occ["n"]
    n_pix_total = 12 * nside * nside
    return {
        "nside": nside,
        "pixel_scale_deg": round(healpix_resolution_deg(nside), 4),
        "pixels_total": n_pix_total,
        "pixels_occupied": occ.height,
        "sky_fraction_occupied": round(occ.height / n_pix_total, 4),
        "tracklets_per_occupied_pixel": {
            "mean": round(float(counts.mean()), 2),
            "median": float(counts.median()),
            "p90": float(counts.quantile(0.9)),
            "p99": float(counts.quantile(0.99)),
            "max": int(counts.max()),
        },
        "busiest_pixels": [
            {"pixel": int(r[col]), "tracklets": int(r["n"])} for r in occ.head(5).to_dicts()
        ],
    }


def candidate_combinatorics(
    df: pl.DataFrame,
    nsides: tuple[int, ...] = (16, 32, 64, 128),
    windows_days: tuple[float, ...] = (3.0, 7.0, 15.0, 30.0),
) -> list[dict[str, Any]]:
    """Measure candidate-pair counts across a grid of ``(nside, window)`` choices.

    Also reports the brute-force ``C(N,2)`` baseline so the reduction factor is explicit.
    """
    n = df.height
    brute = n * (n - 1) // 2
    rows: list[dict[str, Any]] = []
    for nside in nsides:
        col = f"hpx{nside}"
        if col not in df.columns:
            df = add_healpix(df, nside)
        for w in windows_days:
            pairs, triplets = count_pairs_within_window(df, col, w)
            motion = TYPICAL_MOTION_DEG_PER_DAY["main_belt"] * w
            scale = healpix_resolution_deg(nside)
            rows.append(
                {
                    "nside": nside,
                    "pixel_scale_deg": round(scale, 3),
                    "window_days": w,
                    "candidate_pairs": pairs,
                    "candidate_triplets": triplets,
                    "brute_force_pairs": brute,
                    "reduction_factor": round(brute / pairs, 1) if pairs else None,
                    # Motion a main-belt object can make across the window. The pixel must
                    # be at least this big or genuine links fall outside the partition and
                    # are never proposed -- a silent recall failure.
                    "mb_motion_deg": round(motion, 2),
                    "pixel_covers_motion": scale >= motion,
                }
            )
    return rows
