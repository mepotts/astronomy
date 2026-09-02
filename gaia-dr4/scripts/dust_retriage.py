#!/usr/bin/env python
"""M3 task 2: extinction tier for M1 -- re-triage the photometric-M1
population with a per-star dust column, honestly chosen by geometry.

Which stars extinction can move: ONLY those whose M1 comes from photometry
(tier 'photometric_ms') or whose tier assignment used the CMD cut (tier
'evolved_bracket'); tier 'binary_masses' M1 is DPAC's isochrone-luminosity
value and does not depend on our photometry (its own extinction treatment
is DPAC's, documented limitation).  Reddening biases the uncorrected
pipeline in the false-positive direction (M1 low -> AMRF high), and it can
also push a reddened giant BELOW the El-Badry 2026 CMD line so it passes
as MS with a spuriously low point mass -- both directions are re-examined.

Per-star map choice (mixed tiers, justified by parallax geometry):
  d <= 1250 pc  Edenhofer et al. 2023 3D map (all-sky, 69-1250 pc;
                the only all-sky 3D map covering the sample -- no
                declination split needed inside its volume).
  d < 69 pc     linear ramp of Edenhofer's innermost integrated column
                (extinction ~0 there; approximation flagged).
  d > 1250 pc   the truth is bracketed, not guessed:
                  lower bound = Edenhofer integrated to the map edge
                                (misses dust beyond 1.25 kpc);
                  upper bound = SFD 1998 full 2D column (counts ALL dust
                                on the sightline, including background --
                                the overestimate direction for foreground
                                stars; |b|<5 deg additionally unreliable,
                                flagged).
                A candidate is dust-robust class III only if it survives
                the UPPER bound; survivors of the lower bound only are
                'dust-ambiguous' (a far-3D map -- Bayestar19, north-only --
                could arbitrate; deliberately NOT used here because its
                unit chain to Gaia bands adds an unsourced link, and the
                ambiguous set is reported instead).

Unit chain (every constant sourced):
  Edenhofer map unit E (ZGR23): A_lam = R(lam)*E with R from the published
    ZGR23 extinction curve (local copy data/papers/zgr23_curve/), evaluated
    at the Gaia EDR3 pivot wavelengths (Riello et al. 2021):
    R_G(621.79nm)=2.273, R_BP(510.97nm)=3.036, R_RP(776.91nm)=1.648,
    R_V(540nm)=2.779 (the paper's rounded "2.8", Edenhofer+24 line 591).
  SFD: raw E(B-V)_SFD98 (sfdmap2 with scaling=1.0) -> A_V = 2.742*E(B-V)
    [Schlafly & Finkbeiner 2011, ApJ 737, 103, Table 6, F99 R_V=3.1] ->
    Gaia bands via the ZGR23-curve ratios A_G/A_V etc. (keeps one
    extinction law across tiers).

Scope: all rows passing the frozen screen (cuts_eb26) with a
photometry-dependent M1 tier (22,256), plus the full 951-row class-III
list (binary_masses rows carried with unchanged class, extinction as
information columns).  Movements are reported per bound.

Outputs: out/dust_retriage.csv, out/dust_movements_summary.csv, stdout.
Run    : .venv/Scripts/python.exe scripts/dust_retriage.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amrf
from amrf_triage import evolved_bracket_class, CONFIG
from dust3d import Edenhofer3D, zgr23_band_coefficients

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIAGE_PARQUET = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")
SFD_DIR = os.path.join(BASE, "data", "dustmaps", "sfddata-master")
OUT_DIR = os.path.join(BASE, "out")
EB26_CSV = os.path.join(BASE, "fixtures",
                        "elbadry2026_astrometric_candidates.csv")

INFLATE = CONFIG["boundary_inflate"]
SF11_AV_PER_EBV = 2.742  # Schlafly & Finkbeiner 2011 Table 6, F99 R_V=3.1


def compute_dusted_class(df, a_g, e_bprp):
    """Re-run the M2 M1 policy with extinction-corrected photometry.
    Returns (m1, m1_source, class_det, margin, amrf_val)."""
    mg0 = df["abs_g_noext"].values - a_g
    bprp0 = df["bp_rp"].values - e_bprp
    ms = amrf.is_main_sequence(mg0, bprp0)
    m1_phot = amrf.mass_of_mg(mg0)
    phot_ok = ms & np.isfinite(m1_phot)

    m1 = np.full(len(df), np.nan)
    src = np.array(["evolved_bracket"] * len(df), dtype=object)
    m1[phot_ok] = m1_phot[phot_ok]
    src[phot_ok] = "photometric_ms"
    bm = df["m1_source"].values == "binary_masses"
    m1[bm] = df["m1_used"].values[bm]
    src[bm] = "binary_masses"

    cls = np.zeros(len(df), dtype=int)
    margin = np.full(len(df), np.nan)
    aval = np.full(len(df), np.nan)
    point = src != "evolved_bracket"
    if point.any():
        aval[point] = amrf.amrf(df["a0_mas"].values[point],
                                df["nss_parallax"].values[point],
                                m1[point], df["period"].values[point])
        cls[point] = amrf.classify(aval[point], m1[point], inflate=INFLATE)
        margin[point] = aval[point] / amrf.a_tr(m1[point], inflate=INFLATE)
    evb = ~point
    if evb.any():
        c_ev, m_ev, m1w = evolved_bracket_class(
            df["a0_mas"].values[evb], df["nss_parallax"].values[evb],
            df["period"].values[evb], INFLATE)
        cls[evb] = c_ev
        margin[evb] = m_ev
        aval[evb] = amrf.amrf(df["a0_mas"].values[evb],
                              df["nss_parallax"].values[evb],
                              m1w, df["period"].values[evb])
    return m1, src, cls, margin, aval


def main():
    co = zgr23_band_coefficients()
    r_g, r_bp, r_rp, r_v = co["R_G"], co["R_BP"], co["R_RP"], co["R_V"]
    print(f"ZGR23 curve: R_G={r_g:.4f} R_BP={r_bp:.4f} R_RP={r_rp:.4f} "
          f"R_V={r_v:.4f}")

    tri = pd.read_parquet(TRIAGE_PARQUET)
    scope = tri[(tri["cuts_eb26"] & (tri["m1_source"] != "binary_masses"))
                | ((tri["class_det"] == 3) & tri["cuts_eb26"])].copy()
    scope = scope.reset_index(drop=True)
    print(f"scope: {len(scope)} solution rows "
          f"({(scope['m1_source'] != 'binary_masses').sum()} with "
          f"photometry-dependent M1)")

    d_pc = 1000.0 / scope["nss_parallax"].values

    print("loading Edenhofer 3D map...", flush=True)
    eden = Edenhofer3D()
    E_eden, tier = eden.query_integrated(scope["l"].values, scope["b"].values,
                                         d_pc)

    import sfdmap2.sfdmap as sfdmap
    sfd = sfdmap.SFDMap(SFD_DIR, scaling=1.0)
    ebv_sfd = sfd.ebv(scope["ra"].values, scope["dec"].values)

    far = tier == "edenhofer_floor"
    print(f"dust tiers: {pd.Series(tier).value_counts().to_dict()}")

    # lower bound: Edenhofer everywhere (to map edge for far stars)
    ag_lo = r_g * E_eden
    ebprp_lo = (r_bp - r_rp) * E_eden
    # upper bound: same inside coverage; SFD full column for far stars,
    # never below the Edenhofer floor (map disagreement guard, counted)
    E_sfd_equiv = SF11_AV_PER_EBV * ebv_sfd / r_v  # E(ZGR23)-equivalent
    ag_up = ag_lo.copy()
    ebprp_up = ebprp_lo.copy()
    incons = far & (E_sfd_equiv < E_eden)
    ag_up[far] = r_g * np.maximum(E_sfd_equiv[far], E_eden[far])
    ebprp_up[far] = (r_bp - r_rp) * np.maximum(E_sfd_equiv[far], E_eden[far])
    print(f"far stars where SFD column < Edenhofer floor (map tension, "
          f"upper bound clamped to floor): {int(incons.sum())} of "
          f"{int(far.sum())}")

    m1_lo, src_lo, cls_lo, marg_lo, a_lo = compute_dusted_class(
        scope, ag_lo, ebprp_lo)
    m1_up, src_up, cls_up, marg_up, a_up = compute_dusted_class(
        scope, ag_up, ebprp_up)

    out = scope[["source_id", "nss_solution_type", "l", "b",
                 "nss_parallax", "phot_g_mean_mag", "bp_rp", "m1_used",
                 "m1_source", "class_det", "a_tr_margin", "m2_min_dark",
                 "flag_low_lat", "cuts_eb26"]].copy()
    out["d_pc"] = d_pc
    out["dust_tier"] = tier
    out["E_zgr23_eden"] = E_eden
    out["ebv_sfd_raw"] = ebv_sfd
    out["a_g_lower"] = ag_lo
    out["a_g_upper"] = ag_up
    out["a_v_mag"] = r_v * E_eden            # best-estimate (lower for far)
    out["m1_dust"] = m1_lo                    # lower-bound = best inside cov.
    out["m1_source_dust"] = src_lo
    out["class_det_dust"] = cls_lo
    out["margin_dust"] = marg_lo
    out["m1_dust_upper"] = m1_up
    out["m1_source_dust_upper"] = src_up
    out["class_det_dust_upper"] = cls_up
    out["margin_dust_upper"] = marg_up
    out["sfd_lowb_unreliable"] = far & (np.abs(scope["b"].values) < 5.0)
    out.to_csv(os.path.join(OUT_DIR, "dust_retriage.csv"), index=False,
               lineterminator="\n")

    # ---- movements -------------------------------------------------------
    was3 = out["class_det"] == 3
    nonbm = out["m1_source"] != "binary_masses"
    rows = []
    for bound, cls_col in (("lower(best<=1.25kpc)", "class_det_dust"),
                           ("upper(SFD far)", "class_det_dust_upper")):
        now3 = out[cls_col] == 3
        out_mask = was3 & nonbm & ~now3
        in_mask = ~was3 & nonbm & now3 & out["cuts_eb26"]
        rows.append({
            "bound": bound,
            "class3_nonbm_before": int((was3 & nonbm).sum()),
            "moved_out": int(out_mask.sum()),
            "moved_out_lowlat": int((out_mask & out["flag_low_lat"]).sum()),
            "moved_in": int(in_mask.sum()),
            "moved_in_lowlat": int((in_mask & out["flag_low_lat"]).sum()),
            "class3_after_(nonbm)": int((now3 & nonbm).sum()),
        })
    mv = pd.DataFrame(rows)
    mv.to_csv(os.path.join(OUT_DIR, "dust_movements_summary.csv"),
              index=False, lineterminator="\n")
    print("\nmovements (photometry-dependent-M1 rows only; binary_masses "
          "rows cannot move):")
    print(mv.to_string(index=False))

    # ambiguity: survives lower bound, dies under upper bound
    amb = was3 & nonbm & (out["class_det_dust"] == 3) \
        & (out["class_det_dust_upper"] != 3)
    print(f"\ndust-AMBIGUOUS class-III (far star, survives Edenhofer floor, "
          f"killed by SFD full column): {int(amb.sum())}"
          f"  [these are where a far 3D map (Bayestar19, dec>-30) would "
          f"arbitrate]")

    # flagged-set accounting (the 270 low-|b| reservoir)
    flagged = out[was3 & out["flag_low_lat"]]
    print(f"\nthe 270-flag reservoir: {len(flagged)} class-III rows at "
          f"|b|<10 in scope; tier mix "
          f"{flagged['m1_source'].value_counts().to_dict()}")
    fl_nonbm = flagged[flagged["m1_source"] != "binary_masses"]
    print(f"  photometry-dependent among them: {len(fl_nonbm)}; "
          f"killed lower/upper: "
          f"{int((fl_nonbm['class_det_dust'] != 3).sum())}/"
          f"{int((fl_nonbm['class_det_dust_upper'] != 3).sum())}")

    # tier switches
    sw = out[nonbm & (out["m1_source"] != out["m1_source_dust"])]
    print(f"\ntier switches under lower bound: {len(sw)} "
          f"({sw.groupby(['m1_source', 'm1_source_dust']).size().to_dict()})")

    # ---- EB26 ebv cross-check -------------------------------------------
    eb = pd.read_csv(EB26_CSV)
    ej = eb.merge(out[["source_id", "E_zgr23_eden", "ebv_sfd_raw", "d_pc",
                       "dust_tier"]], on="source_id", how="inner")
    ej = ej[pd.to_numeric(ej["ebv"], errors="coerce").notna()].copy()
    ej["ebv"] = ej["ebv"].astype(float)
    if len(ej):
        my_ebv = SF11_AV_PER_EBV * 0 + ej["E_zgr23_eden"] * r_v / SF11_AV_PER_EBV
        ratio = (my_ebv / ej["ebv"]).replace([np.inf, -np.inf], np.nan)
        print(f"\nEB26 ebv cross-check (n={len(ej)} overlap): "
              f"median my-E(B-V)-equiv / their-ebv = "
              f"{np.nanmedian(ratio):.3f} "
              f"(10-90%: {np.nanpercentile(ratio.dropna(), 10):.3f}-"
              f"{np.nanpercentile(ratio.dropna(), 90):.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
