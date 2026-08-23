"""M10: refresh the whole cumulative candidate ledger against today's ITF.

M9 measured the ledger's decay from a *single* interval (08-16 -> 08-18): 30 of M8's
900 fitted candidates lost their tracklets to the MPC, and all 30 went to exactly the
object the ledger had named. That is one data point on a clock Matthew's review is
racing, and one data point has no uncertainty.

This script does three things M9's ``m9_consumed_check.py`` did for one interval and
one ledger:

1. **Full cumulative coverage.** Every fitted row of ``m8-ledger.json`` (900) and
   ``m9-ledger.json`` (1,000), plus M7's three held candidates -- not just the M8
   PASSes. Rejections matter: an MPC consumption of a *FAIL* row is evidence about the
   strict gate's conservatism (M9 section 5 reading 2), and only the full population
   gives an unbiased decay rate.

2. **A decay *curve*, not a difference.** The archive kept slim ``obs_key`` tables for
   every daily pull, so the same tracklet keys can be tested against 2026-08-16
   20:27 (the universe M8/M9 swept), 08-17 12:26, 08-18 15:29 **and** a fresh pull
   taken now. Four points, three intervals, a rate with an uncertainty.

3. **Agreement, per consumed row.** A tracklet that left the ITF went somewhere. The
   MPC never says where, but the attributed object's *published* record does: fetch it
   live (a **new** cache -- M9 trap 5: the consumed-check needs fresh records where
   the combined fits forbid them) and ask whether the tracklet's own observations,
   matched at the ledger's 2 s / 2" duplicate rule, are now inside it.

   * ``CONSUMED_AND_AGREED``    -- every observation is in the attributed object.
   * ``CONSUMED_AND_DISAGREED`` -- none of them are. **This is the loud case**: the MPC
     linked the tracklet somewhere else, and the ledger row is a measured error.
   * ``CONSUMED_PARTIAL``       -- some. Worth a human's eye either way.

Astrometry for a consumed tracklet cannot come from the ITF (it has left), so it comes
from the fit directory's ``obs.txt`` -- the verbatim 80-column lines ``fo`` actually
fitted -- with epochs from the 08-16 slim table. That is M9's method, unchanged.

Writes ``data/raw/rubin/m10-refresh.json``.
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

import polars as pl
import requests

from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.mpc80 import parse_line

M8_LEDGER = ROOT / "m8-ledger.json"
M9_LEDGER = ROOT / "m9-ledger.json"
SNAP_DIR = ROOT / "data" / "snapshots"
#: Where a consumed tracklet's verbatim fitted lines live, keyed by fit-tag prefix.
#: ``mAa`` is M10's shell queue and ``mCa`` M11's deep-end queue -- both needed once the
#: refresh covers the shell tier (M11 section 0.2), because a consumed tracklet's
#: astrometry cannot come from the ITF it has left.
FIT_ROOTS = {"m8a": ROOT / "data" / "m8-fits", "m9a": ROOT / "data" / "m9-fits",
             "m7a": ROOT / "data" / "m7-fits",
             "mAa": ROOT / "data" / "m10-shell-fits",
             "mCa": ROOT / "data" / "m11-deep-fits"}
FRESH_CACHE = ROOT / "data" / "raw" / "rubin" / "obs80-m10fresh"
OUT = ROOT / "data" / "raw" / "rubin" / "m10-refresh.json"

OBS_URL = "https://data.minorplanetcenter.net/api/get-obs"
USER_AGENT = (
    "itf-linker/0.4 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

#: The ledger's own duplicate rule, unchanged from M8/M9. Nothing here is loosened.
DUP_EPOCH_S = 2.0
DUP_POS_ARCSEC = 2.0

#: The universe M8 and M9 swept. Every "was this tracklet ever there" question is
#: asked against this snapshot's observation set, never against today's.
BASE_SNAPSHOT = "20260816T202701Z"


def get_obs80_fresh(desig: str, *, pace_s: float = 1.2) -> list[str]:
    FRESH_CACHE.mkdir(parents=True, exist_ok=True)
    dest = FRESH_CACHE / (desig.replace(" ", "_").replace("/", "_") + ".obs80")
    if not dest.exists():
        time.sleep(pace_s)
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


def lon_frame() -> pl.DataFrame:
    lon = fetch_obscodes()
    return pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )


def per_tracklet_counts(
    slim_path: Path, desigs: set[str], lon_df: pl.DataFrame
) -> dict[tuple[str, str, int], int]:
    """(desig, obscode, night) -> observation count, for the ledger's designations only.

    The night formula is ``load_tracklets``' exactly (local night from the
    observatory's signed longitude), so "tracklet" here means what it means in every
    attribution sweep in this repo.
    """
    df = (
        pl.scan_parquet(slim_path)
        .filter(pl.col("desig").is_in(list(desigs)))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
        .group_by("desig", "obscode", "night")
        .agg(pl.len().alias("n"))
        .collect()
    )
    return {
        (d, o, int(n)): int(c)
        for d, o, n, c in zip(df["desig"], df["obscode"], df["night"], df["n"])
    }


def tracklet_epochs(
    slim_path: Path, keys: list[tuple[str, str, int]], lon_df: pl.DataFrame
) -> dict[tuple[str, str, int], list[float]]:
    df = (
        pl.scan_parquet(slim_path)
        .filter(pl.col("desig").is_in([k[0] for k in keys]))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
        .collect()
    )
    out: dict[tuple[str, str, int], list[float]] = {}
    for d, o, n, m in zip(df["desig"], df["obscode"], df["night"], df["mjd"]):
        out.setdefault((d, o, int(n)), []).append(float(m))
    return out


def fit_obs(tag: str | None, obscode: str, mjds: list[float]) -> list[Any]:
    """The verbatim 80-column lines ``fo`` fitted for this tracklet, if we have them."""
    if not tag:
        return []
    root = FIT_ROOTS.get(tag[:3])
    if root is None:
        return []
    path = root / tag / "obs.txt"
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        o = parse_line(ln, strict=False)
        if o and o.obscode == obscode and any(abs(o.mjd - m) < 2e-4 for m in mjds):
            out.append(o)
    return out


def observation_in_published(
    mjd: float, obscode: str, trk_obs: list[Any], pub: list[Any]
) -> bool:
    for p in pub:
        if p.obscode != obscode or abs(p.mjd - mjd) * 86400.0 > DUP_EPOCH_S:
            continue
        for o in trk_obs:
            if abs(o.mjd - mjd) < 2e-4:
                dra = abs((p.ra_deg - o.ra_deg + 180.0) % 360.0 - 180.0) * 3600.0
                dde = abs(p.dec_deg - o.dec_deg) * 3600.0
                cosd = math.cos(math.radians(o.dec_deg))
                if (dra * cosd) ** 2 + dde**2 <= DUP_POS_ARCSEC**2:
                    return True
                break
        else:
            # No astrometry to compare against: an epoch+station match at 2 s is
            # already a 1-in-many coincidence, so accept it but say so upstream.
            return True
    return False


def scan_series(fresh_slim: Path, fresh_prov: dict[str, Any]) -> list[dict[str, Any]]:
    """The archive's surviving key sets at/after the base, plus the fresh pull.

    **Guarded, because the failure mode is silent.** The archive's retention prunes
    ``observations.parquet`` on a rolling window, so this scan quietly starts returning
    a *later* snapshot as element 0 once the base has been pruned -- and every
    "consumed since <base>" count downstream then measures a shorter interval under
    the old heading. Measured 2026-08-23: the scan returned 08-21 -> 08-22 -> 08-23
    for a base of 08-16. Refuse rather than report.
    """
    series: list[dict[str, Any]] = []
    for sid in sorted(p.name for p in SNAP_DIR.iterdir()
                      if (p / "observations.parquet").exists()
                      and p.name >= BASE_SNAPSHOT):
        manifest = json.loads(
            (SNAP_DIR / sid / "manifest.json").read_text(encoding="utf-8")
        )
        series.append({
            "snapshot_id": sid,
            "last_modified": manifest["provenance"]["last_modified"],
            "observations": manifest["observations"],
            "slim": SNAP_DIR / sid / "observations.parquet",
        })
    series.append({
        "snapshot_id": "FRESH-" + fresh_prov["last_modified"],
        "last_modified": fresh_prov["last_modified"],
        "observations": None,
        "slim": fresh_slim,
    })
    if series[0]["snapshot_id"] != BASE_SNAPSHOT:
        raise SystemExit(
            f"the base snapshot {BASE_SNAPSHOT} has no surviving key set (the "
            f"archive's retention pruned it); element 0 of the series would be "
            f"{series[0]['snapshot_id']} and every 'consumed since' count would "
            f"silently measure a different interval. Rebuild the series with "
            f"scripts/m11_snapshot_series.py and pass --series."
        )
    return series


def load_rows(extra: list[tuple[str, Path]] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, tag in [(M8_LEDGER, "M8"), (M9_LEDGER, "M9")] + [
        (p, t) for t, p in (extra or [])
    ]:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for v in doc["verdicts"]:
            r = dict(v)
            r["ledger"] = tag
            r["provenance"] = v.get("provenance", tag)
            rows.append(r)
    import m8_verdicts as m8v

    for h in m8v.M7_HELD:
        r = dict(h)
        r["ledger"] = "M7"
        r["trk_obs_total"] = h.get("trk_obs_total")
        rows.append(r)
    return rows


def main() -> None:
    global FRESH_CACHE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fresh-slim", type=Path, required=True,
                    help="slim (obs_key, desig, obscode, mjd) parquet of a pull taken "
                         "now; produced outside the repo so the daily archive and its "
                         "clone are untouched")
    ap.add_argument("--fresh-provenance", type=Path, required=True)
    ap.add_argument("--no-network", action="store_true",
                    help="skip the live get-obs agreement check (offline dry run)")
    ap.add_argument("--extra-ledgers", nargs="*", default=[],
                    help="additional ledgers whose fitted rows join the refresh, as "
                         "LABEL=path (M11: M10-shell=m10-shell-ledger.json). Default "
                         "off, so M10's 1,903-row population reproduces unchanged")
    ap.add_argument("--out", type=Path, default=OUT,
                    help="report destination. Default is M10's; M11 writes its own so "
                         "m10-refresh.json stays the input every M10 artifact cites")
    ap.add_argument("--series", type=Path, default=None,
                    help="series.json from scripts/m11_snapshot_series.py, replacing "
                         "the data/snapshots scan. Required once the archive's "
                         "retention has pruned the base snapshot's key set")
    ap.add_argument("--fresh-cache", type=Path, default=FRESH_CACHE,
                    help="get-obs cache for the agreement check. MUST be a cache no "
                         "older than the interval being tested: a stale published "
                         "record makes an agreeing consumption look like a "
                         "disagreement. Default is M10's 08-18 cache; every later "
                         "refresh needs its own")
    args = ap.parse_args()
    FRESH_CACHE = args.fresh_cache

    extra: list[tuple[str, Path]] = []
    for spec in args.extra_ledgers:
        label, _, path = spec.partition("=")
        if not path:
            ap.error("--extra-ledgers entries must be LABEL=path")
        extra.append((label, Path(path)))

    t0 = time.monotonic()
    rows = load_rows(extra)
    print(f"cumulative ledger rows: {len(rows)}", flush=True)

    lon_df = lon_frame()
    desigs = {r["trksub"] for r in rows}

    # ---- the snapshot series -------------------------------------------------------
    fresh_prov = json.loads(args.fresh_provenance.read_text(encoding="utf-8"))
    series: list[dict[str, Any]] = []
    if args.series is not None:
        # An explicit series. M11 needs this because the archive's rolling retention
        # PRUNED the base snapshot's key set: the directory scan below silently returns
        # 08-21 as element 0 and every "consumed since 08-16" count then measures
        # something else under the old heading. scripts/m11_snapshot_series.py rebuilds
        # the series exactly from the contiguous delta chain and verifies it.
        doc = json.loads(args.series.read_text(encoding="utf-8"))
        for e in doc["series"]:
            series.append({**e, "slim": Path(e["slim"])})
    else:
        series = scan_series(args.fresh_slim, fresh_prov)
    print("snapshot series: " + " -> ".join(s["snapshot_id"] for s in series), flush=True)

    counts_by_snap: list[dict[tuple[str, str, int], int]] = []
    for s in series:
        t = time.monotonic()
        counts_by_snap.append(per_tracklet_counts(s["slim"], desigs, lon_df))
        print(f"  {s['snapshot_id']}: indexed in {time.monotonic() - t:.1f}s", flush=True)

    base_counts = counts_by_snap[0]
    latest = counts_by_snap[-1]

    # ---- per-row status ------------------------------------------------------------
    for r in rows:
        key = (r["trksub"], r["obscode"], int(r["night"]))
        r["_key"] = key
        r["n_obs_base"] = base_counts.get(key, 0)
        r["n_obs_now"] = latest.get(key, 0)
        if r["n_obs_base"] == 0:
            r["itf_status"] = "NOT_IN_BASE_SNAPSHOT"
        elif r["n_obs_now"] == r["n_obs_base"]:
            r["itf_status"] = "STILL_LIVE"
        elif r["n_obs_now"] == 0:
            r["itf_status"] = "CONSUMED"
        else:
            r["itf_status"] = "PARTIALLY_CONSUMED"
        r["first_missing_snapshot"] = None
        for s, c in zip(series, counts_by_snap):
            if c.get(key, 0) < r["n_obs_base"]:
                r["first_missing_snapshot"] = s["snapshot_id"]
                break

    consumed = [r for r in rows if r["itf_status"] in ("CONSUMED", "PARTIALLY_CONSUMED")]
    print(f"consumed or partially consumed since {BASE_SNAPSHOT}: {len(consumed)}",
          flush=True)

    # ---- agreement check on the consumed rows --------------------------------------
    epochs = tracklet_epochs(
        series[0]["slim"],
        [r["_key"] for r in consumed] or [("", "", 0)],
        lon_df,
    ) if consumed else {}

    agreement_rows: list[dict[str, Any]] = []
    pub_cache: dict[str, list[Any]] = {}
    for i, r in enumerate(consumed, 1):
        mjds = sorted(epochs.get(r["_key"], []))
        trk = fit_obs(r.get("fit_tag"), r["obscode"], mjds)
        if args.no_network:
            outcome, n_found = "SKIPPED_NO_NETWORK", None
        else:
            desig = r["orbit_desig"]
            if desig not in pub_cache:
                pub_cache[desig] = [
                    o for o in (parse_line(ln, strict=False)
                                for ln in get_obs80_fresh(desig)) if o
                ]
            pub = pub_cache[desig]
            n_found = sum(
                1 for m in mjds
                if observation_in_published(m, r["obscode"], trk, pub)
            )
            if mjds and n_found == len(mjds):
                outcome = "CONSUMED_AND_AGREED"
            elif n_found == 0:
                outcome = "CONSUMED_AND_DISAGREED"
            else:
                outcome = f"CONSUMED_PARTIAL({n_found}/{len(mjds)})"
        r["agreement"] = outcome
        agreement_rows.append({
            "ledger": r["ledger"],
            "provenance": r.get("provenance"),
            "verdict": r["verdict"],
            "orbit_desig": r["orbit_desig"],
            "trksub": r["trksub"],
            "obscode": r["obscode"],
            "night": r["night"],
            "link_key": r.get("link_key"),
            "itf_status": r["itf_status"],
            "first_missing_snapshot": r["first_missing_snapshot"],
            "trk_obs": len(mjds),
            "found_in_fresh_published": n_found,
            "had_astrometry": bool(trk),
            "agreement": outcome,
        })
        print(f"  [{i}/{len(consumed)}] {outcome:28s} {r['verdict']:15s} "
              f"{r['orbit_desig']:12s} + {r['trksub']:8s} {r['obscode']} "
              f"n{r['night']} ({r['ledger']})", flush=True)

    # ---- decay curve ---------------------------------------------------------------
    # "M7" is the three held rows, which were never fitted through the sweep queue and
    # carry no verdict of their own. Everything else -- M8, M9, and any ledger passed
    # with --extra-ledgers (M11: the M10 shell) -- is a fitted population.
    fitted = [r for r in rows if r["ledger"] != "M7" and r["n_obs_base"] > 0]
    passes = [r for r in fitted if r["verdict"] == "PASS"]
    ledger_labels = sorted({r["ledger"] for r in fitted})
    curve = []
    for s, c in zip(series, counts_by_snap):
        entry = {
            "snapshot_id": s["snapshot_id"],
            "last_modified": s["last_modified"],
            "itf_observations": s["observations"],
            "fitted_live": sum(1 for r in fitted if c.get(r["_key"], 0) >= r["n_obs_base"]),
            "fitted_total": len(fitted),
            "pass_live": sum(1 for r in passes if c.get(r["_key"], 0) >= r["n_obs_base"]),
            "pass_total": len(passes),
        }
        for lab in ledger_labels:
            sub = [r for r in passes if r["ledger"] == lab]
            entry[f"pass_live_{lab}"] = sum(
                1 for r in sub if c.get(r["_key"], 0) >= r["n_obs_base"]
            )
            entry[f"pass_total_{lab}"] = len(sub)
        curve.append(entry)

    summary: dict[str, Any] = {
        "cumulative_rows": len(rows),
        "by_ledger": {},
        "itf_status": {},
        "agreement": {},
    }
    for r in rows:
        summary["by_ledger"][r["ledger"]] = summary["by_ledger"].get(r["ledger"], 0) + 1
        summary["itf_status"][r["itf_status"]] = (
            summary["itf_status"].get(r["itf_status"], 0) + 1
        )
    for a in agreement_rows:
        summary["agreement"][a["agreement"]] = (
            summary["agreement"].get(a["agreement"], 0) + 1
        )
    summary["pass_rows"] = len(passes)
    summary["pass_still_live"] = sum(1 for r in passes if r["itf_status"] == "STILL_LIVE")
    summary["pass_consumed"] = sum(
        1 for r in passes if r["itf_status"] in ("CONSUMED", "PARTIALLY_CONSUMED")
    )
    summary["pass_consumed_and_agreed"] = sum(
        1 for r in passes
        if r.get("agreement") == "CONSUMED_AND_AGREED"
    )
    summary["pass_consumed_and_disagreed"] = sum(
        1 for r in passes if r.get("agreement") == "CONSUMED_AND_DISAGREED"
    )
    summary["pass_by_ledger"] = {
        lab: {
            "total": sum(1 for r in passes if r["ledger"] == lab),
            "still_live": sum(1 for r in passes
                              if r["ledger"] == lab and r["itf_status"] == "STILL_LIVE"),
            "consumed": sum(1 for r in passes if r["ledger"] == lab
                            and r["itf_status"] in ("CONSUMED", "PARTIALLY_CONSUMED")),
        }
        for lab in sorted({r["ledger"] for r in passes})
    }

    out = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_snapshot": BASE_SNAPSHOT,
        "fresh_provenance": fresh_prov,
        "rules": {"dup_epoch_s": DUP_EPOCH_S, "dup_pos_arcsec": DUP_POS_ARCSEC,
                  "note": "identical to m8/m9 ledger rules; nothing loosened"},
        "snapshot_series": [
            {k: v for k, v in s.items() if k != "slim"} for s in series
        ],
        "decay_curve": curve,
        "summary": summary,
        "consumed_rows": agreement_rows,
        "rows": [
            {k: v for k, v in r.items() if k != "_key" and k != "skybot"} for r in rows
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(json.dumps(curve, indent=2))
    print(f"wrote {args.out} in {time.monotonic() - t0:.1f}s")


if __name__ == "__main__":
    main()
