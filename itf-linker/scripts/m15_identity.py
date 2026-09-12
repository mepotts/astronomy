"""Offline, fail-closed observation provenance prototype; not a campaign runner.

Only a separately verified exporter contract licenses residual matching. Numeric
lexical precision alone is NOT such verification. No historical fit is regraded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

D = Decimal
IDENTITY_FIELDS = ("JD", "RA", "Dec", "obscode", "note1", "note2", "discovery_asterisk")


class IdentityHold(ValueError):
    """Missing, unsupported or ambiguous identity, never a scientific FAIL."""


def decimal(value: object) -> Decimal:
    # A float has already lost the original JSON/input precision.
    if not isinstance(value, (str, Decimal)):
        raise IdentityHold("decimal identity requires original text or Decimal")
    try:
        number = D(value)
    except InvalidOperation as exc:
        raise IdentityHold("invalid decimal identity") from exc
    if not number.is_finite():
        raise IdentityHold("nonfinite identity")
    return number


def quantum(value: Decimal) -> Decimal:
    return D(10) ** value.as_tuple().exponent


def valid_hash(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class Observation:
    source_sha256: str
    row_number: int
    line_sha256: str
    jd: Decimal
    ra: Decimal
    dec: Decimal
    jd_quantum: Decimal
    ra_quantum: Decimal
    dec_quantum: Decimal
    station: str
    note1: str
    note2: str
    discovery: str

    @property
    def key(self) -> tuple:
        # Precision/provenance stay on each occurrence; physical duplicates need
        # not have the same spelling, designation or number of decimal places.
        return (self.jd, self.ra, self.dec, self.station,
                self.note1, self.note2, self.discovery)


def observation(line: str, *, source_sha256: str, row_number: int) -> Observation:
    """Strict single-line C/B optical subset of the retained OBS80 layout.

    Source is the exact complete input-file hash; physical row numbers are 1-based.
    Two-line/other record types HOLD instead of being silently dropped.
    """
    raw = line.rstrip("\r\n")
    if not valid_hash(source_sha256) or type(row_number) is not int or row_number < 1:
        raise IdentityHold("invalid source provenance")
    if len(raw) != 80 or not raw.isascii() or raw[14] not in {"C", "B"}:
        raise IdentityHold("only complete single-line C/B optical records supported")
    if raw[12] not in {" ", "*"} or not re.fullmatch("[A-Za-z0-9]{3}", raw[77:80]):
        raise IdentityHold("invalid discovery/station field")
    try:
        day = decimal(raw[23:32].strip())
        integer_day = int(day)
        stamp = date(int(raw[15:19]), int(raw[20:22]), integer_day)
        h, m, sec = int(raw[32:34]), int(raw[35:37]), decimal(raw[38:44].strip())
        deg, minute = int(raw[45:47]), int(raw[48:50])
        second = decimal(raw[51:56].strip())
    except (ValueError, OverflowError) as exc:
        raise IdentityHold("invalid optical date/coordinates") from exc
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= sec < 60):
        raise IdentityHold("invalid right ascension")
    if not (0 <= deg <= 90 and 0 <= minute < 60 and 0 <= second < 60):
        raise IdentityHold("invalid declination")
    if raw[44] not in {"+", "-"} or (deg == 90 and (minute or second)):
        raise IdentityHold("invalid declination sign/pole")
    jd = D(stamp.toordinal()) + D("1721424.5") + day - integer_day
    ra = D(15) * (D(h) + D(m) / 60 + sec / 3600)
    dec = (D(deg) + D(minute) / 60 + second / 3600) * (-1 if raw[44] == "-" else 1)
    return Observation(source_sha256, row_number, hashlib.sha256(raw.encode()).hexdigest(),
                       jd, ra, dec, quantum(day), quantum(sec) / 240,
                       quantum(second) / 3600, raw[77:80], raw[13], raw[14], raw[12])


@dataclass(frozen=True)
class ExportContract:
    """Caller-supplied, independently verified contract, not inferred from pixels/digits.

    evidence_sha256 identifies a retained proof binding exporter source/binary/version,
    rounding, transformations, inclusion semantics and complete input-row emission.
    This prototype does not produce that proof or authenticate a caller's assertion.
    """
    evidence_sha256: str
    jd_error: Decimal
    ra_error: Decimal
    dec_error: Decimal
    timescale: str = "UTC"
    coordinates: str = "observed_J2000_degrees"
    complete_rows: bool = True
    notes_verbatim: bool = True

    def validate(self) -> None:
        if not valid_hash(self.evidence_sha256):
            raise IdentityHold("missing exporter evidence hash")
        if (self.timescale != "UTC" or self.coordinates != "observed_J2000_degrees"
                or self.complete_rows is not True or self.notes_verbatim is not True):
            raise IdentityHold("unsupported exporter semantics")
        for error in (self.jd_error, self.ra_error, self.dec_error):
            if not isinstance(error, D) or not error.is_finite() or not 0 <= error <= D("1e-6"):
                raise IdentityHold("export error is unknown or exceeds prototype precision cap")


def residual_identity(row: dict) -> tuple:
    if not isinstance(row, dict):
        raise IdentityHold("residual row is not an object")
    if any(key not in row for key in (*IDENTITY_FIELDS, "incl")):
        raise IdentityHold("missing residual identity/inclusion field")
    jd, ra, dec = (decimal(row[key]) for key in ("JD", "RA", "Dec"))
    if not (0 <= ra < 360 and -90 <= dec <= 90):
        raise IdentityHold("invalid residual coordinates")
    station, note1, note2, discovery = (row[key] for key in IDENTITY_FIELDS[3:])
    if (not isinstance(station, str) or not re.fullmatch("[A-Za-z0-9]{3}", station)
            or not isinstance(note1, str) or len(note1) != 1
            or not isinstance(note2, str) or not isinstance(discovery, str)
            or note2 not in {"C", "B"} or discovery not in {" ", "*"}):
        raise IdentityHold("unsupported residual station/notes encoding")
    # Do not accept truthy strings, null, flags, or silently default missing incl.
    if type(row["incl"]) is not int or row["incl"] not in {0, 1}:
        raise IdentityHold("unsupported inclusion encoding")
    return jd, ra, dec, station, note1, note2, discovery


def match(published: list[Observation], appended: list[Observation], residuals: list[dict],
          contract: ExportContract | None = None) -> dict:
    """Match the COMPLETE joint input to the COMPLETE residual output or HOLD.

    Conservative uniqueness: each side must have degree exactly one in the
    compatibility graph. Even an ambiguous graph with a unique global perfect
    matching HOLDs. No nearest-position, order-based or broad-window tie breaking.
    HOLD/duplicate returns used=None (unmeasurable), never zero or a PASS.
    """
    result = {"status": "HOLD", "appended_total": len(appended), "used": None,
              "pairs": [], "reason": None}
    try:
        if not appended:
            raise IdentityHold("empty appended population")
        rows = published + appended
        occurrences = [(r.source_sha256, r.row_number) for r in rows]
        if len(set(occurrences)) != len(occurrences):
            raise IdentityHold("reused input provenance occurrence")
        for row in rows:
            if not valid_hash(row.source_sha256) or not valid_hash(row.line_sha256):
                raise IdentityHold("missing input provenance hash")
            if type(row.row_number) is not int or row.row_number < 1:
                raise IdentityHold("invalid input occurrence")
            if any(not isinstance(v, D) or not v.is_finite() for v in
                   (row.jd, row.ra, row.dec, row.jd_quantum, row.ra_quantum, row.dec_quantum)):
                raise IdentityHold("invalid input decimals/precision")
            if min(row.jd_quantum, row.ra_quantum, row.dec_quantum) <= 0:
                raise IdentityHold("missing input precision")
            if not (0 <= row.ra < 360 and -90 <= row.dec <= 90):
                raise IdentityHold("invalid input coordinates")
            residual_identity(dict(zip(IDENTITY_FIELDS, row.key, strict=True), incl=0))
        published_keys = {row.key for row in published}
        if any(row.key in published_keys for row in appended):
            result.update(status="ALREADY_PUBLISHED", reason="exact published duplicate")
            return result
        if contract is None:
            raise IdentityHold("exporter precision/identity contract not verified")
        contract.validate()
        identities = [residual_identity(row) for row in residuals]
        if len(rows) != len(identities):
            raise IdentityHold("joint input/residual multiplicity mismatch")
        pairs = []
        consumed: set[int] = set()
        for input_index, row in enumerate(rows):
            candidates = []
            for residual_index, identity in enumerate(identities):
                jd, ra, dec, *notes = identity
                distance_ra = abs(ra - row.ra) % 360
                distance_ra = min(distance_ra, 360 - distance_ra)
                if (tuple(notes) == row.key[3:] and abs(jd - row.jd) <= contract.jd_error
                        and distance_ra <= contract.ra_error
                        and abs(dec - row.dec) <= contract.dec_error):
                    candidates.append(residual_index)
            if len(candidates) != 1 or candidates[0] in consumed:
                raise IdentityHold("unmatched or ambiguous one-to-one residual identity")
            consumed.add(candidates[0])
            pairs.append((input_index, candidates[0]))
        if len(consumed) != len(identities):
            raise IdentityHold("unconsumed residual")
        used = sum(residuals[j]["incl"] for i, j in pairs if i >= len(published))
        if not 0 <= used <= len(appended):
            raise IdentityHold("internal consumption invariant")
        result.update(status="MATCHED", used=used, pairs=pairs,
                      exporter_evidence_sha256=contract.evidence_sha256)
    except IdentityHold as exc:
        result["reason"] = str(exc)
    return result


def compatibility_audit(root: Path) -> dict:
    """Read retained artifacts only; aggregate schema/precision/hash proof, no fits.

    Filenames and identifiers are not emitted. The corpus manifest digest binds
    sorted relative paths + content hashes for total.json and paired obs.txt.
    """
    paths = sorted(root.rglob("total.json"))
    if not paths:
        raise IdentityHold("no retained residual files")
    fields = Counter()
    digits = {key: Counter() for key in ("JD", "RA", "Dec")}
    types = {key: Counter() for key in ("incl", "note1", "note2", "discovery_asterisk")}
    rows = 0
    manifest = []
    for path in paths:
        content = path.read_bytes()
        manifest.append((path.relative_to(root).as_posix(), hashlib.sha256(content).hexdigest()))
        obs = path.with_name("obs.txt")
        if obs.is_file():
            manifest.append((obs.relative_to(root).as_posix(), hashlib.sha256(obs.read_bytes()).hexdigest()))
        document = json.loads(content, parse_float=D)
        for obj in document.get("objects", {}).values():
            for row in obj.get("observations", {}).get("residuals", []):
                rows += 1
                fields.update(row.keys())
                for key, counts in digits.items():
                    value = row.get(key)
                    if isinstance(value, D):
                        counts[str(-value.as_tuple().exponent)] += 1
                    else:
                        counts["non_decimal_or_missing"] += 1
                for key, counts in types.items():
                    counts[type(row.get(key)).__name__] += 1
    return {"status": "HOLD_EXPORT_CONTRACT", "files": len(paths), "residual_rows": rows,
            "field_presence_counts": dict(sorted(fields.items())),
            "lexical_decimal_places_counts": digits, "field_type_counts": types,
            "manifest_entries": len(manifest),
            "manifest_sha256": hashlib.sha256(json.dumps(sorted(manifest), separators=(",", ":")).encode()).hexdigest(),
            "matcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scientific_rows_regraded": 0,
            "reason": "lexical precision does not verify export error, transforms or row lineage"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(compatibility_audit(args.audit_root), indent=2))
