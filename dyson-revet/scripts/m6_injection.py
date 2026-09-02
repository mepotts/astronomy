"""M6: injection-recovery completeness for the extreme mid-IR-excess screen.

M5 Sec 4 marked the high-latitude catalogue's completeness UNMEASURED and
called it the biggest hole in the positive deliverable: nobody knew what
fraction of real extreme-excess objects the 10-band RMSE fit recovers.  M5
Sec 7 item 4 noted it needs no network at all.  This measures it.

    python scripts/m6_injection.py run    --per-cell 200 --jobs 12
    python scripts/m6_injection.py report

METHOD (M6 PR-3, fixed before the run).

* WHAT IS INJECTED.  Synthetic star + blackbody SEDs built by the SELECTION
  CODE'S OWN forward model -- `w1_selection.template_grid` for the photosphere
  and `ds_absolute_mags` + `combine` + the Eq-3 dimming for the shell -- over
  the declared factorial space: gamma x T_ds x host W3 magnitude x |b| band.
* THE HOST IS REAL.  Each injection takes a real parent row: its distance, its
  M_G, its Gvar / RUWE / ext_flag / classprob, and its Galactic latitude.  The
  per-band uncertainty is taken from a REAL parent row of the same band, the
  same |b| band and the same magnitude to +-0.25 mag, so the noise is the
  survey's own, at the INJECTED brightness rather than the host's.
* NOT DETECTED IS A RESULT.  If the injected W3 or W4 magnitude is fainter
  than any parent row in that |b| band (to +-0.5 mag), the object is recorded
  as UNDETECTED and counted as not recovered -- that is a real part of the
  selection function, not a failure of the code.
* WHAT "RECOVERED" MEANS.  The row is pushed through the UNMODIFIED pipeline:
  the same `fit_ds`, the same gamma >= 0.10 model grid, the same RMSE <= 0.2,
  the same extra cuts, the same S/N >= 3.5.  No stage is re-tuned.
* A CONTROL, added as a control and labelled as one: gamma = 0 injections,
  i.e. bare photospheres, measure the RMSE gate's own false-positive rate.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"
CELLS = ROOT / "data" / "w4" / "aip" / "cells"
DIST = ROOT / "data" / "w4" / "aip" / "distances"
INJ = ROOT / "data" / "injection"
INJ.mkdir(parents=True, exist_ok=True)

# PR-3's declared factorial space
GAMMAS = (0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50)
TDS = (100, 150, 200, 300, 450, 700, 1000)
BBANDS = ((0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 90))
SEED = 20260824
# adopted per-band photometric floors where the parent carries no uncertainty
# column: Gaia DR3 BP/G/RP and 2MASS JHKs.  They are far below the RMSE gate
# (0.2 mag) and are documented rather than fitted.
SIG_FIXED = {"BP": 0.01, "G": 0.005, "RP": 0.01, "J": 0.03, "H": 0.03, "Ks": 0.03}
WBANDS = ("W1", "W2", "W3", "W4")
GAMMA_FLOOR = 0.10          # the pipeline's own model-grid floor
MG_LO, MG_HI = 0.5, 14.0    # the screen's template window (M4 select)


def load_parent() -> pd.DataFrame:
    from m5_nebular import galactic
    dfs = [pd.read_csv(p) for p in sorted(CELLS.glob("*.csv"))]
    aip = pd.concat(dfs, ignore_index=True).rename(
        columns={"datalinkID": "source_id"})
    dd = [pd.read_csv(p, usecols=["source_id", "r_med_geo"])
          for p in sorted(DIST.glob("*.csv"))]
    dist = (pd.concat(dd, ignore_index=True).dropna(subset=["source_id", "r_med_geo"])
            .drop_duplicates("source_id"))
    aip = aip.merge(dist, on="source_id", how="left")
    aip = aip[aip["r_med_geo"] < 300.0]
    aip = aip[aip["cc_flags"].astype(str).str.strip().isin(["0000", "0"])]
    need = ["phot_bp_mean_mag", "phot_rp_mean_mag", "j_m", "h_m", "ks_m",
            "w1mpro", "w2mpro", "w3mpro", "w4mpro", "w3mpro_error",
            "w4mpro_error", "w1mpro_error", "w2mpro_error"]
    aip = aip.dropna(subset=need).copy()
    aip["dmod"] = 5 * np.log10(aip["r_med_geo"] / 10.0)
    aip["M_G"] = aip["phot_g_mean_mag"] - aip["dmod"]
    aip = aip[(aip["M_G"] >= MG_LO) & (aip["M_G"] <= MG_HI)]
    _, b = galactic(aip["ra"].to_numpy(), aip["dec"].to_numpy())
    aip["glat"] = b
    aip["abs_b"] = np.abs(b)
    # Gvar exactly as the screen computes it (m4_aip_screen.select): the
    # Vioque+2020 statistic against flux-matched medians in 0.2-mag G bins.
    # It is a property of the REAL host, so an injection inherits it, and
    # leaving it out would have made the extra-cut loss a lower bound.
    bins = np.arange(np.nanmin(aip["phot_g_mean_mag"]) - 0.1,
                     np.nanmax(aip["phot_g_mean_mag"]) + 0.3, 0.2)
    aip["_gbin"] = np.digitize(aip["phot_g_mean_mag"], bins)
    med = aip.groupby("_gbin").agg(fp=("phot_g_mean_flux", "median"),
                                   ep=("phot_g_mean_flux_error", "median"),
                                   np_=("phot_g_n_obs", "median")).reset_index()
    aip = aip.merge(med, on="_gbin", how="left")
    aip["gvar"] = (aip["fp"] * aip["phot_g_mean_flux_error"]
                   * np.sqrt(aip["phot_g_n_obs"])
                   / (aip["phot_g_mean_flux"] * aip["ep"] * np.sqrt(aip["np_"])))
    aip["snr3"] = 1.0857 / aip["w3mpro_error"]
    aip["snr4"] = 1.0857 / aip["w4mpro_error"]
    return aip.reset_index(drop=True)


def bband_index(absb: np.ndarray) -> np.ndarray:
    idx = np.full(len(absb), -1, int)
    for k, (lo, hi) in enumerate(BBANDS):
        idx[(absb >= lo) & (absb < hi)] = k
    idx[absb >= 90] = len(BBANDS) - 1
    return idx


def build_noise_tables(parent: pd.DataFrame) -> dict:
    """Empirical sigma(mag, |b| band) per WISE band: the real parent's own."""
    tab = {}
    for band in WBANDS:
        m = parent[band.lower() + "mpro"].to_numpy()
        s = parent[band.lower() + "mpro_error"].to_numpy()
        bi = parent["_bi"].to_numpy()
        for k in range(len(BBANDS)):
            sel = (bi == k) & np.isfinite(m) & np.isfinite(s) & (s > 0)
            tab[(band, k)] = (m[sel], s[sel])
    return tab


def sample_sigma(tab, band, k, mag, rng, tol=0.25, tol_max=0.5):
    """A real sigma from a real parent row at this magnitude and latitude."""
    mm, ss = tab[(band, k)]
    if len(mm) == 0:
        return None
    sel = np.abs(mm - mag) <= tol
    if sel.sum() < 5:
        sel = np.abs(mm - mag) <= tol_max
    if sel.sum() < 3:
        return None                 # fainter than anything the survey detects
    return float(rng.choice(ss[sel]))


def _init(locus):
    global _PM
    from w1_selection import load_pm13, use_locus
    use_locus(locus)
    _PM = load_pm13()


def _fit_chunk(rows):
    from w1_selection import fit_ds
    out = []
    for r in rows:
        oa = {b: r[b] for b in ("BP", "G", "RP", "J", "H", "Ks",
                                "W1", "W2", "W3", "W4")}
        f = fit_ds(oa, _PM, 100, 700, GAMMA_FLOOR, 0.90, nt=60, ng=30)
        out.append((r["i"], f["rmse"], f["t_ds"], f["gamma"]))
    return out


def cmd_run(a) -> None:
    from w1_selection import (combine, ds_absolute_mags, load_pm13,  # noqa
                              template_grid, use_locus)
    use_locus(a.locus)
    pm = load_pm13()
    parent = load_parent()
    parent["_bi"] = bband_index(parent["abs_b"].to_numpy())
    parent = parent[parent["_bi"] >= 0].reset_index(drop=True)
    print("parent pool: %d rows (C1 + cc_flags + 10-band + template window)"
          % len(parent))
    print("  per |b| band: %s"
          % dict(parent["_bi"].value_counts().sort_index()))
    noise = build_noise_tables(parent)

    rng = np.random.default_rng(SEED)
    gammas = (0.0,) + GAMMAS          # gamma = 0 is the labelled control
    rows, meta = [], []
    i = 0
    for k in range(len(BBANDS)):
        pool = parent[parent["_bi"] == k]
        if not len(pool):
            continue
        for g in gammas:
            for T in TDS:
                pick = pool.iloc[rng.integers(0, len(pool), a.per_cell)]
                for _, h in pick.iterrows():
                    mg = float(h["M_G"])
                    tg = template_grid(pm, mg - 0.02, mg + 0.02, step=0.04)
                    j = int(np.argmin(np.abs(tg["M_G"] - mg)))
                    logl = np.array([tg["logL"][j]])
                    dsm = ds_absolute_mags(np.array([float(T)]),
                                           np.array([g]), logl)
                    dim = -2.5 * np.log10(max(1 - g, 1e-9))
                    ap, undet = {}, False
                    for b in ("BP", "G", "RP", "J", "H", "Ks",
                              "W1", "W2", "W3", "W4"):
                        mstar = tg[b][j] + dim
                        mtot = (float(combine(np.array([mstar]), dsm[b])[0])
                                if b in dsm else mstar)
                        m_app = mtot + float(h["dmod"])
                        if b in WBANDS:
                            s = sample_sigma(noise, b, k, m_app, rng)
                            if s is None:
                                undet = True
                                s = 0.3
                            ap["sig_" + b] = s
                        else:
                            s = SIG_FIXED[b]
                        ap[b] = m_app + rng.normal(0.0, s)
                    rec = dict(ap)
                    rec.update(i=i, gamma_true=g, t_ds_true=float(T),
                               bband=k, abs_b=float(h["abs_b"]),
                               M_G=mg, dmod=float(h["dmod"]),
                               dist_pc=float(h["r_med_geo"]),
                               w3_true=ap["W3"], w4_true=ap["W4"],
                               undetected=bool(undet),
                               snr3=1.0857 / ap["sig_W3"],
                               snr4=1.0857 / ap["sig_W4"],
                               ruwe=float(h["ruwe"]), gvar=float(h["gvar"]),
                               ext_flag=float(h["ext_flag"]),
                               classprob=float(h["classprob_dsc_combmod_star"]),
                               host_source_id=int(h["source_id"]))
                    rows.append(rec)
                    i += 1
        print("  |b| band %d built (%d injections so far)" % (k, i), flush=True)
    df = pd.DataFrame(rows)
    # the DS model is defined in ABSOLUTE mags; fit_ds wants absolute too
    work = []
    for _, r in df.iterrows():
        d = {b: r[b] - r["dmod"] for b in ("BP", "G", "RP", "J", "H", "Ks",
                                           "W1", "W2", "W3", "W4")}
        d["i"] = int(r["i"])
        work.append(d)
    chunks = [work[x:x + 250] for x in range(0, len(work), 250)]
    print("fitting %d injections on %d process(es)..." % (len(work), a.jobs))
    t0 = time.time()
    results = []
    if a.jobs <= 1:
        _init(a.locus)
        for n, ch in enumerate(chunks):
            results += _fit_chunk(ch)
            if n % 20 == 0:
                print("  %d/%d (%.0f s)" % (len(results), len(work),
                                            time.time() - t0), flush=True)
    else:
        import multiprocessing as mp
        with mp.Pool(a.jobs, initializer=_init, initargs=(a.locus,)) as pool:
            for n, res in enumerate(pool.imap_unordered(_fit_chunk, chunks)):
                results += res
                if n % 20 == 0:
                    print("  %d/%d (%.0f s)" % (len(results), len(work),
                                                time.time() - t0), flush=True)
    fit = pd.DataFrame(results, columns=["i", "rmse", "t_ds_fit", "gamma_fit"])
    df = df.merge(fit, on="i", how="left")
    df["pass_rmse"] = (df["rmse"] <= 0.2) & ~df["undetected"]
    df["extra_ok"] = ((df["gvar"] < 2) & (df["ruwe"] < 1.4)
                      & (df["ext_flag"] == 0) & (df["classprob"] > 0.9))
    df["snr_ok"] = (df["snr3"] >= 3.5) & (df["snr4"] >= 3.5)
    df["recovered"] = df["pass_rmse"] & df["extra_ok"] & df["snr_ok"]
    # 75,600 rows is bulk; it lives under data/ (gitignored) per repo
    # convention, and only the aggregates below go to out/.
    p = INJ / "m6_injection_table.csv"
    df.to_csv(p, index=False)
    print("%d injections, %.0f s -> %s" % (len(df), time.time() - t0, p.name))
    print("  overall: RMSE gate %.1f%%, pre-visual %.1f%%, undetected %.1f%%"
          % (100 * df["pass_rmse"].mean(), 100 * df["recovered"].mean(),
             100 * df["undetected"].mean()))


def cmd_report(a) -> None:
    df = pd.read_csv(INJ / "m6_injection_table.csv")
    real = df[df["gamma_true"] > 0]
    ctrl = df[df["gamma_true"] == 0]
    out = {"n_injections": int(len(df)), "n_control_gamma0": int(len(ctrl)),
           "seed": SEED, "gammas": list(GAMMAS), "t_ds": list(TDS),
           "b_bands": [list(b) for b in BBANDS],
           "gamma_floor_of_model_grid": GAMMA_FLOOR}
    out["control_gamma0"] = {
        "rmse_gate_false_positive_rate": float(ctrl["pass_rmse"].mean()),
        "previsual_false_positive_rate": float(ctrl["recovered"].mean()),
        "note": "bare photospheres pushed through the unmodified pipeline; a "
                "bare photosphere that clears RMSE <= 0.2 is what the gate "
                "lets through on noise alone"}

    def tab(keys):
        g = real.groupby(keys).agg(n=("recovered", "size"),
                                   rmse=("pass_rmse", "mean"),
                                   prev=("recovered", "mean"),
                                   undet=("undetected", "mean"))
        return g.reset_index()

    by_g = tab(["gamma_true"])
    by_t = tab(["t_ds_true"])
    by_b = tab(["bband"])
    by_gt = tab(["gamma_true", "t_ds_true"])
    by_gb = tab(["gamma_true", "bband"])
    real2 = real.copy()
    real2["w3bin"] = np.floor(real2["w3_true"]).astype(int)
    by_w3 = real2.groupby("w3bin").agg(n=("recovered", "size"),
                                       rmse=("pass_rmse", "mean"),
                                       prev=("recovered", "mean"),
                                       undet=("undetected", "mean")).reset_index()
    for name, t in (("by_gamma", by_g), ("by_t_ds", by_t), ("by_b_band", by_b),
                    ("by_gamma_t_ds", by_gt), ("by_gamma_b_band", by_gb),
                    ("by_w3_mag", by_w3)):
        out[name] = json.loads(t.to_json(orient="records"))
        t.to_csv(OUT / ("m6_injection_%s.csv" % name), index=False)

    # the headline numbers the catalogue needs
    core = real[real["bband"] == len(BBANDS) - 1]
    hi = real[real["bband"] >= 4]
    # IN-GRID: the part of the parameter space the pipeline's own model grid
    # can represent at all -- gamma >= its floor and T_ds inside [100, 700] K.
    # Outside it the recovery fraction is a statement about the GRID, not about
    # the photometry, and the two must not be averaged together.
    ing = real[(real["gamma_true"] >= GAMMA_FLOOR) & (real["t_ds_true"] <= 700)]
    ing_hi = ing[ing["bband"] >= 4]
    ing_core = ing[ing["bband"] == len(BBANDS) - 1]
    ing_pl = ing[ing["bband"] <= 1]
    out["in_model_grid"] = {
        "definition": "gamma >= %.2f and 100 K <= T_ds <= 700 K" % GAMMA_FLOOR,
        "n": int(len(ing)),
        "all_sky_previsual_recovery": float(ing["recovered"].mean()),
        "all_sky_rmse_gate": float(ing["pass_rmse"].mean()),
        "b_gt_30_previsual_recovery": float(ing_hi["recovered"].mean()),
        "b_gt_50_previsual_recovery": float(ing_core["recovered"].mean()),
        "b_lt_10_previsual_recovery": float(ing_pl["recovered"].mean()),
        "undetected_fraction_b_gt_30": float(ing_hi["undetected"].mean()),
        "snr_gate_loss_b_gt_30": float((ing_hi["pass_rmse"]
                                        & ~ing_hi["snr_ok"]).mean()),
        "extra_gate_loss_b_gt_30": float((ing_hi["pass_rmse"]
                                          & ~ing_hi["extra_ok"]).mean())}
    out["outside_model_grid"] = {
        "gamma_below_floor_recovery": json.loads(
            real[real["gamma_true"] < GAMMA_FLOOR]
            .groupby("gamma_true")["recovered"].mean().to_json()),
        "T_ds_1000K_recovery": float(
            real[real["t_ds_true"] == 1000]["recovered"].mean()),
        "note": "T_ds = 1000 K lies OUTSIDE the pipeline's own [100, 700] K "
                "model grid; its recovery fraction measures the cost of the "
                "grid's temperature range, not of the photometry"}
    out["catalogue_footprint"] = {
        "highlat_b_gt_30_previsual_recovery": float(hi["recovered"].mean()),
        "core_b_gt_50_previsual_recovery": float(core["recovered"].mean()),
        "core_b_gt_50_by_gamma": json.loads(
            core.groupby("gamma_true")["recovered"].mean().to_json()),
        "core_b_gt_50_rmse_by_gamma": json.loads(
            core.groupby("gamma_true")["pass_rmse"].mean().to_json())}
    (OUT / "m6_injection_completeness.json").write_text(json.dumps(out, indent=2))
    pd.set_option("display.width", 200)
    print("CONTROL gamma = 0 (bare photospheres): RMSE gate lets %.2f%% "
          "through, pre-visual %.2f%%"
          % (100 * out["control_gamma0"]["rmse_gate_false_positive_rate"],
             100 * out["control_gamma0"]["previsual_false_positive_rate"]))
    print("\nRECOVERY by covering fraction gamma")
    print(by_g.round(4).to_string(index=False))
    print("\nRECOVERY by dust temperature T_ds")
    print(by_t.round(4).to_string(index=False))
    print("\nRECOVERY by |b| band")
    print(by_b.round(4).to_string(index=False))
    print("\nRECOVERY by W3 magnitude")
    print(by_w3.round(4).to_string(index=False))
    print("\nRECOVERY gamma x T_ds (pre-visual)")
    print(by_gt.pivot(index="gamma_true", columns="t_ds_true",
                      values="prev").round(3).to_string())
    print("\ncatalogue footprint: |b|>30 %.3f, |b|>50 core %.3f"
          % (out["catalogue_footprint"]["highlat_b_gt_30_previsual_recovery"],
             out["catalogue_footprint"]["core_b_gt_50_previsual_recovery"]))
    print("-> out/m6_injection_completeness.json")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--per-cell", type=int, default=200)
    r.add_argument("--jobs", type=int, default=12)
    r.add_argument("--locus", default="wise_locus_extended.csv")
    sub.add_parser("report")
    a = ap.parse_args()
    {"run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
