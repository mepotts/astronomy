#!/usr/bin/env python3
"""M5 E-criteria: the registered ESS floor, applied to every run on disk.

Pre-registration: pta-mpta/M5-ess-floor-sw-census-and-the-paper.md section 1.1.

  E1   floor: run-level MINIMUM ESS over sampled parameters >= 100
  E1a  derivation: MCSE(68% interval edge)/half-width = 1.51/sqrt(ESS); 15%
       requires ESS >= 101, rounded to 100
  E2   NOT retroactive -- gate_met on disk is untouched; the floor is an extra
       reported column, printed beside the gate columns (the R3 discipline)
  E3   every M4 headline recomputed on the ESS-floored subset and reported as
       a PAIR (as-M4 / ESS-floored), never replaced
  E4   runs with ess_min in [80,125] are flagged borderline and NAMED
  E5   falsifier: do the runs the floor REJECTS agree with the published table
       worse than the ones it ADMITS?  If not, the floor is not diagnostic of
       accuracy and that is reported as a negative result about the floor.

    python scripts/m5_ess_floor.py
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m5" / "ess_floor.json"
TAB = json.loads((RES / "published_table.json").read_text())

FLOOR = 100                      # E1
BORDER = (80, 125)               # E4
GRID = np.linspace(-18.0, -11.0, 3001)
MIN_ACC = 0.05
PUB = (-14.28, 0.21)
VARIANTS = [("noise", "n1", 100_000), ("table", "t1", 50_000),
            ("fl", "f1", 50_000), ("swwide", "s1", 100_000)]
# M4's reported headline values, transcribed by hand so the comparison is a
# real check and not a re-print (the m4_note_numbers.py discipline).
M4 = dict(cov=dict(noise=83, table=82, fl=83, swwide=25),
          agree_params=(576, 588), agree_psr=(73, 83),
          dlnl_median=0.70, dlnl_pos=79, dlnl_neg=4,
          fl83=dict(map=-14.44, ci68=[-14.64, -14.35], n=83),
          table82=dict(map=-14.18, ci68=[-14.28, -14.13], n=82),
          seam_b=dict(n=82, dmap=0.259),
          swwide_resolved=10, swwide_created=0,
          f5_step=dict(before=1.92, after=0.37, psr="J1909-3744"))


def ess_min_of(summ):
    ch = summ.get("chain") or {}
    if ch.get("ess_min") is not None:
        return float(ch["ess_min"])
    e = [p.get("ess") for p in ch.get("params", []) if p.get("ess") is not None]
    return float(min(e)) if e else None


def load(variant, tag, gate_raw):
    rows = {}
    for f in sorted(RES.glob(f"*_{variant}_{tag}.summary.json")):
        psr = f.name.split("_")[0]
        s = json.loads(f.read_text())
        ch = s.get("chain") or {}
        em = ess_min_of(s)
        rows[psr] = dict(
            psr=psr, ess_min=em,
            gate_met=bool(s.get("gate_met")),
            gate_abs=bool(ch.get("raw_postburn", 0) >= gate_raw
                          and (ch.get("acc_rate") or 0) >= MIN_ACC
                          and ch.get("stable")),
            ess_ok=(em is not None and em >= FLOOR),
            border=(em is not None and BORDER[0] <= em <= BORDER[1]),
            raw=ch.get("raw_postburn", 0), acc=ch.get("acc_rate"),
            n_agree=s.get("n_agree"), n_compared=s.get("n_compared"),
            misses=[m["key"] for m in s.get("a2", []) if m.get("agree") is False],
            has_curn=(RES / f"{psr}_{variant}_{tag}.curn.npy").exists())
    return rows


def stats(dens):
    dens = np.clip(dens, 0, None)
    dens = dens / np.trapezoid(dens, GRID)
    cdf = np.cumsum(dens) * (GRID[1] - GRID[0])
    lo = float(GRID[np.searchsorted(cdf, 0.16)])
    hi = float(GRID[np.searchsorted(cdf, 0.84)])
    return dict(map=round(float(GRID[int(np.argmax(dens))]), 3),
                median=round(float(GRID[np.searchsorted(cdf, 0.5)]), 3),
                ci68=[round(lo, 3), round(hi, 3)], width=round(hi - lo, 3))


_KDE = {}


def logk(variant, tag, psr):
    key = (variant, psr)
    if key not in _KDE:
        s = np.load(RES / f"{psr}_{variant}_{tag}.curn.npy").astype(float)
        _KDE[key] = np.log(np.clip(gaussian_kde(s)(GRID), 1e-300, None))
    return _KDE[key]


def product(variant, tag, psrs):
    acc = np.zeros_like(GRID)
    for p in psrs:
        acc = acc + logk(variant, tag, p)
    return stats(np.exp(acc - acc.max()))


def consistent(a):
    lo, hi = a["ci68"]
    return bool(max(lo, PUB[0] - PUB[1]) <= min(hi, PUB[0] + PUB[1]))


def agree_rate(rows):
    a = sum(r["n_agree"] for r in rows if r.get("n_compared"))
    c = sum(r["n_compared"] for r in rows if r.get("n_compared"))
    return a, c, (100.0 * a / c if c else float("nan"))


def main():
    data = {v: load(v, t, g) for v, t, g in VARIANTS}
    res = dict(floor=FLOOR, border=list(BORDER), m4_reference=M4)

    # ---------------------------------------------------------------- E1/E2
    print(f"E1 -- registered floor: run-level minimum ESS >= {FLOOR}")
    print("E2 -- reported beside the gate columns; gate_met on disk untouched\n")
    print(f"{'variant':9s} {'gated':>6s} {'+ESS':>6s} {'fail':>5s} "
          f"{'median ESS':>11s} {'p05':>6s} {'p95':>6s}")
    cov = {}
    for v, tag, _ in VARIANTS:
        rows = list(data[v].values())
        g = [r for r in rows if r["gate_met"]]
        ok = [r for r in g if r["ess_ok"]]
        e = [r["ess_min"] for r in g if r["ess_min"] is not None]
        cov[v] = dict(gated=len(g), ess_ok=len(ok), fail=len(g) - len(ok),
                      ess_median=round(float(np.median(e)), 1) if e else None,
                      ess_p05=round(float(np.percentile(e, 5)), 1) if e else None,
                      ess_p95=round(float(np.percentile(e, 95)), 1) if e else None,
                      failed=[r["psr"] for r in g if not r["ess_ok"]],
                      borderline=[r["psr"] for r in g if r["border"]])
        c = cov[v]
        print(f"{v:9s} {c['gated']:6d} {c['ess_ok']:6d} {c['fail']:5d} "
              f"{c['ess_median']:11.1f} {c['ess_p05']:6.1f} {c['ess_p95']:6.1f}")
    res["coverage"] = cov

    # the absolute-gated / relative-only ESS split M4 published, re-derived
    nr = list(data["noise"].values())
    ea = [r["ess_min"] for r in nr if r["gate_abs"] and r["ess_min"]]
    eo = [r["ess_min"] for r in nr
          if r["gate_met"] and not r["gate_abs"] and r["ess_min"]]
    res["m4_r4_recheck"] = dict(
        abs_median=round(float(np.median(ea)), 1),
        rel_only_median=round(float(np.median(eo)), 1),
        m4_printed=dict(abs=347, rel_only=105))
    print(f"\nR4 re-derived: min-ESS median {np.median(ea):.0f} "
          f"(absolute-gated) vs {np.median(eo):.0f} (relative-only); "
          f"M4 printed 347 / 105")

    # ------------------------------------------------------------------- E4
    print("\nE4 -- borderline runs (ess_min in "
          f"[{BORDER[0]},{BORDER[1]}]), named:")
    for v, _, _ in VARIANTS:
        b = cov[v]["borderline"]
        if b:
            print(f"  {v:9s} ({len(b)}): "
                  + ", ".join(f"{p} ({data[v][p]['ess_min']:.0f})"
                              for p in sorted(b)))

    # ------------------------------------------------------------- E3 (a-c)
    diag = {}
    for f in (RES / "diag").glob("*.json"):
        d = json.loads(f.read_text())
        diag[d["psr"]] = d.get("dlnl_best_minus_pub")
    g = [r for r in nr if r["gate_met"]]
    ok = [r for r in g if r["ess_ok"]]
    bad = [r for r in g if not r["ess_ok"]]
    h = {}
    for label, sel in (("as_m4", g), ("ess_floored", ok)):
        a, c, pct = agree_rate(sel)
        full = sum(1 for r in sel
                   if r.get("n_compared") and r["n_agree"] == r["n_compared"])
        dl = [diag[r["psr"]] for r in sel if diag.get(r["psr"]) is not None]
        h[label] = dict(n_pulsars=len(sel), params_agree=a, params_total=c,
                        pct=round(pct, 2), pulsars_full=full,
                        dlnl_median=round(float(np.median(dl)), 3),
                        dlnl_pos=sum(1 for x in dl if x > 0),
                        dlnl_neg=sum(1 for x in dl if x < 0))
    res["headline_agreement"] = h
    print("\nE3(b,c) -- agreement and dlnL, as-M4 vs ESS-floored:")
    for k, d in h.items():
        print(f"  {k:12s} {d['n_pulsars']:3d} psr | "
              f"{d['params_agree']}/{d['params_total']} ({d['pct']:.1f}%) | "
              f"{d['pulsars_full']} full | dlnL median {d['dlnl_median']:+.2f} "
              f"({d['dlnl_pos']}+/{d['dlnl_neg']}-)")

    # ------------------------------------------------------------------- E5
    a1, c1, p1 = agree_rate(ok)
    a0, c0, p0 = agree_rate(bad)
    sig = 100 * ((p1 / 100) * (1 - p1 / 100) / c1) ** 0.5 if c1 else float("nan")
    if c0 == 0:
        verdict = "N/A -- the floor rejects no gated noise run"
    elif p0 < p1 - sig:
        verdict = ("PASS -- rejected runs agree WORSE, so the floor is "
                   "diagnostic of accuracy here")
    else:
        verdict = ("NEGATIVE -- rejected runs agree at least as well, so "
                   "ESS_min is NOT diagnostic of fidelity to the published "
                   "table in this problem; the floor is retained only as a "
                   "bound on our own Monte-Carlo error")
    res["e5_falsifier"] = dict(admitted=dict(agree=a1, total=c1, pct=round(p1, 2)),
                               rejected=dict(agree=a0, total=c0,
                                             pct=(round(p0, 2) if c0 else None)),
                               one_sigma_pct=round(sig, 2), verdict=verdict,
                               rejected_pulsars=[r["psr"] for r in bad])
    print(f"\nE5 falsifier: admitted {a1}/{c1} ({p1:.1f}%) vs "
          f"rejected {a0}/{c0} ({p0:.1f}% )" if c0 else
          f"\nE5 falsifier: admitted {a1}/{c1} ({p1:.1f}%), nothing rejected")
    print(f"  -> {verdict}")
    if bad:
        print("  rejected: " + ", ".join(
            f"{r['psr']} (ESS {r['ess_min']:.0f}, {r['n_agree']}/{r['n_compared']})"
            for r in sorted(bad, key=lambda r: r["ess_min"])))

    kc = Counter(k for r in bad for k in r["misses"])
    res["e5_rejected_miss_keys"] = dict(kc)

    # ----------------------------------------------------------- E3 (d,e,g)
    fl = data["fl"]
    tb = data["table"]
    prods = {}
    for label, pred in (("as_m4", lambda r: r["gate_met"]),
                        ("ess_floored", lambda r: r["gate_met"] and r["ess_ok"])):
        sfl = [p for p, r in fl.items() if pred(r) and r["has_curn"]]
        stb = [p for p, r in tb.items() if pred(r) and r["has_curn"]]
        pf = product("fl", "f1", sorted(sfl))
        pt = product("table", "t1", sorted(stb))
        common = sorted(set(sfl) & set(stb))
        cf = product("fl", "f1", common)
        ct = product("table", "t1", common)
        d = round(ct["map"] - cf["map"], 3)
        excl = (not (cf["ci68"][0] <= ct["map"] <= cf["ci68"][1])
                or not (ct["ci68"][0] <= cf["map"] <= ct["ci68"][1]))
        prods[label] = dict(
            fl=dict(n=len(sfl), **pf, consistent=consistent(pf)),
            table=dict(n=len(stb), **pt, consistent=consistent(pt)),
            common=dict(n=len(common), fl=cf, table=ct,
                        d_map_table_minus_fl=d,
                        significant=bool(abs(d) > 0.21 or excl),
                        rule="M3 doc 1.6 F4, carried over unchanged"))
    res["fl_products"] = prods
    print("\nE3(d,e) -- factorised-likelihood CURN, as-M4 vs ESS-floored:")
    for k, d in prods.items():
        print(f"  {k:12s} fl  n={d['fl']['n']:3d} MAP {d['fl']['map']:+.3f} "
              f"68% [{d['fl']['ci68'][0]:.2f},{d['fl']['ci68'][1]:.2f}] "
              f"w={d['fl']['width']:.2f} consistent={d['fl']['consistent']}")
        print(f"  {'':12s} tab n={d['table']['n']:3d} MAP {d['table']['map']:+.3f} "
              f"68% [{d['table']['ci68'][0]:.2f},{d['table']['ci68'][1]:.2f}] "
              f"w={d['table']['width']:.2f} consistent={d['table']['consistent']}")
        print(f"  {'':12s} seam-b on {d['common']['n']:3d} common: "
              f"dMAP {d['common']['d_map_table_minus_fl']:+.3f} "
              f"significant={d['common']['significant']}")

    # F5 growth curve on the ESS-floored fl set, same pre-registered seed 4
    gro = {}
    for label, pred in (("as_m4", lambda r: r["gate_met"]),
                        ("ess_floored", lambda r: r["gate_met"] and r["ess_ok"])):
        usable = sorted(p for p, r in fl.items() if pred(r) and r["has_curn"])
        rng = np.random.default_rng(4)
        order = [usable[i] for i in rng.permutation(len(usable))]
        acc, curve = np.zeros_like(GRID), []
        for i, p in enumerate(order, 1):
            acc = acc + logk("fl", "f1", p)
            st = stats(np.exp(acc - acc.max()))
            st.update(n=i, added=p)
            curve.append(st)
        steps = [(curve[i]["n"], curve[i]["added"],
                  round(curve[i - 1]["width"] - curve[i]["width"], 3))
                 for i in range(1, len(curve))]
        big = max(steps, key=lambda s: s[2]) if steps else None
        last = [c["map"] for c in curve[-11:]] if len(curve) >= 11 else []
        gro[label] = dict(n=len(order), biggest_width_drop=big,
                          final=curve[-1] if curve else None,
                          map_swing_last10=(round(max(last) - min(last), 3)
                                            if last else None),
                          curve=[dict(n=c["n"], added=c["added"], map=c["map"],
                                      width=c["width"], ci68=c["ci68"])
                                 for c in curve])
    res["f5_growth"] = gro
    print("\nE3(g) -- F5 growth curve (seed 4), as-M4 vs ESS-floored:")
    for k, d in gro.items():
        b = d["biggest_width_drop"]
        print(f"  {k:12s} n={d['n']:3d}  biggest single-step width drop: "
              f"{b[2]:.2f} dex at n={b[0]} when {b[1]} enters; "
              f"MAP swing over last 10 = {d['map_swing_last10']}")

    # ------------------------------------------------------------- E3 (f)
    sw = data["swwide"]
    nz = data["noise"]
    pairs = [p for p in sw if p in nz]
    resolved_all, resolved_ess, dropped = [], [], []
    for p in sorted(pairs):
        rn, rs = nz[p], sw[p]
        if not (rn["gate_met"] and rs["gate_met"]):
            continue
        fixed = [k for k in rn["misses"] if k not in rs["misses"]]
        resolved_all += [(p, k) for k in fixed]
        if rn["ess_ok"] and rs["ess_ok"]:
            resolved_ess += [(p, k) for k in fixed]
        elif fixed:
            dropped.append((p, rn["ess_min"], rs["ess_min"], fixed))
    res["swwide_resolved"] = dict(as_m4=len(resolved_all),
                                  ess_floored=len(resolved_ess),
                                  dropped_pairs=dropped)
    print(f"\nE3(f) -- swwide resolved misses: as-M4 {len(resolved_all)}, "
          f"ESS-floored {len(resolved_ess)}")
    for d in dropped:
        print(f"    dropped by the floor: {d[0]} "
              f"(noise ESS {d[1]:.0f}, swwide ESS {d[2]:.0f}) -> {d[3]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
