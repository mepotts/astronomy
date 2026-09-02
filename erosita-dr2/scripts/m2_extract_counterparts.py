"""M2: extract NWAY counterpart rows for the DR2-detected candidates.

Reads the three Main counterpart catalogs (eRASSc3_Main_{GDR3,LS10,CW2020}, local
gz FITS, ~2M rows each; Ramos-Ceja et al. Sect. 6) serially and pulls the rows whose
IAUNAME is in the candidate list (pair + new_bright sets - vanished sources have no
DR2 entry so cannot appear). Also flags candidates present in the Hard catalog
(eRASS3_Hard_v1.2.fits) via a 15" positional match.

Output: out/m2_counterparts.csv - one row per DR2-detected candidate, with
NWAY p_any/p_i/match_flag + counterpart id/photometry per variant, the consortium
UID_5XMM/UID_2RXS/UID_CSC crosswalks, and Hard-catalog membership.
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"

VARIANTS = {
    "GDR3": ("eRASSc3_Main_GDR3_Public_27Jul2026.fits.gz", [
        "IAUNAME", "UID_5XMM", "UID_2RXS", "UID_CSC",
        "GDR3_source_id", "GDR3_Xray_proba", "NWAY_Separation_GDR3_ERO",
        "NWAY_p_any", "NWAY_p_i", "NWAY_match_flag",
        "GDR3_parallax", "GDR3_parallax_error", "GDR3_pm", "GDR3_ruwe",
        "GDR3_phot_g_mean_mag", "GDR3_phot_bp_mean_mag", "GDR3_phot_rp_mean_mag",
        "GDR3_PQSO", "GDR3_PGal", "GDR3_Pstar",
    ]),
    "LS10": ("eRASSc3_Main_LS10_Public_27Jul2026.fits.gz", [
        "IAUNAME", "ERO_LS10_FULLID", "LS10_Xray_proba", "NWAY_Separation_LS10_ERO",
        "NWAY_p_any", "NWAY_p_i", "NWAY_match_flag", "LS10_TYPE",
        "dered_mag_g", "dered_mag_r", "dered_mag_z", "dered_mag_W1", "dered_mag_W2",
        "g_minus_r", "z_minus_W1", "W1_minus_W2",
        "Class_STAREX", "Exgal_prob_STAREX", "class_gal_exgal", "class_jetted",
        "main_id_simbad", "separation_LS10_simbad",
    ]),
    "CW2020": ("eRASSc3_Main_CW2020_Public_27Jul2026.fits.gz", [
        "IAUNAME", "CW2020_source_id", "CW2020_Xray_proba", "Separation_CW2020_ERO",
        "NWAY_p_any", "NWAY_p_i", "NWAY_match_flag",
        "CW2020_w1mpro", "CW2020_w1sigmpro", "CW2020_w2mpro", "CW2020_w2sigmpro",
        "CW2020_PMRA", "CW2020_PMDec", "CW2020_sigPMRA", "CW2020_sigPMDec",
    ]),
}


def dedup_ttypes(hdr) -> list[str]:
    """Rename duplicate TTYPEn in the header BEFORE first data access.

    The released eRASSc3_Main_GDR3 file carries 'GDR3_source_id' twice (fields 62
    and 88; the Hard variant has 'GDR3_designation' at the second position, so the
    Main file's second copy is a consortium labeling slip). Duplicates make numpy
    refuse to build the record dtype. Renaming the later occurrence in the
    in-memory header is enough because astropy builds ColDefs lazily.
    Returns the list of renames performed ("old->new").
    """
    seen: set[str] = set()
    renames = []
    for i in range(1, hdr["TFIELDS"] + 1):
        n = hdr[f"TTYPE{i}"]
        if n in seen:
            hdr[f"TTYPE{i}"] = f"{n}_dup{i}"
            renames.append(f"{n}->{n}_dup{i}")
        seen.add(n)
    return renames


def to_df(rec, cols: list[str]) -> pd.DataFrame:
    have = set(rec.columns.names)
    missing = [c for c in cols if c not in have]
    if missing:
        print(f"  (columns absent in this variant, skipped: {missing})")
    out = {}
    for c in cols:
        if c not in have:
            continue
        v = rec[c]
        if v.dtype.kind in ("S", "U"):
            out[c] = np.char.strip(v.astype("U64"))
        elif v.dtype.kind == "b":
            out[c] = v.astype(bool)
        else:
            out[c] = v.byteswap().view(v.dtype.newbyteorder("="))
    return pd.DataFrame(out)


def main() -> None:
    cands = pd.read_csv(OUT / "m1_candidates.csv")
    dr2_names = cands.loc[cands["cand_set"].isin(["pair", "new_bright"]), "name"].tolist()
    print(f"DR2-detected candidates: {len(dr2_names)}")
    base = pd.DataFrame({"IAUNAME": dr2_names})

    for tag, (fname, cols) in VARIANTS.items():
        print(f"reading {fname} ...", flush=True)
        with fits.open(DATA / fname) as h:
            ren = dedup_ttypes(h[1].header)
            if ren:
                print(f"  deduplicated columns: {ren}")
            d = h[1].data
            names = np.char.strip(d["IAUNAME"].astype("U32"))
            mask = np.isin(names, dr2_names)
            print(f"  {mask.sum()} candidate rows of {len(names):,}")
            sub = to_df(d[mask], cols)
        # NWAY writes one row per possible counterpart (match_flag 1 = best,
        # 2 = viable alternative). Keep the best; count the alternatives.
        ncp = sub.groupby("IAUNAME").size().rename("n_rows")
        if "NWAY_match_flag" in sub.columns:
            sub = sub.sort_values(["NWAY_match_flag"]).groupby(
                "IAUNAME", as_index=False).first()
        else:
            sub = sub.groupby("IAUNAME", as_index=False).first()
        sub = sub.merge(ncp, on="IAUNAME", how="left")
        # prefix all but IAUNAME; NWAY_* columns collide between variants
        ren = {c: (c if c.startswith(tag) or c == "IAUNAME" else f"{tag}_{c}")
               for c in sub.columns}
        sub = sub.rename(columns=ren)
        base = base.merge(sub, on="IAUNAME", how="left")
        del d, names, mask, sub
        gc.collect()

    # Hard-catalog membership by position
    print("matching Hard catalog ...", flush=True)
    with fits.open(DATA / "eRASS3_Hard_v1.2.fits") as h:
        d = h[1].data
        hard = pd.DataFrame({
            "h_name": np.char.strip(d["IAUNAME"].astype("U32")),
            "h_ra": d["RA"].byteswap().view(d["RA"].dtype.newbyteorder("=")),
            "h_dec": d["DEC"].byteswap().view(d["DEC"].dtype.newbyteorder("=")),
            "h_detlike": d["DET_LIKE_3"].byteswap().view(
                d["DET_LIKE_3"].dtype.newbyteorder("=")),
        })
    cpos = cands.set_index("name").loc[base["IAUNAME"], ["RA", "DEC"]]
    cc = SkyCoord(cpos["RA"].to_numpy("f8") * u.deg, cpos["DEC"].to_numpy("f8") * u.deg)
    hc = SkyCoord(hard["h_ra"].to_numpy("f8") * u.deg, hard["h_dec"].to_numpy("f8") * u.deg)
    i, sep, _ = cc.match_to_catalog_sky(hc)
    base["hard_name"] = np.where(sep.arcsec <= 15, hard["h_name"].to_numpy()[i], "")
    base["hard_sep_arcsec"] = np.where(sep.arcsec <= 15, sep.arcsec, np.nan)
    base["hard_detlike3"] = np.where(sep.arcsec <= 15, hard["h_detlike"].to_numpy()[i], np.nan)

    base.to_csv(OUT / "m2_counterparts.csv", index=False)
    for tag in VARIANTS:
        col = {"GDR3": "GDR3_NWAY_p_any", "LS10": "LS10_NWAY_p_any",
               "CW2020": "CW2020_NWAY_p_any"}[tag]
        if col in base.columns:
            n = base[col].notna().sum()
            print(f"{tag}: {n}/{len(base)} candidates have a row (footprint + match)")
    print(f"hard-catalog members: {(base['hard_name'] != '').sum()}")
    print(f"wrote out/m2_counterparts.csv ({len(base)} rows)")


if __name__ == "__main__":
    main()
