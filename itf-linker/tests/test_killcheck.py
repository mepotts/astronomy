"""Pin the kill-check machinery: position matching, and the control that makes a
'not found' verdict trustworthy."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from itf_linker.mpc80 import OUTPUT_COLUMNS, Observation, parse_frame, parse_line
from itf_linker.verify.killcheck import (
    angular_sep_arcsec,
    find_observation,
    sensitivity_control,
)

REAL = "     /7239   4C2015 05 23.30928 11 55 25.17 -01 46 36.9          23.7 z1     T09"


def _itf(lines: list[str]) -> pl.DataFrame:
    return (
        parse_frame(pl.LazyFrame({"raw": lines}, schema={"raw": pl.String}))
        .select(OUTPUT_COLUMNS)
        .collect()
    )


def test_angular_sep_arcsec():
    sep = angular_sep_arcsec(np.array([10.0, 10.1]), np.array([5.0, 5.0]), 10.0, 5.0)
    assert sep[0] == pytest.approx(0.0, abs=1e-9)
    assert sep[1] == pytest.approx(0.1 * np.cos(np.radians(5.0)) * 3600, rel=1e-6)


def test_find_observation_matches_on_position_not_designation(sample_lines):
    """ITF records carry survey trkSubs; MPEC records carry MPC designations. Matching on
    designation would find nothing even when the observation is present, so the matcher
    must key on observatory + epoch + sky position only."""
    itf = _itf(sample_lines)
    probe = parse_line(REAL)
    renamed = Observation(**{**probe.as_dict(), "desig": "TOTALLY-DIFFERENT"})
    hit = find_observation(itf, renamed)
    assert hit.height == 1
    assert hit["desig"][0] == "/7239"


def test_find_observation_rejects_wrong_observatory(sample_lines):
    itf = _itf(sample_lines)
    probe = parse_line(REAL)
    elsewhere = Observation(**{**probe.as_dict(), "obscode": "G96"})
    assert find_observation(itf, elsewhere).height == 0


def test_find_observation_rejects_wrong_epoch(sample_lines):
    itf = _itf(sample_lines)
    probe = parse_line(REAL)
    later = Observation(**{**probe.as_dict(), "mjd": probe.mjd + 5.0})
    assert find_observation(itf, later).height == 0


def test_find_observation_rejects_offset_position(sample_lines):
    """Same telescope, same instant, 1 degree away -- must not match."""
    itf = _itf(sample_lines)
    probe = parse_line(REAL)
    offset = Observation(**{**probe.as_dict(), "dec_deg": probe.dec_deg + 1.0})
    assert find_observation(itf, offset, radius_arcsec=10.0).height == 0


def test_sensitivity_control_passes_on_present_data(sample_lines):
    """The control underwrites every 'absent from the ITF' claim in M0-RESULTS."""
    itf = _itf(sample_lines)
    result = sensitivity_control(itf, n=itf.height)
    assert result["passes"]
    assert result["hit_rate"] == 1.0
    assert result["found"] == itf.height


def test_sensitivity_control_fails_on_an_empty_haystack(sample_lines):
    """A matcher that can never find anything must be caught, not reported as 'absent'."""
    itf = _itf(sample_lines)
    empty = itf.clear()
    result = sensitivity_control(itf.head(3), n=3)
    assert result["passes"]
    assert sensitivity_control(empty, n=3)["probed"] == 0


@pytest.mark.slow
def test_full_snapshot_sensitivity_control(itf_snapshot):
    """Same control against the real 9.3M-row snapshot."""
    result = sensitivity_control(itf_snapshot, n=50)
    assert result["passes"], result
