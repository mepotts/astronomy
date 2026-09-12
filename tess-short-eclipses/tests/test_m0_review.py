"""Independent synthetic checks; these do not calibrate empirical false alarms."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from astropy.timeseries import BoxLeastSquares

SPEC = importlib.util.spec_from_file_location(
    "tess_m0_review", Path(__file__).resolve().parents[1] / "scripts" / "m0.py"
)
m0 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m0)


def synthetic(gap=False):
    t = np.arange(0.00037, 12, 120 / 86400)
    if gap:
        t = t[(t < 5) | (t > 7)]
    period, epoch, duration = 0.237, 0.04321, 8 / 1440
    inside = np.abs((t - epoch + period / 2) % period - period / 2) < duration / 2
    dy = np.full(len(t), 0.005)
    y = 1 - 0.065 * inside + np.random.default_rng(124).normal(0, dy)
    return t, y, dy, period


class IndependentRecoveryTests(unittest.TestCase):
    def test_synthetic_recovery_with_gap_and_temporal_repetition(self):
        t, y, dy, reference = synthetic(gap=True)
        solution = m0.search(t, y, dy, np.linspace(0.20, 0.28, 321), chunk=37)
        self.assertLess(abs(solution["period"] / reference - 1), 0.001)
        full = m0.depth_stats(t, y, dy, solution)
        first = t < (t.min() + t.max()) / 2
        halves = [m0.depth_stats(t[s], y[s], dy[s], solution) for s in (first, ~first)]
        grade = m0.grade(solution, full, halves, reference)
        self.assertTrue(grade["passed"])
        self.assertEqual(grade["period_match"], "exact")

    def test_chunks_do_not_change_winner(self):
        t, y, dy, _ = synthetic()
        periods = np.linspace(0.23, 0.244, 57)
        first = m0.search(t, y, dy, periods, chunk=7)
        second = m0.search(t, y, dy, periods, chunk=1000)
        for field in first:
            self.assertAlmostEqual(first[field], second[field], places=10, msg=field)

    def test_inadmissible_duration_does_not_hide_shorter_solution(self):
        t = np.arange(0.000137, 12, 120 / 86400)
        period, duration = 0.05, 16 / 1440
        phase = (t - 0.013 + period / 2) % period - period / 2
        y = 1 - 0.1 * (np.abs(phase) < duration / 2)
        dy = np.full(len(t), 0.005)
        unconstrained = BoxLeastSquares(t, y, dy).power([period], m0.DURATIONS)
        self.assertGreater(unconstrained.duration[0] / period, 0.15)
        solution = m0.search(t, y, dy, [period])
        self.assertLessEqual(solution["duration"] / solution["period"], 0.15)
        self.assertGreater(solution["depth_snr"], 10)

    def test_published_grader_values_cannot_change_search(self):
        t, y, dy, _ = synthetic()
        periods = np.array([0.235, 0.237, 0.239])
        first = m0.search(t, y, dy, periods)
        with patch.object(m0, "CONTROLS", {1: (999, 0.812345)}):
            second = m0.search(t, y, dy, periods)
        self.assertEqual(first, second)

    def test_flat_flux_stops(self):
        t = np.arange(0.000137, 12, 120 / 86400)
        with self.assertRaisesRegex(ValueError, "STOP_NO_FINITE_SOLUTION"):
            m0.search(t, np.ones(len(t)), np.ones(len(t)), [0.237])

    def test_grid_includes_endpoints_and_bounds_drift(self):
        baseline = 27.0
        grid = m0.period_grid(baseline)
        self.assertEqual(grid[0], 0.05)
        self.assertEqual(grid[-1], 1.0)
        self.assertTrue(np.all(np.diff(grid) > 0))
        # Log spacing is bounded exactly; actual neighboring-period drift
        # differs from its differential approximation only at O(step**2).
        self.assertLessEqual(np.max(np.diff(np.log(grid))), m0.DURATIONS[0] / (3 * baseline) + 1e-14)


class IndependentStatisticsTests(unittest.TestCase):
    def test_weighted_depth_and_error_match_direct_calculation(self):
        solution = {"period": 1.0, "transit_time": 0.0, "duration": 0.2}
        t = np.array([-0.04, 0.03, 0.40, 0.60, 0.96, 1.04, 1.40])
        y = np.array([0.70, 0.72, 1.02, 0.97, 0.69, 0.71, 1.00])
        dy = np.array([0.02, 0.03, 0.01, 0.02, 0.04, 0.02, 0.01])
        inside = np.array([True, True, False, False, True, True, False])
        w = 1 / dy**2
        expected = (y[~inside] * w[~inside]).sum() / w[~inside].sum()
        expected -= (y[inside] * w[inside]).sum() / w[inside].sum()
        error = np.sqrt(1 / w[inside].sum() + 1 / w[~inside].sum())
        result = m0.depth_stats(t, y, dy, solution)
        self.assertAlmostEqual(result["depth"], expected)
        self.assertAlmostEqual(result["error"], error)
        self.assertAlmostEqual(result["snr"], expected / error)
        self.assertEqual(result["sampled_events"], 2)
        self.assertEqual(result["in_points"], 4)

    def test_shared_flux_error_scaling_preserves_solution_snr(self):
        t, y, dy, _ = synthetic()
        quality = np.zeros(len(t), dtype=int)
        a = m0.prepare(t, y, dy, quality)
        b = m0.prepare(t, y * 137, dy * 137, quality)
        for first, second in zip(a, b, strict=True):
            np.testing.assert_allclose(first, second, rtol=1e-14)
        sa = m0.search(*a, periods=[0.235, 0.237, 0.239])
        sb = m0.search(*b, periods=[0.235, 0.237, 0.239])
        self.assertEqual(sa["period"], sb["period"])
        self.assertAlmostEqual(sa["depth_snr"], sb["depth_snr"], places=8)

    def test_no_in_or_out_samples_returns_non_detection(self):
        solution = {"period": 1.0, "transit_time": 0.0, "duration": 0.2}
        for t in (np.array([0.3, 0.4]), np.array([-0.01, 0.01]), np.array([])):
            result = m0.depth_stats(t, np.ones(len(t)), np.ones(len(t)), solution)
            self.assertIsNone(result["snr"])
            self.assertEqual(result["sampled_events"], 0)

    def test_aliases_are_explicit_and_failed_halves_stop(self):
        full = {"in_points": 100, "sampled_events": 20}
        halves = [{"snr": 7, "sampled_events": 10}] * 2
        for label, period in (("exact", 0.2), ("half", 0.1), ("double", 0.4)):
            solution = {"period": period, "depth_snr": 15}
            result = m0.grade(solution, full, halves, 0.2)
            self.assertTrue(result["passed"])
            self.assertEqual(result["period_match"], label)
        solution = {"period": 0.2, "depth_snr": 15}
        for failed in ({"snr": None, "sampled_events": 10},
                       {"snr": 4.99, "sampled_events": 10},
                       {"snr": 7, "sampled_events": 4}):
            self.assertFalse(m0.grade(solution, full, [halves[0], failed], 0.2)["passed"])


class IndependentInputTests(unittest.TestCase):
    def test_prepare_keeps_negative_flux_and_rejects_bad_measurements(self):
        t = np.linspace(0, 12, 1200)
        y, dy, q = np.ones(1200), np.ones(1200), np.zeros(1200)
        y[1] = -0.5
        y[2] = np.nan
        dy[3] = 0
        dy[4] = np.inf
        q[5] = 1
        prepared = m0.prepare(t[::-1], y[::-1], dy[::-1], q[::-1])
        self.assertEqual(len(prepared[0]), 1196)
        self.assertTrue(np.all(np.diff(prepared[0]) > 0))
        self.assertEqual(np.count_nonzero(prepared[1] < 0), 1)

    def test_coverage_duplicate_and_normalization_stop(self):
        for t, y, expected in (
            (np.linspace(0, 12, 999), np.ones(999), "STOP_COVERAGE"),
            (np.linspace(0, 9, 1200), np.ones(1200), "STOP_COVERAGE"),
            (np.linspace(0, 12, 1200), -np.ones(1200), "STOP_NORMALIZATION"),
            (np.repeat(np.linspace(0, 12, 600), 2), np.ones(1200), "STOP_DUPLICATE_TIMES"),
        ):
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                m0.prepare(t, y, np.ones(len(t)), np.zeros(len(t)))

    def test_header_identity_time_and_cadence_validation(self):
        primary = {"TICID": 450781262, "SECTOR": 99}
        header = {"TIMEUNIT": "d", "TIMESYS": "TDB", "BJDREFI": 2457000,
                  "BJDREFF": 0.0, "TIMEDEL": 120 / 86400}
        m0.validate_header(primary, header, 450781262, 99)
        for key, value, status in (
            ("TIMEUNIT", "s", "STOP_TIME_REFERENCE"),
            ("TIMESYS", "UTC", "STOP_TIME_REFERENCE"),
            ("BJDREFI", 2454833, "STOP_TIME_REFERENCE"),
            ("BJDREFF", 0.5, "STOP_TIME_REFERENCE"),
            ("TIMEDEL", 1800 / 86400, "STOP_CADENCE"),
        ):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, status):
                m0.validate_header(primary, {**header, key: value}, 450781262, 99)
        for changed in ({**primary, "TICID": 53206761}, {**primary, "SECTOR": 72}):
            with self.assertRaisesRegex(ValueError, "STOP_PRODUCT_IDENTITY"):
                m0.validate_header(changed, header, 450781262, 99)


if __name__ == "__main__":
    unittest.main()
