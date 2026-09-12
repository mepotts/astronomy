"""A failed execution is never an imaging non-detection or a valid contrast."""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("e_execution_audit", Path(__file__).resolve().parents[1] / "scripts/e_execution_audit.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ExecutionTests(unittest.TestCase):
    def test_failed_run_cannot_promote_partial_detections(self):
        rows = [{"centroid_finite": True}]*3
        self.assertEqual(M.execution_status(1, rows), "STOP_FROZEN_MEASUREMENT")

    def test_missing_filter_or_nonfinite_centroid_stops(self):
        for rows in ([], [{"centroid_finite": True}]*2,
                     [{"centroid_finite": True}, {"centroid_finite": True}, {"centroid_finite": False}]):
            self.assertEqual(M.execution_status(0, rows), "STOP_INCOMPLETE_MEASUREMENT")

    def test_successful_execution_is_not_scientific_validation(self):
        self.assertEqual(M.execution_status(0, [{"centroid_finite": True}]*3),
                         "REQUIRES_FULL_SCIENTIFIC_VALIDATION")

    def test_nonfinite_is_missing_not_zero(self):
        self.assertIsNone(M.finite_or_none(float("nan")))
        self.assertIsNone(M.finite_or_none(float("inf")))
        self.assertEqual(M.finite_or_none(0.), 0.)


if __name__ == "__main__":
    unittest.main()
