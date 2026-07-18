"""Typed data models shared across the pipeline (pydantic v2).

These serialize to JSON for free, which is what a future web API / notebook helper will emit.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    ERROR = "error"      # query will fail or is certainly wrong (e.g. unknown column)
    WARNING = "warning"  # query will run but is likely a footgun (e.g. no spatial constraint)
    INFO = "info"        # advisory (e.g. add TOP n)


class Fix(BaseModel):
    """A machine-actionable repair attached to a :class:`Diagnostic`.

    This is the seam a CI check or an LLM repair loop consumes: unlike the human-readable
    ``suggestion`` prose, ``fix`` is structured so a tool can apply it programmatically. Additive
    and optional — a Diagnostic without a ``fix`` is still complete.
    """

    kind: str                       # e.g. "replace_table", "replace_column", "rewrite_limit_as_top"
    replacement: str                # the suggested replacement identifier / text
    target: str | None = None       # the original text this replaces, when known
    span: tuple[int, int] | None = None  # (start, end) char offsets into ParsedQuery.raw, when known


class Diagnostic(BaseModel):
    """One linter finding. `code` is a stable identifier for tests/eval."""

    code: str               # e.g. "UNKNOWN_COLUMN", "NO_SPATIAL_CONSTRAINT", "MISSING_JOIN_KEY"
    severity: Severity
    message: str
    suggestion: str | None = None   # e.g. fuzzy "did you mean 'phot_g_mean_mag'?"
    fix: Fix | None = None          # optional machine-actionable repair (additive, backward-compat)


class ColumnMeta(BaseModel):
    """A column as described by the live TAP_SCHEMA.columns."""

    table_name: str
    column_name: str
    datatype: str | None = None
    unit: str | None = None
    ucd: str | None = None
    description: str | None = None


class ForeignKey(BaseModel):
    """A declared foreign key, from TAP_SCHEMA.keys + TAP_SCHEMA.key_columns.

    This is how we know the *legitimate* JOIN keys between two tables, which powers
    the MISSING_JOIN_KEY diagnostic.
    """

    from_table: str
    target_table: str
    from_column: str
    target_column: str


class Schema(BaseModel):
    """A cached snapshot of one endpoint's TAP_SCHEMA, as the linter consumes it.

    Serializes to/from schemas/<key>.json (the live cache) and the bundled offline fixture.
    `source` records where this snapshot came from: "live" (fetched), "cache" (on-disk dump),
    or "fixture" (the committed offline fallback) — surfaced so the CLI can be honest about it.
    """

    endpoint_key: str
    source: str = "fixture"          # "live" | "cache" | "fixture"
    fetched_at: str | None = None    # ISO-8601 UTC timestamp of the live fetch (None for fixtures)
    columns: list[ColumnMeta] = []
    keys: list[ForeignKey] = []

    @property
    def tables(self) -> list[str]:
        """Distinct table names present in the schema, in first-seen order."""
        seen: dict[str, None] = {}
        for c in self.columns:
            seen.setdefault(c.table_name, None)
        return list(seen)

    def columns_for(self, table_name: str) -> list[ColumnMeta]:
        return [c for c in self.columns if c.table_name == table_name]


class ParsedQuery(BaseModel):
    """What the parser extracts from an ADQL string (filled in for real at M1)."""

    raw: str
    tables: list[str] = []          # table references found ("schema.table")
    columns: list[str] = []         # column references (multiple qualified forms per column)
    has_spatial_constraint: bool = False   # CONTAINS / INTERSECTS / DISTANCE predicate in WHERE?
    has_top_or_limit: bool = False
    has_join: bool = False          # JOIN clause present?
    join_on_columns: list[str] = [] # bare column names appearing in JOIN ... ON predicates
    spatial_functions: list[str] = []      # geometry funcs seen in the WHERE clause (for the explainer)
    range_constrained_columns: list[str] = []  # bare cols bounded by BETWEEN/comparison in WHERE
    upload_aliases: list[str] = []  # aliases bound to TAP_UPLOAD.* tables (exempt from schema checks)
    is_aggregate_only: bool = False  # SELECT list is only aggregates + no GROUP BY -> one row
    is_valid_syntax: bool = True
    parse_error: str | None = None
    extraction_error: str | None = None  # syntax OK but identifier extraction failed (unchecked!)


class LintReport(BaseModel):
    """Full result returned to the CLI / API."""

    endpoint_key: str
    parsed: ParsedQuery
    diagnostics: list[Diagnostic] = []
    explanation: str = ""

    @property
    def ok(self) -> bool:
        return not any(d.severity is Severity.ERROR for d in self.diagnostics)
