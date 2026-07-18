"""Plain-English explanation of an ADQL query (deterministic, no LLM).

Builds a short human-readable summary from the parse result enriched with live schema metadata:
the table(s) queried, the selected columns with their units (and a hint from the UCD/description),
any spatial region, the WHERE filters, and the row limit. Everything stated is grounded in the
schema or the literal query text, so the explanation never asserts anything unverified.
"""

from __future__ import annotations

import re

from .models import ColumnMeta, ParsedQuery, Schema


def explain(parsed: ParsedQuery, schema: Schema) -> str:
    """Return a multi-line plain-English summary of the query."""
    if not parsed.is_valid_syntax:
        return f"This query could not be parsed as valid ADQL ({parsed.parse_error})."

    lines: list[str] = []
    lines.append(_summary_sentence(parsed, schema))

    col_lines = _column_lines(parsed, schema)
    if col_lines:
        lines.append("Columns:")
        lines.extend(f"  - {c}" for c in col_lines)

    spatial = _spatial_sentence(parsed)
    if spatial:
        lines.append(spatial)

    filt = _filters_sentence(parsed)
    if filt:
        lines.append(filt)

    limit = _limit_sentence(parsed)
    if limit:
        lines.append(limit)

    return "\n".join(lines)


def _summary_sentence(parsed: ParsedQuery, schema: Schema) -> str:
    tables = parsed.tables or ["(unknown table)"]
    table_phrase = _and_join(tables)
    verb = "Joins and selects from" if parsed.has_join and len(tables) > 1 else "Selects from"
    n_cols = len({c.split(".")[-1] for c in parsed.columns if c.split(".")[-1] != "*"})
    if any(c.endswith("*") or c == "*" for c in parsed.columns) or not parsed.columns:
        col_phrase = "all columns"
    else:
        col_phrase = f"{n_cols} column{'s' if n_cols != 1 else ''}"
    return f"{verb} {table_phrase}, returning {col_phrase}."


def _column_lines(parsed: ParsedQuery, schema: Schema) -> list[str]:
    """Describe each selected column using its unit/UCD/description from the schema, if known."""
    out: list[str] = []
    seen: set[str] = set()
    for ref in parsed.columns:
        bare = ref.split(".")[-1]
        if bare == "*" or bare in seen:
            continue
        # only describe columns that are clearly selected/used; skip if we can't find metadata and
        # the name is already covered by a more-qualified form
        meta = _lookup(schema, parsed.tables, bare)
        if meta is None:
            # still mention the bare column once, without metadata
            seen.add(bare)
            out.append(bare)
            continue
        seen.add(bare)
        out.append(_describe_column(meta))
    # de-dupe while preserving order and cap to keep the explanation readable
    deduped: list[str] = []
    for line in out:
        if line not in deduped:
            deduped.append(line)
    return deduped[:12]


def _describe_column(meta: ColumnMeta) -> str:
    bits = [meta.column_name]
    extras: list[str] = []
    if meta.unit:
        extras.append(f"in {meta.unit}")
    if meta.description:
        extras.append(meta.description.rstrip("."))
    elif meta.ucd:
        extras.append(f"UCD {meta.ucd}")
    if extras:
        return f"{bits[0]} ({'; '.join(extras)})"
    return bits[0]


def _lookup(schema: Schema, tables: list[str], bare: str) -> ColumnMeta | None:
    bare_lower = bare.lower()
    for t in tables:
        for c in schema.columns_for(t):
            if c.column_name.lower() == bare_lower:
                return c
    # fall back to a global search across the schema (handles unqualified refs to other tables)
    for c in schema.columns:
        if c.column_name.lower() == bare_lower:
            return c
    return None


def _spatial_sentence(parsed: ParsedQuery) -> str | None:
    if not parsed.has_spatial_constraint:
        if any(t for t in parsed.tables):
            return "It has no spatial constraint, so it scans the full table(s)."
        return None
    fns = parsed.spatial_functions
    region = None
    if "CIRCLE" in fns:
        region = "a circular (cone-search) region"
    elif "POLYGON" in fns:
        region = "a polygonal region"
    elif "BOX" in fns:
        region = "a rectangular region"
    pred = "DISTANCE" if "DISTANCE" in fns else ("INTERSECTS" if "INTERSECTS" in fns else "CONTAINS")
    if region:
        return f"It is constrained to {region} (via {pred})."
    return f"It applies a spatial constraint (via {pred})."


def _filters_sentence(parsed: ParsedQuery) -> str | None:
    """Surface non-spatial WHERE predicates (e.g. ruwe < 1.4) from the raw ADQL, briefly."""
    m = re.search(r"\bWHERE\b(.*?)(?:\bGROUP\b|\bORDER\b|$)", parsed.raw, re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    where = m.group(1)
    # drop the spatial predicates so we report only the scalar filters
    where = re.sub(r"\bCONTAINS\b\s*\(.*?\)\s*=\s*1", "", where, flags=re.IGNORECASE | re.DOTALL)
    where = re.sub(r"\bINTERSECTS\b\s*\(.*?\)\s*=\s*1", "", where, flags=re.IGNORECASE | re.DOTALL)
    # pull simple "col <op> value" comparisons
    comps = re.findall(
        r"([A-Za-z_][A-Za-z0-9_.]*)\s*(<=|>=|<|>|=|!=)\s*([-+]?\d[\d.eE+-]*)", where
    )
    # filter out leftovers from geometry args (numbers compared to coords inside funcs are gone now)
    parts = [f"{c.split('.')[-1]} {op} {v}" for (c, op, v) in comps]
    if not parts:
        return None
    return "Filters: " + ", ".join(dict.fromkeys(parts)) + "."


def _limit_sentence(parsed: ParsedQuery) -> str | None:
    m = re.search(r"\bTOP\s+(\d+)", parsed.raw, re.IGNORECASE) or re.search(
        r"\bLIMIT\s+(\d+)", parsed.raw, re.IGNORECASE
    )
    if m:
        return f"Returns at most {m.group(1)} rows."
    return "No row limit is set."


def _and_join(items: list[str]) -> str:
    items = list(dict.fromkeys(items))
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"
