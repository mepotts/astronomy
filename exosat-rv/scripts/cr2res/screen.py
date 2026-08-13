"""Screen orders by telluric anchor strength -- the paper's own stated rule -- and measure
the per-frame RV error that results.

Hoy et al.: "not all orders contain sufficient telluric lines for a high-quality
recalibration. These orders are excluded from the calculation, as this failed calibration
produces highly erratic results."

M9 rejected this rule, but tested it on ESO's combined product against epoch-to-epoch rms.
Here it is tested per frame, with the astrophysical signal cancelled by construction.
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

nights=[]
for pa in sorted(glob.glob(os.path.join(SP,"*_base_A.rvo.dat"))):
    b=os.path.basename(pa)
    n = "night1" if b.startswith("W_") else re.match(r"X(night\d+)_",b).group(1)
    pb=pa.replace("_A.rvo","_B.rvo"); qa=pa.replace(".rvo.dat",".par.dat"); qb=pb.replace(".rvo.dat",".par.dat")
    if not all(os.path.exists(x) for x in (pb,qa,qb)): continue
    A,oa=rvo(pa); B,_=rvo(pb); PA,PB=par(qa),par(qb)
    rec=[]
    for o in oa:
        if not all(np.isfinite(x[f"rv{o}"]) and np.isfinite(x[f"e_rv{o}"]) and x[f"e_rv{o}"]>0 for x in (A,B)): continue
        if o not in PA or o not in PB: continue
        sn=[]
        for P in (PA,PB):
            a,e=P[o]; sn.append(abs(a)/e if (np.isfinite(a) and np.isfinite(e) and e>0) else np.nan)
        s=np.nanmean(sn)
        if np.isfinite(s): rec.append((o,A[f"rv{o}"],B[f"rv{o}"],s))
    if rec: nights.append((n,rec))

print(f"{'screen':<34}{'orders kept':>12}{'per-frame err':>15}   per-night A-B")
print("-"*95)
for label, thr in [("all orders (no screen)",-1),("drop order 8 (M9's screen)",None),
                   ("anchor > 0.10",0.10),("anchor > 0.20",0.20),("anchor > 0.30",0.30),
                   ("anchor > 0.40",0.40),("anchor > 0.50",0.50),("anchor > 0.60",0.60)]:
    vals, kept = [], []
    for n,rec in nights:
        if thr is None: sel=[r for r in rec if r[0]!=8]
        elif thr<0:     sel=rec
        else:           sel=[r for r in rec if r[3]>thr]
        if len(sel)<3: vals.append(np.nan); continue
        vals.append(np.mean([r[1] for r in sel])-np.mean([r[2] for r in sel]))
        kept.append(len(sel))
    v=np.array(vals,float)
    rms=np.sqrt(np.nanmean(v**2))
    print(f"{label:<34}{np.mean(kept) if kept else 0:>12.1f}{rms:>15.0f}   "
          + " ".join(f"{x:+6.0f}" for x in v))
print("\nper-frame err = rms over nights of the binned A-B, i.e. the single-frame RV error.")
print("Paper's requirement: 57.68 m/s per binned night = ~82 m/s per frame.")
