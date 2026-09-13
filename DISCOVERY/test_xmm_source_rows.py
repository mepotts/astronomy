"""Independent synthetic selected spans; no retained product/value reads."""

import io
import json
import struct
import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np
import xmm_source_rows as reader


def header():
    items = [('XTENSION', 'BINTABLE'), ('EXTNAME', 'SRCLIST'), ('BITPIX', 8), ('NAXIS', 2),
             ('NAXIS1', 1131), ('NAXIS2', 151), ('PCOUNT', 0), ('GCOUNT', 1), ('TFIELDS', 266)]
    # Independent fixed-width layout with deliberately opaque repeated strings.
    special = {1: ('SRC_NUM', 'J', None), 6: ('RA', 'D', 'deg'), 7: ('DEC', 'D', 'deg'),
               8: ('RADEC_ERR', 'E', 'arcsec'), 146: ('EP_EXTENT', 'E', 'image pixels'),
               147: ('EP_EXT_ERR', 'E', 'image pixels'), 261: ('RA_CORR', 'D', 'deg'),
               262: ('DEC_CORR', 'D', 'deg'), 265: ('SYSERRCC', 'E', 'arcsec')}
    for i in range(1, 267):
        form = 'J' if 2 <= i <= 5 else '12A' if i == 9 else '36A' if i == 148 else 'D' if i in (263, 264) else '7A' if i == 266 else 'E'
        name, form, unit = special.get(i, (f'COLUMN_{i}', form, None))
        items += [(f'TTYPE{i}', name), (f'TFORM{i}', form)]
        if unit is not None:
            items.append((f'TUNIT{i}', unit))
    return items


def changed(items, key, value):
    return [(k, v) for k, v in items if k != key] + [(key, value)]


def fixture():
    raw = bytearray(b'\xa5' * (77760 + 151 * 1131 + 123))
    expected = []
    for i in range(151):
        values = [i - 75, 1.25 + i, -40.5 + i / 4, i / 8, -1. if i == 0 else i / 4,
                  i / 2, 1.5 + i, -40.75 + i / 4, i / 16]
        base = 77760 + i * 1131
        struct.pack_into('>i', raw, base, values[0])
        struct.pack_into('>ddf', raw, base + 20, *values[1:4])
        struct.pack_into('>ff', raw, base + 596, *values[4:6])
        struct.pack_into('>dd', raw, base + 1088, *values[6:8])
        struct.pack_into('>f', raw, base + 1120, values[8])
        expected.append(values)
    return bytes(raw), expected


class Guarded(io.BytesIO):
    def __init__(self, raw):
        super().__init__(raw)
        self.reads = []
        self.allowed = [(77760 + i * 1131 + offset, size) for i in range(151)
                        for offset, size in ((0, 4), (20, 20), (596, 8), (1088, 16), (1120, 4))]

    def read(self, size=-1):
        assert (self.tell(), size) == self.allowed[len(self.reads)]
        self.reads.append((self.tell(), size))
        return super().read(size)


class SourceRowsTests(unittest.TestCase):
    def setUp(self):
        self.schema = reader.build_schema(header(), 77760)
        self.raw, self.expected = fixture()

    def test_width_derivation_selected_offsets_and_json_metadata(self):
        self.assertEqual(len(self.schema.columns), 266)
        self.assertEqual(self.schema.columns[-1].offset + self.schema.columns[-1].width, 1131)
        expected = {1: 0, 6: 20, 7: 28, 8: 36, 146: 596, 147: 600, 261: 1088, 262: 1096, 265: 1120}
        self.assertEqual({i: self.schema.columns[i - 1].offset for i in expected}, expected)
        self.assertEqual(self.schema.metadata(), json.loads(json.dumps(self.schema.metadata())))
        self.assertEqual(self.schema.columns[8].width, 12)
        self.assertEqual(self.schema.columns[147].width, 36)

    def test_exact_755_reads_and_7852_bytes_struct_and_numpy_oracles(self):
        stream, progress, checkpoints = Guarded(self.raw), {}, []
        actual = reader.read_selected(stream, self.schema, accounting=progress, checkpoint=lambda: checkpoints.append(1))
        self.assertEqual(len(stream.reads), 755)
        self.assertEqual(len(checkpoints), 755)
        self.assertEqual(sum(n for _, n in stream.reads), 7852)
        self.assertEqual(progress['read_bytes'], 7852)
        self.assertEqual(progress['decoded_bytes'], 7852)
        self.assertEqual(progress['spans_decoded'], 755)
        self.assertEqual(progress['rows_completed'], 151)
        self.assertEqual(progress['status'], 'COMPLETE')
        names = ['SRC_NUM', 'RA', 'DEC', 'RADEC_ERR', 'EP_EXTENT', 'EP_EXT_ERR', 'RA_CORR', 'DEC_CORR', 'SYSERRCC']
        dtype = np.dtype({'names': names, 'formats': ['>i4', '>f8', '>f8', '>f4', '>f4', '>f4', '>f8', '>f8', '>f4'],
                          'offsets': [0, 20, 28, 36, 596, 600, 1088, 1096, 1120], 'itemsize': 1131})
        oracle = np.frombuffer(self.raw, dtype=dtype, offset=77760, count=151)
        for i, name in enumerate(names):
            self.assertEqual(actual[name], tuple(row[i] for row in self.expected))
            np.testing.assert_array_equal(actual[name], oracle[name])
        self.assertTrue(all(type(v) is int for v in actual['SRC_NUM']))
        self.assertEqual(actual['SRC_NUM'][0], -75)  # Geometry owns positive-ID validation.

    def test_nonfinite_extents_and_full_signed_ids_are_not_filtered(self):
        raw = bytearray(self.raw)
        struct.pack_into('>i', raw, 77760, -(2**31))
        struct.pack_into('>i', raw, 77760 + 1131, 2**31 - 1)
        struct.pack_into('>ddf', raw, 77760 + 20, float('nan'), float('inf'), -1.)
        struct.pack_into('>ff', raw, 77760 + 596, float('-inf'), float('nan'))
        result = reader.read_selected(Guarded(bytes(raw)), self.schema, accounting={})
        self.assertEqual(result['SRC_NUM'][:2], (-(2**31), 2**31 - 1))
        self.assertTrue(np.isnan(result['RA'][0]))
        self.assertTrue(np.isposinf(result['DEC'][0]))
        self.assertTrue(np.isneginf(result['EP_EXTENT'][0]))
        self.assertEqual(len(result['RA']), 151)

    def test_short_span_after_complete_row_has_exact_partial_counts(self):
        # Second row's third span returns three of its eight requested bytes.
        stream = Guarded(self.raw[:77760 + 1131 + 596 + 3])
        progress = {}
        with self.assertRaisesRegex(ValueError, 'STOP_TRUNCATED_SELECTED_SPAN'):
            reader.read_selected(stream, self.schema, accounting=progress)
        self.assertEqual(progress['read_bytes'], 52 + 24 + 3)
        self.assertEqual(progress['decoded_bytes'], 52 + 24)
        self.assertEqual(progress['spans_decoded'], 7)
        self.assertEqual(progress['rows_completed'], 1)
        self.assertEqual(progress['reads_attempted'], 8)
        self.assertFalse(progress['current_read_completion_unknown'])

    def test_storage_failure_counts_decoded_span_before_copy(self):
        progress = {}
        with patch.object(reader, '_store_span', side_effect=MemoryError('private synthetic value')), self.assertRaises(MemoryError):
            reader.read_selected(Guarded(self.raw), self.schema, accounting=progress)
        self.assertEqual(progress['read_bytes'], 4)
        self.assertEqual(progress['decoded_bytes'], 4)
        self.assertEqual(progress['spans_decoded'], 1)
        self.assertEqual(progress['rows_completed'], 0)
        self.assertEqual(progress['phase'], 'STORING')
        self.assertNotIn('private', json.dumps(progress))

    def test_read_and_decode_failures_distinguish_unknown_completion(self):
        progress = {}
        stream = Guarded(self.raw)
        with patch.object(stream, 'read', side_effect=OSError), self.assertRaises(OSError):
            reader.read_selected(stream, self.schema, accounting=progress)
        self.assertTrue(progress['current_read_completion_unknown'])
        self.assertEqual(progress['reads_attempted'], 1)
        self.assertEqual(progress['reads_completed'], 0)
        progress = {}
        with patch.object(reader.struct, 'unpack', side_effect=MemoryError), self.assertRaises(MemoryError):
            reader.read_selected(Guarded(self.raw), self.schema, accounting=progress)
        self.assertTrue(progress['current_decode_completion_unknown'])
        self.assertEqual(progress['read_bytes'], 4)
        self.assertEqual(progress['decoded_bytes'], 0)

    def test_checkpoint_failure_before_next_span_is_no_extra_read(self):
        calls = []

        def checkpoint():
            calls.append(1)
            if len(calls) == 3:
                raise TimeoutError

        stream, progress = Guarded(self.raw), {}
        with self.assertRaises(TimeoutError):
            reader.read_selected(stream, self.schema, accounting=progress, checkpoint=checkpoint)
        self.assertEqual(len(stream.reads), 2)
        self.assertEqual(progress['read_bytes'], 24)
        self.assertEqual(progress['decoded_bytes'], 24)
        self.assertEqual(progress['phase'], 'CHECKPOINT')

    def test_layout_column_identity_units_null_and_scaling_changes_rejected(self):
        cases = [('NAXIS1', 1132), ('NAXIS2', 150), ('NAXIS2', True), ('TFIELDS', 265),
                 ('TTYPE6', 'RA_OTHER'), ('TFORM6', '2E'), ('TUNIT146', 'image_pixels'),
                 ('TNULL1', -1), ('THEAP', 0), ('TSCAL9', 1), ('TZERO9', 0), ('TDIM9', '(12)'),
                 ('TFORM9', '1PJ'), ('TFORM9', '96X'), ('TFORM9', '0A'), ('NAXIS3', 1),
                 ('TFORM267', 'B'), ('TFORM01', 'J')]
        for key, value in cases:
            with self.subTest(key=key), self.assertRaises(ValueError):
                reader.build_schema(changed(header(), key, value), 77760)
        with self.assertRaisesRegex(ValueError, 'STOP_DUPLICATE_SCHEMA_CARD'):
            reader.build_schema(header() + [('NAXIS1', 1131)], 77760)

    def test_unselected_string_repeat_logical_and_integer_null_only_width(self):
        # Replace a four-byte opaque E by 4L; no logical-byte interpretation.
        h = changed(header(), 'TFORM10', '4L')
        h += [('TNULL2', -1)]
        schema = reader.build_schema(h, 77760)
        self.assertEqual(schema.columns[9].width, 4)
        self.assertEqual(schema.columns[1].null, -1)
        reader.read_selected(Guarded(self.raw), schema, accounting={})
        for value in (True, 2**31):
            with self.assertRaises(ValueError):
                reader.build_schema(h + [('TNULL3', value)], 77760)

    def test_forged_schema_or_buffered_stream_rejected_before_read(self):
        stream = Guarded(self.raw)
        for schema in (replace(self.schema, rows=150), replace(self.schema, data_offset=0),
                       replace(self.schema, columns=list(self.schema.columns)),
                       replace(self.schema, columns=(replace(self.schema.columns[0], offset=1), *self.schema.columns[1:]))):
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                reader.read_selected(stream, schema, accounting={})
        self.assertEqual(stream.reads, [])
        with self.assertRaisesRegex(TypeError, 'STOP_BUFFERED_STREAM'):
            reader.read_selected(io.BufferedReader(io.BytesIO(self.raw)), self.schema, accounting={})

    def test_fresh_accounting_required_and_seek_failure_preserved(self):
        with self.assertRaisesRegex(ValueError, 'STOP_ACCOUNTING_ARGUMENT'):
            reader.read_selected(Guarded(self.raw), self.schema, accounting={'read_bytes': 0})
        stream, progress = Guarded(self.raw), {}
        with patch.object(stream, 'seek', return_value=0), self.assertRaisesRegex(ValueError, 'STOP_SEEK_POSITION'):
            reader.read_selected(stream, self.schema, accounting=progress)
        self.assertEqual(progress['reads_attempted'], 0)
        self.assertEqual(progress['decoded_bytes'], 0)


if __name__ == '__main__':
    unittest.main()
