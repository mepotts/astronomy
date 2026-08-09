"""Batching, checkpointing and the global merge -- the machinery that makes a
400,000-link fit survivable.

The properties that matter are not about orbits: they are that an interruption loses only
work in flight, that a resumed run does not silently refit or double-count, and that
"a tracklet belongs to one object" is still enforced *across* batches and not merely
inside them.
"""

from __future__ import annotations

import json

import polars as pl

from itf_linker.fit.findorb import FitResult
from itf_linker.fit.pipeline import FitOutcome
from itf_linker.link.run import (
    FitBatch,
    checkpoint_payload,
    fit_links_batched,
    meets_published_quality_limits,
    merge_checkpoints,
    plan_batches,
    rank_survivor_rows,
    rank_survivors,
    resolve_conflicts,
    resolve_conflicts_rows,
)


def _queue(n: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "desig": [f"lnk{i:04d}" for i in range(n)],
            "arrow_ids": [[i, i + 1000] for i in range(n)],
            "n_nights": [3] * n,
            "arc_days": [6.0] * n,
            "obscodes": [["F51", "G96"]] * n,
            "source_desigs": [["a", "b"]] * n,
        }
    )


def _row(desig, *, rms, sigma_a=None, arc=6.0, ids=(1, 2), codes=("F51", "G96"),
         desigs=("a", "b"), population="middle_belt", nights=3, **extra):
    row = {
        "desig": desig, "rms_residual": rms, "sigma_a": sigma_a, "arc_days": arc,
        "arrow_ids": list(ids), "obscodes": list(codes), "source_desigs": list(desigs),
        "population": population, "n_nights": nights, "band": "belt",
    }
    row.update(extra)
    return row


def _outcome(row):
    fit = FitResult(
        desig=row["desig"], converged=True, status="converged",
        rms_residual=row["rms_residual"], sigma_a=row["sigma_a"],
        first_jd=0.0, last_jd=row["arc_days"],
    )
    return FitOutcome(
        desig=row["desig"], fit=fit, n_nights=3, n_obs_submitted=9,
        prefit_arc_days=row["arc_days"], obscodes=list(row["obscodes"]),
        gate_passes=True, gate_reasons=[],
    )


# --- the rule, stated twice, held to one answer ------------------------------------

def test_row_conflict_resolution_matches_the_object_implementation():
    """Two implementations of 'a tracklet belongs to one object' is how the rule drifts."""
    rows = [
        _row("a", rms=0.20, sigma_a=0.01, ids=(1, 2, 3)),
        _row("b", rms=0.10, sigma_a=0.02, ids=(3, 4, 5)),   # better fit, contests arrow 3
        _row("c", rms=0.30, sigma_a=0.03, ids=(6, 7, 8)),
        _row("d", rms=0.15, sigma_a=None, ids=(8, 9)),      # contests arrow 8 with worse RMS
    ]
    kept_rows, dropped_rows = resolve_conflicts_rows(rows)
    outcomes = [_outcome(r) for r in rows]
    kept_obj, dropped_obj = resolve_conflicts(
        outcomes, {r["desig"]: r["arrow_ids"] for r in rows}
    )
    assert [r["desig"] for r in kept_rows] == [o.desig for o in kept_obj]
    assert [r["desig"] for r in dropped_rows] == [o.desig for o in dropped_obj]
    # b (best RMS) takes arrow 3 from a; d (0.15) takes arrow 8 from c (0.30).
    assert [r["desig"] for r in kept_rows] == ["b", "d"]
    assert [r["desig"] for r in dropped_rows] == ["a", "c"]


def test_row_ranking_matches_the_object_implementation():
    rows = [
        _row("same-obs", rms=0.05, codes=("F51", "F51")),
        _row("cross-obs", rms=0.20),
        _row("cross-obs-rederived", rms=0.10, desigs=("a", "a")),
    ]
    by_row = [r["desig"] for r in rank_survivor_rows(rows)]
    meta = {r["desig"]: {"source_desigs": r["source_desigs"]} for r in rows}
    by_obj = [o.desig for o in rank_survivors([_outcome(r) for r in rows], meta)]
    assert by_row == by_obj
    assert by_row[0] == "cross-obs"          # cross-observatory outranks a better RMS


# --- batching ---------------------------------------------------------------------

def test_seeded_links_are_removed_from_the_queue_rather_than_refitted(tmp_path):
    queue = _queue(25)
    seed = FitBatch("m4", queue.head(10), tmp_path / "m4")
    batches = plan_batches(queue, tmp_path / "new", batch_size=10, seed=[seed])
    assert [b.name for b in batches] == ["m4", "b0000", "b0001"]
    assert [b.table.height for b in batches] == [10, 10, 5]
    fresh = [d for b in batches[1:] for d in b.table["desig"].to_list()]
    assert set(fresh).isdisjoint(seed.table["desig"].to_list())
    assert len(fresh) == 15


def test_batching_preserves_the_ranked_order_exactly(tmp_path):
    queue = _queue(97)
    batches = plan_batches(queue, tmp_path, batch_size=20)
    assert [d for b in batches for d in b.table["desig"].to_list()] == queue["desig"].to_list()


def test_a_finished_batch_is_read_back_and_never_refitted(tmp_path):
    """The checkpoint is the contract: a second run must cost a JSON read, not an fo run."""
    calls: list[str] = []
    batches = [FitBatch("b0000", _queue(3), tmp_path / "b0000")]
    (tmp_path / "cp").mkdir()
    (tmp_path / "cp" / "b0000.json").write_text(
        json.dumps({"batch": "b0000", "links_fitted": 3, "passed": []}), encoding="utf-8"
    )

    def explode(*_a, **_k):
        calls.append("fo")
        raise AssertionError("a cached batch must not be refitted")

    import itf_linker.link.run as run_mod

    original, run_mod.fit_links = run_mod.fit_links, explode
    try:
        payloads = fit_links_batched(batches, pl.DataFrame(), {}, tmp_path / "cp", shell=object())
    finally:
        run_mod.fit_links = original
    assert calls == []
    assert payloads[0]["links_fitted"] == 3


def test_a_half_written_checkpoint_is_refitted_rather_than_trusted(tmp_path):
    (tmp_path / "cp").mkdir()
    (tmp_path / "cp" / "b0000.json").write_text('{"batch": "b0000", "links_fi', encoding="utf-8")
    seen: list[str] = []

    def fake_fit_links(table, *_a, **_k):
        seen.append("ran")
        return {"links_submitted": table.height, "links_fitted": table.height, "ranked": []}

    import itf_linker.link.run as run_mod

    original, run_mod.fit_links = run_mod.fit_links, fake_fit_links
    try:
        payloads = fit_links_batched(
            [FitBatch("b0000", _queue(2), tmp_path / "b0000")],
            pl.DataFrame(), {}, tmp_path / "cp", shell=object(),
        )
    finally:
        run_mod.fit_links = original
    assert seen == ["ran"]
    assert payloads[0]["links_fitted"] == 2
    assert json.loads((tmp_path / "cp" / "b0000.json").read_text())["batch"] == "b0000"


def test_the_checkpoint_keeps_every_passing_link_and_drops_the_rest():
    report = {
        "links_submitted": 500, "links_fitted": 500, "converged": 120,
        "rms_le_0.25": 40, "failed_subset_guard": 70, "passed_all_gates": 2,
        "not_converged_reasons": {"no_covariance": 380}, "elapsed_s": 12.0,
        "ranked": [_row("kept", rms=0.1)],
        "conflicted": [_row("contested", rms=0.2)],
        "outcomes": [_row(f"x{i}", rms=9.0) for i in range(500)],
    }
    payload = checkpoint_payload(report, "b0007")
    assert payload["batch"] == "b0007"
    assert [r["desig"] for r in payload["passed"]] == ["kept", "contested"]
    assert "outcomes" not in payload
    assert payload["converged"] == 120


# --- the merge --------------------------------------------------------------------

def test_the_merge_adds_counters_and_resolves_conflicts_across_batch_boundaries():
    """Two batches each proposing a link over arrow 3 is exactly what per-batch resolution
    cannot see, and it is the reason the merge redoes it."""
    a = checkpoint_payload(
        {
            "links_submitted": 100, "links_fitted": 100, "converged": 30, "rms_le_0.25": 8,
            "failed_subset_guard": 12, "passed_all_gates": 1, "elapsed_s": 5.0,
            "not_converged_reasons": {"no_covariance": 70},
            "converged_by_population": {"middle_belt": 30},
            "ranked": [_row("early", rms=0.22, sigma_a=0.01, ids=(1, 2, 3))],
        },
        "b0000",
    )
    b = checkpoint_payload(
        {
            "links_submitted": 100, "links_fitted": 60, "converged": 20, "rms_le_0.25": 5,
            "failed_subset_guard": 9, "passed_all_gates": 1, "elapsed_s": 4.0,
            "not_converged_reasons": {"no_covariance": 35, "unbound": 5},
            "converged_by_population": {"middle_belt": 15, "centaur": 5},
            "ranked": [_row("later", rms=0.09, sigma_a=0.02, ids=(3, 4, 5))],
        },
        "b0001",
    )
    merged = merge_checkpoints([a, b], gated_total=1000)
    assert merged["links_fitted"] == 160
    assert merged["coverage_fraction"] == 0.16
    assert merged["converged"] == 50
    assert merged["not_converged_reasons"] == {"no_covariance": 105, "unbound": 5}
    assert merged["converged_by_population"] == {"middle_belt": 45, "centaur": 5}
    # The better fit takes the contested tracklet even though it arrived a batch later.
    assert [r["desig"] for r in merged["ranked"]] == ["later"]
    assert merged["dropped_by_conflict_resolution"] == 1
    assert merged["survivors"] == 1
    assert merged["survivors_cross_observatory"] == 1


def test_coverage_is_reported_against_the_whole_gated_set_not_the_part_fitted():
    merged = merge_checkpoints(
        [
            checkpoint_payload(
                {
                    "links_fitted": 41, "links_submitted": 41,
                    "extraction": {"links_with_astrometry": 41, "links_without_astrometry": 2},
                },
                "b0",
            )
        ],
        gated_total=412929,
    )
    assert merged["links_fitted"] == 41
    assert merged["gated_total"] == 412929
    assert merged["coverage_fraction"] == round(41 / 412929, 6)
    assert merged["links_unfitted"] == 412929 - 41
    assert merged["links_without_astrometry"] == 2
    assert merged["survivors"] == 0


def test_quality_limits_are_reported_for_every_survivor_not_only_three_night_ones():
    """M4's discipline: our gate never makes a five-night link meet these, and still shows them.

    Five conditions, not four -- ``e < 0.5`` is published and was missing here until
    2026-08-07, which is why ``high_e`` below used to be counted as meeting them all.
    """
    good = _row("tight", rms=0.1, sigma_a=0.01, nights=5, ids=(1, 2),
                sigma_e=0.01, sigma_i=0.1, sigma_q=0.01, e=0.12)
    loose = _row("loose", rms=0.1, sigma_a=24.6, nights=5, ids=(3, 4),
                 sigma_e=0.01, sigma_i=0.1, sigma_q=0.01, e=0.12)
    missing = _row("no-covariance", rms=0.1, sigma_a=0.01, nights=5, e=0.12)
    at_limit = _row("exactly-at-the-limit", rms=0.1, sigma_a=0.05, nights=3,
                    sigma_e=0.01, sigma_i=0.1, sigma_q=0.01, e=0.12)
    high_e = _row("tight-but-eccentric", rms=0.1, sigma_a=0.01, nights=5, ids=(5, 6),
                  sigma_e=0.01, sigma_i=0.1, sigma_q=0.01, e=0.984)
    no_e = _row("eccentricity-unreported", rms=0.1, sigma_a=0.01, nights=5,
                sigma_e=0.01, sigma_i=0.1, sigma_q=0.01)
    assert meets_published_quality_limits(good)
    assert not meets_published_quality_limits(loose)
    assert not meets_published_quality_limits(missing)
    assert not meets_published_quality_limits(at_limit)  # the gate rejects on >=, so this does
    assert not meets_published_quality_limits(high_e)    # tight sigmas, e = 0.984
    assert not meets_published_quality_limits(no_e)      # unreported is not "small"

    merged = merge_checkpoints(
        [checkpoint_payload({"ranked": [good, loose, high_e], "links_fitted": 3}, "b0")],
        gated_total=3,
    )
    assert merged["survivors"] == 3
    assert merged["survivors_meeting_published_quality"] == 1
