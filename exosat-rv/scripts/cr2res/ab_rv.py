"""A and B are the same star, minutes apart: their true RV difference is ~0.
So A-B is a null test with the astrophysical signal exactly cancelled -- the cleanest
per-frame error measurement available, and one the archive route cannot produce.
"""
import numpy as np, os
SP = os.path.dirname(os.path.abspath(__file__))
def rd(p):
    L=[l for l in open(p).read().splitlines() if l.strip()]
    h=L[0].split(); v=L[1].split()
    d={n:float(x) for n,x in zip(h[:-1],v[:-1])}
    o=sorted(int(n[2:]) for n in h if n.startswith("rv") and n[2:].isdigit())
    return d,o
A,orders=rd(os.path.join(SP,"N_A.rvo.dat")); B,_=rd(os.path.join(SP,"N_B.rvo.dat")); C,_=rd(os.path.join(SP,"N_C.rvo.dat"))
# same epoch from the ADP route (18-night run, corrected model)
h=open(os.path.join(SP,"U_rv.rvo.dat")).readline().split()
row=[l.split() for l in open(os.path.join(SP,"U_rv.rvo.dat")).read().splitlines()[1:]
     if l.strip() and "ADP.2025-05-25T09-47-12.250" in l][0]
E={n:float(x) for n,x in zip(h[:-1],row[:-1])}

print(f"{'order':>6} {'nodA':>9} {'nodB':>9} {'A-B':>9} {'combined':>10} {'ESO ADP':>10}")
print("-"*60)
d=[]
for o in orders:
    ok=lambda D: np.isfinite(D[f"rv{o}"]) and np.isfinite(D[f"e_rv{o}"]) and D[f"e_rv{o}"]>0
    if not (ok(A) and ok(B)): continue
    diff=A[f"rv{o}"]-B[f"rv{o}"]; d.append((o,diff))
    print(f"{o:>6} {A[f'rv{o}']:>9.0f} {B[f'rv{o}']:>9.0f} {diff:>9.0f} "
          f"{C[f'rv{o}']:>10.0f} {E.get(f'rv{o}',np.nan):>10.0f}")
d=np.array([x[1] for x in d]); oo=np.array([x[0] for x in d.reshape(-1,1)*0+0]) if False else np.array([x[0] for x in [(o,0) for o in orders if True]])
print("-"*60)
def m(D,drop=(8,)):
    xs=[D[f"rv{o}"] for o in orders if o not in drop and np.isfinite(D[f"rv{o}"])
        and np.isfinite(D[f"e_rv{o}"]) and D[f"e_rv{o}"]>0]
    return np.mean(xs)
print(f"combined RV (order 8 dropped):  nodA {m(A):+8.0f}   nodB {m(B):+8.0f}   "
      f"cr2res-combined {m(C):+8.0f}   ESO ADP {m(E):+8.0f}  m/s")
print(f"\nA - B, the null test (true value 0):")
print(f"   all 10 orders     : mean {d.mean():+8.0f}   rms {d.std(ddof=1):8.0f}   |max| {np.abs(d).max():8.0f}")
d8=np.array([A[f'rv{o}']-B[f'rv{o}'] for o in orders if o!=8])
print(f"   order 8 dropped   : mean {d8.mean():+8.0f}   rms {d8.std(ddof=1):8.0f}   |max| {np.abs(d8).max():8.0f}")
print(f"   binned A-B (the quantity that matters): {m(A)-m(B):+.0f} m/s")
