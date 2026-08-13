"""Pool the A-B null test over all reduced nights.

Each night contributes one binned A-B and ~9 per-order pairs. Pooling is what gives the
test power: with N nights the standard error on the mean A-B falls as 1/sqrt(9N), so four
nights discriminate configurations at ~150 m/s where one night manages only ~300.
"""
import numpy as np, os, glob, re
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab")
DROP = (8,)

def rd(p):
    L = [l for l in open(p).read().splitlines() if l.strip()]
    if len(L) < 2: return None, None
    h, v = L[0].split(), L[1].split()
    return ({n: float(x) for n, x in zip(h[:-1], v[:-1])},
            sorted(int(n[2:]) for n in h if n.startswith("rv") and n[2:].isdigit()))

def ok(d, o):
    return np.isfinite(d[f"rv{o}"]) and np.isfinite(d[f"e_rv{o}"]) and d[f"e_rv{o}"] > 0

def binned(d, orders):
    xs = [d[f"rv{o}"] for o in orders if o not in DROP and ok(d, o)]
    return np.mean(xs) if len(xs) >= 3 else np.nan

# collect (config, night) -> A/B paths.  night1 files are W_<cfg>_<arm>, others X<night>_<cfg>_<arm>
pairs = {}
for p in glob.glob(os.path.join(SP, "*_A.rvo.dat")):
    b = os.path.basename(p)
    m = re.match(r"W_(.+)_A\.rvo\.dat$", b) or re.match(r"X(night\d+)_(.+)_A\.rvo\.dat$", b)
    if not m: continue
    night, cfg = ("night1", m.group(1)) if b.startswith("W_") else (m.group(1), m.group(2))
    pb = p.replace("_A.rvo.dat", "_B.rvo.dat")
    if os.path.exists(pb): pairs.setdefault(cfg, {})[night] = (p, pb)

rows = []
for cfg, nights in sorted(pairs.items()):
    per, binv = [], []
    for n, (pa, pb) in sorted(nights.items()):
        a, oa = rd(pa); bb, ob = rd(pb)
        if a is None or bb is None: continue
        per += [a[f"rv{o}"] - bb[f"rv{o}"] for o in oa
                if o not in DROP and ok(a, o) and ok(bb, o)]
        d = binned(a, oa) - binned(bb, ob)
        if np.isfinite(d): binv.append(d)
    if len(binv) == 0: continue
    per = np.array(per); binv = np.array(binv)
    se = per.std(ddof=1) / np.sqrt(len(per)) if len(per) > 2 else np.nan
    rows.append((cfg, len(binv), len(per), np.mean(binv), per.mean(), se,
                 per.std(ddof=1), np.sqrt(np.mean(binv**2))))

rows.sort(key=lambda r: abs(r[4]))
print(f"{'config':<10} {'nights':>7} {'pairs':>6} {'mean A-B':>10} {'+/-':>7} {'sigma':>7} "
      f"{'rms(A-B)':>10} {'rms binned':>11}")
print("-" * 76)
for c, nn, npair, mb, mp, se, sd, rb in rows:
    sig = abs(mp) / se if se and np.isfinite(se) else np.nan
    print(f"{c:<10} {nn:>7} {npair:>6} {mp:>10.0f} {se:>7.0f} {sig:>7.1f} {sd:>10.0f} {rb:>11.0f}")
print("\nmean A-B is the per-order mean over all nights; 'sigma' is its distance from zero.")
print("rms binned = scatter of the per-night binned A-B, i.e. the per-frame RV error.")
