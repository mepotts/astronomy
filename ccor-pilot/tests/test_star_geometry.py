import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from star_geometry import OUT, assess, catalogue, measure


class StarGeometryTests(unittest.TestCase):
    def test_synthetic_star(self):
        yy, xx = np.indices((41, 41))
        data = np.random.default_rng(71).normal(0, 1, (41, 41))
        data += 50*np.exp(-((xx-20.5)**2+(yy-19.5)**2)/2)
        result = measure(data, np.zeros(data.shape, dtype=np.uint8), np.array([20., 20.]))
        self.assertTrue(result["ok"])
        self.assertLess(np.linalg.norm(np.array(result["centroid"])-[20.5, 19.5]), .2)

    def test_masked_star_is_not_recovered(self):
        data = np.random.default_rng(71).normal(0, 1, (41, 41))
        data[20, 20] = 100
        mask = np.zeros(data.shape, dtype=np.uint8)
        mask[20, 20] = 16
        self.assertFalse(measure(data, mask, np.array([20., 20.]))["ok"])

    def test_training_count_cannot_be_waived_by_good_holdout(self):
        rows = [{"ok": i >= 3, "centroid": [20., 20.], "prediction": [20., 20.]} for i in range(8)]
        self.assertEqual(assess([rows]*4)["gate"], "STOP_STAR_GEOMETRY")

    def test_bad_catalogue_not_empty_success(self):
        with self.assertRaises(ValueError):
            catalogue(b"error\n")

    def test_tracked_pixel_replay(self):
        expected = json.loads((OUT / "results.json").read_bytes())
        with np.load(OUT / "known-star-cutouts.npz", allow_pickle=False) as z:
            frames = []
            for i in range(4):
                rows = []
                for j in range(8):
                    prediction = z[f"prediction_{i}_{j}"]
                    actual = measure(z[f"data_{i}_{j}"], z[f"mask_{i}_{j}"], prediction)
                    saved = expected["measurements"][i][j]
                    self.assertEqual(actual["ok"], saved["ok"])
                    if "centroid" in actual:
                        np.testing.assert_allclose(actual["centroid"], saved["centroid"], rtol=0, atol=1e-6)
                    rows.append({**actual, "prediction": prediction})
                frames.append(rows)
        result = assess(frames)
        self.assertEqual(result["gate"], expected["gate"])
        for actual, saved in zip(result["frames"], expected["frames"], strict=True):
            self.assertEqual(actual["passed"], saved["passed"])
            np.testing.assert_allclose(actual["rms"], saved["rms"], atol=1e-6)


if __name__ == "__main__":
    unittest.main()
