"""One bounded TAP product-name query, composed from frozen M0 transport."""

import hashlib
import importlib.machinery
import importlib.util
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M1-2026-09-13.md'
BASE = HERE.parent / 'XMM-RXJ-M0-2026-09-13-data/listing.py'
BASE_HASH = 'fe664f73447eae02345358b03c6c7754628e7d9f240028c8720ed2786b462a38'
QUERY = "SELECT obsid,filename\nFROM xsa.data_product\nWHERE obsid = '0851180501'"
URL = 'https://nxsa.esac.esa.int/tap-server/tap/sync?' + urlencode(
    [('REQUEST', 'doQuery'), ('LANG', 'ADQL'), ('FORMAT', 'json'), ('QUERY', QUERY)])
CAP = 1048576
PASS = 'RETURNED_PRODUCT_NAME_RECORDS_ONLY_COMPLETENESS_UNKNOWN'
LOGGER = logging.getLogger(__name__)
PINS = {
    'XMM-RXJ-M0-2026-09-13-data/listing.py': BASE_HASH,
    'XMM-RXJ-M0-2026-09-13-data/test_listing.py': '963e082830d97ce2c743d2003799c2d846e0ead7139ea670a7f5ba8df0e9fdb6',
    'XMM-RXJ-M0-2026-09-13.md': 'b864f9daee136bb27da7d0a94bcd095fdc86c6ea92636ac337f4aab3a1209e18',
    'XMM-RXJ-M0-2026-09-13-data/outcome.json': '57e0e1ec8a149a6e90a1e1847f089c1a4d3529480f1416704f3ac964f37d82c7',
    'XMM-RXJ-M0-NEXT-2026-09-13.md': 'b4358d05d0d1cd4cf945867514b9c5bd3c6bd859dfe17069b5b52d86a8842e14',
    'XMM-C0b1-2026-09-12-data/schema-response.body': '5cccb1603a4e4c4361ba8c6dd9bf974e58bd476fed0d28c51c29db9dd351ceab',
    'XMM-EXOD-ELIGIBILITY-2026-09-12-data/product-table-schema.json': '88e13f868f7487e78a147aec13f5a2280881c3f276350da79e8d75a8e4062fb3',
    'XMM-EXOD-ELIGIBILITY-2026-09-12-data/receipt.json': 'e51772e9ec0526b4670c89267348dc9913099e702f626af1f0b83cca4800d27a',
}


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('STOP_DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def parse_records(raw):
    if not 0 < len(raw) <= CAP:
        raise ValueError('STOP_BODY_LENGTH')
    try:
        value = json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=object_pairs)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError('STOP_JSON_ENCODING_OR_STRUCTURE') from None
    if type(value) is not dict or set(value) != {'metadata', 'data'}:
        raise ValueError('STOP_JSON_SCHEMA')
    metadata = value['metadata']
    keys = {'name', 'datatype', 'xtype', 'arraysize', 'description', 'unit', 'ucd', 'utype'}
    if type(metadata) is not list or len(metadata) != 2:
        raise ValueError('STOP_COLUMN_SCHEMA')
    for column in metadata:
        if (type(column) is not dict or set(column) != keys or column['datatype'] != 'char'
                or column['arraysize'] != '*' or column['xtype'] is not None
                or type(column['name']) is not str or column['name'] not in ('obsid', 'filename')):
            raise ValueError('STOP_COLUMN_SCHEMA')
        for key in ('description', 'unit', 'ucd', 'utype'):
            field = column[key]
            if field is not None and (type(field) is not str or len(field) > 1024
                    or any(ord(c) < 32 or 127 <= ord(c) < 160 for c in field)):
                raise ValueError('STOP_COLUMN_SCHEMA')
    names = [c['name'] for c in metadata]
    if set(names) != {'obsid', 'filename'} or type(value['data']) is not list:
        raise ValueError('STOP_ROW_SCHEMA')
    counts = Counter()
    for row in value['data']:
        if type(row) is not list or len(row) != 2 or any(type(v) is not str for v in row):
            raise ValueError('STOP_ROW_SCHEMA')
        obsid, filename = row[names.index('obsid')], row[names.index('filename')]
        if obsid != '0851180501':
            raise ValueError('STOP_OBSERVATION_IDENTITY')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,254}', filename):
            raise ValueError('STOP_FILENAME_BASENAME')
        counts[filename] += 1
    folded = Counter(name.lower() for name in counts)
    canonical = json.dumps(sorted(counts.items()), separators=(',', ':'), ensure_ascii=True).encode()
    return {'observation': '0851180501', 'returned_rows': sum(counts.values()),
            'unique_filenames': len(counts), 'duplicate_rows': sum(n - 1 for n in counts.values()),
            'duplicate_filename_groups': sum(n > 1 for n in counts.values()),
            'casefold_ambiguous_groups': sum(n > 1 for n in folded.values()),
            'canonical_filename_multiplicities_sha256': hashlib.sha256(canonical).hexdigest(),
            'completeness': 'UNKNOWN', 'products_fetched': 0}


def load_core():
    raw = BASE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_HASH:
        raise ValueError('STOP_BASE_HASH')
    # Only the raw entity's filename changes in the inherited harness.
    # Compile this verified buffer; never reread unchecked source or cached pyc.
    if raw.count(b"'index.html'") != 6:
        raise ValueError('STOP_ADAPTER_LITERAL_COUNT')
    adapted = raw.replace(b"'index.html'", b"'response.body'")
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(adapted, str(BASE), 'exec')
    spec = importlib.util.spec_from_file_location('rxj_m1_base', BASE, loader=Loader('rxj_m1_base', str(BASE)))
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    original_binding = core.binding
    core.HERE, core.SOURCE, core.PROTOCOL = HERE, SOURCE, PROTOCOL
    core.URL, core.CAP, core.PASS = URL, CAP, PASS
    core.parse_index = parse_records

    def binding(protocol):
        result = original_binding(protocol)
        for name, expected in PINS.items():
            path = HERE.parent / name
            if core.sha(path) != expected:
                raise ValueError('STOP_M1_DEPENDENCY_HASH')
            result['dependencies'][str(path)] = expected
        result.update(query=QUERY, body_filename='response.body', receipt_bytes=65536,
                      aggregate_receipt_bytes=262144, completeness='UNKNOWN',
                      adapter_literal_replacements=6)
        return result

    def validate_http(http, body_bytes=None):
        core.validate_http_schema(http)
        if http['status'] != 200:
            raise ValueError('STOP_HTTP_STATUS')
        headers = http['headers']
        if headers.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
            raise ValueError('STOP_CONTENT_ENCODING')
        if headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
            raise ValueError('STOP_NOT_JSON')
        if 'Content-Length' in headers:
            if not re.fullmatch(r'[0-9]+', headers['Content-Length']):
                raise ValueError('STOP_CONTENT_LENGTH')
            if body_bytes is not None and int(headers['Content-Length']) != body_bytes:
                raise ValueError('STOP_RESPONSE_LENGTH')

    core.binding, core.validate_http = binding, validate_http
    return core


if __name__ == '__main__':
    try:
        module = load_core()
        if sys.argv[1:] == ['run']:
            raise SystemExit(module.run())
        if sys.argv[1:] == ['_worker']:
            raise SystemExit(module.worker())
        if sys.argv[1:] == ['replay']:
            module.replay()
        else:
            raise ValueError('STOP_COMMAND')
    except Exception:
        LOGGER.exception('M1 command stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        print('STOP_M1_COMMAND')
        raise SystemExit(1) from None
