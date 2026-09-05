"""Regression checks for classification priority and invalid inference withdrawal."""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "verify_census", Path(__file__).resolve().parents[1] / "scripts/verify_census_package.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CensusTests(unittest.TestCase):
    def row(self, **extra):
        return dict(ul_presence="1.0", in_dr2_any_sep="", nn2_bright_sep_arcsec="",
                    next_sep_arcsec="", **extra)

    def test_missing_neighbours_do_not_create_confusion(self):
        self.assertEqual(MODULE.classify(self.row(), 1.5), "FADE-CANDIDATE")

    def test_geometric_match_precedes_blank_presence(self):
        row = self.row()
        row.update(in_dr2_any_sep="10", ul_presence="0")
        self.assertEqual(MODULE.classify(row, 1.5), "ARTIFACT-SPLIT/MOVED")

    def test_psf_confuser_blocks_fading_class(self):
        row = self.row()
        row["nn2_bright_sep_arcsec"] = "39"
        self.assertEqual(MODULE.classify(row, 1.5), "CONFUSED-IDENTITY")

    def test_real_artifacts_never_claim_candidate_purity(self):
        result = MODULE.audit(Path(__file__).resolve().parents[1])
        self.assertEqual(result["failure_count"], 0)
        self.assertIsNone(result["selected_candidate_contamination"])
        self.assertIsNone(result["confirmed_physical_faders"])


if __name__ == "__main__":
    unittest.main()
