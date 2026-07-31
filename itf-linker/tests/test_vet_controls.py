"""The controls are what license every other number in M2, so they get their own tests.

A control that cannot fail is not a control. These check that :func:`judge` actually
rejects the ways a vetting layer goes wrong -- right object but weak verdict, confident
verdict but wrong object, and the specific mis-resolution the live control caught.
"""

from __future__ import annotations

import json

import pytest

from itf_linker.vet.controls import (
    ITF_COMET_CONTROL,
    NUMBERED_CONTROLS,
    SITE_CONTROLS,
    _same_object,
    comet_control,
    judge,
    run_controls,
)
from itf_linker.vet.types import VetVerdict


def verdict(category: str, identified: str | None) -> VetVerdict:
    return VetVerdict(desig="CTRL", category=category, identified_as=identified)


def test_judge_passes_only_the_right_object_with_a_confident_verdict():
    assert judge(verdict("known", "73P-C"), "73P-C") == []


def test_judge_rejects_the_right_object_with_a_weak_verdict():
    failures = judge(verdict("ambiguous", "73P-C"), "73P-C")
    assert failures and "expected 'known'" in failures[0]


def test_judge_rejects_a_confident_verdict_about_the_wrong_object():
    """The live failure this guards: 73P-C resolving to minor planet (73) Klytia."""
    failures = judge(verdict("known", "73"), "73P-C")
    assert failures and "expected '73P-C'" in failures[0]


def test_judge_rejects_a_non_match():
    failures = judge(verdict("unmatched", None), "433")
    assert len(failures) == 2  # wrong category and no identification


@pytest.mark.parametrize(
    ("a", "b", "same"),
    [
        ("73P-C", "73P-C", True),
        ("73P/C", "73P-C", True),      # services punctuate comet fragments differently
        ("2018 EC25", "2018EC25", True),
        ("73", "73P-C", False),
        (None, "433", False),
        ("", "433", False),
    ],
)
def test_identity_comparison_is_loose_about_punctuation_only(a, b, same):
    assert _same_object(a, b) is same


def test_the_control_set_covers_the_populations_it_needs_to():
    """Each control exists to exclude a specific silent failure; none is decorative."""
    assert ITF_COMET_CONTROL == ("0073P-C", "73P-C")
    # Dynamical classes: a solver or a catalogue query can be right for one and wrong
    # for another.
    assert {c[1] for c in NUMBERED_CONTROLS} == {"433", "7", "588"}
    # Observatory codes: 100 of M1's 128 candidates are X05 alone, and a query bug
    # specific to a 2025-minted code reads as a field full of discoveries.
    assert "X05" in {c[0] for c in SITE_CONTROLS}
    assert all(start.startswith("2025") for _, start, _, _, _ in SITE_CONTROLS)


def test_a_missing_astrometry_file_fails_the_control_rather_than_the_run(tmp_path):
    from itf_linker.vet import CachedSession
    from itf_linker.vet.pipeline import Resolver

    empty = tmp_path / "astrometry.json"
    empty.write_text(json.dumps({"lines": {}}), encoding="utf-8")
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0, offline=True)
    outcome = comet_control(session, Resolver(session), empty)
    assert outcome.passed is False
    assert "vet-extract" in outcome.failures[0]


def test_run_controls_reports_all_passed_as_a_gate(tmp_path):
    """``all_passed`` is what the rest of M2 hangs off; it must be false when one fails."""
    from itf_linker.vet import CachedSession

    empty = tmp_path / "astrometry.json"
    empty.write_text(json.dumps({"lines": {}}), encoding="utf-8")
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0, offline=True)
    report = run_controls(session, astrometry_path=empty, include_numbered=False)
    assert report["summary"]["all_passed"] is False
    assert report["summary"]["n_passed"] == 0
