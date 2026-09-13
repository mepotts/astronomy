"""Pure RXJ header adjudication; accepts only a caller-verified structure report.

No files, arrays or requests. Does not repeat structural/provenance validation.
Primary plus sole EVENTS must collectively carry OBS_ID/INSTRUME/EXPIDSTR.
Placement is explicit evidence, not an implicit inheritance rule.
EXP_ID is optional corroboration, never a substitute for the scheduled flag.
Its obs+three-digit representation is evidenced by XMM-C1-HEADER-REVIEW.md;
keyword vocabulary: https://xmm-tools.cosmos.esa.int/external/sas/current/doc/
rgsfilter/node8.html . PPS exposure naming: .../doc/rgsprods/node6.html .
Neither source guarantees placement in every EPIC exporter. Missing placement
is reported, not silently inherited. No calibration or science eligibility pass.
"""

import hashlib
import math
import re
import warnings

from astropy.io.fits import Header

OBS_ID = "0851180501"
EXPOSURES = {"EPN": "S001", "EMOS1": "S002", "EMOS2": "S003"}
TOKENS = {
    "DATAMODE": {"IMAGING", "TIMING", "BURST", "Imaging", "Timing", "Burst"},
    "SUBMODE": {"PrimeFullWindow", "PrimeLargeWindow", "PrimeSmallWindow",
                "PrimePartialW2", "PrimePartialW3", "PrimePartialW4",
                "PrimeFastUncompressed", "PrimeFastCompressed", "FastTiming", "FastBurst"},
    "FILTER": {"Thin1", "Thin2", "Medium", "Thick", "Open", "Closed", "CalClosed"},
    "TELESCOP": {"XMM", "XMM-Newton"}, "TIMESYS": {"TT", "TDB", "UTC", "TAI"},
    "TIMEUNIT": {"s", "sec", "d"}, "TIMEREF": {"LOCAL", "SOLARSYSTEM", "GEOCENTRIC"},
    "TASSIGN": {"SATELLITE", "GROUND"},
}
NUMBERS = {"TSTART", "TSTOP", "TIMEZERO", "MJDREF", "MJDREFI", "MJDREFF",
           "ONTIME", "LIVETIME", "EXPOSURE", "DEADC", "TIMEDEL", "CCDNR", "CCDID",
           "WINDOWX0", "WINDOWY0", "WINDOWDX", "WINDOWDY"}
NAMES = {"TIME", "RAWX", "RAWY", "X", "Y", "PI", "PHA", "FLAG", "PATTERN",
         "CCDNR", "FRAME", "START", "STOP", "TIMEDEL", "FRACEXP", "FILENAME",
         "CALINDEX", "CALTYPE", "INSTRUMENT", "CALID", "VERSION", "DATE"}
UNITS = {"s", "sec", "d", "eV", "keV", "CHAN", "channel", "pixel", "pixels",
         "deg", "arcsec", "rad", ""}


def _digest(value):
    # Only header primitive values reach here; never expose their repr in errors.
    return hashlib.sha256(str(value).encode("utf-8", errors="replace")).hexdigest()


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _safe(value, kind):
    if kind == "hash_only":
        return {"state": "INTENTIONALLY_HASHED", "value": None, "sha256": _digest(value)}
    good = False
    if kind in TOKENS:
        good = type(value) is str and value in TOKENS[kind]
    elif kind == "number":
        good = _finite(value)
    elif kind == "boolean":
        good = type(value) is bool
    elif kind == "date":
        good = type(value) is str and re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?", value) is not None
    elif kind == "name":
        good = type(value) is str and value in NAMES
    elif kind == "unit":
        good = type(value) is str and value in UNITS
    elif kind == "format":
        good = type(value) is str and re.fullmatch(
            r"[0-9]{0,9}[LXBIJKAEDCM]|[0-9]{0,9}[PQ][LXBIJKAEDCM](?:\([0-9]{1,12}\))?", value) is not None
    elif kind == "extname":
        good = type(value) is str and (value in {"PRIMARY", "EVENTS", "CALINDEX"}
            or re.fullmatch(r"(?:STDGTI|GTI|EXPOSU|BADPIX|OFFSETS|REJPIX)\d{0,2}", value) is not None)
    return {"state": "KNOWN" if good else "UNRECOGNIZED",
            "value": value if good else None,
            "sha256": None if good else _digest(value)}


def _field(header, key, kind):
    values = [card.value for card in header.cards if card.keyword == key]
    return {"count": len(values), "state": "MISSING" if not values else
            "DUPLICATE" if len(values) > 1 else "PRESENT",
            "candidates": [_safe(value, kind) for value in values]}


def _identity(header, camera, exposure, obsid):
    result = {}
    for key, expected in (("OBS_ID", obsid), ("INSTRUME", camera),
                          ("EXPIDSTR", exposure), ("EXP_ID", obsid + exposure[1:])):
        values = [card.value for card in header.cards if card.keyword == key]
        matches = [type(v) is str and v == expected for v in values]
        if key == "EXP_ID":
            matches = [(type(v) is str and v == expected)
                       or (type(v) is int and v == int(expected)) for v in values]
        state = ("MISSING" if not values else "DUPLICATE" if len(values) > 1
                 else "MATCH" if matches[0] else "CONFLICT")
        result[key] = {"state": state, "count": len(values), "matches": matches,
                       "candidate_hashes": [_digest(v) for v in values]}
    return result


def _header(item):
    cards = item.get("cards")
    if (type(cards) is not list or len(cards) > 2304 or
            any(type(card) is not str or len(card) != 80 for card in cards)):
        raise ValueError("STOP_HEADER_REPORT")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            header = Header.fromstring("".join(cards), sep="")
            # Force deferred card parsing within the safe warning boundary.
            list(header.items())
    except Exception:  # noqa: BLE001 -- never expose a private card through library diagnostics
        raise ValueError("STOP_HEADER_PARSE") from None
    return header


def _inventory(header, index):
    count = header.get("TFIELDS", 0)
    if type(count) is not int or not 0 <= count <= 999:
        raise ValueError("STOP_SCHEMA_CAP")
    result = {"hdu": index, "extname": _field(header, "EXTNAME", "extname"),
              "metadata": {}, "columns": [], "schema_fields": count,
              "provenance": {key: _field(header, key, "hash_only")
                             for key in ("CREATOR", "SAS_VER", "SAS_CCF")}}
    for key in sorted(set(TOKENS) | NUMBERS | {"DATE-OBS", "DATE-END", "CLOCKAPP"}):
        kind = (key if key in TOKENS else "number" if key in NUMBERS else
                "boolean" if key == "CLOCKAPP" else "date")
        result["metadata"][key] = _field(header, key, kind)
    result["layout"] = {key: _field(header, key, "number") for key in
                        ("BITPIX", "NAXIS", "NAXIS1", "NAXIS2", "PCOUNT", "GCOUNT")}
    for i in range(1, count + 1):
        column = {"index": i}
        for key, prefix, kind in (("name", "TTYPE", "name"), ("format", "TFORM", "format"),
                                  ("unit", "TUNIT", "unit"), ("null", "TNULL", "number"),
                                  ("scale", "TSCAL", "number"), ("zero", "TZERO", "number")):
            column[key] = _field(header, f"{prefix}{i}", kind)
        result["columns"].append(column)
    # Presence counts only: never include coordinate values or arbitrary keyword text.
    result["wcs_card_count"] = sum(bool(re.fullmatch(
        r"(?:TCTYP|TCRPX|TCRVL|TCDLT|TCUNI)\d+|(?:CTYPE|CUNIT|CRPIX|CRVAL|CDELT)\d+", k))
        for k in header)
    result["dss_card_count"] = sum(bool(re.fullmatch(r"\d*(?:DSTYP|DSUNI|DSVAL|DSREF)\d+", k))
                                   for k in header)
    return result


def inspect_identity(report, camera, exposure, obsid=OBS_ID):
    """Return bounded safe metadata; identity STOPs are results, malformed inputs raise.

    Every mandatory identity needs a match in primary or EVENTS. Missing
    optional EXP_ID does not fail, but duplicate/wrong corroboration does. No
    assumption that an ancillary HDU repeats identity; its metadata is inventoried.
    Caller must preserve returned STOP result, not convert it to acquisition PASS.
    """
    if (type(camera) is not str or camera not in EXPOSURES or
            type(exposure) is not str or exposure != EXPOSURES[camera] or
            type(obsid) is not str or obsid != OBS_ID):
        raise ValueError("STOP_EXPECTED_IDENTITY_CONFIG")
    if (type(report) is not dict or report.get("status") != "HEADER_LAYOUT_ONLY"
            or report.get("declared_data_region_bytes_read") != 0):
        raise ValueError("STOP_STRUCTURE_REPORT")
    hdus = report.get("hdus")
    if (type(hdus) is not list or not 1 <= len(hdus) <= 128
            or report.get("hdu_count") != len(hdus)
            or any(type(item) is not dict or item.get("hdu") != i for i, item in enumerate(hdus))):
        raise ValueError("STOP_HDU_ROSTER")
    if sum(len(item.get("cards", [])) * 80 for item in hdus) > 2 * 1024**2:
        raise ValueError("STOP_HEADER_CAP")
    headers = [_header(item) for item in hdus]
    events = [i for i, header in enumerate(headers) if "EVENTS" in
              [card.value for card in header.cards if card.keyword == "EXTNAME"]]
    reason = []
    if len(events) != 1 or events[0] == 0:
        reason.append("EVENTS_ROSTER")
    identities = []
    for index in [0] + [i for i in events if i != 0]:
        identity = _identity(headers[index], camera, exposure, obsid)
        identities.append({"hdu": index, "role": "PRIMARY" if index == 0 else "EVENTS",
                           "fields": identity})
        if index and (headers[index].get("XTENSION") != "BINTABLE"
                      or headers[index].count("EXTNAME") != 1):
            reason.append("EVENTS_HEADER_CONFLICT")
        for key, field in identity.items():
            if field["state"] not in ("MATCH", "MISSING"):
                reason.append("IDENTITY_CONFLICT")
    for key in ("OBS_ID", "INSTRUME", "EXPIDSTR"):
        if not any(item["fields"][key]["state"] == "MATCH" for item in identities):
            reason.append("IDENTITY_MISSING")
    status = ("STOP_HEADER_IDENTITY_CONFLICT" if any(r != "IDENTITY_MISSING" for r in reason)
              else "STOP_HEADER_IDENTITY_MISSING" if reason else "HEADER_IDENTITY_AUTHENTICATED")
    return {"status": status, "expected": {"obsid": obsid, "camera": camera, "exposure": exposure},
            "identity": identities, "reasons": sorted(set(reason)), "hdu_count": len(headers),
            "hdus": [_inventory(h, i) for i, h in enumerate(headers)],
            "scope": "HEADER_IDENTITY_AND_METADATA_ONLY_NOT_CALIBRATION_OR_RECOVERY"}
