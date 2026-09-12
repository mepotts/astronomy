"""M2 geometry, insertion and fail-accounting regressions; no archive access."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from astropy.io.fits import Header
from astropy.wcs import WCS

SPEC = importlib.util.spec_from_file_location("m2", Path(__file__).parents[1]/"m2.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def epoch():
    header = Header({"BUNIT": "Jy/beam", "BMAJ": 3/3600, "BMIN": 2/3600, "BPA": 30.,
                     "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN", "CRPIX1": 201.,
                     "CRPIX2": 201., "CRVAL1": M.P.TARGET[0], "CRVAL2": M.P.TARGET[1],
                     "CDELT1": -1/3600, "CDELT2": 1/3600})
    wcs = WCS(header)
    return {"array": np.zeros((601, 601)), "rms": np.ones((601, 601))*.0001,
            "wcs": wcs, "header": header, "matrix": wcs.pixel_scale_matrix*3600}


def measurement(amp=1., recovered=True):
    return {"amplitude_jy": amp, "noise_proxy_jy": .1, "amplitude_over_noise": 10.,
            "residual_over_noise": .1, "peak_offset_arcsec": .1, "recovered": recovered}


def example_report():
    screen = [{"id": i, "usable": True, "split": "heldout" if i%2 else "development",
               "block": str(i//20), "flux_jy": [.0003, .0005, .001, .003, .01][i%5],
               "selection": {"local_eligible": i%5 == 4, "global_selected": i%5 == 4}}
              for i in range(200)]
    epochs = []
    for campaign in M.P.CAMPAIGNS[1:]:
        null = {**measurement(0), "amplitude_over_noise": 0}
        grid = [{"id": p["id"], "blank": copy.deepcopy(null),
                 "injected": measurement(p["flux_jy"]),
                 "selected_position_injected": measurement(p["flux_jy"])} for p in screen]
        epochs.append({"campaign": campaign, "target": measurement(),
                       "references": [measurement(i+1) for i in range(12)],
                       "fixed_nulls": [copy.deepcopy(null) for _ in range(8)], "grid": grid})
    return {"reference_screen": screen, "epochs": epochs}, [[i, 0] for i in range(12)]


class TestM2(unittest.TestCase):
    def test_plan_slots_unchanged_through_preflight_clarification(self):
        original = json.loads((M.ROOT/"m2-plan-v1.json").read_text())
        current = json.loads((M.ROOT/"m2-plan.json").read_text())
        self.assertEqual(original["positions"], current["positions"])
        self.assertEqual(len(current["positions"]), 200)
        self.assertEqual(sum(p["split"] == "heldout" for p in current["positions"]), 97)

    def test_numerical_proof_includes_real_estimator(self):
        result = json.loads((M.ROOT/"m2-numerical.json").read_text())
        self.assertEqual(len(result["trials"]), 240)
        self.assertTrue(result["passed"])
        self.assertTrue(all(abs(t["fixed_estimator_amplitude"]-1) <= .01 for t in result["trials"]))

    def test_kernel_handedness(self):
        header = epoch()["header"]
        right, _ = M.kernel(header, np.eye(2))
        left, _ = M.kernel(header, np.diag([-1., 1.]))
        np.testing.assert_allclose(left, np.fliplr(right), atol=1e-14)
        self.assertFalse(np.allclose(left, right))

    def test_no_sharpening(self):
        header = epoch()["header"]
        header["BMAJ"] = 4/3600
        with self.assertRaisesRegex(ValueError, "sharpen"):
            M.kernel(header, np.eye(2))

    def test_invalid_local_geometry(self):
        native = epoch()
        native["array"][200, 200] = np.nan
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            M.patch(native, *M.P.TARGET)

    def test_wrong_units(self):
        native = M.patch(epoch(), *M.P.TARGET)
        native["header"]["BUNIT"] = "MJy/sr"
        with self.assertRaisesRegex(ValueError, "Jy/beam"):
            M.common(native, *M.P.TARGET)

    def test_true_source_stays_fixed_when_selected_position_shifts(self):
        native = epoch()
        native["array"] = np.random.default_rng(5).normal(0, 1e-5, native["array"].shape)
        ra, dec = map(float, native["wcs"].all_pix2world(202, 200, 0))
        true = M.measured(native, *M.P.TARGET, flux=.003)
        shifted = M.measured(native, ra, dec, flux=.003, injection_position=M.P.TARGET)
        self.assertLess(shifted["amplitude_jy"], .8*true["amplitude_jy"])

    def test_local_maximum_full_21_rule(self):
        values = np.zeros((41, 41))
        values[20, 20] = 5
        values[20, 30] = 6
        self.assertFalse(M.local_maximum(values, 20, 20))

    def test_global_rank_and_ties(self):
        baseline = list(range(12, 0, -1))
        self.assertEqual(M.insertion_rank(.5, baseline), 13)
        self.assertEqual(M.insertion_rank(1, baseline), 13)
        self.assertEqual(M.insertion_rank(1.5, baseline), 12)

    def test_injected_selection_error_not_screen_exclusion(self):
        native = epoch()
        references = [list(map(float, native["wcs"].all_pix2world(50+40*i, 50, 0))) for i in range(12)]
        ra, dec = map(float, native["wcs"].all_pix2world(400, 400, 0))
        position = {"id": 0, "x": 400, "y": 400, "ra": ra, "dec": dec, "flux_jy": .003}
        with mock.patch.object(M.P, "ensemble_positions", return_value=references), \
                mock.patch.object(M.P, "photometry", side_effect=ValueError("injected-stage failure")):
            result = M.screen_reference(native, [position], references)[0]
        self.assertTrue(result["usable"])
        self.assertEqual(result["screen_reasons"], [])
        self.assertIn("selection_error", result)

    def test_selected_peak_reapplies_target_distance_cut(self):
        native = epoch()
        references = [list(map(float, native["wcs"].all_pix2world(50+40*i, 50, 0))) for i in range(12)]
        ra, dec = map(float, native["wcs"].all_pix2world(245.5, 200, 0))
        position = {"id": 0, "x": 245.5, "y": 200, "ra": ra, "dec": dec, "flux_jy": .003}
        # Deliberately forced selected maximum at global x=243: inside 45 arcsec,
        # while the originally screened true grid centre is outside 45 arcsec.
        fake_model = np.zeros((89, 89))
        fake_model[44, 41] = 1
        with mock.patch.object(M.P, "ensemble_positions", return_value=references), \
                mock.patch.object(M, "point_model", return_value=fake_model), \
                mock.patch.object(M.P, "photometry", return_value={"residual_over_noise": 0}):
            result = M.screen_reference(native, [position], references)[0]
        self.assertTrue(result["usable"])
        self.assertTrue(result["selection"]["local_maximum_21"])
        self.assertFalse(result["selection"]["selected_geometry_pass"])
        self.assertFalse(result["selection"]["local_eligible"])

    def test_clean_gate_fixture(self):
        report, references = example_report()
        M.summarize(report, references)
        self.assertEqual(report["outcome"], "COMMON_BEAM_CALIBRATION_FEASIBILITY")

    def test_failed_injection_stays_in_bias_denominator(self):
        report, references = example_report()
        report["epochs"][0]["grid"][3]["error"] = "missing injection"
        M.summarize(report, references)
        stratum = report["epochs"][0]["heldout_strata"][3]
        self.assertEqual(stratum["expected_denominator"], 20)
        self.assertEqual(stratum["measured"], 19)
        self.assertIsNone(stratum["unconditional_median_fractional_bias"])
        self.assertEqual(report["outcome"], "STOP_M2")

    def test_joint_recovery_is_not_separate_epoch_rates(self):
        report, references = example_report()
        report["epochs"][0]["grid"][3]["injected"]["recovered"] = False
        report["epochs"][1]["grid"][13]["injected"]["recovered"] = False
        M.summarize(report, references)
        self.assertIn("JOINT_BRIGHT_INJECTION_0.003", report["failed_gates"])
        self.assertEqual(report["heldout_joint_strata"][3]["joint_recovery_fraction"], .9)

    def test_empty_selected_stratum_bias_unmeasured(self):
        report, references = example_report()
        M.summarize(report, references)
        rows = [r for r in report["selection_conditioning"]
                if r["flux_jy"] == .0003 and r["condition"] == "native_global_top12"]
        self.assertTrue(all(r["denominator"] == 0 and r["median_fractional_bias_by_epoch"] == [None]*3
                            for r in rows))

    def test_selection_failure_stops_validity(self):
        report, references = example_report()
        report["reference_screen"][1]["selection"] = None
        M.summarize(report, references)
        self.assertIn("INVALID_INJECTED_SELECTION_TEST", report["failed_gates"])

    def test_conditioning_uses_selected_flux_and_selected_morphology(self):
        report, references = example_report()
        for ep in report["epochs"]:
            for row in ep["grid"]:
                row["selected_position_injected"]["amplitude_jy"] *= 2
        report["epochs"][0]["grid"][9]["selected_position_injected"]["residual_over_noise"] = 4
        M.summarize(report, references)
        rows = {r["condition"]: r for r in report["selection_conditioning"]
                if r["split"] == "heldout" and r["flux_jy"] == .01}
        self.assertEqual(rows["unconditional_after_reference_screen"]["median_fractional_bias_by_epoch"], [0]*3)
        self.assertEqual(rows["native_global_top12"]["median_fractional_bias_by_epoch"], [1]*3)
        self.assertEqual(rows["native_global_top12"]["denominator"], 20)
        self.assertEqual(rows["global_top12_and_final_common_morphology"]["denominator"], 19)
