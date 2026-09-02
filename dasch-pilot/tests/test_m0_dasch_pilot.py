from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "m0_dasch_pilot.py"
PILOT_DIR = SCRIPT.parent.parent
SPEC = importlib.util.spec_from_file_location("m0_dasch_pilot", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DaschPilotTests(unittest.TestCase):
    def test_decimal_year_epoch(self) -> None:
        self.assertAlmostEqual(MODULE.decimal_year(2440587.5), 1970.0)

    def test_standard_mask_matches_documented_values(self) -> None:
        self.assertEqual(MODULE.STANDARD_BAD_AFLAGS, 47168)
        for value in (64, 2048, 4096, 8192, 32768):
            self.assertTrue(MODULE.STANDARD_BAD_AFLAGS & value)

    def test_control_thresholds_are_directional(self) -> None:
        self.assertGreater(MODULE.MIN_BRIGHTENING_MAG, 0.0)
        self.assertGreater(MODULE.MIN_DIFFERENTIAL_BRIGHTENING_MAG, 0.0)
        self.assertGreaterEqual(
            MODULE.MIN_DIFFERENTIAL_BRIGHTENING_MAG,
            MODULE.MIN_BRIGHTENING_MAG,
        )

    def test_load_api_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "table.json"
            path.write_text(json.dumps(["a,b", "1,2"]), encoding="utf-8")
            self.assertEqual(MODULE.load_api_table(path), [{"a": "1", "b": "2"}])

    def test_angular_separation_is_symmetric(self) -> None:
        first = MODULE.angular_sep_arcsec(10.0, 20.0, 10.001, 20.001)
        second = MODULE.angular_sep_arcsec(10.001, 20.001, 10.0, 20.0)
        self.assertAlmostEqual(first, second, places=8)
        self.assertGreater(first, 0.0)

    def test_robust_stats(self) -> None:
        stats = MODULE.robust_stats([10.0, 10.5, 50.0])
        self.assertEqual(stats["n"], 3)
        self.assertEqual(stats["median_mag"], 10.5)
        self.assertEqual(stats["mad_mag"], 0.5)

    def test_effective_input_is_bound_to_its_role_digest(self) -> None:
        defaults = {
            "target_querycat": PILOT_DIR / "data/raw/tcrb-querycat.json",
            "target_lightcurve": PILOT_DIR / "data/raw/tcrb-lightcurve.json",
            "field_querycat": PILOT_DIR / "data/raw/tcrb-field-querycat.json",
            "field_lightcurve": PILOT_DIR / "data/raw/field-control-lightcurve.json",
        }
        with tempfile.TemporaryDirectory() as directory:
            alternate = Path(directory) / "alternate-querycat.json"
            alternate.write_bytes(defaults["target_querycat"].read_bytes())
            supplied = {**defaults, "target_querycat": alternate}
            MODULE._verify_provenance(
                PILOT_DIR / "data/provenance.json", PILOT_DIR, supplied
            )

            alternate.write_bytes(alternate.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                MODULE._verify_provenance(
                    PILOT_DIR / "data/provenance.json", PILOT_DIR, supplied
                )

    def test_detected_row_with_blank_aflags_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing aflags"):
            MODULE.summarize_lightcurve([{"magcal_magdep": "12.3", "aflags": ""}])

    def test_catalog_identity_must_match_lightcurve_request(self) -> None:
        row = {"ref_number": "10", "gsc_bin_index": "20"}
        MODULE._require_catalog_identity(
            row, {"ref_number": 10, "gsc_bin_index": 20}, label="test"
        )
        with self.assertRaisesRegex(ValueError, "gsc_bin_index"):
            MODULE._require_catalog_identity(
                row, {"ref_number": 10, "gsc_bin_index": 21}, label="test"
            )

    def test_manifest_is_bound_to_frozen_analysis_and_target(self) -> None:
        manifest_path = PILOT_DIR / "data/provenance.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["analysis_id"], MODULE.EXPECTED_ANALYSIS_ID)
        self.assertEqual(manifest["target"]["name"], MODULE.EXPECTED_TARGET_NAME)


if __name__ == "__main__":
    unittest.main()
