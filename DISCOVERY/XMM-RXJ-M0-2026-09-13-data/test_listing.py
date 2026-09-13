"""Synthetic anonymous HTTP/index/receipt tests; no live request."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location('rxj_m0_tests', Path(__file__).with_name('listing.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def page(href='PPS/', obs='0851180501'):
    title = f'Index of /FTP/xmm/data/rev0/{obs}'
    return f'<html><head><title>{title}</title></head><body><h1>{title}/</h1><a href="{href}">PPS/</a></body></html>\n'.encode()


class Raw(io.BytesIO):
    def read(self, size=-1, decode_content=False):
        assert not decode_content and 0 < size <= 8192
        return super().read(size)


class ListingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch.object(M, 'HERE', self.root))
        self.protocol = self.root / 'input-protocol.txt'
        # Keep protocol outside the strict stage directory.
        self.stage = self.root / 'stage'
        self.stage.mkdir()
        self.protocol.write_text('Synthetic metadata protocol.\n', encoding='utf-8')
        self.enterContext(patch.object(M, 'HERE', self.stage))
        self.enterContext(patch.object(M, 'PROTOCOL', self.protocol))
        self.enterContext(patch.object(M, 'binding', return_value={'synthetic_binding': True}))

    def response(self, body=None, status=200, headers=None, url=None):
        response = MagicMock(status_code=status, url=url or M.URL)
        response.headers = {'Content-Type': 'text/html; charset=UTF-8', 'Set-Cookie': 'private-cookie', **(headers or {})}
        response.raw = Raw(page() if body is None else body)
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
            result = M.worker()
            return (result if code is None else code), 'Synthetic output that is never persisted verbatim.'
        with patch.object(M, 'deadline_helper', return_value=SimpleNamespace(bounded_run=bounded)), contextlib.redirect_stdout(io.StringIO()):
            return M.run()

    def test_one_anonymous_get_exact_options_safe_headers_and_complete_parser(self):
        session, _response = self.response(headers={'Content-Length': str(len(page()))})
        M.collect()
        session.get.assert_called_once_with(M.URL, timeout=(5, 15), stream=True, allow_redirects=False,
                                             headers={'Accept-Encoding': 'identity'})
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once()
        self.assertNotIn('private-cookie', (self.stage / 'http.json').read_text())
        result = M.parse_index((self.stage / 'index.html').read_bytes())
        self.assertEqual(result['pps_url'], M.URL + 'PPS/')
        self.assertEqual(result['anchor_count'], 1)
        self.assertFalse(result['pps_listing_fetched'])

    def test_exact_cap_and_one_overflow_byte_no_retry(self):
        session, response = self.response(b'x' * (M.CAP + 500))
        with self.assertRaisesRegex(ValueError, 'STOP_BYTE_CAP'):
            M.collect()
        self.assertEqual((self.stage / 'index.html').stat().st_size, M.CAP)
        self.assertEqual(response.raw.tell(), M.CAP + 1)
        session.get.assert_called_once()

    def test_wrong_status_redirect_url_mime_encoding_stops_before_body(self):
        for kwargs, reason in (({'status': 404}, 'STOP_HTTP_STATUS'), ({'status': 302}, 'STOP_HTTP_STATUS'),
                 ({'url': M.URL + 'PPS/'}, 'STOP_HTTP_IDENTITY'),
                 ({'headers': {'Content-Type': 'image/fits'}}, 'STOP_NOT_HTML'),
                 ({'headers': {'Content-Encoding': 'gzip'}}, 'STOP_CONTENT_ENCODING')):
            with self.subTest(kwargs=kwargs):
                _session, response = self.response(**kwargs)
                with self.assertRaisesRegex(ValueError, reason):
                    M.collect()
                self.assertEqual(response.raw.tell(), 0)
                self.assertFalse((self.stage / 'index.html').exists())
                (self.stage / 'http.json').unlink()

    def test_declared_lengths_strict_and_actual_mismatch(self):
        for value, reason in (('1, 1', 'STOP_CONTENT_LENGTH'), ('+1', 'STOP_CONTENT_LENGTH'),
                              (' -1', 'STOP_CONTENT_LENGTH'), ('999', 'STOP_RESPONSE_LENGTH')):
            self.response(headers={'Content-Length': value})
            with self.assertRaisesRegex(ValueError, reason):
                M.collect()
            for name in ('http.json', 'index.html'):
                if (self.stage / name).exists():
                    (self.stage / name).unlink()

    def test_exact_same_observation_links_and_no_encoded_query_external_substitute(self):
        for href in ('PPS/', M.INDEX_PATH + 'PPS/', M.URL + 'PPS/'):
            self.assertEqual(M.parse_index(page(href))['pps_url'], M.URL + 'PPS/')
        for href in ('PPS/?x=1', 'PPS/#x', '%50PS/', '../0851180501/PPS/', '//evil.invalid/PPS/',
                     'https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/'):
            with self.subTest(href=href), self.assertRaisesRegex(ValueError, 'STOP_PPS_CHILD'):
                M.parse_index(page(href))

    def test_wrong_identity_missing_footer_duplicate_pps_and_ambiguous_anchor(self):
        cases = [(page(obs='0884250101'), 'STOP_INDEX_IDENTITY'),
                 (page().replace(b'</html>', b''), 'STOP_INDEX_FOOTER'),
                 (page().replace(b'</body>', b'<a href="PPS/">PPS</a></body>'), 'STOP_PPS_CHILD'),
                 (page().replace(b'href="PPS/"', b'href="PPS/" href="other"'), 'STOP_ANCHOR_SCHEMA'),
                 (page().replace(b'</title>', b'</title><title>extra</title>'), 'STOP_INDEX_STRUCTURE'),
                 (page().replace(b'PPS/</a>', b'\xff</a>'), 'STOP_INDEX_ENCODING')]
        for raw, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                M.parse_index(raw)

    def test_worker_parent_replay_one_shot_success_and_immutable_artifacts(self):
        session, _response = self.response()
        self.assertEqual(self.run_mock(), 0)
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with patch('requests.Session', side_effect=AssertionError('offline replay must not request')), contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', out.getvalue())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})
        session.get.assert_called_once()
        self.assertNotIn('Synthetic output', (self.stage / 'outcome.json').read_text())
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()

    def test_stopped_partial_body_and_worker_nonzero_cannot_promote_success(self):
        self.response(b'x' * (M.CAP + 1))
        self.assertEqual(self.run_mock(), 1)
        outcome = M.read('outcome.json')
        self.assertEqual(outcome['worker_error_code'], 'STOP_BYTE_CAP')
        self.assertIsNone(outcome['index'])
        self.assertEqual(M.read('worker-result.json')['body']['bytes'], M.CAP)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY STOP', out.getvalue())

    def test_nonzero_helper_code_with_valid_index_remains_stop(self):
        self.response()
        self.assertEqual(self.run_mock(code=124), 1)
        self.assertEqual(M.read('outcome.json')['worker_returncode'], 124)
        self.assertEqual(M.read('outcome.json')['status'], 'STOP')

    def test_prelaunch_failure_is_recorded_and_not_repeated(self):
        with patch.object(M, 'binding', side_effect=ValueError('STOP_SYNTHETIC_BINDING')):
            self.assertEqual(self.run_mock(), 1)
        self.assertEqual(M.read('outcome.json')['error_code'], 'STOP_SYNTHETIC_BINDING')
        self.assertFalse((self.stage / 'worker-start.json').exists())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_FAILURE_ARTIFACT_REPLAY', out.getvalue())
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()

    def test_extra_nested_artifacts_changed_body_and_private_receipt_fields_rejected(self):
        self.response()
        self.assertEqual(self.run_mock(), 0)
        (self.stage / 'other.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_ARTIFACT'):
            M.replay()
        (self.stage / 'other.json').unlink()
        (self.stage / 'nested').mkdir()
        with self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_ARTIFACT'):
            M.replay()
        (self.stage / 'nested').rmdir()
        worker = M.read('worker-result.json')
        worker['private_cookie'] = 'secret'
        (self.stage / 'worker-result.json').write_text(json.dumps(worker), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_WORKER_RECEIPT'):
            M.assess(0)

    def test_small_json_receipt_cap(self):
        with self.assertRaisesRegex(ValueError, 'STOP_RECEIPT_CAP'):
            M.save('http.json', {'oversize': 'x' * 65536})
        self.assertFalse((self.stage / 'http.json').exists())

    def test_stopped_http_receipt_rehashed_private_header_is_rejected(self):
        self.response(headers={'Content-Type': 'image/fits'})
        self.assertEqual(self.run_mock(), 1)
        receipt = M.read('http.json')
        receipt['headers']['Set-Cookie'] = 'private'
        (self.stage / 'http.json').write_text(json.dumps(receipt), encoding='utf-8')
        outcome = M.read('outcome.json')
        outcome['artifacts'] = M.artifacts()
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_HEADER_SCHEMA'):
            M.replay()

    def test_orphan_body_and_http_without_request_marker_rejected(self):
        M.save('http.json', {'url': M.URL, 'status': 404, 'headers': {}})
        with self.assertRaisesRegex(ValueError, 'STOP_ORPHAN_RESPONSE'):
            M.validate_response_artifacts()
        (self.stage / 'http.json').unlink()
        M.save('worker-start.json', {'url': M.URL, 'request_invocations': 1})
        (self.stage / 'index.html').write_bytes(page())
        with self.assertRaisesRegex(ValueError, 'STOP_ORPHAN_RESPONSE'):
            M.validate_response_artifacts()

    def test_socket_read_failure_keeps_partial_body_and_no_retry(self):
        session, response = self.response()
        first = page()[:31]
        response.raw = MagicMock()
        response.raw.read.side_effect = [first, TimeoutError('synthetic private transport detail')]
        self.assertEqual(self.run_mock(), 1)
        session.get.assert_called_once()
        worker = M.read('worker-result.json')
        self.assertEqual(worker['body']['bytes'], 31)
        self.assertEqual(worker['error_type'], 'TimeoutError')
        self.assertIsNone(worker['error_code'])
        self.assertNotIn('private', (self.stage / 'worker-result.json').read_text())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY STOP', out.getvalue())

    def test_boolean_returncode_and_success_count_cannot_alias_integer(self):
        self.response()
        self.assertEqual(self.run_mock(), 0)
        with self.assertRaisesRegex(ValueError, 'STOP_WORKER_RETURNCODE'):
            M.assess(False)
        outcome = M.read('outcome.json')
        outcome['products_fetched'] = False
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_OUTCOME_REPLAY'):
            M.replay()

    def test_parent_failure_and_output_metadata_are_safe_and_typed(self):
        with patch.object(M, 'binding', side_effect=ValueError('STOP_SYNTHETIC_BINDING')):
            self.assertEqual(self.run_mock(), 1)
        outcome = M.read('outcome.json')
        for key, bad in [('error_type', 'private error text'), ('error_code', 'private error text'),
                         ('output_bytes', False), ('output_sha256', 'private output')]:
            record = dict(outcome)
            record[key] = bad
            (self.stage / 'outcome.json').write_text(json.dumps(record), encoding='utf-8')
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.replay()


if __name__ == '__main__':
    unittest.main()
