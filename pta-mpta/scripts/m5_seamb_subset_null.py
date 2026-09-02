#!/usr/bin/env python3
"""M5, DECLARED POST-HOC diagnostic (it is not in the M5 pre-registration and
is labelled as post-hoc wherever it is quoted).

The registered E3(e) re-test moved a headline: the seam-(b) product-level
shift between the two CURN configurations reads +0.259 dex on the 82 pulsars
gated in both (M4's B-2 headline) and +0.039 dex on the 52 that also clear the
M5 ESS floor.  Before that is read as "the ESS floor breaks the headline", the
obvious alternative has to be measured: a 52-pulsar product is a SMALLER
product, and M4 F5 already established that an FL product depends on WHICH
pulsars are in it, not just how many.

So: draw random 52-of-82 subsets of the common set, recompute the same dMAP on
each, and see where +0.039 and +0.259 sit in that distribution.  If dMAP is
broadly distributed under random thinning, the ESS-floored value is not
evidence against the 82-pulsar value -- it is a smaller sample.  If it is
tight, the ESS-floored subset is genuinely different and the headline is in
trouble.  Either way the answer is reported.

Also reported here: the seam-(b) per-pulsar control bar recomputed on the
ESS-floored control set, because M4 tripled that bar (0.144 -> 0.463) when the
control set doubled, and the floor removes half of it again.

    python scripts/m5_seamb_subset_null.py
"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
OUT = REPO / "results" / "m5" / "seamb_subset_null.json"
GRID = np.linspace(-18.0, -11.0, 3001)
NDRAW = 400
SEED = 5


def ess_min(psr, variant, tag):
    f = RES / f"{psr}_{variant}_{tag}.summary.json"
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    ch = s.get("chain") or {}
    e = ch.get("ess_min")
    if e is None:
        v = [p.get("ess") for p in ch.get("params", []) if p.get("ess") is not None]
        e = min(v) if v else None
    return e


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
    return (float(GRID[int(np.argmax(dens))]),
            float(GRID[np.searchsorted(cdf, 0.16)]),
            float(GRID[np.searchsorted(cdf, 0.84)]))


def main():
    fl, tb = gated("fl", "f1"), gated("table", "t1")
    common = sorted(set(fl) & set(tb))
    lk = {}
    for v, t in (("fl", "f1"), ("table", "t1")):
        for p in common:
            s = np.load(RES / f"{p}_{v}_{t}.curn.npy").astype(float)
            lk[(v, p)] = np.log(np.clip(gaussian_kde(s)(GRID), 1e-300, None))

    def dmap(psrs):
        af = sum(lk[("fl", p)] for p in psrs)
        at = sum(lk[("table", p)] for p in psrs)
        mf = stats(np.exp(af - af.max()))
        mt = stats(np.exp(at - at.max()))
        return mt[0] - mf[0], mf, mt

    floored = [p for p in common
               if (ess_min(p, "fl", "f1") or 0) >= 100
               and (ess_min(p, "table", "t1") or 0) >= 100]
    d_all, mf_all, mt_all = dmap(common)
    d_ess, mf_ess, mt_ess = dmap(floored)
    k = len(floored)
    print(f"common gated in both: {len(common)}; ESS-floored: {k}")
    print(f"  dMAP(table - fl)  all {len(common)}: {d_all:+.3f}   "
          f"ESS-floored {k}: {d_ess:+.3f}")

    # delete-1 jackknife standard error of the 82-pulsar dMAP -- the honest
    # uncertainty on M4's B-2 headline, which M4 never computed.
    af = sum(lk[("fl", p)] for p in common)
    at = sum(lk[("table", p)] for p in common)
    jk = []
    for p in common:
        f_i = af - lk[("fl", p)]
        t_i = at - lk[("table", p)]
        jk.append(stats(np.exp(t_i - t_i.max()))[0]
                  - stats(np.exp(f_i - f_i.max()))[0])
    jk = np.array(jk)
    n = len(common)
    jk_se = float(np.sqrt((n - 1) / n * ((jk - jk.mean()) ** 2).sum()))
    worst = sorted(zip(common, jk), key=lambda z: -abs(z[1] - d_all))[:5]
    print(f"\ndelete-1 jackknife over the {n} common pulsars:")
    print(f"  dMAP {d_all:+.3f} +/- {jk_se:.3f} (jackknife SE); "
          f"registered F4 magnitude threshold 0.21")
    print("  most influential single pulsars (dMAP with it removed): "
          + ", ".join(f"{p} {v:+.3f}" for p, v in worst))

    rng = np.random.default_rng(SEED)
    draws = []
    for _ in range(NDRAW):
        sub = list(rng.choice(common, size=k, replace=False))
        draws.append(dmap(sub)[0])
    draws = np.array(draws)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    pct_ess = float((draws <= d_ess).mean())
    print(f"\n{NDRAW} random {k}-of-{len(common)} subsets (seed {SEED}):")
    print(f"  dMAP  median {np.median(draws):+.3f}  95% [{lo:+.3f}, {hi:+.3f}]"
          f"  sd {draws.std():.3f}")
    print(f"  the ESS-floored value {d_ess:+.3f} sits at percentile "
          f"{100*pct_ess:.1f} of that distribution")
    inside = bool(lo <= d_ess <= hi)
    print(f"  -> the ESS-floored dMAP is {'INSIDE' if inside else 'OUTSIDE'} "
          f"the random-thinning 95% band")

    # the per-pulsar control bar, recomputed under the floor
    sb = json.loads((RES / "seam_b.json").read_text())
    ctrl = [r for r in sb["rows"] if r["control"]]
    test = [r for r in sb["rows"] if not r["control"]]

    def keep(p):
        return ((ess_min(p, "fl", "f1") or 0) >= 100
                and (ess_min(p, "table", "t1") or 0) >= 100)

    ck = [r for r in ctrl if keep(r["psr"])]
    tk = [r for r in test if keep(r["psr"])]
    bar_all = float(np.percentile([abs(r["delta"]) for r in ctrl], 95))
    bar_ess = (float(np.percentile([abs(r["delta"]) for r in ck], 95))
               if ck else None)
    n_over_all = sum(1 for r in test if abs(r["delta"]) > bar_all)
    n_over_ess = (sum(1 for r in tk if abs(r["delta"]) > bar_ess)
                  if bar_ess else None)
    print(f"\nper-pulsar seam-(b) control bar (95th pct |delta| over controls):")
    print(f"  all controls      n={len(ctrl)}  bar {bar_all:.3f}  -> "
          f"{n_over_all} of {len(test)} test pulsars clear it")
    print(f"  ESS-floored ctrls n={len(ck)}  bar {bar_ess:.3f}  -> "
          f"{n_over_ess} of {len(tk)} test pulsars clear it")
    print(f"  (M3's 6-control bar was 0.144; M4's 12-control bar 0.463)")
    med_all = float(np.median([r["delta"] for r in test]))
    med_ess = float(np.median([r["delta"] for r in tk]))
    print(f"  median delta_b: all test {med_all:+.3f}, "
          f"ESS-floored test {med_ess:+.3f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(
        n_common=len(common), n_floored=k, floored=floored,
        dmap_all=round(d_all, 3), dmap_ess=round(d_ess, 3),
        fl_all=dict(map=round(mf_all[0], 3), ci68=[round(mf_all[1], 3), round(mf_all[2], 3)]),
        table_all=dict(map=round(mt_all[0], 3), ci68=[round(mt_all[1], 3), round(mt_all[2], 3)]),
        fl_ess=dict(map=round(mf_ess[0], 3), ci68=[round(mf_ess[1], 3), round(mf_ess[2], 3)]),
        table_ess=dict(map=round(mt_ess[0], 3), ci68=[round(mt_ess[1], 3), round(mt_ess[2], 3)]),
        jackknife=dict(n=n, se=round(jk_se, 3), dmap=round(d_all, 3),
                       f4_threshold=0.21,
                       most_influential=[[p, round(float(v), 3)] for p, v in worst]),
        null=dict(n=NDRAW, seed=SEED, size=k, median=round(float(np.median(draws)), 3),
                  sd=round(float(draws.std()), 3),
                  ci95=[round(float(lo), 3), round(float(hi), 3)],
                  percentile_of_ess_value=round(100 * pct_ess, 1),
                  ess_inside_band=inside),
        control_bar=dict(all=dict(n=len(ctrl), bar=round(bar_all, 3),
                                  n_test_over=n_over_all, n_test=len(test),
                                  median_delta=round(med_all, 3)),
                         ess=dict(n=len(ck), bar=round(bar_ess, 3),
                                  n_test_over=n_over_ess, n_test=len(tk),
                                  median_delta=round(med_ess, 3)))), indent=1))
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
