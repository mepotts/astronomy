"""Does the per-frame RV error track how well the telluric lines pin the wavelength scale?

viper writes atm0 and its error per order per frame. |atm0|/e_atm0 is how well that order
constrains the telluric abundance -- a proxy for anchor strength. If the A-B error is driven
by a weak anchor, |A-B| should fall as the anchor strengthens.
"""
import numpy as np, os, glob, re
from scipy.stats import spearmanr
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab")
DROP = (8,)

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
        try: out[int(d["order"])]=(float(d["atm0"]), float(d["e_atm0"]))
        except Exception: pass
    return out

rows=[]
for pa in sorted(glob.glob(os.path.join(SP,"*_base_A.rvo.dat"))):
    b=os.path.basename(pa)
    night = "night1" if b.startswith("W_") else re.match(r"X(night\d+)_",b).group(1)
    pb=pa.replace("_A.rvo","_B.rvo")
    qa=pa.replace(".rvo.dat",".par.dat"); qb=pb.replace(".rvo.dat",".par.dat")
    if not (os.path.exists(pb) and os.path.exists(qa) and os.path.exists(qb)): continue
    A,oa=rvo(pa); B,_=rvo(pb); PA,PB=par(qa),par(qb)
    for o in oa:
        if o in DROP: continue
        if not all(np.isfinite(x[f"rv{o}"]) and np.isfinite(x[f"e_rv{o}"]) and x[f"e_rv{o}"]>0 for x in (A,B)):
            continue
        if o not in PA or o not in PB: continue
        sn=[]
        for P in (PA,PB):
            a,e=P[o]
            sn.append(abs(a)/e if (np.isfinite(a) and np.isfinite(e) and e>0) else np.nan)
        if not np.isfinite(np.nanmean(sn)): continue
        rows.append((night,o,abs(A[f"rv{o}"]-B[f"rv{o}"]),np.nanmean(sn)))

if not rows:
    print("no par.dat pairs available"); raise SystemExit
d=np.array([(r[2],r[3]) for r in rows])
rho,p=spearmanr(d[:,1],d[:,0])
print(f"n = {len(d)} (night, order) pairs across {len(set(r[0] for r in rows))} nights\n")
print(f"Spearman |A-B|  vs  telluric constraint |atm0|/e_atm0 :  rho = {rho:+.3f}   p = {p:.4f}\n")
q=np.nanpercentile(d[:,1],[33,67])
lo=d[d[:,1]<=q[0],0]; mid=d[(d[:,1]>q[0])&(d[:,1]<=q[1]),0]; hi=d[d[:,1]>q[1],0]
print(f"{'anchor strength':<22}{'n':>4}{'median |A-B|':>14}{'rms |A-B|':>12}")
print("-"*54)
for name,g in (("weak   (bottom third)",lo),("middle",mid),("strong (top third)",hi)):
    print(f"{name:<22}{len(g):>4}{np.median(g):>14.0f}{np.sqrt(np.mean(g**2)):>12.0f}")
print("\nby order:")
print(f"{'order':>6}{'n':>4}{'median |A-B|':>14}{'median anchor':>15}")
for o in sorted({r[1] for r in rows}):
    g=[r for r in rows if r[1]==o]
    print(f"{o:>6}{len(g):>4}{np.median([x[2] for x in g]):>14.0f}{np.median([x[3] for x in g]):>15.2f}")
