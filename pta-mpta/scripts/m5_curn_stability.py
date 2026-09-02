#!/usr/bin/env python3
"""M5, DECLARED POST-HOC (not in the M5 pre-registration; labelled post-hoc
wherever quoted).

Two things M4 reported without an uncertainty, now given one:

  1. the 83-pulsar factorised-likelihood CURN amplitude, and the 82-pulsar
     `table` amplitude -- delete-1 jackknife over pulsars, i.e. how much of the
     quoted MAP is a property of WHICH pulsars are in the product.  M4 F5
     already showed the product is dominated by its informative members; this
     turns that into a number attached to the headline.
  2. the per-pulsar seam-(b) effect -- a paired sign test and a Wilcoxon
     signed-rank test against the 12-pulsar control set, which is the version
     of the seam-(b) claim that does NOT go through a product and therefore
     does not inherit the product's composition sensitivity.

    python scripts/m5_curn_stability.py
"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, wilcoxon, gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m5" / "curn_stability.json"
GRID = np.linspace(-18.0, -11.0, 3001)


def gated(variant, tag):
    out = []
    for f in sorted(RES.glob(f"*_{variant}_{tag}.summary.json")):
        psr = f.name.split("_")[0]
        s = json.loads(f.read_text())
        if s.get("gate_met") and (RES / f"{psr}_{variant}_{tag}.curn.npy").exists():
            out.append(psr)
    return out


def stats(dens):
    dens = np.clip(dens, 0, None)
    dens = dens / np.trapezoid(dens, GRID)
    cdf = np.cumsum(dens) * (GRID[1] - GRID[0])
    return dict(map=float(GRID[int(np.argmax(dens))]),
                lo=float(GRID[np.searchsorted(cdf, 0.16)]),
                hi=float(GRID[np.searchsorted(cdf, 0.84)]))


def main():
    res = {}
    for variant, tag in (("fl", "f1"), ("table", "t1")):
        psrs = gated(variant, tag)
        lk = {p: np.log(np.clip(gaussian_kde(
            np.load(RES / f"{p}_{variant}_{tag}.curn.npy").astype(float))(GRID),
            1e-300, None)) for p in psrs}
        acc = sum(lk.values())
        full = stats(np.exp(acc - acc.max()))
        jk = []
        for p in psrs:
            a = acc - lk[p]
            jk.append(stats(np.exp(a - a.max()))["map"])
        jk = np.array(jk)
        n = len(psrs)
        se = float(np.sqrt((n - 1) / n * ((jk - jk.mean()) ** 2).sum()))
        worst = sorted(zip(psrs, jk), key=lambda z: -abs(z[1] - full["map"]))[:5]
        res[variant] = dict(
            n=n, map=round(full["map"], 3),
            ci68=[round(full["lo"], 3), round(full["hi"], 3)],
            ci68_width=round(full["hi"] - full["lo"], 3),
            jackknife_se=round(se, 3),
            most_influential=[[p, round(float(v), 3)] for p, v in worst])
        print(f"[{variant}] n={n}  MAP {full['map']:+.3f}  "
              f"68% [{full['lo']:.2f}, {full['hi']:.2f}] "
              f"(width {full['hi']-full['lo']:.2f})  "
              f"jackknife SE over pulsar composition {se:.3f}")
        print("   most influential: "
              + ", ".join(f"{p} -> {v:+.3f}" for p, v in worst))

    # ---- the per-pulsar seam-(b) claim, tested without a product ----------
    sb = json.loads((RES / "seam_b.json").read_text())
    test = [r for r in sb["rows"] if not r["control"]]
    ctrl = [r for r in sb["rows"] if r["control"]]
    d = np.array([r["delta"] for r in test])
    c = np.array([r["delta"] for r in ctrl])
    ndown = int((d < 0).sum())
    bt = binomtest(ndown, len(d), 0.5)
    w = wilcoxon(d)
    wc = wilcoxon(c) if len(c) >= 6 else None
    print(f"\nseam-(b), per pulsar and paired (no product involved):")
    print(f"  test set n={len(d)}  median {np.median(d):+.4f}  "
          f"mean {d.mean():+.4f}  {ndown} of {len(d)} move DOWN  "
          f"sign-test p={bt.pvalue:.3g}")
    print(f"  Wilcoxon signed-rank on the test set: p={w.pvalue:.3g}")
    print(f"  control set n={len(c)}  median {np.median(c):+.4f}  "
          f"{int((c<0).sum())} of {len(c)} down"
          + (f"  Wilcoxon p={wc.pvalue:.3g}" if wc else ""))
    res["seam_b_paired"] = dict(
        n_test=len(d), median=round(float(np.median(d)), 4),
        mean=round(float(d.mean()), 4), n_down=ndown,
        sign_test_p=float(bt.pvalue), wilcoxon_p=float(w.pvalue),
        n_control=len(c), control_median=round(float(np.median(c)), 4),
        control_n_down=int((c < 0).sum()),
        control_wilcoxon_p=(float(wc.pvalue) if wc else None))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
