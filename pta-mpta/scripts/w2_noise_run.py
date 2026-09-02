#!/usr/bin/env python3
"""W2 reproduction slice: single-pulsar noise analysis of MPTA pulsars with
enterprise + PTMCMC, compared against the published MPTA 4.5-yr noise table.

Pre-registered criteria: pta-mpta/M1-access-reproduction.md section 3 (A2/A3).
Published targets: arXiv:2412.01148 LaTeX source, Table "MPTA noise models"
(retrieved 2026-08-16 from https://arxiv.org/e-print/2412.01148).

Model conventions per the paper: 120 Fourier components for time-correlated
GPs; EFAC/EQUAD(tnequad)/ECORR(epoch-quantised, sub-bands correlated);
per-pulsar fixed-gamma=13/3 achromatic term with free amplitude; solar wind =
deterministic n_earth + SW perturbation GP; timing model marginalised; DE440.

Usage (inside the WSL venv):
    python scripts/w2_noise_run.py J2241-5236 --minutes 25
    python scripts/w2_noise_run.py J1909-3744 --minutes 60
    python scripts/w2_noise_run.py J1909-3744 --bench-only
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PARTIM = REPO / "data" / "partim"
TDBDIR = REPO / "data" / "partim_tdb"
CHAINS = REPO / "chains"
RESULTS = REPO / "results"
FIGURES = REPO / "figures"

# Published MAP (68% CI) values, arXiv:2412.01148 Table "MPTA noise models".
# CI stored as (lo_offset, hi_offset) as printed (sub/superscript).
PUBLISHED = {
    "J1909-3744": {
        "efac":          (1.04, -0.02, +0.00),
        "log10_tnequad": (-7.17, -0.03, -0.00),
        "log10_ecorr":   (-7.17, -0.06, +0.02),
        "dm_log10_A":    (-13.60, -0.07, +0.07),
        "dm_gamma":      (2.04, -0.18, +0.28),
        "sw_log10_A":    (-6.43, -0.19, +0.10),
        "sw_gamma":      (1.39, -0.42, +0.21),
        "gw13_log10_A":  (-14.28, -0.21, +0.17),
        "n_earth":       (4.96, -1.24, +0.86),
    },
    "J2241-5236": {
        "efac":          (1.05, -0.01, +0.01),
        "sw_log10_A":    (-6.16, -0.10, +0.06),
        "sw_gamma":      (1.81, -0.30, +0.18),
        "gw13_log10_A":  (-14.82, -1.57, +0.28),
        "n_earth":       (5.86, -2.32, +1.59),
    },
}

# Which components each pulsar's favoured model carries (from the same table).
MODEL_CFG = {
    "J1909-3744": dict(equad=True, ecorr=True, dm=True, sw=True),
    "J2241-5236": dict(equad=False, ecorr=False, dm=False, sw=True),
}

NCOMP = 120  # paper: "We thus chose 120 components"


def build_pta(psrname):
    import pint.logging
    pint.logging.setup(level="WARNING")
    from enterprise.pulsar import Pulsar
    from enterprise.signals import (gp_signals, parameter, signal_base,
                                    utils, white_signals)

    par = TDBDIR / f"{psrname}.tdb.par"
    if not par.exists():
        raise SystemExit(f"{par} missing -- run w1b_residuals.py {psrname} first")
    tim = PARTIM / f"{psrname}.tim"

    t0 = time.perf_counter()
    psr = Pulsar(str(par), str(tim), ephem="DE440", timing_package="pint")
    t_load = time.perf_counter() - t0
    print(f"[load] {psrname}: {len(psr.toas)} ToAs in {t_load:.1f} s")

    cfg = MODEL_CFG[psrname]
    Tspan = psr.toas.max() - psr.toas.min()

    # --- white noise ---
    efac = parameter.Uniform(0.1, 5.0)
    model = white_signals.MeasurementNoise(efac=efac)
    if cfg["equad"]:
        model += white_signals.TNEquadNoise(
            log10_tnequad=parameter.Uniform(-10, -5))
    if cfg["ecorr"]:
        model += white_signals.EcorrKernelNoise(
            log10_ecorr=parameter.Uniform(-10, -5))

    # --- DM GP (power law, 120 components, 1400 MHz reference basis) ---
    if cfg["dm"]:
        dm_basis = utils.createfourierdesignmatrix_dm(nmodes=NCOMP, Tspan=Tspan)
        dm_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                  gamma=parameter.Uniform(0, 7))
        model += gp_signals.BasisGP(dm_prior, dm_basis, name="dm_gp")

    # --- solar wind: deterministic n_earth + SW perturbation GP ---
    if cfg["sw"]:
        from enterprise_extensions.chromatic import solar_wind as sw_mod
        from enterprise.signals import deterministic_signals
        # paper model = Hazboun et al. 2022 (2022ApJ...929...39H), i.e. the
        # e_e solar_wind_block structure; n_earth prior = e_e default U(0,30);
        # linear-spaced harmonics (paper: "harmonically related sinusoids"),
        # not the e_e log-spaced default.
        n_earth = parameter.Uniform(0, 30)("n_earth")
        deter_sw = deterministic_signals.Deterministic(
            sw_mod.solar_wind(n_earth=n_earth), name="n_earth")
        model += deter_sw
        sw_basis = sw_mod.createfourierdesignmatrix_solar_dm(
            nmodes=NCOMP, Tspan=Tspan, logf=False)
        sw_prior = utils.powerlaw(log10_A=parameter.Uniform(-10, 1),
                                  gamma=parameter.Uniform(0, 7))
        model += gp_signals.BasisGP(sw_prior, sw_basis, name="sw_gp")

    # --- fixed-index achromatic term (the paper's A_13/3) ---
    gw13 = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                          gamma=parameter.Constant(13.0 / 3.0))
    model += gp_signals.FourierBasisGP(gw13, components=NCOMP, Tspan=Tspan,
                                       name="gw13")

    model += gp_signals.TimingModel(use_svd=True)

    pta = signal_base.PTA([model(psr)])
    print("[params]", *pta.param_names, sep="\n    ")
    return pta


def benchmark(pta, n=25):
    x0 = np.hstack([p.sample() for p in pta.params])
    t0 = time.perf_counter()
    pta.get_lnlikelihood(x0)
    t_first = time.perf_counter() - t0
    times = []
    for _ in range(n):
        x = np.hstack([p.sample() for p in pta.params])
        t0 = time.perf_counter()
        pta.get_lnlikelihood(x)
        times.append(time.perf_counter() - t0)
    med = float(np.median(times))
    print(f"[bench] first eval (cache build): {t_first:.2f} s; "
          f"steady-state median {med * 1e3:.1f} ms "
          f"=> {1.0 / med:.1f} evals/s")
    return t_first, med


def map_param(name, psrname):
    """enterprise param name -> published-table key."""
    n = name.replace(f"{psrname}_", "")
    table = {
        "efac": "efac",
        "log10_tnequad": "log10_tnequad",
        "log10_ecorr": "log10_ecorr",
        "dm_gp_log10_A": "dm_log10_A",
        "dm_gp_gamma": "dm_gamma",
        "sw_gp_log10_A": "sw_log10_A",
        "sw_gp_gamma": "sw_gamma",
        "gw13_log10_A": "gw13_log10_A",
        "n_earth": "n_earth",
    }
    return table.get(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psr", choices=sorted(PUBLISHED))
    ap.add_argument("--minutes", type=float, default=30.0,
                    help="sampling wall-clock budget (A3 cap: 90)")
    ap.add_argument("--bench-only", action="store_true")
    args = ap.parse_args()

    pta = build_pta(args.psr)
    t_first, t_eval = benchmark(pta)
    if args.bench_only:
        return

    from PTMCMCSampler.PTMCMCSampler import PTSampler

    ndim = len(pta.params)
    # PTMCMC writes every 10th step; target the wall-clock budget from the
    # measured eval rate (sampler overhead ~ small vs eval for these sizes).
    niter = int(args.minutes * 60 / t_eval)
    niter = max(niter, 2_000)  # tiny safeguard only; A3 wall-clock cap rules
    print(f"[plan] ndim={ndim}, budget {args.minutes:.0f} min "
          f"=> Niter ~ {niter:,}")

    x0 = np.hstack([p.sample() for p in pta.params])
    cov = np.diag(np.ones(ndim) * 0.01)
    outdir = CHAINS / args.psr
    sampler = PTSampler(ndim, pta.get_lnlikelihood, pta.get_lnprior,
                        cov=cov, outDir=str(outdir), resume=False)
    t0 = time.perf_counter()
    sampler.sample(x0, niter, SCAMweight=30, AMweight=15, DEweight=50)
    t_samp = time.perf_counter() - t0

    chain = np.loadtxt(outdir / "chain_1.txt")
    samples = chain[:, :ndim]
    nsamp = len(samples)
    burn = nsamp // 4
    post = samples[burn:]
    half = post[len(post) // 2:]

    # A3 convergence gate
    stable = True
    for i, pname in enumerate(pta.param_names):
        m_full, m_half = np.median(post[:, i]), np.median(half[:, i])
        tol = 0.3 if pname.endswith("gamma") or "n_earth" in pname else 0.1
        if abs(m_full - m_half) > tol:
            stable = False
    converged = (len(post) >= 5000) and stable

    # A2 comparison
    pub = PUBLISHED[args.psr]
    rows, n_agree, n_comp = [], 0, 0
    for i, pname in enumerate(pta.param_names):
        key = map_param(pname, args.psr)
        med = float(np.median(post[:, i]))
        lo, hi = (float(np.percentile(post[:, i], q)) for q in (16, 84))
        row = dict(param=pname, key=key, median=med, ci68=[lo, hi])
        if key and key in pub:
            pmap, plo, phi = pub[key]
            agree = (lo <= pmap <= hi) or (pmap + plo <= med <= pmap + phi)
            row.update(published_map=pmap,
                       published_ci=[pmap + plo, pmap + phi], agree=agree)
            n_comp += 1
            n_agree += agree
        rows.append(row)
        print(f"  {pname:35s} med {med:8.3f}  68% [{lo:8.3f},{hi:8.3f}]"
              + (f"  pub {row['published_map']:8.3f} "
                 f"[{row['published_ci'][0]:.3f},{row['published_ci'][1]:.3f}]"
                 f"  {'AGREE' if row['agree'] else 'DISAGREE'}"
                 if "agree" in row else ""))

    need = {"J1909-3744": 7, "J2241-5236": 4}[args.psr]
    verdict = ("NOT-CONVERGED -> feasibility result (A3)" if not converged
               else f"{'PASS' if n_agree >= need else 'FAIL'} "
                    f"(A2: {n_agree}/{n_comp} agree, need {need})")
    print(f"[A3] post-burn samples: {len(post)}, stable: {stable}, "
          f"converged: {converged}")
    print(f"[verdict] {verdict}")

    RESULTS.mkdir(exist_ok=True)
    summary = dict(
        pulsar=args.psr, ndim=ndim, niter=niter,
        thinned_samples=nsamp, post_burn=len(post),
        wallclock_s=round(t_samp, 1),
        eval_ms=round(t_eval * 1e3, 2), evals_per_s=round(1 / t_eval, 1),
        first_eval_s=round(t_first, 2),
        converged=bool(converged), n_agree=n_agree, n_compared=n_comp,
        need=need, verdict=verdict, params=rows,
        published_source="arXiv:2412.01148 Table 'MPTA noise models' "
                         "(LaTeX source, retrieved 2026-08-16)",
    )
    out = RESULTS / f"w2_{args.psr}_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"[saved] {out}")

    # corner plot of the compared parameters
    try:
        import corner
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        idx = [i for i, p in enumerate(pta.param_names)
               if map_param(p, args.psr) in pub]
        labels = [pta.param_names[i].replace(f"{args.psr}_", "")
                  for i in idx]
        fig = corner.corner(post[:, idx], labels=labels,
                            quantiles=[0.16, 0.5, 0.84], show_titles=True,
                            title_fmt=".2f", label_kwargs={"fontsize": 9})
        truths = []
        for i in idx:
            k = map_param(pta.param_names[i], args.psr)
            truths.append(pub[k][0])
        axes = np.array(fig.axes).reshape(len(idx), len(idx))
        for ii, t in enumerate(truths):
            for jj in range(ii + 1):
                axes[ii, jj].axvline(t, color="#C4552D", lw=1.2)
                if jj < ii:
                    axes[ii, jj].axhline(truths[jj] if False else t,
                                         lw=0)  # keep marks vertical-only
        FIGURES.mkdir(exist_ok=True)
        fig.savefig(FIGURES / f"w2_{args.psr}_corner.png", dpi=130)
        print(f"[saved] figures/w2_{args.psr}_corner.png")
    except Exception as e:  # corner is presentation, not acceptance
        print(f"[warn] corner plot skipped: {e}")


if __name__ == "__main__":
    main()
