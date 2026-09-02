"""M4 Q3+Q4: SED / colour of the contaminant, does it explain the WISE excess, and the
archival-centroid-floor calibration (threshold separation as a function of contrast)."""
import sys, warnings, pickle, json
sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

ROOT = "c:/Users/matth/projects/astronomy/dyson-revet/"
summ = pickle.load(open(ROOT+"data/jwst/m4_summ.pkl", "rb"))
FILT = ["f560w", "f1000w", "f1500w"]; LAM = {"f560w": 5.6, "f1000w": 10.0, "f1500w": 15.0}
# WISE Vega zero points (Jy), Jarrett et al. 2011 / AllWISE Expl. Supp. -- same values the
# project already uses in scripts/w1_selection.py (ZP_JY)
ZP = {"W3": 31.674, "W4": 8.363}
# AllWISE catalog photometry for candidate D (data/photometry/candidates_gaia_chain.csv)
W3M, W3E, W4M, W4E = 10.663, 0.104, 7.821, 0.227
LAMW = {"W3": 12.0, "W4": 22.0}
ab = lambda jy: -2.5*np.log10(jy/3631.0)

print("="*80); print("Q3  SED of the two components (EE50 aperture, deblended)"); print("="*80)
tab = []
for f in FILT:
    p = summ[f]["per"][1]
    tab.append(dict(band=f.upper(), lam_um=LAM[f], star_uJy=p["Jy_s"]*1e6, gal_uJy=p["Jy_g"]*1e6,
                    star_AB=ab(p["Jy_s"]), gal_AB=ab(p["Jy_g"]), ratio=p["Fg"]/p["Fs"]))
T = pd.DataFrame(tab)
print(T.round(3).to_string(index=False))

lam = T.lam_um.values; fs = T.star_uJy.values; fg = T.gal_uJy.values; rho = T.ratio.values
print("\n-- contaminant colours --")
print(f"   [F560W]-[F1000W] = {T.gal_AB[0]-T.gal_AB[1]:+.2f} mag   f(10)/f(5.6)  = {fg[1]/fg[0]:6.2f}")
print(f"   [F1000W]-[F1500W]= {T.gal_AB[1]-T.gal_AB[2]:+.2f} mag   f(15)/f(10)   = {fg[2]/fg[1]:6.2f}")
print(f"   [F560W]-[F1500W] = {T.gal_AB[0]-T.gal_AB[2]:+.2f} mag   f(15)/f(5.6)  = {fg[2]/fg[0]:6.2f}")
b1 = np.log(fg[1]/fg[0])/np.log(lam[1]/lam[0]); b2 = np.log(fg[2]/fg[1])/np.log(lam[2]/lam[1])
print(f"   spectral slope  F_nu ~ lambda^beta :  beta(5.6-10) = {b1:+.2f}   beta(10-15) = {b2:+.2f}"
      f"   [stellar Rayleigh-Jeans would be beta = -2]")
bs1 = np.log(fs[1]/fs[0])/np.log(lam[1]/lam[0]); bs2 = np.log(fs[2]/fs[1])/np.log(lam[2]/lam[1])
print(f"   star            F_nu ~ lambda^beta :  beta(5.6-10) = {bs1:+.2f}   beta(10-15) = {bs2:+.2f}")

# is the star photospheric?  3500 K blackbody (Gaia DR3 teff_gspphot = 3473 K) vs measurement
def bb_fnu(lam_um, T):
    x = 14387.77/(lam_um*T)
    return lam_um**-3/(np.exp(x)-1.0)
for T0 in (3473.0,):
    pred = bb_fnu(lam, T0); pred = pred/pred[0]*fs[0]
    print(f"\n-- star vs a {T0:.0f} K photosphere (Gaia DR3 teff_gspphot), normalised at F560W --")
    for i, f in enumerate(FILT):
        print(f"   {f.upper():7s} measured {fs[i]:8.2f} uJy   blackbody {pred[i]:8.2f} uJy   ratio {fs[i]/pred[i]:.3f}")

# implied single-temperature dust colour for the contaminant, in the rest frame at z=0.922
Z = 0.922   # Hephaistos IV, from MIRI/MRS -- NOT measurable from the imaging alone
lr = lam/(1+Z)
target = fg[2]/fg[0]
Ts = np.linspace(150, 1500, 20000)
mod = np.array([bb_fnu(lr[2], t)/bb_fnu(lr[0], t) for t in Ts])
Tbest = Ts[np.argmin(np.abs(mod-target))]
print(f"\n-- contaminant, IF at z = {Z} (paper's MRS redshift): rest-frame lambda = {lr.round(2)} um --")
print(f"   single-temperature blackbody matching f(15)/f(5.6) = {target:.1f}  ->  T ~ {Tbest:.0f} K")
print("   (Hot DOG hot-dust temperatures quoted by Hephaistos IV: ~70 K to ~450 K)")

print("\n" + "="*80); print("Q3b  Does the pair reproduce the AllWISE W3/W4 photometry?"); print("="*80)
fw3 = ZP["W3"]*10**(-W3M/2.5)*1e6; fw4 = ZP["W4"]*10**(-W4M/2.5)*1e6
tot = fs+fg
lg = np.log10(lam); lt = np.log10(tot)
f12 = 10**np.interp(np.log10(12.0), lg, lt)
print(f"   AllWISE  W3 = {W3M:.3f}+-{W3E:.3f} mag -> {fw3:8.1f} uJy at 12 um")
print(f"   AllWISE  W4 = {W4M:.3f}+-{W4E:.3f} mag -> {fw4:8.1f} uJy at 22 um")
print(f"   MIRI total (star+contaminant): {tot.round(1)} uJy at {lam} um")
print(f"   log-interpolated to 12 um    : {f12:8.1f} uJy   ->  MIRI/WISE = {f12/fw3:.2f}"
      f"  ({(f12/fw3-1)*100:+.0f}%)")
print(f"   contaminant share of the total: 5.6um {fg[0]/tot[0]*100:4.1f}%   10um {fg[1]/tot[1]*100:4.1f}%"
      f"   15um {fg[2]/tot[2]*100:4.1f}%")

print("\n" + "="*80); print("Q4  Archival centroid-floor calibration"); print("="*80)
# contrast extrapolated to the WISE bands using the measured log rho - log lambda slope
sl = np.polyfit(np.log10(lam), np.log10(rho), 1)
print(f"   measured contrast rho = f_contam/f_star: {rho.round(2)} at {lam} um")
print(f"   log10(rho) = {sl[0]:.2f} log10(lambda_um) + {sl[1]:.2f}    (rho ~ lambda^{sl[0]:.1f})")
rho_w = {b: 10**np.polyval(sl, np.log10(LAMW[b])) for b in ("W3", "W4")}
SEP = float(np.mean([summ[f]["sep"] for f in FILT]))
SEPE = float(np.std([summ[f]["sep"] for f in FILT], ddof=1))
print(f"   extrapolated rho(W3, 12um) = {rho_w['W3']:.1f} ; rho(W4, 22um) = {rho_w['W4']:.0f}"
      "   [W4 is an extrapolation beyond the data -- flagged]")
print(f"\n   measured separation = {SEP:.3f} +- {SEPE:.3f} arcsec (filter-to-filter)")
print("\n   flux-weighted centroid pull  offset = sep * rho/(1+rho)   [UPPER BOUND on a profile-fit centroid]")
for b in ("W3", "W4"):
    r = rho_w[b]; off = SEP*r/(1+r)
    print(f"     {b}: rho={r:8.1f}  ->  predicted offset = {off:.3f} arcsec  (= {r/(1+r)*100:.1f}% of the separation)")
print(f"\n   HARD CEILING: offset < sep ALWAYS. For this pair no contrast, however extreme,")
print(f"   can pull the WISE centroid further than {SEP:.3f} arcsec.")
MEAS = {"W3": (1.41, 0.21), "W4": (2.55, 0.50)}   # out/w2_centroid_offsets.csv (this project)
REN = {"W3": 0.75, "W4": 1.8}                      # Ren et al. 2026 column in the same file
for b in ("W3", "W4"):
    r = rho_w[b]; off = SEP*r/(1+r); m, e = MEAS[b]
    print(f"     {b}: predicted {off:.2f}\"  vs this project's measured {m:.2f}+-{e:.2f}\""
          f"  ({(m-off)/e:+.1f} sigma)   vs Ren et al. 2026 {REN[b]:.2f}\"")

print("\n   THRESHOLD SEPARATION vs CONTRAST:  offset > F  <=>  sep > F * (1 + 1/rho)")
rows = []
rg = [0.5, 1, 2, 3, 5, 10, 20, 21.4, 50, 100, 1000, np.inf]
print(f"   {'rho':>8} | {'sep_thr (1\" floor)':>19} | {'sep_thr (2\" floor)':>19} | "
      f"{'blind frac 1\"':>13} | {'blind frac 2\"':>13}")
RMAX = 3.25   # Suazo et al. 2024 / Hephaistos IV Sec 5.1: the W3-PSF radius used for contamination rates
for r in rg:
    t1 = 1.0*(1+1/r) if np.isfinite(r) else 1.0
    t2 = 2.0*(1+1/r) if np.isfinite(r) else 2.0
    b1f = min(t1/RMAX, 1)**2; b2f = min(t2/RMAX, 1)**2
    print(f"   {r:8.1f} | {t1:19.3f} | {t2:19.3f} | {b1f*100:12.1f}% | {b2f*100:12.1f}%")
    rows.append(dict(contrast_rho=r, sep_threshold_floor1_arcsec=round(t1, 4),
                     sep_threshold_floor2_arcsec=round(t2, 4),
                     blind_fraction_floor1=round(b1f, 4), blind_fraction_floor2=round(b2f, 4)))
print(f"\n   blind fraction = (sep_thr / {RMAX}\")^2, i.e. the fraction of a uniform-surface-density")
print(f"   background population inside the W3 PSF radius that lands closer than the threshold.")
pd.DataFrame(rows).to_csv(ROOT+"out/m4_jwstD_centroid_threshold.csv", index=False)

# where does D itself sit?
rW3 = rho_w["W3"]
print(f"\n   CANDIDATE D ITSELF: rho(W3)={rW3:.1f}, sep={SEP:.3f}\"")
print(f"     threshold at a 1\" floor = {1.0*(1+1/rW3):.3f}\"  -> D is {'ABOVE (detectable)' if SEP>1.0*(1+1/rW3) else 'BELOW (invisible)'}")
print(f"     threshold at a 2\" floor = {2.0*(1+1/rW3):.3f}\"  -> D is {'ABOVE (detectable)' if SEP>2.0*(1+1/rW3) else 'BELOW (invisible)'}")
json.dump(dict(sep_arcsec=SEP, sep_err=SEPE, rho_measured=dict(zip([f.upper() for f in FILT], rho.tolist())),
               rho_slope=float(sl[0]), rho_W3=float(rho_w["W3"]), rho_W4=float(rho_w["W4"]),
               pred_offset_W3=float(SEP*rho_w["W3"]/(1+rho_w["W3"])),
               pred_offset_W4=float(SEP*rho_w["W4"]/(1+rho_w["W4"])),
               star_uJy=dict(zip([f.upper() for f in FILT], fs.tolist())),
               gal_uJy=dict(zip([f.upper() for f in FILT], fg.tolist())),
               wise_w3_uJy=float(fw3), wise_w4_uJy=float(fw4), miri_interp_12um_uJy=float(f12),
               Tdust_singleBB_restframe_K=float(Tbest), z_assumed=Z),
          open(ROOT+"out/m4_jwstD_summary.json", "w"), indent=2)
print("\nwrote out/m4_jwstD_centroid_threshold.csv and out/m4_jwstD_summary.json")
