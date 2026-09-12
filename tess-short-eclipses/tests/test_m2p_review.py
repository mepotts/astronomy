"""Independent M2p orchestration checks with synthetic/mock-only science inputs."""

import importlib.util
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

SPEC = importlib.util.spec_from_file_location("m2p_independent", Path(__file__).parents[1] / "scripts/m2p.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def catalog_rows():
    return [{"source_id": str(2**53 + i), "x": x, "y": y, "g_mag": mag}
            for i, x, y, mag in ((1, 2., 2., 18.), (2, 2.2, 2., 19.), (3, 2., 2.8, 13.))]


def fit_record():
    return {"success": True, "bound_hit": False, "x": 2., "y": 2.,
            "centroid_covariance": np.eye(2).tolist(), "model": [[0]], "residual": [[0]]}


class MockedScienceTests(unittest.TestCase):
    def environment(self, *, trial_exception=False, shape_failure=False):
        stack = ExitStack()
        self.addCleanup(stack.close)
        times = np.arange(0., 12., .01)
        cube = np.full((len(times), 5, 5), 10.)
        errors = np.ones_like(cube)
        aperture = np.zeros((5, 5), bool)
        aperture[:2, :2] = True
        valid = np.ones((5, 5), bool)
        base_blocks = np.broadcast_to(np.arange(11)[:, None, None], (11, 5, 5)).copy().astype(float)
        prior = {"status": "WITHIN_FIELD_DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE", "primary_amplitude": 4.,
                 "phases": [{"phase": phase, **{name: {"mean_image": np.zeros((5, 5)).tolist(),
                   "error_image": np.ones((5, 5)).tolist(), "valid_pixels": valid.tolist()}
                   for name in ("flux", "background")}} for phase in (.2, .25, .3, .7, .75, .8)]}
        seen = {"injections": [], "profiles": [], "fits": [], "grids": [], "emits": {}}
        products = [{"tic": tic, "filename": f"{tic}-corner{corner}"} for tic in P.TICS for corner in range(4)]
        acquisition = SimpleNamespace(replay=mock.Mock(), products=lambda: products,
                                      folder_for=lambda filename: Path("synthetic"), MANIFEST=Path("synthetic-prf-manifest"))
        catalog_stage = SimpleNamespace(replay=mock.Mock())

        class Grid:
            def __init__(self, arrays, rows, columns, origin):
                seen["grids"].append((arrays.copy(), rows, columns, origin))

            def image(self, x, y, shape, corner):
                if shape_failure and corner == 0:
                    raise ValueError("synthetic shape unavailable")
                return np.full(shape, .01 * (corner + 1)), {"captured_fraction": .25 * (corner + 1), "true_infinite_flux": False}

        def synthetic_fit(image, error, pixels, grid):
            index = len(seen["fits"])
            seen["fits"].append((np.array(image), np.array(error), np.array(pixels)))
            if trial_exception and index == 29:
                raise ValueError("synthetic fifth trial exception")
            return {**fit_record(), "synthetic_image_mean": float(np.mean(image))}

        def profile(image, error, pixels, grid, x, y):
            seen["profiles"].append((x, y))
            return {**fit_record(), "x": x, "y": y, "weighted_residual_sum": 100 - y}

        core = SimpleNamespace(PRFGrid=Grid, fit=synthetic_fit, fixed_hypothesis=profile)

        def module(name, path):
            if name == "m2p_acquisition": return acquisition
            if name == "m2p_catalog": return catalog_stage
            if name == "m2p_prf": return core
            raise AssertionError("Unexpected real module: " + name)

        def read(path):
            if path == acquisition.MANIFEST:
                return {"context": [{"tic": tic, "rows": [0, 10], "columns": [0, 10], "origin": [0, 0]} for tic in P.TICS]}
            if Path(path).name.startswith("m2n-"): return prior
            raise AssertionError("Unexpected retained metadata read: " + str(path))

        def open_fits(path, **kwargs):
            corner = int(Path(path).name[-1])
            return mock.MagicMock(__enter__=mock.Mock(return_value=[SimpleNamespace(data=np.full((117, 117), corner))]))

        def blocks(t, flux, sigma, args, offset, anchor, ap, collected):
            if offset == .25:
                self.assertEqual(anchor, times.min())
                self.assertTrue(np.all(sigma == 1.))
                if not np.all(flux == 10.):
                    changed = P.injection_mask(t, args)
                    self.assertTrue(np.all(flux[~changed] == 10.))
                    self.assertTrue(np.all(flux[changed] < 10.))
                    decrement = (10. - flux[changed])[:, ap].sum(axis=1)
                    self.assertTrue(np.allclose(decrement, decrement[0], atol=1e-12, rtol=0))
                    seen["injections"].append(float(decrement[0]))
            return base_blocks + np.mean(10. - flux, axis=0), np.arange(11), valid.copy(), np.arange(30)

        stack.enter_context(mock.patch.object(P.N, "module", side_effect=module))
        stack.enter_context(mock.patch.object(P.N, "execute", return_value=prior))
        stack.enter_context(mock.patch.object(P.N, "load_data", return_value=(times, [cube, errors, cube, errors],
                            aperture, valid, np.arange(len(times)), (.4, 0., .02))))
        stack.enter_context(mock.patch.object(P, "read", side_effect=read))
        stack.enter_context(mock.patch.object(P, "catalog", side_effect=lambda tic: (catalog_rows(), catalog_rows()[0])) )
        stack.enter_context(mock.patch.object(P.fits, "open", side_effect=open_fits))
        stack.enter_context(mock.patch.object(P, "blocks", side_effect=blocks))
        return seen

    def test_all_fields_all_conditions_paired_draws_and_pre_estimator_aperture_decrement(self):
        seen = self.environment()
        for tic in P.TICS:
            before = len(seen["injections"])
            result = P.measure(tic, lambda name, value: seen["emits"].update({name: value}))
            self.assertEqual(result["planned_trials"], 720)
            self.assertEqual(len(result["conditions"]), 36)
            self.assertEqual(len(seen["injections"]) - before, 36)
            self.assertEqual(len(result["primary"]["profile_hypotheses"]), 3)
            self.assertEqual(len(result["negative_fits"]), 6)
            draws = np.random.default_rng(20260912).integers(0, 11, size=(20, 11))
            np.testing.assert_array_equal(result["day_resampling_indices"], draws)
            shifts = draws.mean(axis=1) - draws[0].mean()
            for condition in result["conditions"]:
                self.assertEqual(len(condition["trials"]), 20)
                self.assertEqual(sum(condition["summary"]["counts"].values()), 20)
                self.assertAlmostEqual(condition["aperture_response"] * condition["model_amplitude"], 4. * condition["scale"])
                values = np.array([t["fit"]["synthetic_image_mean"] for t in condition["trials"]])
                np.testing.assert_allclose(values - values[0], shifts, atol=1e-12, rtol=0)
                self.assertNotIn("model", condition["trials"][0]["fit"])
            self.assertEqual(len(seen["emits"]), 38)
        self.assertEqual(len(seen["profiles"]), 9)
        for arrays, _, _, _ in seen["grids"]:
            np.testing.assert_array_equal(arrays[:, 0, 0], np.arange(4))

    def test_trial_exception_preserves_previous_trials_and_twenty_slot_accounting(self):
        self.environment(trial_exception=True)
        result = P.measure(P.TICS[0], lambda *args: None)
        first = result["conditions"][0]
        self.assertIn("trials", first)
        self.assertEqual(len(first["trials"]), 20)
        self.assertEqual(sum(first["summary"]["counts"].values()), 20)
        self.assertEqual(first["summary"]["counts"]["FAILED"], 1)
        self.assertTrue(all(t["assignment"] != "FAILED" for t in first["trials"][:5]))
        self.assertEqual(first["summary"]["recorded_slots"], 20)
        self.assertEqual(first["summary"]["attempted_trials"], 20)
        self.assertEqual(first["summary"]["completed_trials"], 19)

    def test_shape_setup_failure_retains_twenty_unavailable_slots_per_condition(self):
        self.environment(shape_failure=True)
        result = P.measure(P.TICS[0], lambda *args: None)
        self.assertEqual(len(result["conditions"]), 36)
        for condition in result["conditions"]:
            if condition["corner"] == 0:
                self.assertIn("summary", condition)
                self.assertEqual(condition["summary"]["denominator"], 20)
                self.assertEqual(sum(condition["summary"]["counts"].values()), 20)
                self.assertEqual(condition["summary"]["attempted_trials"], 0)
                self.assertEqual(condition["summary"]["completed_trials"], 0)


class IndependentScoringTests(unittest.TestCase):
    def test_real_core_bound_contract_maps_to_bound_category(self):
        self.assertEqual(P.assignment({**fit_record(), "success": False, "bound_hit": True}, catalog_rows()), "BOUND")

    def test_missing_trial_cannot_form_complete_signed_bias_or_coverage(self):
        rows = catalog_rows()
        trial = {"assignment": rows[0]["source_id"], "signed_displacement": [0., 0.], "nominal_ellipse_covers_truth": True}
        summary = P.condition_summary([trial] * 19, rows[0], rows, (rows[0]["source_id"], rows[1]["source_id"]), .2, 1.)
        self.assertEqual(summary["coverage_fraction"], .95)
        self.assertIsNone(summary["signed_mean_bias"])
        self.assertIn("INCOMPLETE_TRIAL_OR_COVARIANCE", summary["reasons"])


class IndependentReceiptTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        for name, path in (("ROOT", root), ("DATA", root / "data/m2p"), ("OUT", root / "out"),
                           ("MANIFEST", root / "data/m2p/manifest.json")):
            stack.enter_context(mock.patch.object(P, name, path))
        stack.enter_context(mock.patch.object(P, "verify"))
        stack.enter_context(mock.patch("builtins.print"))
        P.M.save(P.MANIFEST, {"synthetic": True})
        self.digest = P.M.sha(P.MANIFEST)
        P.M.save(P.DATA / "run-start.json", {"manifest_sha256": self.digest})

    def success_summary(self):
        outcomes = []
        for tic in P.TICS:
            result = {"tic": tic, "status": "STOP_INPUT_OR_MEASUREMENT", "manifest_sha256": self.digest,
                      "unknown_search_authorized": False, "physical_depth_validated": False, "network_requests": 0}
            P.M.save(P.OUT / f"m2p-{tic}.json", result)
            P.M.save(P.DATA / f"runtime-{tic}.json", {"elapsed_seconds": .01, "peak_working_set_bytes": 100})
            P.M.save(P.DATA / f"worker-{tic}.json", {"tic": tic, "manifest_sha256": self.digest})
            text = P.json.dumps({"tic": tic, "status": result["status"], "replay": False}) + "\n"
            outcomes.append({"tic": tic, "returncode": 0, "worker_returncode": 0,
                             **P.output_receipt(text), "worker_output": P.output_receipt(text)})
        return {"manifest_sha256": self.digest, "artifacts": P.artifacts(), "outcomes": outcomes,
                "unknown_search_authorized": False}

    def replay_runner(self):
        return SimpleNamespace(bounded_run=mock.Mock(side_effect=lambda command, limit: (0, P.json.dumps({
            "tic": int(command[-1]), "status": "STOP_INPUT_OR_MEASUREMENT", "replay": True}) + "\n")))

    def test_consistent_all_field_replay_is_read_only_and_bounded(self):
        P.M.save(P.OUT / "m2p-summary.json", self.success_summary())
        before = {p.as_posix(): p.read_bytes() for p in P.ROOT.rglob("*") if p.is_file()}
        runner = self.replay_runner()
        with mock.patch.object(P.N, "module", return_value=runner):
            P.run(True, None)
        self.assertEqual(runner.bounded_run.call_count, 3)
        self.assertEqual([c.args[1] for c in runner.bounded_run.call_args_list], [600] * 3)
        self.assertEqual(before, {p.as_posix(): p.read_bytes() for p in P.ROOT.rglob("*") if p.is_file()})

    def test_changed_output_digest_is_rejected_before_replay_launch(self):
        summary = self.success_summary()
        summary["outcomes"][0]["output_sha256"] = "0" * 64
        P.M.save(P.OUT / "m2p-summary.json", summary)
        runner = self.replay_runner()
        with mock.patch.object(P.N, "module", return_value=runner), self.assertRaises(ValueError):
            P.run(True, None)
        runner.bounded_run.assert_not_called()

    def condition_fixture(self):
        tic = P.TICS[0]
        rows = catalog_rows()
        selection = P.locations(rows, rows[0])
        P.MANIFEST.unlink()
        P.M.save(P.MANIFEST, {"selection": {str(tic): selection}})
        digest = P.M.sha(P.MANIFEST)
        primary, negatives, conditions = {"synthetic": True}, [], []
        P.M.save(P.DATA / str(tic) / "primary.json", primary)
        P.M.save(P.DATA / str(tic) / "negatives.json", negatives)
        for li, truth in enumerate(selection["locations"]):
            for scale in P.SCALES:
                for corner in range(4):
                    trials = [{"fit": {**fit_record(), "x": truth["x"], "y": truth["y"]},
                               "assignment": truth["source_id"], "signed_displacement": [0., 0.],
                               "radial_error": 0., "nominal_ellipse_covers_truth": True} for _ in range(20)]
                    condition = P.M.clean({"truth": truth, "scale": scale, "corner": corner, "trials": trials,
                        "summary": P.condition_summary(trials, truth, rows, (selection["target_id"], selection["nearest_id"]),
                                                       selection["pair_separation"], scale)})
                    conditions.append(condition)
                    P.M.save(P.DATA / str(tic) / f"condition-{li}-{scale}-{corner}.json", condition)
        result = {"tic": tic, "status": "DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE", "manifest_sha256": digest,
                  "unknown_search_authorized": False, "physical_depth_validated": False, "network_requests": 0,
                  "selection": selection, "planned_trials": 720, "conditions": conditions, "primary": primary,
                  "negative_fits": negatives}
        P.M.save(P.OUT / f"m2p-{tic}.json", result)
        P.M.save(P.DATA / f"runtime-{tic}.json", {"elapsed_seconds": .01, "peak_working_set_bytes": 100})
        P.M.save(P.DATA / f"worker-{tic}.json", {"tic": tic, "manifest_sha256": digest})
        return tic, P.json.dumps({"tic": tic, "status": result["status"], "replay": False}), result

    def test_completed_requires_every_condition_checkpoint(self):
        tic, output, _ = self.condition_fixture()
        with mock.patch.object(P, "catalog", return_value=(catalog_rows(), catalog_rows()[0])):
            P.completed(tic, output, False)
            (P.DATA / str(tic) / "condition-0-0.5-0.json").unlink()
            with self.assertRaisesRegex(ValueError, "CHECKPOINT_CLOSURE"):
                P.completed(tic, output, False)

    def test_checkpoint_and_result_agreement_does_not_hide_wrong_trial_summary(self):
        tic, output, result = self.condition_fixture()
        result["conditions"][0]["summary"]["counts"][catalog_rows()[0]["source_id"]] = 19
        for path, value in ((P.OUT / f"m2p-{tic}.json", result),
                            (P.DATA / str(tic) / "condition-0-0.5-0.json", result["conditions"][0])):
            path.unlink()
            P.M.save(path, value)
        with mock.patch.object(P, "catalog", return_value=(catalog_rows(), catalog_rows()[0])), \
                self.assertRaisesRegex(ValueError, "CONDITION_RECEIPT"):
            P.completed(tic, output, False)

    def test_partial_checkpoint_retained_on_input_failure_replay_is_read_only(self):
        tic = P.TICS[0]
        def partial(tic, emit):
            emit("primary", {"synthetic": True})
            raise ValueError("synthetic later measurement failure")
        with mock.patch.object(P, "measure", side_effect=partial) as measure, \
                mock.patch.object(P.N, "module", return_value=SimpleNamespace(peak_memory=lambda: 100)):
            P.worker(tic, False)
            result = P.read(P.OUT / f"m2p-{tic}.json")
            self.assertEqual(result["status"], "STOP_INPUT_OR_MEASUREMENT")
            self.assertTrue((P.DATA / str(tic) / "primary.json").is_file())
            before = {p.as_posix(): p.read_bytes() for p in P.ROOT.rglob("*") if p.is_file()}
            P.worker(tic, True)
            self.assertEqual(before, {p.as_posix(): p.read_bytes() for p in P.ROOT.rglob("*") if p.is_file()})
            with self.assertRaises(FileExistsError):
                P.worker(tic, False)
            self.assertEqual(measure.call_count, 2)

    def test_scientific_budget_leaves_terminal_summary_reserve(self):
        virtual = P.DATA / "virtual-existing.json"
        P.M.save(virtual, {"synthetic": True})
        original = Path.stat
        def stat(path, *args, **kwargs):
            actual = original(path, *args, **kwargs)
            return SimpleNamespace(st_size=98_999_000, st_mode=actual.st_mode) if path == virtual else actual
        with mock.patch.object(Path, "stat", stat):
            with self.assertRaisesRegex(RuntimeError, "OUTPUT_CAP"):
                P.save(P.DATA / "new-science.json", {"oversized": "x" * 5000})
            P.save(P.OUT / "m2p-summary.json", {"status": "STOP_RESOURCE", "synthetic": True}, terminal=True)
        self.assertFalse((P.DATA / "new-science.json").exists())
        self.assertTrue((P.OUT / "m2p-summary.json").exists())

    def test_replay_rejects_success_after_previous_failed_worker(self):
        outcomes = []
        for index, tic in enumerate(P.TICS):
            result = {"tic": tic, "status": "STOP_INPUT_OR_MEASUREMENT", "manifest_sha256": self.digest,
                      "unknown_search_authorized": False, "physical_depth_validated": False, "network_requests": 0}
            P.M.save(P.OUT / f"m2p-{tic}.json", result)
            P.M.save(P.DATA / f"runtime-{tic}.json", {"elapsed_seconds": .01, "peak_working_set_bytes": 100})
            P.M.save(P.DATA / f"worker-{tic}.json", {"tic": tic, "manifest_sha256": self.digest})
            text = P.json.dumps({"tic": tic, "status": result["status"], "replay": False})
            outcomes.append({"tic": tic, "returncode": 1 if index == 0 else 0,
                             "worker_returncode": 1 if index == 0 else 0,
                             **P.output_receipt(text), "worker_output": P.output_receipt(text)})
        P.M.save(P.OUT / "m2p-summary.json", {"manifest_sha256": self.digest, "artifacts": P.artifacts(),
                                            "outcomes": outcomes, "unknown_search_authorized": False})
        with mock.patch.object(P.N, "module") as launch, self.assertRaisesRegex(ValueError, "OUTCOME_ORDER"):
            P.run(True, None)
        launch.assert_not_called()

    def test_incomplete_success_receipt_blocks_further_launches(self):
        # An OS-success worker is not a validated scientific outcome if it omitted
        # all required files. Preserve that distinction rather than silently pass.
        (P.DATA / "run-start.json").unlink()
        runner = SimpleNamespace(bounded_run=mock.Mock(return_value=(0, 'synthetic incomplete success')))
        with mock.patch.object(P.N, "module", return_value=runner), \
                self.assertLogs(level="ERROR"), self.assertRaises(SystemExit):
            P.run(False, self.digest)
        summary = P.read(P.OUT / "m2p-summary.json")
        self.assertEqual([r["tic"] for r in summary["outcomes"]], list(P.TICS))
        self.assertEqual(summary["outcomes"][0]["worker_returncode"], 0)
        self.assertNotEqual(summary["outcomes"][0]["returncode"], 0)
        self.assertTrue(all(r["output"] == "STOP_NOT_LAUNCHED" for r in summary["outcomes"][1:]))
        runner.bounded_run.assert_called_once()

    def test_utf8_output_prefix_stays_within_limit_and_full_hash_is_retained(self):
        text = "\u2605" * 6000
        receipt = P.output_receipt(text)
        self.assertLessEqual(len(receipt["output"].encode()), 16_000)
        self.assertEqual(receipt["output_bytes"], 18_000)
        self.assertEqual(receipt["output_sha256"], P.hashlib.sha256(text.encode()).hexdigest())
        self.assertTrue(receipt["output_truncated"])
        P.validate_output_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
