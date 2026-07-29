"""Pin tracklet reconstruction, especially the local-night boundary."""

from __future__ import annotations

import polars as pl
import pytest

from itf_linker.index.tracklets import (
    add_night,
    build_tracklets,
    signed_longitude,
    tracklet_stats,
)
from itf_linker.mpc80 import OUTPUT_COLUMNS, parse_frame

# Synthetic M21 (Hakos, Namibia, lon 16.36 E) records straddling UTC midnight.
# 2026-07-21 22:48 UTC and 2026-07-22 01:12 UTC are 2.4 h apart, in the SAME local night
# (local midnight at Hakos falls at 22:55 UTC), but land on different UTC days.
STRADDLE = [
    "     K09A16C 0B2026 07 21.95000023 51 57.016-33 04 00.84         20.5 GWEO057M21",
    "     K09A16C 0B2026 07 22.05000023 51 50.832-33 05 52.77         20.5 GWEO057M21",
]
M21_LON = 16.36144


def _frame(lines: list[str]) -> pl.LazyFrame:
    return parse_frame(pl.LazyFrame({"raw": lines}, schema={"raw": pl.String})).select(
        OUTPUT_COLUMNS
    )


def test_utc_midnight_would_split_a_real_night():
    """Guard the motivation for the longitude correction: naive floor(mjd) splits this."""
    naive = _frame(STRADDLE).with_columns(pl.col("mjd").floor().alias("utc_night")).collect()
    assert naive["utc_night"].n_unique() == 2, "fixture must actually straddle UTC midnight"


def test_local_night_keeps_a_straddling_night_together():
    lf = add_night(_frame(STRADDLE), {"M21": M21_LON})
    trk = build_tracklets(lf).collect()
    assert trk.height == 1
    assert trk["n_obs"][0] == 2
    assert trk["span_hours"][0] == pytest.approx(2.4, abs=0.01)


def test_tracklet_keys_on_designation_observatory_and_night(sample_lines):
    lf = add_night(_frame(sample_lines), {})
    trk = build_tracklets(lf).collect()
    keys = set(zip(trk["desig"].to_list(), trk["obscode"].to_list()))
    # /7239 T09 (3 obs), /3469 303 (2), /07VS8M F51 (3), 00083Tm C51 (1 -- the 's' partner
    # is not an observation). The malformed 947 record never makes it this far.
    assert ("/7239", "T09") in keys
    assert ("00083Tm", "C51") in keys
    assert trk.filter(pl.col("desig") == "/7239")["n_obs"][0] == 3
    assert trk.filter(pl.col("desig") == "00083Tm")["n_obs"][0] == 1
    assert trk.filter(pl.col("desig") == "/3469")["n_obs"][0] == 2


def test_same_designation_at_two_observatories_is_two_tracklets():
    """trkSubs are not globally unique; an observatory split must never be merged."""
    a = STRADDLE[0]
    b = a[:77] + "F51"
    lf = add_night(_frame([a, b]), {"M21": M21_LON, "F51": 203.74409})
    trk = build_tracklets(lf).collect()
    assert trk.height == 2


def test_missing_longitude_falls_back_to_utc_not_null():
    lf = add_night(_frame(STRADDLE), {"XXX": 1.0})  # M21 absent from the table
    df = lf.collect()
    assert df["lon_deg"].to_list() == [0.0, 0.0]
    assert df["night"].null_count() == 0


def test_signed_longitude_wraps_to_plus_minus_180():
    assert signed_longitude(203.74409) == pytest.approx(-156.25591)  # F51, Haleakala
    assert signed_longitude(16.36144) == pytest.approx(16.36144)     # M21, Hakos
    assert signed_longitude(180.0) == pytest.approx(180.0)
    assert signed_longitude(0.0) == 0.0


def test_night_index_equals_the_utc_date_the_night_is_labelled_with():
    """Hawaii's night runs ~04:00-16:00 UTC on a single UTC day; both ends must carry that
    day's index. With unwrapped 0-360 longitude F51 lands a day late and stops lining up
    with the dates printed in an MPEC."""
    f51 = 203.74409
    lines = [
        "     /07VS8M* C2015 08 11.17000 22 01 46.974+09 36 09.70         21.9 wL     F51",
        "     /07VS8M  C2015 08 11.66000 22 01 45.814+09 36 11.55         21.7 wL     F51",
    ]
    df = add_night(_frame(lines), {"F51": f51}).collect()
    assert df["night"].n_unique() == 1
    # MJD of 2015-08-11 00:00 UTC; the night is labelled by that date.
    assert df["night"][0] == int(df["mjd"][0])


def test_tracklet_stats_shape(sample_lines):
    lf = add_night(_frame(sample_lines), {})
    obs = lf.collect()
    trk = build_tracklets(lf).collect()
    stats = tracklet_stats(trk, obs)
    assert stats["n_observations"] == obs.height
    assert stats["n_tracklets"] == trk.height
    assert stats["obs_per_tracklet"]["min"] >= 1
    assert stats["singleton_tracklets"] + stats["tracklets_ge2_obs"] == trk.height
