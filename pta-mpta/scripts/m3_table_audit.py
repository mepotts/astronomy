#!/usr/bin/env python3
"""M3 T-criteria: audit the published MPTA noise + deterministic tables
themselves (no sampling).

T1  how many of the tabulated values have a MAP outside their own printed
    68% interval (printed lower offset >= 0, or upper offset <= 0)
T2  how many tabulated log10 A_13/3 values are prior-floor artefacts:
    the paper's own Savage-Dickey reference point is p(log10 A_CURN < -16.5)
    as "clearly disfavoured", so a row whose 68% interval reaches below
    -16.5 is bounded by the prior, not measured.
"""
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TAB = json.loads((REPO / "results/m3/published_table.json").read_text())
OUT = REPO / "results" / "m3" / "table_audit.json"

FLOOR = -16.5   # the paper's own "clearly disfavoured" point


def main():
    n_vals = 0
    outside = []
    zero_edge = []
    per_key = Counter()
    per_key_tot = Counter()
    for psr, rec in sorted(TAB.items()):
        for key, v in rec["pub"].items():
            if not isinstance(v, list) or len(v) != 3:
                continue
            m, lo, hi = v
            n_vals += 1
            per_key_tot[key] += 1
            # STRICT: a printed offset of exactly -0.00 / +0.00 is a
            # rounding artefact of the printing precision, not a MAP outside
            # its interval. Only strictly wrong-signed offsets are counted.
            if lo > 0 or hi < 0:
                outside.append(dict(psr=psr, key=key, map=m, lo=lo, hi=hi,
                                    side="low" if lo > 0 else "high"))
                per_key[key] += 1
            elif lo == 0 or hi == 0:
                zero_edge.append(dict(psr=psr, key=key, map=m, lo=lo, hi=hi))

    print(f"    ({len(zero_edge)} further values print an offset of exactly "
          f"0.00 on one side - rounding, not a violation; excluded)")
    print(f"T1: {len(outside)} of {n_vals} tabulated values have a MAP "
          f"outside their own printed 68% interval "
          f"({100*len(outside)/n_vals:.1f}%)")
    print("    by parameter:", dict(per_key.most_common()))
    print("    (denominators:", dict(per_key_tot.most_common()), ")")
    psrs_hit = sorted({o["psr"] for o in outside})
    print(f"    affecting {len(psrs_hit)} of {len(TAB)} pulsars")
    for o in sorted(outside, key=lambda o: (o["key"], o["psr"]))[:40]:
        print(f"      {o['psr']:12s} {o['key']:16s} "
              f"MAP {o['map']:9.2f}  [{o['map']+o['lo']:.2f}, "
              f"{o['map']+o['hi']:.2f}]  ({o['side']} side)")

    # T2 — prior-floor A_13/3 rows
    floorish, measured = [], []
    for psr, rec in sorted(TAB.items()):
        v = rec["pub"].get("gw13_log10_A")
        if not isinstance(v, list):
            continue
        m, lo, hi = v
        loedge = m + lo
        (floorish if loedge < FLOOR else measured).append(
            dict(psr=psr, map=m, lo=loedge, hi=m + hi, width=hi - lo))
    print(f"\nT2: {len(floorish)} of {len(floorish)+len(measured)} tabulated "
          f"log10 A_13/3 rows have their 68% interval reaching below "
          f"{FLOOR} (the paper's own 'clearly disfavoured' point)")
    print(f"    -> {len(measured)} rows are genuinely bounded on both sides")
    widths = sorted(r["width"] for r in floorish)
    if widths:
        print(f"    prior-limited rows: 68% width min {widths[0]:.2f} "
              f"median {widths[len(widths)//2]:.2f} max {widths[-1]:.2f} dex")
    print("    both-sides-bounded rows:")
    for r in sorted(measured, key=lambda r: r["map"]):
        print(f"      {r['psr']:12s} {r['map']:7.2f} "
              f"[{r['lo']:.2f}, {r['hi']:.2f}]  width {r['width']:.2f}")

    OUT.write_text(json.dumps(dict(
        n_values=n_vals, n_outside=len(outside), outside=outside,
        n_zero_edge=len(zero_edge), zero_edge=zero_edge,
        outside_by_key=dict(per_key), totals_by_key=dict(per_key_tot),
        n_pulsars_hit=len(psrs_hit),
        a13_floor_point=FLOOR,
        a13_prior_limited=[r["psr"] for r in floorish],
        a13_measured=measured), indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
