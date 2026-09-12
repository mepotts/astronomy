"""Independent synthetic M2n review; retained science inputs are never opened."""

import importlib.util
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

SPEC = importlib.util.spec_from_file_location("m2n_independent", Path(__file__).parents[1] / "scripts/m2n.py")
N = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(N)


class IndependentMeasurementTests(unittest.TestCase):
    def setup_measurement(self, failing_channel):
        stack = ExitStack()
        self.addCleanup(stack.close)
        t = np.arange(1000, dtype=float) * .01
        aperture = np.ones((5, 5), dtype=bool)
        cubes = [np.full((1000, 5, 5), value) for value in (1., 1., 2., 1.)]
        primary = {"stats": {"amplitude": 10., "error": 1., "snr": 10., "blocks": 11},
                   "events": 30, "day_labels": np.arange(11), "mean_image": np.zeros((5, 5))}
        old = {"primary": primary["stats"], "paired_events": 30, "day_labels": list(range(11)),
               "images": {"difference": np.zeros((5, 5)).tolist()}, "aperture_pixels": 25, "points": 1000}
        stack.enter_context(mock.patch.object(N, "load_data", return_value=(
            t, cubes, aperture, aperture, np.arange(1000), (.4, 0., .02))))
        stack.enter_context(mock.patch.object(N, "read", return_value=old))
        calls = []

        def synthetic_channel(times, cube, errors, args, offset, anchor, *rest):
            if offset == 0:
                return primary, {1, 2}
            channel = "background" if np.all(cube == 2.) else "flux"
            calls.append((offset, channel, anchor, times.copy()))
            if channel == failing_channel:
                raise ValueError("STOP_PIXEL_COVERAGE")
            return {"stats": {"amplitude": .1, "error": 1., "snr": .1, "blocks": 11}}, {1, 2}

        stack.enter_context(mock.patch.object(N, "channel", side_effect=synthetic_channel))
        return calls, t

    def test_successful_flux_is_retained_when_background_fails(self):
        self.setup_measurement("background")
        result = N.measure(N.TICS[0])
        self.assertEqual(len(result["phases"]), 6)
        for row in result["phases"]:
            self.assertIn("flux", row)
            self.assertEqual(row["flux"]["stats"]["amplitude"], .1)
            self.assertNotEqual(row["status"], "QUIET_DIAGNOSTIC")
            self.assertIsNone(row["used_cadences"])
            self.assertIsNone(row["cadence_sha256"])
        self.assertEqual(result["overlap"]["intersection_counts"], [[None] * 6 for _ in range(6)])

    def test_flux_failure_does_not_suppress_predetermined_background_channel(self):
        calls, _ = self.setup_measurement("flux")
        result = N.measure(N.TICS[0])
        self.assertEqual(len(result["phases"]), 6)
        self.assertEqual([(offset, channel) for offset, channel, _, _ in calls],
                         [(offset, channel) for offset in N.PHASES for channel in ("flux", "background")])
        for row in result["phases"]:
            self.assertEqual(row["background"]["stats"]["amplitude"], .1)

    def test_exclusion_applies_before_all_channels_without_moving_anchor(self):
        calls, original = self.setup_measurement(None)
        N.measure(N.TICS[0])
        expected = original[N.safe_times(original, .4, 0., .02)]
        self.assertGreater(expected.min(), original.min())
        for _, _, anchor, times in calls:
            self.assertEqual(anchor, original.min())
            np.testing.assert_array_equal(times, expected)

    def test_original_primary_failure_prevents_new_phase_measurement(self):
        calls, _ = self.setup_measurement(None)
        with mock.patch.object(N, "read", return_value={"primary": {"changed": True}}), \
                self.assertRaisesRegex(ValueError, "PRIMARY_REPLAY"):
            N.measure(N.TICS[0])
        self.assertEqual(calls, [])

    def test_zero_error_and_nan_amplitude_or_snr_cannot_look_quiet(self):
        good = {"amplitude": .1, "error": 1., "snr": .1}
        for changed in ({"error": 0.}, {"amplitude": np.nan}, {"snr": np.nan}, {"snr": np.inf}):
            bad = {**good, **changed}
            self.assertIn("PHASE_ERROR_UNDEFINED", N.flags(bad, good, 10.))
            self.assertIn("BACKGROUND_ERROR_UNDEFINED", N.flags(good, bad, 10.))

    def test_temporal_membership_preserves_large_integer_cadences(self):
        ids = np.array([2**53 + 1, 2**53 + 2, 2**53 + 3], dtype=np.int64)
        self.assertEqual(N.cadence_union(np.array([-2., 0., 2.]), [0.], 1., ids), set(map(int, ids)))


class IndependentReplayTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        for name, path in (("ROOT", root), ("DATA", root / "data/m2n"), ("OUT", root / "out"),
                           ("MANIFEST", root / "data/m2n/manifest.json")):
            stack.enter_context(mock.patch.object(N, name, path))
        stack.enter_context(mock.patch.object(N, "verify"))
        stack.enter_context(mock.patch("builtins.print"))
        self.runner = SimpleNamespace(bounded_run=mock.Mock(side_effect=lambda command, limit: (0, N.json.dumps({
            "tic": int(command[-1]), "status": "WITHIN_FIELD_DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE",
            "replay": True}) + "\n")))
        stack.enter_context(mock.patch.object(N, "module", return_value=self.runner))
        N.M.save(N.MANIFEST, {"synthetic": True})
        digest = N.M.sha(N.MANIFEST)
        N.M.save(N.DATA / "run-start.json", {"manifest_sha256": digest})
        paths = [N.DATA / "run-start.json"]
        outcomes = []
        for tic in N.TICS:
            result = {"tic": tic, "status": "WITHIN_FIELD_DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE",
                      "manifest_sha256": digest, "unknown_search_authorized": False,
                      "physical_depth_validated": False, "network_requests": 0}
            marker, runtime, output = N.DATA / f"worker-{tic}.json", N.DATA / f"runtime-{tic}.json", N.OUT / f"m2n-{tic}.json"
            N.M.save(marker, {"tic": tic, "manifest_sha256": digest})
            N.M.save(runtime, {"elapsed_seconds": .01, "peak_working_set_bytes": 100})
            N.M.save(output, result)
            paths.extend((marker, runtime, output))
            outcomes.append({"tic": tic, "returncode": 0, "output": N.json.dumps({"tic": tic, "status": result["status"], "replay": False}) + "\n"})
        self.summary = {"manifest_sha256": digest, "outcomes": outcomes,
                        "artifacts": {p.relative_to(root).as_posix(): N.M.sha(p) for p in paths},
                        "unknown_search_authorized": False}

    def test_replay_rejects_missing_required_artifact_hash_before_launch(self):
        del self.summary["artifacts"][f"data/m2n/runtime-{N.TICS[0]}.json"]
        N.M.save(N.OUT / "m2n-summary.json", self.summary)
        with self.assertRaises(ValueError):
            N.run(True, None)
        self.runner.bounded_run.assert_not_called()

    def test_replay_rejects_inconsistent_original_worker_output_before_launch(self):
        self.summary["outcomes"][0]["output"] = N.json.dumps({"tic": -1, "status": "MADE_UP", "replay": False})
        N.M.save(N.OUT / "m2n-summary.json", self.summary)
        with self.assertRaises(ValueError):
            N.run(True, None)
        self.runner.bounded_run.assert_not_called()

    def test_complete_consistent_replay_launches_all_three_and_writes_nothing(self):
        N.M.save(N.OUT / "m2n-summary.json", self.summary)
        before = {p.relative_to(N.ROOT).as_posix(): p.read_bytes() for p in N.ROOT.rglob("*") if p.is_file()}
        N.run(True, None)
        self.assertEqual(self.runner.bounded_run.call_count, 3)
        self.assertEqual([call.args[1] for call in self.runner.bounded_run.call_args_list], [180] * 3)
        self.assertEqual(before, {p.relative_to(N.ROOT).as_posix(): p.read_bytes() for p in N.ROOT.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
