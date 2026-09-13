"""Synthetic C6 one-product contract and retained-prior receipt-only checks."""

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

import numpy as np
from astropy.io import fits

SPEC = importlib.util.spec_from_file_location("c6", Path(__file__).with_name("acquire.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture(**changes):
    hdu = fits.PrimaryHDU(np.ones((4, 5), dtype=np.float32))
    hdu.header["OBS_ID"], hdu.header["INSTRUME"], hdu.header["EXPIDSTR"] = "0884250101", "EMOS2", "S002"
    for key, value in changes.items():
        hdu.header[key] = value
    stream = io.BytesIO()
    hdu.writeto(stream)
    return stream.getvalue()


class Response:
    def __init__(self, body):
        self.request, self.url, self.status_code = SimpleNamespace(method="GET"), M.URL, 200
        self.values = {"Content-Type": ["image/fits"], "Content-Disposition": [f'inline; filename="{M.EXPECTED}"'],
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
        assert (method, url) == ("GET", M.URL)
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
        self.fits = fixture()
        self.response, self.calls = Response(self.fits), []
        raw = self.here / "products" / M.EXPECTED
        patches = [patch.object(M, "HERE", self.here), patch.object(M.T, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                   patch.object(M.T, "RAW", raw), patch.object(M.T, "EXPANDED", raw.with_suffix(".fits")),
                   patch.object(M.C, "checkpoint"), patch.object(M.C, "peak_memory", return_value=100),
                   patch.object(M.C, "PEAK", 0), patch.object(M.C, "DEADLINE", None),
                   patch("requests.Session", side_effect=lambda: Session(self.response, self.calls)),
                   patch.object(M.T, "worker", side_effect=AssertionError("old worker forbidden")),
                   patch.object(M.T, "run", side_effect=AssertionError("old run forbidden")),
                   patch.object(M.T, "prior_evidence", side_effect=AssertionError("old ATT prior forbidden")),
                   patch.object(M.C, "head_plan", side_effect=AssertionError("old plan forbidden")),
                   patch.object(M.C, "run", side_effect=AssertionError("old C1 run forbidden"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def complete(self, kind):
        M.C.save("run-start.json", {"slot": M.T.SLOT})
        with patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            self.assertEqual(result["status"], M.PASS)
            self.assertEqual(M.assess(124)["status"], "STOP")
            result.update(assessment_completed=True, artifacts=M.T.artifacts(), source_sha256=M.C.sha(M.SOURCE), parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            M.replay()
        record = M.C.read("request-result.json")
        self.assertEqual(record["actual_format"], kind)
        self.assertEqual(record["map_identity"]["shape_rows_columns"], [4, 5])
        self.assertEqual(record["map_identity"]["instrument"], "EMOS2")
        self.assertFalse(record["arrays_interpreted"])
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn("private", (self.here / "http.json").read_text())

    def test_raw_fits_missing_length_full_worker_parent_replay(self):
        self.complete("RAW_FITS")

    def test_gzip_missing_length_full_worker_parent_replay(self):
        self.response = Response(gzip.compress(self.fits))
        self.complete("GZIP_WRAPPED_FITS")

    def test_http_403_404_redirect_and_wrong_url_stop_before_body(self):
        for status in (302, 403, 404):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
                self.response = Response(self.fits)
                self.response.status_code = status
                with self.assertRaisesRegex(ValueError, "STOP_HTTP_IDENTITY_OR_STATUS"):
                    M.T.download()
                self.assertEqual(self.response.reads, [])
        with tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
            self.response = Response(self.fits)
            self.response.url = M.URL.replace("instname=M2", "instname=M1")
            with self.assertRaisesRegex(ValueError, "STOP_HTTP_IDENTITY_OR_STATUS"):
                M.T.download()
            self.assertEqual(self.response.reads, [])

    def test_wrong_entity_package_disposition_and_duplicate_headers_stop_before_body(self):
        cases = [("Content-Disposition", ['inline; filename="P0884250101M1S001EXPMAP8000.FTZ"']),
                 ("Content-Disposition", ['attachment; filename="0884250101.tar"']),
                 ("Content-Disposition", ['inline; filename="../private.FTZ"']),
                 ("Content-Disposition", ["inline; filename*=UTF-8''file.FTZ"]),
                 ("Content-Disposition", []), ("Content-Type", ["application/x-tar"]),
                 ("Content-Type", ["text/html"]), ("Content-Encoding", ["gzip"]),
                 ("Content-Length", ["1", "2"]), ("Content-Length", ["0"]),
                 ("Content-Length", [str(M.CAP + 1)])]
        for key, values in cases:
            with self.subTest(key=key, values=values), tempfile.TemporaryDirectory() as tmp, patch.object(M.C, "HERE", Path(tmp)):
                self.response = Response(self.fits)
                self.response.values[key] = values
                with self.assertRaises(ValueError):
                    M.T.download()
                self.assertEqual(self.response.reads, [])

    def test_optional_length_exact_duplicate_and_truncation(self):
        self.response.values["Content-Length"] = [str(len(self.fits)), "0" + str(len(self.fits))]
        M.T.download()
        self.assertEqual(M.T.RAW.stat().st_size, len(self.fits))
        self.assertEqual(M.T.validate_http(M.C.read("http.json")), len(self.fits))

    def test_raw_cap_one_overflow_byte_not_retained(self):
        self.response = Response(b"x" * (M.CAP + 10))
        with self.assertRaisesRegex(ValueError, "STOP_RAW_BYTE_CAP"):
            M.T.download()
        self.assertEqual(M.T.RAW.stat().st_size, M.CAP)
        self.assertEqual(self.response.stream.tell(), M.CAP + 1)

    def test_gzip_crc_and_expanded_cap_preserve_partial(self):
        damaged = bytearray(gzip.compress(self.fits))
        damaged[-8] ^= 1
        self.response = Response(bytes(damaged))
        M.T.download()
        with self.assertRaises(gzip.BadGzipFile):
            M.T.expand()
        self.assertTrue(M.T.RAW.exists())
        self.assertTrue(M.T.EXPANDED.exists())

    def test_expanded_cap_stops_and_preserves_exact_cap(self):
        self.response = Response(gzip.compress(self.fits))
        M.T.download()
        with patch.object(M.C, "EXPANDED_FILE_CAP", 100), self.assertRaisesRegex(ValueError, "STOP_EXPANDED_BYTE_CAP"):
            M.T.expand()
        self.assertEqual(M.T.EXPANDED.stat().st_size, 100)

    def test_wrong_header_entity_stops_preserving_body_headers(self):
        self.response = Response(fixture(INSTRUME="EMOS1"))
        M.C.save("run-start.json", {})
        with patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 1)
            result = M.assess(1)
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(M.C.read("request-result.json")["error_code"], "STOP_MAP_ENTITY")
        self.assertTrue((self.here / M.T.HEADER_NAME).exists())
        self.assertTrue(M.T.RAW.exists())

    def test_map_identity_shapes_duplicates_and_extra_hdu(self):
        M.T.download()
        M.T.expand()
        report = M.C.headers(M.T.SLOT)
        for field, value in (("OBS_ID", "other"), ("EXPIDSTR", "S001"), ("BITPIX", 16), ("NAXIS", 0), ("NAXIS1", 0)):
            changed = copy.deepcopy(report)
            h = fits.Header.fromstring("".join(changed["hdus"][0]["cards"]))
            h[field] = value
            changed["hdus"][0]["cards"] = [h.tostring()]
            with self.subTest(field=field), self.assertRaises(ValueError):
                M.map_identity(changed)
        changed = copy.deepcopy(report)
        h = fits.Header.fromstring("".join(changed["hdus"][0]["cards"]))
        h.append(("INSTRUME", "EMOS2"))
        changed["hdus"][0]["cards"] = [h.tostring()]
        with self.assertRaisesRegex(ValueError, "STOP_MAP_HEADER_AMBIGUITY"):
            M.map_identity(changed)
        with self.assertRaisesRegex(ValueError, "STOP_MAP_HDU_IDENTITY"):
            M.map_identity({**report, "hdu_count": 2, "hdus": report["hdus"] * 2})

    def test_parent_header_replay_and_exact_product_set(self):
        M.C.save("run-start.json", {})
        with patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            with patch.object(M.C, "headers", return_value={}), self.assertRaisesRegex(ValueError, "STOP_HEADER_REPLAY"):
                M.assess(0)
            (M.T.RAW.parent / "extra.bin").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "STOP_FALSE_SUCCESS_OR_PRODUCT_SET"):
                M.assess(0)

    def test_binding_roundtrip_exact_selector_and_no_att_prior(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic protocol")
        with patch.object(M, "HERE", M.SOURCE.parent), patch.object(M.C, "HERE", M.SOURCE.parent), \
                patch.object(M, "prior_evidence", return_value={"state": "synthetic prior"}):
            value = M.binding(protocol)
        self.assertEqual(value, json.loads(json.dumps(value)))
        self.assertEqual(value["slot"]["filename"], M.EXPECTED)
        self.assertIn("instname=M2&expflag=S&expno=002&name=EXPMAP&datasubsetno=8", value["slot"]["url"])
        self.assertNotIn("ATTTSR", value["slot"]["url"])
        self.assertEqual(value["configuration"]["raw_caps"], [2097152])

    def test_prelaunch_failure_exclusive_and_failed_artifact_replay(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_DEPENDENCY_HASH")):
            self.assertEqual(M.run(), 1)
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_full_parent_worker_only_one_get(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def bounded(command, seconds):
            self.assertEqual(command[-1], "_worker")
            self.assertEqual(seconds, 60)
            return M.worker(), "discarded private text"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value={"slot": M.T.SLOT}), \
                patch.object(M, "verify_binding"), patch.object(M.C, "load_pinned", wraps=M.C.load_pinned) as loader:
            original = M.C.load_pinned._mock_wraps
            loader.side_effect = lambda name, path, digest: SimpleNamespace(bounded_run=bounded) if name == "c6_deadline" else original(name, path, digest)
            self.assertEqual(M.run(), 0)
            M.replay()
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn("private", (self.here / "outcome.json").read_text())

    def test_late_parent_memory_failure_preserves_worker_success(self):
        M.C.save("run-start.json", {"slot": M.T.SLOT})
        with patch.object(M, "verify_binding"):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            result.update(assessment_completed=True, artifacts=M.T.artifacts(), source_sha256=M.C.sha(M.SOURCE))
            with patch.object(M.C, "peak_memory", return_value=M.C.MEMORY_CAP + 1):
                M.C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
            self.assertEqual(result["status"], "STOP")
            self.assertEqual(result["worker_returncode"], 0)
            M.replay()

    def test_actual_prior_receipts_only_no_product_open(self):
        run = M.C3_PATH.with_name("run-start.json")
        if not run.exists() or not M.C5_PATH.exists():
            self.skipTest("Retained local prior receipts unavailable")
        runtime = json.loads(run.read_bytes())["runtime"]
        if runtime["executable"] != str(Path(sys.executable).resolve()) or runtime["python"] != sys.version:
            self.skipTest("Frozen original C3 replay requires exact owner runtime")
        original = Path.open

        def guarded(path, *args, **kwargs):
            if "products" in path.parts:
                raise AssertionError("prior product read forbidden")
            return original(path, *args, **kwargs)

        with patch.object(Path, "open", guarded), patch("requests.Session", side_effect=AssertionError("network forbidden")):
            value = M.prior_evidence()
        self.assertEqual(value["c3_state"], "STOP_MOS2_HEAD_404_PRESERVED")
        self.assertEqual(value["c5_action"], "hash_only_no_numerical_replay")

    def test_timeout_partial_marker_preserves_unknown_attempt(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 60)
            self.assertEqual(command[-1], "_worker")
            (self.here / "request-start.json").write_bytes(b'{"slot":')
            return 124, "discarded"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value={"slot": M.T.SLOT}), \
                patch.object(M, "verify_binding"), patch.object(M.C, "load_pinned", return_value=SimpleNamespace(bounded_run=timeout)):
            self.assertEqual(M.run(), 1)
        self.assertEqual(M.C.read("outcome.json")["worker_returncode"], 124)
        self.assertEqual(M.C.read("outcome.json")["ledger"], [{"slot": 1, "status": "UNVERIFIED_ATTEMPT"}])
        M.replay()


if __name__ == "__main__":
    unittest.main()
