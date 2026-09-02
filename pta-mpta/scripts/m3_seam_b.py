#!/usr/bin/env python3
"""M3 seam (b): intrinsic achromatic red vs the fixed-13/3 term.

Pre-registered B-criteria: M3-noise-criticism.md section 1.5.

  Delta_b(psr) = median(log10 A_13/3 | `fl`) - median(log10 A_13/3 | `table`)

`table` = the favoured model exactly as the noise table reports it;
`fl`    = the same model PLUS a free achromatic red process where the favoured
          model lacks one (what the collaboration itself does for both of its
          common-signal analyses). Whites are held at identical values in both,
          so the added red process is the ONLY difference.

B3 null control: for the pulsars whose favoured model ALREADY has a free red
process the two runs are the same model, so their |Delta_b| is pure sampler
noise and its 95th percentile is the threshold a real shift must clear.
B4: how many tabulated A_13/3 values are prior-floor artefacts.
"""
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
FIG = REPO / "figures"
TAB = json.loads((RES / "published_table.json").read_text())
OUT = RES / "seam_b.json"
FLOOR = -16.5


def get(psr, variant, tag):
    s = RES / f"{psr}_{variant}_{tag}.summary.json"
    f = RES / f"{psr}_{variant}_{tag}.curn.npy"
    if not (s.exists() and f.exists()):
        return None
    summ = json.loads(s.read_text())
    if not summ.get("gate_met"):
        return None
    x = np.load(f).astype(float)
    return dict(median=float(np.median(x)),
                ci68=[float(np.percentile(x, 16)),
                      float(np.percentile(x, 84))],
                samples=x)


def main():
    rows = []
    for psr in sorted(TAB):
        t = get(psr, "table", "t1")
        f = get(psr, "fl", "f1")
        if t is None or f is None:
            continue
        pub = TAB[psr]["pub"].get("gw13_log10_A")
        has_red = TAB[psr]["model"]["red"]
        d = f["median"] - t["median"]
        row = dict(psr=psr, control=bool(has_red), delta=float(d),
                   table_median=t["median"], table_ci68=t["ci68"],
                   fl_median=f["median"], fl_ci68=f["ci68"],
                   pub_map=pub[0] if isinstance(pub, list) else None,
                   pub_ci=([pub[0] + pub[1], pub[0] + pub[2]]
                           if isinstance(pub, list) else None))
        if row["pub_ci"]:
            row["pub_contains_fl"] = bool(
                row["pub_ci"][0] <= f["median"] <= row["pub_ci"][1])
            row["pub_contains_table"] = bool(
                row["pub_ci"][0] <= t["median"] <= row["pub_ci"][1])
            row["pub_prior_limited"] = bool(row["pub_ci"][0] < FLOOR)
        row["fl_prior_limited"] = bool(f["ci68"][0] < FLOOR)
        row["table_prior_limited"] = bool(t["ci68"][0] < FLOOR)
        rows.append(row)

    ctrl = [r for r in rows if r["control"]]
    test = [r for r in rows if not r["control"]]
    print(f"seam (b): {len(rows)} pulsars with BOTH runs gated "
          f"({len(test)} test = no red in the favoured model, "
          f"{len(ctrl)} control = red already present)")
    if ctrl:
        c = np.abs([r["delta"] for r in ctrl])
        thr = float(np.percentile(c, 95))
        print(f"B3 null control |Delta_b|: median {np.median(c):.3f}, "
              f"max {c.max():.3f}, 95th pct {thr:.3f} dex "
              f"-> a shift counts only above {thr:.3f}")
    else:
        thr = None
        print("B3: no control runs yet")
    if test:
        d = np.array([r["delta"] for r in test])
        print(f"B2 test set Delta_b (fl - table): median {np.median(d):+.3f}, "
              f"mean {d.mean():+.3f}, range {d.min():+.2f}..{d.max():+.2f} dex")
        for cut in (0.3, 0.5, 1.0):
            n = int((np.abs(d) > cut).sum())
            print(f"    |Delta_b| > {cut} dex: {n}/{len(test)} pulsars")
        if thr is not None:
            real = [r for r in test if abs(r["delta"]) > thr]
            print(f"    above the control threshold: {len(real)}/{len(test)}")
        down = int((d < 0).sum())
        print(f"    direction: {down}/{len(test)} move DOWN when red is added "
              f"(the 13/3 term was absorbing intrinsic red)")
        nout = sum(1 for r in test
                   if r.get("pub_ci") and not r.get("pub_contains_fl"))
        print(f"    published 68% interval fails to contain the fl median "
              f"for {nout}/{len(test)}")
        big = sorted(test, key=lambda r: r["delta"])[:15]
        print(f"\n{'psr':13s} {'table':>8s} {'fl':>8s} {'Delta':>7s} "
              f"{'pub':>8s}  flags")
        for r in big:
            fl = []
            if r.get("pub_prior_limited"):
                fl.append("pub-prior-limited")
            if not r.get("pub_contains_fl", True):
                fl.append("pub-excludes-fl")
            print(f"{r['psr']:13s} {r['table_median']:8.2f} "
                  f"{r['fl_median']:8.2f} {r['delta']:+7.2f} "
                  f"{(r['pub_map'] if r['pub_map'] is not None else float('nan')):8.2f}"
                  f"  {' '.join(fl)}")
    # B4
    pl = [r for r in rows if r["fl_prior_limited"]]
    print(f"\nB4: {len(pl)}/{len(rows)} of OUR fl posteriors are prior-floor "
          f"limited (68% lower edge below {FLOOR})")

    OUT.write_text(json.dumps(dict(
        threshold_95_control=thr, n_control=len(ctrl), n_test=len(test),
        rows=[{k: v for k, v in r.items()} for r in rows]), indent=1))
    print(f"-> {OUT}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=150)
        if test:
            ax.hist([r["delta"] for r in test], bins=np.arange(-3.0, 1.6, 0.2),
                    color="#20567C", alpha=0.85,
                    label=f"favoured model has no red ({len(test)} psr)")
        if ctrl:
            ax.hist([r["delta"] for r in ctrl],
                    bins=np.arange(-3.0, 1.6, 0.2), color="#C4552D",
                    alpha=0.75,
                    label=f"control: red already present ({len(ctrl)} psr)")
        ax.axvline(0, color="0.3", lw=1)
        ax.set_xlabel("$\\Delta_b = \\log_{10}A_{13/3}$ (with free red) "
                      "$-$ (as tabulated)  [dex]")
        ax.set_ylabel("pulsars")
        ax.set_title("Seam (b): what adding the collaboration's own red "
                     "process does to $A_{13/3}$")
        ax.legend(fontsize=8)
        fig.tight_layout()
        FIG.mkdir(exist_ok=True)
        fig.savefig(FIG / "m3_seam_b_delta.png")
        print("[saved] figures/m3_seam_b_delta.png")
    except Exception as e:
        print(f"[warn] figure skipped: {e}")


if __name__ == "__main__":
    main()
