"""Synthetic transfer/gzip/resource/header checks; never accesses live URLs."""

import gzip
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from astropy.io import fits

SPEC = importlib.util.spec_from_file_location("c1_test", Path(__file__).with_name("acquire.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Raw(io.BytesIO):
    def read(self, amount=-1, decode_content=False):
        return super().read(amount)


class AcquireTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.object(M, "HERE", self.root))
        self.stack.enter_context(patch.object(M, "DEADLINE", None))
        self.stack.enter_context(patch.object(M, "PEAK", 0))
        self.stack.enter_context(patch.object(M, "peak_memory", return_value=10000000))
        self.stack.enter_context(patch.object(M.LOGGER, "exception"))
        self.stack.enter_context(patch("builtins.print"))
        for field, name in (("SOURCE", "acquire.py"), ("PROTOCOL", "protocol.md")):
            p = self.root / name
            p.write_text("synthetic frozen dependency\n", encoding="utf-8")
            self.stack.enter_context(patch.object(M, field, p))
        (self.root / "test_acquire.py").write_text("synthetic tests\n", encoding="utf-8")
        header = fits.PrimaryHDU().header
        header["RA_PNT"] = 123.456789
        self.expanded = header.tostring().encode("ascii")
        self.compressed = gzip.compress(self.expanded, mtime=0)
        self.real_plan = M.head_plan
        self.real_expected = M.EXPECTED
        old = M.load_pinned("c1_fixture_names", M.C0D_PATH, M.C0D_HASH)
        self.plan = [{"slot": i, "method": "GET", "url": old.BASE + name, "filename": name,
                     "expected_bytes": len(self.compressed), "head_headers": {"ETag": ['"fixed"'],
                     "Last-Modified": ["Tue, 26 Nov 2024 19:05:23 GMT"]}}
                     for i, name in enumerate(old.NAMES[:4], 1)]
        self.stack.enter_context(patch.object(M, "head_plan", return_value=self.plan))
        self.stack.enter_context(patch.object(M, "EXPECTED", tuple(len(self.compressed) for _ in self.plan)))

    def response(self, slot, *, body=None, etag='"fixed"', status=200, length=None):
        values = {"Content-Length": [str(slot["expected_bytes"] if length is None else length)],
                  "ETag": [etag], "Last-Modified": slot["head_headers"]["Last-Modified"],
                  "Set-Cookie": ["synthetic-secret"]}
        response = MagicMock(status_code=status, url=slot["url"])
        response.request.method = "GET"
        response.raw = Raw(self.compressed if body is None else body)
        response.raw.headers = SimpleNamespace(getlist=lambda k: values.get(k, []))
        response.__enter__.return_value = response
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value = response
        return response, session

    def prepare(self):
        M.save("run-start.json", M.binding(M.PROTOCOL))
        (self.root / "protocol.snapshot.md").write_bytes(M.PROTOCOL.read_bytes())

    def batch(self, *, bad_slot=None):
        self.prepare()
        pairs = [self.response(s, status=503 if s["slot"] == bad_slot else 200) for s in self.plan]
        self.stack.enter_context(patch("requests.Session", side_effect=[p[1] for p in pairs]))
        return M.worker(), pairs

    @unittest.skipUnless(M.C0D_PATH.with_name("summary.html").is_file(),
                         "Requires the original local-only C0d summary for full provenance closure")
    def test_actual_fixed_head_plan_and_dependencies_without_network(self):
        with patch.object(M, "EXPECTED", self.real_expected):
            rows = self.real_plan()
        self.assertEqual([r["expected_bytes"] for r in rows], list(self.real_expected))
        self.assertEqual(sum(self.real_expected), 126982449)
        self.assertEqual(M.sha(M.STRUCTURE_REVIEW), M.STRUCTURE_REVIEW_HASH)

    def test_download_exact_anonymous_entity_without_secret_receipts(self):
        response, session = self.response(self.plan[0])
        with patch("requests.Session", return_value=session):
            M.download(self.plan[0])
        session.get.assert_called_once_with(self.plan[0]["url"], timeout=(5, 15), stream=True,
            allow_redirects=False, headers={"Accept-Encoding": "identity"})
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once_with()
        self.assertEqual(response.raw.tell(), len(self.compressed))
        self.assertNotIn("synthetic-secret", (self.root / "slot-1-http.json").read_text())

    def test_changed_etag_stops_before_any_product_body_read(self):
        response, session = self.response(self.plan[0], etag='"changed"')
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_CHANGED_PRODUCT"):
            M.download(self.plan[0])
        self.assertEqual(response.raw.tell(), 0)
        self.assertFalse(M.paths(self.plan[0])[0].exists())

    def test_raw_cap_plus_one_and_short_entity(self):
        response, session = self.response(self.plan[0], body=self.compressed + b"overflow")
        with patch("requests.Session", return_value=session), self.assertRaisesRegex(ValueError, "STOP_RAW_BYTE_CAP"):
            M.download(self.plan[0])
        self.assertEqual(response.raw.tell(), len(self.compressed) + 1)
        self.assertEqual(M.paths(self.plan[0])[0].stat().st_size, len(self.compressed))

    def compressed_input(self, body):
        raw, _expanded = M.paths(self.plan[0])
        raw.parent.mkdir(exist_ok=True)
        raw.write_bytes(body)

    def test_gzip_crc_eof_and_header_only_structure(self):
        self.compressed_input(self.compressed)
        result = M.expand(self.plan[0])
        self.assertIs(result["gzip_crc_eof_verified"], True)
        report = M.headers(self.plan[0])
        self.assertEqual(report["declared_data_region_bytes_read"], 0)
        self.assertEqual(report["status"], "HEADER_LAYOUT_ONLY")

    def test_bad_gzip_crc_is_never_success(self):
        body = bytearray(self.compressed)
        body[-8] ^= 1
        self.compressed_input(bytes(body))
        with self.assertRaises(gzip.BadGzipFile):
            M.expand(self.plan[0])

    def test_expanded_cap_counts_prior_partial_files(self):
        self.compressed_input(gzip.compress(b"x" * 100))
        (self.root / "products" / "previous.fits").write_bytes(b"p" * 60)
        with patch.object(M, "EXPANDED_FILE_CAP", 80), patch.object(M, "EXPANDED_TOTAL_CAP", 100), \
                self.assertRaisesRegex(ValueError, "STOP_EXPANDED_BYTE_CAP"):
            M.expand(self.plan[0])
        self.assertEqual(M.paths(self.plan[0])[1].stat().st_size, 40)

    def test_header_json_cap_on_serialized_bytes(self):
        with patch.object(M, "HEADER_CAP", 20), self.assertRaisesRegex(ValueError, "STOP_JSON_BUDGET"):
            M.save("headers/slot-1-headers.json", {"cards": ["x" * 30]}, header=True)
        self.assertFalse((self.root / "headers/slot-1-headers.json").exists())

    def test_json_terminal_reserve_and_monitored_memory_failure_receipt(self):
        with patch.object(M, "JSON_CAP", 1000), patch.object(M, "RESERVE", 900):
            with self.assertRaisesRegex(ValueError, "STOP_JSON_BUDGET"):
                M.save("normal.json", {"text": "x" * 200})
            with patch.object(M, "peak_memory", return_value=M.MEMORY_CAP + 1):
                value = {"status": M.PASS}
                M.save("terminal.json", value, terminal=True, peak_key="peak_memory_bytes")
        result = M.read("terminal.json")
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(result["error_code"], "STOP_PEAK_MEMORY")
        self.assertGreater(result["peak_memory_bytes"], M.MEMORY_CAP)

    def test_four_file_worker_parent_replay_and_header_privacy(self):
        code, pairs = self.batch()
        self.assertEqual(code, 0)
        result = M.assess(code)
        self.assertEqual(result["status"], M.PASS)
        self.assertEqual(result["resource_usage"]["expanded_bytes"], len(self.expanded) * 4)
        for _response, session in pairs:
            session.get.assert_called_once()
        for p in self.root.glob("*.json"):
            self.assertNotIn("123.456789", p.read_text())
        self.assertIn("123.456789", (self.root / "headers/slot-1-headers.json").read_text())
        self.assertEqual(M.assess(124)["status"], "STOP")

    def test_first_http_failure_stops_three_later_slots(self):
        code, pairs = self.batch(bad_slot=1)
        self.assertEqual(code, 1)
        self.assertEqual([r["status"] for r in M.assess(code)["ledger"]],
                         ["FAILED", "NOT_ATTEMPTED", "NOT_ATTEMPTED", "NOT_ATTEMPTED"])
        for _response, session in pairs[1:]:
            session.get.assert_not_called()

    def test_worker_resource_snapshot_tampering_rejected(self):
        self.batch()
        p = self.root / "worker-result.json"
        result = json.loads(p.read_bytes())
        result["resource_usage"]["expanded_bytes"] = 0
        p.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "STOP_WORKER_CLOSURE"):
            M.assess(0)

    def test_parent_full_mock_run_and_offline_replay(self):
        pairs = [self.response(s) for s in self.plan]
        original = M.load_pinned
        calls = []

        def load(name, path, digest):
            if path == M.HELPER:
                def bounded(command, timeout):
                    calls.append((command, timeout))
                    return M.worker(), "unpersisted simulated worker output"
                return SimpleNamespace(bounded_run=bounded)
            return original(name, path, digest)

        with patch.object(M, "load_pinned", side_effect=load), \
                patch("requests.Session", side_effect=[p[1] for p in pairs]):
            self.assertEqual(M.run(), 0)
        self.assertEqual(calls[0][1], 300)
        self.assertEqual(calls[0][0][1:], ["-B", str(M.SOURCE), "_worker"])
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_free_space_failure_launches_nothing(self):
        with patch.object(M.shutil, "disk_usage", return_value=SimpleNamespace(free=1)), patch("requests.Session") as session:
            self.assertEqual(M.run(), 1)
            session.assert_not_called()
        self.assertEqual(M.read("outcome.json")["error_code"], "STOP_FREE_SPACE")

    def test_parent_final_serialization_memory_stop_replays_without_promoting_worker(self):
        pairs = [self.response(s) for s in self.plan]
        original_load, original_save = M.load_pinned, M.save

        def load(name, path, digest):
            if path == M.HELPER:
                return SimpleNamespace(bounded_run=lambda command, timeout: (M.worker(), "mock"))
            return original_load(name, path, digest)

        def save(name, value, **kwargs):
            if name == "outcome.json":
                with patch.object(M, "peak_memory", return_value=M.MEMORY_CAP + 1):
                    return original_save(name, value, **kwargs)
            return original_save(name, value, **kwargs)

        with patch.object(M, "load_pinned", side_effect=load), patch.object(M, "save", side_effect=save), \
                patch("requests.Session", side_effect=[p[1] for p in pairs]):
            self.assertEqual(M.run(), 1)
        self.assertEqual(M.read("worker-result.json")["status"], M.PASS)
        self.assertEqual(M.read("outcome.json")["error_code"], "STOP_PEAK_MEMORY")
        M.PEAK = 0  # Replay is normally a separate fresh process.
        M.replay()


if __name__ == "__main__":
    unittest.main()
