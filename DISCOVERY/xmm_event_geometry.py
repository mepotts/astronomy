"""Pure selected X/Y TAN geometry. No I/O, frame fit, exclusions or coverage.

Caller validates the full EVENTS schema/provenance and supplies five fixed
centres already in FK5/J2000. Local membership arrays are not public receipts.
"""

import re
import warnings
from dataclasses import dataclass

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

SCALE = 1.38888888888889e-05
NULL = -99999999
MAX_ROWS = 10000
LABELS = ('published', 'north120', 'east120', 'south120', 'west120')
AXIS_KEYS = ('TCRPX6', 'TCRPX7', 'TCRVL6', 'TCRVL7')
FIXED = {'XTENSION': 'BINTABLE', 'EXTNAME': 'EVENTS', 'TTYPE6': 'X', 'TTYPE7': 'Y',
         'TNULL6': NULL, 'TNULL7': NULL, 'TCTYP6': 'RA---TAN', 'TCTYP7': 'DEC--TAN',
         'TCUNI6': 'deg', 'TCUNI7': 'deg', 'TCDLT6': -SCALE, 'TCDLT7': SCALE, 'EQUINOX': 2000.}
# All matrix/parameter/rotation versions are outside this diagonal TAN profile.
FORBIDDEN = re.compile(r'(?:T(?:PC|CD|P|C|PV|V|PS|S)\d+_\d+[A-Z]?|TCROT\d+[A-Z]?|'
                       r'(?:WCST|WCSX|LONP|LATP|RADE|EQUI)\d+[A-Z]?|'
                       r'(?:CTYPE|CUNIT|CRPIX|CRVAL|CDELT|CROTA|CNAME|CRDER|CSYER)\d+[A-Z]?|'
                       r'(?:PC|CD|PV|PS)\d+_\d+[A-Z]?|WCSAXES[A-Z]?|'
                       r'(?:LONPOLE|LATPOLE|RADESYS|RADECSYS|EQUINOX)[A-Z]|EPOCH|'
                       r'(?:CPDIS|CQDIS|DP|DQ)\d.*|(?:D2IM|DET2IM).*|(?:A|B|AP|BP)_(?:ORDER|\d+_\d+)|'
                       r'(?:LONPOLE|LATPOLE))\Z')
TABLE_SCALAR = re.compile(r'TC(?:TYP|UNI|RVL|DLT|RPX)[1-9]\d*\Z')
TABLE_INFORMATION = re.compile(r'T(?:CNA|CRD|CSY)[1-9]\d*[A-Z]?\Z')


@dataclass(frozen=True, repr=False)
class Geometry:
    """Private definition, never serialize these absolute reference values."""

    reference: tuple[float, float, float, float]

    def metadata(self):
        return {'columns': [6, 7], 'names': ['X', 'Y'], 'origin': 1, 'projection': 'TAN',
                'frame': 'FK5', 'equinox': 2000, 'max_rows': MAX_ROWS,
                'regions': list(LABELS), 'membership_is_coverage': False}


def _number(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise TypeError('STOP_NUMERIC_METADATA')
    value = float(value)
    if not np.isfinite(value):
        raise ValueError('STOP_NONFINITE_METADATA')
    return value


def build_geometry(header_pairs):
    """Validate primary selected table-axis WCS before creating a minimal WCS.

    Full row schema, camera identity and header provenance remain caller-owned.
    Unselected scalar DET metadata is allowed but never copied to sky axes.
    """
    if not isinstance(header_pairs, (list, tuple)):
        raise TypeError('STOP_HEADER_PAIRS')
    header = {}
    relevant = set(FIXED) | set(AXIS_KEYS) | {'TFORM6', 'TFORM7', 'TUNIT6', 'TUNIT7', 'RADECSYS', 'RADESYS'}
    for pair in header_pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2 or not isinstance(pair[0], str):
            raise ValueError('STOP_HEADER_PAIRS')
        key, value = pair
        if (FORBIDDEN.fullmatch(key) or re.fullmatch(r'T(?:SCAL|ZERO|DIM)[67]', key)
                or ((key.startswith(('TC', 'TP', 'TV', 'TWCS', 'WCS')) or re.match(r'TS\d', key))
                    and not TABLE_SCALAR.fullmatch(key) and not TABLE_INFORMATION.fullmatch(key)
                    and not re.fullmatch(r'T(?:TYPE|FORM|UNIT|NULL|SCAL|ZERO|DIM)\d+', key))):
            raise ValueError('STOP_UNSUPPORTED_WCS')
        if key in relevant:
            if key in header:
                raise ValueError('STOP_DUPLICATE_WCS')
            header[key] = value
    for key, expected in FIXED.items():
        actual = header.get(key)
        if isinstance(expected, (int, float)):
            actual = _number(actual)
        if actual != expected:
            raise ValueError('STOP_SELECTED_WCS')
    for axis in (6, 7):
        if header.get(f'TFORM{axis}') not in ('J', '1J') or header.get(f'TUNIT{axis}') not in ('pixel', '0.05 arcsec'):
            raise ValueError('STOP_SELECTED_COLUMN')
        if type(header[f'TNULL{axis}']) is not int:
            raise ValueError('STOP_NULL_METADATA')
    frames = [header[k] for k in ('RADECSYS', 'RADESYS') if k in header]
    if not frames or any(frame != 'FK5' for frame in frames):
        raise ValueError('STOP_FRAME')
    geometry = Geometry(tuple(_number(header.get(k)) for k in AXIS_KEYS))
    _validate(geometry)
    _make_wcs(geometry)
    return geometry


def _validate(geometry):
    if (type(geometry) is not Geometry or type(geometry.reference) is not tuple
            or len(geometry.reference) != 4 or any(type(v) is not float or not np.isfinite(v) for v in geometry.reference)):
        raise ValueError('STOP_GEOMETRY_DEFINITION')
    if not 0 <= geometry.reference[2] < 360 or not -90 < geometry.reference[3] < 90:
        raise ValueError('STOP_REFERENCE_DOMAIN')


def _make_wcs(geometry):
    _validate(geometry)
    px, py, ra, dec = geometry.reference
    header = fits.Header({'WCSAXES': 2, 'CTYPE1': 'RA---TAN', 'CTYPE2': 'DEC--TAN',
                          'CUNIT1': 'deg', 'CUNIT2': 'deg', 'CRPIX1': px, 'CRPIX2': py,
                          'CRVAL1': ra, 'CRVAL2': dec, 'CDELT1': -SCALE, 'CDELT2': SCALE,
                          'RADESYS': 'FK5', 'EQUINOX': 2000.})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        wcs = WCS(header, fix=False, relax=False)
    if caught or wcs.pixel_n_dim != 2 or wcs.world_n_dim != 2 or not wcs.is_celestial or wcs.has_distortion:
        raise ValueError('STOP_WCS_CONSTRUCTION')
    return wcs


def _project(wcs, xy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = wcs.wcs_pix2world(xy, 1)
    if caught:
        raise ValueError('STOP_WCS_WARNING')
    return result


def _distance(sky, centres):
    a, d = np.deg2rad(sky[:, 0, None]), np.deg2rad(sky[:, 1, None])
    ca, cd = np.deg2rad(centres[None, :, 0]), np.deg2rad(centres[None, :, 1])
    dl = ca - a
    u = np.cos(cd) * np.sin(dl)
    v = np.cos(d) * np.sin(cd) - np.sin(d) * np.cos(cd) * np.cos(dl)
    dot = np.sin(d) * np.sin(cd) + np.cos(d) * np.cos(cd) * np.cos(dl)
    return np.rad2deg(np.arctan2(np.hypot(u, v), dot)) * 3600


def _regions(distance):
    # Literal inclusive comparisons, no tolerance or data-driven boundary shift.
    return distance <= 20, (distance >= 60) & (distance <= 90)


def classify_xy(x, y, xy_valid, geometry, centres_fk5, *, accounting):
    """Return same-row local masks, not exposure, exclusion masks or counts.

    A fresh empty caller accounting dict survives caught exceptions. Projection
    completion is unknown if its call raises; no retry is authorized. Centre
    frame/convention/identity and immutable source lineage belong to caller.
    projection_completed_rows counts rows in a returned projection call, before
    output validation; rows_completed requires successful complete membership.
    """
    if type(accounting) is not dict or accounting:
        raise ValueError('STOP_ACCOUNTING_ARGUMENT')
    accounting.update(status='IN_PROGRESS', phase='VALIDATING', input_rows=None, masked_rows=None,
                      projection_attempted_rows=0, projection_completed_rows=0, rows_completed=0,
                      current_projection_completion_unknown=False)
    try:
        _validate(geometry)
        if any(np.ma.isMaskedArray(v) for v in (x, y, xy_valid, centres_fk5)):
            raise ValueError('STOP_MASKED_ARRAY')
        x, y, valid, centres = (np.asarray(v) for v in (x, y, xy_valid, centres_fk5))
        if (x.ndim != 1 or y.shape != x.shape or valid.shape != x.shape or len(x) > MAX_ROWS
                or x.dtype.kind != 'i' or y.dtype.kind != 'i' or valid.dtype.kind != 'b'):
            raise ValueError('STOP_INPUT_SCHEMA')
        if any(np.any((v < -(2**31)) | (v > 2**31 - 1)) for v in (x, y)):
            raise ValueError('STOP_INT32_DOMAIN')
        if (centres.shape != (5, 2) or centres.dtype.kind not in 'ifu' or not np.isfinite(centres).all()
                or not ((centres[:, 0] >= 0) & (centres[:, 0] < 360)
                        & (centres[:, 1] >= -90) & (centres[:, 1] <= 90)).all()):
            raise ValueError('STOP_CENTRES')
        centres = centres.astype(np.float64)
        valid = valid & (x != NULL) & (y != NULL)
        accounting.update(input_rows=len(x), masked_rows=int((~valid).sum()), phase='CONSTRUCTING')
        wcs = _make_wcs(geometry)
        circle, annulus = np.zeros((len(x), 5), bool), np.zeros((len(x), 5), bool)
        if valid.any():
            xy = np.column_stack((x[valid], y[valid])).astype(np.float64)
            accounting.update(phase='PROJECTING', projection_attempted_rows=len(xy))
            sky = _project(wcs, xy)
            accounting.update(phase='PROJECTED', projection_completed_rows=len(xy))
            if (not isinstance(sky, np.ndarray) or sky.shape != (len(xy), 2) or not np.isfinite(sky).all()
                    or not ((sky[:, 0] >= 0) & (sky[:, 0] < 360) & (sky[:, 1] >= -90) & (sky[:, 1] <= 90)).all()):
                raise ValueError('STOP_PROJECTED_COORDINATES')
            accounting['phase'] = 'CLASSIFYING'
            distance = _distance(sky, centres)
            if not np.isfinite(distance).all():
                raise ValueError('STOP_DISTANCE')
            selected_circle, selected_annulus = _regions(distance)
            accounting['phase'] = 'STORING'
            circle[valid], annulus[valid] = selected_circle, selected_annulus
        accounting['phase'] = 'FINALIZING'
        result = {'valid': valid, 'circle20': circle, 'annulus60_90': annulus}
        for value in result.values():
            value.flags.writeable = False
        accounting.update(status='COMPLETE', phase='COMPLETE', rows_completed=len(x))
        return result
    except Exception:
        accounting['status'] = 'FAILED'
        accounting['current_projection_completion_unknown'] = accounting['phase'] == 'PROJECTING'
        raise
