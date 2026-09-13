"""Synthetic rows/receipts only. Never open retained scientific products."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
import struct
import tempfile
import time
import unittest
import warnings
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from astropy.io import fits

SOURCE = Path(__file__).with_name('inspect_counts.py')
SPEC = importlib.util.spec_from_file_location('c9_synthetic', SOURCE)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
VERIFY_PRODUCT = M.verify_product


def pairs(pn, rows):
    names = ['TIME', 'RAWX', 'RAWY', 'DETX', 'DETY', 'X', 'Y', 'PHA', 'PI', 'FLAG', 'PATTERN']
    forms = ['D', 'I', 'I', 'I', 'I', 'J', 'J', 'I', 'I', 'J', 'B']
    names += ['PAT_ID', 'PAT_SEQ', 'CCDNR', 'TIME_RAW'] if pn else ['CCDNR']
    forms += ['I', 'B', 'B', 'D'] if pn else ['B']
    h = [('XTENSION', 'BINTABLE'), ('EXTNAME', 'EVENTS'), ('BITPIX', 8), ('NAXIS', 2),
         ('NAXIS1', 45 if pn else 34), ('NAXIS2', rows), ('PCOUNT', 0), ('GCOUNT', 1), ('TFIELDS', len(names))]
    for n, (name, form) in enumerate(zip(names, forms, strict=True), 1):
        h += [(f'TTYPE{n}', name), (f'TFORM{n}', form)]
    h += [('TUNIT1', 's'), ('TUNIT9', 'eV' if pn else 'CHAN'), ('TNULL6', -99999999), ('TNULL7', -99999999)]
    if pn:
        h += [('TNULL9', -32768), ('TNULL11', 13)]
    h += [('TUNIT6', 'pixel'), ('TUNIT7', 'pixel'), ('TCTYP6', 'RA---TAN'), ('TCTYP7', 'DEC--TAN'),
          ('TCUNI6', 'deg'), ('TCUNI7', 'deg'), ('TCDLT6', -1.38888888888889e-05), ('TCDLT7', 1.38888888888889e-05),
          ('TCRPX6', 113.), ('TCRPX7', 208.), ('TCRVL6', 137.), ('TCRVL7', -32.),
          ('RADECSYS', 'FK5'), ('EQUINOX', 2000.)]
    return h


def packed(pn, config):
    # Independent manual packed byte offsets. Unselected bytes stay opaque zero.
    raw = bytearray(45 if pn else 34)
    struct.pack_into('>d', raw, 0, config['tstart'] + 100.)
    struct.pack_into('>hh', raw, 8, 1, 2)
    struct.pack_into('>ii', raw, 16, 113, 208)
    struct.pack_into('>h', raw, 26, 1000)
    struct.pack_into('>i', raw, 28, 0)
    raw[32] = 4
    raw[36 if pn else 33] = 1
    return bytes(raw)


def cards(h):
    # Preserve the exact declared increment; generic Card formatting rounds the
    # negative value to fit a default twenty-character numeric field.
    return [(f'{c.keyword:8}= {c.value!s:>20}'.ljust(80) if c.keyword.startswith('TCDLT') else str(c))
            for c in fits.Header(dict(h)).cards]


class Fixture:
    def __init__(self, root, rows=3, chunk_rows=2):
        self.root = root
        self.stage, self.prior = root / 'stage', root / 'synthetic-prior'
        self.stage.mkdir()
        (self.prior / 'products').mkdir(parents=True)
        (self.prior / 'headers').mkdir()
        self.selected, self.geometry, self.counter = M.modules()
        self.configs = {name: self.counter.camera_config(name) for name in M.CAMERAS}
        self.plan = {'cameras': [], 'edges': self.counter.fixed_edges().tolist()}
        for slot, camera in enumerate(M.CAMERAS, 1):
            self.configs[camera]['total_rows'] = rows
            h = pairs(slot == 1, rows)
            schema = self.selected.build_schema(h, 2880)
            definition = self.geometry.build_geometry(h)
            report = {'hdus': [{'extname': 'EVENTS', 'data_offset': 2880, 'cards': cards(h)}]}
            name = f'synthetic-{slot}.fits'
            raw = bytes(2880) + packed(slot == 1, self.configs[camera]) * rows
            (self.prior / 'products' / name).write_bytes(raw)
            (self.prior / f'headers/slot-{slot}-headers.json').write_text(json.dumps(report), encoding='utf-8')
            self.plan['cameras'].append({'slot': slot, 'camera': camera, 'filename': name, 'file_bytes': len(raw),
                'schema': schema.metadata(), 'geometry': definition.metadata(), 'config': self.configs[camera],
                'chunks': math.ceil(rows / chunk_rows)})
        self.protocol = root / 'synthetic-protocol.md'
        self.protocol.write_text('Synthetic bounded fixture, not an experiment.\n', encoding='utf-8')
        self.context = contextlib.ExitStack()
        for target, key, value in ((M, 'HERE', self.stage), (M.C, 'HERE', self.stage), (M, 'PRIOR', self.prior),
                (M, 'PROTOCOL', self.protocol), (M, 'ROW_CAP', chunk_rows), (M.C, 'PEAK', 0), (M.C, 'DEADLINE', None)):
            self.context.enter_context(patch.object(target, key, value))
        self.context.enter_context(patch.object(M, 'modules', return_value=(self.selected, self.geometry, self.counter)))
        self.context.enter_context(patch.object(self.counter, 'camera_config', side_effect=lambda name: copy.deepcopy(self.configs[name])))
        self.context.enter_context(patch.object(M, 'centres', return_value=[(137., -32.)] * 5))
        self.context.enter_context(patch.object(M, 'manifest', return_value=self.plan))
        self.context.enter_context(patch.object(M, 'binding', side_effect=lambda _p: {'manifest': self.plan}))
        self.context.enter_context(patch.object(M, 'verify_product', side_effect=self.verify))

    @staticmethod
    def verify(item, progress):
        progress.update(status='COMPLETE', hash_bytes_returned=item['file_bytes'], header_bytes_read=2880)

    def close(self):
        self.context.close()

    def run(self, code=None):
        def launch(*_args):
            result = M.worker()
            return (result if code is None else code), 'synthetic worker output'
        original = M.C.load_pinned
        def load(name, path, digest):
            return SimpleNamespace(bounded_run=launch) if name == 'c9_deadline' else original(name, path, digest)
        with patch.object(M.C, 'load_pinned', side_effect=load), contextlib.redirect_stdout(io.StringIO()):
            return M.run()


class CountRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.fixture = Fixture(Path(self.temp.name))
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.fixture.close)

    def test_full_synthetic_worker_parent_replay_and_exact_files(self):
        self.assertEqual(self.fixture.run(), 0)
        outcome = M.C.read('outcome.json')
        self.assertEqual(outcome['status'], M.PASS)
        self.assertEqual(outcome['parent_validation']['status'], 'COMPLETED')
        before = M.artifacts()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', out.getvalue())
        self.assertEqual(M.artifacts(), before)
        for item in self.fixture.plan['cameras']:
            summary = M.C.read(f"camera-{item['slot']}-result.json")['summary']
            self.assertEqual(summary['rows'], 3)
            self.assertEqual(summary['accepted_rows'], 3)
            self.assertEqual(np.asarray(summary['circle20']).sum(axis=0).tolist(), [3] * 5)
            self.assertEqual(np.asarray(summary['annulus60_90']).sum(), 0)
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()

    def test_returned_short_read_and_partial_decoder_failure(self):
        item = self.fixture.plan['cameras'][0]
        path = self.fixture.prior / 'products' / item['filename']
        path.write_bytes(path.read_bytes()[:-2])
        progress = {}
        with self.assertRaisesRegex(ValueError, 'STOP_TRUNCATED_ROWS'):
            M.measure(item, progress)
        self.assertEqual(progress['read_bytes'], 133)
        self.assertEqual(progress['selected_bytes_decoded'], 56)
        self.assertEqual(progress['rows_completed'], 2)
        M.valid_progress(progress, item)
        path.write_bytes(bytes(2880) + packed(True, item['config']) * 3)
        old = self.fixture.selected._native_copy
        calls = []
        def convert(field):
            calls.append(1)
            if len(calls) == 2:
                raise MemoryError('synthetic private value')
            return old(field)
        progress = {}
        with patch.object(self.fixture.selected, '_native_copy', side_effect=convert), self.assertRaises(MemoryError):
            M.measure(item, progress)
        self.assertEqual(progress['read_bytes'], 90)
        self.assertEqual(progress['selected_bytes_decoded'], 16)
        self.assertTrue(progress['current']['decoder']['current_conversion_completion_unknown'])
        self.assertNotIn('private', json.dumps(progress))
        M.valid_progress(progress, item)

    def test_geometry_failure_retains_decode_and_projection_unknown(self):
        item, progress = self.fixture.plan['cameras'][0], {}
        with patch.object(self.fixture.geometry, '_project', side_effect=MemoryError), self.assertRaises(MemoryError):
            M.measure(item, progress)
        self.assertEqual(progress['selected_bytes_decoded'], 56)
        self.assertTrue(progress['current']['geometry']['current_projection_completion_unknown'])
        self.assertEqual(progress['rows_completed'], 0)
        M.valid_progress(progress, item)

    def test_rehashed_chunk_digest_or_progress_is_numerically_rejected(self):
        self.assertEqual(self.fixture.run(), 0)
        item = self.fixture.plan['cameras'][0]
        path = M.HERE / M.chunk_name(1, 1, 'result')
        record = M.C.read(path.name)
        record['increment_sha256'] = 'a' * 64
        path.write_text(json.dumps(record), encoding='utf-8')
        progress = {}
        with self.assertRaisesRegex(ValueError, 'STOP_CHUNK_REPLAY'):
            M.measure(item, progress, compare_chunks=True)
        self.assertEqual(progress['selected_bytes_decoded'], 56)
        self.assertEqual(progress['rows_completed'], 0)

    def test_impossible_partial_prefix_and_false_complete_components_rejected(self):
        item, progress = self.fixture.plan['cameras'][0], {}
        M.measure(item, progress)
        progress.update(status='FAILED', read_bytes=0, selected_bytes_decoded=0)
        with self.assertRaisesRegex(ValueError, 'STOP_PARTIAL_ACCOUNTING'):
            M.valid_progress(progress, item)
        self.assertEqual(self.fixture.run(), 0)
        record = M.C.read(M.chunk_name(1, 1, 'result'))['progress']
        record['decoder']['completed_fields'] = ['TIME']
        record['decoder']['selected_field_bytes_decoded'] = 16
        with self.assertRaisesRegex(ValueError, 'STOP_DECODER_ACCOUNTING'):
            M.valid_chunk(record, item)

    def test_extra_nested_nonjson_and_orphan_chunk_rejected(self):
        for name in ('unexpected.txt', 'camera-4-start.json', 'camera-1-chunk-0-start.json'):
            path = M.HERE / name
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_STAGE_ARTIFACT'):
                M.check_files()
            path.unlink()
        (M.HERE / 'nested').mkdir()
        with self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_STAGE_ARTIFACT'):
            M.check_files()
        (M.HERE / 'nested').rmdir()
        M.C.save('camera-1-chunk-2-start.json', {})
        with self.assertRaisesRegex(ValueError, 'STOP_ORPHAN_CAMERA'):
            M.ledger(self.fixture.plan['cameras'])

    def test_aggregate_schema_privacy_and_integer_denominator(self):
        item, progress = self.fixture.plan['cameras'][0], {}
        summary = M.measure(item, progress)
        for key, value in [('source_ra', 137.), ('annuli_are_source_masked', True), ('rows', 4)]:
            wrong = copy.deepcopy(summary)
            wrong[key] = value
            with self.assertRaises(ValueError):
                M.validate_summary(wrong, item['config'], self.fixture.counter)
        wrong = copy.deepcopy(summary)
        wrong['circle20'][0][0] = True
        with self.assertRaisesRegex(ValueError, 'STOP_SUMMARY_TYPE'):
            M.validate_summary(wrong, item['config'], self.fixture.counter)

    def test_parent_partial_second_camera_failure_and_replay_failure_accounting(self):
        original = M.measure
        def measure(item, accounting, **kwargs):
            if item['slot'] == 2 and not kwargs.get('persist'):
                with patch.object(self.fixture.geometry, '_project', side_effect=MemoryError):
                    return original(item, accounting, **kwargs)
            return original(item, accounting, **kwargs)
        with patch.object(M, 'measure', side_effect=measure):
            self.assertEqual(self.fixture.run(), 1)
        outcome = M.C.read('outcome.json')
        self.assertFalse(outcome['assessment_completed'])
        rows = outcome['parent_validation']['cameras']
        self.assertEqual([r['status'] for r in rows], ['COMPLETED', 'FAILED', 'NOT_ATTEMPTED'])
        self.assertEqual(rows[1]['accounting']['selected_bytes_decoded'], 56)
        with patch.object(M, 'measure', side_effect=AssertionError('must not reread')), contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_FAILURE_ARTIFACT_REPLAY', out.getvalue())

    def test_nonzero_worker_code_never_promotes_pass(self):
        self.assertEqual(self.fixture.run(code=124), 1)
        self.assertEqual(M.C.read('outcome.json')['status'], 'STOP')
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', out.getvalue())

    def test_prelaunch_failure_and_empty_state_replay(self):
        with patch.object(M, 'binding', side_effect=ValueError('STOP_SYNTHETIC_BINDING')):
            self.assertEqual(self.fixture.run(), 1)
        outcome = M.C.read('outcome.json')
        self.assertEqual([r['status'] for r in outcome['ledger']], ['NOT_ATTEMPTED'] * 3)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_FAILURE_ARTIFACT_REPLAY', out.getvalue())

    def test_terminal_parent_memory_failure_remains_replayable(self):
        original = M.C.save
        def save(name, value, **kwargs):
            if name == 'outcome.json':
                with patch.object(M.C, 'peak_memory', return_value=M.C.MEMORY_CAP + 1):
                    return original(name, value, **kwargs)
            return original(name, value, **kwargs)
        with patch.object(M.C, 'save', side_effect=save):
            self.assertEqual(self.fixture.run(), 1)
        M.C.PEAK = 0  # New process's monitoring state, recorded old peak remains untouched.
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', out.getvalue())

    def test_numerical_replay_partial_second_camera_reports_new_pass_without_writes(self):
        self.assertEqual(self.fixture.run(), 0)
        before = M.artifacts()
        original = M.measure
        def measure(item, accounting, **kwargs):
            if item['slot'] == 2:
                with patch.object(self.fixture.geometry, '_project', side_effect=MemoryError):
                    return original(item, accounting, **kwargs)
            return original(item, accounting, **kwargs)
        with patch.object(M, 'measure', side_effect=measure), contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(MemoryError):
            M.replay()
        record = json.loads(out.getvalue())
        self.assertEqual(record['replay_status'], 'FAILED')
        cameras = record['additional_numerical_pass']['cameras']
        self.assertEqual([v['status'] for v in cameras], ['COMPLETED', 'FAILED', 'NOT_ATTEMPTED'])
        self.assertEqual(cameras[1]['accounting']['selected_bytes_decoded'], 56)
        self.assertEqual(M.artifacts(), before)

    def test_late_numerical_replay_mismatch_reports_all_completed_bytes(self):
        self.assertEqual(self.fixture.run(), 0)
        record = M.C.read('outcome.json')
        record['source_masks_applied'] = True
        (M.HERE / 'outcome.json').write_text(json.dumps(record), encoding='utf-8')
        before = M.artifacts()
        with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaisesRegex(ValueError, 'STOP_OUTCOME_REPLAY'):
            M.replay()
        additional = json.loads(out.getvalue())['additional_numerical_pass']
        self.assertEqual(additional['status'], 'COMPLETED')
        self.assertEqual(sum(v['accounting']['read_bytes'] for v in additional['cameras']), 3 * (45 + 34 + 34))
        self.assertEqual(sum(v['accounting']['selected_bytes_decoded'] for v in additional['cameras']), 9 * 28)
        self.assertEqual(M.artifacts(), before)

    def test_caught_worker_short_read_persists_stop_and_three_camera_ledger(self):
        item = self.fixture.plan['cameras'][0]
        path = self.fixture.prior / 'products' / item['filename']
        path.write_bytes(path.read_bytes()[:-2])
        self.assertEqual(self.fixture.run(), 1)
        record = M.C.read('camera-1-result.json')
        self.assertEqual(record['error_code'], 'STOP_TRUNCATED_ROWS')
        self.assertEqual(record['accounting']['read_bytes'], 133)
        self.assertEqual(record['accounting']['selected_bytes_decoded'], 56)
        self.assertEqual(M.C.read(M.chunk_name(1, 2, 'result'))['status'], 'STOP')
        self.assertEqual([r['status'] for r in M.C.read('outcome.json')['ledger']], ['STOP', 'NOT_ATTEMPTED', 'NOT_ATTEMPTED'])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', out.getvalue())

    def test_cooperative_deadline_after_completed_chunk_keeps_prefix(self):
        original, calls = M.C.checkpoint, []
        def checkpoint():
            calls.append(1)
            if len(calls) == 5:
                M.C.DEADLINE = time.monotonic() - 1
            original()
        progress, item = {}, self.fixture.plan['cameras'][0]
        try:
            with patch.object(M.C, 'checkpoint', side_effect=checkpoint), self.assertRaisesRegex(ValueError, 'STOP_TOTAL_DEADLINE'):
                M.measure(item, progress)
        finally:
            M.C.DEADLINE = None
        self.assertEqual(progress['rows_completed'], 2)
        self.assertEqual(progress['read_bytes'], 90)
        self.assertEqual(progress['selected_bytes_decoded'], 56)
        M.valid_progress(progress, item)

    def test_ordinary_json_reserve_trip_retains_terminal_worker_and_outcome(self):
        original = M.C.save
        def save(name, value, **kwargs):
            if name == M.chunk_name(1, 2, 'start'):
                used = sum(p.stat().st_size for p in M.HERE.glob('*.json'))
                need = len(M.C.json_bytes(value, monitor=False))
                with patch.object(M.C, 'JSON_CAP', used + need + M.C.RESERVE - 1):
                    return original(name, value, **kwargs)
            return original(name, value, **kwargs)
        with patch.object(M.C, 'save', side_effect=save):
            self.assertEqual(self.fixture.run(), 1)
        self.assertEqual(M.C.read('camera-1-result.json')['error_code'], 'STOP_JSON_BUDGET')
        self.assertTrue((M.HERE / 'worker-result.json').exists())
        self.assertTrue((M.HERE / 'outcome.json').exists())
        self.assertEqual(M.C.read('camera-1-result.json')['accounting']['rows_completed'], 2)
        self.assertLess(M.C.resource_usage()['json_bytes'], M.C.JSON_CAP)

    def test_last_chunk_stop_cannot_be_under_successful_camera(self):
        self.assertEqual(self.fixture.run(), 0)
        path = M.HERE / M.chunk_name(1, 2, 'result')
        record = M.C.read(path.name)
        record.update(status='STOP', error_type='ValueError', error_code='STOP_SYNTHETIC')
        del record['increment_sha256']
        path.write_text(json.dumps(record), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_FAILED_CHUNK_UNDER_OK_CAMERA'):
            M.ledger(self.fixture.plan['cameras'])

    def test_product_structure_warning_tripwire_ignores_outer_filter(self):
        item = copy.deepcopy(self.fixture.plan['cameras'][0])
        raw = (self.fixture.prior / 'products' / item['filename']).read_bytes()
        item['product_sha256'] = hashlib.sha256(raw).hexdigest()
        hp = self.fixture.prior / 'headers/slot-1-headers.json'
        report = json.loads(hp.read_bytes())
        report.update(header_bytes_read=2880, parser_warning_categories=[])
        hp.write_text(json.dumps(report), encoding='utf-8')
        def structure(*_args):
            warnings.warn('synthetic private header', UserWarning, stacklevel=2)
            return copy.deepcopy(report)
        progress = {}
        with warnings.catch_warnings(), patch.object(M.C, 'load_pinned', return_value=SimpleNamespace(structure=structure)):
            warnings.simplefilter('ignore')
            with self.assertRaisesRegex(ValueError, 'STOP_HEADER_REPLAY'):
                VERIFY_PRODUCT(item, progress)
        self.assertEqual(progress['status'], 'FAILED')
        self.assertEqual(progress['hash_bytes_returned'], len(raw))
        self.assertEqual(progress['header_bytes_read'], 2880)
        self.assertNotIn('private', json.dumps(progress))

    def test_terminal_top_level_extra_private_fields_and_bool_marker_rejected(self):
        self.assertEqual(self.fixture.run(), 0)
        outcome = M.C.read('outcome.json')
        outcome['event_ra'] = 137.
        (M.HERE / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_TERMINAL_SCHEMA'):
            M.replay()
        worker = M.C.read('worker-result.json')
        worker['event_times'] = [0.]
        (M.HERE / 'worker-result.json').write_text(json.dumps(worker), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_TERMINAL_SCHEMA'):
            M.assess(0, M.state())
        marker = M.C.read('camera-1-start.json')
        marker['slot'] = True
        (M.HERE / 'camera-1-start.json').write_text(json.dumps(marker), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_CAMERA_ORDER'):
            M.ledger(self.fixture.plan['cameras'])


def benchmark():
    """Full planned synthetic row counts; no retained products/headers used."""
    began = time.monotonic()
    results = []
    with tempfile.TemporaryDirectory() as root:
        f = Fixture(Path(root), rows=3, chunk_rows=10000)
        try:
            # Generate repeated synthetic rows lazily instead of allocating full payloads.
            originals = {camera: config for camera, config in zip(M.CAMERAS, (
                {'total_rows': 2694388}, {'total_rows': 273441}, {'total_rows': 356129}), strict=True)}
            open_original = Path.open
            raw_for = {}
            for item in f.plan['cameras']:
                rows = originals[item['camera']]['total_rows']
                f.configs[item['camera']]['total_rows'] = rows
                h = pairs(item['slot'] == 1, rows)
                item['schema'] = f.selected.build_schema(h, 2880).metadata()
                item['chunks'] = math.ceil(rows / 10000)
                item['config'] = f.configs[item['camera']]
                item['file_bytes'] = 2880 + item['schema']['payload_bytes']
                report = {'hdus': [{'extname': 'EVENTS', 'data_offset': 2880, 'cards': cards(h)}]}
                (f.prior / f"headers/slot-{item['slot']}-headers.json").write_text(json.dumps(report), encoding='utf-8')
                raw_for[item['filename']] = packed(item['slot'] == 1, item['config'])

            class SyntheticStream:
                def __init__(self, row):
                    self.row = row
                def __enter__(self):
                    return self
                def __exit__(self, *_args):
                    return False
                def seek(self, offset):
                    return offset
                def read(self, size):
                    assert size >= 0 and size % len(self.row) == 0 and size <= 10000 * len(self.row)
                    return self.row * (size // len(self.row))

            def synthetic_open(path, *args, **kwargs):
                if path.parent == f.prior / 'products':
                    assert args == ('rb',) and kwargs == {'buffering': 0}
                    return SyntheticStream(raw_for[path.name])
                return open_original(path, *args, **kwargs)
            with patch.object(Path, 'open', synthetic_open):
                status = f.run()
            if status != 0:
                raise AssertionError('Full-size synthetic pipeline failed')
            outcome = M.C.read('outcome.json')
            results = {'synthetic_only': True, 'worker_and_parent_seconds': time.monotonic() - began,
                       'json_bytes': M.C.resource_usage()['json_bytes'], 'peak_memory_bytes': M.C.PEAK,
                       'worker_pass': [r['accounting'] for r in outcome['ledger']],
                       'parent_pass': outcome['parent_validation']}
        finally:
            f.close()
    return results


if __name__ == '__main__':
    unittest.main()
