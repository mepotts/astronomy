import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "m0_pilot.py"
SPEC = importlib.util.spec_from_file_location("m0_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class M0PilotTests(unittest.TestCase):
    def test_interpolate(self):
        self.assertEqual(MODULE.interpolate([(0.0, 2.0), (2.0, 4.0)], 1.0), 3.0)
        self.assertEqual(MODULE.interpolate([(0.0, 2.0), (2.0, 4.0)], -1.0), 2.0)

    def test_blackbody_flux_is_finite_and_positive(self):
        row = {"t_ds": "250", "gamma": "0.1", "r_med_geo": "100", "M_G": "10"}
        value = MODULE.dust_flux_ujy(row, [(5.0, -0.5), (15.0, -3.0)])
        self.assertTrue(math.isfinite(value))
        self.assertGreater(value, 0)

    def test_coverage_parser_is_case_insensitive(self):
        raw = (
            b'BAND,N_IMAGES,MIN_MJD,MAX_MJD\r\n'
            b'SPHEREx-D5,12,60000.5,61000.5\r\n'
        )
        parsed = MODULE.parse_coverage_csv(raw)
        self.assertEqual(parsed["SPHEREx-D5"]["n_images"], 12)

    def test_coverage_parser_rejects_coercion_and_invalid_bounds(self):
        invalid_rows = (
            "SPHEREx-D5,1.5,60000,60001",
            "SPHEREx-D5,-1,60000,60001",
            "SPHEREx-D5,1,nan,60001",
            "SPHEREx-D5,1,60002,60001",
        )
        for row in invalid_rows:
            with self.subTest(row=row), self.assertRaises(ValueError):
                MODULE.parse_coverage_csv(
                    f"band,n_images,min_mjd,max_mjd\n{row}\n".encode()
                )

    def test_qr2_version_response_binds_frozen_versions(self):
        raw = "provenance_version\n" + "\n".join(
            ("6.1", *MODULE.QR2_PIPELINE_VERSIONS)
        )
        observed = MODULE.validate_qr2_versions(raw.encode())
        self.assertTrue(set(MODULE.QR2_PIPELINE_VERSIONS).issubset(observed))
        with self.assertRaises(ValueError):
            MODULE.validate_qr2_versions(b"provenance_version\n6.1\n")

    def test_atomic_persistence_hashes_stored_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            proof = MODULE.persist_bytes(path, b"exact bytes")
            MODULE.verify_stored_proof(path, proof)
            path.write_bytes(b"tampered")
            with self.assertRaises(RuntimeError):
                MODULE.verify_stored_proof(path, proof)

    def test_coverage_requires_exact_positive_d1_through_d6(self):
        complete = {
            f"SPHEREx-D{index}": {"n_images": 1, "min_mjd": 1.0, "max_mjd": 2.0}
            for index in range(1, 7)
        }
        self.assertTrue(MODULE.coverage_metrics(complete)["has_all_d1_d6"])
        incomplete = dict(complete)
        incomplete.pop("SPHEREx-D6")
        incomplete["SPHEREx-All"] = {"n_images": 99, "min_mjd": 1.0, "max_mjd": 2.0}
        metrics = MODULE.coverage_metrics(incomplete)
        self.assertFalse(metrics["has_all_d1_d6"])
        self.assertFalse(metrics["has_d5_d6"])

    def test_narrow_gate_requires_control_and_falsifier_coverage(self):
        targets = [
            {
                "pair": pair,
                "has_all_d1_d6": pair == 1,
                "has_d5_d6": True,
                "warm_runtime_hours_est": 1.0,
            }
            for pair in (1, 2, 3)
        ]
        controls = [
            {
                "pair": pair,
                "has_all_d1_d6": False,
                "has_d5_d6": True,
                "warm_runtime_hours_est": 1.0,
            }
            for pair in (1, 2, 3)
        ]
        self.assertEqual(
            MODULE.decide_coverage_verdict(1, targets, controls), "NARROW/PIVOT"
        )
        controls[0]["has_d5_d6"] = False
        self.assertEqual(MODULE.decide_coverage_verdict(1, targets, controls), "KILL")
        controls[0]["has_d5_d6"] = True
        targets[1]["warm_runtime_hours_est"] = 7.0
        self.assertEqual(MODULE.decide_coverage_verdict(1, targets, controls), "KILL")

    def test_two_to_nine_above_floor_require_new_falsifier_protocol(self):
        targets = [
            {
                "pair": pair,
                "has_all_d1_d6": True,
                "has_d5_d6": True,
                "warm_runtime_hours_est": 1.0,
            }
            for pair in (1, 2, 3)
        ]
        controls = [dict(row) for row in targets]
        for count in (2, 3, 9):
            with self.subTest(count=count):
                self.assertEqual(
                    MODULE.decide_coverage_verdict(count, targets, controls), "BLOCKED"
                )

    def test_public_source_validation_checks_content_and_schema(self):
        payloads = {
            "irsa_mission": b"SPHEREx: An All-Sky Spectral Survey overview_qr.html",
            "irsa_spectrophotometry": b"Spectrophotometry Tool The Tractor",
            "aws_registry": b"SPHEREx Quick Release nasa-irsa-spherex/qr2/level2",
            "aws_level2_list": b"<ListBucketResult <Prefix>qr2/level2/</Prefix>",
        }
        schema = (
            "table_name,column_name,datatype\n"
            "spherex.plane,planeid,char\n"
            "spherex.plane,energy_bandpassname,char\n"
            "spherex.plane,time_bounds_lower,double\n"
            "spherex.plane,poly,char\n"
            "spherex.plane,dataproducttype,char\n"
            "spherex.plane,calibrationlevel,short\n"
            "spherex.plane,provenance_version,char\n"
            "spherex.artifact,planeid,char\n"
            "spherex.artifact,producttype,char\n"
        ).encode()
        checks = MODULE.validate_public_sources(payloads, schema)
        self.assertTrue(all(checks.values()))
        with self.assertRaises(ValueError):
            MODULE.validate_public_sources({**payloads, "aws_level2_list": b"wrong"}, schema)

    def test_aggregate(self):
        self.assertEqual(MODULE.aggregate([1.0, 4.0, 2.0])["median"], 2.0)

    def test_protocol_summary_forbidden_tokens(self):
        safe = json.dumps({"target_rows": 3, "claim_scope": "candidate-free"}).lower()
        for token in ("source_id", '"ra"', '"dec"', "designation"):
            self.assertNotIn(token, safe)

    def test_coordinate_probe_requires_exact_manifest_authorization(self):
        with self.assertRaises(PermissionError):
            MODULE.require_manifest_authorization("abc123", None)
        with self.assertRaises(PermissionError):
            MODULE.require_manifest_authorization("abc123", "different")
        MODULE.require_manifest_authorization("abc123", "ABC123")

    def test_coverage_query_counts_distinct_frozen_qr2_planes(self):
        position = MODULE.Position("slot", "target", 1, 1.0, 2.0, "id", 3.0, 4.0)
        query = MODULE.coverage_query(position)
        self.assertIn("COUNT(DISTINCT p.planeid)", query)
        self.assertIn("p.calibrationlevel = 2", query)
        self.assertIn("p.provenance_version IN", query)
        self.assertNotIn("'6.1'", query)

    def test_tracked_result_adds_no_identifier_or_coordinate_fields(self):
        result_path = SCRIPT.parents[1] / "out" / "m0_result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        serialized = json.dumps(result).lower()
        self.assertEqual(result["blinded_probe"]["coordinates_sent_externally"], 0)
        self.assertEqual(len(result["inputs"]["warm_error_references"]), 2)
        for proof in result["inputs"]["warm_error_references"]:
            self.assertEqual(len(proof["sha256"]), 64)
        for token in ("source_id", '"ra"', '"dec"', "designation"):
            self.assertNotIn(token, serialized)


if __name__ == "__main__":
    unittest.main()
