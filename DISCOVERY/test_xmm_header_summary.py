"""The public structural derivative never emits coordinate-bearing cards."""

import json
import unittest

import xmm_header_summary as module
from astropy.io.fits import Header


class SummaryTests(unittest.TestCase):
    def test_allowlist_and_duplicate_preservation(self):
        header = Header()
        for key, value in (("OBS_ID", "0884250101"), ("TIMESYS", "TT"),
                           ("TIMESYS", "UTC"), ("RA_PNT", 123.456789),
                           ("TCRVL1", 123.456789), ("CONTACT", "secret@example.test"),
                           ("2DSREF2", ":STDGTI02"),
                           ("TFIELDS", 1), ("TTYPE1", "TIME"), ("TFORM1", "D"),
                           ("TUNIT1", "s"), ("NAXIS2", 9)):
            header.append((key, value))
        report = {"status": "HEADER_LAYOUT_ONLY", "file_bytes": 8640, "hdu_count": 1,
                  "header_bytes_read": 2880, "declared_data_region_bytes_read": 0,
                  "hdus": [{"hdu": 0, "extname": "EVENTS", "data_bytes": 72,
                            "cards": [str(card) for card in header.cards]}]}
        result = module.summarize(report)
        text = json.dumps(result)
        self.assertNotIn("123.456789", text)
        self.assertNotIn("secret@example.test", text)
        self.assertEqual(result["hdus"][0]["metadata"]["TIMESYS"], ["TT", "UTC"])
        self.assertEqual(result["hdus"][0]["wcs_keys_present"], ["TCRVL1"])
        self.assertEqual(result["hdus"][0]["data_subspace_keys_present"], ["2DSREF2"])
        self.assertEqual(result["hdus"][0]["columns"],
                         [{"name": "TIME", "format": "D", "unit": "s"}])

    def test_image_geometry_metadata_without_coordinate_values(self):
        header = Header()
        for key, value in (("NAXIS", 2), ("NAXIS1", 8), ("NAXIS2", 6), ("BITPIX", -32),
                           ("BUNIT", "s"), ("E_MIN", 200), ("E_MAX", 12000),
                           ("OOTCORR", True), ("OOTFRAC", .063), ("CTYPE1", "RA---TAN"),
                           ("CTYPE2", "DEC--TAN"), ("CRVAL1", 123.456789),
                           ("CRVAL2", -54.123456), ("CD1_1", .000123),
                           ("OBSERVER", "private name"), ("HISTORY", "private history")):
            header.append((key, value))
        report = {"status": "HEADER_LAYOUT_ONLY", "file_bytes": 5760, "hdu_count": 1,
                  "header_bytes_read": 2880, "declared_data_region_bytes_read": 0,
                  "hdus": [{"hdu": 0, "extname": "PRIMARY", "data_bytes": 192,
                            "cards": [str(card) for card in header.cards]}]}
        result = module.summarize(report)
        row = result["hdus"][0]
        self.assertEqual(row["axis_lengths"], [8, 6])
        self.assertEqual(row["bitpix"], -32)
        self.assertEqual(row["metadata"]["BUNIT"], ["s"])
        self.assertEqual(row["metadata"]["E_MIN"], [200])
        self.assertEqual(row["wcs_keys_present"], ["CD1_1", "CRVAL1", "CRVAL2", "CTYPE1", "CTYPE2"])
        for forbidden in ("123.456789", "54.123456", "0.000123", "private name", "private history"):
            self.assertNotIn(forbidden, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
