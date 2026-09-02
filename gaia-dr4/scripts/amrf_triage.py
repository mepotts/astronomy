#!/usr/bin/env python
"""M2: AMRF compact-companion triage on the full DR3 NSS astrometric-orbit set.

Consumes data/dr3_nss_amrf_input.parquet (scripts/pull_dr3_nss_orbits.py) and
produces, per source:
  a0 [mas], sigma_TI^2, M1 (three-tier source), AMRF A, dark-companion q_min
  and M2_min, deterministic class (1/2/3), Monte-Carlo class-III probability,
  and one boolean per quality cut (cuts are FLAGS here -- nothing is dropped,
  so every rejected population stays measurable).

M1 three-tier policy (the acceptance-critical design decision):
  tier 1 'binary_masses': gaiadr3.binary_masses m1 with m1_ref='IsocLum'
         (what Shahaf et al. 2023 used; DR4 equivalent: nss_masses).
  tier 2 'photometric_ms': EEM/Pecaut-Mamajek M_G->mass, only if the CMD
         main-sequence cut (El-Badry 2026 eq. 1) passes. NO extinction
         correction (documented; biases M1 low / A high when reddened).
  tier 3 'evolved_bracket': off-MS sources (giants! Gaia BH2 is one) get NO
         point M1; class is the WORST case over M1 in [0.8, 2.6] Msun, so an
         evolved primary is never silently dropped and never over-claimed.

Outputs:
  data/dr3_amrf_triage.parquet      full per-source triage table
  out/amrf_class3_candidates.csv    class-III set under the default config
  out/amrf_class_counts.csv         counts per class x cut-stage
  out/amrf_plane.png                A vs M1 plane (density + boundaries +
                                    BH1/BH2 + El-Badry 2026 verdicts)
  out/amrf_class_distribution.png   class counts before/after quality cuts
  stdout                            BH1 + BH2 acceptance report (exit 1 on fail)

Run   : .venv/Scripts/python.exe scripts/amrf_triage.py
"""

import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amrf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PARQUET = os.path.join(BASE, "data", "dr3_nss_amrf_input.parquet")
OUT_PARQUET = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")
OUT_DIR = os.path.join(BASE, "out")
EB26_CSV = os.path.join(BASE, "fixtures", "elbadry2026_astrometric_candidates.csv")

BH1 = 4373465352415301632
BH2 = 5870569352746779008

CONFIG = {
    # window/sanity (DR3 values; DR4 day-one: p_max_days -> 2200, see M2 doc)
    "p_min_days": 10.0,
    "p_max_days": 1500.0,
    "nss_plx_over_err_min": 3.0,
    # Halbwachs et al. 2023 (A&A 674, A9) vetting, as used by S23:
    #   de < 0.079 ln(P) - 0.244 ; plx/sig > 20000/P ; a0 sig > 158/sqrt(P)
    # S23 Thiele-Innes criterion: sigma_TI^2 <= 36
    "sigma_ti2_max": 36.0,
    # El-Badry 2026 (arXiv:2608.06453) spurious-solution discriminators.
    # 10, not 20: >20 would reject Gaia BH1 (sig 13.6) and 5 more EB26-
    # confirmed systems; the >20 tier is kept as a high-purity FLAG.
    "significance_min": 10.0,
    "gof_split_gmag": 13.0,
    "gof_max_bright": 6.0,   # G < 13
    "gof_max_faint": 4.0,    # G > 13
    # class boundary: Mamajek curve x inflate. Calibration (M2 doc 4-5):
    # 1.15 = S23's conservative envelope's typical level; recovers 177/177 of
    # S23's class-III AND is identical to 1.0 on the El-Badry confirmed set,
    # while 1.25 over-rejects (loses 12/177 S23 + 9/42 EB26-confirmed).
    "boundary_inflate": 1.15,
    # evolved-primary bracket [Msun]
    "evolved_lo": 0.8,
    "evolved_hi": 2.6,
    # MC
    "mc_draws": 1000,
    "mc_seed": 20261202,
    "phot_m1_sigma_frac": 0.10,
    # 1-yr alias flag window (flag only, never a cut)
    "alias_lo_days": 330.0,
    "alias_hi_days": 400.0,
}


def compute_m1(df):
    """Three-tier M1. Returns (m1, m1_sigma, m1_source[str])."""
    m1 = np.full(len(df), np.nan)
    m1_sig = np.full(len(df), np.nan)
    src = np.array(["evolved_bracket"] * len(df), dtype=object)

    # tier 2 candidate values for everyone (needed to know MS-ness)
    mg = amrf.abs_g(df["phot_g_mean_mag"].values, df["nss_parallax"].values)
    ms = amrf.is_main_sequence(mg, df["bp_rp"].values)
    m1_phot = amrf.mass_of_mg(mg)
    phot_ok = ms & np.isfinite(m1_phot)

    m1[phot_ok] = m1_phot[phot_ok]
    m1_sig[phot_ok] = CONFIG["phot_m1_sigma_frac"] * m1_phot[phot_ok]
    src[phot_ok] = "photometric_ms"

    # tier 1 overrides where DPAC has an isochrone-luminosity mass
    bm_ok = df["bm_m1"].notna().values & (df["bm_m1_ref"].values == "IsocLum")
    m1[bm_ok] = df.loc[bm_ok, "bm_m1"].values
    with np.errstate(invalid="ignore"):
        bm_sig = (df["bm_m1_upper"].values - df["bm_m1_lower"].values) / 2.0
    m1_sig[bm_ok] = np.clip(bm_sig[bm_ok], 0.02, None)
    src[bm_ok] = "binary_masses"

    return m1, m1_sig, src, mg, ms


def evolved_bracket_class(a0, plx, period, inflate):
    """Worst-case (minimum) class and margin over M1 in the evolved bracket.
    margin = A / A_tr; class 3 only if class 3 at EVERY grid mass."""
    grid = np.linspace(CONFIG["evolved_lo"], CONFIG["evolved_hi"], 7)
    margins = []
    classes = []
    for m in grid:
        A = amrf.amrf(a0, plx, m, period)
        margins.append(A / amrf.a_tr(m, inflate=inflate))
        classes.append(amrf.classify(A, np.full_like(A, m), inflate=inflate))
    margins = np.vstack(margins)
    classes = np.vstack(classes)
    imin = np.argmin(margins, axis=0)
    take = np.arange(margins.shape[1])
    return classes.min(axis=0), margins[imin, take], grid[imin]


def mc_class_probs(df, m1, m1_sig, m1_src, inflate, rng):
    """Monte-Carlo P(class III) and P(class >= II) per source, chunked.
    Draws: TI coefficients, parallax, period ~ independent Gaussians (the DR3
    corr_vec correlations are NOT used -- validated against S23's published
    e_A in the calibration step); M1 ~ N(m1, m1_sig) for tiers 1-2, uniform
    over the evolved bracket for tier 3."""
    n = len(df)
    ndraw = CONFIG["mc_draws"]
    p3 = np.full(n, np.nan)
    p23 = np.full(n, np.nan)
    cols = ["a_thiele_innes", "b_thiele_innes", "f_thiele_innes",
            "g_thiele_innes"]
    for start in range(0, n, 8192):
        sl = slice(start, min(start + 8192, n))
        k = sl.stop - sl.start
        draws_a0 = amrf.thiele_innes_a0(
            *(rng.normal(df[c].values[sl, None].astype(float),
                         np.nan_to_num(df[c + "_error"].values[sl, None]
                                       .astype(float), nan=0.0),
                         (k, ndraw)) for c in cols))
        plx = rng.normal(df["nss_parallax"].values[sl, None],
                         np.nan_to_num(df["nss_parallax_error"].values[sl, None],
                                       nan=0.0), (k, ndraw))
        per = rng.normal(df["period"].values[sl, None],
                         np.nan_to_num(df["period_error"].values[sl, None],
                                       nan=0.0), (k, ndraw))
        m1c = m1[sl]
        m1s = np.nan_to_num(m1_sig[sl], nan=0.0)
        m1d = rng.normal(m1c[:, None], m1s[:, None], (k, ndraw))
        ev = m1_src[sl] == "evolved_bracket"
        if ev.any():
            m1d[ev] = rng.uniform(CONFIG["evolved_lo"], CONFIG["evolved_hi"],
                                  (int(ev.sum()), ndraw))
        bad = (plx <= 0) | (per <= 0) | (m1d <= 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            A = amrf.amrf(draws_a0, plx, m1d, per)
            atr = amrf.a_tr(m1d, inflate=inflate)
            ams = amrf.a_ms(m1d)
        A[bad] = np.nan
        ok = np.isfinite(A)
        nok = ok.sum(axis=1)
        with np.errstate(invalid="ignore"):
            p3[sl] = np.where(nok > 0, np.nansum(A > atr, axis=1) / nok, np.nan)
            p23[sl] = np.where(nok > 0, np.nansum(A > ams, axis=1) / nok, np.nan)
    return p3, p23


def main():
    cfg = CONFIG
    os.makedirs(OUT_DIR, exist_ok=True)
    in_path = sys.argv[1] if len(sys.argv) > 1 else IN_PARQUET
    subset_mode = in_path != IN_PARQUET
    if subset_mode:
        print(f"SUBSET MODE ({in_path}): acceptance + per-source columns are "
              f"valid; sample-wide counts/plots are NOT (skipped)")
    df = pd.read_parquet(in_path)
    print(f"input: {len(df)} rows")

    # --- a0 and TI quality -------------------------------------------------
    df["a0_mas"] = amrf.thiele_innes_a0(df["a_thiele_innes"], df["b_thiele_innes"],
                                        df["f_thiele_innes"], df["g_thiele_innes"])
    df["sigma_ti2"] = amrf.sigma_ti_sq(
        df["a_thiele_innes"], df["a_thiele_innes_error"],
        df["b_thiele_innes"], df["b_thiele_innes_error"],
        df["f_thiele_innes"], df["f_thiele_innes_error"],
        df["g_thiele_innes"], df["g_thiele_innes_error"])

    # --- M1 ----------------------------------------------------------------
    m1, m1_sig, m1_src, mg, ms = compute_m1(df)
    df["abs_g_noext"] = mg
    df["is_ms_cmd"] = ms
    df["m1_used"] = m1
    df["m1_sigma"] = m1_sig
    df["m1_source"] = m1_src

    # --- AMRF + deterministic class ---------------------------------------
    inflate = cfg["boundary_inflate"]
    point = m1_src != "evolved_bracket"
    A = np.full(len(df), np.nan)
    A[point] = amrf.amrf(df["a0_mas"].values[point],
                         df["nss_parallax"].values[point],
                         m1[point], df["period"].values[point])
    cls = np.zeros(len(df), dtype=int)
    margin = np.full(len(df), np.nan)
    cls[point] = amrf.classify(A[point], m1[point], inflate=inflate)
    margin[point] = A[point] / amrf.a_tr(m1[point], inflate=inflate)

    evb = ~point
    c_ev, marg_ev, m1_worst = evolved_bracket_class(
        df["a0_mas"].values[evb], df["nss_parallax"].values[evb],
        df["period"].values[evb], inflate)
    cls[evb] = c_ev
    margin[evb] = marg_ev
    # report a reference A at the bracket's worst-case mass
    A[evb] = amrf.amrf(df["a0_mas"].values[evb], df["nss_parallax"].values[evb],
                       m1_worst, df["period"].values[evb])
    df["amrf"] = A
    df["class_det"] = cls
    df["a_tr_margin"] = margin

    q = amrf.q_min_dark(df["amrf"].values)
    df["q_min_dark"] = q
    m1_eff = np.where(point, m1, m1_worst.mean() if len(m1_worst) else np.nan)
    m1_eff[evb] = m1_worst  # worst-case bracket mass
    df["m2_min_dark"] = q * m1_eff

    # --- quality-cut flags (never drops) -----------------------------------
    P = df["period"].values
    with np.errstate(invalid="ignore", divide="ignore"):
        df["cut_period"] = (P >= cfg["p_min_days"]) & (P <= cfg["p_max_days"])
        df["cut_plx"] = (df["nss_parallax"] > 0) & \
            (df["nss_parallax"] / df["nss_parallax_error"]
             >= cfg["nss_plx_over_err_min"])
        df["cut_halbwachs_ecc"] = df["eccentricity_error"] < \
            (0.079 * np.log(P) - 0.244)
        df["cut_halbwachs_plx"] = (df["nss_parallax"] /
                                   df["nss_parallax_error"]) > 20000.0 / P
        df["cut_halbwachs_a0sig"] = df["significance"] > 158.0 / np.sqrt(P)
        df["cut_sigma_ti"] = df["sigma_ti2"] <= cfg["sigma_ti2_max"]
        df["cut_significance"] = df["significance"] > cfg["significance_min"]
        df["flag_sig_gt20"] = df["significance"] > 20.0  # high-purity tier
        gof = df["goodness_of_fit"].values
        bright = df["phot_g_mean_mag"].values < cfg["gof_split_gmag"]
        df["cut_gof"] = np.where(bright, gof < cfg["gof_max_bright"],
                                 gof < cfg["gof_max_faint"])
        df["flag_alias_1yr"] = (P >= cfg["alias_lo_days"]) & \
            (P <= cfg["alias_hi_days"])
        df["flag_low_lat"] = np.abs(df["b"].values) < 10.0

    core = (df["cut_period"] & df["cut_plx"] & df["cut_halbwachs_ecc"]
            & df["cut_halbwachs_plx"] & df["cut_halbwachs_a0sig"]
            & df["cut_sigma_ti"])
    df["cuts_core"] = core
    df["cuts_eb26"] = core & df["cut_significance"] & df["cut_gof"]

    # --- MC class probabilities -------------------------------------------
    rng = np.random.default_rng(cfg["mc_seed"])
    p3, p23 = mc_class_probs(df, m1, m1_sig, m1_src, inflate, rng)
    df["p_class3_mc"] = p3
    df["p_class23_mc"] = p23

    # --- persist -----------------------------------------------------------
    out_parquet = OUT_PARQUET if not subset_mode else \
        os.path.join(BASE, "data", "dr3_amrf_triage_subset.parquet")
    df.to_parquet(out_parquet, index=False)
    print(f"wrote {out_parquet}")
    if subset_mode:
        return 0 if acceptance_report(df, inflate) else 1

    # --- candidates + counts ----------------------------------------------
    is3 = df["class_det"] == 3
    cand = df[is3 & df["cuts_eb26"]].copy()
    cand = cand.sort_values("m2_min_dark", ascending=False)
    keep_cols = ["source_id", "ra", "dec", "l", "b",
                 "nss_solution_type", "period", "eccentricity",
                 "a0_mas", "nss_parallax", "significance", "goodness_of_fit",
                 "sigma_ti2", "phot_g_mean_mag", "bp_rp", "ruwe",
                 "m1_used", "m1_source", "amrf", "a_tr_margin",
                 "q_min_dark", "m2_min_dark", "p_class3_mc",
                 "flag_alias_1yr", "flag_low_lat", "flag_sig_gt20"]
    cand[keep_cols].to_csv(os.path.join(OUT_DIR, "amrf_class3_candidates.csv"),
                           index=False, lineterminator="\n")

    # the epoch-vet retrieval bin: class III, core + F2 fine, ONLY the
    # significance tier failed (where BH1 would sit if sig_min were 20;
    # DR4 epoch astrometry adjudicates these on day one)
    rescue = df[is3 & core & df["cut_gof"] & ~df["cut_significance"]]
    rescue = rescue.sort_values("m2_min_dark", ascending=False)
    rescue[keep_cols].to_csv(
        os.path.join(OUT_DIR, "amrf_class3_lowsig_retrieval.csv"),
        index=False, lineterminator="\n")

    stages = {
        "input (all 6 astrometric NSS types)": np.ones(len(df), bool),
        "+ core quality (Halbwachs + sigma_TI + window + plx)": core.values,
        "+ El-Badry 2026 screen (significance>10, F2 mag-split)": df["cuts_eb26"].values,
    }
    rows = []
    for name, mask in stages.items():
        c = df.loc[mask, "class_det"].value_counts()
        rows.append({"stage": name, "n": int(mask.sum()),
                     "class1": int(c.get(1, 0)), "class2": int(c.get(2, 0)),
                     "class3": int(c.get(3, 0)),
                     "class0_undefined": int(c.get(0, 0))})
    counts = pd.DataFrame(rows)
    counts.to_csv(os.path.join(OUT_DIR, "amrf_class_counts.csv"), index=False,
                  lineterminator="\n")
    print(counts.to_string(index=False))

    make_plots(df, cand, counts, inflate)

    # --- acceptance: BH1 + BH2 --------------------------------------------
    ok = acceptance_report(df, inflate)
    return 0 if ok else 1


def acceptance_report(df, inflate):
    print("\n" + "=" * 74)
    print("ACCEPTANCE: Gaia BH1 and BH2 must land in class III")
    print("=" * 74)
    all_ok = True
    for name, sid in (("Gaia BH1", BH1), ("Gaia BH2", BH2)):
        sub = df[df["source_id"] == sid]
        if not len(sub):
            print(f"{name}: NOT IN INPUT PULL -- FAIL")
            all_ok = False
            continue
        r = sub.iloc[0]
        atr_here = (amrf.a_tr(r["m1_used"], inflate=inflate)
                    if r["m1_source"] != "evolved_bracket" else np.nan)
        print(f"\n{name} ({sid}, {r['nss_solution_type']}):")
        print(f"  a0 = {r['a0_mas']:.4f} mas, parallax = {r['nss_parallax']:.4f} mas, "
              f"P = {r['period']:.2f} d")
        print(f"  M1 = {r['m1_used'] if np.isfinite(r['m1_used']) else float('nan'):.3f} "
              f"Msun via {r['m1_source']}")
        print(f"  AMRF A = {r['amrf']:.3f}  (A_tr at M1 = "
              f"{atr_here if np.isfinite(atr_here) else float('nan'):.3f}, "
              f"inflate={inflate})")
        print(f"  class = {r['class_det']}  margin A/A_tr = {r['a_tr_margin']:.2f}x  "
              f"P(classIII|MC) = {r['p_class3_mc']:.4f}")
        print(f"  q_min = {r['q_min_dark']:.2f}, M2_min = {r['m2_min_dark']:.2f} Msun")
        core_cuts = {c: bool(r[c]) for c in
                     ["cut_period", "cut_plx", "cut_halbwachs_ecc",
                      "cut_halbwachs_plx", "cut_halbwachs_a0sig",
                      "cut_sigma_ti"]}
        print(f"  core cuts (triage gates): {core_cuts}")
        P = r["period"]
        print(f"  core-cut margins: plx_sig {r['nss_parallax']/r['nss_parallax_error']:.1f}"
              f" vs {20000.0/P:.1f} needed; a0_sig {r['significance']:.1f}"
              f" vs {158.0/np.sqrt(P):.1f} needed; sigma_TI^2 {r['sigma_ti2']:.1f}"
              f" vs 36 allowed")
        print(f"  EB26 spurious-screen tiers (calibrated knobs, NOT the class "
              f"gate): significance={r['significance']:.1f} -> "
              f">5:{r['significance'] > 5} >10:{r['significance'] > 10} "
              f">20:{r['significance'] > 20}; F2={r['goodness_of_fit']:.2f}, "
              f"G={r['phot_g_mean_mag']:.2f} -> magsplit_pass:{bool(r['cut_gof'])}")
        verdict = r["class_det"] == 3 and all(core_cuts.values())
        print(f"  -> {'PASS' if verdict else 'FAIL'} "
              f"(class III + core quality gates)")
        all_ok &= bool(verdict)
    print("\nACCEPTANCE OVERALL:", "PASS" if all_ok else "FAIL")
    return all_ok


# ----------------------------------------------------------------------
# plots (palette + rules: bundled dataviz skill, light surface)
# ----------------------------------------------------------------------
SURF = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BLUE_SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95",
            "#0d366b"]
GOOD = "#0ca30c"
CRIT = "#d03b3b"
BAR1 = "#2a78d6"
BAR2 = "#9ec5f4"


def _style_axes(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.9)
    ax.set_axisbelow(True)


def make_plots(df, cand, counts, inflate):
    from matplotlib.colors import LinearSegmentedColormap, LogNorm
    cmap = LinearSegmentedColormap.from_list("seqblue", BLUE_SEQ)

    # ---- A vs M1 plane ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.6, 6.2), facecolor=SURF)
    _style_axes(ax)
    pt = df[(df["m1_source"] != "evolved_bracket") & df["cuts_core"]
            & np.isfinite(df["amrf"]) & np.isfinite(df["m1_used"])]
    hb = ax.hexbin(pt["m1_used"], pt["amrf"], gridsize=90,
                   extent=(0.1, 2.6, 0.0, 1.4), norm=LogNorm(vmin=1),
                   cmap=cmap, mincnt=1, linewidths=0.1)
    cb = fig.colorbar(hb, ax=ax, pad=0.01, shrink=0.85)
    cb.set_label("sources per cell (log)", color=INK2, fontsize=9)
    cb.ax.tick_params(colors=MUTED, labelsize=8)
    cb.outline.set_visible(False)

    g = np.linspace(0.15, 2.55, 200)
    ax.plot(g, amrf.a_ms(g), color=INK, lw=1.4, ls=(0, (4, 2)))
    ax.plot(g, amrf.a_tr(g), color=INK, lw=1.6)
    ax.plot(g, amrf.a_tr(g, inflate=inflate), color=INK2, lw=1.4,
            ls=(0, (1.5, 1.5)))
    ax.annotate("A_MS (max, single MS companion)", (1.55, amrf.a_ms(1.55)),
                textcoords="offset points", xytext=(0, -14), ha="center",
                color=INK, fontsize=8.5)
    ax.annotate("A_tr (max, close-binary companion)", (1.85, amrf.a_tr(1.85)),
                textcoords="offset points", xytext=(0, -14), ha="center",
                color=INK, fontsize=8.5)
    ax.annotate(f"A_tr x {inflate:.2f} (triage boundary)",
                (2.05, amrf.a_tr(2.05, inflate=inflate)),
                textcoords="offset points", xytext=(0, 7), ha="center",
                color=INK2, fontsize=8.5)

    # El-Badry 2026 verdicts (status colors + distinct shapes)
    if os.path.exists(EB26_CSV):
        eb = pd.read_csv(EB26_CSV)
        j = eb.merge(df[["source_id", "m1_used", "amrf", "m1_source"]],
                     on="source_id", how="inner")
        jj = j[j["m1_source"] != "evolved_bracket"]
        conf = jj[jj["verdict"] == "CONFIRMED"]
        spur = jj[jj["verdict"] == "SPURIOUS"]
        ax.scatter(conf["m1_used"], conf["amrf"], s=26, facecolor=GOOD,
                   edgecolor=SURF, linewidths=0.8, zorder=5,
                   label="El-Badry 2026: confirmed compact object")
        ax.scatter(spur["m1_used"], spur["amrf"], s=34, marker="x", color=CRIT,
                   linewidths=1.6, zorder=5,
                   label="El-Badry 2026: spurious solution")
    y_top = 1.4
    for sid, nm, dxy, ha in (
            (BH1, "Gaia BH1", (10, -6), "left"),
            (BH2, "Gaia BH2 (evolved primary,\nworst-case bracket M1)", (-10, -6), "right")):
        r = df[df["source_id"] == sid]
        if len(r):
            r = r.iloc[0]
            x = r["m1_used"] if np.isfinite(r["m1_used"]) else 2.2
            y = min(r["amrf"], y_top - 0.05)  # clamp: both sit far above the axis
            ax.scatter([x], [y], marker="*", s=190, facecolor="#eda100",
                       edgecolor=INK, linewidths=0.7, zorder=6)
            ax.annotate(f"{nm}\nA = {r['amrf']:.2f} (off scale)", (x, y),
                        textcoords="offset points", xytext=dxy, color=INK,
                        fontsize=8.5, fontweight="bold", va="top", ha=ha)
    ax.set_xlim(0.1, 2.6)
    ax.set_ylim(0.0, y_top)
    ax.set_xlabel("primary mass M1 [Msun]", color=INK2, fontsize=10)
    ax.set_ylabel("AMRF  A = (a0/parallax) M1^(-1/3) (P/yr)^(-2/3)", color=INK2,
                  fontsize=10)
    ax.set_title("DR3 astrometric orbits in the AMRF plane "
                 "(core quality cuts; classes per Shahaf+19/23)",
                 color=INK, fontsize=11, pad=10)
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.02, 0.02),
                    fontsize=8.5, frameon=False, labelcolor=INK2)
    fig.tight_layout()
    p1 = os.path.join(OUT_DIR, "amrf_plane.png")
    fig.savefig(p1, dpi=150, facecolor=SURF)
    plt.close(fig)
    print(f"wrote {p1}")

    # ---- class counts before/after ---------------------------------------
    fig, ax = plt.subplots(figsize=(7.4, 4.4), facecolor=SURF)
    _style_axes(ax)
    labels = ["class I\n(MS companion)", "class II\n(close-binary comp.)",
              "class III\n(compact candidate)"]
    pre = [counts.iloc[1][f"class{i}"] for i in (1, 2, 3)]
    post = [counts.iloc[2][f"class{i}"] for i in (1, 2, 3)]
    x = np.arange(3)
    w = 0.38
    b1 = ax.bar(x - w / 2 - 0.01, pre, w, color=BAR1, label="core quality cuts")
    b2 = ax.bar(x + w / 2 + 0.01, post, w, color=BAR2,
                label="+ El-Badry 2026 cuts (significance, F2)")
    ax.set_yscale("log")
    ax.set_ylim(1, max(pre) * 4)
    for bars in (b1, b2):
        for rect in bars:
            v = rect.get_height()
            ax.annotate(f"{int(v):,}", (rect.get_x() + rect.get_width() / 2, v),
                        textcoords="offset points", xytext=(0, 3), ha="center",
                        color=INK2, fontsize=8.5)
    ax.set_xticks(x, labels, color=INK2, fontsize=9)
    ax.set_ylabel("sources (log)", color=INK2, fontsize=10)
    ax.set_title("AMRF class distribution, Gaia DR3 NSS astrometric orbits",
                 color=INK, fontsize=11, pad=10)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False, labelcolor=INK2)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    p2 = os.path.join(OUT_DIR, "amrf_class_distribution.png")
    fig.savefig(p2, dpi=150, facecolor=SURF)
    plt.close(fig)
    print(f"wrote {p2}")


if __name__ == "__main__":
    sys.exit(main())
