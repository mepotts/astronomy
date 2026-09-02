"""M11: the shell's deep end, sampled by a rank-stratified queue. M11 section 0.6.

M10's shell fit queue was one list ranked by ``sep/gate`` and stopped at 300 by its own
rule. M10 section 9 item 4 asked for a rank-stratified successor on the grounds that the
coarse sweep has 14,717 matches in the 24-25 y bin "that nothing has fitted".

**That premise needs one correction, and this script measures it rather than repeating
it.** M10's global head was not confined to shallow lookbacks: it spans 15.26 to 25.00 y
and already contains 90 fits at 21-25 y. What stopped at -20.74 y was the *yield*, not
the queue -- and those 90 deep fits produced **zero** strict + fully-used passes. So the
question the deep end actually poses is not "has anyone looked" but "is the cliff at
20.7 y real, or an artefact of a single ranked list spending its budget shallow?"

A stratified queue answers that. Five one-year strata (20-21 ... 24-25 y), each ranked by
``sep/gate`` on its own, worked round-robin so no stratum can be starved by another, with
the stopping rule pre-registered in M11 section 0.6 and implemented **in the loop**:

* tranches of 50 new fits (10 per stratum per round); stop when the trailing-50
  fit-grade rate drops below 10/50 -- M10's 20/100 floor at the same rate;
* a stratum producing **0 fit-grade in its first 20 new fits** is closed on its own and
  its share returns to the others;
* hard budget 250 new fits, time backstop 75 minutes.

Rows M10 already fitted are reused from its checkpoint (read-only) and do not consume
budget, and -- like M10's own rule -- the trailing-50 window counts **new** fits only.
Every queued row passes the self-designation identity check before an fo run
(M10 trap 4: check the identity before the fit).

Writes ``m11-deep.json`` in the same shape as ``m10-shell.json`` so
``scripts/m10_verdicts.py`` adjudicates it unchanged. ``m10-shell.json`` and M10's
checkpoint are not written to. Nothing is submitted.
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

import m8_attribution as m8a
import m10_pointed as screens
import polars as pl

from itf_linker import config
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index

COARSE = ROOT / "data" / "raw" / "rubin" / "m11-shell-coarse.parquet"
RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)
M10_FIT_STATE = ROOT / "data" / "m10-shell-fit-state.jsonl"
FIT_STATE = ROOT / "data" / "m11-deep-fit-state.jsonl"
FIT_ROOT = ROOT / "data" / "m11-deep-fits"
OUT = ROOT / "m11-deep.json"

STRATA = [(20, 21), (21, 22), (22, 23), (23, 24), (24, 26)]  # 26 catches |dt| = 25.00 y
PER_ROUND = 10
TRANCHE = 50
TRANCHE_FLOOR = 10
STRATUM_PROBE = 20
STRATUM_PROBE_FLOOR = 1


def fit_grade(fit: dict[str, Any]) -> bool:
    return bool((fit.get("gate_strict") or {}).get("passes")) and (
        fit.get("trk_obs_used") == fit.get("trk_obs_total")
    )


def load_state(path: Path) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                state[rec["fit_key"]] = rec
    return state


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-new-fits", type=int, default=250)
    ap.add_argument("--time-budget-min", type=float, default=75.0)
    ap.add_argument("--per-stratum-cap", type=int, default=400,
                    help="how deep into each stratum's ranked list the queue may go")
    args = ap.parse_args()

    t_start = time.monotonic()
    config.ITF_PARQUET = RECONSTRUCTED
    m8a.FIT_STATE = FIT_STATE
    m8a.FIT_ROOT = FIT_ROOT
    m8a.TAG_FIT = "mCa"
    m8a.TAG_BASE = "mCb"

    df = (
        pl.read_parquet(COARSE)
        .with_columns(
            (pl.col("dt_days").abs() / 365.25).alias("yr"),
            (pl.col("sep_arcsec") / pl.col("gate_radius_arcsec")).alias("sg"),
        )
    )
    queues: dict[str, list[dict[str, Any]]] = {}
    for lo, hi in STRATA:
        label = f"{lo}-{min(hi, 25)}y"
        sub = (df.filter((pl.col("yr") >= lo) & (pl.col("yr") < hi))
                 .sort(["encounter", "sg"])
                 .head(args.per_stratum_cap))
        queues[label] = sub.to_dicts()
        print(f"stratum {label}: {sub.height} queued of "
              f"{df.filter((pl.col('yr') >= lo) & (pl.col('yr') < hi)).height} coarse",
              flush=True)

    # ---- screen before fitting (M10 trap 4) ----------------------------------------
    removed: list[dict[str, Any]] = []
    for label, q in queues.items():
        keep = []
        for m in q:
            sd = screens.self_designation(m["orbit_desig"], m["trksub"])
            if sd["self_designation"]:
                removed.append({"stratum": label, **{k: m[k] for k in
                                ("orbit_desig", "trksub", "obscode", "night",
                                 "sep_arcsec")}, **sd})
            else:
                keep.append(m)
        queues[label] = keep
    print(f"self-designation screen: {len(removed)} removed before any fit", flush=True)

    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preregistered": "M11-RESULTS.md section 0.6",
        "parameters": {
            "itf_parquet": str(config.ITF_PARQUET),
            "strata": [f"{lo}-{min(hi, 25)}y" for lo, hi in STRATA],
            "per_round": PER_ROUND, "tranche": TRANCHE,
            "tranche_floor_per_50": TRANCHE_FLOOR,
            "stratum_probe_fits": STRATUM_PROBE,
            "stratum_probe_floor": STRATUM_PROBE_FLOOR,
            "max_new_fits": args.max_new_fits,
            "time_budget_min": args.time_budget_min,
        },
        "queue_sizes": {k: len(v) for k, v in queues.items()},
        "self_designation_removed": removed,
        "m10_prior": {
            "note": "M10's 300-fit global head already covered these strata; those "
                    "fits are reused from its checkpoint and do not consume budget",
            "state_file": str(M10_FIT_STATE),
        },
    }

    shell = default_shell()
    lon = fetch_obscodes()
    prior = load_state(M10_FIT_STATE)
    state = {**prior, **load_state(FIT_STATE)}
    all_trk = {m["trksub"] for q in queues.values() for m in q}
    index, idx_stats = tracklet_line_index(all_trk, lon)
    report["line_index_stats"] = {
        k: v for k, v in idx_stats.items() if not isinstance(v, (list, dict))
    }

    baseline_cache: dict[str, Any] = {}
    base_tags: dict[str, str] = {}
    fits: list[dict[str, Any]] = []
    new_outcomes: list[bool] = []
    per_stratum: dict[str, dict[str, Any]] = {
        k: {"new": 0, "new_fit_grade": 0, "reused": 0, "reused_fit_grade": 0,
            "cursor": 0, "closed": None}
        for k in queues
    }
    open_strata = list(queues)
    stop_reason = None
    deadline = time.monotonic() + args.time_budget_min * 60.0
    n_run = 0
    seen: set[str] = set()

    while open_strata and stop_reason is None:
        for label in list(open_strata):
            st = per_stratum[label]
            q = queues[label]
            placed = 0
            while placed < PER_ROUND and st["cursor"] < len(q):
                if n_run >= args.max_new_fits:
                    stop_reason = f"hard_budget({args.max_new_fits})"
                    break
                if time.monotonic() > deadline:
                    stop_reason = f"time_budget({args.time_budget_min}min)"
                    break
                m = q[st["cursor"]]
                st["cursor"] += 1
                fit_key = f"{m['orbit_desig']}|{m['link_key']}"
                if fit_key in seen:
                    continue
                seen.add(fit_key)
                if fit_key in state:
                    ok = fit_grade(state[fit_key]["fit"])
                    fits.append({**m, "stratum": label, "fit": state[fit_key]["fit"],
                                 "fit_tag": state[fit_key].get("fit_tag"),
                                 "reused": True})
                    st["reused"] += 1
                    st["reused_fit_grade"] += int(ok)
                    continue
                lines = index.get((m["trksub"], m["obscode"], m["night"]))
                tag = None
                if not lines:
                    outcome: dict[str, Any] = {"status": "tracklet_lines_missing"}
                else:
                    if m["orbit_desig"] not in base_tags:
                        base_tags[m["orbit_desig"]] = (
                            f"{m8a.TAG_BASE}{len(base_tags):04d}"
                        )
                    tag = f"{m8a.TAG_FIT}{n_run:04d}"
                    print(f"deep fit {tag} [{label} #{st['new'] + 1}, "
                          f"{n_run + 1}/{args.max_new_fits}]: {m['orbit_desig']} + "
                          f"{m['trksub']}/{m['obscode']}/n{m['night']} "
                          f"dt {m['dt_days'] / 365.25:+.2f}y "
                          f"sep {m['sep_arcsec']:.0f}\"/"
                          f"{m['gate_radius_arcsec']:.0f}\"", flush=True)
                    outcome = m8a.joint_fit(tag, base_tags[m["orbit_desig"]],
                                            m["orbit_desig"], lines, shell,
                                            baseline_cache)
                rec = {"fit_key": fit_key, "fit_tag": tag, "fit": outcome,
                       "orbit_desig": m["orbit_desig"], "trksub": m["trksub"],
                       "obscode": m["obscode"], "night": m["night"],
                       "link_key": m["link_key"], "stratum": label}
                m8a.append_fit_state(rec)
                state[fit_key] = rec
                ok = fit_grade(outcome)
                fits.append({**m, "stratum": label, "fit": outcome, "fit_tag": tag})
                new_outcomes.append(ok)
                st["new"] += 1
                st["new_fit_grade"] += int(ok)
                n_run += 1
                placed += 1

                # --- the stopping rule, in the loop ---------------------------------
                if (st["new"] >= STRATUM_PROBE
                        and st["new_fit_grade"] < STRATUM_PROBE_FLOOR):
                    st["closed"] = (f"0_fit_grade_in_first_{STRATUM_PROBE}_new_fits")
                    print(f"[rule] stratum {label} closed: "
                          f"{st['new_fit_grade']}/{st['new']} fit-grade", flush=True)
                    if label in open_strata:
                        open_strata.remove(label)
                    break
                if n_run % TRANCHE == 0 and len(new_outcomes) >= TRANCHE:
                    rate = sum(new_outcomes[-TRANCHE:])
                    print(f"[rule] trailing-{TRANCHE} fit-grade: {rate}/{TRANCHE}",
                          flush=True)
                    if rate < TRANCHE_FLOOR:
                        stop_reason = (f"trailing_{TRANCHE}_fit_grade({rate})"
                                       f"_below_floor({TRANCHE_FLOOR})")
                        break
                if n_run % 25 == 0:
                    report["fits"] = fits
                    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            if stop_reason:
                break
            if st["cursor"] >= len(q) and label in open_strata:
                st["closed"] = "queue_exhausted"
                open_strata.remove(label)

    report["fits"] = fits
    report["fit_phase"] = {
        "new": n_run,
        "reused_from_m10": sum(s["reused"] for s in per_stratum.values()),
        "seconds": round(time.monotonic() - t_start, 1),
        "s_per_new_fit": (round((time.monotonic() - t_start) / n_run, 2)
                          if n_run else None),
        "stop_reason": stop_reason or "all_strata_closed",
        "tranche_fit_grade_per_50": [
            sum(new_outcomes[k:k + TRANCHE])
            for k in range(0, len(new_outcomes), TRANCHE)
        ],
    }
    for label, st in per_stratum.items():
        st["total"] = st["new"] + st["reused"]
        st["total_fit_grade"] = st["new_fit_grade"] + st["reused_fit_grade"]
        st["deepest_fit_grade_years"] = max(
            [abs(f["dt_days"]) / 365.25 for f in fits
             if f["stratum"] == label and fit_grade(f.get("fit") or {})] or [0.0]
        ) or None
    report["per_stratum"] = per_stratum
    report["fits_passing_strict_and_fully_used"] = sum(
        1 for f in fits if fit_grade(f.get("fit") or {})
    )
    report["elapsed_s"] = round(time.monotonic() - t_start, 1)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"fit_phase": report["fit_phase"],
                      "per_stratum": per_stratum,
                      "fit_grade": report["fits_passing_strict_and_fully_used"]},
                     indent=2))
    print(f"wrote {OUT} in {report['elapsed_s']} s")


if __name__ == "__main__":
    main()
