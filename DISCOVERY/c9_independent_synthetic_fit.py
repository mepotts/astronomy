"""Independent full-size synthetic C9 fixture. Never opens retained science data.

Generated FITS, headers and receipts stay in an exclusive temporary directory.
Only scientific-input provenance/centres are substituted; real streaming,
structural verification, cores, deadline runner and receipt replay are used.
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import math
import os
import sys
import tempfile
import time
import warnings
from pathlib import Path

import numpy as np
from astropy.io import fits

HERE = Path(__file__).resolve().parent
WRAPPER = HERE / 'XMM-C9-2026-09-12-data/inspect_counts.py'


def load(path, name):
    raw = path.read_bytes()

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError('MODULE_IDENTITY')
            return compile(raw, str(path), 'exec')

    spec = importlib.util.spec_from_file_location(name, path, loader=VerifiedLoader(name, str(path)))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)


def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = str(args[0]).replace('\\', '/').lower()
        if str(HERE).replace('\\', '/').lower() in path and ('/products/' in path or '/headers/' in path):
            raise RuntimeError('REAL_PRODUCT_OR_HEADER_OPEN_FORBIDDEN')
    if event in ('socket.connect', 'socket.getaddrinfo'):
        raise RuntimeError('NETWORK_FORBIDDEN')


def configure(root):
    setup = json.loads((root / 'setup.json').read_bytes())
    if sha(WRAPPER) != setup['wrapper_sha256']:
        raise RuntimeError('DRAFT_SOURCE_CHANGED_STOP')
    m = load(WRAPPER, 'independent_c9')
    m.HERE = root / 'stage'
    m.C.HERE = m.HERE
    m.PRIOR = root / 'synthetic_prior'
    m.SOURCE = Path(__file__).resolve()
    m.PROTOCOL = root / 'synthetic-protocol.md'
    m.centres = lambda: [(50., 10.), (50., 10. + 120 / 3600),
                         (50. + 120 / 3600 / np.cos(np.deg2rad(10)), 10.),
                         (50., 10. - 120 / 3600),
                         (50. - 120 / 3600 / np.cos(np.deg2rad(10)), 10.)]
    m.manifest = lambda: setup['manifest']

    def binding(protocol):
        if sha(WRAPPER) != setup['wrapper_sha256']:
            raise RuntimeError('DRAFT_SOURCE_CHANGED_STOP')
        # Deliberately replaces actual C1/C8/C5 provenance with generated input
        # anchors. No claim this validates real C9 manifest() or binding().
        return {'manifest': setup['manifest'], 'wrapper_sha256': setup['wrapper_sha256'],
                'source_sha256': sha(m.SOURCE), 'protocol_sha256': sha(protocol),
                'synthetic_only': True, 'setup_sha256': sha(root / 'setup.json')}

    m.binding = binding
    return m


def fixed_header(pn, rows, config):
    names = ['TIME', 'RAWX', 'RAWY', 'DETX', 'DETY', 'X', 'Y', 'PHA', 'PI', 'FLAG', 'PATTERN']
    forms = ['D', 'I', 'I', 'I', 'I', 'J', 'J', 'I', 'I', 'J', 'B']
    if pn:
        names += ['PAT_ID', 'PAT_SEQ', 'CCDNR', 'TIME_RAW']
        forms += ['I', 'B', 'B', 'D']
    else:
        names += ['CCDNR']
        forms += ['B']
    h = fits.Header({'XTENSION': 'BINTABLE', 'BITPIX': 8, 'NAXIS': 2,
                     'NAXIS1': 45 if pn else 34, 'NAXIS2': rows, 'PCOUNT': 0,
                     'GCOUNT': 1, 'TFIELDS': len(names), 'EXTNAME': 'EVENTS'})
    for i, (name, form) in enumerate(zip(names, forms, strict=True), 1):
        h[f'TTYPE{i}'], h[f'TFORM{i}'] = name, form
    h.update(TUNIT1='s', TUNIT9='eV' if pn else 'CHAN',
             TNULL6=-99999999, TNULL7=-99999999, TUNIT6='pixel', TUNIT7='pixel',
             TCTYP6='RA---TAN', TCTYP7='DEC--TAN', TCUNI6='deg', TCUNI7='deg',
             TCRPX6=10000., TCRPX7=10000., TCRVL6=50., TCRVL7=10.,
             TCDLT6=-1.38888888888889e-05, TCDLT7=1.38888888888889e-05,
             EQUINOX=2000., RADECSYS='FK5', TIMESYS='TT', MJDREF=50814., TIMEZERO=0.,
             TIMEREF='LOCAL', TASSIGN='SATELLITE', CLOCKAPP=True,
             TSTART=config['tstart'], TSTOP=config['tstop'])
    if pn:
        h.update(TNULL9=-32768, TNULL11=13)
    for key in ('TCDLT6', 'TCDLT7'):
        value = h[key]
        del h[key]
        number = str(value).upper()
        h.append(fits.Card.fromstring(f'{key:8}= {number:>20}'.ljust(80)))
    return h


def padded_header(h, size):
    while len(h) < size // 80 - 1:
        h.append(('', ''), end=True)
    raw = h.tostring().encode('ascii')
    if len(raw) != size:
        raise RuntimeError('SYNTHETIC_HEADER_SIZE')
    return raw


def generate(root):
    m = load(WRAPPER, 'synthetic_generation_c9')
    reader, geometry, counter = m.modules()
    structure = m.C.load_pinned('synthetic_structure', m.C.STRUCTURE_PATH, m.C.STRUCTURE_HASH)
    prior = root / 'synthetic_prior'
    (prior / 'products').mkdir(parents=True)
    (prior / 'headers').mkdir()
    (root / 'stage').mkdir()
    items = []
    for slot, (camera, original) in enumerate(zip(m.CAMERAS, m.PRODUCTS, strict=True), 1):
        name, size, _, _, _, rows, stride, offset = original
        config = counter.camera_config(camera)
        h = fixed_header(slot == 1, rows, config)
        pairs = [(c.keyword, c.value) for c in h.cards]
        schema, geo = reader.build_schema(pairs, offset), geometry.build_geometry(pairs)
        dtype = np.dtype({'names': [c.name for c in schema.columns],
                          'formats': [reader.DTYPES[c.form] for c in schema.columns],
                          'offsets': [c.offset for c in schema.columns], 'itemsize': stride})
        path = prior / 'products' / name
        primary = fits.Header({'SIMPLE': True, 'BITPIX': 8, 'NAXIS': 0, 'EXTEND': True,
                               'OBS_ID': 'SYNTHETIC', 'INSTRUME': camera})
        with path.open('xb', buffering=0) as stream:
            stream.write(primary.tostring().encode('ascii'))
            stream.write(padded_header(h, offset - 2880))
            for lo in range(0, rows, 10000):
                n = min(10000, rows - lo)
                a = np.zeros(n, dtype=dtype)
                k = np.arange(lo, lo + n)
                a['TIME'] = counter.ANCHOR + 200 * (k % 230) + 10
                a['X'] = 10000 + np.choose(k % 6, [0, 0, -2400, 0, 2400, 1500])
                a['Y'] = 10000 + np.choose(k % 6, [0, 2400, 0, -2400, 0, 0])
                a['PI'], a['CCDNR'] = 1000, np.asarray(config['ccds'])[k % len(config['ccds'])]
                a['FLAG'][k % 41 == 0] = -2147483648
                a['PI'][k % 43 == 0] = 200
                a['PATTERN'][k % 47 == 0] = config['pattern_max'] + 1
                a['X'][k % 53 == 0] = -99999999
                stream.write(a.tobytes())
            stream.write(b'\0' * ((-rows * stride) % 2880))
            remainder = size - stream.tell()
            if remainder < 2880 or remainder % 2880:
                raise RuntimeError('SYNTHETIC_TAIL_SIZE')
            tail = fits.Header({'XTENSION': 'IMAGE', 'BITPIX': 8, 'NAXIS': 1,
                                'NAXIS1': remainder - 2880, 'PCOUNT': 0, 'GCOUNT': 1,
                                'EXTNAME': 'OPAQUE_PADDING'})
            stream.write(tail.tostring().encode('ascii'))
            zeros = bytes(1048576)
            while stream.tell() < size:
                stream.write(zeros[:min(len(zeros), size - stream.tell())])
        with path.open('rb', buffering=0) as stream:
            report = structure.structure(stream, size)
        report['parser_warning_categories'] = []
        hp = prior / f'headers/slot-{slot}-headers.json'
        save(hp, report)
        items.append({'slot': slot, 'camera': camera, 'filename': name, 'file_bytes': size,
                      'product_sha256': sha(path), 'header_sha256': sha(hp), 'receipt_sha256': 'synthetic',
                      'schema': schema.metadata(), 'geometry': geo.metadata(), 'config': config,
                      'chunks': math.ceil(rows / 10000)})
    (root / 'synthetic-protocol.md').write_text('Synthetic fixture only; no actual inputs.\n', encoding='utf-8')
    save(root / 'setup.json', {'wrapper_sha256': sha(WRAPPER),
         'manifest': {'cameras': items, 'edges': counter.fixed_edges().tolist(), 'synthetic_only': True}})


def main():
    sys.addaudithook(guard)
    if sys.argv[1:] == ['_worker']:
        return configure(Path(os.environ['C9_SYNTHETIC_ROOT'])).worker()
    root = Path(tempfile.mkdtemp(prefix='xmm-c9-independent-'))
    print(json.dumps({'synthetic_directory': str(root)}), flush=True)
    start = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        generate(root)
    generation = time.monotonic() - start
    os.environ['C9_SYNTHETIC_ROOT'] = str(root)
    m = configure(root)
    start = time.monotonic()
    code = m.run()
    run_elapsed = time.monotonic() - start
    replay_elapsed = None
    if code == 0:
        start = time.monotonic()
        m.replay()
        replay_elapsed = time.monotonic() - start
    outcome = m.C.read('outcome.json')
    receipt = {'synthetic_only': True, 'wrapper_sha256': sha(WRAPPER), 'harness_sha256': sha(Path(__file__)),
               'generation_seconds': generation, 'run_plus_parent_seconds': run_elapsed,
               'replay_seconds': replay_elapsed, 'run_returncode': code,
               'outcome_sha256': sha(root / 'stage/outcome.json'),
               'status': outcome['status'], 'json_bytes': m.C.resource_usage()['json_bytes'],
               'chunk_markers': len(list((root / 'stage').glob('camera-*-chunk-*-start.json'))),
               'chunk_results': len(list((root / 'stage').glob('camera-*-chunk-*-result.json'))),
               'parent_peak_memory_bytes': outcome['parent_peak_memory_bytes'],
               'worker_peak_memory_bytes': outcome.get('worker_peak_memory_bytes'),
               'substituted_only': ['synthetic_input_manifest_binding', 'synthetic_centres', 'harness_child_entrypoint']}
    save(root / 'fit-receipt.json', receipt)
    print(json.dumps(receipt), flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
