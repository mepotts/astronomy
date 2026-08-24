"""M7 PR-2: injection-recovery BEYOND the single-blackbody family.

M6 Sec 3.4 stated the limit precisely: "an injection-recovery test measures the
pipeline against its own model."  M6's completeness -- 45.8% in-grid at
|b| > 30%, a gamma cliff below 0.05 and a hard temperature wall at 1000 K --
rests on ONE family: a single blackbody shell around a main-sequence
photosphere, which is exactly what the selection's own forward model assumes.
This measures how much the completeness function moves when the injected SED
is something the fit CANNOT represent.

    python scripts/m7_injection_families.py run    --per-cell 50 --jobs 6
    python scripts/m7_injection_families.py report

TWO PHYSICALLY DISTINCT FAMILIES (M7 PR-2, fixed before the run).

  1. TWO-TEMPERATURE SHELL.  The reprocessed luminosity is split between a warm
     and a cool blackbody, f_warm in {0.3, 0.5, 0.7} of the total, with
     T_cool = T_warm / 3 -- a radially extended shell rather than one radius.
     No single blackbody in the fit's grid can represent the curvature.
  2. OPTICALLY-THIN DUST EMISSION.  The standard modified blackbody
     f_nu ~ nu^beta B_nu(T), beta in {1, 2}, the emissivity law for
     astronomical silicate / graphite grains.  Broader on the Rayleigh-Jeans
     side than any blackbody -- which is the part of the SED W3 and W4 sample.

THE AXIS IS HELD FIXED SO THE COMPARISON MEANS SOMETHING.  Both families are
parameterised by the SAME bolometric covering fraction gamma = L_reprocessed /
L_star and carry the SAME Suazo Eq. 3 obscuration dimming.  The temperature
axis, the gamma axis, the six |b| bands, the real hosts and the per-band
uncertainties drawn at the INJECTED brightness are all M6 Sec 3's, unchanged.
Everything is pushed through the UNMODIFIED pipeline: same fit_ds, same
gamma >= 0.10 grid, same RMSE <= 0.2, same extra cuts, same S/N >= 3.5.

THE CONTROL, AND IT IS A FALSIFIER.  beta = 0 and f_warm = 1.0 both reduce
ANALYTICALLY to M6's single blackbody.  The reduction is checked to machine
precision against `w1_selection.ds_absolute_mags`, and the beta = 0 family is
run through the whole pipeline and must reproduce M6's own recovery rates
within Monte-Carlo error.  If it does not, the new generator is wrong and the
family comparison is void.
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
INJ = ROOT / "data" / "injection"
INJ.mkdir(parents=True, exist_ok=True)

from m6_injection import (BBANDS, GAMMAS, GAMMA_FLOOR, SIG_FIXED,  # noqa: E402
                          TDS, WBANDS, _fit_chunk, _init, bband_index,
                          build_noise_tables, load_parent, sample_sigma)

SEED = 20260825                     # PR-2's seed, fixed before the run
F_WARM = (0.3, 0.5, 0.7)            # two-temperature splits
BETAS = (1.0, 2.0)                  # optically-thin emissivity indices
T_RATIO = 3.0                       # T_cool = T_warm / T_RATIO
M6_INGRID_B30 = 0.4585              # M6 Sec 3.3, the number this is measured against
DELTA_TRIGGER = 5.0                 # PR-2: |Delta| >= 5 points => catalogue v3


# ----------------------------------------------------- the two generators --
def modbb_absolute_mags(T, gamma, logl, beta):
    """Optically-thin dust: f_nu ~ nu^beta B_nu(T), normalised bolometrically.

    The bolometric flux is gamma * L / (4 pi d^2) at d = 10 pc, exactly as
    `w1_selection.ds_absolute_mags` does for a blackbody, so gamma means the
    same thing in both families.  The normalisation is analytic:

        int nu^beta B_nu dnu = (2h/c^2) (kT/h)^(4+beta) Gamma(4+b) zeta(4+b)

    which at beta = 0 reduces to sigma T^4 / pi -- the control.
    """
    from scipy.special import gamma as G, zeta
    from w1_selection import BANDS, LAM_UM, ZP_JY
    L_SUN, PC = 3.828e26, 3.0857e16
    C, H, KB = 2.99792458e8, 6.62607015e-34, 1.380649e-23
    T = np.maximum(np.asarray(T, float), 1.0)
    F_bol = np.asarray(gamma, float) * (10.0 ** np.asarray(logl, float)) \
        * L_SUN / (4 * np.pi * (10 * PC) ** 2)
    norm = (2 * H / C ** 2) * (KB * T / H) ** (4 + beta) \
        * float(G(4 + beta)) * float(zeta(4 + beta))
    out = {}
    for b in BANDS:
        nu = C / (LAM_UM[b] * 1e-6)
        bnu = 2 * H * nu ** 3 / C ** 2 / np.expm1(H * nu / (KB * T))
        fnu = F_bol * (nu ** beta * bnu) / norm            # W/m2/Hz
        with np.errstate(divide="ignore"):
            out[b] = -2.5 * np.log10((fnu / 1e-26) / ZP_JY[b])
    return out


def twotemp_absolute_mags(t_warm, gamma, logl, f_warm):
    """Two blackbodies at T_warm and T_warm/3 sharing the same total gamma."""
    from w1_selection import combine, ds_absolute_mags
    t_warm = np.asarray(t_warm, float)
    g = np.asarray(gamma, float)
    warm = ds_absolute_mags(t_warm, g * f_warm, logl)
    if f_warm >= 1.0:
        return warm
    cool = ds_absolute_mags(t_warm / T_RATIO, g * (1.0 - f_warm), logl)
    return {b: combine(warm[b], cool[b]) for b in warm}


def sed_mags(family, T, gamma, logl, par):
    if family == "single_bb":
        from w1_selection import ds_absolute_mags
        return ds_absolute_mags(T, gamma, logl)
    if family == "two_temp":
        return twotemp_absolute_mags(T, gamma, logl, par)
    if family == "modbb":
        return modbb_absolute_mags(T, gamma, logl, par)
    raise ValueError(family)


def control_identity() -> dict:
    """PR-2's falsifier, the analytic half: beta = 0 and f_warm = 1 must equal
    `ds_absolute_mags` to machine precision."""
    from w1_selection import BANDS, ds_absolute_mags
    T = np.array([100.0, 300.0, 700.0, 1000.0])
    g = np.array([0.05, 0.10, 0.30, 0.50])
    ll = np.array([-0.4, 0.0, 0.4, 0.8])
    ref = ds_absolute_mags(T, g, ll)
    b0 = modbb_absolute_mags(T, g, ll, 0.0)
    tw = twotemp_absolute_mags(T, g, ll, 1.0)
    d0 = max(float(np.nanmax(np.abs(b0[b] - ref[b]))) for b in BANDS)
    d1 = max(float(np.nanmax(np.abs(tw[b] - ref[b]))) for b in BANDS)
    # PR-2 said "machine precision".  The measured residual on the beta = 0
    # arm is 8.03e-08 mag and it is NOT in the new generator: it is the
    # truncated Stefan-Boltzmann constant inside the PRE-EXISTING
    # `w1_selection.ds_absolute_mags` (SB = 5.670374e-8 against the
    # CODATA-derived 5.670374419184e-8, a relative 7.393e-08, which is exactly
    # 8.026e-08 mag).  The tolerance is therefore stated as 1e-6 mag -- five
    # millionths of the 0.2 mag RMSE gate -- and the reason is recorded rather
    # than the number quietly moved.  The f_warm = 1 arm is exact at 0.0.
    return {"max_abs_mag_diff_modbb_beta0_vs_single_bb": d0,
            "max_abs_mag_diff_twotemp_fwarm1_vs_single_bb": d1,
            "tolerance_mag": 1e-6,
            "residual_traced_to": "w1_selection.py SB = 5.670374e-8 vs CODATA "
                                  "5.670374419184e-8 (relative 7.393e-08 = "
                                  "8.026e-08 mag); the new generator is not "
                                  "the source",
            "machine_precision_pass": bool(d0 < 1e-6 and d1 < 1e-6)}


# -------------------------------------------------------------------- run --
def cmd_run(a) -> None:
    from w1_selection import combine, template_grid, load_pm13, use_locus
    ident = control_identity()
    print("PR-2 analytic control: %s" % json.dumps(ident))
    if not ident["machine_precision_pass"]:
        raise SystemExit("PR-2's analytic control FAILED -- generator is wrong")

    use_locus(a.locus)
    pm = load_pm13()
    parent = load_parent()
    parent["_bi"] = bband_index(parent["abs_b"].to_numpy())
    parent = parent[parent["_bi"] >= 0].reset_index(drop=True)
    print("parent pool: %d rows" % len(parent))
    noise = build_noise_tables(parent)

    arms = ([("single_bb", 0.0)]                        # the run-through control
            + [("two_temp", f) for f in F_WARM]
            + [("modbb", b) for b in BETAS])
    rng = np.random.default_rng(SEED)
    rows, i = [], 0
    t0 = time.time()
    for family, par in arms:
        for k in range(len(BBANDS)):
            pool = parent[parent["_bi"] == k]
            if not len(pool):
                continue
            for g in GAMMAS:
                for T in TDS:
                    pick = pool.iloc[rng.integers(0, len(pool), a.per_cell)]
                    for _, h in pick.iterrows():
                        mg = float(h["M_G"])
                        tg = template_grid(pm, mg - 0.02, mg + 0.02, step=0.04)
                        j = int(np.argmin(np.abs(tg["M_G"] - mg)))
                        logl = np.array([tg["logL"][j]])
                        dsm = sed_mags(family, np.array([float(T)]),
                                       np.array([g]), logl, par)
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
                        rec.update(i=i, family=family, family_par=float(par),
                                   gamma_true=g, t_ds_true=float(T), bband=k,
                                   abs_b=float(h["abs_b"]), M_G=mg,
                                   dmod=float(h["dmod"]),
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
        print("  %-10s par=%-4.1f built (%d rows, %.0f s)"
              % (family, par, i, time.time() - t0), flush=True)

    df = pd.DataFrame(rows)
    work = [dict({b: r[b] - r["dmod"] for b in ("BP", "G", "RP", "J", "H", "Ks",
                                                "W1", "W2", "W3", "W4")},
                 i=int(r["i"])) for _, r in df.iterrows()]
    chunks = [work[x:x + 250] for x in range(0, len(work), 250)]
    print("fitting %d injections through the UNMODIFIED pipeline on %d "
          "process(es)..." % (len(work), a.jobs))
    results = []
    if a.jobs <= 1:
        _init(a.locus)
        for n, ch in enumerate(chunks):
            results += _fit_chunk(ch)
            if n % 40 == 0:
                print("  %d/%d (%.0f s)" % (len(results), len(work),
                                            time.time() - t0), flush=True)
    else:
        import multiprocessing as mp
        with mp.Pool(a.jobs, initializer=_init, initargs=(a.locus,)) as pool:
            for n, res in enumerate(pool.imap_unordered(_fit_chunk, chunks)):
                results += res
                if n % 40 == 0:
                    print("  %d/%d (%.0f s)" % (len(results), len(work),
                                                time.time() - t0), flush=True)
    fit = pd.DataFrame(results, columns=["i", "rmse", "t_ds_fit", "gamma_fit"])
    df = df.merge(fit, on="i", how="left")
    df["pass_rmse"] = (df["rmse"] <= 0.2) & ~df["undetected"]
    df["extra_ok"] = ((df["gvar"] < 2) & (df["ruwe"] < 1.4)
                      & (df["ext_flag"] == 0) & (df["classprob"] > 0.9))
    df["snr_ok"] = (df["snr3"] >= 3.5) & (df["snr4"] >= 3.5)
    df["recovered"] = df["pass_rmse"] & df["extra_ok"] & df["snr_ok"]
    p = INJ / "m7_injection_families.csv"
    df.to_csv(p, index=False)
    (OUT / "m7_injection_control_identity.json").write_text(
        json.dumps(ident, indent=2))
    print("%d injections, %.0f s -> %s" % (len(df), time.time() - t0, p.name))
    for (fam, par), g in df.groupby(["family", "family_par"]):
        print("  %-10s %-4.1f  RMSE gate %.1f%%  pre-visual %.1f%%"
              % (fam, par, 100 * g["pass_rmse"].mean(),
                 100 * g["recovered"].mean()))


# ----------------------------------------------------------------- report --
def cmd_report(a) -> None:
    df = pd.read_csv(INJ / "m7_injection_families.csv")
    ident = json.loads((OUT / "m7_injection_control_identity.json").read_text())
    out = {"n_injections": int(len(df)), "seed": SEED,
           "families": {"single_bb": "control; reduces to M6 Sec 3's family",
                        "two_temp": "f_warm in %s, T_cool = T_warm/%.0f"
                                    % (list(F_WARM), T_RATIO),
                        "modbb": "f_nu ~ nu^beta B_nu(T), beta in %s"
                                 % list(BETAS)},
           "gamma_axis": list(GAMMAS), "t_axis": list(TDS),
           "analytic_control": ident,
           "m6_reference_ingrid_b_gt_30": M6_INGRID_B30,
           "delta_trigger_points": DELTA_TRIGGER}

    def ingrid(d):
        return d[(d["gamma_true"] >= GAMMA_FLOOR) & (d["t_ds_true"] <= 700)]

    rows = []
    for (fam, par), g in df.groupby(["family", "family_par"]):
        ig = ingrid(g)
        hi = ig[ig["bband"] >= 4]
        core = ig[ig["bband"] == len(BBANDS) - 1]
        rows.append({
            "family": fam, "par": par, "n": int(len(g)), "n_ingrid": int(len(ig)),
            "ingrid_all_sky": float(ig["recovered"].mean()),
            "ingrid_rmse_gate": float(ig["pass_rmse"].mean()),
            "ingrid_b_gt_30": float(hi["recovered"].mean()),
            "ingrid_b_gt_50": float(core["recovered"].mean()),
            "delta_points_vs_M6": float(100 * (hi["recovered"].mean()
                                               - M6_INGRID_B30)),
            "undetected_ingrid": float(ig["undetected"].mean()),
            "full_space_b_gt_30": float(
                g[g["bband"] >= 4]["recovered"].mean())})
    hd = pd.DataFrame(rows)
    out["headline"] = json.loads(hd.to_json(orient="records"))
    hd.to_csv(OUT / "m7_injection_families_headline.csv", index=False)

    # the two walls, re-measured per family
    walls = []
    for (fam, par), g in df.groupby(["family", "family_par"]):
        for gam in GAMMAS:
            s = g[g["gamma_true"] == gam]
            walls.append({"family": fam, "par": par, "axis": "gamma",
                          "value": gam, "n": int(len(s)),
                          "rmse_gate": float(s["pass_rmse"].mean()),
                          "previsual": float(s["recovered"].mean())})
        for T in TDS:
            s = g[(g["t_ds_true"] == T) & (g["gamma_true"] >= GAMMA_FLOOR)]
            walls.append({"family": fam, "par": par, "axis": "t_ds",
                          "value": float(T), "n": int(len(s)),
                          "rmse_gate": float(s["pass_rmse"].mean()),
                          "previsual": float(s["recovered"].mean())})
    wl = pd.DataFrame(walls)
    wl.to_csv(OUT / "m7_injection_families_walls.csv", index=False)
    out["walls"] = json.loads(wl.to_json(orient="records"))

    # by |b| band, per family
    bb = df.groupby(["family", "family_par", "bband"]).agg(
        n=("recovered", "size"), rmse=("pass_rmse", "mean"),
        prev=("recovered", "mean"), undet=("undetected", "mean")).reset_index()
    bb.to_csv(OUT / "m7_injection_families_by_b.csv", index=False)
    out["by_b_band"] = json.loads(bb.to_json(orient="records"))

    # what the fit DOES with an SED it cannot represent
    mis = []
    for (fam, par), g in df.groupby(["family", "family_par"]):
        s = ingrid(g)
        s = s[s["pass_rmse"]]
        mis.append({"family": fam, "par": par, "n_passing": int(len(s)),
                    "median_rmse": float(s["rmse"].median()),
                    "median_t_fit_over_t_true": float(
                        (s["t_ds_fit"] / s["t_ds_true"]).median()),
                    "median_gamma_fit_over_gamma_true": float(
                        (s["gamma_fit"] / s["gamma_true"]).median())})
    ms = pd.DataFrame(mis)
    ms.to_csv(OUT / "m7_injection_families_bias.csv", index=False)
    out["parameter_bias_on_passing_objects"] = json.loads(
        ms.to_json(orient="records"))

    ctrl = hd[hd["family"] == "single_bb"]
    dmax = float(np.nanmax(np.abs(hd[hd["family"] != "single_bb"]
                                  ["delta_points_vs_M6"])))
    ctrl_delta = float(ctrl["delta_points_vs_M6"].iloc[0]) if len(ctrl) else np.nan
    out["verdict"] = {
        "run_through_control_ingrid_b_gt_30": (float(ctrl["ingrid_b_gt_30"].iloc[0])
                                               if len(ctrl) else None),
        "run_through_control_delta_points": ctrl_delta,
        "control_reproduces_M6": bool(abs(ctrl_delta) < 2.0),
        "max_abs_delta_points_new_families": dmax,
        "materially_family_dependent": bool(dmax >= DELTA_TRIGGER),
        "consequence": ("PR-2 fixed in advance: |Delta| >= %.0f points for "
                        "either new family means the completeness statement is "
                        "materially family-dependent and the catalogue is "
                        "re-issued as v3 with completeness stated per family; "
                        "below it, v2 stands and no v3 is issued."
                        % DELTA_TRIGGER)}
    (OUT / "m7_injection_families.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(hd.round(4).to_string(index=False))
    print("\nWALLS (in-grid gamma for the T axis)")
    print(wl.pivot_table(index=["axis", "value"],
                         columns=["family", "par"],
                         values="previsual").round(4).to_string())
    print("\nPARAMETER BIAS on objects the fit accepted")
    print(ms.round(3).to_string(index=False))
    print("\nVERDICT " + json.dumps(out["verdict"], indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--per-cell", type=int, default=50)
    r.add_argument("--jobs", type=int, default=6)
    r.add_argument("--locus", default="wise_locus_extended.csv")
    p = sub.add_parser("report")
    p.add_argument("--locus", default="wise_locus_extended.csv")
    a = ap.parse_args()
    {"run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
