"""One bounded summary-only plain TAR request; private fixed-name HTML copy."""

import hashlib
import importlib.machinery
import importlib.util
import logging
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M3-2026-09-13.md'
BASE = HERE.parent / 'XMM-RXJ-M2-2026-09-13-data/listing.py'
BASE_HASH = 'a4620e9d991761276be1b32a6dc693d4a1846999d368bdddb928ab4ff5df24e6'
TAR = HERE.parent / 'xmm_summary_tar.py'
TAR_HASH = 'f9ce311d0e70c3aa264ca885bd202f71f79f91e92c01c62affbaa9f68a11dfa9'
URL = 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&name=SUMMAR&extension=HTM'
CAP = 1048576
PASS = 'SUMMARY_MEMBER_RETAINED_UNADJUDICATED'
LOGGER = logging.getLogger(__name__)
PINS = {
    'XMM-RXJ-M2-2026-09-13-data/listing.py': BASE_HASH,
    'XMM-RXJ-M2-2026-09-13-data/test_listing.py': '12c782baacff8e29b160feb4c197ccf2df335a6403d35623c0c80a322d91d186',
    'XMM-RXJ-M2-2026-09-13.md': 'd26c216910fc9c72f9134e439b012f77d6e2acfc09f3df74eec61f560a5e0871',
    'XMM-RXJ-M2-2026-09-13-data/outcome.json': 'f57b43c9a551a7812afed2be845e1dc88b579251ef36f6e1cceceba3cf20705a',
    'XMM-RXJ-M2-2026-09-13-data/http.json': 'ec3da2ce6dcd0de66e30e6b18cbb96e5d14aa5ad902083bf4104da5c7a5254fc',
    'XMM-RXJ-M2-NEXT-2026-09-13.md': '62fabcea1700407e7c7c0e7e053c6af8b9573148a3253ea6546f04f0878e0a68',
    'xmm_summary_tar.py': TAR_HASH,
    'test_xmm_summary_tar.py': 'eab791a332c26452e6ecd748ec7d349c3f22c54cafe93cc137276e1063b54ad4',
}


def load_verified(path, expected, name, replace_body=False):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('STOP_SOURCE_HASH')
    if replace_body:
        if raw.count(b"'summary.html'") != 3:
            raise ValueError('STOP_ADAPTER_LITERAL_COUNT')
        raw = raw.replace(b"'summary.html'", b"'summary.tar'")
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(path), 'exec')
    spec = importlib.util.spec_from_file_location(name, path, loader=Loader(name, str(path)))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def load_core():
    parent = load_verified(BASE, BASE_HASH, 'rxj_m3_parent', replace_body=True)
    parser = load_verified(TAR, TAR_HASH, 'rxj_m3_tar')
    parent.HERE, parent.SOURCE, parent.PROTOCOL = HERE, SOURCE, PROTOCOL
    parent.CAP, parent.PASS = CAP, PASS
    core = parent.load_core()
    core.ARTIFACTS += ('summary.html',)
    old_binding, old_response, old_parse, old_worker = core.binding, core.validate_response_artifacts, core.parse_index, core.worker
    worker_active = False

    def binding(protocol):
        result = old_binding(protocol)
        for name, expected in PINS.items():
            path = HERE.parent / name
            if core.sha(path) != expected:
                raise ValueError('STOP_M3_DEPENDENCY_HASH')
            result['dependencies'][str(path)] = expected
        result.update(raw_body_cap=CAP, private_html_cap=parser.HTML_CAP,
                      physical_header_cap=parser.MEMBER_CAP, outer_body_replacements=3,
                      parent_validation='ADDITIONAL_BOUNDED_ARCHIVE_PASS',
                      html_filename='summary.html')
        return result

    def validate_http(http, body_bytes=None):
        core.validate_http_schema(http)
        if not http['actual_url_matches']:
            raise ValueError('STOP_HTTP_IDENTITY')
        if http['status'] != 200:
            raise ValueError('STOP_HTTP_STATUS')
        headers = {k: v[0] for k, v in http['headers'].items()}
        if headers.get('Content-Encoding', 'identity').lower() not in ('identity', ''):
            raise ValueError('STOP_CONTENT_ENCODING')
        if headers.get('Content-Type', '').split(';', 1)[0].strip().lower() not in ('application/x-tar', 'application/tar'):
            raise ValueError('STOP_NOT_PLAIN_TAR')
        # Outer disposition is deliberately non-authoritative; no package-name gate.
        if 'Content-Length' in headers:
            length = headers['Content-Length']
            if not re.fullmatch(r'[0-9]{1,9}', length) or not 0 < int(length) <= CAP:
                raise ValueError('STOP_CONTENT_LENGTH')
            if body_bytes is not None and int(length) != body_bytes:
                raise ValueError('STOP_RESPONSE_LENGTH')

    def collect():
        import requests

        if parent.http_client._MAXLINE > 65536 or parent.http_client._MAXHEADERS > 100:
            raise ValueError('STOP_HTTP_PARSER_CAP')
        with requests.Session() as session:
            session.trust_env, session.auth = False, None
            session.cookies.clear()
            with session.get(URL, timeout=(5, 15), stream=True, allow_redirects=False,
                             headers={'Accept-Encoding': 'identity'}) as response:
                http = {'status': response.status_code, 'url': URL, 'actual_url_matches': response.url == URL,
                        'headers': {k: response.raw.headers.getlist(k) for k in core.SAFE_HEADERS if response.raw.headers.getlist(k)},
                        'disposition': parent.disposition(response.raw.headers.getlist('Content-Disposition'))}
                core.validate_http_schema(http)
                core.save('http.json', http)
                validate_http(http)
                count = 0
                with (core.HERE / 'summary.tar').open('xb') as stream:
                    while True:
                        chunk = response.raw.read(min(8192, CAP - count + 1), decode_content=False)
                        if not chunk:
                            break
                        keep = chunk[:CAP - count]
                        stream.write(keep)
                        count += len(keep)
                        if len(chunk) > len(keep):
                            raise ValueError('STOP_BYTE_CAP')
                core.save('transport.json', {'eof': True, 'bytes': count})
                if not count:
                    raise ValueError('STOP_EMPTY_BODY')
                validate_http(http, count)

    def validate_response_artifacts():
        old_response()
        html = core.HERE / 'summary.html'
        if html.exists() and (not (core.HERE / 'transport.json').exists() or not 0 <= html.stat().st_size <= parser.HTML_CAP):
            raise ValueError('STOP_PRIVATE_HTML_ARTIFACT')

    def parse_index(raw):
        old_parse(raw)  # Only inherited EOF/body accounting, never HTML semantics.
        raw_hash = hashlib.sha256(raw).hexdigest()
        result = parser.inspect_summary(raw, '0851180501')
        if result['raw_sha256'] != raw_hash:
            raise ValueError('STOP_TAR_HASH')
        html = result.pop('html')
        path = core.HERE / 'summary.html'
        if worker_active:
            with path.open('xb') as stream:
                stream.write(html)
        elif not path.exists() or path.stat().st_size != len(html) or core.sha(path) != result['html_sha256']:
            raise ValueError('STOP_PRIVATE_HTML_REPLAY')
        return result

    def worker():
        nonlocal worker_active
        worker_active = True
        try:
            return old_worker()
        finally:
            worker_active = False

    core.binding, core.validate_http, core.collect = binding, validate_http, collect
    core.validate_response_artifacts, core.parse_index, core.worker = validate_response_artifacts, parse_index, worker
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
        LOGGER.exception('M3 command stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        print('STOP_M3_COMMAND')
        raise SystemExit(1) from None
