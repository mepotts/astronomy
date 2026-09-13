"""All frozen M5 cases on isolated M6, plus bounded amendment seams."""

import contextlib
import gzip
import importlib.util
import io
import json
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('m6_adapter_test', Path(__file__).with_name('acquire.py'))
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
M = A.load_core()
OLD = M.load_pinned(A.BASE_PATH.with_name('test_acquire.py'), A.TEST_HASH, 'm6_inherited_tests')
OLD.M = M


class AcquireTests(OLD.AcquireTests):
    """Run all sixteen unchanged M5 test methods against M6 globals."""

    def run_mock(self, code=None):
        def loader(_name, _path, _hash):
            def bounded(args, seconds):
                self.assertEqual(args[-2:], [str(M.SOURCE), '_worker'])
                self.assertEqual(M.SOURCE, A.SOURCE)
                self.assertEqual(seconds, 7200)
                result = M.worker()
                return result if code is None else code, 'private process output'
            return SimpleNamespace(bounded_run=bounded)
        with patch('requests.Session', side_effect=self.sessions), patch.object(M.C, 'load_pinned', loader), contextlib.redirect_stdout(io.StringIO()):
            return M.run()

    def test_fresh_instances_paths_lineage_and_stable_real_binding_no_old_private_reads(self):
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            if path.suffix in ('.tar', '.FTZ', '.fits', '.html') or 'headers' in path.parts:
                raise AssertionError('private input open')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded):
            first, second = A.load_core(), A.load_core()
            self.assertIsNot(first, second)
            self.assertIsNot(first.C, second.C)
            self.assertEqual(first.HERE, A.HERE)
            self.assertEqual(first.C.HERE, A.HERE)
            self.assertEqual(first.SOURCE, A.SOURCE)
            self.assertEqual(first.__file__, str(A.SOURCE))
            self.assertEqual(first.PROTOCOL, A.PROTOCOL)
            self.assertTrue(all(p.parent == A.HERE / 'products' for slot in first.PLAN for p in first.paths(slot)))
            definition = first.binding(A.PROTOCOL)
            with patch.object(first, 'SECONDS', 300), patch.object(first, 'CHUNK', 65536):
                self.assertEqual(definition, first.binding(A.PROTOCOL))
        caps = definition['caps']
        self.assertEqual([caps[k] for k in ('hard_worker_seconds', 'worker_seconds', 'parent_seconds', 'replay_seconds', 'network_chunk', 'chunk')],
                         [7200, 7140, 300, 300, 65536, 1048576])
        self.assertFalse(definition['adapter']['prior_partial_reused'])
        for name, sha in A.PINS.items():
            self.assertEqual(definition['dependencies'][str(A.HERE.parent / name)], sha)

    def test_network_and_local_read_sizes_and_exception_restore(self):
        class Reader:
            def __init__(self):
                self.sizes = []
            def read(self, size, **kwargs):
                self.sizes.append((size, kwargs))
                return b''
        for network, expected in ((True, 65536), (False, 1048576)):
            reader = Reader()
            M.copy_bounded(reader, io.BytesIO(), 2 * 1048576, M.progress(), 'raw', network=network)
            self.assertEqual(reader.sizes, [(expected, {'decode_content': False} if network else {})])
            self.assertEqual(M.CHUNK, 1048576)
        class Failing:
            def read(self, size, **kwargs):
                self.size = size
                raise OSError('private socket error')
        reader = Failing()
        with self.assertRaises(OSError):
            M.copy_bounded(reader, io.BytesIO(), 123, M.progress(), 'raw', network=True)
        self.assertEqual(reader.size, 124)
        self.assertEqual(M.CHUNK, 1048576)

    def test_replay_resource_guard_precedes_outcome_json_read(self):
        with patch.object(M, 'resources', side_effect=ValueError('STOP_RESOURCE_CAP')), patch.object(M.C, 'read', side_effect=AssertionError('no JSON allocation')), self.assertRaisesRegex(ValueError, 'STOP_RESOURCE_CAP'):
            M.replay()

    def test_late_parent_peak_after_missing_worker_timeout_remains_replayable(self):
        original_save = M.C.save
        def save(name, value, **kwargs):
            if name == 'outcome.json':
                self.assertEqual(value['error_code'], 'STOP_WORKER_HARD_DEADLINE')
                with patch.object(M.C, 'peak_memory', return_value=M.MEMORY_CAP + 1):
                    return original_save(name, value, **kwargs)
            return original_save(name, value, **kwargs)
        helper = SimpleNamespace(bounded_run=lambda args, seconds: (124, 'hard timeout'))
        with patch.object(M.C, 'load_pinned', return_value=helper), patch.object(M.C, 'save', side_effect=save), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read('outcome.json')
        self.assertEqual(outcome['error_code'], 'STOP_PEAK_MEMORY')
        self.assertEqual(outcome['worker_returncode'], 124)
        self.assertEqual(outcome['parent_peak_memory_bytes'], M.MEMORY_CAP + 1)
        self.assertEqual(outcome['header_verification_pass'], M.header_pass())
        before = M.artifacts()
        with patch.object(M, 'inspect_headers', side_effect=AssertionError('no header pass')), contextlib.redirect_stdout(io.StringIO()):
            M.replay()
        self.assertEqual(before, M.artifacts())
        outcome['parent_peak_memory_bytes'] = M.MEMORY_CAP
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_DEADLINE_CLASSIFICATION'):
            M.replay()

    def test_worker_and_parent_cooperative_deadlines_are_distinct_and_reset(self):
        for slot in M.PLAN:
            self.response(slot)
        values = []
        original_checkpoint = M.C.checkpoint
        def checkpoint(*args, **kwargs):
            if M.C.DEADLINE is not None:
                values.append(M.C.DEADLINE - M.time.monotonic())
            return original_checkpoint(*args, **kwargs)
        with patch.object(M.C, 'checkpoint', side_effect=checkpoint):
            self.assertEqual(self.run_mock(), 0)
        self.assertTrue(any(7130 < n <= 7140 for n in values))
        self.assertTrue(any(290 < n <= 300 for n in values))
        self.assertIsNone(M.C.DEADLINE)
        self.assertEqual(M.SECONDS, 7140)
        with patch.object(M, 'verify_binding', side_effect=ValueError('STOP_SYNTHETIC')), self.assertRaisesRegex(ValueError, 'STOP_SYNTHETIC'):
            M.assess(0)
        self.assertEqual(M.SECONDS, 7140)
        self.assertIsNone(M.C.DEADLINE)

    def test_missing_worker_timeout_keeps_private_partial_and_no_header_pass(self):
        def loader(_name, _path, _hash):
            def bounded(args, seconds):
                self.assertEqual(seconds, 7200)
                self.assertEqual(args[-2:], [str(A.SOURCE), '_worker'])
                M.C.save('worker-start.json', {'binding_sha256': M.C.sha(self.stage / 'run-start.json')})
                M.C.save('slot-1-start.json', M.PLAN[0])
                raw = M.paths(M.PLAN[0])[0]
                raw.parent.mkdir()
                raw.write_bytes(b'synthetic private incomplete bytes')
                return 124, 'hard timeout after 7200 seconds'
            return SimpleNamespace(bounded_run=bounded)
        with patch('requests.Session', side_effect=AssertionError('no network')), patch.object(M.C, 'load_pinned', loader), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read('outcome.json')
        self.assertEqual(outcome['worker_returncode'], 124)
        self.assertEqual(outcome['error_code'], 'STOP_WORKER_HARD_DEADLINE')
        self.assertFalse(outcome['assessment_completed'])
        self.assertEqual(outcome['header_verification_pass'], M.header_pass())
        self.assertEqual(outcome['ledger'], [{'slot': 1, 'status': 'UNVERIFIED_ATTEMPT'},
                                           {'slot': 2, 'status': 'NOT_ATTEMPTED'}, {'slot': 3, 'status': 'NOT_ATTEMPTED'}])
        before = M.artifacts()
        with patch.object(M, 'inspect_headers', side_effect=AssertionError('no headers')), contextlib.redirect_stdout(io.StringIO()):
            M.replay()
        self.assertEqual(before, M.artifacts())
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()
        outcome['error_code'] = 'STOP_INTERNAL'
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_DEADLINE_CLASSIFICATION'):
            M.replay()


def benchmark(image_bytes=64 * 1024**2):
    """Same representative physical synthetic fit; no archive or old partial."""
    test = AcquireTests()
    test.setUp()
    try:
        for i, slot in enumerate(M.PLAN):
            data = OLD.fits_bytes(slot, image_bytes=image_bytes)
            test.response(slot, body=data if i == 1 else gzip.compress(data, mtime=0))
        del data
        started = time.monotonic()
        result = test.run_mock()
        first_seconds = time.monotonic() - started
        before = M.artifacts()
        replay_started = time.monotonic()
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()
        test.assertEqual(before, M.artifacts())
        return {'synthetic_only': True, 'returncode': result, 'worker_parent_seconds': first_seconds,
                'replay_seconds': time.monotonic() - replay_started, 'resources': M.resources(),
                'peak_memory_bytes': M.C.read('outcome.json')['parent_peak_memory_bytes'],
                'mocked': ['HTTP', 'in-process launcher', 'binding'],
                'real': ['physical synthetic files', 'gzip/copy/hash/header/identity', 'Windows peak', 'receipts/replay']}
    finally:
        test.doCleanups()


if __name__ == '__main__':
    unittest.main()
