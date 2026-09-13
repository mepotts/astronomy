"""Synthetic archive tests only; never open a retained archive or product."""

import importlib.util
import io
import json
import tarfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('summary_tar_tested', Path(__file__).with_name('xmm_summary_tar.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
OBSID = '0851180501'
NAME = 'P0851180501OBX000SUMMAR0000.HTM'
HTML = b'<html>private observer contacts; no semantic interpretation'


def archive(entries, fmt=tarfile.USTAR_FORMAT):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=fmt) as output:
        for name, data, kind in entries:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(data)
            if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                info.linkname = 'private-target'
            output.addfile(info, io.BytesIO(data))
    return stream.getvalue()


def valid():
    return archive([('arbitrary/', b'', tarfile.DIRTYPE), ('arbitrary/' + NAME, HTML, tarfile.REGTYPE)])


class SummaryTarTests(unittest.TestCase):
    def test_safe_inventory_private_bytes_no_fixed_prefix_or_semantic_footer(self):
        result = M.inspect_summary(valid(), OBSID)
        self.assertEqual(result.pop('html'), HTML)
        self.assertEqual(result['member_count'], 2)
        self.assertEqual(result['directory_count'], 1)
        self.assertEqual(result['regular_count'], 1)
        self.assertEqual(result['semantic_identity'], 'UNADJUDICATED')
        encoded = json.dumps(result)
        for private in ('arbitrary', NAME, 'observer'):
            self.assertNotIn(private, encoded)

    def test_no_ustar_brand_requirement_and_alternate_instrument_exposure(self):
        raw = archive([('P0851180501M2S123SUMMAR8000.HTM', HTML, tarfile.REGTYPE)], fmt=tarfile.GNU_FORMAT)
        self.assertEqual(M.inspect_summary(raw, OBSID)['html'], HTML)
        self.assertEqual(M.inspect_summary(archive([(NAME, HTML, tarfile.AREGTYPE)]), OBSID)['html'], HTML)

    def test_links_specials_pax_longname_and_sparse_are_unsupported(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE,
                     tarfile.FIFOTYPE, tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME,
                     tarfile.GNUTYPE_LONGLINK, tarfile.GNUTYPE_SPARSE):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'STOP_TAR_UNSUPPORTED_MEMBER'):
                M.inspect_summary(archive([(NAME, b'', kind)]), OBSID)

    def test_actual_pax_and_gnu_longpath_extensions_not_hidden(self):
        for fmt in (tarfile.PAX_FORMAT, tarfile.GNU_FORMAT):
            raw = archive([('a' * 110 + '/' + NAME, HTML, tarfile.REGTYPE)], fmt=fmt)
            with self.assertRaisesRegex(ValueError, 'STOP_TAR_UNSUPPORTED_MEMBER'):
                M.inspect_summary(raw, OBSID)

    def test_safe_paths_and_duplicates(self):
        for name in ('/' + NAME, '../' + NAME, 'a/../' + NAME,
                     'C:/' + NAME, 'a\\' + NAME, 'a%20/' + NAME, 'a b/' + NAME):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'STOP_TAR_PATH'):
                M.inspect_summary(archive([(name, HTML, tarfile.REGTYPE)]), OBSID)
        for entries in ([('a/', b'', tarfile.DIRTYPE), ('./a', b'', tarfile.DIRTYPE)],
                        [(NAME, HTML, tarfile.REGTYPE), (NAME, HTML, tarfile.REGTYPE)]):
            with self.assertRaisesRegex(ValueError, 'STOP_TAR_DUPLICATE_NAME'):
                M.inspect_summary(archive(entries), OBSID)

    def test_leading_dot_root_and_ustar_prefix_resolve_without_hiding_names(self):
        raw = archive([('./', b'', tarfile.DIRTYPE), ('././folder/' + NAME, HTML, tarfile.REGTYPE)])
        result = M.inspect_summary(raw, OBSID)
        self.assertEqual(result['html'], HTML)
        item = result['inventory'][1]
        self.assertNotEqual(item['name_sha256'], item['canonical_name_sha256'])
        prefix = 'a' * 110
        result = M.inspect_summary(archive([(prefix + '/' + NAME, HTML, tarfile.REGTYPE)]), OBSID)
        self.assertEqual(result['html'], HTML)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_DUPLICATE_NAME'):
            M.inspect_summary(archive([('./' + NAME, HTML, tarfile.REGTYPE), (NAME, HTML, tarfile.REGTYPE)]), OBSID)
        self.assertEqual(M.inspect_summary(archive([('a/./b//' + NAME, HTML, tarfile.REGTYPE)]), OBSID)['html'], HTML)
        self.assertEqual(M._path('/'.join(['a'] * 8), True), '/'.join(['a'] * 8))
        for name in ('/'.join(['a'] * 9), 'a' * 513):
            with self.assertRaisesRegex(ValueError, 'STOP_TAR_PATH'):
                M._path(name, True)

    def test_unrelated_owner_unicode_is_not_a_path_gate(self):
        info = tarfile.TarInfo(NAME)
        info.size = len(HTML)
        info.uname = 'owner-\u00e9'
        raw = info.tobuf(format=tarfile.USTAR_FORMAT, encoding='utf-8') + HTML
        raw += bytes((-len(raw)) % 512) + bytes(1024)
        result = M.inspect_summary(raw, OBSID)
        self.assertEqual(result['html'], HTML)
        self.assertNotIn('owner', json.dumps({k: v for k, v in result.items() if k != 'html'}))

    def test_exact_single_summary_and_observation(self):
        for name in ('other.txt', NAME.replace(OBSID, '0884250101'), NAME + '.gz'):
            with self.assertRaisesRegex(ValueError, 'STOP_TAR_SUMMARY_NAME'):
                M.inspect_summary(archive([(name, HTML, tarfile.REGTYPE)]), OBSID)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_MULTIPLE_FILES'):
            M.inspect_summary(archive([(NAME, HTML, tarfile.REGTYPE), ('other/' + NAME, HTML, tarfile.REGTYPE)]), OBSID)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_MISSING_SUMMARY'):
            M.inspect_summary(archive([('a/', b'', tarfile.DIRTYPE)]), OBSID)

    def test_input_member_html_caps(self):
        with self.assertRaises(TypeError):
            M.inspect_summary(bytearray(valid()), OBSID)
        for raw in (b'', b'x' * (M.RAW_CAP + 512), valid()[:-1]):
            with self.assertRaisesRegex(ValueError, 'STOP_TAR_RAW_LENGTH'):
                M.inspect_summary(raw, OBSID)
        for data in (b'', b'x' * (M.HTML_CAP + 1)):
            with self.assertRaisesRegex(ValueError, 'STOP_TAR_HTML_SIZE'):
                M.inspect_summary(archive([(NAME, data, tarfile.REGTYPE)]), OBSID)
        good = [('d' + str(i), b'', tarfile.DIRTYPE) for i in range(15)] + [(NAME, b'x' * M.HTML_CAP, tarfile.REGTYPE)]
        self.assertEqual(M.inspect_summary(archive(good), OBSID)['member_count'], 16)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_MEMBER_CAP'):
            M.inspect_summary(archive([('extra', b'', tarfile.DIRTYPE), *good]), OBSID)

    def test_checksums_truncation_padding_termination_and_append_rejected(self):
        raw = archive([(NAME, HTML, tarfile.REGTYPE)])
        bad = bytearray(raw)
        bad[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_HEADER'):
            M.inspect_summary(bytes(bad), OBSID)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_TRUNCATED_MEMBER'):
            M.inspect_summary(raw[:512], OBSID)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_TERMINATOR'):
            M.inspect_summary(raw[:1536], OBSID)
        bad = bytearray(raw)
        bad[512 + len(HTML)] = 1
        self.assertEqual(M.inspect_summary(bytes(bad), OBSID)['html'], HTML)
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_TERMINATOR'):
            M.inspect_summary(raw + archive([(NAME, HTML, tarfile.REGTYPE)]), OBSID)

    def test_directory_payload_rejected_and_no_error_payload_echo(self):
        with self.assertRaisesRegex(ValueError, 'STOP_TAR_MEMBER_SIZE'):
            M.inspect_summary(archive([('secret/', b'private', tarfile.DIRTYPE)]), OBSID)
        with self.assertRaisesRegex(ValueError, '^STOP_TAR_OBSERVATION$'):
            M.inspect_summary(valid(), 'private input')


if __name__ == '__main__':
    unittest.main()
