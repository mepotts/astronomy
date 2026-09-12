"""Mocked five-slot metadata checks; no network or science inputs."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location("xmm_c0d_test", Path(__file__).with_name("metadata.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Raw(io.BytesIO):
    def __init__(self, body, headers, forbid=False):
        super().__init__(body)
        self.headers = SimpleNamespace(getlist=lambda k: headers.get(k, []))
        self.forbid = forbid

    def read(self, amount=-1, decode_content=False):
        if self.forbid:
            raise AssertionError("HEAD body read")
        return super().read(amount)


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.object(M, "HERE", self.root))
        for field, filename in (("SOURCE", "metadata.py"), ("PROTOCOL", "protocol.md")):
            p = self.root / filename
            p.write_text("synthetic source fixture\n", encoding="utf-8")
            self.stack.enter_context(patch.object(M, field, p))
        (self.root / "test_metadata.py").write_text("synthetic test fixture\n", encoding="utf-8")
        self.stack.enter_context(patch.object(M.LOGGER, "exception"))
        self.stack.enter_context(patch("builtins.print"))

    def response(self, slot, *, body=b"<html>Observation 0884250101</html>", status=200,
                 lengths=None, mime="text/html", encoding=None):
        headers = {"Content-Type": [mime], "Set-Cookie": ["synthetic-secret"]}
        if lengths is not None:
            headers["Content-Length"] = lengths
        elif slot["method"] == "HEAD":
            headers["Content-Length"] = ["123"]
        if encoding is not None:
            headers["Content-Encoding"] = [encoding]
        response = MagicMock(status_code=status, url=slot["url"])
        response.request.method = slot["method"]
        response.raw = Raw(body, headers, forbid=slot["method"] == "HEAD")
        response.__enter__.return_value = response
        session = MagicMock()
        session.__enter__.return_value = session
        session.request.return_value = response
        return response, session

    def prepare(self):
        M.save("run-start.json", M.binding(M.PROTOCOL))
        (self.root / "protocol.snapshot.md").write_bytes(M.PROTOCOL.read_bytes())

    def batch(self, *, bad_slot=None):
        self.prepare()
        pairs = [self.response(s, status=503 if s["slot"] == bad_slot else 200) for s in M.plan()]
        self.stack.enter_context(patch("requests.Session", side_effect=[p[1] for p in pairs]))
        code = M.worker()
        return code, pairs

    def test_length_unambiguous_duplicates_and_failures(self):
        for values in (["123"], ["123", "123"], ["123, 123"], ["00123", "123"]):
            self.assertEqual(M.length(values, True), 123)
        for values in ([], ["1", "2"], ["1, 2"], ["+1"], ["1.0"], ["1e3"], [""], ["0"], ["١"]):
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, "STOP_SIZE_METADATA"):
                M.length(values, True)
        self.assertIsNone(M.length([], False))

    def test_head_never_reads_body_and_anonymous_safe_headers(self):
        slot = M.plan()[0]
        response, session = self.response(slot, mime="application/octet-stream")
        with patch("requests.Session", return_value=session):
            result = M.collect(slot)
        self.assertEqual(result["body_bytes_read"], 0)
        self.assertEqual(response.raw.tell(), 0)
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once_with()
        session.request.assert_called_once_with("HEAD", slot["url"], timeout=(5, 15), stream=True,
            allow_redirects=False, headers={"Accept-Encoding": "identity"})
        self.assertNotIn("synthetic-secret", (self.root / "slot-1-http.json").read_text())

    def test_head_http_error_still_never_reads_body(self):
        slot = M.plan()[0]
        response, session = self.response(slot, status=302)
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_HTTP"):
            M.collect(slot)
        self.assertEqual(response.raw.tell(), 0)
        session.request.assert_called_once()

    def test_raw_duplicate_length_conflict_stops_without_head_read(self):
        slot = M.plan()[0]
        response, session = self.response(slot, lengths=["123", "124"])
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_SIZE_METADATA"):
            M.collect(slot)
        self.assertEqual(response.raw.tell(), 0)
        self.assertEqual(M.read("slot-1-http.json")["headers"]["Content-Length"], ["123", "124"])

    def test_summary_cap_plus_one_exact_retention(self):
        slot = M.plan()[4]
        response, session = self.response(slot, body=b"x" * (M.CAP + 50))
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_BYTE_CAP"):
            M.collect(slot)
        self.assertEqual((self.root / "summary.html").stat().st_size, M.CAP)
        self.assertEqual(response.raw.tell(), M.CAP + 1)

    def test_encoded_summary_is_not_consumed(self):
        slot = M.plan()[4]
        response, session = self.response(slot, encoding="gzip")
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_CONTENT_ENCODING"):
            M.collect(slot)
        self.assertEqual(response.raw.tell(), 0)

    def test_summary_id_without_complete_footer_stops(self):
        slot = M.plan()[4]
        _response, session = self.response(slot, body=b"<html>Observation 0884250101")
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_SUMMARY_FOOTER"):
            M.collect(slot)

    def test_internal_stop_reason_retained_without_arbitrary_message(self):
        self.assertEqual(M.failure(ValueError("STOP_SIZE_METADATA"))["error_code"], "STOP_SIZE_METADATA")
        self.assertIsNone(M.failure(ValueError("arbitrary synthetic private text"))["error_code"])
        code, _pairs = self.batch(bad_slot=2)
        self.assertEqual(M.assess(code)["worker_error_code"], "STOP_HTTP_IDENTITY_OR_STATUS")
        self.assertEqual(M.read("slot-2-result.json")["error_code"], "STOP_HTTP_IDENTITY_OR_STATUS")

    def test_all_five_success_parent_rechecks_and_distinct_sessions(self):
        code, pairs = self.batch()
        self.assertEqual(code, 0)
        result = M.assess(code)
        self.assertEqual(result["status"], M.PASS)
        self.assertEqual(result["request_markers"], 5)
        self.assertEqual(result["compressed_total"], 492)
        self.assertEqual(result["photon_body_bytes_read"], 0)
        for response, session in pairs:
            session.request.assert_called_once()
            if response.request.method == "HEAD":
                self.assertEqual(response.raw.tell(), 0)
        self.assertEqual(M.assess(124)["status"], "STOP")
        self.assertEqual(M.assess(1)["status"], "STOP")

    def test_first_error_stops_remainder_and_preserves_failed_slot(self):
        code, pairs = self.batch(bad_slot=2)
        result = M.assess(code)
        self.assertEqual(code, 1)
        self.assertEqual([r["status"] for r in result["ledger"]],
                         ["OK", "FAILED", "NOT_ATTEMPTED", "NOT_ATTEMPTED", "NOT_ATTEMPTED"])
        for _response, session in pairs[2:]:
            session.request.assert_not_called()

    def test_remaining_time_checked_before_first_request(self):
        self.prepare()
        with patch.object(M.time, "monotonic", side_effect=[0, 61]), patch("requests.Session") as session:
            self.assertEqual(M.worker(), 1)
            session.assert_not_called()
        self.assertTrue(all(r["status"] == "NOT_ATTEMPTED" for r in M.assess(1)["ledger"]))

    def test_parent_rejects_modified_http_even_if_worker_claims_success(self):
        self.batch()
        p = self.root / "slot-1-http.json"
        obj = json.loads(p.read_bytes())
        obj["method"] = "GET"
        p.write_text(json.dumps(obj), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STOP_HTTP"):
            M.assess(0)

    def test_parent_rejects_extra_late_request(self):
        self.batch(bad_slot=2)
        M.save("slot-3-start.json", {**M.plan()[2], "elapsed_seconds": 2})
        with self.assertRaisesRegex(ValueError, "STOP_REQUEST_ORDER"):
            M.assess(1)

    def test_parent_rejects_changed_dependency(self):
        self.batch()
        M.SOURCE.write_text("changed fixture", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STOP_BINDING"):
            M.assess(0)

    def test_prelaunch_failure_keeps_five_not_attempted_slots_and_blocks_retry(self):
        with patch.object(M, "HELPER_HASH", "wrong"), patch("requests.Session") as session:
            self.assertEqual(M.run(), 1)
            session.assert_not_called()
        result = M.read("outcome.json")
        self.assertEqual(result["error_code"], "STOP_HELPER_HASH")
        self.assertIs(result["worker_dispatch_started"], False)
        self.assertEqual(len(result["ledger"]), 5)
        self.assertTrue(all(r["status"] == "NOT_ATTEMPTED" for r in result["ledger"]))
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_helper_uses_one_whole_batch_sixty_second_deadline(self):
        calls = []

        def bounded(command, timeout):
            calls.append((command, timeout))
            return 124, "synthetic timeout"

        helper = SimpleNamespace(bounded_run=bounded)
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))
        with patch.object(M.importlib.util, "spec_from_file_location", return_value=spec), \
                patch.object(M.importlib.util, "module_from_spec", return_value=helper):
            self.assertEqual(M.run(), 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 60)
        self.assertTrue(Path(calls[0][0][0]).is_absolute())
        self.assertEqual(calls[0][0][1:], ["-B", str(M.SOURCE), "_worker"])
        result = M.read("outcome.json")
        self.assertEqual(result["worker_returncode"], 124)
        self.assertTrue(all(r["status"] == "NOT_ATTEMPTED" for r in result["ledger"]))
        M.replay()

    def test_full_mock_parent_worker_hash_closure_and_replay(self):
        pairs = [self.response(s) for s in M.plan()]
        helper = SimpleNamespace(bounded_run=lambda command, timeout: (M.worker(), "mocked worker"))
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))
        with patch("requests.Session", side_effect=[p[1] for p in pairs]), \
                patch.object(M.importlib.util, "spec_from_file_location", return_value=spec), \
                patch.object(M.importlib.util, "module_from_spec", return_value=helper):
            self.assertEqual(M.run(), 0)
        self.assertEqual(M.read("outcome.json")["status"], M.PASS)
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()


if __name__ == "__main__":
    unittest.main()
