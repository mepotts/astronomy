"""Synthetic implementation checks, not empirical discovery validation."""

import importlib.util
import unittest
from pathlib import Path

import numpy as np
from astropy.wcs import WCS

SPEC = importlib.util.spec_from_file_location("m1_tests", Path(__file__).resolve().parents[1] / "scripts/m1.py")
m1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m1)


class PairedEstimatorTests(unittest.TestCase):
    def test_local_pairing_cancels_linear_drift_with_asymmetric_gaps(self):
        t = np.arange(.00017, 12., 120 / 86400)
        t = t[~((t > 4.11) & (t < 4.14))]
        period, epoch, duration = .237, .043, 8 / 1440
        inside = np.abs((t - epoch + period / 2) % period - period / 2) < duration / 2
        flux = (3. + .8 * t - .2 * inside)[:, None, None]
        errors = (0.01 + .0001 * t)[:, None, None]
        centers, events = m1.paired_events(t, flux, errors, period, epoch, duration)
        self.assertGreater(len(centers), 20)
        np.testing.assert_allclose(events[:, 0, 0], .2, atol=1e-12)

    def test_off_phase_control_is_zero_for_isolated_box_signal(self):
        t = np.arange(.00017, 12., 120 / 86400)
        period, epoch, duration = .237, .043, 8 / 1440
        inside = np.abs((t - epoch + period / 2) % period - period / 2) < duration / 2
        flux = (3. + .8 * t - .2 * inside)[:, None, None]
        errors = np.ones_like(flux)
        for offset in (.25, .75):
            _, events = m1.paired_events(t, flux, errors, period, epoch, duration, offset=offset)
            np.testing.assert_allclose(events, 0, atol=1e-12)

    def test_missing_pixels_are_not_converted_to_zero(self):
        t = np.array([0., 1., 2.])
        cube = np.array([[[1., np.nan]], [[2., np.nan]], [[3., np.nan]]])
        mean, mean_time = m1.window_mean(t, cube, np.ones_like(cube), np.ones(3, dtype=bool))
        self.assertEqual(mean[0, 0], 2.)
        self.assertEqual(mean_time[0, 0], 1.)
        self.assertTrue(np.isnan(mean[0, 1]))

    def test_insufficient_events_and_day_coverage_stop(self):
        t = np.arange(0, 1, 120 / 86400)
        with self.assertRaisesRegex(ValueError, "STOP_PAIRED_EVENTS"):
            m1.paired_events(t, np.ones((len(t), 1, 1)), np.ones((len(t), 1, 1)), .237, .043, 8 / 1440)
        with self.assertRaisesRegex(ValueError, "STOP_DAY_COVERAGE"):
            m1.day_blocks(np.linspace(0, 8, 30), np.ones((30, 1, 1)), 0.)

    def test_day_blocks_preserve_pixel_covariance_in_aperture_error(self):
        centers = np.arange(12) + .3
        common = np.arange(12, dtype=float)
        images = np.stack([common, common], axis=1)[:, None, :]
        blocks, labels = m1.day_blocks(centers, images, 0)
        result = m1.block_statistics(blocks, np.ones((1, 2), dtype=bool))
        self.assertEqual(len(labels), 12)
        self.assertAlmostEqual(result["error"], 2 * common.std(ddof=1) / np.sqrt(12))


class CentroidTests(unittest.TestCase):
    def test_gaussian_plane_recovers_unbiased_center_without_target_initialization(self):
        yy, xx = np.indices((11, 11))
        for cx, cy in ((5.2, 4.7), (2.2, 7.4)):
            parameters = [10., cx, cy, .9, 1.2, .2, 4., .13, -.06]
            image = m1.gaussian_plane(parameters, xx, yy)
            result = m1.fit_centroid(image, np.ones_like(image) * .1, np.ones_like(image, dtype=bool))
            self.assertTrue(result["success"])
            self.assertFalse(result["bound_hit"])
            self.assertAlmostEqual(result["x"], cx, places=5)
            self.assertAlmostEqual(result["y"], cy, places=5)

    def test_insufficient_or_zero_error_pixels_stop_centroid(self):
        image = np.ones((11, 11))
        result = m1.fit_centroid(image, np.zeros_like(image), np.ones_like(image, dtype=bool))
        self.assertFalse(result["success"])

    def test_wcs_zero_based_xy_not_row_column_transposed(self):
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [6., 6.]
        wcs.wcs.cdelt = [-.005, .005]
        wcs.wcs.crval = [150., -30.]
        wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        np.testing.assert_allclose(wcs.world_to_pixel_values(150., -30.), [5., 5.], atol=1e-10)
        sky = wcs.pixel_to_world_values(2., 7.)
        np.testing.assert_allclose(wcs.world_to_pixel_values(*sky), [2., 7.], atol=1e-9)


if __name__ == "__main__":
    unittest.main()
