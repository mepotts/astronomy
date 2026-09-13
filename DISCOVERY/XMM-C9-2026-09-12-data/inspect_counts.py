"""C9 bounded local recorded counts. Uncalibrated; no recovery or discovery.

Three fixed EVENTS tables only. All source/map/GTI/attitude values are excluded.
Product hash/header validation and numerical row reads have separate accounting.
"""

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

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-C9-2026-09-12.md'
PLAN = HERE.parent / 'XMM-RECORDED-COUNTS-PLAN-2026-09-12.md'
C8_PATH = HERE.parent / 'XMM-C8-2026-09-12-data/inspect_sources.py'
C8_HASH = 'bd76ab70fb36ca2ea9c350401ab36991baa8fd30b3bf160c546c788a536ad0e3'
C8_OUTCOME = '82cd6df3d673c86059494e9d38a3bfd1312ee9ce8b19301873309dfc995ad16e'
C8_RESULT = '719afedaca93f82f85a5e7003564bab7f02bf1c23065d871d80b3bae53f16cfa'
READER_PATH = HERE.parent / 'xmm_event_rows.py'
READER_HASH = '9a5b86117956f98e1dcabec197fd70bab148ed9bba93048793680b7b6c448f4c'
READER_TEST_HASH = '205752eb49855c029dadd99ae9961dd9a028091e23423f3c5386e0cba8b9aa3d'
GEOMETRY_PATH = HERE.parent / 'xmm_event_geometry.py'
GEOMETRY_HASH = '8adcb227f61c2f86855652ada4d66b5f677e84caa0cb16b5dd182be3081de9da'
GEOMETRY_TEST_HASH = 'e1e1d41daffec25ada03fd155f958082c62f09c62cef4cdd83ee2cd8fa14f538'
COUNTER_PATH = HERE.parent / 'xmm_recorded_counts.py'
COUNTER_HASH = '5094b15b735619c5de25f7c6fe7a4f5207f82c8c7bc64cac6565678f8975090c'
COUNTER_TEST_HASH = '5e5b1bc15646ab12c856582142cad6331019ff9e23455a961761b3e4d374df9c'
SECONDS, ROW_CAP, ROW_BYTES, SELECTED_BYTES = 120, 10000, 142652840, 93070824
PASS = 'RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY'
LOGGER = logging.getLogger(__name__)
CAMERAS = ('EPN', 'EMOS1', 'EMOS2')
PRODUCTS = (
    ('P0884250101PNS003PIEVLI0000.fits', 219988800, '7fc15ff164943acadcea741457ccd2fba529883677e3d7693d35d01136097570',
     'a6d78ea07324eeef06ed544555525ebb4e071f069eb428ed050913d6cbcbf0ba',
     '5bf8b3550442b0bf78bb73f3350c8ab207b04e96aace7e362fa4dfd9e9e7a8e6', 2694388, 45, 63360),
    ('P0884250101M1S001MIEVLI0000.fits', 11707200, '7703a0c2475225b02bc44134eab033cf39ba11cc28a4a1843d0105b47afc294a',
     'a99589df5bbce769557e09f150365a109a705bf20cf1e464819559d7af1d15ae',
     '5ab5e72735021d7e181d44d22d6cda0bc45cb57c0238110f7009ef56092e5fae', 273441, 34, 40320),
    ('P0884250101M2S002MIEVLI0000.fits', 15194880, '203a7b798558ab6c895a0fa0cdecef9c3936d81578549fb235a43c65beb26150',
     '4ab18a78e8677e9db62c9ad07bbefe143bfcecb72aebb640fa6f4da721e20417',
     '8694aa12d67af42519678c6c4aa362640f902e322da59487f525f085685b400d', 356129, 34, 40320))
FIXED_FILES = ('run-start.json', 'protocol.snapshot.md', 'worker-start.json', 'worker-result.json', 'outcome.json')


def load_base():
    raw = C8_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != C8_HASH:
        raise ValueError('STOP_HELPER_SOURCE_HASH')

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(C8_PATH), 'exec')

    spec = importlib.util.spec_from_file_location('c9_base', C8_PATH, loader=VerifiedLoader('c9_base', str(C8_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_base()
C = B.C
C.HERE, C.SECONDS = HERE, SECONDS
C.MEMORY_CAP, C.JSON_CAP, C.RESERVE = 536870912, 4194304, 262144
C.EXPECTED, C.EXPANDED_FILE_CAP, C.EXPANDED_TOTAL_CAP = (), 0, 0
PRIOR = B.PRIOR
failure, header, centres = B.failure, B.header, B.centres


def modules():
    return (C.load_pinned('c9_rows', READER_PATH, READER_HASH),
            C.load_pinned('c9_geometry', GEOMETRY_PATH, GEOMETRY_HASH),
            C.load_pinned('c9_counts', COUNTER_PATH, COUNTER_HASH))


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if type(value) is dict:
        return {k: json_value(v) for k, v in value.items()}
    if type(value) in (list, tuple):
        return [json_value(v) for v in value]
    return value


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def manifest():
    selected, geometry, counter = modules()
    if C.sha(PRIOR / 'outcome.json') != B.OUTCOME_HASH:
        raise ValueError('STOP_C1_OUTCOME_HASH')
    prior = json.loads((PRIOR / 'outcome.json').read_bytes())
    if prior['status'] != C.PASS or prior['worker_returncode'] != 0:
        raise ValueError('STOP_C1_STATUS')
    items = []
    for slot, (camera, expected) in enumerate(zip(CAMERAS, PRODUCTS, strict=True), 1):
        name, size, digest, hdigest, rdigest, rows, stride, offset = expected
        rp, hp = PRIOR / f'slot-{slot}-result.json', PRIOR / f'headers/slot-{slot}-headers.json'
        if C.sha(rp) != rdigest or C.sha(hp) != hdigest:
            raise ValueError('STOP_PRIOR_RECEIPT_HASH')
        r, report = json.loads(rp.read_bytes()), json.loads(hp.read_bytes())
        if (r['status'] != 'OK' or r['slot']['slot'] != slot or r['slot']['filename'] != name[:-5] + '.FTZ'
                or r['expanded'] != {'bytes': size, 'sha256': digest} or r['headers_sha256'] != hdigest
                or r['gzip_crc_eof_verified'] is not True or report['file_bytes'] != size
                or report['parser_warning_categories']
                or prior['artifacts'].get(f'slot-{slot}-result.json') != rdigest
                or prior['artifacts'].get(f'headers/slot-{slot}-headers.json') != hdigest
                or prior['artifacts'].get('products/' + name) != digest):
            raise ValueError('STOP_PRIOR_CLOSURE')
        tables = [h for h in report['hdus'] if h['extname'] == 'EVENTS']
        if len(tables) != 1:
            raise ValueError('STOP_EVENTS_HDU')
        t, primary = tables[0], header(report['hdus'][0])
        h = header(t)
        config = counter.camera_config(camera)
        if (primary.get('OBS_ID') != '0884250101' or primary.get('INSTRUME') != camera
                or t['data_offset'] != offset or t['data_bytes'] != rows * stride
                or h.get('TSTART') != config['tstart'] or h.get('TSTOP') != config['tstop']
                or [h.get(k) for k in ('TIMESYS', 'MJDREF', 'TIMEZERO', 'TIMEREF', 'TASSIGN', 'CLOCKAPP')]
                != ['TT', 50814., 0., 'LOCAL', 'SATELLITE', True]):
            raise ValueError('STOP_EVENTS_TIME_IDENTITY')
        pairs = [(c.keyword, c.value) for c in h.cards]
        schema = selected.build_schema(pairs, offset)
        g = geometry.build_geometry(pairs)
        if (schema.rows, schema.row_bytes) != (rows, stride):
            raise ValueError('STOP_EVENTS_LAYOUT')
        items.append({'slot': slot, 'camera': camera, 'filename': name, 'file_bytes': size,
                      'product_sha256': digest, 'header_sha256': hdigest, 'receipt_sha256': rdigest,
                      'schema': schema.metadata(), 'geometry': g.metadata(), 'config': config,
                      'chunks': math.ceil(rows / ROW_CAP)})
    if C.sha(C8_PATH.with_name('outcome.json')) != C8_OUTCOME or C.sha(C8_PATH.with_name('table-result.json')) != C8_RESULT:
        raise ValueError('STOP_C8_HASH')
    return {'cameras': items, 'edges': counter.fixed_edges().tolist(), 'prior_c1_outcome': B.OUTCOME_HASH,
            'c8_outcome': C8_OUTCOME, 'c8_contact_result': C8_RESULT,
            'centre_convention': 'unchanged_C5_ICRS_offsets_then_FK5_J2000',
            'backgrounds_source_masked': False, 'recovery_requirements_met': False}


def binding(protocol):
    import astropy

    paths = {C8_PATH: C8_HASH,
             C8_PATH.with_name('test_inspect_sources.py'): '0bd5ba02add739318553de6029147e79d625b8dcde8c5180b3674c9088370733',
             B.C1_PATH: B.C1_HASH, C.HELPER: C.HELPER_HASH,
             C.STRUCTURE_PATH: C.STRUCTURE_HASH, C.STRUCTURE_TEST: C.STRUCTURE_TEST_HASH,
             C.STRUCTURE_REVIEW: C.STRUCTURE_REVIEW_HASH, B.C5_PATH: B.C5_HASH,
             B.DEFINITION: B.DEFINITION_HASH,
             B.C1_PATH.with_name('test_acquire.py'): 'd751843243552cfdf3d65558c2ff96cf34c6885832378a02789f6dc23fbb541c',
             READER_PATH: READER_HASH,
             READER_PATH.with_name('test_xmm_event_rows.py'): READER_TEST_HASH,
             GEOMETRY_PATH: GEOMETRY_HASH, GEOMETRY_PATH.with_name('test_xmm_event_geometry.py'): GEOMETRY_TEST_HASH,
             COUNTER_PATH: COUNTER_HASH, COUNTER_PATH.with_name('test_xmm_recorded_counts.py'): COUNTER_TEST_HASH}
    if any(C.sha(p) != h for p, h in paths.items()):
        raise ValueError('STOP_DEPENDENCY_HASH')
    B.verify_centres_definition()
    return {'manifest': manifest(), 'dependencies': {str(p): h for p, h in paths.items()},
            'source_sha256': C.sha(SOURCE), 'tests_sha256': C.sha(HERE / 'test_inspect_counts.py'),
            'protocol_sha256': C.sha(protocol), 'plan_sha256': C.sha(PLAN), 'output_directory': str(HERE),
            'runtime': {'python': sys.version, 'executable': str(Path(sys.executable).resolve()),
                        'numpy': np.__version__, 'astropy': astropy.__version__},
            'caps': {'seconds': SECONDS, 'memory': C.MEMORY_CAP, 'json': C.JSON_CAP, 'reserve': C.RESERVE,
                     'chunk_rows': ROW_CAP, 'row_bytes_per_pass': ROW_BYTES, 'selected_bytes_per_pass': SELECTED_BYTES}}


def verify_binding():
    if digest_json(C.read('run-start.json')) != digest_json(binding(HERE / 'protocol.snapshot.md')):
        raise ValueError('STOP_BINDING')


def verify_product(item, progress):
    path = PRIOR / 'products' / item['filename']
    progress.update(status='IN_PROGRESS', hash_bytes_returned=0, header_bytes_read=None)
    try:
        if path.stat().st_size != item['file_bytes']:
            raise ValueError('STOP_PRODUCT_SIZE')
        digest = hashlib.sha256()
        with path.open('rb', buffering=0) as stream:
            while True:
                block = stream.read(C.CHUNK)
                if not block:
                    break
                progress['hash_bytes_returned'] += len(block)
                digest.update(block)
                C.checkpoint()
        if digest.hexdigest() != item['product_sha256'] or progress['hash_bytes_returned'] != item['file_bytes']:
            raise ValueError('STOP_PRODUCT_HASH')
        structural = C.load_pinned('c9_structure', C.STRUCTURE_PATH, C.STRUCTURE_HASH)
        with path.open('rb', buffering=0) as stream, warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            report = structural.structure(stream, item['file_bytes'])
        progress['header_bytes_read'] = report['header_bytes_read']
        report['parser_warning_categories'] = [w.category.__name__ for w in caught]
        if report != json.loads((PRIOR / f"headers/slot-{item['slot']}-headers.json").read_bytes()):
            raise ValueError('STOP_HEADER_REPLAY')
        progress['status'] = 'COMPLETE'
    except Exception:
        progress['status'] = 'FAILED'
        raise


def template(config, counter):
    return {'status': PASS, 'camera': config['camera'], 'labels': list(counter.LABELS), 'rows': 0,
            'rejected': dict.fromkeys(counter.REJECTIONS, 0),
            'field_diagnostics': {k: {'null_rows': 0, 'nonfinite_rows': 0, 'valid_rows': 0} for k in counter.FIELDS},
            'accepted_rows': 0, 'accepted_inside_grid': 0, 'accepted_outside_grid': 0,
            'circle20': [[0] * 5 for _ in range(254)], 'annulus60_90': [[0] * 5 for _ in range(254)],
            'per_ccd': [{'ccd': ccd, 'accepted_rows': 0, 'accepted_inside_grid': 0, 'accepted_outside_grid': 0,
                         'circle20': [0] * 5, 'annulus60_90': [0] * 5} for ccd in config['ccds']],
            'annuli_are_source_masked': False, 'gti_filter_applied': False, 'exposure_or_significance_computed': False}


def combine(a, b, limit, key=None, *, add=True):
    """Exact recursive aggregate schema, no extra keys or integer overflow."""
    if type(a) is not type(b):
        raise ValueError('STOP_SUMMARY_TYPE')
    if type(a) is dict:
        if set(a) != set(b):
            raise ValueError('STOP_SUMMARY_KEYS')
        return {k: combine(a[k], b[k], limit, k, add=add) for k in a}
    if type(a) is list:
        if len(a) != len(b):
            raise ValueError('STOP_SUMMARY_SHAPE')
        return [combine(x, y, limit, key, add=add) for x, y in zip(a, b, strict=True)]
    if type(a) is int and key != 'ccd':
        if not 0 <= b <= limit or not 0 <= a <= limit or (add and a > limit - b):
            raise ValueError('STOP_SUMMARY_COUNT')
        return a + b if add else b
    if a != b:
        raise ValueError('STOP_SUMMARY_LITERAL')
    return a


def validate_summary(summary, config, counter, complete=False):
    combine(template(config, counter), summary, config['total_rows'], add=False)
    n, accepted = summary['rows'], summary['accepted_rows']
    inside = summary['accepted_inside_grid']
    if (sum(summary['rejected'].values()) + accepted != n
            or inside + summary['accepted_outside_grid'] != accepted
            or any(sum(d.values()) != n for d in summary['field_diagnostics'].values())
            or any(sum(r[k] for r in summary['per_ccd']) != summary[k]
                   for k in ('accepted_rows', 'accepted_inside_grid', 'accepted_outside_grid'))
            or (complete and n != config['total_rows'])):
        raise ValueError('STOP_COUNT_DENOMINATOR')
    hist = {}
    for key in ('circle20', 'annulus60_90'):
        h = np.asarray(summary[key], dtype=np.int64)
        hist[key] = h.sum(axis=0)
        c = np.asarray([r[key] for r in summary['per_ccd']], dtype=np.int64)
        if np.any(hist[key] > inside) or not np.array_equal(hist[key], c.sum(axis=0)):
            raise ValueError('STOP_CCD_COUNT_CLOSURE')
        if any(any(v > r['accepted_inside_grid'] for v in r[key]) for r in summary['per_ccd']):
            raise ValueError('STOP_CCD_COUNT_CLOSURE')
    if np.any(hist['circle20'] + hist['annulus60_90'] > inside):
        raise ValueError('STOP_REGION_DISJOINTNESS')


def progress_new():
    return {'status': 'IN_PROGRESS', 'phase': 'OPENING', 'read_bytes': 0, 'selected_bytes_decoded': 0,
            'rows_completed': 0, 'chunks_completed': 0, 'current': None}


def chunk_name(slot, index, suffix):
    return f'camera-{slot}-chunk-{index}-{suffix}.json'


def measure(item, accounting, *, persist=False, compare_chunks=False):
    selected, geometry, counter = modules()
    report = json.loads((PRIOR / f"headers/slot-{item['slot']}-headers.json").read_bytes())
    t = next(t for t in report['hdus'] if t['extname'] == 'EVENTS')
    h = header(t)
    pairs = [(c.keyword, c.value) for c in h.cards]
    schema = selected.build_schema(pairs, t['data_offset'])
    g = geometry.build_geometry(pairs)
    if schema.metadata() != item['schema'] or g.metadata() != item['geometry']:
        raise ValueError('STOP_MEASUREMENT_SCHEMA')
    config, edges = item['config'], counter.fixed_edges()
    total = template(config, counter)
    fixed_centres = np.asarray(centres(), dtype=np.float64)
    accounting.update(progress_new())
    try:
        with (PRIOR / 'products' / item['filename']).open('rb', buffering=0) as stream:
            for index, start in enumerate(range(0, schema.rows, ROW_CAP), 1):
                C.checkpoint()
                n = min(ROW_CAP, schema.rows - start)
                current = {'index': index, 'row_start': start, 'rows_requested': n,
                           'bytes_requested': n * schema.row_bytes, 'bytes_returned': None,
                           'read_completion_unknown': False, 'decoder': {}, 'geometry': {},
                           'histogram_rows_completed': 0, 'accumulated_rows': 0}
                accounting.update(phase='CHECKPOINT', current=current)
                if persist:
                    C.save(chunk_name(item['slot'], index, 'start'), {'slot': item['slot'], 'index': index,
                           'row_start': start, 'rows_requested': n, 'bytes_requested': n * schema.row_bytes})
                try:
                    accounting['phase'] = 'SEEKING'
                    expected = schema.data_offset + start * schema.row_bytes
                    if stream.seek(expected) != expected:
                        raise ValueError('STOP_SEEK')
                    accounting['phase'] = 'READING'
                    raw = stream.read(current['bytes_requested'])
                    if type(raw) is not bytes:
                        raise TypeError('STOP_READ_TYPE')
                    current['bytes_returned'] = len(raw)
                    accounting['read_bytes'] += len(raw)
                    accounting['phase'] = 'READ_VALIDATING'
                    if len(raw) != current['bytes_requested']:
                        raise ValueError('STOP_TRUNCATED_ROWS')
                    C.checkpoint()
                    accounting['phase'] = 'DECODING'
                    try:
                        decoded = selected.decode_rows(raw, schema, row_start=start, accounting=current['decoder'])
                    finally:
                        accounting['selected_bytes_decoded'] += current['decoder'].get('selected_field_bytes_decoded', 0)
                    C.checkpoint()
                    accounting['phase'] = 'GEOMETRY'
                    membership = geometry.classify_xy(decoded['values']['X'], decoded['values']['Y'],
                        decoded['masks']['X']['valid'] & decoded['masks']['Y']['valid'], g, fixed_centres,
                        accounting=current['geometry'])
                    C.checkpoint()
                    accounting['phase'] = 'COUNTING'
                    increment = json_value(counter.count_chunk(decoded, membership, config, edges))
                    current['histogram_rows_completed'] = n
                    accounting['phase'] = 'COUNT_VALIDATING'
                    validate_summary(increment, config, counter)
                    accounting['phase'] = 'ACCUMULATING'
                    total = combine(total, increment, config['total_rows'])
                    current['accumulated_rows'] = n
                    accounting['phase'] = 'SAVING_CHUNK'
                    receipt = {'slot': item['slot'], 'status': 'OK', 'progress': current,
                               'increment_sha256': digest_json(increment)}
                    if persist:
                        C.save(chunk_name(item['slot'], index, 'result'), receipt)
                    if compare_chunks and C.read(chunk_name(item['slot'], index, 'result')) != receipt:
                        raise ValueError('STOP_CHUNK_REPLAY')
                    accounting['rows_completed'] += n
                    accounting['chunks_completed'] += 1
                    accounting['current'] = None
                except Exception as error:
                    current['read_completion_unknown'] = accounting['phase'] == 'READING'
                    if persist and not (HERE / chunk_name(item['slot'], index, 'result')).exists():
                        C.save(chunk_name(item['slot'], index, 'result'), {'slot': item['slot'], 'status': 'STOP',
                               'progress': current, **failure(error)}, terminal=True)
                    raise
        validate_summary(total, config, counter, complete=True)
        accounting.update(status='COMPLETE', phase='COMPLETE')
        C.checkpoint()
        return total
    except Exception:
        accounting['status'] = 'FAILED'
        raise


def state():
    return {'status': 'NOT_ATTEMPTED', 'cameras': [{'slot': n, 'status': 'NOT_ATTEMPTED',
            'verification': {}, 'accounting': {}} for n in range(1, 4)]}


def check_files():
    for p in HERE.rglob('*'):
        if p.is_dir() and p.name == '__pycache__' and p.parent == HERE:
            continue
        if p.is_file() and p.suffix == '.pyc' and p.parent == HERE / '__pycache__':
            continue
        allowed = p.name in (*FIXED_FILES, 'inspect_counts.py', 'test_inspect_counts.py', '.gitattributes') or bool(
            re.fullmatch(r'camera-[123]-(?:start|result|chunk-[1-9]\d*-(?:start|result))\.json', p.name))
        if p.is_dir() or p.parent != HERE or not allowed:
            raise ValueError('STOP_UNEXPECTED_STAGE_ARTIFACT')


def artifacts(exclude=()):
    check_files()
    return {p.name: C.sha(p, monitor=False) for p in HERE.iterdir() if p.is_file() and p.name not in exclude
            and (p.suffix == '.json' or p.name == 'protocol.snapshot.md')}


def fallback():
    return [{'slot': n, 'status': 'UNVERIFIED_ATTEMPT' if any(HERE.glob(f'camera-{n}-*.json')) else 'NOT_ATTEMPTED',
             'verification': None if any(HERE.glob(f'camera-{n}-*.json')) else {},
             'accounting': None if any(HERE.glob(f'camera-{n}-*.json')) else {}} for n in range(1, 4)]


def valid_failure(record):
    if (not isinstance(record.get('error_type'), str) or not record['error_type'].isidentifier()
            or len(record['error_type']) > 80 or (record.get('error_code') is not None
                and (not isinstance(record['error_code'], str) or not re.fullmatch(r'STOP_[A-Z0-9_]+', record['error_code'])))):
        raise ValueError('STOP_FAILURE_SCHEMA')


def safe_terminal(record, required, allowed):
    if (type(record) is not dict or not required <= set(record) or not set(record) <= allowed
            or record.get('status') not in ('STOP', PASS)):
        raise ValueError('STOP_TERMINAL_SCHEMA')
    if 'error_type' in record and (not isinstance(record['error_type'], str)
                                  or not record['error_type'].isidentifier() or len(record['error_type']) > 80):
        raise ValueError('STOP_TERMINAL_SCHEMA')
    if 'error_code' in record and record['error_code'] is not None and (
            not isinstance(record['error_code'], str) or not re.fullmatch(r'STOP_[A-Z0-9_]+', record['error_code'])):
        raise ValueError('STOP_TERMINAL_SCHEMA')


def valid_progress(a, item, complete=False):
    if type(a) is not dict:
        raise ValueError('STOP_PASS_ACCOUNTING')
    if not a and not complete:
        return
    expected = set(progress_new())
    if (set(a) != expected or a['status'] not in ('IN_PROGRESS', 'FAILED', 'COMPLETE')
            or a['phase'] not in ('OPENING', 'CHECKPOINT', 'SEEKING', 'READING', 'READ_VALIDATING', 'DECODING',
                                   'GEOMETRY', 'COUNTING', 'COUNT_VALIDATING', 'ACCUMULATING', 'SAVING_CHUNK', 'COMPLETE')
            or any(type(a[k]) is not int or a[k] < 0 for k in ('read_bytes', 'selected_bytes_decoded', 'rows_completed', 'chunks_completed'))
            or a['read_bytes'] > item['schema']['payload_bytes'] or a['selected_bytes_decoded'] > item['schema']['rows'] * 28
            or a['selected_bytes_decoded'] > a['read_bytes'] or a['rows_completed'] > item['schema']['rows']
            or a['chunks_completed'] > item['chunks']):
        raise ValueError('STOP_PASS_ACCOUNTING')
    if a['current'] is not None:
        valid_chunk(a['current'], item)
    completed = min(a['chunks_completed'] * ROW_CAP, item['schema']['rows'])
    p = a['current']
    if (a['rows_completed'] != completed
            or (p is not None and p['index'] != a['chunks_completed'] + 1)
            or a['read_bytes'] != completed * item['schema']['row_bytes'] + (p['bytes_returned'] or 0 if p else 0)
            or a['selected_bytes_decoded'] != completed * 28 + (p['decoder'].get('selected_field_bytes_decoded', 0) if p else 0)):
        raise ValueError('STOP_PARTIAL_ACCOUNTING')
    if (complete or a['status'] == 'COMPLETE') and (a['status'] != 'COMPLETE' or a['phase'] != 'COMPLETE' or a['current'] is not None
                or (a['read_bytes'], a['selected_bytes_decoded'], a['rows_completed'], a['chunks_completed'])
                != (item['schema']['payload_bytes'], item['schema']['rows'] * 28, item['schema']['rows'], item['chunks'])):
        raise ValueError('STOP_COMPLETE_ACCOUNTING')


def valid_chunk(p, item):
    if (type(p) is not dict or set(p) != {'index', 'row_start', 'rows_requested', 'bytes_requested', 'bytes_returned',
                                         'read_completion_unknown', 'decoder', 'geometry', 'histogram_rows_completed', 'accumulated_rows'}
            or any(type(p[k]) is not int for k in ('index', 'row_start', 'rows_requested', 'bytes_requested'))
            or not 1 <= p['index'] <= item['chunks'] or p['row_start'] != (p['index'] - 1) * ROW_CAP
            or p['rows_requested'] != min(ROW_CAP, item['schema']['rows'] - p['row_start'])
            or p['bytes_requested'] != p['rows_requested'] * item['schema']['row_bytes']
            or type(p['read_completion_unknown']) is not bool
            or any(type(p[k]) is not int or p[k] not in (0, p['rows_requested'])
                   for k in ('histogram_rows_completed', 'accumulated_rows'))
            or p['accumulated_rows'] > p['histogram_rows_completed']
            or (p['bytes_returned'] is not None and (type(p['bytes_returned']) is not int
                                                     or not 0 <= p['bytes_returned'] <= p['bytes_requested']))):
        raise ValueError('STOP_CHUNK_ACCOUNTING')
    d, g = p['decoder'], p['geometry']
    if type(d) is not dict or type(g) is not dict:
        raise ValueError('STOP_COMPONENT_ACCOUNTING')
    if p['histogram_rows_completed'] and (d.get('status') != 'COMPLETE' or g.get('status') != 'COMPLETE'):
        raise ValueError('STOP_HISTOGRAM_ACCOUNTING')
    if d:
        fields = ['TIME', 'RAWX', 'RAWY', 'X', 'Y', 'PI', 'FLAG', 'PATTERN', 'CCDNR']
        widths = [8, 2, 2, 4, 4, 2, 4, 1, 1]
        if (set(d) != {'status', 'phase', 'current_field', 'buffer_bytes_supplied', 'selected_field_bytes_decoded',
                      'completed_fields', 'rows_completed', 'current_conversion_completion_unknown'}
                or d['status'] not in ('IN_PROGRESS', 'COMPLETE', 'FAILED')
                or d['phase'] not in ('VALIDATING', 'CONVERTING', 'MASKING', 'FINALIZING', 'COMPLETE')
                or d['current_field'] not in [None, *fields] or type(d['completed_fields']) is not list
                or d['completed_fields'] != fields[:len(d['completed_fields'])]
                or type(d['buffer_bytes_supplied']) is not int or d['buffer_bytes_supplied'] != p['bytes_returned']
                or type(d['selected_field_bytes_decoded']) is not int
                or d['selected_field_bytes_decoded'] != p['rows_requested'] * sum(widths[:len(d['completed_fields'])])
                or type(d['rows_completed']) is not int or d['rows_completed'] not in (0, p['rows_requested'])
                or type(d['current_conversion_completion_unknown']) is not bool):
            raise ValueError('STOP_DECODER_ACCOUNTING')
        if (d['current_conversion_completion_unknown'] != (d['status'] == 'FAILED' and d['phase'] == 'CONVERTING')
                or (d['status'] == 'COMPLETE' and (d['phase'] != 'COMPLETE' or d['current_field'] is not None
                    or d['completed_fields'] != fields or d['rows_completed'] != p['rows_requested']))):
            raise ValueError('STOP_DECODER_ACCOUNTING')
    if g:
        if (set(g) != {'status', 'phase', 'input_rows', 'masked_rows', 'projection_attempted_rows',
                      'projection_completed_rows', 'rows_completed', 'current_projection_completion_unknown'}
                or g['status'] not in ('IN_PROGRESS', 'COMPLETE', 'FAILED')
                or g['phase'] not in ('VALIDATING', 'CONSTRUCTING', 'PROJECTING', 'PROJECTED', 'CLASSIFYING', 'STORING', 'FINALIZING', 'COMPLETE')
                or any(g[k] is not None and (type(g[k]) is not int or not 0 <= g[k] <= p['rows_requested'])
                       for k in ('input_rows', 'masked_rows'))
                or any(type(g[k]) is not int or not 0 <= g[k] <= p['rows_requested']
                       for k in ('projection_attempted_rows', 'projection_completed_rows', 'rows_completed'))
                or type(g['current_projection_completion_unknown']) is not bool):
            raise ValueError('STOP_GEOMETRY_ACCOUNTING')
        if (g['projection_completed_rows'] > g['projection_attempted_rows']
                or g['current_projection_completion_unknown'] != (g['status'] == 'FAILED' and g['phase'] == 'PROJECTING')
                or (g['status'] == 'COMPLETE' and (g['phase'] != 'COMPLETE' or g['input_rows'] != p['rows_requested']
                    or g['rows_completed'] != p['rows_requested'] or g['masked_rows'] is None
                    or g['projection_completed_rows'] != p['rows_requested'] - g['masked_rows']
                    or g['projection_attempted_rows'] != g['projection_completed_rows']))):
            raise ValueError('STOP_GEOMETRY_ACCOUNTING')


def valid_verification(v, item, complete=False):
    if type(v) is not dict:
        raise ValueError('STOP_VERIFICATION_ACCOUNTING')
    if not v and not complete:
        return
    if (set(v) != {'status', 'hash_bytes_returned', 'header_bytes_read'}
            or v['status'] not in ('IN_PROGRESS', 'FAILED', 'COMPLETE')
            or type(v['hash_bytes_returned']) is not int or not 0 <= v['hash_bytes_returned'] <= item['file_bytes']
            or (v['header_bytes_read'] is not None and (type(v['header_bytes_read']) is not int or v['header_bytes_read'] < 0))
            or (complete and (v['status'] != 'COMPLETE' or v['hash_bytes_returned'] != item['file_bytes']
                              or v['header_bytes_read'] is None))):
        raise ValueError('STOP_VERIFICATION_ACCOUNTING')


def validate_state(value, items):
    if type(value) is not dict or set(value) != {'status', 'cameras'} or value['status'] not in ('NOT_ATTEMPTED', 'ATTEMPTED', 'FAILED', 'COMPLETED'):
        raise ValueError('STOP_VALIDATION_STATE')
    if type(value['cameras']) is not list or len(value['cameras']) != 3:
        raise ValueError('STOP_VALIDATION_STATE')
    stopped = False
    for row, item in zip(value['cameras'], items, strict=True):
        if (type(row) is not dict or set(row) != {'slot', 'status', 'verification', 'accounting'}
                or type(row['slot']) is not int or row['slot'] != item['slot']
                or row['status'] not in ('NOT_ATTEMPTED', 'ATTEMPTED', 'FAILED', 'COMPLETED')
                or (stopped and row['status'] != 'NOT_ATTEMPTED')):
            raise ValueError('STOP_VALIDATION_ORDER')
        stopped |= row['status'] != 'COMPLETED'
        valid_progress(row['accounting'], item, complete=row['status'] == 'COMPLETED')
        valid_verification(row['verification'], item, complete=row['status'] == 'COMPLETED')
        if row['status'] == 'NOT_ATTEMPTED' and (row['accounting'] or row['verification']):
            raise ValueError('STOP_UNATTEMPTED_ACCOUNTING')
    statuses = [r['status'] for r in value['cameras']]
    if ((value['status'] == 'COMPLETED') != all(s == 'COMPLETED' for s in statuses)
            or (value['status'] == 'NOT_ATTEMPTED') != all(s == 'NOT_ATTEMPTED' for s in statuses)
            or (value['status'] == 'FAILED') != ('FAILED' in statuses)):
        raise ValueError('STOP_VALIDATION_STATUS')


def ledger(items, validation=None):
    _, _, counter = modules()
    rows, stopped = [], False
    for item in items:
        slot = item['slot']
        startpath, resultpath = HERE / f'camera-{slot}-start.json', HERE / f'camera-{slot}-result.json'
        chunks = list(HERE.glob(f'camera-{slot}-chunk-*.json'))
        if not startpath.exists():
            if resultpath.exists() or chunks:
                raise ValueError('STOP_ORPHAN_CAMERA')
            rows.append({'slot': slot, 'status': 'NOT_ATTEMPTED', 'verification': {}, 'accounting': {}})
            stopped = True
            continue
        if stopped or digest_json(C.read(startpath.name)) != digest_json({'slot': slot, 'camera': item['camera']}):
            raise ValueError('STOP_CAMERA_ORDER')
        if not resultpath.exists():
            rows.append({'slot': slot, 'status': 'INTERRUPTED', 'verification': None, 'accounting': None})
            stopped = True
            continue
        r = C.read(resultpath.name)
        if (type(r) is not dict or type(r.get('slot')) is not int or r.get('slot') != slot or r.get('status') not in ('OK', 'STOP')
                or set(r) != ({'slot', 'status', 'verification', 'accounting', 'summary'} if r.get('status') == 'OK'
                               else {'slot', 'status', 'verification', 'accounting', 'error_type', 'error_code'})):
            raise ValueError('STOP_CAMERA_RECEIPT')
        valid_progress(r['accounting'], item, complete=r['status'] == 'OK')
        valid_verification(r['verification'], item, complete=r['status'] == 'OK')
        if r['status'] == 'STOP':
            valid_failure(r)
        seen = set()
        for index in range(1, item['chunks'] + 1):
            sname, rname = chunk_name(slot, index, 'start'), chunk_name(slot, index, 'result')
            if not (HERE / sname).exists():
                break
            seen.add(sname)
            expected = {'slot': slot, 'index': index, 'row_start': (index - 1) * ROW_CAP,
                        'rows_requested': min(ROW_CAP, item['schema']['rows'] - (index - 1) * ROW_CAP)}
            expected['bytes_requested'] = expected['rows_requested'] * item['schema']['row_bytes']
            if digest_json(C.read(sname)) != digest_json(expected):
                raise ValueError('STOP_CHUNK_MARKER')
            if not (HERE / rname).exists():
                break
            seen.add(rname)
            cr = C.read(rname)
            if type(cr.get('slot')) is not int or cr.get('slot') != slot or cr.get('status') not in ('OK', 'STOP'):
                raise ValueError('STOP_CHUNK_RECEIPT')
            valid_chunk(cr.get('progress'), item)
            if cr['progress']['index'] != index:
                raise ValueError('STOP_CHUNK_ORDER')
            keys = {'slot', 'status', 'progress', 'increment_sha256'} if cr['status'] == 'OK' else {'slot', 'status', 'progress', 'error_type', 'error_code'}
            if set(cr) != keys:
                raise ValueError('STOP_CHUNK_RECEIPT')
            if cr['status'] == 'STOP':
                valid_failure(cr)
                if r['status'] == 'OK':
                    raise ValueError('STOP_FAILED_CHUNK_UNDER_OK_CAMERA')
                break
            p = cr['progress']
            if (p['bytes_returned'] != p['bytes_requested'] or p['read_completion_unknown']
                    or p['decoder'].get('status') != 'COMPLETE' or p['geometry'].get('status') != 'COMPLETE'
                    or p['histogram_rows_completed'] != p['rows_requested'] or p['accumulated_rows'] != p['rows_requested']):
                raise ValueError('STOP_FALSE_CHUNK_SUCCESS')
            if not isinstance(cr['increment_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', cr['increment_sha256']):
                raise ValueError('STOP_CHUNK_HASH')
        if {p.name for p in chunks} != seen or (r['status'] == 'OK' and len(seen) != 2 * item['chunks']):
            raise ValueError('STOP_CHUNK_SET')
        if r['status'] == 'OK':
            validate_summary(r['summary'], item['config'], counter, complete=True)
            if validation is not None:
                v = validation['cameras'][slot - 1]
                validation['status'], v['status'] = 'ATTEMPTED', 'ATTEMPTED'
                try:
                    verify_product(item, v['verification'])
                    summary = measure(item, v['accounting'], compare_chunks=True)
                    if summary != r['summary'] or v['accounting'] != r['accounting'] or v['verification'] != r['verification']:
                        raise ValueError('STOP_CAMERA_REPLAY')
                except Exception:
                    validation['status'], v['status'] = 'FAILED', 'FAILED'
                    raise
                v['status'] = 'COMPLETED'
        stopped = r['status'] != 'OK'
        rows.append({k: r[k] for k in ('slot', 'status', 'verification', 'accounting')})
    if validation is not None and all(v['status'] == 'COMPLETED' for v in validation['cameras']):
        validation['status'] = 'COMPLETED'
    return rows


def worker():
    C.DEADLINE = time.monotonic() + SECONDS
    result = {'status': 'STOP'}
    try:
        check_files()
        verify_binding()
        C.save('worker-start.json', {'binding_sha256': C.sha(HERE / 'run-start.json')})
        for item in C.read('run-start.json')['manifest']['cameras']:
            C.checkpoint()
            C.save(f"camera-{item['slot']}-start.json", {'slot': item['slot'], 'camera': item['camera']})
            verification, accounting = {}, {}
            try:
                verify_product(item, verification)
                summary = measure(item, accounting, persist=True)
                C.save(f"camera-{item['slot']}-result.json", {'slot': item['slot'], 'status': 'OK',
                       'verification': verification, 'accounting': accounting, 'summary': summary})
            except Exception as error:
                C.save(f"camera-{item['slot']}-result.json", {'slot': item['slot'], 'status': 'STOP',
                       'verification': verification, 'accounting': accounting, **failure(error)}, terminal=True)
                raise
        result['status'] = PASS
    except Exception as error:
        LOGGER.exception('Count worker stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(failure(error))
    finally:
        C.DEADLINE = None
        try:
            result['ledger'] = ledger(C.read('run-start.json')['manifest']['cameras'])
        except Exception:
            LOGGER.exception('Count ledger incomplete', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
            result.update(status='STOP', ledger=fallback(), error_code='STOP_LEDGER_UNVERIFIED')
        result.update(artifacts=artifacts(), resource_usage=C.resource_usage(exclude=('worker-result.json', 'outcome.json')))
        C.save('worker-result.json', result, terminal=True, peak_key='peak_memory_bytes')
    return 0 if result['status'] == PASS else 1


def assess(code, validation):
    C.DEADLINE = time.monotonic() + SECONDS
    try:
        check_files()
        verify_binding()
        items = C.read('run-start.json')['manifest']['cameras']
        rows = ledger(items, validation)
        w = C.read('worker-result.json') if (HERE / 'worker-result.json').exists() else None
        if w is not None:
            required = {'status', 'ledger', 'artifacts', 'resource_usage', 'peak_memory_bytes'}
            safe_terminal(w, required, required | {'error_type', 'error_code'})
        if w and (w['ledger'] != rows or w['artifacts'] != artifacts(('worker-result.json', 'outcome.json'))
                  or w['resource_usage'] != C.resource_usage(exclude=('worker-result.json', 'outcome.json'))
                  or type(w['peak_memory_bytes']) is not int or w['peak_memory_bytes'] <= 0):
            raise ValueError('STOP_WORKER_CLOSURE')
        success = code == 0 and w is not None and w['status'] == PASS
        validate_state(validation, items)
        if success and (any(r['status'] != 'OK' for r in rows) or w['peak_memory_bytes'] > C.MEMORY_CAP
                        or validation['status'] != 'COMPLETED'
                        or C.read('worker-start.json') != {'binding_sha256': C.sha(HERE / 'run-start.json')}):
            raise ValueError('STOP_FALSE_SUCCESS')
        C.checkpoint()
        return {'status': PASS if success else 'STOP', 'worker_returncode': code, 'ledger': rows,
                'worker_peak_memory_bytes': w['peak_memory_bytes'] if w else None,
                'worker_error_code': w.get('error_code') if w else None,
                'resource_usage': C.resource_usage(exclude=('outcome.json',)),
                'source_masks_applied': False, 'exposure_or_significance_computed': False,
                'private_event_or_sky_values_persisted': False}
    finally:
        C.DEADLINE = None


def run():
    check_files()
    if any((HERE / name).exists() for name in FIXED_FILES) or any(HERE.glob('camera-*.json')):
        raise ValueError('STOP_ALREADY_ATTEMPTED')
    validation = state()
    result = {'status': 'STOP', 'worker_returncode': None, 'assessment_completed': False}
    try:
        C.save('run-start.json', binding(PROTOCOL))
        with (HERE / 'protocol.snapshot.md').open('xb') as stream:
            stream.write(PROTOCOL.read_bytes())
        helper = C.load_pinned('c9_deadline', C.HELPER, C.HELPER_HASH)
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), '-B', str(SOURCE), '_worker'], SECONDS)
        result['worker_returncode'] = code
        result.update(assess(code, validation))
        result['assessment_completed'] = True
    except Exception as error:
        LOGGER.exception('Count parent stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(failure(error), ledger=fallback())
    finally:
        C.DEADLINE = None
        result.update(parent_validation=validation, artifacts=artifacts(('outcome.json',)), source_sha256=C.sha(SOURCE, monitor=False))
        C.save('outcome.json', result, terminal=True, peak_key='parent_peak_memory_bytes')
    print(result['status'])
    return 0 if result['status'] == PASS else 1


def replay():
    outcome = C.read('outcome.json')
    required = {'status', 'worker_returncode', 'assessment_completed', 'ledger', 'parent_validation',
                'artifacts', 'source_sha256', 'parent_peak_memory_bytes'}
    allowed = required | {'error_type', 'error_code', 'worker_peak_memory_bytes', 'worker_error_code',
                          'resource_usage', 'source_masks_applied', 'exposure_or_significance_computed',
                          'private_event_or_sky_values_persisted'}
    safe_terminal(outcome, required, allowed)
    if outcome['worker_returncode'] is not None and type(outcome['worker_returncode']) is not int:
        raise ValueError('STOP_WORKER_RETURNCODE')
    if type(outcome.get('assessment_completed')) is not bool:
        raise ValueError('STOP_ASSESSMENT_FLAG')
    if outcome['artifacts'] != artifacts(('outcome.json',)) or outcome['source_sha256'] != C.sha(SOURCE):
        raise ValueError('STOP_OUTCOME_ARTIFACTS')
    items = manifest()['cameras']
    validate_state(outcome['parent_validation'], items)
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
    validation = state()
    try:
        expected = assess(outcome['worker_returncode'], validation)
        if peak > C.MEMORY_CAP:
            expected['status'] = 'STOP'
        if any(outcome.get(k) != v for k, v in expected.items()) or outcome['parent_validation'] != validation:
            raise ValueError('STOP_OUTCOME_REPLAY')
    except Exception:
        print(json.dumps({'replay_status': 'FAILED', 'additional_numerical_pass': validation}, allow_nan=False))
        raise
    print(json.dumps({'replay_status': 'PASS_OFFLINE_REPLAY', 'status': expected['status'],
                      'additional_numerical_pass': validation}, allow_nan=False))


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
        LOGGER.exception('Count command stopped', exc_info=(RuntimeError, RuntimeError('Safe code only'), None))
        print(failure(error).get('error_code') or 'STOP_INTERNAL')
        raise SystemExit(1) from None
