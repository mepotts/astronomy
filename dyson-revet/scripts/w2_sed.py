"""W2(c): archival SEDs for candidates D and I (control C included) from the
VizieR photometry (sed) service, plus a photosphere+excess decomposition.

Services:
  - CDS VizieR sed API (anonymous): https://vizier.cds.unistra.fr/viz-bin/sed
    (was 502-down on 2026-08-16; up again 2026-08-18)
  - Photosphere template: Pecaut & Mamajek 2013 dwarf locus (see
    w1_selection.py), obscured per Suazo Eq 3; excess = blackbody (Suazo
    Eqs 1-3) -- the refined-grid fit from w1_selection.fit_ds.

Output: data/photometry/sed_{label}.csv (all harvested points),
        out/w2_sed_{label}.png, out/w2_sed_fits.csv
"""

from __future__ import annotations

import io
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from astropy.table import Table

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "photometry"
OUT = ROOT / "out"
sys.path.insert(0, str(ROOT / "scripts"))
from w1_selection import (BANDS, LAM_UM, OPT_BANDS, ZP_JY,  # noqa: E402
                          ds_absolute_mags, fit_ds, load_pm13, template_grid)

SED_URL = "https://vizier.cds.unistra.fr/viz-bin/sed"
TARGETS = {
    "C": dict(ra=74.01205, dec=-74.17051),
    "D": dict(ra=351.96373, dec=5.10726),
    "I": dict(ra=144.97633, dec=7.00774),
}
C_UM_GHZ = 299792.458  # c in um*GHz


def harvest(label: str, ra: float, dec: float, radius_arcsec: float = 3.0
            ) -> pd.DataFrame:
    cache = DATA / f"sed_{label}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    r = requests.get(SED_URL, params={"-c": f"{ra} {dec:+f}",
                                      "-c.rs": str(radius_arcsec)}, timeout=180)
    r.raise_for_status()
    t = Table.read(io.BytesIO(r.content), format="votable").to_pandas()
    # columns: _RAJ2000 _DEJ2000 _tabname _ID ... sed_freq[GHz] sed_flux[Jy]
    #          sed_eflux sed_filter
    t["lam_um"] = C_UM_GHZ / t["sed_freq"]
    dra = (t["_RAJ2000"] - ra) * np.cos(np.radians(dec))
    dde = t["_DEJ2000"] - dec
    t["sep_arcsec"] = np.hypot(dra, dde) * 3600.0
    for c in ("_tabname", "sed_filter"):
        if t[c].dtype == object:
            t[c] = t[c].astype(str)
    t = t.sort_values("lam_um").reset_index(drop=True)
    t.to_csv(cache, index=False)
    return t


def model_curves(row: pd.Series, fit: dict) -> tuple[dict, dict, np.ndarray]:
    """Template + DS model magnitudes/fluxes for plotting."""
    pm = load_pm13()
    dmod = 5 * np.log10(row["r_med_geo"] / 10.0)
    tg = template_grid(pm, fit["template_mg"] - 0.01, fit["template_mg"] + 0.01)
    star_abs = {b: tg[b][0] for b in OPT_BANDS + BANDS}
    logl = np.array([tg["logL"][0]])
    ds_abs = ds_absolute_mags(np.array([fit["t_ds"]]),
                              np.array([fit["gamma"]]), logl)
    dim = -2.5 * np.log10(1 - fit["gamma"])
    lam_all = {"BP": 0.511, "G": 0.622, "RP": 0.777, **LAM_UM}
    zp_all = {"BP": 3552.0, "G": 3229.0, "RP": 2555.0, **ZP_JY}
    # Gaia Vega zps in Jy (approx, Evans et al. 2018 / SVO filter service --
    # display only, the fit itself works in magnitudes)
    star_jy, comp_jy = {}, {}
    for b in OPT_BANDS + BANDS:
        m_star = star_abs[b] + dim + dmod
        star_jy[lam_all[b]] = zp_all[b] * 10 ** (-0.4 * m_star)
        if b in BANDS:
            m_ds = float(ds_abs[b][0]) + dmod
            comp = -2.5 * np.log10(10 ** (-0.4 * m_star) + 10 ** (-0.4 * m_ds))
        else:
            comp = m_star
        comp_jy[lam_all[b]] = zp_all[b] * 10 ** (-0.4 * comp)
    lam = np.array(sorted(star_jy))
    return star_jy, comp_jy, lam


def main() -> None:
    gc = pd.read_csv(DATA / "candidates_gaia_chain.csv")
    fits_rows = []
    for label, t in TARGETS.items():
        print(f"== {label}")
        sed = harvest(label, t["ra"], t["dec"])
        print(f"  VizieR sed points: {len(sed)} from "
              f"{sed['_tabname'].nunique()} catalog tables")

        row = gc[gc["label"] == label].iloc[0]
        dmod = 5 * np.log10(row["r_med_geo"] / 10.0)
        obs = {"BP": row["phot_bp_mean_mag"], "G": row["phot_g_mean_mag"],
               "RP": row["phot_rp_mean_mag"], "J": row["j_m"], "H": row["h_m"],
               "Ks": row["ks_m"], "W1": row["w1mpro"], "W2": row["w2mpro"],
               "W3": row["w3mpro"], "W4": row["w4mpro"]}
        obs_abs = {k: v - dmod for k, v in obs.items()}
        fit = fit_ds(obs_abs, load_pm13(), 10, 400, 1e-4, 0.40, nt=120, ng=60)
        fit["label"] = label
        fits_rows.append(fit)
        print(f"  photosphere+excess fit: T_excess={fit['t_ds']:.0f} K, "
              f"gamma={fit['gamma']:.3f}, RMSE={fit['rmse']:.3f} mag")

        star_jy, comp_jy, lam = model_curves(row, fit)

        fig, ax = plt.subplots(figsize=(8, 5.5))
        near = sed[sed["sep_arcsec"] <= 2.0]
        ax.errorbar(near["lam_um"], near["sed_flux"] * 1e3,
                    yerr=near["sed_eflux"] * 1e3, fmt="o", ms=4, alpha=0.55,
                    color="#3466a4", label=f"VizieR sed (<=2\", n={len(near)})")
        far = sed[sed["sep_arcsec"] > 2.0]
        if len(far):
            ax.plot(far["lam_um"], far["sed_flux"] * 1e3, "x", ms=4,
                    alpha=0.4, color="#888888",
                    label=f"sed 2-3\" away (n={len(far)})")
        ax.plot(lam, [star_jy[x] * 1e3 for x in lam], "--", color="#444444",
                label="PM13 photosphere (obscured)")
        ax.plot(lam, [comp_jy[x] * 1e3 for x in lam], "-", color="#c23b22",
                label=(f"+ blackbody excess T={fit['t_ds']:.0f} K, "
                       f"gamma={fit['gamma']:.3f}"))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("wavelength [um]")
        ax.set_ylabel("flux density [mJy]")
        ax.set_title(f"Candidate {label}: archival SED "
                     f"(RMSE {fit['rmse']:.3f} mag over 10 bands)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25, which="both")
        fig.tight_layout()
        fig.savefig(OUT / f"w2_sed_{label}.png", dpi=130)
        plt.close(fig)

    pd.DataFrame(fits_rows).to_csv(OUT / "w2_sed_fits.csv", index=False)
    print("wrote out/w2_sed_fits.csv")


if __name__ == "__main__":
    main()
