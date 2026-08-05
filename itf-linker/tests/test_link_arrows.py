"""Arrow construction: the rate fit, and every population deliberately excluded."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from itf_linker.index.tracklets import add_night
from itf_linker.ingest.fetch import parse_obscodes_full
from itf_linker.link.arrows import (
    MAX_RATE_DEG_PER_DAY,
    MAX_TRACKLET_SPAN_HOURS,
    arrow_arrays,
    build_arrows,
    fit_rates,
)

OBS_SCHEMA = {
    "desig": pl.String, "obscode": pl.String, "mjd": pl.Float64,
    "ra_deg": pl.Float64, "dec_deg": pl.Float64, "mag": pl.Float64,
    "note2": pl.String,
}

#: A real observatory with real parallax constants, so the geometry is not degenerate.
SITES = {"F51": (203.74409, 0.936241, 0.351543), "G96": (249.21128, 0.845107, 0.533611)}


def _obs(rows: list[tuple]) -> pl.DataFrame:
    """rows: ``(desig, obscode, mjd, ra, dec[, note2])``."""
    body = [(r[0], r[1], r[2], r[3], r[4], 20.0, r[5] if len(r) > 5 else "C") for r in rows]
    return pl.DataFrame(body, schema=OBS_SCHEMA, orient="row")


def _nighted(rows: list[tuple]) -> pl.DataFrame:
    return add_night(_obs(rows).lazy(), {k: v[0] for k, v in SITES.items()}).collect()


def test_rate_fit_recovers_a_known_linear_motion():
    ra_rate, dec_rate = 0.4, -0.25          # deg/day, great circle in RA
    dec0 = 30.0
    rows = []
    for k in range(4):
        dt = k * 0.01
        rows.append(
            ("A", "F51", 60000.0 + dt,
             10.0 + ra_rate * dt / np.cos(np.radians(dec0)), dec0 + dec_rate * dt)
        )
    out = fit_rates(_nighted(rows))
    assert out.height == 1
    assert out["ra_rate"][0] == pytest.approx(ra_rate, rel=2e-3)
    assert out["dec_rate"][0] == pytest.approx(dec_rate, rel=2e-3)
    assert out["mjd"][0] == pytest.approx(60000.015)


def test_rate_fit_survives_the_ra_wrap():
    """A tracklet straddling RA=0 must not acquire a 360 deg/day rate."""
    rows = [
        ("A", "F51", 60000.00, 359.98, 0.0),
        ("A", "F51", 60000.01, 359.99, 0.0),
        ("A", "F51", 60000.02, 0.005, 0.0),
    ]
    out = fit_rates(_nighted(rows))
    assert abs(out["ra_rate"][0]) < 5.0
    assert out["ra_rate"][0] == pytest.approx(1.25, rel=0.05)


def test_position_is_reported_at_the_mean_epoch():
    rows = [("A", "F51", 60000.0, 10.0, 0.0), ("A", "F51", 60000.1, 10.1, 0.0)]
    out = fit_rates(_nighted(rows))
    assert out["mjd"][0] == pytest.approx(60000.05)
    assert out["ra_deg"][0] == pytest.approx(10.05, abs=1e-6)


def test_single_detection_tracklets_are_dropped_and_counted():
    rows = [
        ("A", "F51", 60000.0, 10.0, 0.0),
        ("B", "F51", 60000.0, 20.0, 0.0), ("B", "F51", 60000.01, 20.01, 0.0),
    ]
    arrows = build_arrows(_nighted(rows), SITES)
    assert arrows.stats["dropped_single_detection_tracklets"] == 1
    assert arrows.table["desig"].to_list() == ["B"]


def test_space_based_observations_are_excluded():
    """An S record's observer is a spacecraft, not the geocentre."""
    rows = [
        ("A", "F51", 60000.0, 10.0, 0.0, "S"), ("A", "F51", 60000.01, 10.01, 0.0, "S"),
        ("B", "F51", 60000.0, 20.0, 0.0, "C"), ("B", "F51", 60000.01, 20.01, 0.0, "C"),
    ]
    arrows = build_arrows(_nighted(rows), SITES)
    assert arrows.stats["dropped_space_based_observations"] == 2
    assert arrows.table["desig"].to_list() == ["B"]


def test_sites_without_parallax_constants_are_excluded():
    rows = [
        ("A", "ZZZ", 60000.0, 10.0, 0.0), ("A", "ZZZ", 60000.01, 10.01, 0.0),
        ("B", "F51", 60000.0, 20.0, 0.0), ("B", "F51", 60000.01, 20.01, 0.0),
    ]
    arrows = build_arrows(_nighted(rows), SITES)
    assert arrows.stats["dropped_observations_without_parallax_constants"] == 2
    assert arrows.table["desig"].to_list() == ["B"]


def test_long_span_and_impossible_rate_tracklets_are_excluded():
    span = (MAX_TRACKLET_SPAN_HOURS + 1.0) / 24.0
    rows = [
        ("LONG", "F51", 60000.0, 10.0, 0.0), ("LONG", "F51", 60000.0 + span, 10.05, 0.0),
        ("FAST", "F51", 60000.0, 20.0, 0.0),
        ("FAST", "F51", 60000.001, 20.0 + MAX_RATE_DEG_PER_DAY * 0.002, 0.0),
        ("OK", "F51", 60000.0, 30.0, 0.0), ("OK", "F51", 60000.01, 30.003, 0.0),
    ]
    arrows = build_arrows(_nighted(rows), SITES)
    assert arrows.stats["dropped_long_span_tracklets"] == 1
    assert arrows.stats["dropped_implausible_rate_tracklets"] == 1
    assert arrows.table["desig"].to_list() == ["OK"]


def test_arrows_carry_a_plausible_heliocentric_observer():
    rows = [("A", "F51", 60000.0, 10.0, 0.0), ("A", "F51", 60000.01, 10.01, 0.0)]
    arrows = build_arrows(_nighted(rows), SITES)
    a = arrow_arrays(arrows.table)
    assert 0.98 < np.linalg.norm(a["obs_pos"][0]) < 1.02
    assert np.linalg.norm(a["rho_hat"][0]) == pytest.approx(1.0)


def test_the_mjd_slice_is_applied_before_anything_else():
    rows = [
        ("OLD", "F51", 50000.0, 10.0, 0.0), ("OLD", "F51", 50000.01, 10.01, 0.0),
        ("NEW", "F51", 60000.0, 20.0, 0.0), ("NEW", "F51", 60000.01, 20.01, 0.0),
    ]
    arrows = build_arrows(_nighted(rows), SITES, mjd_min=55000.0)
    assert arrows.table["desig"].to_list() == ["NEW"]


# --- the ObsCodes parser the arrows depend on ------------------------------------

def test_obscodes_full_parses_fields_that_abut():
    """Whitespace splitting silently mangles rows where the columns touch."""
    text = (
        "Code  Long.   cos      sin    Name\n"
        "005   2.231000.659891+0.748875Meudon\n"
        "F51 203.744090.936241+0.351543Pan-STARRS 1, Haleakala\n"
        "W84 289.193580.865572-0.499793Cerro Tololo-DECam\n"
        "247                           Roving Observer\n"
    )
    out = parse_obscodes_full(text)
    assert out["005"] == pytest.approx((2.2310, 0.659891, 0.748875))
    assert out["F51"] == pytest.approx((203.74409, 0.936241, 0.351543))
    assert out["W84"][2] == pytest.approx(-0.499793)
    assert "247" not in out          # blank coordinates are omitted, not defaulted
    assert "Cod" not in out


def test_window_slicing_by_binary_search_matches_a_filter():
    """The sorted slice is an optimisation, so it must return the same rows.

    Randomised over window edges that fall between arrows, exactly on an arrow, before
    everything and after everything -- the cases where an off-by-one would show up as a
    quietly missing tracklet rather than as an error.
    """
    import random

    import polars as pl

    from itf_linker.link.arrows import Arrows

    rng = random.Random(7)
    mjd = sorted(round(rng.uniform(60000.0, 60050.0), 3) for _ in range(200))
    table = pl.DataFrame({"mjd": mjd, "arrow_id": list(range(len(mjd)))})
    arrows = Arrows(table=table, stats={})
    edges = [59990.0, 60000.0, 60060.0, *rng.sample(mjd, 12)]
    for lo in edges:
        for width in (0.0, 0.5, 5.0, 14.0, 100.0):
            got = arrows.slice_window(lo, lo + width)
            want = table.filter((pl.col("mjd") >= lo) & (pl.col("mjd") < lo + width))
            assert got["arrow_id"].to_list() == want["arrow_id"].to_list(), (lo, width)
