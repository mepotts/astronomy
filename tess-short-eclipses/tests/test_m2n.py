"""Synthetic software checks, not empirical false-positive validation."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

SPEC = importlib.util.spec_from_file_location("m2n_test", Path(__file__).resolve().parents[1] / "scripts/m2n.py")
N = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(N)


class NegativeTests(unittest.TestCase):
    def test_primary_secondary_and_exact_boundary_excluded(self):
        t = np.array([-1., -.5, -.125, 0., .125, .25, .375, .5, .625, .75, 1.])
        np.testing.assert_array_equal(N.safe_times(t, 1., 0., .125),
                                      [False, False, False, False, False, True, False, False, False, True, False])

    def test_translation_and_wrap(self):
        t = np.arange(-5., 5., .03125)
        np.testing.assert_array_equal(N.safe_times(t, 1., 0., .125), N.safe_times(t + 256, 1., 256., .125))

    def test_invalid_ephemeris(self):
        for args in ((0, 0, .01), (1, np.nan, .01), (1, 0, -.01)):
            with self.assertRaisesRegex(ValueError, "STOP_EPHEMERIS"):
                N.safe_times(np.array([0.]), *args)

    def test_signed_linear_drift_estimator(self):
        t = np.arange(.003, 12., .003)
        args = (.4, .07, .015)
        a = np.ones((5, 5), dtype=bool)
        base = np.broadcast_to((100 + t * 2)[:, None, None], (len(t), 5, 5)).copy()
        errors = np.ones_like(base)
        for sign in (-1, 1):
            cube = base.copy()
            dt = (t - args[1] - .25 * args[0] + args[0] / 2) % args[0] - args[0] / 2
            cube[np.abs(dt) < args[2] / 2] -= sign * 2
            record, used = N.channel(t, cube, errors, args, .25, t.min(), a, a, np.arange(len(t)))
            self.assertAlmostEqual(record["stats"]["amplitude"], sign * 50, places=9)
            self.assertGreater(len(used), 0)

    def test_missing_aperture_pixel_stops(self):
        t = np.arange(0., 12., .002)
        cube = np.ones((len(t), 5, 5))
        cube[:, 0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "STOP_PIXEL_COVERAGE"):
            N.channel(t, cube, np.ones_like(cube), (.4, .1, .02), .25, 0.,
                      np.ones((5, 5), bool), np.ones((5, 5), bool), np.arange(len(t)))

    def test_insufficient_events_stops(self):
        t = np.arange(0., 1., .002)
        cube = np.ones((len(t), 5, 5))
        with self.assertRaisesRegex(ValueError, "STOP_PAIRED_EVENTS"):
            N.channel(t, cube, cube, (.4, .1, .02), .25, 0., np.ones((5, 5), bool),
                      np.ones((5, 5), bool), np.arange(len(t)))

    def test_flags_symmetric_and_primary_reference(self):
        for sign in (-1, 1):
            flux = {"amplitude": sign * 3., "error": 1., "snr": sign * 3.}
            background = {"amplitude": sign * 1.01, "error": .1, "snr": sign * 10.1}
            self.assertEqual(N.flags(flux, background, 10.), ["PHASE_CONTROL_STRUCTURE", "BACKGROUND_COHERENCE"])
            background.update(amplitude=sign * 1.)
            self.assertEqual(N.flags(flux, background, 10.), ["PHASE_CONTROL_STRUCTURE"])

    def test_undefined_error_not_clean(self):
        good = {"amplitude": .1, "error": 1., "snr": .1}
        for error in (0., np.nan, np.inf):
            bad = {"amplitude": .1, "error": error, "snr": None}
            self.assertIn("PHASE_ERROR_UNDEFINED", N.flags(bad, good, 1.))
            self.assertIn("BACKGROUND_ERROR_UNDEFINED", N.flags(good, bad, 1.))

    def test_cadence_union_and_overlap(self):
        t = np.array([-2., -1.5, -.25, .25, 1.5, 2., 3.])
        used = N.cadence_union(t, [0.], 1., np.arange(7))
        self.assertEqual(used, set(range(6)))
        result = N.overlap([used, {5, 6}, set()])
        self.assertEqual(result["intersection_counts"], [[6, 1, 0], [1, 2, 0], [0, 0, 0]])
        self.assertEqual(result["jaccard"][0][1], 1 / 7)
        self.assertIsNone(result["jaccard"][2][2])

    def test_parent_requires_hash(self):
        with (patch.object(N, "verify"), patch.object(N.M, "sha", return_value="correct"),
              self.assertRaisesRegex(ValueError, "STOP_APPROVAL_HASH")):
            N.run(False, "wrong")

    def test_parent_failure_preserves_all_slots_and_stops_launches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (patch.object(N, "DATA", root / "data"), patch.object(N, "OUT", root / "out"),
                  patch.object(N, "ROOT", root), patch.object(N, "verify"),
                  patch.object(N.M, "sha", return_value="hash"),
                  patch.object(N, "module", side_effect=ImportError("fixture"))):
                with self.assertRaises(SystemExit):
                    N.run(False, "hash")
                rows = json.loads((root / "out/m2n-summary.json").read_bytes())["outcomes"]
                self.assertEqual([r["tic"] for r in rows], list(N.TICS))
                self.assertIn("fixture", rows[0]["output"])
                self.assertTrue(all(r["output"] == "STOP_NOT_LAUNCHED" for r in rows[1:]))
                with self.assertRaises(FileExistsError):
                    N.run(False, "hash")


if __name__ == "__main__":
    unittest.main()
