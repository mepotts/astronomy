"""M10: the pointed-field screen, the shell window, and the ledger-refresh arithmetic.

Everything M10 added is milestone scripts rather than library code, so these tests pin
the three pieces of it that make a *claim* — the screen that decides whether a distant
candidate is survey debris, the lookback floor that defines the 15-25 y shell, and the
small arithmetic the review queue and decay analysis put in front of a human. The
production-scale checks live in the milestone doc; these are the ones a unit test can
actually hold.

The screen's fixtures are built from M9's own numbers: its two pointed-field failures
sat at **Delta t = 0.0 s** with the tracklet ~30" from a published same-station row,
and its one genuine independent epoch had no same-station published row within a day.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


@dataclass
class Obs:
    """The two fields the screen reads, plus astrometry. Mirrors mpc80's parse_line."""

    mjd: float
    obscode: str
    ra_deg: float
    dec_deg: float


# ----------------------------------------------------------------------------------
# The pointed-field screen
# ----------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def screen():
    import m10_pointed

    return m10_pointed


def test_same_instant_same_station_is_a_pointed_field(screen):
    """M9's CT190/VV130 shape: identical exposure instant, ~30 arcsec apart."""
    trk = [Obs(55921.44687, "688", 120.0, 15.0), Obs(55921.45687, "688", 120.001, 15.0)]
    pub = [Obs(55921.44687, "688", 120.0086, 15.0)]  # ~30" east, same instant
    res = screen.pointed_field_flags(trk, pub)
    assert res["flags"] == ["POINTED_FIELD"]
    assert res["screened_out"] is True
    assert res["min_dt_seconds"] == 0.0
    # Both tracklet observations are inside the hour of that one published row.
    assert res["n_same_instant"] == 2
    assert res["n_duplicate"] == 0


def test_no_same_station_row_within_a_day_is_clean(screen):
    """M9's EZ90 shape: a genuine independent epoch. It failed the *fit*, not this."""
    trk = [Obs(52671.2, "645", 200.0, 40.0), Obs(52671.25, "645", 200.001, 40.0)]
    pub = [Obs(52680.0, "645", 200.5, 40.1), Obs(52671.2, "T09", 200.0, 40.0)]
    res = screen.pointed_field_flags(trk, pub)
    assert res["flags"] == []
    assert res["screened_out"] is False
    assert res["min_dt_seconds"] is None


def test_a_different_station_at_the_same_instant_does_not_flag(screen):
    """The confound is a *pointed field*, which is a property of one telescope."""
    trk = [Obs(55921.44687, "688", 120.0, 15.0)]
    pub = [Obs(55921.44687, "W84", 120.0086, 15.0)]
    assert screen.pointed_field_flags(trk, pub)["flags"] == []


def test_duplicate_is_reported_as_duplicate_not_as_a_pointed_field(screen):
    """Same instant AND same position is ALREADY_LINKED. Never conflate the two."""
    trk = [Obs(55921.44687, "688", 120.0, 15.0)]
    pub = [Obs(55921.44688, "688", 120.00003, 15.0)]  # ~0.1", ~0.09 s
    res = screen.pointed_field_flags(trk, pub)
    assert res["n_duplicate"] == 1
    assert "POINTED_FIELD" not in res["flags"]
    assert res["flags"] == ["DUPLICATE"]
    assert res["screened_out"] is False


def test_same_night_but_a_different_exposure_is_the_weaker_flag(screen):
    trk = [Obs(57335.2, "G96", 10.0, 5.0)]
    pub = [Obs(57335.2 + 5772.0 / 86400.0, "G96", 10.02, 5.0)]  # 1.6 h later
    res = screen.pointed_field_flags(trk, pub)
    assert res["flags"] == ["SAME_NIGHT_FIELD"]
    assert res["screened_out"] is False  # named for the reviewer, not screened out
    assert res["min_dt_seconds"] == pytest.approx(5772.0, abs=1.0)


def test_the_one_hour_boundary_is_where_it_is_declared(screen):
    """Pre-registered at +/- 1 h; a test that would pass at any threshold pins nothing."""
    inside = [Obs(57335.2 + 3500.0 / 86400.0, "G96", 10.02, 5.0)]
    outside = [Obs(57335.2 + 3700.0 / 86400.0, "G96", 10.02, 5.0)]
    trk = [Obs(57335.2, "G96", 10.0, 5.0)]
    assert screen.pointed_field_flags(trk, inside)["flags"] == ["POINTED_FIELD"]
    assert screen.pointed_field_flags(trk, outside)["flags"] == ["SAME_NIGHT_FIELD"]


# ----------------------------------------------------------------------------------
# The 15-25 y shell window
# ----------------------------------------------------------------------------------

def test_min_lookback_defaults_to_zero_so_m8_behaviour_is_unchanged():
    """M8's and M9's numbers must stay reproducible after the shell knob was added."""
    import m8_attribution as m8a

    assert m8a.MIN_LOOKBACK_DAYS == 0.0
    assert m8a.MAX_LOOKBACK_DAYS == pytest.approx(15.0 * 365.25)
    assert m8a.CALIBRATION_KEY == "perturbed_envelope_arcsec"
    assert m8a.TAG_FIT == "m8a" and m8a.TAG_BASE == "m8b"
    # Seven characters is the trkSub field width; an 8-char tag silently truncates and
    # two tags can collide into one object (HANDOFF section 2).
    assert len(f"{m8a.TAG_FIT}0000") == 7
    assert len(f"{m8a.TAG_BASE}0000") == 7


def test_shell_gate_is_the_frozen_formula_on_the_measured_envelope(tmp_path):
    """The M10 gate must be *derived*: same floor, same safety factor, same runoff."""
    import m8_attribution as m8a
    import numpy as np

    cal = tmp_path / "cal.json"
    cal.write_text(json.dumps({
        "env25": {"15.00y": 55.17, "18.00y": 149.43, "20.00y": 95.15, "25.00y": 139.59}
    }), encoding="utf-8")
    old = (m8a.CALIBRATION, m8a.CALIBRATION_KEY)
    try:
        m8a.CALIBRATION, m8a.CALIBRATION_KEY = cal, "env25"
        env = m8a.envelope_fn()
        # Monotone max-accumulate: 18 y's 149.43 is the running max at 20 and 25 y.
        assert env(np.array([25.0 * 365.25]))[0] == pytest.approx(149.43)
        r = m8a.gate_radius_arcsec(
            np.array([25.0 * 365.25]), np.array([2]), env
        )[0]
        expected = 120.0 + 1.5 * 149.43 + 0.01 * 10 ** (0.868 * 2) * 2.5
        assert r == pytest.approx(expected, rel=1e-9)
        assert 340.0 < r < 350.0  # the value M10-RESULTS section 0.2 states
    finally:
        m8a.CALIBRATION, m8a.CALIBRATION_KEY = old


def test_main_belt_and_tno_envelopes_are_never_mixed():
    """28 y is a TNO number; the main-belt envelope breaks there at 304 arcsec.

    The envelopes are copied into ``tests/data`` rather than read from the M9
    calibration doc under ``data/``: that tree is gitignored, so reading it made this
    the one test in the suite that could not run on a fresh clone.
    """
    doc = json.loads(
        (Path(__file__).parent / "data" / "m9-calibration-envelopes.json").read_text(
            encoding="utf-8"
        )
    )
    mb = doc["perturbed_envelope_arcsec_mainbelt_25y"]
    tno = doc["perturbed_envelope_arcsec_tno_25y"]
    assert float(mb["25.00y"]) < 150.0 and float(mb["28.00y"]) > 300.0
    assert float(tno["28.00y"]) < 0.5
    import m10_shell

    assert m10_shell.SHELL_MAX_YEARS == 25.0  # not 28: that bound is not ours to use
    assert m10_shell.SHELL_MIN_YEARS == 15.0  # the interior is already in the ledger


# ----------------------------------------------------------------------------------
# Ledger-refresh and review-queue arithmetic
# ----------------------------------------------------------------------------------

def test_consumed_outcomes_reads_both_report_shapes(tmp_path):
    """M9 wrote rows[].outcome; M10 writes consumed_rows[].agreement. One meaning."""
    import m9_adjudicate

    m9 = tmp_path / "m9.json"
    m9.write_text(json.dumps({"rows": [
        {"orbit_desig": "2025 AA", "link_key": "lk1",
         "outcome": "CONSUMED_INTO_SAME_OBJECT"},
    ]}), encoding="utf-8")
    m10 = tmp_path / "m10.json"
    m10.write_text(json.dumps({"consumed_rows": [
        {"orbit_desig": "2025 BB", "link_key": "lk2", "agreement": "CONSUMED_AND_AGREED"},
        {"orbit_desig": "2025 CC", "link_key": "lk3",
         "agreement": "CONSUMED_AND_DISAGREED"},
    ]}), encoding="utf-8")
    assert m9_adjudicate.consumed_outcomes(m9) == {
        ("2025 AA", "lk1"): "CONSUMED_INTO_SAME_OBJECT"
    }
    got = m9_adjudicate.consumed_outcomes(m10)
    assert got[("2025 BB", "lk2")] == "CONSUMED_INTO_SAME_OBJECT"
    # A disagreement must NOT read as "reality adjudicated in our favour".
    assert got[("2025 CC", "lk3")] == "CONSUMED_ELSEWHERE"


def test_arc_extension_distinguishes_extending_from_densifying():
    import m10_review_queue as rq

    # A precovery 100 d before the published arc extends it by 100 d.
    assert rq.arc_extension(1000.0, 2000.0, [900.0, 900.1]) == pytest.approx(100.0)
    # A tracklet inside the arc adds nothing to its span, and must not read as if it did.
    assert rq.arc_extension(1000.0, 2000.0, [1500.0, 1500.1]) == 0.0
    # Extension after the last published epoch counts too.
    assert rq.arc_extension(1000.0, 2000.0, [2050.0]) == pytest.approx(50.0)
    assert rq.arc_extension(None, None, [900.0]) is None


def test_wilson_interval_behaves_at_zero_successes():
    """M9's PASS rows are 0-of-272 consumed; a normal interval would report [0, 0]."""
    import m10_decay

    lo, hi = m10_decay.wilson(0, 272)
    assert lo == 0.0
    assert 0.0 < hi < 0.02  # a real upper bound, not a claim of certainty
    lo, hi = m10_decay.wilson(21, 482)
    assert lo < 21 / 482 < hi


def test_survival_rate_reproduces_m9_headline_number():
    """M9 measured 30 of 900 in ~2 days and called it 3.3%. The general form must agree."""
    import m10_decay

    r = m10_decay.survival_rate(30, 900, 2.0415)
    assert r["fraction"] == pytest.approx(30 / 900, abs=1e-5)
    assert 3.0 < r["percent_per_2_days"] < 3.5
    assert r["half_life_days"] == pytest.approx(41.7, abs=1.0)


def test_fisher_exact_finds_the_head_vs_tail_difference():
    import m10_decay

    # 21/482 consumed vs 0/272 consumed: the M8 head decays, the M9 tail does not.
    p = m10_decay.fisher_exact_greater(21, 461, 0, 272)
    assert p < 0.001
    # A table with no difference must not report one.
    assert m10_decay.fisher_exact_greater(10, 90, 10, 90) > 0.4


# ----------------------------------------------------------------------------------
# The self-designation screen
# ----------------------------------------------------------------------------------

def test_packed_provisional_designation(screen):
    """Pinned against the four all-sky head rows that exposed the artefact."""
    assert screen.packed_provisional("2018 KH3") == "K18K03H"
    assert screen.packed_provisional("2024 PP8") == "K24P08P"
    assert screen.packed_provisional("2021 GQ57") == "K21G57Q"
    assert screen.packed_provisional("2020 KR11") == "K20K11R"
    assert screen.packed_provisional("2013 HS150") == "K13HF0S"  # cycle >= 100
    assert screen.packed_provisional("1998 SM165") == "J98SG5M"
    assert screen.packed_provisional("(20000) Varuna") is None  # not provisional


def test_self_designation_catches_the_century_byte_swap(screen):
    """A trkSub that IS the object's packed designation is bookkeeping, not a link."""
    r = screen.self_designation("2018 KH3", "/18K03H")
    assert r["self_designation"] is True
    assert r["packed"] == "K18K03H"


def test_self_designation_does_not_fire_on_a_real_tracklet(screen):
    """W84's AIXe1M5 near 2013 HS150 is a genuine candidate; the screen must leave it."""
    assert screen.self_designation("2013 HS150", "AIXe1M5")["self_designation"] is False
    assert screen.self_designation("2025 PD152", "P11zG98")["self_designation"] is False
    # A 7-char trkSub that merely shares a couple of characters must not trip it.
    assert screen.self_designation("2018 KH3", "K18K999")["self_designation"] is False


def test_no_ledger_row_is_a_self_designation(screen):
    """The measurement the review queue depends on: 0 of the M8/M9/M10-shell rows."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    n = hits = 0
    for name in ("m8-ledger.json", "m9-ledger.json", "m10-shell-ledger.json"):
        p = root / name
        if not p.exists():
            continue
        for v in json.loads(p.read_text(encoding="utf-8"))["verdicts"]:
            n += 1
            hits += int(
                screen.self_designation(v["orbit_desig"], v["trksub"])["self_designation"]
            )
    if n == 0:
        import pytest as _pytest

        _pytest.skip("no ledgers present in this working copy")
    assert hits == 0, f"{hits} of {n} ledger rows are self-designation artefacts"
