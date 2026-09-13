"""Pure fixed recorded-count increments; no I/O, exposure or inference.

Inputs are local decoded rows and same-row geometry masks. Outputs are fixed
histograms and aggregate diagnostics only. A successful call is not recovery.
"""

import numpy as np

LABELS = ('published', 'north120', 'east120', 'south120', 'west120')
FIELDS = ('TIME', 'RAWX', 'RAWY', 'X', 'Y', 'PI', 'FLAG', 'PATTERN', 'CCDNR')
DTYPES = ('f8', 'i2', 'i2', 'i4', 'i4', 'i2', 'i4', 'u1', 'u1')
REJECTIONS = ('invalid_selected_field', 'unsupported_ccd', 'outside_header_interval',
              'outside_energy_band', 'pattern_above_limit', 'nonzero_flag')
ANCHOR = 738530124.914825
MAX_ROWS, BINS = 10000, 254


def fixed_edges():
    """255 exact plan edges, 254 half-open bins; no event-time anchoring."""
    result = ANCHOR + 200 * np.arange(-8, 247, dtype=np.float64)
    result.flags.writeable = False
    return result


def camera_config(camera):
    if camera == 'EPN':
        start, stop, ccds, pattern, stride, rows = ANCHOR, 738579196.505283, list(range(1, 13)), 4, 45, 2694388
    elif camera == 'EMOS1':
        start, stop, ccds, pattern, stride, rows = 738528580.207049, 738578603.890584, [1, 2, 4, 5, 7], 12, 34, 273441
    elif camera == 'EMOS2':
        start, stop, ccds, pattern, stride, rows = 738528600.951524, 738578795.595291, list(range(1, 8)), 12, 34, 356129
    else:
        raise ValueError('STOP_CAMERA')
    return {'camera': camera, 'tstart': start, 'tstop': stop, 'ccds': ccds,
            'pattern_max': pattern, 'row_bytes': stride, 'total_rows': rows}


def _config(config, edges):
    if type(config) is not dict or type(config.get('camera')) is not str:
        raise ValueError('STOP_CAMERA_CONFIG')
    expected = camera_config(config['camera'])
    if (set(config) != set(expected) or any(type(config[k]) is not type(v) or config[k] != v
                                          for k, v in expected.items())
            or any(type(v) is not int for v in config['ccds'])):
        raise ValueError('STOP_CAMERA_CONFIG')
    if (np.ma.isMaskedArray(edges) or not isinstance(edges, np.ndarray) or edges.dtype != np.dtype('f8')
            or edges.shape != (BINS + 1,) or not np.array_equal(edges, fixed_edges())):
        raise ValueError('STOP_FIXED_EDGES')


def _array(value, dtype, shape):
    if (np.ma.isMaskedArray(value) or not isinstance(value, np.ndarray)
            or value.dtype != np.dtype(dtype) or value.shape != shape):
        raise ValueError('STOP_ARRAY_SCHEMA')
    return value


def _validate_decoded(decoded, config):
    if (type(decoded) is not dict or set(decoded) != {'values', 'masks', 'row_valid', 'flag_bits', 'accounting'}
            or type(decoded['values']) is not dict or set(decoded['values']) != set(FIELDS)
            or type(decoded['masks']) is not dict or set(decoded['masks']) != set(FIELDS)):
        raise ValueError('STOP_DECODER_SCHEMA')
    time = decoded['values']['TIME']
    if not isinstance(time, np.ndarray) or time.ndim != 1 or len(time) > MAX_ROWS:
        raise ValueError('STOP_ROW_CAP')
    n, diagnostics = len(time), {}
    combined = np.ones(n, dtype=bool)
    nulls = {'X': -99999999, 'Y': -99999999}
    if config['camera'] == 'EPN':
        nulls.update(PI=-32768, PATTERN=13)
    for name, dtype in zip(FIELDS, DTYPES, strict=True):
        value = _array(decoded['values'][name], dtype, (n,))
        masks = decoded['masks'][name]
        if type(masks) is not dict or set(masks) != {'null', 'nonfinite', 'valid'}:
            raise ValueError('STOP_MASK_SCHEMA')
        null = value == nulls[name] if name in nulls else np.zeros(n, dtype=bool)
        nonfinite = ~np.isfinite(value)
        valid = ~(null | nonfinite)
        for key, expected in [('null', null), ('nonfinite', nonfinite), ('valid', valid)]:
            if not np.array_equal(_array(masks[key], 'bool', (n,)), expected):
                raise ValueError('STOP_MASK_VALUE_MISMATCH')
        combined &= valid
        diagnostics[name] = {'null_rows': int(null.sum()), 'nonfinite_rows': int(nonfinite.sum()),
                             'valid_rows': int(valid.sum())}
    if not np.array_equal(_array(decoded['row_valid'], 'bool', (n,)), combined):
        raise ValueError('STOP_ROW_VALID_MISMATCH')
    if not np.array_equal(_array(decoded['flag_bits'], 'u4', (n,)), decoded['values']['FLAG'].view(np.uint32)):
        raise ValueError('STOP_FLAG_BITS_MISMATCH')
    a = decoded['accounting']
    if (type(a) is not dict or set(a) != {'row_start', 'rows_decoded', 'buffer_bytes_supplied',
                                        'selected_field_bytes_decoded', 'unselected_bytes_present'}
            or any(type(v) is not int or v < 0 for v in a.values())
            or a['row_start'] + n > config['total_rows'] or a['rows_decoded'] != n
            or a['buffer_bytes_supplied'] != n * config['row_bytes']
            or a['selected_field_bytes_decoded'] != n * 28
            or a['unselected_bytes_present'] != n * (config['row_bytes'] - 28)):
        raise ValueError('STOP_DECODER_ACCOUNTING')
    return n, combined, diagnostics


def _validate_membership(membership, decoded, n, row_valid):
    if type(membership) is not dict or set(membership) != {'valid', 'circle20', 'annulus60_90'}:
        raise ValueError('STOP_MEMBERSHIP_SCHEMA')
    valid = _array(membership['valid'], 'bool', (n,))
    xy_valid = decoded['masks']['X']['valid'] & decoded['masks']['Y']['valid']
    if np.any(valid & ~xy_valid) or np.any(row_valid & ~valid):
        raise ValueError('STOP_GEOMETRY_VALIDITY')
    for key in ('circle20', 'annulus60_90'):
        masks = _array(membership[key], 'bool', (n, 5))
        if masks[~valid].any():
            raise ValueError('STOP_MASKED_MEMBERSHIP')
    if (membership['circle20'] & membership['annulus60_90']).any():
        raise ValueError('STOP_SAME_CENTRE_REGION_OVERLAP')


def checked_add_counts(total, increment):
    """Fresh int64 sum for histogram/region vectors, checking before arithmetic.

    Wrapper owns durable accumulation/order. Inputs are never modified; no
    implicit broadcasting, unsigned conversion or overflow wrapping is allowed.
    """
    if not isinstance(total, np.ndarray) or total.shape not in ((BINS, 5), (5,)):
        raise ValueError('STOP_COUNT_SHAPE')
    a = _array(total, 'i8', total.shape)
    b = _array(increment, 'i8', total.shape)
    if (a < 0).any() or (b < 0).any() or (a > np.iinfo(np.int64).max - b).any():
        raise ValueError('STOP_COUNT_OVERFLOW_OR_NEGATIVE')
    result = a + b
    result.flags.writeable = False
    return result


def count_chunk(decoded, membership, config, edges):
    """Return fixed integer increments; no rate, peak or significance products.

    Geometry may project XY-valid rows or just decoder-row-valid rows. Every
    row surviving missingness must have valid geometry under either convention.
    Membership arrays are local same-row masks; ordering/provenance is wrapper-
    owned and cannot be proved from boolean arrays alone.
    """
    _config(config, edges)
    n, row_valid, diagnostics = _validate_decoded(decoded, config)
    _validate_membership(membership, decoded, n, row_valid)
    values = decoded['values']
    failures = (~row_valid, ~np.isin(values['CCDNR'], config['ccds']),
                (values['TIME'] < config['tstart']) | (values['TIME'] > config['tstop']),
                ~((values['PI'] > 200) & (values['PI'] < 12000)),
                values['PATTERN'] > config['pattern_max'], values['FLAG'] != 0)
    remaining, rejected = np.ones(n, dtype=bool), {}
    for name, failed in zip(REJECTIONS, failures, strict=True):
        rejected[name] = int((remaining & failed).sum())
        remaining &= ~failed
    inside = remaining & (values['TIME'] >= edges[0]) & (values['TIME'] < edges[-1])
    accepted, inside_count = int(remaining.sum()), int(inside.sum())
    indices = np.searchsorted(edges, values['TIME'][inside], side='right') - 1
    histograms = {}
    for region in ('circle20', 'annulus60_90'):
        result = np.zeros((BINS, 5), dtype=np.int64)
        for column in range(5):
            np.add.at(result[:, column], indices[membership[region][inside, column]], 1)
        result.flags.writeable = False
        histograms[region] = result
    per_ccd = []
    for ccd in config['ccds']:
        camera_rows = remaining & (values['CCDNR'] == ccd)
        in_grid = inside & camera_rows
        item = {'ccd': ccd, 'accepted_rows': int(camera_rows.sum()),
                'accepted_inside_grid': int(in_grid.sum()), 'accepted_outside_grid': int((camera_rows & ~inside).sum())}
        for region in histograms:
            item[region] = membership[region][in_grid].sum(axis=0, dtype=np.int64)
            item[region].flags.writeable = False
        per_ccd.append(item)
    if (sum(rejected.values()) + accepted != n or sum(r['accepted_rows'] for r in per_ccd) != accepted
            or sum(r['accepted_inside_grid'] for r in per_ccd) != inside_count
            or any(not np.array_equal(sum((r[key] for r in per_ccd), np.zeros(5, dtype=np.int64)),
                                      histograms[key].sum(axis=0)) for key in histograms)):
        raise ValueError('STOP_COUNT_CLOSURE')
    return {'status': 'RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY', 'camera': config['camera'],
            'labels': list(LABELS), 'rows': n, 'rejected': rejected, 'field_diagnostics': diagnostics,
            'accepted_rows': accepted, 'accepted_inside_grid': inside_count,
            'accepted_outside_grid': accepted - inside_count, **histograms, 'per_ccd': per_ccd,
            'annuli_are_source_masked': False, 'gti_filter_applied': False,
            'exposure_or_significance_computed': False}
