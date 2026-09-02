"""M14: sweep authenticated August Rubin orbits against one frozen ITF generation.

The M8 perturbed gate, U<=6 quality cut, 0--15 year calibrated window, half-period
decoy, and strict Find_Orb fit gate remain unchanged.  M14 changes the input discipline:

* both the raw and full-Parquet ITF inputs are one run-local frozen pair;
* the batch/orbit proof from :mod:`m14_prepare` is mandatory;
* every report and fit checkpoint is bound to a complete run fingerprint;
* candidates are deduplicated against M8--M11 by any current orbit alias plus link key;
* same-tracklet/different-orbit collisions are retained and labelled for adjudication;
* missing raw astrometry or unproved published astrometry stops the fit run closed.

All candidate-bearing artifacts stay below gitignored ``data/m14/``.  Only anonymous,
read-only public GETs are used.  Nothing is submitted, published, or sent externally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m7_attribution as m7run
import m8_attribution as m8run
import polars as pl
import requests
from m14_freeze_itf import M14_RUNS, canonical_json_digest, validate_frozen
from m14_prepare import (
    OUT_PARQUET,
    OUT_PROVENANCE,
    M14DataError,
    digest_file,
    file_hashes,
    iso_utc,
    load_prior_coverage,
    utc_now,
    write_json_atomic,
)

from itf_linker import config
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import link_key, tracklet_line_index
from itf_linker.mpc80 import parse_line

CALIBRATION = ROOT / "data" / "raw" / "rubin" / "m8-calibration.json"
MAX_TOTAL_FITS = 400
MAX_TIME_BUDGET_MIN = 90.0
TRANCHE = 100
PASS_FLOOR = 20
M14_RETIRED_REASON = (
    "M14 is retired after its post-run input/provenance and residual-attribution "
    "audits; preserve its historical artifacts and preregister a new milestone"
)
FIT_TAG = "mEa"
BASE_TAG = "mEb"
USER_AGENT = (
    "itf-linker/M14 fit validation "
    "(read-only; contact matthew.e.potts@gmail.com) python-requests"
)


def load_orbit_table() -> tuple[pl.DataFrame, dict[str, Any], dict[str, Any]]:
    if not OUT_PARQUET.is_file() or not OUT_PROVENANCE.is_file():
        raise M14DataError("M14 orbit table/provenance is missing; run m14_prepare.py")
    provenance = json.loads(OUT_PROVENANCE.read_text(encoding="utf-8"))
    if provenance.get("schema") != 1 or not isinstance(provenance.get("output"), dict):
        raise M14DataError("M14 orbit-table provenance has the wrong schema")
    hashes = file_hashes(OUT_PARQUET)
    for key in ("bytes", "sha256"):
        if hashes[key] != provenance["output"].get(key):
            raise M14DataError(f"M14 orbit table failed its {key} proof")
    frame = pl.read_parquet(OUT_PARQUET)
    if frame.height != provenance["output"].get("rows") or frame.height <= 0:
        raise M14DataError("M14 orbit table row count is empty or disagrees with proof")
    if frame["primary"].n_unique() != frame.height:
        raise M14DataError("M14 orbit table contains duplicate primary designations")
    eligible_u = (
        pl.col("u_param").is_not_null()
        & (pl.col("u_param") >= 0)
        & (pl.col("u_param") <= m8run.MAX_U_PARAM)
    )
    keep = frame.filter(eligible_u)
    stats: dict[str, Any] = {
        "rows": frame.height,
        "u_excluded": frame.height - keep.height,
        "swept": keep.height,
        "by_source": dict(keep.group_by("source").len().rows()),
        "u_histogram": {
            str(key): value for key, value in sorted(keep.group_by("u_param").len().rows())
        },
    }
    per_partition: Counter[str] = Counter()
    for memberships in keep["partitions"].to_list():
        if not memberships:
            raise M14DataError("sweepable M14 orbit has no authenticated batch membership")
        per_partition.update(memberships)
    stats["swept_by_partition"] = dict(sorted(per_partition.items()))
    return keep, stats, provenance


def code_proof_paths() -> tuple[Path, ...]:
    return (
        ROOT / "scripts" / "m14_prepare.py",
        ROOT / "scripts" / "m14_freeze_itf.py",
        ROOT / "scripts" / "m14_attribution.py",
        ROOT / "scripts" / "m7_attribution.py",
        ROOT / "scripts" / "m8_attribution.py",
        ROOT / "src" / "itf_linker" / "ingest" / "fetch.py",
        ROOT / "src" / "itf_linker" / "attrib" / "perturbed.py",
        ROOT / "src" / "itf_linker" / "fit" / "findorb.py",
        ROOT / "src" / "itf_linker" / "fit" / "gates.py",
        ROOT / "src" / "itf_linker" / "link" / "assemble.py",
        ROOT / "data" / "raw" / "ObsCodes.html",
        ROOT / "M14-PLAN.md",
    )


def code_proofs() -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): digest_file(path)
        for path in code_proof_paths()
    }


def build_run_contract(
    snapshot: dict[str, Any],
    orbit_provenance: dict[str, Any],
    prior_sources: dict[str, Any],
    *,
    max_total_fits: int,
    time_budget_min: float,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "schema": 1,
        "snapshot_id": snapshot["snapshot_id"],
        "itf_fingerprint": snapshot["fingerprint"],
        "orbit_sha256": orbit_provenance["output"]["sha256"],
        "orbit_provenance_sha256": digest_file(OUT_PROVENANCE),
        "calibration_sha256": digest_file(CALIBRATION),
        "prior_inputs": prior_sources,
        "parameters": {
            "max_lookback_days": m8run.MAX_LOOKBACK_DAYS,
            "min_lookback_days": m8run.MIN_LOOKBACK_DAYS,
            "max_u_param": m8run.MAX_U_PARAM,
            "gate_floor_arcsec": m8run.GATE_FLOOR_ARCSEC,
            "gate_envelope_safety": m8run.GATE_ENVELOPE_SAFETY,
            "decoy": "half-period phase shift",
            "fit_tranche": TRANCHE,
            "trailing_pass_floor": PASS_FLOOR,
            "hard_cap_total_fits": max_total_fits,
            "initial_time_budget_min": time_budget_min,
            "fit_tag_stem": FIT_TAG,
            "baseline_tag_stem": BASE_TAG,
        },
        "code": code_proofs(),
    }
    contract["fingerprint"] = canonical_json_digest(contract)
    return contract


def load_fit_state(path: Path, fingerprint: str) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or document.get("run_fingerprint") != fingerprint:
        raise M14DataError("M14 fit checkpoint belongs to a different input/code contract")
    records = document.get("records")
    if not isinstance(records, dict):
        raise M14DataError("M14 fit checkpoint records are malformed")
    for key, record in records.items():
        if not isinstance(record, dict) or record.get("fit_key") != key:
            raise M14DataError("M14 fit checkpoint contains a malformed record")
    return records


def save_fit_state(
    path: Path,
    records: dict[str, dict[str, Any]],
    fingerprint: str,
) -> None:
    write_json_atomic(
        path,
        {
            "schema": 1,
            "run_fingerprint": fingerprint,
            "updated_utc": iso_utc(utc_now()),
            "records": records,
        },
    )


def passes_strict_fully_used(outcome: dict[str, Any]) -> bool:
    total = outcome.get("trk_obs_total")
    used = outcome.get("trk_obs_used")
    return bool(
        outcome.get("gate_strict", {}).get("passes")
        and isinstance(total, int)
        and isinstance(used, int)
        and total > 0
        and 0 <= used <= total
        and used == total
    )


def fit_stop_exit_code(stop_reason: str) -> int:
    """Return nonzero for incomplete evaluation caused by a proof failure."""

    proof_failure_prefixes = (
        "refused_missing_pinned_tracklet_lines_",
        "input_proof_failure_",
    )
    return 1 if stop_reason.startswith(proof_failure_prefixes) else 0


def refuse_retired_m14_run() -> None:
    """M14 is immutable; repaired attribution belongs to a new preregistration."""

    raise M14DataError(M14_RETIRED_REASON)


def obs80_cache_path(cache: Path, designation: str) -> Path:
    digest = hashlib.sha256(designation.encode("utf-8")).hexdigest()
    return cache / f"{digest}.json"


def get_obs80_proved(cache: Path, designation: str) -> list[str]:
    """Current published astrometry, with an identifier-bound local proof."""
    path = obs80_cache_path(cache, designation)
    if path.exists():
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("schema") != 1 or document.get("requested_desig") != designation:
            raise M14DataError("M14 OBS80 cache request proof mismatch")
        block = document.get("obs80")
        if not isinstance(block, str) or not block.strip():
            raise M14DataError("M14 OBS80 cache contains no astrometry")
        if hashlib.sha256(block.encode("utf-8")).hexdigest() != document.get("sha256"):
            raise M14DataError("M14 OBS80 cache digest mismatch")
    else:
        time.sleep(1.1)
        response = requests.get(
            "https://data.minorplanetcenter.net/api/get-obs",
            json={"desigs": [designation], "output_format": ["OBS80"]},
            headers={"User-Agent": USER_AGENT},
            timeout=(30, 120),
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise M14DataError("MPC get-obs returned malformed JSON") from exc
        row = payload[0] if isinstance(payload, list) and payload else payload
        if not isinstance(row, dict):
            raise M14DataError("MPC get-obs response has no object row")
        block = row.get("OBS80")
        if not isinstance(block, str) or not block.strip():
            raise M14DataError("MPC get-obs returned no published astrometry")
        document = {
            "schema": 1,
            "requested_desig": designation,
            "fetched_utc": iso_utc(utc_now()),
            "sha256": hashlib.sha256(block.encode("utf-8")).hexdigest(),
            "obs80": block,
        }
        write_json_atomic(path, document)
    lines = [line for line in block.splitlines() if line.strip()]
    parsed = [parse_line(line, strict=False) for line in lines]
    if sum(item is not None for item in parsed) < 2:
        raise M14DataError("published OBS80 proof has fewer than two parseable observations")
    return lines


def deduplicate_prior_pairs(
    matches: list[dict[str, Any]],
    orbit_frame: pl.DataFrame,
    prior_pairs: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Drop exact prior orbit-alias/link pairs; retain alternate-orbit collisions."""
    aliases: dict[str, set[str]] = {}
    for row in orbit_frame.select("primary", "matched_provids", "all_desigs").to_dicts():
        names = {row["primary"], *(row["matched_provids"] or []), *(row["all_desigs"] or [])}
        aliases[row["primary"]] = {name for name in names if isinstance(name, str) and name}
    prior_by_link: dict[str, set[str]] = {}
    for orbit, key in prior_pairs:
        prior_by_link.setdefault(key, set()).add(orbit)

    kept: list[dict[str, Any]] = []
    exact_duplicates = alternate_orbit_collisions = 0
    seen: set[tuple[str, str]] = set()
    for match in matches:
        candidate = (match["orbit_desig"], match["link_key"])
        if candidate in seen:
            raise M14DataError("M14 sweep emitted the same orbit/link pair more than once")
        seen.add(candidate)
        current_aliases = aliases.get(match["orbit_desig"], {match["orbit_desig"]})
        prior_orbits = prior_by_link.get(match["link_key"], set())
        exact = bool(current_aliases & prior_orbits)
        alternate = bool(prior_orbits - current_aliases)
        if exact:
            exact_duplicates += 1
            continue
        enriched = dict(match)
        enriched["prior_tracklet_alternate_orbit"] = alternate
        if alternate:
            alternate_orbit_collisions += 1
        kept.append(enriched)
    return kept, {
        "raw_real_matches": len(matches),
        "exact_prior_alias_link_pairs_removed": exact_duplicates,
        "alternate_orbit_same_tracklet_retained": alternate_orbit_collisions,
        "remaining": len(kept),
    }


def write_summary(path: Path, report: dict[str, Any]) -> None:
    summary = {
        "schema": 1,
        "milestone": "M14",
        "generated_utc": iso_utc(utc_now()),
        "run_fingerprint": report["run_fingerprint"],
        "snapshot_id": report["snapshot_id"],
        "orbits": report.get("orbits"),
        "tracklets_in_window": report.get("tracklets_in_window"),
        "nights_in_window": report.get("nights_in_window"),
        "coarse": report.get("coarse"),
        "prior_ledger_dedup": report.get("prior_ledger_dedup"),
        "fit_phase": report.get("fit_phase"),
        "fits_passing_strict_and_fully_used": report.get(
            "fits_passing_strict_and_fully_used", 0
        ),
        "submission_or_publication": False,
        "identifiers_in_summary": False,
    }
    write_json_atomic(path, summary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--max-total-fits", type=int, default=MAX_TOTAL_FITS)
    parser.add_argument("--time-budget-min", type=float, default=MAX_TIME_BUDGET_MIN)
    parser.add_argument("--skip-fits", action="store_true")
    parser.add_argument("--resume-sweep", action="store_true")
    args = parser.parse_args()
    if args.max_total_fits <= 0 or args.max_total_fits > MAX_TOTAL_FITS:
        raise SystemExit(f"--max-total-fits must be in 1..{MAX_TOTAL_FITS}")
    if args.time_budget_min <= 0 or args.time_budget_min > MAX_TIME_BUDGET_MIN:
        raise SystemExit(f"--time-budget-min must be in (0, {MAX_TIME_BUDGET_MIN}]")
    refuse_retired_m14_run()

    run_dir = M14_RUNS / args.snapshot_id
    input_manifest_path = run_dir / "inputs" / "itf-input-manifest.json"
    if not input_manifest_path.is_file():
        raise M14DataError("frozen M14 ITF input is missing; run m14_freeze_itf.py")
    snapshot = validate_frozen(input_manifest_path)
    if snapshot["snapshot_id"] != args.snapshot_id:
        raise M14DataError("frozen ITF snapshot id does not match requested run")
    raw_itf = input_manifest_path.parent / snapshot["raw"]["filename"]
    parquet_itf = input_manifest_path.parent / snapshot["parquet"]["filename"]

    orbit_frame, orbit_stats, orbit_provenance = load_orbit_table()
    _aliases, _objects, prior_pairs, prior_sources = load_prior_coverage()
    contract = build_run_contract(
        snapshot,
        orbit_provenance,
        prior_sources,
        max_total_fits=args.max_total_fits,
        time_budget_min=args.time_budget_min,
    )
    fingerprint = contract["fingerprint"]
    report_path = run_dir / "m14-attribution.json"
    summary_path = run_dir / "m14-attribution-summary.json"
    fit_state_path = run_dir / "m14-fit-state.json"
    fit_root = run_dir / "fits"
    obs80_cache = run_dir / "obs80"
    if not args.resume_sweep and (report_path.exists() or fit_state_path.exists()):
        raise M14DataError(
            "M14 run artifacts already exist; refusing to overwrite them. The recorded "
            "STOP is not a new-run input."
        )

    config.ITF_PARQUET = parquet_itf
    m8run.CALIBRATION = CALIBRATION
    m8run.FIT_ROOT = fit_root
    m8run.FIT_STATE = fit_state_path
    m8run.get_obs80_cached = lambda designation: get_obs80_proved(obs80_cache, designation)

    started = time.monotonic()
    report: dict[str, Any] = {
        "schema": 1,
        "milestone": "M14",
        "generated_utc": iso_utc(utc_now()),
        "snapshot_id": args.snapshot_id,
        "run_fingerprint": fingerprint,
        "run_contract": contract,
        "submission_or_publication": False,
        "orbits": orbit_stats,
    }

    if args.resume_sweep:
        if not report_path.is_file():
            raise M14DataError("--resume-sweep requested but no M14 report exists")
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if previous.get("run_fingerprint") != fingerprint:
            raise M14DataError("M14 sweep report belongs to another run contract")
        real = previous.get("real_matches")
        if not isinstance(real, list):
            raise M14DataError("M14 sweep report has no resumable real-match list")
        for key in (
            "tracklets_in_window", "nights_in_window", "coarse", "sweep_timing",
            "prior_ledger_dedup", "per_partition_coarse", "control_matches_sample",
        ):
            if key in previous:
                report[key] = previous[key]
        report["real_matches"] = real
        print(f"resumed authenticated M14 sweep with {len(real):,} deduplicated matches")
    else:
        arrays = m8run.orbit_arrays(orbit_frame)
        mjd_min = float(arrays["epoch"].min() - m8run.MAX_LOOKBACK_DAYS)
        mjd_max = float(arrays["epoch"].max() + 1.0)
        tracklets = m7run.load_tracklets(mjd_min, mjd_max)
        report["tracklets_in_window"] = tracklets.height
        longitudes = fetch_obscodes()
        night_index = m8run.NightIndex(tracklets, longitudes)
        report["nights_in_window"] = len(night_index.night_mjd)
        envelope = m8run.envelope_fn()

        print(
            f"M14 sweep: {orbit_stats['swept']:,} orbits x "
            f"{tracklets.height:,} tracklets on {len(night_index.night_mjd):,} nights",
            flush=True,
        )
        raw_real, real_timing = m8run.run_sweep(
            arrays, night_index, envelope, decoy=False, label="M14 real"
        )
        decoy, decoy_timing = m8run.run_sweep(
            arrays, night_index, envelope, decoy=True, label="M14 decoy"
        )
        raw_summary = m8run.summarise(raw_real)
        decoy_summary = m8run.summarise(decoy)

        keys = tracklets.select(
            "desig", "obscode", "night", "n_obs", "mjd_mid", "mag_mean"
        ).rows()
        memberships = dict(
            zip(orbit_frame["primary"].to_list(), orbit_frame["partitions"].to_list())
        )
        for match in raw_real:
            designation, obscode, night, n_obs, mjd_mid, magnitude = keys[match["row"]]
            match["trksub"] = designation
            match["obscode"] = obscode
            match["night"] = int(night)
            match["trk_n_obs"] = int(n_obs)
            match["trk_mjd_mid"] = float(mjd_mid)
            match["trk_mag_mean"] = None if magnitude is None else float(magnitude)
            match["link_key"] = link_key([(designation, obscode, int(night))])
            match["partitions"] = memberships.get(match["orbit_desig"], [])
            del match["row"]
        for match in decoy:
            match.pop("row", None)

        real, dedup = deduplicate_prior_pairs(raw_real, orbit_frame, prior_pairs)
        real.sort(
            key=lambda match: (
                match["encounter"],
                match["sep_arcsec"] / match["gate_radius_arcsec"],
                match["orbit_desig"],
                match["link_key"],
            )
        )
        report["prior_ledger_dedup"] = dedup
        report["coarse"] = {
            "real_before_prior_dedup": raw_summary,
            "real_after_prior_dedup": m8run.summarise(real),
            "control": decoy_summary,
        }
        report["sweep_timing"] = {"real": real_timing, "control": decoy_timing}
        report["control_matches_sample"] = decoy[:100]
        report["real_matches"] = real
        per_partition: dict[str, dict[str, int]] = {}
        for match in real:
            for partition in match["partitions"]:
                counts = per_partition.setdefault(partition, {"coarse": 0, "orbits": 0})
                counts["coarse"] += 1
        for partition, counts in per_partition.items():
            counts["orbits"] = len(
                {
                    match["orbit_desig"]
                    for match in real
                    if partition in match["partitions"]
                }
            )
        report["per_partition_coarse"] = dict(sorted(per_partition.items()))
        write_json_atomic(report_path, report)
        write_summary(summary_path, report)
        print(
            f"coarse: {raw_summary.get('n', 0):,} real raw; "
            f"{len(real):,} after prior-ledger dedup; {decoy_summary.get('n', 0):,} decoy",
            flush=True,
        )

    if args.skip_fits or not real:
        report["fit_phase"] = {
            "status": "skipped_by_request" if args.skip_fits else "no_candidates",
            "hard_cap_total_fits": args.max_total_fits,
        }
        report["fits_passing_strict_and_fully_used"] = 0
        report["elapsed_s"] = round(time.monotonic() - started, 2)
        write_json_atomic(report_path, report)
        write_summary(summary_path, report)
        return 0

    shell = default_shell()
    longitudes = fetch_obscodes()
    queue = list(real[: args.max_total_fits])
    wanted_tracklets = {match["trksub"] for match in queue}
    line_index, line_stats = tracklet_line_index(
        wanted_tracklets, longitudes, src=raw_itf
    )
    report["line_index_stats"] = {
        key: value for key, value in line_stats.items() if not isinstance(value, (list, dict))
    }
    state = load_fit_state(fit_state_path, fingerprint)
    baseline_cache: dict[str, Any] = {}
    base_tags: dict[str, str] = {}
    fits: list[dict[str, Any]] = []
    outcomes: list[bool] = []
    new_runs = reused = 0
    stop_reason = "hard_cap_or_queue_exhausted"
    deadline = time.monotonic() + args.time_budget_min * 60.0
    fit_started = time.monotonic()

    for index, match in enumerate(queue):
        if index and index % TRANCHE == 0:
            trailing = outcomes[-TRANCHE:]
            if len(trailing) != TRANCHE:
                raise M14DataError("M14 stopping-rule tranche accounting is incomplete")
            rate = sum(trailing)
            print(f"M14 fit tranche {index // TRANCHE}: {rate}/{TRANCHE} strict+fully-used")
            if rate < PASS_FLOOR:
                stop_reason = f"trailing_{TRANCHE}_pass_rate({rate})_below_floor({PASS_FLOOR})"
                break
        if time.monotonic() > deadline:
            stop_reason = f"time_budget({args.time_budget_min}min)_after_{index}_fits"
            break
        fit_key = f"{match['orbit_desig']}|{match['link_key']}"
        if fit_key in state:
            record = state[fit_key]
            fit = record["fit"]
            fits.append({**match, "fit": fit, "fit_tag": record.get("fit_tag"), "reused": True})
            outcomes.append(passes_strict_fully_used(fit))
            reused += 1
            continue
        lines = line_index.get((match["trksub"], match["obscode"], match["night"]))
        if not lines:
            report["fit_proof_failure"] = {
                "rank": index,
                "error_type": "MissingPinnedTrackletLines",
                "action": "stopped_closed; candidate not fitted or passed",
            }
            stop_reason = f"refused_missing_pinned_tracklet_lines_at_rank_{index}"
            break
        if match["orbit_desig"] not in base_tags:
            base_tags[match["orbit_desig"]] = f"{BASE_TAG}{len(base_tags):04d}"
        tag = f"{FIT_TAG}{index:04d}"
        if len(tag) != 7 or len(base_tags[match["orbit_desig"]]) != 7:
            raise M14DataError("M14 Find_Orb tag is not exactly seven characters")
        try:
            fit = m8run.joint_fit(
                tag,
                base_tags[match["orbit_desig"]],
                match["orbit_desig"],
                lines,
                shell,
                baseline_cache,
            )
        except (requests.RequestException, M14DataError) as exc:
            report["fit_proof_failure"] = {
                "rank": index,
                "error_type": type(exc).__name__,
                "action": "stopped_closed; candidate not fitted or passed",
            }
            stop_reason = f"input_proof_failure_at_rank_{index}"
            break
        record = {
            "fit_key": fit_key,
            "fit_tag": tag,
            "fit": fit,
            "orbit_desig": match["orbit_desig"],
            "trksub": match["trksub"],
            "obscode": match["obscode"],
            "night": match["night"],
            "link_key": match["link_key"],
        }
        state[fit_key] = record
        save_fit_state(fit_state_path, state, fingerprint)
        fits.append({**match, "fit": fit, "fit_tag": tag})
        outcomes.append(passes_strict_fully_used(fit))
        new_runs += 1
        if new_runs % 10 == 0:
            print(
                f"M14 fits completed: {len(fits)}/{len(queue)}; "
                f"strict+fully-used: {sum(outcomes)}",
                flush=True,
            )
        if new_runs % 25 == 0:
            report["fits"] = fits
            write_json_atomic(report_path, report)

    fit_seconds = time.monotonic() - fit_started
    report["fits"] = fits
    report["fit_phase"] = {
        "queue_after_prior_dedup": len(real),
        "hard_cap_total_fits": args.max_total_fits,
        "attempted_prefix": len(queue),
        "completed": len(fits),
        "run_new": new_runs,
        "reused_from_authenticated_checkpoint": reused,
        "coverage_of_deduplicated_coarse": round(len(fits) / max(len(real), 1), 6),
        "seconds": round(fit_seconds, 2),
        "seconds_per_new_fit": round(fit_seconds / new_runs, 3) if new_runs else None,
        "stop_reason": stop_reason,
        "tranche_pass_rates": [
            sum(outcomes[start : start + TRANCHE])
            for start in range(0, len(outcomes), TRANCHE)
        ],
    }
    report["fits_passing_strict_and_fully_used"] = sum(outcomes)
    report["elapsed_s"] = round(time.monotonic() - started, 2)
    write_json_atomic(report_path, report)
    write_summary(summary_path, report)
    print(
        f"M14 fits: {len(fits)} completed, {sum(outcomes)} strict+fully-used; "
        f"stop={stop_reason}",
        flush=True,
    )
    return fit_stop_exit_code(stop_reason)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except M14DataError as error:
        print(f"M14 attribution refused: {error}", file=sys.stderr)
        raise SystemExit(1) from error
