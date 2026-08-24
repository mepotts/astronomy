"""M9: attribute ITF tracklets to the unconsumed Rubin partitions. NOTHING IS SUBMITTED.

The M8 chain (perturbed backend, frozen gate, decoy control, ranked checkpointed fit
queue) pointed at the net-new objects of the six unconsumed bucket partitions
(``scripts/m9_fetch_bulk.py`` -> ``m9-orbits.parquet``), swept against the
**reconstructed 2026-08-16 snapshot** (``scripts/m9_reconstruct_snapshot.py``) so that
M9 candidates live in the same tracklet universe as M8's ledger.

Everything heavy is imported from ``scripts/m8_attribution.py`` unchanged — the gate
envelope is M8's frozen calibration file, the sweep code is byte-identical, the decoy
is the same half-period phase shift. What is new here:

* **Own artifacts**: ``m9-attribution.json``, ``data/m9-fit-state.jsonl``,
  ``data/m9-fits/``, tags ``m9a####``/``m9b####`` — M8's runs stay pristine.
* **Per-partition rollups**: each orbit knows which partitions carried it.
* **The pre-registered stopping rule runs in the loop** (M9-RESULTS.md §0.2, written
  before any fit): tranches of 100 new fits; stop when the trailing-100
  strict+fully-used pass rate < 20/100, or at the hard budget (``--max-new-fits``,
  default 800), whichever first. ``tracklet_lines_missing`` counts as a failure.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m7_attribution as m7run
import m8_attribution as m8run
import polars as pl

from itf_linker import config
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import link_key, tracklet_line_index

ORBITS_PARQUET = ROOT / "data" / "raw" / "rubin" / "m9-orbits.parquet"
RECONSTRUCTED = ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
OUT = ROOT / "m9-attribution.json"

#: M9 fit artifacts — never M8's (m8run module attrs are re-pointed in main()).
FIT_ROOT = ROOT / "data" / "m9-fits"
FIT_STATE = ROOT / "data" / "m9-fit-state.jsonl"

PASS_FLOOR_PER_100 = 20
TRANCHE = 100


def load_orbit_table() -> tuple[pl.DataFrame, dict[str, Any]]:
    df = pl.read_parquet(ORBITS_PARQUET)
    stats: dict[str, Any] = {"rows": df.height}
    keep = df.filter(pl.col("u_param") <= m8run.MAX_U_PARAM)
    stats["u_excluded"] = df.height - keep.height
    stats["swept"] = keep.height
    stats["by_source"] = dict(keep.group_by("source").len().rows())
    hist = dict(sorted(keep.group_by("u_param").len().rows()))
    stats["u_histogram"] = {str(k): v for k, v in hist.items()}
    per_part: dict[str, int] = {}
    for parts in keep["partitions"].to_list():
        for p in parts or []:
            per_part[p] = per_part.get(p, 0) + 1
    stats["swept_by_partition"] = dict(sorted(per_part.items()))
    return keep, stats


def passes_strict_fully_used(outcome: dict[str, Any]) -> bool:
    return bool(
        outcome.get("gate_strict", {}).get("passes")
        and outcome.get("trk_obs_used", 0) == outcome.get("trk_obs_total", -1)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-new-fits", type=int, default=800,
                    help="hard budget (pre-registered: 800)")
    ap.add_argument("--time-budget-min", type=float, default=240.0)
    ap.add_argument("--skip-fits", action="store_true")
    ap.add_argument("--resume-sweep", action="store_true",
                    help="reuse the coarse sweep in an existing m9-attribution.json")
    args = ap.parse_args()

    # Point the shared M8 machinery at M9's artifacts. joint_fit/load_fit_state/
    # append_fit_state read these module attributes at call time.
    m8run.FIT_ROOT = FIT_ROOT
    m8run.FIT_STATE = FIT_STATE
    config.ITF_PARQUET = RECONSTRUCTED

    t_start = time.monotonic()
    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "itf_parquet": str(RECONSTRUCTED),
        "snapshot_reconstruction": json.loads(
            (ROOT / "data" / "raw" / "rubin" / "m9-snapshot-reconstruction.json")
            .read_text(encoding="utf-8")
        )["snapshot_provenance"],
        "parameters": {
            "orbits_parquet": str(ORBITS_PARQUET),
            "max_lookback_days": m8run.MAX_LOOKBACK_DAYS,
            "gate_floor_arcsec": m8run.GATE_FLOOR_ARCSEC,
            "gate_envelope_safety": m8run.GATE_ENVELOPE_SAFETY,
            "max_u_param": m8run.MAX_U_PARAM,
            "backend": "perturbed (M8 frozen calibration envelope)",
            "stopping_rule": {
                "tranche": TRANCHE,
                "trailing_pass_floor_per_100": PASS_FLOOR_PER_100,
                "hard_budget_new_fits": args.max_new_fits,
            },
        },
    }

    if args.resume_sweep and OUT.exists():
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        real = prev["real_matches"]
        report.update({k: prev[k] for k in
                       ("orbits", "tracklets_in_window", "coarse", "sweep_timing",
                        "nights_in_window", "per_partition_coarse")
                       if k in prev})
        report["control_matches_sample"] = prev.get("control_matches_sample", [])
        report["real_matches"] = real
        print(f"resumed sweep: {len(real)} real matches from {OUT.name}", flush=True)
    else:
        df, orbit_stats = load_orbit_table()
        report["orbits"] = orbit_stats
        print(f"orbits: {orbit_stats}", flush=True)
        arrays = m8run.orbit_arrays(df)
        part_by_primary = dict(zip(df["primary"].to_list(),
                                   df["partitions"].to_list()))

        mjd_min = float(arrays["epoch"].min() - m8run.MAX_LOOKBACK_DAYS)
        mjd_max = float(arrays["epoch"].max() + 1.0)
        trk = m7run.load_tracklets(mjd_min, mjd_max)
        report["tracklets_in_window"] = trk.height
        print(f"tracklets in window [{mjd_min:.0f}, {mjd_max:.0f}]: {trk.height}",
              flush=True)

        lon = fetch_obscodes()
        nightindex = m8run.NightIndex(trk, lon)
        report["nights_in_window"] = len(nightindex.night_mjd)
        env = m8run.envelope_fn()

        print("real sweep:", flush=True)
        real, t_real = m8run.run_sweep(arrays, nightindex, env, decoy=False,
                                       label="m9 real")
        print("control sweep (half-period phase shift):", flush=True)
        fake, t_fake = m8run.run_sweep(arrays, nightindex, env, decoy=True,
                                       label="m9 control")
        report["sweep_timing"] = {"real": t_real, "control": t_fake}
        report["coarse"] = {"real": m8run.summarise(real),
                            "control": m8run.summarise(fake)}
        print(json.dumps(report["coarse"], indent=1), flush=True)

        keys = trk.select("desig", "obscode", "night", "n_obs", "mjd_mid",
                          "mag_mean").rows()
        for m in real:
            desig, obscode, night, n_obs, mjd_mid, mag = keys[m["row"]]
            m["trksub"] = desig
            m["obscode"] = obscode
            m["night"] = int(night)
            m["trk_n_obs"] = int(n_obs)
            m["trk_mjd_mid"] = float(mjd_mid)
            m["trk_mag_mean"] = None if mag is None else float(mag)
            m["link_key"] = link_key([(desig, obscode, int(night))])
            m["partitions"] = part_by_primary.get(m["orbit_desig"], [])
            del m["row"]
        for m in fake:
            m.pop("row", None)
        real.sort(key=lambda m: (m["encounter"],
                                 m["sep_arcsec"] / m["gate_radius_arcsec"]))

        per_part: dict[str, dict[str, int]] = {}
        for m in real:
            for p in m["partitions"]:
                d = per_part.setdefault(p, {"coarse": 0, "orbits": 0})
                d["coarse"] += 1
        for p, d in per_part.items():
            d["orbits"] = len(
                {m["orbit_desig"] for m in real if p in m["partitions"]}
            )
        report["per_partition_coarse"] = dict(sorted(per_part.items()))

        report["real_matches"] = real
        report["control_matches_sample"] = fake[:100]
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"sweep written to {OUT.name}; {len(real)} real coarse candidates",
              flush=True)

    if args.skip_fits or not real:
        report["elapsed_s"] = round(time.monotonic() - t_start, 1)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {OUT} in {report['elapsed_s']} s (fits skipped)", flush=True)
        return

    # ---- fit phase: ranked, checkpointed, stopping rule in the loop ----------------
    shell = default_shell()
    lon = fetch_obscodes()
    state = m8run.load_fit_state()
    queue = list(real)
    prefix = args.max_new_fits + sum(
        1 for m in queue if f"{m['orbit_desig']}|{m['link_key']}" in state
    )
    wanted = {m["trksub"] for m in queue[:prefix]}
    index, idx_stats = tracklet_line_index(wanted, lon)
    report["line_index_stats"] = {
        k: v for k, v in idx_stats.items() if not isinstance(v, (list, dict))
    }
    baseline_cache: dict[str, Any] = {}
    base_tags: dict[str, str] = {}
    fits: list[dict[str, Any]] = []
    new_outcomes: list[bool] = []  # pass/fail per NEW fit, rule input
    fit_deadline = time.monotonic() + args.time_budget_min * 60.0
    n_run = n_reused = 0
    stop_reason = "queue_exhausted_within_prefix"
    t_fit_phase = time.monotonic()
    for i, m in enumerate(queue[:prefix]):
        fit_key = f"{m['orbit_desig']}|{m['link_key']}"
        if fit_key in state:
            fits.append({**m, "fit": state[fit_key]["fit"],
                         "fit_tag": state[fit_key].get("fit_tag"), "reused": True})
            n_reused += 1
            continue
        if n_run >= args.max_new_fits:
            stop_reason = f"hard_budget({args.max_new_fits})"
            break
        if time.monotonic() > fit_deadline:
            stop_reason = f"time_budget({args.time_budget_min}min)_after_{n_run}_fits"
            break
        if n_run and n_run % TRANCHE == 0:
            trailing = new_outcomes[-TRANCHE:]
            rate = sum(trailing)
            print(f"[rule] trailing-{TRANCHE} pass rate: {rate}/{TRANCHE}", flush=True)
            if rate < PASS_FLOOR_PER_100:
                stop_reason = (
                    f"trailing_{TRANCHE}_pass_rate({rate})_below_floor({PASS_FLOOR_PER_100})"
                )
                break
        lines = index.get((m["trksub"], m["obscode"], m["night"]))
        tag = f"m9a{i:04d}"  # 7 chars: trkSub field width (M7 trap 5)
        if not lines:
            outcome: dict[str, Any] = {"status": "tracklet_lines_missing"}
        else:
            if m["orbit_desig"] not in base_tags:
                base_tags[m["orbit_desig"]] = f"m9b{len(base_tags):04d}"
            print(f"fit {tag} [{i + 1}/{prefix}]: "
                  f"{m['orbit_desig']} + {m['trksub']}/{m['obscode']}/n{m['night']} "
                  f"sep {m['sep_arcsec']:.0f}\"/{m['gate_radius_arcsec']:.0f}\"",
                  flush=True)
            outcome = m8run.joint_fit(tag, base_tags[m["orbit_desig"]],
                                      m["orbit_desig"], lines, shell, baseline_cache)
        rec = {"fit_key": fit_key, "fit_tag": tag if lines else None, "fit": outcome,
               "orbit_desig": m["orbit_desig"], "trksub": m["trksub"],
               "obscode": m["obscode"], "night": m["night"],
               "link_key": m["link_key"]}
        m8run.append_fit_state(rec)
        state[fit_key] = rec
        fits.append({**m, "fit": outcome, "fit_tag": rec["fit_tag"]})
        new_outcomes.append(passes_strict_fully_used(outcome))
        n_run += 1
        if n_run % 25 == 0:
            report["fits"] = fits
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    fit_phase_s = time.monotonic() - t_fit_phase
    report["fits"] = fits
    report["fit_phase"] = {
        "queued": len(queue),
        "prefix": prefix,
        "run": n_run,
        "reused_from_checkpoint": n_reused,
        "coverage_of_coarse": round(len(fits) / max(len(queue), 1), 4),
        "seconds": round(fit_phase_s, 1),
        "s_per_new_fit": round(fit_phase_s / n_run, 2) if n_run else None,
        "stop_reason": stop_reason,
        "tranche_pass_rates": [
            sum(new_outcomes[k:k + TRANCHE])
            for k in range(0, len(new_outcomes), TRANCHE)
        ],
    }
    passing = [f for f in fits if passes_strict_fully_used(f.get("fit", {}))]
    report["fits_passing_strict_and_fully_used"] = len(passing)
    report["elapsed_s"] = round(time.monotonic() - t_start, 1)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"fits: {len(fits)} ({n_run} new, {n_reused} checkpointed), "
          f"passing strict+fully-used: {len(passing)}; stop: {stop_reason}", flush=True)
    print(f"wrote {OUT} in {report['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
