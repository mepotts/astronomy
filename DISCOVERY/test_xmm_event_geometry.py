"""Synthetic EVENTS geometry only; no retained products or value reads."""

import json
import math
import unittest
import warnings
from dataclasses import FrozenInstanceError, replace
from itertools import product
from unittest.mock import patch

import numpy as np
import xmm_event_geometry as g
from astropy.io import fits
from astropy.wcs import WCS


def header(ra=137., dec=-32.):
    return [('XTENSION', 'BINTABLE'), ('EXTNAME', 'EVENTS'), ('TTYPE6', 'X'), ('TTYPE7', 'Y'),
            ('TFORM6', 'J'), ('TFORM7', '1J'), ('TUNIT6', 'pixel'), ('TUNIT7', 'pixel'),
            ('TNULL6', -99999999), ('TNULL7', -99999999), ('TCTYP6', 'RA---TAN'), ('TCTYP7', 'DEC--TAN'),
            ('TCUNI6', 'deg'), ('TCUNI7', 'deg'), ('TCDLT6', -1.38888888888889e-05), ('TCDLT7', 1.38888888888889e-05),
            ('TCRPX6', 113.25), ('TCRPX7', 207.75), ('TCRVL6', ra), ('TCRVL7', dec),
            ('RADECSYS', 'FK5'), ('EQUINOX', 2000.),
            ('TTYPE2', 'RAWX'), ('TTYPE3', 'RAWY'), ('TTYPE4', 'DETX'), ('TTYPE5', 'DETY'),
            ('TCTYP4', 'DETX'), ('TCTYP5', 'DETY'), ('TCRPX4', 900.), ('TCRPX5', 300.),
            ('TCRVL4', 0.), ('TCRVL5', 0.), ('TCDLT4', 2.), ('TCDLT5', 3.)]


def changed(items, key, value):
    return [(k, v) for k, v in items if k != key] + [(key, value)]


def vectors(sky):
    a, d = np.deg2rad(sky[:, 0]), np.deg2rad(sky[:, 1])
    return np.column_stack((np.cos(d) * np.cos(a), np.cos(d) * np.sin(a), np.sin(d)))


def oracle(reference, xy):
    px, py, ra, dec = reference
    a, d = math.radians(ra), math.radians(dec)
    z = np.array([math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)])
    east = np.array([-math.sin(a), math.cos(a), 0.])
    north = np.array([-math.sin(d) * math.cos(a), -math.sin(d) * math.sin(a), math.cos(d)])
    v = z + np.deg2rad((xy[:, 0] - px) * -1.38888888888889e-05)[:, None] * east
    v += np.deg2rad((xy[:, 1] - py) * 1.38888888888889e-05)[:, None] * north
    return v / np.linalg.norm(v, axis=1)[:, None]


class EventGeometryTests(unittest.TestCase):
    def setUp(self):
        self.geometry = g.build_geometry(header())
        self.centres = np.array([[137., -32.], [137., -31.9667], [137.04, -32.],
                                 [137., -32.0333], [136.96, -32.]])

    def test_origin_reference_and_independent_tan_oracle(self):
        for ra, dec in ((137., -32.), (359.999, 70.), (0.001, -70.)):
            definition = g.build_geometry(header(ra, dec))
            w = g._make_wcs(definition)
            xy = np.array(list(product([-4000., -1., 0., 1., 4000.], repeat=2))) + [113.25, 207.75]
            sky = g._project(w, xy)
            expected, actual = oracle(definition.reference, xy), vectors(sky)
            error = np.arctan2(np.linalg.norm(np.cross(expected, actual), axis=1), (expected * actual).sum(axis=1))
            self.assertLess(float(np.rad2deg(error).max() * 3600), 1e-8)
            np.testing.assert_allclose(w.wcs_world2pix(sky, 1), xy, rtol=0, atol=1e-6)
            np.testing.assert_allclose(w.wcs_pix2world(xy, 1), w.wcs_pix2world(xy - 1, 0), rtol=0, atol=1e-12)
            np.testing.assert_allclose(w.wcs_pix2world([[113.25, 207.75]], 1), [[ra, dec]], rtol=0, atol=1e-12)
            wrong = w.wcs_pix2world([[113.25, 207.75]], 0)
            self.assertGreater(float(g._distance(wrong, np.array([[ra, dec]]))[0, 0]), .07)

    def test_direct_pixel_table_selected_axes_match_adapter(self):
        # Native pixel-list frame keywords avoid any global-image repair warning.
        h = fits.Header(dict(changed(header(), 'RADECSYS', 'FK5')))
        del h['RADECSYS']
        del h['EQUINOX']
        h['RADE6'] = 'FK5'
        h['EQUI6'] = 2000.
        h['NAXIS'] = 2
        h['NAXIS1'] = 45
        h['NAXIS2'] = 10
        h['TFIELDS'] = 15
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            direct = WCS(h, keysel=['pixel'], colsel=[6, 7], fix=False, relax=False)
        self.assertEqual(caught, [])
        self.assertEqual(direct.wcs.radesys, 'FK5')
        self.assertEqual(direct.wcs.equinox, 2000.)
        xy = np.array([[113., 208.], [500., -200.], [-15., 19.]])
        self.assertEqual(direct.pixel_n_dim, 2)
        np.testing.assert_allclose(direct.wcs_pix2world(xy, 1), g._project(g._make_wcs(self.geometry), xy), rtol=0, atol=1e-11)

    def test_immutable_definition_safe_metadata_and_frame_alias(self):
        with self.assertRaises(FrozenInstanceError):
            self.geometry.reference = (1., 2., 3., 4.)
        self.assertNotIn('137', repr(self.geometry))
        self.assertNotIn('137', json.dumps(self.geometry.metadata()))
        self.assertEqual(g.build_geometry(header() + [('RADESYS', 'FK5')]), self.geometry)
        modern = [(k, v) for k, v in header() if k != 'RADECSYS'] + [('RADESYS', 'FK5')]
        self.assertEqual(g.build_geometry(modern), self.geometry)
        for bad in (replace(self.geometry, reference=list(self.geometry.reference)),
                    replace(self.geometry, reference=(1., 2., float('nan'), 3.)),
                    replace(self.geometry, reference=(1., 2., 360., 3.))):
            with self.assertRaises(ValueError):
                g.classify_xy(np.array([], int), np.array([], int), np.array([], bool), bad, self.centres, accounting={})

    def test_required_fields_sign_scale_frame_and_duplicates_rejected(self):
        cases = [('TTYPE6', 'DETX'), ('TCTYP6', 'DEC--TAN'), ('TCTYP7', 'DEC--SIN'),
                 ('TFORM6', 'E'), ('TNULL6', -99999999.), ('TUNIT6', 'arcsec'), ('TCUNI6', 'rad'),
                 ('TCDLT6', 1.38888888888889e-05), ('TCDLT7', 2.77777777777778e-05),
                 ('TCRPX6', True), ('TCRVL6', float('inf')), ('TCRVL7', 90.),
                 ('RADECSYS', 'ICRS'), ('EQUINOX', 1950.)]
        for key, value in cases:
            with self.subTest(key=key), self.assertRaises((ValueError, TypeError)):
                g.build_geometry(changed(header(), key, value))
        for key in ('TCRPX6', 'TCUNI7', 'RADECSYS'):
            with self.subTest(missing=key), self.assertRaises((ValueError, TypeError)):
                g.build_geometry([(k, v) for k, v in header() if k != key])
        with self.assertRaisesRegex(ValueError, 'STOP_DUPLICATE_WCS'):
            g.build_geometry(header() + [('TCRPX6', 113.25)])
        with self.assertRaisesRegex(ValueError, 'STOP_FRAME'):
            g.build_geometry(header() + [('RADESYS', 'ICRS')])

    def test_unsupported_table_image_distortion_and_alternate_families(self):
        keys = ['TPC6_7', 'TP6_7A', 'TCD6_7', 'TC6_7Z', 'TPV6_1', 'TV6_1A', 'TPS7_0', 'TS7_0A',
                'TCROT6', 'TCROT4', 'TCTY6A', 'TCUN7B', 'TCRP6A', 'TCRV7Z', 'TCDE6A',
                'WCST6', 'WCSX7A', 'LONP6', 'LATP7A', 'RADE6', 'EQUI7', 'EPOCH',
                'PC1_2', 'CD1_2', 'PV1_1', 'PS2_0', 'CTYPE1', 'WCSAXES', 'LONPOLE', 'LATPOLE',
                'CPDIS1', 'CQDIS2', 'DP1', 'DQ2', 'D2IMDIS1', 'DET2IM1', 'A_ORDER', 'B_1_0',
                'AP_ORDER', 'BP_1_2', 'TSCAL6', 'TZERO7', 'TDIM6', 'TPC0607', 'TCRPX06']
        for key in keys:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'STOP_UNSUPPORTED_WCS'):
                g.build_geometry(header() + [(key, 1)])

    def test_non_wcs_time_and_processing_flags_do_not_collide_with_distortions(self):
        harmless = [('TSTART', 100.), ('TSTOP', 200.), ('DPSCORRF', 'VALID')]
        self.assertEqual(g.build_geometry(header() + harmless), self.geometry)
        for key in ('DP1', 'DP1.AXIS.1', 'DQ2', 'DQ2.EXTVER', 'TS6_0', 'TS7_1A'):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'STOP_UNSUPPORTED_WCS'):
                g.build_geometry(header() + harmless + [(key, 1)])

    def test_null_and_supplied_mask_gate_before_projection(self):
        x = np.array([113, -99999999, 113, 114, 115], np.int32)
        y = np.array([208, 208, -99999999, 209, 210], np.int32)
        valid = np.array([True, True, True, False, True])
        original = (x.copy(), y.copy(), valid.copy())
        progress = {}
        with patch.object(g, '_project', wraps=g._project) as project:
            result = g.classify_xy(x, y, valid, self.geometry, self.centres, accounting=progress)
        np.testing.assert_array_equal(project.call_args.args[1], [[113., 208.], [115., 210.]])
        np.testing.assert_array_equal(result['valid'], [True, False, False, False, True])
        self.assertFalse(result['circle20'][1:4].any())
        self.assertEqual(progress['input_rows'], 5)
        self.assertEqual(progress['masked_rows'], 3)
        self.assertEqual(progress['projection_completed_rows'], 2)
        self.assertEqual(progress['rows_completed'], 5)
        for after, before in zip((x, y, valid), original, strict=True):
            np.testing.assert_array_equal(after, before)
        for value in result.values():
            self.assertFalse(value.flags.writeable)

    def test_empty_all_invalid_and_bound(self):
        for size in (0, 3, 10000):
            progress = {}
            with patch.object(g, '_project', side_effect=AssertionError('must not project')):
                result = g.classify_xy(np.zeros(size, np.int32), np.zeros(size, np.int32), np.zeros(size, bool),
                                       self.geometry, self.centres, accounting=progress)
            self.assertEqual(result['circle20'].shape, (size, 5))
            self.assertEqual(progress['projection_attempted_rows'], 0)
            self.assertEqual(progress['rows_completed'], size)
        with self.assertRaises(ValueError):
            g.classify_xy(np.zeros(10001, int), np.zeros(10001, int), np.ones(10001, bool),
                          self.geometry, self.centres, accounting={})

    def test_reject_masked_wrong_shapes_dtypes_and_unbounded_integers(self):
        defaults = [np.array([113], np.int32), np.array([208], np.int32), np.array([True]), self.centres]
        cases = [(0, np.array([113.0])), (0, np.array([True])), (0, np.array([113], np.uint32)),
                 (0, np.array([2**31], np.int64)), (0, np.ma.array([113], mask=[False])),
                 (1, np.array([208, 209])), (2, np.array([1])), (3, np.zeros((4, 2))),
                 (3, np.full((5, 2), float('nan'))), (3, np.full((5, 2), True))]
        for index, bad in cases:
            args = list(defaults)
            args[index] = bad
            with self.subTest(index=index, dtype=str(bad.dtype)), self.assertRaises(ValueError):
                g.classify_xy(*args[:3], self.geometry, args[3], accounting={})

    def test_literal_boundaries_and_just_inside_outside(self):
        distances = np.array([0., np.nextafter(20., 0.), 20., np.nextafter(20., 100.),
                              np.nextafter(60., 0.), 60., np.nextafter(60., 100.),
                              np.nextafter(90., 0.), 90., np.nextafter(90., 100.)])
        circle, annulus = g._regions(distances)
        np.testing.assert_array_equal(circle, [1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        np.testing.assert_array_equal(annulus, [0, 0, 0, 0, 0, 1, 1, 1, 1, 0])

    def test_five_centres_spherical_not_planar_membership_and_shared_rows(self):
        # Controlled projection isolates the fixed region classifier, all five columns.
        sky = self.centres.copy()
        x, y, valid = np.arange(5, dtype=np.int32), np.arange(5, dtype=np.int32), np.ones(5, bool)
        with patch.object(g, '_project', return_value=sky):
            result = g.classify_xy(x, y, valid, self.geometry, self.centres, accounting={})
        np.testing.assert_array_equal(result['circle20'], np.eye(5, dtype=bool))
        self.assertFalse((result['circle20'] & result['annulus60_90']).any())
        repeated_centres = np.repeat(self.centres[:1], 5, axis=0)
        with patch.object(g, '_project', return_value=sky):
            result = g.classify_xy(x, y, valid, self.geometry, repeated_centres, accounting={})
        self.assertTrue(result['circle20'][0].all())  # Overlaps aren't forced into exclusive assignment.
        distance = g._distance(np.array([[359.999, 70.]]), np.array([[0.001, 70.]]))
        self.assertLess(distance[0, 0], 3.)  # RA difference is not a flat Euclidean distance.

    def test_failure_accounting_at_projection_validation_and_classification(self):
        args = (np.array([113]), np.array([208]), np.array([True]), self.geometry, self.centres)
        for name, failure, phase, completed, unknown in (
                ('_project', MemoryError('private coordinates'), 'PROJECTING', 0, True),
                ('_distance', MemoryError('private coordinates'), 'CLASSIFYING', 1, False)):
            progress = {}
            with patch.object(g, name, side_effect=failure), self.assertRaises(MemoryError):
                g.classify_xy(*args, accounting=progress)
            self.assertEqual(progress['phase'], phase)
            self.assertEqual(progress['projection_completed_rows'], completed)
            self.assertEqual(progress['current_projection_completion_unknown'], unknown)
            self.assertEqual(progress['rows_completed'], 0)
            self.assertNotIn('private', json.dumps(progress))
        progress = {}
        with patch.object(g, '_project', return_value=np.array([[np.nan, 0.]])), self.assertRaisesRegex(ValueError, 'STOP_PROJECTED_COORDINATES'):
            g.classify_xy(*args, accounting=progress)
        self.assertEqual(progress['projection_completed_rows'], 1)
        self.assertFalse(progress['current_projection_completion_unknown'])

    def test_warning_stops_and_fresh_accounting(self):
        def noisy(*args, **kwargs):
            warnings.warn('private synthetic reference', UserWarning, stacklevel=2)
            return WCS(*args, **kwargs)

        with patch.object(g, 'WCS', side_effect=noisy), self.assertRaisesRegex(ValueError, 'STOP_WCS_CONSTRUCTION'):
            g.build_geometry(header())
        with self.assertRaisesRegex(ValueError, 'STOP_ACCOUNTING_ARGUMENT'):
            g.classify_xy(np.array([1]), np.array([2]), np.array([True]), self.geometry, self.centres, accounting={'status': 'old'})


if __name__ == '__main__':
    unittest.main()
