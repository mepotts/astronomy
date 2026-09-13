"""Pure sampled-attitude diagnostics; never return absolute pointing values."""

import numpy as np

COLUMNS = ('TIME', 'AHFRA', 'AHFDEC', 'AHFPA', 'OMRA', 'OMDEC', 'OMPA', 'DAHFPNT', 'DOMPNT', 'DAHFOM')


def separation_arcsec(ra1, dec1, ra2, dec2):
    """Great-circle distance, stable near coincident points and longitude wrap."""
    ra1, dec1, ra2, dec2 = map(np.deg2rad, (ra1, dec1, ra2, dec2))
    a = np.sin((dec2 - dec1) / 2)**2 + np.cos(dec1) * np.cos(dec2) * np.sin((ra2 - ra1) / 2)**2
    return np.rad2deg(2 * np.arctan2(np.sqrt(np.clip(a, 0, 1)), np.sqrt(np.clip(1 - a, 0, 1)))) * 3600


def extrema(values):
    values = values[np.isfinite(values)]
    return {'min': float(values.min()), 'max': float(values.max())} if len(values) else {'min': None, 'max': None}


def summarize(data, camera_ranges, header_counts):
    """Describe all rows, retaining quality failures rather than dropping them.

    Mission-time convention and coordinate sanity domains are supplied by the
    prospective protocol. Finite/domain-valid samples are not certified good
    attitude. Sampled motion never bounds continuous motion between samples.
    """
    if (not isinstance(header_counts, dict) or set(header_counts) != {'NATT', 'NGAHF', 'NGOM', 'NGAHFOM'}
            or any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) or v < 0
                   for v in header_counts.values())):
        raise ValueError('STOP_HEADER_COUNTER_SCHEMA')
    if not isinstance(camera_ranges, (list, tuple)):
        raise TypeError('STOP_CAMERA_TIME_SCHEMA')
    for camera in camera_ranges:
        if (not isinstance(camera, dict) or set(camera) != {'camera', 'start', 'stop'}
                or camera['camera'] not in ('EPN', 'EMOS1', 'EMOS2')
                or any(isinstance(camera[k], (bool, np.bool_))
                       or not isinstance(camera[k], (int, float, np.integer, np.floating)) for k in ('start', 'stop'))):
            raise ValueError('STOP_CAMERA_TIME_SCHEMA')
    if np.ma.isMaskedArray(data):
        raise ValueError('STOP_MASKED_ARRAY_SCHEMA')
    data = np.asarray(data)
    if data.ndim != 2 or data.shape[1] != 10 or data.dtype.kind != 'f' or len(data) == 0:
        raise ValueError('STOP_ARRAY_SCHEMA')
    finite = np.isfinite(data)
    time = data[:, 0]
    with np.errstate(over='ignore', invalid='ignore'):
        dt = np.diff(time)
    finite_pairs = finite[1:, 0] & finite[:-1, 0] & np.isfinite(dt)
    good_step = finite_pairs & (dt > 0) & (np.abs(dt - 1) <= 1e-6)
    timing_ok = bool(finite[:, 0].all() and finite_pairs.all() and np.all(dt > 0))
    result = {
        'status': 'SAMPLED_ATTITUDE_DIAGNOSTICS_NOT_COVERAGE', 'rows': len(data),
        'column_counts': {name: {'finite': int(finite[:, i].sum()), 'nan': int(np.isnan(data[:, i]).sum()),
                                'infinite': int(np.isinf(data[:, i]).sum())} for i, name in enumerate(COLUMNS)},
        'time': {'range': extrema(time), 'finite_strictly_increasing': timing_ok,
                 'finite_adjacent_pairs': int(finite_pairs.sum()),
                 'nonpositive_adjacent_steps': int((finite_pairs & (dt <= 0)).sum()),
                 'nonunit_positive_steps': int((finite_pairs & (dt > 0) & ~good_step).sum()),
                 'adjacent_step_seconds': extrema(dt[finite_pairs]),
                 'mission_convention': 'TT seconds since MJD50814 assumed prospectively, no fitted offset',
                 'file_time_reference_keywords_absent': True},
        'header_counts': {key: int(value) for key, value in header_counts.items()}, 'sources': {},
        'continuous_motion_bound_established': False, 'clock_reference_verified': False,
    }
    masks = {}
    for source, start in (('AHF', 1), ('OM', 4)):
        triple = data[:, start:start + 3]
        nfinite = finite[:, start:start + 3].sum(axis=1)
        domains = ((triple[:, 0] >= 0) & (triple[:, 0] <= 360) & (triple[:, 1] >= -90)
                   & (triple[:, 1] <= 90) & (triple[:, 2] >= 0) & (triple[:, 2] <= 360))
        valid = (nfinite == 3) & domains
        masks[source] = valid
        eligible = valid & finite[:, 0]
        indices = np.flatnonzero(eligible)
        pairs = eligible[1:] & eligible[:-1] & good_step
        rows = np.flatnonzero(pairs) + 1
        offsets = np.empty(0)
        steps = np.empty(0)
        roll = np.empty(0)
        if len(indices):
            first = indices[0]
            offsets = separation_arcsec(triple[first, 0], triple[first, 1], triple[indices, 0], triple[indices, 1])
        if len(rows):
            steps = separation_arcsec(triple[rows - 1, 0], triple[rows - 1, 1], triple[rows, 0], triple[rows, 1])
            roll = np.abs((triple[rows, 2] - triple[rows - 1, 2] + 180) % 360 - 180) * 3600
        result['sources'][source] = {
            'all_finite_triplets': int((nfinite == 3).sum()), 'all_nan_triplets': int(np.isnan(triple).all(axis=1).sum()),
            'partial_finite_triplets': int(((nfinite > 0) & (nfinite < 3)).sum()),
            'finite_domain_failures': int(((nfinite == 3) & ~domains).sum()),
            'finite_domain_valid_triplets': int(valid.sum()), 'time_eligible_rows': len(indices),
            'first_reference_row': int(indices[0]) if len(indices) else None,
            'separation_from_first_arcsec': extrema(offsets),
            'contiguous_one_second_motion_pairs': len(rows),
            'unmeasured_adjacent_pairs': len(data) - 1 - len(rows),
            'adjacent_separation_arcsec': extrema(steps), 'adjacent_roll_absolute_arcsec': extrema(roll),
        }
    result['joint_finite_domain_valid_triplets'] = int((masks['AHF'] & masks['OM']).sum())
    result['header_vs_measured_finite_counts'] = {
        'NATT_matches_rows': header_counts.get('NATT') == len(data),
        'NGAHF_matches_finite_AHF': header_counts.get('NGAHF') == result['sources']['AHF']['all_finite_triplets'],
        'NGOM_matches_finite_OM': header_counts.get('NGOM') == result['sources']['OM']['all_finite_triplets'],
        'NGAHFOM_matches_joint_finite': header_counts.get('NGAHFOM') == int(
            (finite[:, 1:4].all(axis=1) & finite[:, 4:7].all(axis=1)).sum()),
    }
    result['offset_columns'] = {name: {'finite_degrees': extrema(data[:, i]),
                                      'domain_valid_arcsec': extrema(data[finite[:, i] & (data[:, i] >= 0) & (data[:, i] <= 180), i] * 3600),
                                      'finite_outside_0_180_degrees': int((finite[:, i] & ((data[:, i] < 0) | (data[:, i] > 180))).sum())}
                                for i, name in enumerate(COLUMNS) if i >= 7}
    result['camera_time_range_diagnostics'] = []
    for camera in camera_ranges:
        start, stop = camera['start'], camera['stop']
        if not np.isfinite(start) or not np.isfinite(stop) or start >= stop:
            raise ValueError('STOP_CAMERA_TIME_RANGE')
        result['camera_time_range_diagnostics'].append({'camera': camera['camera'], 'start': float(start), 'stop': float(stop),
            'strictly_ordered_attitude_brackets_header_range': bool(timing_ok and time[0] <= start and time[-1] >= stop),
            'finite_samples_within_half_open_header_range': int((finite[:, 0] & (time >= start) & (time < stop)).sum()),
            'interpretation': 'range diagnostic only, not a GTI or time-reference proof'})
    return result
