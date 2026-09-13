"""Synthetic sky geometry and static-support checks; no retained maps."""

import copy
import json
import unittest
from unittest.mock import patch

import numpy as np
import xmm_map_support as M
from astropy.wcs import WCS, Sip


def wcs_at(shape=(64, 64), centre=(123.456789, -37.123456)):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]
    w.wcs.crpix = [(shape[1] + 1) / 2, (shape[0] + 1) / 2]
    w.wcs.crval = centre
    w.wcs.cdelt = [-4 / 3600, 4 / 3600]
    return w


class Tests(unittest.TestCase):
    def setUp(self):
        self.image = np.ones((64, 64))
        self.centre = (123.456789, -37.123456)
        self.wcs = wcs_at()

    def summary(self, image=None, kind="circle20", wcs=None, centre=None):
        return M.summarize(self.image if image is None else image, self.wcs if wcs is None else wcs,
                           self.centre if centre is None else centre, kind)

    def test_full_circle_two_fixed_resolutions_and_analytical_area(self):
        result = self.summary()
        self.assertEqual(result["status"], "STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE")
        self.assertEqual([r["subdivision"] for r in result["resolutions"]], [4, 8])
        self.assertEqual(result["nominal_subdivision"], 8)
        exact = result["analytical_full_spherical_region_area_arcsec2"]
        self.assertAlmostEqual(exact, np.pi * 400, delta=.001)
        for r in result["resolutions"]:
            self.assertEqual(r["estimated_area_fractions"]["finite_positive"], 1)
            self.assertAlmostEqual(r["estimated_total_area_arcsec2"], exact, delta=exact * .02)
            self.assertEqual(sum(r["selected_subpixel_counts"].values()), r["selected_subpixel_counts"]["finite_positive"])
        self.assertIsNone(result["proximity"]["nearest_unsupported_pixel_centre_arcsec"])

    def test_annulus_area_and_inner_hole(self):
        result = self.summary(kind="annulus60_90")
        exact = result["analytical_full_spherical_region_area_arcsec2"]
        self.assertAlmostEqual(exact, np.pi * (90**2 - 60**2), delta=.01)
        self.assertAlmostEqual(result["resolutions"][1]["estimated_total_area_arcsec2"], exact, delta=exact * .01)
        altered = self.image.copy()
        altered[30:34, 30:34] = 0
        r = self.summary(altered, "annulus60_90")
        self.assertEqual(r["resolutions"][1]["selected_subpixel_counts"]["zero"], 0)

    def test_half_zero_area_not_weighted_by_amplitude(self):
        self.image[:, :32] = 0
        result = self.summary()
        for r in result["resolutions"]:
            self.assertAlmostEqual(r["estimated_area_fractions"]["zero"], .5, places=10)
            self.assertAlmostEqual(r["estimated_area_fractions"]["finite_positive"], .5, places=10)
        self.image[:, 32:] = 1000000
        self.assertEqual(result, self.summary())

    def test_negative_nan_infinity_and_zero_are_disjoint(self):
        self.image[30, 31], self.image[31, 31], self.image[32, 31], self.image[33, 31] = -1, np.nan, np.inf, 0
        result = self.summary()
        fine = result["resolutions"][1]
        self.assertEqual(fine["selected_subpixel_counts"]["negative"], 64)
        self.assertEqual(fine["selected_subpixel_counts"]["nonfinite"], 128)
        self.assertEqual(fine["selected_subpixel_counts"]["zero"], 64)
        self.assertEqual(result["proximity"]["unsupported_image_pixel_count"], 4)
        self.assertAlmostEqual(sum(fine["estimated_area_fractions"].values()), 1)
        json.dumps(result, allow_nan=False)

    def test_partial_outside_image_has_explicit_area_and_sample_counts(self):
        centre = self.wcs.all_pix2world(-.5, 31.5, 0)
        result = self.summary(centre=centre)
        fine = result["resolutions"][1]
        self.assertGreater(fine["selected_subpixel_counts"]["out_of_image"], 0)
        self.assertAlmostEqual(fine["estimated_area_fractions"]["out_of_image"], .5, delta=.01)
        self.assertAlmostEqual(fine["estimated_total_area_arcsec2"], result["analytical_full_spherical_region_area_arcsec2"], delta=20)

    def test_wholly_outside_keeps_full_region_accounting(self):
        result = self.summary(centre=self.wcs.all_pix2world(-30, 31.5, 0))
        self.assertEqual(result["resolutions"][1]["estimated_area_fractions"]["out_of_image"], 1)
        self.assertFalse(result["proximity"]["region_centre_inside_image_rectangle"])

    def test_row_column_order_and_nearest_pixel_centre_not_boundary(self):
        self.image[:] = 1
        self.image[10, 40] = 0
        centre = self.wcs.all_pix2world(40, 10, 0)
        result = self.summary(centre=centre)
        self.assertAlmostEqual(result["proximity"]["nearest_unsupported_pixel_centre_arcsec"], 0, places=9)
        self.assertEqual(result["resolutions"][1]["sampled_intersected_base_pixel_counts"]["zero"], 1)
        far = self.summary(centre=self.wcs.all_pix2world(10, 40, 0))
        self.assertGreater(far["proximity"]["nearest_unsupported_pixel_centre_arcsec"], 100)

    def test_border_sampling_includes_corners_and_no_guarantee(self):
        centre = self.wcs.all_pix2world(-.5, -.5, 0)
        result = self.summary(centre=centre)
        self.assertAlmostEqual(result["proximity"]["nearest_sampled_image_border_arcsec"], 0, places=9)
        self.assertIn("not true nearest-boundary", result["proximity"]["interpretation"])

    def test_ra_wrap_and_rotated_anisotropic_tan(self):
        w = wcs_at(centre=(359.99999, 70))
        angle = .4
        w.wcs.pc = [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
        w.wcs.cdelt = [-3 / 3600, 5 / 3600]
        result = self.summary(wcs=w, centre=(359.99999, 70))
        exact = result["analytical_full_spherical_region_area_arcsec2"]
        self.assertAlmostEqual(result["resolutions"][1]["estimated_total_area_arcsec2"], exact, delta=exact * .02)
        self.assertEqual(result["resolutions"][1]["estimated_area_fractions"]["finite_positive"], 1)

    def test_chunk_size_changes_neither_counts_nor_meaning(self):
        self.image[:32, :] = 0
        first = self.summary(kind="annulus60_90")
        with patch.object(M, "CHUNK_ROWS", 1):
            other = self.summary(kind="annulus60_90")
        for a, b in zip(first["resolutions"], other["resolutions"], strict=True):
            self.assertEqual(a["selected_subpixel_counts"], b["selected_subpixel_counts"])
            for key in M.CATEGORIES:
                self.assertAlmostEqual(a["estimated_area_arcsec2"][key], b["estimated_area_arcsec2"][key], places=8)
        self.assertEqual(first["proximity"], other["proximity"])

    def test_no_absolute_coordinate_or_reference_serialization(self):
        text = json.dumps(self.summary(), allow_nan=False)
        for secret in ("123.456789", "37.123456", "crval", "crpix", "centre_ra", "centre_dec"):
            self.assertNotIn(secret, text)
        self.assertNotIn('"pass"', text)
        self.assertNotIn('"clean"', text)

    def test_masked_non_numeric_large_and_invalid_regions_rejected(self):
        for image in (np.ma.array(self.image), np.zeros((649, 2)), np.zeros((2, 2, 2)), np.zeros((2, 2), dtype=complex)):
            with self.subTest(shape=image.shape), self.assertRaises(ValueError):
                self.summary(image=image)
        with self.assertRaisesRegex(ValueError, "STOP_REGION"):
            self.summary(kind="optimized")

    def test_non_tan_nondegree_distorted_and_wide_region_rejected(self):
        bad = copy.deepcopy(self.wcs)
        bad.wcs.ctype = ["RA---SIN", "DEC--SIN"]
        with self.assertRaisesRegex(ValueError, "STOP_WCS_SCHEMA"):
            self.summary(wcs=bad)
        bad = copy.deepcopy(self.wcs)
        bad.wcs.cunit = ["rad", "rad"]
        with self.assertRaisesRegex(ValueError, "STOP_WCS_SCHEMA"):
            self.summary(wcs=bad)
        bad = copy.deepcopy(self.wcs)
        zeros = np.zeros((3, 3))
        bad.sip = Sip(zeros, zeros, None, None, bad.wcs.crpix)
        with self.assertRaisesRegex(ValueError, "STOP_WCS_SCHEMA"):
            self.summary(wcs=bad)
        with self.assertRaisesRegex(ValueError, "STOP_TAN_RADIUS"):
            self.summary(centre=(130, -37))
        bad = copy.deepcopy(self.wcs)
        bad.wcs.cdelt = [-.01 / 3600, .01 / 3600]
        with self.assertRaisesRegex(ValueError, "STOP_REGION_BOX_CAP"):
            self.summary(wcs=bad)

    def test_roundtrip_mismatch_stops(self):
        original = self.wcs.all_world2pix

        def wrong(ra, dec, origin):
            x, y = original(ra, dec, origin)
            return (x + 1, y) if np.ndim(x) else (x, y)

        with patch.object(self.wcs, "all_world2pix", side_effect=wrong), self.assertRaisesRegex(ValueError, "STOP_WCS_ROUNDTRIP"):
            self.summary()


if __name__ == "__main__":
    unittest.main()
