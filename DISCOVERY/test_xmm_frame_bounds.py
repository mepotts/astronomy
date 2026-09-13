"""Synthetic-only tests; no astronomy arrays, products or network."""

import unittest

import numpy as np
from xmm_frame_bounds import FrameBounds, exposure_bounds


class FrameBoundsTests(unittest.TestCase):
    def test_known_interior_and_unbounded_exterior(self):
        out = exposure_bounds([0, 1, 2, 3, 4], [1, 2, 3, 4, 5], [[0, 4]], [[-10, 10]])
        self.assertEqual(out["lower_exposure_s"], 9)
        self.assertEqual(out["upper_exposure_s"], 15)
        self.assertEqual(out["fully_contained_frames"], 3)
        self.assertEqual(out["uncertain_frames"], 2)
        self.assertEqual(out["outside_frames"], 0)

    def test_touching_is_not_positive_overlap(self):
        out = exposure_bounds([0, 1, 2, 3], [1, 2, 3, 4], [[1, 2]], [[1, 2]])
        self.assertEqual(out["lower_exposure_s"], 0)
        self.assertEqual(out["upper_exposure_s"], 5)
        self.assertEqual(out["outside_frames"], 2)

    def test_disconnected_union_never_counts_frame_twice(self):
        out = exposure_bounds([0, 10, 20], [2, 7, 3], [[1, 3], [17, 19]], [[0, 20]])
        self.assertEqual(out["lower_exposure_s"], 0)
        self.assertEqual(out["upper_exposure_s"], 12)
        self.assertEqual(out["accepted_gti_intervals"], 2)

    def test_union_overlap_and_touching_merge_before_containment(self):
        out = exposure_bounds([0, 1, 2], [2, 7, 3], [[1, 2], [0, 1], [.5, 1.5]], [[0, 2]])
        self.assertEqual(out["lower_exposure_s"], 7)
        self.assertEqual(out["upper_exposure_s"], 12)
        self.assertEqual(out["accepted_gti_intervals"], 1)

    def test_gti_cut_prevents_false_containment(self):
        out = exposure_bounds([0, 1, 2], [2, 7, 3], [[0, 2]], [[0, .9], [1.1, 2]])
        self.assertEqual(out["lower_exposure_s"], 0)
        self.assertEqual(out["upper_exposure_s"], 12)

    def test_long_omitted_frame_gap_never_becomes_exposure(self):
        out = exposure_bounds([0, 1, 1000, 1001], [.5] * 4, [[200, 800]], [[0, 1001]])
        self.assertEqual(out["lower_exposure_s"], 0)
        self.assertEqual(out["upper_exposure_s"], 1)

    def test_single_frame_has_unbounded_support(self):
        out = exposure_bounds([10], [2], [[100, 101]], [[100, 101]])
        self.assertEqual(out["lower_exposure_s"], 0)
        self.assertEqual(out["upper_exposure_s"], 2)
        self.assertEqual(out["uncertain_frames"], 1)

    def test_empty_frames_and_empty_query(self):
        out = exposure_bounds([], [], [[0, 1]], [[0, 1]])
        self.assertEqual(out["frame_count"], 0)
        self.assertEqual(out["upper_exposure_s"], 0)
        for accepted, gtis in (([], [[0, 1]]), ([[0, 1]], []), ([[0, 1]], [[2, 3]])):
            out = exposure_bounds([0], [1], accepted, gtis)
            self.assertEqual(out["upper_exposure_s"], 0)
            self.assertEqual(out["outside_frames"], 1)

    def test_zero_weights_remain_counted(self):
        out = exposure_bounds([0, 1, 2], [0, 0, 0], [[0, 2]], [[0, 2]])
        self.assertEqual(out["fully_contained_frames"], 1)
        self.assertEqual(out["uncertain_frames"], 2)
        self.assertEqual(out["upper_exposure_s"], 0)

    def test_invalid_centres_weights_and_chunks(self):
        for centres, weights in (([1, 1], [1, 1]), ([2, 1], [1, 1]),
                                 ([np.nan], [1]), ([1], [np.inf]), ([1], [-1]),
                                 ([1], []), ([[1]], [[1]]), ([True], [1]),
                                 ([1], [True]), ([1, True], [1, 1]),
                                 ([0, 1], [1, True]), (["1"], [1]), ([1j], [1])):
            with self.subTest(centres=centres, weights=weights), self.assertRaises(ValueError):
                FrameBounds(centres, weights)
        for chunk in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                FrameBounds([0], [1], chunk)

    def test_invalid_interval_inputs(self):
        frame = FrameBounds([0], [1])
        for bad in (np.empty((2, 0)), np.empty((0, 3)), [0, 1], [[0, 0]], [[2, 1]],
                    [[0, np.inf]], [[np.nan, 1]], [[False, True]], [[0, True]], [["0", "1"]]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    frame.bounds(bad, [[0, 1]])
                with self.assertRaises(ValueError):
                    frame.bounds([[0, 1]], bad)

    def test_prepared_arrays_are_copied(self):
        centres = np.array([0., 1., 2.])
        weights = np.array([1., 2., 3.])
        frame = FrameBounds(centres, weights)
        centres[:] = 0
        weights[:] = 0
        self.assertEqual(frame.bounds([[0, 2]], [[0, 2]])["upper_exposure_s"], 6)

    def test_overflow_is_not_success(self):
        with self.assertRaises(ValueError):
            exposure_bounds([0, 1, 2], [1e308] * 3, [[0, 2]], [[0, 2]])

    def test_actual_synthetic_extended_frame_allocations_inside_bounds(self):
        # Non-overlapping, centred frames with varied/extended widths and gaps.
        physical = np.array([[0., 1.], [1., 3.], [4., 5.], [20., 24.], [25., 26.]])
        centres = physical.mean(axis=1)
        weights = np.array([.8, 1.6, .5, 3., .9])
        for start in np.arange(-1, 28, .25):
            stop = start + 1.75
            out = exposure_bounds(centres, weights, [[start, stop]], [[-10, 40]], chunk_size=2)
            overlap = np.maximum(0, np.minimum(physical[:, 1], stop) - np.maximum(physical[:, 0], start))
            actual = float(np.sum(weights * overlap / np.diff(physical, axis=1).ravel()))
            self.assertLessEqual(out["lower_exposure_s"], actual + 1e-12)
            self.assertGreaterEqual(out["upper_exposure_s"] + 1e-12, actual)

    def test_chunk_invariance_and_scalar_union_oracle(self):
        rng = np.random.default_rng(422)
        for _ in range(50):
            centres = np.cumsum(rng.uniform(.1, 4, 41))
            weights = rng.uniform(0, 2, 41)
            accepted = [[3, 20], [25, 40], [60, 100]]
            gtis = [[0, 15], [17, 30], [35, 80]]
            combined = [[3, 15], [17, 20], [25, 30], [35, 40], [60, 80]]
            lower, upper = [], []
            for i, weight in enumerate(weights):
                low = centres[i - 1] if i else -np.inf
                high = centres[i + 1] if i + 1 < len(centres) else np.inf
                if any(start <= low and high <= stop for start, stop in combined):
                    lower.append(weight)
                if any(max(start, low) < min(stop, high) for start, stop in combined):
                    upper.append(weight)
            for chunk in (1, 2, 17, 100):
                out = exposure_bounds(centres, weights, accepted, gtis, chunk)
                self.assertAlmostEqual(out["lower_exposure_s"], sum(lower), places=12)
                self.assertAlmostEqual(out["upper_exposure_s"], sum(upper), places=12)
                self.assertEqual(out["fully_contained_frames"], len(lower))
                self.assertEqual(out["uncertain_frames"], len(upper) - len(lower))


if __name__ == "__main__":
    unittest.main()
