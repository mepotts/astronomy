"""One private raw-HTML metadata acquisition; no semantic adjudication."""

import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import json
import logging
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M2-2026-09-13.md'
BASE = HERE.parent / 'XMM-RXJ-M0-2026-09-13-data/listing.py'
BASE_HASH = 'fe664f73447eae02345358b03c6c7754628e7d9f240028c8720ed2786b462a38'
URL = 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&name=SUMMAR&extension=HTM'
CAP, JSON_CAP, RESERVE = 262144, 1048576, 65536
PASS = 'SUMMARY_HTML_RETAINED_UNADJUDICATED'
LOGGER = logging.getLogger(__name__)
PINS = {
    'XMM-RXJ-M0-2026-09-13-data/listing.py': BASE_HASH,
    'XMM-RXJ-M0-2026-09-13-data/test_listing.py': '963e082830d97ce2c743d2003799c2d846e0ead7139ea670a7f5ba8df0e9fdb6',
    'XMM-RXJ-M0-2026-09-13.md': 'b864f9daee136bb27da7d0a94bcd095fdc86c6ea92636ac337f4aab3a1209e18',
    'XMM-RXJ-M1-2026-09-13-data/listing.py': '953d28ef3c079faf11a660bdae8c7c32cd1d8e0259c72bde9c0f794d30b5fb91',
    'XMM-RXJ-M1-2026-09-13-data/test_listing.py': '0885a3b200f4a4f1bd8281b963e19362b2bce41e995ebc7aafc0d79df5ae57ae',
    'XMM-RXJ-M1-2026-09-13-data/outcome.json': '159ee0322ae964ec20e4f79471e927dc7dc93a08adcb0a1f8b2b751ca843b384',
    'XMM-RXJ-M1-2026-09-13-data/response.body': '75d75114d209795f7177124f3eb44fc5c6f6d15e3aa4f485d36364df9aeab635',
    'XMM-RXJ-M1-NEXT-2026-09-13.md': 'feeab4a4c3b552f544097c0a89ff17019078bb3faf9981f7f1d5a4c78668c1db',
}


def disposition(values):
    result = {'status': 'ABSENT', 'kind': None, 'filename_sha256': None}
    if not values:
        return result
    if (len(values) != 1 or type(values[0]) is not str or len(values[0]) > 2048
            or any(ord(c) < 32 or ord(c) > 126 for c in values[0])):
        return {**result, 'status': 'REJECTED'}
    match = re.fullmatch(r'(inline|attachment)(?:\s*;\s*filename\s*=\s*(?:"([A-Za-z0-9._-]+)"|([A-Za-z0-9._-]+)))?\s*', values[0], re.IGNORECASE)
    if not match:
        return {**result, 'status': 'REJECTED'}
    kind, filename = match[1].lower(), match[2] or match[3]
    if filename is None:
        return {**result, 'status': 'NO_FILENAME', 'kind': kind}
    # PPS positions, not an invented instrument or exposure for this observation.
    if not re.fullmatch(r'P0851180501[A-Z0-9]{2}[A-Z][0-9]{3}SUMMAR[A-Z0-9]{4}\.HTM', filename):
        return {**result, 'status': 'REJECTED'}
    return {'status': 'MATCH', 'kind': kind, 'filename_sha256': hashlib.sha256(filename.encode()).hexdigest()}


def load_core():
    raw = BASE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_HASH:
        raise ValueError('STOP_BASE_HASH')
    replacements = ((b"'index.html'", b"'summary.html'", 6),
                    (b"'listing.py', 'test_listing.py', '.gitattributes'", b"'listing.py', 'test_listing.py', '.gitattributes', '.gitignore'", 1),
                    (b'products_fetched', b'science_products_fetched', 3))
    for old, new, count in replacements:
        if raw.count(old) != count:
            raise ValueError('STOP_ADAPTER_LITERAL_COUNT')
        raw = raw.replace(old, new)
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(BASE), 'exec')
    spec = importlib.util.spec_from_file_location('rxj_m2_base', BASE, loader=Loader('rxj_m2_base', str(BASE)))
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    original_binding, original_response = core.binding, core.validate_response_artifacts
    core.HERE, core.SOURCE, core.PROTOCOL = HERE, SOURCE, PROTOCOL
    core.URL, core.CAP, core.JSON_CAP, core.PASS = URL, CAP, JSON_CAP, PASS
    core.ARTIFACTS += ('transport.json',)

    def binding(protocol):
        result = original_binding(protocol)
        for name, expected in PINS.items():
            path = HERE.parent / name
            if core.sha(path) != expected:
                raise ValueError('STOP_M2_DEPENDENCY_HASH')
            result['dependencies'][str(path)] = expected
        result.update(body_filename='summary.html', aggregate_receipt_bytes=JSON_CAP,
                      receipt_bytes=65536, terminal_reserve_bytes=RESERVE,
                      gitignore_sha256=core.sha(core.HERE / '.gitignore'),
                      attributes_sha256=core.sha(core.HERE / '.gitattributes'),
                      interpretation='UNADJUDICATED', adapter_counts=[6, 1, 3])
        return result

    def save(name, value):
        data = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
        ceiling = JSON_CAP if name == 'outcome.json' else JSON_CAP - RESERVE
        if len(data) > 65536 or sum(p.stat().st_size for p in core.HERE.glob('*.json')) + len(data) > ceiling:
            raise ValueError('STOP_RECEIPT_CAP')
        with (core.HERE / name).open('xb') as stream:
            stream.write(data)

    def validate_http_schema(http):
        if (type(http) is not dict or set(http) != {'status', 'url', 'actual_url_matches', 'headers', 'disposition'}
                or http['url'] != URL or type(http['actual_url_matches']) is not bool
                or type(http['status']) is not int or not 100 <= http['status'] <= 599):
            raise ValueError('STOP_HTTP_SCHEMA')
        headers = http['headers']
        if (type(headers) is not dict or not set(headers) <= set(core.SAFE_HEADERS)
                or any(type(v) is not list or len(v) != 1 or type(v[0]) is not str
                       or len(v[0]) > 1024 or any(ord(c) < 32 or ord(c) > 126 for c in v[0]) for v in headers.values())):
            raise ValueError('STOP_SAFE_HEADER_SCHEMA')
        d = http['disposition']
        if type(d) is not dict or set(d) != {'status', 'kind', 'filename_sha256'}:
            raise ValueError('STOP_DISPOSITION_RECEIPT')
        allowed = {'ABSENT', 'REJECTED', 'NO_FILENAME', 'MATCH'}
        if (d['status'] not in allowed or (d['status'] in ('ABSENT', 'REJECTED') and (d['kind'] is not None or d['filename_sha256'] is not None))
                or (d['status'] in ('NO_FILENAME', 'MATCH') and d['kind'] not in ('inline', 'attachment'))
                or (d['status'] == 'NO_FILENAME' and d['filename_sha256'] is not None)
                or (d['status'] == 'MATCH' and (type(d['filename_sha256']) is not str or not re.fullmatch(r'[0-9a-f]{64}', d['filename_sha256'])))):
            raise ValueError('STOP_DISPOSITION_RECEIPT')

    def validate_http(http, body_bytes=None):
        validate_http_schema(http)
        if not http['actual_url_matches']:
            raise ValueError('STOP_HTTP_IDENTITY')
        if http['status'] != 200:
            raise ValueError('STOP_HTTP_STATUS')
        headers = {k: v[0] for k, v in http['headers'].items()}
        if headers.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
            raise ValueError('STOP_CONTENT_ENCODING')
        if headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'text/html':
            raise ValueError('STOP_NOT_HTML')
        if http['disposition']['status'] == 'REJECTED':
            raise ValueError('STOP_DISPOSITION')
        if 'Content-Length' in headers:
            length = headers['Content-Length']
            if not re.fullmatch(r'[0-9]{1,9}', length) or not 0 < int(length) <= CAP:
                raise ValueError('STOP_CONTENT_LENGTH')
            if body_bytes is not None and int(length) != body_bytes:
                raise ValueError('STOP_RESPONSE_LENGTH')

    def collect():
        import requests

        if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
            raise ValueError('STOP_HTTP_PARSER_CAP')
        with requests.Session() as session:
            session.trust_env, session.auth = False, None
            session.cookies.clear()
            with session.get(URL, timeout=(5, 15), stream=True, allow_redirects=False,
                             headers={'Accept-Encoding': 'identity'}) as response:
                http = {'status': response.status_code, 'url': URL, 'actual_url_matches': response.url == URL,
                        'headers': {k: response.raw.headers.getlist(k) for k in core.SAFE_HEADERS if response.raw.headers.getlist(k)},
                        'disposition': disposition(response.raw.headers.getlist('Content-Disposition'))}
                validate_http_schema(http)  # Discard unsafe/raw header text before persistence.
                save('http.json', http)
                validate_http(http)
                count = 0
                with (core.HERE / 'summary.html').open('xb') as stream:
                    while True:
                        chunk = response.raw.read(min(8192, CAP - count + 1), decode_content=False)
                        if not chunk:
                            break
                        keep = chunk[:CAP - count]
                        stream.write(keep)
                        count += len(keep)
                        if len(chunk) > len(keep):
                            raise ValueError('STOP_BYTE_CAP')
                save('transport.json', {'eof': True, 'bytes': count})
                if not count:
                    raise ValueError('STOP_EMPTY_BODY')
                validate_http(http, count)

    def validate_response_artifacts():
        original_response()
        path = core.HERE / 'transport.json'
        if path.exists():
            body = core.body_record()
            if body is None or core.read('transport.json') != {'eof': True, 'bytes': body['bytes']}:
                raise ValueError('STOP_TRANSPORT_RECEIPT')
            if json.dumps(core.read('transport.json'), sort_keys=True) != json.dumps({'eof': True, 'bytes': body['bytes']}, sort_keys=True):
                raise ValueError('STOP_TRANSPORT_RECEIPT')

    def parse_index(raw_body):
        validate_response_artifacts()
        if not 0 < len(raw_body) <= CAP or not (core.HERE / 'transport.json').exists():
            raise ValueError('STOP_TRANSPORT_INCOMPLETE')
        return {'transport_eof': True, 'semantic_identity': 'UNADJUDICATED', 'science_products_fetched': 0}

    core.binding, core.save, core.collect = binding, save, collect
    core.validate_http_schema, core.validate_http = validate_http_schema, validate_http
    core.validate_response_artifacts, core.parse_index = validate_response_artifacts, parse_index
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
        LOGGER.exception('M2 command stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        print('STOP_M2_COMMAND')
        raise SystemExit(1) from None
