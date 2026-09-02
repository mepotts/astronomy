#!/usr/bin/env python3
"""M4 V4/V5/V6: the registered gamma_SW wide-prior variant, measured against
the registered campaign.

Pre-registration: M4-finish-the-array.md section 1.3.
  registered campaign  `<psr>_noise_n1`    gamma_SW ~ U(0, 7)
  registered variant   `<psr>_swwide_s1`   gamma_SW ~ U(-4, 4)   <- V1
Everything else identical.  The variant NEVER replaces the campaign: V6 forbids
recomputing the headline agreement statistic with the variant substituted in,
so this script prints the two side by side with the prior in every row label.

V4  how many of the campaign's misses the wide prior resolves, and how many
    it creates.
V5  the internal control -- the 7 SW_Full pulsars whose published gamma_SW is
    comfortably positive and whose 68% interval does not cross zero must barely
    move (< 0.19, the M3 section 6.5 run-to-run yardstick), and no
    currently-agreeing parameter anywhere may start disagreeing.  Either
    failure voids V4.

    python scripts/m4_swwide_compare.py
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m4" / "swwide.json"
TAB = json.loads((RES / "published_table.json").read_text())
YARDSTICK = 0.19        # M3 section 6.5: 90th pct of our own repeat difference


def summ(psr, kind):
    f = RES / (f"{psr}_noise_n1.summary.json" if kind == "reg"
               else f"{psr}_swwide_s1.summary.json")
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    if not s.get("gate_met"):
        return None
    return s


def a2map(s):
    return {r["key"]: r for r in s.get("a2", [])}


def medians(s):
    return {r["param"].split("_", 1)[-1]: r["median"]
            for r in s["chain"]["params"]}


def main():
    swf = sorted(p for p, r in TAB.items() if r["model"]["sw"] == "full")
    neg, cross, clean = [], [], []
    for p in swf:
        g = TAB[p]["pub"]["sw_gamma"]
        if g[0] < 0:
            neg.append(p)
        elif g[0] + g[1] < 0:
            cross.append(p)
        else:
            clean.append(p)
    print(f"SW_Full set: {len(swf)} pulsars = {len(neg)} negative gamma_SW + "
          f"{len(cross)} interval crossing 0 + {len(clean)} clean (the V5 "
          f"control)")
    print(f"  V5 control set: {', '.join(clean)}")

    rows, resolved, created, missing = [], [], [], []
    for p in swf:
        a, b = summ(p, "reg"), summ(p, "sw")
        if a is None or b is None:
            missing.append(dict(psr=p, registered=a is not None,
                                variant=b is not None))
            continue
        ra, rb = a2map(a), a2map(b)
        keys = sorted(set(ra) | set(rb))
        miss_a = [k for k in keys if ra.get(k, {}).get("agree") is False]
        miss_b = [k for k in keys if rb.get(k, {}).get("agree") is False]
        fixed = [k for k in miss_a if k not in miss_b]
        broke = [k for k in miss_b if k not in miss_a]
        resolved += [(p, k) for k in fixed]
        created += [(p, k) for k in broke]
        ma, mb = medians(a), medians(b)
        dg = (mb.get("sw_gp_gamma", mb.get("gamma_sw")) or 0) - \
             (ma.get("sw_gp_gamma", ma.get("gamma_sw")) or 0)
        da = (mb.get("sw_gp_log10_A", mb.get("log10_A_sw")) or 0) - \
             (ma.get("sw_gp_log10_A", ma.get("log10_A_sw")) or 0)
        rows.append(dict(
            psr=p, klass=("negative" if p in neg else
                          "crosses-0" if p in cross else "clean"),
            pub_gamma=TAB[p]["pub"]["sw_gamma"][0],
            n_agree_reg=a.get("n_agree"), n_cmp_reg=a.get("n_compared"),
            n_agree_var=b.get("n_agree"), n_cmp_var=b.get("n_compared"),
            miss_reg=miss_a, miss_var=miss_b, fixed=fixed, broke=broke,
            d_gamma_sw=round(dg, 3), d_log10A_sw=round(da, 3),
            raw_var=b["chain"]["raw_postburn"], acc_var=b["chain"]["acc_rate"]))

    if not rows:
        print("\nNo pulsar has BOTH runs gated yet -- nothing to compare.")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(dict(compared=0, missing=missing), indent=1))
        return

    print(f"\n{len(rows)} of {len(swf)} SW_Full pulsars have both runs gated. "
          f"V6: the left column is gamma_SW ~ U(0,7) (registered campaign), "
          f"the right is gamma_SW ~ U(-4,4) (registered variant).")
    print(f"\n{'pulsar':13s} {'class':10s} {'pub g_SW':>9s} "
          f"{'U(0,7)':>8s} {'U(-4,4)':>8s}  {'d g_SW':>7s} {'d A_SW':>7s}  "
          f"resolved / created")
    for r in sorted(rows, key=lambda r: (r["klass"], r["psr"])):
        print(f"{r['psr']:13s} {r['klass']:10s} {r['pub_gamma']:9.2f} "
              f"{r['n_agree_reg']:4d}/{r['n_cmp_reg']:<3d} "
              f"{r['n_agree_var']:4d}/{r['n_cmp_var']:<3d}  "
              f"{r['d_gamma_sw']:+7.2f} {r['d_log10A_sw']:+7.2f}  "
              f"{','.join(r['fixed']) or '-'} / {','.join(r['broke']) or '-'}")

    # ---- V5 control -------------------------------------------------------
    ctrl = [r for r in rows if r["klass"] == "clean"]
    worst = max((max(abs(r["d_gamma_sw"]), abs(r["d_log10A_sw"])), r["psr"])
                for r in ctrl) if ctrl else (0.0, None)
    v5_move = worst[0] <= YARDSTICK
    v5_nobreak = not created
    # an empty control set is UNTESTED, not PASS -- a vacuous pass here would
    # be exactly the kind of free win R3/V5 exist to prevent
    v5 = ("UNTESTED (no control pulsar gated yet)" if not ctrl
          else "PASS" if (v5_move and v5_nobreak) else "FAIL")
    print(f"\nV5 control ({len(ctrl)} clean pulsars): largest |move| in "
          f"gamma_SW or log10 A_SW = {worst[0]:.3f} on {worst[1]} "
          f"(yardstick {YARDSTICK}) -> {'ok' if v5_move else 'FAIL'}")
    print(f"V5 no-new-misses: {len(created)} parameters started disagreeing "
          f"-> {'ok' if v5_nobreak else 'FAIL'}"
          + (f" ({created})" if created else ""))
    print(f"V5 VERDICT: {v5}"
          + ("  -- V4's count is reported VOID" if v5 == "FAIL" else
             "  -- V4's count stands, but its control clause is not yet "
             "exercised and must be quoted with that caveat"
             if v5.startswith("UNTESTED") else ""))

    # ---- V4 ---------------------------------------------------------------
    tot_reg = sum(len(r["miss_reg"]) for r in rows)
    tot_var = sum(len(r["miss_var"]) for r in rows)
    print(f"\nV4: over the {len(rows)} compared pulsars the registered "
          f"campaign misses {tot_reg} parameters under gamma_SW ~ U(0,7); "
          f"the variant misses {tot_var} under U(-4,4).")
    print(f"  RESOLVED by the wide prior ({len(resolved)}): "
          + (", ".join(f"{p}:{k}" for p, k in resolved) or "none"))
    print(f"  CREATED by the wide prior ({len(created)}): "
          + (", ".join(f"{p}:{k}" for p, k in created) or "none"))
    if missing:
        print(f"\n  not compared ({len(missing)}): "
              + ", ".join(m["psr"] for m in missing))

    # ---- POST-HOC (declared, not pre-registered) --------------------------
    # V5's control set was defined by the SIGN of the published gamma_SW.
    # If that is the wrong proxy for "data-constrained", the tell is that a
    # control pulsar's own posterior WIDENS when the prior is widened -- i.e.
    # its apparent constraint was the prior edge, not the data.
    print("\nPOST-HOC (declared): how much of each gamma_SW posterior was the "
          "prior holding up?")
    widen = []
    for r in rows:
        a = summ(r["psr"], "reg")
        b = summ(r["psr"], "sw")
        wa = {p["param"].split("_", 1)[-1]: p for p in a["chain"]["params"]}
        wb = {p["param"].split("_", 1)[-1]: p for p in b["chain"]["params"]}
        g0, g1 = wa["sw_gp_gamma"]["w68"], wb["sw_gp_gamma"]["w68"]
        a0, a1 = wa["sw_gp_log10_A"]["w68"], wb["sw_gp_log10_A"]["w68"]
        widen.append(dict(psr=r["psr"], klass=r["klass"],
                          w_gamma_narrow=g0, w_gamma_wide=g1,
                          ratio=round(g1 / g0, 2) if g0 else None,
                          w_A_narrow=a0, w_A_wide=a1))
    widen.sort(key=lambda d: -(d["ratio"] or 0))
    for d in widen:
        if d["ratio"] and d["ratio"] > 2:
            print(f"  {d['psr']:13s} {d['klass']:10s} gamma_SW 68% width "
                  f"{d['w_gamma_narrow']:.2f} -> {d['w_gamma_wide']:.2f} "
                  f"({d['ratio']:.1f}x), log10A_SW {d['w_A_narrow']:.2f} -> "
                  f"{d['w_A_wide']:.2f}")
    n2 = sum(1 for d in widen if d["ratio"] and d["ratio"] > 2)
    print(f"  {n2} of {len(widen)} compared SW_Full pulsars widen their "
          f"gamma_SW 68% interval by more than 2x -- for those, the narrow "
          f"posterior under U(0,7) was the prior edge, not a measurement")
    res_widen = widen

    # POST-HOC re-specification of the control (declared; the REGISTERED V5
    # verdict above stands unchanged).  A control for "does widening the prior
    # perturb a measured parameter?" must be built from parameters the data
    # actually measure.  Objective rule: gamma_SW 68% width below 25% of the
    # prior width under BOTH priors (1.75 of 7, and 2.0 of 8).
    byname = {d["psr"]: d for d in widen}
    dc = [r for r in rows
          if byname[r["psr"]]["w_gamma_narrow"] < 0.25 * 7
          and byname[r["psr"]]["w_gamma_wide"] < 0.25 * 8]
    if dc:
        w2 = max((max(abs(r["d_gamma_sw"]), abs(r["d_log10A_sw"])), r["psr"])
                 for r in dc)
        ok2 = w2[0] <= YARDSTICK
        print(f"\nPOST-HOC control, data-constrained gamma_SW only "
              f"({len(dc)} pulsars: {', '.join(r['psr'] for r in dc)}): "
              f"largest |move| {w2[0]:.3f} on {w2[1]} -> "
              f"{'ok' if ok2 else 'FAIL'}")
        print("  (declared post-hoc; it does NOT overturn the registered V5 "
              "verdict, it diagnoses it)")
    else:
        w2, ok2 = (0.0, None), None

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(
        n_swfull=len(swf), negative=neg, crossing=cross, control=clean,
        compared=len(rows), rows=rows, missing=missing,
        resolved=resolved, created=created,
        n_miss_registered=tot_reg, n_miss_variant=tot_var,
        v5=dict(worst_move=worst[0], worst_psr=worst[1],
                yardstick=YARDSTICK, verdict=v5),
        posthoc_widening=res_widen,
        posthoc_control=dict(pulsars=[r["psr"] for r in dc],
                             worst_move=w2[0], worst_psr=w2[1],
                             ok=ok2,
                             rule="gamma_SW 68% width < 25% of the prior "
                                  "width under BOTH priors"),
        priors=dict(registered="gamma_SW ~ U(0,7)",
                    variant="gamma_SW ~ U(-4,4)")), indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
