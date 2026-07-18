"""Tests for the M1 export layer: CSV, ACP .tgt, Markdown digest. Deterministic."""

from __future__ import annotations

import csv

import pytest

from seti_ellipsoid_broker import export
from seti_ellipsoid_broker.models import RankedTarget


def _targets() -> list[RankedTarget]:
    return [
        RankedTarget(
            source_ref="ZTF26aaaaaab",
            gaia_source_id=4657701054736643840,
            ra_deg=83.86658,
            dec_deg=-60.26961,
            distance_pc=985.8,
            parallax_over_error=25.0,
            ruwe=0.98,
            crossing_epoch_jyear=2027.5,
            crossing_window_yr=1.65,
            density_bin=9,
            score=3.3846,
            crossing_now=True,
            crossing_flag_2yr=True,
            survey="ZTF",
            notes="synthetic",
        ),
        RankedTarget(
            source_ref="ZTF26aaaaaad",
            gaia_source_id=4657700123456789012,
            ra_deg=83.86658,
            dec_deg=-65.26961,
            distance_pc=4413.6,
            parallax_over_error=40.0,
            ruwe=1.31,
            crossing_epoch_jyear=2025.5,
            crossing_window_yr=1.05,
            density_bin=5,
            score=3.0587,
            crossing_now=False,
            crossing_flag_2yr=False,
            survey="ZTF",
            notes="synthetic",
        ),
    ]


DATESTAMP = "20260615"


# --- CSV ----------------------------------------------------------------------------

def test_write_csv_roundtrips_and_is_well_formed(tmp_path):
    path = export.write_csv(_targets(), tmp_path, DATESTAMP)
    assert path.name == f"ellipsoid_targets_{DATESTAMP}.csv"
    assert path.exists()
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert list(rows[0].keys()) == list(export.CSV_COLUMNS)
    assert rows[0]["source_ref"] == "ZTF26aaaaaab"
    assert rows[0]["rank"] == "1"
    assert rows[1]["rank"] == "2"
    # Gaia id round-trips exactly (no float mangling of the 19-digit int).
    assert rows[0]["gaia_source_id"] == "4657701054736643840"
    assert float(rows[0]["crossing_epoch_jyear"]) == pytest.approx(2027.5)
    # crossing_now column present and reflects the target flags.
    assert "crossing_now" in rows[0]
    assert rows[0]["crossing_now"] == "True"
    assert rows[1]["crossing_now"] == "False"
    assert rows[0]["crossing_flag_2yr"] == "True"


def test_write_csv_is_deterministic(tmp_path):
    p1 = export.write_csv(_targets(), tmp_path / "a", DATESTAMP)
    p2 = export.write_csv(_targets(), tmp_path / "b", DATESTAMP)
    assert p1.read_bytes() == p2.read_bytes()


def test_write_csv_empty(tmp_path):
    path = export.write_csv([], tmp_path, DATESTAMP)
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == []


# --- ACP .tgt -----------------------------------------------------------------------

def test_write_acp_tgt_format(tmp_path):
    path = export.write_acp_tgt(_targets(), tmp_path, DATESTAMP)
    assert path.name == f"ellipsoid_targets_{DATESTAMP}.tgt"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Header comments begin with ';'.
    assert lines[0].startswith("; SETI Ellipsoid")
    # Two target (non-comment) lines, each Name<TAB>RA<TAB>Dec.
    target_lines = [ln for ln in lines if ln and not ln.startswith(";")]
    assert len(target_lines) == 2
    name, ra, dec = target_lines[0].split("\t")
    assert name == "ZTF26aaaaaab"
    # RA in hours: 83.86658 deg = 5h 35m 27.98s -> starts "05".
    assert ra.startswith("05 35")
    # Dec is signed.
    assert dec.startswith("-60")
    # The on-shell-now star is annotated in its comment line.
    assert "crossing_now=True" in text
    assert "ON-SHELL-NOW" in text


def test_write_acp_tgt_deterministic(tmp_path):
    p1 = export.write_acp_tgt(_targets(), tmp_path / "a", DATESTAMP)
    p2 = export.write_acp_tgt(_targets(), tmp_path / "b", DATESTAMP)
    assert p1.read_bytes() == p2.read_bytes()


# --- Markdown digest ----------------------------------------------------------------

def test_write_markdown_digest(tmp_path):
    path = export.write_markdown_digest(_targets(), tmp_path, DATESTAMP)
    assert path.name == f"ellipsoid_digest_{DATESTAMP}.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith(f"# SETI Ellipsoid crossing candidates - {DATESTAMP}")
    assert "| # |" in text  # has the table header
    assert "ZTF26aaaaaab" in text
    assert "ZTF26aaaaaad" in text
    # Mentions the quality cuts so the digest is self-documenting.
    assert "RUWE" in text
    # The 'now?' column header is present.
    assert "now?" in text


def test_write_markdown_digest_empty(tmp_path):
    path = export.write_markdown_digest([], tmp_path, DATESTAMP)
    text = path.read_text(encoding="utf-8")
    assert "No surviving candidates" in text


def test_write_markdown_deterministic(tmp_path):
    p1 = export.write_markdown_digest(_targets(), tmp_path / "a", DATESTAMP)
    p2 = export.write_markdown_digest(_targets(), tmp_path / "b", DATESTAMP)
    assert p1.read_bytes() == p2.read_bytes()


# --- write_all ----------------------------------------------------------------------

def test_write_all_produces_three_artifacts(tmp_path):
    arts = export.write_all(_targets(), tmp_path, DATESTAMP)
    assert set(arts) == {"csv", "tgt", "md"}
    assert all(p.exists() for p in arts.values())
