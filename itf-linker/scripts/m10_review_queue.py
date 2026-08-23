"""M10: emit ``out/review-queue.csv`` — the one artifact Matthew opens.

Everything else in this repository is evidence *about* candidates. This is the
candidates, in the order a submitter should work through them, with the columns a human
can adjudicate on and without the ones a human cannot.

Two rules decide what is in it:

* **Only still-live rows.** A tracklet the MPC has already consumed is not submittable,
  whatever its verdict was. Liveness comes from ``m10-refresh.json``, which tested every
  ledger tracklet key against a pull taken now.
* **Ranked by submission value**, which is not the same as ranked by fit quality:

  | tier | what it is | why it ranks here |
  |---|---|---|
  | **A** | `combined_pass` objects, every member tracklet still live | the strongest artifacts the project has produced: two or three independent tracklets that fit *jointly* to one orbit, arc extensions to +5,107 d, sigma_a down 10-10,000x. Mutual corroboration that survived being tested |
  | **B** | caveat-free single PASS rows | one tracklet, every gate clean, no SkyBoT claimant, no named ambiguity, not demoted by a joint fit |
  | **C** | PASS rows carrying a named caveat | a lost-object ambiguity (with its adjudication verdict, so the reviewer sees it was *tested*), or membership of an object whose joint fit demoted it (`combined_below_gate` — read as weakened, M9 section 6) |
  | **D** | BORDERLINE and M7's held rows | the strict gate missed by thousandths of an arcsecond while the MPC's own published rule passes. Explicitly Matthew's call, and always has been |

Within A and B the sort key is **arc extension in days** — how far outside the object's
published arc the new astrometry sits, which is the quantity a submission is *for*.

The first ten data rows are a **spot-check sample**: two from each tier plus the two
deepest arc extensions overall, repeated at the top of the file under a
``SPOTCHECK`` tier marker so a reviewer can sanity-check the machinery in thirty
seconds before trusting the other several hundred rows.

Reads the ledgers, ``m9-combined.json``, both adjudications, ``m10-refresh.json`` and
the era-pinned ``obs80/`` cache. Writes ``out/review-queue.csv`` and
``out/review-queue-summary.json``. No network, no fits, nothing loosened.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import polars as pl

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.mpc80 import parse_line

REFRESH = ROOT / "data" / "raw" / "rubin" / "m10-refresh.json"
M8_LEDGER = ROOT / "m8-ledger.json"
M9_LEDGER = ROOT / "m9-ledger.json"
COMBINED = ROOT / "m9-combined.json"
ADJ_M9 = ROOT / "m9-adjudication.json"
ADJ_M10 = ROOT / "m10-adjudication.json"
POINTED = ROOT / "data" / "raw" / "rubin" / "m10-pointed.json"
OBS80 = ROOT / "data" / "raw" / "rubin" / "obs80"
SLIM = ROOT / "data" / "snapshots" / "20260816T202701Z" / "observations.parquet"
OUT_CSV = ROOT / "out" / "review-queue.csv"
OUT_JSON = ROOT / "out" / "review-queue-summary.json"

COLUMNS = [
    "rank", "tier", "tier_label", "object", "n_tracklets", "tracklets", "obs_codes",
    "n_new_obs", "arc_extension_days", "deepest_dt_years", "joint_rms_arcsec",
    "baseline_rms_arcsec", "sigma_a_ratio", "gates", "skybot", "ambiguity",
    "provenance", "itf_status", "pointed_screen", "link_keys", "why_real",
]

TIER_LABELS = {
    "A": "combined-fit, all members live",
    "B": "single tracklet, caveat-free",
    "C": "single tracklet, named caveat",
    "D": "borderline / held - Matthew's call",
}


def published_arc(desig: str) -> tuple[float | None, float | None, int]:
    path = OBS80 / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not path.exists():
        return (None, None, 0)
    mjds = [
        o.mjd for o in (parse_line(ln, strict=False)
                        for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip())
        if o
    ]
    return (min(mjds), max(mjds), len(mjds)) if mjds else (None, None, 0)


def arc_extension(pub_first: float | None, pub_last: float | None,
                  trk_mjds: list[float]) -> float | None:
    """Days of arc the tracklet adds *outside* the object's published span.

    Zero means the tracklet falls inside the existing arc: still evidence (it densifies
    the orbit) but not an arc extension, and a reviewer should see the difference.
    """
    if pub_first is None or not trk_mjds:
        return None
    lo, hi = min(trk_mjds), max(trk_mjds)
    return round(max(0.0, pub_first - lo) + max(0.0, hi - pub_last), 1)


def skybot_cell(sb: dict[str, Any] | None) -> str:
    if not sb:
        return "not run"
    if sb.get("status") != "ok":
        return f"UNAVAILABLE ({sb.get('status')})"
    bits = []
    if sb.get("self"):
        bits.append("object itself present")
    if sb.get("conflicts"):
        bits.append("CONFLICT: " + "; ".join(
            f"{c['name']} at {c['sep_arcsec']}\"" for c in sb["conflicts"]))
    if sb.get("lost_object_ambiguity"):
        bits.append("lost-object claimant: " + "; ".join(
            f"{c['name']} (err {c['ephem_err_arcsec']}\")"
            for c in sb["lost_object_ambiguity"][:2]))
    other = sb.get("nearest_other")
    if other and not bits:
        bits.append(f"nearest other {other.get('sep_arcsec')}\"")
    return "clean" if not bits else "; ".join(bits)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT_CSV)
    ap.add_argument("--summary", type=Path, default=OUT_JSON)
    ap.add_argument("--refresh", type=Path, default=REFRESH,
                    help="liveness source. A queue is only as fresh as this file")
    ap.add_argument("--adjudications", nargs="*", default=None,
                    help="REPLACE the default adjudication list")
    ap.add_argument("--slim", type=Path, default=SLIM,
                    help="08-16 observation table; the archive's retention prunes the "
                         "snapshot this defaults to (scripts/m11_snapshot_series.py)")
    args = ap.parse_args()
    if not args.slim.exists():
        raise SystemExit(
            f"{args.slim} does not exist -- the archive's retention has pruned the "
            "08-16 key set. Rebuild it with scripts/m11_snapshot_series.py and pass "
            "--slim; do NOT silently substitute a newer snapshot."
        )

    refresh = json.loads(args.refresh.read_text(encoding="utf-8"))
    status = {
        (r["trksub"], r["obscode"], int(r["night"])): r["itf_status"]
        for r in refresh["rows"]
    }

    ledger_rows: list[dict[str, Any]] = []
    for path, tag in ((M8_LEDGER, "M8"), (M9_LEDGER, "M9")):
        for v in json.loads(path.read_text(encoding="utf-8"))["verdicts"]:
            ledger_rows.append({**v, "ledger": tag,
                                "provenance": v.get("provenance", tag)})
    by_key = {(r["trksub"], r["obscode"], int(r["night"])): r for r in ledger_rows}

    # ---- the pointed-field screen, applied to every live row (M10 section 5) -------
    pointed: dict[tuple[str, str, int], dict[str, Any]] = {}
    if POINTED.exists():
        for f in (json.loads(POINTED.read_text(encoding="utf-8"))
                  .get("ledger_screen") or {}).get("flagged") or []:
            pointed[(f["trksub"], f["obscode"], int(f["night"]))] = f

    def pointed_cell(keys: list[tuple[str, str, int]]) -> str:
        hits = [pointed[k] for k in keys if k in pointed]
        if not hits:
            return "clean"
        return "; ".join(
            f"{'/'.join(h['flags'])} (nearest same-station published row "
            f"{h['min_dt_seconds'] / 3600.0:.1f} h away)" for h in hits
        )

    # ---- adjudications, both milestones' -------------------------------------------
    adj: dict[tuple[str, str], dict[str, Any]] = {}
    for p in ([Path(x) for x in args.adjudications]
              if args.adjudications is not None else (ADJ_M9, ADJ_M10)):
        if p.exists():
            for e in json.loads(p.read_text(encoding="utf-8"))["results"]:
                adj[(e["orbit_desig"], e["link_key"])] = e

    # ---- tracklet epochs from the universe the fits used ----------------------------
    lon = fetch_obscodes()
    lon_df = pl.DataFrame({"obscode": list(lon.keys()),
                           "lon_deg": [v - 360.0 if v > 180.0 else v
                                       for v in lon.values()]})
    slim = (
        pl.scan_parquet(args.slim)
        .filter(pl.col("desig").is_in([r["trksub"] for r in ledger_rows]))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns((pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
                      .floor().cast(pl.Int32).alias("night"))
        .collect()
    )
    epochs: dict[tuple[str, str, int], list[float]] = {}
    for d, o, n, m in zip(slim["desig"], slim["obscode"], slim["night"], slim["mjd"]):
        epochs.setdefault((d, o, int(n)), []).append(float(m))

    arc_cache: dict[str, tuple[float | None, float | None, int]] = {}

    def arc_of(desig: str) -> tuple[float | None, float | None, int]:
        if desig not in arc_cache:
            arc_cache[desig] = published_arc(desig)
        return arc_cache[desig]

    # ---- tier A: combined fits whose every member is still live ---------------------
    combined = json.loads(COMBINED.read_text(encoding="utf-8"))["results"]
    demoted_keys: set[tuple[str, str, int]] = set()
    rows: list[dict[str, Any]] = []
    a_members: set[tuple[str, str, int]] = set()

    for c in combined:
        keys = [(m["trksub"], m["obscode"], int(m["night"])) for m in c["members"]]
        live = [status.get(k, "UNKNOWN") == "STILL_LIVE" for k in keys]
        if c["tier"] != "combined_pass":
            demoted_keys.update(keys)
            continue
        if not all(live):
            continue  # a partly-consumed joint fit is not submittable as a joint fit
        a_members.update(keys)
        pf, plst, _npub = arc_of(c["orbit_desig"])
        trk_mjds = [m for k in keys for m in epochs.get(k, [])]
        ext = c.get("arc_extension_days")
        ext = round(ext, 1) if ext is not None else arc_extension(pf, plst, trk_mjds)
        sbs = [skybot_cell((by_key.get(k) or {}).get("skybot")) for k in keys]
        ambs_raw = [adj.get((c["orbit_desig"], m["link_key"]), {}).get("adjudication")
                    for m in c["members"]]
        n_amb = sum(1 for a in ambs_raw if a)
        ambs = ([f"{a} ({sum(1 for x in ambs_raw if x == a)}/{c['n_tracklets']} members)"
                 for a in sorted({a for a in ambs_raw if a})] if n_amb else [])
        deep = min((m["dt_years"] for m in c["members"]), default=None)
        n_new = sum(m.get("n_obs") or 0 for m in c["members"])
        rows.append({
            "tier": "A",
            "sort": -(ext or 0.0),
            "object": c["orbit_desig"],
            "n_tracklets": c["n_tracklets"],
            "tracklets": "; ".join(f"{k[0]}@{k[1]}/n{k[2]}" for k in keys),
            "obs_codes": "; ".join(sorted({k[1] for k in keys})),
            "n_new_obs": n_new,
            "arc_extension_days": ext,
            "deepest_dt_years": deep,
            "joint_rms_arcsec": round(c["combined"]["rms"], 4),
            "baseline_rms_arcsec": round(c["baseline"]["rms"], 4),
            "sigma_a_ratio": (None if c.get("sigma_a_ratio") is None
                              else float(f"{c['sigma_a_ratio']:.3g}")),
            "gates": (f"strict={'Y' if c['gate_strict']['passes'] else 'N'} "
                      f"published={'Y' if c['gate_mpc_published']['passes'] else 'N'} "
                      f"all-members-used="
                      f"{'Y' if c['all_tracklets_fully_used'] else 'N'} "
                      f"distinct-nights={c.get('distinct_member_nights')}"
                      + (f" shared-night-groups={c['shared_night_groups']}"
                         if c.get("shared_night_groups") else "")),
            "skybot": " | ".join(sbs),
            "ambiguity": "; ".join(ambs) if ambs else "none",
            # m9_combined labelled its --extra-ledgers source "extra0"; name it.
            "provenance": "; ".join(sorted({
                {"extra0": "M9"}.get(m["ledger"], m["ledger"]) for m in c["members"]
            })),
            "itf_status": "STILL_LIVE (all members)",
            "pointed_screen": pointed_cell(keys),
            "link_keys": "; ".join(m["link_key"] for m in c["members"]),
            "why_real": (
                f"{c['n_tracklets']} tracklets across "
                f"{len({k[1] for k in keys})} station(s) fit jointly to one orbit at "
                f"{c['combined']['rms']:.3f}\" with every observation used "
                f"({c['combined']['n_used']}/{c['combined']['n_obs']})"
                + (f"; sigma_a falls to {c['sigma_a_ratio']:.3g}x baseline"
                   if c.get("sigma_a_ratio") else "")
                + (f"; the arc grows {ext:.0f} d" if ext else
                   "; the tracklets fall inside the published arc")
                + ". Mutual corroboration that was tested rather than assumed - the "
                  "joint fit had the power to refute it and did not."
            ),
        })

    # ---- tiers B/C: single PASS rows, and D: borderline + held ----------------------
    for r in ledger_rows:
        key = (r["trksub"], r["obscode"], int(r["night"]))
        if status.get(key) != "STILL_LIVE":
            continue
        if key in a_members:
            continue  # its value is reported on the tier-A row
        if r["verdict"] not in ("PASS", "BORDERLINE"):
            continue
        pf, plst, _npub = arc_of(r["orbit_desig"])
        trk_mjds = epochs.get(key, [])
        ext = arc_extension(pf, plst, trk_mjds)
        a = adj.get((r["orbit_desig"], r.get("link_key")))
        caveats: list[str] = []
        if any(x.startswith("skybot_lost_object_ambiguity") for x in r["reasons"]):
            caveats.append("lost-object ambiguity")
        if key in demoted_keys:
            caveats.append("joint fit with sibling DEMOTED (M9 section 6): read as weakened")
        if r.get("duplicates_in_published"):
            caveats.append(f"{r['duplicates_in_published']} obs already in published record")
        if r["verdict"] == "BORDERLINE":
            tier = "D"
        elif caveats:
            tier = "C"
        else:
            tier = "B"
        amb = "none"
        if a:
            amb = a["adjudication"]
            if a.get("claimants"):
                amb += (f" ({len(a['claimants'])} claimant(s) fitted"
                        + (", " + a["note"] if a.get("note") else "") + ")")
        elif caveats and "lost-object ambiguity" in caveats:
            amb = "NOT ADJUDICATED"
        fully = f"{r.get('trk_obs_used')}/{r.get('trk_obs_total')}"
        rows.append({
            "tier": tier,
            "sort": -(ext or 0.0),
            "object": r["orbit_desig"],
            "n_tracklets": 1,
            "tracklets": f"{key[0]}@{key[1]}/n{key[2]}",
            "obs_codes": key[1],
            "n_new_obs": r.get("trk_obs_total"),
            "arc_extension_days": ext,
            "deepest_dt_years": r.get("dt_years"),
            "joint_rms_arcsec": r.get("rms_joint"),
            "baseline_rms_arcsec": r.get("rms_baseline"),
            "sigma_a_ratio": None,
            "gates": (f"strict={'Y' if not any(x.startswith('strict_gate') for x in r['reasons']) else 'N'} "
                      f"published={'Y' if r.get('mpc_published_gate_passes') else 'N'} "
                      f"tracklet-used={fully} sep={r.get('sep_arcsec')}\"/"
                      f"gate={r.get('gate_radius_arcsec')}\""
                      + (" ENCOUNTER" if r.get("encounter") else "")),
            "skybot": skybot_cell(r.get("skybot")),
            "ambiguity": amb,
            "provenance": r["provenance"],
            "itf_status": "STILL_LIVE",
            "pointed_screen": pointed_cell([key]),
            "link_keys": r.get("link_key"),
            "why_real": (
                f"{r.get('trk_obs_total')}-observation {key[1]} tracklet "
                f"{abs(r.get('dt_years') or 0):.1f} y from the orbit epoch fits jointly "
                f"with the object's whole published record at "
                f"{r.get('rms_joint')}\" (baseline {r.get('rms_baseline')}\") with every "
                f"observation used ({fully}); coarse separation {r.get('sep_arcsec')}\" "
                f"inside a {r.get('gate_radius_arcsec')}\" gate"
                + (f"; extends the published arc by {ext:.0f} d" if ext else
                   "; falls inside the published arc (densifies, does not extend)")
                + (". " + " ".join(caveats) if caveats else ".")
            ),
        })

    # M7's held rows: carried verbatim, never recomputed (M8 task law).
    import m8_verdicts as m8v

    emitted = {(r["object"], r["tracklets"]) for r in rows}
    for h in m8v.M7_HELD:
        key = (h["trksub"], h["obscode"], int(h["night"]))
        if status.get(key) != "STILL_LIVE":
            continue
        # 2025 MQ241 + nf2088 is BOTH an M7 held row and M8's BORDERLINE row: one
        # candidate, two records of it. The ledger row is the re-fitted one, so it
        # wins and the held row only adds M7's note.
        if (h["orbit_desig"], f"{key[0]}@{key[1]}/n{key[2]}") in emitted:
            for r in rows:
                if (r["object"], r["tracklets"]) == (
                    h["orbit_desig"], f"{key[0]}@{key[1]}/n{key[2]}"
                ):
                    r["provenance"] += "; also M7-HELD"
                    r["why_real"] += f" M7 held it since {h['status']}: {h['note']}."
            continue
        pf, plst, _ = arc_of(h["orbit_desig"])
        ext = arc_extension(pf, plst, epochs.get(key, []))
        rows.append({
            "tier": "D", "sort": -(ext or 0.0), "object": h["orbit_desig"],
            "n_tracklets": 1, "tracklets": f"{key[0]}@{key[1]}/n{key[2]}",
            "obs_codes": key[1], "n_new_obs": h.get("trk_obs_total"),
            "arc_extension_days": ext,
            "deepest_dt_years": round(h["dt_days"] / 365.25, 2),
            "joint_rms_arcsec": h["rms_joint"], "baseline_rms_arcsec": None,
            "sigma_a_ratio": None,
            "gates": f"M7 verdict {h['verdict']}; sep={h['sep_arcsec']}\"",
            "skybot": "M7 manual cone search (M7-RESULTS section 8)",
            "ambiguity": "none", "provenance": "M7 (HELD)",
            "itf_status": "STILL_LIVE", "pointed_screen": pointed_cell([key]),
            "link_keys": h["link_key"],
            "why_real": h["note"] + " - held for Matthew since M7; still live in the ITF.",
        })

    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    rows.sort(key=lambda r: (order[r["tier"]], r["sort"], r["object"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["tier_label"] = TIER_LABELS[r["tier"]]

    # ---- the ten-row spot check ------------------------------------------------------
    sample: list[dict[str, Any]] = []
    seen: set[int] = set()
    for t in "ABCD":
        for r in [x for x in rows if x["tier"] == t][:2]:
            sample.append(r)
            seen.add(r["rank"])
    # Top up to ten with the deepest arc extensions not already sampled, so the
    # spot check always shows the rows a reviewer would most want to disbelieve.
    for r in sorted(rows, key=lambda x: -(x["arc_extension_days"] or 0)):
        if len(sample) >= 10:
            break
        if r["rank"] not in seen:
            sample.append(r)
            seen.add(r["rank"])
    sample.sort(key=lambda r: r["rank"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: this file is opened in Excel, which reads plain UTF-8 as the system
    # codepage and mangles every non-ASCII character in it.
    with args.out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for s in sample:
            w.writerow({**s, "tier": "SPOTCHECK",
                        "tier_label": f"sample of tier {s['tier']} (row {s['rank']})"})
        for r in rows:
            w.writerow(r)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1
    summary = {
        "generated_from_refresh": refresh["generated_utc"],
        "fresh_itf": refresh["fresh_provenance"]["last_modified"],
        "rows": len(rows),
        "spotcheck_rows": len(sample),
        "by_tier": counts,
        "tier_labels": TIER_LABELS,
        "distinct_objects": len({r["object"] for r in rows}),
        "distinct_tracklets": sum(r["n_tracklets"] for r in rows),
        "pointed_field_flagged": sum(1 for r in rows if r["pointed_screen"] != "clean"),
        "adjudications_folded_in": sorted(
            p.name for p in (ADJ_M9, ADJ_M10) if p.exists()
        ),
        "csv_bytes": args.out.stat().st_size,
        "csv": str(args.out),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
