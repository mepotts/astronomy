"""Two competing models for the archived combined product:
   H1 naive     : ESO = a*A + b*B            (summed at matching pixel index)
   H2 resampled : ESO = a*A + b*B_on_A_grid  (B interpolated onto A's wavelengths first)
Fit both by linear least squares per segment and compare residuals.
"""
import numpy as np
from astropy.io import fits
W = "/home/matth/cr2res/red/night1/"
adp = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/spectra/ADP.2025-05-25T09-47-12.250.fits"
A = fits.open(W+"cr2res_obs_nodding_extractedA.fits"); B = fits.open(W+"cr2res_obs_nodding_extractedB.fits")
d = fits.open(adp)[1].data
af=np.asarray(d["FLUX"][0]).ravel(); ao=np.asarray(d["ORDER"][0]).ravel().astype(int)
ad=np.asarray(d["DETEC"][0]).ravel().astype(int)

def fit(X, y):
    X = np.column_stack(X + [np.ones_like(y)])
    beta,*_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X@beta
    return np.std(r), beta

print(f"{'det':>3} {'ord':>4} {'A-B px':>7} {'rms H1 naive':>13} {'rms H2 resamp':>14} {'H1/H2':>7} {'winner':>9}")
print("-"*66)
w1=w2=0; rows=[]
for det in (1,2,3):
    for c in sorted(x for x in A[det].columns.names if x.endswith("_WL")):
        o=int(c.split("_")[0]); s=c.replace("_WL","_SPEC")
        m=(ao==o)&(ad==det)
        if m.sum()==0: continue
        wa=np.asarray(A[det].data[c],float); wb=np.asarray(B[det].data[c],float)
        fa=np.asarray(A[det].data[s],float); fb=np.asarray(B[det].data[s],float); fe=af[m]
        k=np.isfinite(wa)&np.isfinite(wb)&np.isfinite(fa)&np.isfinite(fb)&np.isfinite(fe)&(wa>0)
        if k.sum()<800: continue
        disp=np.median(np.diff(wa[k])); abpx=np.median(wa[k]-wb[k])/disp
        fb_on_a=np.interp(wa, wb, np.nan_to_num(fb))          # B resampled to A's grid
        r1,_=fit([fa[k], fb[k]],       fe[k])
        r2,_=fit([fa[k], fb_on_a[k]],  fe[k])
        rows.append((abpx,r1,r2)); 
        if r1<r2: w1+=1
        else: w2+=1
        if det==2:
            print(f"{det:>3} {o:>4} {abpx:>7.2f} {r1:>13.1f} {r2:>14.1f} {r1/r2:>7.3f} "
                  f"{'H1 naive' if r1<r2 else 'H2 resamp':>9}")
r=np.array(rows)
print("-"*66)
print(f"segments won: H1 naive={w1}  H2 resampled={w2}   (of {len(r)})")
print(f"median rms ratio H1/H2 = {np.median(r[:,1]/r[:,2]):.3f}   (<1 favours the naive sum)")
big=r[np.abs(r[:,0])>3]
print(f"restricted to the {len(big)} segments with |A-B| > 3 px: ratio {np.median(big[:,1]/big[:,2]):.3f}")
