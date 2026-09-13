"""Bounded, offline PPS HTML metadata only; no product or source-science reader.

Unknown values are hashed, never copied to output. A parsed document is not
complete inventory, calibrated exposure, or an authorization to follow links.
"""

import codecs
import hashlib
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit

MAX_BYTES = 872917
ROLES = {"EP", "OB", "RG", "OM"}
INSTRUMENTS = {"EPN", "PN", "EMOS1", "EMOS2", "M1", "M2", "RGS1", "RGS2", "R1", "R2", "RG", "OM", "EP"}
MODES = {"PrimeFullWindow", "PrimeFullWindowExtended", "PrimeLargeWindow", "PrimeSmallWindow",
         "PrimePartialW2", "PrimePartialW3", "PrimePartialW4", "PrimeTiming", "PrimeBurst",
         "Fast", "Image", "Imaging", "Offset", "Diagnostic", "Diagnostic3x3", "UNDEFINED",
         "HighEventRateWithSES", "HighEventRateWithoutSES", "Spectroscopy", "FullFrame"}
FILTERS = {"Thin", "Thin1", "Thin2", "Medium", "Thick", "Open", "Closed", "CalClosed",
           "Blocked", "UVM2", "UVW1", "UVW2", "U", "B", "V", "White", "Grism1", "Grism2"}
DATA_MODES = {"imaging", "fast", "fast, imaging", "spectroscopy", "offsetdata",
              "discardedlinesdata", "diagnostic", "timing", "burst", "undefined"}
PRODUCTS = {"PIEVLI", "MIEVLI", "ATTTSR", "EXPMAP", "OBSMLI", "SUMMAR", "BADPIX", "FBKTSR"}
LABELS = {
    "observation id": "obsid", "observation identifier": "obsid", "obsid": "obsid",
    "obs id": "obsid", "revolution": "revolution", "odf version": "odf_version",
    "odf id": "odf_id", "sas version": "sas_version", "sasvers": "sas_version",
    "pps version": "pps_version", "processing date": "processing_date",
    "generator": "generator", "start time": "start", "stop time": "stop",
    "scheduled length": "duration", "proposed duration": "duration",
    "inst": "instrument", "instrument": "instrument", "exp id": "exposure_id",
    "exposure id": "exposure_id", "sched": "scheduled", "scheduled": "scheduled",
    "mode": "mode", "data mode": "data_mode", "filter": "filter",
    "total duration": "duration", "duration": "duration", "actual start": "start",
    "actual stop": "stop", "start": "start", "stop": "stop",
}
OBS_FIELDS = {"obsid", "revolution", "odf_version", "odf_id", "sas_version", "pps_version",
              "processing_date", "generator", "start", "stop", "duration"}
EXPOSURE_FIELDS = {"instrument", "exposure_id", "scheduled", "mode", "data_mode", "filter",
                   "duration", "start", "stop"}


def _hash(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def _label(value):
    text = " ".join(value.lower().strip(" :.").split())
    match = re.search(r"\s*[\[(](s|sec|seconds|ks|utc|tt)[\])]$", text)
    unit = match[1] if match else None
    if match:
        text = text[:match.start()].strip()
    return LABELS.get(text), unit


def _safe(field, text, unit=None):
    value = " ".join(text.split())
    result = {"status": "MISSING", "value": None, "unit": unit}
    if not value:
        return result
    valid = False
    if field == "obsid":
        valid = re.fullmatch(r"[0-9]{10}", value) is not None
    elif field == "instrument":
        valid = value in INSTRUMENTS
    elif field == "exposure_id":
        valid = re.fullmatch(r"[SUX][0-9]{3}", value) is not None
    elif field == "scheduled":
        valid = value in {"Y", "N", "Yes", "No"}
    elif field == "mode":
        valid = value in MODES
    elif field == "data_mode":
        valid = value.lower() in DATA_MODES
    elif field == "filter":
        valid = value in FILTERS
    elif field in {"revolution", "odf_version"}:
        valid = re.fullmatch(r"[0-9]{1,8}", value) is not None
    elif field in {"sas_version", "pps_version"}:
        valid = re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{1,6}){0,4}", value) is not None
    elif field == "odf_id":
        valid = re.fullmatch(r"[0-9]{4}_[0-9]{10}_[0-9]{3}", value) is not None
    elif field == "generator":
        valid = re.fullmatch(r"(?:ppssumm|epicsumm|rgssumm|omsumm)-[0-9]+(?:\.[0-9]+){1,3}", value) is not None
    elif field == "duration":
        valid = re.fullmatch(r"[0-9]{1,9}(?:\.[0-9]{1,9})?", value) is not None
    elif field in {"start", "stop", "processing_date"} and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?(?:Z|[+-][0-9]{2}:[0-9]{2})?", value):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            valid = True
        except ValueError:
            pass
    result["status"] = "VALID" if valid else "UNRECOGNIZED"
    if valid:
        result["value"] = value
    else:
        result["value_sha256"] = _hash(value)
    return result


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.stack = []
        self.blocks = []
        self.block = []
        self.hrefs = []
        self.encodings = []
        self.suppressed = 0
        self.flags = set()
        self.cells = 0

    def _flush(self):
        if self.block:
            self.blocks.append(" ".join(self.block))
            self.block = []

    def handle_starttag(self, tag, attrs):
        raw_attrs = attrs
        attrs = dict(attrs)
        if tag in {"script", "style"}:
            self.suppressed += 1
        if self.suppressed:
            return
        if tag == "meta":
            for key, value in raw_attrs:
                if key == "charset":
                    self.encodings.append(value or "")
            if (attrs.get("http-equiv") or "").lower() == "content-type":
                match = re.search(r"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)", attrs.get("content") or "", re.IGNORECASE)
                if match:
                    self.encodings.append(match[1])
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag in {"p", "div", "h1", "h2", "h3", "br", "dt", "dd"}:
            self._flush()
        if tag == "table":
            self.stack.append({"rows": [], "row": None, "cell": None})
        elif self.stack and tag == "tr":
            table = self.stack[-1]
            self._row(table)
            table["row"] = []
        elif self.stack and tag in {"td", "th"}:
            table = self.stack[-1]
            self._cell(table)
            if table["row"] is None:
                table["row"] = []
            table["cell"] = []

    def _cell(self, table):
        if table["cell"] is not None:
            table["row"].append(" ".join(table["cell"]))
            table["cell"] = None
            self.cells += 1
            if self.cells > 20000:
                raise ValueError("STOP_HTML_COMPLEXITY")

    def _row(self, table):
        self._cell(table)
        if table["row"] is not None:
            table["rows"].append(table["row"])
            table["row"] = None

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.suppressed:
            self.suppressed -= 1
            return
        if self.suppressed:
            return
        if self.stack:
            table = self.stack[-1]
            if tag in {"td", "th"}:
                self._cell(table)
            elif tag == "tr":
                self._row(table)
            elif tag == "table":
                self._row(table)
                self.tables.append(self.stack.pop()["rows"])
        if tag in {"p", "div", "h1", "h2", "h3", "dt", "dd"}:
            self._flush()

    def handle_data(self, data):
        if self.suppressed:
            return
        if self.stack and self.stack[-1]["cell"] is not None:
            self.stack[-1]["cell"].append(data)
        else:
            self.block.append(data)

    def finish(self):
        self._flush()
        if self.stack:
            self.flags.add("UNCLOSED_TABLE")
        while self.stack:
            table = self.stack.pop()
            self._row(table)
            self.tables.append(table["rows"])


def _decode(raw):
    probe = _Collector()
    probe.feed(raw.decode("latin-1"))
    names = []
    for name in probe.encodings:
        try:
            normalized = codecs.lookup(name).name
        except LookupError:
            return None, {"status": "UNSUPPORTED", "codec": None, "declarations": len(probe.encodings)}
        if normalized not in {"utf-8", "iso8859-1", "cp1252", "ascii"}:
            return None, {"status": "UNSUPPORTED", "codec": None, "declarations": len(probe.encodings)}
        names.append(normalized)
    if len(set(names)) > 1:
        return None, {"status": "CONFLICTING", "codec": None, "declarations": len(names)}
    codec = names[0] if names else "ascii"
    status = "DECLARED" if names else "MISSING_ASCII_ONLY"
    try:
        text = raw.decode(codec, errors="strict")
    except UnicodeError:
        return None, {"status": "DECODE_FAILED" if names else "MISSING_NONASCII", "codec": codec, "declarations": len(names)}
    return text, {"status": status, "codec": codec, "declarations": len(names)}


def parse_summary(raw: bytes, role: str, obsid: str):
    """Return safe metadata candidates; no automatic completeness/science PASS.

    Missing/unknown encoding or fields produce METADATA_INCOMPLETE. Invalid
    argument/resource contracts raise safe ValueError/TypeError. All exposure
    rows after an identified header remain, including duplicate/short rows.
    """
    if type(raw) is not bytes:
        raise TypeError("STOP_RAW_TYPE")
    if not 0 < len(raw) <= MAX_BYTES or type(role) is not str or role not in ROLES or type(obsid) is not str or not re.fullmatch(r"[0-9]{10}", obsid):
        raise ValueError("STOP_INPUT_CONTRACT")
    text, encoding = _decode(raw)
    result = {"status": "METADATA_INCOMPLETE", "role": role, "input_bytes": len(raw),
              "input_sha256": _hash(raw), "encoding": encoding, "identity": {"status": "MISSING", "labelled_candidates": 0},
              "observation_fields": {}, "exposure_rows": [], "exposure_tables": 0,
              "exposure_status": "NOT_IDENTIFIED", "duplicate_exposure_keys": 0,
              "product_references": [], "flags": []}
    if text is None:
        return result
    parser = _Collector()
    parser.feed(text)
    parser.close()
    parser.finish()
    fields = result["observation_fields"]

    def add(label, value):
        field, unit = _label(label)
        if field in OBS_FIELDS:
            fields.setdefault(field, []).append(_safe(field, value, unit))

    keys = []
    for table in parser.tables:
        header = None
        for row in table:
            labels = [_label(cell) for cell in row]
            kinds = [label[0] for label in labels]
            if "instrument" in kinds and "exposure_id" in kinds:
                header = labels
                result["exposure_tables"] += 1
                continue
            if header is not None:
                entry = {"row_number": len(result["exposure_rows"]) + 1, "fields": {},
                         "shape_matches_header": len(row) == len(header)}
                for i, (field, unit) in enumerate(header):
                    if field in EXPOSURE_FIELDS:
                        candidate = _safe(field, row[i] if i < len(row) else "", unit)
                        if field in entry["fields"]:
                            parser.flags.add("DUPLICATE_EXPOSURE_COLUMN")
                            previous = entry["fields"][field]
                            candidates = previous.get("candidates", [previous]) + [candidate]
                            entry["fields"][field] = {"status": "AMBIGUOUS", "value": None,
                                                      "unit": None, "candidates": candidates}
                        else:
                            entry["fields"][field] = candidate
                result["exposure_rows"].append(entry)
                for field in EXPOSURE_FIELDS:
                    entry["fields"].setdefault(field, _safe(field, ""))
                pair = tuple(entry["fields"].get(k, {}).get("value") for k in ("instrument", "exposure_id"))
                if all(pair):
                    keys.append(pair)
            else:
                for i in range(0, len(row) - 1, 2):
                    add(row[i], row[i + 1])
    for block in parser.blocks:
        # Explicit labelled observation identity; a bare number never qualifies.
        match = re.fullmatch(r"\s*(Observation\s+(?:ID|Identifier)|OBSID)\s*:?\s*([0-9]{10})\s*", block, re.IGNORECASE)
        if match:
            add("obsid", match[2])
        elif ":" in block:
            label, value = block.split(":", 1)
            add(label, value)
    identity = fields.get("obsid", [])
    values = [item["value"] for item in identity if item["status"] == "VALID"]
    result["identity"] = {"status": "MATCH" if values and len(values) == len(identity) and set(values) == {obsid} else "CONFLICT_OR_INVALID" if identity else "MISSING", "labelled_candidates": len(identity)}
    result["duplicate_exposure_keys"] = len(keys) - len(set(keys))
    if result["exposure_tables"]:
        result["exposure_status"] = "ROWS_RETAINED" if result["exposure_rows"] else "HEADER_WITHOUT_ROWS"
    refs = set()
    for href in parser.hrefs:
        try:
            base = urlsplit(href).path.rsplit("/", 1)[-1]
        except ValueError:
            continue
        if re.fullmatch(r"P" + obsid + r"[A-Z0-9]{2}[A-Z][0-9]{3}[A-Z0-9]{6}[A-Z0-9]{4}\.(?:FTZ|HTM)", base) and base[17:23] in PRODUCTS:
            refs.add(base)
    result["product_references"] = sorted(refs)
    result["flags"] = sorted(parser.flags)
    if result["identity"]["status"] == "MATCH" and encoding["status"] == "DECLARED" and not result["flags"]:
        result["status"] = "METADATA_PARSED_UNADJUDICATED"
    return result


def compare_summaries(results, obsid):
    """Compare parser-owned outputs, not arbitrary external dictionaries.

    Runtime must first authenticate/recompute each parse result. Equal values
    are consistency only; missing fields/roles remain explicit. Instrument
    aliases PN/EPN, M1/EMOS1, M2/EMOS2 and R1/RGS1,R2/RGS2 normalize solely
    for joining exposure keys. Processing dates/generators are not conflated.
    """
    if type(results) is not list or len(results) > 4 or type(obsid) is not str or not re.fullmatch(r"[0-9]{10}", obsid):
        raise ValueError("STOP_COMPARISON_INPUT")
    roles = [result["role"] for result in results]
    if len(set(roles)) != len(roles) or any(role not in ROLES for role in roles):
        raise ValueError("STOP_COMPARISON_ROLES")
    alias = {"PN": "EPN", "M1": "EMOS1", "M2": "EMOS2", "R1": "RGS1", "R2": "RGS2"}
    groups = {}
    unjoinable = 0
    for result in results:
        for row in result["exposure_rows"]:
            fields = row["fields"]
            instrument = fields["instrument"]["value"]
            exposure = fields["exposure_id"]["value"]
            if instrument is None or exposure is None:
                unjoinable += 1
                continue
            key = (alias.get(instrument, instrument), exposure)
            groups.setdefault(key, []).append((result["role"], fields))
    ledger = []
    for (instrument, exposure), rows in sorted(groups.items()):
        conflicts = []
        missing = []
        for field in sorted(EXPOSURE_FIELDS - {"instrument", "exposure_id"}):
            values = {(item[field]["value"], item[field]["unit"]) for _, item in rows if item[field]["status"] == "VALID"}
            if len(values) > 1:
                conflicts.append(field)
            if any(item[field]["status"] != "VALID" for _, item in rows):
                missing.append(field)
        ledger.append({"instrument": instrument, "exposure_id": exposure, "records": len(rows),
                       "roles": sorted({role for role, _ in rows}), "conflicting_fields": conflicts,
                       "comparison_scope": "CROSS_ROLE" if len({role for role, _ in rows}) > 1 else "SINGLE_ROLE_UNMATCHED",
                       "missing_label_unit_fields": [field for field in ("duration", "start", "stop")
                                                     if any(item[field]["unit"] is None for _, item in rows)],
                       "missing_or_unrecognized_fields": missing})
    obs_conflicts = []
    for field in ("obsid", "revolution", "odf_id", "odf_version"):
        values = {item["value"] for result in results for item in result["observation_fields"].get(field, []) if item["status"] == "VALID"}
        if len(values) > 1 or (field == "obsid" and values and values != {obsid}):
            obs_conflicts.append(field)
    return {"status": "CROSS_DOCUMENT_DIAGNOSTIC_ONLY", "roles_present": sorted(roles),
            "roles_missing": sorted(ROLES - set(roles)), "identity_by_role": {result["role"]: result["identity"]["status"] for result in results},
            "observation_conflicting_fields": obs_conflicts, "exposure_groups": ledger,
            "unjoinable_exposure_rows": unjoinable,
            "processing_comparison": "ROLE_SCOPED_NOT_ASSUMED_EQUAL"}
