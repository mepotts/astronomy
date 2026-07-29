"""Pin the partitioning maths: HEALPix assignment and the candidate counters."""

from __future__ import annotations

import polars as pl
import pytest

from itf_linker.index.partition import (
    add_healpix,
    candidate_combinatorics,
    count_pairs_within_window,
    healpix_resolution_deg,
    partition_stats,
)


def _tracklets(rows: list[tuple[float, float, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "ra_deg": [r[0] for r in rows],
            "dec_deg": [r[1] for r in rows],
            "mjd_mid": [r[2] for r in rows],
        }
    )


def test_healpix_resolution_shrinks_with_nside():
    assert healpix_resolution_deg(16) == pytest.approx(3.665, abs=0.01)
    assert healpix_resolution_deg(64) == pytest.approx(healpix_resolution_deg(16) / 4, rel=1e-6)


def test_nearby_positions_share_a_pixel_and_distant_ones_do_not():
    df = _tracklets([(10.0, 5.0, 0.0), (10.05, 5.02, 0.0), (200.0, -40.0, 0.0)])
    out = add_healpix(df, 64)
    pix = out["hpx64"].to_list()
    assert pix[0] == pix[1]
    assert pix[2] != pix[0]


def test_pair_counting_excludes_same_night():
    """Two tracklets 0.1 d apart are the same night -- useless for linking."""
    df = add_healpix(_tracklets([(10.0, 5.0, 100.0), (10.01, 5.0, 100.1)]), 64)
    pairs, triplets = count_pairs_within_window(df, "hpx64", window_days=15.0)
    assert (pairs, triplets) == (0, 0)


def test_pair_and_triplet_counting_is_exact():
    # Three tracklets in one pixel on three separate nights within the window.
    df = add_healpix(
        _tracklets([(10.0, 5.0, 100.0), (10.01, 5.0, 103.0), (10.02, 5.0, 106.0)]), 64
    )
    pairs, triplets = count_pairs_within_window(df, "hpx64", window_days=15.0)
    assert pairs == 3      # C(3,2)
    assert triplets == 1   # C(3,3)


def test_window_truncates_pairs():
    df = add_healpix(
        _tracklets([(10.0, 5.0, 100.0), (10.01, 5.0, 103.0), (10.02, 5.0, 140.0)]), 64
    )
    pairs, triplets = count_pairs_within_window(df, "hpx64", window_days=10.0)
    assert pairs == 1      # only the 100/103 pair fits
    assert triplets == 0


def test_separate_pixels_never_pair():
    df = add_healpix(_tracklets([(10.0, 5.0, 100.0), (200.0, -40.0, 103.0)]), 64)
    pairs, _ = count_pairs_within_window(df, "hpx64", window_days=15.0)
    assert pairs == 0


def test_partition_stats_shape():
    df = _tracklets([(10.0, 5.0, 100.0), (10.01, 5.0, 103.0), (200.0, -40.0, 106.0)])
    stats = partition_stats(df, 64)
    assert stats["nside"] == 64
    assert stats["pixels_total"] == 12 * 64 * 64
    assert stats["pixels_occupied"] == 2


def test_combinatorics_flags_pixels_too_small_for_the_window():
    """A pixel smaller than the object's motion silently loses real links."""
    df = _tracklets([(10.0, 5.0, 100.0), (10.01, 5.0, 103.0)])
    rows = candidate_combinatorics(df, nsides=(16, 128), windows_days=(3.0, 30.0))
    by_key = {(r["nside"], r["window_days"]): r for r in rows}
    assert by_key[(16, 3.0)]["pixel_covers_motion"] is True     # 3.66 deg > 0.90 deg
    assert by_key[(128, 30.0)]["pixel_covers_motion"] is False  # 0.46 deg < 9.0 deg
