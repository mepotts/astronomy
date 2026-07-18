"""M1 deterministic linter/parser/explainer tests.

Offline by construction: every test resolves against the committed Gaia fixture
(``adql_copilot.schema.load_fixture_schema('gaia')``), never the network or the on-disk cache, so
results are reproducible regardless of connectivity. Assertions target the stable diagnostic
``code`` values that the CLI / future API depend on.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from adql_copilot import explainer, linter, parser
from adql_copilot.schema import SCHEMA_MAX_AGE_DAYS, load_fixture_schema, snapshot_age_days
from adql_copilot.models import Schema, Severity


@pytest.fixture(scope="module")
def gaia() -> Schema:
    return load_fixture_schema("gaia")


def _codes(diags) -> set[str]:
    return {d.code for d in diags}


def _lint(adql: str, schema: Schema):
    return linter.lint(parser.parse(adql), schema, "gaia")


# --- fixture sanity ---------------------------------------------------------------------


def test_fixture_loads_with_real_gaia_metadata(gaia: Schema):
    assert gaia.source == "fixture"
    assert "gaiadr3.gaia_source" in gaia.tables
    ra = next(c for c in gaia.columns_for("gaiadr3.gaia_source") if c.column_name == "ra")
    assert ra.unit == "deg"
    assert "pos.eq.ra" in (ra.ucd or "")          # correct UCD, incl. ;meta.main
    # No fabricated foreign key: Gaia's live TAP_SCHEMA.keys declares only tap_schema-internal keys,
    # so the fixture declares none. source_id is nonetheless the real join column and co-exists in
    # both tables -- which is what the redesigned MISSING_JOIN_KEY rule relies on.
    assert gaia.keys == []
    for tbl in ("gaiadr3.gaia_source", "gaiadr3.astrophysical_parameters"):
        assert any(c.column_name == "source_id" for c in gaia.columns_for(tbl))


# --- parser -----------------------------------------------------------------------------


def test_parser_extracts_tables_columns_and_flags():
    p = parser.parse(
        "SELECT TOP 10 source_id, ra, dec FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1"
    )
    assert p.is_valid_syntax
    assert "gaiadr3.gaia_source" in p.tables
    assert "source_id" in p.columns and "ra" in p.columns
    assert p.has_spatial_constraint is True
    assert p.has_top_or_limit is True
    assert "CIRCLE" in p.spatial_functions


def test_parser_reports_invalid_syntax():
    p = parser.parse("SELCT ra FROM gaiadr3.gaia_source")
    assert p.is_valid_syntax is False
    assert p.parse_error                         # a message is present
    assert _codes(linter.lint(p, load_fixture_schema("gaia"), "gaia")) == {"INVALID_SYNTAX"}


def test_parser_detects_join_and_on_columns():
    p = parser.parse(
        "SELECT s.source_id, ap.teff_gspphot "
        "FROM gaiadr3.gaia_source AS s "
        "JOIN gaiadr3.astrophysical_parameters AS ap ON s.source_id = ap.source_id"
    )
    assert p.has_join is True
    assert "source_id" in p.join_on_columns
    assert "gaiadr3.astrophysical_parameters" in p.tables


# --- rule 1: unknown table / column -----------------------------------------------------


def test_unknown_table(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 ra FROM gaiadr3.gaia_sourcex "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "UNKNOWN_TABLE" in _codes(diags)
    d = next(d for d in diags if d.code == "UNKNOWN_TABLE")
    assert d.severity is Severity.ERROR
    assert d.suggestion and "gaiadr3.gaia_source" in d.suggestion   # did-you-mean


def test_unknown_column_with_did_you_mean(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 parallx FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "UNKNOWN_COLUMN" in _codes(diags)
    d = next(d for d in diags if d.code == "UNKNOWN_COLUMN")
    assert d.severity is Severity.ERROR
    assert d.suggestion and "parallax" in d.suggestion


def test_known_columns_produce_no_unknown_diagnostics(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 source_id, ra, dec, parallax, ruwe FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "UNKNOWN_COLUMN" not in _codes(diags)
    assert "UNKNOWN_TABLE" not in _codes(diags)


# --- rule 2: missing JOIN key (M1.1 redesign) -------------------------------------------
# The FK-only premise is empirically false at Gaia (TAP_SCHEMA.keys declares only tap_schema
# internals), so the rule now blesses a join when the ON uses a curated join key (source_id) OR a
# column co-existing in both tables with compatible datatype, and warns ONLY when the ON columns
# don't co-exist. The fixture declares NO foreign keys.


def test_canonical_source_id_join_is_clean(gaia: Schema):
    # The canonical Gaia value-added-table join. No declared FK exists, but source_id is a curated
    # join key AND co-exists in both tables -> must NOT warn.
    diags = _lint(
        "SELECT TOP 5 s.source_id, ap.teff_gspphot "
        "FROM gaiadr3.gaia_source AS s "
        "JOIN gaiadr3.astrophysical_parameters AS ap ON s.source_id = ap.source_id "
        "WHERE CONTAINS(POINT('ICRS', s.ra, s.dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "MISSING_JOIN_KEY" not in _codes(diags)


def test_join_on_shared_non_allowlisted_column_is_clean(gaia: Schema):
    # solution_id is NOT in the curated allowlist but exists in both tables (datatype long) -> the
    # co-existence path (b') keeps it clean.
    diags = _lint(
        "SELECT TOP 5 s.source_id "
        "FROM gaiadr3.gaia_source AS s "
        "JOIN gaiadr3.astrophysical_parameters AS ap ON s.solution_id = ap.solution_id "
        "WHERE CONTAINS(POINT('ICRS', s.ra, s.dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "MISSING_JOIN_KEY" not in _codes(diags)


def test_join_on_non_coexisting_columns_warns(gaia: Schema):
    # ra exists only in gaia_source; azero_gspphot only in astrophysical_parameters -> the ON does
    # not reference any shared/known join column, so warn.
    diags = _lint(
        "SELECT TOP 5 s.source_id "
        "FROM gaiadr3.gaia_source AS s "
        "JOIN gaiadr3.astrophysical_parameters AS ap ON s.ra = ap.azero_gspphot "
        "WHERE CONTAINS(POINT('ICRS', s.ra, s.dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "MISSING_JOIN_KEY" in _codes(diags)
    d = next(d for d in diags if d.code == "MISSING_JOIN_KEY")
    assert d.severity is Severity.WARNING
    assert d.suggestion and "source_id" in d.suggestion


def test_no_join_no_join_diagnostic(gaia: Schema):
    diags = _lint("SELECT TOP 5 source_id FROM gaiadr3.gaia_source", gaia)
    assert "MISSING_JOIN_KEY" not in _codes(diags)


# --- rule 3: no spatial constraint ------------------------------------------------------


def test_no_spatial_constraint_on_positional_table_warns(gaia: Schema):
    diags = _lint("SELECT TOP 5 source_id, ra, dec FROM gaiadr3.gaia_source WHERE ruwe < 1.4", gaia)
    assert "NO_SPATIAL_CONSTRAINT" in _codes(diags)
    assert next(d for d in diags if d.code == "NO_SPATIAL_CONSTRAINT").severity is Severity.WARNING


def test_contains_predicate_satisfies_spatial(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 source_id FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1",
        gaia,
    )
    assert "NO_SPATIAL_CONSTRAINT" not in _codes(diags)


def test_distance_predicate_satisfies_spatial(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 source_id FROM gaiadr3.gaia_source "
        "WHERE DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', 45, 0)) < 0.5",
        gaia,
    )
    assert "NO_SPATIAL_CONSTRAINT" not in _codes(diags)


# --- rule 4: no row limit ---------------------------------------------------------------


def test_no_row_limit_advisory_mentions_gaia_cap(gaia: Schema):
    diags = _lint(
        "SELECT source_id FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "NO_ROW_LIMIT" in _codes(diags)
    d = next(d for d in diags if d.code == "NO_ROW_LIMIT")
    assert d.severity is Severity.INFO
    assert "2000" in d.message


def test_top_suppresses_row_limit_advisory(gaia: Schema):
    diags = _lint(
        "SELECT TOP 100 source_id FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "NO_ROW_LIMIT" not in _codes(diags)


# --- composite: a fully clean query has no diagnostics ----------------------------------


def test_clean_cone_search_has_no_diagnostics(gaia: Schema):
    diags = _lint(
        "SELECT TOP 10 source_id, ra, dec, parallax, ruwe FROM gaiadr3.gaia_source "
        "WHERE parallax_over_error > 10 AND ruwe < 1.4 "
        "AND CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1",
        gaia,
    )
    assert diags == []


def test_report_ok_flag_tracks_errors(gaia: Schema):
    bad = parser.parse("SELECT nope FROM gaiadr3.gaia_source WHERE ruwe < 1.4")
    diags = linter.lint(bad, gaia, "gaia")
    assert any(d.severity is Severity.ERROR for d in diags)  # UNKNOWN_COLUMN is an error


# --- explainer --------------------------------------------------------------------------


def test_explainer_describes_columns_units_and_region(gaia: Schema):
    text = explainer.explain(
        parser.parse(
            "SELECT TOP 10 source_id, ra, dec, parallax FROM gaiadr3.gaia_source "
            "WHERE ruwe < 1.4 "
            "AND CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1"
        ),
        gaia,
    )
    assert "gaiadr3.gaia_source" in text
    assert "deg" in text                        # unit surfaced from schema
    assert "cone-search" in text or "circular" in text
    assert "10 rows" in text                    # TOP value surfaced


def test_explainer_flags_full_scan_for_unconstrained_query(gaia: Schema):
    text = explainer.explain(
        parser.parse("SELECT source_id, ra, dec FROM gaiadr3.gaia_source WHERE ruwe < 1.4"),
        gaia,
    )
    assert "no spatial constraint" in text.lower()


def test_explainer_handles_invalid_syntax_gracefully(gaia: Schema):
    text = explainer.explain(parser.parse("SELCT ra FROM gaiadr3.gaia_source"), gaia)
    assert "could not be parsed" in text.lower()


# --- schema loader contract -------------------------------------------------------------


def test_unknown_endpoint_raises():
    from adql_copilot import schema

    with pytest.raises(KeyError):
        schema.load_schema("not-an-endpoint")


# ========================================================================================
# M1.1 correctness pass
# ========================================================================================


# --- fix 1: case-insensitive table matching ---------------------------------------------


def test_uppercase_table_resolves_and_enables_checks(gaia: Schema):
    # ADQL regular identifiers are case-insensitive: an uppercased table must NOT be UNKNOWN_TABLE,
    # and column + spatial checks must still run against it (proving it resolved, not silently skipped).
    diags = _lint("SELECT ra, dec, parallax FROM GAIADR3.GAIA_SOURCE WHERE ruwe < 1.4", gaia)
    codes = _codes(diags)
    assert "UNKNOWN_TABLE" not in codes
    assert "UNKNOWN_COLUMN" not in codes           # ra/dec/parallax resolved against canonical table
    assert "NO_SPATIAL_CONSTRAINT" in codes        # spatial check ran on the resolved positional table


def test_uppercase_unknown_column_still_flagged(gaia: Schema):
    diags = _lint("SELECT nope FROM GAIADR3.GAIA_SOURCE WHERE ruwe < 1.4", gaia)
    assert "UNKNOWN_COLUMN" in _codes(diags)


# --- fix 2: TAP_UPLOAD exemption --------------------------------------------------------


def test_tap_upload_join_is_exempt_from_schema_checks(gaia: Schema):
    # The canonical Gaia upload-crossmatch. TAP_UPLOAD.mylist and its columns are never in
    # TAP_SCHEMA, so they must not raise UNKNOWN_TABLE / UNKNOWN_COLUMN.
    diags = _lint(
        "SELECT TOP 10 s.source_id, m.myid "
        "FROM gaiadr3.gaia_source AS s "
        "JOIN TAP_UPLOAD.mylist AS m ON s.source_id = m.source_id",
        gaia,
    )
    codes = _codes(diags)
    assert "UNKNOWN_TABLE" not in codes
    assert "UNKNOWN_COLUMN" not in codes


def test_parser_extracts_upload_aliases():
    p = parser.parse(
        "SELECT s.source_id, m.myid FROM gaiadr3.gaia_source AS s "
        "JOIN TAP_UPLOAD.mylist AS m ON s.source_id = m.source_id"
    )
    assert "m" in p.upload_aliases


# --- fix 4: honest identifier-extraction failure ----------------------------------------


def test_region_first_contains_reports_identifiers_unchecked(gaia: Schema):
    # queryparser's stage-2 extraction fails on a region-first CONTAINS; we must say so honestly,
    # never report the query clean with zero identifier checks.
    adql = (
        "SELECT source_id FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(CIRCLE('ICRS', 45.0, 0.0, 0.5), POINT('ICRS', ra, dec)) = 1"
    )
    p = parser.parse(adql)
    assert p.is_valid_syntax is True
    assert p.extraction_error                       # extraction failed, honestly recorded
    assert p.tables == []
    diags = linter.lint(p, gaia, "gaia")
    d = next(d for d in diags if d.code == "IDENTIFIERS_UNCHECKED")
    assert d.severity is Severity.WARNING


def test_normal_query_has_no_extraction_error(gaia: Schema):
    p = parser.parse(
        "SELECT TOP 5 source_id FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1"
    )
    assert p.extraction_error is None
    assert "IDENTIFIERS_UNCHECKED" not in _codes(linter.lint(p, gaia, "gaia"))


# --- fix 5: clause-aware spatial detection ----------------------------------------------


def test_geometry_in_select_only_does_not_satisfy_spatial(gaia: Schema):
    # DISTANCE(...) computed in the SELECT list, no WHERE -> a full-catalog scan, must warn.
    p = parser.parse(
        "SELECT DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', 45, 0)) AS d "
        "FROM gaiadr3.gaia_source"
    )
    assert p.has_spatial_constraint is False
    assert "NO_SPATIAL_CONSTRAINT" in _codes(linter.lint(p, gaia, "gaia"))


def test_narrow_ra_dec_box_satisfies_spatial(gaia: Schema):
    p = parser.parse(
        "SELECT TOP 10 source_id FROM gaiadr3.gaia_source "
        "WHERE ra BETWEEN 10 AND 11 AND dec BETWEEN 41 AND 42"
    )
    assert "ra" in p.range_constrained_columns and "dec" in p.range_constrained_columns
    assert "NO_SPATIAL_CONSTRAINT" not in _codes(linter.lint(p, gaia, "gaia"))


def test_range_on_non_positional_columns_does_not_satisfy_spatial(gaia: Schema):
    # Bounding ruwe (not an RA/Dec axis) is not a positional box -> still a full scan.
    diags = _lint(
        "SELECT TOP 10 source_id FROM gaiadr3.gaia_source WHERE ruwe BETWEEN 0 AND 1.4", gaia
    )
    assert "NO_SPATIAL_CONSTRAINT" in _codes(diags)


# --- fix 6: aggregate awareness ---------------------------------------------------------


def test_aggregate_only_query_suppresses_row_limit(gaia: Schema):
    p = parser.parse("SELECT COUNT(*) FROM gaiadr3.gaia_source")
    assert p.is_aggregate_only is True
    assert "NO_ROW_LIMIT" not in _codes(linter.lint(p, gaia, "gaia"))


def test_non_aggregate_still_gets_row_limit(gaia: Schema):
    p = parser.parse("SELECT source_id, COUNT(*) FROM gaiadr3.gaia_source GROUP BY source_id")
    assert p.is_aggregate_only is False
    assert "NO_ROW_LIMIT" in _codes(linter.lint(p, gaia, "gaia"))


# --- fix 7: structured fix payloads -----------------------------------------------------


def test_unknown_column_carries_structured_fix(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 parallx FROM gaiadr3.gaia_source "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    d = next(d for d in diags if d.code == "UNKNOWN_COLUMN")
    assert d.fix is not None
    assert d.fix.kind == "replace_column"
    assert d.fix.target == "parallx"
    assert d.fix.replacement == "parallax"


def test_unknown_table_carries_structured_fix(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 ra FROM gaiadr3.gaia_sourcex "
        "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    d = next(d for d in diags if d.code == "UNKNOWN_TABLE")
    assert d.fix is not None and d.fix.kind == "replace_table"
    assert d.fix.replacement == "gaiadr3.gaia_source"


def test_fix_serializes_in_json(gaia: Schema):
    from adql_copilot.models import LintReport

    diags = _lint("SELECT parallx FROM gaiadr3.gaia_source WHERE ruwe < 1.4", gaia)
    report = LintReport(endpoint_key="gaia", parsed=parser.parse("SELECT parallx FROM x"), diagnostics=diags)
    payload = report.model_dump_json()
    assert '"fix"' in payload and '"replace_column"' in payload


# --- fix 8: schema cache age ------------------------------------------------------------


def test_stale_schema_warns(gaia: Schema):
    stale = gaia.model_copy(
        update={"fetched_at": (datetime.now(timezone.utc) - timedelta(days=SCHEMA_MAX_AGE_DAYS + 30)).isoformat()}
    )
    diags = linter.lint(parser.parse("SELECT TOP 5 source_id FROM gaiadr3.gaia_source"), stale, "gaia")
    d = next(d for d in diags if d.code == "SCHEMA_STALE")
    assert d.severity is Severity.WARNING
    assert snapshot_age_days(stale) > SCHEMA_MAX_AGE_DAYS


def test_fresh_schema_does_not_warn(gaia: Schema):
    fresh = gaia.model_copy(update={"fetched_at": datetime.now(timezone.utc).isoformat()})
    diags = linter.lint(parser.parse("SELECT TOP 5 source_id FROM gaiadr3.gaia_source"), fresh, "gaia")
    assert "SCHEMA_STALE" not in _codes(diags)


def test_fixture_snapshot_age_is_unknown(gaia: Schema):
    # The bundled fixture carries no fetched_at, so its age is unknown (never spuriously "stale").
    assert gaia.fetched_at is None
    assert snapshot_age_days(gaia) is None


# --- fix 9: TOP-not-LIMIT hint ----------------------------------------------------------


def test_limit_parse_failure_hints_top(gaia: Schema):
    diags = _lint("SELECT ra, dec FROM gaiadr3.gaia_source LIMIT 10", gaia)
    d = next(d for d in diags if d.code == "INVALID_SYNTAX")
    assert d.suggestion and "TOP" in d.suggestion
    assert d.fix is not None and d.fix.kind == "rewrite_limit_as_top"
    assert d.fix.replacement == "TOP 10"


# --- fix 10: coordsys-less POINT guidance -----------------------------------------------


def test_no_spatial_suggestion_uses_coordsys_less_form(gaia: Schema):
    diags = _lint("SELECT source_id, ra, dec FROM gaiadr3.gaia_source WHERE ruwe < 1.4", gaia)
    d = next(d for d in diags if d.code == "NO_SPATIAL_CONSTRAINT")
    assert "POINT(ra, dec)" in d.suggestion          # ADQL 2.1 coordsys-less form
    assert "also accepted" in d.suggestion            # notes the legacy 'ICRS' form still works
