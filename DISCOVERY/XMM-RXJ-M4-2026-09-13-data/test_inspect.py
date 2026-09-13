"""Synthetic full-size fixed HTML slices; never opens the retained archive."""

import contextlib
import importlib.util
import io
import json
import tarfile
import tempfile
import time
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('m4_test_module', Path(__file__).with_name('inspect.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
PAGE = (b'<meta charset="utf-8"><p>Observation ID: 0851180501</p><table><tr><th>Instrument</th>'
        b'<th>Exposure ID</th><th>Mode</th><th>Filter</th><th>Duration (s)</th></tr>'
        + b''.join(f'<tr><td>EPN</td><td>S{i:03d}</td><td>PrimeFullWindow</td><td>Thin1</td><td>10</td></tr>'.encode() for i in range(100))
        + b'</table>'
        b'<p>private observer email; coordinates and source flux not selected</p>')


class InspectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stage = root / 'stage'
        self.stage.mkdir()
        self.archive = root / 'synthetic.tar'
        self.protocol = root / 'protocol.md'
        self.protocol.write_text('Synthetic offline protocol\n', encoding='utf-8')
        plan = deepcopy(M.PLAN)
        raw = bytearray(M.ARCHIVE_BYTES)
        for p in plan:
            header = tarfile.TarInfo('0851180501/pps/P0851180501' + p['role'] + 'X000SUMMAR0000.HTM')
            header.size = p['bytes']
            header_raw = header.tobuf(format=tarfile.USTAR_FORMAT)
            raw[p['header']:p['offset']] = header_raw
            p['header_sha256'] = M.digest(header_raw)
            data = PAGE + b' ' * (p['bytes'] - len(PAGE))
            raw[p['offset']:p['offset'] + p['bytes']] = data
        raw[M.TAIL_OFFSET + 1024:] = b'x' * 7168
        self.archive.write_bytes(raw)
        for key, val in {'HERE': self.stage, 'PROTOCOL': self.protocol, 'ARCHIVE': self.archive,
                         'PLAN': plan, 'ARCHIVE_HASH': M.digest(raw), 'TAIL_HASH': M.digest(raw[M.TAIL_OFFSET:]),
                         'TRAILER_HASH': M.digest(raw[M.TAIL_OFFSET + 1024:]), 'PEAK': 0, 'DEADLINE': None}.items():
            self.enterContext(patch.object(M, key, val))
        self.original_binding = M.binding
        self.enterContext(patch.object(M, 'binding', return_value={'synthetic': True}))

    def run_mock(self, code=None):
        original_load = M.C.load_pinned
        def loader(name, path, expected):
            if name != 'm4_deadline':
                return original_load(name, path, expected)
            def bounded(args, seconds):
                self.assertEqual(seconds, 30)
                self.assertEqual(args[-2:], [str(M.SOURCE), '_worker'])
                result = M.worker()
                return result if code is None else code, 'private subprocess output'
            return SimpleNamespace(bounded_run=bounded)
        with patch.object(M.C, 'load_pinned', loader), contextlib.redirect_stdout(io.StringIO()):
            return M.run()

    def test_full_size_real_parser_worker_parent_replay_and_resource_budget(self):
        started = time.monotonic()
        self.assertEqual(self.run_mock(), 0)
        outcome = M.read('outcome.json')
        state = outcome['verification']
        self.assertEqual(state['selected_bytes'], 1033100)
        self.assertEqual(state['archive'], {'opaque_bytes': 1044480, 'header_bytes': 2048,
                         'tail_bytes': 8192, 'read_unknown': False, 'verified': True})
        self.assertEqual([s['bytes_read'] for s in state['slots']], [872917, 48229, 25265, 86689])
        self.assertTrue(all(s['status'] == 'OK' for s in state['slots']))
        self.assertLessEqual(outcome['peak_memory_bytes'], 268435456)
        self.assertLess(sum(p.stat().st_size for p in self.stage.glob('*.json')), 1048576)
        for p in self.stage.glob('*.json'):
            self.assertNotIn('private observer', p.read_text())
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY', output.getvalue())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})
        self.assertLess(time.monotonic() - started, 30)
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()

    def test_binding_is_metadata_only_no_archive_open(self):
        # Restore actual stage paths solely for source/metadata dependency binding.
        actual_here = Path(__file__).resolve().parent
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            if path.suffix == '.tar':
                raise AssertionError('binding cannot open archive')
            return original_open(path, *args, **kwargs)
        with patch.object(M, 'HERE', actual_here), patch.object(Path, 'open', guarded):
            result = self.original_binding(actual_here.parent / 'XMM-RXJ-M4-2026-09-13.md')
        self.assertEqual(result, json.loads(json.dumps(result)))

    def test_caught_parser_failure_continues_all_roles_and_counts_full_bytes(self):
        original_load = M.load_pinned
        def loader(path, expected, name):
            parser = original_load(path, expected, name)
            if name == 'm4_metadata_parser':
                original_parse = parser.parse_summary
                def parsed(raw, role, obsid):
                    if role == 'OB':
                        raise ValueError('STOP_SYNTHETIC_PARSE')
                    return original_parse(raw, role, obsid)
                parser.parse_summary = parsed
            return parser
        with patch.object(M, 'load_pinned', loader):
            self.assertEqual(self.run_mock(), 1)
            with contextlib.redirect_stdout(io.StringIO()):
                M.replay()
        state = M.read('worker-result.json')['state']
        self.assertEqual([s['status'] for s in state['slots']], ['OK', 'STOP', 'OK', 'OK'])
        self.assertEqual(state['slots'][1]['parse_state'], 'ATTEMPTED')
        self.assertEqual(state['selected_bytes'], 1033100)
        self.assertEqual(M.read('comparison.json')['roles_missing'], ['OB'])

    def test_parent_partial_read_failure_keeps_returned_bytes_and_replay_additional_state(self):
        self.assertEqual(self.run_mock(), 0)
        original_read = M.bounded_read
        def partial(stream, count, accounting, key):
            if key == 'bytes_read' and accounting.get('role') == 'OB':
                accounting[key] += 7
                raise ValueError('STOP_SHORT_READ')
            return original_read(stream, count, accounting, key)
        before = {p.name: p.read_bytes() for p in self.stage.iterdir()}
        with patch.object(M, 'bounded_read', partial), contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaisesRegex(ValueError, 'STOP_WORKER_REPLAY'):
            M.replay()
        receipt = json.loads(output.getvalue())['additional_verification_pass']
        self.assertEqual(receipt['slots'][1]['bytes_read'], 7)
        self.assertEqual(receipt['selected_bytes'], 872924)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.stage.iterdir()})

    def test_terminal_typed_status_and_nested_accounting_tamper(self):
        self.assertEqual(self.run_mock(), 0)
        original = M.read('outcome.json')
        for key, value in [('status', 'DISCOVERY'), ('assessment_completed', 1),
                           ('worker_returncode', False), ('error_code', 'private text'), ('output_bytes', True)]:
            outcome = deepcopy(original)
            outcome[key] = value
            (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.replay()
        outcome = deepcopy(original)
        outcome['verification']['selected_bytes'] = 0
        (self.stage / 'outcome.json').write_text(json.dumps(outcome), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STOP_SELECTED_ACCOUNTING'):
            M.replay()

    def test_worker_nonzero_never_promotes_success(self):
        self.assertEqual(self.run_mock(code=124), 1)
        self.assertEqual(M.read('worker-result.json')['state']['status'], M.PASS)
        self.assertEqual(M.read('outcome.json')['status'], 'STOP')
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()

    def test_archive_hash_failure_reads_no_selected_payload_and_no_slots(self):
        with patch.object(M, 'ARCHIVE_HASH', '0' * 64):
            self.assertEqual(self.run_mock(), 1)
        state = M.read('worker-result.json')['state']
        self.assertEqual(state['selected_bytes'], 0)
        self.assertEqual(state['archive']['header_bytes'], 0)
        self.assertTrue(all(s['status'] == 'NOT_ATTEMPTED' for s in state['slots']))

    def test_memory_deadline_and_terminal_reserve(self):
        with patch.object(M.C, 'peak_memory', return_value=M.MEMORY_CAP + 1):
            self.assertEqual(self.run_mock(), 1)
        self.assertEqual(M.read('outcome.json')['error_code'], 'STOP_PEAK_MEMORY')
        with contextlib.redirect_stdout(io.StringIO()):
            M.replay()
        with patch.object(M, 'PEAK', 0), patch.object(M.C, 'peak_memory', return_value=1000), patch.object(M, 'DEADLINE', -1), self.assertRaisesRegex(ValueError, 'STOP_TOTAL_DEADLINE'):
            M.checkpoint()

    def test_terminal_reserve_is_separate_and_large_ordinary_receipt_rejected(self):
        (self.stage / 'filler.json').write_bytes(b' ' * (M.JSON_CAP - M.RESERVE - 1))
        with self.assertRaisesRegex(ValueError, 'STOP_JSON_BUDGET'):
            M.save('worker-result.json', {'status': 'STOP'})
        M.save('outcome.json', {'status': 'STOP'}, terminal=True)
        self.assertTrue((self.stage / 'outcome.json').exists())
        with self.assertRaisesRegex(ValueError, 'STOP_JSON_BUDGET'):
            M.save('huge.json', {'text': 'x' * M.RECEIPT_CAP})

    def test_final_parent_serialization_peak_downgrades_without_losing_replay(self):
        original_save = M.save
        def saved(name, value, **kwargs):
            if name == 'outcome.json':
                with patch.object(M.C, 'peak_memory', return_value=M.MEMORY_CAP + 1):
                    return original_save(name, value, **kwargs)
            return original_save(name, value, **kwargs)
        with patch.object(M, 'save', saved):
            self.assertEqual(self.run_mock(), 1)
        self.assertEqual(M.read('outcome.json')['error_code'], 'STOP_PEAK_MEMORY')
        self.assertTrue(M.read('outcome.json')['assessment_completed'])
        with patch.object(M, 'PEAK', 0), contextlib.redirect_stdout(io.StringIO()) as output:
            M.replay()
        self.assertIn('PASS_OFFLINE_REPLAY STOP', output.getvalue())


if __name__ == '__main__':
    unittest.main()
