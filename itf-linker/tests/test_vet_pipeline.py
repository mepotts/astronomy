"""Orchestration: epoch selection, the calendar inverse, sources, and one end-to-end run.

The end-to-end test runs the real pipeline against a session in ``offline`` mode backed by
hand-written cache entries. That exercises the actual query construction -- if a parameter
name changes, the cache key changes and the lookup misses -- without touching the network.
"""

from __future__ import annotations

import json

import pytest

from itf_linker.mpc80 import gregorian_to_mjd
from itf_linker.vet import (
    CachedSession,
    VetCandidate,
    VetObservation,
    from_mpc80_lines,
    select_epochs,
    vet_candidate,
    vet_candidates,
)
from itf_linker.vet.cache import _cache_key
from itf_linker.vet.pipeline import Resolver, _calendar
from itf_linker.vet.sources import elements_from_fit

#: Real ITF records for M1's best-conditioned candidate, three Rubin nights over 11 days.
RL00ADT = [
    "     RL00adt 0C2025 07 18.09327920 50 39.064-22 05 13.67         23.22gW     X05",
    "     RL00adt 0C2025 07 18.11667620 50 37.645-22 05 21.76         22.88rW     X05",
    "     RL00adt 0C2025 07 20.36598320 48 22.061-22 18 02.36         23.53gW     X05",
    "     RL00adt 0C2025 07 20.38934320 48 20.601-22 18 09.98         22.97rW     X05",
    "     RL00adt 0C2025 07 29.34172120 38 48.294-23 07 01.83         22.56iW     X05",
    "     RL00adt 0C2025 07 29.36193620 38 46.934-23 07 07.91         22.51iW     X05",
]


# --- sources ----------------------------------------------------------------------
def test_mpc80_lines_become_a_candidate():
    cand = from_mpc80_lines("RL00adt", RL00ADT, origin="test")
    assert len(cand.observations) == 6
    assert cand.n_nights == 3
    assert cand.obscodes == ["X05"]
    first = cand.observations[0]
    assert first.mjd_utc == pytest.approx(60874.093279, abs=1e-6)
    assert first.ra_deg == pytest.approx(312.66276667, abs=1e-6)
    assert first.dec_deg == pytest.approx(-22.08713056, abs=1e-6)
    assert first.mag == pytest.approx(23.22)
    # Observations arrive time-ordered whatever order the file gave them in.
    assert [o.mjd_utc for o in cand.observations] == sorted(o.mjd_utc for o in cand.observations)


def test_space_based_continuation_lines_are_not_treated_as_positions():
    """An ``s`` line carries spacecraft x/y/z in the RA/Dec columns; querying it is nonsense."""
    pair = [
        "     C51SAMP  S2019 05 01.00000 12 00 00.000+10 00 00.0          19.5 VC51",
        "     C51SAMP  s2019 05 01.00000 1 - 1272.5482 + 5678.1234 - 999.0000        C51",
    ]
    cand = from_mpc80_lines("C51SAMP", pair)
    assert len(cand.observations) == 1


def test_elements_are_read_from_an_m1_row():
    row = {"a": 2.1855, "e": 0.1209, "incl": 3.79, "q": 1.92, "sigma_a": 0.00164,
           "sigma_q": 0.0235, "epoch_jd": 2460885.5, "desig": "RL00adt"}
    els = elements_from_fit(row)
    assert els.a == pytest.approx(2.1855)
    assert els.sigma_a == pytest.approx(0.00164)
    assert els.well_constrained is True
    assert "Find_Orb" in els.source


# --- epoch selection --------------------------------------------------------------
def test_epochs_are_sampled_one_per_night():
    cand = from_mpc80_lines("RL00adt", RL00ADT)
    picked = select_epochs(cand, max_epochs=3)
    assert len(picked) == 3
    nights = {int(o.mjd_utc) for _, o in picked}
    assert len(nights) == 3, "two detections on one night are not independent evidence"


def test_epoch_selection_spreads_across_the_arc_and_keeps_the_ends():
    obs = tuple(
        VetObservation(mjd_utc=60000.0 + i * 3, ra_deg=1.0, dec_deg=1.0, obscode="X05", night=i)
        for i in range(10)
    )
    picked = select_epochs(VetCandidate(desig="W", observations=obs), max_epochs=3)
    assert [o.night for _, o in picked] == [0, 4, 9]


def test_epoch_selection_caps_but_never_pads():
    obs = (VetObservation(mjd_utc=60000.0, ra_deg=1.0, dec_deg=1.0, obscode="X05", night=0),)
    assert len(select_epochs(VetCandidate(desig="W", observations=obs), max_epochs=3)) == 1
    assert select_epochs(VetCandidate(desig="W", observations=()), max_epochs=3) == []


def test_the_earliest_detection_of_each_night_is_the_one_queried():
    obs = (
        VetObservation(mjd_utc=60000.9, ra_deg=1.0, dec_deg=1.0, obscode="X05", night=0),
        VetObservation(mjd_utc=60000.1, ra_deg=2.0, dec_deg=2.0, obscode="X05", night=0),
    )
    (_, chosen), = select_epochs(VetCandidate(desig="W", observations=obs), max_epochs=3)
    assert chosen.mjd_utc == pytest.approx(60000.1)


# --- the calendar inverse ---------------------------------------------------------
@pytest.mark.parametrize(
    ("year", "month", "day"),
    [
        (2006, 4, 8.95108), (2025, 7, 18.093279), (1900, 1, 1.0), (2000, 2, 29.5),
        (2026, 12, 31.999), (1889, 6, 15.25),
    ],
)
def test_calendar_inverts_the_mjd_conversion(year, month, day):
    """MPChecker takes a calendar date, so this inverse sits between the ITF and the MPC."""
    y, m, d = _calendar(gregorian_to_mjd(year, month, day))
    assert (y, m) == (year, month)
    assert d == pytest.approx(day, abs=1e-6)


# --- end to end, offline ----------------------------------------------------------
def _seed(session: CachedSession, service: str, url: str, params: dict, text: str) -> None:
    path = session.cache_dir / service / f"{_cache_key(service, url, params)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": 200, "url": url, "text": text}), encoding="utf-8")


def _seed_candidate_replies(session, cand, *, name, sep_by_epoch):
    """Pre-load SkyBoT and MPChecker replies for each epoch this candidate will query."""
    from itf_linker.vet import mpchecker, skybot
    from itf_linker.vet.pipeline import SEARCH_RADIUS_ARCSEC

    for i, (_, obs) in enumerate(select_epochs(cand)):
        sky_params = {
            "-ra": f"{obs.ra_deg:.7f}", "-dec": f"{obs.dec_deg:+.7f}",
            "-rd": f"{SEARCH_RADIUS_ARCSEC / 3600.0:.5f}", "-ep": f"{obs.jd_utc:.6f}",
            "-loc": obs.obscode, "-mime": "json", "-output": "all", "-filter": "0",
            "-objFilter": "111", "-from": "itf-linker-vet",
        }
        body = json.dumps(
            [{"Name": name, "Class": "MB>Inner", "d (arcsec)": sep_by_epoch[i],
              "Err (arcsec)": 0.4, "VMag (mag)": 21.8}]
            if sep_by_epoch[i] is not None else []
        )
        _seed(session, skybot.SERVICE, skybot.SKYBOT_URL, sky_params, body)

        year, month, day = _calendar(obs.mjd_utc)
        mpc_params = {
            "year": f"{year:04d}", "month": f"{month:02d}", "day": f"{day:09.6f}",
            "which": "pos", "ra": mpchecker._fmt_ra(obs.ra_deg),
            "decl": mpchecker._fmt_dec(obs.dec_deg), "TextArea": "",
            "radius": "5", "limit": "25.0", "oc": obs.obscode, "sort": "d", "mot": "h",
            "tmot": "s", "pdes": "u", "needed": "f", "ps": "n", "type": "p",
        }
        _seed(
            session, mpchecker.SERVICE, mpchecker.MPCHECKER_URL, mpc_params,
            "<html>No known minor planets, brighter than <i>V</i> = 25.0, were found in "
            "the 5.0-arcminute region.</html>",
        )


def _seed_sbdb(session, sstr, des, fullname):
    from itf_linker.vet import sbdb

    _seed(
        session, sbdb.SERVICE, sbdb.SBDB_URL,
        {"sstr": sstr, "full-prec": "true", "discovery": "0"},
        json.dumps({
            "object": {"des": des, "fullname": fullname, "kind": "au",
                       "orbit_class": {"name": "Main-belt Asteroid"}},
            "orbit": {"epoch": 2460885.5, "elements": [
                {"name": "a", "value": "2.1855"}, {"name": "e", "value": "0.1209"},
                {"name": "i", "value": "3.7915"}, {"name": "q", "value": "1.9213"},
            ]},
        }),
    )


def test_a_full_offline_run_identifies_a_seeded_object(tmp_path):
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0)
    cand = from_mpc80_lines(
        "RL00adt", RL00ADT,
        elements=elements_from_fit({"a": 2.1855, "e": 0.1209, "incl": 3.7915, "q": 1.9213,
                                    "sigma_a": 0.00164}),
        origin="test",
    )
    _seed_candidate_replies(session, cand, name="2018 EC25", sep_by_epoch=[12.0, 9.0, 14.0])
    _seed_sbdb(session, "2018 EC25", "2018 EC25", "(2018 EC25)")
    session.offline = True

    verdict = vet_candidate(session, cand, Resolver(session))
    assert verdict.category == "known"
    assert verdict.identified_as == "2018 EC25"
    assert verdict.n_epochs_matched == 3
    assert verdict.element_comparison is not None
    assert verdict.element_comparison.consistent is True
    # SBIDENT is escalation-only, and this candidate never needed escalating.
    assert "sbident" not in verdict.services


def test_a_full_offline_run_reports_a_clean_non_match_without_claiming_discovery(tmp_path):
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0)
    cand = from_mpc80_lines(
        "RL00adt", RL00ADT,
        elements=elements_from_fit({"a": 2.1855, "sigma_a": 0.00164}), origin="test",
    )
    _seed_candidate_replies(session, cand, name="", sep_by_epoch=[None, None, None])
    session.offline = True

    verdict = vet_candidate(session, cand, Resolver(session), use_sbident=False)
    assert verdict.category == "unmatched"
    assert verdict.unmatched_reason == "no_catalogue_object_near_astrometry"
    assert verdict.identified_as is None


def test_vet_candidates_reports_the_tally_and_the_http_cost(tmp_path):
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0)
    cand = from_mpc80_lines("RL00adt", RL00ADT, origin="test")
    _seed_candidate_replies(session, cand, name="2018 EC25", sep_by_epoch=[12.0, 9.0, 14.0])
    _seed_sbdb(session, "2018 EC25", "2018 EC25", "(2018 EC25)")
    session.offline = True

    result = vet_candidates(session, [cand], use_sbident=False)
    assert result["tally"]["by_category"] == {"known": 1}
    assert result["http"]["per_service"]["skybot"]["cache_hits"] == 3
    assert result["settings"]["max_epochs"] == 3
    assert result["verdicts"][0]["desig"] == "RL00adt"


def test_a_candidate_without_astrometry_is_reported_not_crashed(tmp_path):
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0, offline=True)
    empty = VetCandidate(desig="NOTHING", observations=())
    verdict = vet_candidate(session, empty, Resolver(session))
    assert verdict.category == "service_failed"
    assert "no usable astrometry" in " ".join(verdict.reasons)


def test_resolution_is_memoised_across_candidates(tmp_path):
    session = CachedSession(tmp_path / "cache", min_interval_s=0.0)
    _seed_sbdb(session, "2018 EC25", "2018 EC25", "(2018 EC25)")
    session.offline = True
    resolver = Resolver(session)
    first, _ = resolver.resolve("2018 EC25")
    second, _ = resolver.resolve("2018 EC25")
    assert first is second
    assert len(resolver.cache) == 1
