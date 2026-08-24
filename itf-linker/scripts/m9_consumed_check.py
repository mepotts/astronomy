"""M9: where did the consumed M8 candidates go? An involuntary external validation.

Between M8's ITF pull (2026-08-16) and M9's (2026-08-18), the MPC consumed 22,353 ITF
observations. 30 of M8's 900 fitted candidates — 21 ledger PASSes, 8 FAILs, 1
ALREADY_LINKED — involve tracklets in that consumed set. The MPC does not say where a
consumed tracklet went, but the objects' *published records* do: if a PASS tracklet's
observations now appear under the same object M8 attributed them to, the MPC
independently made the identical link two days after the ledger proposed it — ground
truth for the attribution chain that did not exist when M8 ran (and those candidates
become moot for submission). If they appear nowhere, the consumption went elsewhere
and the candidate is evidence of a *disagreement* worth naming.

Method, per consumed fitted candidate:

1. The tracklet's exact observation epochs come from the archive's slim 08-16 table
   (desig, obscode, mjd — the tracklet's own rows, by the sweep's night definition).
2. Its astrometry comes from the M8 fit directory's ``obs.txt`` (the verbatim relabelled
   80-column lines fo actually fitted), matched to those epochs.
3. The object's **fresh** published record is fetched live (get-obs, paced) into a
   separate cache (``obs80-m9fresh/``) — the M8-era ``obs80/`` cache is deliberately
   left untouched: M8's fits used it, and M9's combined fits must keep using it so a
   tracklet consumed *into* an object is never double-counted as tracklet + published.
4. An observation "went to this object" if the fresh record has a row at the same
   obscode within 2 s and 2 arcsec (the ledger's duplicate rule).

Writes ``data/raw/rubin/m9-consumed-check.json``.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl
import requests

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.mpc80 import parse_line

DROPPED = ROOT / "data" / "raw" / "rubin" / "m9-dropped-tracklets.parquet"
SLIM = ROOT / "data" / "snapshots" / "20260816T202701Z" / "observations.parquet"
FIT_STATE = ROOT / "data" / "m8-fit-state.jsonl"
LEDGER = ROOT / "m8-ledger.json"
FIT_ROOT = ROOT / "data" / "m8-fits"
FRESH_CACHE = ROOT / "data" / "raw" / "rubin" / "obs80-m9fresh"
OUT = ROOT / "data" / "raw" / "rubin" / "m9-consumed-check.json"

OBS_URL = "https://data.minorplanetcenter.net/api/get-obs"
USER_AGENT = (
    "itf-linker/0.4 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

DUP_EPOCH_S = 2.0
DUP_POS_ARCSEC = 2.0


def get_obs80_fresh(desig: str) -> list[str]:
    FRESH_CACHE.mkdir(parents=True, exist_ok=True)
    dest = FRESH_CACHE / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not dest.exists():
        time.sleep(1.1)
        resp = requests.get(
            OBS_URL,
            json={"desigs": [desig], "output_format": ["OBS80"]},
            headers={"User-Agent": USER_AGENT},
            timeout=120,
        )
        resp.raise_for_status()
        doc = resp.json()
        block = (doc[0] if isinstance(doc, list) else doc).get("OBS80") or ""
        dest.write_text(block, encoding="utf-8", newline="\n")
    return [ln for ln in dest.read_text(encoding="utf-8").splitlines() if ln.strip()]


def main() -> None:
    dropped = pl.read_parquet(DROPPED)
    dset = set(zip(dropped["desig"].to_list(), dropped["obscode"].to_list(),
                   dropped["night"].to_list()))
    state = [json.loads(l) for l in FIT_STATE.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    consumed = [r for r in state if (r["trksub"], r["obscode"], r["night"]) in dset]

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    verdict_by_key = {
        (v["orbit_desig"], v["link_key"]): v["verdict"] for v in ledger["verdicts"]
    }

    # night per slim row, load_tracklets' formula
    lon = fetch_obscodes()
    lon_df = pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )
    slim = (
        pl.scan_parquet(SLIM)
        .filter(pl.col("desig").is_in([r["trksub"] for r in consumed]))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
        .collect()
    )

    rows: list[dict[str, Any]] = []
    for r in consumed:
        mjds = (
            slim.filter(
                (pl.col("desig") == r["trksub"])
                & (pl.col("obscode") == r["obscode"])
                & (pl.col("night") == r["night"])
            )["mjd"].to_list()
        )
        # astrometry from the fit dir's obs.txt (verbatim lines fo fitted)
        trk_obs = []
        tag = r.get("fit_tag")
        obs_txt = FIT_ROOT / tag / "obs.txt" if tag else None
        if obs_txt and obs_txt.exists():
            for ln in obs_txt.read_text(encoding="utf-8", errors="replace").splitlines():
                o = parse_line(ln, strict=False)
                if o and o.obscode == r["obscode"] and any(
                    abs(o.mjd - m) < 2e-4 for m in mjds
                ):
                    trk_obs.append(o)

        pub = [o for o in (parse_line(ln, strict=False)
                           for ln in get_obs80_fresh(r["orbit_desig"])) if o]
        n_found = 0
        for m in mjds:
            hit = False
            for p in pub:
                if p.obscode != r["obscode"] or abs(p.mjd - m) * 86400.0 > DUP_EPOCH_S:
                    continue
                match_pos = True
                for o in trk_obs:
                    if abs(o.mjd - m) < 2e-4:
                        dra = abs((p.ra_deg - o.ra_deg + 180.0) % 360.0 - 180.0) * 3600.0
                        dde = abs(p.dec_deg - o.dec_deg) * 3600.0
                        cosd = math.cos(math.radians(o.dec_deg))
                        match_pos = (dra * cosd) ** 2 + dde ** 2 <= DUP_POS_ARCSEC ** 2
                        break
                if match_pos:
                    hit = True
                    break
            n_found += int(hit)
        outcome = (
            "CONSUMED_INTO_SAME_OBJECT" if n_found == len(mjds) and mjds
            else "NOT_IN_THIS_OBJECT" if n_found == 0
            else f"PARTIAL({n_found}/{len(mjds)})"
        )
        rows.append(
            {
                "orbit_desig": r["orbit_desig"],
                "trksub": r["trksub"],
                "obscode": r["obscode"],
                "night": r["night"],
                "link_key": r["link_key"],
                "m8_verdict": verdict_by_key.get((r["orbit_desig"], r["link_key"]),
                                                 "(not in ledger)"),
                "trk_obs": len(mjds),
                "found_in_fresh_published": n_found,
                "outcome": outcome,
            }
        )
        print(f"{outcome:28s} {r['orbit_desig']:12s} + {r['trksub']:8s} "
              f"{r['obscode']} n{r['night']} [{verdict_by_key.get((r['orbit_desig'], r['link_key']), '?')}]",
              flush=True)

    summary: dict[str, Any] = {"n_consumed_fitted": len(rows)}
    for v in ("PASS", "FAIL", "ALREADY_LINKED"):
        sub = [x for x in rows if x["m8_verdict"] == v]
        summary[v] = {
            "n": len(sub),
            "consumed_into_same_object": sum(
                1 for x in sub if x["outcome"] == "CONSUMED_INTO_SAME_OBJECT"
            ),
            "not_in_this_object": sum(
                1 for x in sub if x["outcome"] == "NOT_IN_THIS_OBJECT"
            ),
            "partial": sum(1 for x in sub if x["outcome"].startswith("PARTIAL")),
        }
    out = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rules": {"dup_epoch_s": DUP_EPOCH_S, "dup_pos_arcsec": DUP_POS_ARCSEC},
        "summary": summary,
        "rows": rows,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
