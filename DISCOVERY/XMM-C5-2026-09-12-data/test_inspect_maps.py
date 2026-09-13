"""Synthetic-only C5 execution; actual inputs are metadata-only smoke tests."""

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from astropy.io.fits import Header

SPEC = importlib.util.spec_from_file_location("c5", Path(__file__).with_name("inspect_maps.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def report(item):
    h = Header()
    for k, v in {"SIMPLE": True, "BITPIX": -32, "NAXIS": 2, "NAXIS1": 648, "NAXIS2": 648,
                 "OBS_ID": "0884250101", "INSTRUME": item["camera"], "EXPIDSTR": item["exposure"],
                 "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN", "CUNIT1": "deg", "CUNIT2": "deg",
                 "RADECSYS": "FK5", "EQUINOX": 2000., "CRPIX1": 324., "CRPIX2": 324.,
                 "CRVAL1": 123.456789, "CRVAL2": -37.123456, "CDELT1": -4 / 3600, "CDELT2": 4 / 3600}.items():
        h[k] = v
    return {"file_bytes": item["file_bytes"], "hdu_count": 1, "parser_warning_categories": [], "hdus": [
        {"hdu": 0, "extname": "PRIMARY", "header_offset": 0, "header_bytes": item["offset"],
         "data_offset": item["offset"], "data_bytes": M.PAYLOAD, "data_span_padded": 1681920, "cards": [h.tostring()]}]}


class BoundedStream(io.BytesIO):
    def __init__(self, raw, offset):
        super().__init__(raw)
        self.offset, self.reads = offset, []

    def read(self, size=-1):
        assert 0 < size <= M.CHUNK_ROWS * M.SIDE * 4
        assert self.tell() >= self.offset
        self.reads.append((self.tell(), size))
        return super().read(size)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here = Path(self.temp.name)
        self.prior = self.here / "prior"
        (self.prior / "products").mkdir(parents=True)
        self.start = {"manifest": {"maps": list(M.MAPS)}}
        self.data = np.ones((648, 648), dtype=">f4")
        self.data[0, :5] = [0, -1, np.nan, np.inf, -np.inf]
        for item in M.MAPS:
            (self.prior / "products" / item["filename"]).write_bytes(b"X" * item["offset"] + self.data.tobytes() + b"forbidden padding")
        self.wcs = M.map_header(report(M.MAPS[0]), M.MAPS[0])
        patches = [patch.object(M, "HERE", self.here), patch.object(M.C, "HERE", self.here),
                   patch.object(M, "PRIOR_PATH", self.prior / "acquire.py"), patch.object(M.C, "checkpoint"),
                   patch.object(M.C, "peak_memory", return_value=100), patch.object(M.C, "PEAK", 0),
                   patch.object(M.C, "DEADLINE", None), patch.object(M, "read_header", return_value=self.wcs),
                   patch("requests.Session", side_effect=AssertionError("network forbidden")),
                   patch.object(M.P, "worker", side_effect=AssertionError("old worker forbidden")),
                   patch.object(M.P, "run", side_effect=AssertionError("old run forbidden")),
                   patch.object(M.C, "head_plan", side_effect=AssertionError("old plan forbidden"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_exact_big_endian_two_spans_and_zeros_nonfinite(self):
        total = M.zero()
        for item in M.MAPS:
            stream = BoundedStream(b"X" * item["offset"] + self.data.tobytes() + b"never read", item["offset"])
            a = M.zero()
            actual = M.decode(stream, item, a, total)
            np.testing.assert_array_equal(actual, self.data)
            self.assertEqual(a, {"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD})
            self.assertEqual(len(stream.reads), 41)
            self.assertEqual(stream.tell(), item["offset"] + M.PAYLOAD)
        self.assertEqual(total, {"read_bytes": M.TOTAL, "decoded_bytes": M.TOTAL})

    def test_short_map_preserves_returned_and_decoded_totals(self):
        item = M.MAPS[1]
        chunk = M.CHUNK_ROWS * M.SIDE * 4
        stream = BoundedStream(b"X" * item["offset"] + b"\0" * (chunk + 17), item["offset"])
        a, total = M.zero(), {"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD}
        with self.assertRaisesRegex(ValueError, "STOP_TRUNCATED_MAP"):
            M.decode(stream, item, a, total)
        self.assertEqual(a, {"read_bytes": chunk + 17, "decoded_bytes": chunk})
        self.assertEqual(total, {"read_bytes": M.PAYLOAD + chunk + 17, "decoded_bytes": M.PAYLOAD + chunk})

    def test_changed_span_repeat_and_total_cap_before_read(self):
        stream = BoundedStream(b"", M.MAPS[0]["offset"])
        for item in ({**M.MAPS[0], "offset": 0}, {**M.MAPS[0], "filename": "EVENTS.fits"}):
            with self.assertRaisesRegex(ValueError, "STOP_FORBIDDEN_ARRAY_OR_REPEAT"):
                M.decode(stream, item, M.zero(), M.zero())
        with self.assertRaisesRegex(ValueError, "STOP_FORBIDDEN_ARRAY_OR_REPEAT"):
            M.decode(stream, M.MAPS[0], {"read_bytes": 1, "decoded_bytes": 0}, M.zero())
        with self.assertRaisesRegex(ValueError, "STOP_PAYLOAD_CAP"):
            M.decode(stream, M.MAPS[0], M.zero(), {"read_bytes": M.TOTAL, "decoded_bytes": M.TOTAL})
        self.assertEqual(stream.reads, [])

    def test_exact_schema_rejects_ambiguity_without_echo(self):
        for key, value in (("BITPIX", -64), ("NAXIS1", 647), ("CTYPE1", "RA---SIN"), ("CUNIT1", "rad"),
                           ("RADECSYS", "ICRS"), ("RADESYS", "ICRS"), ("EQUINOX", 1950.),
                           ("BSCALE", 1), ("BZERO", 0), ("BLANK", 0), ("BUNIT", "s"),
                           ("CD1_1", 1), ("PC1_1", 1), ("PV1_0", 0), ("A_ORDER", 2), ("CROTA2", 0)):
            r = report(M.MAPS[0])
            h = Header.fromstring("".join(r["hdus"][0]["cards"]))
            h[key] = value
            r["hdus"][0]["cards"] = [h.tostring()]
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.map_header(r, M.MAPS[0])
        r = report(M.MAPS[0])
        h = Header.fromstring("".join(r["hdus"][0]["cards"]))
        h.append(("CRVAL1", 5.))
        r["hdus"][0]["cards"] = [h.tostring()]
        with self.assertRaisesRegex(ValueError, "STOP_HEADER_AMBIGUITY"):
            M.map_header(r, M.MAPS[0])

    def test_alternate_linear_wcs_never_selected(self):
        r = report(M.MAPS[0])
        h = Header.fromstring("".join(r["hdus"][0]["cards"]))
        for key, value in {"CTYPE1L": "LINEAR", "CTYPE2L": "LINEAR", "CRVAL1L": 999., "CRVAL2L": 999.,
                           "LTM1_1": 80., "LTM2_2": 80.}.items():
            h[key] = value
        r["hdus"][0]["cards"] = [h.tostring()]
        actual = M.map_header(r, M.MAPS[0])
        np.testing.assert_array_equal(actual.wcs.crval, self.wcs.wcs.crval)
        self.assertEqual(actual.wcs.radesys, "FK5")

    def test_fixed_centre_cardinal_offsets_and_frame(self):
        from astropy import units as u
        from astropy.coordinates import FK5, SkyCoord

        coords = [SkyCoord(ra * u.deg, dec * u.deg, frame=FK5(equinox="J2000")).icrs for ra, dec in M.centres()]
        for expected, position in zip((0, 90, 180, 270), coords[1:], strict=True):
            self.assertAlmostEqual(coords[0].separation(position).arcsec, 120, places=6)
            angle = coords[0].position_angle(position).deg
            self.assertLess(abs((angle - expected + 180) % 360 - 180), 1e-6)

    def fake_core(self):
        return SimpleNamespace(summarize=lambda data, wcs, centre, kind: {"status": M.PASS, "region": kind})

    def test_full_worker_parent_replay_twenty_regions_three_passes(self):
        M.C.save("run-start.json", self.start)
        original = M.measure
        passes = []

        def measure(item, a, total):
            value = original(item, a, total)
            passes.append((item["map"], dict(a)))
            return value

        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), \
                patch.object(M.C, "load_pinned", return_value=self.fake_core()), patch.object(M, "measure", side_effect=measure):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            self.assertEqual(result["status"], M.PASS)
            self.assertEqual(result["summarized_regions"], 20)
            result.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE), parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            M.replay()
        self.assertEqual(passes, [(n, {"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD}) for n in (1, 2) * 3])
        self.assertEqual(result["additional_validation_pass_accounting"], {"read_bytes": M.TOTAL, "decoded_bytes": M.TOTAL})
        text = "".join(p.read_text() for p in self.here.glob("*.json"))
        for secret in ("123.456789", "-37.123456", "CRVAL", "CRPIX"):
            self.assertNotIn(secret, text)

    def test_nonzero_worker_and_denominator_tamper(self):
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(M.worker(), 0)
            self.assertEqual(M.assess(124)["status"], "STOP")
            old = M.C.read
            record = copy.deepcopy(old("map-1-result.json"))
            record["summaries"].pop()
            with patch.object(M.C, "read", side_effect=lambda n: record if n == "map-1-result.json" else old(n)), \
                    self.assertRaisesRegex(ValueError, "STOP_REGION_DENOMINATOR"):
                M.assess(0)

    def test_replay_postdecode_mismatch_emits_extra_pass_without_writes(self):
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            result.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE), parent_peak_memory_bytes=100)
            M.C.save("outcome.json", result, terminal=True)
            before = M.artifacts()
            old = M.C.read
            changed = {**result, "planned_regions": 19}
            output = io.StringIO()
            with patch.object(M.C, "read", side_effect=lambda n: changed if n == "outcome.json" else old(n)), \
                    contextlib.redirect_stdout(output), self.assertRaisesRegex(ValueError, "STOP_OUTCOME_REPLAY"):
                M.replay()
        self.assertEqual(M.artifacts(), before)
        self.assertTrue(output.getvalue().startswith("STOP_OFFLINE_REPLAY_PASS "))
        receipt = json.loads(output.getvalue().split(" ", 1)[1])
        self.assertEqual(receipt["accounting"], {"read_bytes": M.TOTAL, "decoded_bytes": M.TOTAL})

    def test_first_map_failure_stops_second_with_partial_accounting(self):
        item = M.MAPS[0]
        (self.prior / "products" / item["filename"]).write_bytes(b"X" * item["offset"] + b"123")
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(M.worker(), 1)
            result = M.assess(1)
        self.assertEqual(result["worker_accounting"], {"read_bytes": 3, "decoded_bytes": 0})
        self.assertEqual(result["additional_validation_pass_accounting"], M.zero())
        self.assertEqual(result["ledger"][1]["status"], "NOT_ATTEMPTED")
        self.assertEqual(M.C.read("map-1-result.json")["error_code"], "STOP_TRUNCATED_MAP")

    def test_second_marker_after_failed_first_rejected(self):
        M.C.save("map-1-start.json", {"map": 1, "elapsed_seconds": 1})
        M.C.save("map-2-start.json", {"map": 2, "elapsed_seconds": 2})
        with self.assertRaisesRegex(ValueError, "STOP_MAP_ORDER"):
            M.ledger()

    def test_prelaunch_stop_unknown_and_exclusive_failure_replay(self):
        with patch.object(M, "binding", side_effect=ValueError("STOP_DEPENDENCY_HASH")):
            self.assertEqual(M.run(), 1)
        self.assertEqual(M.C.read("outcome.json")["additional_validation_pass_accounting"], M.zero())
        self.assertEqual(M.C.read("outcome.json")["validation_pass"]["status"], "NOT_ATTEMPTED")
        M.replay()
        with self.assertRaisesRegex(ValueError, "STOP_ALREADY_ATTEMPTED"):
            M.run()

    def test_validation_top_status_matches_actual_map_states(self):
        untouched = M.validation_state()
        M.validate_validation(untouched)
        for status in ("FAILED", "COMPLETED_ELIGIBLE_RECEIPTS", "ATTEMPTED"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "STOP_VALIDATION_ACCOUNTING"):
                M.validate_validation({**untouched, "status": status})
        failed = M.validation_state()
        failed["status"] = failed["maps"][0]["status"] = "FAILED"
        M.validate_validation(failed)
        for status in ("NOT_ATTEMPTED", "COMPLETED_ELIGIBLE_RECEIPTS", "ATTEMPTED"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "STOP_VALIDATION_ACCOUNTING"):
                M.validate_validation({**failed, "status": status})
        partial = M.validation_state()
        partial["maps"][0].update(status="COMPLETED", accounting={"read_bytes": M.PAYLOAD, "decoded_bytes": M.PAYLOAD})
        partial["accounting"] = dict(partial["maps"][0]["accounting"])
        for status in ("ATTEMPTED", "COMPLETED_ELIGIBLE_RECEIPTS"):
            M.validate_validation({**partial, "status": status})
        for status in ("FAILED", "NOT_ATTEMPTED"):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "STOP_VALIDATION_ACCOUNTING"):
                M.validate_validation({**partial, "status": status})

    def test_timeout_partial_marker_unknown_not_zero(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")

        def timeout(command, seconds):
            self.assertEqual(seconds, 60)
            self.assertEqual(command[-1], "_worker")
            (self.here / "map-1-start.json").write_bytes(b'{"map":')
            return 124, "private worker output"

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value=self.start), \
                patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), \
                patch.object(M.C, "load_pinned", return_value=SimpleNamespace(bounded_run=timeout)):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read("outcome.json")
        self.assertEqual(outcome["worker_returncode"], 124)
        self.assertIsNone(outcome["ledger"][0]["accounting"])
        self.assertIsNone(outcome["worker_accounting"])
        self.assertNotIn("private", (self.here / "outcome.json").read_text())
        M.replay()

    def test_parent_recompute_partial_failure_retains_exact_extra_pass(self):
        protocol = self.here / "protocol.md"
        protocol.write_bytes(b"synthetic")
        original_loader = M.C.load_pinned

        def complete_then_truncate(_command, _seconds):
            self.assertEqual(M.worker(), 0)
            item = M.MAPS[1]
            (self.prior / "products" / item["filename"]).write_bytes(b"X" * item["offset"] + b"1234567")
            return 0, ""

        def loader(name, path, digest):
            if name == "c5_deadline":
                return SimpleNamespace(bounded_run=complete_then_truncate)
            if path == M.CORE_PATH:
                return self.fake_core()
            return original_loader(name, path, digest)

        with patch.object(M, "PROTOCOL", protocol), patch.object(M, "binding", return_value=self.start), \
                patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), patch.object(M.C, "load_pinned", side_effect=loader):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read("outcome.json")
        self.assertEqual(outcome["worker_returncode"], 0)
        self.assertFalse(outcome["assessment_completed"])
        self.assertEqual(outcome["additional_validation_pass_accounting"], {"read_bytes": M.PAYLOAD + 7, "decoded_bytes": M.PAYLOAD})
        self.assertEqual([r["status"] for r in outcome["validation_pass"]["maps"]], ["COMPLETED", "FAILED"])
        self.assertEqual(outcome["validation_pass"]["maps"][1]["accounting"], {"read_bytes": 7, "decoded_bytes": 0})
        M.replay()
        old = M.C.read
        changed = copy.deepcopy(outcome)
        changed["validation_pass"]["accounting"]["read_bytes"] -= 1
        with patch.object(M.C, "read", side_effect=lambda n: changed if n == "outcome.json" else old(n)), \
                self.assertRaisesRegex(ValueError, "STOP_VALIDATION_ACCOUNTING"):
            M.replay()

    def test_late_parent_peak_stop_replays(self):
        M.C.save("run-start.json", self.start)
        with patch.object(M, "verify_binding"), patch.object(M, "verify_prior"), patch.object(M.C, "load_pinned", return_value=self.fake_core()):
            self.assertEqual(M.worker(), 0)
            result = M.assess(0)
            result.update(assessment_completed=True, artifacts=M.artifacts(), source_sha256=M.C.sha(M.SOURCE))
            with patch.object(M.C, "peak_memory", return_value=M.C.MEMORY_CAP + 1):
                M.C.save("outcome.json", result, terminal=True, peak_key="parent_peak_memory_bytes")
            self.assertEqual(result["status"], "STOP")
            self.assertEqual(result["worker_returncode"], 0)
            M.replay()

    def test_actual_metadata_only_binding_under_product_read_guard(self):
        original = M.SOURCE.parent
        prior = original.parent / "XMM-C3e-2026-09-12-data/acquire.py"
        if not (prior.parent / "headers/slot-1-headers.json").exists():
            self.skipTest("Local ignored headers unavailable; synthetic schema tests still mandatory")
        raw_open = Path.open

        def guarded(path, *args, **kwargs):
            if "products" in path.parts:
                raise AssertionError("product read forbidden in manifest")
            return raw_open(path, *args, **kwargs)

        with patch.object(M, "HERE", original), patch.object(M.C, "HERE", original), patch.object(M, "PRIOR_PATH", prior), \
                patch.object(Path, "open", guarded):
            # Restore the true read_header function; setUp's patch is intentionally bypassed.
            spec = importlib.util.spec_from_file_location("c5_manifest_smoke", M.SOURCE)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            actual = module.binding(module.PROTOCOL)
        self.assertEqual(actual, json.loads(json.dumps(actual)))
        self.assertEqual(actual["manifest"]["planned_regions"], 20)
        self.assertNotIn("CRVAL", json.dumps(actual))
        self.assertIsNot(M.C, M.P.T.C)

    def test_synthetic_twenty_region_core_benchmark_and_json_budget(self):
        core = M.C.load_pinned("c5_benchmark", M.CORE_PATH, M.CORE_HASH)
        centres = [(123.456789, -37.123456), (123.456789, -37.09), (123.49, -37.123456),
                   (123.456789, -37.156), (123.42, -37.123456)]
        began = time.monotonic()
        summaries = [core.summarize(self.data, self.wcs, centre, kind) for _camera in range(2)
                     for centre in centres for kind in M.KINDS]
        elapsed = time.monotonic() - began
        self.assertEqual(len(summaries), 20)
        self.assertLess(elapsed, M.SECONDS)
        self.assertLess(len(M.C.json_bytes(summaries)), M.C.JSON_CAP - M.C.RESERVE)
        self.assertTrue(all(r["status"] == M.PASS for r in summaries))
        print("SYNTHETIC_20_REGION_BENCHMARK", round(elapsed, 3), "seconds", len(M.C.json_bytes(summaries)), "JSON bytes")


if __name__ == "__main__":
    unittest.main()
