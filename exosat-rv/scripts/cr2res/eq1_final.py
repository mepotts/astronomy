"""The paper's own error statistic, computed on our from-raw per-nodding frames.

Kohler Eq.1 = weighted dispersion of the per-order RVs within one frame. The paper bins two
nodding frames per night, so the per-night error is Eq.1/sqrt(2). Published: 57.68 m/s.
"""
import numpy as np, os, glob, re
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab")
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
def eq1(d, orders, keep):
    xs=[d[f"rv{o}"] for o in orders if o in keep]
    es=[d[f"e_rv{o}"] for o in orders if o in keep]
    if len(xs)<3: return np.nan
    x,e=np.array(xs),np.array(es); w=e**-2.
    xb=np.sum(w*x)/np.sum(w)
    return np.sqrt(np.sum(w*(x-xb)**2)/np.sum(w)/(len(x)-1))

for cfg in ("base","kap","dw3"):
    vals_s, vals_n = [], []
    for pa in sorted(glob.glob(os.path.join(SP,f"*_{cfg}_A.rvo.dat"))):
        for p in (pa, pa.replace("_A.rvo","_B.rvo")):
            q=p.replace(".rvo.dat",".par.dat")
            if not (os.path.exists(p) and os.path.exists(q)): continue
            D,od=rvo(p); P=par(q)
            good=lambda o: (np.isfinite(D[f"rv{o}"]) and np.isfinite(D[f"e_rv{o}"]) and D[f"e_rv{o}"]>0)
            allk={o for o in od if good(o)}
            keep={o for o in allk if o in P and np.isfinite(P[o][0]) and P[o][1]>0
                  and abs(P[o][0])/P[o][1] > 0.20}
            vals_n.append(eq1(D,od,allk)); vals_s.append(eq1(D,od,keep))
    a=np.array(vals_n,float); b=np.array(vals_s,float)
    print(f"{cfg:<6} frames={np.isfinite(b).sum():>3}   "
          f"Eq.1 no screen {np.nanmedian(a):>7.0f}   with screen {np.nanmedian(b):>7.0f}   "
          f"-> per night {np.nanmedian(b)/np.sqrt(2):>6.0f} m/s")
print("\npaper: 57.68 m/s per binned night")
