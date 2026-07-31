"""The classifier, which is where over-claiming would happen if it happened anywhere.

Half of these tests assert that something is *not* called known. That asymmetry is the
point: a false ``known`` costs one candidate, while a false "new" costs the submitter's
standing with the MPC and pollutes a shared scientific resource.
"""

from __future__ import annotations

import math

import pytest

from itf_linker.vet.types import (
    OrbitElements,
    ServiceMatch,
    ServiceReport,
    VetCandidate,
    VetObservation,
    angular_sep_arcsec,
)
from itf_linker.vet.verdict import CONSIDER_ARCSEC, classify, considered, tally


def obs(mjd: float, night: int) -> VetObservation:
    return VetObservation(mjd_utc=mjd, ra_deg=10.0, dec_deg=5.0, obscode="X05", night=night)


def candidate(*, elements: OrbitElements | None = None, nights: int = 3) -> VetCandidate:
    return VetCandidate(
        desig="TEST1",
        observations=tuple(obs(60000.0 + i, i) for i in range(nights)),
        elements=elements,
        origin="unit test",
    )


def report(service: str, epochs: list[int], matches: list[ServiceMatch]) -> ServiceReport:
    return ServiceReport(
        service=service,
        queries=len(epochs),
        epochs_queried=list(epochs),
        epochs_answered=list(epochs),
        matches=matches,
    )


def match(name: str, epoch: int, sep: float, service: str = "skybot", **kw) -> ServiceMatch:
    return ServiceMatch(
        service=service, raw_name=name, resolved_des=kw.pop("resolved", name),
        sep_arcsec=sep, obs_index=epoch, **kw
    )


TIGHT = OrbitElements(a=2.2, e=0.12, incl=3.8, q=1.9, sigma_a=0.0016)
LOOSE = OrbitElements(a=1.09e11, e=0.999, incl=3.0, q=1.0, sigma_a=8173.0)


# --- the multi-epoch rule ----------------------------------------------------------
def test_one_object_at_several_epochs_is_an_identification():
    services = {
        "skybot": report("skybot", [0, 1, 2], [
            match("2018 EC25", 0, 12.0), match("2018 EC25", 1, 9.0), match("2018 EC25", 2, 14.0)
        ])
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "known"
    assert v.identified_as == "2018 EC25"
    assert v.n_epochs_matched == 3
    assert v.best_sep_arcsec == 9.0 and v.worst_sep_arcsec == 14.0


def test_a_lone_distant_neighbour_is_an_empty_field_not_an_ambiguity():
    """Measured on RL00eAJ: nothing within 114", 200-300" everywhere else. That is nothing.

    Calling it ``ambiguous`` would overstate the evidence -- three catalogued objects sit
    within 5' of any Rubin pointing, so one of them landing 114" away on one night of three
    is the null hypothesis, not a lead.
    """
    services = {"skybot": report("skybot", [0, 1, 2], [match("2016 PU44", 0, 114.0)])}
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "unmatched"
    assert v.identified_as is None
    assert "empty field" in " ".join(v.reasons)


def test_a_lone_but_tight_neighbour_is_flagged_for_a_human():
    """5" on one night of three is odd enough to look at, not enough to identify."""
    services = {"skybot": report("skybot", [0, 1, 2], [match("2016 PU44", 0, 3.0)])}
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "ambiguous"
    assert v.identified_as == "2016 PU44"
    assert "human look" in " ".join(v.reasons)


def test_a_very_close_single_epoch_match_counts_when_there_is_only_one_epoch():
    cand = VetCandidate(desig="ONE", observations=(obs(60000.0, 0),), elements=TIGHT)
    services = {"skybot": report("skybot", [0], [match("2018 EC25", 0, 1.2)])}
    assert classify(cand, services).category == "known"


def test_a_loose_single_epoch_match_is_not_an_identification():
    cand = VetCandidate(desig="ONE", observations=(obs(60000.0, 0),), elements=TIGHT)
    services = {"skybot": report("skybot", [0], [match("2018 EC25", 0, 44.0)])}
    v = classify(cand, services)
    assert v.category == "unmatched"
    assert v.identified_as is None


def test_two_rival_objects_each_covering_the_arc_is_ambiguous():
    services = {
        "skybot": report("skybot", [0, 1], [
            match("2018 EC25", 0, 10.0), match("2018 EC25", 1, 11.0),
            match("2016 PU44", 0, 24.0), match("2016 PU44", 1, 25.0),
        ])
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "ambiguous"
    assert "each explain the arc" in " ".join(v.reasons)


def test_agreement_across_services_is_counted():
    services = {
        "skybot": report("skybot", [0, 1], [
            match("2018 EC25", 0, 10.0), match("2018 EC25", 1, 11.0)
        ]),
        "mpchecker": report("mpchecker", [0, 1], [
            match("2018 EC25", 0, 9.5, service="mpchecker"),
            match("2018 EC25", 1, 10.5, service="mpchecker"),
        ]),
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "known"
    assert v.n_services_agreeing == 2


def test_services_naming_the_same_object_differently_are_unified_by_resolution():
    """``(130536) 2000 QV208`` and ``130536 (2000 QV208)`` are one object, not two rivals."""
    services = {
        "mpchecker": report("mpchecker", [0, 1], [
            match("(130536) 2000 QV208", 0, 8.0, service="mpchecker", resolved="130536"),
            match("(130536) 2000 QV208", 1, 9.0, service="mpchecker", resolved="130536"),
        ]),
        "sbident": report("sbident", [0, 1], [
            match("130536 (2000 QV208)", 0, 8.4, service="sbident", resolved="130536"),
            match("130536 (2000 QV208)", 1, 9.1, service="sbident", resolved="130536"),
        ]),
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "known"
    assert v.identified_as == "130536"
    assert len(v.candidates_considered) == 1


# --- the consideration radius ------------------------------------------------------
def test_matches_beyond_the_radius_are_not_evidence():
    services = {
        "skybot": report("skybot", [0, 1], [
            match("FAR", 0, CONSIDER_ARCSEC + 50), match("FAR", 1, CONSIDER_ARCSEC + 60)
        ])
    }
    assert classify(candidate(elements=TIGHT), services).category == "unmatched"


def test_a_large_quoted_ephemeris_error_does_not_widen_the_radius():
    """Measured on RL00iMW: it let ``2022 QB161`` in at 273" because its error bar was big.

    Four arcminutes away is not the candidate whatever the service's uncertainty says.
    """
    wide = ServiceMatch(service="skybot", raw_name="X", sep_arcsec=273.0, ephem_err_arcsec=90.0)
    assert considered(wide) is False
    assert considered(ServiceMatch(service="s", raw_name="Z", sep_arcsec=None)) is False


def test_a_comet_gets_a_wider_identification_radius_than_an_asteroid():
    """Non-gravitational forces are real; 73P was disintegrating when the ITF saw it."""
    from itf_linker.vet.verdict import COMET_MATCH_ARCSEC, MATCH_ARCSEC, match_radius

    assert match_radius("cn") == COMET_MATCH_ARCSEC
    assert match_radius("cu") == COMET_MATCH_ARCSEC
    assert match_radius("an") == MATCH_ARCSEC
    assert match_radius("au") == MATCH_ARCSEC
    assert match_radius(None) == MATCH_ARCSEC, "unresolved identities get the tight radius"


def test_the_73p_control_is_identified_and_an_asteroid_at_the_same_distances_is_not():
    """The one case that forced a class-dependent radius, and its counter-case."""
    comet = {"skybot": report("skybot", [0, 1, 2], [
        ServiceMatch(service="skybot", raw_name="73P-C", resolved_des="73P-C", kind="cn",
                     sep_arcsec=s, ephem_err_arcsec=0.7, obs_index=i)
        for i, s in enumerate((32.842, 75.197, 118.342))
    ])}
    assert classify(candidate(), comet).category == "known"

    asteroid = {"skybot": report("skybot", [0, 1, 2], [
        ServiceMatch(service="skybot", raw_name="2018 EC25", resolved_des="2018 EC25",
                     kind="au", sep_arcsec=s, obs_index=i)
        for i, s in enumerate((32.842, 75.197, 118.342))
    ])}
    assert classify(candidate(), asteroid).category == "unmatched"


def test_a_co_moving_neighbour_is_not_an_identification():
    """``2018 EC25`` sat 16" from ``RL00adt`` and 80" from it 2.3 days later.

    Present at two epochs, at the candidate's position at neither. A main-belt neighbour
    moves at nearly the candidate's own rate, so mere presence across epochs is worthless;
    what counts is being *at* the candidate on more than one night.
    """
    services = {
        "skybot": report("skybot", [0, 1, 2], [
            match("2018 EC25", 0, 18.71, kind="au"), match("2018 EC25", 1, 76.79, kind="au")
        ]),
        "mpchecker": report("mpchecker", [0, 1, 2], [
            match("2018 EC25", 0, 15.68, service="mpchecker", kind="au"),
            match("2018 EC25", 1, 79.73, service="mpchecker", kind="au"),
        ]),
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "ambiguous"
    assert v.n_epochs_matched == 1
    assert "human look" in " ".join(v.reasons)


# --- non-matches, and why they are not discoveries ---------------------------------
def test_a_non_match_is_never_called_new():
    services = {"skybot": report("skybot", [0, 1, 2], [])}
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "unmatched"
    assert v.unmatched_reason == "no_catalogue_object_near_astrometry"
    assert "NOT new" in " ".join(v.reasons)
    assert v.identified_as is None


def test_an_unconstrained_orbit_makes_a_non_match_uninformative():
    """M1's t75502b: sigma(a) = 8,173 AU. Nothing could have matched that."""
    services = {"skybot": report("skybot", [0, 1, 2], [])}
    v = classify(candidate(elements=LOOSE), services)
    assert v.category == "unmatched"
    assert v.unmatched_reason == "orbit_too_poorly_constrained"


def test_a_coverage_gap_is_distinguished_from_an_absence():
    services = {"mpchecker": report("mpchecker", [0, 1, 2], [])}
    v = classify(
        candidate(elements=TIGHT), services,
        coverage_notes={"mpchecker": "excludes comets before 2009"},
    )
    assert v.category == "unmatched"
    assert v.unmatched_reason == "epoch_outside_service_coverage"


def test_a_gap_in_one_service_does_not_excuse_a_clean_service():
    """SkyBoT answered with full coverage, so the absence is real for what it covers."""
    services = {
        "mpchecker": report("mpchecker", [0, 1, 2], []),
        "skybot": report("skybot", [0, 1, 2], []),
    }
    v = classify(
        candidate(elements=TIGHT), services,
        coverage_notes={"mpchecker": "excludes comets before 2009"},
    )
    assert v.unmatched_reason == "no_catalogue_object_near_astrometry"


def test_no_service_answering_is_service_failed_not_unmatched():
    services = {
        "skybot": ServiceReport(service="skybot", queries=3, epochs_queried=[0, 1, 2],
                                errors=["timeout"]),
        "mpchecker": ServiceReport(service="mpchecker", skipped="disabled after 5 failures"),
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "service_failed"
    assert v.identified_as is None
    assert any("skipped" in r for r in v.reasons)


def test_a_candidate_with_no_astrometry_cannot_be_vetted():
    v = classify(VetCandidate(desig="EMPTY", observations=()), {})
    assert v.category == "service_failed"


# --- elements as a check on a positional match -------------------------------------
def test_element_disagreement_downgrades_a_positional_match():
    from itf_linker.vet.types import ElementComparison

    services = {
        "skybot": report("skybot", [0, 1], [
            match("2018 EC25", 0, 10.0), match("2018 EC25", 1, 11.0)
        ])
    }
    bad = ElementComparison(des="2018 EC25", consistent=False, note="outside tolerance")
    v = classify(candidate(elements=TIGHT), services, element_comparison=bad)
    assert v.category == "ambiguous"
    assert any("differ by more than tolerance" in r for r in v.reasons)


def test_an_unresolvable_identity_is_flagged():
    services = {
        "skybot": report("skybot", [0, 1], [
            match("MYSTERY", 0, 5.0, resolved=None), match("MYSTERY", 1, 6.0, resolved=None)
        ])
    }
    v = classify(candidate(elements=TIGHT), services)
    assert v.category == "known"
    assert any("could not be resolved" in r for r in v.reasons)


# --- counting ----------------------------------------------------------------------
def test_tally_counts_categories_and_unmatched_reasons():
    services_empty = {"skybot": report("skybot", [0, 1, 2], [])}
    verdicts = [
        classify(candidate(elements=TIGHT), services_empty),
        classify(candidate(elements=LOOSE), services_empty),
        classify(candidate(elements=TIGHT), {
            "skybot": report("skybot", [0, 1], [
                match("A", 0, 5.0), match("A", 1, 6.0)
            ])
        }),
    ]
    counts = tally(verdicts)
    assert counts["n"] == 3
    assert counts["by_category"] == {"known": 1, "unmatched": 2}
    assert counts["unmatched_reasons"] == {
        "no_catalogue_object_near_astrometry": 1,
        "orbit_too_poorly_constrained": 1,
    }


# --- geometry ----------------------------------------------------------------------
def test_angular_separation_matches_astropy():
    astropy_coords = pytest.importorskip("astropy.coordinates")
    import astropy.units as u

    cases = [
        (10.0, 5.0, 10.001, 5.001),
        (359.999, -22.0, 0.001, -22.0005),
        (312.66276667, -22.08713056, 312.6636, -22.0913),
        (0.0, 89.9, 180.0, 89.9),
    ]
    for ra1, dec1, ra2, dec2 in cases:
        a = astropy_coords.SkyCoord(ra1 * u.deg, dec1 * u.deg)
        b = astropy_coords.SkyCoord(ra2 * u.deg, dec2 * u.deg)
        assert angular_sep_arcsec(ra1, dec1, ra2, dec2) == pytest.approx(
            a.separation(b).arcsec, rel=1e-9, abs=1e-9
        )


def test_angular_separation_is_precise_at_sub_arcsecond_scales():
    """The acos form loses all precision here, which is exactly where identification lives."""
    sep = angular_sep_arcsec(10.0, 5.0, 10.0 + 0.1 / 3600.0 / math.cos(math.radians(5.0)), 5.0)
    assert sep == pytest.approx(0.1, rel=1e-6)


# --- orbit quality -----------------------------------------------------------------
def test_well_constrained_reflects_whether_the_orbit_scale_is_determined():
    assert TIGHT.well_constrained is True
    assert LOOSE.well_constrained is False
    assert OrbitElements(a=2.0).well_constrained is False
    assert OrbitElements(a=58.0, sigma_a=784.0).well_constrained is False
    assert OrbitElements(a=58.0, sigma_a=1.5).well_constrained is True
