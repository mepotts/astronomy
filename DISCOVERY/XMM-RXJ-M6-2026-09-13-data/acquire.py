"""Isolated M5 mechanics: one fresh M6 batch, longer finite worker only."""

import hashlib
import importlib.machinery
import importlib.util
import logging
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / 'XMM-RXJ-M6-2026-09-13.md'
BASE_PATH = HERE.parent / 'XMM-RXJ-M5-2026-09-13-data/acquire.py'
BASE_HASH = 'e8597327a7cbe4f6ca975d88d2e4b2584fef1afa21a4bf16c388daa046be2b12'
TEST_HASH = 'd387056f90bac2eed0f9480ef16a381f9d35e8f468f9f04449e64d1964dd50a9'
HARD_SECONDS, WORKER_SECONDS, PARENT_SECONDS = 7200, 7140, 300
NETWORK_CHUNK = 65536
LOGGER = logging.getLogger(__name__)
PINS = {
    'XMM-RXJ-M5-2026-09-13-data/acquire.py': BASE_HASH,
    'XMM-RXJ-M5-2026-09-13-data/test_acquire.py': TEST_HASH,
    'XMM-RXJ-M5-2026-09-13.md': '7273718a789146accd9ecd5c51b9b36cea698a25234b093fc419216cb16a425e',
    'XMM-RXJ-M5-2026-09-13-data/outcome.json': '9eb6912a34cabdfad6c5da42d751e7be25c249ed72ec2910f194bdbca59119bb',
    'XMM-RXJ-M5-2026-09-13-data/slot-1-http.json': '9defa91737820d025299806875c86b81d9aa8c989eed4786851f065bdc29af33',
    'XMM-RXJ-M5-NEXT.md': '94cdd8bd9272521cbdc943845604f0e226acab29641b32e042a91f03ae4490c6',
}


def load_core():
    raw = BASE_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_HASH:
        raise ValueError('STOP_BASE_HASH')
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('STOP_MODULE_IDENTITY')
            return compile(raw, str(BASE_PATH), 'exec')
    name = 'm6_isolated_m5'
    spec = importlib.util.spec_from_file_location(name, BASE_PATH, loader=Loader(name, str(BASE_PATH)))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.HERE, m.SOURCE, m.PROTOCOL, m.__file__ = HERE, SOURCE, PROTOCOL, str(SOURCE)
    m.C.HERE, m.C.SECONDS, m.SECONDS = HERE, WORKER_SECONDS, WORKER_SECONDS
    m.PINS = {**m.PINS, **PINS}
    original_binding, original_copy, original_assess, original_replay = m.binding, m.copy_bounded, m.assess, m.replay

    def binding(protocol):
        result = original_binding(protocol)
        result['caps'].update(worker_seconds=WORKER_SECONDS, hard_worker_seconds=HARD_SECONDS,
                              parent_seconds=PARENT_SECONDS, replay_seconds=PARENT_SECONDS,
                              chunk=1048576, network_chunk=NETWORK_CHUNK)
        result['adapter'] = {'stage': 'M6', 'base_source_sha256': BASE_HASH,
                             'prior_partial_reused': False, 'range_requests': False}
        return result

    def copy_bounded(source, target, cap, state, stage, network=False):
        # One single-threaded worker. Local copy/hash/expansion stays at 1 MiB.
        previous = m.CHUNK
        try:
            if network:
                m.CHUNK = NETWORK_CHUNK
            return original_copy(source, target, cap, state, stage, network=network)
        finally:
            m.CHUNK = previous

    def assess(code, verification=None):
        previous = m.SECONDS
        try:
            m.SECONDS = PARENT_SECONDS
            return original_assess(code, verification)
        finally:
            m.SECONDS = previous

    def run():
        m.artifacts()
        if any((m.HERE / name).exists() for name in m.artifact_paths()):
            raise ValueError('STOP_ALREADY_ATTEMPTED')
        verification = m.header_pass()
        result = {'status': 'STOP', 'worker_returncode': None, 'assessment_completed': False,
                  'error_code': None, 'header_verification_pass': verification}
        try:
            m.C.save('run-start.json', m.binding(m.PROTOCOL))
            with (m.HERE / 'protocol.snapshot.md').open('xb') as stream:
                stream.write(m.PROTOCOL.read_bytes())
            if m.shutil.disk_usage(m.HERE).free < m.FREE_BYTES:
                raise ValueError('STOP_FREE_SPACE')
            helper = m.C.load_pinned('m6_deadline', m.C.HELPER, m.C.HELPER_HASH)
            code, output = helper.bounded_run([str(Path(sys.executable).resolve()), '-B', str(m.SOURCE), '_worker'], HARD_SECONDS)
            result.update(worker_returncode=code, output_bytes=len(output.encode()), output_sha256=m.digest(output.encode()))
            if type(code) is int and code == 124 and not (m.HERE / 'worker-result.json').exists():
                raise ValueError('STOP_WORKER_HARD_DEADLINE')
            result.update(m.assess(code, verification))
            result['assessment_completed'] = True
        except Exception as error:
            m.LOGGER.exception('M6 parent stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
            result.update(error_code=m.failure(error), ledger=m.marker_evidence())
        result['artifacts'] = m.artifacts(exclude=('outcome.json',))
        m.C.save('outcome.json', result, terminal=True, peak_key='parent_peak_memory_bytes')
        print(result['status'])
        return 0 if result['status'] == m.PASS else 1

    def replay():
        m.resources()
        outcome = m.C.read('outcome.json')
        if type(outcome) is dict:
            hard = type(outcome.get('worker_returncode')) is int and outcome['worker_returncode'] == 124 and not (m.HERE / 'worker-result.json').exists()
            late_peak = (outcome.get('error_code') == 'STOP_PEAK_MEMORY' and outcome.get('status') == 'STOP'
                         and outcome.get('assessment_completed') is False
                         and type(outcome.get('parent_peak_memory_bytes')) is int
                         and outcome['parent_peak_memory_bytes'] > m.MEMORY_CAP)
            if (hard and outcome.get('error_code') != 'STOP_WORKER_HARD_DEADLINE' and not late_peak
                    or not hard and outcome.get('error_code') == 'STOP_WORKER_HARD_DEADLINE'):
                raise ValueError('STOP_DEADLINE_CLASSIFICATION')
        return original_replay()

    m.binding, m.copy_bounded, m.assess, m.run, m.replay = binding, copy_bounded, assess, run, replay
    return m


if __name__ == '__main__':
    try:
        core = load_core()
        if sys.argv[1:] == ['run']:
            raise SystemExit(core.run())
        if sys.argv[1:] == ['_worker']:
            raise SystemExit(core.worker())
        if sys.argv[1:] == ['replay']:
            core.replay()
        else:
            raise ValueError('STOP_COMMAND')
    except Exception:
        LOGGER.exception('M6 stopped', exc_info=(RuntimeError, RuntimeError('Safe receipt only'), None))
        print('STOP_M6_COMMAND')
        raise SystemExit(1) from None
