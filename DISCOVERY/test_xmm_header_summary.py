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


if __name__ == "__main__":
    unittest.main()
