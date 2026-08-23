"""M11: run both artefact screens against the shell tier. Pre-registered in M11 section 0.7.

M10 built two screens and ran each against only part of what it should cover:

* **`screen_ledger()`** applied the pointed-field screen to ``m8-ledger.json`` and
  ``m9-ledger.json`` -- 735 rows -- and found 0 `POINTED_FIELD`. **No shell row has ever
  been screened**, and the shell is the tier M11 is deciding the status of.
* the **self-designation** identity check was measured across the three ledgers' fitted
  rows (0 of 1,971) but never against the shell's **coarse** head, which is where the
  all-sky sweep's seven hits lived (7 of its top 200). A screen that only ever sees rows
  that already survived a fit cannot find the artefact class it exists to catch, because
  the whole point of the class is that it survives every fit.

So this runs, over the shell tier specifically:

1. self-designation over the shell's coarse ranked **top 2,000**, over all 300 M10 shell
   fitted rows, and over every deep-end fitted row;
2. the pointed-field screen over every shell PASS/BORDERLINE row, with M10's
   pre-declared actions (`POINTED_FIELD` removes a row from the tier;
   `SAME_NIGHT_FIELD` names it).

**The prediction was recorded before the run** (M11 section 0.7): M10 section 6.1 argues
the pointed-field confound is a property of *follow-up*, so a 15-25 y precovery sweep --
proposing tracklets from before the object was discovered -- should flag nothing. If the
shell flags any, that explanation is wrong and the finding is the flag.

Writes ``data/raw/rubin/m11-shell-screens.json``. ``m10-pointed.json`` is not touched.
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

import m10_pointed as screens
import polars as pl

from itf_linker import config
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import tracklet_line_index

COARSE = ROOT / "data" / "raw" / "rubin" / "m11-shell-coarse.parquet"
RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)
OUT = ROOT / "data" / "raw" / "rubin" / "m11-shell-screens.json"


def self_designation_over(rows: list[tuple[str, str]]) -> dict[str, Any]:
    hits = []
    for desig, trksub in rows:
        res = screens.self_designation(desig, trksub)
        if res["self_designation"]:
            hits.append({"orbit_desig": desig, **res})
    return {"n_screened": len(rows), "n_hits": len(hits), "hits": hits}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coarse-top", type=int, default=2000)
    ap.add_argument("--ledgers", nargs="+", required=True,
                    help="shell-tier ledgers to screen (m10-shell-ledger.json, and "
                         "m11-deep-ledger.json once it exists)")
    args = ap.parse_args()

    config.ITF_PARQUET = RECONSTRUCTED
    out: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preregistered": "M11-RESULTS.md section 0.7",
        "prediction": (
            "M10 section 6.1 predicts 0 POINTED_FIELD in a 15-25 y precovery shell, "
            "because the confound is a property of follow-up. Recorded before the run."
        ),
        "screen": {
            "pointed_hours": screens.POINTED_HOURS,
            "same_night_days": screens.SAME_NIGHT_DAYS,
            "dup_epoch_s": screens.DUP_EPOCH_S,
            "dup_pos_arcsec": screens.DUP_POS_ARCSEC,
        },
    }

    # ---- 1. self-designation over the coarse head ----------------------------------
    df = (
        pl.read_parquet(COARSE)
        .with_columns((pl.col("sep_arcsec") / pl.col("gate_radius_arcsec")).alias("sg"))
        .sort(["encounter", "sg"])
        .head(args.coarse_top)
    )
    out["self_designation_coarse_head"] = {
        "top_n": args.coarse_top,
        **self_designation_over(list(zip(df["orbit_desig"], df["trksub"]))),
        "note": ("the population M10's 0-of-1,971 measurement could not cover: rows "
                 "that have not been through a fit yet"),
    }
    print(f"self-designation, coarse top {args.coarse_top}: "
          f"{out['self_designation_coarse_head']['n_hits']} hits", flush=True)

    # ---- 2. both screens over the shell tier's fitted rows -------------------------
    rows: list[dict[str, Any]] = []
    for p in args.ledgers:
        doc = json.loads(Path(p).read_text(encoding="utf-8"))
        for v in doc["verdicts"]:
            rows.append({**v, "ledger": Path(p).stem})
    out["self_designation_fitted"] = {
        **self_designation_over([(v["orbit_desig"], v["trksub"]) for v in rows]),
        "ledgers": list(args.ledgers),
    }
    print(f"self-designation, {len(rows)} shell-tier fitted rows: "
          f"{out['self_designation_fitted']['n_hits']} hits", flush=True)

    keep = [v for v in rows if v["verdict"] in ("PASS", "BORDERLINE")]
    lon = fetch_obscodes()
    idx, _ = tracklet_line_index({v["trksub"] for v in keep}, lon)
    counts = {"POINTED_FIELD": 0, "SAME_NIGHT_FIELD": 0, "DUPLICATE": 0, "clean": 0,
              "no_tracklet_lines": 0, "no_published_record": 0}
    flagged: list[dict[str, Any]] = []
    for v in keep:
        trk = screens.tracklet_obs(idx, (v["trksub"], v["obscode"], int(v["night"])))
        pub = screens.published(v["orbit_desig"])
        if not trk:
            counts["no_tracklet_lines"] += 1
            continue
        if not pub:
            counts["no_published_record"] += 1
            continue
        res = screens.pointed_field_flags(trk, pub)
        if not res["flags"]:
            counts["clean"] += 1
            continue
        for f in res["flags"]:
            counts[f] = counts.get(f, 0) + 1
        flagged.append({"orbit_desig": v["orbit_desig"], "trksub": v["trksub"],
                        "obscode": v["obscode"], "night": v["night"],
                        "ledger": v["ledger"], "verdict": v["verdict"],
                        "dt_years": v.get("dt_years"), **res})
        print(f"  {res['flags']} {v['orbit_desig']:12s} + {v['trksub']:8s} "
              f"{v['obscode']} min_dt={res['min_dt_seconds']}s", flush=True)
    out["pointed_field_shell"] = {
        "n_screened": len(keep), "counts": counts, "flagged": flagged,
        "prediction_held": counts["POINTED_FIELD"] == 0,
    }
    print(json.dumps(counts, indent=1), flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
