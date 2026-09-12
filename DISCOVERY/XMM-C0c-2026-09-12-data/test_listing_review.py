"""Independent mocked C0c transport/receipt review; never performs a GET."""

import importlib.util
import io
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SPEC = importlib.util.spec_from_file_location("c0c_independent", Path(__file__).with_name("listing.py"))
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class Raw(io.BytesIO):
    def read(self, amount=-1, decode_content=False):
        return super().read(amount)


class IndependentListingTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(mock.patch.object(P, "HERE", root))
        for name, filename in (("SOURCE", "source.py"), ("HELPER", "helper.py"), ("PROTOCOL", "scope.md")):
            path = root / filename
            path.write_text("synthetic fixture\n", encoding="utf-8")
            self.stack.enter_context(mock.patch.object(P, name, path))
        self.stack.enter_context(mock.patch.object(P, "HELPER_HASH", P.sha(P.HELPER)))
        self.stack.enter_context(mock.patch("builtins.print"))

    def parent_helper(self, *, http_status=200, omit_marker=False, code=0):
        def bounded(command, timeout):
            self.assertEqual(timeout, 30)
            self.assertEqual(command[1:], ["-B", str(P.SOURCE), "_worker"])
            if code:
                return code, "synthetic hard timeout"
            body = b"<html>synthetic index</html>"
            if not omit_marker:
                P.save("worker-start.json", {"url": P.URL, "request_attempts": 1})
            P.save("http.json", {"status": http_status, "url": P.URL,
                                 "headers": {"Content-Type": "text/html", "Content-Length": str(len(body))}})
            (P.HERE / "index.html").write_bytes(body)
            P.save("worker-result.json", {"status": "HTTP_INDEX_RETAINED", "request_attempts": 1,
                   "science_products_fetched": 0, "body": {"bytes": len(body), "sha256": P.sha(P.HERE / "index.html")}})
            return 0, "synthetic worker"
        helper = SimpleNamespace(bounded_run=mock.Mock(side_effect=bounded))
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=mock.Mock()))
        self.stack.enter_context(mock.patch.object(P.importlib.util, "spec_from_file_location", return_value=spec))
        self.stack.enter_context(mock.patch.object(P.importlib.util, "module_from_spec", return_value=helper))
        return helper

    def test_ambient_netrc_cannot_add_credentials_to_anonymous_request(self):
        response = mock.MagicMock(status_code=200, url=P.URL)
        response.headers = {"Content-Type": "text/html", "Set-Cookie": "synthetic-secret-cookie"}
        response.raw = Raw(b"<html>synthetic</html>")
        response.__enter__.return_value = response
        with mock.patch("requests.sessions.get_netrc_auth", return_value=("synthetic-user", "synthetic-secret")) as netrc, \
                mock.patch("requests.sessions.Session.send", return_value=response) as send:
            P.collect()
        netrc.assert_not_called()
        request = send.call_args.args[0]
        self.assertNotIn("Authorization", request.headers)
        self.assertNotIn("Cookie", request.headers)
        self.assertNotIn("Proxy-Authorization", request.headers)
        self.assertEqual(request.url, P.URL)
        self.assertFalse(send.call_args.kwargs["allow_redirects"])
        self.assertEqual(send.call_args.kwargs["timeout"], (5, 15))
        self.assertNotIn("synthetic-secret", (P.HERE / "http.json").read_text())

    def test_parent_rejects_http_error_despite_forged_success_worker_receipt(self):
        self.parent_helper(http_status=503)
        with self.assertLogs(level="ERROR"):
            self.assertEqual(P.run(), 1)
        self.assertEqual(P.json.loads((P.HERE / "outcome.json").read_bytes())["worker_returncode"], 0)

    def test_parent_requires_worker_marker(self):
        self.parent_helper(omit_marker=True)
        with self.assertLogs(level="ERROR"):
            self.assertEqual(P.run(), 1)

    def test_complete_parent_retains_hashes_and_refuses_second_launch(self):
        helper = self.parent_helper()
        self.assertEqual(P.run(), 0)
        outcome = P.json.loads((P.HERE / "outcome.json").read_bytes())
        self.assertEqual(outcome["status"], "HTTP_INDEX_RETAINED")
        for name, digest in outcome["artifacts"].items():
            self.assertEqual(P.sha(P.HERE / name), digest)
        self.assertEqual((P.HERE / "protocol.snapshot.md").read_bytes(), P.PROTOCOL.read_bytes())
        with self.assertRaises(FileExistsError):
            P.run()
        helper.bounded_run.assert_called_once()

    def test_timeout_preserves_raw_return_code_and_has_no_retry(self):
        helper = self.parent_helper(code=124)
        with self.assertLogs(level="ERROR"):
            self.assertEqual(P.run(), 1)
        outcome = P.json.loads((P.HERE / "outcome.json").read_bytes())
        self.assertEqual(outcome["worker_returncode"], 124)
        self.assertEqual(outcome["status"], "STOP")
        self.assertFalse((P.HERE / "index.html").exists())
        helper.bounded_run.assert_called_once()

    def test_worker_failure_receipt_and_marker_prevent_second_attempt(self):
        (P.HERE / "protocol.snapshot.md").write_bytes(P.PROTOCOL.read_bytes())
        P.save("run-start.json", {"source_sha256": P.sha(P.SOURCE), "helper_sha256": P.sha(P.HELPER),
                                 "protocol_sha256": P.sha(P.HERE / "protocol.snapshot.md"),
                                 "url": P.URL, "cap": P.CAP, "worker_seconds": 30})
        with mock.patch.object(P, "collect", side_effect=TimeoutError("synthetic socket timeout")) as collect:
            with self.assertLogs(level="ERROR"):
                self.assertEqual(P.worker(), 1)
            result = P.json.loads((P.HERE / "worker-result.json").read_bytes())
            self.assertEqual(result["status"], "STOP")
            self.assertIsNone(result["body"])
            with self.assertRaises(FileExistsError):
                P.worker()
        collect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
