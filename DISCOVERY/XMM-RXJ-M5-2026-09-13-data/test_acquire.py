"""Synthetic three-product acquisition/header proof, no live HTTP or products."""

import contextlib
import gzip
import importlib.util
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from astropy.io.fits import Header

SPEC = importlib.util.spec_from_file_location('m5_test_module', Path(__file__).with_name('acquire.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fits_bytes(slot, wrong=False, image_bytes=0):
    primary = Header()
    for key, value in [('SIMPLE', True), ('BITPIX', 8), ('NAXIS', 1 if image_bytes else 0)]:
        primary[key] = value
    if image_bytes:
        primary['NAXIS1'] = image_bytes
    for key, value in [('EXTEND', True), ('OBS_ID', '0851180501'), ('INSTRUME', slot['camera']),
                       ('EXPIDSTR', 'S999' if wrong else slot['exposure']), ('SUBMODE', 'PrimeFullWindow'),
                       ('DATAMODE', 'IMAGING'), ('FILTER', 'Thin1'), ('OBSERVER', 'private observer'), ('RA_OBJ', 123.4)]:
        primary[key] = value
    events = Header()
    for key, value in [('XTENSION', 'BINTABLE'), ('BITPIX', 8), ('NAXIS', 2), ('NAXIS1', 8),
                       ('NAXIS2', 1), ('PCOUNT', 0), ('GCOUNT', 1), ('TFIELDS', 1), ('EXTNAME', 'EVENTS'),
                       ('TTYPE1', 'TIME'), ('TFORM1', '1D'), ('TUNIT1', 's')]:
        events[key] = value
    return (primary.tostring().encode() + bytes(image_bytes) + bytes((-image_bytes) % 2880)
            + events.tostring().encode() + bytes(2880))


class Raw(io.BytesIO):
    def read(self, size=-1, decode_content=False):
        assert not decode_content and 0 < size <= M.CHUNK
        return super().read(size)


class AcquireTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name) / 'stage'
        self.stage.mkdir()
        self.protocol = self.stage.parent / 'protocol.md'
        self.protocol.write_text('Synthetic protocol\n', encoding='utf-8')
        self.enterContext(patch.object(M, 'HERE', self.stage))
        self.enterContext(patch.object(M, 'PROTOCOL', self.protocol))
        self.enterContext(patch.object(M.C, 'HERE', self.stage))
        self.enterContext(patch.object(M.C, 'PEAK', 0))
        self.enterContext(patch.object(M.C, 'DEADLINE', None))
        self.original_binding = M.binding
        self.enterContext(patch.object(M, 'binding', return_value={'synthetic': True}))
        self.enterContext(patch.object(M.shutil, 'disk_usage', return_value=SimpleNamespace(free=10 * M.FREE_BYTES)))
        self.sessions, self.responses = [], []

    def response(self, slot, body=None, status=200, headers=None):
        response = MagicMock(status_code=status, url=slot['url'])
        values = {'Content-Type': ['application/octet-stream'], 'Content-Disposition': [f'attachment; filename="{slot["filename"]}"'],
                  'Set-Cookie': ['private-cookie'], **(headers or {})}
        response.raw = Raw(gzip.compress(fits_bytes(slot), mtime=0) if body is None else body)
        response.raw.headers = SimpleNamespace(getlist=lambda k: values.get(k, []))
        response.__enter__.return_value = response
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value = response
        self.sessions.append(session)
        self.responses.append(response)
        return response

    def run_mock(self, code=None):
        def loader(_name, _path, _hash):
            def bounded(args, seconds):
                self.assertEqual(args[-2:], [str(M.SOURCE), '_worker'])
                self.assertEqual(seconds, 300)
                result = M.worker()
                return result if code is None else code, 'private process output'
            return SimpleNamespace(bounded_run=bounded)
        with patch('requests.Session', side_effect=self.sessions), patch.object(M.C, 'load_pinned', loader), contextlib.redirect_stdout(io.StringIO()):
            return M.run()

    def test_three_gets_gzip_and_raw_fits_real_headers_identity_replay_no_decompression(self):
        for i, slot in enumerate(M.PLAN):
            self.response(slot, body=fits_bytes(slot) if i == 1 else None)
        started = time.monotonic()
        self.assertEqual(self.run_mock(), 0)
        for session, slot in zip(self.sessions, M.PLAN, strict=True):
            session.get.assert_called_once_with(slot['url'], timeout=(5, 15), stream=True, allow_redirects=False,
                                                headers={'Accept-Encoding': 'identity'})
            self.assertIs(session.trust_env, False)
            self.assertIsNone(session.auth)
            session.cookies.clear.assert_called_once()
        self.assertEqual(M.C.read('outcome.json')['ledger'], [{'slot': i, 'status': 'OK'} for i in range(1, 4)])
        for p in self.stage.glob('*.json'):
            for private in ('private observer', 'private-cookie', 'private process', 'RA_OBJ'):
                self.assertNotIn(private, p.read_text())
        self.assertEqual(M.C.read('slot-2-result.json')['progress']['actual_format'], 'RAW_FITS')
        before = M.artifacts()
        with patch('requests.Session', side_effect=AssertionError('no request')), patch.object(M, 'expand', side_effect=AssertionError('no repeated expansion')), contextlib.redirect_stdout(io.StringIO()) as output:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', output.getvalue())
        self.assertEqual(before, M.artifacts())
        self.assertLess(time.monotonic() - started, 300)
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()

    def test_exact_binding_without_prior_private_input_opens(self):
        real_here = Path(__file__).resolve().parent
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            if path.suffix in ('.tar', '.FTZ', '.fits', '.html') or 'headers' in path.parts:
                raise AssertionError('private input read')
            return original_open(path, *args, **kwargs)
        with patch.object(M, 'HERE', real_here), patch.object(Path, 'open', guarded):
            result = self.original_binding(real_here.parent / 'XMM-RXJ-M5-2026-09-13.md')
        self.assertEqual(result, json.loads(json.dumps(result)))
        self.assertEqual([p['filename'] for p in result['plan']], [
            'P0851180501PNS001PIEVLI0000.FTZ', 'P0851180501M1S002MIEVLI0000.FTZ', 'P0851180501M2S003MIEVLI0000.FTZ'])

    def test_second_http_failure_stops_third_and_keeps_all_three_slots(self):
        self.response(M.PLAN[0])
        response = self.response(M.PLAN[1], status=404)
        self.response(M.PLAN[2])
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual(response.raw.tell(), 0)
        self.sessions[2].get.assert_not_called()
        self.assertEqual(M.C.read('outcome.json')['ledger'], [{'slot': 1, 'status': 'OK'}, {'slot': 2, 'status': 'FAILED'}, {'slot': 3, 'status': 'NOT_ATTEMPTED'}])
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()

    def test_wrong_identity_retained_safe_stop_no_later_gets(self):
        self.response(M.PLAN[0], body=gzip.compress(fits_bytes(M.PLAN[0], wrong=True), mtime=0))
        self.response(M.PLAN[1])
        self.assertEqual(self.run_mock(), 1)
        self.sessions[1].get.assert_not_called()
        self.assertEqual(M.C.read('slot-1-identity.json')['status'], 'STOP_HEADER_IDENTITY_CONFLICT')
        self.assertEqual(M.C.read('slot-1-result.json')['phase'], 'IDENTITY')
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()

    def test_wrong_disposition_packaging_and_duplicate_length_before_body(self):
        slot = M.PLAN[0]
        cases = [({'Content-Disposition': ['attachment; filename="package.tar"']}, 'STOP_EXACT_FILENAME'),
                 ({'Content-Type': ['application/x-tar']}, 'STOP_MEDIA_TYPE'),
                 ({'Content-Length': ['4', '4']}, 'STOP_SAFE_HEADER_SCHEMA'),
                 ({'Content-Encoding': ['gzip']}, 'STOP_CONTENT_ENCODING')]
        for headers, reason in cases:
            response = self.response(slot, headers=headers)
            with patch('requests.Session', return_value=self.sessions[-1]), self.assertRaisesRegex(ValueError, reason):
                M.download(slot, M.progress())
            self.assertEqual(response.raw.tell(), 0)
            path = self.stage / 'slot-1-http.json'
            if path.exists():
                path.unlink()

    def test_raw_overflow_one_byte_partial_and_aggregate_zero_no_get(self):
        slot = M.PLAN[0]
        response = self.response(slot, body=b'x' * 2000)
        with patch.object(M, 'CAP', 1024), patch('requests.Session', return_value=self.sessions[-1]):
            state = M.progress()
            with self.assertRaisesRegex(ValueError, 'STOP_BYTE_CAP'):
                M.download(slot, state)
        self.assertEqual(response.raw.tell(), 1025)
        self.assertEqual(state['raw_returned_bytes'], 1025)
        self.assertEqual(state['raw_retained_bytes'], 1024)
        with patch.object(M, 'RAW_TOTAL', 1024), patch('requests.Session', side_effect=AssertionError('no GET when exhausted')), self.assertRaisesRegex(ValueError, 'STOP_RAW_TOTAL_CAP'):
            M.download(M.PLAN[1], M.progress())

    def test_crc_failure_and_expanded_overflow_preserve_partials(self):
        slot = M.PLAN[0]
        bad = bytearray(gzip.compress(fits_bytes(slot), mtime=0))
        bad[-8] ^= 1
        self.response(slot, body=bytes(bad))
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual(M.C.read('slot-1-result.json')['error_code'], 'STOP_GZIP_INTEGRITY')
        self.assertFalse(M.C.read('slot-1-result.json')['progress']['gzip_crc_eof_verified'])

    def test_expansion_cap_direct_and_returned_vs_retained(self):
        slot = M.PLAN[0]
        raw, _expanded = M.paths(slot)
        raw.parent.mkdir()
        raw.write_bytes(gzip.compress(fits_bytes(slot), mtime=0))
        state = M.progress()
        with patch.object(M, 'EXPANDED_CAP', 1024), self.assertRaisesRegex(ValueError, 'STOP_BYTE_CAP'):
            M.expand(slot, state)
        self.assertEqual(state['expanded_returned_bytes'], 1025)
        self.assertEqual(state['expanded_retained_bytes'], 1024)
        self.assertFalse(state['expanded_eof'])

    def test_socket_failure_preserves_unknown_invocation_and_safe_partial(self):
        response = self.response(M.PLAN[0])
        headers = response.raw.headers
        response.raw = MagicMock(headers=headers)
        response.raw.read.side_effect = [b'1234567', TimeoutError('private endpoint detail')]
        self.assertEqual(self.run_mock(), 1)
        state = M.C.read('slot-1-result.json')['progress']
        self.assertEqual(state['raw_returned_bytes'], 7)
        self.assertEqual(state['raw_retained_bytes'], 7)
        self.assertTrue(state['raw_read_unknown'])
        self.assertNotIn('private', (self.stage / 'slot-1-result.json').read_text())

    def test_rehashed_typed_terminal_and_header_mutations_fail(self):
        for slot in M.PLAN:
            self.response(slot)
        self.assertEqual(self.run_mock(), 0)
        original = M.C.read('outcome.json')
        for key, value in [('status', 'DISCOVERY'), ('worker_returncode', False), ('assessment_completed', 1), ('output_bytes', True),
                           ('error_code', 'STOP_SYNTHETIC')]:
            record = {**original, key: value}
            (self.stage / 'outcome.json').write_text(json.dumps(record), encoding='utf-8')
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.replay()

    def test_raised_and_short_writes_preserve_known_returned_and_actual_interval(self):
        for raises in (True, False):
            state = M.progress()
            actual = io.BytesIO()
            def write(block, actual=actual, raises=raises):
                actual.write(block[:3])
                if raises:
                    raise OSError('private write failure')
                return 3
            with self.subTest(raises=raises), self.assertRaises((ValueError, OSError)):
                M.copy_bounded(io.BytesIO(b'1234567'), SimpleNamespace(write=write), 100, state, 'raw')
            self.assertEqual(state['raw_returned_bytes'], 7)
            self.assertEqual(state['raw_retained_bytes'], 0 if raises else 3)
            record = {'status': 'FAILED', 'raw': {'bytes': len(actual.getvalue())}, 'expanded': None}
            M.validate_progress(state, record)
            record['raw']['bytes'] = 8
            with self.assertRaisesRegex(ValueError, 'STOP_PROGRESS_FILE_BYTES'):
                M.validate_progress(state, record)

    def test_parent_header_failure_retains_partial_pass_and_artifact_replay(self):
        for slot in M.PLAN:
            self.response(slot)
        original = M.inspect_headers
        calls = []
        def inspect(slot):
            calls.append(slot['slot'])
            if len(calls) == 5:
                raise ValueError('STOP_SYNTHETIC_HEADER')
            return original(slot)
        with patch.object(M, 'inspect_headers', side_effect=inspect):
            self.assertEqual(self.run_mock(), 1)
        outcome = M.C.read('outcome.json')
        self.assertFalse(outcome['assessment_completed'])
        self.assertEqual(outcome['header_verification_pass'], [
            {'slot': 1, 'started': True, 'completed': True},
            {'slot': 2, 'started': True, 'completed': False},
            {'slot': 3, 'started': False, 'completed': False}])
        before = M.artifacts()
        with patch.object(M, 'inspect_headers', side_effect=AssertionError('artifact-only')), contextlib.redirect_stdout(io.StringIO()):
            M.replay()
        self.assertEqual(before, M.artifacts())

    def test_replay_partial_and_late_failure_reports_new_header_pass(self):
        for slot in M.PLAN:
            self.response(slot)
        self.assertEqual(self.run_mock(), 0)
        original = M.inspect_headers
        def inspect(slot):
            if slot['slot'] == 2:
                raise ValueError('STOP_SYNTHETIC_HEADER')
            return original(slot)
        before = M.artifacts()
        with patch.object(M, 'inspect_headers', side_effect=inspect), contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaisesRegex(ValueError, 'STOP_SYNTHETIC_HEADER'):
            M.replay()
        state = json.loads(output.getvalue())['additional_header_verification_pass']
        self.assertEqual([row['started'] for row in state], [True, True, False])
        self.assertEqual([row['completed'] for row in state], [True, False, False])
        self.assertEqual(before, M.artifacts())
        outcome = M.C.read('outcome.json')
        outcome['worker_error_code'] = 'STOP_SYNTHETIC'
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        before = M.artifacts()
        with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaisesRegex(ValueError, 'STOP_OUTCOME_REPLAY'):
            M.replay()
        state = json.loads(output.getvalue())['additional_header_verification_pass']
        self.assertTrue(all(row['completed'] for row in state))
        self.assertEqual(before, M.artifacts())
        for bad in ([{'slot': 1, 'started': 1, 'completed': True}] + M.header_pass()[1:],
                    [M.header_pass()[0], {'slot': 2, 'started': True, 'completed': True}, M.header_pass()[2]]):
            with self.assertRaisesRegex(ValueError, 'STOP_HEADER_PASS_SCHEMA'):
                M.validate_header_pass(bad)

    def test_large_identity_stop_preserves_terminal_reserve(self):
        for slot in M.PLAN:
            self.response(slot)
        with patch.object(M, 'summarize_identity', return_value={'status': 'HEADER_IDENTITY_AUTHENTICATED', 'huge': 'x' * M.HEADER_CAP}):
            self.assertEqual(self.run_mock(), 1)
        self.assertEqual(M.C.read('slot-1-result.json')['error_code'], 'STOP_JSON_BUDGET')
        self.assertTrue((self.stage / 'worker-result.json').exists())
        self.assertTrue((self.stage / 'outcome.json').exists())
        self.assertFalse((self.stage / 'slot-1-identity.json').exists())
        self.sessions[1].get.assert_not_called()

    def test_free_space_prelaunch_and_raw_worker_nonzero(self):
        with patch.object(M.shutil, 'disk_usage', return_value=SimpleNamespace(free=M.FREE_BYTES - 1)):
            self.assertEqual(self.run_mock(), 1)
        self.assertFalse((self.stage / 'worker-start.json').exists())
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()

    def test_raw_nonzero_result_does_not_promote_completed_worker(self):
        for slot in M.PLAN:
            self.response(slot)
        self.assertEqual(self.run_mock(code=124), 1)
        self.assertEqual(M.C.read('worker-result.json')['status'], M.PASS)
        self.assertEqual(M.C.read('outcome.json')['worker_returncode'], 124)
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()


def benchmark(image_bytes=64 * 1024**2):
    """Optional bounded synthetic physical-file benchmark, no actual inputs."""
    test = AcquireTests()
    test.setUp()
    try:
        for i, slot in enumerate(M.PLAN):
            data = fits_bytes(slot, image_bytes=image_bytes)
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
        outcome = M.C.read('outcome.json')
        return {'synthetic_only': True, 'returncode': result, 'worker_parent_seconds': first_seconds,
                'replay_seconds': time.monotonic() - replay_started, 'resources': M.resources(),
                'peak_memory_bytes': outcome['parent_peak_memory_bytes'],
                'mocked': ['anonymous HTTP bodies supplied from synthetic bytes', 'launcher in-process', 'metadata binding'],
                'real': ['gzip/raw copying', 'physical temporary products', 'opaque hashes', 'FITS structure', 'identity parser', 'Windows peak sampler', 'receipts/replay']}
    finally:
        test.doCleanups()


if __name__ == '__main__':
    unittest.main()
