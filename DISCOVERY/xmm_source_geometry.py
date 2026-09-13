"""Pure fixed-region catalogue contacts; no I/O, WCS, masks or area estimates.

The caller supplies original/corrected catalogue coordinates and five centres
already in the same declared frame. Nothing here fits/recentres/transforms them.
Public return values are aggregate diagnostics, never source IDs or positions.
"""

import numpy as np

FIELDS = ('SRC_NUM', 'RA', 'DEC', 'RADEC_ERR', 'EP_EXTENT', 'EP_EXT_ERR',
          'RA_CORR', 'DEC_CORR', 'SYSERRCC')
REGIONS = ('published', 'north120', 'east120', 'south120', 'west120')
RULES = {'association_arcsec': 5, 'aperture_centre_arcsec': 20,
         'aperture_disk_contact_arcsec': 50, 'annulus_disk_contact_min_arcsec': 30,
         'annulus_disk_contact_max_arcsec': 120, 'exclusion_radius_arcsec': 30,
         'comparison': 'inclusive literal computed float64; no added tolerance'}


def separation_arcsec(ra1, dec1, ra2, dec2):
    """Vincenty-style spherical atan2 distance; stable at wrap/poles/antipodes.

    Inputs must already be finite, domain-valid degree coordinates. This helper
    does not turn an invalid catalogue position into an apparent non-contact.
    """
    dlon = np.deg2rad(np.asarray(ra2) - np.asarray(ra1))
    lat1, lat2 = np.deg2rad(dec1), np.deg2rad(dec2)
    a = np.cos(lat2) * np.sin(dlon)
    b = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    dot = np.sin(lat1) * np.sin(lat2) + np.cos(lat1) * np.cos(lat2) * np.cos(dlon)
    return np.rad2deg(np.arctan2(np.hypot(a, b), dot)) * 3600


def position_valid(ra, dec):
    return np.isfinite(ra) & np.isfinite(dec) & (ra >= 0) & (ra < 360) & (dec >= -90) & (dec <= 90)


def nonnegative_summary(values):
    finite = np.isfinite(values)
    valid = finite & (values >= 0)
    return {'rows': len(values), 'nonfinite': int((~finite).sum()),
            'negative': int((finite & (values < 0)).sum()), 'zero': int((finite & (values == 0)).sum()),
            'positive': int((finite & (values > 0)).sum()),
            'valid_nonnegative_min': float(values[valid].min()) if valid.any() else None,
            'valid_nonnegative_max': float(values[valid].max()) if valid.any() else None}


def contact_masks(distance):
    """Fixed inclusive contacts, not positive area or a source-wing boundary."""
    return {'centre_within_20': distance <= 20, 'disk_contact_within_50': distance <= 50,
            'annulus_disk_contact_30_to_120': (distance >= 30) & (distance <= 120)}


def _numeric(value):
    if np.ma.isMaskedArray(value):
        raise ValueError('STOP_MASKED_INPUT')
    result = np.asarray(value)
    if result.dtype.kind not in 'ifu':
        raise ValueError('STOP_NUMERIC_INPUT')
    return result


def summarize(columns, centres):
    """Summarize <=151 rows and exactly five fixed (RA,Dec) centres.

    SRC_NUM must retain integer representation; invalid sign/range/duplicates
    are data-quality counts. Other arrays must be real numeric, equally sized
    1D vectors. No scalar-error/extent threshold changes positional association.
    Original-coordinate invalidity is separate from corrected association and
    makes the geometric screen incomplete. Input arrays are never modified.
    """
    if type(columns) is not dict or set(columns) != set(FIELDS):
        raise ValueError('STOP_COLUMN_SCHEMA')
    data = {name: _numeric(columns[name]) for name in FIELDS}
    ids = data['SRC_NUM']
    if ids.ndim != 1 or len(ids) > 151 or ids.dtype.kind != 'i':
        raise ValueError('STOP_ID_OR_ROW_SCHEMA')
    count = len(ids)
    if any(v.ndim != 1 or len(v) != count for v in data.values()):
        raise ValueError('STOP_ROW_SHAPE')
    centres = _numeric(centres)
    if centres.shape != (5, 2) or not position_valid(centres[:, 0], centres[:, 1]).all():
        raise ValueError('STOP_CENTRES')
    centres = centres.astype(np.float64)
    # Convert real fields only, never promote integer source identities to float.
    data = {name: value if name == 'SRC_NUM' else value.astype(np.float64)
            for name, value in data.items()}
    id_valid = (ids > 0) & (ids <= np.iinfo(np.int32).max)
    _, multiplicities = np.unique(ids[id_valid], return_counts=True)
    duplicates = multiplicities[multiplicities > 1]
    ids_complete = bool(id_valid.all() and len(duplicates) == 0)
    original = position_valid(data['RA'], data['DEC'])
    corrected = position_valid(data['RA_CORR'], data['DEC_CORR'])
    original_dist = np.full((count, 5), np.nan)
    original_dist[original] = separation_arcsec(data['RA'][original, None], data['DEC'][original, None],
                                               centres[None, :, 0], centres[None, :, 1])
    corrected_dist = np.full(count, np.nan)
    corrected_dist[corrected] = separation_arcsec(data['RA_CORR'][corrected], data['DEC_CORR'][corrected],
                                                 centres[0, 0], centres[0, 1])
    candidates = corrected & (corrected_dist <= 5)
    matches = int(candidates.sum())
    complete_association = ids_complete and bool(corrected.all())
    unique = complete_association and matches == 1
    association_status = ('INCOMPLETE_INPUT' if not complete_association else
                          'NO_MATCH' if matches == 0 else 'MULTIPLE_MATCHES' if matches > 1 else
                          'UNIQUE_POSITIONAL_ASSOCIATION')
    index = int(np.flatnonzero(candidates)[0]) if unique else None
    native_distance = (float(original_dist[index, 0]) if unique and original[index] else None)
    extent = data['EP_EXTENT']
    extent_classes = {'point_model_zero': np.isfinite(extent) & (extent == 0),
                      'extended_model_positive': np.isfinite(extent) & (extent > 0),
                      'invalid_or_unknown': ~np.isfinite(extent) | (extent < 0)}

    def contacts(mask):
        return {'rows': int(mask.sum()),
                'extent_categories': {name: int((mask & membership).sum())
                                      for name, membership in extent_classes.items()}}

    apertures, annuli = [], []
    for region_index, label in enumerate(REGIONS):
        masks = contact_masks(original_dist[:, region_index])
        included = original.copy()
        if unique and region_index == 0:
            included[index] = False
        apertures.append({'region': label, 'catalogue_rows': count,
                          'invalid_original_positions': int((~original).sum()),
                          'other_source_classification': ('UNRESOLVED_ASSOCIATION' if region_index == 0
                                                           and not unique else 'FIXED_CATALOGUE_ROWS'),
                          'control_row_exempted': bool(unique and region_index == 0),
                          'centre_within_20': contacts(masks['centre_within_20'] & included),
                          'disk_contact_within_50': contacts(masks['disk_contact_within_50'] & included)})
        annuli.append({'region': label, 'catalogue_rows': count,
                       'invalid_original_positions': int((~original).sum()),
                       'disk_contact_30_to_120': contacts(masks['annulus_disk_contact_30_to_120'] & original)})
    return {'status': 'SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY', 'rules': dict(RULES),
            'rows': count, 'identity': {'invalid_rows': int((~id_valid).sum()),
                                      'duplicate_valid_id_rows': int(duplicates.sum()),
                                      'duplicate_valid_id_extra_rows': int((duplicates - 1).sum()),
                                      'duplicate_valid_id_groups': len(duplicates)},
            'positions': {'valid_original': int(original.sum()), 'invalid_original': int((~original).sum()),
                          'valid_corrected': int(corrected.sum()), 'invalid_corrected': int((~corrected).sum())},
            'screen_completeness': ('COMPLETE_CATALOGUE_GEOMETRY_INPUT' if ids_complete and original.all()
                                    else 'INCOMPLETE_CATALOGUE_GEOMETRY_INPUT'),
            'association': {'status': association_status, 'valid_corrected_matches_within_5': matches,
                            'original_position_distance_arcsec': native_distance,
                            'original_position_within_20_arcsec': (native_distance <= 20
                                                                  if native_distance is not None else None)},
            'nonnegative_field_diagnostics': {name: nonnegative_summary(data[name])
                                             for name in ('RADEC_ERR', 'SYSERRCC', 'EP_EXTENT', 'EP_EXT_ERR')},
            'apertures': apertures, 'annuli': annuli,
            'limitations': ['Positional association is not physical identification or a confidence probability.',
                            'Error fields are separate diagnostics, not a fitted or adaptive matching radius.',
                            'Extent is a model scale, not a validated enclosing radius.',
                            'Inclusive disk contact does not prove positive area or contaminating flux.',
                            'No mask union, supported area, clean-sky verdict or recovery gate is computed.']}
