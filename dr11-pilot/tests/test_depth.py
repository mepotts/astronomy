import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from empirical_depth import ROOT, summary


class DepthTests(unittest.TestCase):
    def test_empty_and_noisy_not_passed(self):
        self.assertEqual(summary([])["gate"], "STOP_NO_MATERIAL_DEPTH_GAIN")
        pairs = [{k: {"mean_nmgy_arcsec2": i} for k in ("dr10", "dr11")} for i in range(40)]
        self.assertEqual(summary(pairs)["scatter_ratio"], 1)
        self.assertEqual(summary(pairs)["gate"], "STOP_NO_MATERIAL_DEPTH_GAIN")

    def test_real_gain_and_sample_size_gate(self):
        pairs = [{"dr10": {"mean_nmgy_arcsec2": i}, "dr11": {"mean_nmgy_arcsec2": .8*i}} for i in range(40)]
        self.assertEqual(summary(pairs)["gate"], "PASS_LOCAL_DEPTH_ONLY")
        self.assertEqual(summary(pairs[:20])["gate"], "STOP_NO_MATERIAL_DEPTH_GAIN")

    def test_retained_pair_arithmetic(self):
        saved = json.loads((ROOT / "results/depth-20260907/results.json").read_bytes())
        result = summary(saved["pairs"])
        self.assertEqual(result["gate"], saved["gate"])
        self.assertEqual(len(saved["pairs"]), 2258)
        np.testing.assert_allclose(result["scatter_ratio"], saved["scatter_ratio"], rtol=1e-10)

    def test_qualifying_footprint_invariants(self):
        with np.load(ROOT / "evidence/footprint-20260907.npz", allow_pickle=False) as z:
            self.assertEqual(len(z["brick"]), 8468)
            self.assertEqual(len(np.unique(z["brick"])), 8468)
            v = z["values"]
            self.assertTrue((v[:, 2] >= 1).all())
            self.assertTrue((v[:, 3] >= v[:, 2]+3).all())
            self.assertTrue((v[:, 3] >= 1.5*v[:, 2]).all())


if __name__ == "__main__":
    unittest.main()
