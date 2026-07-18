"""M1 deterministic linter/parser/explainer tests.

Offline by construction: every test resolves against the committed Gaia fixture
(``adql_copilot.schema.load_fixture_schema('gaia')``), never the network or the on-disk cache, so
results are reproducible regardless of connectivity. Assertions target the stable diagnostic
``code`` values that the CLI / future API depend on.
"""

from __future__ import annotations

import pytest

from adql_copilot import explainer, linter, parser
from adql_copilot.schema import load_fixture_schema
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
    assert any(k.from_column == "source_id" for k in gaia.keys)  # declared FK present


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


# --- rule 2: missing JOIN key -----------------------------------------------------------


def test_join_on_declared_fk_is_clean(gaia: Schema):
    diags = _lint(
        "SELECT TOP 5 s.source_id, ap.teff_gspphot "
        "FROM gaiadr3.gaia_source AS s "
        "JOIN gaiadr3.astrophysical_parameters AS ap ON s.source_id = ap.source_id "
        "WHERE CONTAINS(POINT('ICRS', s.ra, s.dec), CIRCLE('ICRS', 1, 2, 0.1)) = 1",
        gaia,
    )
    assert "MISSING_JOIN_KEY" not in _codes(diags)


def test_join_not_on_declared_fk_warns(gaia: Schema):
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
