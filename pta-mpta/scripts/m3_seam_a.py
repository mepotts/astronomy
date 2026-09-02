#!/usr/bin/env python3
"""M3 seam (a): the chromatic A-beta ridge and its untabulated priors.

Pre-registered S-criteria: M3-noise-criticism.md section 1.4. Operates on the
all-83 noise campaign's own post-burn posteriors (results/m3/*_noise_n1.post.npy)
- no extra sampling.

S1 ridge existence   Pearson r and OLS slope of log10A_Chrom against beta
S2 beta constrained? 68%/95% CI width as a fraction of the U(0,14) prior
S3 prior sensitivity importance reweighting to U(0,10), U(0,7), U(2,6)
S4 verdict           prior-driven iff |median shift| > published 68% half-width
S5 fairness control  the same reweighting applied to EFAC (must not move) and
                     to the fixed-beta=4 contrast set (has no beta to reweight,
                     so its A_Chrom must not move either)
"""
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "m3"
TAB = json.loads((RES / "published_table.json").read_text())
OUT = RES / "seam_a.json"

ALT_PRIORS = {"U(0,10)": (0.0, 10.0), "U(0,7)": (0.0, 7.0),
              "U(2,6)": (2.0, 6.0)}
# EXPLORATORY (declared as such, NOT part of the pre-registered S4 rule):
# prior SHAPE changes on the same support. Importance reweighting is valid for
# any prior whose support is contained in ours.
ALT_SHAPES = {"N(4,1)": (4.0, 1.0), "N(4,0.5)": (4.0, 0.5)}
BASE = (0.0, 14.0)
ESS_MIN = 200
NU_REF = 1400.0   # MHz, the paper's chromatic/DM reference frequency


M2RES = REPO / "results" / "m2"
M2CH = REPO / "chains" / "m2"
M2TAG = {"J1909-3744": "blind1"}


def load_post(psr):
    """M3's own gated posterior, or - clearly labelled - M2's gated run of the
    IDENTICAL model and conventions where M3's has not gated yet. M2's runs
    passed the same C1 gate (M2 doc section 4) and the M2-vs-M3 repeat control
    measures how far apart two such runs land."""
    f = RES / f"{psr}_noise_n1.post.npy"
    s = RES / f"{psr}_noise_n1.summary.json"
    if f.exists() and s.exists():
        summ = json.loads(s.read_text())
        if summ.get("gate_met"):
            return np.load(f), summ.get("param_names"), "M3"
    s2 = M2RES / f"{psr}_noise_{M2TAG.get(psr, 'c1')}.summary.json"
    c2 = M2CH / f"{psr}_noise_{M2TAG.get(psr, 'c1')}" / "chain_1.txt"
    if s2.exists() and c2.exists():
        summ = json.loads(s2.read_text())
        if summ.get("gate_met"):
            names = [r["param"] for r in summ["chain"]["params"]]
            ch = np.loadtxt(c2, ndmin=2)
            return ch[len(ch) // 4:, :len(names)], names, "M2"
    return None, None, None


def wmedian(x, w):
    i = np.argsort(x)
    x, w = x[i], w[i]
    c = np.cumsum(w) / w.sum()
    return float(np.interp(0.5, c, x))


def main():
    rows = []
    for psr in sorted(TAB):
        cfg = TAB[psr]["model"]
        if cfg["chrom"] is None:
            continue
        post, names, src = load_post(psr)
        if post is None:
            continue
        idx = {n.replace(f"{psr}_", ""): i for i, n in enumerate(names)}
        ia = idx.get("chrom_gp_log10_A")
        ig = idx.get("chrom_gp_gamma")
        ib = idx.get("chrom_gp_idx")
        ie = idx.get("efac")
        i13 = idx.get("gw13_log10_A")
        pub = TAB[psr]["pub"]
        pa = pub.get("chrom_log10_A")
        half = (abs(pa[1]) + abs(pa[2])) / 2 if isinstance(pa, list) else None
        row = dict(psr=psr, chrom=cfg["chrom"], n=len(post), source=src,
                   pub_A=pa[0] if isinstance(pa, list) else None,
                   pub_A_half68=half,
                   med_A=float(np.median(post[:, ia])),
                   med_gamma=float(np.median(post[:, ig])))
        if ib is not None:
            b = post[:, ib]
            row.update(
                med_beta=float(np.median(b)),
                r_Abeta=float(np.corrcoef(post[:, ia], b)[0, 1]),
                slope_dA_dbeta=float(np.polyfit(b, post[:, ia], 1)[0]),
                beta_ci68=[float(np.percentile(b, 16)),
                           float(np.percentile(b, 84))],
                beta_ci95=[float(np.percentile(b, 2.5)),
                           float(np.percentile(b, 97.5))])
            row["beta_frac68"] = ((row["beta_ci68"][1] - row["beta_ci68"][0])
                                  / (BASE[1] - BASE[0]))
            row["beta_frac95"] = ((row["beta_ci95"][1] - row["beta_ci95"][0])
                                  / (BASE[1] - BASE[0]))
            # S3 reweighting
            alts = {}
            for label, (lo, hi) in ALT_PRIORS.items():
                w = ((b >= lo) & (b <= hi)).astype(float)
                if w.sum() == 0:
                    alts[label] = dict(ess=0.0, valid=False)
                    continue
                w /= w.sum()
                ess = float(1.0 / np.sum(w ** 2))
                d = dict(ess=ess, valid=bool(ess >= ESS_MIN),
                         med_A=wmedian(post[:, ia], w),
                         med_gamma=wmedian(post[:, ig], w),
                         med_beta=wmedian(b, w),
                         med_efac=(wmedian(post[:, ie], w)
                                   if ie is not None else None),
                         med_A13=(wmedian(post[:, i13], w)
                                  if i13 is not None else None))
                d["dA"] = d["med_A"] - row["med_A"]
                d["dbeta"] = d["med_beta"] - row["med_beta"]
                d["defac"] = ((d["med_efac"] -
                               float(np.median(post[:, ie])))
                              if ie is not None else None)
                d["dA13"] = ((d["med_A13"] - float(np.median(post[:, i13])))
                             if i13 is not None else None)
                alts[label] = d
            row["alt"] = alts
            moved = [lab for lab, d in alts.items()
                     if d.get("valid") and half
                     and abs(d["dA"]) > half]
            row["prior_driven"] = bool(moved)
            row["moved_under"] = moved
            # exploratory: prior SHAPE, and the ridge's pivot frequency
            shapes = {}
            for label, (mu, sd) in ALT_SHAPES.items():
                w = np.exp(-0.5 * ((b - mu) / sd) ** 2)
                if w.sum() <= 0:
                    continue
                w /= w.sum()
                ess = float(1.0 / np.sum(w ** 2))
                shapes[label] = dict(
                    ess=ess, valid=bool(ess >= ESS_MIN),
                    dA=wmedian(post[:, ia], w) - row["med_A"],
                    dbeta=wmedian(b, w) - row["med_beta"],
                    dA13=((wmedian(post[:, i13], w)
                           - float(np.median(post[:, i13])))
                          if i13 is not None else None))
            row["alt_shape"] = shapes
            # S6 (exploratory): the reference frequency at which the tabulated
            # chromatic amplitude stops covarying with beta. delay ~ A *
            # (1400/nu)^beta, so re-referencing to nu_piv adds k*beta to
            # log10 A with k = log10(1400/nu_piv); the covariance vanishes at
            # k = -Cov(A, beta)/Var(beta).
            k = -np.cov(post[:, ia], b)[0, 1] / np.var(b, ddof=1)
            row["k_decorrelate"] = float(k)
            row["nu_pivot_MHz"] = float(NU_REF / 10 ** k)
            Ap = post[:, ia] + k * b
            row["med_A_at_pivot"] = float(np.median(Ap))
            row["ci68_A_at_pivot"] = [float(np.percentile(Ap, 16)),
                                      float(np.percentile(Ap, 84))]
            row["width_A_1400"] = float(np.percentile(post[:, ia], 84)
                                        - np.percentile(post[:, ia], 16))
            row["width_A_pivot"] = float(np.percentile(Ap, 84)
                                         - np.percentile(Ap, 16))
            row["max_dA"] = max((abs(d["dA"]) for d in alts.values()
                                 if d.get("valid")), default=None)
            row["max_defac"] = max((abs(d["defac"]) for d in alts.values()
                                    if d.get("valid")
                                    and d["defac"] is not None), default=None)
            row["max_dA13"] = max((abs(d["dA13"]) for d in alts.values()
                                   if d.get("valid")
                                   and d["dA13"] is not None), default=None)
        rows.append(row)

    free = [r for r in rows if r["chrom"] == "free"]
    fix4 = [r for r in rows if r["chrom"] == "fixed4"]
    print(f"chromatic pulsars with a campaign posterior: {len(rows)} "
          f"({len(free)} free-beta, {len(fix4)} beta=4)")
    if free:
        rr = [r["r_Abeta"] for r in free]
        sl = [r["slope_dA_dbeta"] for r in free]
        print(f"S1 ridge: Pearson r(log10A_Chrom, beta) median {np.median(rr):+.2f} "
              f"range {min(rr):+.2f}..{max(rr):+.2f}; "
              f"slope median {np.median(sl):+.2f} dex per unit beta")
        f68 = [r["beta_frac68"] for r in free]
        f95 = [r["beta_frac95"] for r in free]
        print(f"S2 beta constraint: 68% CI = {100*np.median(f68):.0f}% of the "
              f"U(0,14) prior (median), 95% CI = {100*np.median(f95):.0f}%")
        pd = [r for r in free if r.get("prior_driven")]
        print(f"S4 verdict: {len(pd)}/{len(free)} free-beta pulsars are "
              f"PRIOR-DRIVEN by the registered rule")
        print(f"{'psr':13s} {'r':>6s} {'beta68frac':>11s} {'maxdA':>7s} "
              f"{'pub68/2':>8s} {'maxdA13':>8s} {'maxdEFAC':>9s} verdict")
        nm2 = sum(1 for r in rows if r.get("source") == "M2")
        if nm2:
            print(f"    ({nm2} of these posteriors come from M2's gated run of "
                  f"the identical model, not M3's - flagged in the table)")
        for r in sorted(free, key=lambda r: -(r["max_dA"] or 0)):
            print(f"{r['psr']:13s}{'*' if r.get('source')=='M2' else ' '}"
                  f"{r['r_Abeta']:+5.2f} "
                  f"{r['beta_frac68']*100:10.0f}% {r['max_dA'] or 0:7.2f} "
                  f"{r['pub_A_half68'] or 0:8.2f} {r['max_dA13'] or 0:8.2f} "
                  f"{r['max_defac'] or 0:9.4f} "
                  f"{'PRIOR-DRIVEN' if r.get('prior_driven') else 'data-driven'}")
        me = [r["max_defac"] for r in free if r["max_defac"] is not None]
        if me:
            print(f"S5 control: worst EFAC median shift under any beta-prior "
                  f"reweighting = {max(me):.4f} (must be ~0)")
        print("\nEXPLORATORY (not pre-registered):")
        sh = [max((abs(d["dA"]) for d in r.get("alt_shape", {}).values()
                   if d.get("valid")), default=0.0) for r in free]
        print(f"  prior SHAPE (Gaussian on beta): worst |dA_Chrom| "
              f"{max(sh):.2f} dex, median {np.median(sh):.2f}")
        nsh = sum(1 for r, s in zip(free, sh)
                  if r["pub_A_half68"] and s > r["pub_A_half68"])
        print(f"    would flag {nsh}/{len(free)} as shape-sensitive")
        piv = [r["nu_pivot_MHz"] for r in free]
        w14 = [r["width_A_1400"] for r in free]
        wpv = [r["width_A_pivot"] for r in free]
        print(f"  S6 decorrelating reference frequency: median "
              f"{np.median(piv):.0f} MHz, range {min(piv):.0f}-{max(piv):.0f} "
              f"(the band is 856-1712 MHz; the table quotes 1400)")
        print(f"    68% width of log10A_Chrom: {np.median(w14):.2f} dex at "
              f"1400 MHz vs {np.median(wpv):.2f} dex at each pulsar's own "
              f"pivot (median over {len(free)} pulsars)")
    OUT.write_text(json.dumps(rows, indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
