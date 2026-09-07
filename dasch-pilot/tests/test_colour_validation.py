import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from colour_validation import joined, select_twelve, window
from exploratory_search import select_sources


def fixture():
    return [{"series": s, "year": y+j/12, "jd": y*365+j, "ct": 0., "mag": 10.}
            for s in ("a", "b") for y in range(1900, 1980) for j in range(2)]


class ColourTests(unittest.TestCase):
    def test_constant_and_injected(self):
        rows = fixture()
        self.assertTrue(window(rows, 1950)["eligible"])
        self.assertFalse(window(rows, 1950)["positive_flag"])
        self.assertTrue(window(rows, 1950, 1)["positive_flag"])
        self.assertTrue(window(rows, 1950, -1)["negative_flag"])

    def test_colour_confounded_epoch_is_missing_not_quiet(self):
        rows = fixture()
        for r in rows:
            if 1950 <= r["year"] < 1955:
                r.update(ct=-2, mag=12)
        result = window(rows, 1950)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["matched_n"], 0)

    def test_series_offset_is_removed(self):
        rows = fixture()
        for r in rows:
            if r["series"] == "b":
                r["mag"] += 2
        self.assertEqual(window(rows, 1950)["series_medians"], {"a": 0., "b": 0.})

    def test_single_series_cannot_confirm(self):
        self.assertFalse(window([r for r in fixture() if r["series"] == "a"], 1950, 1)["eligible"])

    def test_true_window_not_fit_away(self):
        rows = fixture()
        for r in rows:
            if 1950 <= r["year"] < 1955:
                r["mag"] += 1
        self.assertTrue(window(rows, 1950)["positive_flag"])

    def test_holdouts_preselected(self):
        from colour_validation import old
        stars = select_twelve(old("table3"))
        self.assertEqual([r["spss_id"] for r in stars], [11, 13, 14, 24, 27, 43, 44, 101, 104, 113, 116, 120])

    def test_conflict_strict_stop_and_variant_quarantine(self):
        row = {"series": "a", "plate_number": "1", "mosaic_number": "0", "solution_number": "0", "exposure_number": "1"}
        exp = {"series": "a", "platenum": "1", "mosnum": "0", "solnum": "0", "expnum": "0"}
        with patch("colour_validation.clean", return_value=[row]):
            with self.assertRaisesRegex(ValueError, "exposure number"):
                joined([row], [exp])
            data, account = joined([row], [exp], quarantine=True)
            self.assertEqual(data, [])
            self.assertEqual(account["excluded"], {"exposure_conflict": 1})

    def test_catalogue_screen_is_capped_and_known_variable_flag_vetoes(self):
        center = {"ra_deg": 0, "dec_deg": 0}
        rows = [{"ref_number": str(i), "stdmag": "11", "color": ".5", "ra_deg": ".1", "dec_deg": ".1", "num_matches": "600", "v_flag": "0", "mag_flag": "0"} for i in range(40)]
        rows[0]["v_flag"] = "1"
        result = select_sources(rows, center)
        self.assertEqual(len(result), 32)
        self.assertEqual(result[0]["ref_number"], "1")


if __name__ == "__main__":
    unittest.main()
