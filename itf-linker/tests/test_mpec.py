"""Pin MPEC extraction against the three real July-2026 identification circulars."""

from __future__ import annotations

from collections import Counter

import pytest

from itf_linker.verify.killcheck import pack_designation
from itf_linker.verify.mpec import (
    acceptance_summary,
    parse_mpec,
    residual_blocks,
    residual_tracklets,
)

pytestmark = pytest.mark.slow  # needs the cached MPEC HTML


EXPECTED = {
    "K26O40": ("2026-O40", "2017 SC33 = 2026 NY1", "A. Lowe", 25, 8),
    "K26O57": ("2026-O57", "2009 AC16", "P. VanWylen", 49, 16),
    "K26O86": ("2026-O86", "2011 YD40 = 2026 OO3", "R. Matson, F. Manca, B. Engebreth", 51, 13),
}


@pytest.mark.parametrize("packed", sorted(EXPECTED))
def test_mpec_identity_and_inventory(mpec_dir, packed):
    mpec_id, headline, credit, n_obs, n_trk = EXPECTED[packed]
    m = parse_mpec(mpec_dir / f"{packed}.html", packed)
    assert m.mpec_id == mpec_id
    assert m.headline == headline
    assert m.identified_by == credit
    assert m.n_constituent == n_obs
    assert len(residual_tracklets(m)) == n_trk


def test_first_last_minitable_is_not_double_counted(mpec_dir):
    """2026-O57 prints a 2-row first/last residual table on top of the main one.

    Counting both yields 51 constituent observations instead of 49, and inflates the
    2026-07-20 F51 tracklet from 4 observations to 5.
    """
    text = parse_mpec(mpec_dir / "K26O57.html", "K26O57").text
    assert "First and last observations above in comparison with prediction" in text
    assert len(residual_blocks(text)) == 1  # the mini-table's block is excluded


def test_residual_table_and_eighty_column_block_agree(mpec_dir):
    """2026-O57 is the cross-check: two independent extraction paths, same answer.

    The residual table and the 'Additional Observations' 80-column block describe the
    same three 2026 tracklets. If the parser or the grouping were wrong, these would
    disagree.
    """
    m = parse_mpec(mpec_dir / "K26O57.html", "K26O57")
    assert len(m.observations) == 9

    from_80col = Counter((o.obscode, int(o.day)) for o in m.observations)
    from_resid = {
        (t["obscode"], int(t["obs_date"][-2:])): t["n_obs"]
        for t in residual_tracklets(m)
        if t["obs_date"].startswith("2026")
    }
    assert dict(from_80col) == from_resid == {("F51", 20): 4, ("T14", 21): 3, ("M21", 22): 2}


def test_eighty_column_block_parses_with_the_itf_parser(mpec_dir):
    """Same parser, both sides of the comparison -- that is the point of the check."""
    m = parse_mpec(mpec_dir / "K26O57.html", "K26O57")
    obs = m.observations
    assert {o.desig for o in obs} == {"K09A16C"}
    assert sum(o.discovery for o in obs) == 1
    assert obs[0].obscode == "F51"
    assert obs[0].mjd == pytest.approx(61241.586075, abs=1e-6)
    assert all(0 <= o.ra_deg < 360 and -90 <= o.dec_deg <= 90 for o in obs)


def test_pipeline_regroups_the_mpec_astrometry_into_the_right_tracklets(mpec_dir):
    """The end-to-end M0 claim: feed a published MPEC's own 80-column astrometry through
    the *production* parser and tracklet builder, and recover exactly the tracklets the
    MPEC itself reports. This is what 'our grouping would have handled it' means."""
    import polars as pl

    from itf_linker.index.tracklets import add_night, build_tracklets
    from itf_linker.mpc80 import OUTPUT_COLUMNS, parse_frame

    m = parse_mpec(mpec_dir / "K26O57.html", "K26O57")
    raw = [ln for ln in m.text.splitlines() if len(ln) == 80 and ln[15:19].isdigit()]
    lf = parse_frame(pl.LazyFrame({"raw": raw}, schema={"raw": pl.String})).select(
        OUTPUT_COLUMNS
    )
    lon = {"F51": 203.74409, "T14": 204.53109, "M21": 16.36144}
    trk = build_tracklets(add_night(lf, lon)).collect().sort("mjd_min")

    assert trk.height == 3
    assert trk["obscode"].to_list() == ["F51", "T14", "M21"]
    assert trk["n_obs"].to_list() == [4, 3, 2]
    assert trk["desig"].to_list() == ["K09A16C"] * 3
    # Each is a real short tracklet, and the three nights are consecutive and distinct.
    assert all(s < 1.0 for s in trk["span_hours"].to_list())
    assert trk["night"].to_list() == [61241, 61242, 61243]


@pytest.mark.parametrize(
    "desig,packed",
    [
        ("2009 AC16", "K09A16C"),  # ground truth: this packing appears in MPEC 2026-O57
        ("2017 SC33", "K17S33C"),
        ("2011 YD40", "K11Y40D"),
        ("2026 NY1", "K26N01Y"),
        ("2026 OO3", "K26O03O"),
    ],
)
def test_pack_designation(desig, packed):
    assert pack_designation(desig) == packed


def test_pack_designation_rejects_non_provisional():
    assert pack_designation("(433) Eros") is None
    assert pack_designation("nonsense") is None


@pytest.mark.parametrize("packed", sorted(EXPECTED))
def test_published_links_satisfy_the_published_acceptance_criteria(mpec_dir, packed):
    """Every one of these was accepted by the MPC, so our gate must not reject them."""
    m = parse_mpec(mpec_dir / f"{packed}.html", packed)
    summary = acceptance_summary(residual_tracklets(m))
    assert summary["passes"], summary["reasons"]
    assert summary["nights"] >= 3
    assert summary["arc_days"] >= 3


def test_acceptance_criteria_actually_reject():
    """The gate must have teeth -- pin each published auto-reject rule."""
    two_nights = [
        {"obs_date": "2026-07-01", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61222.0},
        {"obs_date": "2026-07-05", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61226.0},
    ]
    assert not acceptance_summary(two_nights)["passes"]

    short_arc = [
        {"obs_date": "2026-07-01", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61222.0},
        {"obs_date": "2026-07-02", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61223.0},
        {"obs_date": "2026-07-03", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61224.0},
    ]
    assert "arc 2.0 d < 3 d" in acceptance_summary(short_arc)["reasons"]

    three_wide = [
        {"obs_date": "2026-07-01", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61222.0},
        {"obs_date": "2026-07-10", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61231.0},
        {"obs_date": "2026-08-01", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61253.0},
    ]
    assert not acceptance_summary(three_wide)["passes"]

    singleton_ends = [
        {"obs_date": "2026-07-01", "obscode": "F51", "n_obs": 1, "mjd_midnight": 61222.0},
        {"obs_date": "2026-07-10", "obscode": "F51", "n_obs": 3, "mjd_midnight": 61231.0},
        {"obs_date": "2026-07-14", "obscode": "F51", "n_obs": 1, "mjd_midnight": 61235.0},
    ]
    reasons = acceptance_summary(singleton_ends)["reasons"]
    assert any("single-detection" in r for r in reasons)
