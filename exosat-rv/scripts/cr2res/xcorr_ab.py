"""Are A and B's spectra actually shifted on the detector, or only their labels?

If the flux patterns are aligned in PIXEL space (lag ~ 0) while the wavelength solutions
differ, then one solution is wrong. If the flux is shifted by the same amount the
wavelength solutions claim, the solutions are right -- and summing A and B onto a single
grid smears every line by that amount.
"""
import numpy as np
from astropy.io import fits
C = 299792.458
W = "/home/matth/cr2res/red/night1/"
A = fits.open(W + "cr2res_obs_nodding_extractedA.fits")
B = fits.open(W + "cr2res_obs_nodding_extractedB.fits")

def lag(a, b):
    """sub-pixel lag of b relative to a by parabolic peak of the cross-correlation"""
    a = np.nan_to_num(a - np.nanmedian(a)); b = np.nan_to_num(b - np.nanmedian(b))
    n = len(a); mx = 30
    cc = np.array([np.dot(a[mx:n-mx], b[mx+k:n-mx+k]) for k in range(-mx, mx+1)])
    i = int(np.argmax(cc))
    if 0 < i < len(cc)-1:
        d = 0.5*(cc[i-1]-cc[i+1])/(cc[i-1]-2*cc[i]+cc[i+1])
    else:
        d = 0.0
    return (i - mx) + d

print(f"{'det':>3} {'ord':>4} {'nm/px':>8} {'wl-soln dv':>11} {'flux lag px':>12} {'flux dv':>10} {'soln px':>8}")
print("-"*64)
rows = []
for det in (1, 2, 3):
    for c in sorted(x for x in A[det].columns.names if x.endswith("_WL")):
        o = int(c.split("_")[0])
        wa = np.asarray(A[det].data[c], float); wb = np.asarray(B[det].data[c], float)
        fa = np.asarray(A[det].data[c.replace("_WL","_SPEC")], float)
        fb = np.asarray(B[det].data[c.replace("_WL","_SPEC")], float)
        g = np.isfinite(wa) & np.isfinite(wb) & (wa > 0)
        if g.sum() < 500 or not np.isfinite(fa).any() or not np.isfinite(fb).any(): continue
        disp = np.median(np.diff(wa[g]))                       # nm per pixel
        dv_soln = C*np.median(wa[g]-wb[g])/np.median(wa[g])*1000
        px_soln = np.median(wa[g]-wb[g])/disp                   # solution offset in pixels
        L = lag(fa, fb)
        dv_flux = C*(L*disp)/np.median(wa[g])*1000
        rows.append((dv_soln, dv_flux, L, px_soln))
        if det == 2:
            print(f"{det:>3} {o:>4} {disp:>8.5f} {dv_soln:>11.1f} {L:>12.2f} {dv_flux:>10.1f} {px_soln:>8.2f}")
r = np.array(rows)
print("-"*64)
print(f"all {len(r)} segments:")
print(f"  wavelength-solution offset : median {np.median(r[:,0]):+9.1f} m/s  ({np.median(r[:,3]):+.2f} px)")
print(f"  actual flux offset         : median {np.median(r[:,1]):+9.1f} m/s  ({np.median(r[:,2]):+.2f} px)")
