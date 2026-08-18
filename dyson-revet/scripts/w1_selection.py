"""W1: implementation of the Hephaistos II selection cuts (Suazo et al. 2024,
MNRAS 531, 695; arXiv:2405.02927) + acceptance test on the 7 published
candidates (A-G) and the 3 Hephaistos III add-ons (H-J, expected to FAIL the
SNR cut per Korn et al. 2026 Sec 2, arXiv:2607.25701).

Cuts implemented as code (paper section in brackets):
  C1  [2.1] Bailer-Jones EDR3 geometric distance r_med_geo < 300 pc
  C2  [2.1] W3 AND W4 detections (AllWISE ph_qual in A/B/C, i.e. not U upper
            limit) and no contamination flag (cc_flags == '0000')
  C3  [2.3] Dyson-sphere grid fit RMSE <= 0.2 mag over the 10-band
            Gaia+2MASS+AllWISE SED (model: Suazo Eqs 1-3; star templates =
            Pecaut & Mamajek 2013 empirical dwarf locus interpolated in M_G --
            the paper's 265 in-sample template stars are NOT published, this
            is the documented substitution; initial-pipeline grid T_DS in
            [100,700] K and gamma in [0.1,0.9])
  C5a [2.5.1] reject if Halpha pEW < 0 at 3 sigma (Gaia DR3
            astrophysical_parameters.ew_espels_halpha; negative = emission)
  C5b [2.5.2] Gvar < 2 (Vioque et al. 2020 definition; medians from a
            flux-matched random Gaia reference sample)
  C5c [2.5.3] RUWE < 1.4
  C5d [2.5.4] AllWISE ext_flg == 0
  C5e [2.5.5] classprob_dsc_combmod_star > 0.9
  C6  [2.6] AllWISE w3snr >= 3.5 AND w4snr >= 3.5

NOT reproducible from the paper (the boundary; see M1 doc):
  C4  [2.4] CNN nebular-image classifier: trained weights and the 960
            hand-labelled training images are not published.
  C7  [2.7] Visual inspection (368 -> 7): human judgement, not code.

Inputs:  data/photometry/candidates_gaia_chain.csv (w1_fetch_candidates.py)
         data/photometry/candidates_allwise_irsa.csv
         data/EEM_dwarf_UBVIJHK_colors_Teff.txt (Pecaut & Mamajek 2013 tbl,
           version 2022.04.16, https://www.pas.rochester.edu/~emamajek/
           EEM_dwarf_UBVIJHK_colors_Teff.txt)
Output:  out/w1_acceptance.csv, out/w1_ds_fits.csv, stdout report
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

# --- band constants ---------------------------------------------------------
# Vega zero points (Jy): 2MASS Cohen et al. 2003 (AJ 126, 1090); WISE Jarrett
# et al. 2011 / AllWISE Expl. Supp. IV.4.h (w4 zp per Jarrett+11 8.363 Jy West).
# Isophotal wavelengths (um): Cohen et al. 2003 (2MASS), Wright et al. 2010
# Table 1 (WISE).
BANDS = ["J", "H", "Ks", "W1", "W2", "W3", "W4"]
ZP_JY = {"J": 1594.0, "H": 1024.0, "Ks": 666.8,
         "W1": 309.540, "W2": 171.787, "W3": 31.674, "W4": 8.363}
LAM_UM = {"J": 1.235, "H": 1.662, "Ks": 2.159,
          "W1": 3.3526, "W2": 4.6028, "W3": 11.5608, "W4": 22.0883}
OPT_BANDS = ["BP", "G", "RP"]  # DS blackbody contributes 0 there (T<=700K)

H_CK = 14387.769  # um*K  (h c / k_B)
SNR_MIN = 3.5
RMSE_MAX = 0.2

GVAR_CACHE = DATA / "photometry" / "gvar_reference.csv"


# --- Pecaut & Mamajek template locus ---------------------------------------
PM13_URL = ("https://www.pas.rochester.edu/~emamajek/"
            "EEM_dwarf_UBVIJHK_colors_Teff.txt")


def load_pm13() -> pd.DataFrame:
    path = DATA / "EEM_dwarf_UBVIJHK_colors_Teff.txt"
    if not path.exists():  # data/ is gitignored; fetch on first use
        import requests
        r = requests.get(PM13_URL, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
    rows = []
    header = None
    for ln in path.read_text().splitlines():
        if ln.startswith("#SpT") and header is None:
            header = ln.lstrip("#").split()
        elif header and ln and not ln.startswith("#"):
            parts = ln.split()
            if len(parts) == len(header):
                rows.append(parts)
    df = pd.DataFrame(rows, columns=header)

    def num(col):
        return pd.to_numeric(df[col].str.replace("...", "nan", regex=False)
                             .str.replace(":", "", regex=False), errors="coerce")

    out = pd.DataFrame({
        "SpT": df["SpT"], "Teff": num("Teff"), "logL": num("logL"),
        "M_G": num("M_G"), "Bp_Rp": num("Bp-Rp"), "G_Rp": num("G-Rp"),
        "M_J": num("M_J"), "M_Ks": num("M_Ks"), "J_H": num("J-H"),
        "H_Ks": num("H-K") if "H-K" in df else num("H-Ks"),
        "Ks_W1": num("Ks-W1"), "W1_W2": num("W1-W2"),
        "W1_W3": num("W1-W3"), "W1_W4": num("W1-W4"),
    })
    # dwarf locus rows with the optical/NIR/W1 columns we need (K..M range;
    # W2/W3/W4 come from the empirical locus, see template_grid)
    out = out.dropna(subset=["M_G", "Bp_Rp", "G_Rp", "M_J", "M_Ks",
                             "Ks_W1", "H_Ks", "logL"])
    out = out[(out["M_G"] > 5.0) & (out["M_G"] < 15.0)].sort_values("M_G")
    return out.reset_index(drop=True)


_LOCUS_CACHE: list[pd.DataFrame] = []


def wise_locus() -> pd.DataFrame:
    """Empirical M-dwarf photospheric W1-W2/W1-W3/W1-W4 vs M_G locus
    (built by w1_fetch_locus.py from <30 pc dwarfs with clean W3/W4;
    PM13 has no WISE colors for K6V-M4.5V)."""
    if not _LOCUS_CACHE:
        path = DATA / "photometry" / "mdwarf_wise_locus.csv"
        if not path.exists():
            raise FileNotFoundError("run scripts/w1_fetch_locus.py first")
        _LOCUS_CACHE.append(pd.read_csv(path))
    return _LOCUS_CACHE[0]


def template_grid(pm: pd.DataFrame, mg_lo: float, mg_hi: float,
                  step: float = 0.05) -> dict[str, np.ndarray]:
    """Continuous MS template absolute magnitudes vs M_G (linear interp).

    Optical/NIR/W1 from Pecaut & Mamajek 2013; W2/W3/W4 photospheric colors
    from the empirical nearby-dwarf locus (see wise_locus)."""
    mg = np.arange(mg_lo, mg_hi + step, step)
    t = {"M_G": mg}
    interp = lambda col: np.interp(mg, pm["M_G"], pm[col])  # noqa: E731
    # Bp-Rp = BP-RP and G-Rp = G-RP  =>  M_BP = M_G + (Bp-Rp) - (G-Rp)
    t["BP"] = mg + interp("Bp_Rp") - interp("G_Rp")
    t["G"] = mg
    t["RP"] = mg - interp("G_Rp")
    t["J"] = interp("M_J")
    t["Ks"] = interp("M_Ks")
    t["H"] = t["Ks"] + interp("H_Ks")
    t["W1"] = t["Ks"] - interp("Ks_W1")
    loc = wise_locus()
    t["W2"] = t["W1"] - np.interp(mg, loc["mg"], loc["w12"])
    t["W3"] = t["W1"] - np.interp(mg, loc["mg"], loc["w13"])
    t["W4"] = t["W1"] - np.interp(mg, loc["mg"], loc["w14"])
    # per-star scatter of the photospheric MIR colors (the paper's 265 real
    # template stars carry this diversity; the median locus does not)
    t["W3_sig"] = np.interp(mg, loc["mg"], loc["w13_scatter"])
    t["W4_sig"] = np.interp(mg, loc["mg"], loc["w14_scatter"])
    t["logL"] = np.interp(mg, pm["M_G"], pm["logL"])
    return t


# --- Dyson-sphere model (Suazo et al. 2024 Eqs 1-3) -------------------------
def ds_absolute_mags(t_ds: np.ndarray, gamma: np.ndarray, logl: np.ndarray
                     ) -> dict[str, np.ndarray]:
    """Absolute Vega mags of the DS blackbody in JHKs+W1-4.

    DS bolometric flux at d=10pc: F = gamma * L / (4 pi d^2);
    B_nu normalised: f_nu(lam) = F * pi * B_nu(lam,T) / (sigma T^4)
    with B_nu in per-frequency units; mags via Vega zero points.
    Monochromatic (isophotal-wavelength) approximation -- documented.
    """
    L_SUN = 3.828e26        # W (IAU)
    PC = 3.0857e16          # m
    SB = 5.670374e-8        # W m-2 K-4
    C = 2.99792458e8        # m/s
    H = 6.62607015e-34      # J s
    KB = 1.380649e-23       # J/K

    F_bol = gamma * (10.0 ** logl) * L_SUN / (4 * np.pi * (10 * PC) ** 2)
    out = {}
    for b in BANDS:
        lam = LAM_UM[b] * 1e-6
        nu = C / lam
        bnu = (2 * H * nu ** 3 / C ** 2 /
               np.expm1(H * nu / (KB * np.maximum(t_ds, 1.0))))
        fnu = F_bol * np.pi * bnu / (SB * np.maximum(t_ds, 1.0) ** 4)  # W/m2/Hz
        fnu_jy = fnu / 1e-26
        with np.errstate(divide="ignore"):
            out[b] = -2.5 * np.log10(fnu_jy / ZP_JY[b])
    return out


def combine(m1: np.ndarray, m2: np.ndarray) -> np.ndarray:
    """Suazo Eq 1: magnitude of the sum of two components."""
    return -2.5 * np.log10(10 ** (-0.4 * m1) + 10 ** (-0.4 * m2))


def fit_ds(obs_abs: dict[str, float], pm: pd.DataFrame,
           t_lo: float, t_hi: float, g_lo: float, g_hi: float,
           nt: int = 90, ng: int = 45,
           template_sigma_steps: tuple = (0.0,)) -> dict:
    """Grid-search best (template M_G, T_DS, gamma); return RMSE and params.

    RMSE over all 10 bands, equal weights, no errors (paper Sec 2.3).
    template_sigma_steps: multiples of the empirical photospheric W3/W4 color
    scatter by which the template MIR colors may shift -- (0,) uses the
    median locus only; e.g. (-1, -0.5, 0, 0.5, 1) emulates the diversity of
    the paper's 265 individual template stars (documented in the M1 doc).
    """
    mg0 = obs_abs["G"]
    tgrid = template_grid(pm, mg0 - 0.6, mg0 + 0.6)
    ts = np.linspace(t_lo, t_hi, nt)
    gs = np.geomspace(g_lo, g_hi, ng)
    T, Gam = np.meshgrid(ts, gs, indexing="ij")          # (nt, ng)
    best = dict(rmse=np.inf)
    bands_all = OPT_BANDS + BANDS
    obs_vec = np.array([obs_abs[b] for b in bands_all])

    for i in range(len(tgrid["M_G"])):
        logl = np.full_like(T, tgrid["logL"][i])
        dsm = ds_absolute_mags(T, Gam, logl)             # dict of (nt,ng)
        dim = -2.5 * np.log10(1 - Gam)                   # Eq 3 obscuration
        for ksig in template_sigma_steps:
            model = np.empty(T.shape + (len(bands_all),))
            for k, b in enumerate(bands_all):
                tb = tgrid[b][i]
                if ksig and b == "W3":
                    tb = tb - ksig * tgrid["W3_sig"][i]
                elif ksig and b == "W4":
                    tb = tb - ksig * tgrid["W4_sig"][i]
                mstar = tb + dim
                model[..., k] = combine(mstar, dsm[b]) if b in BANDS else mstar
            rmse = np.sqrt(((model - obs_vec) ** 2).mean(axis=-1))
            j = np.unravel_index(np.argmin(rmse), rmse.shape)
            if rmse[j] < best["rmse"]:
                best = dict(rmse=float(rmse[j]), t_ds=float(T[j]),
                            gamma=float(Gam[j]),
                            template_mg=float(tgrid["M_G"][i]),
                            template_ksig=float(ksig))
    return best


# --- Gvar (Vioque et al. 2020 definition, paper Sec 2.5.2) ------------------
def gvar_reference() -> pd.DataFrame:
    """Random Gaia DR3 sample, G in [15.5, 19.0], for flux-matched medians."""
    if GVAR_CACHE.exists():
        return pd.read_csv(GVAR_CACHE)
    import pyvo
    svc = pyvo.dal.TAPService("https://gea.esac.esa.int/tap-server/tap")
    q = """
    SELECT phot_g_mean_flux, phot_g_mean_flux_error, phot_g_n_obs,
           phot_g_mean_mag
    FROM gaiadr3.gaia_source
    WHERE phot_g_mean_mag BETWEEN 15.5 AND 19.0 AND random_index < 400000
    """
    df = svc.search(q).to_table().to_pandas()
    df.to_csv(GVAR_CACHE, index=False)
    return df


def gvar(row: pd.Series, ref: pd.DataFrame) -> float:
    sel = ref[np.abs(ref["phot_g_mean_mag"] - row["phot_g_mean_mag"]) < 0.10]
    fp = sel["phot_g_mean_flux"].median()
    ep = sel["phot_g_mean_flux_error"].median()
    npr = sel["phot_g_n_obs"].median()
    return float((fp * row["phot_g_mean_flux_error"]
                  * np.sqrt(row["phot_g_n_obs"]))
                 / (row["phot_g_mean_flux"] * ep * np.sqrt(npr)))


# --- main --------------------------------------------------------------------
PAPER = {  # published Table 5 / Heph III Table 3 values for cross-checks
    "A": dict(gvar=1.03, ruwe=1.03, snr3=22.5, snr4=16.6, tds=138, gam=0.08),
    "B": dict(gvar=0.94, ruwe=1.06, snr3=13.9, snr4=3.8, tds=275, gam=0.06),
    "C": dict(gvar=0.90, ruwe=1.21, snr3=10.5, snr4=5.0, tds=187, gam=0.14),
    "D": dict(gvar=0.97, ruwe=0.96, snr3=10.4, snr4=4.8, tds=178, gam=0.16),
    "E": dict(gvar=0.90, ruwe=1.05, snr3=10.3, snr4=3.6, tds=180, gam=0.08),
    "F": dict(gvar=0.93, ruwe=1.01, snr3=5.7, snr4=4.5, tds=137, gam=0.03),
    "G": dict(gvar=0.99, ruwe=1.01, snr3=5.0, snr4=3.5, tds=100, gam=0.13),
    "H": dict(gvar=np.nan, ruwe=np.nan, snr3=2.4, snr4=3.3, tds=130, gam=0.103),
    "I": dict(gvar=np.nan, ruwe=np.nan, snr3=2.4, snr4=3.3, tds=99, gam=0.147),
    "J": dict(gvar=np.nan, ruwe=np.nan, snr3=2.2, snr4=2.8, tds=114, gam=0.058),
}


def main() -> None:
    gaia = pd.read_csv(DATA / "photometry" / "candidates_gaia_chain.csv")
    irsa_path = DATA / "photometry" / "candidates_allwise_irsa.csv"
    if irsa_path.exists():
        irsa = pd.read_csv(irsa_path)
        irsa = irsa.sort_values("w3snr", ascending=False).groupby("label").first()
        print("using IRSA w?snr columns")
    else:
        # snr proxy 1.0857/sigmpro from the Gaia-hosted AllWISE copy: verified
        # to reproduce the paper's Table 5 / Heph III Table 3 S/N values to
        # +-0.2 for all 10 candidates (see M1 doc)
        irsa = gaia.set_index("label")[["w1mpro", "w2mpro", "w3mpro", "w4mpro",
                                        "cc_flags", "ext_flag", "ph_qual"]].copy()
        irsa["w3snr"] = 1.0857 / gaia.set_index("label")["w3mpro_error"]
        irsa["w4snr"] = 1.0857 / gaia.set_index("label")["w4mpro_error"]
        irsa = irsa.rename(columns={"ext_flag": "ext_flg"})
        print("IRSA pull absent -> using validated snr proxy 1.0857/sigmpro")

    pm = load_pm13()
    ref = gvar_reference()
    print(f"Gvar reference sample: {len(ref)} stars (G 15.5-19.0)")

    rows, fits = [], []
    for _, r in gaia.iterrows():
        lab = r["label"]
        w = irsa.loc[lab]
        ph = str(w["ph_qual"])
        gv = gvar(r, ref)

        # observed absolute magnitudes (BJ geometric distance)
        dmod = 5 * np.log10(r["r_med_geo"] / 10.0)
        obs = {"BP": r["phot_bp_mean_mag"], "G": r["phot_g_mean_mag"],
               "RP": r["phot_rp_mean_mag"], "J": r["j_m"], "H": r["h_m"],
               "Ks": r["ks_m"], "W1": w["w1mpro"], "W2": w["w2mpro"],
               "W3": w["w3mpro"], "W4": w["w4mpro"]}
        obs_abs = {k: v - dmod for k, v in obs.items()}

        # C3: stated initial T range [100,700] K, but gamma floor relaxed
        # 0.1 -> 0.01, because the paper's own candidate F has gamma =
        # 0.03 +- 0.008 (their Table 5), 9 sigma below the stated gamma >= 0.1
        # grid floor -- with the floor as stated, F cannot pass the RMSE gate
        # (needs gamma <= 0.07; see M1 doc, "reproducibility boundary").
        # Template-color diversity +-1 sigma emulates their 265 real templates.
        steps = (-1.0, -0.5, 0.0, 0.5, 1.0)
        sel_fit = fit_ds(obs_abs, pm, 100, 700, 0.01, 0.90,
                         template_sigma_steps=steps)
        stated = fit_ds(obs_abs, pm, 100, 700, 0.10, 0.90,
                        template_sigma_steps=steps)
        sel_fit["rmse_stated_gfloor"] = stated["rmse"]
        ref_fit = fit_ds(obs_abs, pm, 10, 400, 1e-4, 0.40, nt=120, ng=60)
        fits.append(dict(label=lab, **{f"sel_{k}": v for k, v in sel_fit.items()},
                         **{f"ref_{k}": v for k, v in ref_fit.items()},
                         paper_tds=PAPER[lab]["tds"], paper_gam=PAPER[lab]["gam"]))

        halpha_emission_3sig = (
            pd.notna(r["ew_espels_halpha"])
            and r["ew_espels_halpha"] < 0
            and abs(r["ew_espels_halpha"]) >= 3 * r["ew_espels_halpha_uncertainty"])

        checks = {
            "C1_dist300": r["r_med_geo"] < 300,
            "C2_w34det": ph[2] in "ABC" and ph[3] in "ABC",
            "C2_ccflags0": str(w["cc_flags"]).strip() in ("0000", "0"),
            "C3_rmse": sel_fit["rmse"] <= RMSE_MAX,
            "C5a_halpha": not halpha_emission_3sig,
            "C5b_gvar": gv < 2.0,
            "C5c_ruwe": r["ruwe"] < 1.4,
            "C5d_extflg": int(w["ext_flg"]) == 0,
            "C5e_starprob": r["classprob_dsc_combmod_star"] > 0.9,
            "C6_snr": (w["w3snr"] >= SNR_MIN) and (w["w4snr"] >= SNR_MIN),
        }
        rows.append(dict(
            label=lab, gaia_id=r["source_id"], r_med_geo=r["r_med_geo"],
            ruwe=r["ruwe"], gvar=gv, gvar_paper=PAPER[lab]["gvar"],
            ew_halpha=r["ew_espels_halpha"],
            ew_halpha_unc=r["ew_espels_halpha_uncertainty"],
            starprob=r["classprob_dsc_combmod_star"],
            w3snr=w["w3snr"], w4snr=w["w4snr"],
            w3snr_paper=PAPER[lab]["snr3"], w4snr_paper=PAPER[lab]["snr4"],
            ph_qual=ph, cc_flags=w["cc_flags"], ext_flg=w["ext_flg"],
            rmse_sel=sel_fit["rmse"], tds_sel=sel_fit["t_ds"],
            gam_sel=sel_fit["gamma"],
            rmse_stated_gfloor=sel_fit["rmse_stated_gfloor"],
            **checks,
            PASS_ALL=all(checks.values()),
        ))

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "w1_acceptance.csv", index=False)
    pd.DataFrame(fits).to_csv(OUT / "w1_ds_fits.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    print("\n== cross-checks vs published values ==")
    print(df[["label", "gvar", "gvar_paper", "ruwe", "w3snr", "w3snr_paper",
              "w4snr", "w4snr_paper", "rmse_sel", "tds_sel", "gam_sel"]]
          .to_string(index=False))
    print("\n== cut results ==")
    ccols = [c for c in df.columns if c.startswith("C")] + ["PASS_ALL"]
    print(df[["label"] + ccols].to_string(index=False))
    n7 = df[df["label"].isin(list("ABCDEFG"))]["PASS_ALL"].sum()
    print(f"\nACCEPTANCE: {n7}/7 Hephaistos II candidates pass all coded cuts.")
    hij = df[df["label"].isin(list("HIJ"))]
    print("H/I/J (expected to fail C6 only): "
          + ", ".join(f"{r.label}: C6={'PASS' if r.C6_snr else 'FAIL'}"
                      f" others={'PASS' if all([r.C1_dist300, r.C2_w34det, r.C2_ccflags0, r.C3_rmse, r.C5a_halpha, r.C5b_gvar, r.C5c_ruwe, r.C5d_extflg, r.C5e_starprob]) else 'FAIL'}"
                      for r in hij.itertuples()))


if __name__ == "__main__":
    main()
