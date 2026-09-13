"""No real photons: edge, interval and conditional-rate arithmetic contracts."""

import math
import unittest

import numpy as np
import xmm_timing as module


class TimingTests(unittest.TestCase):
    def test_half_open_final_edge_is_excluded(self):
        counts, outside = module.half_open_counts([-1, 0, 1, 2, 3], [0, 1, 2, 3])
        np.testing.assert_array_equal(counts, [1, 1, 1])
        self.assertEqual(outside, 2)

    def test_unsorted_events_and_empty_input(self):
        counts, outside = module.half_open_counts([1.5, 0.1, 1.5], [0, 1, 2])
        np.testing.assert_array_equal(counts, [1, 2])
        self.assertEqual(outside, 0)
        np.testing.assert_array_equal(module.half_open_counts([], [0, 1, 2])[0], [0, 0])

    def test_gti_union_does_not_double_count_or_fill_gaps(self):
        intervals = [[2, 4], [0, 1], [0.5, 2], [6, 8], [6, 7]]
        np.testing.assert_array_equal(module.interval_union(intervals), [[0, 4], [6, 8]])
        np.testing.assert_array_equal(module.wall_coverage([0, 3, 6, 9], intervals), [3, 1, 2])
        np.testing.assert_array_equal(module.wall_coverage([0, 1, 2], []), [0, 0])

    def test_invalid_time_inputs_are_not_silently_dropped(self):
        for intervals in ([[1, 1]], [[2, 1]], [[0, float("nan")]], np.empty((2, 0)), np.empty((0, 3))):
            with self.assertRaises(ValueError):
                module.interval_union(intervals)
        for edges in ([0, 0, 1], [1, 0], [0, float("inf")]):
            with self.assertRaises(ValueError):
                module.half_open_counts([], edges)
        with self.assertRaises(ValueError):
            module.half_open_counts([float("nan")], [0, 1])

    def test_reference_uses_whole_bins_and_fixed_mask(self):
        edges = np.arange(0, 4201, 200)
        accepted = np.ones(21, dtype=bool)
        accepted[1] = False
        actual = module.reference_mask(edges, 10, accepted, exclusion_seconds=1000)
        expected = np.zeros(21, dtype=bool)
        expected[:5] = True
        expected[16:] = True
        expected[1] = False
        np.testing.assert_array_equal(actual, expected)
        with self.assertRaises(ValueError):
            module.reference_mask(edges, 10, np.ones(21, dtype=int))
        with self.assertRaises(ValueError):
            module.reference_mask(edges, True, accepted)

    def test_exact_small_count_tail_by_enumeration(self):
        for count in range(7):
            reference_count = 6 - count
            expected = sum(math.comb(6, k) * 0.25**k * 0.75**(6 - k) for k in range(count, 7))
            self.assertAlmostEqual(module.constant_rate_tail(count, reference_count, 1, 3), expected, places=14)

    def test_constant_efficiency_cancels_and_zero_counts_are_valid(self):
        first = module.constant_rate_tail(12, 3, 200, 2000)
        second = module.constant_rate_tail(12, 3, 160, 1600)
        self.assertAlmostEqual(first, second, places=14)
        self.assertEqual(module.constant_rate_tail(0, 0, 1, 10), 1)
        self.assertLess(module.constant_rate_tail(12, 3, 200, 2000),
                        module.constant_rate_tail(11, 4, 200, 2000))

    def test_invalid_counts_or_exposures_are_unmeasured_not_zero(self):
        for count in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                module.constant_rate_tail(count, 2, 1, 3)
        for exposure in (0, -1, float("nan"), float("inf"), True, np.bool_(True)):
            with self.assertRaises(ValueError):
                module.constant_rate_tail(1, 2, exposure, 3)
            with self.assertRaises(ValueError):
                module.constant_rate_tail(1, 2, 3, exposure)


if __name__ == "__main__":
    unittest.main()
