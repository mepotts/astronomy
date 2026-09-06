"""Offline follow-up evidence contracts; never authorize a science measurement."""

import importlib.util
import json
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_retrospective", ROOT / "scripts/audit_retrospective.py"
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class RetrospectiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(
            (ROOT / "results/retrospective-preflight-20260906.json").read_text()
        )

    def test_four_header_only_records(self):
        self.assertEqual(len(self.evidence["records"]), 4)
        self.assertEqual(self.evidence["images_decompressed"], 0)
        self.assertEqual(self.evidence["image_prefix_bytes_received"], 262144)

    def test_replay_and_geometry_discrepancies(self):
        for record in self.evidence["records"]:
            result = audit.assess(record["headers"][1])
            self.assertEqual(result, record["assessment"])
            self.assertEqual(result["missing_documented_flags"], [])
            self.assertEqual(result["flags_not_boolean_true"], [])
            self.assertAlmostEqual(result["dsun_m_divided_by_hee_numeric_norm"], 1000)
            self.assertFalse(result["observer_units_consistent_if_both_meters"])
            self.assertFalse(result["measurement_authorized"])
            self.assertEqual(result["wcs_a_types"], ["RA---ZPN", "DEC--ZPN"])
            self.assertEqual(result["wcs_b_types"], ["HPLN-ZPN", "HPLT-ZPN"])

    def test_exact_header_cards_and_bounded_parser(self):
        for record in self.evidence["records"]:
            chunks = [s.encode("ascii") for s in record["header_cards_ascii"]]
            self.assertEqual(audit.first_two_headers(b"".join(chunks)), chunks)
            self.assertEqual([audit.digest(b) for b in chunks], record["header_sha256"])
            with self.assertRaises(ValueError):
                audit.first_two_headers(b"".join(chunks)[:2880])

    def test_refuse_nonempty_primary(self):
        chunks = self.evidence["records"][0]["header_cards_ascii"]
        data = (
            "".join(chunks)
            .encode("ascii")
            .replace(
                b"NAXIS   =                    0", b"NAXIS   =                    1", 1
            )
        )
        with self.assertRaisesRegex(ValueError, "Primary data"):
            audit.first_two_headers(data)

    def test_missing_false_and_string_flags_are_not_passes(self):
        header = dict(self.evidence["records"][0]["headers"][1])
        del header["ISVIABLE"]
        header["ISNORMAL"] = "True"
        header["EPVALID"] = False
        result = audit.assess(header)
        self.assertIn("ISVIABLE", result["missing_documented_flags"])
        self.assertEqual(set(result["flags_not_boolean_true"]), {"ISNORMAL", "EPVALID"})

    def test_invalid_geometry_does_not_look_consistent(self):
        for value in (None, float("nan"), "149000000"):
            header = dict(self.evidence["records"][0]["headers"][1])
            header["HEEX_OBS"] = value
            self.assertIsNone(
                audit.assess(header)["dsun_m_divided_by_hee_numeric_norm"]
            )
            self.assertFalse(audit.assess(header)["measurement_authorized"])

    def test_source_bundle_binds_execution_and_inventory(self):
        with ZipFile(ROOT / "results/unblock-sources-20260906.zip") as bundle:
            self.assertEqual(
                audit.digest(bundle.read("audit_retrospective.py")),
                self.evidence["collect_script_sha256"],
            )
            ledger = self.evidence["acquisition_ledger"]
            self.assertEqual(
                audit.digest(bundle.read("probe_retrospective.ps1")),
                ledger["script_sha256"],
            )
            for record in ledger["records"][:2]:
                data = bundle.read(record["file"])
                self.assertEqual(len(data), record["bytes"])
                self.assertEqual(audit.digest(data), record["sha256"])
            self.assertEqual(
                audit.digest(
                    bundle.read(
                        "SWFO_CCOR-2_Operational_Product_Metadata_Definitions_V1.0.pdf"
                    )
                ),
                "0bc3ce7f25c6b309c64f940753010f343f35599f125f70a7fb7f8b00e13f766c",
            )


if __name__ == "__main__":
    unittest.main()
