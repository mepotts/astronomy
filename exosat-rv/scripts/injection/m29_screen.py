"""M29: the M13 order screen, generalized to any target, with a PRE-COMMITTED rule.

Same sanctioned drop rule as ctcha_screen.py, which is the point: an order survives if
|recovery - 100| <= 15 points AND arm scatter <= 25 points in BOTH injection arms. The
rule looks only at injected-signal transmission. It never looks at the science RVs, so
it cannot select its way to a nicer answer -- which is the failure M9 recorded, where the
best-looking improvement worked by deleting the signal.

The decision rule for this run was fixed before the screen was executed:

  A. screen keeps most orders AND the mean/median combines converge
     -> the epoch is usable.
  B. screen keeps most orders AND the combines still disagree
     -> the epoch is bad as a whole, not order-wise. Report it as such.
  C. the screen must drop about half the orders or more to make it work
     -> that is selection, not repair. REJECT the epoch regardless of how good the
        surviving series looks.

"Most" is fixed here as > 2/3 of orders surviving; "converge" as the mean- and
median-combine epoch rms agreeing within a factor of 2.

Usage (WSL, ~/viper-src): python m29_screen.py SLUG [K15_ARM K3_ARM]
"""
import json
import os
import sys

import numpy as np

SC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SC)
from vs_published import load  # noqa: E402

KEEP_FRAC = 2.0 / 3.0
CONVERGE_FACTOR = 2.0


def rvo_rows(path):
    lines = [ln for ln in open(path).read().splitlines() if ln.strip()]
    if len(lines) < 2:
        return None, []
    hdr = lines[0].split()
    orders = sorted(int(n[2:]) for n in hdr if n.startswith("rv") and n[2:].isdigit())
    out = {}
    for ln in lines[1:]:
        v = ln.split()
        out[os.path.basename(v[-1])] = {n: float(x) for n, x in zip(hdr[:-1], v[:-1])}
    return out, orders


def ok(d, o):
    return (np.isfinite(d.get(f"rv{o}", np.nan)) and
            np.isfinite(d.get(f"e_rv{o}", np.nan)) and d[f"e_rv{o}"] > 0)


def arm_recovery(arm, ref, plan_path):
    plan = json.load(open(plan_path))
    per = {}
    for i, p in enumerate(plan):
        f = os.path.basename(p["file"])
        v = p["v"]
        if abs(v) < 50:
            continue
        path = f"{arm}_inj{i:02d}.rvo.dat"
        if not os.path.exists(path) or f not in ref:
            continue
        inj, orders = rvo_rows(path)
        if not inj:
            continue
        di = next(iter(inj.values()))
        dr = ref[f]
        for o in orders:
            if ok(di, o) and ok(dr, o):
                per.setdefault(o, []).append((di[f"rv{o}"] - dr[f"rv{o}"]) / v)
    return {o: (100 * np.mean(r), 100 * (np.std(r, ddof=1) if len(r) > 1 else 0.0),
                len(r))
            for o, r in per.items()}


def combines(path, keep=None):
    c, orders = load(path)
    use = [o for o in orders if keep is None or o in keep]
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in use])
    with np.errstate(all="ignore"):
        med = np.nanmedian(RV, axis=0)
        mean = np.nanmean(RV, axis=0)
    return np.asarray(c["BJD"], float), med, mean, len(use)


def main():
    slug = sys.argv[1]
    a15n = sys.argv[2] if len(sys.argv) > 2 else f"{slug}_K15"
    a3n = sys.argv[3] if len(sys.argv) > 3 else f"{slug}_K3"
    rvo = f"{slug}_RV.rvo.dat"

    ref, all_orders = rvo_rows(rvo)
    ref = {os.path.basename(k): v for k, v in ref.items()}
    a15 = arm_recovery(a15n, ref, f"{SC}/inject_plan_{a15n}.json")
    a3 = arm_recovery(a3n, ref, f"{SC}/inject_plan_{a3n}.json")

    print(f"# {slug}: M13 screen, rule fixed before execution")
    print(f"# keep if |rec-100| <= 15 and scatter <= 25 in BOTH arms\n")
    print(f"{'ord':>4} {'K15 recovery':>16} {'K3 recovery':>16}  verdict")
    keep = []
    for o in sorted(set(a15) | set(a3)):
        m15, s15, n15 = a15.get(o, (np.nan, np.nan, 0))
        m3, s3, n3 = a3.get(o, (np.nan, np.nan, 0))
        good = (abs(m15 - 100) <= 15 and s15 <= 25 and
                abs(m3 - 100) <= 15 and s3 <= 25)
        if good:
            keep.append(o)
        print(f"{o:>4} {m15:8.0f} +-{s15:<4.0f}(n{n15}) {m3:8.0f} +-{s3:<4.0f}(n{n3})"
              f"  {'KEEP' if good else 'drop'}")

    n_all = len(set(a15) | set(a3))
    frac = len(keep) / max(n_all, 1)
    print(f"\nkept {len(keep)}/{n_all} orders ({100 * frac:.0f}%)")
    print("screened oset:", ",".join(map(str, keep)) or "(none)")

    def epoch_rms(t, v):
        g = np.isfinite(v)
        if g.sum() < 2:
            return np.nan
        # collapse A/B frames of the same night first
        order = np.argsort(t[g])
        tt, vv = t[g][order], v[g][order]
        nights, cur = [], [0]
        for j in range(1, len(tt)):
            if tt[j] - tt[j - 1] < 0.2:
                cur.append(j)
            else:
                nights.append(cur)
                cur = [j]
        nights.append(cur)
        means = [np.mean(vv[c]) for c in nights]
        return np.std(means, ddof=1) if len(means) > 1 else np.nan

    for label, k in (("unscreened", None), ("screened", keep)):
        if k is not None and not k:
            continue
        t, med, mean, n = combines(rvo, k)
        r_med, r_mean = epoch_rms(t, med), epoch_rms(t, mean)
        ratio = (max(r_med, r_mean) / max(min(r_med, r_mean), 1e-9)
                 if np.isfinite(r_med) and np.isfinite(r_mean) else np.nan)
        print(f"\n{label} ({n} orders): night-to-night rms  "
              f"median-combine {r_med:.0f}  mean-combine {r_mean:.0f} m/s   "
              f"disagreement factor {ratio:.1f}x")

    # ---- the pre-committed verdict ------------------------------------
    t, med, mean, _ = combines(rvo, keep) if keep else (None, None, None, 0)
    print("\n" + "=" * 66)
    if frac < KEEP_FRAC:
        print(f"VERDICT C: screen drops {100 * (1 - frac):.0f}% of orders "
              f"(> {100 * (1 - KEEP_FRAC):.0f}% threshold).")
        print("That is selection, not repair. REJECT the epoch, per the rule fixed")
        print("in advance -- regardless of how the surviving series looks.")
        return
    r_med, r_mean = epoch_rms(t, med), epoch_rms(t, mean)
    ratio = max(r_med, r_mean) / max(min(r_med, r_mean), 1e-9)
    if ratio <= CONVERGE_FACTOR:
        print(f"VERDICT A: {100 * frac:.0f}% of orders survive and the combines "
              f"converge ({ratio:.1f}x <= {CONVERGE_FACTOR}x).")
        print("The epoch is usable.")
    else:
        print(f"VERDICT B: {100 * frac:.0f}% of orders survive but the combines "
              f"still disagree ({ratio:.1f}x > {CONVERGE_FACTOR}x).")
        print("The epoch is bad as a whole, not order-wise. Report it as such.")


if __name__ == "__main__":
    main()
