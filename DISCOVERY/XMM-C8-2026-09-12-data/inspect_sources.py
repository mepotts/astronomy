"""C8: one local selected source-list pass and aggregate geometry only.

No prior acquisition plan/replay or network function is called. Product hashing
and structural header replay are separate from selected scientific byte counts.
"""

import ast
import hashlib
import importlib.machinery
import importlib.util
import json
import logging
import math
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import FK5, SkyCoord
from astropy.io.fits import Header

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-C8-2026-09-12.md'
C1_PATH = HERE.parent / 'XMM-C1-2026-09-12-data/acquire.py'
C1_HASH = '13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5'
PRIOR = C1_PATH.parent
OUTCOME_HASH = 'c8f746092ab9203dc0e2be4e78e93e13037b10656b733132bb977331ba5168bc'
RECEIPT_HASH = '10fd4dd339100c29fa08af477dbdc1622295b3f6aa24dfb9e4750a33c3adb677'
HEADER_PATH = PRIOR / 'headers/slot-4-headers.json'
HEADER_HASH = 'd19ede1f11156b75954e4fa5de3d29c7ce0222bcfa816dc64ed88d7be6c78c3e'
PRODUCT = PRIOR / 'products/P0884250101EPX000OBSMLI0000.fits'
PRODUCT_HASH = '7ee2302307c5336d2e4699c4997e711eda197483f6bec9a62598c0490bcf7677'
CORE_PATH = HERE.parent / 'xmm_source_geometry.py'
CORE_HASH = '33f483e69dd78ad64a6b015ecfa02a1e49bf5e2aa8da83f7869f560ecb0059be'
CORE_TEST = HERE.parent / 'test_xmm_source_geometry.py'
CORE_TEST_HASH = 'c013dbc2c7d0599b07b7fb7b76094d26f7ffbc1f7567085d941ed63ae80bf68d'
READER_PATH = HERE.parent / 'xmm_source_rows.py'
READER_HASH = '33acfedec1328cac1517abc703ee9644c653330648630edb8d96b6235562a927'
READER_TEST = HERE.parent / 'test_xmm_source_rows.py'
READER_TEST_HASH = '4fd4b13b5698c2d40a476d390b780b47cc8e899c2ad6fe39024d6cff9f0ef272'
C5_PATH = HERE.parent / 'XMM-C5-2026-09-12-data/inspect_maps.py'
C5_HASH = '5e7af10b0d8ac5ea8272229efb8a618a392c92d802e6efc401e6b3a54cb5a05b'
DEFINITION = HERE.parent / 'XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md'
DEFINITION_HASH = '7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e'
SECONDS, PAYLOAD = 60, 7852
PASS = 'SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY'
LOGGER = logging.getLogger(__name__)
FILES = ('protocol.snapshot.md', 'run-start.json', 'worker-start.json', 'worker-result.json',
         'table-start.json', 'table-result.json', 'outcome.json')


def load_helpers():
    raw = C1_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != C1_HASH:
        raise ValueError('STOP_HELPER_SOURCE_HASH')

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(C1_PATH), 'exec')

    spec = importlib.util.spec_from_file_location('c8_helpers', C1_PATH,
                                                loader=VerifiedLoader('c8_helpers', str(C1_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_helpers()
C.HERE, C.SECONDS = HERE, SECONDS
C.MEMORY_CAP, C.JSON_CAP, C.RESERVE = 268435456, 1048576, 65536
C.EXPECTED, C.EXPANDED_FILE_CAP, C.EXPANDED_TOTAL_CAP = (), 0, 0


def failure(error):
    """C0d's safe named STOP convention; never persist arbitrary exception text."""
    text = str(error)
    return {'error_type': type(error).__name__, 'error_code': text if isinstance(error, ValueError)
            and re.fullmatch(r'STOP_[A-Z0-9_]+', text) else None}


def centres():
    """Published ICRS convention and fixed spherical offsets; never persisted."""
    base = SkyCoord("23h54m40.76s", "-37d30m19.4s", frame="icrs")
    values = [base] + [base.directional_offset_by(angle * u.deg, 120 * u.arcsec) for angle in (0, 90, 180, 270)]
    return [tuple(float(v) for v in (c.ra.deg, c.dec.deg)) for c in
            [position.transform_to(FK5(equinox="J2000")) for position in values]]


def verify_centres_definition():
    functions = []
    for path in (C5_PATH, SOURCE):
        tree = ast.parse(path.read_bytes())
        found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'centres']
        if len(found) != 1:
            raise ValueError('STOP_CENTRE_DEFINITION')
        functions.append(ast.dump(found[0], include_attributes=False))
    if functions[0] != functions[1]:
        raise ValueError('STOP_CENTRE_DEFINITION')


def header(record):
    with warnings.catch_warnings(record=True) as caught:
        value = Header.fromstring(''.join(record['cards']))
        keys = [k for k in value if k not in ('', 'HISTORY', 'COMMENT')]
        if caught or len(keys) != len(set(keys)):
            raise ValueError('STOP_HEADER_AMBIGUITY')
    return value


def reader():
    return C.load_pinned('c8_selected_reader', READER_PATH, READER_HASH)


def table_schema(report):
    if (report.get('file_bytes') != 250560 or report.get('hdu_count') != 2
            or len(report.get('hdus', [])) != 2 or report.get('parser_warning_categories')):
        raise ValueError('STOP_PRODUCT_LAYOUT')
    primary, table = report['hdus']
    p, h = header(primary), header(table)
    if (primary['extname'] != 'PRIMARY' or table['extname'] != 'SRCLIST'
            or (p.get('OBS_ID'), p.get('INSTRUME'), p.get('RADECSYS'), p.get('EQUINOX'))
            != ('0884250101', 'EPIC', 'FK5', 2000.0)
            or p.get('RADESYS', 'FK5') != 'FK5'
            or h.get('POSCOROK') is not True or h.get('REFCAT') != 'USNO'):
        raise ValueError('STOP_SOURCE_IDENTITY_FRAME')
    if (p.get('BITPIX'), p.get('NAXIS'), primary.get('header_offset'), primary.get('header_bytes'),
            primary.get('data_bytes'), table.get('header_offset'), table.get('header_bytes'),
            table.get('data_offset'), table.get('data_bytes'), table.get('data_span_padded')) != (
            8, 0, 0, 8640, 0, 8640, 69120, 77760, 170781, 172800):
        raise ValueError('STOP_SOURCE_TABLE_SPAN')
    # Reader independently derives every TFORM width and validates the fixed schema.
    return reader().build_schema([(card.keyword, card.value) for card in h.cards], table['data_offset']).metadata()


def manifest():
    for path, digest in ((PRIOR / 'outcome.json', OUTCOME_HASH), (PRIOR / 'slot-4-result.json', RECEIPT_HASH),
                         (HEADER_PATH, HEADER_HASH)):
        if C.sha(path) != digest:
            raise ValueError('STOP_PRIOR_RECEIPT_HASH')
    prior = json.loads((PRIOR / 'outcome.json').read_bytes())
    receipt = json.loads((PRIOR / 'slot-4-result.json').read_bytes())
    if (prior['status'] != C.PASS or prior['worker_returncode'] != 0
            or prior['artifacts'].get('headers/slot-4-headers.json') != HEADER_HASH
            or prior['artifacts'].get('products/' + PRODUCT.name) != PRODUCT_HASH
            or prior['artifacts'].get('slot-4-result.json') != RECEIPT_HASH
            or receipt['status'] != 'OK' or receipt['slot']['slot'] != 4
            or receipt['slot']['filename'] != 'P0884250101EPX000OBSMLI0000.FTZ'
            or receipt['expanded'] != {'bytes': 250560, 'sha256': PRODUCT_HASH}
            or receipt['headers_sha256'] != HEADER_HASH or receipt['gzip_crc_eof_verified'] is not True):
        raise ValueError('STOP_PRIOR_CLOSURE')
    return {'table': table_schema(json.loads(HEADER_PATH.read_bytes())),
            'product_sha256': PRODUCT_HASH, 'header_sha256': HEADER_HASH,
            'prior_outcome_sha256': OUTCOME_HASH, 'prior_slot_receipt_sha256': RECEIPT_HASH,
            'centre_convention': 'published_ICRS_offsets_then_FK5_J2000',
            'labels': ['published', 'north120', 'east120', 'south120', 'west120']}


def binding(protocol):
    import astropy

    paths = {C1_PATH: C1_HASH, CORE_PATH: CORE_HASH, CORE_TEST: CORE_TEST_HASH,
             C1_PATH.with_name('test_acquire.py'): 'd751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c',
             READER_PATH: READER_HASH, READER_TEST: READER_TEST_HASH, C5_PATH: C5_HASH,
             DEFINITION: DEFINITION_HASH, C.HELPER: C.HELPER_HASH,
             C.STRUCTURE_PATH: C.STRUCTURE_HASH, C.STRUCTURE_TEST: C.STRUCTURE_TEST_HASH,
             C.STRUCTURE_REVIEW: C.STRUCTURE_REVIEW_HASH}
    if any(C.sha(path) != digest for path, digest in paths.items()):
        raise ValueError('STOP_DEPENDENCY_HASH')
    verify_centres_definition()
    return {'manifest': manifest(), 'dependencies': {str(p): h for p, h in paths.items()},
            'source_sha256': C.sha(SOURCE), 'tests_sha256': C.sha(HERE / 'test_inspect_sources.py'),
            'protocol_sha256': C.sha(protocol), 'output_directory': str(HERE),
            'runtime': {'python': sys.version, 'executable': str(Path(sys.executable).resolve()),
                        'numpy': np.__version__, 'astropy': astropy.__version__},
            'caps': {'seconds': SECONDS, 'memory': C.MEMORY_CAP, 'json': C.JSON_CAP, 'reserve': C.RESERVE,
                     'selected_bytes_per_pass': PAYLOAD, 'source_rows': 151, 'span_reads': 755}}


def verify_binding():
    if C.read('run-start.json') != binding(HERE / 'protocol.snapshot.md'):
        raise ValueError('STOP_BINDING')


def verify_product():
    if PRODUCT.stat().st_size != 250560 or C.sha(PRODUCT) != PRODUCT_HASH:
        raise ValueError('STOP_PRODUCT_HASH')
    structural = C.load_pinned('c8_structure', C.STRUCTURE_PATH, C.STRUCTURE_HASH)
    with PRODUCT.open('rb') as stream, warnings.catch_warnings(record=True) as caught:
        result = structural.structure(stream, PRODUCT.stat().st_size)
    result['parser_warning_categories'] = [w.category.__name__ for w in caught]
    if result != json.loads(HEADER_PATH.read_bytes()):
        raise ValueError('STOP_HEADER_REPLAY')
    C.checkpoint()


def measure(plan, accounting):
    selected = reader()
    core = C.load_pinned('c8_geometry', CORE_PATH, CORE_HASH)
    report = json.loads(HEADER_PATH.read_bytes())
    if table_schema(report) != plan['table']:
        raise ValueError('STOP_SOURCE_SCHEMA_BINDING')
    h = header(report['hdus'][1])
    schema = selected.build_schema([(card.keyword, card.value) for card in h.cards], 77760)
    progress = {}
    try:
        with PRODUCT.open('rb', buffering=0) as stream:
            columns = selected.read_selected(stream, schema, accounting=progress, checkpoint=C.checkpoint)
    finally:
        # Progress counters remain public, but no current catalogue row ordinal.
        accounting.update({k: v for k, v in progress.items() if k not in ('current_row', 'current_span')})
    if set(columns) != set(core.FIELDS) or any(len(v) != 151 for v in columns.values()):
        raise ValueError('STOP_MISSING_SOURCE_ROWS')
    C.checkpoint()
    summary = core.summarize(columns, centres())
    validate_summary(summary)
    C.checkpoint()
    return summary


def zero():
    return {}


def validate_summary(summary):
    if (type(summary) is not dict or summary.get('status') != PASS or summary.get('rows') != 151
            or any(not isinstance(summary.get(kind), list) or len(summary[kind]) != 5
                   or [r.get('region') for r in summary[kind]] != ['published', 'north120', 'east120', 'south120', 'west120']
                   for kind in ('apertures', 'annuli'))):
        raise ValueError('STOP_SUMMARY_DENOMINATOR')


def valid_accounting(value, complete=False):
    if type(value) is not dict:
        raise ValueError('STOP_SELECTED_ACCOUNTING')
    if not value and not complete:
        return
    counters = ('read_bytes', 'decoded_bytes', 'reads_attempted', 'reads_completed', 'spans_decoded', 'rows_completed')
    flags = ('current_read_completion_unknown', 'current_decode_completion_unknown')
    if (set(value) != {'status', 'phase', *counters, *flags}
            or any(type(value[k]) is not int or value[k] < 0 for k in counters)
            or any(type(value[k]) is not bool for k in flags)
            or value['status'] not in ('IN_PROGRESS', 'FAILED', 'COMPLETE')
            or value['phase'] not in ('VALIDATING', 'CHECKPOINT', 'SEEKING', 'READING', 'READ_VALIDATING',
                                      'DECODING', 'STORING', 'FINALIZING', 'COMPLETE')):
        raise ValueError('STOP_SELECTED_ACCOUNTING')
    a = value
    spans = a['spans_decoded']
    sizes = (4, 20, 8, 16, 4)
    prefix = lambda n: n // 5 * 52 + sum(sizes[:n % 5])
    if (not 0 <= a['decoded_bytes'] <= a['read_bytes'] <= PAYLOAD
            or not spans <= a['reads_completed'] <= a['reads_attempted'] <= 755
            or a['reads_completed'] - spans > 1
            or a['reads_attempted'] - a['reads_completed'] > 1
            or a['decoded_bytes'] != prefix(spans) or not 0 <= a['rows_completed'] <= 151
            or not a['rows_completed'] * 5 <= spans <= min(755, (a['rows_completed'] + 1) * 5)
            or a['read_bytes'] > prefix(a['reads_completed'])
            or a[flags[0]] != (a['status'] == 'FAILED' and a['phase'] == 'READING')
            or a[flags[1]] != (a['status'] == 'FAILED' and a['phase'] == 'DECODING')):
        raise ValueError('STOP_SELECTED_ACCOUNTING')
    if complete or a['status'] == 'COMPLETE':
        expected = dict(zip(counters, (7852, 7852, 755, 755, 755, 151), strict=True))
        if a['status'] != 'COMPLETE' or a['phase'] != 'COMPLETE' or any(a[k] != v for k, v in expected.items()):
            raise ValueError('STOP_COMPLETE_ACCOUNTING')


def artifacts(exclude=()):
    check_files()
    return {p.name: C.sha(p, monitor=False) for p in HERE.iterdir() if p.is_file() and p.name not in exclude
            and (p.suffix == '.json' or p.name == 'protocol.snapshot.md')}


def check_files():
    if any(p.parent != HERE or p.name not in FILES for p in HERE.rglob('*.json')):
        raise ValueError('STOP_UNEXPECTED_STAGE_JSON')


def fallback():
    attempted = any((HERE / name).exists() for name in ('table-start.json', 'table-result.json'))
    return [{'table': 1, 'status': 'UNVERIFIED_ATTEMPT' if attempted else 'NOT_ATTEMPTED',
             'accounting': None if attempted else zero()}]


def validation_state():
    return {'status': 'NOT_ATTEMPTED', 'accounting': zero()}


def validate_validation(value):
    if (type(value) is not dict or set(value) != {'status', 'accounting'}
            or value['status'] not in ('NOT_ATTEMPTED', 'ATTEMPTED', 'FAILED', 'COMPLETED')):
        raise ValueError('STOP_PARENT_VALIDATION_RECEIPT')
    valid_accounting(value['accounting'], complete=value['status'] == 'COMPLETED')
    if value['status'] == 'NOT_ATTEMPTED' and value['accounting'] != zero():
        raise ValueError('STOP_PARENT_VALIDATION_RECEIPT')


def ledger(validation=None):
    if not (HERE / 'table-start.json').exists():
        if (HERE / 'table-result.json').exists():
            raise ValueError('STOP_ORPHAN_TABLE_RESULT')
        return [{'table': 1, 'status': 'NOT_ATTEMPTED', 'accounting': zero()}]
    marker = C.read('table-start.json')
    elapsed = marker.get('elapsed_seconds')
    if (set(marker) != {'table', 'elapsed_seconds'} or marker['table'] != 1
            or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 <= elapsed < SECONDS):
        raise ValueError('STOP_TABLE_MARKER')
    if not (HERE / 'table-result.json').exists():
        return [{'table': 1, 'status': 'INTERRUPTED', 'accounting': None}]
    record = C.read('table-result.json')
    if record.get('table') != 1 or record.get('status') not in ('OK', 'STOP'):
        raise ValueError('STOP_TABLE_RECEIPT')
    valid_accounting(record.get('accounting'), complete=record['status'] == 'OK')
    if record['status'] == 'STOP':
        if (set(record) != {'table', 'status', 'accounting', 'error_type', 'error_code'}
                or not isinstance(record['error_type'], str) or not record['error_type'].isidentifier()
                or (record['error_code'] is not None and (not isinstance(record['error_code'], str)
                    or not re.fullmatch(r'STOP_[A-Z0-9_]+', record['error_code'])))):
            raise ValueError('STOP_FAILED_TABLE_RECEIPT')
    else:
        if set(record) != {'table', 'status', 'accounting', 'summary'}:
            raise ValueError('STOP_SUCCESS_TABLE_RECEIPT')
        validate_summary(record['summary'])
        if validation is not None:
            validation['status'] = 'ATTEMPTED'
            try:
                summary = measure(C.read('run-start.json')['manifest'], validation['accounting'])
                if record['summary'] != summary or record['accounting'] != validation['accounting']:
                    raise ValueError('STOP_SUMMARY_REPLAY')
            except Exception:
                validation['status'] = 'FAILED'
                raise
            validation['status'] = 'COMPLETED'
    return [{'table': 1, 'status': record['status'], 'accounting': record['accounting']}]


def worker():
    began = time.monotonic()
    C.DEADLINE = began + SECONDS
    result, accounting = {'status': 'STOP'}, zero()
    try:
        check_files()
        verify_binding()
        C.save('worker-start.json', {'binding_sha256': C.sha(HERE / 'run-start.json')})
        verify_product()
        C.save('table-start.json', {'table': 1, 'elapsed_seconds': time.monotonic() - began})
        try:
            summary = measure(C.read('run-start.json')['manifest'], accounting)
            C.save('table-result.json', {'table': 1, 'status': 'OK', 'accounting': accounting, 'summary': summary})
        except Exception as error:
            C.save('table-result.json', {'table': 1, 'status': 'STOP', **failure(error), 'accounting': accounting}, terminal=True)
            raise
        C.checkpoint()
        result['status'] = PASS
    except Exception as error:
        LOGGER.exception('Source worker stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(failure(error))
    finally:
        C.DEADLINE = None
        try:
            result['ledger'] = ledger()
        except Exception:
            LOGGER.exception('Source ledger incomplete', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
            result.update(status='STOP', ledger=fallback(), error_code='STOP_LEDGER_UNVERIFIED')
        result.update(artifacts=artifacts(), resource_usage=C.resource_usage(exclude=('worker-result.json', 'outcome.json')))
        C.save('worker-result.json', result, terminal=True, peak_key='peak_memory_bytes')
    return 0 if result['status'] == PASS else 1


def assess(code, validation):
    C.DEADLINE = time.monotonic() + SECONDS
    try:
        check_files()
        verify_binding()
        verify_product()
        rows = ledger(validation)
        w = C.read('worker-result.json') if (HERE / 'worker-result.json').exists() else None
        if w and (w['ledger'] != rows or w['artifacts'] != artifacts(('worker-result.json', 'outcome.json'))
                  or w['resource_usage'] != C.resource_usage(exclude=('worker-result.json', 'outcome.json'))
                  or type(w['peak_memory_bytes']) is not int or w['peak_memory_bytes'] <= 0):
            raise ValueError('STOP_WORKER_CLOSURE')
        success = code == 0 and w is not None and w['status'] == PASS
        validate_validation(validation)
        if success and (rows[0]['status'] != 'OK' or w['peak_memory_bytes'] > C.MEMORY_CAP
                        or validation['status'] != 'COMPLETED'
                        or C.read('worker-start.json') != {'binding_sha256': C.sha(HERE / 'run-start.json')}):
            raise ValueError('STOP_FALSE_SUCCESS')
        C.checkpoint()
        return {'status': PASS if success else 'STOP', 'worker_returncode': code, 'ledger': rows,
                'worker_peak_memory_bytes': w['peak_memory_bytes'] if w else None,
                'worker_error_code': w.get('error_code') if w else None,
                'resource_usage': C.resource_usage(exclude=('outcome.json',)),
                'photons_or_map_pixels_interpreted': False, 'source_coordinates_or_ids_persisted': False}
    finally:
        C.DEADLINE = None


def run():
    check_files()
    if any((HERE / name).exists() for name in FILES):
        raise ValueError('STOP_ALREADY_ATTEMPTED')
    validation = validation_state()
    result = {'status': 'STOP', 'worker_returncode': None, 'assessment_completed': False}
    try:
        C.save('run-start.json', binding(PROTOCOL))
        with (HERE / 'protocol.snapshot.md').open('xb') as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned('c8_deadline', C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), '-B', str(SOURCE), '_worker'], SECONDS)
        result['worker_returncode'] = code
        result.update(assess(code, validation))
        result['assessment_completed'] = True
    except Exception as error:
        LOGGER.exception('Source parent stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(failure(error), ledger=fallback())
    finally:
        result.update(parent_validation=validation, artifacts=artifacts(('outcome.json',)),
                      source_sha256=C.sha(SOURCE, monitor=False))
        C.save('outcome.json', result, terminal=True, peak_key='parent_peak_memory_bytes')
    print(result['status'])
    return 0 if result['status'] == PASS else 1


def replay():
    outcome = C.read('outcome.json')
    if type(outcome.get('assessment_completed')) is not bool:
        raise ValueError('STOP_ASSESSMENT_FLAG')
    if outcome['artifacts'] != artifacts(('outcome.json',)) or outcome['source_sha256'] != C.sha(SOURCE):
        raise ValueError('STOP_OUTCOME_ARTIFACTS')
    validate_validation(outcome['parent_validation'])
    peak = outcome.get('parent_peak_memory_bytes')
    if type(peak) is not int or peak <= 0 or (peak > C.MEMORY_CAP and
            (outcome['status'] != 'STOP' or outcome.get('error_code') != 'STOP_PEAK_MEMORY')):
        raise ValueError('STOP_PARENT_MEMORY_RECEIPT')
    C.resource_usage()
    if not outcome['assessment_completed']:
        if outcome['status'] != 'STOP' or outcome['ledger'] != fallback():
            raise ValueError('STOP_FAILURE_ARTIFACT_REPLAY')
        print('PASS_FAILURE_ARTIFACT_REPLAY STOP; no numerical reread')
        return
    validation = validation_state()
    try:
        expected = assess(outcome['worker_returncode'], validation)
        if peak > C.MEMORY_CAP:
            expected['status'] = 'STOP'
        if any(outcome.get(k) != v for k, v in expected.items()) or outcome['parent_validation'] != validation:
            raise ValueError('STOP_OUTCOME_REPLAY')
    except Exception:
        print(json.dumps({'replay_status': 'FAILED', 'additional_selected_pass': validation}, allow_nan=False))
        raise
    print(json.dumps({'replay_status': 'PASS_OFFLINE_REPLAY', 'status': expected['status'],
                      'additional_selected_pass': validation}, allow_nan=False))


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['run']:
            raise SystemExit(run())
        if sys.argv[1:] == ['_worker']:
            raise SystemExit(worker())
        if sys.argv[1:] == ['replay']:
            replay()
        else:
            raise ValueError('STOP_COMMAND')
    except Exception as error:
        LOGGER.exception('Source command stopped', exc_info=(RuntimeError, RuntimeError('Safe code only'), None))
        print(failure(error).get('error_code') or 'STOP_INTERNAL')
        raise SystemExit(1) from None
