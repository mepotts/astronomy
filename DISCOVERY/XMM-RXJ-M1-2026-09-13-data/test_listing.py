"""Synthetic M1 composition and JSON tests; no requests or product reads."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

SPEC = importlib.util.spec_from_file_location('rxj_m1_tests', Path(__file__).with_name('listing.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def body(rows=None, reverse=False):
    metadata = [{'name': name, 'datatype': 'char', 'xtype': None, 'arraysize': '*',
                 'description': None, 'unit': None, 'ucd': None, 'utype': None}
                for name in ('obsid', 'filename')]
    rows = [['0851180501', 'P0851180501PNS003PIEVLI0000.FTZ']] if rows is None else rows
    if reverse:
        metadata.reverse()
        rows = [list(reversed(row)) for row in rows]
    return json.dumps({'metadata': metadata, 'data': rows}).encode()


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
        self.protocol = root / 'protocol.txt'
        self.protocol.write_text('Synthetic protocol\n', encoding='utf-8')
        self.core.HERE, self.core.PROTOCOL = self.stage, self.protocol
        self.core.binding = lambda _p: {'synthetic_binding': True}

    def response(self, raw=None, status=200, headers=None):
        response = MagicMock(status_code=status, url=M.URL)
        response.headers = {'Content-Type': 'application/json; charset=UTF-8',
                            'Set-Cookie': 'secret', **(headers or {})}
        response.raw = Raw(body() if raw is None else raw)
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
            return result if code is None else code, 'Never retained output text'
        with patch.object(self.core, 'deadline_helper', return_value=SimpleNamespace(bounded_run=bounded)), contextlib.redirect_stdout(io.StringIO()):
            return self.core.run()

    def test_query_binding_and_fresh_verified_module_without_cached_reads(self):
        with patch('importlib.machinery.SourceFileLoader.get_data', side_effect=AssertionError('unchecked reread')):
            a, b = M.load_core(), M.load_core()
        self.assertIsNot(a, b)
        a.CAP = 1
        self.assertEqual(b.CAP, 1048576)
        self.assertEqual(b.HERE, M.HERE)
        self.assertEqual(b.SOURCE, M.SOURCE)
        self.assertIn('response.body', b.ARTIFACTS)
        self.assertNotIn('index.html', b.ARTIFACTS)
        self.assertEqual(parse_qs(urlsplit(M.URL).query), {'REQUEST': ['doQuery'], 'LANG': ['ADQL'],
                         'FORMAT': ['json'], 'QUERY': [M.QUERY]})
        binding = b.binding(M.PROTOCOL)
        self.assertEqual(binding, json.loads(json.dumps(binding)))
        self.assertEqual(binding['adapter_literal_replacements'], 6)
        self.assertEqual(binding['receipt_bytes'], 65536)
        self.assertEqual(binding['aggregate_receipt_bytes'], 262144)
        self.assertIn(str(M.BASE), binding['dependencies'])

    def test_records_preserve_multiplicity_order_independence_and_empty_unknown(self):
        rows = [['0851180501', name] for name in ('a.FTZ', 'b.FTZ', 'a.FTZ', 'A.FTZ')]
        result = M.parse_records(body(rows))
        self.assertEqual(result, M.parse_records(body(list(reversed(rows)), reverse=True)))
        self.assertEqual((result['returned_rows'], result['unique_filenames'], result['duplicate_rows'],
                          result['duplicate_filename_groups'], result['casefold_ambiguous_groups']), (4, 3, 1, 1, 1))
        self.assertEqual(M.parse_records(body([]))['completeness'], 'UNKNOWN')
        self.assertEqual(M.parse_records(body([]))['returned_rows'], 0)

    def test_exact_schema_malformed_json_duplicate_keys_and_column_types(self):
        mutations = [b'{', b'\xff', b'{"metadata":[],"metadata":[],"data":[]}', body() + b'{}']
        for key, val in [('extra', None), ('data', {}), ('metadata', [])]:
            record = json.loads(body())
            record[key] = val
            mutations.append(json.dumps(record).encode())
        for key, val in [('datatype', 'long'), ('arraysize', 1), ('xtype', 'text'),
                         ('name', 'extra'), ('description', 'bad\ntext'), ('description', 'bad\u0085text')]:
            record = json.loads(body())
            record['metadata'][0][key] = val
            mutations.append(json.dumps(record).encode())
        for raw in mutations:
            with self.subTest(raw=raw[:20]), self.assertRaises(ValueError):
                M.parse_records(raw)

    def test_row_identity_no_coercion_or_paths_and_bounded_basename(self):
        for row in ([True, 'x'], [851180501, 'x'], ['0851180502', 'x'], ['0851180501', None],
                    ['0851180501', []], ['0851180501', 'x', 'extra']):
            with self.subTest(row=row), self.assertRaises(ValueError):
                M.parse_records(body([row]))
        for name in ('', '.', '..', '../x', 'x/y', 'x\\y', 'https:x', 'x?y', '%41', 'x\n', 'é', 'a' * 256):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'STOP_FILENAME_BASENAME'):
                M.parse_records(body([['0851180501', name]]))
        self.assertEqual(M.parse_records(body([['0851180501', 'a' * 255]]))['returned_rows'], 1)

    def test_one_anonymous_get_json_entity_and_unchanged_receipt_caps(self):
        session, _response = self.response(headers={'Content-Length': str(len(body()))})
        self.core.collect()
        session.get.assert_called_once_with(M.URL, timeout=(5, 15), stream=True, allow_redirects=False,
                                             headers={'Accept-Encoding': 'identity'})
        self.assertIs(session.trust_env, False)
        self.assertIsNone(session.auth)
        session.cookies.clear.assert_called_once()
        self.assertEqual((self.stage / 'response.body').read_bytes(), body())
        self.assertNotIn('secret', (self.stage / 'http.json').read_text())
        with self.assertRaisesRegex(ValueError, 'STOP_RECEIPT_CAP'):
            self.core.save('worker-result.json', {'huge': 'x' * 65536})

    def test_exact_raw_cap_plus_one_retains_partial_and_does_not_retry(self):
        session, response = self.response(b'x' * (M.CAP + 500))
        self.assertEqual(self.run_mock(), 1)
        self.assertEqual((self.stage / 'response.body').stat().st_size, M.CAP)
        self.assertEqual(response.raw.tell(), M.CAP + 1)
        session.get.assert_called_once()
        self.assertEqual(self.core.read('outcome.json')['worker_error_code'], 'STOP_BYTE_CAP')

    def test_status_mime_encoding_and_conflicting_length_before_body(self):
        cases = [(404, {}, 'STOP_HTTP_STATUS'), (302, {}, 'STOP_HTTP_STATUS'),
                 (200, {'Content-Type': 'text/html'}, 'STOP_NOT_JSON'),
                 (200, {'Content-Encoding': 'gzip'}, 'STOP_CONTENT_ENCODING'),
                 (200, {'Content-Length': '2, 2'}, 'STOP_CONTENT_LENGTH')]
        for status, headers, reason in cases:
            _session, response = self.response(status=status, headers=headers)
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.core.collect()
            self.assertEqual(response.raw.tell(), 0)
            (self.stage / 'http.json').unlink()

    def test_complete_worker_parent_readonly_replay_and_exclusive_attempt(self):
        session, _response = self.response()
        self.assertEqual(self.run_mock(), 0)
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with patch('requests.Session', side_effect=AssertionError('no replay network')), contextlib.redirect_stdout(io.StringIO()) as output:
            self.core.replay()
        self.assertIn(M.PASS, output.getvalue())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})
        session.get.assert_called_once()
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            self.core.run()

    def test_partial_timeout_preserves_safe_stop_and_raw_code(self):
        session, response = self.response()
        response.raw = MagicMock()
        response.raw.read.side_effect = [b'{"met', TimeoutError('private transport detail')]
        self.assertEqual(self.run_mock(code=124), 1)
        session.get.assert_called_once()
        self.assertEqual(self.core.read('worker-result.json')['body']['bytes'], 5)
        self.assertEqual(self.core.read('outcome.json')['worker_returncode'], 124)
        self.assertNotIn('private', (self.stage / 'worker-result.json').read_text())
        with contextlib.redirect_stdout(io.StringIO()):
            self.core.replay()

    def test_failure_receipt_private_header_mutation_rejected(self):
        self.response(status=404)
        self.assertEqual(self.run_mock(), 1)
        receipt = self.core.read('http.json')
        receipt['headers']['Set-Cookie'] = 'private'
        (self.stage / 'http.json').write_text(json.dumps(receipt), encoding='utf-8')
        outcome = self.core.read('outcome.json')
        outcome['artifacts'] = self.core.artifacts()
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_HEADER_SCHEMA'):
            self.core.replay()

    def test_canonical_counts_and_raw_body_mutations_rejected(self):
        self.response()
        self.assertEqual(self.run_mock(), 0)
        with self.assertRaisesRegex(ValueError, 'STOP_WORKER_RETURNCODE'):
            self.core.assess(False)
        worker = self.core.read('worker-result.json')
        worker['index']['returned_rows'] = True
        (self.stage / 'worker-result.json').write_text(json.dumps(worker), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_INDEX_REPLAY'):
            self.core.assess(0)
        (self.stage / 'unallowed.body').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_ARTIFACT'):
            self.core.artifacts()


if __name__ == '__main__':
    unittest.main()
