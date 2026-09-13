"""Synthetic attitude diagnostics, including missing rows and privacy."""

import json
import unittest

import numpy as np
import xmm_attitude as M


class Tests(unittest.TestCase):
    def data(self, n=5):
        data = np.zeros((n, 10))
        data[:, 0] = np.arange(n)
        data[:, [1, 4]] = 123.456789
        data[:, [2, 5]] = -37.123456
        data[:, [3, 6]] = 270.123456
        return data

    def summary(self, data):
        return M.summarize(data, [{'camera': 'EPN', 'start': 0, 'stop': 4}],
                           {'NATT': 5, 'NGAHF': 5, 'NGOM': 5, 'NGAHFOM': 0})

    def test_zero_offsets_and_coordinate_privacy(self):
        result = self.summary(self.data())
        self.assertEqual(result['sources']['AHF']['contiguous_one_second_motion_pairs'], 4)
        self.assertEqual(result['offset_columns']['DAHFPNT']['domain_valid_arcsec'], {'min': 0, 'max': 0})
        self.assertEqual(result['joint_finite_domain_valid_triplets'], 5)
        self.assertFalse(result['header_vs_measured_finite_counts']['NGAHFOM_matches_joint_finite'])
        text = json.dumps(result, allow_nan=False)
        for secret in ('123.456789', '-37.123456', '270.123456'):
            self.assertNotIn(secret, text)
        self.assertFalse(result['continuous_motion_bound_established'])

    def test_nan_partial_infinity_and_finite_sentinel_are_distinct(self):
        data = self.data()
        data[1, 1:4] = np.nan
        data[2, 4] = np.inf
        data[3, 1] = -1e30
        result = self.summary(data)
        self.assertEqual(result['sources']['AHF']['all_nan_triplets'], 1)
        self.assertEqual(result['sources']['AHF']['finite_domain_failures'], 1)
        self.assertEqual(result['sources']['OM']['partial_finite_triplets'], 1)
        self.assertEqual(result['column_counts']['OMRA']['infinite'], 1)
        self.assertEqual(result['sources']['AHF']['contiguous_one_second_motion_pairs'], 0)
        json.dumps(result, allow_nan=False)

    def test_wrap_and_poles_use_spherical_distance(self):
        self.assertAlmostEqual(float(M.separation_arcsec(359.999, 0, .001, 0)), 7.2, places=7)
        self.assertLess(float(M.separation_arcsec(0, 90, 180, 90)), 1e-8)
        data = self.data(2)
        data[:, 1:4] = [[359.999, 0, 359.999], [.001, 0, .001]]
        result = self.summary(data)['sources']['AHF']
        self.assertAlmostEqual(result['adjacent_roll_absolute_arcsec']['max'], 7.2, places=7)
        self.assertAlmostEqual(result['adjacent_separation_arcsec']['max'], 7.2, places=7)

    def test_time_gaps_invalid_time_and_nonpositive_steps(self):
        for times in ([0, 1, 3, 4, 5], [0, 1, np.nan, 3, 4], [0, 1, 1, 3, 4]):
            data = self.data()
            data[:, 0] = times
            result = self.summary(data)
            self.assertLess(result['sources']['AHF']['contiguous_one_second_motion_pairs'], 4)
            json.dumps(result, allow_nan=False)
        data[:, 0] = [0, 1, 1, 3, 4]
        self.assertFalse(self.summary(data)['time']['finite_strictly_increasing'])

    def test_all_missing_angles_and_single_row(self):
        data = self.data()
        data[:, 1:] = np.nan
        result = self.summary(data)
        self.assertIsNone(result['sources']['AHF']['first_reference_row'])
        self.assertIsNone(result['sources']['AHF']['separation_from_first_arcsec']['max'])
        self.assertEqual(result['joint_finite_domain_valid_triplets'], 0)
        self.assertEqual(self.summary(self.data(1))['sources']['AHF']['contiguous_one_second_motion_pairs'], 0)

    def test_time_range_is_not_clock_proof(self):
        result = self.summary(self.data())
        self.assertTrue(result['camera_time_range_diagnostics'][0]['strictly_ordered_attitude_brackets_header_range'])
        self.assertFalse(result['clock_reference_verified'])
        self.assertEqual(result['camera_time_range_diagnostics'][0]['finite_samples_within_half_open_header_range'], 4)

    def test_schema_rejected_and_extreme_offsets_remain_flagged(self):
        for data in ([], np.zeros((2, 9)), np.zeros((2, 10), dtype=int), np.empty((0, 10))):
            with self.assertRaises(ValueError):
                self.summary(data)
        data = self.data()
        data[0, 7] = 1e308
        result = self.summary(data)
        self.assertEqual(result['offset_columns']['DAHFPNT']['finite_outside_0_180_degrees'], 1)
        json.dumps(result, allow_nan=False)

    def test_metadata_privacy_keys_and_types_are_allowlisted(self):
        counts = {'NATT': 5, 'NGAHF': 5, 'NGOM': 5, 'NGAHFOM': 0}
        camera = {'camera': 'EPN', 'start': 0, 'stop': 4}
        for changed in ({**camera, 'pointing_ra': 123.456789}, {**camera, 'camera': 'private123.456789'},
                        {**camera, 'start': True}, {**camera, 'stop': np.nan}):
            with self.assertRaises(ValueError):
                M.summarize(self.data(), [changed], counts)
        for changed in ({**counts, 'unrelated_coordinate': 123.456789}, {**counts, 'NATT': True}, {**counts, 'NATT': -1}):
            with self.assertRaises(ValueError):
                M.summarize(self.data(), [camera], changed)
        with self.assertRaisesRegex(ValueError, 'STOP_MASKED_ARRAY_SCHEMA'):
            M.summarize(np.ma.array(self.data(), mask=False), [camera], counts)


if __name__ == '__main__':
    unittest.main()
