"""Synthetic numerical-core checks only: never load a real PRF or science image."""

import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

SPEC = importlib.util.spec_from_file_location("prf_author", Path(__file__).parents[1] / "scripts/prf_model.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def gaussian():
    y, x = (np.indices((117, 117)) - 58) / 9
    return np.exp(-.5 * ((x / .85)**2 + (y / 1.2)**2))


def grid(arrays=None, origin=(1000., 1000.)):
    arrays = np.stack([gaussian()] * 4) if arrays is None else arrays
    return P.PRFGrid(arrays, [900, 1100], [900, 1100], origin)


def science(g, x=5.27, y=4.63, amplitude=7.):
    model, _ = g.image(x, y, (11, 11))
    yy, xx = np.indices((11, 11))
    return amplitude * model + .2 + .03 * (xx - 5) / 10 - .04 * (yy - 5) / 10


class InterpolationTests(unittest.TestCase):
    def test_all_81_exact_phase_arrays_asymmetric_axes_and_sign(self):
        yy, xx = np.indices((117, 117))
        values = 10000 * yy + xx + 1.
        g = grid(np.stack([values] * 4))
        py, px = np.mgrid[-6:7, -6:7]
        for phase_y in range(9):
            for phase_x in range(9):
                actual = g.sample(px, py, (4 - phase_x) / 9, (4 - phase_y) / 9, corner=0)
                expected = values[phase_y::9, phase_x::9]
                with self.subTest(x=phase_x, y=phase_y):
                    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)

    def test_bilinear_subpixel_reproduces_affine_surface(self):
        yy, xx = np.indices((117, 117))
        g = grid(np.stack([2 * xx + 3 * yy + 5.] * 4))
        actual = g.sample(.12, -.23, .31, -.11, corner=0)
        expected = 2 * (58 + 9 * (.12 - .31)) + 3 * (58 + 9 * (-.23 + .11)) + 5
        self.assertAlmostEqual(float(actual), expected, places=12)

    def test_field_weights_true_corners_and_interior(self):
        arrays = np.stack([np.full((117, 117), n) for n in (1., 3., 5., 9.)])
        g = grid(arrays, origin=(900, 900))
        for index, xy in enumerate(((0, 0), (200, 0), (0, 200), (200, 200))):
            np.testing.assert_array_equal(g.weights(*xy), np.eye(4)[index])
        np.testing.assert_allclose(g.weights(50, 150), [.1875, .0625, .5625, .1875])
        self.assertAlmostEqual(float(g.sample(50, 150, 50, 150)), np.dot([1, 3, 5, 9], g.weights(50, 150)))
        for xy in ((-1e-6, 0), (201, 0), (0, -1), (0, 201)):
            with self.assertRaisesRegex(ValueError, "EXTRAPOLATION"):
                g.image(*xy, (11, 11), corner=0)

    def test_integer_translation_and_positive_direction(self):
        g = grid()
        first, _ = g.image(8.2, 8.3, (21, 21))
        second, _ = g.image(9.2, 9.3, (21, 21))
        np.testing.assert_allclose(first[:-1, :-1], second[1:, 1:], atol=2e-16, rtol=0)
        self.assertEqual(np.unravel_index(np.argmax(second), second.shape), (9, 9))

    def test_integer_phase_continuity_and_nonzero_boundary_taper(self):
        g = grid(np.ones((4, 117, 117)))
        eps = 1e-8
        self.assertAlmostEqual(float(g.sample(P.RADIUS, 0, 0, 0)), 0.)
        self.assertAlmostEqual(float(g.sample(P.RADIUS - eps, 0, 0, 0)), 9 * eps, places=12)
        self.assertEqual(float(g.sample(P.RADIUS + eps, 0, 0, 0)), 0.)
        for x in (5., 5 + 4 / 9, 5 + 5 / 9):
            left, _ = g.image(x - eps, 5., (15, 15))
            right, _ = g.image(x + eps, 5., (15, 15))
            self.assertLess(np.max(np.abs(left - right)), 2e-8)

    def test_full_support_normalization_before_crop(self):
        g = grid()
        whole, wm = g.image(10.2, 10.3, (23, 23))
        self.assertAlmostEqual(float(whole.sum()), 1., places=14)
        self.assertAlmostEqual(wm["lost_wing_fraction"], 0., places=14)
        crop, meta = g.image(.2, .3, (11, 11))
        self.assertLess(float(crop.sum()), .8)
        self.assertEqual(meta["lost_wing_fraction"], 1 - float(crop.sum()))
        np.testing.assert_allclose(crop, whole[10:21, 10:21], atol=2e-16, rtol=0)
        self.assertFalse(meta["true_infinite_flux"])

    def test_grid_validation_copy_and_nonpositive_support(self):
        arrays = np.stack([gaussian()] * 4)
        g = grid(arrays)
        arrays[:] = 0
        self.assertGreater(float(g.image(5, 5, (11, 11))[0].sum()), .99)
        with self.assertRaises(ValueError):
            P.PRFGrid(arrays, [1, 1], [1, 2], [0, 0])
        with self.assertRaisesRegex(ValueError, "NORMALIZATION"):
            grid(np.zeros((4, 117, 117))).image(5, 5, (11, 11))


class FitTests(unittest.TestCase):
    def setUp(self):
        self.g = grid()
        self.error = np.full((11, 11), .02)
        self.valid = np.ones((11, 11), dtype=bool)

    def test_signed_position_amplitude_plane_recovery(self):
        for amplitude in (7., -7.):
            result = P.fit(science(self.g, amplitude=amplitude), self.error, self.valid, self.g)
            with self.subTest(amplitude=amplitude):
                self.assertTrue(result["success"], result)
                np.testing.assert_allclose([result["x"], result["y"]], [5.27, 4.63], atol=1e-5, rtol=0)
                self.assertAlmostEqual(result["amplitude"], amplitude, places=5)
                np.testing.assert_allclose(result["plane"], [.2, .03, -.04], atol=1e-6, rtol=0)
                self.assertLess(result["weighted_residual_sum"], 1e-8)
                self.assertIsNotNone(result["centroid_covariance"])

    def test_fixed_hypothesis_signed_score_and_error_covariance_scaling(self):
        data = science(self.g)
        first = P.fit(data, self.error, self.valid, self.g)
        second = P.fit(data, self.error * 2, self.valid, self.g)
        np.testing.assert_allclose(np.array(first["centroid_covariance"]) * 4, second["centroid_covariance"], rtol=1e-4)
        fixed = P.fixed_hypothesis(data, self.error, self.valid, self.g, 5.27, 4.63)
        wrong = P.fixed_hypothesis(data, self.error, self.valid, self.g, 6., 4.63)
        self.assertGreater(wrong["weighted_residual_sum"], fixed["weighted_residual_sum"] + 10)
        self.assertEqual(first["nominal_ellipse_threshold"], -2 * np.log(.05))

    def test_integer_coordinate_covariance_uses_float_perturbations(self):
        data = science(self.g)
        _, sigma, mask, plane = P.inputs(data, self.error, self.valid)
        lo, hi = P.bounds(self.g, data.shape)
        integer, status = P.covariance(self.g, 5, 5, data.shape, 7., sigma, mask, plane, lo, hi)
        floating, _ = P.covariance(self.g, 5., 5., data.shape, 7., sigma, mask, plane, lo, hi)
        self.assertEqual(status, "NOMINAL_DIAGONAL_PIXEL_ERRORS_NO_RESIDUAL_RESCALING")
        np.testing.assert_array_equal(integer, floating)

    def test_masked_nonfinite_pixels_preserved_as_null_residuals(self):
        data = science(self.g)
        self.valid[0, 0] = False
        data[0, 0] = self.error[0, 0] = np.nan
        result = P.fit(data, self.error, self.valid, self.g)
        self.assertTrue(result["success"], result)
        self.assertIsNone(result["residual"][0][0])
        json.dumps(result, allow_nan=False)

    def test_rank_and_invalid_inputs_reported(self):
        constant = grid(np.ones((4, 117, 117)))
        result = P.fixed_hypothesis(np.ones((11, 11)), self.error, self.valid, constant, 5., 5.)
        self.assertFalse(result["success"])
        self.assertIn("RANK", result["status"])
        self.error[2, 2] = 0
        self.assertFalse(P.fit(science(self.g), self.error, self.valid, self.g)["success"])
        self.assertFalse(P.fixed_hypothesis(science(self.g), np.ones((11, 11)), self.valid, self.g, -1, 5)["success"])

    def test_flat_amplitude_covariance_unavailable_not_detection(self):
        result = P.fit(np.zeros((11, 11)), self.error, self.valid, self.g)
        self.assertIsNone(result["centroid_covariance"])
        self.assertFalse(result["localization_validated"])

    def test_bound_solution_retained_as_unsuccessful_diagnostic(self):
        data = science(self.g, x=-.5, y=5.)
        result = P.fit(data, self.error, self.valid, self.g)
        self.assertFalse(result["success"], result)
        self.assertTrue(result["bound_hit"], result)
        self.assertIn("model", result)

    def test_solver_active_flag_alone_marks_bound(self):
        data = science(self.g)
        optimized = SimpleNamespace(x=np.array([5.27, 4.63]), active_mask=np.array([1, 0]),
                                    success=True, nfev=1, message="synthetic active flag")
        with patch.object(P, "least_squares", return_value=optimized):
            result = P.fit(data, self.error, self.valid, self.g)
        self.assertTrue(result["bound_hit"])
        self.assertFalse(result["success"])
        self.assertEqual(result["optimizer_active_mask"], [1, 0])

    def test_determinism_and_optimizer_exhaustion(self):
        data = science(self.g)
        first, second = (P.fit(data, self.error, self.valid, self.g) for _ in range(2))
        self.assertEqual(first, second)
        self.assertLessEqual(first["evaluations"], 4 * P.MAX_NFEV)
        with patch.object(P, "MAX_NFEV", 1):
            result = P.fit(data, self.error, self.valid, self.g)
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
