"""Synthetic ancillary-table checks; no real payload access."""

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

SPEC = importlib.util.spec_from_file_location("c2", Path(__file__).with_name("inspect_values.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def table(kind="EXPOSU", slot=2, rows=4, offset=64):
    columns = [("START", "D", "s"), ("STOP", "D", "s")] if kind == "STDGTI" else (
        [("TIME", "D", "s"), ("FRACEXP", "E", "fraction")] if slot == 1 else
        [("TIME", "D", "s"), ("TIMEDEL", "E", "s"), ("FRACEXP", "E", "fraction")])
    width = sum(8 if form == "D" else 4 for _, form, _ in columns)
    return {"table": 1, "slot": slot, "ccdnr": 1, "kind": kind, "extname": kind + "01", "columns": columns,
            "rows": rows, "width": width, "data_offset": offset, "data_bytes": rows * width,
            "file_bytes": offset + rows * width + 40, "header_metadata": {"TIMEDEL": 2.0,
             "ONTIME": 9.0, "LIVETIME": 8.0, "EXPOSURE": None}, "events_ccd_livetime": 7.0}


def data(t, rows):
    return np.array(rows, dtype=[(col, ">f8" if form == "D" else ">f4") for col, form, _ in t["columns"]])


class Guard(io.BytesIO):
    def __init__(self, t, payload):
        super().__init__(b"F" * t["data_offset"] + payload + b"X" * 40)
        self.start, self.end = t["data_offset"], t["data_offset"] + len(payload)
        self.sizes = []

    def read(self, size=-1):
        if not self.start <= self.tell() <= self.tell() + size <= self.end:
            raise AssertionError("forbidden array read")
        self.sizes.append(size)
        return super().read(size)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here = Path(self.temp.name)
        self.patches = [patch.object(M, "checkpoint"), patch.object(M, "HERE", self.here),
                        patch.object(M.C, "peak_memory", return_value=100), patch.object(M, "PEAK", 0)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_only_allowed_span_big_endian_chunk_accounting(self):
        t = table()
        a = data(t, [(1, 2, .5), (2, 2, 1), (3, 2, .25), (4, 2, 1)])
        stream, usage = Guard(t, a.tobytes()), {"read_bytes": 0, "interpreted_bytes": 0}
        with patch.object(M, "CHUNK_ROWS", 2):
            result = M.exposure_summary(M.chunks(stream, t, usage), t, [[1, 4]])
        self.assertEqual(stream.sizes, [32, 32])
        self.assertEqual(usage, {"read_bytes": 64, "interpreted_bytes": 64})
        self.assertEqual(result["valid_fraction_weighted_width_sum"], 5.5)
        self.assertEqual(result["gti_member_valid_fraction_weighted_width_sum"], 3.5)
        self.assertEqual(result["gti_member_valid_rows"], 3)

    def test_forbidden_array_never_read(self):
        t = table("EVENTS")
        with self.assertRaisesRegex(ValueError, "STOP_FORBIDDEN_ARRAY"):
            list(M.chunks(io.BytesIO(), t, {"read_bytes": 0, "interpreted_bytes": 0}))

    def test_payload_cap_and_truncation_accounting(self):
        t = table(rows=1, offset=0)
        usage = {"read_bytes": 0, "interpreted_bytes": 0}
        with patch.object(M, "PAYLOAD_CAP", 1), self.assertRaisesRegex(ValueError, "STOP_PAYLOAD_CAP"):
            list(M.chunks(io.BytesIO(b"x" * 16), t, usage))
        self.assertEqual(usage["read_bytes"], 0)
        with self.assertRaisesRegex(ValueError, "STOP_TRUNCATED_TABLE"):
            list(M.chunks(io.BytesIO(b"x" * 9), t, usage))
        self.assertEqual(usage, {"read_bytes": 9, "interpreted_bytes": 0})

    def test_gti_invalid_overlap_and_order(self):
        t = table("STDGTI", rows=6)
        summary, union = M.gti_summary([data(t, [(5, 8), (1, 4), (3, 6), (9, 9), (10, 9), (np.nan, 12)])])
        self.assertEqual(union, [[1, 8]])
        self.assertEqual(summary["rows"], 6)
        self.assertEqual(summary["valid_positive_rows"], 3)
        self.assertEqual(summary["nonpositive_finite_rows"], 2)
        self.assertEqual(summary["nonfinite_rows"], 1)
        self.assertEqual(summary["valid_rows_only_union_duration"], 7)
        self.assertEqual(summary["overlap_rows_in_sorted_valid_intervals"], 2)

    def test_global_duplicates_and_cross_chunk_pairs(self):
        t = table(rows=5)
        a = data(t, [(1, 1, 1), (2, 1, 1), (2, 1, 1), (3, 1, 1), (1, 1, 1)])
        r = M.exposure_summary([a[:2], a[2:4], a[4:]], t, [])
        self.assertEqual(r["global_duplicate_finite_times"], 2)
        self.assertEqual(r["adjacent_duplicate_finite_times"], 1)
        self.assertEqual(r["nonincreasing_adjacent_finite_times"], 2)
        self.assertEqual((r["min_spacing"], r["max_spacing"]), (-2, 1))

    def test_invalid_exposure_rows_retained_not_zeroed(self):
        t = table(rows=6)
        a = data(t, [(0, 1, .5), (1, 0, .5), (2, -1, .5), (3, 1, 1.5), (4, np.nan, .2), (np.nan, 1, .3)])
        r = M.exposure_summary([a], t, [[0, 5]])
        self.assertEqual(r["rows"], 6)
        self.assertEqual(r["valid_rows"], 1)
        self.assertEqual(r["valid_fraction_weighted_width_sum"], .5)
        self.assertEqual(r["nonpositive_finite_widths"], 2)
        self.assertEqual(r["fractions_outside_unit_interval"], 1)
        self.assertIsNone(r["last_time"])
        self.assertIn("nonfinite_widths", r["data_quality_flags"])
        json.dumps(r, allow_nan=False)

    def test_pn_uses_header_width_not_spacing_and_boundaries_half_open(self):
        t = table(slot=1, rows=3)
        a = data(t, [(0, .5), (10, .5), (20, .5)])
        r = M.exposure_summary([a], t, [[0, 10], [20, 21]])
        self.assertEqual(r["valid_width_sum"], 6)
        self.assertEqual(r["valid_fraction_weighted_width_sum"], 3)
        self.assertEqual(r["gti_member_valid_fraction_weighted_width_sum"], 2)
        self.assertEqual(r["max_spacing"], 10)
        self.assertEqual(r["arithmetic_minus_metadata"]["valid_width_sum"]["table_ONTIME"], -3)

    def test_empty_tables_and_nonfinite_endpoints(self):
        r, u = M.gti_summary([])
        self.assertEqual(r["rows"], 0)
        self.assertEqual(u, [])
        r = M.exposure_summary([], table(), [])
        self.assertEqual(r["valid_width_sum"], 0)
        self.assertIsNone(r["first_time"])

    def test_failure_privacy(self):
        self.assertEqual(M.failure(ValueError("raw sensitive cards")), {"status": "STOP", "error_code": "STOP_INTERNAL"})
        self.assertEqual(M.failure(ValueError("STOP_PAYLOAD_CAP"))["error_code"], "STOP_PAYLOAD_CAP")

    def test_terminal_memory_and_reserve(self):
        with patch.object(M, "JSON_CAP", 100), patch.object(M, "RESERVE", 80):
            with self.assertRaisesRegex(ValueError, "STOP_JSON_BUDGET"):
                M.save("regular.json", {"padding": "z" * 30})
            M.save("terminal.json", {"status": "STOP"}, terminal=True)
        r = {"status": M.PASS}
        with patch.object(M.C, "peak_memory", return_value=M.MEMORY_CAP + 1):
            M.save("memory.json", r, terminal=True, peak_key="peak_memory_bytes")
        self.assertEqual(r["error_code"], "STOP_PEAK_MEMORY")
        with self.assertRaises(FileExistsError):
            M.save("memory.json", {})

    def test_ledger_failure_and_interruption_stop_later_launch(self):
        tables = [{"table": i} for i in range(1, 4)]
        M.save("table-1-start.json", {"table": 1, "elapsed_seconds": 1})
        r = M.ledger(tables)
        self.assertEqual([x["status"] for x in r], ["INTERRUPTED", "NOT_ATTEMPTED", "NOT_ATTEMPTED"])
        M.save("table-2-start.json", {"table": 2, "elapsed_seconds": 2})
        with self.assertRaisesRegex(ValueError, "STOP_TABLE_ORDER"):
            M.ledger(tables)

    def test_replay_detects_changed_summary(self):
        t = {"table": 1}
        M.save("table-1-start.json", {"table": 1, "elapsed_seconds": 1})
        M.save("table-1-result.json", {"table": 1, "status": "OK", "interpreted_bytes": 0, "summary": {"rows": 2}})
        with patch.object(M, "measure", return_value={"rows": 1}), self.assertRaisesRegex(ValueError, "STOP_SUMMARY_REPLAY"):
            M.ledger([t], recompute=True)

    def test_nonzero_worker_cannot_promote_success(self):
        with patch.object(M, "verify_binding"), patch.object(M, "verify_c1"), patch.object(M, "ledger", return_value=[]):
            M.save("run-start.json", {"tables": []})
            r = M.assess(124)
        self.assertEqual(r["status"], "STOP")
        self.assertEqual(r["worker_returncode"], 124)

    def test_complete_synthetic_worker_parent_replay_and_accounting_tamper(self):
        g = table("STDGTI", rows=1)
        e = table(rows=3, offset=80)
        g.update(table=1, filename="synthetic.fits", file_bytes=168)
        e.update(table=2, filename="synthetic.fits", file_bytes=168)
        (self.here / "products").mkdir()
        (self.here / "products/synthetic.fits").write_bytes(
            b"X" * 64 + data(g, [(0, 3)]).tobytes() + data(e, [(0, 1, .5), (1, 1, 1), (3, 1, 1)]).tobytes() + b"X" * 40)
        (self.here / "protocol.snapshot.md").write_bytes(b"synthetic protocol")
        M.save("run-start.json", {"tables": [g, e]})
        with patch.object(M, "C1_PATH", self.here / "acquire.py"), patch.object(M, "PAYLOAD_CAP", 64), \
                patch.object(M, "verify_binding"), patch.object(M, "verify_c1"):
            self.assertEqual(M.worker(), 0)
            outcome = M.assess(0)
            self.assertEqual(outcome["status"], M.PASS)
            self.assertEqual(M.assess(124)["status"], "STOP")
            outcome.update(artifacts=M.artifact_hashes(), source_sha256=M.sha(M.SOURCE),
                           snapshot_sha256=M.sha(self.here / "protocol.snapshot.md"), parent_peak_memory_bytes=100)
            M.save("outcome.json", outcome, terminal=True)
            M.replay()
            receipt = M.read("worker-result.json")
            receipt["accounting"]["interpreted_bytes"] -= 1
            (self.here / "worker-result.json").write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "STOP_ACCOUNTING_RECEIPT"):
                M.assess(0)

    def test_parent_prelaunch_failure_all48_and_failure_artifact_replay(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_C1_OUTCOME_HASH")):
            self.assertEqual(M.run(), 1)
        outcome = M.read("outcome.json")
        self.assertEqual(len(outcome["ledger"]), 48)
        self.assertEqual({r["status"] for r in outcome["ledger"]}, {"NOT_ATTEMPTED"})
        self.assertIsNone(outcome["worker_returncode"])
        self.assertFalse(outcome["assessment_completed"])
        M.replay()
        outcome["parent_peak_memory_bytes"] = 0
        (self.here / "outcome.json").write_text(json.dumps(outcome))
        with self.assertRaisesRegex(ValueError, "STOP_PARENT_MEMORY_RECEIPT"):
            M.replay()

    def test_parent_partial_marker_failure_is_not_reparsed_and_remains_retained(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def killed_worker(command, seconds):
            self.assertEqual(seconds, 120)
            self.assertEqual(command[-1], "_worker")
            (self.here / "table-1-start.json").write_bytes(b'{"table":')
            return 124, "discarded worker output"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value={"tables": []}), \
                patch.object(M.C, "load_pinned", return_value=SimpleNamespace(bounded_run=killed_worker)), \
                patch.object(M, "assess", side_effect=ValueError("STOP_TABLE_RECEIPT")):
            self.assertEqual(M.run(), 1)
        outcome = M.read("outcome.json")
        self.assertEqual(outcome["worker_returncode"], 124)
        self.assertEqual(outcome["ledger"][0]["status"], "UNVERIFIED_ATTEMPT")
        self.assertEqual(len(outcome["ledger"]), 48)
        self.assertEqual((self.here / "table-1-start.json").read_bytes(), b'{"table":')
        M.replay()

    def test_actual_manifest_headers_only(self):
        if not M.C1_PATH.with_name("headers").exists():
            self.skipTest("Local ignored C1 headers required; no real payload access")
        real_open = Path.open

        def guard(path, *args, **kwargs):
            if "products" in path.parts:
                raise AssertionError("manifest must not open product arrays")
            return real_open(path, *args, **kwargs)

        with patch.object(Path, "open", guard):
            plan = M.manifest()
            with patch.object(M, "HERE", M.SOURCE.parent):
                binding = M.binding(M.PROTOCOL)
        self.assertEqual(json.loads(json.dumps(binding)), binding)
        self.assertEqual(len(plan), 48)
        self.assertEqual(sum(t["data_bytes"] for t in plan), 97029016)
        self.assertEqual([t["ccdnr"] for t in plan if t["slot"] == 2 and t["kind"] == "STDGTI"], [1, 2, 4, 5, 7])


if __name__ == "__main__":
    unittest.main()
