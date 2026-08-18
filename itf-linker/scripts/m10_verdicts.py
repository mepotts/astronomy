"""M10: the verdict chain over the 15-25 y shell fits — appends, never rewrites.

The chain is ``scripts/m8_verdicts.py``'s exactly (its functions are imported, its
constants unchanged): the "did fo actually use the tracklet" primary gate, the duplicate
check against the object's published record, the strict and published gates, and the
SkyBoT cone search with the frozen informative-claimant rule. Nothing about the shell
justifies a different standard, so nothing about the shell gets one.

Two things are added, both because the shell is a *new* window rather than more of an
old one:

* **Liveness against the same pull the ledger refresh used**, so a shell candidate and a
  M8/M9 candidate mean the same thing by "still live".
* **A same-station-cluster note.** 52 of the shell's 76 fit-grade passes come from one
  observatory (705, Palomar). Cross-observatory tracklets are the ITF's distinctive
  value (M3 onward ranks them first) and a single survey's own unlinked archive is a
  weaker proposition than a genuine cross-match. The verdict does not change; the row
  says which it is, so the reviewer can weigh it.

Writes ``m10-shell-ledger.json``. ``m8-ledger.json`` and ``m9-ledger.json`` are not
touched.
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

import m8_verdicts as m8v
import polars as pl

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index
from itf_linker.mpc80 import parse_line
from itf_linker.vet.cache import CachedSession

REPORT = ROOT / "m10-shell.json"
ORBITS = ROOT / "data" / "raw" / "rubin" / "m10-orbits.parquet"
VET_CACHE = ROOT / "data" / "vet-cache"
OUT = ROOT / "m10-shell-ledger.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fresh-slim", type=Path, required=True,
                    help="the same pull m10_refresh.py used, so 'still live' means one "
                         "thing across the whole review queue")
    args = ap.parse_args()

    fits = json.loads(REPORT.read_text(encoding="utf-8")).get("fits") or []
    print(f"shell fits to adjudicate: {len(fits)}", flush=True)

    lon = fetch_obscodes()
    lon_df = pl.DataFrame({"obscode": list(lon.keys()),
                           "lon_deg": [v - 360.0 if v > 180.0 else v
                                       for v in lon.values()]})
    live = set(
        pl.scan_parquet(args.fresh_slim)
        .filter(pl.col("desig").is_in([f["trksub"] for f in fits]))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns((pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
                      .floor().cast(pl.Int32).alias("night"))
        .select("desig", "obscode", "night")
        .unique()
        .collect()
        .rows()
    )

    index, _ = tracklet_line_index({f["trksub"] for f in fits}, lon)
    session = CachedSession(VET_CACHE)
    odf = pl.read_parquet(ORBITS, columns=["primary", "all_desigs"])
    desigs = dict(zip(odf["primary"].to_list(), odf["all_desigs"].to_list()))

    # How many of THIS run's passes each object and each station carries: the
    # same-station-cluster note needs the whole population, so count first.
    def is_fit_grade(f: dict[str, Any]) -> bool:
        fit = f.get("fit") or {}
        return bool((fit.get("gate_strict") or {}).get("passes")) and (
            fit.get("trk_obs_used") == fit.get("trk_obs_total")
        )

    per_object: dict[str, list[dict[str, Any]]] = {}
    for f in fits:
        if is_fit_grade(f):
            per_object.setdefault(f["orbit_desig"], []).append(f)

    verdicts: list[dict[str, Any]] = []
    n_skybot = 0
    for f in fits:
        fit = f.get("fit") or {}
        key = (f["trksub"], f["obscode"], f["night"])
        trk_lines = index.get(key) or []
        pub = m8v.published_obs(f["orbit_desig"])
        dup = m8v.count_duplicates(trk_lines, pub) if trk_lines else 0
        n_trk = fit.get("trk_obs_total") or len(
            [ln for ln in trk_lines if parse_line(ln, strict=False)]
        )

        reasons: list[str] = []
        skybot: dict[str, Any] | None = None
        if dup and n_trk and dup >= n_trk:
            verdict = "ALREADY_LINKED"
        else:
            if dup:
                reasons.append(f"partial_duplicate({dup}/{n_trk})")
            if fit.get("trk_obs_used") != fit.get("trk_obs_total"):
                reasons.append(
                    f"tracklet_not_fully_used({fit.get('trk_obs_used')}/"
                    f"{fit.get('trk_obs_total')})"
                )
            if not fit.get("converged"):
                reasons.append(f"not_converged({fit.get('status')})")
            gate = fit.get("gate_strict") or {}
            if not gate.get("passes"):
                reasons.append("strict_gate:" + "; ".join(gate.get("reasons") or ["?"]))
            n_obs, n_used = fit.get("n_obs") or 0, fit.get("n_used") or 0
            if not n_obs or n_used / n_obs < m8v.MIN_USED_FRACTION:
                reasons.append(f"joint_set_not_used({n_used}/{n_obs})")

            published_ok = bool((fit.get("gate_mpc_published") or {}).get("passes"))
            rms = fit.get("rms_joint")
            only_strict_failed = (
                reasons
                and all(r.startswith("strict_gate:") for r in reasons)
                and published_ok
                and rms is not None
                and rms <= 0.25 + m8v.BORDERLINE_RMS_ARCSEC
            )
            verdict = ("PASS" if not reasons
                       else "BORDERLINE" if only_strict_failed else "FAIL")

            if verdict in ("PASS", "BORDERLINE") and trk_lines:
                skybot = m8v.skybot_check(session, trk_lines, f["orbit_desig"],
                                          desigs.get(f["orbit_desig"], []))
                n_skybot += 1
                if skybot.get("conflicts"):
                    verdict = "SKYBOT_CONFLICT"
                    reasons.append("skybot_conflict:" + "; ".join(
                        f"{c['name']} at {c['sep_arcsec']}\"" for c in skybot["conflicts"]
                    ))
                elif skybot.get("status") != "ok":
                    reasons.append(f"skybot_{skybot.get('status')}")
                if skybot.get("lost_object_ambiguity"):
                    reasons.append("skybot_lost_object_ambiguity:" + "; ".join(
                        f"{c['name']} (err {c['ephem_err_arcsec']}\")"
                        for c in skybot["lost_object_ambiguity"][:3]
                    ))

        siblings = per_object.get(f["orbit_desig"], [])
        stations = sorted({s["obscode"] for s in siblings})
        verdicts.append({
            "provenance": "M10-shell",
            "orbit_desig": f["orbit_desig"],
            "trksub": f["trksub"],
            "obscode": f["obscode"],
            "night": f["night"],
            "link_key": f.get("link_key"),
            "sep_arcsec": round(f["sep_arcsec"], 1),
            "gate_radius_arcsec": round(f.get("gate_radius_arcsec", 0.0), 1),
            "dt_days": round(f["dt_days"], 1),
            "dt_years": round(f["dt_days"] / 365.25, 2),
            "encounter": bool(f.get("encounter")),
            "rms_joint": fit.get("rms_joint"),
            "rms_baseline": (fit.get("baseline") or {}).get("rms"),
            "trk_obs_used": fit.get("trk_obs_used"),
            "trk_obs_total": n_trk,
            "duplicates_in_published": dup,
            "verdict": verdict,
            "reasons": reasons,
            "mpc_published_gate_passes": (fit.get("gate_mpc_published") or {}).get("passes"),
            "skybot": skybot,
            "fit_tag": f.get("fit_tag"),
            "still_live": key in live,
            "sibling_passes_on_object": len(siblings),
            "sibling_stations": stations,
            "cross_observatory": len(stations) > 1,
        })

    counts: dict[str, int] = {}
    for v in verdicts:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    passes = [v for v in verdicts if v["verdict"] == "PASS"]
    ledger = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generated_from": REPORT.name,
        "window": "15 y < |dt| <= 25 y (M10-RESULTS.md section 0.2)",
        "ledgers_untouched": ["m8-ledger.json", "m9-ledger.json"],
        "rules": {
            "note": "identical to m8-ledger.json rules; nothing loosened",
            "dup_epoch_s": m8v.DUP_EPOCH_S,
            "dup_pos_arcsec": m8v.DUP_POS_ARCSEC,
            "min_used_fraction": m8v.MIN_USED_FRACTION,
            "borderline_rms_arcsec": m8v.BORDERLINE_RMS_ARCSEC,
            "skybot_claimant_max_err_arcsec": m8v.SKYBOT_CLAIMANT_MAX_ERR_ARCSEC,
        },
        "counts": counts,
        "skybot_calls": n_skybot,
        "pass_objects": len({v["orbit_desig"] for v in passes}),
        "pass_still_live": sum(1 for v in passes if v["still_live"]),
        "pass_cross_observatory": sum(1 for v in passes if v["cross_observatory"]),
        "pass_by_station": {
            s: sum(1 for v in passes if v["obscode"] == s)
            for s in sorted({v["obscode"] for v in passes})
        },
        "verdicts": verdicts,
    }
    OUT.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"M10 shell verdicts: {json.dumps(counts)}; SkyBoT calls: {n_skybot}")
    for v in verdicts:
        if v["verdict"] != "FAIL":
            print(f"{v['verdict']:16s} {v['orbit_desig']:12s} + {v['trksub']:8s} "
                  f"{v['obscode']} n{v['night']} dt {v['dt_years']:+6.2f}y "
                  f"sep {v['sep_arcsec']:7.1f}\"/{v['gate_radius_arcsec']:.0f}\" "
                  f"rms {v['rms_joint']} used {v['trk_obs_used']}/{v['trk_obs_total']}"
                  f" sib {v['sibling_passes_on_object']}"
                  f"{' XSURVEY' if v['cross_observatory'] else ''}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
