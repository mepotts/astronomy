"""W4 -- the full-sky re-screen of the Hephaistos II selection.

Stage 1 (this file's `pull` mode): harvest the parent sample from the ESA Gaia
archive in sky tiles, applying only the two cuts that are cheap server-side and
that shrink the payload by ~15x:

    C1  Bailer-Jones EDR3 r_med_geo < 300 pc
    C2a W3 AND W4 have a measured profile-fit uncertainty (= a detection,
        AllWISE ph_qual not 'U')

Everything after that -- cc_flags, the star+Dyson-sphere RMSE grid, Gvar, RUWE,
ext_flg, classprob, the S/N >= 3.5 cut -- runs locally on the harvested rows,
in the paper's Table 4 order, so the funnel stays comparable stage-for-stage.

Design notes (why it looks like this):
  * ESA's anonymous ASYNC endpoint returned HTTP 500 on every job we submitted
    on 2026-08-18 (scripts/_w4_diag.py). M1's cost plan assumed async strips but
    only ever exercised SYNC. The driver therefore takes --mode {sync,async} and
    defaults to whatever the diagnostic proved works.
  * ESA sync fails at a hard ~181 s wall under load. MEASURED: that wall does
    NOT depend on tile size -- 215, 107 and 54 deg^2 tiles all failed at
    181.6 +- 0.3 s, while 215 and 107 deg^2 tiles succeeded at 93 s and 127 s.
    It is queue/load, not compute. So the right response to a failure is to
    RETRY (--retries high, --min-area huge), not to split; splitting doubles
    the number of queries without improving the odds. Splitting is kept as a
    last resort for tiles that fail repeatedly.
  * Every tile is checkpointed to data/w4/tiles/<id>.csv the moment it lands and
    the manifest is rewritten, so a session kill costs at most one tile.
  * Resume is automatic: re-running skips tiles already marked done.

Usage:
    python scripts/w4_screen.py pull  [--mode sync] [--tiles 24] [--rasplit 1]
                                      [--budget-min 120] [--join 6]
    python scripts/w4_screen.py status
    python scripts/w4_screen.py select        # local cuts on whatever landed
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
W4 = ROOT / "data" / "w4"
TILES = W4 / "tiles"
MANIFEST = W4 / "manifest.json"
W4.mkdir(parents=True, exist_ok=True)
TILES.mkdir(parents=True, exist_ok=True)

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"
SKY_DEG2 = 41252.96

COLS = """g.source_id, g.ra, g.dec, g.pmra, g.pmdec, g.parallax, g.ruwe,
    g.phot_g_mean_mag, g.phot_bp_mean_mag, g.phot_rp_mean_mag,
    g.phot_g_mean_flux, g.phot_g_mean_flux_error, g.phot_g_n_obs,
    g.classprob_dsc_combmod_star, d.r_med_geo, ab.allwise_oid,
    w.w1mpro, w.w2mpro, w.w3mpro, w.w4mpro,
    w.w1mpro_error, w.w2mpro_error, w.w3mpro_error, w.w4mpro_error,
    w.cc_flags, w.ext_flag, w.ph_qual"""
COLS_2MASS = ", t.designation AS tmass_designation, t.j_m, t.h_m, t.ks_m"

FROM3 = """FROM gaiadr3.gaia_source g
    JOIN external.gaiaedr3_distance d ON d.source_id = g.source_id
    JOIN gaiadr3.allwise_best_neighbour ab ON ab.source_id = g.source_id"""
JOIN_W = ("JOIN gaiadr1.allwise_original_valid w "
          "ON w.allwise_oid = ab.allwise_oid")
JOIN_T = ("JOIN gaiadr3.tmass_psc_xsc_best_neighbour tb "
          "ON tb.source_id = g.source_id "
          "JOIN gaiadr1.tmass_original_valid t "
          "ON t.designation = tb.original_ext_source_id")
WDET = "AND w.w3mpro_error IS NOT NULL AND w.w4mpro_error IS NOT NULL"


# ---------------------------------------------------------------- tiling ---
def make_tiles(n_dec: int, ra_split: int) -> list[dict]:
    """Equal-solid-angle dec bands, optionally split in RA."""
    s = np.linspace(-1.0, 1.0, n_dec + 1)
    decs = np.degrees(np.arcsin(s))
    ras = np.linspace(0.0, 360.0, ra_split + 1)
    tiles = []
    for i in range(n_dec):
        for j in range(ra_split):
            tiles.append(dict(
                id=f"d{i:02d}r{j:02d}", dec0=float(decs[i]),
                dec1=float(decs[i + 1]), ra0=float(ras[j]),
                ra1=float(ras[j + 1]),
                area=float((ras[j + 1] - ras[j]) / 360.0 * 4 * np.pi
                           * (s[i + 1] - s[i]) / 2 * (180 / np.pi) ** 2)))
    # Deterministic interleave so that a PARTIAL screen is an unbiased sample
    # of the sky (uniform in dec, RA and |b|) rather than a polar cap: the
    # funnel measured on whatever lands is then directly comparable to the
    # paper's all-sky rates.
    rng = np.random.default_rng(20260818)
    order = rng.permutation(len(tiles))
    return [tiles[k] for k in order]


def where_of(t: dict) -> str:
    w = f"WHERE g.dec BETWEEN {t['dec0']:.8f} AND {t['dec1']:.8f}"
    if not (t["ra0"] <= 0.0 and t["ra1"] >= 360.0):
        w += f" AND g.ra >= {t['ra0']:.8f} AND g.ra < {t['ra1']:.8f}"
    return w + " AND d.r_med_geo < 300"


def split(t: dict) -> list[dict]:
    """Halve a tile: in RA if it spans >45 deg of RA, else in dec."""
    if t["ra1"] - t["ra0"] > 45.0:
        m = 0.5 * (t["ra0"] + t["ra1"])
        a = dict(t, id=t["id"] + "a", ra1=m, area=t["area"] / 2)
        b = dict(t, id=t["id"] + "b", ra0=m, area=t["area"] / 2)
    else:
        s0, s1 = np.sin(np.radians([t["dec0"], t["dec1"]]))
        m = float(np.degrees(np.arcsin(0.5 * (s0 + s1))))
        a = dict(t, id=t["id"] + "a", dec1=m, area=t["area"] / 2)
        b = dict(t, id=t["id"] + "b", dec0=m, area=t["area"] / 2)
    return [a, b]


# ------------------------------------------------------------- manifest ---
def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"tiles": {}, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "params": {}}


def save_manifest(m: dict) -> None:
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=1, default=str))
    tmp.replace(MANIFEST)


# ----------------------------------------------------------------- pull ---
def pull(args: argparse.Namespace) -> None:
    svc = pyvo.dal.TAPService(GAIA_TAP)
    m = load_manifest()
    m["params"] = dict(mode=args.mode, n_dec=args.tiles, ra_split=args.rasplit,
                       join=args.join, budget_min=args.budget_min)
    base = make_tiles(args.tiles, args.rasplit)
    base_ids = {t["id"] for t in base}
    # A tile marked "split" has been superseded by its children, which carry the
    # sky; re-queuing the parent would duplicate rows its done children already
    # hold. Queue = un-done base tiles that were never split, PLUS any orphan
    # children from an earlier session that are still outstanding.
    queue = [t for t in base
             if m["tiles"].get(t["id"], {}).get("status")
             not in ("done", "split")]
    for tid, rec in m["tiles"].items():
        if tid in base_ids or rec.get("status") in ("done", "split"):
            continue
        queue.append({k: rec[k] for k in
                      ("id", "dec0", "dec1", "ra0", "ra1", "area")})
    print(f"W4 pull: {len(queue)} tiles to go (mode={args.mode}, "
          f"join={args.join}-table), budget {args.budget_min} min")
    t_start = time.time()
    n_done = n_fail = 0
    rows_total = 0

    while queue:
        if (time.time() - t_start) / 60.0 > args.budget_min:
            print(f"\n[budget] {args.budget_min} min reached; "
                  f"{len(queue)} tiles left. Re-run to resume.")
            break
        t = queue.pop(0)
        rec = m["tiles"].get(t["id"], {})
        if rec.get("status") == "done":
            continue
        cols = COLS + (COLS_2MASS if args.join == 6 else "")
        joins = JOIN_W + (" " + JOIN_T if args.join == 6 else "")
        q = f"SELECT {cols} {FROM3} {joins} {where_of(t)} {WDET}"
        t0 = time.time()
        try:
            run = svc.run_async if args.mode == "async" else svc.search
            df = run(q).to_table().to_pandas()
            dt = time.time() - t0
            path = TILES / f"{t['id']}.csv"
            df.to_csv(path, index=False)
            rows_total += len(df)
            n_done += 1
            m["tiles"][t["id"]] = dict(t, status="done", n=len(df),
                                       seconds=round(dt, 1),
                                       file=path.name)
            save_manifest(m)
            print(f"  [{t['id']}] {dt:6.1f} s  {len(df):7d} rows  "
                  f"({t['area']:.0f} deg2)   queue={len(queue)}")
        except Exception as e:  # noqa: BLE001
            dt = time.time() - t0
            rec = m["tiles"].get(t["id"], {})
            tries = rec.get("tries", 0) + 1
            msg = f"{type(e).__name__}: {str(e)[:160]}"
            print(f"  [{t['id']}] {dt:6.1f} s  FAIL ({tries}) {msg}")
            if tries < args.retries:
                m["tiles"][t["id"]] = dict(t, status="retry", tries=tries,
                                           last_error=msg)
                queue.append(t)   # back of the queue: let the server breathe
            elif t["area"] > args.min_area:
                kids = split(t)
                m["tiles"][t["id"]] = dict(t, status="split", tries=tries,
                                           last_error=msg,
                                           children=[k["id"] for k in kids])
                queue = kids + queue
                print(f"      -> split into {kids[0]['id']}, {kids[1]['id']} "
                      f"({kids[0]['area']:.0f} deg2 each)")
            else:
                n_fail += 1
                m["tiles"][t["id"]] = dict(t, status="failed", tries=tries,
                                           last_error=msg)
                print(f"      -> GIVING UP on {t['id']} "
                      f"({t['area']:.1f} deg2 lost)")
            save_manifest(m)

    done = [r for r in m["tiles"].values() if r.get("status") == "done"]
    area = sum(r["area"] for r in done)
    print(f"\npull: {len(done)} tiles done, {area:.0f} deg2 "
          f"({100 * area / SKY_DEG2:.1f}% of sky), "
          f"{sum(r['n'] for r in done)} W3W4-detected rows, "
          f"{n_fail} tiles abandoned")
    save_manifest(m)


# --------------------------------------------------------------- status ---
def status(_args: argparse.Namespace) -> None:
    m = load_manifest()
    if not m["tiles"]:
        print("no manifest yet")
        return
    by = {}
    for r in m["tiles"].values():
        by.setdefault(r.get("status", "?"), []).append(r)
    print(f"params: {m.get('params')}")
    for k, v in sorted(by.items()):
        a = sum(x.get("area", 0) for x in v)
        n = sum(x.get("n", 0) for x in v)
        print(f"  {k:8s} {len(v):4d} tiles  {a:9.0f} deg2  {n:9d} rows")
    done = by.get("done", [])
    if done:
        area = sum(r["area"] for r in done)
        secs = sum(r.get("seconds", 0) for r in done)
        print(f"\ncoverage {100 * area / SKY_DEG2:.2f}% of sky; "
              f"{secs / 60:.1f} min of query time; "
              f"mean {secs / max(len(done), 1):.0f} s/tile, "
              f"{secs / max(area, 1e-9) * SKY_DEG2 / 3600:.1f} h projected "
              f"for the full sky at this rate")


# --------------------------------------------------------------- repair ---
def repair(_args: argparse.Namespace) -> None:
    """Re-queue sky orphaned by an interrupted split.

    When a tile is split its children are pushed onto the in-memory queue but
    are not written to the manifest until they are attempted. If the run stops
    in between, those children vanish and their sky is silently lost. This
    finds every tile marked "split" that does not have a full set of DONE
    children and resets it to "retry", so the next pull re-covers it whole.
    Run it with the pull STOPPED (a live pull rewrites the manifest).
    """
    m = load_manifest()
    fixed, freed = [], 0.0
    done_ids = {k for k, v in m["tiles"].items() if v.get("status") == "done"}
    for tid, rec in sorted(m["tiles"].items()):
        if rec.get("status") != "split":
            continue
        kids = rec.get("children", [])
        if kids and all(k in done_ids for k in kids):
            continue                      # genuinely superseded, leave alone
        # drop any descendant records so the parent is re-pulled whole
        for k in list(m["tiles"]):
            if k.startswith(tid) and k != tid and k not in done_ids:
                m["tiles"].pop(k)
        m["tiles"][tid] = {kk: rec[kk] for kk in
                           ("id", "dec0", "dec1", "ra0", "ra1", "area")}
        m["tiles"][tid]["status"] = "retry"
        m["tiles"][tid]["tries"] = 0
        fixed.append(tid)
        freed += rec.get("area", 0.0)
    save_manifest(m)
    print(f"repair: re-queued {len(fixed)} orphaned tiles "
          f"({freed:.0f} deg2): {', '.join(fixed) if fixed else '(none)'}")
    print("NOTE: DONE children of a re-queued parent are kept; `select` "
          "de-duplicates on source_id, so the overlap is harmless.")


# --------------------------------------------------------------- select ---
def select(args: argparse.Namespace) -> None:
    """Run the local cuts (C2b..C6) on every tile harvested so far and write
    the funnel + the survivor list. Safe to run on a partial screen."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from w1_selection import fit_ds, load_pm13   # noqa: PLC0415

    m = load_manifest()
    done = [r for r in m["tiles"].values() if r.get("status") == "done"]
    if not done:
        print("nothing harvested yet")
        return
    area = sum(r["area"] for r in done)
    frames = []
    for r in done:
        p = TILES / r["file"]
        if p.exists() and p.stat().st_size > 2:
            frames.append(pd.read_csv(p))
    rows = pd.concat(frames, ignore_index=True)
    n_raw = len(rows)
    rows = rows.drop_duplicates(subset="source_id").reset_index(drop=True)
    if n_raw != len(rows):
        print(f"  dropped {n_raw - len(rows)} duplicate source_ids "
              f"(overlapping parent/child tiles)")
    print(f"loaded {len(rows)} W3W4-detected rows from {len(frames)} tiles "
          f"({area:.0f} deg2, {100 * area / SKY_DEG2:.2f}% of sky)")

    funnel = {"_area_deg2": area, "_sky_fraction": area / SKY_DEG2,
              "T2_w34det": len(rows)}

    rows["cc_ok"] = rows["cc_flags"].astype(str).str.strip().isin(["0000", "0"])
    funnel["T3_ccflags"] = int(rows["cc_ok"].sum())

    # Gvar from the screen's own flux-matched medians (0.2-mag bins) -- the
    # in-sample reference the paper presumably used; M1 showed the absolute
    # value is reference-sample dependent but the <2 cut outcome is not.
    bins = np.arange(np.nanmin(rows["phot_g_mean_mag"]) - 0.1,
                     np.nanmax(rows["phot_g_mean_mag"]) + 0.3, 0.2)
    rows["_bin"] = np.digitize(rows["phot_g_mean_mag"], bins)
    med = rows.groupby("_bin").agg(
        fp=("phot_g_mean_flux", "median"), ep=("phot_g_mean_flux_error", "median"),
        np_=("phot_g_n_obs", "median")).reset_index()
    rows = rows.merge(med, on="_bin", how="left")
    rows["gvar"] = (rows["fp"] * rows["phot_g_mean_flux_error"]
                    * np.sqrt(rows["phot_g_n_obs"])
                    / (rows["phot_g_mean_flux"] * rows["ep"]
                       * np.sqrt(rows["np_"])))
    rows["snr3"] = 1.0857 / rows["w3mpro_error"]
    rows["snr4"] = 1.0857 / rows["w4mpro_error"]
    rows["snr_ok"] = (rows["snr3"] >= 3.5) & (rows["snr4"] >= 3.5)
    rows["extra_ok"] = ((rows["gvar"] < 2) & (rows["ruwe"] < 1.4)
                        & (rows["ext_flag"] == 0)
                        & (rows["classprob_dsc_combmod_star"] > 0.9))
    # C5a (Halpha) is deferred to the survivor list: it needs a PK lookup on
    # gaiadr3.astrophysical_parameters and rejects a negligible fraction.

    need = ["phot_bp_mean_mag", "phot_rp_mean_mag", "j_m", "h_m", "ks_m",
            "w1mpro", "w2mpro", "w3mpro", "w4mpro", "r_med_geo"]
    have = [c for c in need if c in rows.columns]
    pre = rows[rows["cc_ok"]].dropna(subset=have).copy()
    funnel["T2_full10band"] = len(pre)
    pre["dmod"] = 5 * np.log10(pre["r_med_geo"] / 10.0)
    pre["M_G"] = pre["phot_g_mean_mag"] - pre["dmod"]
    infit = pre[(pre["M_G"] >= 6.0) & (pre["M_G"] <= 14.5)]
    funnel["T3_in_template_window"] = len(infit)

    pm = load_pm13()
    t0 = time.time()
    keep, n = [], 0
    lim = args.max_fits if args.max_fits > 0 else len(infit)
    gfloor = args.gamma_floor
    funnel["_gamma_floor"] = gfloor
    for _, r in infit.head(lim).iterrows():
        obs = {"BP": r["phot_bp_mean_mag"], "G": r["phot_g_mean_mag"],
               "RP": r["phot_rp_mean_mag"], "J": r["j_m"], "H": r["h_m"],
               "Ks": r["ks_m"], "W1": r["w1mpro"], "W2": r["w2mpro"],
               "W3": r["w3mpro"], "W4": r["w4mpro"]}
        oa = {k: v - r["dmod"] for k, v in obs.items()}
        f = fit_ds(oa, pm, 100, 700, gfloor, 0.90, nt=60, ng=30)
        n += 1
        if f["rmse"] <= 0.2:
            keep.append(dict(source_id=int(r["source_id"]), ra=r["ra"],
                             dec=r["dec"], rmse=f["rmse"], t_ds=f["t_ds"],
                             gamma=f["gamma"], M_G=r["M_G"],
                             snr3=r["snr3"], snr4=r["snr4"],
                             gvar=r["gvar"], ruwe=r["ruwe"],
                             extra_ok=bool(r["extra_ok"]),
                             snr_ok=bool(r["snr_ok"]),
                             r_med_geo=r["r_med_geo"],
                             w1mpro=r["w1mpro"], w2mpro=r["w2mpro"],
                             w3mpro=r["w3mpro"], w4mpro=r["w4mpro"]))
        if n % 2000 == 0:
            print(f"    fitted {n}/{min(lim, len(infit))} "
                  f"({time.time() - t0:.0f} s, {len(keep)} pass RMSE)")
    funnel["_fit_n"] = n
    funnel["_fit_seconds"] = round(time.time() - t0, 1)

    surv = pd.DataFrame(keep)
    funnel["T3_rmse"] = len(surv)
    if len(surv):
        s2 = surv[surv["extra_ok"]]
        funnel["T4_extra"] = len(s2)
        fin = s2[s2["snr_ok"]]
        funnel["T5_snr"] = len(fin)
        tag = args.tag or f"g{gfloor:g}"
        surv.to_csv(OUT / f"w4_rmse_survivors_{tag}.csv", index=False)
        fin.to_csv(OUT / f"w4_previsual_candidates_{tag}.csv", index=False)
    else:
        funnel["T4_extra"] = funnel["T5_snr"] = 0

    # published rates for the stage-by-stage comparison (Suazo 2024 Table 4)
    fsky = area / SKY_DEG2
    funnel["_paper_expected"] = {
        "parent_5e6": 5.0e6 * fsky, "w34det_3.2e5": 3.2e5 * fsky,
        "rmse_11243": 11243 * fsky, "extra_5137": 5137 * fsky,
        "snr_368": 368 * fsky, "final_7": 7 * fsky}
    tag = args.tag or f"g{gfloor:g}"
    OUT.joinpath(f"w4_funnel_{tag}.json").write_text(
        json.dumps(funnel, indent=2, default=str))
    print(json.dumps(funnel, indent=2, default=str))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--mode", default="sync", choices=["sync", "async"])
    p.add_argument("--tiles", type=int, default=24)
    p.add_argument("--rasplit", type=int, default=1)
    p.add_argument("--join", type=int, default=6, choices=[4, 6])
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--min-area", dest="min_area", type=float, default=25.0)
    p.add_argument("--budget-min", dest="budget_min", type=float, default=120.0)
    p.set_defaults(func=pull)
    p = sub.add_parser("status")
    p.set_defaults(func=status)
    p = sub.add_parser("repair")
    p.set_defaults(func=repair)
    p = sub.add_parser("select")
    p.add_argument("--max-fits", dest="max_fits", type=int, default=0)
    # 0.10 = the paper's STATED initial grid floor (Suazo+24 Sec 2.2);
    # 0.01 = the floor needed to admit their own candidate F (gamma=0.03).
    # M2 measures the funnel at both -- the difference is 10x in selectivity.
    p.add_argument("--gamma-floor", dest="gamma_floor", type=float, default=0.10)
    p.add_argument("--tag", default="")
    p.set_defaults(func=select)
    a = ap.parse_args()
    try:
        a.func(a)
    except KeyboardInterrupt:
        print("\ninterrupted -- manifest is current, re-run to resume")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
