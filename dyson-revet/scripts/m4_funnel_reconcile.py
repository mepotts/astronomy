"""M4 -- reconcile this screen's funnel with Hephaistos II's Table 4.

Two things M3 left open, both attacked here from the paper's own text rather
than by tuning anything:

  (1) THE 1.43x PARENT DISCREPANCY.  M3 compared our W3+W4-detected count
      (220,632, BEFORE the contamination-flag cut) against Table 4's
      "W3/W4 detection ~3.2e5".  Suazo et al. 2024 Sec 2.1 says in words what
      that row is:  "...demanding detections in the 12 and 22 um bands ...
      We ADDITIONALLY EXCLUDED SOURCES THAT EXHIBITED CONTAMINATION ACCORDING
      TO THE WISE CONTAMINATION FLAG.  As a result of this filtering step, our
      sample was downsized to approximately 320,000 stars."
      So Table 4's 3.2e5 row is POST-cc_flags and the like-for-like row of our
      funnel is T3_ccflags, not T2_w34det.

  (2) THE GVAR REFERENCE GAP.  M3 measured our extra cuts rejecting 11% where
      "the paper's" reject 54%, and blamed Gvar's unpublished reference sample.
      But Table 4's own ordering puts the CNN ("Nebular classifier", 11243 ->
      5732) BETWEEN the RMSE gate and the extra cuts (5732 -> 5137).  The
      paper's extra cuts alone therefore reject 10.4%, not 54%.  The 54% was
      the CNN.  This script measures our per-criterion rejection against the
      paper's own Sec 2.5.6 accounting, and then bounds what a different Gvar
      reference sample could possibly do by recomputing Gvar under several
      pre-registered reference definitions.

Nothing here is fitted, tuned or chosen after seeing an answer: the stage
alignment comes from the paper's own sentences, and the Gvar reference
variants were listed in M4 PR-2 before any of them was run.

Usage:  python scripts/m4_funnel_reconcile.py [--tag m4] [--ext-ref FILE.csv]
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
W4 = ROOT / "data" / "w4"
SKY_DEG2 = 41252.96

# ---- Hephaistos II Table 4, all-sky, verbatim -----------------------------
PAPER = {
    "parent": 5.0e6,   # "Stars in Gaia DR3-2MASS-AllWISE within 300 pc"
    "w34det": 3.2e5,   # "W3/W4 detection" -- Sec 2.1 says this INCLUDES cc_flags
    "rmse": 11243,     # "RMSE <= 0.2"
    "cnn": 5732,       # "Nebular classifier"  <-- sits HERE, before the extras
    "extra": 5137,     # "Extra cuts"
    "snr": 368,        # "SNR W3/W4 > 3.5"
    "final": 7,
}
# Sec 2.5.6, verbatim: "the RUWE criterion refutes the largest quantity of
# candidates. A total of 282 sources are rejected by this criterion alone,
# which corresponds to roughly half of all sources rejected by any criteria in
# Section 2.5. The Halpha emission, the optical variability, and the extended
# flag criteria equally contribute to the rest of the cuts."
PAPER_EXTRA_TOTAL = PAPER["cnn"] - PAPER["extra"]                 # 595
PAPER_RUWE_REJ = 282
PAPER_EACH_OTHER = (PAPER_EXTRA_TOTAL - PAPER_RUWE_REJ) / 3.0     # ~104 each


def covered_area(tiles: dict) -> float:
    done = {k: v for k, v in tiles.items() if v.get("status") == "done"}
    return sum(v.get("area", 0.0) for k, v in done.items()
               if not any(k != j and k.startswith(j) for j in done))


def load_rows(parent: str = "esac"):
    """The parent sample.

    `esac`  -- the 93 ESAC tiles, 48.18% of sky (what M3 measured on).
    `aip`   -- the completed AIP harvest, 100% of sky, C1 applied with the
               exact ESAC r_med_geo. Its area is exact by construction.
    """
    if parent == "aip":
        sys.path.insert(0, str(ROOT / "scripts"))
        from m4_aip_screen import (CELLS, DIST, load_manifest,   # noqa: PLC0415
                                   read_cell, covered_area as cov_cells)
        m = load_manifest()
        done = [c for c in m["cells"].values() if c.get("status") == "done"]
        rows = pd.concat([read_cell(CELLS / c["file"]) for c in done],
                         ignore_index=True).drop_duplicates(subset="source_id")
        dfs = [pd.read_csv(q) for q in sorted(DIST.glob("*.csv"))]
        dist = (pd.concat(dfs, ignore_index=True)
                .dropna(subset=["source_id", "r_med_geo"])
                .drop_duplicates(subset="source_id"))
        rows = rows.merge(dist[["source_id", "r_med_geo"]], on="source_id",
                          how="left")
        rows = rows[rows["r_med_geo"] < 300].reset_index(drop=True)
        area = cov_cells(m["cells"])
        return rows, (SKY_DEG2 if area > SKY_DEG2 * 0.999 else area)
    m = json.loads((W4 / "manifest.json").read_text())
    done = [r for r in m["tiles"].values() if r.get("status") == "done"]
    rows = pd.concat([pd.read_csv(W4 / "tiles" / r["file"]) for r in done],
                     ignore_index=True)
    rows = rows.drop_duplicates(subset="source_id").reset_index(drop=True)
    return rows, covered_area(m["tiles"])


def gvar_binned(rows, ref, width, on="phot_g_mean_mag"):
    """Suazo Eq.4 / Vioque+20:
        Gvar = F'_G e(F_G) sqrt(N_obs) / (F_G e'(F_G) sqrt(N'_obs))
    where the primed quantities are the MEDIAN over "sources with similar
    fluxes".  `ref` is the reference sample those medians are taken from --
    the thing the paper never publishes.
    """
    lo = float(np.nanmin(ref[on])) - width
    hi = float(np.nanmax(ref[on])) + 2 * width
    edges = np.arange(lo, hi, width)
    rb = np.digitize(ref[on], edges)
    med = (pd.DataFrame({"_b": rb,
                         "fp": ref["phot_g_mean_flux"].to_numpy(),
                         "ep": ref["phot_g_mean_flux_error"].to_numpy(),
                         "np_": ref["phot_g_n_obs"].to_numpy()})
           .groupby("_b").median())
    b = np.digitize(rows[on], edges)
    j = med.reindex(b)
    return pd.Series(
        j["fp"].to_numpy() * rows["phot_g_mean_flux_error"].to_numpy()
        * np.sqrt(rows["phot_g_n_obs"].to_numpy())
        / (rows["phot_g_mean_flux"].to_numpy() * j["ep"].to_numpy()
           * np.sqrt(j["np_"].to_numpy())), index=rows.index)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m4")
    ap.add_argument("--parent", choices=["esac", "aip"], default="esac")
    ap.add_argument("--funnel", default="w4_funnel_m3_g0.1.json")
    ap.add_argument("--rmse-file", dest="rmse_file",
                    default="w4_rmse_survivors_m3_g0.1.csv")
    ap.add_argument("--ext-ref", dest="ext_ref", default="",
                    help="CSV of external Gaia reference medians "
                         "(g_lo, fp, ep, np_) for Gvar variant R7")
    a = ap.parse_args()

    rows, area = load_rows(a.parent)
    fsky = area / SKY_DEG2
    print(f"coverage {area:,.0f} deg2 = {100 * fsky:.2f}% of sky; "
          f"{len(rows):,} W3W4-detected rows")
    rep = {"_area_deg2": area, "_sky_fraction": fsky,
           "_n_w34det": int(len(rows))}

    # ===================================================== (1) THE PARENT ===
    cc = rows["cc_flags"].astype(str).str.strip().isin(["0000", "0"])
    s3 = 1.0857 / rows["w3mpro_error"]
    s4 = 1.0857 / rows["w4mpro_error"]
    snr = (s3 >= 3.5) & (s4 >= 3.5)
    n_cc = int(cc.sum())
    print("\n=== (1) the 1.43x parent discrepancy ===")
    print(f"  W3&W4 detected, BEFORE cc_flags : {len(rows):8,}  -> sky-wide "
          f"{len(rows) / fsky:10,.0f}   vs 3.2e5 = "
          f"{(len(rows) / fsky) / PAPER['w34det']:.3f}x   <- M3's comparison")
    print(f"  W3&W4 detected, AFTER  cc_flags : {n_cc:8,}  -> sky-wide "
          f"{n_cc / fsky:10,.0f}   vs 3.2e5 = "
          f"{(n_cc / fsky) / PAPER['w34det']:.3f}x   <- the paper's own "
          f"definition (Sec 2.1)")
    print(f"  cc_flags pass rate: {cc.mean():.4f}")
    print("\n  the paper's INDEPENDENT cross-check (Sec 5): '~200,000 sources' "
          "with W3/W4 detection and SNR>=3.5:")
    print(f"    ours, cc-clean  : {int((cc & snr).sum()):8,} -> sky-wide "
          f"{(cc & snr).sum() / fsky:10,.0f}  = "
          f"{((cc & snr).sum() / fsky) / 2.0e5:.3f}x")
    print(f"    ours, no cc cut : {int(snr.sum()):8,} -> sky-wide "
          f"{snr.sum() / fsky:10,.0f}  = {(snr.sum() / fsky) / 2.0e5:.3f}x")
    rep["parent"] = {
        "n_w34det_pre_cc": int(len(rows)), "n_w34det_post_cc": n_cc,
        "skywide_pre_cc": len(rows) / fsky, "skywide_post_cc": n_cc / fsky,
        "ratio_pre_cc": (len(rows) / fsky) / PAPER["w34det"],
        "ratio_post_cc": (n_cc / fsky) / PAPER["w34det"],
        "cc_pass_rate": float(cc.mean()),
        "sec5_200k_ccclean": (cc & snr).sum() / fsky,
        "sec5_200k_nocc": snr.sum() / fsky,
    }

    # ============================================== (2) STAGE ALIGNMENT =====
    surv = pd.read_csv(OUT / a.rmse_file)
    keep = ["source_id", "phot_g_mean_flux", "phot_g_mean_flux_error",
            "phot_g_n_obs", "ext_flag", "classprob_dsc_combmod_star",
            "phot_g_mean_mag"]
    surv = surv.merge(rows[keep], on="source_id", how="left")
    print("\n=== (2) stage alignment: the CNN sits BEFORE the extra cuts ===")
    print(f"  paper: RMSE {PAPER['rmse']:,} -> CNN {PAPER['cnn']:,} "
          f"({100 * (1 - PAPER['cnn'] / PAPER['rmse']):.1f}% rejected) "
          f"-> extras {PAPER['extra']:,} "
          f"({100 * (1 - PAPER['extra'] / PAPER['cnn']):.1f}% rejected)")
    print(f"  M3 compared 5137/11243 = "
          f"{100 * PAPER['extra'] / PAPER['rmse']:.1f}% pass and attributed "
          f"the missing 54% to Gvar.\n  That 54% is CNN x extras, not extras.")

    rej = {
        "ruwe>=1.4": int((surv["ruwe"] >= 1.4).sum()),
        "ext_flg!=0": int((surv["ext_flag"] != 0).sum()),
        "classprob<=0.9": int((surv["classprob_dsc_combmod_star"] <= 0.9).sum()),
        "gvar>=2 (in-sample ref)": int((surv["gvar"] >= 2).sum()),
    }
    n_rmse = len(surv)
    n_extra_pass = int(surv["extra_ok"].sum())
    print(f"\n  per-criterion rejection of our {n_rmse:,} RMSE survivors "
          f"(each criterion applied ALONE):")
    for k, v in rej.items():
        print(f"    {k:28s} {v:5,}  = {100 * v / n_rmse:5.2f}%")
    print(f"    {'ALL FOUR together':28s} {n_rmse - n_extra_pass:5,}  = "
          f"{100 * (n_rmse - n_extra_pass) / n_rmse:5.2f}%")
    print(f"\n  paper Sec 2.5.6 accounting, out of its {PAPER['cnn']:,} "
          f"post-CNN sources:")
    print(f"    {'RUWE (stated: 282)':28s} {PAPER_RUWE_REJ:5,}  = "
          f"{100 * PAPER_RUWE_REJ / PAPER['cnn']:5.2f}%")
    print(f"    {'Halpha / Gvar / ext_flg':28s} {PAPER_EACH_OTHER:5.0f}  = "
          f"{100 * PAPER_EACH_OTHER / PAPER['cnn']:5.2f}%  each "
          f"('equally contribute to the rest')")
    print(f"    {'ALL together':28s} {PAPER_EXTRA_TOTAL:5,}  = "
          f"{100 * PAPER_EXTRA_TOTAL / PAPER['cnn']:5.2f}%")
    rep["stage_alignment"] = {
        "paper_cnn_rejects_pct": 100 * (1 - PAPER["cnn"] / PAPER["rmse"]),
        "paper_extras_reject_pct": 100 * (1 - PAPER["extra"] / PAPER["cnn"]),
        "ours_extras_reject_pct": 100 * (n_rmse - n_extra_pass) / n_rmse,
        "ours_per_criterion": rej, "n_rmse": n_rmse,
        "paper_ruwe_pct": 100 * PAPER_RUWE_REJ / PAPER["cnn"],
        "paper_each_other_pct": 100 * PAPER_EACH_OTHER / PAPER["cnn"],
    }

    # ========================================= (3) GVAR REFERENCE VARIANTS ==
    print("\n=== (3) how much can the Gvar reference sample possibly move? ===")
    full10 = ["phot_bp_mean_mag", "phot_rp_mean_mag", "j_m", "h_m", "ks_m",
              "w1mpro", "w2mpro", "w3mpro", "w4mpro", "r_med_geo"]
    have = [c for c in full10 if c in rows.columns]
    variants = {
        "R1 in-sample W3W4-detected, 0.2 mag (M3's)": (rows, 0.2),
        "R2 cc-clean subsample, 0.2 mag": (rows[cc], 0.2),
        "R3 full-10-band subsample, 0.2 mag": (rows[cc].dropna(subset=have), 0.2),
        "R4 in-sample, 0.1 mag bins": (rows, 0.1),
        "R5 in-sample, 0.5 mag bins": (rows, 0.5),
        "R6 in-sample, 1.0 mag bins": (rows, 1.0),
    }
    gv_rows = {n: gvar_binned(surv, ref, w) for n, (ref, w) in variants.items()}
    if a.ext_ref and Path(a.ext_ref).exists():
        ext = pd.read_csv(a.ext_ref).sort_values("g_lo").reset_index(drop=True)
        b = np.clip(np.digitize(surv["phot_g_mean_mag"],
                                ext["g_lo"].to_numpy()) - 1, 0, len(ext) - 1)
        j = ext.iloc[b]
        gv_rows["R7 EXTERNAL Gaia <300pc, no WISE requirement"] = pd.Series(
            j["fp"].to_numpy() * surv["phot_g_mean_flux_error"].to_numpy()
            * np.sqrt(surv["phot_g_n_obs"].to_numpy())
            / (surv["phot_g_mean_flux"].to_numpy() * j["ep"].to_numpy()
               * np.sqrt(j["np_"].to_numpy())), index=surv.index)

    # R8 -- the reference sample RECONSTRUCTED from the paper's own numbers.
    # Suazo et al. Table 5 publishes Gvar for the 7 candidates; M1 computed
    # ours for the same 7 stars from our own in-sample reference.  The ratio
    # IS the reference-sample offset, measured on real objects rather than
    # guessed.  Applying it rescales our threshold to the paper's effective one.
    acc = pd.read_csv(OUT / "w1_acceptance.csv")
    ratio = (acc["gvar"] / acc["gvar_paper"]).dropna()
    k = float(ratio.median())
    print(f"  reference-sample offset, measured on the {len(ratio)} candidates "
          f"with a published Gvar:")
    print(f"    ours/paper = {k:.4f} (median), sd {ratio.std():.4f}, "
          f"range {ratio.min():.3f}-{ratio.max():.3f}")
    print(f"    => our Gvar is systematically {100 * (k - 1):.1f}% HIGH, i.e. "
          f"our cut at 2 is the paper's cut at {2 / k:.3f}")
    print(f"    => the paper's cut at 2 is ours at {2 * k:.3f}\n")
    rep["gvar_reference_offset"] = {
        "n_calibrators": int(len(ratio)), "median_ratio": k,
        "sd": float(ratio.std()), "min": float(ratio.min()),
        "max": float(ratio.max()),
        "our_threshold_matching_paper": 2 * k}

    other_ok = ((surv["ruwe"] < 1.4) & (surv["ext_flag"] == 0)
                & (surv["classprob_dsc_combmod_star"] > 0.9))
    exp_snr = PAPER["snr"] * fsky
    gv_rows["R8 in-sample, threshold rescaled to the paper's published Gvar"] = (
        gv_rows["R1 in-sample W3W4-detected, 0.2 mag (M3's)"] / k)
    print(f"  {'reference sample':50s} {'Gvar>=2':>8s} {'extras':>8s} "
          f"{'pre-vis':>8s} {'vs paper':>9s}")
    gvres = {}
    for name, gv in gv_rows.items():
        n_g = int((gv >= 2).sum())
        ok = other_ok & (gv < 2)
        n_ex = int(ok.sum())
        n_pv = int((ok & surv["snr_ok"]).sum())
        print(f"  {name:50s} {n_g:8,} {n_ex:8,} {n_pv:8,} "
              f"{n_pv / exp_snr:8.2f}x")
        gvres[name] = dict(gvar_rejected=n_g, gvar_rejected_pct=100 * n_g / n_rmse,
                           extras_pass=n_ex, previsual=n_pv,
                           ratio_vs_paper=n_pv / exp_snr)
    rep["gvar_variants"] = gvres

    n_pv_none = int((other_ok & surv["snr_ok"]).sum())
    print(f"\n  REFERENCE-FREE BOUND: Gvar's cut is monotone, so no choice of "
          f"reference sample can\n  give more pre-visual survivors than "
          f"{n_pv_none:,} (Gvar disabled) or fewer than 0.")
    print(f"  Gvar disabled entirely: {n_pv_none:,} = "
          f"{n_pv_none / exp_snr:.2f}x the paper's {exp_snr:.0f}.")
    print(f"  So the ENTIRE Gvar reference question is worth at most "
          f"{n_pv_none - min(g['previsual'] for g in gvres.values()):,} "
          f"survivors out of {n_pv_none:,}.")
    rep["gvar_bound"] = {"previsual_gvar_disabled": n_pv_none,
                         "ratio_gvar_disabled": n_pv_none / exp_snr}

    # ======================================= (4) THE ALIGNED FUNNEL ========
    print("\n=== (4) the funnel with the paper's own stage order ===")
    fun = json.loads((OUT / a.funnel).read_text())
    n_rmse_f, n_ex_f, n_snr_f = fun["T3_rmse"], fun["T4_extra"], fun["T5_snr"]
    paper_rmse = PAPER["rmse"] * fsky
    paper_extras_nocnn = PAPER["rmse"] * (PAPER["extra"] / PAPER["cnn"]) * fsky
    paper_snr_nocnn = paper_extras_nocnn * (PAPER["snr"] / PAPER["extra"])
    print(f"  {'stage':46s} {'ours':>9s} {'paper, no CNN':>15s} {'ratio':>8s}")
    print(f"  {'W3W4-detected + cc_flags (the parent)':46s} {n_cc:9,} "
          f"{PAPER['w34det'] * fsky:15,.0f} "
          f"{n_cc / (PAPER['w34det'] * fsky):7.2f}x")
    print(f"  {'RMSE <= 0.2':46s} {n_rmse_f:9,} {paper_rmse:15,.0f} "
          f"{n_rmse_f / paper_rmse:7.2f}x")
    print(f"  {'+ extra cuts (CNN applied by neither)':46s} {n_ex_f:9,} "
          f"{paper_extras_nocnn:15,.0f} {n_ex_f / paper_extras_nocnn:7.2f}x")
    print(f"  {'+ S/N >= 3.5':46s} {n_snr_f:9,} {paper_snr_nocnn:15,.0f} "
          f"{n_snr_f / paper_snr_nocnn:7.2f}x")
    print(f"\n  if the paper's CNN is credited (we cannot reproduce it):")
    print(f"  {'+ S/N >= 3.5, paper WITH CNN':46s} {n_snr_f:9,} "
          f"{exp_snr:15,.0f} {n_snr_f / exp_snr:7.2f}x")
    rep["aligned_funnel"] = {
        "parent_ratio": n_cc / (PAPER["w34det"] * fsky),
        "rmse_ratio": n_rmse_f / paper_rmse,
        "extras_ratio_noCNN": n_ex_f / paper_extras_nocnn,
        "snr_ratio_noCNN": n_snr_f / paper_snr_nocnn,
        "snr_ratio_withCNN": n_snr_f / exp_snr,
        "cnn_factor": PAPER["rmse"] / PAPER["cnn"],
    }

    # ============================ (5) the residual S/N gap, split by M_G ====
    print("\n=== (5) the residual S/N gap, split by absolute magnitude ===")
    s = surv[surv["extra_ok"]].copy()
    print(f"  {'M_G bin':12s} {'n':>7s} {'pass S/N':>9s} {'rate':>7s}")
    mg = {}
    for lo, hi in [(-99, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 99)]:
        sel = s[(s["M_G"] >= lo) & (s["M_G"] < hi)]
        if not len(sel):
            continue
        print(f"  {f'{lo:g}..{hi:g}':12s} {len(sel):7,} "
              f"{int(sel['snr_ok'].sum()):9,} {100 * sel['snr_ok'].mean():6.1f}%")
        mg[f"{lo:g}..{hi:g}"] = dict(n=int(len(sel)),
                                     n_pass=int(sel["snr_ok"].sum()),
                                     rate=float(sel["snr_ok"].mean()))
    print(f"  {'ALL':12s} {len(s):7,} {int(s['snr_ok'].sum()):9,} "
          f"{100 * s['snr_ok'].mean():6.1f}%   (paper: "
          f"{100 * PAPER['snr'] / PAPER['extra']:.1f}%)")
    narrow = s[(s["M_G"] >= 6) & (s["M_G"] <= 14.5)]
    print(f"  restricted to M1/M2's old K/M window M_G 6-14.5: {len(narrow):,} "
          f"-> {int(narrow['snr_ok'].sum()):,} = "
          f"{100 * narrow['snr_ok'].mean():.1f}%")
    rep["snr_by_mg"] = mg
    rep["snr_rate_all"] = float(s["snr_ok"].mean())
    rep["snr_rate_paper"] = PAPER["snr"] / PAPER["extra"]
    rep["snr_rate_narrow_window"] = float(narrow["snr_ok"].mean())

    # ============ (6) the S/N gap against GALACTIC LATITUDE = the CNN =======
    # The paper's missing stage is a NEBULAR classifier.  Nebulosity lives in
    # the Galactic plane and makes W3/W4 bright, i.e. HIGH S/N.  If the S/N
    # gap is the missing CNN, our S/N pass rate must fall towards the paper's
    # as |b| rises -- and at high |b|, where there is little nebulosity to
    # classify, the two should agree.  This is a prediction with a direction,
    # made before it was run (M4 PR-4), not a fit.
    from astropy.coordinates import SkyCoord           # noqa: PLC0415
    import astropy.units as u                          # noqa: PLC0415
    print("\n=== (6) the S/N gap against Galactic latitude ===")
    gl = np.abs(SkyCoord(ra=s["ra"].to_numpy() * u.deg,
                         dec=s["dec"].to_numpy() * u.deg).galactic.b.deg)
    s = s.assign(glat=gl)
    prate = PAPER["snr"] / PAPER["extra"]
    print(f"  {'|b| bin':10s} {'n':>7s} {'passS/N':>8s} {'rate':>7s} "
          f"{'/paper':>8s}")
    lat = {}
    for lo, hi in [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]:
        q = s[(s["glat"] >= lo) & (s["glat"] < hi)]
        if not len(q):
            continue
        print(f"  {f'{lo}-{hi}':10s} {len(q):7,} {int(q['snr_ok'].sum()):8,} "
              f"{100 * q['snr_ok'].mean():6.1f}% "
              f"{q['snr_ok'].mean() / prate:7.2f}x")
        lat[f"{lo}-{hi}"] = dict(n=int(len(q)), n_pass=int(q["snr_ok"].sum()),
                                 rate=float(q["snr_ok"].mean()),
                                 ratio_vs_paper=float(q["snr_ok"].mean() / prate))
    print(f"  {'ALL':10s} {len(s):7,} {int(s['snr_ok'].sum()):8,} "
          f"{100 * s['snr_ok'].mean():6.1f}% "
          f"{s['snr_ok'].mean() / prate:7.2f}x    (paper {100 * prate:.1f}%)")
    print(f"\n  median |b|: S/N-pass {s[s.snr_ok]['glat'].median():.1f} deg, "
          f"S/N-fail {s[~s.snr_ok]['glat'].median():.1f} deg")
    rep["snr_by_glat"] = lat

    # absolute yield per deg2 by |b|, needing the covered area per band
    BANDS = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90)]
    areas = {}
    if fsky > 0.999:
        # Full sky: the area with |b| in [lo, hi) is exactly
        # (sin hi - sin lo) x 4pi sr. No Monte Carlo, no tile geometry.
        for lo, hi in BANDS:
            areas[(lo, hi)] = SKY_DEG2 * (np.sin(np.radians(hi))
                                          - np.sin(np.radians(lo)))
    else:
        rng = np.random.default_rng(20260821)
        mm = json.loads((W4 / "manifest.json").read_text())
        dn = [r for r in mm["tiles"].values() if r.get("status") == "done"]
        dn = [r for r in dn
              if not any(r["id"] != j["id"] and r["id"].startswith(j["id"])
                         for j in dn)]
        for r in dn:
            n = 4000
            sd = rng.uniform(np.sin(np.radians(r["dec0"])),
                             np.sin(np.radians(r["dec1"])), n)
            dec = np.degrees(np.arcsin(sd))
            ra = rng.uniform(r["ra0"], r["ra1"], n)
            b = np.abs(SkyCoord(ra=ra * u.deg, dec=dec * u.deg).galactic.b.deg)
            for lo, hi in BANDS:
                areas[(lo, hi)] = areas.get((lo, hi), 0.0) + \
                    r["area"] * float(((b >= lo) & (b < hi)).mean())
    paper_rate = PAPER["snr"] / SKY_DEG2          # pre-visual survivors / deg2
    print(f"\n  absolute pre-visual yield per 1000 deg2, by |b| "
          f"(paper's all-sky mean = {1000 * paper_rate:.2f}):")
    yl = {}
    for (lo, hi), ar in sorted(areas.items()):
        q = s[(s["glat"] >= lo) & (s["glat"] < hi)]
        n_pv = int(q["snr_ok"].sum())
        print(f"  {f'|b| {lo}-{hi}':14s} area {ar:8,.0f} deg2  n={n_pv:5,}  "
              f"{1000 * n_pv / ar:8.2f}  = {(n_pv / ar) / paper_rate:6.2f}x "
              f"the paper's mean")
        yl[f"{lo}-{hi}"] = dict(area_deg2=ar, n=n_pv, per1000=1000 * n_pv / ar,
                                ratio=float((n_pv / ar) / paper_rate))
    rep["yield_by_glat"] = yl

    p = OUT / f"m4_funnel_reconcile_{a.tag}.json"
    p.write_text(json.dumps(rep, indent=2, default=str))
    print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
