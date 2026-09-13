"""Synthetic one-map composition, exact caps, callback isolation and replay."""

import contextlib
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

SPEC = importlib.util.spec_from_file_location("c7", Path(__file__).with_name("inspect_maps.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
B = M.B


def report():
    item = M.ITEM
    h = Header()
    for k, v in {"SIMPLE": True, "BITPIX": -32, "NAXIS": 2, "NAXIS1": 648, "NAXIS2": 648,
                 "OBS_ID": "0884250101", "INSTRUME": "EMOS2", "EXPIDSTR": "S002",
                 "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN", "CUNIT1": "deg", "CUNIT2": "deg",
                 "RADECSYS": "FK5", "EQUINOX": 2000., "CRPIX1": 324., "CRPIX2": 324.,
                 "CRVAL1": 123.456789, "CRVAL2": -37.123456, "CDELT1": -4 / 3600, "CDELT2": 4 / 3600}.items():
        h[k] = v
    return {"file_bytes": item["file_bytes"], "hdu_count": 1, "parser_warning_categories": [], "hdus": [
        {"hdu": 0, "extname": "PRIMARY", "header_offset": 0, "header_bytes": item["offset"],
         "data_offset": item["offset"], "data_bytes": B.PAYLOAD, "data_span_padded": 1681920, "cards": [h.tostring()]}]}


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here = Path(self.temp.name)
        self.prior = self.here / "prior"
        (self.prior / "products").mkdir(parents=True)
        self.product = self.prior / "products" / M.ITEM["filename"]
        self.data = np.ones((648, 648), dtype=">f4")
        self.data[0, :5] = [0, -1, np.nan, np.inf, -np.inf]
        self.product.write_bytes(b"X" * M.ITEM["offset"] + self.data.tobytes() + b"forbidden padding")
        self.start = {"manifest": {"maps": [M.ITEM]}}
        self.wcs = B.map_header(report(), M.ITEM)
        patches = [patch.object(M, "HERE", self.here), patch.object(B, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                   patch.object(B, "PRIOR_PATH", self.prior / "acquire.py"), patch.object(B, "read_header", return_value=self.wcs),
                   patch.object(M.C, "checkpoint"), patch.object(M.C, "peak_memory", return_value=100),
                   patch.object(M.C, "PEAK", 0), patch.object(M.C, "DEADLINE", None),
                   patch("requests.Session", side_effect=AssertionError("network forbidden")),
                   patch.object(B.P, "replay", side_effect=AssertionError("old C3e replay forbidden")),
                   patch.object(B.P, "worker", side_effect=AssertionError("old network worker forbidden")),
                   patch.object(M.C, "head_plan", side_effect=AssertionError("old plan forbidden"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def fake_core(self):
        return SimpleNamespace(summarize=lambda data, wcs, centre, kind: {"status": B.PASS, "region": kind})

    def test_isolated_globals_and_single_map_cap(self):
        original = M.load_base()
        self.assertEqual(len(original.MAPS), 2)
        self.assertEqual(original.TOTAL, 3359232)
        self.assertEqual(original.SOURCE, M.BASE_PATH)
        self.assertEqual(B.MAPS, (M.ITEM,))
        self.assertEqual(B.TOTAL, 1679616)
        self.assertEqual(B.SOURCE, M.SOURCE)
        self.assertIsNot(original.C, M.C)
        np.testing.assert_array_equal(B.centres(), original.centres())

    def test_exact_endian_span_and_no_second_map_or_padding(self):
        stream = io.BytesIO(self.product.read_bytes())
        reads, read = [], stream.read

        def bounded(size):
            self.assertGreater(size, 0)
            self.assertLessEqual(size, 16 * 648 * 4)
            reads.append(size)
            return read(size)

        a, total = B.zero(), B.zero()
        with patch.object(stream, "read", side_effect=bounded):
            actual = B.decode(stream, M.ITEM, a, total)
        np.testing.assert_array_equal(actual, self.data)
        self.assertEqual(a, {"read_bytes": B.PAYLOAD, "decoded_bytes": B.PAYLOAD})
        self.assertEqual(a, total)
        self.assertEqual(len(reads), 41)
        self.assertEqual(stream.tell(), M.ITEM["offset"] + B.PAYLOAD)
        with self.assertRaisesRegex(ValueError, "STOP_PAYLOAD_CAP"):
            B.decode(stream, M.ITEM, B.zero(), total)
        with self.assertRaisesRegex(ValueError, "STOP_FORBIDDEN_ARRAY_OR_REPEAT"):
            B.decode(stream, {**M.ITEM, "camera": "EMOS1"}, B.zero(), B.zero())

    def test_one_map_validation_state_correlations_and_no_second_slot(self):
        record = M.validation_state()
        self.assertEqual(len(record["maps"]), 1)
        M.validate_validation(record)
        for status in ("FAILED", "ATTEMPTED", "COMPLETED_ELIGIBLE_RECEIPTS"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "STOP_VALIDATION_ACCOUNTING"):
                M.validate_validation({**record, "status": status})
        with self.assertRaisesRegex(ValueError, "STOP_VALIDATION_ACCOUNTING"):
            M.validate_validation({**record, "maps": record["maps"] * 2})
        done = M.validation_state()
        done["status"] = "COMPLETED_ELIGIBLE_RECEIPTS"
        done["maps"][0].update(status="COMPLETED", accounting={"read_bytes": B.PAYLOAD, "decoded_bytes": B.PAYLOAD})
        done["accounting"] = dict(done["maps"][0]["accounting"])
        M.validate_validation(done)

    def test_second_map_receipt_rejected_before_any_measurement(self):
        M.C.save("map-2-start.json", {"map": 2})
        with patch.object(B, "measure", side_effect=AssertionError("no measurement allowed")), \
                self.assertRaisesRegex(ValueError, "STOP_EXTRA_MAP_ARTIFACT"):
            M.ledger(recompute=True)

    def test_full_worker_parent_replay_three_distinct_one_map_passes(self):
        M.C.save("run-start.json", self.start)
        original, passes = B.measure, []

        def measure(item, a, total):
            value = original(item, a, total)
            passes.append(dict(a))
            return value

        with patch.object(B, "verify_binding"), patch.object(B, "verify_prior"), \
                patch.object(M.C, "load_pinned", return_value=self.fake_core()), patch.object(B, "measure", side_effect=measure):
            self.assertEqual(B.worker(), 0)
            result = B.assess(0)
            self.assertEqual(result["status"], B.PASS)
            self.assertEqual(result["planned_regions"], 10)
            self.assertEqual(result["summarized_regions"], 10)
            self.assertEqual(result["MOS2"], "ONLY_MAP_IN_THIS_STAGE")
            result.update(assessment_completed=True, artifacts=B.artifacts(), source_sha256=M.C.sha(M.SOURCE), parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            B.replay()
        self.assertEqual(passes, [{"read_bytes": B.PAYLOAD, "decoded_bytes": B.PAYLOAD}] * 3)
        self.assertEqual(len(result["validation_pass"]["maps"]), 1)
        text = "".join(p.read_text() for p in self.here.glob("*.json"))
        for secret in ("123.456789", "-37.123456", "CRVAL", "CRPIX", '"map": 2'):
            self.assertNotIn(secret, text)

    def test_truncated_worker_preserves_partial_single_map(self):
        self.product.write_bytes(b"X" * M.ITEM["offset"] + b"1234567")
        M.C.save("run-start.json", self.start)
        with patch.object(B, "verify_binding"), patch.object(B, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(B.worker(), 1)
            result = B.assess(1)
        self.assertEqual(result["worker_accounting"], {"read_bytes": 7, "decoded_bytes": 0})
        self.assertEqual(len(result["ledger"]), 1)
        self.assertEqual(result["additional_validation_pass_accounting"], B.zero())

    def test_caught_parent_partial_pass_failure_and_no_retry(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def bounded(command, seconds):
            self.assertEqual(seconds, 60)
            self.assertEqual(command[-2:], [str(M.SOURCE), "_worker"])
            self.assertEqual(B.worker(), 0)
            self.product.write_bytes(b"X" * M.ITEM["offset"] + b"1234567")
            return 0, ""

        original = M.C.load_pinned

        def loader(name, path, digest):
            if name == "c5_deadline":
                return SimpleNamespace(bounded_run=bounded)
            return self.fake_core() if path == B.CORE_PATH else original(name, path, digest)

        with patch.object(B, "PROTOCOL", protocol), patch.object(B, "binding", return_value=self.start), \
                patch.object(B, "verify_binding"), patch.object(B, "verify_prior"), patch.object(M.C, "load_pinned", side_effect=loader):
            self.assertEqual(B.run(), 1)
        r = M.C.read("outcome.json")
        self.assertEqual(r["worker_returncode"], 0)
        self.assertEqual(r["additional_validation_pass_accounting"], {"read_bytes": 7, "decoded_bytes": 0})
        self.assertEqual(r["validation_pass"]["status"], "FAILED")
        self.assertEqual(len(r["validation_pass"]["maps"]), 1)
        B.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            B.run()

    def test_replay_mismatch_reports_this_pass_without_mutation(self):
        M.C.save("run-start.json", self.start)
        with patch.object(B, "verify_binding"), patch.object(B, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(B.worker(), 0)
            result = B.assess(0)
            result.update(assessment_completed=True, artifacts=B.artifacts(), source_sha256=M.C.sha(M.SOURCE), parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            before, old, output = B.artifacts(), M.C.read, io.StringIO()
            changed = {**result, "planned_regions": 20}
            with patch.object(M.C, "read", side_effect=lambda n: changed if n == "outcome.json" else old(n)), \
                    contextlib.redirect_stdout(output), self.assertRaisesRegex(ValueError, "STOP_OUTCOME_REPLAY"):
                B.replay()
        self.assertEqual(B.artifacts(), before)
        emitted = json.loads(output.getvalue().split(" ", 1)[1])
        self.assertEqual(emitted["accounting"], {"read_bytes": B.PAYLOAD, "decoded_bytes": B.PAYLOAD})

    def test_nonzero_worker_and_missing_region_cannot_pass(self):
        M.C.save("run-start.json", self.start)
        with patch.object(B, "verify_binding"), patch.object(B, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(B.worker(), 0)
            self.assertEqual(B.assess(124)["status"], "STOP")
            old = M.C.read
            record = copy.deepcopy(old("map-1-result.json"))
            record["summaries"].pop()
            with patch.object(M.C, "read", side_effect=lambda n: record if n == "map-1-result.json" else old(n)), \
                    self.assertRaisesRegex(ValueError, "STOP_REGION_DENOMINATOR"):
                B.assess(0)

    def test_prelaunch_failure_has_only_one_unattempted_slot(self):
        with patch.object(B, "binding", side_effect=ValueError("STOP_COMPOSITION_DEPENDENCY")):
            self.assertEqual(B.run(), 1)
        result = M.C.read("outcome.json")
        self.assertEqual(result["ledger"], [{"map": 1, "status": "NOT_ATTEMPTED", "accounting": None}])
        B.replay()

    def test_metadata_only_actual_manifest_binding_product_open_forbidden(self):
        if not (M.PRIOR_PATH.parent / "headers/slot-1-headers.json").exists():
            self.skipTest("Local ignored headers unavailable; synthetic schema tests retained")
        original_open = Path.open

        def guarded(path, *args, **kwargs):
            if "products" in path.parts:
                raise AssertionError("no product open in metadata preflight")
            return original_open(path, *args, **kwargs)

        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic protocol")
        with patch.object(Path, "open", guarded):
            spec = importlib.util.spec_from_file_location("c7_metadata_smoke", M.SOURCE)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            actual = module.binding(protocol)
        self.assertEqual(actual, json.loads(json.dumps(actual)))
        self.assertEqual(actual["manifest"]["planned_regions"], 10)
        self.assertEqual(actual["caps"]["payload_bytes_per_pass"], 1679616)
        self.assertNotIn("CRVAL", json.dumps(actual))

    def test_synthetic_real_core_ten_region_measure(self):
        centres = [(123.456789, -37.123456), (123.456789, -37.09), (123.49, -37.123456),
                   (123.456789, -37.156), (123.42, -37.123456)]
        a, total = B.zero(), B.zero()
        with patch.object(B, "centres", return_value=centres):
            summaries = B.measure(M.ITEM, a, total)
        self.assertEqual(len(summaries), 10)
        self.assertTrue(all(r["diagnostic"]["status"] == B.PASS for r in summaries))
        self.assertTrue(all([r["subdivision"] for r in s["diagnostic"]["resolutions"]] == [4, 8] for s in summaries))
        self.assertLess(len(M.C.json_bytes(summaries)), M.C.JSON_CAP - M.C.RESERVE)


if __name__ == "__main__":
    unittest.main()
