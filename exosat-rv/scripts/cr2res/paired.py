"""Paired comparison of configurations on the A-B null test.

Every configuration sees the same nights and the same orders, so comparing independent rms
values throws away most of the power. Pair on (night, order) and test whether |A-B| shrinks.
"""
import numpy as np, os, glob, re
from scipy.stats import wilcoxon
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab")
DROP = (8,)

def rd(p):
    L = [l for l in open(p).read().splitlines() if l.strip()]
    if len(L) < 2: return None, None
    h, v = L[0].split(), L[1].split()
    return ({n: float(x) for n, x in zip(h[:-1], v[:-1])},
            sorted(int(n[2:]) for n in h if n.startswith("rv") and n[2:].isdigit()))
def ok(d, o): return np.isfinite(d[f"rv{o}"]) and np.isfinite(d[f"e_rv{o}"]) and d[f"e_rv{o}"] > 0

def collect(cfg):
    """-> {(night,order): A-B}, {night: binned A-B}"""
    per, bnd = {}, {}
    for p in glob.glob(os.path.join(SP, "*_A.rvo.dat")):
        b = os.path.basename(p)
        m1 = re.match(rf"W_{re.escape(cfg)}_A\.rvo\.dat$", b)
        m2 = re.match(rf"X(night\d+)_{re.escape(cfg)}_A\.rvo\.dat$", b)
        if not (m1 or m2): continue
        night = "night1" if m1 else m2.group(1)
        a, oa = rd(p); bb, _ = rd(p.replace("_A.rvo", "_B.rvo"))
        if a is None or bb is None: continue
        xs = []
        for o in oa:
            if o in DROP or not (ok(a, o) and ok(bb, o)): continue
            per[(night, o)] = a[f"rv{o}"] - bb[f"rv{o}"]
            xs.append(o)
        if len(xs) >= 3:
            bnd[night] = (np.mean([a[f"rv{o}"] for o in xs])
                          - np.mean([bb[f"rv{o}"] for o in xs]))
    return per, bnd

cfgs = ["base", "dw3", "add2", "add2dw3", "kap"]
data = {c: collect(c) for c in cfgs}
nights = sorted(set(data["base"][1]) & set(data["dw3"][1]))
print(f"nights in common: {len(nights)}  ({', '.join(nights)})\n")

print("per-night binned A-B, m/s   (true value 0)")
print(f"{'config':<9}" + "".join(f"{n.replace('night','N'):>9}" for n in nights) + f"{'rms':>9}")
print("-" * (9 + 9*len(nights) + 9))
for c in cfgs:
    v = [data[c][1].get(n, np.nan) for n in nights]
    print(f"{c:<9}" + "".join(f"{x:>9.0f}" for x in v) + f"{np.sqrt(np.nanmean(np.array(v)**2)):>9.0f}")

print("\npaired test vs baseline, on |A-B| per (night, order)")
print(f"{'config':<9} {'n':>4} {'median |A-B|':>13} {'vs base':>9} {'better':>8} {'Wilcoxon p':>11}")
print("-" * 60)
kb = set(data["base"][0])
mb = np.array([abs(data["base"][0][k]) for k in sorted(kb)])
print(f"{'base':<9} {len(mb):>4} {np.median(mb):>13.0f} {'--':>9} {'--':>8} {'--':>11}")
for c in cfgs:
    if c == "base": continue
    keys = sorted(kb & set(data[c][0]))
    x = np.array([abs(data["base"][0][k]) for k in keys])
    y = np.array([abs(data[c][0][k]) for k in keys])
    better = int((y < x).sum())
    try:    p = wilcoxon(x, y).pvalue
    except Exception: p = np.nan
    print(f"{c:<9} {len(keys):>4} {np.median(y):>13.0f} {np.median(y)-np.median(x):>+9.0f} "
          f"{better:>4}/{len(keys):<3} {p:>11.4f}")
