#!/usr/bin/env python
"""W1: Keplerian (orbital) fit to the Gaia DR4 pre-release epoch astrometry of Gaia BH3.

Mirrors ESA's official notebook (branch gaia-dr4-prerelease of esa/gaia-bhthree):
  https://github.com/esa/gaia-bhthree/tree/gaia-dr4-prerelease
  Gaia-DR4-prerelease_BH3_fit_astrometric_orbit.ipynb
using kepmodel/spleaf (Delisle) + gaiasupdate for data preparation and
pystrometry (Sahlmann) for the angular-to-linear and m2 conversions, but with
plain-matplotlib plots so it runs headless.

Target : Gaia BH3, DR4 pre-release source_id 4318465066420528000
         (NOTE: differs from the DR3 source_id 4318465066420528896 —
          DR4 has a new source list; match by position, not by DR3 id)
Primary: m1 = 0.76 Msun (value used in the ESA notebook)

Outputs: out/bh3_orbit_fit.txt   - fitted Campbell elements + companion mass
         out/bh3_orbit_fit.png   - residuals, periodogram, phase-folded orbit signal

Run    : .venv/Scripts/python.exe scripts/fit_prerelease_orbit_bh3.py
"""

import copy
import logging
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.table import Table

import spleaf
from kepmodel.astro import AstroModel as AstrometricModel
from pystrometry.pystrometry import convert_from_angular_to_linear, pjGet_m2, MS_kg

from gaiasupdate.epoch_astrometry import GaiaEpochAstrometryArchive

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(
    BASE, "data", "epoch-astrometry", "GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml"
)
OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)

# DR4 pre-release ids (from the sample file itself + ESA's notebook name_dict)
SOURCE_ID = 4318465066420528000  # Gaia BH3
M1_MSUN = 0.76                   # primary mass adopted in the ESA notebook


def main():
    df = Table.read(XML, format="votable").to_pandas()
    sel = df[df["source_id"] == SOURCE_ID]
    log.info("BH3: %d transit rows", len(sel))

    ea = GaiaEpochAstrometryArchive.from_dataframe(sel)
    ea.epoch_data = ea.epoch_data.epochastrometryarchive.filter_on_used_by_agis()
    ea.epoch_data.epochastrometryarchive.sort_by_column("obs_time_tcb")
    ea.epoch_data.epochastrometryarchive.set_relative_time()
    ea.epoch_data = ea.epoch_data.epochastrometryarchive.set_scan_angle_derived_columns()
    d = ea.epoch_data
    log.info("After used_by_agis filter: %d CCD measurements", len(d))

    # ---- single-star model (kepmodel), exactly as the ESA notebook
    single = AstrometricModel(
        d["relative_time_day"].values,
        d["centroid_pos_al"].values,
        d["cos_theta"].values,
        d["sin_theta"].values,
        err=spleaf.term.Error(d["centroid_pos_error_al"].values),
        jit=spleaf.term.Jitter(0.0),
    )
    single.add_lin(d["sin_theta"].values, "ra")
    single.add_lin(d["cos_theta"].values, "dec")
    single.add_lin(d["parallax_factor_al"].values, "parallax")
    single.add_lin(d["relative_time_year"].values * d["sin_theta"].values, "mura")
    single.add_lin(d["relative_time_year"].values * d["cos_theta"].values, "mudec")
    single.fit()

    residuals = single.residuals()
    res_err = np.sqrt(single.cov.A)
    log.info("single-star rms residual: %.3f mas", np.std(residuals))

    # ---- periodogram of single-star residuals
    pmin, pmax, nfreq = 5.0, 10000.0, 10000
    nu0 = 2 * np.pi / pmax
    dnu = (2 * np.pi / pmin - nu0) / (nfreq - 1)
    model = copy.deepcopy(single)
    nu, power = model.periodogram(nu0, dnu, nfreq)
    periods = 2 * np.pi / nu
    kmax = int(np.argmax(power))
    fap = model.fap(power[kmax], nu.max())
    p_best = periods[kmax]
    log.info("periodogram peak: P = %.1f d, FAP = %.3g", p_best, fap)

    # ---- Keplerian fit
    kep = copy.deepcopy(model)
    kep.add_keplerian_from_period(p_best)
    kep.fit()
    kep.set_keplerian_param("0", param=["P", "Tp", "as", "e", "w", "i", "bigw"])
    kep.fit()

    kp = {k: kep.keplerian["0"]._par[i] for i, k in enumerate(kep.keplerian["0"]._param)}
    lp = {k: kep._lin_par[i] for i, k in enumerate(kep._lin_name)}

    # companion mass from the photocentre orbit (dark companion => photocentre = primary)
    a_m = convert_from_angular_to_linear(kp["as"], lp["parallax"])
    m2_kg = pjGet_m2(M1_MSUN * MS_kg, a_m, kp["P"])
    m2_msun = float(m2_kg / MS_kg)
    p_yr = kp["P"] / 365.25
    mass_function = kp["as"] ** 3 / (p_yr ** 2 * lp["parallax"] ** 3)

    lines = [
        "Gaia BH3 orbital fit on DR4 pre-release epoch astrometry",
        f"source_id (DR4 pre-release) : {SOURCE_ID}",
        f"n CCD measurements (AGIS)   : {len(d)}",
        f"single-star residual rms    : {np.std(residuals):.3f} mas",
        f"periodogram peak            : P = {p_best:.1f} d (FAP {fap:.3g})",
        "--- Keplerian (Campbell) elements ---",
        f"P    = {kp['P']:.2f} d ({p_yr:.3f} yr)",
        f"e    = {kp['e']:.4f}",
        f"a0   = {kp['as']:.4f} mas (photocentre semi-major axis)",
        f"i    = {np.degrees(kp['i']):.2f} deg",
        f"omega= {np.degrees(kp['w']):.2f} deg",
        f"Omega= {np.degrees(kp['bigw']):.2f} deg",
        f"Tp   = {kp['Tp']:.1f} d (rel. J2017.5)",
        "--- linear parameters ---",
        f"parallax = {lp['parallax']:.4f} mas",
        f"pm ra*   = {lp['mura']:.3f} mas/yr",
        f"pm dec   = {lp['mudec']:.3f} mas/yr",
        "--- masses ---",
        f"astrometric mass function   : {mass_function:.3f} Msun",
        f"adopted primary mass        : {M1_MSUN} Msun",
        f"=> companion mass           : {m2_msun:.2f} Msun",
        "(published: Gaia Collaboration / Panuzzo et al. 2024, A&A 686 L2: "
        "P = 11.6 yr, e = 0.729, MBH = 32.70 +/- 0.82 Msun)",
    ]
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(OUT, "bh3_orbit_fit.txt"), "w", newline="\n") as fh:
        fh.write(txt)
    print(txt)

    # ---- figure: residuals, periodogram, Keplerian-only signal vs time
    fig, axes = plt.subplots(3, 1, figsize=(9, 9))
    axes[0].errorbar(single.t, residuals, yerr=res_err, fmt="o", ms=3, ecolor="0.7", color="k")
    axes[0].axhline(0, ls="--", lw=0.8)
    axes[0].set_xlabel("relative time (days since J2017.5)")
    axes[0].set_ylabel("single-star residuals (mas)")
    axes[0].set_title(f"Gaia BH3 (DR4 pre-release {SOURCE_ID})")

    axes[1].plot(periods, power, "k", lw=1.0, rasterized=True)
    axes[1].axvline(p_best, color="r", lw=1.0)
    axes[1].set_xscale("log")
    axes[1].set_xlim(pmin, pmax)
    axes[1].set_xlabel("period (days)")
    axes[1].set_ylabel("normalized power")
    axes[1].set_title(f"residual periodogram: P = {p_best:.0f} d, FAP = {fap:.2g}")

    # Keplerian-only contribution at the epochs = full model minus linear part,
    # with the linear part rebuilt explicitly from the design columns we added
    lin_part = (
        lp["ra"] * d["sin_theta"].values
        + lp["dec"] * d["cos_theta"].values
        + lp["parallax"] * d["parallax_factor_al"].values
        + lp["mura"] * d["relative_time_year"].values * d["sin_theta"].values
        + lp["mudec"] * d["relative_time_year"].values * d["cos_theta"].values
    )
    kep_signal = kep.model() - lin_part
    kep_residuals = kep.residuals()
    order = np.argsort(kep.t)
    axes[2].plot(kep.t[order], kep_signal[order], "-", color="tab:blue", lw=0.8,
                 label="Keplerian AL signal (model)")
    axes[2].errorbar(kep.t, kep_signal + kep_residuals, yerr=np.sqrt(kep.cov.A),
                     fmt="o", ms=3, ecolor="0.8", color="k", label="data - linear part")
    axes[2].set_xlabel("relative time (days since J2017.5)")
    axes[2].set_ylabel("AL abscissa (mas)")
    axes[2].legend(loc="best", fontsize=8)
    axes[2].set_title(
        f"P = {kp['P']:.0f} d, e = {kp['e']:.3f}, a0 = {kp['as']:.2f} mas, "
        f"parallax = {lp['parallax']:.3f} mas -> M2 = {m2_msun:.1f} Msun (m1 = {M1_MSUN})"
    )
    fig.tight_layout()
    png = os.path.join(OUT, "bh3_orbit_fit.png")
    fig.savefig(png, dpi=120)
    log.info("Wrote %s", png)


if __name__ == "__main__":
    sys.exit(main())
