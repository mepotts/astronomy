"""Candidate selection, trkSub collision screening, and the ITF line extractor."""

from __future__ import annotations

import gzip

import polars as pl
import pytest

from itf_linker.fit import collide
from itf_linker.fit.candidates import (
    MIN_PLAUSIBLE_MJD,
    bad_data_filter,
    gate_summary,
    per_designation,
    prefit_gate,
)
from itf_linker.fit.extract import extract_lines
from itf_linker.index.tracklets import add_night, build_tracklets
from itf_linker.verify.mpec import acceptance_summary

OBS_SCHEMA = {
    "desig": pl.String, "obscode": pl.String, "mjd": pl.Float64,
    "ra_deg": pl.Float64, "dec_deg": pl.Float64,
    "mag": pl.Float64, "discovery": pl.Boolean,
}


def _obs(rows: list[tuple]) -> pl.DataFrame:
    filled = [(*row, 20.0, False) for row in rows]
    return pl.DataFrame(filled, schema=OBS_SCHEMA, orient="row")


def _tracklets(rows: list[tuple]) -> pl.DataFrame:
    """Build tracklets through the production code path, not a hand-made frame."""
    return build_tracklets(add_night(_obs(rows).lazy(), {})).collect()


# ----------------------------------------------------------------------------------
# Bad-data filter
# ----------------------------------------------------------------------------------

def test_bad_data_filter_removes_exactly_the_known_defects():
    rows = [
        ("good1", "F51", 60000.5, 10.0, 5.0),
        ("good1", "F51", 60000.6, 10.1, 5.0),
        ("sentinel", "705", 0.0002, 10.0, 5.0),          # pre-1900 sentinel epoch
        ("", "F51", 60000.5, 12.0, 5.0),                  # blank designation
        ("dupe", "W84", 60700.25, 142.88, -6.49),
        ("dupe", "W84", 60700.25, 142.88, -6.49),         # byte-identical repeat
        ("dupe", "W84", 60700.25, 142.88, -6.49),
    ]
    kept, stats = bad_data_filter(_obs(rows).lazy())
    kept = kept.collect()
    assert stats["input"] == 7
    assert stats["dropped_pre_1900_epoch"] == 1
    assert stats["dropped_blank_designation"] == 1
    assert stats["dropped_duplicate_records"] == 2
    assert stats["kept"] == kept.height == 3
    assert set(kept["desig"]) == {"good1", "dupe"}


def test_duplicate_removal_does_not_merge_distinct_observations():
    """Same object, same night, one second apart -- two measurements, not one."""
    rows = [
        ("d", "F51", 60000.500000, 10.0, 5.0),
        ("d", "F51", 60000.500012, 10.0, 5.0),
    ]
    kept, stats = bad_data_filter(_obs(rows).lazy())
    assert stats["dropped_duplicate_records"] == 0
    assert kept.collect().height == 2


def test_pre_1900_threshold_is_1900_01_01():
    assert MIN_PLAUSIBLE_MJD == 15020.0


# ----------------------------------------------------------------------------------
# The published pre-fit gate, pinned against the MPEC implementation
# ----------------------------------------------------------------------------------

def _gate_one(rows: list[tuple]) -> dict:
    gated = prefit_gate(per_designation(_tracklets(rows)))
    return gated.to_dicts()[0]


def _nightly(desig: str, nights: list[tuple[int, int]], obscode: str = "F51") -> list[tuple]:
    """``nights`` is [(night_mjd, n_detections), ...]; positions drift 0.2 deg/day."""
    out = []
    for night, n in nights:
        for k in range(n):
            mjd = night + 0.1 + 0.01 * k
            out.append((desig, obscode, mjd, 10.0 + 0.2 * (night - nights[0][0]), 5.0))
    return out


def test_gate_accepts_a_clean_three_night_arc():
    row = _gate_one(_nightly("ok", [(60000, 3), (60003, 3), (60006, 3)]))
    assert row["prefit_pass"]
    assert row["n_nights"] == 3
    assert row["arc_days"] == pytest.approx(6.02, abs=0.05)


@pytest.mark.parametrize(
    ("nights", "flag"),
    [
        ([(60000, 3), (60001, 3)], "reject_too_few_nights"),
        ([(60000, 3), (60001, 3), (60002, 3)], "reject_short_arc"),
        ([(60000, 3), (60010, 3), (60030, 3)], "reject_three_nights_wide_arc"),
        ([(60000, 1), (60004, 3), (60008, 1)], "reject_singleton_ends"),
    ],
)
def test_gate_rejects_each_published_failure_mode(nights, flag):
    row = _gate_one(_nightly("x", nights))
    assert not row["prefit_pass"]
    assert row[flag] is True


def test_four_nights_may_span_more_than_fifteen_days():
    """The 15-day limit is specific to *exactly* three nights."""
    row = _gate_one(_nightly("x", [(60000, 3), (60010, 3), (60020, 3), (60030, 3)]))
    assert row["prefit_pass"]


def test_singleton_at_only_one_end_is_allowed():
    row = _gate_one(_nightly("x", [(60000, 1), (60004, 3), (60008, 3)]))
    assert row["prefit_pass"]


def test_vectorised_gate_agrees_with_the_mpec_implementation():
    """Two implementations of one published rule, pinned against each other.

    ``acceptance_summary`` loops over one MPEC's tracklets; ``prefit_gate`` is vectorised
    over millions of designations. They are fed the same decomposition, with the arc
    measured the same way (night midnights), so any disagreement is a real divergence.
    """
    cases = [
        [(60000, 3), (60003, 3), (60006, 3)],
        [(60000, 3), (60001, 3)],
        [(60000, 3), (60001, 3), (60002, 3)],
        [(60000, 3), (60010, 3), (60030, 3)],
        [(60000, 1), (60004, 3), (60008, 1)],
        [(60000, 3), (60010, 3), (60020, 3), (60030, 3)],
    ]
    for nights in cases:
        row = _gate_one(_nightly("x", nights))
        scalar = acceptance_summary(
            [
                {
                    "obs_date": str(night),
                    "obscode": "F51",
                    "n_obs": n,
                    "mjd_midnight": float(night),
                }
                for night, n in nights
            ]
        )
        vector_pass = (
            row["n_nights"] >= 3
            and row["arc_days_night"] >= 3
            and not (row["n_nights"] == 3 and row["arc_days_night"] > 15)
            and not row["reject_singleton_ends"]
        )
        assert vector_pass == scalar["passes"], (nights, row, scalar)


def test_gate_summary_counts_add_up():
    rows = (
        _nightly("pass", [(60000, 3), (60003, 3), (60006, 3)])
        + _nightly("short", [(60000, 3), (60001, 3), (60002, 3)])
    )
    summary = gate_summary(prefit_gate(per_designation(_tracklets(rows))))
    assert summary["designations_considered"] == 2
    assert summary["prefit_pass"] + summary["prefit_reject"] == 2
    assert summary["reject_reasons"]["arc_lt_3_days"] == 1


# ----------------------------------------------------------------------------------
# trkSub collision screening
# ----------------------------------------------------------------------------------

def _screen(rows: list[tuple]) -> dict:
    trk = _tracklets(rows)
    screened = collide.screen(prefit_gate(per_designation(trk)), collide.tracklet_motion(trk))
    return screened.to_dicts()[0]


def test_a_plausible_single_run_arc_is_not_flagged():
    assert not _screen(_nightly("ok", [(60000, 3), (60003, 3), (60006, 3)]))["collision_suspect"]


def test_multi_year_arc_under_one_trksub_is_flagged():
    """des278 (1,154 d) and soho183 (3,555 d) are the real examples this encodes."""
    row = _screen(_nightly("reused", [(56000, 3), (56500, 3), (57154, 3)]))
    assert row["collision_long_arc"] and row["collision_suspect"]


def test_the_rate_screen_alone_would_miss_a_long_arc_collision():
    """Measured on des278: 0.021 deg/day, slower than a main-belt asteroid.

    Great-circle separation saturates at 180 deg, so over a 700-day gap even two random
    directions imply a small rate. This is why the arc screen exists and why "implausible
    sky motion" is not sufficient on its own.
    """
    rows = [
        ("reused", "F51", 56000.1, 10.0, 5.0), ("reused", "F51", 56000.2, 10.0, 5.0),
        ("reused", "F51", 56700.1, 12.0, 5.0), ("reused", "F51", 56700.2, 12.0, 5.0),
        ("reused", "F51", 57154.1, 14.0, 5.0), ("reused", "F51", 57154.2, 14.0, 5.0),
    ]
    row = _screen(rows)
    assert row["max_rate_deg_per_day"] < 0.1          # far below any plausible limit
    assert not row["collision_fast_motion"]           # the rate screen sees nothing
    assert row["collision_long_arc"] and row["collision_suspect"]   # the arc screen does


def test_impossible_sustained_motion_is_flagged():
    rows = [
        ("fast", "F51", 60000.1, 10.0, 5.0), ("fast", "F51", 60000.2, 10.0, 5.0),
        ("fast", "F51", 60003.1, 80.0, 5.0), ("fast", "F51", 60003.2, 80.0, 5.0),
        ("fast", "F51", 60006.1, 150.0, 5.0), ("fast", "F51", 60006.2, 150.0, 5.0),
    ]
    row = _screen(rows)
    assert row["max_rate_deg_per_day"] > collide.MAX_SUSTAINED_RATE_DEG_PER_DAY
    assert row["collision_fast_motion"] and row["collision_suspect"]


def test_same_night_cross_site_split_is_geometrically_impossible():
    """Two sites see one object displaced by ~2 R_earth/delta: degrees at most, never 170."""
    rows = [
        ("split", "F51", 60000.10, 10.0, 5.0), ("split", "F51", 60000.11, 10.0, 5.0),
        ("split", "G96", 60000.12, 190.0, -40.0), ("split", "G96", 60000.13, 190.0, -40.0),
        ("split", "T09", 60003.10, 11.0, 5.0), ("split", "T09", 60003.11, 11.0, 5.0),
    ]
    row = _screen(rows)
    assert row["max_same_night_sep_deg"] > collide.MAX_SAME_NIGHT_CROSS_SITE_SEP_DEG
    assert row["collision_same_night_split"] and row["collision_suspect"]


def test_gaps_below_half_a_day_do_not_trigger_the_rate_screen():
    """A close-approaching NEO really can move degrees per day for a few hours."""
    rows = [
        ("neo", "F51", 60000.10, 10.0, 5.0), ("neo", "F51", 60000.12, 10.0, 5.0),
        ("neo", "F51", 60000.30, 10.4, 5.0), ("neo", "F51", 60000.32, 10.4, 5.0),
        ("neo", "F51", 60004.10, 12.0, 5.0), ("neo", "F51", 60004.12, 12.0, 5.0),
    ]
    assert not _screen(rows)["collision_fast_motion"]


# ----------------------------------------------------------------------------------
# The post-fit collision guard
# ----------------------------------------------------------------------------------

def test_subset_guard_rejects_a_fit_that_dropped_most_observations():
    """The failure mode the self-test reproduced: 6/24 used, RMS 0.225", elements wrong."""
    ok, reasons = collide.post_fit_collision_check(n_obs=24, n_used=6, used_nights=2)
    assert not ok
    assert any("6/24" in r for r in reasons)
    assert any("2 nights" in r for r in reasons)


def test_subset_guard_accepts_a_complete_fit():
    ok, reasons = collide.post_fit_collision_check(n_obs=9, n_used=9, used_nights=3)
    assert ok and not reasons


def test_subset_guard_needs_the_used_observations_to_still_span_three_nights():
    ok, reasons = collide.post_fit_collision_check(n_obs=9, n_used=9, used_nights=2)
    assert not ok and any("nights" in r for r in reasons)


def test_subset_guard_reports_missing_counts_rather_than_assuming():
    assert collide.post_fit_collision_check(None, None) == (
        False, ["observation counts unavailable"]
    )


# ----------------------------------------------------------------------------------
# Extraction of original 80-column lines
# ----------------------------------------------------------------------------------

def _line(desig: str, note2: str, day: str, obscode: str) -> str:
    """An exact 80-column record: desig in 6-12, note 2 in **column 15**, obscode in 78-80."""
    line = f"     {desig:<7.7s}  {note2}2024 01 {day} 22 53 22.106+03 17 39.61"
    line = line.ljust(71) + "X" + " " * 5 + obscode
    assert len(line) == 80 and line[14] == note2 and line[77:80] == obscode
    return line


def test_extract_keeps_original_bytes_and_pairs_space_based_records(tmp_path):
    gz = tmp_path / "itf.txt.gz"
    lines = [
        _line("WANT1", "C", "05.041667", "F51"),
        _line("OTHER", "C", "05.041667", "F51"),
        _line("WANT1", "S", "06.041667", "C51"),
        _line("WANT1", "s", "06.041667", "C51"),   # spacecraft position -- must follow
        _line("WANT1", "S", "07.041667", "C51"),   # unpaired: no 's' line follows
        _line("WANT1", "C", "08.041667", "F51"),
    ]
    with gzip.open(gz, "wt", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    out, stats = extract_lines(["WANT1"], src=gz)
    kept = out["WANT1"]
    assert kept == [lines[0], lines[2], lines[3], lines[5]]
    assert stats["observations_kept"] == 3
    assert stats["continuations_kept"] == 1
    assert stats["dropped_unpaired_paired_note"] == 1
    assert all(len(ln) == 80 for ln in kept)


def test_extract_drops_a_trailing_unpaired_space_observation(tmp_path):
    gz = tmp_path / "itf.txt.gz"
    lines = [_line("W", "C", "05.041667", "F51"), _line("W", "S", "06.041667", "C51")]
    with gzip.open(gz, "wt", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    out, stats = extract_lines(["W"], src=gz)
    assert out["W"] == [lines[0]]
    assert stats["dropped_unpaired_paired_note"] == 1


def test_extract_ignores_designations_not_asked_for(tmp_path):
    gz = tmp_path / "itf.txt.gz"
    with gzip.open(gz, "wt", encoding="ascii", newline="\n") as fh:
        fh.write(_line("A", "C", "05.041667", "F51") + "\n")
    out, stats = extract_lines(["B"], src=gz)
    assert out == {"B": []}
    assert stats["designations_found"] == 0
