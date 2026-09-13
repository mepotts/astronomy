"""Exact nine-column SRCLIST span reader; no geometry, provenance or policy.

Only a caller-supplied unbuffered stream is read. Returned column tuples contain
private local working values, not safe public artifacts. The caller owns file
identity, declared source/correction frames, deadlines and durable receipts.
"""

import io
import re
import struct
from dataclasses import dataclass

ROWS, ROW_BYTES, DATA_OFFSET = 151, 1131, 77760
FIELD_COUNT, SELECTED_BYTES, READ_COUNT = 266, 7852, 755
WIDTHS = {'A': 1, 'L': 1, 'B': 1, 'I': 2, 'J': 4, 'K': 8, 'E': 4, 'D': 8, 'C': 8, 'M': 16}
SELECTED = (
    (1, 'SRC_NUM', 'J', None, 0),
    (6, 'RA', 'D', 'deg', 20), (7, 'DEC', 'D', 'deg', 28), (8, 'RADEC_ERR', 'E', 'arcsec', 36),
    (146, 'EP_EXTENT', 'E', 'image pixels', 596), (147, 'EP_EXT_ERR', 'E', 'image pixels', 600),
    (261, 'RA_CORR', 'D', 'deg', 1088), (262, 'DEC_CORR', 'D', 'deg', 1096),
    (265, 'SYSERRCC', 'E', 'arcsec', 1120))
SPANS = ((0, 4, '>i', ('SRC_NUM',)), (20, 20, '>ddf', ('RA', 'DEC', 'RADEC_ERR')),
         (596, 8, '>ff', ('EP_EXTENT', 'EP_EXT_ERR')), (1088, 16, '>dd', ('RA_CORR', 'DEC_CORR')),
         (1120, 4, '>f', ('SYSERRCC',)))
SCHEMA_KEY = re.compile(r'(?:XTENSION|EXTNAME|BITPIX|NAXIS\d*|PCOUNT|GCOUNT|TFIELDS|THEAP|'
                        r'T(?:TYPE|FORM|UNIT|NULL|SCAL|ZERO|DIM)\d+)\Z')
FORM = re.compile(r'([1-9][0-9]*)?([ALBIJKEDCM])\Z')


@dataclass(frozen=True)
class Column:
    name: str
    form: str
    unit: str | None
    null: int | None
    offset: int
    width: int


@dataclass(frozen=True)
class SourceSchema:
    """Use only unchanged build_schema results; the reader revalidates them."""

    columns: tuple[Column, ...]
    rows: int = ROWS
    row_bytes: int = ROW_BYTES
    data_offset: int = DATA_OFFSET

    def metadata(self):
        return {'rows': self.rows, 'row_bytes': self.row_bytes, 'data_offset': self.data_offset,
                'table_payload_bytes': self.rows * self.row_bytes, 'selected_bytes_per_pass': SELECTED_BYTES,
                'reads_per_pass': READ_COUNT,
                'columns': [{'name': c.name, 'form': c.form, 'unit': c.unit, 'null': c.null,
                             'offset': c.offset, 'width': c.width} for c in self.columns]}


def _integer(value):
    if type(value) is not int:
        raise ValueError('STOP_INTEGER_METADATA')
    return value


def build_schema(header_items, data_offset):
    """Derive all 266 fixed widths, then require the exact nine selected spans.

    Header framing and PRIMARY identity belong to the caller. Repeated A/L and
    other fixed-width fields contribute byte widths only; unselected contents
    are never decoded. Variable-length, bit-array, heap/scaling/dimension
    variants are unsupported rather than approximated.
    """
    if _integer(data_offset) != DATA_OFFSET or not isinstance(header_items, (list, tuple)):
        raise ValueError('STOP_SOURCE_LAYOUT')
    header = {}
    for pair in header_items:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2 or not isinstance(pair[0], str):
            raise ValueError('STOP_HEADER_PAIRS')
        key, value = pair
        if SCHEMA_KEY.fullmatch(key):
            if key in header:
                raise ValueError('STOP_DUPLICATE_SCHEMA_CARD')
            header[key] = value
    exact = {'XTENSION': 'BINTABLE', 'EXTNAME': 'SRCLIST', 'BITPIX': 8, 'NAXIS': 2,
             'NAXIS1': ROW_BYTES, 'NAXIS2': ROWS, 'PCOUNT': 0, 'GCOUNT': 1, 'TFIELDS': FIELD_COUNT}
    for key, value in exact.items():
        actual = header.get(key)
        if type(value) is int:
            actual = _integer(actual)
        if actual != value:
            raise ValueError('STOP_SOURCE_LAYOUT')
    if ('THEAP' in header or any(k.startswith(('TSCAL', 'TZERO', 'TDIM')) for k in header)
            or any(k.startswith('NAXIS') and k not in ('NAXIS', 'NAXIS1', 'NAXIS2') for k in header)):
        raise ValueError('STOP_SCALING_DIMENSION_HEAP')
    for key in header:
        match = re.fullmatch(r'T(?:TYPE|FORM|UNIT|NULL)(\d+)', key)
        if match and (str(int(match[1])) != match[1] or not 1 <= int(match[1]) <= FIELD_COUNT):
            raise ValueError('STOP_COLUMN_INDEX')
    position, columns, names = 0, [], set()
    for i in range(1, FIELD_COUNT + 1):
        name, form = header.get(f'TTYPE{i}'), header.get(f'TFORM{i}')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,31}', name) or name in names:
            raise ValueError('STOP_COLUMN_NAME')
        match = FORM.fullmatch(form) if isinstance(form, str) else None
        if match is None:
            raise ValueError('STOP_FIXED_TFORM')
        repeat, code = int(match[1] or 1), match[2]
        width = repeat * WIDTHS[code]
        if width > ROW_BYTES or position + width > ROW_BYTES:
            raise ValueError('STOP_COLUMN_WIDTH')
        canonical = code if repeat == 1 else str(repeat) + code
        unit = header.get(f'TUNIT{i}')
        if unit is not None and (not isinstance(unit, str) or len(unit) > 64 or any(not 32 <= ord(ch) <= 126 for ch in unit)):
            raise ValueError('STOP_COLUMN_UNIT')
        null = header.get(f'TNULL{i}')
        if f'TNULL{i}' in header:
            if code not in 'BIJK' or type(null) is not int:
                raise ValueError('STOP_NULL_SCHEMA')
            low, high = (0, 255) if code == 'B' else (-(1 << (WIDTHS[code] * 8 - 1)), (1 << (WIDTHS[code] * 8 - 1)) - 1)
            if not low <= null <= high:
                raise ValueError('STOP_NULL_RANGE')
        columns.append(Column(name, canonical, unit, null, position, width))
        names.add(name)
        position += width
    if position != ROW_BYTES:
        raise ValueError('STOP_ROW_WIDTH')
    for index, name, form, unit, offset in SELECTED:
        column = columns[index - 1]
        if (column.name, column.form, column.unit, column.offset, column.width) != (name, form, unit, offset, WIDTHS[form]):
            raise ValueError('STOP_SELECTED_SCHEMA')
        if f'TNULL{index}' in header:
            raise ValueError('STOP_SELECTED_NULL')
    return SourceSchema(tuple(columns))


def _validate_schema(schema):
    if (type(schema) is not SourceSchema or type(schema.columns) is not tuple
            or len(schema.columns) != FIELD_COUNT or any(type(c) is not Column or type(c.offset) is not int
                                                        or type(c.width) is not int for c in schema.columns)):
        raise ValueError('STOP_UNVALIDATED_SCHEMA')
    items = [('XTENSION', 'BINTABLE'), ('EXTNAME', 'SRCLIST'), ('BITPIX', 8), ('NAXIS', 2),
             ('NAXIS1', schema.row_bytes), ('NAXIS2', schema.rows), ('PCOUNT', 0), ('GCOUNT', 1), ('TFIELDS', FIELD_COUNT)]
    for i, c in enumerate(schema.columns, 1):
        items += [(f'TTYPE{i}', c.name), (f'TFORM{i}', c.form)]
        if c.unit is not None:
            items.append((f'TUNIT{i}', c.unit))
        if c.null is not None:
            items.append((f'TNULL{i}', c.null))
    if build_schema(items, schema.data_offset) != schema:
        raise ValueError('STOP_UNVALIDATED_SCHEMA')


def _store_span(columns, names, values):
    for name, value in zip(names, values, strict=True):
        columns[name].append(value)


def read_selected(stream, schema, *, accounting, checkpoint=None):
    """Read exactly five spans/row, never an entire row or intervening bytes.

    Stream must be an already-open unbuffered binary stream (raw I/O or a
    caller-guaranteed equivalent). BytesIO synthetic fixtures are supported;
    known buffered wrappers are rejected. Caller must bind the stream's file
    identity and not reuse this function to retry a failed scientific pass.
    A fresh EMPTY accounting dict survives caught failures. Returned floats,
    including NaN/inf, and signed integer IDs are not scientifically filtered.
    """
    if type(accounting) is not dict or accounting:
        raise ValueError('STOP_ACCOUNTING_ARGUMENT')
    accounting.update(status='IN_PROGRESS', phase='VALIDATING', current_row=None, current_span=None,
                      read_bytes=0, decoded_bytes=0, reads_attempted=0, reads_completed=0,
                      spans_decoded=0, rows_completed=0, current_read_completion_unknown=False,
                      current_decode_completion_unknown=False)
    try:
        _validate_schema(schema)
        if isinstance(stream, (io.BufferedReader, io.BufferedRandom, io.TextIOBase)):
            raise TypeError('STOP_BUFFERED_STREAM')
        if checkpoint is not None and not callable(checkpoint):
            raise ValueError('STOP_CHECKPOINT_ARGUMENT')
        columns = {name: [] for _, name, *_ in SELECTED}
        for row in range(ROWS):
            accounting['current_row'] = row
            for index, (offset, size, form, names) in enumerate(SPANS):
                accounting.update(current_span=index, phase='CHECKPOINT')
                if checkpoint is not None:
                    checkpoint()
                accounting['phase'] = 'SEEKING'
                expected = DATA_OFFSET + ROW_BYTES * row + offset
                if stream.seek(expected) != expected:
                    raise ValueError('STOP_SEEK_POSITION')
                if accounting['read_bytes'] + size > SELECTED_BYTES or accounting['reads_attempted'] >= READ_COUNT:
                    raise ValueError('STOP_SELECTED_BYTE_CAP')
                accounting['phase'] = 'READING'
                accounting['reads_attempted'] += 1
                raw = stream.read(size)
                if type(raw) is not bytes:
                    raise TypeError('STOP_BINARY_READ')
                accounting['read_bytes'] += len(raw)
                accounting['reads_completed'] += 1
                accounting['phase'] = 'READ_VALIDATING'
                if len(raw) != size:
                    raise ValueError('STOP_TRUNCATED_SELECTED_SPAN')
                accounting['phase'] = 'DECODING'
                values = struct.unpack(form, raw)
                accounting['decoded_bytes'] += size
                accounting['spans_decoded'] += 1
                accounting['phase'] = 'STORING'
                _store_span(columns, names, values)
            accounting['rows_completed'] += 1
        accounting['phase'] = 'FINALIZING'
        result = {name: tuple(values) for name, values in columns.items()}
        accounting.update(status='COMPLETE', phase='COMPLETE', current_row=None, current_span=None)
        return result
    except Exception:
        accounting['status'] = 'FAILED'
        accounting['current_read_completion_unknown'] = accounting['phase'] == 'READING'
        accounting['current_decode_completion_unknown'] = accounting['phase'] == 'DECODING'
        raise
