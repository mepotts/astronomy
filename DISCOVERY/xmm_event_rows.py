"""Packed scalar EVENTS decoding only; no I/O, WCS, selection or counting.

Callers own product/header provenance and read/deadline budgets. Full row buffers
contain unselected bytes physically; only the nine selected fields are decoded.
Returned values/masks are local working arrays, not safe public JSON artifacts.
"""

import re
from dataclasses import dataclass

import numpy as np

SELECTED = {'TIME': 'D', 'RAWX': 'I', 'RAWY': 'I', 'X': 'J', 'Y': 'J',
            'PI': 'I', 'FLAG': 'J', 'PATTERN': 'B', 'CCDNR': 'B'}
WIDTHS = {'A': 1, 'L': 1, 'B': 1, 'I': 2, 'J': 4, 'K': 8,
          'E': 4, 'D': 8, 'C': 8, 'M': 16}
DTYPES = {'B': 'u1', 'I': '>i2', 'J': '>i4', 'K': '>i8', 'E': '>f4', 'D': '>f8'}
MAX_CHUNK_ROWS = 10000
SCHEMA_KEY = re.compile(r'(?:XTENSION|EXTNAME|BITPIX|NAXIS[12]?|PCOUNT|GCOUNT|TFIELDS|THEAP|'
                        r'T(?:TYPE|FORM|UNIT|NULL|SCAL|ZERO|DIM)\d+)\Z')


def integer(value, minimum=0):
    """Metadata integers, never bool, floating approximations or numeric strings."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError('STOP_INTEGER_METADATA')
    return int(value)


@dataclass(frozen=True)
class Column:
    name: str
    form: str
    offset: int
    unit: str | None
    null: int | None


@dataclass(frozen=True)
class EventSchema:
    """Only instances returned by build_schema are supported by decode_rows.

    Direct construction/replacement is unsupported; decode_rows additionally
    reconstructs the schema to reject forged offsets, formats or row widths.
    """

    rows: int
    row_bytes: int
    data_offset: int
    columns: tuple[Column, ...]

    def metadata(self):
        """Schema only; excludes every coordinate/reference/header-history value."""
        return {'rows': self.rows, 'row_bytes': self.row_bytes, 'data_offset': self.data_offset,
                'payload_bytes': self.rows * self.row_bytes, 'selected_bytes_per_row': 28,
                'columns': [{'name': c.name, 'form': c.form, 'offset': c.offset,
                             'unit': c.unit, 'null': c.null} for c in self.columns]}


def build_schema(header_items, data_offset):
    """Use (keyword,value) pairs so duplicate schema cards cannot disappear.

    Only scalar repeat-omitted or repeat-1 FITS forms are supported. Unselected
    A/L/C/M fields contribute widths but are not interpreted. Scaling, dimensions,
    heaps and variable-length/bit/vector columns are outside this narrow schema.
    Header framing/checksum/provenance belongs to the verified structural reader.
    """
    offset = integer(data_offset)
    if offset % 2880:
        raise ValueError('STOP_DATA_OFFSET')
    if not isinstance(header_items, (list, tuple)):
        raise TypeError('STOP_HEADER_PAIRS')
    header = {}
    for pair in header_items:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2 or not isinstance(pair[0], str):
            raise ValueError('STOP_HEADER_PAIRS')
        key, value = pair
        if SCHEMA_KEY.fullmatch(key):
            if key in header:
                raise ValueError('STOP_DUPLICATE_SCHEMA_CARD')
            header[key] = value
    required = {'XTENSION': 'BINTABLE', 'EXTNAME': 'EVENTS', 'BITPIX': 8,
                'NAXIS': 2, 'PCOUNT': 0, 'GCOUNT': 1}
    for key, expected in required.items():
        actual = header.get(key)
        if isinstance(expected, int):
            actual = integer(actual)
        if actual != expected:
            raise ValueError('STOP_TABLE_LAYOUT')
    rows = integer(header.get('NAXIS2'))
    row_bytes = integer(header.get('NAXIS1'), 1)
    fields = integer(header.get('TFIELDS'), 1)
    if fields > 64 or row_bytes > 1024:
        raise ValueError('STOP_SCHEMA_CAP')
    if 'THEAP' in header or any(k.startswith(('TSCAL', 'TZERO', 'TDIM')) for k in header):
        raise ValueError('STOP_SCALING_DIMENSION_HEAP')
    for key in header:
        match = re.fullmatch(r'T(?:TYPE|FORM|UNIT|NULL)(\d+)', key)
        if match and not 1 <= int(match[1]) <= fields:
            raise ValueError('STOP_COLUMN_INDEX')
    columns, names, position = [], set(), 0
    for i in range(1, fields + 1):
        name, form = header.get(f'TTYPE{i}'), header.get(f'TFORM{i}')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,31}', name) or name in names:
            raise ValueError('STOP_COLUMN_NAME')
        if not isinstance(form, str) or not re.fullmatch(r'1?[ALBIJKEDCM]', form):
            raise ValueError('STOP_SCALAR_TFORM')
        form = form[-1]
        unit = header.get(f'TUNIT{i}')
        if unit is not None and (not isinstance(unit, str) or len(unit) > 64
                                 or any(ord(ch) < 32 or ord(ch) > 126 for ch in unit)):
            raise ValueError('STOP_COLUMN_UNIT')
        null = header.get(f'TNULL{i}')
        if f'TNULL{i}' in header:
            if (form not in ('B', 'I', 'J', 'K') or isinstance(null, (bool, np.bool_))
                    or not isinstance(null, (int, np.integer))):
                raise ValueError('STOP_NULL_SCHEMA')
            limits = np.iinfo(DTYPES[form])
            if not limits.min <= null <= limits.max:
                raise ValueError('STOP_NULL_RANGE')
            null = int(null)
        if name in SELECTED and form != SELECTED[name]:
            raise ValueError('STOP_SELECTED_FORMAT')
        columns.append(Column(name, form, position, unit, null))
        names.add(name)
        position += WIDTHS[form]
    if position != row_bytes or not set(SELECTED) <= names:
        raise ValueError('STOP_ROW_LAYOUT')
    return EventSchema(rows, row_bytes, offset, tuple(columns))


def decode_rows(raw_bytes, schema, *, row_start=0, accounting=None):
    """Decode one complete-row chunk with separate null/nonfinite masks.

    Values are copied into native-endian, read-only arrays. Null sentinels and
    NaN/inf remain in values; callers MUST use masks before any geometry/cuts.
    Row validity here means only all selected values non-null and finite, not
    calibrated validity, valid CCD/window, GTI membership or accepted energy.
    schema MUST be the unchanged result of build_schema, not a hand-constructed
    or dataclasses.replace-modified instance. Optional accounting is a caller-
    owned EMPTY dict updated in place. Completed field conversions are recorded
    before mask work; a failed current conversion is explicitly unknown, never
    counted as completed or zero work. No absolute values enter that dict.
    Exceptions still require caller accounting of bytes actually returned by
    I/O, including a truncated row or killed pass. Hard process termination may
    prevent persistence of this in-memory progress; this is not a durable log.
    """
    if accounting is not None and (type(accounting) is not dict or accounting):
        raise ValueError('STOP_ACCOUNTING_ARGUMENT')
    progress = {} if accounting is None else accounting
    progress.update({'status': 'IN_PROGRESS', 'phase': 'VALIDATING', 'current_field': None,
                     'buffer_bytes_supplied': len(raw_bytes) if isinstance(raw_bytes, bytes) else None,
                     'selected_field_bytes_decoded': 0, 'completed_fields': [],
                     'rows_completed': 0, 'current_conversion_completion_unknown': False})
    try:
        result = _decode_rows(raw_bytes, schema, row_start, progress)
    except Exception:
        progress['status'] = 'FAILED'
        progress['current_conversion_completion_unknown'] = progress['phase'] == 'CONVERTING'
        raise
    progress.update(status='COMPLETE', phase='COMPLETE', current_field=None,
                    rows_completed=result['accounting']['rows_decoded'])
    return result


def _native_copy(field):
    return field.astype(field.dtype.newbyteorder('='), copy=True)


def _validate_schema(schema):
    """Small defensive reconstruction; never deserialize offsets on trust."""
    if (type(schema.columns) is not tuple or any(type(c) is not Column or type(c.offset) is not int
                                               for c in schema.columns)):
        raise ValueError('STOP_UNVALIDATED_SCHEMA')
    items = [('XTENSION', 'BINTABLE'), ('EXTNAME', 'EVENTS'), ('BITPIX', 8), ('NAXIS', 2),
             ('NAXIS1', schema.row_bytes), ('NAXIS2', schema.rows), ('PCOUNT', 0), ('GCOUNT', 1),
             ('TFIELDS', len(schema.columns))]
    for i, column in enumerate(schema.columns, 1):
        items += [(f'TTYPE{i}', column.name), (f'TFORM{i}', column.form)]
        if column.unit is not None:
            items.append((f'TUNIT{i}', column.unit))
        if column.null is not None:
            items.append((f'TNULL{i}', column.null))
    if build_schema(items, schema.data_offset) != schema:
        raise ValueError('STOP_UNVALIDATED_SCHEMA')


def _decode_rows(raw_bytes, schema, row_start, progress):
    if not isinstance(raw_bytes, bytes) or not isinstance(schema, EventSchema):
        raise TypeError('STOP_BUFFER_OR_SCHEMA')
    _validate_schema(schema)
    start = integer(row_start)
    if schema.row_bytes <= 0 or len(raw_bytes) % schema.row_bytes:
        raise ValueError('STOP_PARTIAL_ROW')
    count = len(raw_bytes) // schema.row_bytes
    if count > MAX_CHUNK_ROWS or start > schema.rows or start + count > schema.rows:
        raise ValueError('STOP_ROW_BOUND')
    lookup = {c.name: c for c in schema.columns}
    dtype = np.dtype({'names': list(SELECTED),
                      'formats': [DTYPES[lookup[n].form] for n in SELECTED],
                      'offsets': [lookup[n].offset for n in SELECTED], 'itemsize': schema.row_bytes})
    packed = np.frombuffer(raw_bytes, dtype=dtype, count=count)
    values, masks = {}, {}
    row_valid = np.ones(count, dtype=bool)
    for name in SELECTED:
        progress.update(phase='CONVERTING', current_field=name)
        values[name] = _native_copy(packed[name])
        progress['selected_field_bytes_decoded'] += count * WIDTHS[lookup[name].form]
        progress['completed_fields'].append(name)
        progress['phase'] = 'MASKING'
        null = lookup[name].null
        null_mask = values[name] == null if null is not None else np.zeros(count, dtype=bool)
        nonfinite = ~np.isfinite(values[name])
        valid = ~(null_mask | nonfinite)
        masks[name] = {'null': null_mask, 'nonfinite': nonfinite, 'valid': valid}
        row_valid &= valid
        values[name].flags.writeable = False
        for mask in masks[name].values():
            mask.flags.writeable = False
    progress.update(phase='FINALIZING', current_field=None)
    flag_bits = values['FLAG'].view(np.uint32)
    flag_bits.flags.writeable = False
    row_valid.flags.writeable = False
    return {'values': values, 'masks': masks, 'row_valid': row_valid, 'flag_bits': flag_bits,
            'accounting': {'row_start': start, 'rows_decoded': count,
                           'buffer_bytes_supplied': len(raw_bytes),
                           'selected_field_bytes_decoded': count * 28,
                           'unselected_bytes_present': count * (schema.row_bytes - 28)}}
