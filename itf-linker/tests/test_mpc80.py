"""Pin the 80-column parser: field positions, epochs, continuation lines, and the
agreement between the scalar and vectorised implementations."""

from __future__ import annotations

import math

import polars as pl
import pytest
from astropy.time import Time

from itf_linker.mpc80 import (
    CONTINUATION_NOTE2,
    OUTPUT_COLUMNS,
    Mpc80ParseError,
    gregorian_to_mjd,
    parse_frame,
    parse_line,
)

# A real ITF record, decomposed by hand from the published column table.
REAL = "     /7239   4C2015 05 23.30928 11 55 25.17 -01 46 36.9          23.7 z1     T09"


def test_line_is_exactly_eighty_columns(sample_lines):
    assert all(len(ln) == 80 for ln in sample_lines)


def test_field_positions():
    obs = parse_line(REAL)
    assert obs is not None
    assert obs.number == ""            # cols 1-5 are blank throughout the ITF
    assert obs.desig == "/7239"        # cols 6-12, a survey trkSub
    assert obs.discovery is False      # col 13
    assert obs.note1 == "4"            # col 14
    assert obs.note2 == "C"            # col 15, CCD
    assert (obs.year, obs.month) == (2015, 5)
    assert obs.day == pytest.approx(23.30928)
    assert obs.band == "z"             # col 71
    assert obs.catalog == "1"          # col 72
    assert obs.obscode == "T09"        # cols 78-80
    assert obs.mag == pytest.approx(23.7)


def test_sexagesimal_conversion():
    obs = parse_line(REAL)
    # 11h 55m 25.17s -> degrees;  -01d 46' 36.9"
    assert obs.ra_deg == pytest.approx(15 * (11 + 55 / 60 + 25.17 / 3600))
    assert obs.dec_deg == pytest.approx(-(1 + 46 / 60 + 36.9 / 3600))


def test_negative_declination_sign_is_read_from_column_45():
    """The sign lives in col 45, separate from the degrees field -- so -00d must work."""
    line = REAL[:44] + "-00 46 36.9 " + REAL[56:]
    assert parse_line(line).dec_deg == pytest.approx(-(46 / 60 + 36.9 / 3600))
    line_pos = REAL[:44] + "+00 46 36.9 " + REAL[56:]
    assert parse_line(line_pos).dec_deg == pytest.approx(+(46 / 60 + 36.9 / 3600))


@pytest.mark.parametrize(
    "year,month,day",
    [(2015, 5, 23.30928), (2026, 7, 20.586075), (1858, 11, 17.0), (2000, 1, 1.5)],
)
def test_mjd_matches_astropy(year, month, day):
    mine = gregorian_to_mjd(year, month, day)
    ref = Time(f"{year}-{month:02d}-01T00:00:00", scale="utc").mjd + (day - 1)
    assert mine == pytest.approx(ref, abs=1e-9)


def test_continuation_lines_are_not_observations(sample_lines):
    """A space-based observation is TWO physical lines; only the 'S' line is a detection.

    The 's' line carries the spacecraft's geocentric x/y/z in the RA/Dec columns. Counting
    it would both inflate the observation count and inject a nonsense sky position.
    """
    s_lines = [ln for ln in sample_lines if ln[14] == "s"]
    assert s_lines, "fixture must contain a continuation line"
    assert all(parse_line(ln) is None for ln in s_lines)
    assert "s" in CONTINUATION_NOTE2


def test_malformed_record_is_rejected_not_silently_coerced(sample_lines):
    """The 947 record has 'Dec seconds' of `39 8` -- a missing decimal point in the source."""
    bad = [ln for ln in sample_lines if ln.startswith("     BCH0108")]
    assert len(bad) == 1
    with pytest.raises(Mpc80ParseError):
        parse_line(bad[0], strict=True)
    assert parse_line(bad[0], strict=False) is None


def test_discovery_asterisk(sample_lines):
    disc = [ln for ln in sample_lines if ln[12] == "*"]
    assert disc, "fixture must contain a discovery record"
    assert all(parse_line(ln).discovery for ln in disc)


def test_scalar_and_vectorised_parsers_agree(sample_lines):
    """The two implementations exist for different reasons; they must not drift."""
    scalar = [parse_line(ln, strict=False) for ln in sample_lines]
    scalar = [o for o in scalar if o is not None]

    frame = (
        parse_frame(pl.LazyFrame({"raw": sample_lines}, schema={"raw": pl.String}))
        .select(OUTPUT_COLUMNS)
        .collect()
    )
    assert frame.height == len(scalar)

    for got, want in zip(frame.iter_rows(named=True), scalar):
        assert got["desig"] == want.desig
        assert got["obscode"] == want.obscode
        assert got["discovery"] == want.discovery
        assert got["note2"] == want.note2
        assert got["mjd"] == pytest.approx(want.mjd, abs=1e-9)
        assert got["ra_deg"] == pytest.approx(want.ra_deg, abs=1e-9)
        assert got["dec_deg"] == pytest.approx(want.dec_deg, abs=1e-9)
        if want.mag is None:
            assert got["mag"] is None or math.isnan(got["mag"])
        else:
            assert got["mag"] == pytest.approx(want.mag)


def test_vectorised_parser_drops_the_same_rows(sample_lines):
    frame = parse_frame(
        pl.LazyFrame({"raw": sample_lines}, schema={"raw": pl.String})
    ).collect()
    # 11 fixture lines - 1 continuation - 1 malformed = 9 observations
    assert frame.height == 9
    assert "s" not in frame["note2"].to_list()


def test_blank_and_short_lines():
    assert parse_line("") is None
    assert parse_line("   \n") is None
    padded = parse_line(REAL.rstrip()[:78])  # truncated, still parseable
    assert padded is not None
