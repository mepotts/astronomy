"""Synthetic HEAD/GET phase integration only; no real requests or payloads."""

import gzip
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from astropy.io.fits import Header

SPEC = importlib.util.spec_from_file_location("c3", Path(__file__).with_name("acquire.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fits_bytes():
    h = Header()
    h["SIMPLE"], h["BITPIX"], h["NAXIS"], h["EXTEND"] = True, 8, 0, True
    return h.tostring().encode("ascii")


class Response:
    def __init__(self, method, url, body=b"", status=200, headers=None):
        self.request, self.url, self.status_code = SimpleNamespace(method=method), url, status
        self.values = headers if headers is not None else {"Content-Length": [str(len(body))], "ETag": ['"fixed"']}
        self.stream, self.calls = io.BytesIO(body), []
        self.raw = SimpleNamespace(headers=SimpleNamespace(getlist=lambda k: self.values.get(k, [])), read=self.read)

    def read(self, size, decode_content=False):
        if self.request.method == "HEAD":
            raise AssertionError("HEAD body read")
        self.calls.append(size)
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
        self.patches = [patch.object(M, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                        patch.object(M.C, "checkpoint"), patch.object(M.C, "peak_memory", return_value=100),
                        patch.object(M.C, "PEAK", 0), patch.object(M.C, "DEADLINE", None),
                        patch.object(M.C, "head_plan", side_effect=AssertionError("old C1 plan forbidden")),
                        patch.object(M.C, "run", side_effect=AssertionError("old C1 run forbidden"))]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.slots = M.plan()
        self.compressed = gzip.compress(fits_bytes())
        self.calls, self.queue = [], []

    def fixture(self):
        self.queue = [Response(s["method"], s["url"], self.compressed) for s in self.slots]
        M.C.save("run-start.json", {"slots": self.slots})
        return patch("requests.Session", side_effect=lambda: Session(self.queue, self.calls))

    def test_full_head_get_worker_parent_and_replay_no_arrays(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            outcome = M.assess(0)
            self.assertEqual(outcome["status"], M.PASS)
            self.assertEqual([m for m, _ in self.calls], ["HEAD"] * 4 + ["GET"] * 4)
            self.assertEqual(outcome["resource_usage"]["compressed_bytes"], 4 * len(self.compressed))
            self.assertEqual(outcome["resource_usage"]["expanded_bytes"], 4 * len(fits_bytes()))
            self.assertEqual(M.assess(124)["status"], "STOP")
            outcome.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE),
                           parent_peak_memory_bytes=100)
            M.C.save("outcome.json", outcome, terminal=True)
            M.replay()
            self.assertEqual(len(self.calls), 8)
            (self.here / "products/orphan.FTZ").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "STOP_PRODUCT_SET"):
                M.verify_product_set(M.get_plan(self.slots))

    def test_each_head_failure_prevents_all_gets(self):
        for headers, status in (({}, 200), ({"Content-Length": [str(M.RAW_CAP + 1)]}, 200),
                                ({"Content-Length": ["10"]}, 503), ({"Content-Length": ["10", "11"]}, 200)):
            with self.subTest(headers=headers, status=status), tempfile.TemporaryDirectory() as tmp, \
                    patch.object(M, "HERE", Path(tmp)), patch.object(M.C, "HERE", Path(tmp)):
                self.calls = []
                with self.fixture(), patch.object(M, "verify_binding"):
                    self.queue[1] = Response("HEAD", self.slots[1]["url"], b"error body", status, headers)
                    self.assertEqual(M.worker(), 1)
                self.assertEqual([m for m, _ in self.calls], ["HEAD", "HEAD"])
                self.assertEqual([r["status"] for r in M.C.read("worker-result.json")["ledger"]],
                                 ["OK", "FAILED"] + ["NOT_ATTEMPTED"] * 6)

    def test_changed_get_entity_rejected_before_body(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            response = self.queue[4]
            response.values["ETag"] = ['"changed"']
            self.assertEqual(M.worker(), 1)
            self.assertEqual(response.calls, [])
        self.assertEqual(len(self.calls), 5)
        self.assertFalse((self.here / "products").exists())

    def test_get_overflow_retains_only_accepted_bytes(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            response = self.queue[4]
            response.stream = io.BytesIO(self.compressed + b"x")
            self.assertEqual(M.worker(), 1)
        raw = self.here / "products" / M.NAMES[0]
        self.assertEqual(raw.read_bytes(), self.compressed)
        self.assertEqual(sum(response.calls), len(self.compressed) + 1)
        self.assertEqual(M.C.read("slot-5-result.json")["error_code"], "STOP_RAW_BYTE_CAP")

    def test_expansion_cap_preserves_partial_and_counts_existing(self):
        with self.fixture(), patch.object(M, "verify_binding"), patch.object(M.C, "EXPANDED_FILE_CAP", 100):
            self.assertEqual(M.worker(), 1)
        expanded = next((self.here / "products").glob("*.fits"))
        self.assertEqual(expanded.stat().st_size, 100)
        self.assertEqual(M.C.read("slot-5-result.json")["error_code"], "STOP_EXPANDED_BYTE_CAP")

    def test_crc_failure_retains_raw_and_partial(self):
        with self.fixture(), patch.object(M, "verify_binding"):
            corrupt = self.compressed[:-1] + bytes([self.compressed[-1] ^ 1])
            self.queue[4].stream = io.BytesIO(corrupt)
            self.assertEqual(M.worker(), 1)
        self.assertTrue((self.here / "products" / M.NAMES[0]).exists())
        self.assertEqual(len(self.calls), 5)

    def test_all_four_head_gate_and_total_not_partial(self):
        M.C.save("slot-1-http.json", {"method": "HEAD", "url": self.slots[0]["url"], "status": 200,
                                       "headers": {"Content-Length": ["1"]}})
        M.C.save("slot-1-result.json", M.validate_head(self.slots[0], M.C.read("slot-1-http.json")))
        with self.assertRaises(FileNotFoundError):
            M.get_plan(self.slots)

    def test_binding_json_roundtrip_and_config_mutation(self):
        with patch.object(M, "HERE", M.SOURCE.parent), patch.object(M.C, "HERE", M.SOURCE.parent):
            binding = M.binding(M.PROTOCOL)
        self.assertEqual(binding, json.loads(json.dumps(binding)))
        M.C.save("run-start.json", binding)
        with patch.object(M, "binding", return_value={**binding, "configuration": {"memory": 1}}), \
                self.assertRaisesRegex(ValueError, "STOP_BINDING"):
            M.verify_binding()
        self.assertEqual(binding["configuration"]["compressed_caps"], [2097152] * 4)
        self.assertEqual(binding["configuration"]["expanded_file"], 33554432)

    def test_parent_prelaunch_and_partial_marker_all_eight_slots(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_INVENTORY_HASH")):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read("outcome.json")
        self.assertEqual(len(outcome["ledger"]), 8)
        self.assertTrue(all(r["status"] == "NOT_ATTEMPTED" for r in outcome["ledger"]))
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_truncated_marker_failure_artifacts_not_product_verification(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 120)
            self.assertEqual(command[-1], "_worker")
            (self.here / "slot-1-start.json").write_bytes(b'{"slot":')
            return 124, "discarded"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value={"slots": self.slots}), \
                patch.object(M, "verify_binding"), patch.object(M.C, "load_pinned", return_value=SimpleNamespace(bounded_run=timeout)):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read("outcome.json")
        self.assertEqual(outcome["worker_returncode"], 124)
        self.assertEqual(outcome["ledger"][0]["status"], "UNVERIFIED_ATTEMPT")
        M.replay()

    def test_header_collector_ignores_cookie_and_never_head_body(self):
        s = self.slots[0]
        response = Response("HEAD", s["url"], b"forbidden", headers={"Content-Length": ["9"], "Set-Cookie": ["private"]})
        with patch("requests.Session", return_value=Session([response], self.calls)):
            result = M.collect_head(s)
        self.assertEqual(result["body_bytes_read"], 0)
        self.assertNotIn("Set-Cookie", M.C.read("slot-1-http.json")["headers"])
        self.assertEqual(response.calls, [])

    def test_free_space_before_every_request(self):
        with self.fixture(), patch.object(M, "verify_binding"), \
                patch.object(M.shutil, "disk_usage", side_effect=[SimpleNamespace(free=M.FREE_BYTES), SimpleNamespace(free=0)]):
            self.assertEqual(M.worker(), 1)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(M.C.read("worker-result.json")["error_code"], "STOP_FREE_SPACE")


if __name__ == "__main__":
    unittest.main()
