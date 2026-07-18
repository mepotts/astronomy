"""ADQL parsing — validate syntax and extract table/column references and structural facts.

Primary backend: ``queryparser-python3`` (``queryparser.adql.ADQLQueryTranslator``). Its ANTLR4
ADQL grammar validates syntax (it raises on invalid ADQL) and, via the companion
``PostgreSQLQueryProcessor``, surfaces fully-resolved ``(schema, table, column)`` references —
which is exactly the "is this valid ADQL + what names does it reference" step the linter needs.
We use it purely for parsing/extraction and **ignore** its PostgreSQL/pgSphere translation output.

A small ``lark`` grammar is kept as a documented fallback (DATA-SOURCES.md S4) and is only used if
``queryparser`` cannot be imported at all.

Two facts are deliberately read off the **raw ADQL string**, not the parse result:

* **spatial constraint** — translation rewrites ``CONTAINS``/``CIRCLE``/``POINT`` into pgSphere
  operators (``scircle``/``spoint``/``@``), so the original ADQL geometry keywords would be lost.
* **TOP / row limit** — ``TOP n`` is translated to SQL ``LIMIT n``; detecting it on the raw text
  keeps the ``ParsedQuery`` faithful to what the user actually wrote.
"""

from __future__ import annotations

import re

from .models import ParsedQuery

# ADQL spherical-geometry / region functions whose presence constitutes a spatial constraint.
# (DATA-SOURCES.md S3 — ADQL 2.1 geometry.)
SPATIAL_FUNCTIONS = ("CONTAINS", "INTERSECTS", "DISTANCE", "POINT", "CIRCLE", "POLYGON", "BOX")

# Functions that, on their own, only *describe* a region rather than *constrain* the result set.
# A query that merely SELECTs a POINT/CIRCLE without a CONTAINS/INTERSECTS/DISTANCE predicate is
# still effectively a full scan, so the "has a real spatial constraint" signal is the predicate
# functions below; the constructors are tracked separately for the explainer.
SPATIAL_PREDICATES = ("CONTAINS", "INTERSECTS", "DISTANCE")

_WORD = r"\b{}\b"


def _find_spatial_functions(adql_upper: str) -> list[str]:
    """Geometry function names present in the raw ADQL (uppercased), in declared order."""
    found: list[str] = []
    for fn in SPATIAL_FUNCTIONS:
        if re.search(_WORD.format(fn) + r"\s*\(", adql_upper):
            found.append(fn)
    return found


def _has_top_or_limit(adql_upper: str) -> bool:
    """True if the raw ADQL uses ``TOP n`` (ADQL) or ``LIMIT n`` (some servers accept it)."""
    return bool(re.search(r"\bTOP\s+\d+", adql_upper) or re.search(r"\bLIMIT\s+\d+", adql_upper))


def _has_join(adql_upper: str) -> bool:
    return bool(re.search(r"\bJOIN\b", adql_upper))


# A JOIN ... ON predicate runs until the next clause keyword (WHERE/GROUP/ORDER/HAVING), the next
# JOIN, or end-of-query. We pull the bare column names out of each ON predicate so the linter can
# check whether the join actually uses a declared foreign-key column.
_ON_CLAUSE = re.compile(
    r"\bON\b(.*?)(?=\bWHERE\b|\bGROUP\b|\bORDER\b|\bHAVING\b|\bJOIN\b|$)",
    re.IGNORECASE | re.DOTALL,
)
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
# SQL/ADQL words that can appear inside an ON predicate but are not column names.
_ON_NOISE = {"and", "or", "not", "between", "in", "is", "null", "like"}


def _join_on_columns(adql: str) -> list[str]:
    """Bare column names referenced in JOIN ... ON predicates (lowercased, de-duped)."""
    cols: list[str] = []
    for m in _ON_CLAUSE.finditer(adql):
        for tok in _IDENT.findall(m.group(1)):
            bare = tok.split(".")[-1].lower()
            if bare and bare not in _ON_NOISE and not bare.isdigit() and bare not in cols:
                cols.append(bare)
    return cols


def parse(adql: str) -> ParsedQuery:
    """Parse an ADQL string into a :class:`ParsedQuery`.

    On any syntax/parse error, returns ``ParsedQuery(is_valid_syntax=False, parse_error=...)``
    so the linter can emit a single ``INVALID_SYNTAX`` diagnostic rather than crashing.
    """
    adql_upper = adql.upper()
    spatial_fns = _find_spatial_functions(adql_upper)
    has_spatial = any(p in spatial_fns for p in SPATIAL_PREDICATES)
    has_top = _has_top_or_limit(adql_upper)
    has_join = _has_join(adql_upper)
    join_on_cols = _join_on_columns(adql) if has_join else []

    try:
        tables, columns = _extract_with_queryparser(adql)
    except _ParserUnavailable:
        # queryparser couldn't be imported at all -> documented lark fallback.
        try:
            tables, columns = _extract_with_lark(adql)
        except Exception as exc:  # noqa: BLE001 - any fallback failure is a parse failure
            return ParsedQuery(raw=adql, is_valid_syntax=False, parse_error=str(exc))
    except _ParseFailed as exc:
        return ParsedQuery(raw=adql, is_valid_syntax=False, parse_error=str(exc))

    return ParsedQuery(
        raw=adql,
        tables=tables,
        columns=columns,
        has_spatial_constraint=has_spatial,
        has_top_or_limit=has_top,
        has_join=has_join,
        join_on_columns=join_on_cols,
        spatial_functions=spatial_fns,
        is_valid_syntax=True,
        parse_error=None,
    )


# --- queryparser (primary) --------------------------------------------------------------


class _ParserUnavailable(Exception):
    """queryparser itself could not be imported (fall back to lark)."""


class _ParseFailed(Exception):
    """queryparser imported fine but the ADQL is syntactically invalid."""


def _extract_with_queryparser(adql: str) -> tuple[list[str], list[str]]:
    """Validate + extract refs via queryparser.

    Returns ``(tables, columns)`` where tables are ``"schema.table"`` and columns are emitted in
    several qualified forms (``"schema.table.col"``, ``"table.col"``, bare ``"col"``) so the linter
    can match whatever form the user / schema uses. Raises :class:`_ParserUnavailable` if the
    package is missing, :class:`_ParseFailed` on invalid ADQL.
    """
    try:
        from queryparser.adql import ADQLQueryTranslator
        from queryparser.postgresql import PostgreSQLQueryProcessor
    except Exception as exc:  # noqa: BLE001 - import problem -> try the fallback parser
        raise _ParserUnavailable(str(exc)) from exc

    # Stage 1: ADQL syntax validation. to_postgresql() forces a full parse and raises on bad ADQL.
    try:
        translator = ADQLQueryTranslator(adql)
        pg = translator.to_postgresql()
    except Exception as exc:  # noqa: BLE001 - queryparser raises QuerySyntaxError & friends
        raise _ParseFailed(_clean_parser_error(exc, adql)) from exc

    # Stage 2: identifier extraction off the translated (still fully-qualified) SQL.
    tables: list[str] = []
    columns: list[str] = []
    try:
        proc = PostgreSQLQueryProcessor(pg)
        proc.process_query()
        tables = _format_tables(getattr(proc, "tables", []) or [])
        columns = _format_columns(getattr(proc, "columns", []) or [])
    except Exception:  # noqa: BLE001 - extraction is best-effort; syntax already validated above
        # The ADQL is valid (stage 1 passed); we just couldn't pull every identifier. The linter
        # still runs its non-identifier rules (spatial/TOP) and skips unknown-name checks gracefully.
        pass

    return tables, columns


def _format_tables(raw_tables: list) -> list[str]:
    out: list[str] = []
    for t in raw_tables:
        name = _join_parts(t)
        if name and name not in out:
            out.append(name)
    return out


def _format_columns(raw_columns: list) -> list[str]:
    """Emit each column in multiple qualified forms for flexible matching.

    queryparser yields ``(schema, table, column)`` tuples. We add ``schema.table.column``,
    ``table.column`` and bare ``column`` so the linter can resolve against any of them.
    ``*`` (from ``SELECT *``) is dropped — it is not a concrete column to validate.
    """
    out: list[str] = []

    def add(name: str) -> None:
        if name and name not in out:
            out.append(name)

    for c in raw_columns:
        parts = [p for p in (c if isinstance(c, (list, tuple)) else [c]) if p]
        if not parts:
            continue
        col = parts[-1]
        if col == "*":
            continue
        add(".".join(parts))          # schema.table.column
        if len(parts) >= 2:
            add(".".join(parts[-2:]))  # table.column
        add(col)                       # bare column
    return out


def _join_parts(item) -> str:
    if isinstance(item, (list, tuple)):
        return ".".join(p for p in item if p)
    return str(item)


def _clean_parser_error(exc: Exception, adql: str) -> str:
    """Turn queryparser's terse error payload into a human-ish message.

    QuerySyntaxError carries a list of ``(line, col, offending_token)`` tuples; surface the first
    one with a short pointer so the CLI message is useful.
    """
    msg = str(exc)
    try:
        payload = exc.args[0]
        if isinstance(payload, (list, tuple)) and payload:
            first = payload[0]
            if isinstance(first, (list, tuple)) and len(first) >= 3:
                line, col, tok = first[0], first[1], first[2]
                return f"syntax error near {tok!r} (line {line}, col {col})"
    except Exception:  # noqa: BLE001
        pass
    return msg or f"{type(exc).__name__}"


# --- lark fallback (only if queryparser cannot be imported) ------------------------------

# Intentionally minimal: enough to pull FROM/JOIN tables and SELECT columns so the linter's
# identifier rules keep working when queryparser is unavailable. queryparser is the primary and
# this branch is not exercised in normal installs (queryparser is a hard dependency).
_LARK_GRAMMAR = r"""
    start: "SELECT"i ["TOP"i INT] select_list "FROM"i table_ref (join)* where?
    select_list: "*" | col_item ("," col_item)*
    col_item: qualified_name
    table_ref: qualified_name ["AS"i NAME]
    join: "JOIN"i qualified_name ["AS"i NAME] "ON"i /.+?(?=WHERE|JOIN|$)/i
    where: "WHERE"i /.+/s
    qualified_name: NAME ("." NAME)*
    NAME: /[A-Za-z_][A-Za-z0-9_]*/
    %import common.INT
    %import common.WS
    %ignore WS
"""


def _extract_with_lark(adql: str) -> tuple[list[str], list[str]]:
    import lark  # raises ImportError if the optional fallback isn't installed either

    parser = lark.Lark(_LARK_GRAMMAR, parser="earley")
    tree = parser.parse(adql)  # raises lark.exceptions.* on invalid input

    tables: list[str] = []
    columns: list[str] = []
    for node in tree.iter_subtrees():
        if node.data == "table_ref":
            name = _lark_qualified(node)
            if name and name not in tables:
                tables.append(name)
        elif node.data == "join":
            name = _lark_qualified(node)
            if name and name not in tables:
                tables.append(name)
        elif node.data == "col_item":
            name = _lark_qualified(node)
            if name:
                if name not in columns:
                    columns.append(name)
                bare = name.split(".")[-1]
                if bare not in columns:
                    columns.append(bare)
    return tables, columns


def _lark_qualified(node) -> str:
    import lark

    for sub in node.iter_subtrees():
        if sub.data == "qualified_name":
            return ".".join(
                tok.value for tok in sub.children if isinstance(tok, lark.Token)
            )
    return ""
