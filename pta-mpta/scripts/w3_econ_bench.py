#!/usr/bin/env python3
"""Runtime-economics benchmark for W3 planning: measures the likelihood cost
of the configuration a full-PTA common-signal run actually uses -- white noise
FIXED (enterprise caches TNT), only GP hyperparameters free.

Measures, for one pulsar: (i) free-white eval cost (single-pulsar noise-run
regime, = W2), (ii) fixed-white eval cost (CURN-run regime), then projects
all-83 costs. Usage: python scripts/w3_econ_bench.py J1909-3744
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
TDBDIR = REPO / "data" / "partim_tdb"
PARTIM = REPO / "data" / "partim"
RESULTS = REPO / "results"


def build(psrname, fixed_white):
    import pint.logging
    pint.logging.setup(level="WARNING")
    from enterprise.pulsar import Pulsar
    from enterprise.signals import (gp_signals, parameter, signal_base,
                                    utils, white_signals)

    psr = Pulsar(str(TDBDIR / f"{psrname}.tdb.par"),
                 str(PARTIM / f"{psrname}.tim"),
                 ephem="DE440", timing_package="pint")
    Tspan = psr.toas.max() - psr.toas.min()

    if fixed_white:
        # J1909-3744 published MAP values, arXiv:2412.01148 noise table
        efac = parameter.Constant(1.04)
        equad = parameter.Constant(-7.17)
        ecorr = parameter.Constant(-7.17)
    else:
        efac = parameter.Uniform(0.1, 5.0)
        equad = parameter.Uniform(-10, -5)
        ecorr = parameter.Uniform(-10, -5)

    model = white_signals.MeasurementNoise(efac=efac)
    model += white_signals.TNEquadNoise(log10_tnequad=equad)
    model += white_signals.EcorrKernelNoise(log10_ecorr=ecorr)

    dm_basis = utils.createfourierdesignmatrix_dm(nmodes=120, Tspan=Tspan)
    dm_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                              gamma=parameter.Uniform(0, 7))
    model += gp_signals.BasisGP(dm_prior, dm_basis, name="dm_gp")

    crn = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                         gamma=parameter.Uniform(0, 7))
    model += gp_signals.FourierBasisGP(crn, components=120, Tspan=Tspan,
                                       name="red")
    model += gp_signals.TimingModel(use_svd=True)
    return signal_base.PTA([model(psr)]), len(psr.toas)


def bench(pta, n=40):
    x0 = np.hstack([p.sample() for p in pta.params])
    t0 = time.perf_counter()
    pta.get_lnlikelihood(x0)
    t_first = time.perf_counter() - t0
    ts = []
    for _ in range(n):
        x = np.hstack([p.sample() for p in pta.params])
        t0 = time.perf_counter()
        pta.get_lnlikelihood(x)
        ts.append(time.perf_counter() - t0)
    return t_first, float(np.median(ts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psr", default="J1909-3744", nargs="?")
    args = ap.parse_args()

    out = {}
    for mode, fixed in [("free_white", False), ("fixed_white", True)]:
        pta, ntoa = build(args.psr, fixed)
        t_first, t_med = bench(pta)
        out[mode] = dict(ntoa=ntoa, ndim=len(pta.params),
                         first_eval_s=round(t_first, 3),
                         eval_ms=round(t_med * 1e3, 2),
                         evals_per_s=round(1 / t_med, 1))
        print(f"[{mode}] ndim={len(pta.params)} first={t_first:.2f}s "
              f"median={t_med * 1e3:.1f}ms => {1 / t_med:.1f}/s")

    r = out["fixed_white"]["eval_ms"] / 1e3
    proj = dict(
        note="full-array CURN-run projection scaled from this pulsar's "
             "fixed-white eval; per-pulsar cost varies with ntoa and model",
        full_array_eval_s=round(83 * r, 2),
        iters_1e6_days=round(83 * r * 1e6 / 86400, 1),
    )
    out["projection"] = proj
    print(f"[projection] 83x fixed-white eval ~ {proj['full_array_eval_s']} "
          f"s/eval => 1M PTMCMC iters ~ {proj['iters_1e6_days']} days "
          f"(upper bound; see note)")
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"w3_econ_{args.psr}.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
