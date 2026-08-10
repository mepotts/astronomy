"""Target-list classification and dedup, offline.

The control that matters (CD-35 2722 B being rediscovered by an archive-first search) needs
the network and is marked accordingly; everything else here is pure logic.
"""

import pytest

from exosat_rv.targets.catalog import (
    COMPANION_TOKEN,
    JUNK_NAME,
    CompanionTarget,
    _norm,
    dedupe,
    shortlist,
)


def t(name, simbad=None, otype=None, sp=None, frames=10, pub=10, kind="identifier"):
    return CompanionTarget(eso_object=name, n_frames=frames, n_public=pub, ra_deg=0.0,
                           dec_deg=0.0, simbad_id=simbad, otype=otype, sp_type=sp,
                           match_kind=kind)


@pytest.mark.parametrize("name", ["CD-35 2722 B", "AB PIC B", "HR-7329-B", "GJ 667 C", "ETA TEL B"])
def test_component_names_are_selected(name):
    assert COMPANION_TOKEN.search(name)


@pytest.mark.parametrize("name", ["HD 218396", "TWA 27", "51 ERI", "GQ LUP"])
def test_plain_star_names_are_not_selected(name):
    assert not COMPANION_TOKEN.search(name)


@pytest.mark.parametrize("name", ["C_2006_W3", "C_2007_N3_LULIN", "73P/COMET"])
def test_comets_are_excluded(name):
    """These trip the component-letter pattern; a word-boundary anchor does NOT work
    because the designations continue with an underscore."""
    assert JUNK_NAME.search(name)


@pytest.mark.parametrize(
    "a,b",
    [("BET PIC B", "* bet Pic b"), ("PZ TEL B", "V* PZ Tel B"),
     ("CD-35 2722 B", "CD-35  2722B"), ("HR-7329-B", "HR 7329 B")],
)
def test_normalisation_bridges_simbad_and_observer_spellings(a, b):
    assert _norm(a) == _norm(b)


def test_spectral_type_overrides_otype_for_stars():
    """tau Boo B is typed `*` by SIMBAD but is an M3V star -- must not pass as borderline."""
    assert t("TAU-BOO-B", "* tau Boo B", "*", "M3V").is_substellar is False
    assert t("HIP 81208 B", "HD 149274B", "LM*", "M5").is_substellar is False


def test_late_types_stay_substellar_or_borderline():
    assert t("CD-35 2722 B", "CD-35  2722B", "BD*", "L0-1").is_substellar is True
    assert t("ETA TEL B", "* eta Tel B", "LM*", "M7.5V").is_substellar is None


def test_unknown_stays_unknown():
    assert t("X B", None, None, None).is_substellar is None


def test_dedupe_merges_aliases_of_one_object():
    """ETA TEL B and HR-7329-B are the same object: HR 7329 *is* eta Tel."""
    merged = dedupe([t("ETA TEL B", "* eta Tel B", "LM*", "M7.5V", frames=68, pub=68),
                     t("HR-7329-B", "* eta Tel B", "LM*", "M7.5V", frames=48, pub=48)])
    assert len(merged) == 1
    assert merged[0].n_frames == 116
    assert merged[0].aliases == ["HR-7329-B"]


def test_dedupe_keeps_unresolved_targets_separate():
    """Two unresolved targets must not collapse into each other."""
    assert len(dedupe([t("A B", None), t("C B", None)])) == 2


def test_dedupe_promotes_the_stronger_match_kind():
    merged = dedupe([t("X B", "obj", "BD*", "L1", kind="nearest-any"),
                     t("Y B", "obj", "BD*", "L1", kind="identifier")])
    assert merged[0].match_kind == "identifier"


def test_shortlist_drops_stars_and_embargoed_targets():
    keep_bd = t("A B", "a", "BD*", "L1")
    keep_border = t("B B", "b", "LM*", "M8")
    drop_star = t("C B", "c", "*", "M3V")
    drop_private = t("D B", "d", "BD*", "L1", pub=0)
    out = shortlist([keep_bd, keep_border, drop_star, drop_private])
    assert out == [keep_bd, keep_border]


@pytest.mark.network
def test_archive_first_search_rediscovers_cd35_2722b():
    """The control for the whole M5 method.

    A catalogue-first search could not find this object at all (the NASA Exoplanet Archive
    caps at 30 M_Jup). If the archive-first search stops returning it, the pipeline is broken.
    """
    from exosat_rv.targets.catalog import build

    ts = build(min_frames=4)
    ids = [str(x.simbad_id or "") for x in ts]
    assert any("2722" in i for i in ids), "CD-35 2722 B not rediscovered"
