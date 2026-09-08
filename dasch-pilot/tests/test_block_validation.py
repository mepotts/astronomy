import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import block_validation as bv


def fixture():
    return [{"series": s, "year": y+j/12, "jd": y*365+j, "ct": 0., "mag": 10.}
            for s in ("a", "b") for y in range(1880, 1990) for j in range(3)]


class BlockTests(unittest.TestCase):
    def test_fixed_family(self):
        self.assertEqual(len(bv.GRID), 55)
        self.assertEqual(len(set(bv.GRID)), 55)
        self.assertTrue(all(y+d <= 1990 for y, d in bv.GRID))

    def test_instrumental_controls_match_original_usable_set(self):
        controls = json.loads((bv.CONTROL / "results.json").read_bytes())["controls"]
        self.assertEqual([c["spss_id"] for c in controls if not c["development"] and c["unique_match"]],
                         [44, 113, 116, 120])

    def test_constant_and_full_block_injection(self):
        for sign in (-1, 1):
            rows = fixture()
            self.assertFalse(bv.block(rows, 1930, 20)["positive_flag"])
            for row in rows:
                if 1930 <= row["year"] < 1950:
                    row["mag"] += sign
            b = bv.block(rows, 1930, 20)
            self.assertTrue(b["eligible"])
            self.assertEqual(b["series_medians"], {"a": sign, "b": sign})
            self.assertEqual(b["positive_flag"], sign > 0)
            self.assertEqual(b["negative_flag"], sign < 0)

    def test_missing_one_baseline_side_is_not_quiet(self):
        rows = [r for r in fixture() if r["year"] >= 1930]
        b = bv.block(rows, 1930, 20)
        self.assertFalse(b["eligible"])
        self.assertGreater(b["missing_before"], 0)

    def test_colour_support_must_exist_on_both_sides(self):
        rows = fixture()
        for r in rows:
            if r["year"] > 1950:
                r["ct"] = -2
        self.assertFalse(bv.block(rows, 1930, 20)["eligible"])

    def test_single_series_cannot_pass(self):
        rows = [r for r in fixture() if r["series"] == "a"]
        self.assertFalse(bv.block(rows, 1930, 20)["eligible"])

    def test_series_zero_point_cancels(self):
        rows = fixture()
        for r in rows:
            if r["series"] == "b":
                r["mag"] += 2
        self.assertEqual(bv.block(rows, 1930, 20)["series_medians"], {"a": 0, "b": 0})

    def test_guard_years_cannot_leak_into_baseline(self):
        rows = fixture()
        for r in rows:
            if 1929 <= r["year"] < 1930 or 1950 <= r["year"] < 1951:
                r["mag"] = 1000
        self.assertEqual(bv.block(rows, 1930, 20)["series_medians"], {"a": 0, "b": 0})

    def test_failed_development_prevents_holdout_requests(self):
        with patch.object(Path, "read_bytes", return_value=b'{"contract": {}, "gate": "STOP_BLOCK_DEVELOPMENT"}'), \
                patch.object(bv, "contract", return_value={}), patch.object(bv, "HoldoutArchive") as archive, \
                self.assertRaisesRegex(ValueError, "holdout acquisition forbidden"):
            bv.holdout()
        archive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
