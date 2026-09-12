"""Prospective orchestration fixtures; no actual calibration or science fits."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

SPEC = importlib.util.spec_from_file_location("m2p_tests", Path(__file__).parents[1] / "scripts/m2p.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def rows():
    return [{"source_id": "9007199254740993", "x": 5., "y": 5., "g_mag": 18.},
            {"source_id": "9007199254740994", "x": 5.2, "y": 5., "g_mag": 19.},
            {"source_id": "9007199254740995", "x": 5., "y": 5.8, "g_mag": 13.}]


def fit(x=5., y=5.):
    return {"success": True, "bound_hit": False, "x": x, "y": y, "centroid_covariance": np.eye(2) * .01}


def trial(label, delta=(0., 0.), covers=True):
    return {"assignment": label, "signed_displacement": delta, "nominal_ellipse_covers_truth": covers}


class OrchestrationTests(unittest.TestCase):
    def test_three_geometry_roles_and_exact_ids(self):
        r = rows()
        selection = P.locations(r, r[0])
        self.assertEqual([x["source_id"] for x in selection["locations"]], [x["source_id"] for x in r])
        self.assertEqual(selection["planned_trials"], 720)
        self.assertAlmostEqual(selection["pair_separation"], .2)

    def test_deduplicates_brightest_nearest_without_replacement(self):
        r = rows()[:2]
        selection = P.locations(r, r[0])
        self.assertEqual(len(selection["locations"]), 2)
        self.assertEqual(selection["locations"][1]["roles"], ["nearest_other", "brightest_other_within_one_pixel"])
        self.assertEqual(selection["planned_trials"], 480)

    def test_missing_bright_role_stays_missing(self):
        r = rows()[:2]
        r[1]["x"] = 8.
        self.assertTrue(P.locations(r, r[0])["missing_bright_role"])

    def test_nearest_assignment_failure_bound_and_exact_tie(self):
        r = rows()
        self.assertEqual(P.assignment(fit(), r), r[0]["source_id"])
        self.assertEqual(P.assignment(fit(5.1), r), "AMBIGUOUS")
        self.assertEqual(P.assignment({"success": False}, r), "FAILED")
        self.assertEqual(P.assignment({**fit(), "bound_hit": True}, r), "BOUND")

    def test_formal_ellipse_truth_coverage_and_singular_failure(self):
        truth = rows()[0]
        self.assertTrue(P.ellipse(fit(), truth))
        self.assertFalse(P.ellipse(fit(6), truth))
        self.assertIsNone(P.ellipse({**fit(), "centroid_covariance": np.zeros((2, 2))}, truth))
        self.assertIsNone(P.ellipse({**fit(), "bound_hit": True}, truth))

    def test_pair_and_third_source_misassignments_all_count(self):
        r = rows()
        correct = trial(r[0]["source_id"])
        for wrong in r[1:]:
            ts = [correct] * 18 + [trial(wrong["source_id"])] * 2
            summary = P.condition_summary(ts, r[0], r, (r[0]["source_id"], r[1]["source_id"]), .2, 1.)
            self.assertEqual(summary["wrong_row_fraction"], .1)
            self.assertIn("STOP_LOCALIZATION_CONFUSION", summary["reasons"])
            self.assertEqual(sum(summary["counts"].values()), 20)

    def test_exact_one_error_not_over_five_percent(self):
        r = rows()
        ts = [trial(r[0]["source_id"])] * 19 + [trial(r[1]["source_id"])]
        summary = P.condition_summary(ts, r[0], r, (r[0]["source_id"], r[1]["source_id"]), .2, 1.)
        self.assertNotIn("STOP_LOCALIZATION_CONFUSION", summary["reasons"])

    def test_signed_bias_not_mean_radial_error(self):
        r = rows()
        ts = [trial(r[0]["source_id"], (.2, 0))] * 10 + [trial(r[0]["source_id"], (-.2, 0))] * 10
        summary = P.condition_summary(ts, r[0], r, (r[0]["source_id"], r[1]["source_id"]), .2, 1.)
        self.assertAlmostEqual(summary["bias_norm"], 0.)
        ts = [trial(r[0]["source_id"], (.11, 0))] * 20
        self.assertIn("STOP_LOCALIZATION_BIAS", P.condition_summary(ts, r[0], r, (r[0]["source_id"], r[1]["source_id"]), .2, 1.)["reasons"])

    def test_missing_failed_bound_ambiguous_and_covariance_never_dropped(self):
        r = rows()
        for kind in ("FAILED", "BOUND", "AMBIGUOUS"):
            ts = [trial(r[0]["source_id"])] * 19 + [trial(kind, None, None)]
            summary = P.condition_summary(ts, r[0], r, (r[0]["source_id"], r[1]["source_id"]), .2, 1.)
            self.assertIsNone(summary["signed_mean_bias"])
            self.assertEqual(summary["denominator"], 20)
            self.assertEqual(summary["coverage_fraction"], .95)
            self.assertIn("INCOMPLETE_TRIAL_OR_COVARIANCE", summary["reasons"])

    def test_secondary_and_primary_exclusions_before_shifted_injection(self):
        t = np.arange(0., 3., .001)
        args = (1., 0., .01)
        safe = P.N.safe_times(t, *args)
        injected = P.injection_mask(t, args) & safe
        self.assertTrue(np.any(injected))
        self.assertFalse(np.any(injected & (np.abs(t - 1.5) < .01)))
        self.assertTrue(np.allclose(t[injected] % 1, .25, atol=.005))

    def test_lower_amplitude_not_used_to_relax_one_x_gate(self):
        r = rows()
        ts = [trial(r[1]["source_id"])] * 20
        self.assertEqual(P.condition_summary(ts, r[0], r, (r[0]["source_id"], r[1]["source_id"]), .2, .5)["reasons"], [])

    def test_wrong_approval_never_starts(self):
        with (patch.object(P, "verify"), patch.object(P.M, "sha", return_value="hash"),
              self.assertRaisesRegex(ValueError, "STOP_APPROVAL_HASH")):
            P.run(False, "wrong")

    def test_output_budget_checked_before_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (patch.object(P, "DATA", root), patch.object(P, "OUT", root),
                  patch.object(P.json, "dumps", return_value="x" * 100_000_001),
                  self.assertRaisesRegex(RuntimeError, "STOP_OUTPUT_CAP")):
                P.save(root / "large.json", {})
            self.assertFalse((root / "large.json").exists())

    def test_bounded_utf8_output_receipts_and_hash_tampering(self):
        for value in ("success", "a" * 15_999 + "\u2603" * 100):
            receipt = P.output_receipt(value)
            P.validate_output_receipt(receipt)
            self.assertLessEqual(len(receipt["output"].encode()), 16_000)
            self.assertEqual(receipt["output_bytes"], len(value.encode()))
        with self.assertRaisesRegex(ValueError, "STOP_OUTPUT_RECEIPT"):
            P.validate_output_receipt({**P.output_receipt("success"), "output_sha256": "0" * 64})

    def test_serialized_size_counts_indentation_and_newline(self):
        value = {"nested": [{"a": 1}, {"b": 2}]}
        expected = (P.json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
        self.assertEqual(P.serialized_size(value), len(expected))


if __name__ == "__main__":
    unittest.main()
