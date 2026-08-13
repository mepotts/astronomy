"""Injection recovery, per order, with the rv <-> wavelength-zero-point decomposition.

Shifting the template by -v should be absorbed entirely by the fitted `rv`.  It can
instead be absorbed by `wave0`, the constant term of the per-order wavelength polynomial,
because the two are degenerate unless the telluric lines pin the wavelength scale.  So:

    v_rv   = d(rv)                     -- went into the velocity, correct
    v_wave = -c * d(wave0)/wave0       -- leaked into the wavelength solution

A sound order has slope(v_rv) ~ 1 and slope(v_wave) ~ 0.
"""
import json, os, sys
import numpy as np
C = 299792458.0
SP = os.path.dirname(os.path.abspath(__file__))
DROP = (8,)

def rows(path):
    lines = [l for l in open(path).read().splitlines() if l.strip()]
    if len(lines) < 2: return None
    hdr = lines[0].split()
    return hdr, [dict(zip(hdr, l.split())) for l in lines[1:]]

def par_by_order(path):
    r = rows(path)
    if r is None: return {}
    _, rr = r
    return {int(d["order"]): d for d in rr}

def rvo1(path):
    lines = [l for l in open(path).read().splitlines() if l.strip()]
    if len(lines) < 2: return None, None
    hdr, vals = lines[0].split(), lines[1].split()
    d = {n: float(v) for n, v in zip(hdr[:-1], vals[:-1])}
    return d, sorted(int(n[2:]) for n in hdr if n.startswith("rv") and n[2:].isdigit())

def rvomulti(path):
    lines = [l for l in open(path).read().splitlines() if l.strip()]
    hdr = lines[0].split()
    orders = sorted(int(n[2:]) for n in hdr if n.startswith("rv") and n[2:].isdigit())
    return {l.split()[-1]: ({n: float(v) for n, v in zip(hdr[:-1], l.split()[:-1])}, orders)
            for l in lines[1:]}, orders

def ok(d, o):
    return np.isfinite(d[f"rv{o}"]) and np.isfinite(d[f"e_rv{o}"]) and d[f"e_rv{o}"] > 0

def fit(v, y):
    v, y = np.asarray(v, float), np.asarray(y, float)
    g = np.isfinite(v) & np.isfinite(y)
    v, y = v[g], y[g]
    if len(v) < 4: return np.nan, np.nan, np.nan, len(v)
    A = np.column_stack([v, np.ones_like(v)])
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - A @ b
    se = np.sqrt(np.sum(r**2) / (len(v) - 2) * np.linalg.inv(A.T @ A)[0, 0])
    return b[0], se, r.std(ddof=2), len(v)

ARMS = [("clean",    "K=306   telluric-free tpl + -nocell", "U_rv.rvo.dat",    "inject_plan.json"),
        ("base",     "K=306   M2/M9 baseline",              "X_base.rvo.dat",  "inject_plan.json"),
        ("cleanbig", "K=1530  telluric-free tpl + -nocell", "U_rv.rvo.dat",    "inject_plan_big.json"),
        ("basebig",  "K=1530  M2/M9 baseline",              "X_base.rvo.dat",  "inject_plan_big.json")]

summary, po_all, wave_all = [], {}, {}
for arm, label, reffile, planfile in ARMS:
    planp = os.path.join(SP, planfile)
    if not os.path.exists(planp): continue
    plan = json.load(open(planp))
    ref, orders = rvomulti(os.path.join(SP, reffile))
    # unshifted wave0 for the SAME epoch, from the multi-epoch run's par.dat, keyed by BJD
    refpar = {}
    rp = os.path.join(SP, reffile.replace(".rvo.dat", ".par.dat"))
    if os.path.exists(rp):
        r = rows(rp)
        if r:
            for d in r[1]:
                refpar.setdefault(round(float(d["BJD"]), 4), {})[int(d["order"])] = d
    v, dc, po, wv = [], [], {}, {}
    for i, d in enumerate(plan):
        p = os.path.join(SP, "inj", f"{arm}_inj{i:02d}.rvo.dat")
        if not os.path.exists(p) or d["file"] not in ref: continue
        di, orders_i = rvo1(p)
        if di is None: continue
        dr, _ = ref[d["file"]]
        xs = [di[f"rv{o}"] for o in orders_i if o not in DROP and ok(di, o)]
        ys = [dr[f"rv{o}"] for o in orders_i if o not in DROP and ok(dr, o)]
        if xs and ys:
            v.append(d["v"]); dc.append(np.mean(xs) - np.mean(ys))
        for o in orders_i:
            if ok(di, o) and ok(dr, o):
                po.setdefault(o, []).append((d["v"], di[f"rv{o}"] - dr[f"rv{o}"]))
        # wavelength-zero-point leak
        pi = par_by_order(os.path.join(SP, "inj", f"{arm}_inj{i:02d}.par.dat"))
        pr = refpar.get(round(d["bjd"], 4), {})
        for o, row in pi.items():
            if o in pr:
                try:
                    w1, w0 = float(row["wave0"]), float(pr[o]["wave0"])
                    if np.isfinite(w1) and np.isfinite(w0) and w0 > 0:
                        wv.setdefault(o, []).append((d["v"], -C * (w1 - w0) / w0))
                except (KeyError, ValueError):
                    pass
    if len(v) >= 4:
        s, se, rms, n = fit(v, dc)
        summary.append((label, n, s, se, rms))
        po_all[label] = {o: fit([a for a, _ in xs], [b for _, b in xs]) for o, xs in po.items()}
        wave_all[label] = {o: fit([a for a, _ in xs], [b for _, b in xs]) for o, xs in wv.items()}

print(f"{'run':<40}{'n':>4}{'recovery':>11}{'+/-':>8}{'resid rms':>11}")
print("-" * 74)
for label, n, s, se, rms in summary:
    print(f"{label:<40}{n:>4}{100*s:>10.0f}%{100*se:>7.0f}%{rms:>11.0f}")

allo = sorted({o for d in po_all.values() for o in d})
print(f"\nper-order recovery of the injected velocity (%)   [ideal 100]")
print("  " + " " * 38 + "".join(f"{o:>7}" for o in allo))
for label in po_all:
    print(f"  {label:<38}" + "".join(
        f"{100*po_all[label][o][0]:>6.0f}%" if o in po_all[label] and np.isfinite(po_all[label][o][0]) else f"{'-':>7}"
        for o in allo))
print(f"\nfraction that leaked into the wavelength zero point (%)   [ideal 0]")
for label in wave_all:
    if not wave_all[label]: continue
    print(f"  {label:<38}" + "".join(
        f"{100*wave_all[label][o][0]:>6.0f}%" if o in wave_all[label] and np.isfinite(wave_all[label][o][0]) else f"{'-':>7}"
        for o in allo))
