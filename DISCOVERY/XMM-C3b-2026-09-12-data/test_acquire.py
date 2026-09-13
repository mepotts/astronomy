"""Synthetic four-request continuation and isolated prior provenance checks."""

import copy
import gzip
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from astropy.io.fits import Header

SPEC = importlib.util.spec_from_file_location("c3b", Path(__file__).with_name("acquire.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fits_bytes():
    h = Header()
    h["SIMPLE"], h["BITPIX"], h["NAXIS"], h["EXTEND"] = True, 8, 0, True
    return h.tostring().encode()


class Response:
    def __init__(self, method, url, body, status=200, headers=None):
        self.request, self.url, self.status_code = SimpleNamespace(method=method), url, status
        self.values = headers if headers is not None else {"Content-Length": [str(len(body))], "ETag": ['"fixed"']}
        self.stream, self.reads = io.BytesIO(body), []
        self.raw = SimpleNamespace(headers=SimpleNamespace(getlist=lambda k: self.values.get(k, [])), read=self.read)

    def read(self, size, decode_content=False):
        assert self.request.method != "HEAD", "HEAD body forbidden"
        self.reads.append(size)
        return self.stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Session:
    def __init__(self, queue, calls):
        self.queue, self.calls = queue, calls
        self.trust_env, self.auth = True, "forbidden"
        self.cookies = SimpleNamespace(clear=lambda: None)

    def request(self, method, url, **kwargs):
        assert self.trust_env is False and self.auth is None
        assert kwargs == {"timeout": (5, 15), "stream": True, "allow_redirects": False,
                          "headers": {"Accept-Encoding": "identity"}}
        response = self.queue.pop(0)
        assert (method, url) == (response.request.method, response.url)
        self.calls.append((method, url))
        return response

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here = Path(self.temp.name)
        self.patches = [patch.object(M, "HERE", self.here), patch.object(M.T, "HERE", self.here),
                        patch.object(M.T.C, "HERE", self.here), patch.object(M.T.C, "checkpoint"),
                        patch.object(M.T.C, "peak_memory", return_value=100), patch.object(M.T.C, "PEAK", 0),
                        patch.object(M.T.C, "DEADLINE", None)]
        for module in (M.T, M.P):
            for function in ("worker", "run"):
                self.patches.append(patch.object(module, function, side_effect=AssertionError("old network worker forbidden")))
        self.patches.append(patch.object(M.T, "plan", side_effect=AssertionError("old current plan forbidden")))
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.slots = M.plan()
        self.compressed = gzip.compress(fits_bytes())
        self.prior_heads = []
        for i, (slot, size) in enumerate(zip(self.slots[1:3], M.PRIOR_SIZES, strict=True), 1):
            original = {**slot, "slot": i, "method": "HEAD"}
            http = {"method": "HEAD", "url": slot["url"], "status": 200,
                    "headers": {"Content-Length": [str(size)], "ETag": ['"fixed"']}}
            self.prior_heads.append({"original_slot": original, "http": http,
                                     "receipt": M.T.validate_head(original, http),
                                     "http_sha256": "synthetic", "receipt_sha256": "synthetic"})
        self.start = {"slots": self.slots, "prior_heads": self.prior_heads}
        self.calls = []

    def fixture(self):
        bodies = [self.compressed] + [self.compressed + b"\0" * (size - len(self.compressed)) for size in M.PRIOR_SIZES] + [self.compressed]
        self.queue = [Response(slot["method"], slot["url"], body) for slot, body in zip(self.slots, bodies, strict=True)]
        M.T.C.save("run-start.json", self.start)
        return patch("requests.Session", side_effect=lambda: Session(self.queue, self.calls))

    def test_complete_one_head_three_get_worker_parent_replay(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            self.assertEqual(result["status"], M.PASS)
            self.assertEqual([m for m, _ in self.calls], ["HEAD", "GET", "GET", "GET"])
            self.assertEqual(result["resource_usage"]["compressed_bytes"], 779072 + len(self.compressed))
            self.assertEqual(result["resource_usage"]["expanded_bytes"], 3 * len(fits_bytes()))
            self.assertEqual(M.assess(124)["status"], "STOP")
            result.update(assessment_completed=True, artifacts=M.T.artifacts(), source_sha256=M.T.C.sha(M.SOURCE),
                          parent_peak_memory_bytes=100)
            M.T.C.save("outcome.json", result, terminal=True)
            M.replay()
            self.assertEqual(len(self.calls), 4)
            self.assertEqual(len(list((self.here / "products").iterdir())), 6)
            self.assertEqual(len(list((self.here / "headers").iterdir())), 3)
            (self.here / "products/orphan.FTZ").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "STOP_PRODUCT_SET"):
                M.T.verify_product_set(M.get_plan(self.start))

    def test_att_failure_prevents_every_get(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            self.queue[0].status_code = 404
            response = self.queue[0]
            self.assertEqual(M.worker(), 1)
        self.assertEqual(response.reads, [])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual([r["status"] for r in M.T.C.read("worker-result.json")["ledger"]],
                         ["FAILED", "NOT_ATTEMPTED", "NOT_ATTEMPTED", "NOT_ATTEMPTED"])

    def test_changed_prior_entity_stops_before_body(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            response = self.queue[1]
            response.values["ETag"] = ['"changed"']
            self.assertEqual(M.worker(), 1)
        self.assertEqual(response.reads, [])
        self.assertEqual(len(self.calls), 2)
        self.assertFalse((self.here / "products").exists())

    def test_404_size_cannot_replace_prior_head(self):
        invalid = copy.deepcopy(self.start)
        invalid["prior_heads"][1]["receipt"]["advertised_compressed_bytes"] = 19
        with self.assertRaisesRegex(ValueError, "STOP_IMPORTED_HEADS"):
            M.get_plan(invalid)

    def test_prior_url_cannot_be_substituted(self):
        with self.fixture():
            M.T.C.save("slot-1-result.json", M.T.collect_head(self.slots[0]))
        invalid = copy.deepcopy(self.start)
        invalid["prior_heads"][0]["http"]["url"] = self.slots[2]["url"]
        with self.assertRaisesRegex(ValueError, "STOP_HTTP_IDENTITY_OR_STATUS"):
            M.get_plan(invalid)

    def test_prior_outcome_mutation_stops_before_replay(self):
        with patch.object(M.T.C, "sha", return_value="wrong"), patch.object(M.P, "replay") as replay:
            with self.assertRaisesRegex(ValueError, "STOP_PRIOR_OUTCOME_HASH"):
                M.prior_evidence()
            replay.assert_not_called()

    def test_isolated_modules_reduced_configuration_and_roundtrip(self):
        self.assertIsNot(M.P, M.T)
        self.assertIsNot(M.P.C, M.T.C)
        self.assertEqual(M.P.C.HERE, M.PRIOR_PATH.parent)
        self.assertEqual(M.P.C.EXPANDED_TOTAL_CAP, 134217728)
        self.assertEqual(M.T.C.EXPANDED_TOTAL_CAP, 100663296)
        self.assertEqual(sum(M.T.C.EXPECTED), 2876224)
        with patch.object(M, "HERE", M.SOURCE.parent), patch.object(M.T, "HERE", M.SOURCE.parent), \
                patch.object(M.T.C, "HERE", M.SOURCE.parent), patch.object(M, "prior_evidence", return_value=self.prior_heads):
            binding = M.binding(M.PROTOCOL)
        self.assertEqual(binding, json.loads(json.dumps(binding)))
        self.assertEqual(binding["configuration"]["expanded_total"], 100663296)
        self.assertEqual(binding["prior_heads"], self.prior_heads)

    def test_imported_head_binding_mutation(self):
        M.T.C.save("run-start.json", self.start)
        changed = copy.deepcopy(self.start)
        changed["prior_heads"][0]["http_sha256"] = "changed"
        with patch.object(M, "binding", return_value=changed), self.assertRaisesRegex(ValueError, "STOP_BINDING"):
            M.verify_binding()

    def test_actual_prior_replay_only_on_exact_owner_runtime(self):
        path = M.PRIOR_PATH.with_name("run-start.json")
        if not path.exists():
            self.skipTest("Local frozen C3 receipts required")
        import astropy
        import requests

        frozen = json.loads(path.read_bytes())
        runtime = {"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                   "requests": requests.__version__, "astropy": astropy.__version__}
        if frozen["runtime"] != runtime or frozen["configuration"]["output_directory"] != str(M.P.C.HERE):
            self.skipTest("Exact frozen owner runtime/path required for actual prior replay; mocked integration remains mandatory")
        evidence = M.prior_evidence()
        self.assertEqual([r["receipt"]["advertised_compressed_bytes"] for r in evidence], [503855, 275217])
        self.assertEqual(M.P.C.HERE, M.PRIOR_PATH.parent)

    def test_truncated_marker_timeout_preserves_all_four_slots(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 120)
            self.assertEqual(command[-1], "_worker")
            (self.here / "slot-1-start.json").write_bytes(b'{"slot":')
            return 124, "discarded"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value=self.start), \
                patch.object(M, "verify_binding"), patch.object(M.T.C, "load_pinned", return_value=SimpleNamespace(bounded_run=timeout)):
            self.assertEqual(M.run(), 1)
        outcome = M.T.C.read("outcome.json")
        self.assertEqual(outcome["worker_returncode"], 124)
        self.assertEqual(len(outcome["ledger"]), 4)
        self.assertEqual(outcome["ledger"][0]["status"], "UNVERIFIED_ATTEMPT")
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_prelaunch_failure_has_all_four_slots(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_PRIOR_STATE")):
            self.assertEqual(M.run(), 1)
        outcome = M.T.C.read("outcome.json")
        self.assertEqual(len(outcome["ledger"]), 4)
        self.assertTrue(all(r["status"] == "NOT_ATTEMPTED" for r in outcome["ledger"]))
        M.replay()


if __name__ == "__main__":
    unittest.main()
