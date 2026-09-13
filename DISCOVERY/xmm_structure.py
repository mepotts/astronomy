"""Bounded FITS header inventory, seeking past rather than reading data arrays.

For a later separately authorized structural-only stage; no network or analysis.
Uses Astropy Header.data_size_padded, not a custom table-layout implementation.
"""

import io

from astropy.io.fits import Column, Header

BLOCK = 2880
MAX_HEADER_BLOCKS = 64
MAX_HDUS = 128
MAX_FILE_BYTES = 2 * 1024**3


def structure(stream, file_bytes):
    """Skip declared data spans; malformed headers can consume unknown bytes.

    No arrays are interpreted. An unterminated or corrupt header can only be
    rejected after a bounded scan, not certified without reading any payload.
    """
    if type(file_bytes) is not int or not 0 < file_bytes <= MAX_FILE_BYTES or file_bytes % BLOCK:
        raise ValueError("STOP_FILE_SIZE_OR_ALIGNMENT")
    if stream.seek(0, io.SEEK_END) != file_bytes:
        raise ValueError("STOP_ACTUAL_FILE_SIZE")
    stream.seek(0)
    rows = []
    while stream.tell() < file_bytes:
        if len(rows) >= MAX_HDUS:
            raise ValueError("STOP_HDU_CAP")
        start = stream.tell()
        chunks = []
        for _ in range(MAX_HEADER_BLOCKS):
            block = stream.read(BLOCK)
            if len(block) != BLOCK:
                raise ValueError("STOP_TRUNCATED_HEADER")
            chunks.append(block)
            if any(block[i:i + 80] == b"END" + b" " * 77 for i in range(0, BLOCK, 80)):
                break
        else:
            raise ValueError("STOP_HEADER_CAP")
        raw = b"".join(chunks)
        header = Header.fromstring(raw.decode("ascii"))
        critical = ["SIMPLE", "XTENSION", "BITPIX", "NAXIS", "PCOUNT", "GCOUNT", "GROUPS"]
        critical += [key for key in header if key.startswith("NAXIS")]
        if any(header.count(key) > 1 for key in set(critical) if key in header):
            raise ValueError("STOP_DUPLICATE_LAYOUT_KEY")
        if not rows:
            if header.cards[0].keyword != "SIMPLE" or header.get("SIMPLE") is not True:
                raise ValueError("STOP_PRIMARY_IDENTITY")
        elif header.cards[0].keyword != "XTENSION" or header.get("XTENSION") not in ("BINTABLE", "IMAGE"):
            raise ValueError("STOP_EXTENSION_TYPE")
        if header.get("GROUPS", False):
            raise ValueError("STOP_RANDOM_GROUPS_UNSUPPORTED")
        naxis = header.get("NAXIS")
        if (type(naxis) is not int or not 0 <= naxis <= 16
                or header.get("BITPIX") not in (8, 16, 32, 64, -32, -64)):
            raise ValueError("STOP_LAYOUT")
        lengths = [header.get(f"NAXIS{i}") for i in range(1, naxis + 1)]
        if any(type(n) is not int or n < 0 for n in lengths):
            raise ValueError("STOP_DIMENSIONS")
        if any(type(header.get(k, default)) is not int or header.get(k, default) < low
               for k, default, low in (("PCOUNT", 0, 0), ("GCOUNT", 1, 1))):
            raise ValueError("STOP_GROUP_OR_HEAP_SIZE")
        if header.get("XTENSION") == "BINTABLE":
            if (header["BITPIX"] != 8 or naxis != 2 or header.get("GCOUNT") != 1
                    or "PCOUNT" not in header):
                raise ValueError("STOP_BINARY_TABLE_LAYOUT")
            count = header.get("TFIELDS")
            if type(count) is not int or not 0 <= count <= 999 or header.count("TFIELDS") != 1:
                raise ValueError("STOP_BINARY_TABLE_FIELDS")
            width = 0
            for i in range(1, count + 1):
                key = f"TFORM{i}"
                if key not in header or header.count(key) != 1 or not isinstance(header[key], str):
                    raise ValueError("STOP_BINARY_TABLE_FORMAT")
                width += Column(name=f"COLUMN{i}", format=header[key]).dtype.itemsize
            if width != header["NAXIS1"]:
                raise ValueError("STOP_BINARY_TABLE_WIDTH")
        data_bytes = header.data_size
        padded = header.data_size_padded
        data_start = stream.tell()
        end = data_start + padded
        if not 0 <= data_bytes <= padded or end > file_bytes or end <= start:
            raise ValueError("STOP_DATA_SPAN")
        rows.append({"hdu": len(rows), "extname": header.get("EXTNAME", "PRIMARY" if not rows else None),
                     "header_offset": start, "header_bytes": len(raw), "data_offset": data_start,
                     "data_bytes": data_bytes, "data_span_padded": padded,
                     "cards": [str(card) for card in header.cards]})
        stream.seek(end)
    return {"status": "HEADER_LAYOUT_ONLY", "file_bytes": file_bytes, "hdu_count": len(rows),
            "header_bytes_read": sum(row["header_bytes"] for row in rows),
            "declared_data_region_bytes_read": 0, "hdus": rows,
            "limits": "No array, GTI-value, exposure-value, checksum or scientific-validity assessment."}
