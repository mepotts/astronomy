"""The Rubin watcher must treat only canonical daily aggregates as batches."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="module")
def watcher():
    return pytest.importorskip("watch_rubin_batches")


@pytest.fixture()
def bucket_listing():
    path = ROOT / "tests" / "data" / "rubin_bucket_listing.json"
    return json.loads(path.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload, *, text=""):
        self.payload = payload
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_bucket_listing_keeps_only_canonical_daily_aggregates(
        watcher, bucket_listing, monkeypatch):
    monkeypatch.setattr(
        watcher.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(bucket_listing),
    )
    partitions = watcher.list_partitions()
    assert [watcher.canonical_partition_date(name) for name in partitions] == [
        "2026-08-18", "2026-08-19", "2026-08-24"
    ]
    assert all("parquet_generations" not in name for name in partitions)


def test_august_19_and_24_are_the_only_genuine_new_batches(
        watcher, bucket_listing, monkeypatch):
    monkeypatch.setattr(
        watcher.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(bucket_listing),
    )
    partitions = watcher.list_partitions()
    old_name = (
        "production/rubin/mpc/obs_sbn/daily/2026-08-18/parquet/"
        "obs_sbn_X05_2026-08-18.parquet"
    )
    events = watcher.partition_events(
        partitions,
        {old_name: partitions[old_name]},
        min_bytes=1_000_000,
    )
    assert [(event["kind"], event["date"]) for event in events] == [
        ("new_batch_partition", "2026-08-19"),
        ("new_batch_partition", "2026-08-24"),
    ]


@pytest.mark.parametrize("name", [
    "production/rubin/mpc/obs_sbn/daily/2026-08-19/parquet_generations/x.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-08-19/parquet/parts/x.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-08-19/parquet/obs_sbn_X05_2026-08-20.parquet",
])
def test_noncanonical_parquets_can_never_emit_events(watcher, name):
    assert watcher.canonical_partition_date(name) is None
    assert watcher.partition_events(
        {name: {"bytes": 100_000_000, "updated": "2026-08-24T18:00:00Z"}},
        {"some-old-partition": {"bytes": 1}},
        min_bytes=1_000_000,
    ) == []


@pytest.mark.parametrize("payload", [{}, {"items": []}, {"items": "not-a-list"}])
def test_bucket_soft_empty_or_malformed_response_fails_closed(
    watcher, monkeypatch, payload
):
    monkeypatch.setattr(
        watcher.requests, "get", lambda *args, **kwargs: FakeResponse(payload)
    )
    with pytest.raises(watcher.WatcherDataError):
        watcher.list_partitions()


def test_same_size_new_updated_time_is_a_partition_refresh(watcher):
    name = (
        "production/rubin/mpc/obs_sbn/daily/2026-08-24/parquet/"
        "obs_sbn_X05_2026-08-24.parquet"
    )
    old = {name: {"bytes": 2_000_000, "updated": "2026-08-24T12:00:00Z"}}
    current = {name: {"bytes": 2_000_000, "updated": "2026-08-24T13:00:00Z"}}
    events = watcher.partition_events(current, old, min_bytes=1_000_000)
    assert events == [{
        "kind": "partition_refreshed",
        "date": "2026-08-24",
        "name": name,
        "bytes_before": 2_000_000,
        "updated_before": "2026-08-24T12:00:00Z",
        "bytes": 2_000_000,
        "updated": "2026-08-24T13:00:00Z",
    }]


def test_bucket_failure_preserves_the_previous_state(
    watcher, monkeypatch, tmp_path
):
    state = tmp_path / "watcher-state.json"
    original = {
        "partitions": {"existing": {"bytes": 42, "updated": "then"}},
        "newsletters": ["https://example.invalid/old"],
        "updated_utc": "before",
    }
    state.write_text(json.dumps(original), encoding="utf-8")

    def fail_listing():
        raise watcher.WatcherDataError("soft-empty fixture")

    monkeypatch.setattr(watcher, "list_partitions", fail_listing)
    monkeypatch.setattr(
        sys, "argv", ["watch_rubin_batches.py", "--state", str(state), "--skip-newsletter"]
    )
    assert watcher.main() == 1
    assert json.loads(state.read_text(encoding="utf-8")) == original


def test_empty_newsletter_response_preserves_previous_links(
    watcher, monkeypatch, tmp_path
):
    state = tmp_path / "watcher-state.json"
    partition = {
        "production/rubin/mpc/obs_sbn/daily/2026-08-24/parquet/"
        "obs_sbn_X05_2026-08-24.parquet": {
            "bytes": 2_000_000,
            "updated": "2026-08-24T13:00:00Z",
        }
    }
    old_link = "https://buttondown.com/MPC_newsletter/archive/newsletter-august-2026/"
    state.write_text(
        json.dumps({"partitions": partition, "newsletters": [old_link]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(watcher, "list_partitions", lambda: partition)
    monkeypatch.setattr(
        watcher.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({}, text="<html><body></body></html>"),
    )
    monkeypatch.setattr(sys, "argv", ["watch_rubin_batches.py", "--state", str(state)])

    assert watcher.main() == 3
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["newsletters"] == [old_link]
    assert saved["partitions"] == partition


def test_state_replacement_is_atomic(watcher, tmp_path):
    state = tmp_path / "watcher-state.json"
    watcher.write_state_atomic(state, {"partitions": {}, "newsletters": []})
    assert json.loads(state.read_text(encoding="utf-8"))["partitions"] == {}
    assert not list(tmp_path.glob(".watcher-state.json.tmp-*"))
