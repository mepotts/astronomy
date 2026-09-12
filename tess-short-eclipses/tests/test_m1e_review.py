"""Independent M1e harness tests; fake network and isolated temporary receipts."""

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests

SPEC = importlib.util.spec_from_file_location(
    "m1e_reviewed", Path(__file__).resolve().parents[1] / "scripts/m1e.py")
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


class Harness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tess-m1e-review-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, value in (("ROOT", self.root), ("DATA", self.root / "data"),
                            ("MANIFEST", self.root / "manifest.json"),
                            ("SUMMARY", self.root / "summary.json")):
            handle = patch.object(E, name, value)
            handle.start()
            self.addCleanup(handle.stop)
        E.M.save(E.MANIFEST, {"fixture": "not a real authorization"})
        E.M.save(E.DATA / "run-start.json", {"approved_manifest_sha256": E.M.sha(E.MANIFEST)})
        self.tic = E.TARGETS[0]
        self.expected = {"tic": self.tic, "url": E.URL, "adql": "EXACT KNOWN QUERY",
                         "manifest_sha256": E.M.sha(E.MANIFEST)}
        self.folder = E.DATA / str(self.tic)
        E.M.save(self.folder / "attempt.json", self.expected)
        self.patches = [patch.object(E, "verify"), patch.object(E, "plan", return_value=self.expected),
                        patch.object(E, "validated", return_value=[1]),
                        patch.object(E, "diagnostic", return_value={"fixture": True})]
        self.verify, self.plan, self.validate, self.diagnostic = [item.start() for item in self.patches]
        for item in self.patches:
            self.addCleanup(item.stop)
        logger_patch = patch.object(E.LOGGER, "exception")
        logger_patch.start()
        self.addCleanup(logger_patch.stop)
        self.session = MagicMock()
        self.response = MagicMock()
        self.response.status_code = 200
        self.response.headers = {}
        self.response.iter_content.return_value = [b"complete fake XML"]
        self.session.post.return_value.__enter__.return_value = self.response
        session_patch = patch("requests.Session")
        factory = session_patch.start()
        self.addCleanup(session_patch.stop)
        factory.return_value.__enter__.return_value = self.session

    def read(self, name):
        return json.loads((self.folder / name).read_bytes())

    def test_success_exact_request_and_raw_receipt(self):
        E.worker(self.tic)
        self.session.post.assert_called_once_with(
            E.URL, data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable",
                         "QUERY": self.expected["adql"]},
            stream=True, timeout=(45, 45), allow_redirects=False)
        adapter = self.session.mount.call_args.args[1]
        self.assertEqual(adapter.max_retries.total, 0)
        raw = self.read("response-receipt.json")
        self.assertEqual(raw["bytes"], len(b"complete fake XML"))
        self.assertEqual(raw["sha256"], E.M.sha(self.folder / "gaia-dr3.xml"))
        self.assertEqual(self.read("catalog-receipt.json")["rows"], 1)

    def test_second_worker_never_reissues_network(self):
        E.worker(self.tic)
        with self.assertRaises(FileExistsError):
            E.worker(self.tic)
        self.assertEqual(self.session.post.call_count, 1)

    def test_redirect_records_failure_without_response(self):
        self.response.status_code = 302
        with self.assertRaisesRegex(ValueError, "STOP_HTTP:302"):
            E.worker(self.tic)
        self.assertIn("STOP_HTTP:302", self.read("failure.json")["traceback"])
        self.assertEqual(self.read("failure.json")["partial_bytes"], 0)
        self.assertFalse((self.folder / "catalog-receipt.json").exists())

    def test_socket_timeout_records_failure(self):
        self.session.post.side_effect = requests.Timeout("synthetic socket deadline")
        with self.assertRaises(requests.Timeout):
            E.worker(self.tic)
        self.assertIn("synthetic socket deadline", self.read("failure.json")["traceback"])
        self.assertTrue((self.folder / "worker-start.json").exists())

    def test_actual_stream_cap_retains_partial_not_complete_receipt(self):
        self.response.iter_content.return_value = [b"a" * 3_000_000, b"b" * 3_000_000]
        with self.assertRaisesRegex(ValueError, "STOP_TRANSFER_LIMIT"):
            E.worker(self.tic)
        self.assertEqual((self.folder / "gaia-dr3.xml").stat().st_size, 3_000_000)
        self.assertEqual(self.read("failure.json")["partial_bytes"], 3_000_000)
        self.assertFalse((self.folder / "response-receipt.json").exists())
        self.validate.assert_not_called()

    def test_announced_oversize_stops_before_file(self):
        self.response.headers = {"Content-Length": "5000001"}
        with self.assertRaisesRegex(ValueError, "STOP_SIZE"):
            E.worker(self.tic)
        self.assertFalse((self.folder / "gaia-dr3.xml").exists())
        self.validate.assert_not_called()

    def test_complete_unsupported_decode_keeps_raw_hash_and_failure(self):
        self.validate.side_effect = ValueError("STOP_SCHEMA")
        with self.assertRaisesRegex(ValueError, "STOP_SCHEMA"):
            E.worker(self.tic)
        self.assertEqual(self.read("response-receipt.json")["sha256"],
                         E.M.sha(self.folder / "gaia-dr3.xml"))
        self.assertFalse((self.folder / "catalog-receipt.json").exists())
        self.assertIn("STOP_SCHEMA", self.read("failure.json")["traceback"])
        self.diagnostic.assert_not_called()

    def test_pre_request_provenance_failure_preserves_marker(self):
        self.verify.side_effect = ValueError("STOP_MANIFEST_CHANGED")
        with self.assertRaisesRegex(ValueError, "STOP_MANIFEST_CHANGED"):
            E.worker(self.tic)
        self.session.post.assert_not_called()
        self.assertTrue((self.folder / "worker-start.json").exists())
        self.assertIn("STOP_MANIFEST_CHANGED", self.read("failure.json")["traceback"])

    def test_attempt_mismatch_never_starts_request(self):
        self.plan.return_value = {**self.expected, "adql": "MISMATCH"}
        with self.assertRaisesRegex(ValueError, "STOP_ATTEMPT"):
            E.worker(self.tic)
        self.session.post.assert_not_called()
        self.assertFalse((self.folder / "worker-start.json").exists())

    def test_successful_receipt_remains_when_diagnostic_fails(self):
        self.diagnostic.side_effect = ValueError("STOP_TIME_SELECTION")
        with self.assertRaisesRegex(ValueError, "STOP_TIME_SELECTION"):
            E.worker(self.tic)
        self.assertTrue((self.folder / "catalog-receipt.json").exists())
        self.assertIn("STOP_TIME_SELECTION", self.read("failure.json")["traceback"])
        self.assertFalse((E.ROOT / f"out/m1e-{self.tic}.json").exists())


class ParentHarness(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="tess-m1e-parent-review-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name, value in (("ROOT", self.root), ("DATA", self.root / "data"),
                            ("MANIFEST", self.root / "manifest.json"),
                            ("SUMMARY", self.root / "summary.json")):
            handle = patch.object(E, name, value)
            handle.start()
            self.addCleanup(handle.stop)
        E.M.save(E.MANIFEST, {"fixture": True})
        for tic in E.TARGETS:
            E.M.save(E.ROOT / f"data/m1/{tic}/catalog-query.json", {"adql": f"known {tic}"})
        self.loader = MagicMock()
        self.runner = MagicMock()
        self.patches = [patch.object(E, "verify"), patch.object(E.LOGGER, "exception"),
                        patch.object(E.importlib.util, "spec_from_file_location",
                                     return_value=SimpleNamespace(loader=self.loader)),
                        patch.object(E.importlib.util, "module_from_spec", return_value=self.runner)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def run_parent(self):
        with redirect_stdout(StringIO()):
            E.run(E.M.sha(E.MANIFEST))
        return E.C.read_json(E.SUMMARY)

    def inventory(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def replay_unchanged(self):
        before = self.inventory()
        with patch("requests.Session") as network, redirect_stdout(StringIO()):
            E.replay()
        network.assert_not_called()
        self.assertEqual(before, self.inventory())

    def test_loader_failure_accounts_both_unlaunched_and_replays(self):
        self.loader.exec_module.side_effect = RuntimeError("synthetic import failure")
        result = self.run_parent()
        self.assertEqual(result["status"], "STOP_PRELAUNCH")
        self.assertEqual([row["status"] for row in result["outcomes"]], ["STOP_NOT_LAUNCHED"] * 2)
        self.assertEqual([row["tic"] for row in result["outcomes"]], list(E.TARGETS))
        self.assertFalse(any(E.DATA.glob("*/attempt.json")))
        self.runner.bounded_run.assert_not_called()
        self.replay_unchanged()

    def test_reservation_failure_accounts_remaining_without_launch(self):
        original_save = E.M.save

        def fail_attempt(path, value):
            if path.name == "attempt.json":
                raise OSError("synthetic reservation failure")
            return original_save(path, value)

        with patch.object(E.M, "save", side_effect=fail_attempt):
            result = self.run_parent()
        self.assertEqual(result["status"], "STOP_PRELAUNCH")
        self.assertEqual([row["status"] for row in result["outcomes"]], ["STOP_NOT_LAUNCHED"] * 2)
        self.runner.bounded_run.assert_not_called()
        self.replay_unchanged()

    def test_first_timeout_retains_two_ordered_exact_deadlines_and_replay(self):
        self.runner.bounded_run.side_effect = [(124, "synthetic deadline"), (1, "synthetic failure")]
        result = self.run_parent()
        self.assertEqual([row["returncode"] for row in result["outcomes"]], [124, 1])
        calls = self.runner.bounded_run.call_args_list
        self.assertEqual([call.args[0][-1] for call in calls], [str(tic) for tic in E.TARGETS])
        self.assertTrue(all(call.args[1] == 60 and Path(call.args[0][2]).is_absolute() for call in calls))
        self.replay_unchanged()
        with self.assertRaises(FileExistsError), redirect_stdout(StringIO()):
            E.run(E.M.sha(E.MANIFEST))
        self.assertEqual(self.runner.bounded_run.call_count, 2)

    def test_launch_exception_is_captured_and_second_is_still_bounded(self):
        self.runner.bounded_run.side_effect = [OSError("synthetic launch failure"), (1, "second failed")]
        result = self.run_parent()
        self.assertIn("synthetic launch failure", result["outcomes"][0]["output"])
        self.assertEqual(len(result["outcomes"]), 2)
        self.assertTrue(all(row["status"] == "STOP_CATALOG_UNAVAILABLE" for row in result["outcomes"]))
        self.replay_unchanged()

    def test_success_replay_recomputes_diagnostics_and_detects_tampering(self):
        def successful_worker(command, _deadline):
            tic = int(command[-1])
            E.M.save(E.ROOT / f"out/m1e-{tic}.json", {"tic": tic, "fixture": True})
            return 0, "synthetic success"

        self.runner.bounded_run.side_effect = successful_worker
        self.run_parent()
        with patch.object(E, "diagnostic", side_effect=lambda tic: {"tic": tic, "fixture": True}) as diagnostic:
            self.replay_unchanged()
            self.assertEqual([call.args[0] for call in diagnostic.call_args_list], list(E.TARGETS))
        path = E.ROOT / f"out/m1e-{E.TARGETS[0]}.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "STOP_OUTCOME_REPLAY"):
            E.replay()


if __name__ == "__main__":
    unittest.main()
