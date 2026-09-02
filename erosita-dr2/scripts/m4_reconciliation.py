"""M4 Part B: value-of-reconciliation experiment on DR2 (IDEAS classifier M0 check #3).

Question (from ../IDEAS/erosita-source-classifier.md M0): for random DR2 point
sources, how often does a single released catalog already give an unambiguous
class, vs coverage gaps / cross-catalog disagreement? Kill threshold from the
plan: if essentially every source is trivially classified by one catalog, the
unification wedge dies; it lives if >~20% are outside the classified footprint
or ambiguous/conflicting.

Substrate: the six released eRASSc3 NWAY counterpart catalogs (local, M2), of
which the Main x LS10 variant carries the consortium's own per-source
classification columns (`class_gal_exgal`: "negative values for stars,
positive for extragalactic (see Salvato et al 2025)"; `Class_STAREX`;
`Exgal_prob_STAREX`; `class_jetted` - data model
https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/
eRASSc3_Main_LS10_Public_27Jul2026.html), the GDR3 variant carries the Gaia
DSC probabilities (GDR3_PQSO/PGal/Pstar), and CW2020 carries photometry only.

Design [computed]:
  * Sample: N=2000 random point sources (EXT_LIKE == 0) from the local
    eRASS3_Main_v1.3 catalog, rng seed 20260816; the first 100 of the draw are
    the plan's "~100 random sources" primary sample, the 2000 give the
    robustness numbers.
  * Join to each counterpart catalog on DETUID; NWAY_match_flag==1 row is the
    primary counterpart, match_flag==2 rows are counted as alternatives.
  * Tiers at p_any thresholds 0.5 (primary) and 0.8 (sensitivity):
      T1 single-catalog classified: LS10 row exists, NWAY_p_any >= thr,
         class_gal_exgal != 0
      T2 classified-but-contested: T1 but an alternative counterpart exists,
         or the confident GDR3 counterpart is a different object (>1.5"), or
         the GDR3 DSC class contradicts the LS10 gal/exgal sign
      T3 out of footprint: no LS10 row (LS10 file only covers the Legacy
         Survey DR10 footprint) - subdivided by whether GDR3 DSC gives a
         confident class instead
      T4 in footprint but unclassified: LS10 row with p_any < thr, or class 0

Output: out/m4_reconciliation.csv (one row per sampled source, all evidence
columns + tier) and a printed summary block for the M4 doc. Local data only;
no network.
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"

SEED = 20260816
N_SAMPLE = 2000
N_PRIMARY = 100


def dedup_ttypes(hdr) -> list[str]:
    """Rename duplicate TTYPEn in-memory (eRASSc3_Main_GDR3 ships
    GDR3_source_id twice - M2 finding)."""
    seen: set[str] = set()
    renames = []
    for i in range(1, hdr["TFIELDS"] + 1):
        n = hdr[f"TTYPE{i}"]
        if n in seen:
            hdr[f"TTYPE{i}"] = f"{n}_dup{i}"
            renames.append(f"{n}->{n}_dup{i}")
        seen.add(n)
    return renames


def native(v: np.ndarray) -> np.ndarray:
    if v.dtype.kind in ("S", "U"):
        return np.char.strip(v.astype("U64"))
    if v.dtype.kind == "b":
        return v.astype(bool)
    return v.byteswap().view(v.dtype.newbyteorder("="))


def extract(fname: str, want: list[str], keep_detuid: np.ndarray) -> pd.DataFrame:
    with fits.open(DATA / fname) as h:
        ren = dedup_ttypes(h[1].header)
        if ren:
            print(f"  deduplicated: {ren}")
        d = h[1].data
        det = np.char.strip(d["DETUID"].astype("U40"))
        mask = np.isin(det, keep_detuid)
        print(f"  {fname}: {mask.sum()} rows for {len(keep_detuid)} sources "
              f"(of {len(det):,})")
        out = {"DETUID": det[mask]}
        for c in want:
            out[c] = native(d[c][mask])
        df = pd.DataFrame(out)
    del d
    gc.collect()
    return df


def main() -> None:
    # ---- sample from the Main catalog -----------------------------------
    with fits.open(DATA / "eRASS3_Main_v1.3.fits", memmap=True) as h:
        d = h[1].data
        ext = native(d["EXT_LIKE"])
        pt_idx = np.flatnonzero(ext == 0)
        rng = np.random.default_rng(SEED)
        pick = rng.choice(pt_idx, size=N_SAMPLE, replace=False)
        base = pd.DataFrame({
            "DETUID": native(d["DETUID"][pick]),
            "IAUNAME": native(d["IAUNAME"][pick]),
            "RA": native(d["RA"][pick]),
            "DEC": native(d["DEC"][pick]),
            "DET_LIKE_0": native(d["DET_LIKE_0"][pick]),
        })
    base["primary_100"] = False
    base.loc[: N_PRIMARY - 1, "primary_100"] = True
    print(f"sampled {len(base)} point sources "
          f"({(ext == 0).sum():,} available); seed {SEED}")
    del d
    gc.collect()

    keep = base["DETUID"].to_numpy()

    ls10 = extract("eRASSc3_Main_LS10_Public_27Jul2026.fits.gz",
                   ["NWAY_p_any", "NWAY_match_flag", "LS10_RA", "LS10_DEC",
                    "class_gal_exgal", "Class_STAREX", "Exgal_prob_STAREX",
                    "class_jetted", "dered_mag_r", "LS10_TYPE"], keep)
    gdr3 = extract("eRASSc3_Main_GDR3_Public_27Jul2026.fits.gz",
                   ["NWAY_p_any", "NWAY_match_flag", "GDR3_RA", "GDR3_DEC",
                    "GDR3_PQSO", "GDR3_PGal", "GDR3_Pstar",
                    "GDR3_parallax", "GDR3_parallax_over_error",
                    "GDR3_phot_g_mean_mag"], keep)
    cw = extract("eRASSc3_Main_CW2020_Public_27Jul2026.fits.gz",
                 ["NWAY_p_any", "NWAY_match_flag", "CW2020_RA", "CW2020_DEC",
                  "CW2020_w1mpro", "CW2020_w2mpro"], keep)

    def fold(df: pd.DataFrame, tag: str) -> pd.DataFrame:
        n_alt = (df[df["NWAY_match_flag"] == 2].groupby("DETUID").size()
                 .rename(f"{tag}_n_alt"))
        best = (df[df["NWAY_match_flag"] == 1]
                .sort_values("NWAY_p_any", ascending=False)
                .groupby("DETUID", as_index=False).first())
        best = best.rename(columns={
            c: f"{tag}_{c}" for c in best.columns if c != "DETUID"})
        best = best.merge(n_alt, on="DETUID", how="left")
        best[f"{tag}_n_alt"] = best[f"{tag}_n_alt"].fillna(0).astype(int)
        return best

    res = base.merge(fold(ls10, "ls10"), on="DETUID", how="left")
    res = res.merge(fold(gdr3, "gdr3"), on="DETUID", how="left")
    res = res.merge(fold(cw, "cw"), on="DETUID", how="left")

    # ---- derived evidence ----------------------------------------------
    res["in_ls10"] = res["ls10_NWAY_p_any"].notna()
    res["in_gdr3"] = res["gdr3_NWAY_p_any"].notna()
    res["in_cw"] = res["cw_NWAY_p_any"].notna()

    dsc = res[["gdr3_GDR3_PQSO", "gdr3_GDR3_PGal", "gdr3_GDR3_Pstar"]].to_numpy()
    with np.errstate(invalid="ignore"):
        res["gdr3_dsc_max"] = np.nanmax(dsc, axis=1)
    res["gdr3_dsc_label"] = np.select(
        [np.nanargmax(np.nan_to_num(dsc, nan=-1), axis=1) == i
         for i in range(3)],
        ["QSO", "GALAXY", "STAR"], default="")
    res.loc[~np.isfinite(res["gdr3_dsc_max"]), "gdr3_dsc_label"] = ""

    # identity agreement (confident counterparts on both sides)
    def sep_arcsec(ra1, de1, ra2, de2):
        dra = (ra1 - ra2) * np.cos(np.radians(de1))
        return np.hypot(dra, de1 - de2) * 3600.0

    res["ls10_gdr3_sep"] = sep_arcsec(
        res["ls10_LS10_RA"], res["ls10_LS10_DEC"],
        res["gdr3_GDR3_RA"], res["gdr3_GDR3_DEC"])

    for thr in (0.5, 0.8):
        both = ((res["ls10_NWAY_p_any"] >= thr)
                & (res["gdr3_NWAY_p_any"] >= thr))
        res[f"diff_object_{thr}"] = both & (res["ls10_gdr3_sep"] > 1.5)
        # class conflict: LS10 sign vs GDR3 DSC (both confident)
        cls = res["ls10_class_gal_exgal"].fillna(0).astype(float)
        dscok = both & (res["gdr3_dsc_max"] >= 0.5)
        conflict = dscok & (
            ((cls < 0) & res["gdr3_dsc_label"].isin(["QSO", "GALAXY"]))
            | ((cls > 0) & (res["gdr3_dsc_label"] == "STAR")))
        res[f"class_conflict_{thr}"] = conflict

        t1 = (res["in_ls10"] & (res["ls10_NWAY_p_any"] >= thr) & (cls != 0))
        contested = t1 & ((res["ls10_n_alt"] > 0) | res[f"diff_object_{thr}"]
                          | conflict)
        t3 = ~res["in_ls10"]
        t3_dsc = t3 & (res["gdr3_NWAY_p_any"] >= thr) & (res["gdr3_dsc_max"] >= 0.5)
        tier = np.select(
            [t1 & ~contested, contested, t3 & t3_dsc, t3 & ~t3_dsc],
            ["T1_single_catalog_classified", "T2_classified_contested",
             "T3_no_ls10_gdr3_dsc_only", "T3_no_ls10_nothing"],
            default="T4_in_ls10_unclassified")
        res[f"tier_{thr}"] = tier

    res.to_csv(OUT / "m4_reconciliation.csv", index=False)

    # ---- summary --------------------------------------------------------
    for label, sub in [("PRIMARY n=100", res[res["primary_100"]]),
                       ("ROBUSTNESS n=2000", res)]:
        print(f"\n=== {label} ===")
        n = len(sub)
        print(f"in LS10 file: {sub['in_ls10'].sum()} ({sub['in_ls10'].mean():.1%})"
              f" | in GDR3: {sub['in_gdr3'].sum()} | in CW2020: {sub['in_cw'].sum()}")
        for thr in (0.5, 0.8):
            vc = sub[f"tier_{thr}"].value_counts()
            print(f"  p_any >= {thr}:")
            for k in ["T1_single_catalog_classified", "T2_classified_contested",
                      "T3_no_ls10_gdr3_dsc_only", "T3_no_ls10_nothing",
                      "T4_in_ls10_unclassified"]:
                c = int(vc.get(k, 0))
                print(f"    {k:32s} {c:5d}  ({c / n:.1%})")
            not_t1 = n - int(vc.get("T1_single_catalog_classified", 0))
            print(f"    NOT trivially classified: {not_t1} ({not_t1 / n:.1%})")
        print(f"  any alternative counterpart (any variant): "
              f"{((sub['ls10_n_alt'] > 0) | (sub['gdr3_n_alt'] > 0) | (sub['cw_n_alt'] > 0)).sum()}")
        print(f"  diff-object LS10 vs GDR3 (both p_any>=0.5): "
              f"{sub['diff_object_0.5'].sum()}")
        print(f"  class conflict LS10 vs GDR3 DSC (0.5): "
              f"{sub['class_conflict_0.5'].sum()}")
    print("\nwrote out/m4_reconciliation.csv")


if __name__ == "__main__":
    main()
