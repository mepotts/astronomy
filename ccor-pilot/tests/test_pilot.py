"""Offline regression tests for the frozen CCOR2 input/statistic gates."""

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from zipfile import ZipFile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ccor_pilot", ROOT / "scripts/pilot.py")
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def good_header(index=0):
    return {
        **dict.fromkeys(pilot.TRUE_KEYS, True),
        "BADBLK_N": 0,
        "MISBLK_N": 0,
        "SHIFT_X": 0.0,
        "SHIFT_Y": 0.0,
        "NAXIS1": 2048,
        "NAXIS2": 1920,
        "DATE-OBS": f"2026-09-01T13:{index * 15:02d}:14",
        "CTYPE1": "HPLN-TAN",
        "CTYPE2": "HPLT-TAN",
        "CDELT1": 24.0,
        "CDELT2": 24.0,
    }


class HeaderTests(unittest.TestCase):
    def test_empty_and_malformed_index_fail_closed(self):
        for value in ([], {}, None, "[]"):
            with self.subTest(value=value), self.assertRaises(pilot.PilotStop):
                pilot.validate_index(value)

    def test_valid_headers(self):
        self.assertEqual(pilot.header_errors(good_header(), pilot.FILES[0], 2), [])

    def test_every_required_flag_fails_closed(self):
        for key in pilot.TRUE_KEYS:
            for value in (False, None, "T", 1):
                header = good_header()
                header[key] = value
                with self.subTest(key=key, value=value):
                    self.assertTrue(pilot.header_errors(header, pilot.FILES[0], 2))

    def test_fill_shift_missing_blocks_time_and_shape(self):
        for key, value in (
            ("SHIFT_X", 7),
            ("SHIFT_Y", -7),
            ("SHIFT_Y", -9999),
            ("SHIFT_X", float("nan")),
            ("BADBLK_N", 1),
            ("MISBLK_N", None),
            ("NAXIS2", 2048),
            ("DATE-OBS", "2026-09-01T13:00:17"),
        ):
            header = good_header()
            header[key] = value
            with self.subTest(key=key, value=value):
                self.assertTrue(pilot.header_errors(header, pilot.FILES[0], 2))

    def test_mapping_is_not_inferred_from_wcs(self):
        records = [
            {"filename": name, "hdu_count": 2, "header": good_header(i)}
            for i, name in enumerate(pilot.FILES)
        ]
        result = pilot.gate_records(records)
        self.assertEqual(result["outcome"], "STOP_ORIENTATION_UNRESOLVED")
        self.assertFalse(result["real_pixels_scored"])

    def test_axis_mapping_and_rotation_rejection(self):
        mapped = pilot.display_to_fits(np.array([[1632, 1400]]), good_header())
        np.testing.assert_array_equal(mapped, [[1632, 519]])
        header = {**good_header(), "CDELT1": -24, "CDELT2": -24}
        np.testing.assert_array_equal(
            pilot.display_to_fits(np.array([[1632, 1400]]), header), [[415, 1400]]
        )
        with self.assertRaises(pilot.PilotStop):
            pilot.display_flips({**good_header(), "PC1_2": 0.02})

    def test_wrong_frame_order_fails(self):
        records = [
            {"filename": name, "hdu_count": 2, "header": good_header(i)}
            for i, name in enumerate(pilot.FILES)
        ]
        with self.assertRaises(pilot.PilotStop):
            pilot.gate_records(records[::-1])

    def test_recorded_evidence_replays_without_pixels(self):
        path = ROOT / "results/header-evidence.json"
        if not path.exists():
            self.skipTest("live header evidence not collected yet")
        evidence = json.loads(path.read_text(encoding="utf-8"))
        result = json.loads((ROOT / "results/result.json").read_text(encoding="utf-8"))
        self.assertEqual(
            evidence["spec_sha256"], pilot.sha256(ROOT / "SPEC-2026-09-05.md")
        )
        self.assertEqual(result["header_evidence_sha256"], pilot.sha256(path))
        self.assertEqual(
            pilot.gate_records(evidence["records"])["outcome"], result["outcome"]
        )
        self.assertFalse(result["real_pixels_scored"])
        self.assertEqual(result["images_decompressed"], 0)

    def test_recorded_independent_wcs_and_primary_header_audit(self):
        evidence = json.loads(
            (ROOT / "results/header-evidence.json").read_text(encoding="utf-8")
        )
        audit = json.loads(
            (ROOT / "results/header-audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            audit["header_evidence_sha256"],
            pilot.sha256(ROOT / "results/header-evidence.json"),
        )
        self.assertEqual(audit["images_decompressed"], 0)
        for record, row in zip(evidence["records"], audit["audits"], strict=True):
            self.assertEqual(record["filename"], row["filename"])
            self.assertEqual(row["hdu_indices_containing_ISVIABLE"], [])
            self.assertGreater(min(row["default_wcs_cross_axis_ratios"]), 0.01)
            with self.assertRaisesRegex(pilot.PilotStop, "STOP_WCS_ROTATION"):
                pilot.display_flips(record["header"])

    def test_exact_executed_sources_are_preserved(self):
        evidence = json.loads(
            (ROOT / "results/header-evidence.json").read_text(encoding="utf-8")
        )
        audit = json.loads(
            (ROOT / "results/header-audit.json").read_text(encoding="utf-8")
        )
        with ZipFile(ROOT / "results/executed-source.zip") as archive:
            expected = {
                "scripts/pilot.py": evidence["script_sha256"],
                "scripts/audit_headers.py": audit["audit_script_sha256"],
                "SPEC-2026-09-05.md": evidence["spec_sha256"],
            }
            self.assertEqual(set(archive.namelist()), set(expected))
            for name, digest in expected.items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)


class StatisticTests(unittest.TestCase):
    def setUp(self):
        self.cube = np.random.default_rng(20260905).normal(size=(4, 216, 216))

    def test_leave_one_out_residual(self):
        data = np.array([0, 1, 2, 3], dtype=float).reshape(4, 1, 1)
        np.testing.assert_array_equal(pilot.residuals(data).ravel(), [-2, -1, 1, 2])

    def test_synthetic_injection_and_no_source_search(self):
        result = pilot.measure_frozen_cube(self.cube)
        self.assertEqual(len(result["negative_tracks"]), 8)
        self.assertTrue(result["injection"]["pass"])
        self.assertFalse(result["reported_source_recovery_gate_pass"])

    def test_fixed_synthetic_source_recovers(self):
        yy, xx = np.indices(self.cube.shape[1:])
        for i, pos in enumerate(pilot.POSITIONS - [1520, 1280]):
            self.cube[i] += 20 * np.exp(
                -0.5 * ((xx - pos[0]) ** 2 + (yy - pos[1]) ** 2)
            )
        result = pilot.measure_frozen_cube(self.cube)
        self.assertTrue(result["reported_source_recovery_gate_pass"])
        self.assertTrue(result["injection"]["pass"])

    def test_invalid_pixels_and_zero_noise_fail(self):
        with self.assertRaises(pilot.PilotStop):
            pilot.robust_scale(np.array([1, np.nan]))
        with self.assertRaises(pilot.PilotStop):
            pilot.measure_frozen_cube(np.zeros_like(self.cube))
        with self.assertRaises(pilot.PilotStop):
            pilot.masks((20, 20), np.array([1, 1]))


if __name__ == "__main__":
    unittest.main()
