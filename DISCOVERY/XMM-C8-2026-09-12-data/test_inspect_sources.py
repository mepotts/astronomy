"""Synthetic C8 integration only; all real products and network are forbidden."""

import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from astropy.io.fits import Header

SPEC = importlib.util.spec_from_file_location('c8_tested', Path(__file__).with_name('inspect_sources.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture_report(items):
    primary = Header()
    for key, value in {'SIMPLE': True, 'BITPIX': 8, 'NAXIS': 0, 'OBS_ID': '0884250101',
                       'INSTRUME': 'EPIC', 'RADECSYS': 'FK5', 'EQUINOX': 2000.}.items():
        primary[key] = value
    h = Header(items)
    h['POSCOROK'], h['REFCAT'] = True, 'USNO'
    return {'file_bytes': 250560, 'hdu_count': 2, 'parser_warning_categories': [], 'hdus': [
        {'extname': 'PRIMARY', 'header_offset': 0, 'header_bytes': 8640, 'data_bytes': 0,
         'cards': [primary.tostring()]},
        {'extname': 'SRCLIST', 'header_offset': 8640, 'header_bytes': 69120, 'data_offset': 77760,
         'data_bytes': 170781, 'data_span_padded': 172800, 'cards': [h.tostring()]}]}


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.here = Path(self.temp.name)
        self.product = self.here / 'synthetic.bin'
        self.headers = self.here / 'synthetic-headers.txt'
        self.reader = M.reader()
        with patch.dict('sys.modules', {'xmm_source_rows': self.reader}):
            self.fixtures = M.C.load_pinned('c8_synthetic_reader_fixtures', M.READER_TEST, M.READER_TEST_HASH)
        self.report = fixture_report(self.fixtures.header())
        self.raw, _expected = self.fixtures.fixture()
        self.product.write_bytes(self.raw)
        self.headers.write_text(json.dumps(self.report), encoding='utf-8')
        patches = [patch.object(M, 'HERE', self.here), patch.object(M.C, 'HERE', self.here),
                   patch.object(M, 'PRODUCT', self.product), patch.object(M, 'HEADER_PATH', self.headers),
                   patch.object(M, 'reader', return_value=self.reader), patch.object(M.C, 'checkpoint'),
                   patch.object(M.C, 'peak_memory', return_value=100), patch.object(M.C, 'PEAK', 0),
                   patch.object(M.C, 'DEADLINE', None), patch('requests.Session', side_effect=AssertionError('NO_NETWORK')),
                   patch.object(M.C, 'worker', side_effect=AssertionError('NO_OLD_WORKER')),
                   patch.object(M.C, 'head_plan', side_effect=AssertionError('NO_OLD_PLAN')),
                   patch.object(M.C, 'replay', side_effect=AssertionError('NO_OLD_REPLAY'))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.plan = {'table': M.table_schema(self.report)}
        self.start = {'manifest': self.plan}

    def start_worker(self):
        M.C.save('run-start.json', self.start)
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'):
            return M.worker()

    def test_real_selected_reader_measure_unbuffered_and_private(self):
        accounting, opened = {}, []
        original = Path.open

        def tracked(path, *args, **kwargs):
            if path == self.product:
                opened.append((args, kwargs))
            return original(path, *args, **kwargs)

        with patch.object(Path, 'open', tracked):
            summary = M.measure(self.plan, accounting)
        self.assertEqual(opened, [(('rb',), {'buffering': 0})])
        M.valid_accounting(accounting, complete=True)
        self.assertEqual(accounting['read_bytes'], 7852)
        self.assertEqual(accounting['spans_decoded'], 755)
        self.assertEqual(summary['rows'], 151)
        self.assertEqual(summary['status'], M.PASS)
        self.assertNotIn('current_row', accounting)
        self.assertNotIn('current_span', accounting)
        self.assertEqual(summary, json.loads(json.dumps(summary, allow_nan=False)))

    def test_short_selected_span_preserves_read_decode_and_rows(self):
        self.product.write_bytes(self.raw[:77760 + 1131 + 596 + 3])
        accounting = {}
        with self.assertRaisesRegex(ValueError, 'STOP_TRUNCATED_SELECTED_SPAN'):
            M.measure(self.plan, accounting)
        self.assertEqual((accounting['read_bytes'], accounting['decoded_bytes'], accounting['rows_completed']), (79, 76, 1))
        M.valid_accounting(accounting)

    def test_missing_returned_rows_stops_before_core(self):
        original = self.reader.read_selected

        def missing(*args, **kwargs):
            result = original(*args, **kwargs)
            result['RA'] = result['RA'][:-1]
            return result

        accounting = {}
        with patch.object(self.reader, 'read_selected', side_effect=missing), self.assertRaisesRegex(ValueError, 'STOP_MISSING_SOURCE_ROWS'):
            M.measure(self.plan, accounting)
        M.valid_accounting(accounting, complete=True)

    def test_primary_identity_and_table_layout_schema_mutations(self):
        for key, value in [('RADECSYS', 'ICRS'), ('RADESYS', 'ICRS'), ('NAXIS', 1), ('OBS_ID', 'wrong')]:
            report = copy.deepcopy(self.report)
            h = M.header(report['hdus'][0])
            h[key] = value
            report['hdus'][0]['cards'] = [h.tostring()]
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.table_schema(report)
        for key, value in [('NAXIS2', 150), ('TUNIT6', 'rad'), ('TNULL1', -1), ('POSCOROK', False)]:
            report = copy.deepcopy(self.report)
            h = M.header(report['hdus'][1])
            h[key] = value
            report['hdus'][1]['cards'] = [h.tostring()]
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.table_schema(report)
        self.assertEqual(self.plan, json.loads(json.dumps(self.plan)))

    def test_duplicate_header_and_safe_error_text(self):
        h = Header()
        h.append(('OBS_ID', 'secret'))
        h.append(('OBS_ID', 'secret'))
        with self.assertRaisesRegex(ValueError, 'STOP_HEADER_AMBIGUITY'):
            M.header({'cards': [h.tostring()]})
        self.assertEqual(M.failure(ValueError('private coordinate')), {'error_type': 'ValueError', 'error_code': None})

    def test_worker_assess_and_exact_replay_success(self):
        self.assertEqual(self.start_worker(), 0)
        validation = M.validation_state()
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'):
            outcome = M.assess(0, validation)
        self.assertEqual(outcome['status'], M.PASS)
        self.assertEqual(validation['status'], 'COMPLETED')
        M.valid_accounting(validation['accounting'], complete=True)
        outcome.update(assessment_completed=True, parent_validation=validation,
                       artifacts=M.artifacts(('outcome.json',)), source_sha256=M.C.sha(M.SOURCE))
        M.C.save('outcome.json', outcome, terminal=True, peak_key='parent_peak_memory_bytes')
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'), io.StringIO() as output, patch('sys.stdout', output):
            M.replay()
            self.assertIn('PASS_OFFLINE_REPLAY', output.getvalue())

    def test_nonzero_worker_cannot_be_promoted(self):
        self.assertEqual(self.start_worker(), 0)
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'):
            result = M.assess(124, M.validation_state())
        self.assertEqual(result['status'], 'STOP')
        self.assertEqual(result['worker_returncode'], 124)

    def test_caught_parent_partial_read_persists_and_failure_replay_no_reads(self):
        original_load = M.C.load_pinned

        def launch(_args, _seconds):
            with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'):
                self.assertEqual(M.worker(), 0)
            self.product.write_bytes(self.raw[:77760 + 1131 + 596 + 3])
            return 0, 'not persisted'

        def load(name, path, digest):
            return SimpleNamespace(bounded_run=launch) if name == 'c8_deadline' else original_load(name, path, digest)

        protocol = self.here / 'prospective.txt'
        protocol.write_text('synthetic protocol', encoding='utf-8')
        with patch.object(M, 'PROTOCOL', protocol), patch.object(M, 'binding', return_value=self.start), \
                patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'), patch.object(M.C, 'load_pinned', side_effect=load):
            self.assertEqual(M.run(), 1)
        outcome = M.C.read('outcome.json')
        self.assertFalse(outcome['assessment_completed'])
        self.assertEqual(outcome['parent_validation']['status'], 'FAILED')
        self.assertEqual(outcome['parent_validation']['accounting']['read_bytes'], 79)
        self.assertEqual(outcome['parent_validation']['accounting']['decoded_bytes'], 76)
        with patch.object(M, 'measure', side_effect=AssertionError('NO_REREAD')):
            M.replay()

    def test_orphan_exclusivity_and_malformed_table_fallback(self):
        (self.here / 'table-start.json').write_bytes(b'{')
        with self.assertRaisesRegex(ValueError, 'STOP_ALREADY_ATTEMPTED'):
            M.run()
        self.assertEqual(M.fallback(), [{'table': 1, 'status': 'UNVERIFIED_ATTEMPT', 'accounting': None}])

    def test_worker_caught_failure_has_safe_partial_table_receipt(self):
        self.product.write_bytes(self.raw[:77760 + 2])
        self.assertEqual(self.start_worker(), 1)
        record = M.C.read('table-result.json')
        self.assertEqual(record['status'], 'STOP')
        self.assertEqual(record['accounting']['read_bytes'], 2)
        self.assertEqual(record['accounting']['decoded_bytes'], 0)
        self.assertEqual(record['error_code'], 'STOP_TRUNCATED_SELECTED_SPAN')
        self.assertEqual(M.C.read('worker-result.json')['status'], 'STOP')

    def test_centres_ast_equivalence_without_prior_module_execution(self):
        M.verify_centres_definition()

    def test_unexpected_and_nested_json_rejected_before_measure(self):
        for relative in ['extra.json', 'nested/table-result.json']:
            with self.subTest(relative=relative):
                path = self.here / relative
                path.parent.mkdir(exist_ok=True)
                path.write_text('{}', encoding='utf-8')
                try:
                    with patch.object(M, 'measure', side_effect=AssertionError('NO_READ')), \
                            self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_STAGE_JSON'):
                        M.run()
                    with self.assertRaisesRegex(ValueError, 'STOP_UNEXPECTED_STAGE_JSON'):
                        M.artifacts()
                finally:
                    path.unlink()

    def test_impossible_failure_accounting_and_summary_denominators(self):
        accounting = {}
        summary = M.measure(self.plan, accounting)
        bad = {**accounting, 'status': 'FAILED', 'phase': 'READ_VALIDATING', 'spans_decoded': 0,
               'rows_completed': 0, 'read_bytes': 0, 'decoded_bytes': 0}
        with self.assertRaisesRegex(ValueError, 'STOP_SELECTED_ACCOUNTING'):
            M.valid_accounting(bad)
        for key, value in [('rows', 150), ('status', 'CLEAN'), ('apertures', summary['apertures'][:-1]),
                           ('annuli', summary['annuli'][::-1])]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'STOP_SUMMARY_DENOMINATOR'):
                M.validate_summary({**summary, key: value})

    def test_replay_failure_prints_additional_pass_even_after_measurement(self):
        self.assertEqual(self.start_worker(), 0)
        validation = M.validation_state()
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'):
            outcome = M.assess(0, validation)
        outcome.update(assessment_completed=True, parent_validation=validation,
                       artifacts=M.artifacts(('outcome.json',)), source_sha256=M.C.sha(M.SOURCE),
                       source_coordinates_or_ids_persisted=True)  # Unbound outcome tamper, caught after reread.
        M.C.save('outcome.json', outcome, terminal=True, peak_key='parent_peak_memory_bytes')
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'), io.StringIO() as output, patch('sys.stdout', output):
            with self.assertRaisesRegex(ValueError, 'STOP_OUTCOME_REPLAY'):
                M.replay()
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt['replay_status'], 'FAILED')
            self.assertEqual(receipt['additional_selected_pass']['accounting']['decoded_bytes'], 7852)
        self.product.write_bytes(self.raw[:77760 + 1131 + 596 + 3])
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'), io.StringIO() as output, patch('sys.stdout', output):
            with self.assertRaisesRegex(ValueError, 'STOP_TRUNCATED_SELECTED_SPAN'):
                M.replay()
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt['additional_selected_pass']['status'], 'FAILED')
            self.assertEqual(receipt['additional_selected_pass']['accounting']['read_bytes'], 79)

    def test_parent_late_peak_stop_is_preserved_on_replay(self):
        self.assertEqual(self.start_worker(), 0)
        validation = M.validation_state()
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'):
            outcome = M.assess(0, validation)
        outcome.update(assessment_completed=True, parent_validation=validation,
                       artifacts=M.artifacts(('outcome.json',)), source_sha256=M.C.sha(M.SOURCE))
        with patch.object(M.C, 'peak_memory', return_value=M.C.MEMORY_CAP + 1):
            M.C.save('outcome.json', outcome, terminal=True, peak_key='parent_peak_memory_bytes')
        self.assertEqual(outcome['status'], 'STOP')
        with patch.object(M, 'verify_binding'), patch.object(M, 'verify_product'), io.StringIO() as output, patch('sys.stdout', output):
            M.replay()
            self.assertEqual(json.loads(output.getvalue())['status'], 'STOP')

    def test_failure_after_complete_reader_preserves_complete_counters(self):
        accounting = {}
        core = M.C.load_pinned('c8_test_core', M.CORE_PATH, M.CORE_HASH)
        with patch.object(core, 'summarize', side_effect=ValueError('private coordinate string')), \
                patch.object(M.C, 'load_pinned', return_value=core), self.assertRaises(ValueError):
            M.measure(self.plan, accounting)
        M.valid_accounting(accounting, complete=True)
        self.assertEqual(accounting['rows_completed'], 151)


if __name__ == '__main__':
    unittest.main()
