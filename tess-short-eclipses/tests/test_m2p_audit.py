"""Synthetic checks of the separate post-run verifier, not scientific calibration."""

import importlib.util
import unittest
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "m2p_postrun_audit", Path(__file__).resolve().parents[1] / "scripts/m2p_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class AuditTests(unittest.TestCase):
    def test_label_failures_and_tie(self):
        rows = [{"source_id": "left", "x": 0., "y": 0.},
                {"source_id": "right", "x": 2., "y": 0.}]
        cases = [({"success": False, "bound_hit": True}, "BOUND"),
                 ({"success": False}, "FAILED"),
                 ({"success": True, "x": 0., "y": 0.}, "left"),
                 ({"success": True, "x": 1., "y": 0.}, "AMBIGUOUS")]
        for fit, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(AUDIT.classify(fit, rows), expected)

    def test_nominal_ellipse_and_undefined(self):
        cases = [([[1., 0.], [0., 1.]], True),
                 ([[.01, 0.], [0., .01]], False),
                 ([[0., 0.], [0., 1.]], None), (None, None)]
        for covariance, expected in cases:
            with self.subTest(covariance=covariance):
                fit = {"success": True, "x": 1., "y": 0., "centroid_covariance": covariance}
                covered, _ = AUDIT.trial_ellipse(fit, {"x": 0., "y": 0.})
                self.assertIs(covered, expected)

    def test_independent_sampler_integer_shift_and_full_wings(self):
        yy, xx = np.indices((117, 117))
        array = np.exp(-((xx - 58)**2 + (yy - 58)**2) / (2 * 18**2))
        arrays = np.array([array] * 4)
        context = {"origin": [0., 0.], "columns": [-20., 20.], "rows": [-20., 20.]}
        centered = AUDIT.independent_model(arrays, context, 5., 5.)
        shifted = AUDIT.independent_model(arrays, context, 6., 5.)
        np.testing.assert_allclose(centered[:, :-1], shifted[:, 1:], atol=1e-15, rtol=0)
        self.assertTrue(0 < shifted.sum() < centered.sum() < 1)
        with self.assertRaisesRegex(ValueError, "field bracket"):
            AUDIT.independent_model(arrays, context, 21., 5.)


if __name__ == "__main__":
    unittest.main()
