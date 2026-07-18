"""Deterministic lint rules over (ParsedQuery, live Schema). THE PRODUCT.

Every rule asserts only what the live schema confirms, so the output is correct by construction.
The M1 rules (BUILD-PLAN.md S4) plus the correctness pass (M1.1):

1. **UNKNOWN_TABLE / UNKNOWN_COLUMN** — any referenced table/column absent from the schema, with a
   ``difflib`` "did you mean?" suggestion drawn from the *real* schema names. Table matching is
   **case-insensitive** (ADQL regular identifiers are), and ``TAP_UPLOAD.*`` tables (and columns
   qualified by their alias) are **exempt** — uploaded tables never appear in TAP_SCHEMA.
2. **MISSING_JOIN_KEY** — a JOIN whose ``ON`` does not use a legitimate join key. "Legitimate" means:
   a declared inter-table FK (``TAP_SCHEMA.keys``), OR a curated per-archive join column, OR a
   column that co-exists in both joined tables with a compatible datatype. Only an ``ON`` that
   references columns that don't co-exist warns. (Gaia's live ``TAP_SCHEMA.keys`` declares only
   tap_schema-internal keys, so the FK-only premise is empirically false — hence the allowlist.)
3. **NO_SPATIAL_CONSTRAINT** — a FROM table has positional columns (UCD ``pos.eq.ra``/``pos.eq.dec``)
   but the **WHERE clause** has no ``CONTAINS``/``INTERSECTS``/``DISTANCE`` predicate and no narrow
   positional box (RA and Dec both range-bounded) → full-catalog scan.
4. **NO_ROW_LIMIT** — no ``TOP``/``LIMIT``; advisory, endpoint-aware (Gaia caps sync at 2000 rows).
   Suppressed for aggregate-only queries (``SELECT COUNT(*) ...`` returns one row).
5. **IDENTIFIERS_UNCHECKED** — the ADQL parsed but identifier extraction failed; we say so honestly
   instead of reporting the query clean with zero identifier checks.
6. **SCHEMA_STALE** — the cached TAP_SCHEMA snapshot is older than the freshness threshold.
"""

from __future__ import annotations

import difflib
import re

from .endpoints import ENDPOINTS
from .models import Diagnostic, Fix, ParsedQuery, Schema, Severity
from .schema import SCHEMA_MAX_AGE_DAYS, snapshot_age_days

# UCDs that mark a table as positional (so a missing spatial constraint is a full-scan footgun).
_RA_UCDS = ("pos.eq.ra",)
_DEC_UCDS = ("pos.eq.dec",)

# Endpoints with a known sync-query row cap, surfaced in the NO_ROW_LIMIT advisory.
_SYNC_ROW_CAP = {"gaia": 2000}

# The uploaded-table schema name (case-insensitive). Tables under it never appear in TAP_SCHEMA.
_UPLOAD_SCHEMA = "tap_upload"

# Curated per-archive JOIN-key allowlist (M1.1 redesign of MISSING_JOIN_KEY). Gaia's live
# TAP_SCHEMA.keys declares only tap_schema-internal foreign keys, so it cannot bless real science
# joins; ``source_id`` is the universal join column across gaiadr3.gaia_source and the DR3
# value-added tables (astrophysical_parameters, etc.). Extend per archive as needed.
_JOIN_KEY_ALLOWLIST: dict[str, set[str]] = {
    "gaia": {"source_id"},
}

# Datatype families for JOIN-key compatibility (a shared join column should have compatible types).
_INT_TYPES = {"long", "int", "integer", "short", "smallint", "bigint", "unsignedbyte"}
_FLOAT_TYPES = {"float", "double", "real", "double precision"}

# LIMIT n — the single most common SQL->ADQL stumble; ADQL uses SELECT TOP n instead.
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)", re.IGNORECASE)


def lint(parsed: ParsedQuery, schema: Schema, endpoint_key: str = "gaia") -> list[Diagnostic]:
    """Run all lint rules and return the diagnostics."""
    diagnostics: list[Diagnostic] = []

    # Schema-freshness advisory is independent of the query, so surface it for every lint.
    diagnostics += _rule_schema_age(schema)

    if not parsed.is_valid_syntax:
        diagnostics.append(_invalid_syntax_diagnostic(parsed))
        return diagnostics  # nothing else is meaningful on an unparseable query

    # The ADQL was syntactically valid but identifier extraction failed: be honest that the
    # unknown-table/column checks did NOT run rather than silently reporting the query clean.
    if parsed.extraction_error:
        diagnostics.append(
            Diagnostic(
                code="IDENTIFIERS_UNCHECKED",
                severity=Severity.WARNING,
                message=(
                    f"Identifier validation was skipped: {parsed.extraction_error}. "
                    "Unknown-table/column checks did NOT run, so this query is not confirmed clean."
                ),
                suggestion="Verify table/column names manually, or rephrase so the parser can "
                           "extract identifiers (e.g. put the POINT argument first in CONTAINS).",
            )
        )

    # Case-insensitive table resolution: map each referenced table to its canonical schema name so
    # column and spatial checks run even when the query uses a different case (e.g. GAIADR3.GAIA_SOURCE).
    known_by_lc = {t.lower(): t for t in schema.tables}
    referenced_tables = list(parsed.tables)
    upload_ids = _upload_identifiers(parsed)

    diagnostics += _rule_unknown_tables(referenced_tables, known_by_lc, upload_ids)

    # Only validate columns against tables we actually recognise (resolving a column against a
    # table the schema doesn't know would produce noise on top of the UNKNOWN_TABLE error).
    resolvable_tables = list(
        dict.fromkeys(
            known_by_lc[t.lower()] for t in referenced_tables if t.lower() in known_by_lc
        )
    )
    diagnostics += _rule_unknown_columns(parsed, schema, resolvable_tables, upload_ids)

    diagnostics += _rule_missing_join_key(parsed, schema, resolvable_tables, endpoint_key)
    diagnostics += _rule_no_spatial_constraint(parsed, schema, resolvable_tables)
    diagnostics += _rule_no_row_limit(parsed, endpoint_key)

    return diagnostics


# --- INVALID_SYNTAX (with TOP-not-LIMIT hint) -------------------------------------------


def _invalid_syntax_diagnostic(parsed: ParsedQuery) -> Diagnostic:
    """Build the INVALID_SYNTAX diagnostic, with a targeted TOP-not-LIMIT hint when relevant."""
    suggestion: str | None = None
    fix: Fix | None = None
    m = _LIMIT_RE.search(parsed.raw)
    if m:
        n = m.group(1)
        suggestion = f"ADQL uses `SELECT TOP n`, not `LIMIT` — write `SELECT TOP {n} ...`."
        fix = Fix(
            kind="rewrite_limit_as_top",
            target=m.group(0),
            replacement=f"TOP {n}",
            span=(m.start(), m.end()),
        )
    return Diagnostic(
        code="INVALID_SYNTAX",
        severity=Severity.ERROR,
        message=f"ADQL failed to parse: {parsed.parse_error}",
        suggestion=suggestion,
        fix=fix,
    )


# --- SCHEMA_STALE -----------------------------------------------------------------------


def _rule_schema_age(schema: Schema) -> list[Diagnostic]:
    age = snapshot_age_days(schema)
    if age is None or age <= SCHEMA_MAX_AGE_DAYS:
        return []
    return [
        Diagnostic(
            code="SCHEMA_STALE",
            severity=Severity.WARNING,
            message=(
                f"The cached TAP_SCHEMA snapshot is {age:.0f} days old (older than "
                f"{SCHEMA_MAX_AGE_DAYS} days); table/column checks may be out of date."
            ),
            suggestion="Refresh it with `--refresh` (or load_schema(..., refresh=True)).",
        )
    ]


# --- TAP_UPLOAD exemption ---------------------------------------------------------------


def _is_upload_table(name: str) -> bool:
    """True if ``name`` is a ``TAP_UPLOAD.*`` table (case-insensitive, tolerant of quoting)."""
    return name.split(".")[0].strip('"').lower() == _UPLOAD_SCHEMA


def _upload_identifiers(parsed: ParsedQuery) -> set[str]:
    """Lowercased names exempt from schema checks: upload tables, their bare names, and aliases."""
    ids: set[str] = set(parsed.upload_aliases)  # aliases are already lowercased by the parser
    for t in parsed.tables:
        if _is_upload_table(t):
            ids.add(t.lower())
            ids.add(t.split(".")[-1].lower())
    return ids


def _is_upload_ref(table_hint: str | None, upload_ids: set[str]) -> bool:
    """True if a column's table qualifier points at an uploaded table (so it's exempt)."""
    if not table_hint:
        return False
    if _is_upload_table(table_hint):
        return True
    hint = table_hint.lower()
    return hint in upload_ids or hint.split(".")[0] in upload_ids


# --- rule 1a: unknown table -------------------------------------------------------------


def _rule_unknown_tables(
    referenced: list[str], known_by_lc: dict[str, str], upload_ids: set[str]
) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for tbl in referenced:
        if _is_upload_table(tbl):
            continue  # uploaded tables are never in TAP_SCHEMA
        if tbl.lower() in known_by_lc:
            continue  # case-insensitive match
        matches = _close_matches(tbl, list(known_by_lc.values()))
        out.append(
            Diagnostic(
                code="UNKNOWN_TABLE",
                severity=Severity.ERROR,
                message=f"Table {tbl!r} is not in the schema.",
                suggestion=_format_did_you_mean(matches),
                fix=Fix(kind="replace_table", target=tbl, replacement=matches[0])
                if matches
                else None,
            )
        )
    return out


# --- rule 1b: unknown column ------------------------------------------------------------


def _rule_unknown_columns(
    parsed: ParsedQuery, schema: Schema, resolvable_tables: list[str], upload_ids: set[str]
) -> list[Diagnostic]:
    if not resolvable_tables:
        return []

    # Valid bare column names per recognised table (keyed by lowercased table name for
    # case-insensitive qualifier matching), plus a union across all recognised tables.
    valid_by_table_lc: dict[str, set[str]] = {
        t.lower(): {c.column_name for c in schema.columns_for(t)} for t in resolvable_tables
    }
    all_valid: set[str] = set().union(*valid_by_table_lc.values()) if valid_by_table_lc else set()

    out: list[Diagnostic] = []
    for table_hint, bare in _distinct_column_refs(parsed):
        if _is_upload_ref(table_hint, upload_ids):
            continue  # column belongs to an uploaded table -> not in TAP_SCHEMA, exempt
        # If the reference is qualified with a known table, check against that table only;
        # otherwise check against the union of all recognised tables.
        if table_hint and table_hint.lower() in valid_by_table_lc:
            candidates = valid_by_table_lc[table_hint.lower()]
            scope: str | None = table_hint
        else:
            candidates = all_valid
            scope = None

        if bare.lower() in {c.lower() for c in candidates}:
            continue

        where = f" on table {scope!r}" if scope else ""
        matches = _close_matches(bare, sorted(all_valid))
        out.append(
            Diagnostic(
                code="UNKNOWN_COLUMN",
                severity=Severity.ERROR,
                message=f"Column {bare!r} is not in the schema{where}.",
                suggestion=_format_did_you_mean(matches),
                fix=Fix(kind="replace_column", target=bare, replacement=matches[0])
                if matches
                else None,
            )
        )
    return out


def _distinct_column_refs(parsed: ParsedQuery) -> list[tuple[str | None, str]]:
    """Reduce the parser's multi-form column list to distinct ``(table_hint, bare_name)`` refs.

    The parser emits each column as ``schema.table.col``, ``table.col`` and bare ``col``. We pick
    the most-qualified form per bare name to recover the owning table when available.
    """
    best: dict[str, tuple[str | None, str]] = {}
    for raw in parsed.columns:
        parts = raw.split(".")
        bare = parts[-1]
        if bare == "*":
            continue
        # table hint = the schema.table part if this form carries one (3+ parts), else the
        # single qualifier (2 parts), else None.
        if len(parts) >= 3:
            table_hint: str | None = ".".join(parts[:-1])
        elif len(parts) == 2:
            table_hint = parts[0]
        else:
            table_hint = None
        existing = best.get(bare)
        # Prefer the entry that carries a fully-qualified (dotted) table hint.
        if existing is None or (table_hint and "." in table_hint and not (existing[0] and "." in existing[0])):
            best[bare] = (table_hint, bare)
    return list(best.values())


# --- rule 2: missing JOIN key -----------------------------------------------------------


def _rule_missing_join_key(
    parsed: ParsedQuery, schema: Schema, resolvable_tables: list[str], endpoint_key: str
) -> list[Diagnostic]:
    if not parsed.has_join:
        return []
    # Need at least two recognised tables to talk about a join between them. (An unresolved side,
    # e.g. a TAP_UPLOAD table, means we can't check co-existence — so we don't guess.)
    if len(resolvable_tables) < 2:
        return []

    on_cols = {c.lower() for c in parsed.join_on_columns}
    if not on_cols:
        return []  # the ON predicate couldn't be parsed; don't fabricate a warning

    # (a) A declared inter-table foreign key that the ON clause actually uses -> legitimate join.
    declared_fk_cols: set[str] = set()
    for k in schema.keys:
        if k.from_table in resolvable_tables and k.target_table in resolvable_tables:
            declared_fk_cols.add(k.from_column.lower())
            declared_fk_cols.add(k.target_column.lower())
    if declared_fk_cols & on_cols:
        return []

    # (b) A curated per-archive join key that the ON clause uses -> legitimate join.
    allow = _JOIN_KEY_ALLOWLIST.get(endpoint_key, set())
    if on_cols & allow:
        return []

    # (b') An ON column that co-exists in >=2 joined tables with a compatible datatype -> legitimate.
    if _has_shared_join_column(on_cols, schema, resolvable_tables):
        return []

    # (c) The ON references columns that don't co-exist in the joined tables -> warn.
    hint = ", ".join(sorted(allow)) if allow else "a shared identifier (e.g. source_id)"
    return [
        Diagnostic(
            code="MISSING_JOIN_KEY",
            severity=Severity.WARNING,
            message=(
                "JOIN ON does not use a recognized join key: the referenced columns do not "
                "co-exist in the joined tables, and no declared foreign key links them."
            ),
            suggestion=f"Join on a column shared by both tables, e.g. {hint}.",
        )
    ]


def _has_shared_join_column(on_cols: set[str], schema: Schema, tables: list[str]) -> bool:
    """True if some ON column exists in >=2 of the joined tables with pairwise-compatible datatypes."""
    for col in on_cols:
        dtypes: list[str] = []
        for t in tables:
            for c in schema.columns_for(t):
                if c.column_name.lower() == col:
                    dtypes.append((c.datatype or "").lower())
                    break
        if len(dtypes) >= 2 and all(_datatypes_compatible(dtypes[0], d) for d in dtypes[1:]):
            return True
    return False


def _datatypes_compatible(a: str, b: str) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    if a == b:
        return True
    if a in _INT_TYPES and b in _INT_TYPES:
        return True
    if a in _FLOAT_TYPES and b in _FLOAT_TYPES:
        return True
    return False


# --- rule 3: no spatial constraint ------------------------------------------------------


def _rule_no_spatial_constraint(
    parsed: ParsedQuery, schema: Schema, resolvable_tables: list[str]
) -> list[Diagnostic]:
    if parsed.has_spatial_constraint:
        return []

    positional = [t for t in resolvable_tables if _is_positional_table(schema, t)]
    if not positional:
        return []

    # A narrow positional box (RA and Dec both range-bounded in the WHERE clause) also constrains
    # the query to a region, so it satisfies the rule (DATA-SOURCES.md S3).
    range_cols = {c.lower() for c in parsed.range_constrained_columns}
    if range_cols and any(_has_positional_box(schema, t, range_cols) for t in positional):
        return []

    tbls = ", ".join(positional)
    return [
        Diagnostic(
            code="NO_SPATIAL_CONSTRAINT",
            severity=Severity.WARNING,
            message=(
                f"No CONTAINS/INTERSECTS/DISTANCE constraint; {tbls} has RA/Dec columns, so this "
                f"scans the whole catalog."
            ),
            suggestion=(
                "Add a positional predicate, e.g. "
                "CONTAINS(POINT(ra, dec), CIRCLE(<ra>, <dec>, <radius_deg>)) = 1 "
                "(ADQL 2.1 made the coordinate-frame argument optional; the legacy "
                "POINT('ICRS', ra, dec) form is also accepted)."
            ),
        )
    ]


def _is_positional_table(schema: Schema, table: str) -> bool:
    has_ra = has_dec = False
    for c in schema.columns_for(table):
        ucd = (c.ucd or "").lower()
        if any(tag in ucd for tag in _RA_UCDS):
            has_ra = True
        if any(tag in ucd for tag in _DEC_UCDS):
            has_dec = True
    return has_ra and has_dec


def _has_positional_box(schema: Schema, table: str, range_cols: set[str]) -> bool:
    """True if the table's primary RA column AND its primary Dec column are both range-bounded."""
    ra_cols, dec_cols = _positional_axis_columns(schema, table)
    return bool(ra_cols & range_cols) and bool(dec_cols & range_cols)


def _positional_axis_columns(schema: Schema, table: str) -> tuple[set[str], set[str]]:
    """Primary RA / Dec column names for a table (UCD's leading token is pos.eq.ra / pos.eq.dec).

    Using the *leading* UCD token deliberately excludes derivatives like ra_error
    (``stat.error;pos.eq.ra``) and pmra (``pos.pm;pos.eq.ra``) whose primary meaning is not position.
    """
    ra_cols: set[str] = set()
    dec_cols: set[str] = set()
    for c in schema.columns_for(table):
        first = (c.ucd or "").lower().split(";")[0].strip()
        if first in _RA_UCDS:
            ra_cols.add(c.column_name.lower())
        if first in _DEC_UCDS:
            dec_cols.add(c.column_name.lower())
    return ra_cols, dec_cols


# --- rule 4: no row limit ---------------------------------------------------------------


def _rule_no_row_limit(parsed: ParsedQuery, endpoint_key: str) -> list[Diagnostic]:
    if parsed.has_top_or_limit:
        return []
    if parsed.is_aggregate_only:
        return []  # an aggregate-only query (e.g. COUNT(*)) returns a single row; no TOP needed
    cap = _SYNC_ROW_CAP.get(endpoint_key)
    ep_name = ENDPOINTS[endpoint_key].name if endpoint_key in ENDPOINTS else endpoint_key
    if cap:
        msg = f"No TOP/row limit; {ep_name} caps sync queries at {cap} rows."
    else:
        msg = "No TOP/row limit; consider adding one to bound the result set."
    return [
        Diagnostic(
            code="NO_ROW_LIMIT",
            severity=Severity.INFO,
            message=msg,
            suggestion="Add 'TOP 100' (or a suitable limit) while iterating.",
        )
    ]


# --- shared helpers ---------------------------------------------------------------------


def _close_matches(name: str, candidates: list[str]) -> list[str]:
    """Fuzzy matches from real schema names (case-insensitive), best first, up to 3."""
    if not candidates:
        return []
    matches = difflib.get_close_matches(name, candidates, n=3, cutoff=0.6)
    if not matches:
        lower_map = {c.lower(): c for c in candidates}
        lc = difflib.get_close_matches(name.lower(), list(lower_map), n=3, cutoff=0.6)
        matches = [lower_map[m] for m in lc]
    return matches


def _format_did_you_mean(matches: list[str]) -> str | None:
    """Human 'did you mean?' prose from a ranked match list (or None if empty)."""
    if not matches:
        return None
    if len(matches) == 1:
        return f"did you mean {matches[0]!r}?"
    quoted = ", ".join(repr(m) for m in matches)
    return f"did you mean one of: {quoted}?"
