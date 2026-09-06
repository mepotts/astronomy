import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stable_controls as s


class StableContracts(unittest.TestCase):
    def test_published_selection_and_original_stop(self):
        with zipfile.ZipFile(ROOT / "data/stable-20260906/responses.zip") as z:
            raw = z.read("table3.raw")
        self.assertEqual(s.select(raw), [])
        self.assertEqual([r["spss_id"] for r in s.select(raw, True)], [11, 13, 14, 24, 27, 43])

    def test_not_century_truth(self):
        result = json.loads((ROOT / "data/stable-normalized-20260906/results.json").read_bytes())
        self.assertEqual(result["useful_coverage"], 6)
        self.assertFalse(result["century_scale_false_positive_rate_measured"])
        self.assertFalse(result["blind_search_authorized"])

    def test_empty_is_not_stable(self):
        self.assertEqual(s.excursions([]), {"eligible_years": 0, "flagged_years": []})

    def test_short_or_duplicate_table_rejected(self):
        with self.assertRaises(ValueError):
            s.select(b"broken")
        with zipfile.ZipFile(ROOT / "data/stable-20260906/responses.zip") as z:
            raw = z.read("table3.raw")
        with self.assertRaises(ValueError):
            s.select(raw + b"\n" + raw, True)


if __name__ == "__main__":
    unittest.main()
