"""Parsers for the four services, pinned against replies the services actually sent.

Every fixture in ``tests/data/vet`` is a verbatim body captured from a live call during M2,
not something hand-written to make a parser pass. The distinction matters: the MPChecker
table is fixed-width ASCII with an optional magnitude column, SBIDENT's numbers arrive as
strings like ``"1.E4"``, and SkyBoT's keys carry units inside the key name. All three are
formats that drift, and a fixture is the only thing that will notice when they do.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from itf_linker.vet import mpchecker, sbdb, sbident, skybot
from itf_linker.vet.types import OrbitElements

DATA = Path(__file__).parent / "data" / "vet"


# --- SkyBoT -----------------------------------------------------------------------
def test_skybot_parses_the_73p_control_reply():
    rows, err = skybot.parse_conesearch((DATA / "skybot_73p.json").read_text(encoding="utf-8"))
    assert err is None
    assert len(rows) == 1
    matches = skybot.rows_to_matches(rows, obs_index=0, mjd=53833.95108)
    (m,) = matches
    assert m.raw_name == "73P-C"
    assert m.orbit_class == "Comet"
    assert m.sep_arcsec == pytest.approx(32.842)
    assert m.ephem_err_arcsec == pytest.approx(0.7)
    assert m.service == "skybot"


def test_skybot_empty_and_malformed_bodies():
    assert skybot.parse_conesearch("") == ([], None)
    assert skybot.parse_conesearch("[]") == ([], None)
    rows, err = skybot.parse_conesearch("<html>gateway timeout</html>")
    assert rows == [] and err and "unparseable" in err
    rows, err = skybot.parse_conesearch('{"error": "bad epoch"}')
    assert rows == [] and err and "bad epoch" in err


def test_skybot_coverage_window_is_enforced():
    assert skybot.covers(2460000.0)
    assert not skybot.covers(2400000.0)   # 1858, before the 1889 floor
    assert not skybot.covers(2500000.0)   # 2132, past the 2060 ceiling


# --- SBIDENT ----------------------------------------------------------------------
def test_sbident_parses_a_two_pass_reply_and_recomputes_separations():
    payload = json.loads((DATA / "sbident_two_pass.json").read_text(encoding="utf-8"))
    matches, err, n_first = sbident.parse_identify(
        payload, ra_deg=312.66276667, dec_deg=-22.08713056, obs_index=0, mjd_utc=60874.093279
    )
    assert err is None and n_first == 5455
    assert [m.raw_name for m in matches] == [
        "130536 (2000 QV208)", "887872 (2007 TO134)", "(2018 EC25)"
    ]
    by_name = {m.raw_name: m for m in matches}
    # Separations are recomputed from the returned astrometry; they must agree with the
    # API's own two-significant-figure "Dist. from center Norm" column.
    assert by_name["(2018 EC25)"].sep_arcsec == pytest.approx(16.18, abs=0.3)
    assert by_name["887872 (2007 TO134)"].sep_arcsec == pytest.approx(63.44, abs=0.5)
    assert by_name["130536 (2000 QV208)"].sep_arcsec == pytest.approx(240.6, abs=1.0)


def test_sbident_first_pass_only_is_an_error_not_an_empty_result():
    """The coarse pre-filter is not an identification and must never be read as one."""
    matches, err, n_first = sbident.parse_identify(
        {"n_first_pass": 242791, "fields_first": [], "data_first_pass": [["8 Flora", "..."]]},
        ra_deg=0.0, dec_deg=0.0, obs_index=0, mjd_utc=0.0,
    )
    assert matches == []
    assert err and "first pass" in err
    assert n_first == 242791


def test_sbident_refuses_epochs_it_is_measured_to_choke_on():
    """Measured: the first pass crosses its budget between 9 and 12 years of lookback."""
    now = 2461250.0  # 2026-07-29
    assert sbident.too_old(now - 365.25 * 1.0, now) is None
    assert sbident.too_old(now - 365.25 * 8.0, now) is None
    stale = sbident.too_old(now - 365.25 * 20.0, now)
    assert stale and "time out" in stale


def test_sbident_no_matching_records_is_a_clean_negative():
    matches, err, _ = sbident.parse_identify(
        {"warning": "no matching records"}, ra_deg=0.0, dec_deg=0.0, obs_index=0, mjd_utc=0.0
    )
    assert matches == [] and err is None


@pytest.mark.parametrize(
    ("deg", "expected"),
    [
        (0.0, "00-00-00.00"),
        (312.66276667, "20-50-39.06"),
        (359.99, "23-59-57.60"),
        # Rounds up past 24h and must wrap, not emit "24-00-00.00".
        (359.99999, "00-00-00.00"),
        # Rounds up past a minute and must carry, not emit "12-00-60.00".
        (180.0 - 0.001 / 3600.0 * 15.0, "12-00-00.00"),
    ],
)
def test_sbident_ra_formatting_rounds_before_splitting(deg, expected):
    assert sbident._hms(deg) == expected


@pytest.mark.parametrize(
    ("deg", "expected"), [(-22.08713056, "-22-05-13.7"), (5.0, "05-00-00.0")]
)
def test_sbident_dec_formatting(deg, expected):
    assert sbident._dms(deg) == expected


# --- MPChecker --------------------------------------------------------------------
def test_mpchecker_parses_its_fixed_width_table():
    matches, err = mpchecker.parse_result(
        (DATA / "mpchecker_matches.html").read_text(encoding="utf-8"),
        ra_deg=312.66276667, dec_deg=-22.08713056, obs_index=0, mjd_utc=60874.093279,
    )
    assert err is None
    assert [m.raw_name for m in matches] == ["2018 EC25", "2016 PU44", "(130536) 2000 QV208"]
    by_name = {m.raw_name: m for m in matches}
    assert by_name["2018 EC25"].sep_arcsec == pytest.approx(15.9, abs=1.0)
    assert by_name["2018 EC25"].v_mag == pytest.approx(21.8)
    # MPC's own orbit-quality tag: "4o" = four oppositions.
    assert by_name["2018 EC25"].orbit_class == "4o"
    assert by_name["(130536) 2000 QV208"].orbit_class == "18o"


def test_mpchecker_agrees_with_sbident_on_the_same_field():
    """Two independent services, one field: the separations must agree to ~1"."""
    mpc, _ = mpchecker.parse_result(
        (DATA / "mpchecker_matches.html").read_text(encoding="utf-8"),
        ra_deg=312.66276667, dec_deg=-22.08713056, obs_index=0, mjd_utc=60874.093279,
    )
    jpl, _, _ = sbident.parse_identify(
        json.loads((DATA / "sbident_two_pass.json").read_text(encoding="utf-8")),
        ra_deg=312.66276667, dec_deg=-22.08713056, obs_index=0, mjd_utc=60874.093279,
    )
    mpc_ec25 = next(m for m in mpc if m.raw_name == "2018 EC25")
    jpl_ec25 = next(m for m in jpl if m.raw_name == "(2018 EC25)")
    assert mpc_ec25.sep_arcsec == pytest.approx(jpl_ec25.sep_arcsec, abs=1.5)


def test_mpchecker_none_found_is_a_clean_negative():
    matches, err = mpchecker.parse_result(
        (DATA / "mpchecker_none_found.html").read_text(encoding="utf-8"),
        ra_deg=223.88376667, dec_deg=22.12908889, obs_index=0, mjd_utc=53833.95108,
    )
    assert matches == [] and err is None


def test_mpchecker_webcs_error_is_surfaced_not_swallowed():
    body = (
        "<html><h1>Error from WebCS Script</h1>"
        'The text of the error message is "Invalid data (R1/017/000/001) passed to script"'
        "</html>"
    )
    matches, err = mpchecker.parse_result(body, ra_deg=0, dec_deg=0, obs_index=0, mjd_utc=0)
    assert matches == []
    assert err and "Invalid data" in err


def test_mpchecker_coverage_gap_is_declared_for_pre_2009_epochs():
    """The 73P-C control's null answer here is a coverage gap, not a negative result."""
    gap = mpchecker.coverage_gap(2006)
    assert gap and "comets" in gap
    assert mpchecker.coverage_gap(2025) is None
    assert "500 numbered" in (mpchecker.coverage_gap(1890) or "")


def test_mpchecker_sexagesimal_formatting_round_trips():
    ra, dec = 312.66276667, -22.08713056
    assert mpchecker._fmt_ra(ra) == "20 50 39.06"
    assert mpchecker._fmt_dec(dec) == "-22 05 13.7"
    # The format quantises RA to 0.01 s (1.5e-5 deg) and Dec to 0.1" (2.8e-5 deg); the
    # round trip cannot be tighter than the format, and must not be looser.
    assert mpchecker._sexa_ra("20 50 39.06") == pytest.approx(ra, abs=2e-5)
    assert mpchecker._sexa_dec("-22 05 13.7") == pytest.approx(dec, abs=3e-5)


def test_mpchecker_reports_how_many_objects_were_checked():
    body = (DATA / "mpchecker_matches.html").read_text(encoding="utf-8")
    assert mpchecker.parse_objects_checked(body) == 1411747


# --- SBDB -------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # The regression the positive control caught: peeling the leading integer off a
        # comet designation resolved 73P-C to minor planet (73) Klytia.
        ("73P-C", "73P-C"),
        ("C/2019 Y4-A", "C/2019 Y4-A"),
        ("(130536) 2000 QV208", "130536"),
        ("887872 (2007 TO134)", "887872"),
        ("(2018 EC25)", "2018 EC25"),
        ("8 Flora (A847 UA)", "8"),
        ("2018 EC25", "2018 EC25"),
        ("1927 LA", "1927 LA"),
        ("130535", "130535"),
        ("", ""),
    ],
)
def test_sbdb_name_normalisation(raw, expected):
    assert sbdb.name_to_sstr(raw) == expected


def test_sbdb_parses_the_comet_control_object():
    payload = json.loads((DATA / "sbdb_any.json").read_text(encoding="utf-8"))
    obj = sbdb.parse_sbdb(payload)
    assert obj is not None
    assert obj.des == "73P-C"
    assert obj.fullname == "73P/Schwassmann-Wachmann 3-C"
    assert obj.kind == "cn"
    assert obj.orbit_class == "Jupiter-family Comet"
    assert obj.elements.a == pytest.approx(3.06, abs=0.05)
    assert obj.elements.e == pytest.approx(0.692, abs=0.01)
    assert obj.elements.incl == pytest.approx(11.4, abs=0.1)


def test_sbdb_parse_returns_none_when_nothing_resolved():
    assert sbdb.parse_sbdb({"message": "no matches found"}) is None


def test_element_comparison_flags_agreement_and_disagreement():
    catalogue = OrbitElements(a=2.19, e=0.12, incl=3.79, q=1.93, source="JPL SBDB")
    close = OrbitElements(
        a=2.1855, e=0.1209, incl=3.7915, q=1.9213,
        sigma_a=0.0164, sigma_e=0.011, sigma_i=0.06, sigma_q=0.0235,
    )
    far = OrbitElements(
        a=3.30, e=0.55, incl=19.0, q=1.48,
        sigma_a=0.02, sigma_e=0.01, sigma_i=0.05, sigma_q=0.02,
    )

    good = sbdb.compare_elements(close, catalogue, "X")
    assert good.consistent is True
    assert good.d_a_au == pytest.approx(-0.0045, abs=1e-3)
    assert good.n_sigma_a == pytest.approx(0.27, abs=0.05)

    bad = sbdb.compare_elements(far, catalogue, "X")
    assert bad.consistent is False
    assert "sigma" in bad.note


def test_a_short_arc_fit_is_judged_in_its_own_sigmas_not_a_fixed_fraction():
    """The /21TB2S case: 0.6"-3.2" positionally, but ``a`` differs by 31%.

    M1 measured why -- a short ITF arc determines an orbit's scale badly -- and this fit's
    own sigma(a) is 0.97 AU, so 0.68 AU is 0.7 sigma. Judging it against a fixed 5% would
    reject a certain identification for being short-arc.
    """
    catalogue = OrbitElements(a=2.20, e=0.14, incl=8.0, q=1.89, source="JPL SBDB")
    fitted = OrbitElements(
        a=2.883, e=0.170, incl=7.76, q=2.327,
        sigma_a=0.973, sigma_e=0.143, sigma_i=0.34, sigma_q=0.34,
    )
    cmp = sbdb.compare_elements(fitted, catalogue, "2021 TS112")
    assert cmp.d_a_au == pytest.approx(0.683, abs=0.01)
    assert abs(cmp.d_a_au) > 0.05 * catalogue.a, "a fixed 5% test would reject this"
    assert cmp.consistent is True
    assert cmp.n_sigma_a == pytest.approx(0.70, abs=0.05)


def test_a_vacuous_element_check_says_so():
    """An orbit too loose to contradict anything must not read as corroboration.

    M1's distant-object candidates are the real case: fitted a of 58-304 AU with sigma(a)
    of 37-784 AU. Any catalogue orbit is "within a sigma or two" of that, which is a
    statement about the arc, not about the object.
    """
    catalogue = OrbitElements(a=2.19, e=0.12, incl=3.79, q=1.93)
    loose = OrbitElements(a=58.0, e=0.5, incl=4.0, q=29.0, sigma_a=37.0, sigma_q=20.0)
    cmp = sbdb.compare_elements(loose, catalogue, "X")
    assert cmp.consistent is True
    assert "too loose" in cmp.note


def test_a_runaway_fit_is_still_reported_as_contradicting():
    """t75502b: a = 1.09e11 AU. That disagrees with everything by millions of sigmas."""
    catalogue = OrbitElements(a=2.19, e=0.12, incl=3.79, q=1.93)
    runaway = OrbitElements(a=1.09e11, e=0.999, incl=3.0, q=1.0, sigma_a=8173.0)
    cmp = sbdb.compare_elements(runaway, catalogue, "X")
    assert cmp.consistent is False


def test_element_comparison_without_a_fitted_orbit_is_not_a_failure():
    cmp = sbdb.compare_elements(None, OrbitElements(a=2.0), "X")
    assert cmp.consistent is None
    assert "positional match only" in cmp.note
