"""M30: verify the 2026-08-14 outside-sweep claims against ESO TAP metadata.

The DISCOVERY/run3-prospectus.md avenue #1 sweep (which did not read this repo's
ledger) claims three newly-public CRIRES+ blocks:
  (a) HIP 65426  — 90 exposures, "K/HK", Mar 2024–May 2025, public since 2026-05-04
  (b) CD-35 2722 — 300 exposures, Oct 2024, public since 2025-10-19, filter "K,LM"
  (c) beta Pic   — 360-exposure K series public 2026-10-01; 1,266-exposure L/M 2027-04-07

This script pulls every CRIRES science frame in a coordinate box around each
target (coordinates from data/m25-census2.json — the census's own resolutions,
LESSONS §3.7: targets hide under host/programme names), windowed by year with
MAXREC raised explicitly (LESSONS §3.2: the 20k cap is silent), and summarizes
per night: frames, OBJECT names, filter_path (a hint, not truth — LESSONS §3.1),
ins_mode, DIT, programme, release dates, public-now status.

filter_path/ins_mode here are metadata; the band truth for any night acted on is
a header probe (m30_probe.py, the m19_verify_bands.py pattern).

Writes data/m30-verify.json. Read-only against ESO TAP.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TAP = "https://archive.eso.org/tap_obs/sync"
MAXREC = 200000

# census-resolved names -> the sweep's claim labels
TARGETS = {
    "HIP65426 b": "HIP 65426",
    "CD-35 2722 B": "CD-35 2722",
    "beta Pic b": "beta Pic",
}
BOX_ARCSEC = 60.0

WINDOWS = [("2021-06-01", "2022-06-01"), ("2022-06-01", "2023-06-01"),
           ("2023-06-01", "2024-06-01"), ("2024-06-01", "2025-06-01"),
           ("2025-06-01", "2026-06-01"), ("2026-06-01", "2027-06-01")]

COLS = ["object", "ra", "dec", "date_obs", "exp_start", "exposure", "prog_id",
        "filter_path", "ins_mode", "origfile", "dp_tech", "dp_type", "dp_id",
        "release_date", "tpl_id", "tpl_expno", "tpl_nexp"]


def tap(query: str, tries: int = 6, timeout: int = 300) -> list[dict]:
    for k in range(tries):
        try:
            r = requests.get(TAP, params={
                "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                "MAXREC": str(MAXREC), "QUERY": query}, timeout=timeout)
            r.raise_for_status()
            j = r.json()
            cols = [c["name"] for c in j["metadata"]]
            return [dict(zip(cols, row)) for row in j["data"]]
        except Exception as e:  # noqa: BLE001
            print(f"  TAP retry {k + 1}: {str(e)[:90]}", flush=True)
            time.sleep(15 * (k + 1))
    raise RuntimeError("TAP unreachable after retries")


def main() -> None:
    import math

    census = json.loads((ROOT / "data" / "m25-census2.json")
                        .read_text(encoding="utf-8"))
    coords = census["targets_resolved"]

    # which of COLS exist in dbo.raw (schema drifts; don't 500 on a guess)
    schema = tap("SELECT column_name FROM TAP_SCHEMA.columns "
                 "WHERE table_name = 'dbo.raw'")
    have = {r["column_name"].lower() for r in schema}
    cols = [c for c in COLS if c in have]
    missing = [c for c in COLS if c not in have]
    if missing:
        print(f"dbo.raw lacks columns {missing}; proceeding without", flush=True)

    now = datetime.now(timezone.utc).isoformat()
    out: dict = {"generated_utc": now, "box_arcsec": BOX_ARCSEC, "targets": {}}

    for name, label in TARGETS.items():
        ra, dec = coords[name]
        cosd = max(abs(math.cos(math.radians(dec))), 1e-3)
        dra = BOX_ARCSEC / 3600.0 / cosd
        ddec = BOX_ARCSEC / 3600.0
        print(f"\n=== {label}  (census '{name}', RA={ra:.5f} Dec={dec:.5f}) ===",
              flush=True)

        frames: list[dict] = []
        for y0, y1 in WINDOWS:
            chunk = tap(f"""
                SELECT {', '.join(cols)}
                FROM dbo.raw
                WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE'
                  AND ra  BETWEEN {ra - dra} AND {ra + dra}
                  AND dec BETWEEN {dec - ddec} AND {dec + ddec}
                  AND date_obs >= '{y0}' AND date_obs < '{y1}'
                """)
            assert len(chunk) < MAXREC, f"window {y0} hit MAXREC — narrow it"
            frames.extend(chunk)
            time.sleep(1)  # politeness between windowed queries
        print(f"{len(frames)} science frames total", flush=True)

        nights: dict[str, dict] = {}
        for f in frames:
            d = (f.get("date_obs") or f.get("exp_start") or "?")[:10]
            n = nights.setdefault(d, {
                "n_frames": 0, "objects": defaultdict(int),
                "filter_path": defaultdict(int), "ins_mode": defaultdict(int),
                "dit_s": defaultdict(int), "progs": set(), "tpl_ids": set(),
                "releases": [], "dp_ids": []})
            n["n_frames"] += 1
            n["objects"][(f.get("object") or "?").strip()] += 1
            n["filter_path"][str(f.get("filter_path") or "?")] += 1
            n["ins_mode"][str(f.get("ins_mode") or "?")] += 1
            n["dit_s"][str(f.get("exposure") or "?")] += 1
            n["progs"].add(f.get("prog_id") or "?")
            if f.get("tpl_id"):
                n["tpl_ids"].add(f["tpl_id"])
            if f.get("release_date"):
                n["releases"].append(f["release_date"])
            n["dp_ids"].append(f.get("dp_id"))

        for d, n in nights.items():
            rel = sorted(n["releases"])
            n["release_min"] = rel[0] if rel else None
            n["release_max"] = rel[-1] if rel else None
            n["public_now"] = bool(rel) and rel[-1] <= now
            n["objects"] = dict(n["objects"])
            n["filter_path"] = dict(n["filter_path"])
            n["ins_mode"] = dict(n["ins_mode"])
            n["dit_s"] = dict(n["dit_s"])
            n["progs"] = sorted(n["progs"])
            n["tpl_ids"] = sorted(n["tpl_ids"])
            del n["releases"]

        for d in sorted(nights):
            n = nights[d]
            objs = ",".join(f"{k}x{v}" for k, v in sorted(n["objects"].items()))
            filt = ",".join(sorted(n["filter_path"]))
            mode = ",".join(sorted(n["ins_mode"]))
            print(f"  {d} n={n['n_frames']:3d} pub={'Y' if n['public_now'] else 'n'} "
                  f"rel={str(n['release_max'])[:10]} mode={mode:<8} filt={filt:<8} "
                  f"prog={','.join(n['progs'])} obj={objs}", flush=True)

        out["targets"][label] = {
            "census_name": name, "ra": ra, "dec": dec,
            "n_frames_total": len(frames),
            "nights": {d: nights[d] for d in sorted(nights)}}

    p = ROOT / "data" / "m30-verify.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {p}", flush=True)


if __name__ == "__main__":
    main()
