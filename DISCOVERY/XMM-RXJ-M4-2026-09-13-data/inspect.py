"""Offline four fixed metadata slices; no requests or scientific products."""

import hashlib
import importlib.machinery
import importlib.util
import json
import logging
import re
import sys
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M4-2026-09-13.md'
ARCHIVE = HERE.parent / 'XMM-RXJ-M3-2026-09-13-data/summary.tar'
ARCHIVE_HASH = 'fa3c45838875c61f68e07508d862fc56d32e83f0b39ed3f6b1bef2207b9ccbe2'
ARCHIVE_BYTES, SELECTED_BYTES = 1044480, 1033100
TAIL_OFFSET, TAIL_BYTES = 1036288, 8192
TAIL_HASH = 'e3c5d4864109c463b69f6f7b124995ae36b2082f40e972339da26f0e9200a0ea'
TRAILER_HASH = 'c304f59f74ff1408146b797c68f001e4284f7bb014ae2267d98e60f44de040f9'
PLAN = [
    {'slot': 1, 'role': 'EP', 'header': 0, 'offset': 512, 'bytes': 872917, 'next': 873472,
     'header_sha256': '1515d452115254c73b8f402efec58b8d08cf8530b7b11e7a85172741ee194321'},
    {'slot': 2, 'role': 'OB', 'header': 873472, 'offset': 873984, 'bytes': 48229, 'next': 922624,
     'header_sha256': '7e570189d8e9ad67d78a0e67bb5c4129e448b51120de24c8149b826e9c666f64'},
    {'slot': 3, 'role': 'RG', 'header': 922624, 'offset': 923136, 'bytes': 25265, 'next': 948736,
     'header_sha256': 'bb622ea07a7cbeb122f8ad7546f5086e9734521cc066e48d23822d3faac050c9'},
    {'slot': 4, 'role': 'OM', 'header': 948736, 'offset': 949248, 'bytes': 86689, 'next': 1036288,
     'header_sha256': '2c47e616fa9eb43ae3cf0cb712cebe0fb4ec23d0006b93d2cae4cf0295f4b607'},
]
C1 = HERE.parent / 'XMM-C1-2026-09-12-data/acquire.py'
C1_HASH = '13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5'
PARSER = HERE.parent / 'xmm_summary_metadata.py'
PARSER_HASH = 'bca91205c9983986f7bfac2b596a03d8da7d92af8b343fba70e3d82a31148f0d'
PARSER_TEST_HASH = '6f26a135c792f442c20a3e31bdbadbe30e399464e165a0bdf54039709e8d64a1'
PINS = {
    'XMM-C1-2026-09-12-data/acquire.py': C1_HASH,
    'XMM-C1-2026-09-12-data/test_acquire.py': 'd751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c',
    'XMM-RXJ-M3-2026-09-13-data/listing.py': '01564aff6d0873eb7a8bda42ddd408f085e85489e7410b739a1dfd9d40978472',
    'XMM-RXJ-M3-2026-09-13-data/test_listing.py': 'd6ee89793f0b09ad1c53a240423c5c421048d1130f07922e16fab9ca344a8e8b',
    'XMM-RXJ-M3-2026-09-13.md': '230a900079e8220a7a29a5ceeb16a714cdfae684e525f83b783f7a26925a245a',
    'XMM-RXJ-M3-2026-09-13-data/outcome.json': '1a897ff9dbf74f0b88c7428b2dbd63dc16944036191256374204056d3b3f5678',
    'XMM-RXJ-M3-2026-09-13-data/http.json': '6b2e62f84d8412f00e8ca60f73bcbc400f1009010f21556c381a5fb0cf5924f0',
    'XMM-RXJ-M3-2026-09-13-data/transport.json': 'ce59925f72d7675fd155eced7c5b6d0c1465258254c468bedf2046b7d249b2a0',
    'XMM-RXJ-M3-NEXT-2026-09-13.md': '2034068945bb923710b7c0df081580f0fcbd53cd9d5975d5cf0c03e4e6de8267',
}
SECONDS, MEMORY_CAP, JSON_CAP, RESERVE = 30, 268435456, 1048576, 65536
RECEIPT_CAP, CHUNK = 196608, 65536
PASS = 'FOUR_FIXED_METADATA_DOCUMENTS_ACCOUNTED_UNADJUDICATED'
DEADLINE, PEAK = None, 0
LOGGER = logging.getLogger(__name__)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(path.read_bytes())


def load_pinned(path, expected, name):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('STOP_DEPENDENCY_HASH')
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(path), 'exec')
    spec = importlib.util.spec_from_file_location(name, path, loader=Loader(name, str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_pinned(C1, C1_HASH, 'm4_peak_helper')


def checkpoint():
    global PEAK
    PEAK = max(PEAK, C.peak_memory())
    if PEAK > MEMORY_CAP:
        raise ValueError('STOP_PEAK_MEMORY')
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise ValueError('STOP_TOTAL_DEADLINE')


def failure(error):
    code = str(error)
    return code if isinstance(error, ValueError) and re.fullmatch(r'STOP_[A-Z0-9_]+', code) else 'STOP_INTERNAL'


def artifact_names():
    return {'run-start.json', 'protocol.snapshot.md', 'worker-start.json', 'worker-result.json', 'outcome.json', 'comparison.json'} | {
        f'slot-{slot}-{kind}.json' for slot in range(1, 5) for kind in ('start', 'result')}


def artifacts():
    allowed = artifact_names() | {'inspect.py', 'test_inspect.py', '.gitattributes', '.gitignore'}
    for path in HERE.rglob('*'):
        if path == HERE / '__pycache__' or (path.parent == HERE / '__pycache__' and path.suffix == '.pyc'):
            continue
        if path.parent != HERE or not path.is_file() or path.name not in allowed:
            raise ValueError('STOP_UNEXPECTED_ARTIFACT')
    if sum(p.stat().st_size for p in HERE.glob('*.json')) > JSON_CAP:
        raise ValueError('STOP_JSON_BUDGET')
    return {name: sha(HERE / name) for name in sorted(artifact_names() - {'outcome.json'}) if (HERE / name).exists()}


def save(name, value, terminal=False, final_peak=False):
    global PEAK
    raw = (canonical(value) + '\n').encode()
    if final_peak:
        for _ in range(2):
            PEAK = max(PEAK, C.peak_memory())
            value['peak_memory_bytes'] = PEAK
            if PEAK > MEMORY_CAP:
                if 'state' in value:
                    value['state'].update(status='STOP', error_code='STOP_PEAK_MEMORY')
                else:
                    value.update(status='STOP', error_code='STOP_PEAK_MEMORY')
            raw = (canonical(value) + '\n').encode()
    cap = RESERVE if terminal else RECEIPT_CAP
    if len(raw) > cap or sum(p.stat().st_size for p in HERE.glob('*.json')) + len(raw) > JSON_CAP - (0 if terminal else RESERVE):
        raise ValueError('STOP_JSON_BUDGET')
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


def read(name):
    path = HERE / name
    if path.stat().st_size > RECEIPT_CAP:
        raise ValueError('STOP_JSON_BUDGET')
    return json.loads(path.read_bytes())


def binding(protocol):
    pins = {**PINS, 'xmm_summary_metadata.py': PARSER_HASH, 'test_xmm_summary_metadata.py': PARSER_TEST_HASH}
    dependencies = {str(HERE.parent / name): expected for name, expected in pins.items()}
    dependencies[str(C.HELPER)] = C.HELPER_HASH
    if any(sha(Path(p)) != expected for p, expected in dependencies.items()):
        raise ValueError('STOP_DEPENDENCY_HASH')
    return {'source_sha256': sha(SOURCE), 'tests_sha256': sha(HERE / 'test_inspect.py'),
            'protocol_sha256': sha(protocol), 'attributes_sha256': sha(HERE / '.gitattributes'),
            'privacy_sha256': sha(HERE / '.gitignore'), 'dependencies': dependencies,
            'plan': PLAN, 'archive': {'bytes': ARCHIVE_BYTES, 'sha256': ARCHIVE_HASH},
            'tail': {'offset': TAIL_OFFSET, 'bytes': TAIL_BYTES, 'sha256': TAIL_HASH, 'trailer_sha256': TRAILER_HASH},
            'limits': {'seconds': SECONDS, 'memory_bytes': MEMORY_CAP, 'json_bytes': JSON_CAP,
                       'reserve_bytes': RESERVE, 'receipt_bytes': RECEIPT_CAP, 'selected_bytes_per_pass': SELECTED_BYTES},
            'runtime': {'python': sys.version, 'executable': str(Path(sys.executable).resolve())}}


def verify_binding():
    if canonical(read('run-start.json')) != canonical(binding(HERE / 'protocol.snapshot.md')):
        raise ValueError('STOP_BINDING')


def is_hash(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def safe_error(value):
    return value is None or (type(value) is str and re.fullmatch(r'STOP_[A-Z0-9_]+', value) is not None)


def validate_state(state):
    template = fresh_pass()
    if (type(state) is not dict or set(state) != set(template) or state['status'] not in ('NOT_ATTEMPTED', 'ATTEMPTED', 'STOP', PASS)
            or not safe_error(state['error_code']) or (state['comparison_sha256'] is not None and not is_hash(state['comparison_sha256']))):
        raise ValueError('STOP_PASS_SCHEMA')
    a = state['archive']
    if (type(a) is not dict or set(a) != set(template['archive']) or type(a['read_unknown']) is not bool or type(a['verified']) is not bool
            or any(type(a[k]) is not int or not 0 <= a[k] <= cap for k, cap in
                   (('opaque_bytes', ARCHIVE_BYTES), ('header_bytes', 2048), ('tail_bytes', TAIL_BYTES)))):
        raise ValueError('STOP_ARCHIVE_ACCOUNTING')
    if ((a['header_bytes'] or a['tail_bytes']) and a['opaque_bytes'] != ARCHIVE_BYTES
            or a['tail_bytes'] and a['header_bytes'] != 2048
            or a['verified'] and (a['opaque_bytes'] != ARCHIVE_BYTES or a['header_bytes'] != 2048 or a['tail_bytes'] != TAIL_BYTES or a['read_unknown'])):
        raise ValueError('STOP_ARCHIVE_ACCOUNTING')
    if type(state['slots']) is not list or len(state['slots']) != 4:
        raise ValueError('STOP_SLOT_SCHEMA')
    for p, slot, empty in zip(PLAN, state['slots'], template['slots'], strict=True):
        if (type(slot) is not dict or set(slot) != set(empty) or type(slot['slot']) is not int or slot['slot'] != p['slot']
                or slot['role'] != p['role'] or slot['status'] not in ('NOT_ATTEMPTED', 'ATTEMPTED', 'STOP', 'OK')
                or type(slot['bytes_read']) is not int or not 0 <= slot['bytes_read'] <= p['bytes']
                or type(slot['read_unknown']) is not bool or slot['parse_state'] not in ('NOT_ATTEMPTED', 'ATTEMPTED', 'COMPLETED')
                or not safe_error(slot['error_code'])
                or any(slot[k] is not None and not is_hash(slot[k]) for k in ('content_sha256', 'result_sha256'))):
            raise ValueError('STOP_SLOT_SCHEMA')
        if slot['status'] == 'NOT_ATTEMPTED' and canonical(slot) != canonical(empty):
            raise ValueError('STOP_SLOT_ACCOUNTING')
        if ((slot['bytes_read'] or slot['status'] != 'NOT_ATTEMPTED') and not a['verified']
                or slot['parse_state'] != 'NOT_ATTEMPTED' and (slot['bytes_read'] != p['bytes'] or slot['read_unknown'] or not is_hash(slot['content_sha256']))
                or slot['result_sha256'] is not None and slot['parse_state'] != 'COMPLETED'
                or slot['status'] == 'OK' and (slot['parse_state'] != 'COMPLETED' or not is_hash(slot['result_sha256']) or slot['error_code'] is not None)
                or slot['status'] == 'STOP' and slot['error_code'] is None):
            raise ValueError('STOP_SLOT_ACCOUNTING')
    if (type(state['selected_bytes']) is not int or state['selected_bytes'] != sum(s['bytes_read'] for s in state['slots'])
            or not 0 <= state['selected_bytes'] <= SELECTED_BYTES):
        raise ValueError('STOP_SELECTED_ACCOUNTING')
    if state['status'] == 'NOT_ATTEMPTED' and canonical(state) != canonical(template):
        raise ValueError('STOP_PASS_ACCOUNTING')
    if state['status'] == PASS and (not all(s['status'] == 'OK' for s in state['slots'])
            or state['selected_bytes'] != SELECTED_BYTES or not is_hash(state['comparison_sha256']) or state['error_code'] is not None):
        raise ValueError('STOP_PASS_ACCOUNTING')


def validate_receipts():
    artifacts()
    has_start = (HERE / 'run-start.json').exists()
    has_snapshot = (HERE / 'protocol.snapshot.md').exists()
    if has_start and has_snapshot:
        verify_binding()
    if has_snapshot and not has_start:
        raise ValueError('STOP_ORPHAN_SNAPSHOT')
    worker_started = (HERE / 'worker-start.json').exists()
    if worker_started and (not has_start or not has_snapshot
            or canonical(read('worker-start.json')) != canonical({'offline': True, 'slots': 4})):
        raise ValueError('STOP_WORKER_MARKER')
    worker_result = read('worker-result.json') if (HERE / 'worker-result.json').exists() else None
    if worker_result is not None:
        if (type(worker_result) is not dict or set(worker_result) != {'state', 'peak_memory_bytes'}
                or type(worker_result['peak_memory_bytes']) is not int or worker_result['peak_memory_bytes'] <= 0):
            raise ValueError('STOP_WORKER_RESOURCE')
        validate_state(worker_result['state'])
        if (worker_result['peak_memory_bytes'] > MEMORY_CAP and (worker_result['state']['status'] != 'STOP'
                or worker_result['state']['error_code'] != 'STOP_PEAK_MEMORY')):
            raise ValueError('STOP_WORKER_RESOURCE')
    missing = False
    for p in PLAN:
        marker = HERE / f"slot-{p['slot']}-start.json"
        result_path = HERE / f"slot-{p['slot']}-result.json"
        if not marker.exists():
            missing = True
            if result_path.exists():
                raise ValueError('STOP_ORPHAN_SLOT')
        else:
            if missing or not worker_started or canonical(read(marker.name)) != canonical(p):
                raise ValueError('STOP_SLOT_ORDER')
        if worker_result is not None:
            slot = worker_result['state']['slots'][p['slot'] - 1]
            if marker.exists() != (slot['status'] != 'NOT_ATTEMPTED'):
                raise ValueError('STOP_SLOT_MARKER_ACCOUNTING')
            if not result_path.exists() and worker_result['state']['status'] == PASS:
                raise ValueError('STOP_MISSING_SLOT_RESULT')
        if result_path.exists():
            record = read(result_path.name)
            if type(record) is not dict or set(record) != {'accounting', 'metadata'}:
                raise ValueError('STOP_SLOT_RESULT_SCHEMA')
            if worker_result is not None and canonical(record['accounting']) != canonical(slot):
                raise ValueError('STOP_SLOT_RESULT_ACCOUNTING')
            if record['accounting']['status'] == 'OK':
                if type(record['metadata']) is not dict or digest(canonical(record['metadata']).encode()) != record['accounting']['result_sha256']:
                    raise ValueError('STOP_METADATA_DIGEST')
            elif record['metadata'] is not None:
                raise ValueError('STOP_STOPPED_METADATA')
    if (HERE / 'comparison.json').exists():
        if not all((HERE / f'slot-{i}-result.json').exists() for i in range(1, 5)):
            raise ValueError('STOP_ORPHAN_COMPARISON')
        if worker_result is not None and digest(canonical(read('comparison.json')).encode()) != worker_result['state']['comparison_sha256']:
            raise ValueError('STOP_COMPARISON_DIGEST')
    return worker_result


def fresh_pass():
    return {'status': 'NOT_ATTEMPTED', 'error_code': None,
            'archive': {'opaque_bytes': 0, 'header_bytes': 0, 'tail_bytes': 0, 'read_unknown': False, 'verified': False},
            'selected_bytes': 0, 'comparison_sha256': None,
            'slots': [{'slot': p['slot'], 'role': p['role'], 'status': 'NOT_ATTEMPTED', 'bytes_read': 0,
                       'read_unknown': False, 'parse_state': 'NOT_ATTEMPTED', 'content_sha256': None,
                       'result_sha256': None, 'error_code': None} for p in PLAN]}


def bounded_read(stream, count, accounting, key):
    accounting['read_unknown'] = True
    raw = stream.read(count)
    accounting['read_unknown'] = False
    accounting[key] += len(raw)
    if len(raw) != count:
        raise ValueError('STOP_SHORT_READ')
    checkpoint()
    return raw


def verify_archive(state):
    a = state['archive']
    if ARCHIVE.stat().st_size != ARCHIVE_BYTES:
        raise ValueError('STOP_ARCHIVE_SIZE')
    h = hashlib.sha256()
    with ARCHIVE.open('rb', buffering=0) as stream:
        while a['opaque_bytes'] < ARCHIVE_BYTES:
            h.update(bounded_read(stream, min(CHUNK, ARCHIVE_BYTES - a['opaque_bytes']), a, 'opaque_bytes'))
        if h.hexdigest() != ARCHIVE_HASH:
            raise ValueError('STOP_ARCHIVE_HASH')
        names = set()
        for p in PLAN:
            stream.seek(p['header'])
            raw = bounded_read(stream, 512, a, 'header_bytes')
            if digest(raw) != p['header_sha256']:
                raise ValueError('STOP_HEADER_HASH')
            try:
                info = tarfile.TarInfo.frombuf(raw, encoding='utf-8', errors='surrogateescape')
            except (tarfile.HeaderError, ValueError):
                raise ValueError('STOP_HEADER_SCHEMA') from None
            parts = [part for part in info.name.split('/') if part not in ('', '.')]
            expected = 'P0851180501' + p['role'] + 'X000SUMMAR0000.HTM'
            if (info.type != tarfile.REGTYPE or info.size != p['bytes'] or info.linkname
                    or len(parts) != 3 or parts[0] != '0851180501' or parts[1].lower() != 'pps'
                    or parts[-1] != expected or info.name.startswith('/')
                    or '\\' in info.name or ':' in info.name or '..' in parts
                    or p['offset'] != p['header'] + 512
                    or p['next'] != p['offset'] + ((p['bytes'] + 511) // 512) * 512):
                raise ValueError('STOP_HEADER_IDENTITY')
            normalized = '/'.join(parts)
            if normalized in names:
                raise ValueError('STOP_HEADER_DUPLICATE')
            names.add(normalized)
        stream.seek(TAIL_OFFSET)
        tail = bounded_read(stream, TAIL_BYTES, a, 'tail_bytes')
        if digest(tail) != TAIL_HASH or tail[:1024] != bytes(1024) or digest(tail[1024:]) != TRAILER_HASH:
            raise ValueError('STOP_QUARANTINED_TRAILER')
    a['verified'] = True


def measure(state, persist=False):
    global DEADLINE
    state['status'] = 'ATTEMPTED'
    DEADLINE = time.monotonic() + SECONDS
    try:
        checkpoint()
        parser = load_pinned(PARSER, PARSER_HASH, 'm4_metadata_parser')
        verify_archive(state)
        parsed_documents = []
        for p, slot in zip(PLAN, state['slots'], strict=True):
            checkpoint()
            if persist:
                save(f"slot-{p['slot']}-start.json", p)
            slot['status'] = 'ATTEMPTED'
            result = None
            try:
                chunks = []
                with ARCHIVE.open('rb', buffering=0) as stream:
                    stream.seek(p['offset'])
                    while slot['bytes_read'] < p['bytes']:
                        before = slot['bytes_read']
                        try:
                            chunks.append(bounded_read(stream, min(CHUNK, p['bytes'] - before), slot, 'bytes_read'))
                        finally:
                            state['selected_bytes'] += slot['bytes_read'] - before
                raw = b''.join(chunks)
                slot['content_sha256'] = digest(raw)
                slot['parse_state'] = 'ATTEMPTED'
                result = parser.parse_summary(raw, p['role'], '0851180501')
                parsed_documents.append(result)
                slot['parse_state'] = 'COMPLETED'
                slot['result_sha256'] = digest(canonical(result).encode())
                checkpoint()
                slot['status'] = 'OK'
            except Exception as error:
                LOGGER.exception('Metadata slot stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
                slot.update(status='STOP', error_code=failure(error))
            record = {'accounting': slot, 'metadata': result if slot['status'] == 'OK' else None}
            if persist:
                save(f"slot-{p['slot']}-result.json", record)
            else:
                if canonical(record) != canonical(read(f"slot-{p['slot']}-result.json")):
                    raise ValueError('STOP_SLOT_REPLAY')
            if slot['error_code'] in ('STOP_PEAK_MEMORY', 'STOP_TOTAL_DEADLINE'):
                raise ValueError(slot['error_code'])
        comparison = parser.compare_summaries(parsed_documents, '0851180501')
        state['comparison_sha256'] = digest(canonical(comparison).encode())
        checkpoint()
        if persist:
            save('comparison.json', comparison)
        elif canonical(comparison) != canonical(read('comparison.json')):
            raise ValueError('STOP_COMPARISON_REPLAY')
        state['status'] = PASS if all(s['status'] == 'OK' for s in state['slots']) else 'STOP'
    except Exception as error:
        LOGGER.exception('Metadata pass stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        state.update(status='STOP', error_code=failure(error))
    finally:
        DEADLINE = None
    return state


def worker():
    state = fresh_pass()
    try:
        artifacts()
        verify_binding()
        save('worker-start.json', {'offline': True, 'slots': 4})
        measure(state, persist=True)
    except Exception as error:
        LOGGER.exception('Metadata worker stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        state.update(status='STOP', error_code=failure(error))
    save('worker-result.json', {'state': state, 'peak_memory_bytes': PEAK}, final_peak=True)
    return 0 if state['status'] == PASS else 1


def run():
    artifacts()
    if any((HERE / name).exists() for name in artifact_names()):
        raise ValueError('STOP_ALREADY_ATTEMPTED')
    verification = fresh_pass()
    outcome = {'status': 'STOP', 'worker_returncode': None, 'verification': verification,
               'assessment_completed': False, 'error_code': None}
    try:
        save('run-start.json', binding(PROTOCOL))
        with (HERE / 'protocol.snapshot.md').open('xb') as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned('m4_deadline', C.HELPER, C.HELPER_HASH)
        code, output = helper.bounded_run([str(Path(sys.executable).resolve()), '-B', str(SOURCE), '_worker'], SECONDS)
        outcome.update(worker_returncode=code, output_bytes=len(output.encode()), output_sha256=digest(output.encode()))
        assess(code, verification)
        outcome['assessment_completed'] = True
        outcome['status'] = PASS if code == 0 and verification['status'] == PASS else 'STOP'
    except Exception as error:
        LOGGER.exception('Metadata parent stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        outcome['error_code'] = failure(error)
    outcome['peak_memory_bytes'] = max(PEAK, C.peak_memory())
    if outcome['peak_memory_bytes'] > MEMORY_CAP:
        outcome.update(status='STOP', error_code='STOP_PEAK_MEMORY')
    outcome['artifacts'] = artifacts()
    outcome['worker_slots_evidence'] = worker_evidence()
    save('outcome.json', outcome, terminal=True, final_peak=True)
    print(outcome['status'])
    return 0 if outcome['status'] == PASS else 1


def assess(code, verification):
    if type(code) is not int:
        raise ValueError('STOP_WORKER_RETURNCODE')
    worker_result = validate_receipts()
    if worker_result is None or worker_result['peak_memory_bytes'] > MEMORY_CAP:
        raise ValueError('STOP_WORKER_RESOURCE')
    measure(verification)
    validate_state(verification)
    if canonical(verification) != canonical(worker_result['state']):
        raise ValueError('STOP_WORKER_REPLAY')


def worker_evidence():
    return [{'slot': p['slot'], 'role': p['role'],
             'marker_present': (HERE / f"slot-{p['slot']}-start.json").exists(),
             'result_present': (HERE / f"slot-{p['slot']}-result.json").exists()}
            for p in PLAN]


def validate_outcome(outcome):
    required = {'status', 'worker_returncode', 'verification', 'assessment_completed', 'error_code',
                'peak_memory_bytes', 'artifacts', 'worker_slots_evidence'}
    optional = {'output_bytes', 'output_sha256'}
    if (type(outcome) is not dict or not required <= set(outcome) or not set(outcome) <= required | optional
            or outcome['status'] not in ('STOP', PASS) or type(outcome['assessment_completed']) is not bool
            or not safe_error(outcome['error_code'])
            or outcome['worker_returncode'] is not None and type(outcome['worker_returncode']) is not int
            or type(outcome['peak_memory_bytes']) is not int or outcome['peak_memory_bytes'] <= 0
            or canonical(outcome['artifacts']) != canonical(artifacts())
            or canonical(outcome['worker_slots_evidence']) != canonical(worker_evidence())):
        raise ValueError('STOP_OUTCOME_SCHEMA')
    if (('output_bytes' in outcome) != ('output_sha256' in outcome)
            or 'output_bytes' in outcome and (type(outcome['output_bytes']) is not int or outcome['output_bytes'] < 0
                                            or not is_hash(outcome['output_sha256']))):
        raise ValueError('STOP_OUTPUT_SCHEMA')
    validate_state(outcome['verification'])
    if outcome['peak_memory_bytes'] > MEMORY_CAP and (outcome['status'] != 'STOP' or outcome['error_code'] != 'STOP_PEAK_MEMORY'):
        raise ValueError('STOP_PARENT_MEMORY')
    expected = PASS if (outcome['assessment_completed'] and outcome['worker_returncode'] == 0
                        and outcome['verification']['status'] == PASS and outcome['error_code'] is None) else 'STOP'
    if outcome['status'] != expected or outcome['assessment_completed'] and outcome['worker_returncode'] is None:
        raise ValueError('STOP_OUTCOME_STATUS')


def replay():
    outcome = read('outcome.json')
    validate_outcome(outcome)
    validate_receipts()
    verification = fresh_pass()
    if not outcome['assessment_completed']:
        print('PASS_FAILURE_ARTIFACT_REPLAY STOP; metadata unverified')
        return
    try:
        assess(outcome['worker_returncode'], verification)
        if canonical(verification) != canonical(outcome['verification']):
            raise ValueError('STOP_OUTCOME_REPLAY')
        print('PASS_OFFLINE_REPLAY ' + outcome['status'])
    except Exception:
        print(canonical({'status': 'STOP_OFFLINE_REPLAY', 'additional_verification_pass': verification}))
        raise


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
    except Exception:
        LOGGER.exception('M4 stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        print('STOP_M4_COMMAND')
        raise SystemExit(1) from None
