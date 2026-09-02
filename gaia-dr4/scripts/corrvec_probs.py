#!/usr/bin/env python
"""M3 task 1: covariance-aware (corr_vec) class-III probabilities.

Replaces M2's independent-Gaussian Monte Carlo (measured to overestimate
sigma(A) by a median 2.27x vs Shahaf+23's covariance-aware e_A, M2 Sec. 4)
with the full DR3 NSS covariance, reconstructed by the DPAC reference
implementation `nsstools` (PyPI; version printed at runtime):

  NssSource(row).covmat() -> labeled covariance over the fitted parameters
  (correlations from corr_vec scaled by the published errors; parameter
  order per solution type is nsstools' own -- the DR3 AstroSpectroSB1
  corr_vec ordering subtlety is exactly what the package exists to encode).

Per solution row:
  - extract the 6x6 covariance block over (parallax, A, B, F, G, period)
    and the matching mean vector;
  - draw `ndraw` multivariate-normal samples (Cholesky; eigenvalue-clip
    fallback for numerically non-PD matrices, counted);
  - a0 via Halbwachs eq. 12-14 per draw; M1 per M2's three-tier policy
    (tier-2 now RECOMPUTED per draw from the drawn parallax -- the
    M1-parallax coupling M2 ignored; 10% relative scatter retained);
  - A = amrf(a0, plx, M1, P) per draw; Pr(class III) = fraction of finite
    draws with A > A_tr(M1)*inflate; Pr(class >= II) likewise vs A_MS.
  - sigma_A_corr = std of draws; sigma_A_indep = same machinery with
    off-diagonal covariance zeroed (isolates the correlation effect);
  - cross-checks: covmat diagonal == published errors^2; nsstools
    campbell() a0_error vs the archive `significance` (= a0/sigma_a0).

Validation: rows flagged is_validation_sample (seeded S23-table1 sample)
are compared against S23's published e_A -> out/corrvec_validation.csv.

Outputs:
  data/dr3_corrvec_probs.parquet   per-solution-row probabilities + checks
  out/corrvec_validation.csv       sigma(A) vs S23 e_A (corr + indep)
  out/corrvec_eb26_operating_point.csv  EB26 completeness/purity vs Pr cut
  stdout                           BH1/BH2 + harden/dissolve summary

Run   : .venv/Scripts/python.exe scripts/corrvec_probs.py
"""

import os
import sys
import time
from importlib.metadata import version as pkg_version

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amrf
from nsstools import NssSource

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORRVEC_PARQUET = os.path.join(BASE, "data", "dr3_nss_corrvec.parquet")
TRIAGE_PARQUET = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")
OUT_PARQUET = os.path.join(BASE, "data", "dr3_corrvec_probs.parquet")
OUT_DIR = os.path.join(BASE, "out")
EB26_CSV = os.path.join(BASE, "fixtures", "elbadry2026_astrometric_candidates.csv")

BH1 = 4373465352415301632
BH2 = 5870569352746779008

SEED = 20261202
NDRAW_MAIN = 10000      # candidate / retrieval / EB26 rows
NDRAW_VAL = 2000        # validation-sample rows
INFLATE = 1.15          # frozen M2 boundary
PHOT_SIGMA_FRAC = 0.10  # M2's tier-2 engineering scatter, retained
EVOLVED_LO, EVOLVED_HI = 0.8, 2.6

SUB = ["parallax", "a_thiele_innes", "b_thiele_innes", "f_thiele_innes",
       "g_thiele_innes", "period"]


def mvn_draws(mean, cov, ndraw, rng):
    """Multivariate normal draws; Cholesky, eigenvalue-clip fallback.
    Returns (draws[ndraw, k], used_fallback)."""
    try:
        L = np.linalg.cholesky(cov)
        fallback = False
    except np.linalg.LinAlgError:
        w, V = np.linalg.eigh(cov)
        w = np.clip(w, 0.0, None)
        L = V * np.sqrt(w)
        fallback = True
    z = rng.standard_normal((ndraw, len(mean)))
    return mean + z @ L.T, fallback


def process_row(row, tri_row, ndraw, rng):
    """Returns dict of per-row outputs."""
    out = {"source_id": int(row["source_id"]),
           "nss_solution_type": row["nss_solution_type"],
           "ndraw": ndraw}
    src = NssSource(pd.DataFrame([row]))
    cm = src.covmat()

    # self-check 1: covmat diagonal == published errors^2
    diag_ok = True
    for p in SUB:
        if p in cm.index:
            sig_pub = row[p + "_error"]
            if np.isfinite(sig_pub) and sig_pub > 0:
                if abs(np.sqrt(cm.loc[p, p]) / sig_pub - 1.0) > 1e-6:
                    diag_ok = False
    out["diag_ok"] = diag_ok

    missing = [p for p in SUB if p not in cm.index]
    if missing:
        out["cov_status"] = "missing:" + ",".join(missing)
        return out
    cov = cm.loc[SUB, SUB].to_numpy(dtype=float)
    mean = np.array([row[p] for p in SUB], dtype=float)

    draws, fb = mvn_draws(mean, cov, ndraw, rng)
    out["cov_status"] = "eig_clip" if fb else "cholesky"
    plx, A_, B_, F_, G_, per = draws.T
    a0 = amrf.thiele_innes_a0(A_, B_, F_, G_)
    out["a0_mc_mean"] = float(a0.mean())
    out["a0_mc_sigma"] = float(a0.std())

    # nsstools linearized a0 +- error (Campbell) for the external cross-check
    try:
        camp = src.campbell().iloc[0]
        out["a0_campbell"] = float(camp["a0"])
        out["a0_err_campbell"] = float(camp["a0_error"])
    except Exception:
        out["a0_campbell"] = np.nan
        out["a0_err_campbell"] = np.nan

    # M1 draws per M2 tier
    tier = tri_row["m1_source"]
    out["m1_source"] = tier
    if tier == "binary_masses":
        m1 = rng.normal(tri_row["m1_used"], tri_row["m1_sigma"], ndraw)
    elif tier == "photometric_ms":
        mg = tri_row["phot_g_mean_mag"] + 5.0 * np.log10(
            np.clip(plx, 1e-6, None) / 100.0)
        m1 = amrf.mass_of_mg(mg) * (1.0 + PHOT_SIGMA_FRAC
                                    * rng.standard_normal(ndraw))
    else:  # evolved_bracket
        m1 = rng.uniform(EVOLVED_LO, EVOLVED_HI, ndraw)

    bad = (plx <= 0) | (per <= 0) | ~np.isfinite(m1) | (m1 <= 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        Aval = amrf.amrf(a0, plx, m1, per)
        atr = amrf.a_tr(m1, inflate=INFLATE)
        ams = amrf.a_ms(m1)
    Aval[bad] = np.nan
    ok = np.isfinite(Aval)
    nok = int(ok.sum())
    out["n_bad_draws"] = ndraw - nok
    if nok == 0:
        return out
    out["sigma_A_corr"] = float(np.nanstd(Aval))
    out["A_mc_mean"] = float(np.nanmean(Aval))
    out["p_class3_corr"] = float(np.nansum(Aval > atr) / nok)
    out["p_class23_corr"] = float(np.nansum(Aval > ams) / nok)

    # independent-error twin (same marginals, zero correlations)
    draws_i, _ = mvn_draws(mean, np.diag(np.diag(cov)), ndraw, rng)
    plx_i, A_i, B_i, F_i, G_i, per_i = draws_i.T
    a0_i = amrf.thiele_innes_a0(A_i, B_i, F_i, G_i)
    with np.errstate(invalid="ignore", divide="ignore"):
        Aval_i = amrf.amrf(a0_i, plx_i, m1, per_i)
    Aval_i[bad | (plx_i <= 0) | (per_i <= 0)] = np.nan
    if np.isfinite(Aval_i).sum():
        out["sigma_A_indep"] = float(np.nanstd(Aval_i))
        atr_i = atr  # same m1 draws
        out["p_class3_indep"] = float(
            np.nansum(Aval_i > atr_i) / np.isfinite(Aval_i).sum())
    return out


def main():
    print(f"nsstools version: {pkg_version('nsstools')}")
    cv = pd.read_parquet(CORRVEC_PARQUET)
    tri = pd.read_parquet(TRIAGE_PARQUET)
    print(f"corrvec rows: {len(cv)}; triage rows: {len(tri)}")

    tri_key = tri.set_index(["source_id", "nss_solution_type"])
    # consistency guard: archive values in the fresh pull must equal the M2
    # parquet's (same archive, same rows) -- protects against join errors
    j = cv[["source_id", "nss_solution_type", "parallax", "period"]].merge(
        tri[["source_id", "nss_solution_type", "nss_parallax", "period"]],
        on=["source_id", "nss_solution_type"], how="left",
        suffixes=("_new", "_m2"))
    dplx = np.nanmax(np.abs(j["parallax"] - j["nss_parallax"]))
    dper = np.nanmax(np.abs(j["period_new"] - j["period_m2"]))
    print(f"consistency: max |plx_new - plx_m2| = {dplx:.3e}, "
          f"max |P_new - P_m2| = {dper:.3e}")
    if dplx > 1e-9 or dper > 1e-6:
        raise RuntimeError("corrvec pull disagrees with M2 parquet -- ABORT")

    rows = []
    t0 = time.time()
    n_err = 0
    for i, row in enumerate(cv.to_dict("records")):
        key = (row["source_id"], row["nss_solution_type"])
        if key not in tri_key.index:
            continue
        tri_row = tri_key.loc[key]
        if isinstance(tri_row, pd.DataFrame):
            tri_row = tri_row.iloc[0]
        ndraw = NDRAW_VAL if row["is_validation_sample"] else NDRAW_MAIN
        rng = np.random.default_rng(
            [SEED, row["source_id"] & 0xFFFFFFFF,
             row["source_id"] >> 32, len(row["nss_solution_type"])])
        try:
            rows.append(process_row(row, tri_row, ndraw, rng))
        except Exception as e:
            n_err += 1
            rows.append({"source_id": int(row["source_id"]),
                         "nss_solution_type": row["nss_solution_type"],
                         "cov_status": f"ERROR:{type(e).__name__}"})
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(cv)} rows ({time.time()-t0:.0f}s)",
                  flush=True)
    res = pd.DataFrame(rows)
    res["is_validation_sample"] = res["source_id"].isin(
        set(cv.loc[cv["is_validation_sample"], "source_id"]))
    res.to_parquet(OUT_PARQUET, index=False)
    print(f"wrote {OUT_PARQUET} ({len(res)} rows, {n_err} errors, "
          f"{time.time()-t0:.0f}s)")
    print(f"cov_status: {res['cov_status'].value_counts().to_dict()}")
    print(f"diag_ok: {res['diag_ok'].value_counts(dropna=False).to_dict()}")

    # ---- external cross-check: campbell a0_error vs archive significance
    sig = cv.set_index(["source_id", "nss_solution_type"])
    res_k = res.set_index(["source_id", "nss_solution_type"])
    tri_sig = tri_key["significance"]
    both = res_k.join(tri_sig, how="left")
    with np.errstate(invalid="ignore", divide="ignore"):
        r_sig = (both["a0_campbell"] / both["a0_err_campbell"]) \
            / both["significance"]
    print(f"campbell a0/sig(a0) vs archive significance: median ratio "
          f"{np.nanmedian(r_sig):.4f} (10-90%: "
          f"{np.nanpercentile(r_sig, 10):.4f}-"
          f"{np.nanpercentile(r_sig, 90):.4f}, n={np.isfinite(r_sig).sum()})")

    # ---- validation vs S23 e_A ------------------------------------------
    import s23_reference
    t1 = s23_reference.load_table1().set_index("source_id")
    val = res[res["is_validation_sample"]].copy()
    val = val.join(t1[["A", "e_A"]], on="source_id", how="inner")
    with np.errstate(invalid="ignore"):
        val["ratio_corr"] = val["sigma_A_corr"] / val["e_A"]
        val["ratio_indep"] = val["sigma_A_indep"] / val["e_A"]
    val_out = val[["source_id", "nss_solution_type", "A", "e_A",
                   "sigma_A_corr", "sigma_A_indep", "ratio_corr",
                   "ratio_indep", "cov_status"]]
    val_out.to_csv(os.path.join(OUT_DIR, "corrvec_validation.csv"),
                   index=False, lineterminator="\n")
    for c in ("ratio_corr", "ratio_indep"):
        v = val[c].dropna()
        print(f"validation {c}: median {v.median():.3f} "
              f"(10-90%: {v.quantile(0.10):.3f}-{v.quantile(0.90):.3f}, "
              f"n={len(v)})")

    # ---- candidate summary ----------------------------------------------
    cand = pd.read_csv(os.path.join(OUT_DIR, "amrf_class3_candidates.csv"))
    ck = cand.merge(res, on=["source_id", "nss_solution_type"], how="left")
    print(f"\nclass-III 951: matched {ck['p_class3_corr'].notna().sum()} "
          f"with corr probabilities")
    for thr, name in ((0.999, "harden Pr>=99.9%"), (0.99, "Pr>=99%"),
                      (0.9, "Pr>=90%")):
        print(f"  {name}: {(ck['p_class3_corr'] >= thr).sum()} "
              f"(M2 indep-MC >= {thr}: "
              f"{(ck['p_class3_mc'] >= thr).sum()})")
    print(f"  dissolve Pr<50%: {(ck['p_class3_corr'] < 0.5).sum()} "
          f"(M2 indep: {(ck['p_class3_mc'] < 0.5).sum()})")
    dd = (ck["p_class3_corr"] - ck["p_class3_mc"]).dropna()
    print(f"  delta (corr - indep): median {dd.median():+.4f}, "
          f"10-90% {dd.quantile(0.1):+.4f}..{dd.quantile(0.9):+.4f}")

    for nm, sid in (("Gaia BH1", BH1), ("Gaia BH2", BH2)):
        r = res[res["source_id"] == sid]
        if len(r):
            r = r.iloc[0]
            print(f"  {nm}: p_class3_corr = {r['p_class3_corr']:.4f}, "
                  f"sigma_A_corr = {r['sigma_A_corr']:.4f} "
                  f"(indep {r['sigma_A_indep']:.4f}), {r['cov_status']}")

    # ---- EB26 operating point vs Pr threshold ---------------------------
    eb = pd.read_csv(EB26_CSV)
    tri_eb = tri.merge(eb[["source_id", "verdict"]], on="source_id",
                       how="inner")
    tri_eb = tri_eb.merge(res[["source_id", "nss_solution_type",
                               "p_class3_corr"]],
                          on=["source_id", "nss_solution_type"], how="left")
    passing = tri_eb[(tri_eb["class_det"] == 3) & tri_eb["cuts_eb26"]]
    rows_op = []
    for thr in (None, 0.5, 0.9, 0.99, 0.999):
        if thr is None:
            sel = passing
            label = "frozen screen (M2)"
        else:
            sel = passing[passing["p_class3_corr"] >= thr]
            label = f"+ Pr(III|corr) >= {thr}"
        srcs = set(sel["source_id"])
        n_conf = eb[(eb["verdict"] == "CONFIRMED")
                    & eb["source_id"].isin(srcs)]["source_id"].nunique()
        n_spur = eb[(eb["verdict"] == "SPURIOUS")
                    & eb["source_id"].isin(srcs)]["source_id"].nunique()
        rows_op.append({"screen": label, "confirmed_kept_of_42": n_conf,
                        "spurious_passed_of_23": n_spur})
    op = pd.DataFrame(rows_op)
    op.to_csv(os.path.join(OUT_DIR, "corrvec_eb26_operating_point.csv"),
              index=False, lineterminator="\n")
    print("\nEB26 operating point:")
    print(op.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
