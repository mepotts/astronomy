"""Synthetic scalar-loop/counting oracles; no event products or WCS reads."""

import copy
import unittest

import numpy as np
from xmm_recorded_counts import (
    BINS,
    DTYPES,
    FIELDS,
    camera_config,
    checked_add_counts,
    count_chunk,
    fixed_edges,
)


def decoded(camera='EPN', n=1, **changes):
    config = camera_config(camera)
    data = {name: np.zeros(n, dtype=dtype) for name, dtype in zip(FIELDS, DTYPES, strict=True)}
    data['TIME'][:] = config['tstart']
    data['CCDNR'][:] = 1
    data['PI'][:] = 1000
    for key, value in changes.items():
        data[key][:] = value
    sentinels = {'X': -99999999, 'Y': -99999999}
    if camera == 'EPN':
        sentinels.update(PI=-32768, PATTERN=13)
    masks = {}
    valid = np.ones(n, dtype=bool)
    for name, value in data.items():
        null = value == sentinels[name] if name in sentinels else np.zeros(n, dtype=bool)
        nonfinite = ~np.isfinite(value)
        good = ~(null | nonfinite)
        masks[name] = {'null': null, 'nonfinite': nonfinite, 'valid': good}
        valid &= good
    return {'values': data, 'masks': masks, 'row_valid': valid, 'flag_bits': data['FLAG'].view(np.uint32),
            'accounting': {'row_start': 0, 'rows_decoded': n, 'buffer_bytes_supplied': n * config['row_bytes'],
                           'selected_field_bytes_decoded': 28 * n,
                           'unselected_bytes_present': n * (config['row_bytes'] - 28)}}


def geometry(d):
    valid = d['masks']['X']['valid'] & d['masks']['Y']['valid']
    circles, annuli = np.zeros((len(valid), 5), bool), np.zeros((len(valid), 5), bool)
    circles[valid, 0] = True
    annuli[valid, 1] = True
    return {'valid': valid.copy(), 'circle20': circles, 'annulus60_90': annuli}


def count(d, camera='EPN', member=None):
    return count_chunk(d, geometry(d) if member is None else member, camera_config(camera), fixed_edges())


class Tests(unittest.TestCase):
    def test_maximum_chunk_and_single_row_over_cap(self):
        self.assertEqual(count(decoded(n=10000))['accepted_rows'], 10000)
        with self.assertRaisesRegex(ValueError, 'STOP_ROW_CAP'):
            count(decoded(n=10001))

    def test_fixed_grid_and_empty(self):
        edges = fixed_edges()
        self.assertEqual(len(edges), 255)
        self.assertTrue(np.all(np.diff(edges) == 200))
        r = count(decoded(n=0))
        self.assertEqual(r['circle20'].shape, (254, 5))
        self.assertEqual(r['rows'], 0)
        self.assertEqual(r['accepted_rows'], 0)
        self.assertEqual(len(r['per_ccd']), 12)

    def test_disjoint_priority_all_reasons(self):
        c = camera_config('EPN')
        d = decoded(n=7, TIME=[np.nan, c['tstart'], c['tstart'] - 1, c['tstart'], c['tstart'], c['tstart'], c['tstart']],
                    CCDNR=[0, 0, 1, 1, 1, 1, 1], PI=[0, 0, 0, 200, 1000, 1000, 1000],
                    PATTERN=[0, 0, 0, 9, 5, 0, 0], FLAG=[-1, -1, -1, -1, -1, -1, 0])
        r = count(d)
        self.assertEqual(list(r['rejected'].values()), [1] * 6)
        self.assertEqual(r['accepted_rows'], 1)
        self.assertEqual(r['circle20'].sum(), 1)

    def test_energy_pattern_and_null_camera_boundaries(self):
        for camera, limit in [('EPN', 4), ('EMOS1', 12), ('EMOS2', 12)]:
            r = count(decoded(camera, 6, PI=[199, 200, 201, 11999, 12000, 12001]), camera)
            self.assertEqual(r['accepted_rows'], 2)
            self.assertEqual(r['rejected']['outside_energy_band'], 4)
            r = count(decoded(camera, 3, PATTERN=[limit - 1, limit, limit + 1]), camera)
            self.assertEqual(r['accepted_rows'], 2)
            # pn13 is a null, whereas MOS13 is a valid scalar rejected by pattern.
            r = count(decoded(camera, 1, PATTERN=13), camera)
            self.assertEqual(r['rejected']['invalid_selected_field'], int(camera == 'EPN'))
            self.assertEqual(r['rejected']['pattern_above_limit'], int(camera != 'EPN'))

    def test_inclusive_header_times_halfopen_bins_unsorted_duplicates(self):
        for camera in ['EPN', 'EMOS1', 'EMOS2']:
            c, e = camera_config(camera), fixed_edges()
            times = [c['tstop'], c['tstart'], c['tstart'] - 1e-5, c['tstop'] + 1e-5, e[10], e[10], e[10] - 1e-5]
            r = count(decoded(camera, len(times), TIME=times), camera)
            self.assertEqual(r['accepted_rows'], 5)
            self.assertEqual(r['rejected']['outside_header_interval'], 2)
            self.assertEqual(r['circle20'][10, 0], 2)
            self.assertEqual(r['circle20'][9, 0], 1)
            self.assertEqual(r['accepted_outside_grid'], 0)

    def test_ccd_sets_full_signed_flag_and_per_ccd_zeros(self):
        for camera, nccd in [('EPN', 12), ('EMOS1', 5), ('EMOS2', 7)]:
            r = count(decoded(camera, 4, CCDNR=[0, 1, 3, 255], FLAG=[0, -2147483648, 0, -1]), camera)
            self.assertEqual(len(r['per_ccd']), nccd)
            self.assertEqual(r['rejected']['unsupported_ccd'], 3 if camera == 'EMOS1' else 2)
            self.assertEqual(r['rejected']['nonzero_flag'], 1)
            self.assertEqual(r['accepted_rows'], 0 if camera == 'EMOS1' else 1)

    def test_overlapping_regions_not_total_event_partition(self):
        d = decoded(n=2)
        m = geometry(d)
        m['circle20'][:] = True
        m['annulus60_90'][:] = False
        r = count(d, member=m)
        self.assertEqual(r['accepted_rows'], 2)
        self.assertEqual(r['circle20'].sum(), 10)
        np.testing.assert_array_equal(r['per_ccd'][0]['circle20'], [2] * 5)

    def test_all_missing_diagnostics_overlap_not_dropped(self):
        d = decoded(n=3, TIME=[np.nan, np.inf, -np.inf], X=-99999999, PI=-32768, PATTERN=13)
        r = count(d)
        self.assertEqual(r['rejected']['invalid_selected_field'], 3)
        self.assertEqual(r['accepted_rows'], 0)
        self.assertEqual(r['field_diagnostics']['X']['null_rows'], 3)
        self.assertEqual(r['field_diagnostics']['PI']['null_rows'], 3)
        self.assertEqual(r['field_diagnostics']['TIME']['nonfinite_rows'], 3)

    def test_forged_masks_flags_values_accounting_rejected(self):
        base = decoded(n=2)
        cases = []
        d = copy.deepcopy(base); d['row_valid'][0] = False; cases.append(d)
        d = copy.deepcopy(base); d['masks']['X']['null'][0] = True; cases.append(d)
        d = copy.deepcopy(base); d['values']['PI'] = d['values']['PI'].astype('i8'); cases.append(d)
        d = copy.deepcopy(base); d['values']['TIME'] = np.ma.array(d['values']['TIME']); cases.append(d)
        d = copy.deepcopy(base); d['flag_bits'] = np.ones(2, dtype='u4'); cases.append(d)
        d = copy.deepcopy(base); d['accounting']['rows_decoded'] = True; cases.append(d)
        d = copy.deepcopy(base); d['masks']['PI']['valid'] = np.ones(2, dtype='u1'); cases.append(d)
        for d in cases:
            with self.assertRaises(ValueError):
                count(d)

    def test_geometry_invalid_masks_and_both_projection_conventions(self):
        d = decoded(n=2, PI=[-32768, 1000])
        xy = geometry(d)
        row = copy.deepcopy(xy)
        row['valid'] = d['row_valid'].copy()
        row['circle20'][~row['valid']] = False
        row['annulus60_90'][~row['valid']] = False
        np.testing.assert_array_equal(count(d, member=xy)['circle20'], count(d, member=row)['circle20'])
        bad = copy.deepcopy(xy); bad['valid'][1] = False
        with self.assertRaises(ValueError): count(d, member=bad)
        bad = copy.deepcopy(xy); bad['annulus60_90'][1, 0] = True
        with self.assertRaises(ValueError): count(d, member=bad)
        d = decoded(n=1, X=-99999999)
        bad = geometry(d); bad['circle20'][0, 0] = True
        with self.assertRaises(ValueError): count(d, member=bad)

    def test_config_and_edge_impostors(self):
        d, e = decoded(), fixed_edges()
        for key, value in [('pattern_max', True), ('tstart', str(camera_config('EPN')['tstart'])),
                           ('ccds', [True] + list(range(2, 13))), ('row_bytes', 34)]:
            with self.assertRaises(ValueError):
                count_chunk(d, geometry(d), {**camera_config('EPN'), key: value}, e)
        for bad in [e + 1e-5, e[:-1], e.astype('f4'), np.ma.array(e), e.tolist()]:
            with self.assertRaises(ValueError):
                count_chunk(d, geometry(d), camera_config('EPN'), bad)

    def test_overflow_guard_shapes_negative_and_no_mutation(self):
        total, inc = np.zeros((BINS, 5), dtype='i8'), np.ones((BINS, 5), dtype='i8')
        result = checked_add_counts(total, inc)
        self.assertFalse(result.flags.writeable)
        self.assertFalse(total.any())
        total[0, 0] = np.iinfo(np.int64).max
        with self.assertRaisesRegex(ValueError, 'STOP_COUNT_OVERFLOW_OR_NEGATIVE'):
            checked_add_counts(total, inc)
        for bad in [np.full((BINS, 5), -1, dtype='i8'), np.ones(5, dtype='i8'), inc.astype('u8')]:
            with self.assertRaises(ValueError):
                checked_add_counts(np.zeros_like(total), bad)

    def test_independent_scalar_oracle_and_split_chunk_invariance(self):
        rng = np.random.default_rng(884250101)
        for camera in ['EPN', 'EMOS1', 'EMOS2']:
            c = camera_config(camera)
            n = 311
            d = decoded(camera, n, TIME=rng.uniform(c['tstart'] - 300, c['tstop'] + 300, n),
                        PI=rng.choice([200, 201, 1000, 11999, 12000], n),
                        CCDNR=rng.integers(0, 14, n), PATTERN=rng.integers(0, 16, n), FLAG=rng.choice([0, 0, 0, -1], n))
            m = geometry(d)
            categories = rng.integers(0, 3, (n, 5))
            m['circle20'] = categories == 1
            m['annulus60_90'] = categories == 2
            expected = {'circle20': np.zeros((254, 5), dtype='i8'), 'annulus60_90': np.zeros((254, 5), dtype='i8')}
            rejection = [0] * 6
            for i in range(n):
                v = d['values']
                checks = [not d['row_valid'][i], int(v['CCDNR'][i]) not in c['ccds'],
                          not c['tstart'] <= v['TIME'][i] <= c['tstop'], not 200 < v['PI'][i] < 12000,
                          v['PATTERN'][i] > c['pattern_max'], v['FLAG'][i] != 0]
                if any(checks):
                    rejection[checks.index(True)] += 1
                    continue
                k = next(j for j in range(254) if fixed_edges()[j] <= v['TIME'][i] < fixed_edges()[j + 1])
                for kind, histogram in expected.items():
                    for r in range(5):
                        if m[kind][i, r]: histogram[k, r] += 1
            r = count(d, camera, m)
            self.assertEqual(list(r['rejected'].values()), rejection)
            totals = {key: np.zeros_like(value) for key, value in expected.items()}
            rejections = {key: 0 for key in r['rejected']}
            pieces = []
            for lo, hi in [(0, 73), (73, 190), (190, n)]:
                piece = decoded(camera, hi - lo, **{k: v[lo:hi] for k, v in d['values'].items()})
                piece['accounting']['row_start'] = lo
                result = count(piece, camera, {k: v[lo:hi] for k, v in m.items()})
                pieces.append(result)
                for key, total in totals.items(): totals[key] = checked_add_counts(total, result[key])
                for key in rejections: rejections[key] += result['rejected'][key]
            self.assertEqual(rejections, r['rejected'])
            for key, total in totals.items():
                np.testing.assert_array_equal(total, expected[key])
                np.testing.assert_array_equal(r[key], expected[key])
            for index, ccd in enumerate(r['per_ccd']):
                for key in ('accepted_rows', 'accepted_inside_grid', 'accepted_outside_grid'):
                    self.assertEqual(sum(p['per_ccd'][index][key] for p in pieces), ccd[key])
                for key in ('circle20', 'annulus60_90'):
                    np.testing.assert_array_equal(sum((p['per_ccd'][index][key] for p in pieces),
                                                      np.zeros(5, dtype='i8')), ccd[key])
            for name, diagnostics in r['field_diagnostics'].items():
                for key, total in diagnostics.items():
                    self.assertEqual(sum(p['field_diagnostics'][name][key] for p in pieces), total)


if __name__ == '__main__':
    unittest.main()
