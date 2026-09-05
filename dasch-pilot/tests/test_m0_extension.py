from __future__ import annotations

import base64
import gzip
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("m0_extension", SCRIPTS / "m0_extension.py")
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def detection(jd="2429213.5", **kwargs):
    return {"date_jd": jd, "magcal_magdep": "12.8", "aflags": "0",
            "ra_deg": "306", "dec_deg": "33", "ra_cat_corrected": "306",
            "dec_cat_corrected": "33", "ref_number": "17", "gsc_bin_index": "23", **kwargs}


class ExtensionTests(unittest.TestCase):
    def test_missing_flags_cannot_be_good_detection(self):
        with self.assertRaisesRegex(ValueError, "missing quality flags"):
            M.clean([detection(aflags="")])

    def test_sparse_bright_excursions_never_become_quiet(self):
        result = M.summarize([detection("2420000"), detection("2430000")], 2)
        self.assertFalse(result["access_gate"])
        self.assertEqual(result["coverage_verdict"], "INSUFFICIENT_COVERAGE")

    def test_wrong_source_rejected_even_with_matching_count(self):
        with self.assertRaisesRegex(ValueError, "different catalog source"):
            M.summarize([detection()], 1, {"ref_number": "18", "gsc_bin_index": "23"})

    def test_catalog_count_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "accounting mismatch"):
            M.summarize([detection()], 2)

    def test_two_close_sources_are_ambiguous(self):
        pos = {"ra_deg": 306, "dec_deg": 33}
        self.assertIsNone(M.select_source([pos, {**pos, "ra_deg": 306.0001}], pos))

    def test_distant_source_not_substituted(self):
        self.assertIsNone(M.select_source([{"ra_deg": 306.01, "dec_deg": 33}],
                                         {"ra_deg": 306, "dec_deg": 33}))

    def test_raw_api_camel_case_and_malformed_rows(self):
        self.assertEqual(M.table(b'["dateJd,magcalMagdep", "1,2"]'),
                         [{"date_jd": "1", "magcal_magdep": "2"}])
        with self.assertRaisesRegex(ValueError, "malformed"):
            M.table(b'["dateJd,magcalMagdep", "1,2,3"]')

    def test_cutout_must_be_fits(self):
        raw = json.dumps(base64.b64encode(gzip.compress(b"not fits")).decode()).encode()
        with self.assertRaisesRegex(ValueError, "not a primary FITS"):
            M.decode_cutout(raw)

    def test_tampered_cached_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = M.Archive(Path(tmp))
            path = Path(tmp) / "test.raw"
            path.write_bytes(b"original")
            archive.manifest["artifacts"]["test"] = {
                "file": "test.raw", "bytes": 8, "sha256": M.sha256_file(path),
            }
            archive.verify()
            path.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "mutated"):
                archive.verify()

    def test_cached_path_cannot_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = M.Archive(Path(tmp))
            archive.manifest["artifacts"]["test"] = {
                "file": "../outside.raw", "bytes": 8, "sha256": "irrelevant",
            }
            with self.assertRaisesRegex(ValueError, "escapes"):
                archive.verify()

    def test_committed_bundle_reproduces_without_loose_responses(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for name in ("provenance.json", "known-control-responses.tar.gz"):
                shutil.copyfile(M.RUN / name, directory / name)
            archive = M.Archive(directory)
            rows = M.table(archive.get("v404cyg-lightcurve"))
            result = M.summarize(rows, 32)
            self.assertEqual(result["clean_detections"], 5)
            self.assertFalse(result["access_gate"])
            self.assertEqual(len(archive.manifest["artifacts"]), 19)

    def test_text_hash_is_cross_platform_but_not_content_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "protocol.md"
            path.write_bytes(b"first\nsecond\n")
            original = M.text_sha256(path)
            path.write_bytes(b"first\r\nsecond\r\n")
            self.assertEqual(M.text_sha256(path), original)
            path.write_bytes(b"changed\nsecond\n")
            self.assertNotEqual(M.text_sha256(path), original)


if __name__ == "__main__":
    unittest.main()
