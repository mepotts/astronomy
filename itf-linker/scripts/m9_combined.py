"""M9: combined fits for multi-tracklet objects — the strongest-evidence tier.

M7's PD152 evidence peaked at the *combined* 33-of-33 fit of two independently-passing
tracklets; M8's chain fitted tracklets singly and left combination to the human. This
automates it: every object with 2+ independently-PASSing tracklets (M8 ledger, plus
any M9 ledgers passed on the command line) gets ONE joint fit of its full published
astrometry (the M8-era ``obs80/`` cache — deliberately, see below) plus ALL passing
tracklets, against an object-only baseline run the same way.

Reported per object: arc extension, joint RMS vs baseline RMS, per-tracklet
fully-used counts, and formal uncertainty deltas (fo's sigma_a/e/i) — the orbit
improvement a submission would buy.

Two honesty notes baked in:

* **The 08-16 astrometry cache is load-bearing.** The MPC consumed 21 PASS tracklets
  into their objects between 08-16 and 08-18 (``m9_consumed_check.py``: 21/21 to the
  same objects M8 named). A *fresh* get-obs for those objects now contains the
  tracklet observations, so fitting fresh-obs + tracklet would double-count the same
  astrometry. The M8-era cache predates the consumption; each combined fit is
  therefore evidence about the 08-16 universe, and every consumed tracklet is flagged
  (``consumed_since_snapshot``) so the tier separates *submission value* (unconsumed)
  from *validation value* (consumed: the MPC already agreed).
* **Line sources are explicit.** Tracklet lines come from the current ``itf.txt.gz``
  where the tracklet still exists, else verbatim from the M8 fit directory's
  ``obs.txt`` (the lines fo actually fitted, relabelled). A tracklet with neither is
  reported, not silently skipped.

Writes ``m9-combined.json`` (root, gitignored by ``/m[0-9]*.json``). Tags ``m9c####``
(combined) / ``m9e####`` (baselines). Nothing is submitted.
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

import m8_attribution as m8run
import polars as pl

from itf_linker.fit.findorb import prepare_config_dir, run_fo
from itf_linker.fit.gates import mpc_published_gate, post_fit_gate
from itf_linker.fit.wsl import default_shell
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.link.assemble import _relabel, tracklet_line_index
from itf_linker.mpc80 import parse_line

LEDGER_M8 = ROOT / "m8-ledger.json"
DROPPED = ROOT / "data" / "raw" / "rubin" / "m9-dropped-tracklets.parquet"
#: The 08-16 key set. **The archive's rolling retention prunes it** -- by
#: 2026-08-23 this path no longer exists (M11 section 1.0). Override with
#: --slim, pointing at a rebuilt table from scripts/m11_snapshot_series.py.
SLIM = ROOT / "data" / "snapshots" / "20260816T202701Z" / "observations.parquet"
M8_FIT_ROOT = ROOT / "data" / "m8-fits"
FIT_ROOT = ROOT / "data" / "m9-fits"
OUT = ROOT / "m9-combined.json"


def fit_fields(fit: Any) -> dict[str, Any]:
    return {
        "status": fit.status,
        "converged": bool(fit.converged),
        "rms": fit.rms_residual,
        "n_obs": fit.n_obs,
        "n_used": fit.n_used,
        "a": fit.a,
        "e": fit.e,
        "incl": fit.incl,
        "sigma_a": fit.sigma_a,
        "sigma_e": fit.sigma_e,
        "sigma_i": fit.sigma_i,
        "first_jd": fit.first_jd,
        "last_jd": fit.last_jd,
    }


#: Where a consumed tracklet's verbatim fitted lines live, by fit-tag prefix. M9 only
#: ever needed M8's directory (every M8 tag is ``m8a...``); M11 combines the M10 shell
#: tier, whose tags are ``mAa...``, and its own deep-end queue (``mCa...``).
FIT_ROOTS_BY_PREFIX = {
    "m7a": ROOT / "data" / "m7-fits",
    "m8a": M8_FIT_ROOT,
    "m9a": ROOT / "data" / "m9-fits",
    "mAa": ROOT / "data" / "m10-shell-fits",
    "mCa": ROOT / "data" / "m11-deep-fits",
}


def tracklet_lines_from_fit_dir(tag: str, obscode: str, mjds: list[float]) -> list[str]:
    root = FIT_ROOTS_BY_PREFIX.get(tag[:3], M8_FIT_ROOT)
    obs_txt = root / tag / "obs.txt"
    if not obs_txt.exists():
        return []
    out = []
    for ln in obs_txt.read_text(encoding="utf-8", errors="replace").splitlines():
        o = parse_line(ln, strict=False)
        if o and o.obscode == obscode and any(abs(o.mjd - m) < 2e-4 for m in mjds):
            out.append(ln)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extra-ledgers", nargs="*", default=[],
                    help="additional ledger JSONs whose PASS rows join the pool "
                         "(e.g. m9-ledger.json once it exists)")
    ap.add_argument("--min-tracklets", type=int, default=2)
    ap.add_argument("--consumed", type=Path, default=None,
                    help="a refresh report (m11-refresh.json) whose consumed rows join "
                         "m9-dropped-tracklets.parquet. Without it, only the 08-16 to "
                         "08-18 consumptions are known and a member the MPC took last "
                         "week is silently reported as unconsumed submission value")
    ap.add_argument("--ledgers", nargs="*", default=None,
                    help="REPLACE the default source list (m8-ledger.json). M11 uses "
                         "this to combine the M10 shell tier on its own without "
                         "re-running or overwriting M9's 45-object tier")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--fit-root", type=Path, default=FIT_ROOT,
                    help="where this run's fo directories go")
    ap.add_argument("--tag-prefix", default="m9",
                    help="two characters; fit tags are <prefix>c#### (combined) and "
                         "<prefix>e#### (baseline). Seven characters total -- the "
                         "trkSub field truncates at 7 (HANDOFF section 2)")
    ap.add_argument("--slim", type=Path, default=SLIM,
                    help="08-16 observation table (obs_key/desig/obscode/mjd "
                         "is enough). The archive prunes the snapshot this "
                         "defaults to; scripts/m11_snapshot_series.py rebuilds "
                         "it exactly from the delta chain")
    args = ap.parse_args()
    if not args.slim.exists():
        raise SystemExit(
            f"{args.slim} does not exist -- the archive's retention has pruned "
            "the 08-16 key set. Rebuild it with scripts/m11_snapshot_series.py "
            "and pass --slim; do NOT silently substitute a newer snapshot."
        )

    # ---- the pool: PASS rows grouped by object -------------------------------------
    if len(args.tag_prefix) != 2:
        ap.error("--tag-prefix must be exactly two characters (7-char trkSub field)")
    base = ([("M8", LEDGER_M8)] if args.ledgers is None
            else [(Path(p).stem, Path(p)) for p in args.ledgers])
    sources = base + [(f"extra{i}", Path(p))
                      for i, p in enumerate(args.extra_ledgers)]
    passes: dict[str, list[dict[str, Any]]] = {}
    for label, path in sources:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for v in doc["verdicts"]:
            if v["verdict"] == "PASS":
                v = {**v, "ledger": label}
                passes.setdefault(v["orbit_desig"], []).append(v)
    # de-dupe on link_key within an object (a tracklet can only count once)
    for desig in list(passes):
        seen: set[str] = set()
        rows = []
        for v in passes[desig]:
            if v["link_key"] not in seen:
                seen.add(v["link_key"])
                rows.append(v)
        passes[desig] = rows
    multi = {d: rows for d, rows in passes.items() if len(rows) >= args.min_tracklets}
    print(f"objects with >= {args.min_tracklets} independently-passing tracklets: "
          f"{len(multi)}", flush=True)

    dropped = pl.read_parquet(DROPPED)
    dset = set(zip(dropped["desig"].to_list(), dropped["obscode"].to_list(),
                   dropped["night"].to_list()))
    if args.consumed is not None:
        doc = json.loads(args.consumed.read_text(encoding="utf-8"))
        extra = {(r["trksub"], r["obscode"], int(r["night"]))
                 for r in doc.get("consumed_rows", [])}
        print(f"consumed keys: {len(dset)} from the 08-16/08-18 drop set "
              f"+ {len(extra - dset)} newer", flush=True)
        dset |= extra

    # tracklet observation epochs from the 08-16 slim table (for fit-dir extraction
    # of consumed tracklets, and for per-tracklet used checks)
    lon = fetch_obscodes()
    lon_df = pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )
    all_trksubs = {v["trksub"] for rows in multi.values() for v in rows}
    slim = (
        pl.scan_parquet(args.slim)
        .filter(pl.col("desig").is_in(sorted(all_trksubs)))
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
        .collect()
    )

    def trk_mjds(trksub: str, obscode: str, night: int) -> list[float]:
        return slim.filter(
            (pl.col("desig") == trksub) & (pl.col("obscode") == obscode)
            & (pl.col("night") == night)
        )["mjd"].to_list()

    index, _ = tracklet_line_index(all_trksubs, lon)

    shell = default_shell()
    results: list[dict[str, Any]] = []
    for k, (desig, rows) in enumerate(sorted(multi.items())):
        obj_lines = m8run.get_obs80_cached(desig)  # M8-era cache (see module doc)

        base_tag = f"{args.tag_prefix}e{k:04d}"
        cfg = prepare_config_dir(shell, base_tag)
        run = run_fo(
            [_relabel(ln, base_tag) for ln in obj_lines],
            args.fit_root / base_tag,
            designations=[base_tag],
            shell=shell,
            config_dir=cfg,
            timeout=600,
            scratch_dir=f"$HOME/.cache/itf-linker-fo-work/{base_tag}",
        )
        bfit = run.results.get(base_tag) or next(iter(run.results.values()), None)
        baseline = fit_fields(bfit) if bfit else {"status": "fo_returned_nothing"}

        # assemble every passing tracklet's lines
        members = []
        joint_lines = list(obj_lines)
        for v in rows:
            key = (v["trksub"], v["obscode"], v["night"])
            mjds = trk_mjds(*key)
            # The ITF line index is built from *today's* pull, but the tracklet is a
            # statement about the 08-16 universe. A tracklet the MPC has partially
            # consumed since then still appears in today's file with FEWER
            # observations, and taking those lines would silently fit a different
            # tracklet from the one the ledger passed. Accept the live lines only when
            # their count matches the 08-16 slim; otherwise fall back to the verbatim
            # lines fo actually fitted.
            live = index.get(key) or []
            live_ok = bool(live) and len(
                [ln for ln in live if parse_line(ln, strict=False)]
            ) == len(mjds)
            lines = live if live_ok else tracklet_lines_from_fit_dir(
                v.get("fit_tag") or "", v["obscode"], mjds
            )
            source = ("itf" if live_ok else
                      "fit_dir" if lines else "MISSING")
            if live and not live_ok:
                print(f"  {v['trksub']}/{v['obscode']}/n{v['night']}: live ITF has "
                      f"{len(live)} lines vs {len(mjds)} at 08-16 -- using the fit dir",
                      flush=True)
            obs = [o for o in (parse_line(ln, strict=False) for ln in lines) if o]
            members.append(
                {
                    "trksub": v["trksub"],
                    "obscode": v["obscode"],
                    "night": v["night"],
                    "link_key": v["link_key"],
                    "ledger": v["ledger"],
                    "dt_years": v.get("dt_years"),
                    "single_rms": v.get("rms_joint"),
                    "n_obs": len(mjds),
                    "line_source": source,
                    "consumed_since_snapshot": key in dset,
                    "mjds": mjds,
                    "obs": [(o.mjd, o.ra_deg, o.dec_deg) for o in obs],
                }
            )
            joint_lines += lines
        if any(m["line_source"] == "MISSING" for m in members):
            results.append({"orbit_desig": desig, "members": members,
                            "status": "member_lines_missing"})
            print(f"{desig}: MISSING lines for a member; skipped", flush=True)
            continue

        tag = f"{args.tag_prefix}c{k:04d}"
        cfg = prepare_config_dir(shell, tag)
        run = run_fo(
            [_relabel(ln, tag) for ln in joint_lines],
            args.fit_root / tag,
            designations=[tag],
            shell=shell,
            config_dir=cfg,
            timeout=600,
            scratch_dir=f"$HOME/.cache/itf-linker-fo-work/{tag}",
        )
        cfit = run.results.get(tag) or next(iter(run.results.values()), None)
        if cfit is None:
            results.append({"orbit_desig": desig, "members": members,
                            "status": "fo_returned_nothing", "baseline": baseline})
            continue
        combined = fit_fields(cfit)

        # Per-tracklet used counts. A JD-window match is NOT enough here: sibling
        # tracklets from the same station and night (the PD152 pattern) share the
        # window, and Pan-STARRS pairs can even share the same exposures with
        # near-duplicate astrometry (measured: 0.03-0.16 arcsec apart). Each member
        # observation is therefore matched to residual rows by obscode + exact epoch
        # + observed position (the residual records carry RA/Dec), one row per obs,
        # nearest-position first.
        used_rows: set[int] = set()
        for m in members:
            n_used = n_found = 0
            for mjd, ra, dec in m["obs"]:
                jd = mjd + 2400000.5
                cosd = math.cos(math.radians(dec))
                best = None
                best_d = 1.5  # arcsec
                for ri, r in enumerate(cfit.residuals):
                    if ri in used_rows or r.get("obscode") != m["obscode"]:
                        continue
                    if abs(float(r.get("JD", 0)) - jd) > 2e-4:
                        continue
                    dra = abs((float(r.get("RA", 0)) - ra + 180.0) % 360.0 - 180.0)
                    dde = abs(float(r.get("Dec", 0)) - dec)
                    d = 3600.0 * math.hypot(dra * cosd, dde)
                    if d < best_d:
                        best_d = d
                        best = ri
                if best is not None:
                    used_rows.add(best)
                    n_found += 1
                    if cfit.residuals[best].get("incl"):
                        n_used += 1
            m["obs_in_resids"] = n_found
            m["obs_used"] = n_used
            m["fully_used"] = n_used == m["n_obs"] > 0
            del m["mjds"], m["obs"]

        # Sibling structure, surfaced for the reviewer: same-night pairs are weaker
        # corroboration than independent nights, and same-exposure near-duplicates
        # are weaker still (they re-measure the same photons).
        nights_seen: dict[tuple[str, int], int] = {}
        for m in members:
            k = (m["obscode"], m["night"])
            nights_seen[k] = nights_seen.get(k, 0) + 1
        shared = sum(1 for c in nights_seen.values() if c > 1)
        distinct_nights = len(nights_seen)

        obs_all = [o for o in (parse_line(ln, strict=False) for ln in joint_lines) if o]
        nights = {int(o.mjd + 0.5) for o in obs_all}
        arc_days = max(o.mjd for o in obs_all) - min(o.mjd for o in obs_all)
        strict = post_fit_gate(cfit, n_nights=len(nights))
        published = mpc_published_gate(cfit, n_nights=len(nights), arc_days=arc_days)

        base_arc = ((baseline.get("last_jd") or 0) - (baseline.get("first_jd") or 0)
                    if baseline.get("first_jd") else None)
        entry = {
            "orbit_desig": desig,
            "n_tracklets": len(members),
            "members": members,
            "baseline": baseline,
            "combined": combined,
            "gate_strict": strict.as_dict(),
            "gate_mpc_published": published.as_dict(),
            "all_tracklets_fully_used": all(m["fully_used"] for m in members),
            "arc_days_baseline": base_arc,
            "arc_days_combined": arc_days,
            "arc_extension_days": (round(arc_days - base_arc, 2)
                                   if base_arc is not None else None),
            "sigma_a_ratio": (combined["sigma_a"] / baseline["sigma_a"]
                              if combined.get("sigma_a") and baseline.get("sigma_a")
                              else None),
            "sigma_e_ratio": (combined["sigma_e"] / baseline["sigma_e"]
                              if combined.get("sigma_e") and baseline.get("sigma_e")
                              else None),
            "sigma_i_ratio": (combined["sigma_i"] / baseline["sigma_i"]
                              if combined.get("sigma_i") and baseline.get("sigma_i")
                              else None),
            "n_members_consumed": sum(1 for m in members
                                      if m["consumed_since_snapshot"]),
            "distinct_member_nights": distinct_nights,
            "shared_night_groups": shared,
            "fit_tag": tag,
            "baseline_tag": base_tag,
        }
        entry["tier"] = (
            "combined_pass" if entry["all_tracklets_fully_used"]
            and strict.as_dict().get("passes") else "combined_below_gate"
        )
        results.append(entry)
        print(f"{desig}: {len(members)} trk, rms {combined['rms']} "
              f"(base {baseline['rms']}), arc +{entry['arc_extension_days']} d, "
              f"sigma_a x{entry['sigma_a_ratio'] if entry['sigma_a_ratio'] is None else round(entry['sigma_a_ratio'], 3)}, "
              f"all-used={entry['all_tracklets_fully_used']}, "
              f"consumed {entry['n_members_consumed']}/{len(members)}", flush=True)

    doc = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ledgers": [str(p) for _, p in sources],
        "n_objects": len(multi),
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    n_pass = sum(1 for r in results if r.get("tier") == "combined_pass")
    print(f"combined_pass: {n_pass}/{len(results)}; wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
