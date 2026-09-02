"""Regression tests for the public-safe M13 queue/freshness watcher."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def watch():
    return pytest.importorskip("m13_submission_watch")


def test_row_state_uses_a_fingerprint_not_the_candidate_id(watch):
    row = {"object": "2025 PC147", "link_keys": "lk-first; lk-second"}
    exact = watch.row_id(row)
    digest = watch.fingerprint(exact)
    assert exact == "2025 PC147|lk-first; lk-second"
    assert len(digest) == 64
    assert "2025 PC147" not in digest
    assert watch._previous_ready({"ready": [exact]}) == {digest}


def test_snapshot_and_candidate_signals_are_independent(watch):
    assert watch.snapshot_status(None, "20260901T122612Z") == "baseline"
    assert watch.snapshot_status(
        "20260901T122612Z", "20260901T122612Z"
    ) == "repeated"
    assert watch.snapshot_status(
        "20260901T122612Z", "20260902T122612Z"
    ) == "advanced"
    assert watch.snapshot_status(
        "20260902T122612Z", "20260901T122612Z"
    ) == "regressed"


def test_every_snapshot_observation_is_persisted(watch):
    first = watch.update_snapshot_history({}, "20260901T122612Z", "2026-09-01T15:00:00Z")
    previous = {"freshness": {"snapshots_observed": first}}
    repeated = watch.update_snapshot_history(
        previous, "20260901T122612Z", "2026-09-02T15:00:00Z"
    )
    assert repeated == [{
        "snapshot": "20260901T122612Z",
        "first_observed_utc": "2026-09-01T15:00:00Z",
        "last_observed_utc": "2026-09-02T15:00:00Z",
        "runs_seen": 2,
    }]

    advanced = watch.update_snapshot_history(
        {"freshness": {"snapshots_observed": repeated}},
        "20260902T122612Z",
        "2026-09-02T15:05:00Z",
    )
    assert [item["snapshot"] for item in advanced] == [
        "20260901T122612Z", "20260902T122612Z"
    ]


def test_state_write_is_complete_json(watch, tmp_path):
    state = tmp_path / "watch-state.json"
    watch.write_json_atomic(state, {"version": 2, "candidate": {"n_ready": 4}})
    assert json.loads(state.read_text(encoding="utf-8"))["candidate"]["n_ready"] == 4
    assert not (tmp_path / ".watch-state.json.tmp").exists()


def test_snapshot_age_parsing_is_strict(watch):
    now = dt.datetime(2026, 9, 2, 15, tzinfo=dt.UTC)
    assert watch.snapshot_age_hours("20260901T120000Z", now) == 27.0
    assert watch.snapshot_age_hours("not-a-snapshot", now) is None
    assert watch.snapshot_age_hours("20260902T150001Z", now) is None


@pytest.mark.parametrize(
    ("status", "age_hours", "expected"),
    [
        ("baseline", 2.0, False),
        ("baseline", 25.0, True),
        ("repeated", 2.0, False),
        ("repeated", 25.0, True),
        ("advanced", 30.0, True),
        ("regressed", 1.0, True),
        ("advanced", None, True),
    ],
)
def test_freshness_alert_depends_on_age_not_candidate_change(
        watch, status, age_hours, expected):
    assert watch.should_alert_freshness(status, age_hours) is expected


def test_public_report_contains_counts_but_no_candidate_details(watch):
    report = watch.render(
        snapshot="20260902T122612Z",
        status="advanced",
        age_hours=2.6,
        ready=20,
        held=648,
        new_ready=1,
        no_longer_ready=7,
        queue_changed=False,
        first_run=False,
    )
    assert "ready: **20**" in report
    assert "1 newly ready; 7 no longer ready" in report
    for secret in ("2025 PC147", "lk-first", '"links"', '"trksubs"'):
        assert secret not in report


def test_candidate_parse_failure_is_fail_closed_and_public_safe(watch, tmp_path,
                                                                monkeypatch):
    queue = tmp_path / "queue.csv"
    queue.write_text(
        "tier,object,link_keys\nA,2025 SECRET,lk-private\n", encoding="utf-8"
    )

    class EmptyNights:
        def iter_rows(self, named=False):
            return []

    monkeypatch.setattr(watch, "load_itf_nights", lambda path: EmptyNights())
    monkeypatch.setattr(
        watch,
        "check_row",
        lambda *args: (_ for _ in ()).throw(ValueError("2025 SECRET lk-private")),
    )
    with pytest.raises(RuntimeError) as error:
        watch.evaluate(queue, tmp_path / "itf.parquet", {"A"})
    assert str(error.value) == (
        "candidate evaluation failed; rerun the watcher locally for private details"
    )


def test_workflow_cannot_publish_a_payload_or_push_runtime_state():
    workflow = (REPO / ".github" / "workflows" /
                "itf-submission-watch.yml").read_text(encoding="utf-8")
    for forbidden in (
        "actions/upload-artifact",
        "--out-payload",
        "submission-tierA.json",
        "git push",
        "contents: write",
        "issues: write",
        "gh issue",
        "gh label",
    ):
        assert forbidden not in workflow
    assert "actions/cache/save" in workflow
    assert "candidate_changed" in workflow
    assert "freshness_alert" in workflow
    assert "if: always() && steps.watch.outcome == 'success'" in workflow
    assert "::notice title=ITF candidate counts changed" in workflow
    assert "::warning title=ITF snapshot stale" in workflow
    assert "Fail stale snapshot health check" in workflow
    assert "::error::no published key set" in workflow
    assert 'echo "found=0"' not in workflow
