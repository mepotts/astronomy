#!/usr/bin/env python
"""Load Shahaf et al. 2023 (MNRAS 518, 2991) published per-source triage
results from the CDS machine-readable tables (J/MNRAS/518/2991, local copies
in data/papers/s23_cds/) and reconstruct their *adopted* class-II/III
boundary curve empirically.

Why: S23's conservative limiting-curve lookup table lives only in the
paywalled OUP supplementary material.  But table1.dat publishes, for all
101,380 sources in their clean sample: M1 (binary_masses IsocLum), the AMRF
A +- e_A, and the Monte-Carlo class probabilities PII / PIII.  For a source
with small e_A, PIII jumps 0 -> 1 as A crosses their adopted A_tr(M1), so
the 50% crossing traced in narrow M1 bins reconstructs the curve they used.
Same logic with (PII + PIII) reconstructs A_MS(M1).
"""

import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDS = os.path.join(BASE, "data", "papers", "s23_cds")

# byte positions from the CDS ReadMe (1-indexed inclusive -> python slices)
T1_COLSPECS = [(0, 19), (20, 28), (29, 37), (38, 55), (56, 73), (74, 92),
               (93, 110), (111, 132), (133, 154)]
T1_NAMES = ["source_id", "gmag", "m1", "A", "e_A", "m2min", "e_m2min",
            "pII", "pIII"]


def load_table1():
    df = pd.read_fwf(os.path.join(CDS, "table1.dat"), colspecs=T1_COLSPECS,
                     names=T1_NAMES, dtype={"source_id": np.int64})
    for c in T1_NAMES[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # CDS stores the probabilities as fractions although the ReadMe says [%]
    # (verified against the paper's printed table: 5.6198e-01 <-> 56.198%).
    df["pII"] *= 100.0
    df["pIII"] *= 100.0
    return df


def load_table2():
    """Class-III sample (177 rows). Only source_id and the class label are
    needed; parse them positionally (id = first token, label = 'WD'/'NS'/'BH'
    token near the end)."""
    rows = []
    with open(os.path.join(CDS, "table2.dat"), encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            sid = int(parts[0])
            label = next((p for p in parts if p in ("WD", "NS", "BH")), "")
            rows.append({"source_id": sid, "s23_label": label})
    return pd.DataFrame(rows)


def crossing_curve(df, prob_col, m1_bins, prob_level=50.0, min_n=50):
    """A value at which `prob_col` crosses `prob_level` [%], per M1 bin.
    Robust recipe: within a bin, sort by A and take the midpoint between the
    highest-A source clearly below the level and the lowest-A source clearly
    above it (clear = <5% or >95%); NaN when the bin lacks both sides."""
    centers, avals = [], []
    for lo, hi in zip(m1_bins[:-1], m1_bins[1:]):
        sub = df[(df["m1"] >= lo) & (df["m1"] < hi)]
        if len(sub) < min_n:
            continue
        below = sub.loc[sub[prob_col] < 5.0, "A"]
        above = sub.loc[sub[prob_col] > 95.0, "A"]
        if len(below) < 5 or len(above) < 5:
            continue
        # guard against outliers: use high/low quantiles instead of extremes
        a_lo = below.quantile(0.995)
        a_hi = above.quantile(0.005)
        centers.append(0.5 * (lo + hi))
        avals.append(0.5 * (a_lo + a_hi))
    return np.array(centers), np.array(avals)


def s23_empirical_boundaries(df=None, step=0.05, lo=0.2, hi=2.2):
    """Returns DataFrame(m1, a_tr_s23, a_ms_s23) reconstructed from table1."""
    if df is None:
        df = load_table1()
    good = df[np.isfinite(df["A"]) & np.isfinite(df["m1"])
              & (df["e_A"] < 0.05)].copy()
    good["pII_plus_III"] = good["pII"].fillna(0) + good["pIII"].fillna(0)
    bins = np.arange(lo, hi + step, step)
    m_tr, a_tr = crossing_curve(good, "pIII", bins)
    m_ms, a_ms = crossing_curve(good, "pII_plus_III", bins)
    out = pd.DataFrame({"m1": np.unique(np.concatenate([m_tr, m_ms]))})
    out["a_tr_s23"] = np.interp(out["m1"], m_tr, a_tr, left=np.nan,
                                right=np.nan) if len(m_tr) else np.nan
    out["a_ms_s23"] = np.interp(out["m1"], m_ms, a_ms, left=np.nan,
                                right=np.nan) if len(m_ms) else np.nan
    return out


if __name__ == "__main__":
    t1 = load_table1()
    t2 = load_table2()
    print(f"table1: {len(t1)} rows; table2: {len(t2)} rows; "
          f"labels: {t2['s23_label'].value_counts().to_dict()}")
    emp = s23_empirical_boundaries(t1)
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import amrf
    emp["a_tr_mamajek"] = amrf.a_tr(emp["m1"].values)
    emp["a_ms_mamajek"] = amrf.a_ms(emp["m1"].values)
    emp["ratio_tr"] = emp["a_tr_s23"] / emp["a_tr_mamajek"]
    emp["ratio_ms"] = emp["a_ms_s23"] / emp["a_ms_mamajek"]
    with pd.option_context("display.width", 140, "display.max_rows", 100):
        print(emp.round(4).to_string(index=False))
    print("\nmedian a_tr_s23 / a_tr_mamajek =", round(emp["ratio_tr"].median(), 4))
    print("median a_ms_s23 / a_ms_mamajek =", round(emp["ratio_ms"].median(), 4))
