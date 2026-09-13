"""Synthetic attitude payloads only; actual manifest smoke reads headers only."""

import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from astropy.io.fits import Header

SPEC = importlib.util.spec_from_file_location("c4", Path(__file__).with_name("inspect_values.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def report():
    primary = Header()
    primary["OBS_ID"] = "0884250101"
    for key, value in {"NATT": M.ROWS, "NGAHF": M.ROWS, "NGOM": M.ROWS, "NGAHFOM": 0}.items():
        primary[key] = value
    h = Header()
    for key, value in {"XTENSION": "BINTABLE", "BITPIX": 8, "NAXIS": 2, "NAXIS1": 80, "NAXIS2": M.ROWS,
                       "PCOUNT": 0, "GCOUNT": 1, "TFIELDS": 10}.items():
        h[key] = value
    for i, name in enumerate(("TIME", "AHFRA", "AHFDEC", "AHFPA", "OMRA", "OMDEC", "OMPA", "DAHFPNT", "DOMPNT", "DAHFOM"), 1):
        h[f"TTYPE{i}"], h[f"TFORM{i}"], h[f"TUNIT{i}"] = name, "D", "sec" if i == 1 else "degrees"
    return {"file_bytes": 4173120, "hdu_count": 2, "hdus": [
        {"extname": "PRIMARY", "cards": [primary.tostring()]},
        {"extname": "ATTHK", "data_offset": 14400, "data_bytes": M.PAYLOAD, "cards": [h.tostring()]}]}


class BoundedStream(io.BytesIO):
    def __init__(self, raw):
        super().__init__(raw)
        self.reads = []

    def read(self, size=-1):
        assert 0 < size <= M.CHUNK_ROWS * M.WIDTH
        assert self.tell() >= 14400
        self.reads.append((self.tell(), size))
        return super().read(size)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here = Path(self.temp.name)
        self.table = M.att_table(report())
        self.plan = {"table": self.table, "camera_ranges": [{"camera": "EPN", "start": 0, "stop": 50000}]}
        self.start = {"manifest": self.plan}
        self.data = np.zeros((M.ROWS, 10), dtype=">f8")
        self.data[:, 0] = np.arange(M.ROWS)
        self.data[:, [1, 4]] = 123.456789
        self.data[:, [2, 5]] = -37.123456
        self.data[:, [3, 6]] = 270.123456
        self.product = self.here / "synthetic.bin"
        self.product.write_bytes(b"X" * 14400 + self.data.tobytes() + b"trailing forbidden")
        patches = [patch.object(M, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                   patch.object(M, "PRODUCT", self.product), patch.object(M.C, "checkpoint"),
                   patch.object(M.C, "peak_memory", return_value=100), patch.object(M.C, "PEAK", 0),
                   patch.object(M.C, "DEADLINE", None), patch("requests.Session", side_effect=AssertionError("network forbidden")),
                   patch.object(M.P, "worker", side_effect=AssertionError("old worker forbidden")),
                   patch.object(M.P, "run", side_effect=AssertionError("old run forbidden")),
                   patch.object(M.C, "head_plan", side_effect=AssertionError("old plan forbidden"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_decode_exact_big_endian_span_chunk_and_no_other_bytes(self):
        stream = BoundedStream(self.product.read_bytes())
        accounting = {"read_bytes": 0, "decoded_bytes": 0}
        actual = M.decode(stream, self.table, accounting)
        np.testing.assert_array_equal(actual, self.data)
        self.assertEqual(accounting, {"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD})
        self.assertEqual(len(stream.reads), 6)
        self.assertEqual(stream.tell(), 14400 + M.PAYLOAD)

    def test_short_chunk_records_read_and_preceding_decoded(self):
        raw = self.product.read_bytes()[:14400 + M.CHUNK_ROWS * 80 + 17]
        accounting = {"read_bytes": 0, "decoded_bytes": 0}
        with self.assertRaisesRegex(ValueError, "STOP_TRUNCATED_TABLE"):
            M.decode(BoundedStream(raw), self.table, accounting)
        self.assertEqual(accounting, {"read_bytes": 800017, "decoded_bytes": 800000})

    def test_forbidden_array_span_and_exhausted_budget(self):
        for key, value in (("extname", "EVENTS"), ("data_offset", 0), ("width", 79), ("rows", 1)):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "STOP_FORBIDDEN_ARRAY_OR_SPAN"):
                M.decode(BoundedStream(b""), {**self.table, key: value}, {"read_bytes": 0, "decoded_bytes": 0})
        with self.assertRaisesRegex(ValueError, "STOP_PAYLOAD_CAP"):
            M.decode(BoundedStream(self.product.read_bytes()), self.table, {"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD})

    def test_schema_scaling_null_heap_unit_and_column_mutations(self):
        for key, value in (("TSCAL1", 1), ("TZERO2", 0), ("TNULL1", 0), ("TDIM2", "(1)"),
                           ("THEAP", 0), ("TUNIT2", "rad"), ("TFORM2", "E"), ("TTYPE2", "other"), ("TIMEREF", "LOCAL")):
            data = report()
            h = M.header(data["hdus"][1])
            h[key] = value
            data["hdus"][1]["cards"] = [h.tostring()]
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.att_table(data)

    def test_duplicate_semantic_key_stops_without_echo(self):
        h = Header()
        h.append(("NAXIS1", 80))
        h.append(("NAXIS1", 80))
        with self.assertRaisesRegex(ValueError, "STOP_HEADER_AMBIGUITY"):
            M.header({"cards": [h.tostring()]})

    def test_camera_identity_time_and_unique_event(self):
        h = Header()
        for key, value in {"OBS_ID": "0884250101", "INSTRUME": "EPN", "EXPIDSTR": "S003", "TIMESYS": "TT",
                           "TIMEUNIT": "s", "MJDREF": 50814., "TIMEZERO": 0, "TSTART": 1., "TSTOP": 2.}.items():
            h[key] = value
        data = {"hdus": [{"extname": "EVENTS", "cards": [h.tostring()]}]}
        self.assertEqual(M.camera_range(data, "EPN", "S003"), {"camera": "EPN", "start": 1., "stop": 2.})
        with self.assertRaisesRegex(ValueError, "STOP_EVENTS_COUNT"):
            M.camera_range({"hdus": data["hdus"] * 2}, "EPN", "S003")
        h["TIMEZERO"] = 1
        data["hdus"][0]["cards"] = [h.tostring()]
        with self.assertRaisesRegex(ValueError, "STOP_CAMERA_TIME_REFERENCE"):
            M.camera_range(data, "EPN", "S003")

    def test_full_worker_assess_replay_three_distinct_payload_passes(self):
        M.C.save("run-start.json", self.start)
        original = M.measure
        passes = []

        def measure(plan, accounting):
            result = original(plan, accounting)
            passes.append(dict(accounting))
            return result

        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), patch.object(M, "measure", side_effect=measure):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            self.assertEqual(result["status"], M.PASS)
            result.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE),
                          parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            M.replay()
        self.assertEqual(passes, [{"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD}] * 3)
        text = "".join(p.read_text() for p in self.here.glob("*.json"))
        for secret in ("123.456789", "-37.123456", "270.123456"):
            self.assertNotIn(secret, text)
        summary = M.C.read("table-result.json")["summary"]
        self.assertEqual(summary["status"], "SAMPLED_ATTITUDE_DIAGNOSTICS_NOT_COVERAGE")
        self.assertFalse(summary["continuous_motion_bound_established"])

    def test_nonzero_worker_cannot_promote_and_accounting_tamper(self):
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"):
            self.assertEqual(M.worker(), 0)
            self.assertEqual(M.assess(124)["status"], "STOP")
            old = M.C.read
            record = copy.deepcopy(old("table-result.json"))
            record["accounting"]["decoded_bytes"] -= 80
            with patch.object(M.C, "read", side_effect=lambda n: record if n == "table-result.json" else old(n)), \
                    self.assertRaisesRegex(ValueError, "STOP_SUCCESS_ACCOUNTING"):
                M.assess(0)

    def test_failure_retains_partial_byte_accounting_and_no_raw_exception(self):
        self.product.write_bytes(self.product.read_bytes()[:14417])
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"):
            self.assertEqual(M.worker(), 1)
            result = M.assess(1)
        self.assertEqual(result["ledger"][0]["accounting"], {"read_bytes": 17, "decoded_bytes": 0})
        self.assertEqual(M.C.read("table-result.json")["error_code"], "STOP_TRUNCATED_TABLE")

    def test_actual_headers_only_manifest_json_roundtrip(self):
        if not (M.PRIOR_PATH.parent / "headers/slot-1-headers.json").exists():
            self.skipTest("Local ignored header reports required; synthetic schema checks remain mandatory")
        # Product is synthetic and must never be opened by this manifest call.
        with patch.object(M, "PRODUCT", M.P.EXPANDED):
            actual = M.manifest()
        self.assertEqual(actual, json.loads(json.dumps(actual)))
        self.assertEqual(actual["table"]["rows"], 51975)
        self.assertEqual([r["camera"] for r in actual["camera_ranges"]], ["EPN", "EMOS1", "EMOS2"])

    def test_binding_isolation_roundtrip_and_mutation(self):
        self.assertIsNot(M.P.C, M.C)
        self.assertEqual(M.P.C.HERE, M.PRIOR_PATH.parent)
        with patch.object(M, "HERE", M.SOURCE.parent), patch.object(M.C, "HERE", M.SOURCE.parent), \
                patch.object(M, "manifest", return_value=self.plan):
            binding = M.binding(M.PROTOCOL)
        self.assertEqual(binding, json.loads(json.dumps(binding)))
        M.C.save("run-start.json", binding)
        with patch.object(M, "binding", return_value={**binding, "runtime": {}}), self.assertRaisesRegex(ValueError, "STOP_BINDING"):
            M.verify_binding()

    def test_prelaunch_failure_exclusive_and_safe_failure_replay(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_DEPENDENCY_HASH")):
            self.assertEqual(M.run(), 1)
        self.assertEqual(M.C.read("outcome.json")["ledger"], [{"table": 1, "status": "NOT_ATTEMPTED"}])
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_completion_flag_requires_boolean(self):
        for value in ("not a boolean", 0, 1, None, []):
            with self.subTest(value=value), patch.object(M.C, "read", return_value={"assessment_completed": value}), \
                    self.assertRaisesRegex(ValueError, "STOP_ASSESSMENT_FLAG"):
                M.replay()

    def test_orphan_attempt_markers_refused_before_binding(self):
        for name in ("worker-start.json", "worker-result.json", "table-start.json", "table-result.json", "protocol.snapshot.md"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp, patch.object(M, "HERE", Path(tmp)), \
                    patch.object(M, "binding", side_effect=AssertionError("binding must not run")):
                (Path(tmp) / name).write_bytes(b"partial")
                with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
                    M.run()

    def test_late_parent_memory_stop_retained_by_replay(self):
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            result.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE))
            with patch.object(M.C, "peak_memory", return_value=M.C.MEMORY_CAP + 1):
                M.C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
            self.assertEqual(result["status"], "STOP")
            self.assertEqual(result["worker_returncode"], 0)
            self.assertEqual(result["error_code"], "STOP_PEAK_MEMORY")
            M.replay()

    def test_timeout_truncated_marker_preserved(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 60)
            self.assertEqual(command[-1], "_worker")
            (self.here / "table-start.json").write_bytes(b'{"table":')
            return 124, "discarded private text"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value=self.start), \
                patch.object(M, "verify_binding"), patch.object(M.C, "load_pinned", return_value=SimpleNamespace(bounded_run=timeout)):
            self.assertEqual(M.run(), 1)
        result = M.C.read("outcome.json")
        self.assertEqual(result["worker_returncode"], 124)
        self.assertEqual(result["ledger"], [{"table": 1, "status": "UNVERIFIED_ATTEMPT"}])
        self.assertNotIn("private", (self.here / "outcome.json").read_text())
        M.replay()


if __name__ == "__main__":
    unittest.main()
