"""Synthetic plain-TAR acquisition and immutable local replay tests only."""

import contextlib
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location('m3_test_module', Path(__file__).with_name('listing.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
HTML = b'<html>private contacts; not adjudicated; no closing tags'
NAME = 'P0851180501OBX000SUMMAR0000.HTM'  # Unobserved synthetic identity only.


def archive(extra=False):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w', format=tarfile.USTAR_FORMAT) as t:
        info = tarfile.TarInfo('./arbitrary/' + NAME)
        info.size = len(HTML)
        t.addfile(info, io.BytesIO(HTML))
        if extra:
            info = tarfile.TarInfo('unrelated.txt')
            info.size = 1
            t.addfile(info, io.BytesIO(b'x'))
    return out.getvalue()


class Raw(io.BytesIO):
    def read(self, size=-1, decode_content=False):
        assert not decode_content and 0 < size <= 8192
        return super().read(size)


class ListingTests(unittest.TestCase):
    def setUp(self):
        self.core = M.load_core()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stage = root / 'stage'
        self.stage.mkdir()
        protocol = root / 'protocol.txt'
        protocol.write_text('Synthetic protocol\n', encoding='utf-8')
        self.core.HERE, self.core.PROTOCOL = self.stage, protocol
        self.core.binding = lambda _p: {'synthetic': True}

    def response(self, body=None, status=200, headers=None):
        response = MagicMock(status_code=status, url=M.URL)
        values = {'Content-Type': ['application/x-tar'], 'Set-Cookie': ['secret'], **(headers or {})}
        response.raw = Raw(archive() if body is None else body)
        response.raw.headers = SimpleNamespace(getlist=lambda k: values.get(k, []))
        response.__enter__.return_value = response
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value = response
        self.enterContext(patch('requests.Session', return_value=session))
        return session, response

    def run_mock(self, code=None):
        def bounded(args, seconds):
            self.assertEqual(args[-2:], [str(M.SOURCE), '_worker'])
            self.assertEqual(seconds, 30)
            result = self.core.worker()
            return result if code is None else code, 'private child output'
        with patch.object(self.core, 'deadline_helper', return_value=SimpleNamespace(bounded_run=bounded)), contextlib.redirect_stdout(io.StringIO()):
            return self.core.run()

    def test_actual_binding_privacy_paths_and_fresh_verified_buffer(self):
        with patch('importlib.machinery.SourceFileLoader.get_data', side_effect=AssertionError('unchecked source')):
            a, b = M.load_core(), M.load_core()
        a.CAP = 1
        self.assertEqual(b.CAP, 1048576)
        self.assertEqual(b.SOURCE, M.SOURCE)
        self.assertEqual(b.HERE, M.HERE)
        result = b.binding(M.PROTOCOL)
        self.assertEqual(result, json.loads(json.dumps(result)))
        self.assertEqual(result['body_filename'], 'summary.tar')
        self.assertEqual(result['outer_body_replacements'], 3)
        self.assertEqual(result['private_html_cap'], 262144)
        self.assertEqual(set((M.HERE / '.gitignore').read_text().splitlines()), {'/summary.tar', '/summary.html'})
        self.assertTrue({'summary.tar', 'summary.html', 'transport.json'} <= set(b.ARTIFACTS))

    def test_full_one_get_worker_parent_and_readonly_replay_safe_inventory(self):
        session, _response = self.response(headers={'Content-Length': [str(len(archive()))],
            'Content-Disposition': ['unparseable private package-name']})
        self.assertEqual(self.run_mock(), 0)
        session.get.assert_called_once_with(M.URL, timeout=(5, 15), stream=True, allow_redirects=False,
                                             headers={'Accept-Encoding': 'identity'})
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once()
        self.assertEqual((self.stage / 'summary.html').read_bytes(), HTML)
        self.assertEqual(self.core.read('http.json')['disposition']['status'], 'REJECTED')
        result = self.core.read('outcome.json')
        self.assertEqual(result['status'], M.PASS)
        self.assertEqual(result['index']['regular_count'], 1)
        self.assertEqual(result['science_products_fetched'], 0)
        for p in self.stage.glob('*.json'):
            for secret in ('private', NAME, 'arbitrary'):
                self.assertNotIn(secret, p.read_text())
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with patch('requests.Session', side_effect=AssertionError('no replay network')), contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            self.core.run()

    def test_extra_member_retains_tar_but_never_creates_private_html(self):
        self.response(body=archive(extra=True))
        self.assertEqual(self.run_mock(), 1)
        self.assertTrue((self.stage / 'summary.tar').exists())
        self.assertFalse((self.stage / 'summary.html').exists())
        self.assertEqual(self.core.read('outcome.json')['worker_error_code'], 'STOP_TAR_MULTIPLE_FILES')
        with contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()

    def test_media_framing_before_body_no_package_autodetect(self):
        for headers, reason in (({'Content-Type': ['text/html']}, 'STOP_NOT_PLAIN_TAR'),
                ({'Content-Type': ['application/gzip']}, 'STOP_NOT_PLAIN_TAR'),
                ({'Content-Encoding': ['gzip']}, 'STOP_CONTENT_ENCODING'),
                ({'Content-Length': [str(M.CAP + 1)]}, 'STOP_CONTENT_LENGTH'),
                ({'Content-Length': ['1', '1']}, 'STOP_SAFE_HEADER_SCHEMA')):
            _session, response = self.response(headers=headers)
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.core.collect()
            self.assertEqual(response.raw.tell(), 0)
            if (self.stage / 'http.json').exists():
                (self.stage / 'http.json').unlink()

    def test_overflow_cap_plus_one_partial_no_member_copy_or_retry(self):
        session, response = self.response(body=b'x' * (M.CAP + 55))
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual((self.stage / 'summary.tar').stat().st_size, M.CAP)
        self.assertEqual(response.raw.tell(), M.CAP + 1)
        self.assertFalse((self.stage / 'summary.html').exists())
        self.assertFalse((self.stage / 'transport.json').exists())
        session.get.assert_called_once()

    def test_caught_partial_transfer_stop_preserves_safe_receipt(self):
        session, response = self.response()
        headers = response.raw.headers
        response.raw = MagicMock(headers=headers)
        response.raw.read.side_effect = [b'1234567', TimeoutError('private transport text')]
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual(self.core.read('worker-result.json')['body']['bytes'], 7)
        self.assertNotIn('private', (self.stage / 'worker-result.json').read_text())
        session.get.assert_called_once()
        with contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()

    def test_nonzero_cannot_promote_and_parent_never_recreates_missing_html(self):
        self.response()
        self.assertEqual(self.run_mock(code=124), 1)
        self.assertEqual(self.core.read('outcome.json')['worker_returncode'], 124)
        (self.stage / 'summary.html').unlink()
        with self.assertRaisesRegex(ValueError, 'STOP_PRIVATE_HTML_REPLAY'):
            self.core.assess(0)
        self.assertFalse((self.stage / 'summary.html').exists())

    def test_rehashed_inventory_mutation_fails_numerical_archive_replay(self):
        self.response()
        self.assertEqual(self.run_mock(), 0)
        worker = self.core.read('worker-result.json')
        worker['index']['inventory'][0]['payload_offset'] += 512
        (self.stage / 'worker-result.json').write_text(json.dumps(worker), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_INDEX_REPLAY'):
            self.core.assess(0)

    def test_prelaunch_failure_one_shot_and_terminal_reserve(self):
        self.core.binding = MagicMock(side_effect=ValueError('STOP_SYNTHETIC_BINDING'))
        self.assertEqual(self.run_mock(), 1)
        self.assertFalse((self.stage / 'worker-start.json').exists())
        with contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            self.core.run()
        self.assertEqual(self.core.read('outcome.json')['error_code'], 'STOP_SYNTHETIC_BINDING')

    def test_caught_html_write_failure_preserves_zero_byte_partial_and_replays(self):
        self.response()
        original_open = Path.open

        def opened(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            if path == self.stage / 'summary.html' and args == ('xb',):
                wrapper = MagicMock()
                wrapper.__enter__.return_value = SimpleNamespace(write=MagicMock(side_effect=OSError('private disk detail')))
                wrapper.__exit__.side_effect = lambda *_args: stream.close()
                return wrapper
            return stream

        with patch.object(Path, 'open', opened):
            self.assertEqual(self.run_mock(), 1)
        self.assertEqual((self.stage / 'summary.html').stat().st_size, 0)
        self.assertTrue(self.core.read('outcome.json')['assessment_completed'])
        self.assertEqual(self.core.read('worker-result.json')['error_type'], 'OSError')
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.core.replay()
        self.assertIn('PASS_OFFLINE_REPLAY STOP', output.getvalue())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})


if __name__ == '__main__':
    unittest.main()
