"""Synthetic private HTML acquisition; no live requests or science products."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location('m2_test_module', Path(__file__).with_name('listing.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
PAGE = b'<html><body>private contacts and sky coordinates; deliberately no closing tags'
NAME = 'P0851180501OBX000SUMMAR0000.HTM'  # Synthetic fixture, not observed identity.


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

    def response(self, body=PAGE, status=200, headers=None, url=None):
        response = MagicMock(status_code=status, url=M.URL if url is None else url)
        values = {'Content-Type': ['text/html; charset=UTF-8'], 'Set-Cookie': ['private-cookie'], **(headers or {})}
        response.raw = Raw(body)
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
            return result if code is None else code, 'private child output not saved'
        with patch.object(self.core, 'deadline_helper', return_value=SimpleNamespace(bounded_run=bounded)), contextlib.redirect_stdout(io.StringIO()):
            return self.core.run()

    def test_real_binding_isolated_loader_and_privacy_files(self):
        with patch('importlib.machinery.SourceFileLoader.get_data', side_effect=AssertionError('unchecked source')):
            a, b = M.load_core(), M.load_core()
        a.CAP = 1
        self.assertEqual(b.CAP, 262144)
        binding = b.binding(M.PROTOCOL)
        self.assertEqual(binding, json.loads(json.dumps(binding)))
        self.assertEqual(binding['adapter_counts'], [6, 1, 3])
        self.assertEqual(binding['terminal_reserve_bytes'], 65536)
        self.assertEqual((M.HERE / '.gitignore').read_text().strip(), '/summary.html')
        self.assertIn('summary.html', b.ARTIFACTS)
        self.assertIn('transport.json', b.ARTIFACTS)

    def test_success_anonymous_unadjudicated_eof_no_footer_and_private_body(self):
        session, _response = self.response(headers={'Content-Length': [str(len(PAGE))]})
        self.assertEqual(self.run_mock(), 0)
        session.get.assert_called_once_with(M.URL, timeout=(5, 15), stream=True, allow_redirects=False,
                                             headers={'Accept-Encoding': 'identity'})
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once()
        self.assertEqual(self.core.read('transport.json'), {'eof': True, 'bytes': len(PAGE)})
        self.assertEqual(self.core.read('outcome.json')['status'], M.PASS)
        self.assertEqual(self.core.read('outcome.json')['science_products_fetched'], 0)
        self.assertEqual((self.stage / 'summary.html').read_bytes(), PAGE)
        for p in self.stage.glob('*.json'):
            self.assertNotIn('private', p.read_text())
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with patch('requests.Session', side_effect=AssertionError('no replay request')), contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            self.core.run()

    def test_disposition_optional_and_exact_positions_not_invented_exposure(self):
        self.assertEqual(M.disposition([])['status'], 'ABSENT')
        self.assertEqual(M.disposition(['inline'])['status'], 'NO_FILENAME')
        for name in (NAME, 'P0851180501M2S123SUMMAR8000.HTM'):
            result = M.disposition([f'attachment; filename="{name}"'])
            self.assertEqual(result['status'], 'MATCH')
            self.assertNotIn(name, json.dumps(result))
        for value in ('attachment; filename="archive.tar.gz"', 'inline; filename="../x.HTM"',
                      f'inline; filename="{NAME}"; filename="{NAME}"', f"inline; filename*=UTF-8''{NAME}",
                      'inline; filename="P0884250101OBX000SUMMAR0000.HTM"', 'x' * 2049, 'inline\r\nprivate'):
            self.assertEqual(M.disposition([value])['status'], 'REJECTED')
        self.assertEqual(M.disposition(['inline', 'inline'])['status'], 'REJECTED')

    def test_status_packaging_encoding_length_and_disposition_stop_before_body(self):
        cases = [(404, {}, 'STOP_HTTP_STATUS'), (302, {}, 'STOP_HTTP_STATUS'),
                 (200, {'Content-Type': ['application/gzip']}, 'STOP_NOT_HTML'),
                 (200, {'Content-Encoding': ['gzip']}, 'STOP_CONTENT_ENCODING'),
                 (200, {'Content-Length': ['0']}, 'STOP_CONTENT_LENGTH'),
                 (200, {'Content-Length': [str(M.CAP + 1)]}, 'STOP_CONTENT_LENGTH'),
                 (200, {'Content-Disposition': ['inline; filename="archive.tar"']}, 'STOP_DISPOSITION')]
        for status, headers, reason in cases:
            _session, response = self.response(status=status, headers=headers)
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.core.collect()
            self.assertEqual(response.raw.tell(), 0)
            self.assertFalse((self.stage / 'summary.html').exists())
            (self.stage / 'http.json').unlink()

    def test_duplicate_unsafe_headers_never_persisted_and_url_not_echoed(self):
        for headers in ({'Content-Length': ['1', '1']}, {'ETag': ['private\r\ntext']}, {'Date': ['a' * 1025]}):
            _session, response = self.response(headers=headers)
            with self.assertRaisesRegex(ValueError, 'STOP_SAFE_HEADER_SCHEMA'):
                self.core.collect()
            self.assertFalse((self.stage / 'http.json').exists())
            self.assertEqual(response.raw.tell(), 0)
        self.response(url='https://private.invalid/secret')
        self.assertEqual(self.run_mock(), 1)
        self.assertNotIn('private', (self.stage / 'http.json').read_text())
        self.assertEqual(self.core.read('outcome.json')['worker_error_code'], 'STOP_HTTP_IDENTITY')

    def test_cap_plus_one_retained_without_eof(self):
        session, response = self.response(b'x' * (M.CAP + 900))
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual(response.raw.tell(), M.CAP + 1)
        self.assertEqual((self.stage / 'summary.html').stat().st_size, M.CAP)
        self.assertFalse((self.stage / 'transport.json').exists())
        session.get.assert_called_once()
        with contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()

    def test_caught_partial_read_error_safe_without_eof(self):
        session, response = self.response()
        original_headers = response.raw.headers
        response.raw = MagicMock(headers=original_headers)
        response.raw.read.side_effect = [PAGE[:12], TimeoutError('private exception payload')]
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual(self.core.read('worker-result.json')['body']['bytes'], 12)
        self.assertFalse((self.stage / 'transport.json').exists())
        self.assertNotIn('private', (self.stage / 'worker-result.json').read_text())
        session.get.assert_called_once()

    def test_eof_length_mismatch_is_not_success_and_nonzero_cannot_promote(self):
        self.response(headers={'Content-Length': [str(len(PAGE) + 1)]})
        self.assertEqual(self.run_mock(), 1)
        self.assertTrue(self.core.read('transport.json')['eof'])
        self.assertEqual(self.core.read('outcome.json')['worker_error_code'], 'STOP_RESPONSE_LENGTH')

    def test_valid_worker_with_raw_124_remains_stop(self):
        self.response()
        self.assertEqual(self.run_mock(code=124), 1)
        self.assertEqual(self.core.read('worker-result.json')['status'], M.PASS)
        self.assertEqual(self.core.read('outcome.json')['worker_returncode'], 124)

    def test_terminal_reserve_and_individual_json_limit(self):
        # Budget only: fill ordinary JSON space with synthetic bytes, no replay.
        (self.stage / 'filler.json').write_bytes(b' ' * (M.JSON_CAP - M.RESERVE - 10))
        with self.assertRaisesRegex(ValueError, 'STOP_RECEIPT_CAP'):
            self.core.save('worker-result.json', {'status': 'STOP'})
        self.core.save('outcome.json', {'status': 'STOP'})
        self.assertTrue((self.stage / 'outcome.json').exists())
        with self.assertRaisesRegex(ValueError, 'STOP_RECEIPT_CAP'):
            self.core.save('big.json', {'value': 'x' * 65536})

    def test_typed_eof_and_private_header_mutations_fail_replay(self):
        self.response()
        self.assertEqual(self.run_mock(), 0)
        transport = self.core.read('transport.json')
        transport['eof'] = 1
        (self.stage / 'transport.json').write_text(json.dumps(transport), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_TRANSPORT_RECEIPT'):
            self.core.assess(0)
        transport['eof'] = True
        (self.stage / 'transport.json').write_text(json.dumps(transport), encoding='utf-8')
        http = self.core.read('http.json')
        http['headers']['Content-Disposition'] = ['private']
        (self.stage / 'http.json').write_text(json.dumps(http), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_SAFE_HEADER_SCHEMA'):
            self.core.assess(0)


if __name__ == '__main__':
    unittest.main()
