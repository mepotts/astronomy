"""Deterministic lint rules over (ParsedQuery, live Schema). THE PRODUCT.

Every rule asserts only what the live schema confirms, so the output is correct by construction.
The four M1 rules (BUILD-PLAN.md S4):

1. **UNKNOWN_TABLE / UNKNOWN_COLUMN** — any referenced table/column absent from the schema, with a
   ``difflib`` "did you mean?" suggestion drawn from the *real* schema names.
2. **MISSING_JOIN_KEY** — a JOIN is present but its ``ON`` doesn't use a declared foreign key
   (``TAP_SCHEMA.keys``), i.e. the two tables are joined on a relationship the schema doesn't bless.
3. **NO_SPATIAL_CONSTRAINT** — a FROM table has positional columns (UCD ``pos.eq.ra``/``pos.eq.dec``)
   but the query has no ``CONTAINS``/``INTERSECTS``/``DISTANCE`` predicate → full-catalog scan.
4. **NO_ROW_LIMIT** — no ``TOP``/``LIMIT``; advisory, endpoint-aware (Gaia caps sync at 2000 rows).
"""

from __future__ import annotations

import difflib

from .endpoints import ENDPOINTS
from .models import Diagnostic, ParsedQuery, Schema, Severity

# UCDs that mark a table as positional (so a missing spatial constraint is a full-scan footgun).
_RA_UCDS = ("pos.eq.ra",)
_DEC_UCDS = ("pos.eq.dec",)

# Endpoints with a known sync-query row cap, surfaced in the NO_ROW_LIMIT advisory.
_SYNC_ROW_CAP = {"gaia": 2000}


def lint(parsed: ParsedQuery, schema: Schema, endpoint_key: str = "gaia") -> list[Diagnostic]:
    """Run all M1 lint rules and return the diagnostics."""
    diagnostics: list[Diagnostic] = []

    if not parsed.is_valid_syntax:
        diagnostics.append(
            Diagnostic(
                code="INVALID_SYNTAX",
                severity=Severity.ERROR,
                message=f"ADQL failed to parse: {parsed.parse_error}",
            )
        )
        return diagnostics  # nothing else is meaningful on an unparseable query

    known_tables = set(schema.tables)
    referenced_tables = list(parsed.tables)

    diagnostics += _rule_unknown_tables(referenced_tables, known_tables)

    # Only validate columns against tables we actually recognise (resolving a column against a
    # table the schema doesn't know would produce noise on top of the UNKNOWN_TABLE error).
    resolvable_tables = [t for t in referenced_tables if t in known_tables]
    diagnostics += _rule_unknown_columns(parsed, schema, resolvable_tables)

    diagnostics += _rule_missing_join_key(parsed, schema, resolvable_tables)
    diagnostics += _rule_no_spatial_constraint(parsed, schema, resolvable_tables)
    diagnostics += _rule_no_row_limit(parsed, endpoint_key)

    return diagnostics


# --- rule 1a: unknown table -------------------------------------------------------------


def _rule_unknown_tables(referenced: list[str], known: set[str]) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for tbl in referenced:
        if tbl in known:
            continue
        suggestion = _did_you_mean(tbl, sorted(known))
        out.append(
            Diagnostic(
                code="UNKNOWN_TABLE",
                severity=Severity.ERROR,
                message=f"Table {tbl!r} is not in the schema.",
                suggestion=suggestion,
            )
        )
    return out


# --- rule 1b: unknown column ------------------------------------------------------------


def _rule_unknown_columns(
    parsed: ParsedQuery, schema: Schema, resolvable_tables: list[str]
) -> list[Diagnostic]:
    if not resolvable_tables:
        return []

    # Valid bare column names across all recognised tables (case-insensitive set), plus a map of
    # which table each column belongs to (for nicer suggestions/messages).
    valid_by_table: dict[str, set[str]] = {
        t: {c.column_name for c in schema.columns_for(t)} for t in resolvable_tables
    }
    all_valid: set[str] = set().union(*valid_by_table.values()) if valid_by_table else set()

    out: list[Diagnostic] = []
    for ref in _distinct_column_refs(parsed):
        table_hint, bare = ref
        # If the reference is qualified with a known table, check against that table only;
        # otherwise check against the union of all recognised tables.
        if table_hint and table_hint in valid_by_table:
            candidates = valid_by_table[table_hint]
            scope = table_hint
        else:
            candidates = all_valid
            scope = None

        if bare.lower() in {c.lower() for c in candidates}:
            continue

        where = f" on table {scope!r}" if scope else ""
        suggestion = _did_you_mean(bare, sorted(all_valid))
        out.append(
            Diagnostic(
                code="UNKNOWN_COLUMN",
                severity=Severity.ERROR,
                message=f"Column {bare!r} is not in the schema{where}.",
                suggestion=suggestion,
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
    parsed: ParsedQuery, schema: Schema, resolvable_tables: list[str]
) -> list[Diagnostic]:
    if not parsed.has_join:
        return []
    # Need at least two recognised tables to talk about a join between them.
    if len(resolvable_tables) < 2:
        return []

    # Declared FKs among the recognised tables (direction-insensitive pairs).
    declared_pairs: set[frozenset[str]] = set()
    fk_columns: set[str] = set()
    for k in schema.keys:
        if k.from_table in resolvable_tables and k.target_table in resolvable_tables:
            declared_pairs.add(frozenset((k.from_table, k.target_table)))
            fk_columns.add(k.from_column.lower())
            fk_columns.add(k.target_column.lower())

    # Columns used specifically in the JOIN ... ON predicate (not the SELECT/WHERE), since that is
    # what makes the join legitimate. Fall back to all referenced columns if ON couldn't be parsed.
    on_columns = {c.lower() for c in parsed.join_on_columns}
    if not on_columns:
        on_columns = {bare.lower() for (_h, bare) in _distinct_column_refs(parsed)}

    # If the joined tables have a declared FK and the ON clause uses the FK column(s), it's a good join.
    if declared_pairs and (fk_columns & on_columns):
        return []

    if not declared_pairs:
        # The schema declares no FK linking these tables at all — the join may be ad hoc.
        joined = ", ".join(sorted(resolvable_tables))
        return [
            Diagnostic(
                code="MISSING_JOIN_KEY",
                severity=Severity.WARNING,
                message=(
                    f"JOIN between {joined} does not use a foreign key declared in TAP_SCHEMA.keys "
                    f"(the schema declares no key linking these tables)."
                ),
                suggestion="Verify the join condition; cross-archive joins often need an explicit "
                           "shared identifier (e.g. source_id).",
            )
        ]

    # There IS a declared FK but the query didn't reference its column(s).
    fk_hint = ", ".join(sorted(fk_columns)) or "the declared key column"
    return [
        Diagnostic(
            code="MISSING_JOIN_KEY",
            severity=Severity.WARNING,
            message=(
                "JOIN does not appear to use the declared foreign key for these tables."
            ),
            suggestion=f"Join on the declared key column(s): {fk_hint}.",
        )
    ]


# --- rule 3: no spatial constraint ------------------------------------------------------


def _rule_no_spatial_constraint(
    parsed: ParsedQuery, schema: Schema, resolvable_tables: list[str]
) -> list[Diagnostic]:
    if parsed.has_spatial_constraint:
        return []

    positional = [t for t in resolvable_tables if _is_positional_table(schema, t)]
    if not positional:
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
                "CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', <ra>, <dec>, <radius_deg>)) = 1"
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


# --- rule 4: no row limit ---------------------------------------------------------------


def _rule_no_row_limit(parsed: ParsedQuery, endpoint_key: str) -> list[Diagnostic]:
    if parsed.has_top_or_limit:
        return []
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


def _did_you_mean(name: str, candidates: list[str]) -> str | None:
    """Fuzzy 'did you mean?' from real schema names (case-insensitive)."""
    if not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=3, cutoff=0.6)
    if not matches:
        # try case-insensitive matching against a lowercased view
        lower_map = {c.lower(): c for c in candidates}
        lc = difflib.get_close_matches(name.lower(), list(lower_map), n=3, cutoff=0.6)
        matches = [lower_map[m] for m in lc]
    if not matches:
        return None
    if len(matches) == 1:
        return f"did you mean {matches[0]!r}?"
    quoted = ", ".join(repr(m) for m in matches)
    return f"did you mean one of: {quoted}?"
