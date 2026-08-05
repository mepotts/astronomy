"""The widened hypothesis grid: the near root, the bands, and the r ~ 1 AU degeneracy.

M3 searched 1.4-5.6 AU, where the observer is always *inside* the hypothesised sphere and
the ``r ~ 1 AU`` degeneracy it discovered can never be reached. M4 spans 0.55-50 AU, which
turns both of those from theoretical concerns into things the production grid walks
straight through on every window. These tests pin the behaviour there.
"""

from __future__ import annotations

import numpy as np
import pytest

from itf_linker.link.geometry import (
    MIN_TOPOCENTRIC_DISTANCE_AU,
    earth_heliocentric_posvel,
    solve_rho,
    state_from_hypothesis,
    unit_vector_rates,
    unit_vectors,
)
from itf_linker.link.heliolinc import (
    NEAR_BRANCH_MAX_R_AU,
    HypothesisGrid,
    link_window,
)
from itf_linker.link.pipeline import (
    Band,
    belt_band,
    curvature_window_days,
    link_bands,
    wide_bands,
)
from test_link_heliolinc import SITES, _arrows, _synthetic_observations

# ----------------------------------------------------------------------------------
# The near root
# ----------------------------------------------------------------------------------

def _sunward_geometry(r_obs: float = 1.0, elongation_deg: float = 20.0):
    """An observer at ``r_obs`` on the x axis, looking ``elongation_deg`` off the Sun."""
    obs = np.array([[r_obs, 0.0, 0.0]])
    e = np.radians(elongation_deg)
    direction = np.array([[-np.cos(e), np.sin(e), 0.0]])
    return obs, direction


def test_an_interior_sphere_is_pierced_twice_and_both_roots_are_real():
    obs, direction = _sunward_geometry(elongation_deg=20.0)
    far, ok_far = solve_rho(obs, direction, np.array([0.7]))
    near, ok_near = solve_rho(obs, direction, np.array([0.7]), near=True)
    assert ok_far[0] and ok_near[0]
    assert near[0] < far[0]
    for rho in (near[0], far[0]):
        point = obs[0] + rho * direction[0]
        assert np.linalg.norm(point) == pytest.approx(0.7, abs=1e-12)


def test_the_near_root_is_behind_the_observer_once_the_sphere_encloses_them():
    """Beyond ~1 AU the near branch is not merely redundant, it is unphysical."""
    obs = np.array([[1.0, 0.0, 0.0]])
    direction = np.array([[-1.0, 0.0, 0.0]])
    for r in (1.05, 1.4, 2.5, 30.0):
        _, ok = solve_rho(obs, direction, np.array([r]), near=True)
        assert not ok[0], r


def test_a_line_of_sight_that_misses_an_interior_sphere_is_invalid_on_both_roots():
    """An object at 0.7 AU cannot be seen at 90 deg elongation, and the solver says so."""
    obs, direction = _sunward_geometry(elongation_deg=90.0)
    for near in (False, True):
        _, ok = solve_rho(obs, direction, np.array([0.7]), near=near)
        assert not ok[0]


def test_the_grid_sweeps_the_near_branch_only_where_it_exists():
    grid = HypothesisGrid.geometric(0.55, 2.0, fractional_step=0.05)
    seen = {(round(r, 6), near) for r, _, near in grid}
    for r, near in seen:
        if near:
            assert r < NEAR_BRANCH_MAX_R_AU
    assert any(near for _, near in seen), "no near-branch hypotheses at all"
    assert len(grid) == sum(
        len(grid.rdot_fractions) * (2 if r < NEAR_BRANCH_MAX_R_AU else 1) for r in grid.r_au
    )


# ----------------------------------------------------------------------------------
# The r ~ 1 AU degeneracy, now that the grid actually spans 1 AU
# ----------------------------------------------------------------------------------

def test_every_hypothesis_within_the_guard_of_the_observers_own_distance_is_rejected():
    """The collapse M3 found is now inside the production grid on every window.

    At opposition the topocentric distance is exactly ``r - r_obs``, so a hypothesis within
    ``MIN_TOPOCENTRIC_DISTANCE_AU`` of the observer's own heliocentric distance puts every
    tracklet on the observer's own state vector -- the failure mode M3 diagnosed. The same
    thing happens from *below* on the near branch, at zero elongation, where the
    topocentric distance is ``r_obs - r``. Both are checked.
    """
    mjd = np.array([60000.0])
    obs_pos, obs_vel = earth_heliocentric_posvel(mjd)
    r_obs = float(np.linalg.norm(obs_pos[0]))
    sun_hat = obs_pos[0] / r_obs

    for offset in (0.001, 0.01, 0.04):
        for near, direction in ((False, sun_hat), (True, -sun_hat)):
            r = r_obs + offset if not near else r_obs - offset
            _, _, rho, valid = state_from_hypothesis(
                obs_pos, obs_vel, direction[None, :], np.zeros((1, 3)),
                np.array([r]), np.array([0.0]), near=near,
            )
            assert not valid[0], (near, offset, rho)
            assert abs(rho[0]) < MIN_TOPOCENTRIC_DISTANCE_AU


def test_the_widened_grid_fabricates_no_link_out_of_unrelated_objects_near_one_au():
    """Three genuinely different objects must not collapse into one at r ~ 1 AU.

    This is the failure the guard exists to prevent, exercised through the whole
    production path rather than through ``solve_rho`` alone: a grid that steps across the
    observer's own distance every window has hundreds of chances per night to make it.
    """
    rows: list[dict] = []
    nights = [(60000.0, "F51"), (60001.5, "F51"), (60003.0, "F51")]
    for i, (a, e, inc) in enumerate([(1.1, 0.15, 4.0), (2.6, 0.10, 9.0), (3.1, 0.2, 15.0)]):
        rows += _synthetic_observations(f"D{i}", a, e, inc, 60.0 + 40.0 * i, nights)
    arrows = _arrows(rows)

    grid = HypothesisGrid.geometric(0.55, 1.45, fractional_step=0.02)
    links, _ = link_window(arrows.table, grid, radius_au=0.0025)
    for link in links:
        assert len(set(link.desigs)) == 1, link.desigs


# ----------------------------------------------------------------------------------
# Bands
# ----------------------------------------------------------------------------------

def test_the_curvature_rule_reproduces_m3s_fourteen_days_at_the_main_belt():
    assert curvature_window_days(1.4) == pytest.approx(11.5, abs=0.1)
    assert curvature_window_days(2.5) == pytest.approx(20.6, abs=0.1)
    # ...and says plainly that a 14-day window is wrong for an NEO hypothesis.
    assert curvature_window_days(1.0) < 9.0
    assert curvature_window_days(0.5) < 5.0


def test_every_production_band_respects_its_own_curvature_limit_or_says_why():
    """Two bands knowingly exceed the limit at their inner edge, and only two.

    * ``inner`` -- the rule wants 4.5 days and the MPC's 3-day minimum arc needs more, so
      the 5-day floor wins and the model error there is ~1.5x the clustering radius.
    * ``belt`` -- M3's 14 days, kept byte-identical so its numbers stay reproducible. M3
      justified 14 days at 2.5 AU (where the limit is 20.6 days); at the band's 1.4 AU edge
      the limit is 11.5. That is M3's own trade and M4 does not relitigate it.
    """
    known_exceptions = {"inner": 5.0, "belt": 14.0}
    for band in wide_bands():
        limit = curvature_window_days(band.grid.r_au[0])
        if band.label in known_exceptions:
            assert band.window_days == known_exceptions[band.label]
        else:
            assert band.window_days <= limit + 1e-9, band.label
        assert band.window_step_days == pytest.approx(band.window_days / 4.0)


def test_the_band_set_spans_neo_to_tno_and_keeps_m3s_belt_grid_exactly():
    bands = {b.label: b for b in wide_bands()}
    assert bands["inner"].grid.r_au[0] < 0.6
    assert bands["outer"].grid.r_au[-1] > 45.0
    belt = bands["belt"].grid
    assert belt.r_au == belt_band().grid.r_au == HypothesisGrid.build().r_au
    assert bands["belt"].window_days == 14.0


def test_geometric_spacing_is_a_constant_fraction_and_covers_the_range():
    grid = HypothesisGrid.geometric(5.6, 50.0, fractional_step=0.04)
    steps = np.diff(np.asarray(grid.r_au)) / np.asarray(grid.r_au[:-1])
    assert np.allclose(steps, 0.04)
    assert grid.r_au[0] == 5.6
    assert grid.r_au[-1] > 45.0
    with pytest.raises(ValueError):
        HypothesisGrid.geometric(1.0, 2.0, fractional_step=0.0)


def test_an_outer_band_hypothesis_may_imply_a_scattered_disc_orbit():
    """100 AU is a hard rejection of every scattered-disc object, so the ceiling moves."""
    assert {b.label: b.grid.max_a_au for b in wide_bands()}["outer"] > 100.0
    assert {b.label: b.grid.max_a_au for b in wide_bands()}["belt"] == 100.0


# ----------------------------------------------------------------------------------
# What the widening actually buys, on synthetic objects of known orbit
# ----------------------------------------------------------------------------------

def _link_with(bands, rows, radius_au: float = 0.0025):
    return link_bands(_arrows(rows), bands, radius_au=radius_au)[0]


def test_a_tno_is_recovered_by_the_outer_band_and_is_invisible_to_m3s_grid():
    nights = [(60000.0, "F51"), (60006.0, "G96"), (60012.0, "W84")]
    rows = _synthetic_observations("TNO1", 43.0, 0.05, 12.0, 2000.0, nights)
    found = _link_with([b for b in wide_bands() if b.label == "outer"], rows)
    assert len(found) == 1
    assert found[0].r_au > 30.0
    assert _link_with([belt_band()], rows) == []


def test_a_centaur_is_recovered_by_the_outer_band():
    nights = [(60000.0, "F51"), (60005.0, "F51"), (60011.0, "G96")]
    rows = _synthetic_observations("CEN1", 15.0, 0.20, 7.0, 900.0, nights)
    found = _link_with([b for b in wide_bands() if b.label == "outer"], rows)
    assert len(found) == 1
    assert 5.6 < found[0].r_au < 50.0


def test_an_object_interior_to_the_earth_is_recovered_by_the_inner_band():
    """An Atira-class orbit, which is only ever seen with the Sun beyond it.

    Deliberately **not** asserted as "the near branch is required". Measured on this same
    synthetic orbit, sweeping 0.5-0.95 AU at 0.5% steps, the best cluster diameter is
    0.00108 AU on the near branch and 0.00154 AU on the far one -- both inside the 0.0025 AU
    radius. A wrong-branch hypothesis at a wrong distance can still make three tracklets
    agree, which is the same phenomenon M3 documented for ``RL00hfG`` and the reason a
    cluster is never treated as an orbit. What *is* true is that the near root is real
    geometry the far-root-only solver could not express at all, and that M3's 1.4-5.6 AU
    grid cannot reach this object by any route.
    """
    nights = [(60000.0, "F51"), (60001.0, "F51"), (60002.0, "F51")]
    rows = _synthetic_observations("ATIRA1", 0.74, 0.32, 26.0, 40.0, nights)
    if len(_arrows(rows).table) < 3:
        pytest.skip("synthetic Atira not observable from F51 at these epochs")

    inner = Band(
        grid=HypothesisGrid.geometric(0.5, 0.95, fractional_step=0.01, label="inner"),
        window_days=5.0, window_step_days=1.25, label="inner",
    )
    assert _link_with([inner], rows)
    assert _link_with([belt_band()], rows) == []


def test_both_roots_are_distinct_valid_states_for_an_interior_hypothesis():
    """The near root is not a duplicate of the far one -- it is the other half of the space."""
    obs, direction = _sunward_geometry(elongation_deg=25.0)
    rate = np.zeros((1, 3))
    states = {}
    for near in (False, True):
        r_vec, _v, rho, valid = state_from_hypothesis(
            obs, np.array([[0.0, 0.017, 0.0]]), direction, rate,
            np.array([0.7]), np.array([0.0]), near=near,
        )
        assert valid[0]
        states[near] = (r_vec[0], float(rho[0]))
    assert states[True][1] < states[False][1]
    assert np.linalg.norm(states[True][0] - states[False][0]) > 0.1
    for r_vec, _ in states.values():
        assert np.linalg.norm(r_vec) == pytest.approx(0.7, abs=1e-12)


def test_widening_the_grid_does_not_lose_the_main_belt_object_m3_would_have_found():
    nights = [(60000.0, "F51"), (60004.0, "G96"), (60008.0, "W84")]
    rows = _synthetic_observations("MB1", 2.6, 0.12, 8.0, 120.0, nights)
    m3_links = _link_with([belt_band()], rows)
    wide_links = _link_with(wide_bands(), rows)
    assert len(m3_links) == 1
    assert {c.key for c in wide_links} >= {c.key for c in m3_links}


def test_bands_are_labelled_on_the_links_they_produce():
    nights = [(60000.0, "F51"), (60004.0, "G96"), (60008.0, "W84")]
    rows = _synthetic_observations("MB2", 2.9, 0.08, 5.0, 300.0, nights)
    links = _link_with(wide_bands(), rows)
    assert links and all(c.extra.get("band") for c in links)


def test_arrows_beyond_the_grid_do_not_kill_a_whole_hypothesis():
    """One arrow the linear ``r(t)`` model carries inside the Sun must not veto the rest.

    M3 skipped the entire hypothesis in that case, which is free on a 1.4-5.6 AU grid and
    would silently gut the NEO bands.
    """
    ra = np.array([10.0, 10.1, 10.2])
    dec = np.array([5.0, 5.1, 5.2])
    obs_pos, obs_vel = earth_heliocentric_posvel(np.array([60000.0, 60001.0, 60002.0]))
    rho_hat = unit_vectors(ra, dec)
    rho_hat_dot = unit_vector_rates(ra, dec, np.full(3, 0.1), np.full(3, 0.1))
    r_at_t = np.array([0.6, 0.6, 0.001])  # the third is nonsense
    ok = np.array([True, True, False])
    _, _, _, valid = state_from_hypothesis(
        obs_pos, obs_vel, rho_hat, rho_hat_dot,
        np.where(ok, r_at_t, 1.0), np.zeros(3), near=True,
    )
    assert valid[:2].any()


def test_all_three_observatories_are_used_by_the_synthetic_helper():
    """Guards the fixture the rest of this module leans on."""
    assert set(SITES) == {"F51", "G96", "W84"}


# ----------------------------------------------------------------------------------
# Carrying the band through to the fit, and fitting the interesting bands first
# ----------------------------------------------------------------------------------

def test_the_band_and_the_branch_survive_into_the_gated_link_table():
    from itf_linker.link.assemble import links_frame

    nights = [(60000.0, "F51"), (60004.0, "G96"), (60008.0, "W84")]
    rows = _synthetic_observations("MB3", 2.7, 0.10, 6.0, 200.0, nights)
    links = _link_with(wide_bands(), rows)
    frame = links_frame(links)
    assert set(frame["band"].to_list()) <= {"inner", "neo", "belt", "outer"}
    assert "near_branch" in frame.columns
    assert not any(frame["near_branch"].to_list())  # a 2.7 AU object is never near-branch


def test_fitting_order_puts_whole_bands_ahead_of_the_main_belt():
    import polars as pl

    from itf_linker.link.run import prioritise_bands

    frame = pl.DataFrame({"desig": ["a", "b", "c", "d"],
                          "band": ["belt", "outer", "neo", "mystery"]})
    ranked = prioritise_bands(frame, ("neo", "inner", "outer", "belt")).sort("band_priority")
    assert ranked["band"].to_list() == ["neo", "outer", "belt", "mystery"]


def test_one_bands_superset_does_not_delete_another_bands_link():
    """The cross-band merge deduplicates, it does not adjudicate.

    Measured cost of getting this wrong: exact recall on M3's own ground truth fell from
    0.874 to 0.677, because a NEO-band proposal that is the true group *plus one neighbour*
    is a proper superset of the correct belt-band link and deletes it.
    """
    from itf_linker.link.pipeline import merge_links
    from test_link_heliolinc import _fake

    belt = _fake([1, 2, 3], ["F51"])
    belt.extra["band"] = "belt"
    neo = _fake([1, 2, 3, 9], ["F51"])
    neo.extra["band"] = "neo"

    both = merge_links([belt, neo], drop_subset_links=False)
    assert {c.key for c in both} == {belt.key, neo.key}
    # ...whereas inside one band the subset rule still applies, as M3 had it.
    assert {c.key for c in merge_links([belt, neo])} == {neo.key}


def test_a_single_band_run_still_drops_subsets_exactly_as_m3_did():
    nights = [(60000.0, "F51"), (60004.0, "G96"), (60008.0, "W84")]
    rows = _synthetic_observations("MB4", 2.6, 0.12, 8.0, 120.0, nights)
    _, report = link_bands(_arrows(rows), [belt_band()])
    assert report["cross_band_subset_drop"] is True
    _, wide = link_bands(_arrows(rows), wide_bands())
    assert wide["cross_band_subset_drop"] is False


def test_a_link_table_with_no_band_column_still_sorts():
    import polars as pl

    from itf_linker.link.run import prioritise_bands

    out = prioritise_bands(pl.DataFrame({"desig": ["a"]}), ("neo",))
    assert out["band_priority"].to_list() == [0]


def test_the_hashed_isolation_check_agrees_with_the_full_scan_it_replaced():
    """Exactness is the whole claim, so it is tested against the naive implementation.

    Randomised over clustered and uniform point sets, because the failure mode of a
    spatial hash is a *missed* neighbour at a cell boundary and that only shows up when
    points sit near one.
    """
    from itf_linker.link.heliolinc import _neighbours_within

    rng = np.random.default_rng(20260803)
    radius = 0.0025
    for trial in range(25):
        n = int(rng.integers(5, 400))
        if trial % 2:
            centres = rng.normal(0.0, 0.02, size=(6, 6))
            state6 = centres[rng.integers(0, 6, n)] + rng.normal(0.0, radius, size=(n, 6))
        else:
            state6 = rng.normal(0.0, 0.01, size=(n, 6))
        picks = rng.integers(0, n, size=min(n, 12))
        centroids = state6[picks] + rng.normal(0.0, radius / 3, size=(len(picks), 6))

        got = _neighbours_within(centroids, state6, radius)
        for i in range(len(centroids)):
            want = np.flatnonzero(
                np.linalg.norm(state6 - centroids[i], axis=1) <= radius
            )
            assert got[i].tolist() == want.tolist(), (trial, i)


def test_the_isolation_check_still_rejects_a_crowded_neighbourhood():
    """Behaviour, not just the neighbour list: the guard M3 added must still bite."""
    from itf_linker.link.heliolinc import MAX_BALL_MEMBERS, isolated_groups

    rng = np.random.default_rng(7)
    crowd = rng.normal(0.0, 0.0002, size=(MAX_BALL_MEMBERS + 8, 6))
    lonely = np.array([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]) + rng.normal(
        0.0, 0.0002, size=(3, 6)
    )
    state6 = np.vstack([crowd, lonely])
    night = np.array([0, 1, 2] * ((len(state6) + 2) // 3))[: len(state6)]
    slot = np.arange(len(state6))
    groups = [np.array([0, 1, 2]), np.arange(len(crowd), len(state6))]
    kept, rejected = isolated_groups(groups, state6, night, slot, radius_au=0.0025)
    assert rejected == 1
    assert len(kept) == 1
    assert kept[0].tolist() == groups[1].tolist()
