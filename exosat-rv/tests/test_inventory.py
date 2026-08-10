"""Rollup logic, exercised offline with synthetic frames.

The awkward cases are the point: a night that is public in raw but has no reduced product,
a night whose frames straddle the release date, and a reduced product for a night in a band
we did not ask for.
"""

from datetime import UTC, datetime, timedelta

import pytest

from exosat_rv.archive.inventory import (
    Frame,
    Inventory,
    parse_release,
    parse_setting,
    roll_up,
)

NOW = datetime(2026, 8, 9, tzinfo=UTC)
PAST = NOW - timedelta(days=30)
FUTURE = NOW + timedelta(days=200)


def f(night, setting="H", release=PAST, reduced=False, prog="1.A"):
    return Frame("CD-35 2722 B", night, prog, setting, release, reduced)


def test_parse_setting_splits_filter_path():
    assert parse_setting("H,HK") == "H"
    assert parse_setting("HX5E-2,HK") == "HX5E-2"
    assert parse_setting("J,YJ") == "J"
    assert parse_setting(None) == "?"


def test_parse_release_handles_trailing_z():
    assert parse_release("2027-05-02T23:35:56Z").tzinfo is not None


def test_roll_up_groups_and_counts():
    nights = roll_up([f("2024-01-01"), f("2024-01-01"), f("2024-01-01", reduced=True),
                      f("2024-02-01")])
    assert [n.night for n in nights] == ["2024-01-01", "2024-02-01"]
    assert nights[0].n_raw == 2 and nights[0].n_reduced == 1
    assert nights[0].has_reduced and not nights[1].has_reduced


def test_roll_up_keeps_earliest_release():
    """If any frame from a night is public, the night has usable data."""
    n = roll_up([f("2024-01-01", release=FUTURE), f("2024-01-01", release=PAST)])[0]
    assert n.earliest_release == PAST
    assert n.is_public(NOW)


def test_band_filter_excludes_other_settings():
    inv = Inventory("t", roll_up([f("2024-01-01", setting="K", reduced=True),
                                  f("2024-01-01", setting="K")]), NOW)
    assert inv.usable("H") == []
    assert len(inv.usable("K")) == 1


def test_unknown_setting_never_matches_a_band():
    """A reduced product with no raw counterpart keeps "?" and stays out of any band."""
    inv = Inventory("t", roll_up([f("2024-01-01", setting="?", reduced=True)]), NOW)
    assert inv.usable("H") == [] and inv.usable("K") == []


def test_the_three_way_split_is_exhaustive():
    frames = [
        f("2024-01-01", reduced=True), f("2024-01-01"),          # usable
        f("2024-02-01"),                                          # reduction gap
        f("2024-03-01", release=FUTURE),                          # embargoed
        f("2024-04-01", release=FUTURE, reduced=True),            # embargoed
    ]
    inv = Inventory("t", roll_up(frames), NOW)
    s = inv.summary("H")
    assert s["usable_now"] == 1
    assert s["reduction_gap"] == 1
    assert s["embargoed"] == 2
    assert s["usable_now"] + s["reduction_gap"] + s["embargoed"] == s["nights_total"]
    assert s["gap_nights"] == ["2024-02-01"]


def test_baseline_spans_first_to_last_usable_night():
    inv = Inventory("t", roll_up([f("2023-10-13", reduced=True), f("2025-01-21", reduced=True),
                                  f("2024-06-01", reduced=True)]), NOW)
    assert inv.summary("H")["usable_baseline"] == ["2023-10-13", "2025-01-21"]


def test_empty_inventory_reports_no_baseline():
    assert Inventory("t", [], NOW).summary("H")["usable_baseline"] is None


@pytest.mark.network
def test_live_inventory_matches_the_published_epoch_count():
    """M0's headline, as a test: 20 public H-band nights, and the paper analysed 20 epochs.

    Note the paper *obtained* 21 and discarded one for continuum S/N ~5, so this is an
    equality of analysed epochs to public nights, not of observations to nights. Marked
    ``network``; will drift when the embargoed frames release, at which point the assertion
    should be updated deliberately rather than loosened.
    """
    from exosat_rv.archive.tap import build_inventory
    from exosat_rv.config import PUBLISHED as P

    inv = build_inventory("CD-35 2722 B", P.star_ra_deg, P.star_dec_deg)
    s = inv.summary("H")
    # 20, not 21, because `dbo.raw` mislabels 2024-01-03 as K-band while the product built
    # from those exact frames is H1567. The archive-only count is therefore one short of the
    # 21 epochs the paper obtained; M2 verified the true band from the product header.
    assert s["usable_now"] + s["reduction_gap"] == P.n_epochs_obtained - 1
    assert s["usable_now"] + s["reduction_gap"] == P.n_epochs_used
    assert s["usable_baseline"] == ["2023-10-13", "2025-01-21"]
