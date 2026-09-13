"""Synthetic one-GET transport, format and bounded header-only replay tests."""

import gzip
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from astropy.io import fits

SPEC = importlib.util.spec_from_file_location("c3d", Path(__file__).with_name("acquire.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Response:
    def __init__(self, body):
        self.request, self.url, self.status_code = SimpleNamespace(method="GET"), M.P.URL, 200
        self.values = {"Content-Type": ["image/fits"], "Content-Disposition": [f'inline; filename="{M.P.EXPECTED}"'],
                       "Set-Cookie": ["private"]}
        self.stream, self.reads = io.BytesIO(body), []
        self.raw = SimpleNamespace(headers=SimpleNamespace(getlist=lambda k: self.values.get(k, [])), read=self.read)

    def read(self, size, *, decode_content):
        assert decode_content is False and 0 < size <= M.C.CHUNK
        self.reads.append(size)
        return self.stream.read(size)

    def forbidden(self, *args, **kwargs):
        raise AssertionError("unbounded body access forbidden")

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
        assert (method, url) == ("GET", M.P.URL)
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
        self.here = Path(self.temp.name)
        stream = io.BytesIO()
        fits.PrimaryHDU().writeto(stream)
        self.fits = stream.getvalue()
        self.response, self.calls = Response(self.fits), []
        raw = self.here / "products" / M.P.EXPECTED
        expanded = raw.with_suffix(".fits")
        patches = [patch.object(M, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                   patch.object(M, "RAW", raw), patch.object(M, "EXPANDED", expanded),
                   patch.object(M.C, "checkpoint"), patch.object(M.C, "peak_memory", return_value=100),
                   patch.object(M.C, "PEAK", 0), patch.object(M.C, "DEADLINE", None),
                   patch("requests.Session", side_effect=lambda: Session(self.response, self.calls)),
                   patch.object(M.C, "head_plan", side_effect=AssertionError("old plan forbidden")),
                   patch.object(M.C, "run", side_effect=AssertionError("old run forbidden"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def complete(self, kind):
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
        record = M.C.read("request-result.json")
        self.assertEqual(record["actual_format"], kind)
        self.assertEqual(record["hdu_count"], 1)
        self.assertFalse(record["arrays_interpreted"])
        self.assertEqual(M.EXPANDED.read_bytes(), self.fits)
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn("private", (self.here / "http.json").read_text())
        self.assertNotIn("Content-Length", M.C.read("http.json")["headers"])
        return record

    def test_raw_fits_missing_length_full_worker_assess_replay(self):
        record = self.complete("RAW_FITS")
        self.assertTrue(record["raw_fits_copy_hash_equal"])
        self.assertIsNone(record["gzip_crc_eof_verified"])

    def test_gzip_missing_length_full_worker_assess_replay(self):
        self.response = Response(gzip.compress(self.fits))
        record = self.complete("GZIP_WRAPPED_FITS")
        self.assertTrue(record["gzip_crc_eof_verified"])
        self.assertIsNone(record["raw_fits_copy_hash_equal"])

    def test_optional_length_duplicate_decimal_matches_actual(self):
        self.response.values["Content-Length"] = ["02880", "2880"]
        M.download()
        self.assertEqual(M.RAW.stat().st_size, 2880)
        self.assertEqual(M.validate_http(M.C.read("http.json")), 2880)

    def test_optional_length_longer_than_body_stops_retains_body(self):
        self.response.values["Content-Length"] = ["2881"]
        with self.assertRaisesRegex(ValueError, "STOP_ACTUAL_LENGTH"):
            M.download()
        self.assertEqual(M.RAW.stat().st_size, 2880)

    def test_optional_length_shorter_stops_after_one_overflow_byte(self):
        self.response.values["Content-Length"] = ["100"]
        with self.assertRaisesRegex(ValueError, "STOP_RAW_BYTE_CAP"):
            M.download()
        self.assertEqual(M.RAW.stat().st_size, 100)
        self.assertEqual(self.response.stream.tell(), 101)

    def test_unknown_length_cap_retains_exact_cap_plus_one_read(self):
        self.response = Response(self.fits + b"0" * M.CAP)
        with self.assertRaisesRegex(ValueError, "STOP_RAW_BYTE_CAP"):
            M.download()
        self.assertEqual(M.RAW.stat().st_size, M.CAP)
        self.assertEqual(self.response.stream.tell(), M.CAP + 1)

    def test_hostile_metadata_rejected_before_body(self):
        cases = [("Content-Length", ["0"]), ("Content-Length", ["1", "2"]),
                 ("Content-Length", [str(M.CAP + 1)]), ("Content-Encoding", ["gzip"]),
                 ("Content-Type", ["application/json"]), ("Content-Type", ["application/x-tar"]),
                 ("Content-Disposition", ['inline; filename="0884250101.tar"']),
                 ("Content-Disposition", ["inline; filename*=UTF-8''file.FTZ"])]
        for key, value in cases:
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
                self.response = Response(self.fits)
                self.response.values[key] = value
                with self.assertRaises(ValueError):
                    M.download()
                self.assertEqual(self.response.reads, [])
        for status in (302, 404):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
                self.response = Response(self.fits)
                self.response.status_code = status
                with self.assertRaisesRegex(ValueError, "STOP_HTTP_IDENTITY_OR_STATUS"):
                    M.download()
                self.assertEqual(self.response.reads, [])

    def test_unknown_magic_not_extracted_or_parsed(self):
        self.response = Response(b"PK\x03\x04not FITS")
        M.download()
        with self.assertRaisesRegex(ValueError, "STOP_RAW_SIGNATURE"):
            M.expand()
        self.assertFalse(M.EXPANDED.exists())

    def test_gzip_crc_failure_preserves_raw_and_partial(self):
        data = bytearray(gzip.compress(self.fits))
        data[-8] ^= 1
        self.response = Response(bytes(data))
        M.download()
        with self.assertRaises(gzip.BadGzipFile):
            M.expand()
        self.assertEqual(M.RAW.read_bytes(), bytes(data))
        self.assertTrue(M.EXPANDED.exists())

    def test_expanded_cap_preserves_partial(self):
        self.response = Response(gzip.compress(self.fits))
        M.download()
        with patch.object(M.C, "EXPANDED_FILE_CAP", 100), self.assertRaisesRegex(ValueError, "STOP_EXPANDED_BYTE_CAP"):
            M.expand()
        self.assertEqual(M.EXPANDED.stat().st_size, 100)

    def test_binding_roundtrip_and_prior_module_isolation(self):
        self.assertIsNot(M.P.C, M.C)
        self.assertEqual(M.P.C.HERE, M.PRIOR_PATH.parent)
        self.assertEqual(M.P.C.SECONDS, 30)
        with patch.object(M, "HERE", M.SOURCE.parent), patch.object(M.C, "HERE", M.SOURCE.parent), \
                patch.object(M, "prior_evidence", return_value={"status": "synthetic prior STOP"}):
            binding = M.binding(M.PROTOCOL)
        self.assertEqual(binding, json.loads(json.dumps(binding)))
        self.assertEqual(binding["configuration"]["raw_caps"], [2097152])
        M.C.save("run-start.json", binding)
        with patch.object(M, "binding", return_value={**binding, "runtime": {}}), self.assertRaisesRegex(ValueError, "STOP_BINDING"):
            M.verify_binding()

    def test_failed_receipt_values_and_extra_raw_text_rejected(self):
        M.C.save("request-start.json", {"slot": M.SLOT, "elapsed_seconds": 1})
        for bad in ({"error_code": "unsafe text"}, {"error_type": "unsafe text"}, {"raw": "unsafe text"}):
            record = {"slot": M.SLOT, "status": "FAILED", "error_type": "ValueError", "error_code": "STOP_INTERNAL", **bad}
            with patch.object(M.C, "read", side_effect=lambda name, r=record: r if name == "request-result.json" else
                              {"slot": M.SLOT, "elapsed_seconds": 1}), patch.object(Path, "exists", return_value=True), \
                    self.assertRaisesRegex(ValueError, "STOP_FAILED_RECEIPT"):
                M.ledger()

    def test_parent_product_set_and_header_replay(self):
        M.C.save("run-start.json", {})
        with patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            with patch.object(M.C, "headers", return_value={}), self.assertRaisesRegex(ValueError, "STOP_HEADER_REPLAY"):
                M.assess(0)
            (M.RAW.parent / "extra.bin").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "STOP_FALSE_SUCCESS_OR_PRODUCT_SET"):
                M.assess(0)

    def test_prelaunch_failure_and_timeout_marker_all_accounted(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_DEPENDENCY_HASH")):
            self.assertEqual(M.run(), 1)
        self.assertEqual(M.C.read("outcome.json")["ledger"], [{"slot": 1, "status": "NOT_ATTEMPTED"}])
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_timeout_partial_marker_preserved(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 60)
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
