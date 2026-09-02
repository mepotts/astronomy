"""M13: the submission payload builder, and the four ways it must refuse.

This is the only code in the repository whose output is meant to leave the building, so
its tests are about refusal rather than construction. Building the JSON is trivial;
knowing which rows must never be in it is the whole job.

Three of these were found by running the thing and reading the output rather than by
reasoning about it, which is why they are pinned here:

* **``nearest other N"`` is the CLEAN branch of the skybot column**, not a warning.
  ``m10_review_queue.skybot_cell`` emits it only when nothing else was found. A
  ``startswith("clean")`` check refused 411 of the queue's 679 good rows on phrasing.
* **"fo used the tracklet" has two spellings** -- ``all-members-used=Y`` on a combined
  fit, ``tracklet-used=4/4`` on a single one. Requiring the first refused 645 of 679.
  M11 §4.2 measured this gate as carrying the chain's *entire* discriminating power, so
  it has to be read correctly in both dialects.
* **A tracklet absent from the current ITF must not be submitted without review.** M12
  measured the ITF draining at 4.4 departures per arrival; the queue goes stale underneath
  itself. Disappearance alone does not prove identification or establish a destination.

And one that is structural: the module must have no way to send anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def sub():
    return pytest.importorskip("m13_submit_payload")


# ----------------------------------------------------------------------------------
# The module cannot send. This is a property, not a policy.
# ----------------------------------------------------------------------------------

def test_the_builder_has_no_way_to_send_anything():
    """Guardrail 1 is 'automated end-to-end submission is out of scope permanently'.

    A comment saying so is worth less than an import list that makes it impossible, so
    this asserts on the source: no HTTP client, no socket, no subprocess.
    """
    src = (ROOT / "scripts" / "m13_submit_payload.py").read_text(encoding="utf-8")
    for banned in ("import requests", "import urllib", "import http",
                   "import socket", "import subprocess", "urlopen", "requests.post"):
        assert banned not in src, f"the payload builder must not be able to send: {banned}"


# ----------------------------------------------------------------------------------
# skybot: the phrasing trap
# ----------------------------------------------------------------------------------

@pytest.mark.parametrize("cell", [
    "clean",
    'nearest other 228.72"',                       # the reassuring branch, NOT a warning
    'clean | nearest other 228.72"',
    'nearest other 239.902" | clean',              # same thing, other order
    "object itself present",                       # the target is meant to be in its cone
    'lost-object claimant: 2014 HZ323 (err 10606250.0")',   # ruled on by `ambiguity`
])
def test_these_skybot_cells_are_not_refusals(sub, cell):
    assert sub.skybot_reasons(cell) == []


@pytest.mark.parametrize("cell", [
    'CONFLICT: 2011 AB at 3.2"',
    "UNAVAILABLE (timeout)",
    "not run",
    "M7 manual cone search (M7-RESULTS section 8)",   # unrecognised => quarantine
])
def test_these_skybot_cells_refuse(sub, cell):
    assert sub.skybot_reasons(cell), f"{cell!r} must refuse"


def test_a_conflict_refuses_even_beside_a_clean_segment(sub):
    """One bad tracklet poisons the row; the clean sibling does not redeem it."""
    assert sub.skybot_reasons('clean | CONFLICT: 2011 AB at 3.2"')


# ----------------------------------------------------------------------------------
# The gate that does all the work, in both dialects
# ----------------------------------------------------------------------------------

def test_a_combined_fit_row_passes_on_all_members_used(sub):
    assert sub.gate_reasons("strict=Y published=Y all-members-used=Y distinct-nights=2") == []


def test_a_single_tracklet_row_passes_on_tracklet_used(sub):
    """645 of 679 rows speak this dialect and only this one."""
    assert sub.gate_reasons('strict=Y published=Y tracklet-used=4/4 sep=7.6"/gate=582.5"') == []


def test_a_partially_used_tracklet_refuses(sub):
    """3 of 4 observations used is exactly what the gate exists to catch."""
    reasons = sub.gate_reasons('strict=Y published=Y tracklet-used=3/4 sep=7.6"/gate=582.5"')
    assert reasons and "3 of 4" in reasons[0]


def test_strict_no_refuses(sub):
    assert any("strict" in r for r in
               sub.gate_reasons('strict=N published=Y tracklet-used=3/3 sep=7.2"'))


def test_a_row_with_no_used_gate_at_all_refuses(sub):
    """M7's manual row carries neither spelling; absence must not read as pass."""
    assert sub.gate_reasons('strict=Y published=Y sep=197.0"')


# ----------------------------------------------------------------------------------
# Tracklet cell parsing
# ----------------------------------------------------------------------------------

def test_parses_the_queues_tracklet_cell(sub):
    got = sub.parse_tracklets("Arms063@W85/n60879; SUBFE89@G96/n55855")
    assert got == [
        {"trksub": "Arms063", "obscode": "W85", "night": 60879},
        {"trksub": "SUBFE89", "obscode": "G96", "night": 55855},
    ]


def test_an_unparseable_tracklet_cell_raises_rather_than_guessing(sub):
    with pytest.raises(ValueError):
        sub.parse_tracklets("Arms063 W85 60879")


# ----------------------------------------------------------------------------------
# check_row: the two refusals that protect the batch
# ----------------------------------------------------------------------------------

def _row(**over):
    row = {
        "rank": "1", "tier": "A", "object": "2025 PC147",
        # Two tracklets, as every row that can actually be submitted is: the MPC's
        # 0.75 d rule rejects a lone short tracklet on a non-NEO, and it rejects 640 of
        # this queue's 679 rows on exactly that.
        "tracklets": "Arms063@W85/n60879; SUBFE89@G96/n55855",
        "gates": "strict=Y published=Y all-members-used=Y distinct-nights=2",
        "skybot": 'clean | nearest other 228.72"',
        "ambiguity": "none", "itf_status": "STILL_LIVE (all members)",
        "pointed_screen": "clean",
    }
    row.update(over)
    return row


def _nights(n_obs=4):
    # mjd only -- the same three columns the published slim key set carries, which is
    # what lets this run on a GitHub runner where the MPC is unreachable.
    return {
        ("Arms063", "W85", 60879): {"n_obs": n_obs, "mjd": 60879.41, "mjd_hi": 60879.45},
        ("SUBFE89", "G96", 55855): {"n_obs": n_obs, "mjd": 55855.30, "mjd_hi": 55855.34},
    }


def test_a_clean_row_yields_the_triple_with_a_real_observation_date(sub):
    triples, reasons = sub.check_row(_row(), _nights())
    assert reasons == []
    # dates come from each tracklet's own MJD -- never from the night integer
    assert triples == [["Arms063", "20250723", "W85"],
                       ["SUBFE89", "20111021", "G96"]]


def test_a_tracklet_no_longer_in_the_current_itf_is_refused(sub):
    """Absence is enough to hold the row, but not to claim an identification."""
    triples, reasons = sub.check_row(_row(), {})
    assert triples == []
    assert sum("no longer in the current ITF" in r for r in reasons) == 2
    assert all("consumed" not in r.lower() for r in reasons)
    assert all("identified" not in r.lower() for r in reasons)


def test_a_single_observation_night_is_refused_because_it_kills_the_whole_batch(sub):
    """Guardrail 5: below two observations the MPC auto-rejects the ENTIRE submission."""
    triples, reasons = sub.check_row(_row(), _nights(n_obs=1))
    assert triples == []
    assert any("WHOLE batch" in r for r in reasons)
    assert sub.MIN_OBS_PER_NIGHT == 2


def test_an_adjudicated_ambiguity_passes_and_an_open_one_does_not(sub):
    """RESOLVED_TO_CANDIDATE went our way; STILL_AMBIGUOUS means a rival orbit fits too."""
    _, ok = sub.check_row(_row(ambiguity="RESOLVED_TO_CANDIDATE (2/2 members)"), _nights())
    assert ok == []
    _, bad = sub.check_row(
        _row(ambiguity="STILL_AMBIGUOUS (1 claimant(s) fitted, claimant_fit_also_passes)"),
        _nights())
    assert any("unresolved ambiguity" in r for r in bad)


def test_a_consumed_queue_row_is_refused(sub):
    _, reasons = sub.check_row(_row(itf_status="CONSUMED"), _nights())
    assert any("CONSUMED" in r for r in reasons)


def test_a_flagged_pointed_field_is_refused(sub):
    _, reasons = sub.check_row(
        _row(pointed_screen="SAME_NIGHT_FIELD (nearest same-station published row 23.7 h away)"),
        _nights())
    assert any("pointed-field" in r for r in reasons)


def test_an_unpackable_designation_is_refused_rather_than_sent_raw(sub):
    """Designations must go in PACKED form; a name we cannot pack must not be guessed at."""
    _, reasons = sub.check_row(_row(object="Ceres"), _nights())
    assert any("will not pack" in r for r in reasons)


# ----------------------------------------------------------------------------------
# The date, derived from MJD so the slim key set is enough
# ----------------------------------------------------------------------------------

def test_obs_date_is_the_calendar_day_of_the_mjd(sub):
    import datetime as dt
    assert sub.obs_date(60879.0) == "20250723"
    assert sub.obs_date(60879.99) == "20250723"   # any time that day is the same day
    assert sub.obs_date(60879 + 1.0) == "20250724"
    assert sub.obs_date(sub.MJD_UNIX_EPOCH) == "19700101"
    # agrees with a plain date walk over a long baseline
    for off in (0, 1, 365, 4000, 20000):
        want = (dt.date(1970, 1, 1) + dt.timedelta(days=off)).strftime("%Y%m%d")
        assert sub.obs_date(sub.MJD_UNIX_EPOCH + off + 0.5) == want


# ----------------------------------------------------------------------------------
# The MPC's OWN acceptance criteria -- the gate that was missing entirely
# ----------------------------------------------------------------------------------
#
# Built only after reading the current MPC Public Documentation Hub acceptance criteria,
# which had been linked but never opened. Measured against the real queue it rejects 640 rows --
# the whole B and C tiers. Submitting them would have been a batch the MPC auto-rejects
# almost in its entirety, which is precisely the reputational failure the guardrails name.

def test_a_lone_short_tracklet_on_a_non_neo_is_refused(sub):
    """The one criterion that applies to ITF-to-DES links, and it is decisive."""
    reasons = sub.mpc_criteria_reasons(n_tracklets=1, arc_days=1.0 / 24, is_neo=False)
    assert reasons and "auto-rejected" in reasons[0]


def test_neos_are_exempt_however_short_the_arc(sub):
    """'this criteria does not apply to NEOs', verbatim from the page."""
    assert sub.mpc_criteria_reasons(n_tracklets=1, arc_days=1.0 / 24, is_neo=True) == []


def test_multiple_tracklets_are_outside_the_rule(sub):
    """The rule is scoped to a *single* tracklet; Tier A's combined fits are not that."""
    assert sub.mpc_criteria_reasons(n_tracklets=2, arc_days=0.01, is_neo=False) == []


def test_a_single_tracklet_long_enough_passes(sub):
    assert sub.mpc_criteria_reasons(n_tracklets=1, arc_days=0.9, is_neo=False) == []
    assert sub.MIN_ARC_DAYS_NON_NEO == 0.75


def test_an_unmeasurable_arc_refuses_rather_than_assuming(sub):
    """Not being able to clear a rule is not the same as clearing it."""
    assert sub.mpc_criteria_reasons(n_tracklets=1, arc_days=None, is_neo=False)


def test_absence_from_the_neo_sidecar_means_non_neo_not_exempt(sub):
    """The restrictive branch is the safe default; absence must never grant an exemption."""
    row = _row(tracklets="Arms063@W85/n60879", object="2025 PC147")
    nights = {("Arms063", "W85", 60879):
              {"n_obs": 4, "mjd": 60879.40, "mjd_hi": 60879.44}}   # ~1 h, single tracklet
    _, reasons = sub.check_row(row, nights, {})          # empty sidecar
    assert any("auto-rejected" in r for r in reasons)
    # ...and present-and-NEO does grant it
    _, ok = sub.check_row(row, nights, {"2025 PC147": {"is_neo": True}})
    assert ok == []
