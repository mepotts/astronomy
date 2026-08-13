"""Score each configuration on the A-B null test.

|A-B| is the headline, but a config could win it by returning identical garbage, so also
report the within-frame across-order dispersion (Kohler Eq.1, computed on frame A) and the
number of orders that survived. A good config is small on BOTH.
"""
import numpy as np, os, glob, re
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab")
DROP = (8,)

def rd(p):
    L = [l for l in open(p).read().splitlines() if l.strip()]
    if len(L) < 2: return None, None
    h, v = L[0].split(), L[1].split()
    d = {n: float(x) for n, x in zip(h[:-1], v[:-1])}
    return d, sorted(int(n[2:]) for n in h if n.startswith("rv") and n[2:].isdigit())

def ok(d, o): return np.isfinite(d[f"rv{o}"]) and np.isfinite(d[f"e_rv{o}"]) and d[f"e_rv{o}"] > 0

def stats(d, orders):
    xs = [d[f"rv{o}"] for o in orders if o not in DROP and ok(d, o)]
    es = [d[f"e_rv{o}"] for o in orders if o not in DROP and ok(d, o)]
    if len(xs) < 3: return np.nan, np.nan, len(xs)
    x, e = np.array(xs), np.array(es); w = e**-2.0
    xb = np.sum(w*x)/np.sum(w)
    eq1 = np.sqrt(np.sum(w*(x-xb)**2)/np.sum(w)/(len(x)-1))
    return np.mean(x), eq1, len(x)

names = sorted({re.match(r"W_(.+)_[AB]\.rvo\.dat$", os.path.basename(p)).group(1)
                for p in glob.glob(os.path.join(SP, "W_*_A.rvo.dat"))})
rows = []
for n in names:
    a, oa = rd(os.path.join(SP, f"W_{n}_A.rvo.dat"))
    b, ob = rd(os.path.join(SP, f"W_{n}_B.rvo.dat"))
    if a is None or b is None: continue
    ma, e1a, na = stats(a, oa); mb, e1b, nb = stats(b, ob)
    per = [a[f"rv{o}"]-b[f"rv{o}"] for o in oa
           if o not in DROP and ok(a, o) and ok(b, o)]
    rows.append((n, ma-mb, np.std(per, ddof=1) if len(per) > 2 else np.nan,
                 0.5*(e1a+e1b), na, nb))
rows.sort(key=lambda r: abs(r[1]) if np.isfinite(r[1]) else 1e9)
print(f"{'config':<10} {'A-B m/s':>9} {'rms(A-B)':>10} {'Eq.1 (per frame)':>17} {'nord':>6}")
print("-"*58)
for n, d, r, e, na, nb in rows:
    star = "  <--" if n == "base" else ""
    print(f"{n:<10} {d:>9.0f} {r:>10.0f} {e:>17.0f} {na:>3}/{nb:<3}{star}")
