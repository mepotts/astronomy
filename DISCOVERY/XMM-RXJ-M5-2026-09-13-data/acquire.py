"""Three exactly named RXJ event products; header layout/identity only."""

import gzip
import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import json
import logging
import re
import shutil
import sys
import time
import warnings
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M5-2026-09-13.md'
C1_PATH = HERE.parent / 'XMM-C1-2026-09-12-data/acquire.py'
C1_HASH = '13184df5d2b9d6e4bae83446316974ba90f46e3412e51c10c40cfbe2f5e2cca5'
IDENTITY_PATH = HERE.parent / 'xmm_rxj_header_identity.py'
IDENTITY_HASH = '22d05a66a9afaeee8dc4ceb781ddc9f54354dafcf7eb139535456f773b9e947a'
IDENTITY_TEST_HASH = '891569eba7c9d1fcd5199b3e64c796e470bda64fd2e8924532bacb376683d6ee'
CAP, RAW_TOTAL = 268435456, 536870912
EXPANDED_CAP, EXPANDED_TOTAL = 1073741824, 2147483648
SECONDS, MEMORY_CAP, JSON_CAP, HEADER_CAP = 300, 500000000, 10485760, 2097152
RESERVE, FREE_BYTES, CHUNK = 262144, 4294967296, 1048576
PASS = 'RXJ_EVENT_PRODUCTS_RETAINED_HEADERS_ONLY'
LOGGER = logging.getLogger(__name__)
SAFE_HEADERS = ('Content-Type', 'Content-Length', 'Content-Encoding', 'Date', 'ETag', 'Last-Modified')
MEDIA = {'image/fits', 'application/fits', 'application/x-fits', 'application/octet-stream', 'application/gzip', 'application/x-gzip'}
PLAN = []
for _n, (_inst, _camera, _exposure, _product) in enumerate((('PN', 'EPN', 'S001', 'PIEVLI'),
        ('M1', 'EMOS1', 'S002', 'MIEVLI'), ('M2', 'EMOS2', 'S003', 'MIEVLI')), 1):
    PLAN.append({'slot': _n, 'camera': _camera, 'exposure': _exposure,
                 'filename': f'P0851180501{_inst}{_exposure}{_product}0000.FTZ',
                 'url': 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS'
                        f'&instname={_inst}&expflag=S&expno={_exposure[1:]}&name={_product}&datasubsetno=0&sourceno=000&extension=FTZ'})
PINS = {
    'XMM-C1-2026-09-12-data/acquire.py': C1_HASH,
    'XMM-C1-2026-09-12-data/test_acquire.py': 'd751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c',
    'XMM-RXJ-M4-NEXT-2026-09-13.md': '4a2a3af7f8837f036605b7e1956dcb8019119fa732f31a31c4e2fda95a1033f4',
    'XMM-RXJ-M4-2026-09-13-data/outcome.json': '7a571f930679c4077c7a337292ffceadf19e99a71b819f79777e90a88da0cc05',
    'XMM-RXJ-M4-2026-09-13-data/slot-1-result.json': 'dffd27867686a5226205a0a25c5743c6f9b95ab150e00b86dc18f460859c3615',
    'XMM-RXJ-M4-2026-09-13-data/slot-2-result.json': '3809cc5a1c7524433d018bbcbf9ee64af1dc10ad198bc6b3b6cec2ced75390b5',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


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


C = load_pinned(C1_PATH, C1_HASH, 'm5_c1_primitives')
C.HERE, C.SECONDS, C.CHUNK = HERE, SECONDS, CHUNK
C.MEMORY_CAP, C.JSON_CAP, C.HEADER_CAP, C.RESERVE = MEMORY_CAP, JSON_CAP, HEADER_CAP, RESERVE


def failure(error):
    value = str(error)
    return value if isinstance(error, ValueError) and re.fullmatch(r'STOP_[A-Z0-9_]+', value) else 'STOP_INTERNAL'


def paths(slot):
    return HERE / 'products' / slot['filename'], HERE / 'products' / (slot['filename'][:-4] + '.fits')


def names(slot):
    n = slot['slot']
    return [f'slot-{n}-start.json', f'slot-{n}-http.json', f'slot-{n}-result.json', f'headers/slot-{n}.json', f'slot-{n}-identity.json']


def artifact_paths():
    return {'run-start.json', 'protocol.snapshot.md', 'worker-start.json', 'worker-result.json', 'outcome.json'} | {
        name for slot in PLAN for name in names(slot)} | {p.relative_to(HERE).as_posix() for slot in PLAN for p in paths(slot)}


def resources(exclude=()):
    raw = sum(p.stat().st_size for p in (HERE / 'products').glob('*.FTZ'))
    expanded = sum(p.stat().st_size for p in (HERE / 'products').glob('*.fits'))
    json_bytes = sum(p.stat().st_size for p in HERE.rglob('*.json') if p.relative_to(HERE).as_posix() not in exclude)
    if (raw > RAW_TOTAL or expanded > EXPANDED_TOTAL or json_bytes > JSON_CAP
            or any(p.stat().st_size > CAP for p in (HERE / 'products').glob('*.FTZ'))
            or any(p.stat().st_size > EXPANDED_CAP for p in (HERE / 'products').glob('*.fits'))
            or any(p.stat().st_size > HEADER_CAP for p in (HERE / 'headers').glob('*.json'))):
        raise ValueError('STOP_RESOURCE_CAP')
    return {'raw_bytes': raw, 'expanded_bytes': expanded, 'json_bytes': json_bytes}


def artifacts(exclude=(), monitor=False):
    allowed = artifact_paths() | {'acquire.py', 'test_acquire.py', '.gitattributes', '.gitignore'}
    result = {}
    for p in HERE.rglob('*'):
        rel = p.relative_to(HERE).as_posix()
        if rel in ('products', 'headers', '__pycache__') and p.is_dir():
            continue
        if p.parent == HERE / '__pycache__' and p.suffix == '.pyc':
            continue
        if not p.is_file() or rel not in allowed:
            raise ValueError('STOP_UNEXPECTED_ARTIFACT')
        if rel in artifact_paths() and rel not in exclude:
            result[rel] = C.sha(p, monitor=monitor)
    resources()
    return result


def binding(protocol):
    import astropy
    import requests

    dependencies = {str(HERE.parent / name): h for name, h in PINS.items()}
    dependencies.update({str(p): h for p, h in ((C.HELPER, C.HELPER_HASH), (C.STRUCTURE_PATH, C.STRUCTURE_HASH),
        (C.STRUCTURE_TEST, C.STRUCTURE_TEST_HASH), (C.STRUCTURE_REVIEW, C.STRUCTURE_REVIEW_HASH),
        (IDENTITY_PATH, IDENTITY_HASH), (IDENTITY_PATH.with_name('test_xmm_rxj_header_identity.py'), IDENTITY_TEST_HASH))})
    if any(C.sha(Path(p), monitor=False) != h for p, h in dependencies.items()):
        raise ValueError('STOP_DEPENDENCY_HASH')
    return {'plan': PLAN, 'dependencies': dependencies, 'source_sha256': C.sha(SOURCE, monitor=False),
            'tests_sha256': C.sha(HERE / 'test_acquire.py', monitor=False), 'protocol_sha256': C.sha(protocol, monitor=False),
            'attributes_sha256': C.sha(HERE / '.gitattributes', monitor=False), 'privacy_sha256': C.sha(HERE / '.gitignore', monitor=False),
            'caps': {'raw_file': CAP, 'raw_total': RAW_TOTAL, 'expanded_file': EXPANDED_CAP, 'expanded_total': EXPANDED_TOTAL,
                     'worker_seconds': SECONDS, 'parent_seconds': SECONDS, 'memory': MEMORY_CAP, 'json': JSON_CAP,
                     'header': HEADER_CAP, 'reserve': RESERVE, 'free': FREE_BYTES, 'chunk': CHUNK},
            'runtime': {'python': sys.version, 'executable': str(Path(sys.executable).resolve()), 'astropy': astropy.__version__, 'requests': requests.__version__}}


def verify_binding():
    if canonical(C.read('run-start.json')) != canonical(binding(HERE / 'protocol.snapshot.md')):
        raise ValueError('STOP_BINDING')


def disposition(values, slot):
    result = {'status': 'REJECTED', 'filename_sha256': None}
    if (len(values) != 1 or type(values[0]) is not str or len(values[0]) > 2048
            or any(ord(c) < 32 or ord(c) > 126 for c in values[0])):
        return result
    match = re.fullmatch(r'(?:inline|attachment)\s*;\s*filename\s*=\s*(?:"([A-Za-z0-9._-]+)"|([A-Za-z0-9._-]+))\s*', values[0], re.IGNORECASE)
    if not match or (match[1] or match[2]) != slot['filename']:
        return result
    return {'status': 'EXACT_NAME', 'filename_sha256': digest(slot['filename'].encode())}


def http_schema(http, slot):
    if (type(http) is not dict or set(http) != {'status', 'url', 'actual_url_matches', 'headers', 'disposition'}
            or http['url'] != slot['url'] or type(http['actual_url_matches']) is not bool
            or type(http['status']) is not int or not 100 <= http['status'] <= 599):
        raise ValueError('STOP_HTTP_SCHEMA')
    h = http['headers']
    if (type(h) is not dict or not set(h) <= set(SAFE_HEADERS)
            or any(type(v) is not list or len(v) != 1 or type(v[0]) is not str or len(v[0]) > 2048
                   or any(ord(c) < 32 or ord(c) > 126 for c in v[0]) for v in h.values())):
        raise ValueError('STOP_SAFE_HEADER_SCHEMA')
    d = http['disposition']
    if canonical(d) not in (canonical({'status': 'REJECTED', 'filename_sha256': None}),
                            canonical({'status': 'EXACT_NAME', 'filename_sha256': digest(slot['filename'].encode())})):
        raise ValueError('STOP_DISPOSITION_SCHEMA')


def validate_http(http, slot, actual_bytes=None):
    http_schema(http, slot)
    if not http['actual_url_matches'] or http['status'] != 200:
        raise ValueError('STOP_HTTP_IDENTITY_OR_STATUS')
    h = {k: v[0] for k, v in http['headers'].items()}
    if h.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
        raise ValueError('STOP_CONTENT_ENCODING')
    if h.get('Content-Type', '').split(';', 1)[0].strip().lower() not in MEDIA:
        raise ValueError('STOP_MEDIA_TYPE')
    if http['disposition']['status'] != 'EXACT_NAME':
        raise ValueError('STOP_EXACT_FILENAME')
    length = h.get('Content-Length')
    if length is not None:
        if not re.fullmatch(r'[0-9]{1,12}', length) or not 0 < int(length) <= CAP:
            raise ValueError('STOP_CONTENT_LENGTH')
        if actual_bytes is not None and int(length) != actual_bytes:
            raise ValueError('STOP_ACTUAL_LENGTH')
    return int(length) if length is not None else None


def progress():
    return {**{f'{stage}_{key}': value for stage in ('raw', 'expanded') for key, value in
               (('returned_bytes', 0), ('retained_bytes', 0), ('read_unknown', False), ('write_unknown', False), ('eof', False))},
            'actual_format': None, 'gzip_crc_eof_verified': False, 'request_invocations': 0}


def copy_bounded(source, target, cap, state, stage, network=False):
    while True:
        C.checkpoint()
        remaining = cap - state[f'{stage}_retained_bytes']
        state[f'{stage}_read_unknown'] = True
        block = source.read(min(CHUNK, remaining + 1), **({'decode_content': False} if network else {}))
        state[f'{stage}_read_unknown'] = False
        state[f'{stage}_returned_bytes'] += len(block)
        if not block:
            state[f'{stage}_eof'] = True
            break
        keep = block[:remaining]
        state[f'{stage}_write_unknown'] = True
        written = target.write(keep)
        if type(written) is not int or not 0 <= written <= len(keep):
            raise ValueError('STOP_WRITE_RETURN')
        state[f'{stage}_retained_bytes'] += written
        state[f'{stage}_write_unknown'] = False
        if written != len(keep):
            raise ValueError('STOP_SHORT_WRITE')
        if len(block) > len(keep):
            raise ValueError('STOP_BYTE_CAP')
    C.checkpoint()


def download(slot, state):
    import requests

    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError('STOP_HTTP_PARSER_CAP')
    cap = min(CAP, RAW_TOTAL - resources()['raw_bytes'])
    if cap <= 0:
        raise ValueError('STOP_RAW_TOTAL_CAP')
    with requests.Session() as session:
        session.trust_env, session.auth = False, None
        session.cookies.clear()
        state['request_invocations'] = 1
        with session.get(slot['url'], timeout=(5, 15), stream=True, allow_redirects=False,
                         headers={'Accept-Encoding': 'identity'}) as response:
            http = {'status': response.status_code, 'url': slot['url'], 'actual_url_matches': response.url == slot['url'],
                    'headers': {k: response.raw.headers.getlist(k) for k in SAFE_HEADERS if response.raw.headers.getlist(k)},
                    'disposition': disposition(response.raw.headers.getlist('Content-Disposition'), slot)}
            http_schema(http, slot)
            C.save(f"slot-{slot['slot']}-http.json", http)
            length = validate_http(http, slot)
            if length is not None and length > cap:
                raise ValueError('STOP_RAW_TOTAL_CAP')
            raw = paths(slot)[0]
            raw.parent.mkdir(exist_ok=True)
            with raw.open('xb') as target:
                copy_bounded(response.raw, target, cap, state, 'raw', network=True)
            if not state['raw_retained_bytes']:
                raise ValueError('STOP_EMPTY_BODY')
            validate_http(http, slot, state['raw_retained_bytes'])


def expand(slot, state):
    raw, expanded = paths(slot)
    kind = actual_format(raw)
    state['actual_format'] = kind
    cap = min(EXPANDED_CAP, EXPANDED_TOTAL - resources()['expanded_bytes'])
    if cap <= 0:
        raise ValueError('STOP_EXPANDED_TOTAL_CAP')
    opener = gzip.open if kind == 'GZIP_WRAPPED_FITS' else Path.open
    try:
        with opener(raw, 'rb') as stream, expanded.open('xb') as target:
            copy_bounded(stream, target, cap, state, 'expanded')
    except (gzip.BadGzipFile, EOFError, zlib.error):
        raise ValueError('STOP_GZIP_INTEGRITY') from None
    if kind == 'GZIP_WRAPPED_FITS':
        state['gzip_crc_eof_verified'] = True
    elif C.sha(raw) != C.sha(expanded):
        raise ValueError('STOP_RAW_COPY')


def actual_format(raw):
    with raw.open('rb') as stream:
        signature = stream.read(30)
    if signature.startswith(b'\x1f\x8b\x08'):
        kind = 'GZIP_WRAPPED_FITS'
    elif signature.startswith(b'SIMPLE  =                    T'):
        kind = 'RAW_FITS'
    else:
        raise ValueError('STOP_RAW_SIGNATURE')
    return kind


def inspect_headers(slot):
    reader = load_pinned(C.STRUCTURE_PATH, C.STRUCTURE_HASH, 'm5_structure')
    path = paths(slot)[1]
    C.checkpoint()
    with path.open('rb') as stream, warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        report = reader.structure(stream, path.stat().st_size)
    if captured:
        raise ValueError('STOP_HEADER_WARNINGS')
    C.checkpoint()
    return report


def file_record(path, monitor=False):
    return {'bytes': path.stat().st_size, 'sha256': C.sha(path, monitor=monitor)} if path.exists() else None


def summarize_identity(report, slot):
    helper = load_pinned(IDENTITY_PATH, IDENTITY_HASH, 'm5_identity')
    result = helper.inspect_identity(report, slot['camera'], slot['exposure'], '0851180501')
    sources = [result['hdus'][item['hdu']] for item in result['identity']]
    crosscheck = {}
    for key, expected in (('SUBMODE', 'PrimeFullWindow'), ('DATAMODE', 'Imaging'), ('FILTER', 'Thin1')):
        fields = [hdu['metadata'][key] for hdu in sources]
        candidates = [candidate for field in fields for candidate in field['candidates']]
        matches = sum(c['state'] == 'KNOWN' and str(c['value']).lower() == expected.lower() for c in candidates)
        conflicts = sum(c['state'] == 'KNOWN' and str(c['value']).lower() != expected.lower() for c in candidates)
        unknown = sum(c['state'] != 'KNOWN' for c in candidates)
        status = ('DUPLICATE' if any(f['state'] == 'DUPLICATE' for f in fields) else 'CONFLICT' if conflicts
                  else 'UNRECOGNIZED' if unknown else 'CONSISTENT' if matches else 'MISSING')
        crosscheck[key] = {'expected_m4_ob': expected, 'status': status, 'matching_candidates': matches,
                          'conflicting_candidates': conflicts, 'unknown_candidates': unknown}
    result['m4_ob_crosscheck_non_gating'] = crosscheck
    return result


def marker_evidence():
    return [{'slot': p['slot'], 'status': 'UNVERIFIED_ATTEMPT' if any((HERE / name).exists() for name in names(p))
             or any(path.exists() for path in paths(p)) else 'NOT_ATTEMPTED'} for p in PLAN]


def safe_code(value):
    return value is None or (type(value) is str and re.fullmatch(r'STOP_[A-Z0-9_]+', value) is not None)


def is_hash(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def validate_progress(state, record):
    if type(state) is not dict or set(state) != set(progress()):
        raise ValueError('STOP_PROGRESS_SCHEMA')
    if type(state['request_invocations']) is not int or state['request_invocations'] not in (0, 1):
        raise ValueError('STOP_REQUEST_ACCOUNTING')
    for stage, cap in (('raw', CAP), ('expanded', EXPANDED_CAP)):
        for key in ('read_unknown', 'write_unknown', 'eof'):
            if type(state[f'{stage}_{key}']) is not bool:
                raise ValueError('STOP_PROGRESS_SCHEMA')
        got, kept = state[f'{stage}_returned_bytes'], state[f'{stage}_retained_bytes']
        if type(got) is not int or type(kept) is not int or not 0 <= kept <= got <= cap + 1:
            raise ValueError('STOP_PROGRESS_BYTES')
        actual = record[stage]['bytes'] if record[stage] is not None else 0
        if (actual > cap or (actual != kept and not state[f'{stage}_write_unknown'])
                or state[f'{stage}_write_unknown'] and not kept <= actual <= got):
            raise ValueError('STOP_PROGRESS_FILE_BYTES')
        if state[f'{stage}_eof'] and state[f'{stage}_read_unknown']:
            raise ValueError('STOP_PROGRESS_EOF')
    if type(state['gzip_crc_eof_verified']) is not bool or state['actual_format'] not in (None, 'RAW_FITS', 'GZIP_WRAPPED_FITS'):
        raise ValueError('STOP_PROGRESS_FORMAT')
    if state['gzip_crc_eof_verified'] and (state['actual_format'] != 'GZIP_WRAPPED_FITS' or not state['expanded_eof']):
        raise ValueError('STOP_PROGRESS_FORMAT')
    if record['status'] == 'OK' and (state['request_invocations'] != 1 or not state['raw_eof'] or not state['expanded_eof'] or state['actual_format'] is None
                or any(state[f'{stage}_{key}'] for stage in ('raw', 'expanded') for key in ('read_unknown', 'write_unknown'))
                or any(state[f'{stage}_returned_bytes'] != state[f'{stage}_retained_bytes'] or state[f'{stage}_retained_bytes'] <= 0 for stage in ('raw', 'expanded'))
                or state['actual_format'] == 'GZIP_WRAPPED_FITS' and not state['gzip_crc_eof_verified']):
        raise ValueError('STOP_FALSE_COMPLETE_PROGRESS')


def header_pass():
    return [{'slot': slot['slot'], 'started': False, 'completed': False} for slot in PLAN]


def validate_header_pass(state):
    if type(state) is not list or len(state) != len(PLAN):
        raise ValueError('STOP_HEADER_PASS_SCHEMA')
    stopped = False
    for row, slot in zip(state, PLAN, strict=True):
        if (type(row) is not dict or set(row) != {'slot', 'started', 'completed'}
                or type(row['slot']) is not int or row['slot'] != slot['slot']
                or type(row['started']) is not bool or type(row['completed']) is not bool
                or row['completed'] and not row['started'] or stopped and row['started']):
            raise ValueError('STOP_HEADER_PASS_SCHEMA')
        stopped = not row['completed']


def validate_record(slot, record, verify=False, verification=None):
    keys = {'slot', 'status', 'error_code', 'phase', 'progress', 'raw', 'expanded', 'headers', 'identity'}
    if (type(record) is not dict or set(record) != keys or canonical(record['slot']) != canonical(slot)
            or record['status'] not in ('OK', 'FAILED') or not safe_code(record['error_code'])
            or record['phase'] not in ('HTTP', 'EXPANSION', 'HEADERS', 'IDENTITY', 'COMPLETE')
            or record['status'] == 'OK' and (record['error_code'] is not None or record['phase'] != 'COMPLETE')
            or record['status'] == 'FAILED' and record['error_code'] is None):
        raise ValueError('STOP_SLOT_SCHEMA')
    for key in ('raw', 'expanded', 'headers', 'identity'):
        value = record[key]
        if value is not None and (type(value) is not dict or set(value) != {'bytes', 'sha256'}
                                 or type(value['bytes']) is not int or value['bytes'] < 0 or not is_hash(value['sha256'])):
            raise ValueError('STOP_FILE_RECEIPT_SCHEMA')
    validate_progress(record['progress'], record)
    raw, expanded = paths(slot)
    header_path = HERE / f"headers/slot-{slot['slot']}.json"
    identity_path = HERE / f"slot-{slot['slot']}-identity.json"
    for key, path in (('raw', raw), ('expanded', expanded), ('headers', header_path), ('identity', identity_path)):
        if canonical(record[key]) != canonical(file_record(path, monitor=verify)):
            raise ValueError('STOP_FILE_RECEIPT_REPLAY')
    if record['progress']['actual_format'] is not None and actual_format(raw) != record['progress']['actual_format']:
        raise ValueError('STOP_FORMAT_REPLAY')
    http_path = HERE / f"slot-{slot['slot']}-http.json"
    if http_path.exists():
        http_schema(C.read(http_path.name), slot)
        if record['progress']['request_invocations'] != 1:
            raise ValueError('STOP_REQUEST_ACCOUNTING')
    if record['status'] == 'OK':
        validate_http(C.read(http_path.name), slot, record['raw']['bytes'])
        if record['headers'] is None or record['identity'] is None:
            raise ValueError('STOP_MISSING_HEADER_IDENTITY')
        if record['progress']['actual_format'] == 'RAW_FITS' and record['raw'] != record['expanded']:
            raise ValueError('STOP_RAW_COPY')
    if record['headers'] is not None:
        if record['headers']['bytes'] > HEADER_CAP:
            raise ValueError('STOP_HEADER_CAP')
        if verify:
            entry = verification[slot['slot'] - 1] if verification is not None else None
            if entry is not None:
                entry['started'] = True
            report = inspect_headers(slot)
            if canonical(report) != canonical(C.read(header_path.relative_to(HERE).as_posix())):
                raise ValueError('STOP_HEADER_REPLAY')
            identity = summarize_identity(report, slot)
            if record['identity'] is not None and canonical(identity) != canonical(C.read(identity_path.name)):
                raise ValueError('STOP_IDENTITY_REPLAY')
            if entry is not None:
                entry['completed'] = True
        if record['identity'] is not None and record['identity']['bytes'] > HEADER_CAP:
            raise ValueError('STOP_IDENTITY_CAP')
        if record['status'] == 'OK' and C.read(identity_path.name).get('status') != 'HEADER_IDENTITY_AUTHENTICATED':
            raise ValueError('STOP_FALSE_IDENTITY')


def ledger(verify=False, verification=None):
    artifacts(exclude=('outcome.json',))
    rows, stopped = [], False
    for slot in PLAN:
        n = slot['slot']
        marker = HERE / f'slot-{n}-start.json'
        record_path = HERE / f'slot-{n}-result.json'
        row = {'slot': n, 'status': 'NOT_ATTEMPTED'}
        if marker.exists():
            if stopped or canonical(C.read(marker.name)) != canonical(slot):
                raise ValueError('STOP_SLOT_ORDER')
            row['status'] = 'INTERRUPTED'
            if record_path.exists():
                record = C.read(record_path.name)
                validate_record(slot, record, verify=verify, verification=verification)
                row['status'] = record['status']
            stopped = row['status'] != 'OK'
        else:
            if any((HERE / name).exists() for name in names(slot)[1:]) or any(path.exists() for path in paths(slot)):
                raise ValueError('STOP_ORPHAN_SLOT')
            stopped = True
        rows.append(row)
    return rows


def worker():
    C.DEADLINE = time.monotonic() + SECONDS
    result = {'status': 'STOP', 'error_code': None}
    try:
        verify_binding()
        C.save('worker-start.json', {'binding_sha256': C.sha(HERE / 'run-start.json')})
        if shutil.disk_usage(HERE).free < FREE_BYTES:
            raise ValueError('STOP_FREE_SPACE')
        for slot in PLAN:
            C.checkpoint()
            C.save(f"slot-{slot['slot']}-start.json", slot)
            state = progress()
            record = {'slot': slot, 'status': 'FAILED', 'error_code': None, 'phase': 'HTTP', 'progress': state,
                      'raw': None, 'expanded': None, 'headers': None, 'identity': None}
            try:
                download(slot, state)
                record['phase'] = 'EXPANSION'
                expand(slot, state)
                record['phase'] = 'HEADERS'
                report = inspect_headers(slot)
                C.save(f"headers/slot-{slot['slot']}.json", report, header=True)
                record['phase'] = 'IDENTITY'
                identity = summarize_identity(report, slot)
                C.save(f"slot-{slot['slot']}-identity.json", identity, header=True)
                if identity['status'] != 'HEADER_IDENTITY_AUTHENTICATED':
                    raise ValueError(identity['status'])
                record.update(status='OK', phase='COMPLETE')
            except Exception as error:
                LOGGER.exception('M5 slot stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
                record['error_code'] = failure(error)
            for key, path in (('raw', paths(slot)[0]), ('expanded', paths(slot)[1]), ('headers', HERE / f"headers/slot-{slot['slot']}.json"),
                              ('identity', HERE / f"slot-{slot['slot']}-identity.json")):
                record[key] = file_record(path)
            if len(canonical(record).encode()) > 65536:
                raise ValueError('STOP_SLOT_RECEIPT_CAP')
            C.save(f"slot-{slot['slot']}-result.json", record, terminal=record['status'] != 'OK')
            if record['status'] != 'OK':
                raise ValueError(record['error_code'])
        C.checkpoint()
        result['status'] = PASS
    except Exception as error:
        LOGGER.exception('M5 worker stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result['error_code'] = failure(error)
    finally:
        C.DEADLINE = None
        try:
            result['ledger'] = ledger()
        except Exception:
            LOGGER.exception('M5 ledger unverified', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
            result.update(status='STOP', ledger=marker_evidence(), error_code='STOP_LEDGER_UNVERIFIED')
        result['artifacts'] = artifacts(exclude=('worker-result.json', 'outcome.json'))
        result['resources'] = resources(exclude=('worker-result.json', 'outcome.json'))
        C.save('worker-result.json', result, terminal=True, peak_key='peak_memory_bytes')
    return 0 if result['status'] == PASS else 1


def assess(code, verification=None):
    if verification is None:
        verification = header_pass()
    if type(code) is not int:
        raise ValueError('STOP_RETURNCODE')
    verify_binding()
    if canonical(C.read('worker-start.json')) != canonical({'binding_sha256': C.sha(HERE / 'run-start.json')}):
        raise ValueError('STOP_WORKER_MARKER')
    C.DEADLINE = time.monotonic() + SECONDS
    try:
        rows = ledger(verify=True, verification=verification)
        worker_result = C.read('worker-result.json')
        if (type(worker_result) is not dict or set(worker_result) != {'status', 'error_code', 'ledger', 'artifacts', 'resources', 'peak_memory_bytes'}
                or worker_result['status'] not in ('STOP', PASS) or not safe_code(worker_result['error_code'])
                or type(worker_result['peak_memory_bytes']) is not int or worker_result['peak_memory_bytes'] <= 0
                or canonical(worker_result['ledger']) != canonical(rows)
                or canonical(worker_result['artifacts']) != canonical(artifacts(exclude=('worker-result.json', 'outcome.json'), monitor=True))
                or canonical(worker_result['resources']) != canonical(resources(exclude=('worker-result.json', 'outcome.json')))):
            raise ValueError('STOP_WORKER_CLOSURE')
        success = code == 0 and worker_result['status'] == PASS
        if success and (rows != [{'slot': i, 'status': 'OK'} for i in range(1, 4)]
                        or worker_result['error_code'] is not None or worker_result['peak_memory_bytes'] > MEMORY_CAP):
            raise ValueError('STOP_FALSE_SUCCESS')
        C.checkpoint()
        return {'status': PASS if success else 'STOP', 'worker_returncode': code, 'ledger': rows,
                'worker_error_code': worker_result['error_code'], 'worker_peak_memory_bytes': worker_result['peak_memory_bytes'],
                'resources': resources(exclude=('outcome.json',)), 'arrays_decoded': False,
                'header_verification_pass': verification}
    finally:
        C.DEADLINE = None


def run():
    artifacts()
    if any((HERE / name).exists() for name in artifact_paths()):
        raise ValueError('STOP_ALREADY_ATTEMPTED')
    verification = header_pass()
    result = {'status': 'STOP', 'worker_returncode': None, 'assessment_completed': False, 'error_code': None,
              'header_verification_pass': verification}
    try:
        C.save('run-start.json', binding(PROTOCOL))
        with (HERE / 'protocol.snapshot.md').open('xb') as stream:
            stream.write(PROTOCOL.read_bytes())
        if shutil.disk_usage(HERE).free < FREE_BYTES:
            raise ValueError('STOP_FREE_SPACE')
        helper = C.load_pinned('m5_deadline', C.HELPER, C.HELPER_HASH)
        code, output = helper.bounded_run([str(Path(sys.executable).resolve()), '-B', str(SOURCE), '_worker'], SECONDS)
        result.update(worker_returncode=code, output_bytes=len(output.encode()), output_sha256=digest(output.encode()))
        result.update(assess(code, verification))
        result['assessment_completed'] = True
    except Exception as error:
        LOGGER.exception('M5 parent stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(error_code=failure(error), ledger=marker_evidence())
    result['artifacts'] = artifacts(exclude=('outcome.json',))
    C.save('outcome.json', result, terminal=True, peak_key='parent_peak_memory_bytes')
    print(result['status'])
    return 0 if result['status'] == PASS else 1


def replay():
    resources()
    outcome = C.read('outcome.json')
    required = {'status', 'worker_returncode', 'assessment_completed', 'error_code', 'ledger', 'artifacts', 'parent_peak_memory_bytes',
                'header_verification_pass'}
    optional = {'output_bytes', 'output_sha256', 'worker_error_code', 'worker_peak_memory_bytes', 'resources', 'arrays_decoded'}
    if (type(outcome) is not dict or not required <= set(outcome) or not set(outcome) <= required | optional
            or outcome['status'] not in ('STOP', PASS) or type(outcome['assessment_completed']) is not bool
            or outcome['status'] == PASS and outcome['error_code'] is not None
            or not safe_code(outcome['error_code']) or type(outcome['parent_peak_memory_bytes']) is not int or outcome['parent_peak_memory_bytes'] <= 0
            or outcome['worker_returncode'] is not None and type(outcome['worker_returncode']) is not int
            or canonical(outcome['artifacts']) != canonical(artifacts(exclude=('outcome.json',)))):
        raise ValueError('STOP_OUTCOME_SCHEMA')
    validate_header_pass(outcome['header_verification_pass'])
    if (('output_bytes' in outcome) != ('output_sha256' in outcome)
            or 'output_bytes' in outcome and (type(outcome['output_bytes']) is not int or outcome['output_bytes'] < 0 or not is_hash(outcome['output_sha256']))):
        raise ValueError('STOP_OUTPUT_SCHEMA')
    peak = outcome['parent_peak_memory_bytes']
    if peak > MEMORY_CAP and (outcome['status'] != 'STOP' or outcome['error_code'] != 'STOP_PEAK_MEMORY'):
        raise ValueError('STOP_PARENT_MEMORY')
    if not outcome['assessment_completed']:
        if outcome['status'] != 'STOP' or canonical(outcome['ledger']) != canonical(marker_evidence()):
            raise ValueError('STOP_FAILURE_REPLAY')
        if (HERE / 'run-start.json').exists() and (HERE / 'protocol.snapshot.md').exists():
            verify_binding()
        for slot in PLAN:
            path = HERE / f"slot-{slot['slot']}-http.json"
            if path.exists():
                http_schema(C.read(path.name), slot)
        print('PASS_FAILURE_ARTIFACT_REPLAY STOP; product verification incomplete')
        return
    verification = header_pass()
    try:
        expected = assess(outcome['worker_returncode'], verification)
        if peak > MEMORY_CAP:
            expected['status'] = 'STOP'
        if not set(expected) <= set(outcome) or canonical({k: outcome[k] for k in expected}) != canonical(expected):
            raise ValueError('STOP_OUTCOME_REPLAY')
    except Exception:
        print(canonical({'status': 'STOP_OFFLINE_HEADER_PASS', 'additional_header_verification_pass': verification}))
        raise
    print('PASS_OFFLINE_REPLAY ' + expected['status'])


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
        LOGGER.exception('M5 stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        print('STOP_M5_COMMAND')
        raise SystemExit(1) from None
