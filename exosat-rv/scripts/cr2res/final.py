"""Every configuration, with and without the telluric-anchor order screen,
scored on the per-frame RV error (rms over nights of the binned A-B)."""
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
def gather(cfg):
    nights=[]
    for pa in sorted(glob.glob(os.path.join(SP,f"*_{cfg}_A.rvo.dat"))):
        b=os.path.basename(pa)
        if not (re.fullmatch(rf"W_{re.escape(cfg)}_A\.rvo\.dat",b) or
                re.fullmatch(rf"X night\d+_{re.escape(cfg)}_A\.rvo\.dat".replace(" ",""),b)): continue
        pb=pa.replace("_A.rvo","_B.rvo"); qa=pa.replace(".rvo.dat",".par.dat"); qb=pb.replace(".rvo.dat",".par.dat")
        if not all(os.path.exists(x) for x in (pb,qa,qb)): continue
        A,oa=rvo(pa); B,_=rvo(pb); PA,PB=par(qa),par(qb); rec=[]
        for o in oa:
            if not all(np.isfinite(x[f"rv{o}"]) and np.isfinite(x[f"e_rv{o}"]) and x[f"e_rv{o}"]>0 for x in (A,B)): continue
            if o not in PA or o not in PB: continue
            sn=[]
            for P in (PA,PB):
                a,e=P[o]; sn.append(abs(a)/e if (np.isfinite(a) and np.isfinite(e) and e>0) else np.nan)
            s=np.nanmean(sn)
            if np.isfinite(s): rec.append((o,A[f"rv{o}"],B[f"rv{o}"],s))
        if rec: nights.append(rec)
    return nights
def err(nights, thr):
    v=[]
    for rec in nights:
        sel=rec if thr is None else [r for r in rec if r[3]>thr]
        if len(sel)<3: continue
        v.append(np.mean([r[1] for r in sel])-np.mean([r[2] for r in sel]))
    return (np.sqrt(np.mean(np.square(v))), len(v)) if v else (np.nan,0)
print(f"{'config':<10}{'nights':>7}{'no screen':>11}{'anchor>0.2':>12}{'gain':>7}")
print("-"*48)
out=[]
for c in ("base","dw3","add2","add2dw3","kap"):
    n=gather(c)
    if not n: continue
    a,na=err(n,None); b,nb=err(n,0.20)
    out.append((c,na,a,b))
for c,na,a,b in sorted(out,key=lambda r:r[3]):
    print(f"{c:<10}{na:>7}{a:>11.0f}{b:>12.0f}{a/b:>6.1f}x")
print("\nTarget: ~82 m/s per frame (57.68 m/s per binned night).")
