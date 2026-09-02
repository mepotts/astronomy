from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import requests

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import m1_fetch_fink as fink  # noqa: E402


class StubResponse:
    def __init__(self, status_code: int = 200, payload=None, json_error=None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class StubSession:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if not self.replies:
            raise AssertionError("unexpected HTTP call")
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply


def record(oid: str, jd: float = 2460000.5) -> dict:
    return {
        "i:objectId": oid,
        "i:jd": jd,
        "i:candid": 123456789,
        "i:magpsf": 18.5,
        "i:fid": 1,
        "i:ra": 12.5,
        "i:dec": -4.25,
        "i:isdiffpos": "t",
        "i:drb": 0.99,
    }


class FinkCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.cache = Path(self.temp.name) / "fink"
        self.cache.mkdir()
        self.cache_patch = mock.patch.object(fink, "CACHE", self.cache)
        self.cache_patch.start()
        self.sleep_patch = mock.patch.object(fink.time, "sleep")
        self.sleep_patch.start()

    def tearDown(self):
        self.sleep_patch.stop()
        self.cache_patch.stop()
        self.temp.cleanup()

    def assert_no_cache(self, oid: str) -> None:
        self.assertFalse((self.cache / f"{oid}.json").exists())
        self.assertFalse((self.cache / "_meta" / f"{oid}.json").exists())

    def test_transport_outage_never_writes_empty_cache(self):
        oid = "ZTF26outage"
        s = StubSession(
            [requests.ConnectionError("offline") for _ in range(fink.FETCH_ATTEMPTS)]
        )

        with self.assertRaises(fink.FinkFetchError):
            fink.fetch_one(s, oid)

        self.assert_no_cache(oid)

    def test_non_200_never_writes_empty_cache(self):
        oid = "ZTF26non200"
        s = StubSession(
            [StubResponse(status_code=503) for _ in range(fink.FETCH_ATTEMPTS)]
        )

        with self.assertRaises(fink.FinkFetchError):
            fink.fetch_one(s, oid)

        self.assert_no_cache(oid)

    def test_malformed_json_never_writes_empty_cache(self):
        oid = "ZTF26malformed"
        s = StubSession(
            [StubResponse(json_error=ValueError("bad JSON"))
             for _ in range(fink.FETCH_ATTEMPTS)]
        )

        with self.assertRaises(fink.FinkFetchError):
            fink.fetch_one(s, oid)

        self.assert_no_cache(oid)

    def test_missing_core_field_never_enters_cache(self):
        oid = "ZTF26missingjd"
        incomplete = record(oid)
        del incomplete["i:jd"]
        s = StubSession(
            [StubResponse(payload=[incomplete])
             for _ in range(fink.FETCH_ATTEMPTS)]
        )

        with self.assertRaises(fink.FinkFetchError):
            fink.fetch_one(s, oid)

        self.assert_no_cache(oid)

    def test_wrong_object_response_never_enters_cache(self):
        oid = "ZTF26wanted"
        s = StubSession(
            [StubResponse(payload=[record("ZTF26other")])
             for _ in range(fink.FETCH_ATTEMPTS)]
        )

        with self.assertRaises(fink.FinkFetchError):
            fink.fetch_one(s, oid)

        self.assert_no_cache(oid)

    def test_http_200_empty_is_cached_with_provenance(self):
        oid = "ZTF26empty"
        first = StubSession([StubResponse(payload=[])])

        self.assertEqual(fink.fetch_one(first, oid), [])
        meta = json.loads(
            (self.cache / "_meta" / f"{oid}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["status"], "ok_empty")
        self.assertEqual(meta["http_status"], 200)
        self.assertTrue(meta["response_validated"])
        self.assertEqual(meta["row_count"], 0)
        self.assertEqual(meta["source_url"], fink.FINK_OBJECTS)
        self.assertIn("fetched_at_utc", meta)

        # A proved empty is a real cache hit, not another network request.
        second = StubSession([])
        self.assertEqual(fink.fetch_one(second, oid), [])
        self.assertEqual(second.calls, [])

    def test_stale_empty_is_refetched(self):
        oid = "ZTF26staleempty"
        self.assertEqual(fink.fetch_one(StubSession([StubResponse(payload=[])]), oid), [])
        meta_path = self.cache / "_meta" / f"{oid}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["fetched_at_utc"] = "2000-01-01T00:00:00Z"
        meta_path.write_text(json.dumps(meta), encoding="utf-8")

        refreshed = fink.fetch_one(
            StubSession([StubResponse(payload=[record(oid)])]),
            oid,
            max_age_seconds=60,
        )

        self.assertEqual(refreshed, [record(oid)])
        current = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertEqual(current["status"], "ok")

    def test_future_fetched_timestamp_is_refetched(self):
        oid = "ZTF26futuretime"
        self.assertEqual(
            fink.fetch_one(StubSession([StubResponse(payload=[])]), oid), []
        )
        meta_path = self.cache / "_meta" / f"{oid}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["fetched_at_utc"] = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat().replace("+00:00", "Z")
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        replacement = record(oid)
        session = StubSession([StubResponse(payload=[replacement])])

        self.assertEqual(fink.fetch_one(session, oid), [replacement])
        self.assertEqual(len(session.calls), 1)

    def test_fresh_by_ttl_but_not_covering_window_is_refetched(self):
        oid = "ZTF26coverage"
        original = record(oid, 2460000.5)
        fink.fetch_one(StubSession([StubResponse(payload=[original])]), oid)
        meta_path = self.cache / "_meta" / f"{oid}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc)
        fetched = now - timedelta(hours=23)
        meta["fetched_at_utc"] = fetched.isoformat().replace("+00:00", "Z")
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        requested_ceiling = fink._datetime_to_jd(now - timedelta(hours=12))
        newer = record(oid, 2460001.5)
        s = StubSession([StubResponse(payload=[newer])])

        got = fink.fetch_one(
            s,
            oid,
            max_age_seconds=24 * 60 * 60,
            required_coverage_jd=requested_ceiling,
        )

        self.assertEqual(got, [newer])
        self.assertEqual(len(s.calls), 1)

    def test_legacy_empty_is_quarantined_then_refetched(self):
        oid = "ZTF26legacyempty"
        (self.cache / f"{oid}.json").write_text("[]", encoding="utf-8")
        s = StubSession([StubResponse(payload=[record(oid)])])

        self.assertEqual(fink.fetch_one(s, oid), [record(oid)])

        quarantines = list((self.cache / "_quarantine").glob(f"*_{oid}"))
        self.assertEqual(len(quarantines), 1)
        self.assertEqual(
            (quarantines[0] / f"{oid}.json").read_text(encoding="utf-8"), "[]"
        )
        self.assertEqual(
            json.loads((self.cache / f"{oid}.json").read_text(encoding="utf-8")),
            [record(oid)],
        )

    def test_legacy_nonempty_remains_compatible_and_gets_sidecar(self):
        oid = "ZTF26legacydata"
        payload = json.dumps([record(oid)])
        (self.cache / f"{oid}.json").write_text(payload, encoding="utf-8")

        self.assertEqual(fink.fetch_one(StubSession([]), oid), [record(oid)])
        meta = json.loads(
            (self.cache / "_meta" / f"{oid}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["status"], "legacy_nonempty")
        self.assertEqual(meta["provenance"], "inferred_from_pre_sidecar_writer")

    def test_new_mtime_legacy_payload_cannot_prove_window_coverage(self):
        oid = "ZTF26copiedlegacy"
        (self.cache / f"{oid}.json").write_text(
            json.dumps([record(oid)]), encoding="utf-8"
        )
        replacement = record(oid, 2460001.5)
        session = StubSession([StubResponse(payload=[replacement])])
        required = fink._datetime_to_jd(
            datetime.now(timezone.utc) - timedelta(hours=1)
        )

        got = fink.fetch_one(
            session,
            oid,
            required_coverage_jd=required,
        )

        self.assertEqual(got, [replacement])
        self.assertEqual(len(session.calls), 1)
        meta = json.loads(
            (self.cache / "_meta" / f"{oid}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["status"], "ok")

    def test_batch_proves_rows_but_confirms_omitted_object_individually(self):
        oid_a, oid_b = "ZTF26batcha", "ZTF26batchb"
        s = StubSession(
            [StubResponse(payload=[record(oid_a)]), StubResponse(payload=[])]
        )

        got = fink.fetch_histories_batch(s, [oid_a, oid_b], chunk=60)

        self.assertEqual(got[oid_a], [record(oid_a)])
        self.assertEqual(got[oid_b], [])
        self.assertEqual(len(s.calls), 2)
        self.assertEqual(s.calls[0][1]["json"]["objectId"], f"{oid_a},{oid_b}")
        self.assertEqual(s.calls[1][1]["json"]["objectId"], oid_b)
        meta_b = json.loads(
            (self.cache / "_meta" / f"{oid_b}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta_b["request_mode"], "single")
        self.assertEqual(meta_b["status"], "ok_empty")

    def test_batch_refresh_bypasses_a_fresh_cache(self):
        oid = "ZTF26batchrefresh"
        fink.fetch_one(StubSession([StubResponse(payload=[record(oid, 2460000.5)])]), oid)
        newer = record(oid, 2460001.5)
        s = StubSession([StubResponse(payload=[newer])])

        got = fink.fetch_histories_batch(s, [oid], refresh=True)

        self.assertEqual(got[oid], [newer])
        self.assertEqual(len(s.calls), 1)

    def test_batch_aborts_if_fallback_cannot_verify_every_object(self):
        oid = "ZTF26batchfail"
        replies = [StubResponse(status_code=503) for _ in range(3)]
        replies.extend(
            requests.ConnectionError("offline") for _ in range(fink.FETCH_ATTEMPTS)
        )
        s = StubSession(replies)

        with self.assertRaisesRegex(fink.FinkFetchError, "aborting the science pass"):
            fink.fetch_histories_batch(s, [oid])

        self.assert_no_cache(oid)

    def test_bulk_migration_moves_only_unproved_empty_arrays(self):
        empty_oid = "ZTF26migrateempty"
        data_oid = "ZTF26migratedata"
        (self.cache / f"{empty_oid}.json").write_text("[]", encoding="utf-8")
        (self.cache / f"{data_oid}.json").write_text(
            json.dumps([record(data_oid)]), encoding="utf-8"
        )

        self.assertEqual(fink.quarantine_legacy_empty_caches(), 1)
        self.assertFalse((self.cache / f"{empty_oid}.json").exists())
        self.assertTrue((self.cache / f"{data_oid}.json").exists())
        self.assertTrue(list((self.cache / "_quarantine").glob(f"*_{empty_oid}")))

    def test_bulk_migration_rejects_merely_present_invalid_sidecar(self):
        oid = "ZTF26invalidproof"
        (self.cache / f"{oid}.json").write_text("[]", encoding="utf-8")
        meta_path = self.cache / "_meta" / f"{oid}.json"
        meta_path.parent.mkdir()
        meta_path.write_text("{}", encoding="utf-8")

        self.assertEqual(fink.quarantine_legacy_empty_caches(), 1)

        quarantines = list((self.cache / "_quarantine").glob(f"*_{oid}"))
        self.assertEqual(len(quarantines), 1)
        self.assertTrue((quarantines[0] / "metadata.json").exists())

    def test_bulk_migration_preserves_proved_empty_cache(self):
        oid = "ZTF26provedempty"
        fink.fetch_one(StubSession([StubResponse(payload=[])]), oid)

        self.assertEqual(fink.quarantine_legacy_empty_caches(), 0)
        self.assertTrue((self.cache / f"{oid}.json").exists())
        self.assertTrue((self.cache / "_meta" / f"{oid}.json").exists())

    def test_cone_outage_does_not_authenticate_legacy_null(self):
        key = "10.000000_20.000000_3.0"
        (self.cache / "_resolve.json").write_text(
            json.dumps({key: None}), encoding="utf-8"
        )
        s = StubSession(
            [requests.ConnectionError("offline") for _ in range(fink.FETCH_ATTEMPTS)]
        )

        with self.assertRaises(fink.FinkFetchError):
            fink.resolve_oid(s, 10.0, 20.0)

        self.assertFalse((self.cache / "_resolve_meta.json").exists())

    def test_cone_http_200_empty_is_reused_with_provenance(self):
        first = StubSession([StubResponse(payload=[])])
        self.assertIsNone(fink.resolve_oid(first, 10.0, 20.0))

        second = StubSession([])
        self.assertIsNone(fink.resolve_oid(second, 10.0, 20.0))
        self.assertEqual(second.calls, [])
        meta = json.loads(
            (self.cache / "_resolve_meta.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["10.000000_20.000000_3.0"]["status"], "ok_empty")

    def test_cone_fresh_mismatched_proof_is_refetched(self):
        key = "10.000000_20.000000_3.0"
        first_oid = "ZTF26resolvefirst"
        self.assertEqual(
            fink.resolve_oid(
                StubSession([StubResponse(payload=[record(first_oid)])]),
                10.0,
                20.0,
            ),
            first_oid,
        )
        meta_path = self.cache / "_resolve_meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta[key]["source_url"] = "https://example.invalid/not-fink"
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        replacement = "ZTF26resolverefetched"
        session = StubSession([StubResponse(payload=[record(replacement)])])

        self.assertEqual(fink.resolve_oid(session, 10.0, 20.0), replacement)
        self.assertEqual(len(session.calls), 1)

    def test_cone_interrupted_payload_then_old_proof_is_refetched(self):
        key = "10.000000_20.000000_3.0"
        old_oid = "ZTF26resolveold"
        new_oid = "ZTF26resolvenew"
        final_oid = "ZTF26resolvefinal"
        self.assertEqual(
            fink.resolve_oid(
                StubSession([StubResponse(payload=[record(old_oid)])]),
                10.0,
                20.0,
            ),
            old_oid,
        )
        cache_path = self.cache / "_resolve.json"
        meta_path = self.cache / "_resolve_meta.json"
        real_write = fink._atomic_write

        def interrupt_before_proof(path, text):
            if path == meta_path:
                raise OSError("simulated interruption before proof")
            real_write(path, text)

        with mock.patch.object(fink, "_atomic_write", side_effect=interrupt_before_proof):
            with self.assertRaisesRegex(OSError, "simulated interruption"):
                fink.resolve_oid(
                    StubSession([StubResponse(payload=[record(new_oid)])]),
                    10.0,
                    20.0,
                    refresh=True,
                )

        self.assertEqual(json.loads(cache_path.read_text(encoding="utf-8"))[key], new_oid)
        self.assertEqual(
            json.loads(meta_path.read_text(encoding="utf-8"))[key]["resolved_oid"],
            old_oid,
        )
        session = StubSession([StubResponse(payload=[record(final_oid)])])
        self.assertEqual(fink.resolve_oid(session, 10.0, 20.0), final_oid)
        self.assertEqual(len(session.calls), 1)

    def test_stale_cone_empty_is_refetched(self):
        key = "10.000000_20.000000_3.0"
        self.assertIsNone(
            fink.resolve_oid(StubSession([StubResponse(payload=[])]), 10.0, 20.0)
        )
        meta_path = self.cache / "_resolve_meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta[key]["fetched_at_utc"] = "2000-01-01T00:00:00Z"
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        response = [{"i:objectId": "ZTF26resolved", "i:jd": 2460000.5}]

        got = fink.resolve_oid(
            StubSession([StubResponse(payload=response)]),
            10.0,
            20.0,
            max_age_seconds=60,
        )

        self.assertEqual(got, "ZTF26resolved")

    def test_history_as_of_excludes_future_alerts(self):
        oid = "ZTF26window"
        records = [record(oid, 2460000.5), record(oid, 2460002.5)]

        self.assertEqual(
            fink.history_as_of(records, 2460001.0),
            [record(oid, 2460000.5)],
        )

    def test_mixed_history_ceilings_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            fink.require_single_jd_ceiling([2460000.5, 2460001.5], "test.csv")


if __name__ == "__main__":
    unittest.main()
