"""Synthetic bytes only; no local science products or header dependencies."""

import json
import struct
import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np
import xmm_event_rows as decoder
from xmm_event_rows import MAX_CHUNK_ROWS, SELECTED, build_schema, decode_rows


def header(pn=True, rows=3):
    names = ['TIME', 'RAWX', 'RAWY', 'DETX', 'DETY', 'X', 'Y', 'PHA', 'PI', 'FLAG', 'PATTERN']
    forms = ['D', 'I', 'I', 'I', 'I', 'J', 'J', 'I', 'I', 'J', 'B']
    if pn:
        names += ['PAT_ID', 'PAT_SEQ', 'CCDNR', 'TIME_RAW']
        forms += ['I', 'B', 'B', 'D']
    else:
        names += ['CCDNR']
        forms += ['B']
    items = [('XTENSION', 'BINTABLE'), ('EXTNAME', 'EVENTS'), ('BITPIX', 8), ('NAXIS', 2),
             ('NAXIS1', 45 if pn else 34), ('NAXIS2', rows), ('PCOUNT', 0),
             ('GCOUNT', 1), ('TFIELDS', len(names))]
    for i, (name, form) in enumerate(zip(names, forms, strict=True), 1):
        items += [(f'TTYPE{i}', name), (f'TFORM{i}', form)]
    items += [('TUNIT1', 's'), ('TUNIT9', 'eV' if pn else 'CHAN'),
              ('TNULL6', -99999999), ('TNULL7', -99999999)]
    if pn:
        items += [('TNULL9', -32768), ('TNULL11', 13)]
    return items


def changed(items, key, value):
    return [(k, v) for k, v in items if k != key] + [(key, value)]


def packed(pn=True, **values):
    defaults = {'TIME': 123.25, 'RAWX': -2, 'RAWY': 123, 'DETX': 30000, 'DETY': -30000,
                'X': 70000, 'Y': -80000, 'PHA': -123, 'PI': 1000, 'FLAG': -2147483648,
                'PATTERN': 4, 'PAT_ID': -234, 'PAT_SEQ': 255, 'CCDNR': 7, 'TIME_RAW': -5.5}
    defaults.update(values)
    schema = build_schema(header(pn), 0)
    formats = {'D': 'd', 'I': 'h', 'J': 'i', 'B': 'B'}
    return b''.join(struct.pack('>' + formats[c.form], defaults[c.name]) for c in schema.columns)


class EventRowsTests(unittest.TestCase):
    def test_handbuilt_schema_cannot_bypass_offsets_formats_or_width(self):
        s = build_schema(header(), 0)
        changed_columns = [replace(s.columns[0], offset=1), *s.columns[1:]]
        wrong_format = [replace(s.columns[0], form='E'), *s.columns[1:]]
        for forged in [replace(s, columns=tuple(changed_columns)), replace(s, columns=tuple(wrong_format)),
                       replace(s, columns=list(s.columns)), replace(s, row_bytes=44),
                       replace(s, rows=True), replace(s, data_offset=1)]:
            with self.subTest(forged=forged), self.assertRaises(ValueError):
                decode_rows(b'', forged)

    def test_partial_mask_failure_accounts_converted_time(self):
        progress = {}
        s, raw = build_schema(header(), 0), packed()
        with patch.object(decoder.np, 'isfinite', side_effect=MemoryError), self.assertRaises(MemoryError):
            decode_rows(raw, s, accounting=progress)
        self.assertEqual(progress['status'], 'FAILED')
        self.assertEqual(progress['buffer_bytes_supplied'], 45)
        self.assertEqual(progress['selected_field_bytes_decoded'], 8)
        self.assertEqual(progress['completed_fields'], ['TIME'])
        self.assertEqual(progress['phase'], 'MASKING')
        self.assertEqual(progress['current_field'], 'TIME')
        self.assertEqual(progress['rows_completed'], 0)
        self.assertFalse(progress['current_conversion_completion_unknown'])

    def test_partial_conversion_failure_is_distinctly_unknown(self):
        progress = {}
        s, raw = build_schema(header(), 0), packed()
        original = decoder._native_copy
        calls = []

        def convert(field):
            calls.append(1)
            if len(calls) == 2:
                raise MemoryError
            return original(field)

        with patch.object(decoder, '_native_copy', side_effect=convert), self.assertRaises(MemoryError):
            decode_rows(raw, s, accounting=progress)
        self.assertEqual(progress['selected_field_bytes_decoded'], 8)
        self.assertEqual(progress['completed_fields'], ['TIME'])
        self.assertEqual(progress['current_field'], 'RAWX')
        self.assertEqual(progress['phase'], 'CONVERTING')
        self.assertTrue(progress['current_conversion_completion_unknown'])

    def test_progress_success_and_invalid_buffer_accounting(self):
        progress = {}
        result = decode_rows(packed(), build_schema(header(), 0), accounting=progress)
        self.assertEqual(progress['status'], 'COMPLETE')
        self.assertEqual(progress['rows_completed'], 1)
        self.assertEqual(progress['selected_field_bytes_decoded'], 28)
        self.assertEqual(progress['completed_fields'], list(SELECTED))
        self.assertEqual(progress['buffer_bytes_supplied'], result['accounting']['buffer_bytes_supplied'])
        self.assertEqual(progress, json.loads(json.dumps(progress)))
        failed = {}
        with self.assertRaises(ValueError):
            decode_rows(packed()[:-1], build_schema(header(), 0), accounting=failed)
        self.assertEqual(failed['buffer_bytes_supplied'], 44)
        self.assertEqual(failed['selected_field_bytes_decoded'], 0)
        self.assertEqual(failed['phase'], 'VALIDATING')
        with self.assertRaises(ValueError):
            decode_rows(packed(), build_schema(header(), 0), accounting=progress)

    def test_exact_layout_and_json_native(self):
        for pn, width, ccd in [(True, 45, 36), (False, 34, 33)]:
            s = build_schema(header(pn), 63360 if pn else 40320)
            self.assertEqual(s.row_bytes, width)
            offsets = {c.name: c.offset for c in s.columns}
            self.assertEqual({n: offsets[n] for n in SELECTED},
                             dict(zip(SELECTED, [0, 8, 10, 16, 20, 26, 28, 32, ccd], strict=True)))
            self.assertEqual(s.metadata(), json.loads(json.dumps(s.metadata())))

    def test_independent_struct_decode_and_signed_flag(self):
        for pn in [True, False]:
            result = decode_rows(packed(pn), build_schema(header(pn), 0))
            for name, value in [('TIME', 123.25), ('RAWX', -2), ('RAWY', 123), ('X', 70000),
                                ('Y', -80000), ('PI', 1000), ('PATTERN', 4), ('CCDNR', 7)]:
                self.assertEqual(result['values'][name][0], value)
            self.assertEqual(result['values']['FLAG'].dtype, np.dtype('i4'))
            self.assertEqual(result['values']['FLAG'][0], -2147483648)
            self.assertEqual(result['flag_bits'][0], 0x80000000)
            self.assertEqual(set(result['values']), set(SELECTED))
            self.assertEqual(result['accounting']['selected_field_bytes_decoded'], 28)
            self.assertEqual(result['accounting']['buffer_bytes_supplied'], 45 if pn else 34)

    def test_flag_all_bits_zero_and_lowbit(self):
        raw = b''.join(packed(FLAG=v) for v in [-1, 0, 1])
        result = decode_rows(raw, build_schema(header(), 0))
        np.testing.assert_array_equal(result['flag_bits'], [0xffffffff, 0, 1])
        self.assertTrue(result['row_valid'].all())

    def test_null_and_nonfinite_not_dropped(self):
        raw = packed(TIME=float('nan'), X=-99999999) + packed(TIME=float('inf'), PI=-32768) + packed(PATTERN=13)
        result = decode_rows(raw, build_schema(header(), 0))
        self.assertEqual(len(result['values']['TIME']), 3)
        np.testing.assert_array_equal(result['row_valid'], [False, False, False])
        np.testing.assert_array_equal(result['masks']['TIME']['nonfinite'], [True, True, False])
        self.assertTrue(result['masks']['X']['null'][0])
        self.assertEqual(result['values']['X'][0], -99999999)
        self.assertTrue(result['masks']['PI']['null'][1])
        self.assertTrue(result['masks']['PATTERN']['null'][2])

    def test_camera_specific_missingness_not_science_cut(self):
        result = decode_rows(packed(False, PI=-32768, PATTERN=13, CCDNR=0), build_schema(header(False), 0))
        self.assertTrue(result['row_valid'][0])  # No MOS sentinel or detector/science policy invented.
        self.assertFalse(result['masks']['PI']['null'][0])

    def test_every_selected_integer_null(self):
        for name in list(SELECTED)[1:]:
            h = header()
            index = next(i for i in range(1, 16) if dict(h)[f'TTYPE{i}'] == name)
            h = changed(h, f'TNULL{index}', 0)
            result = decode_rows(packed(**{name: 0}), build_schema(h, 0))
            self.assertTrue(result['masks'][name]['null'][0])
            self.assertFalse(result['row_valid'][0])

    def test_readonly_and_buffer_isolation(self):
        r = decode_rows(packed(), build_schema(header(), 0))
        for a in [*r['values'].values(), r['flag_bits'], r['row_valid'], r['masks']['X']['null']]:
            with self.assertRaises(ValueError):
                a[0] = 0
        with self.assertRaises(TypeError):
            decode_rows(bytearray(packed()), build_schema(header(), 0))

    def test_duplicate_missing_format_and_row_width(self):
        cases = [header() + [('NAXIS1', 45)], changed(header(), 'TTYPE2', 'TIME'),
                 changed(header(), 'TTYPE6', 'OTHER'), changed(header(), 'TFORM6', 'I'),
                 changed(header(), 'NAXIS1', 46), changed(header(), 'NAXIS2', True),
                 changed(header(), 'BITPIX', True), header() + [('TFORM16', 'B')]]
        for h in cases:
            with self.subTest(h=h), self.assertRaises(ValueError):
                build_schema(h, 0)

    def test_rejected_vector_heap_scaling_null_schemas(self):
        for key, value in [('TFORM4', '2I'), ('TFORM4', 'X'), ('TFORM4', '1PJ'),
                           ('TFORM4', '0I'), ('THEAP', 0), ('PCOUNT', 1), ('TDIM4', '(1)'),
                           ('TSCAL4', 1), ('TZERO10', 2147483648), ('TNULL1', 0),
                           ('TNULL11', 256), ('TNULL9', -32769), ('TNULL9', True)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                build_schema(changed(header(), key, value), 0)

    def test_scalar_repeat_and_opaque_scalar_widths(self):
        s = build_schema(changed(header(), 'TFORM1', '1D'), 0)
        self.assertEqual(s.columns[0].form, 'D')
        for form, width in [('A', 1), ('L', 1), ('C', 8), ('M', 16), ('K', 8), ('E', 4)]:
            h = changed(changed(header(), 'TFORM4', form), 'NAXIS1', 45 - 2 + width)
            s = build_schema(h, 0)
            self.assertEqual(s.columns[4].offset, 12 + width)

    def test_chunk_range_empty_and_truncation(self):
        s = build_schema(header(), 0)
        self.assertEqual(decode_rows(b'', s, row_start=3)['accounting']['rows_decoded'], 0)
        for raw, start in [(packed()[:-1], 0), (packed(), 3), (b'', 4), (packed(), -1), (packed(), True)]:
            with self.assertRaises(ValueError):
                decode_rows(raw, s, row_start=start)
        big = build_schema(header(rows=MAX_CHUNK_ROWS + 1), 0)
        with self.assertRaises(ValueError):
            decode_rows(packed() * (MAX_CHUNK_ROWS + 1), big)

    def test_no_padding_or_cross_row_leakage(self):
        s = build_schema(header(), 0)
        raw = packed(X=42, CCDNR=1) + packed(X=-71, CCDNR=12)
        r = decode_rows(raw, s, row_start=1)
        np.testing.assert_array_equal(r['values']['X'], [42, -71])
        np.testing.assert_array_equal(r['values']['CCDNR'], [1, 12])
        self.assertEqual(r['accounting'], {'row_start': 1, 'rows_decoded': 2,
                                          'buffer_bytes_supplied': 90, 'selected_field_bytes_decoded': 56,
                                          'unselected_bytes_present': 34})


if __name__ == '__main__':
    unittest.main()
