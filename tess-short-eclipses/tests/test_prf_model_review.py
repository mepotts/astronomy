"""Independent arithmetic oracles and synthetic-only PRF regression cases."""

import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

SPEC = importlib.util.spec_from_file_location("review_prf_model", Path(__file__).parents[1] / "scripts/prf_model.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def node(array, y, x):
    return array[y, x] if 0 <= y < 117 and 0 <= x < 117 else 0.


def oracle_sample(array, pixel_x, pixel_y, source_x, source_y):
    """Scalar four-node oracle, without the author's sampler/interpolator."""
    u = 58 + 9 * (pixel_x - source_x)
    v = 58 + 9 * (pixel_y - source_y)
    i, j = int(np.floor(u)), int(np.floor(v))
    a, b = u - i, v - j
    return ((1 - a) * (1 - b) * node(array, j, i) + a * (1 - b) * node(array, j, i + 1)
            + (1 - a) * b * node(array, j + 1, i) + a * b * node(array, j + 1, i + 1))


def oracle_image(array, x, y, shape=(11, 11)):
    total = sum(oracle_sample(array, ix, iy, x, y)
                for iy in range(int(np.floor(y)) - 8, int(np.floor(y)) + 9)
                for ix in range(int(np.floor(x)) - 8, int(np.floor(x)) + 9))
    return np.array([[oracle_sample(array, ix, iy, x, y) / total for ix in range(shape[1])]
                     for iy in range(shape[0])]), total


def asymmetric():
    y, x = np.indices((117, 117), dtype=float)
    return 1 + x / 23 + y / 47 + x * y / 1999


def gaussian():
    y, x = np.indices((117, 117), dtype=float)
    return np.exp(-((x - 58) / 8.) ** 2 / 2 - ((y - 58) / 12.) ** 2 / 2)


def grid(array=None):
    array = gaussian() if array is None else array
    return P.PRFGrid([array] * 4, rows=[100, 140], columns=[200, 240], origin=[210, 110])


def observed(g, x=4.23, y=5.71, amplitude=7.):
    model, _ = g.image(x, y, (11, 11))
    yy, xx = np.indices(model.shape)
    data = amplitude * model + .17 + .009 * xx - .013 * yy
    return data, np.ones_like(data), np.ones_like(data, dtype=bool)


class IndependentNumerics(unittest.TestCase):
    def test_all_81_phases_against_asymmetric_scalar_oracle(self):
        array = asymmetric()
        g = grid(array)
        for p in range(9):
            for q in range(9):
                x, y = 5 + p / 9, 5 + q / 9
                expected, total = oracle_image(array, x, y)
                actual, info = g.image(x, y, (11, 11))
                with self.subTest(p=p, q=q):
                    np.testing.assert_allclose(actual, expected, rtol=0, atol=3e-16)
                    self.assertAlmostEqual(info["full_support_normalization"], total, places=10)

    def test_positive_source_offset_and_row_column_order(self):
        array = np.zeros((117, 117))
        array[76, 67] = 1
        g = grid(array)
        self.assertEqual(float(g.sample(6, 7, 5, 5)), 1)
        self.assertEqual(float(g.sample(7, 6, 5, 5)), 0)
        self.assertEqual(float(g.sample(7, 8, 6, 6)), 1)
        self.assertEqual(float(g.sample(5, 6, 6, 6)), 0)

    def test_zero_nodal_extension_tapers_edge_and_corner(self):
        g = grid(np.ones((117, 117)))
        self.assertAlmostEqual(float(g.sample(0, 0, 58.5 / 9, 0)), .5, places=13)
        self.assertAlmostEqual(float(g.sample(0, 0, 58.5 / 9, 58.5 / 9)), .25, places=13)
        self.assertEqual(float(g.sample(0, 0, 59 / 9, 0)), 0)
        self.assertEqual(float(g.sample(0, 0, 59 / 9 + 1e-8, 0)), 0)

    def test_image_continuity_across_integer_and_support_transitions(self):
        g = grid(asymmetric())
        for center in (5., 5.5, 5 + 4 / 9):
            left, _ = g.image(center - 1e-8, 5.3, (11, 11))
            right, _ = g.image(center + 1e-8, 5.3, (11, 11))
            self.assertLess(np.max(np.abs(left - right)), 1e-7)

    def test_normalization_precedes_crop_and_retains_wing_loss(self):
        array = asymmetric()
        g = grid(array)
        small, a = g.image(.2, .7, (3, 4))
        large, b = g.image(.2, .7, (11, 11))
        expected, total = oracle_image(array, .2, .7, (3, 4))
        np.testing.assert_allclose(small, large[:3, :4], rtol=0, atol=0)
        np.testing.assert_allclose(small, expected, rtol=0, atol=2e-16)
        self.assertAlmostEqual(a["full_support_normalization"], total, places=10)
        self.assertEqual(a["full_support_normalization"], b["full_support_normalization"])
        self.assertLess(small.sum(), 1)
        self.assertAlmostEqual(a["lost_wing_fraction"], 1 - small.sum())
        self.assertFalse(a["true_infinite_flux"])

    def test_field_corners_midpoint_and_no_extrapolation(self):
        arrays = [np.full((117, 117), value) for value in (1., 2., 4., 8.)]
        g = P.PRFGrid(arrays, [0, 10], [0, 20], [0, 0])
        for x, y, weights in ((0, 0, [1, 0, 0, 0]), (20, 0, [0, 1, 0, 0]),
                              (0, 10, [0, 0, 1, 0]), (20, 10, [0, 0, 0, 1])):
            np.testing.assert_array_equal(g.weights(x, y), weights)
        self.assertAlmostEqual(float(g.sample(10, 5, 10, 5)), 3.75)
        for x, y in ((-.001, 0), (20.001, 10), (0, 10.001)):
            with self.assertRaisesRegex(ValueError, "EXTRAPOLATION"):
                g.image(x, y, (11, 11))

    def test_constructor_copies_inputs_and_freezes_arrays(self):
        arrays = np.stack([gaussian()] * 4)
        g = P.PRFGrid(arrays, [100, 140], [200, 240], [210, 110])
        old = g.arrays.copy()
        arrays[:] = 0
        np.testing.assert_array_equal(g.arrays, old)
        with self.assertRaises(ValueError):
            g.arrays[0, 0, 0] = 42

    def test_fixed_signed_amplitudes_and_score_scale_not_probability(self):
        g = grid()
        for amplitude in (-7., 7.):
            data, sigma, mask = observed(g, amplitude=amplitude)
            result = P.fixed_hypothesis(data, sigma, mask, g, 4.23, 5.71)
            self.assertTrue(result["success"])
            self.assertAlmostEqual(result["amplitude"], amplitude, places=10)
            self.assertLess(result["weighted_residual_sum"], 1e-25)
            self.assertFalse(result["localization_validated"])
        wrong = P.fixed_hypothesis(data, sigma, mask, g, 5.23, 5.71)
        scaled = P.fixed_hypothesis(data, sigma * 2, mask, g, 5.23, 5.71)
        self.assertAlmostEqual(wrong["weighted_residual_sum"] / 4, scaled["weighted_residual_sum"])

    def test_fixed_outside_or_bad_hypothesis_is_explicit_failure(self):
        g = grid()
        data, sigma, mask = observed(g)
        for x, y in ((-1, 5), (5, 11), (float("nan"), 5)):
            result = P.fixed_hypothesis(data, sigma, mask, g, x, y)
            self.assertFalse(result["success"])
            self.assertFalse(result["localization_validated"])

    def test_rank_deficient_amplitude_plane_is_not_a_success(self):
        g = grid(np.ones((117, 117)))
        image = np.ones((5, 5))
        result = P.fixed_hypothesis(image, image, image.astype(bool), g, 2, 2)
        self.assertFalse(result["success"])
        self.assertIn("RANK", result["status"])

    def test_bad_errors_and_insufficient_mask_are_not_discarded(self):
        g = grid()
        data, sigma, mask = observed(g)
        sigma[4, 4] = 0
        self.assertFalse(P.fit(data, sigma, mask, g)["success"])
        mask[:] = False
        mask.flat[:24] = True
        self.assertFalse(P.fit(data, np.ones_like(data), mask, g)["success"])

    def test_fit_both_signs_deterministic_and_bounded(self):
        g = grid()
        for amplitude in (-7., 7.):
            data, sigma, mask = observed(g, amplitude=amplitude)
            a = P.fit(data, sigma, mask, g)
            b = P.fit(data, sigma, mask, g)
            self.assertTrue(a["success"], a)
            np.testing.assert_allclose([a["x"], a["y"], a["amplitude"]], [4.23, 5.71, amplitude], atol=2e-5, rtol=0)
            self.assertEqual(a, b)
            self.assertLessEqual(a["nfev"], P.MAX_NFEV)
            self.assertFalse(a["localization_validated"])

    def test_optimizer_nonconvergence_is_retained(self):
        g = grid()
        data, sigma, mask = observed(g)
        with patch.object(P, "MAX_NFEV", 1):
            result = P.fit(data, sigma, mask, g)
        self.assertFalse(result["success"])
        self.assertIn("OPTIMIZER", result["status"])

    def test_zero_signal_does_not_supply_centroid_covariance(self):
        g = grid()
        image = np.zeros((11, 11))
        result = P.fit(image, np.ones_like(image), np.ones_like(image, dtype=bool), g)
        self.assertIsNone(result["centroid_covariance"])
        self.assertFalse(result["localization_validated"])

    def test_nominal_covariance_matches_independent_six_parameter_jacobian(self):
        array = gaussian()
        g = grid(array)
        x, y, amplitude = 4.23, 5.71, 7.
        yy, xx = np.indices((11, 11))
        sigma = 1 + .03 * xx + .01 * yy
        mask = np.ones((11, 11), dtype=bool)
        plane = np.stack([np.ones((11, 11)), (xx - 5) / 10, (yy - 5) / 10], axis=-1)
        model = oracle_image(array, x, y)[0]
        step = 1e-4
        dx = (oracle_image(array, x + step, y)[0] - oracle_image(array, x - step, y)[0]) / (2 * step)
        dy = (oracle_image(array, x, y + step)[0] - oracle_image(array, x, y - step)[0]) / (2 * step)
        design = np.column_stack([model.ravel(), amplitude * dx.ravel(), amplitude * dy.ravel(),
                                  plane.reshape(-1, 3)]) / sigma.ravel()[:, None]
        expected = np.linalg.inv(design.T @ design)[1:3, 1:3]
        lower, upper = np.array([-.5, -.5]), np.array([10.5, 10.5])
        actual, status = P.covariance(g, x, y, (11, 11), amplitude, sigma, mask, plane, lower, upper)
        np.testing.assert_allclose(actual, expected, rtol=2e-8, atol=1e-10)
        self.assertEqual(status, "NOMINAL_DIAGONAL_PIXEL_ERRORS_NO_RESIDUAL_RESCALING")
        negative, _ = P.covariance(g, x, y, (11, 11), -amplitude, sigma, mask, plane, lower, upper)
        scaled, _ = P.covariance(g, x, y, (11, 11), amplitude, sigma * 2, mask, plane, lower, upper)
        np.testing.assert_allclose(negative, actual, rtol=1e-12)
        np.testing.assert_allclose(scaled, np.asarray(actual) * 4, rtol=1e-12)

    def test_hard_model_call_cap_counts_finite_difference_work(self):
        g = grid()
        data, sigma, mask = observed(g)

        def runaway(function, initial, **_kwargs):
            for _ in range(4 * P.MAX_NFEV + 1):
                function(initial)
            self.fail("residual evaluation guard did not interrupt")

        with patch.object(P, "least_squares", side_effect=runaway), patch.object(g, "image", wraps=g.image) as call:
            result = P.fit(data, sigma, mask, g)
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "STOP_MODEL_EVALUATION_CAP")
        self.assertEqual(call.call_count, 4 * P.MAX_NFEV)
        self.assertEqual(result["evaluations"], 4 * P.MAX_NFEV + 1)

    def test_masked_invalid_pixels_remain_null_not_filled_residuals(self):
        g = grid()
        data, sigma, mask = observed(g)
        data[0, 0], sigma[0, 0], mask[0, 0] = np.nan, np.nan, False
        result = P.fixed_hypothesis(data, sigma, mask, g, 4.23, 5.71)
        self.assertTrue(result["success"])
        self.assertEqual(result["points"], 120)
        self.assertIsNone(result["residual"][0][0])
        self.assertAlmostEqual(result["amplitude"], 7, places=10)

    def test_boundary_fit_is_explicit_failed_diagnostic(self):
        g = grid()
        data, sigma, mask = observed(g, x=-.5, y=5.71)
        optimized = SimpleNamespace(x=np.array([-.5, 5.71]), success=True, nfev=1,
                                    active_mask=np.array([-1, 0]), message="synthetic exact boundary result")
        with patch.object(P, "least_squares", return_value=optimized):
            result = P.fit(data, sigma, mask, g)
        self.assertFalse(result["success"])
        self.assertTrue(result["bound_hit"])
        self.assertEqual(result["optimizer_active_mask"], [-1, 0])
        self.assertEqual(result["status"], "STOP_FIT_BOUND_OR_OPTIMIZER")
        self.assertIn("amplitude", result)
        self.assertFalse(result["localization_validated"])

    def test_true_boundary_can_converge_inside_literal_fitted_bound_guard(self):
        """Retain a counterexample: bound_hit is not a true-position classifier."""
        g = grid()
        data, sigma, mask = observed(g, x=-.5, y=5.71)
        result = P.fit(data, sigma, mask, g)
        self.assertTrue(result["optimizer_success"])
        self.assertGreater(result["x"] - (-.5), 1e-5)
        self.assertFalse(result["bound_hit"])
        self.assertFalse(result["localization_validated"])

    def test_solver_active_bound_flag_stops_even_if_literal_distance_does_not(self):
        g = grid()
        data, sigma, mask = observed(g)
        optimized = SimpleNamespace(x=np.array([4.23, 5.71]), success=True, nfev=1,
                                    active_mask=np.array([-1, 0]), message="synthetic active constraint")
        with patch.object(P, "least_squares", return_value=optimized):
            result = P.fit(data, sigma, mask, g)
        self.assertEqual(result["optimizer_active_mask"], [-1, 0])
        self.assertTrue(result["bound_hit"])
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "STOP_FIT_BOUND_OR_OPTIMIZER")


if __name__ == "__main__":
    unittest.main()
