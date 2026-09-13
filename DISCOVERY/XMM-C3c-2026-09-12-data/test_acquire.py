"""One-request metadata fixtures; any response-body access is forbidden."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("c3c", Path(__file__).with_name("acquire.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Response:
    def __init__(self):
        self.request, self.url, self.status_code = SimpleNamespace(method="HEAD"), M.URL, 200
        self.values = {"Content-Length": ["12345"], "Content-Type": ["application/x-tar"],
                       "Content-Disposition": ['attachment; filename="0884250101.tar"'], "Set-Cookie": ["private"]}
        self.raw = SimpleNamespace(headers=SimpleNamespace(getlist=lambda k: self.values.get(k, [])), read=self.forbidden)

    def forbidden(self, *args, **kwargs):
        raise AssertionError("response body forbidden")

    content = property(forbidden)
    text = property(forbidden)
    iter_content = forbidden

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Session:
    def __init__(self, response, calls):
        self.response, self.calls = response, calls
        self.trust_env, self.auth = True, "forbidden"
        self.cookies = SimpleNamespace(clear=lambda: None)

    def request(self, method, url, **kwargs):
        assert self.trust_env is False and self.auth is None
        assert (method, url) == ("HEAD", M.URL)
        assert kwargs == {"timeout": (5, 15), "stream": True, "allow_redirects": False,
                          "headers": {"Accept-Encoding": "identity"}}
        self.calls.append((method, url))
        return self.response

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here, self.response, self.calls = Path(self.temp.name), Response(), []
        patches = [patch.object(M, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                   patch.object(M.C, "checkpoint"), patch.object(M.C, "peak_memory", return_value=100),
                   patch.object(M.C, "PEAK", 0), patch.object(M.C, "DEADLINE", None),
                   patch("requests.Session", side_effect=lambda: Session(self.response, self.calls)),
                   patch.object(M.C, "head_plan", side_effect=AssertionError("old plan forbidden")),
                   patch.object(M.C, "run", side_effect=AssertionError("old run forbidden"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_complete_worker_parent_replay_one_head_no_body(self):
        M.C.save("run-start.json", {"slot": M.SLOT})
        with patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            self.assertEqual(result["status"], M.PASS)
            self.assertEqual(M.assess(124)["status"], "STOP")
            result.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE),
                          parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            M.replay()
        self.assertEqual(len(self.calls), 1)
        http = M.C.read("http.json")
        self.assertNotIn("Set-Cookie", http["headers"])
        self.assertNotIn("Content-Disposition", http["headers"])
        self.assertNotIn("attachment;", (self.here / "http.json").read_text())
        self.assertFalse(M.C.read("request-result.json")["package_member_identity_verified"])

    def test_disposition_strict_safe_basename_and_ambiguity(self):
        invalid = [[], ['attachment; filename="../bad.tar"'], ['attachment; filename="a\\b.tar"'],
                   ['attachment; filename="ok.tar"; filename="other.tar"'],
                   ["attachment; filename*=UTF-8''ok.tar"], ['attachment; filename="a.tar"\r\nOther: bad'],
                   ['attachment; filename="ok.tar"', 'attachment; filename="other.tar"'],
                   ['attachment; filename="a..tar"'], ['attachment; filename="a."'],
                   ['attachment; filename="' + 'a' * 129 + '.tar"'], ['attachment; filename="é.tar"']]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                M.disposition(values)
        parsed = M.disposition(['attachment; filename="ok.tar"'] * 2)
        self.assertEqual(parsed["value_count"], 2)
        self.assertEqual(M.classify(parsed, "application/x-tar"), "PACKAGE_ADVERTISED_MEMBERS_UNKNOWN")

    def test_raw_advertised_filename_not_verified_product(self):
        self.response.values["Content-Disposition"] = [f'attachment; filename="{M.EXPECTED}"']
        self.response.values["Content-Type"] = ["application/octet-stream"]
        result = M.collect()
        self.assertEqual(result["packaging"], "EXPECTED_RAW_FILENAME_ADVERTISED")
        self.assertFalse(result["product_get_performed"])
        self.assertEqual(result["body_bytes_read"], 0)

    def test_length_encodings_media_and_status_rejected_without_body(self):
        cases = [("Content-Length", []), ("Content-Length", ["12345", "999"]),
                 ("Content-Length", [str(M.CAP + 1)]), ("Content-Length", ["0"]),
                 ("Content-Encoding", ["gzip"]), ("Content-Type", ["application/json"]),
                 ("Content-Type", ["application/xml"]), ("Content-Type", ["text/html"]),
                 ("Content-Type", ["application/zip"])]
        for key, value in cases:
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
                old = self.response.values.copy()
                self.response.values[key] = value
                with self.assertRaises(ValueError):
                    M.collect()
                self.response.values = old

    def test_duplicate_identical_decimal_lengths_are_preserved(self):
        self.response.values["Content-Length"] = ["012345", "12345"]
        self.assertEqual(M.collect()["advertised_entity_bytes"], 12345)
        self.assertEqual(M.C.read("http.json")["headers"]["Content-Length"], ["012345", "12345"])

    def test_404_and_redirect_do_not_read_body(self):
        for status in (404, 302):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
                self.response.status_code = status
                with self.assertRaisesRegex(ValueError, "STOP_HTTP_IDENTITY_OR_STATUS"):
                    M.collect()

    def test_invalid_disposition_never_persisted_raw(self):
        self.response.values["Content-Disposition"] = ['attachment; filename="../../private.tar"']
        with self.assertRaises(ValueError):
            M.collect()
        self.assertNotIn("private", (self.here / "http.json").read_text())
        self.assertEqual(M.C.read("http.json")["disposition"]["status"], "REJECTED")

    def test_binding_roundtrip_and_changed_runtime(self):
        with patch.object(M, "HERE", M.SOURCE.parent), patch.object(M.C, "HERE", M.SOURCE.parent):
            binding = M.binding(M.PROTOCOL)
        self.assertEqual(json.loads(json.dumps(binding)), binding)
        M.C.save("run-start.json", binding)
        with patch.object(M, "binding", return_value={**binding, "runtime": {}}), self.assertRaisesRegex(ValueError, "STOP_BINDING"):
            M.verify_binding()

    def test_parent_independently_reclassifies_safe_metadata(self):
        M.collect()
        http = M.C.read("http.json")
        http["disposition"]["filename"] = "unsafe.xml"
        with self.assertRaisesRegex(ValueError, "STOP_UNRECOGNIZED_PACKAGING"):
            M.measurement(http)
        http["disposition"]["filename"] = "safe.tar"
        http["disposition"]["value_count"] = 0
        with self.assertRaisesRegex(ValueError, "STOP_DISPOSITION_RECEIPT"):
            M.measurement(http)

    def test_prelaunch_failure_one_unattempted_slot(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_DEPENDENCY_HASH")):
            self.assertEqual(M.run(), 1)
        self.assertEqual(M.C.read("outcome.json")["ledger"], [{"slot": 1, "status": "NOT_ATTEMPTED"}])
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_failed_receipt_rejects_extra_raw_text(self):
        M.C.save("request-start.json", {"slot": M.SLOT, "elapsed_seconds": 1})
        M.C.save("request-result.json", {"slot": M.SLOT, "status": "FAILED", "error_type": "ValueError",
                                          "error_code": "STOP_DISPOSITION_SYNTAX", "raw": "forbidden"})
        with self.assertRaisesRegex(ValueError, "STOP_FAILED_RECEIPT_SCHEMA"):
            M.ledger()

    def test_timeout_partial_marker_preserved(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 30)
            self.assertEqual(command[-1], "_worker")
            (self.here / "request-start.json").write_bytes(b'{"slot":')
            return 124, "discarded"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value={"slot": M.SLOT}), \
                patch.object(M, "verify_binding"), patch.object(M.C, "load_pinned", return_value=SimpleNamespace(bounded_run=timeout)):
            self.assertEqual(M.run(), 1)
        result = M.C.read("outcome.json")
        self.assertEqual(result["worker_returncode"], 124)
        self.assertEqual(result["ledger"], [{"slot": 1, "status": "UNVERIFIED_ATTEMPT"}])
        M.replay()


if __name__ == "__main__":
    unittest.main()
