"""W1 fetch: Gaia DR3 + 2MASS + AllWISE (+CatWISE2020) photometry for the 10
labelled Dyson-sphere candidates (A-G: Suazo et al. 2024 = Hephaistos II;
H/I/J: Korn et al. 2026 = Hephaistos III).

Candidate labels and Gaia DR3 source_ids from:
  - Hephaistos II Table 5 (A-G): https://arxiv.org/abs/2405.02927 (MNRAS 531, 695)
  - Ren et al. 2026 Table 1 (A-J + J2016 positions): https://arxiv.org/abs/2607.03619
  - Hephaistos III Table 3 (H-J): https://arxiv.org/abs/2607.25701

Services (all anonymous):
  - ESA Gaia TAP  https://gea.esac.esa.int/tap-server/tap
      gaia_source x astrophysical_parameters (Halpha pEW) x external.gaiaedr3_distance
      x allwise_best_neighbour x gaiadr1.allwise_original_valid
      x tmass_psc_xsc_best_neighbour x tmass_psc_xsc_join x gaiadr1.tmass_original_valid
      (this is the same cross-match route Hephaistos II Sec 2.1 says it used)
  - IRSA TAP      https://irsa.ipac.caltech.edu/TAP
      allwise_p3as_psd  (w1snr..w4snr, cc_flags, ext_flg, ph_qual)
      catwise_2020      (W1/W2 only -- CatWISE2020 has NO W3/W4; see M1 doc)

Output: data/photometry/candidates_gaia_chain.csv,
        data/photometry/candidates_allwise_irsa.csv,
        data/photometry/candidates_catwise.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyvo

sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 stdout trap

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "data" / "photometry"
OUTDIR.mkdir(parents=True, exist_ok=True)

GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap"
IRSA_TAP = "https://irsa.ipac.caltech.edu/TAP"

# label -> (gaia_dr3_source_id, ra_j2016, dec_j2016)  [Ren et al. 2026 Table 1]
CANDIDATES = {
    "A": (3496509309189181184, 191.30392, -26.86758),
    "B": (4843191593270342656, 59.01583, -40.53001),
    "C": (4649396037451459712, 74.01205, -74.17051),
    "D": (2660349163149053824, 351.96373, 5.10726),
    "E": (3190232820489766656, 60.53249, -10.91131),
    "F": (2956570141274256512, 78.44374, -25.18643),
    "G": (2644370304260053376, 353.88537, -0.07339),
    "H": (2437221214075471744, 354.01111, -9.33344),
    "I": (3854090071297359616, 144.97633, 7.00774),
    "J": (651765552072217216, 128.06908, 14.70515),
}


def fetch_gaia_chain() -> pd.DataFrame:
    """Per-table sync queries on primary keys (fast), merged locally."""
    ids = ",".join(str(v[0]) for v in CANDIDATES.values())
    svc = pyvo.dal.TAPService(GAIA_TAP)

    def sq(q: str) -> pd.DataFrame:
        return svc.search(q).to_table().to_pandas()

    df = sq(f"""
        SELECT source_id, ra, dec, pmra, pmdec, parallax, parallax_error,
               ruwe, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
               phot_g_mean_flux, phot_g_mean_flux_error, phot_g_n_obs,
               bp_rp, teff_gspphot, classprob_dsc_combmod_star
        FROM gaiadr3.gaia_source WHERE source_id IN ({ids})""")
    print(f"  gaia_source: {len(df)}")

    ap = sq(f"""
        SELECT source_id, ew_espels_halpha, ew_espels_halpha_uncertainty
        FROM gaiadr3.astrophysical_parameters WHERE source_id IN ({ids})""")
    print(f"  astrophysical_parameters: {len(ap)}")
    df = df.merge(ap, on="source_id", how="left")

    d = sq(f"""
        SELECT source_id, r_med_geo, r_lo_geo, r_hi_geo
        FROM external.gaiaedr3_distance WHERE source_id IN ({ids})""")
    print(f"  gaiaedr3_distance: {len(d)}")
    df = df.merge(d, on="source_id", how="left")

    ab = sq(f"""
        SELECT source_id, original_ext_source_id AS allwise_designation,
               angular_distance AS allwise_sep_arcsec, allwise_oid
        FROM gaiadr3.allwise_best_neighbour WHERE source_id IN ({ids})""")
    print(f"  allwise_best_neighbour: {len(ab)}")
    df = df.merge(ab, on="source_id", how="left")

    oids = ",".join(str(int(x)) for x in ab["allwise_oid"].dropna())
    w = sq(f"""
        SELECT allwise_oid, w1mpro, w1mpro_error, w2mpro, w2mpro_error,
               w3mpro, w3mpro_error, w4mpro, w4mpro_error,
               cc_flags, ext_flag, ph_qual,
               w1mjd_mean, w2mjd_mean, w3mjd_mean, w4mjd_mean
        FROM gaiadr1.allwise_original_valid WHERE allwise_oid IN ({oids})""")
    print(f"  allwise_original_valid: {len(w)}")
    df = df.merge(w, on="allwise_oid", how="left")

    tb = sq(f"""
        SELECT source_id, original_ext_source_id AS tmass_designation
        FROM gaiadr3.tmass_psc_xsc_best_neighbour WHERE source_id IN ({ids})""")
    print(f"  tmass_psc_xsc_best_neighbour: {len(tb)}")
    df = df.merge(tb, on="source_id", how="left")

    desigs = [x for x in df["tmass_designation"].dropna().astype(str) if x]
    dlist = ",".join(f"'{x}'" for x in desigs)
    tm = sq(f"""
        SELECT designation AS tmass_designation, j_m, j_msigcom, h_m, h_msigcom,
               ks_m, ks_msigcom, ph_qual AS tmass_ph_qual
        FROM gaiadr1.tmass_original_valid WHERE designation IN ({dlist})""")
    print(f"  tmass_original_valid: {len(tm)}")
    df = df.merge(tm, on="tmass_designation", how="left")

    id2label = {v[0]: k for k, v in CANDIDATES.items()}
    df["label"] = df["source_id"].map(id2label)
    return df.sort_values("label").reset_index(drop=True)


def fetch_irsa_allwise() -> pd.DataFrame:
    """AllWISE psd rows (with snr columns) within 3 arcsec of each J2016 position.

    3 arcsec covers the <=0.6 arcsec of proper motion between J2010.5 (AllWISE)
    and J2016.0 for these stars (largest PM: A, 89 mas/yr -> 0.5 arcsec).
    """
    svc = pyvo.dal.TAPService(IRSA_TAP)
    rows = []
    for label, (sid, ra, dec) in CANDIDATES.items():
        q = f"""
        SELECT designation, ra, dec, w1mpro, w1sigmpro, w2mpro, w2sigmpro,
               w3mpro, w3sigmpro, w4mpro, w4sigmpro,
               w1snr, w2snr, w3snr, w4snr, cc_flags, ext_flg, ph_qual,
               tmass_key, n_2mass, j_m_2mass, h_m_2mass, k_m_2mass
        FROM allwise_p3as_psd
        WHERE CONTAINS(POINT('ICRS', ra, dec),
                       CIRCLE('ICRS', {ra}, {dec}, {3.0 / 3600.0})) = 1
        """
        t = svc.search(q).to_table().to_pandas()
        t["label"] = label
        t["gaia_source_id"] = sid
        rows.append(t)
        print(f"  IRSA AllWISE {label}: {len(t)} row(s)")
    return pd.concat(rows, ignore_index=True)


def fetch_catwise() -> pd.DataFrame:
    """CatWISE2020 (W1/W2 only) within 3 arcsec of each J2016 position."""
    svc = pyvo.dal.TAPService(IRSA_TAP)
    rows = []
    for label, (sid, ra, dec) in CANDIDATES.items():
        q = f"""
        SELECT source_name, ra, dec, w1mpro, w1sigmpro, w2mpro, w2sigmpro,
               w1snr, w2snr, cc_flags, ab_flags
        FROM catwise_2020
        WHERE CONTAINS(POINT('ICRS', ra, dec),
                       CIRCLE('ICRS', {ra}, {dec}, {3.0 / 3600.0})) = 1
        """
        t = svc.search(q).to_table().to_pandas()
        t["label"] = label
        t["gaia_source_id"] = sid
        rows.append(t)
        print(f"  CatWISE2020 {label}: {len(t)} row(s)")
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    print("Fetching Gaia DR3 chain (gaia_source x AP x BJ-dist x AllWISE x 2MASS) ...")
    gaia = fetch_gaia_chain()
    gaia.to_csv(OUTDIR / "candidates_gaia_chain.csv", index=False)
    print(f"  {len(gaia)} rows -> candidates_gaia_chain.csv")
    print(gaia[["label", "ruwe", "r_med_geo", "phot_g_mean_mag",
                "classprob_dsc_combmod_star", "allwise_designation"]]
          .to_string(index=False))

    print("Fetching IRSA AllWISE (snr + flags) ...")
    irsa = fetch_irsa_allwise()
    irsa.to_csv(OUTDIR / "candidates_allwise_irsa.csv", index=False)

    print("Fetching CatWISE2020 (W1/W2 only) ...")
    cat = fetch_catwise()
    cat.to_csv(OUTDIR / "candidates_catwise.csv", index=False)

    print("done.")


if __name__ == "__main__":
    main()
