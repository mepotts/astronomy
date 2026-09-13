"""One bounded observation-index GET, no products or linked requests."""

import hashlib
import http.client as http_client
import importlib.machinery
import importlib.util
import json
import logging
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M0-2026-09-13.md'
DECISION = HERE.parent / 'XMM-NEXT-CONTROL-DECISION-2026-09-12.md'
DECISION_HASH = 'beb4a8edda667ad4adb75dad773600a8276278d3d473e276ed5d34b2e3b5b7aa'
CORE = HERE.parent / 'XMM-C0c-2026-09-12-data/listing.py'
CORE_HASH = '6dfc1715fa477a69687fd54a01a6cd61abd26be99519f18fd4e9297cd3091e31'
CORE_TEST_HASH = '30475b5119844d1f28300bd03d40e1efeb404603d963c2580055079a934acbb1'
HELPER = HERE.parents[1] / 'dyson-revet/scripts/check_e_release.py'
HELPER_HASH = '11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd'
URL = 'https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0851180501/'
INDEX_PATH = '/FTP/xmm/data/rev0/0851180501/'
CAP, SECONDS, JSON_CAP = 65536, 30, 262144
PASS = 'OBSERVATION_INDEX_WITH_PPS_LINK_RETAINED'
LOGGER = logging.getLogger(__name__)
SAFE_HEADERS = ('Content-Type', 'Content-Length', 'Content-Encoding', 'Date', 'ETag', 'Last-Modified')
ARTIFACTS = ('run-start.json', 'protocol.snapshot.md', 'worker-start.json', 'http.json',
             'index.html', 'worker-result.json', 'outcome.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def failure(error):
    message = str(error)
    return {'error_type': type(error).__name__, 'error_code': message if isinstance(error, ValueError)
            and re.fullmatch(r'STOP_[A-Z0-9_]+', message) else None}


def save(name, value):
    raw = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    if len(raw) > 65536 or sum(p.stat().st_size for p in HERE.glob('*.json')) + len(raw) > JSON_CAP:
        raise ValueError('STOP_RECEIPT_CAP')
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


def read(name):
    path = HERE / name
    if path.stat().st_size > 65536:
        raise ValueError('STOP_RECEIPT_CAP')
    return json.loads(path.read_bytes())


def check_files():
    allowed = set(ARTIFACTS) | {'listing.py', 'test_listing.py', '.gitattributes'}
    for p in HERE.rglob('*'):
        if p == HERE / '__pycache__' or (p.suffix == '.pyc' and p.parent == HERE / '__pycache__'):
            continue
        if p.parent != HERE or not p.is_file() or p.name not in allowed:
            raise ValueError('STOP_UNEXPECTED_ARTIFACT')
    if sum(p.stat().st_size for p in HERE.glob('*.json')) > JSON_CAP:
        raise ValueError('STOP_RECEIPT_CAP')


def artifacts():
    check_files()
    return {name: sha(HERE / name) for name in ARTIFACTS if name != 'outcome.json' and (HERE / name).exists()}


def binding(protocol):
    dependencies = {str(HELPER): HELPER_HASH, str(CORE): CORE_HASH,
                    str(CORE.with_name('test_listing.py')): CORE_TEST_HASH, str(DECISION): DECISION_HASH}
    if any(sha(Path(p)) != h for p, h in dependencies.items()):
        raise ValueError('STOP_DEPENDENCY_HASH')
    return {'url': URL, 'cap': CAP, 'worker_seconds': SECONDS, 'source_sha256': sha(SOURCE),
            'tests_sha256': sha(HERE / 'test_listing.py'), 'protocol_sha256': sha(protocol),
            'dependencies': dependencies, 'runtime': {'python': sys.version,
                    'executable': str(Path(sys.executable).resolve())}}


def verify_binding():
    if json.dumps(read('run-start.json'), sort_keys=True) != json.dumps(binding(HERE / 'protocol.snapshot.md'), sort_keys=True):
        raise ValueError('STOP_BINDING')


def deadline_helper():
    raw = HELPER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != HELPER_HASH:
        raise ValueError('STOP_HELPER_HASH')
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(HELPER), 'exec')
    spec = importlib.util.spec_from_file_location('rxj_m0_deadline', HELPER, loader=Loader('rxj_m0_deadline', str(HELPER)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_http_schema(http):
    if (type(http) is not dict or set(http) != {'status', 'url', 'headers'} or http['url'] != URL
            or type(http['status']) is not int or not 100 <= http['status'] <= 599):
        raise ValueError('STOP_HTTP_IDENTITY')
    h = http['headers']
    if type(h) is not dict or not set(h) <= set(SAFE_HEADERS) or any(type(v) is not str for v in h.values()):
        raise ValueError('STOP_HEADER_SCHEMA')


def validate_http(http, body_bytes=None):
    validate_http_schema(http)
    if http['status'] != 200:
        raise ValueError('STOP_HTTP_STATUS')
    h = http['headers']
    if h.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
        raise ValueError('STOP_CONTENT_ENCODING')
    if h.get('Content-Type', '').split(';', 1)[0].strip().lower() not in ('text/html', 'application/xhtml+xml'):
        raise ValueError('STOP_NOT_HTML')
    if 'Content-Length' in h:
        if not re.fullmatch(r'[0-9]+', h['Content-Length']):
            raise ValueError('STOP_CONTENT_LENGTH')
        if body_bytes is not None and int(h['Content-Length']) != body_bytes:
            raise ValueError('STOP_RESPONSE_LENGTH')


def collect():
    import requests

    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError('STOP_HTTP_PARSER_CAP')
    with requests.Session() as session:
        session.trust_env = False
        session.auth = None
        session.cookies.clear()
        with session.get(URL, timeout=(5, 15), stream=True, allow_redirects=False,
                         headers={'Accept-Encoding': 'identity'}) as response:
            receipt = {'status': response.status_code, 'url': response.url,
                       'headers': {k: response.headers[k] for k in SAFE_HEADERS if k in response.headers}}
            save('http.json', receipt)
            validate_http(receipt)
            count = 0
            with (HERE / 'index.html').open('xb') as stream:
                while True:
                    chunk = response.raw.read(min(8192, CAP - count + 1), decode_content=False)
                    if not chunk:
                        break
                    keep = chunk[:CAP - count]
                    stream.write(keep)
                    count += len(keep)
                    if len(chunk) > len(keep):
                        raise ValueError('STOP_BYTE_CAP')
            if not count:
                raise ValueError('STOP_EMPTY_INDEX')
            validate_http(receipt, count)


class Index(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.starts, self.ends, self.texts, self.hrefs, self.active = {}, {}, {'title': [], 'h1': []}, [], []

    def handle_starttag(self, tag, attrs):
        self.starts[tag] = self.starts.get(tag, 0) + 1
        if tag in self.texts:
            self.active.append(tag)
        if tag == 'a':
            hrefs = [v for k, v in attrs if k == 'href']
            if len(hrefs) != 1 or hrefs[0] is None:
                raise ValueError('STOP_ANCHOR_SCHEMA')
            self.hrefs.append(hrefs[0])

    def handle_endtag(self, tag):
        self.ends[tag] = self.ends.get(tag, 0) + 1
        if tag in self.texts and (not self.active or self.active.pop() != tag):
            raise ValueError('STOP_INDEX_STRUCTURE')

    def handle_data(self, data):
        for tag in self.active:
            self.texts[tag].append(data)


def parse_index(raw):
    if not 0 < len(raw) <= CAP:
        raise ValueError('STOP_BODY_LENGTH')
    try:
        text = raw.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        raise ValueError('STOP_INDEX_ENCODING') from None
    if not re.search(r'</body>\s*</html>\s*\Z', text, re.IGNORECASE):
        raise ValueError('STOP_INDEX_FOOTER')
    parser = Index()
    parser.feed(text)
    parser.close()
    if parser.active or any(parser.starts.get(k) != 1 or parser.ends.get(k) != 1 for k in ('html', 'body', 'title', 'h1')):
        raise ValueError('STOP_INDEX_STRUCTURE')
    expected = 'Index of ' + INDEX_PATH.rstrip('/')
    if any(' '.join(''.join(parser.texts[k]).split()).rstrip('/') != expected for k in ('title', 'h1')):
        raise ValueError('STOP_INDEX_IDENTITY')
    pps = [v for v in parser.hrefs if v in ('PPS/', INDEX_PATH + 'PPS/', URL + 'PPS/')]
    if len(pps) != 1:
        raise ValueError('STOP_PPS_CHILD')
    return {'observation': '0851180501', 'anchor_count': len(parser.hrefs), 'pps_url': URL + 'PPS/',
            'products_fetched': 0, 'pps_listing_fetched': False}


def body_record():
    path = HERE / 'index.html'
    if not path.exists():
        return None
    if path.stat().st_size > CAP:
        raise ValueError('STOP_BODY_LENGTH')
    return {'bytes': path.stat().st_size, 'sha256': sha(path)}


def worker():
    result = {'status': 'STOP', 'request_invocations': 0}
    try:
        check_files()
        verify_binding()
        save('worker-start.json', {'url': URL, 'request_invocations': 1})
        result['request_invocations'] = 1
        collect()
        result['index'] = parse_index((HERE / 'index.html').read_bytes())
        result['status'] = PASS
    except Exception as error:
        LOGGER.exception('Index worker stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(failure(error))
    finally:
        result['body'] = body_record()
        save('worker-result.json', result)
    return 0 if result['status'] == PASS else 1


def assess(code):
    if type(code) is not int:
        raise ValueError('STOP_WORKER_RETURNCODE')
    check_files()
    verify_binding()
    validate_response_artifacts()
    attempts = int((HERE / 'worker-start.json').exists())
    if attempts and json.dumps(read('worker-start.json'), sort_keys=True) != json.dumps({'url': URL, 'request_invocations': 1}, sort_keys=True):
        raise ValueError('STOP_WORKER_MARKER')
    w = read('worker-result.json') if (HERE / 'worker-result.json').exists() else None
    if w is not None:
        keys = {'status', 'request_invocations', 'body', 'index'} if w.get('status') == PASS else {'status', 'request_invocations', 'body', 'error_type', 'error_code'}
        if (set(w) != keys or w.get('status') not in ('STOP', PASS) or type(w.get('request_invocations')) is not int
                or w['request_invocations'] != attempts
                or json.dumps(w['body'], sort_keys=True) != json.dumps(body_record(), sort_keys=True)):
            raise ValueError('STOP_WORKER_RECEIPT')
        if w['status'] == 'STOP' and (not isinstance(w['error_type'], str) or not w['error_type'].isidentifier()
                or (w['error_code'] is not None and (not isinstance(w['error_code'], str)
                    or not re.fullmatch(r'STOP_[A-Z0-9_]+', w['error_code'])))):
            raise ValueError('STOP_FAILURE_SCHEMA')
    success = code == 0 and w is not None and w['status'] == PASS
    if success:
        validate_http(read('http.json'), w['body']['bytes'])
        if attempts != 1 or json.dumps(w['index'], sort_keys=True) != json.dumps(parse_index((HERE / 'index.html').read_bytes()), sort_keys=True):
            raise ValueError('STOP_INDEX_REPLAY')
    return {'status': PASS if success else 'STOP', 'worker_returncode': code, 'request_invocations': attempts,
            'products_fetched': 0, 'index': w['index'] if success else None,
            'worker_error_code': w.get('error_code') if w else 'STOP_WORKER_INTERRUPTED'}


def validate_response_artifacts():
    has_http = (HERE / 'http.json').exists()
    has_body = (HERE / 'index.html').exists()
    if ((has_http or has_body) and not (HERE / 'worker-start.json').exists()) or (has_body and not has_http):
        raise ValueError('STOP_ORPHAN_RESPONSE')
    if has_http:
        validate_http_schema(read('http.json'))
    body_record()


def run():
    check_files()
    if any((HERE / name).exists() for name in ARTIFACTS):
        raise ValueError('STOP_ALREADY_ATTEMPTED')
    result = {'status': 'STOP', 'worker_returncode': None, 'assessment_completed': False}
    try:
        save('run-start.json', binding(PROTOCOL))
        with (HERE / 'protocol.snapshot.md').open('xb') as stream:
            stream.write(PROTOCOL.read_bytes())
        code, output = deadline_helper().bounded_run([str(Path(sys.executable).resolve()), '-B', str(SOURCE), '_worker'], SECONDS)
        result.update(worker_returncode=code, output_bytes=len(output.encode()), output_sha256=hashlib.sha256(output.encode()).hexdigest())
        result.update(assess(code))
        result['assessment_completed'] = True
    except Exception as error:
        LOGGER.exception('Index parent stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        result.update(failure(error))
    finally:
        result['artifacts'] = artifacts()
        save('outcome.json', result)
    print(result['status'])
    return 0 if result['status'] == PASS else 1


def replay():
    outcome = read('outcome.json')
    allowed = {'status', 'worker_returncode', 'assessment_completed', 'output_bytes', 'output_sha256',
               'request_invocations', 'products_fetched', 'index', 'worker_error_code', 'error_type', 'error_code', 'artifacts'}
    if (not {'status', 'worker_returncode', 'assessment_completed', 'artifacts'} <= set(outcome)
            or not set(outcome) <= allowed or type(outcome['assessment_completed']) is not bool
            or outcome['artifacts'] != artifacts()):
        raise ValueError('STOP_OUTCOME_CLOSURE')
    validate_response_artifacts()
    if ('error_type' in outcome and (not isinstance(outcome['error_type'], str)
            or not outcome['error_type'].isidentifier() or len(outcome['error_type']) > 80)
            or ('error_code' in outcome and outcome['error_code'] is not None and (
                not isinstance(outcome['error_code'], str) or not re.fullmatch(r'STOP_[A-Z0-9_]+', outcome['error_code'])))):
        raise ValueError('STOP_PARENT_FAILURE_SCHEMA')
    if (outcome['worker_returncode'] is not None and type(outcome['worker_returncode']) is not int
            or ('output_bytes' in outcome and (type(outcome['output_bytes']) is not int or outcome['output_bytes'] < 0))
            or ('output_sha256' in outcome and (not isinstance(outcome['output_sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', outcome['output_sha256'])))
            or (('output_bytes' in outcome) != ('output_sha256' in outcome))):
        raise ValueError('STOP_WORKER_OUTPUT_RECEIPT')
    if outcome['assessment_completed']:
        expected = assess(outcome['worker_returncode'])
        if (not set(expected) <= set(outcome) or json.dumps({k: outcome[k] for k in expected}, sort_keys=True)
                != json.dumps(expected, sort_keys=True)):
            raise ValueError('STOP_OUTCOME_REPLAY')
        print('PASS_OFFLINE_REPLAY ' + expected['status'])
    elif outcome['status'] == 'STOP':
        print('PASS_FAILURE_ARTIFACT_REPLAY STOP; index interpretation unverified')
    else:
        raise ValueError('STOP_FAILURE_STATUS')


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
        LOGGER.exception('Index command stopped', exc_info=(RuntimeError, RuntimeError('Safe code only'), None))
        print(failure(error)['error_code'] or 'STOP_INTERNAL')
        raise SystemExit(1) from None
