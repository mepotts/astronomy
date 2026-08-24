"""M11: price the 15-25 y shell's FIT stage with a decoy. Pre-registered in M11 section 0.5.

M10 section 5.3 named the shell's honest weakness and section 9 item 3 made it the
milestone's recommendation: the half-period phase-shifted control prices the **coarse**
stage (76 real vs 23 decoy under 15 arcsec) and nothing prices the **fit** stage, so the
shell's 71 PASS rows are not separated from chance the way the main tier's are.

The cheap way to do it, and the one pre-registered here, is to run decoy candidates
through the *identical* fit chain at the *identical* ranks and compare fit-grade pass
rates. Two facts about M8's machinery make that more than a one-liner:

* ``run_sweep(decoy=True)`` throws the tracklet identity away -- ``m.pop("row", None)``
  -- and only the first 100 *unranked* decoy matches were ever stored
  (``control_matches_sample``). M10's decoy matches therefore cannot be fitted at all.
  The control has to be re-run, with identity attached this time.
* Because it is re-run, it must be shown to be the *same* control. The reproduction
  check in :func:`check_reproduction` is a gate on the whole result: if the re-run's
  coarse counts do not reproduce M10's (188,494 matches; 3/20/66/274/1185 in the
  sub-120 arcsec bins) then this is a different control and the measurement is void.

Everything downstream of the sweep is M8's, imported rather than reimplemented: the same
``joint_fit`` (the object's real published astrometry plus the decoy-matched tracklet's
verbatim ITF lines, relabelled under one 7-character tag), the same fo build, the same
strict and MPC-published gates, the same baselines. Only the tags and roots differ, so
the real shell's fits and checkpoints stay untouched.

Writes ``m11-shell-decoy.json`` (root, gitignored). Nothing is submitted.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m7_attribution as m7run
import m8_attribution as m8a

from itf_linker import config
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import link_key, tracklet_line_index

ORBITS_UNION = ROOT / "data" / "raw" / "rubin" / "m10-orbits.parquet"
RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)
SHELL_REPORT = ROOT / "m10-shell.json"
OUT = ROOT / "m11-shell-decoy.json"
FIT_STATE = ROOT / "data" / "m11-decoy-fit-state.jsonl"
FIT_ROOT = ROOT / "data" / "m11-decoy-fits"

SHELL_MIN_YEARS = 15.0
SHELL_MAX_YEARS = 25.0

#: M10's measured decoy coarse counts. The re-run must reproduce these or the control
#: is not the same control (M11 section 0.5 item 2).
M10_CONTROL_N = 188494
M10_CONTROL_HIST = {"[0,5)": 3, "[5,15)": 20, "[15,30)": 66, "[30,60)": 274,
                    "[60,120)": 1185}

#: The real arm this prices: M10 section 5.2's 300 fits, 76 fit-grade.
REAL_FITS = 300
REAL_FIT_GRADE = 76


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval; behaves at k = 0 and k = n, unlike the normal one."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def fisher_exact_greater(a: int, b: int, c: int, d: int) -> float:
    """One-sided Fisher p that row 1 has the higher success rate."""
    def lc(n: int, k: int) -> float:
        return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1))

    n = a + b + c + d
    r1, c1 = a + b, a + c
    total = 0.0
    obs = lc(r1, a) + lc(n - r1, c1 - a) - lc(n, c1)
    for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1):
        lp = lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1)
        if x >= a and lp <= obs + 1e-12:
            total += math.exp(lp)
    return min(1.0, total)


def check_reproduction(summary: dict[str, Any]) -> dict[str, Any]:
    """Gate on the whole result (M11 section 0.5 item 2)."""
    hist = summary.get("sep_arcsec_hist", {})
    same_n = summary.get("n") == M10_CONTROL_N
    same_hist = all(hist.get(k) == v for k, v in M10_CONTROL_HIST.items())
    return {
        "m10_control_n": M10_CONTROL_N,
        "rerun_n": summary.get("n"),
        "m10_control_hist": M10_CONTROL_HIST,
        "rerun_hist": {k: hist.get(k) for k in M10_CONTROL_HIST},
        "reproduces": bool(same_n and same_hist),
        "verdict": ("same control" if same_n and same_hist
                    else "DIFFERENT CONTROL -- measurement void"),
    }


def fit_grade(fit: dict[str, Any]) -> bool:
    return bool((fit.get("gate_strict") or {}).get("passes")) and (
        fit.get("trk_obs_used") == fit.get("trk_obs_total")
    )


def strata(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Fit-grade counts by the sub-populations M10 section 5.3's caveats indict."""
    out: dict[str, dict[str, int]] = {}

    def bump(bucket: str, ok: bool) -> None:
        d = out.setdefault(bucket, {"n": 0, "fit_grade": 0})
        d["n"] += 1
        d["fit_grade"] += int(ok)

    for r in rows:
        fit = r.get("fit") or {}
        ok = fit_grade(fit)
        sg = r["sep_arcsec"] / r["gate_radius_arcsec"]
        bump("sep_over_gate " + ("<0.01" if sg < 0.01 else
                                 "0.01-0.02" if sg < 0.02 else
                                 "0.02-0.03" if sg < 0.03 else ">=0.03"), ok)
        bump("sep " + ("<15\"" if r["sep_arcsec"] < 15 else
                       "15-60\"" if r["sep_arcsec"] < 60 else
                       "60-120\"" if r["sep_arcsec"] < 120 else ">=120\""), ok)
        n = r.get("trk_n_obs") or 0
        bump(f"trk_n_obs {'2' if n <= 2 else '3' if n == 3 else '4+'}", ok)
        bump("station " + str(r["obscode"]), ok)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-fits", type=int, default=REAL_FITS,
                    help="pre-registered at 300: the same count and the same ranks as "
                         "the real shell queue")
    ap.add_argument("--time-budget-min", type=float, default=75.0)
    ap.add_argument("--resume", action="store_true",
                    help="reuse the decoy sweep in an existing m11-shell-decoy.json")
    args = ap.parse_args()

    t_start = time.monotonic()

    # ---- the substitutions: M10 section 0.2's, verbatim ----------------------------
    config.ITF_PARQUET = RECONSTRUCTED
    m8a.ORBITS_PARQUET = ORBITS_UNION
    m8a.CALIBRATION = ROOT / "data" / "raw" / "rubin" / "m9-calibration.json"
    m8a.CALIBRATION_KEY = "perturbed_envelope_arcsec_mainbelt_25y"
    m8a.MIN_LOOKBACK_DAYS = SHELL_MIN_YEARS * 365.25
    m8a.MAX_LOOKBACK_DAYS = SHELL_MAX_YEARS * 365.25
    m8a.FIT_STATE = FIT_STATE
    m8a.FIT_ROOT = FIT_ROOT
    m8a.TAG_FIT = "mBa"
    m8a.TAG_BASE = "mBb"

    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preregistered": "M11-RESULTS.md section 0.5",
        "arm": "decoy (half-period phase shift), 15 y < |dt| <= 25 y",
        "parameters": {
            "itf_parquet": str(config.ITF_PARQUET),
            "orbits": str(ORBITS_UNION),
            "calibration_key": m8a.CALIBRATION_KEY,
            "min_lookback_days": m8a.MIN_LOOKBACK_DAYS,
            "max_lookback_days": m8a.MAX_LOOKBACK_DAYS,
            "gate_floor_arcsec": m8a.GATE_FLOOR_ARCSEC,
            "gate_envelope_safety": m8a.GATE_ENVELOPE_SAFETY,
            "max_u_param": m8a.MAX_U_PARAM,
        },
        "real_arm": {"fits": REAL_FITS, "fit_grade": REAL_FIT_GRADE,
                     "source": "M10-RESULTS.md section 5.2 / m10-shell.json"},
    }

    if args.resume and OUT.exists():
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        matches = prev["decoy_matches"]
        report["coarse"] = prev["coarse"]
        report["reproduction_check"] = prev["reproduction_check"]
        report["sweep_timing"] = prev.get("sweep_timing")
        print(f"resumed: {len(matches)} decoy matches", flush=True)
    else:
        df, orbit_stats = m8a.load_orbit_table()
        report["orbits"] = orbit_stats
        print(f"orbits: {orbit_stats}", flush=True)
        arrays = m8a.orbit_arrays(df)

        mjd_min = float(arrays["epoch"].min() - m8a.MAX_LOOKBACK_DAYS)
        mjd_max = float(arrays["epoch"].max() + 1.0)
        trk = m7run.load_tracklets(mjd_min, mjd_max)
        report["tracklets_in_window"] = trk.height
        print(f"tracklets in window: {trk.height}", flush=True)

        lon = fetch_obscodes()
        nightindex = m8a.NightIndex(trk, lon)
        report["nights_in_window"] = len(nightindex.night_mjd)
        env = m8a.envelope_fn()

        print("decoy sweep (half-period phase shift):", flush=True)
        fake, timing = m8a.run_sweep(arrays, nightindex, env, decoy=True,
                                     label="control")
        report["sweep_timing"] = timing
        report["coarse"] = m8a.summarise(fake)
        report["reproduction_check"] = check_reproduction(report["coarse"])
        print(json.dumps(report["reproduction_check"], indent=1), flush=True)

        # The line M8 does not have: attach tracklet identity to the DECOY matches so
        # they can be fitted. Identical to the real arm's attachment.
        keys = trk.select("desig", "obscode", "night", "n_obs", "mjd_mid",
                          "mag_mean").rows()
        for m in fake:
            desig, obscode, night, n_obs, mjd_mid, mag = keys[m["row"]]
            m["trksub"] = desig
            m["obscode"] = obscode
            m["night"] = int(night)
            m["trk_n_obs"] = int(n_obs)
            m["trk_mjd_mid"] = float(mjd_mid)
            m["trk_mag_mean"] = None if mag is None else float(mag)
            m["link_key"] = link_key([(desig, obscode, int(night))])
            del m["row"]
        # The identical rank key the real arm used.
        fake.sort(key=lambda m: (m["encounter"],
                                 m["sep_arcsec"] / m["gate_radius_arcsec"]))
        matches = fake[: max(args.max_fits * 4, 2000)]
        report["decoy_matches"] = matches
        report["decoy_matches_stored"] = len(matches)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"decoy sweep written; {report['coarse']['n']} matches, "
              f"top {len(matches)} kept for the fit stage", flush=True)

    if not report["reproduction_check"]["reproduces"]:
        report["result"] = "VOID: the re-run is not the same control"
        report["elapsed_s"] = round(time.monotonic() - t_start, 1)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("REPRODUCTION CHECK FAILED -- not fitting; measurement void", flush=True)
        return

    # ---- fit stage: M8's chain, same ranks, same gates -----------------------------
    shell = default_shell()
    lon = fetch_obscodes()
    state = m8a.load_fit_state()
    queue = matches[: args.max_fits]
    wanted = {m["trksub"] for m in queue}
    index, idx_stats = tracklet_line_index(wanted, lon)
    report["line_index_stats"] = {
        k: v for k, v in idx_stats.items() if not isinstance(v, (list, dict))
    }

    baseline_cache: dict[str, Any] = {}
    base_tags: dict[str, str] = {}
    fits: list[dict[str, Any]] = []
    new_outcomes: list[bool] = []
    stop_reason = None
    deadline = time.monotonic() + args.time_budget_min * 60.0
    n_run = n_reused = 0
    t_fit = time.monotonic()
    for i, m in enumerate(queue):
        fit_key = f"{m['orbit_desig']}|{m['link_key']}"
        if fit_key in state:
            fits.append({**m, "fit": state[fit_key]["fit"],
                         "fit_tag": state[fit_key].get("fit_tag"), "reused": True})
            n_reused += 1
            continue
        if time.monotonic() > deadline:
            stop_reason = f"time_budget({args.time_budget_min}min)"
            break
        lines = index.get((m["trksub"], m["obscode"], m["night"]))
        tag = None
        if not lines:
            outcome: dict[str, Any] = {"status": "tracklet_lines_missing"}
        else:
            if m["orbit_desig"] not in base_tags:
                base_tags[m["orbit_desig"]] = f"{m8a.TAG_BASE}{len(base_tags):04d}"
            tag = f"{m8a.TAG_FIT}{i:04d}"
            print(f"decoy fit {tag} [{i + 1}/{len(queue)}]: {m['orbit_desig']} + "
                  f"{m['trksub']}/{m['obscode']}/n{m['night']} "
                  f"sep {m['sep_arcsec']:.0f}\"/{m['gate_radius_arcsec']:.0f}\"",
                  flush=True)
            outcome = m8a.joint_fit(tag, base_tags[m["orbit_desig"]],
                                    m["orbit_desig"], lines, shell, baseline_cache)
        rec = {"fit_key": fit_key, "fit_tag": tag, "fit": outcome,
               "orbit_desig": m["orbit_desig"], "trksub": m["trksub"],
               "obscode": m["obscode"], "night": m["night"],
               "link_key": m["link_key"]}
        m8a.append_fit_state(rec)
        state[fit_key] = rec
        fits.append({**m, "fit": outcome, "fit_tag": tag})
        new_outcomes.append(fit_grade(outcome))
        n_run += 1
        if n_run % 25 == 0:
            report["fits"] = fits
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    report["fits"] = fits
    n_grade = sum(1 for f in fits if fit_grade(f.get("fit") or {}))
    lo, hi = wilson(n_grade, len(fits))
    rlo, rhi = wilson(REAL_FIT_GRADE, REAL_FITS)
    p = fisher_exact_greater(REAL_FIT_GRADE, REAL_FITS - REAL_FIT_GRADE,
                             n_grade, len(fits) - n_grade)
    ratio = ((REAL_FIT_GRADE / REAL_FITS) / (n_grade / len(fits))
             if fits and n_grade else None)
    rate = n_grade / len(fits) if fits else 0.0
    if rate >= REAL_FIT_GRADE / REAL_FITS:
        band = "no separation -- shell tier demoted (M11 section 0.5 row 1)"
    elif rate >= 0.5 * REAL_FIT_GRADE / REAL_FITS:
        band = "under 2x -- not submission-grade at any rank (row 2)"
    elif rate > REAL_FIT_GRADE / REAL_FITS / 3.0:
        band = "weakly separated -- nothing promoted (row 3)"
    else:
        band = "separated (>= 3x) -- subject to M10 section 5.3's caveats (row 4)"

    report["fit_phase"] = {
        "queued": len(queue),
        "run": n_run,
        "reused_from_checkpoint": n_reused,
        "seconds": round(time.monotonic() - t_fit, 1),
        "s_per_new_fit": round((time.monotonic() - t_fit) / n_run, 2) if n_run else None,
        "stop_reason": stop_reason or "cap_or_queue_end",
        "tranche_pass_rates_per_100": [
            sum(new_outcomes[k:k + 100]) for k in range(0, len(new_outcomes), 100)
        ],
    }
    report["result"] = {
        "decoy_fits": len(fits),
        "decoy_fit_grade": n_grade,
        "decoy_rate": round(rate, 4),
        "decoy_rate_ci95": [round(lo, 4), round(hi, 4)],
        "real_fits": REAL_FITS,
        "real_fit_grade": REAL_FIT_GRADE,
        "real_rate": round(REAL_FIT_GRADE / REAL_FITS, 4),
        "real_rate_ci95": [round(rlo, 4), round(rhi, 4)],
        "real_over_decoy": round(ratio, 2) if ratio else None,
        "fisher_one_sided_p_real_gt_decoy": p,
        "preregistered_band": band,
    }
    report["strata_decoy"] = strata(fits)
    report["elapsed_s"] = round(time.monotonic() - t_start, 1)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["result"], indent=2))
    print(f"wrote {OUT} in {report['elapsed_s']} s")


if __name__ == "__main__":
    main()
