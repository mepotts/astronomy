"""Pure bounded TAR profile for a future summary-metadata acquisition.

Not an acquisition contract or authorization. No filesystem/network/extraction.
Only uncompressed TAR bytes, ordinary regular files and empty directory entries
are supported. PAX/global PAX, GNU long name/link, sparse and all special/link
records are explicitly rejected, rather than letting hidden extension records
escape member accounting. Standard-library TarInfo.frombuf validates each raw
512-byte header and checksum; no ustar brand or directory prefix is required.

At most 1 MiB supplied bytes, 16 physical/logical members, 512 ASCII path bytes
and eight substantive path components,
one <=256 KiB regular HTML member. Two zero end blocks and zero-only trailing
padding are required. We inspect headers and padding, never other payloads;
the sole allowed payload is copied only after the entire archive validates.
The caller owns transport, deadline, private HTML storage and semantic review.
These input/output bounds are not an OS memory quota: Python/parser objects and
the private HTML copy add overhead to the caller-owned input buffer.
"""

import hashlib
import re
import tarfile

RAW_CAP = 1048576
HTML_CAP = 262144
MEMBER_CAP = 16
PATH_CAP = 512
BLOCK = 512


def _path(name, directory):
    if type(name) is not str or not 0 < len(name) <= PATH_CAP or any(ord(c) < 33 or ord(c) > 126 for c in name):
        raise ValueError('STOP_TAR_PATH')
    if name.startswith('/') or '\\' in name or ':' in name:
        raise ValueError('STOP_TAR_PATH')
    parts = name.split('/')
    if '..' in parts:
        raise ValueError('STOP_TAR_PATH')
    substantive = [part for part in parts if part not in ('', '.')]
    if len(substantive) > 8 or (not substantive and not directory):
        raise ValueError('STOP_TAR_PATH')
    normalized = '/'.join(substantive) if substantive else '.'
    # Strict safe relative ASCII subset; no URL escaping or shell metacharacters.
    if not re.fullmatch(r'[A-Za-z0-9_.\-/]+', normalized):
        raise ValueError('STOP_TAR_PATH')
    return normalized


def inspect_summary(raw, obsid):
    """Return safe aggregate inventory plus private ``html`` bytes, or STOP.

    ``obsid`` is an explicit caller-supplied ten-digit string. No default target,
    basename, instrument, exposure number, directory prefix or HTML content is
    inferred. The filename establishes only advertised PPS identity, not body
    identity or a complete observation inventory. Exceptions never quote input.
    """
    if type(raw) is not bytes:
        raise TypeError('STOP_TAR_INPUT_TYPE')
    if not 0 < len(raw) <= RAW_CAP or len(raw) % BLOCK:
        raise ValueError('STOP_TAR_RAW_LENGTH')
    if type(obsid) is not str or not re.fullmatch(r'[0-9]{10}', obsid):
        raise ValueError('STOP_TAR_OBSERVATION')
    inventory, seen = [], set()
    offset, payload = 0, None
    while offset + BLOCK <= len(raw):
        header = raw[offset:offset + BLOCK]
        if header == bytes(BLOCK):
            if offset + 2 * BLOCK > len(raw) or any(raw[offset:]):
                raise ValueError('STOP_TAR_TERMINATOR')
            break
        if len(inventory) >= MEMBER_CAP:
            raise ValueError('STOP_TAR_MEMBER_CAP')
        try:
            member = tarfile.TarInfo.frombuf(header, encoding='utf-8', errors='surrogateescape')
        except (tarfile.HeaderError, UnicodeError, ValueError, OverflowError):
            raise ValueError('STOP_TAR_HEADER') from None
        if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
            raise ValueError('STOP_TAR_UNSUPPORTED_MEMBER')
        if member.linkname or member.sparse is not None or member.pax_headers:
            raise ValueError('STOP_TAR_UNSUPPORTED_MEMBER')
        directory = member.type == tarfile.DIRTYPE
        name = _path(member.name, directory)
        if name in seen:
            raise ValueError('STOP_TAR_DUPLICATE_NAME')
        seen.add(name)
        if member.size < 0 or (directory and member.size != 0):
            raise ValueError('STOP_TAR_MEMBER_SIZE')
        start = offset + BLOCK
        end = start + member.size
        next_header = start + ((member.size + BLOCK - 1) // BLOCK) * BLOCK
        if next_header > len(raw):
            raise ValueError('STOP_TAR_TRUNCATED_MEMBER')
        if not directory:
            if payload is not None:
                raise ValueError('STOP_TAR_MULTIPLE_FILES')
            if not 0 < member.size <= HTML_CAP:
                raise ValueError('STOP_TAR_HTML_SIZE')
            expected = r'P' + obsid + r'[A-Z0-9]{2}[A-Z][0-9]{3}SUMMAR[A-Z0-9]{4}\.HTM'
            if not re.fullmatch(expected, name.rsplit('/', 1)[-1]):
                raise ValueError('STOP_TAR_SUMMARY_NAME')
            payload = (start, end)
        inventory.append({'ordinal': len(inventory) + 1,
                          'name_sha256': hashlib.sha256(member.name.encode('ascii')).hexdigest(),
                          'canonical_name_sha256': hashlib.sha256(name.encode('ascii')).hexdigest(),
                          'header_sha256': hashlib.sha256(header).hexdigest(),
                          'name_ascii_bytes': len(member.name), 'type': 'directory' if directory else 'regular',
                          'size': member.size, 'header_offset': offset, 'payload_offset': start})
        offset = next_header
    else:
        raise ValueError('STOP_TAR_TERMINATOR')
    if payload is None:
        raise ValueError('STOP_TAR_MISSING_SUMMARY')
    html = raw[payload[0]:payload[1]]
    html_hash = hashlib.sha256(html).hexdigest()
    for item in inventory:
        item['content_sha256'] = html_hash if item['type'] == 'regular' else None
    return {'inventory': inventory, 'member_count': len(inventory),
            'directory_count': sum(item['type'] == 'directory' for item in inventory),
            'regular_count': 1, 'raw_bytes': len(raw), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'html_bytes': len(html), 'html_sha256': html_hash,
            'semantic_identity': 'UNADJUDICATED', 'html': html}
