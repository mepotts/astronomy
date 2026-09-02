"""M2: candidate I -- excess significance stated in FLUX (not magnitudes),
plus an archival search for any independent mid-IR measurement.

Magnitudes flatter a faint excess: a 4.5-mag W1-W4 "excess" on a source
detected at S/N 3.3 is not a 12-sigma result, it is a 3.3-sigma one. This
script states the excess the way it should be stated -- excess flux over the
photospheric prediction, divided by the flux error -- and then asks whether
anything other than AllWISE has ever measured this position above 5 um.

Archival checks (all account-free, IRSA TAP / SIA):
  * Spitzer SEIP source list (IRAC 3.6-8.0, MIPS 24)  -- 6" beam but ~10x
    deeper than WISE at 24 um: would confirm or refute the W4 flux.
  * AKARI IRC point source catalogue (9, 18 um)
  * IRAS PSC/FSC (12, 25 um)
  * WISE W3/W4 from unWISE-independent reprocessings if present

Output: out/m2_I_excess.json, stdout report.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "out"
sys.path.insert(0, str(ROOT / "scripts"))

IRSA_TAP = "https://irsa.ipac.caltech.edu/TAP"
RA_I, DEC_I = 144.976333, 7.007741          # Gaia DR3 J2016
ZP_JY = {"W1": 309.540, "W2": 171.787, "W3": 31.674, "W4": 8.363,
         "J": 1594.0, "H": 1024.0, "Ks": 666.8}


def mag_to_jy(m, band):
    return ZP_JY[band] * 10 ** (-0.4 * m)


def main() -> None:
    res: dict = {"target": "candidate I", "gaia_dr3": 3854090071297359616,
                 "ra": RA_I, "dec": DEC_I}

    # ---- 1. excess significance in flux ----------------------------------
    g = pd.read_csv(DATA / "photometry" / "candidates_gaia_chain.csv")
    r = g[g.label == "I"].iloc[0]
    loc = pd.read_csv(DATA / "photometry" / "mdwarf_wise_locus.csv")

    dmod = 5 * np.log10(r["r_med_geo"] / 10.0)
    m_g_abs = r["phot_g_mean_mag"] - dmod
    res["M_G"] = float(m_g_abs)

    w1, sw1 = r["w1mpro"], r["w1mpro_error"]
    bands = {}
    for band, col, ecol, lcol, scol in [
            ("W2", "w2mpro", "w2mpro_error", "w12", "w12_scatter"),
            ("W3", "w3mpro", "w3mpro_error", "w13", "w13_scatter"),
            ("W4", "w4mpro", "w4mpro_error", "w14", "w14_scatter")]:
        m, sm = r[col], r[ecol]
        col_phot = float(np.interp(m_g_abs, loc["mg"], loc[lcol]))
        col_sig = float(np.interp(m_g_abs, loc["mg"], loc[scol]))
        # locus columns are (W1 - Wn) photospheric colours, so Wn = W1 - colour
        m_phot = w1 - col_phot
        f_obs = mag_to_jy(m, band)
        f_phot = mag_to_jy(m_phot, band)
        # sigma on f_obs from the band's own mpro error (== 1.0857/sigma = SNR)
        snr = 1.0857 / sm
        sig_obs = f_obs / snr
        # sigma on f_phot from W1 + the empirical photospheric colour scatter
        sig_phot = f_phot * 0.9210 * np.hypot(sw1, col_sig)   # ln10/2.5
        f_exc = f_obs - f_phot
        sig_exc = np.hypot(sig_obs, sig_phot)
        bands[band] = dict(
            mpro=float(m), mpro_err=float(sm), snr=float(snr),
            colour_phot=col_phot, colour_phot_scatter=col_sig,
            m_phot=float(m_phot), f_obs_mjy=float(f_obs * 1e3),
            f_phot_mjy=float(f_phot * 1e3), f_exc_mjy=float(f_exc * 1e3),
            sig_exc_mjy=float(sig_exc * 1e3),
            excess_sigma_flux=float(f_exc / sig_exc),
            excess_mag=float(m_phot - m),
            excess_sigma_mag_naive=float((m_phot - m)
                                         / np.hypot(sm, np.hypot(sw1, col_sig))),
            frac_of_obs_flux_that_is_excess=float(f_exc / f_obs))
    res["bands"] = bands
    j = np.hypot(bands["W3"]["excess_sigma_flux"], bands["W4"]["excess_sigma_flux"])
    res["joint_W3W4_sigma_flux"] = float(j)

    print("== candidate I: excess stated in flux ==")
    print(f"M_G = {m_g_abs:.3f}  (d = {r['r_med_geo']:.2f} pc, "
          f"Teff_GSP = {r['teff_gspphot']:.0f} K)")
    hdr = (f"{'band':4s} {'mpro':>7s} {'S/N':>5s} {'f_obs':>8s} {'f_phot':>8s} "
           f"{'f_exc':>8s} {'sig':>7s} {'FLUX s':>7s} {'mag exc':>8s} {'(mag s)':>8s}")
    print(hdr)
    for b, d in bands.items():
        print(f"{b:4s} {d['mpro']:7.3f} {d['snr']:5.2f} "
              f"{d['f_obs_mjy']:8.4f} {d['f_phot_mjy']:8.4f} "
              f"{d['f_exc_mjy']:8.4f} {d['sig_exc_mjy']:7.4f} "
              f"{d['excess_sigma_flux']:7.2f} {d['excess_mag']:8.3f} "
              f"{d['excess_sigma_mag_naive']:8.1f}")
    print(f"\njoint W3+W4 flux significance (quadrature, no trials): {j:.2f} sigma")
    print("NOTE: magnitude-space significance is meaningless here -- W4's "
          "'12 sigma' colour excess is a 3.3 sigma flux measurement.")

    # ---- 2. is there ANY other mid-IR measurement of this position? ------
    svc = pyvo.dal.TAPService(IRSA_TAP)
    checks = {}

    probes = [
        ("spitzer_seip", "slphotdr4",
         "ra,dec,i1_f_ap1,i2_f_ap1,i3_f_ap1,i4_f_ap1,m1_f_ap,"
         "i1_snr,i2_snr,i3_snr,i4_snr,m1_snr", 10.0),
        ("akari_irc", "akari_irc",
         "*", 15.0),
        ("iras_psc", "iraspsc", "*", 60.0),
        ("wise_allsky", "allsky_4band_p3as_psd",
         "designation,ra,dec,w1mpro,w1sigmpro,w2mpro,w2sigmpro,"
         "w3mpro,w3sigmpro,w4mpro,w4sigmpro,w3snr,w4snr,ph_qual,cc_flags,"
         "ext_flg,nb,na,w3rchi2,w4rchi2", 5.0),
        # AllWISE blend/quality detail: nb = number of PSF components fitted in
        # the blend, na = active deblending flag, w?rchi2 = per-band profile-fit
        # chi2 -- these say whether the W3/W4 measurement is a clean single-PSF
        # fit or a deblending outcome.
        ("allwise_detail", "allwise_p3as_psd",
         "designation,ra,dec,w3mpro,w3sigmpro,w4mpro,w4sigmpro,w3snr,w4snr,"
         "nb,na,w1rchi2,w2rchi2,w3rchi2,w4rchi2,rchi2,w3sat,w4sat,"
         "w3nm,w4nm,w3m,w4m,w3flg,w4flg,var_flg,ph_qual,cc_flags", 5.0),
    ]
    for tag, table, cols, rad in probes:
        q = (f"SELECT {cols} FROM {table} WHERE CONTAINS(POINT('ICRS',ra,dec),"
             f"CIRCLE('ICRS',{RA_I},{DEC_I},{rad / 3600.0}))=1")
        try:
            t = svc.search(q).to_table().to_pandas()
            checks[tag] = dict(status="ok", n=len(t),
                               rows=t.head(5).to_dict("records"))
            print(f"\n-- {tag} ({table}, r={rad}\"): {len(t)} rows")
            if len(t):
                pd.set_option("display.width", 250)
                pd.set_option("display.max_columns", 40)
                print(t.head(5).to_string())
        except Exception as e:  # noqa: BLE001
            checks[tag] = dict(status="fail", err=f"{type(e).__name__}: {str(e)[:200]}")
            print(f"\n-- {tag} ({table}): FAILED {type(e).__name__}: {str(e)[:200]}")

    res["archival_midir_probes"] = checks
    OUT.joinpath("m2_I_excess.json").write_text(
        json.dumps(res, indent=2, default=str))
    print("\nwrote out/m2_I_excess.json")


if __name__ == "__main__":
    main()
