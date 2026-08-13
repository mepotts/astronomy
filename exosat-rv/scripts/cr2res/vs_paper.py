"""The real test: do our from-raw RVs track the published ones, night by night?

Bin A and B per night (as the paper does), screen orders by telluric anchor, remove a
constant offset (the systemic velocity is arbitrary), and compare to the Nature Table 2 RVs
for the same BJDs. The scatter of the difference is the reproduction error.
"""
import numpy as np, os, glob, re
SP = os.path.dirname(os.path.abspath(__file__)); AB = os.path.join(SP, "ab")
PUB = "/c/Users/matth/projects/astronomy/exosat-rv/papers/text/hoy2026_nature_published.txt".replace("/c/","C:/")

pub = {}
for m in re.finditer(r"(24\d{5}\.\d{4})\s+(-?\d+\.\d+)\s+(\d+\.\d+)", open(PUB,encoding="utf-8",errors="replace").read()):
    pub[float(m.group(1))] = (float(m.group(2)), float(m.group(3)))

def rvo(p):
    L=[l for l in open(p).read().splitlines() if l.strip()]
    h,v=L[0].split(),L[1].split()
    return ({n:float(x) for n,x in zip(h[:-1],v[:-1])},
            sorted(int(n[2:]) for n in h if n.startswith("rv") and n[2:].isdigit()))
def par(p):
    L=[l for l in open(p).read().splitlines() if l.strip()]
    h=L[0].split(); out={}
    for line in L[1:]:
        d=dict(zip(h,line.split()))
        try: out[int(d["order"])]=(float(d["atm0"]),float(d["e_atm0"]))
        except Exception: pass
    return out

for cfg in ("base","kap"):
    rows=[]
    for pa in sorted(glob.glob(os.path.join(AB,f"*_{cfg}_A.rvo.dat"))):
        pb=pa.replace("_A.rvo","_B.rvo")
        vals=[]; bjd=None
        for p in (pa,pb):
            q=p.replace(".rvo.dat",".par.dat")
            if not (os.path.exists(p) and os.path.exists(q)): break
            D,od=rvo(p); P=par(q); bjd=D["BJD"]
            keep=[o for o in od if np.isfinite(D[f"rv{o}"]) and np.isfinite(D[f"e_rv{o}"])
                  and D[f"e_rv{o}"]>0 and o in P and P[o][1]>0 and abs(P[o][0])/P[o][1]>0.20]
            if len(keep)>=3: vals.append(np.mean([D[f"rv{o}"] for o in keep]))
        if len(vals)==2 and bjd:
            k=min(pub, key=lambda x: abs(x-bjd))
            if abs(k-bjd) < 0.01: rows.append((bjd, np.mean(vals), pub[k][0], pub[k][1]))
    if not rows: print(f"{cfg}: no matched nights"); continue
    a=np.array(rows)
    off=np.mean(a[:,1]-a[:,2])
    d=a[:,1]-off-a[:,2]
    print(f"\n=== {cfg} + anchor screen, {len(a)} nights matched to Nature Table 2 ===")
    print(f"{'BJD':>14}{'ours (m/s)':>12}{'published':>11}{'pub err':>9}{'diff':>9}")
    for (b,o,p_,e),dd in zip(a,d): print(f"{b:>14.4f}{o-off:>12.0f}{p_:>11.0f}{e:>9.0f}{dd:>9.0f}")
    print(f"   rms of difference : {d.std(ddof=1):.0f} m/s")
    print(f"   published errors  : {a[:,3].mean():.0f} m/s mean")
    print(f"   implied our error : {np.sqrt(max(d.var(ddof=1)-np.mean(a[:,3]**2),0)):.0f} m/s")
