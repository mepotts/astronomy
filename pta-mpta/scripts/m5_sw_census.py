#!/usr/bin/env python3
"""M5 S-criteria: the re-specified solar-wind control and the prior-propping
census over the SW_Full pulsars.

Pre-registration: pta-mpta/M5-ess-floor-sw-census-and-the-paper.md section 1.2.

M4's registered control V5 keyed on the SIGN of the published gamma_SW as a
proxy for "measured".  It is not one: J1744-1134 has a published +0.91 and its
68% width still goes 1.52 -> 4.42 when the prior is widened, because the narrow
posterior WAS the prior edge.  S1 re-specifies the control by posterior width
relative to prior width, and S3 turns the same measurement into a census of the
whole column.

  S1  MEASURED  iff O_narrow < 0.25 and O_wide < 0.25, where
      O_narrow = W68(gamma_SW | U(0,7))/7 and O_wide = W68(gamma_SW | U(-4,4))/8
  S2  control test on the MEASURED set: |d median gamma_SW| and
      |d median log10A_SW| < 0.19 (M3 6.5 yardstick), and nothing that agreed
      may start disagreeing
  S3  census over ALL 26 SW_Full pulsars; primary number = PRIOR-PROPPED +
      UNCONSTRAINED-BOTH, i.e. rows that are NOT a measurement of gamma_SW
  S4  sensitivity over R in {1.5,2,3} x occupancy in {0.20,0.25,0.33}
  S5  table-only cross-check from the published printed widths alone
  S6  scope: this measures OUR posteriors under TWO PRIORS WE CHOSE
  S7  coverage stated exactly

    python scripts/m5_sw_census.py
"""
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m5" / "sw_census.json"
TAB = json.loads((RES / "published_table.json").read_text())

W_NARROW, W_WIDE = 7.0, 8.0          # U(0,7) and U(-4,4) prior widths
OCC = 0.25                            # inherited unchanged from M4 4.3
RATIO = 2.0                           # S3
YARDSTICK = 0.19                      # M3 6.5
# candidate priors a reproducer might apply, for the S5 table-only check
CANDIDATES = {"U(0,7)": 7.0, "U(-2,1)": 3.0, "U(-4,4)": 8.0, "U(-6,5)": 11.0}


def load(psr, kind):
    f = RES / (f"{psr}_noise_n1.summary.json" if kind == "narrow"
               else f"{psr}_swwide_s1.summary.json")
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    if not s.get("gate_met"):
        return None
    return s


def par(s, stem):
    for r in s["chain"]["params"]:
        if r["param"].split("_", 1)[-1] == stem or r["param"] == stem:
            lo, hi = r["ci68"]
            return dict(median=r["median"], w68=float(hi - lo), ci68=[lo, hi])
    return None


def a2map(s):
    return {r["key"]: r for r in s.get("a2", [])}


def classify(o_n, o_w, ratio, occ=OCC, rthr=RATIO):
    if o_n < occ and o_w < occ:
        return "MEASURED"
    if ratio >= rthr:
        return "PRIOR-PROPPED"
    if o_n >= occ and o_w >= occ:
        return "UNCONSTRAINED-BOTH"
    return "OTHER"


def main():
    swf = sorted(p for p, r in TAB.items() if r["model"]["sw"] == "full")
    rows, missing = [], []
    for p in swf:
        a, b = load(p, "narrow"), load(p, "wide")
        if a is None or b is None:
            missing.append(dict(psr=p, narrow=a is not None, wide=b is not None))
            continue
        ga, gb = par(a, "sw_gp_gamma"), par(b, "sw_gp_gamma")
        aa, ab = par(a, "sw_gp_log10_A"), par(b, "sw_gp_log10_A")
        o_n, o_w = ga["w68"] / W_NARROW, gb["w68"] / W_WIDE
        ratio = gb["w68"] / ga["w68"]
        pub = TAB[p]["pub"]["sw_gamma"]
        ra, rb = a2map(a), a2map(b)
        broke = [k for k in rb
                 if ra.get(k, {}).get("agree") is True
                 and rb[k].get("agree") is False]
        rows.append(dict(
            psr=p, pub_gamma=pub[0], pub_w68=round(pub[2] - pub[1], 3),
            w_narrow=round(ga["w68"], 3), w_wide=round(gb["w68"], 3),
            occ_narrow=round(o_n, 3), occ_wide=round(o_w, 3),
            ratio=round(ratio, 3),
            wA_narrow=round(aa["w68"], 3), wA_wide=round(ab["w68"], 3),
            d_gamma=round(gb["median"] - ga["median"], 3),
            d_logA=round(ab["median"] - aa["median"], 3),
            broke=broke, klass=classify(o_n, o_w, ratio)))

    n_cmp = len(rows)
    print(f"S7 -- coverage: {n_cmp} of {len(swf)} SW_Full pulsars have BOTH "
          f"runs gated.")
    if missing:
        print("  not compared: "
              + ", ".join(f"{m['psr']} (narrow={m['narrow']}, wide={m['wide']})"
                          for m in missing))

    # ------------------------------------------------------------ S1 + S2
    meas = [r for r in rows if r["klass"] == "MEASURED"]
    worst_g = max((abs(r["d_gamma"]) for r in meas), default=0.0)
    worst_a = max((abs(r["d_logA"]) for r in meas), default=0.0)
    broke_any = [(r["psr"], r["broke"]) for r in rows if r["broke"]]
    ok = (worst_g < YARDSTICK and worst_a < YARDSTICK and not broke_any)
    print(f"\nS1 -- re-specified control set (MEASURED, occupancy < {OCC} "
          f"under BOTH priors): {len(meas)} pulsars")
    print("  " + ", ".join(r["psr"] for r in meas))
    print(f"S2 -- control test against the {YARDSTICK} yardstick:")
    for r in sorted(meas, key=lambda r: -abs(r["d_gamma"])):
        print(f"    {r['psr']:13s} d gamma {r['d_gamma']:+.3f}  "
              f"d log10A {r['d_logA']:+.3f}  "
              f"widths {r['w_narrow']:.2f} -> {r['w_wide']:.2f}")
    print(f"  worst |d gamma| {worst_g:.3f}, worst |d log10A| {worst_a:.3f}, "
          f"parameters broken by the wider prior: {len(broke_any)}")
    print(f"  VERDICT: {'PASS' if ok else 'FAIL'}"
          + ("" if ok else "  -> M4's V4 resolve count is VOID again"))

    # ---------------------------------------------------------------- S3
    order = {"MEASURED": 0, "PRIOR-PROPPED": 1, "UNCONSTRAINED-BOTH": 2,
             "OTHER": 3}
    print(f"\nS3 -- the census, all {n_cmp} compared SW_Full pulsars "
          f"(gamma_SW under U(0,7) vs U(-4,4)):")
    print(f"  {'pulsar':13s} {'pub g':>6s} {'pubW':>5s} {'W|U(0,7)':>9s} "
          f"{'W|U(-4,4)':>10s} {'R':>5s} {'occN':>5s} {'occW':>5s} "
          f"{'A wid n->w':>13s}  class")
    for r in sorted(rows, key=lambda r: (order[r["klass"]], -r["ratio"])):
        print(f"  {r['psr']:13s} {r['pub_gamma']:+6.2f} {r['pub_w68']:5.2f} "
              f"{r['w_narrow']:9.2f} {r['w_wide']:10.2f} {r['ratio']:5.2f} "
              f"{r['occ_narrow']:5.2f} {r['occ_wide']:5.2f} "
              f"{r['wA_narrow']:5.2f}->{r['wA_wide']:5.2f}  {r['klass']}")
    counts = {k: sum(1 for r in rows if r["klass"] == k) for k in order}
    not_meas = counts["PRIOR-PROPPED"] + counts["UNCONSTRAINED-BOTH"]
    print(f"\n  class counts: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    print(f"  >>> PRIMARY (registered S3): {not_meas} of {n_cmp} published "
          f"gamma_SW rows are NOT a measurement of gamma_SW under this "
          f"reproduction "
          f"({counts['PRIOR-PROPPED']} prior-propped + "
          f"{counts['UNCONSTRAINED-BOTH']} unconstrained under both priors)")
    for k in ("MEASURED", "PRIOR-PROPPED", "UNCONSTRAINED-BOTH", "OTHER"):
        sel = [r for r in rows if r["klass"] == k]
        if sel:
            print(f"    {k:20s} median log10A_SW 68% width "
                  f"{np.median([r['wA_narrow'] for r in sel]):.2f} dex under "
                  f"U(0,7) -> {np.median([r['wA_wide'] for r in sel]):.2f} "
                  f"under U(-4,4)")

    # ---------------------------------------------------------------- S4
    print("\nS4 -- sensitivity of the primary number (registered grid):")
    grid = {}
    for occ in (0.20, 0.25, 0.33):
        for rt in (1.5, 2.0, 3.0):
            c = {}
            for r in rows:
                k = classify(r["occ_narrow"], r["occ_wide"], r["ratio"], occ, rt)
                c[k] = c.get(k, 0) + 1
            v = c.get("PRIOR-PROPPED", 0) + c.get("UNCONSTRAINED-BOTH", 0)
            grid[f"occ{occ}_R{rt}"] = dict(primary=v, counts=c)
            print(f"    occupancy {occ:.2f}  R>={rt:.1f}  ->  primary {v:2d} "
                  f"({c.get('MEASURED',0)} measured, "
                  f"{c.get('PRIOR-PROPPED',0)} propped, "
                  f"{c.get('UNCONSTRAINED-BOTH',0)} unconstrained, "
                  f"{c.get('OTHER',0)} other)")
    vals = [g["primary"] for g in grid.values()]
    # Registered wording (S4): "if the primary number MOVES BY MORE THAN
    # +/-2 ROWS across that grid, it is quoted as a range".  That is a
    # deviation from the point value, not a total spread -- the first
    # implementation here tested the total spread against 4, which is a looser
    # reading, and the difference decides the answer.  Fixed to the
    # registration; declared in M5 section 1.5.
    dev = max(abs(v - not_meas) for v in vals)
    quote = (f"{not_meas}" if dev <= 2 else f"{min(vals)}-{max(vals)}")
    print(f"    grid range {min(vals)}-{max(vals)}; largest deviation from "
          f"the point value {not_meas} is {dev} row(s) "
          f"(registered rule: quote as a RANGE if it moves by more than "
          f"+/-2 rows) -> quote '{quote}'")
    # The COMPLEMENT is the more stable statistic and is reported beside it:
    # the rows that leave the primary count at R>=3 do not become
    # measurements, they fall into OTHER, so the primary count understates
    # at the strict end of the grid while MEASURED barely moves.
    mvals = [g["counts"].get("MEASURED", 0) for g in grid.values()]
    print(f"    complement (rows that ARE measurements of gamma_SW): "
          f"{counts['MEASURED']} at the registered thresholds, "
          f"{min(mvals)}-{max(mvals)} across the whole grid")

    # ---------------------------------------------------------------- S5
    print("\nS5 -- table-only cross-check: the PUBLISHED printed gamma_SW 68% "
          "widths, as a fraction of each candidate prior range")
    tonly = {}
    for name, w in CANDIDATES.items():
        n_un = sum(1 for r in rows if r["pub_w68"] / w >= OCC)
        tonly[name] = n_un
        print(f"    under {name:8s} (width {w:4.1f}): "
              f"{n_un} of {n_cmp} printed intervals occupy >= {OCC:.0%} "
              f"of the prior")
    agree_flag = sum(1 for r in rows
                     if (r["pub_w68"] / W_WIDE >= OCC)
                     == (r["klass"] != "MEASURED"))
    print(f"    agreement between the table-only flag (under U(-4,4)) and the "
          f"chain-based class: {agree_flag} of {n_cmp}")
    diverge = [r["psr"] for r in rows
               if (r["pub_w68"] / W_WIDE >= OCC) != (r["klass"] != "MEASURED")]
    if diverge:
        print(f"    divergent rows (reported, not reconciled): "
              + ", ".join(diverge))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(
        n_swfull=len(swf), n_compared=n_cmp, missing=missing,
        occupancy_threshold=OCC, ratio_threshold=RATIO,
        yardstick=YARDSTICK,
        priors=dict(narrow="gamma_SW ~ U(0,7)", wide="gamma_SW ~ U(-4,4)"),
        rows=rows, counts=counts, primary=not_meas,
        control=dict(set=[r["psr"] for r in meas], n=len(meas),
                     worst_d_gamma=round(worst_g, 3),
                     worst_d_logA=round(worst_a, 3),
                     broke=broke_any, verdict=("PASS" if ok else "FAIL")),
        sensitivity=dict(grid=grid, spread=[min(vals), max(vals)],
                         max_deviation=dev, quote=quote,
                         measured_range=[min(mvals), max(mvals)]),
        table_only=dict(counts=tonly, agreement=agree_flag,
                        divergent=diverge)), indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
