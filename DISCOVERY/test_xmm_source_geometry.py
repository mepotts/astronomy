"""Synthetic geometry only; never open a catalogue or image."""

import json
import unittest

import numpy as np
from xmm_source_geometry import FIELDS, contact_masks, separation_arcsec, summarize


def fixture(ra, dec=None):
    ra = np.asarray(ra, dtype=float)
    dec = np.zeros(len(ra)) if dec is None else np.asarray(dec, dtype=float)
    data = {name: np.zeros(len(ra)) for name in FIELDS}
    data.update(SRC_NUM=np.arange(1, len(ra) + 1, dtype=np.int32), RA=ra, DEC=dec,
                RA_CORR=ra.copy(), DEC_CORR=dec.copy())
    return data


CENTRES = np.array([[0, 0], [0, 120 / 3600], [120 / 3600, 0],
                    [0, -120 / 3600], [360 - 120 / 3600, 0]])


class SourceGeometryTests(unittest.TestCase):
    def test_unique_association_and_exemption_only_own_aperture(self):
        # Coincident synthetic centres explicitly prove exemption locality.
        r = summarize(fixture([0]), np.zeros((5, 2)))
        self.assertEqual(r['association']['status'], 'UNIQUE_POSITIONAL_ASSOCIATION')
        self.assertEqual(r['apertures'][0]['centre_within_20']['rows'], 0)
        for aperture in r['apertures'][1:]:
            self.assertEqual(aperture['centre_within_20']['rows'], 1)
            self.assertFalse(aperture['control_row_exempted'])

    def test_no_match_multiple_and_no_nearest_selection(self):
        self.assertEqual(summarize(fixture([1]), CENTRES)['association']['status'], 'NO_MATCH')
        r = summarize(fixture([0, 1 / 3600]), CENTRES)
        self.assertEqual(r['association']['status'], 'MULTIPLE_MATCHES')
        self.assertEqual(r['association']['valid_corrected_matches_within_5'], 2)
        self.assertEqual(r['apertures'][0]['centre_within_20']['rows'], 2)
        self.assertFalse(r['apertures'][0]['control_row_exempted'])

    def test_invalid_corrected_row_prevents_unique_match(self):
        d = fixture([0, 1])
        d['RA_CORR'][1] = np.nan
        r = summarize(d, CENTRES)
        self.assertEqual(r['association']['status'], 'INCOMPLETE_INPUT')
        self.assertEqual(r['association']['valid_corrected_matches_within_5'], 1)
        self.assertEqual(r['rows'], 2)
        self.assertFalse(r['apertures'][0]['control_row_exempted'])

    def test_original_invalidity_separate_and_displacement_retained(self):
        d = fixture([0])
        d['RA'][0] = 60 / 3600
        r = summarize(d, CENTRES)
        self.assertEqual(r['association']['status'], 'UNIQUE_POSITIONAL_ASSOCIATION')
        self.assertFalse(r['association']['original_position_within_20_arcsec'])
        self.assertAlmostEqual(r['association']['original_position_distance_arcsec'], 60, places=10)
        self.assertEqual(r['annuli'][0]['disk_contact_30_to_120']['rows'], 1)
        d['RA'][0] = np.nan
        r = summarize(d, CENTRES)
        self.assertEqual(r['association']['status'], 'UNIQUE_POSITIONAL_ASSOCIATION')
        self.assertIsNone(r['association']['original_position_distance_arcsec'])
        self.assertEqual(r['apertures'][0]['invalid_original_positions'], 1)
        self.assertEqual(r['screen_completeness'], 'INCOMPLETE_CATALOGUE_GEOMETRY_INPUT')

    def test_invalid_and_duplicate_ids_preserve_denominators(self):
        d = fixture([0, 1, 2, 3, 4])
        d['SRC_NUM'] = np.array([7, 7, 0, -1, 2**31], dtype=np.int64)
        r = summarize(d, CENTRES)
        self.assertEqual(r['rows'], 5)
        self.assertEqual(r['identity'], {'invalid_rows': 3, 'duplicate_valid_id_rows': 2,
                                        'duplicate_valid_id_extra_rows': 1, 'duplicate_valid_id_groups': 1})
        self.assertEqual(r['association']['status'], 'INCOMPLETE_INPUT')

    def test_duplicate_positions_are_not_deduplicated(self):
        d = fixture([40 / 3600] * 3)
        d['EP_EXTENT'] = np.array([0, 1, np.nan])
        r = summarize(d, CENTRES)
        record = r['apertures'][0]['disk_contact_within_50']
        self.assertEqual(record, {'rows': 3, 'extent_categories': {'point_model_zero': 1,
                                                                 'extended_model_positive': 1,
                                                                 'invalid_or_unknown': 1}})
        self.assertEqual(r['annuli'][0]['disk_contact_30_to_120']['rows'], 3)

    def test_literal_inclusive_contact_boundaries(self):
        d = np.array([np.nextafter(20., 0), 20., np.nextafter(20., np.inf), 30., 50., 120.,
                      np.nextafter(120., np.inf), np.nan])
        masks = contact_masks(d)
        np.testing.assert_array_equal(masks['centre_within_20'], [1, 1, 0, 0, 0, 0, 0, 0])
        np.testing.assert_array_equal(masks['disk_contact_within_50'], [1, 1, 1, 1, 1, 0, 0, 0])
        np.testing.assert_array_equal(masks['annulus_disk_contact_30_to_120'], [0, 0, 0, 1, 1, 1, 0, 0])
        self.assertFalse(contact_masks(np.array([np.nextafter(30., 0)]))['annulus_disk_contact_30_to_120'][0])

    def test_spherical_distance_oracles_wrap_poles_antipodes(self):
        self.assertAlmostEqual(float(separation_arcsec(359.999, 0, .001, 0)), 7.2, places=7)
        self.assertAlmostEqual(float(separation_arcsec(0, 90, 180, 89)), 3600, places=7)
        self.assertAlmostEqual(float(separation_arcsec(0, 0, 180, 0)), 648000, places=7)
        self.assertLess(float(separation_arcsec(0, 90, 123, 90)), 1e-9)
        # Independent Cartesian cross/dot oracle away from coordinate singularities.
        for a, b in [((359.99, 71), (.01, 71.001)), ((20, -89.999), (250, -89.998))]:
            def vector(p):
                lon, lat = np.deg2rad(p)
                return np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
            u, v = vector(a), vector(b)
            expected = np.rad2deg(np.arctan2(np.linalg.norm(np.cross(u, v)), u @ v)) * 3600
            self.assertAlmostEqual(float(separation_arcsec(*a, *b)), expected, places=8)

    def test_association_inside_outside_fixed_five(self):
        for delta, matches in [(5 - 1e-6, 1), (5 + 1e-6, 0)]:
            r = summarize(fixture([delta / 3600]), CENTRES)
            self.assertEqual(r['association']['valid_corrected_matches_within_5'], matches)
        self.assertAlmostEqual(float(separation_arcsec(0, 0, 5 / 3600, 0)), 5, places=12)

    def test_errors_not_matching_weights_and_invalidity_retained(self):
        d = fixture([0, 1, 2, 3])
        for name in ['RADEC_ERR', 'SYSERRCC', 'EP_EXTENT', 'EP_EXT_ERR']:
            d[name] = np.array([0, -1, np.inf, 1000000])
        r = summarize(d, CENTRES)
        self.assertEqual(r['association']['status'], 'UNIQUE_POSITIONAL_ASSOCIATION')
        for record in r['nonnegative_field_diagnostics'].values():
            self.assertEqual(record['rows'], 4)
            self.assertEqual([record[k] for k in ['nonfinite', 'negative', 'zero', 'positive']], [1, 1, 1, 1])

    def test_input_rejection_bounds_mask_bool_string_shapes(self):
        for bad in [np.array([True]), np.array(['1']), np.ma.array([1], mask=[True])]:
            d = fixture([0])
            d['RA'] = bad
            with self.assertRaises(ValueError):
                summarize(d, CENTRES)
        for bad in [np.zeros((4, 2)), np.full((5, 2), np.nan), np.full((5, 2), 360),
                    np.ma.array(CENTRES, mask=False), np.ones((5, 2), dtype=bool)]:
            with self.assertRaises(ValueError):
                summarize(fixture([0]), bad)
        for d in [fixture(np.zeros(152)), {**fixture([0]), 'SRC_NUM': np.array([1.])},
                  {**fixture([0]), 'DEC': np.zeros(2)}, {**fixture([0]), 'FLUX': np.zeros(1)}]:
            with self.assertRaises(ValueError):
                summarize(d, CENTRES)

    def test_invalid_position_domains_and_empty_rows(self):
        d = fixture([0, 360, -1, 1, np.inf], [0, 0, 0, 91, 0])
        r = summarize(d, CENTRES)
        self.assertEqual(r['positions']['invalid_original'], 4)
        self.assertEqual(r['positions']['invalid_corrected'], 4)
        empty = summarize(fixture([]), CENTRES)
        self.assertEqual(empty['rows'], 0)
        self.assertEqual(empty['association']['status'], 'NO_MATCH')

    def test_public_result_json_no_ids_coordinates_arrays_or_mutation(self):
        d = fixture([0, 1])
        original = {k: v.copy() for k, v in d.items()}
        result = summarize(d, CENTRES)
        self.assertEqual(result, json.loads(json.dumps(result, allow_nan=False)))
        self.assertEqual(result['status'], 'SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY')
        self.assertEqual(len(result['apertures']), 5)
        self.assertEqual(len(result['annuli']), 5)
        labels = ['published', 'north120', 'east120', 'south120', 'west120']
        self.assertEqual([v['region'] for v in result['apertures']], labels)
        self.assertEqual([v['region'] for v in result['annuli']], labels)
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & {'SRC_NUM', 'RA', 'DEC', 'RA_CORR', 'DEC_CORR',
                                               'row_ids', 'row_ordinals', 'clean', 'pass', 'coordinates'})
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
            else:
                self.assertIsInstance(value, (str, int, float, bool, type(None)))
        check(result)
        for name in FIELDS:
            np.testing.assert_array_equal(d[name], original[name])


if __name__ == '__main__':
    unittest.main()
