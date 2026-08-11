"""M14 warm-up: nested sampling (dynesty) on the Nature table — does M13 §5's flip survive?

M13 §5 re-ran the model comparison on the paper's own revised (Nature) RV table and the
second satellite's evidence flipped sign: BIC/2 proxy −0.51 where the paper claims
delta-logZ +2.622. The proxy caveat was stated up front: periods fixed, BIC/2, not an
evidence integral. This script computes the actual integral with dynesty.

The paper (Table 1): logZ = −144.323 ± 0.695 (1 sat) vs −141.701 ± 0.691 (2 sat),
both models full Keplerians (e free; the 2-sat posterior lands at e1=0.001, e2=0.008),
EMPEROR/reddemcee, sqrt(e)sin(omega)/sqrt(e)cos(omega) parameterization, windowed period
priors for the evidence comparison (sat 1 -> the long-period peak, sat 2 -> the 88-d window).

Variants here (likelihood identical to analysis/orbits.py: s2 = erv^2 + jit^2):

  fixP   1-sat ecc (P=171.112) vs 2-sat circ (P=171.454, 87.349) — the proxy's exact
         pairing, periods pinned at Table 1 values. Tests the −0.51 number directly.
  freeP  same pairing, periods free: P1 ~ U(150, 200), P2 ~ U(75, 100) — the paper's
         windowed-prior structure.
  eccP   both models full Keplerians with free periods — the paper's literal Table 1 pair.

Priors (identical across models wherever the parameter is shared, so the Occam terms
compare like with like): offset U(−600, 600); jitter log-U(0.1, 300); K U(0, 1000);
e U(0, 0.85) (the proxy's clip); omega U(0, 2pi); tp U(0, P).

Usage: python scripts/nested_orbits.py [--nlive 1000] [--seeds 2] [--out data/m14-nested.json]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", module=r"dynesty(\..*)?")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exosat_rv.analysis.aliases import keplerian_rv  # noqa: E402
from exosat_rv.analysis.orbits import load_published  # noqa: E402

TWO_PI = 2 * np.pi


PRIOR_STYLE = "default"   # "default" | "linjit" (jitter U(0,300)) | "logK" (K log-U(1,1000))


def make_model(periods_fixed, n_sats, eccentric):
    """Return (ndim, prior_transform, loglike, labels) for one model.

    periods_fixed: tuple of fixed periods, or None -> free with windowed priors.
    Parameter order: offset, log10(jitter), then per satellite:
      circular:   K, omega            (+ P if free)
      eccentric:  K, omega, e, tp_frac (+ P if free)
    tp is sampled as a fraction of that satellite's period so the prior volume
    is well-defined when P floats.
    """
    p_windows = [(150.0, 200.0), (75.0, 100.0)][:n_sats]
    labels = ["offset", "log10_jit"]
    for i in range(n_sats):
        if periods_fixed is None:
            labels.append(f"P{i + 1}")
        labels.append(f"K{i + 1}")
        labels.append(f"om{i + 1}")
        if eccentric:
            labels += [f"e{i + 1}", f"tpf{i + 1}"]
    ndim = len(labels)

    def prior_transform(u):
        x = np.empty_like(u)
        j = 0
        x[j] = -600 + 1200 * u[j]; j += 1                     # offset
        if PRIOR_STYLE == "linjit":
            x[j] = np.log10(max(300 * u[j], 1e-3)); j += 1    # jitter U(0,300), stored log10
        else:
            x[j] = -1 + (np.log10(300) + 1) * u[j]; j += 1    # log10 jitter in [-1, ~2.48]
        for i in range(n_sats):
            if periods_fixed is None:
                lo, hi = p_windows[i]
                x[j] = lo + (hi - lo) * u[j]; j += 1          # P
            if PRIOR_STYLE == "logK":
                x[j] = 10.0 ** (3.0 * u[j]); j += 1           # K log-U(1,1000)
            else:
                x[j] = 1000 * u[j]; j += 1                    # K
            x[j] = TWO_PI * u[j]; j += 1                      # omega
            if eccentric:
                x[j] = 0.85 * u[j]; j += 1                    # e
                x[j] = u[j]; j += 1                           # tp fraction of P
        return x

    def loglike(x):
        off, jit = x[0], 10.0 ** x[1]
        model = np.full_like(TT, off)
        j = 2
        for i in range(n_sats):
            if periods_fixed is None:
                period = x[j]; j += 1
            else:
                period = periods_fixed[i]
            k, om = x[j], x[j + 1]; j += 2
            if eccentric:
                e, tpf = x[j], x[j + 1]; j += 2
                model = model + keplerian_rv(TT, period, k, e, om, tpf * period)
            else:
                model = model + keplerian_rv(TT, period, k, 0.0, om, 0.0)
        s2 = ERV**2 + jit**2
        return -0.5 * float(np.sum((RV - model) ** 2 / s2 + np.log(TWO_PI * s2)))

    return ndim, prior_transform, loglike, labels


VARIANTS = {
    # name -> (model_one, model_two); each model = (periods_fixed, n_sats, eccentric)
    "fixP": (((171.112,), 1, True), ((171.454, 87.349), 2, False)),
    "freeP": ((None, 1, True), (None, 2, False)),
    "eccP": ((None, 1, True), (None, 2, True)),
}


def run_one(spec, nlive, seed, sample="rwalk"):
    import dynesty

    ndim, ptf, lnl, labels = make_model(*spec)
    rstate = np.random.default_rng(seed)
    t0 = time.time()
    sam = dynesty.NestedSampler(lnl, ptf, ndim, nlive=nlive, rstate=rstate,
                                sample=sample)
    sam.run_nested(dlogz=0.01, print_progress=False)
    res = sam.results
    w = np.exp(res.logwt - res.logz[-1])
    mean = np.einsum("i,ij->j", w, res.samples)
    return dict(logz=float(res.logz[-1]), logzerr=float(res.logzerr[-1]),
                ndim=ndim, nlive=nlive, seed=seed, ncall=int(np.sum(res.ncall)),
                secs=round(time.time() - t0, 1),
                post_mean={l: round(float(m), 4) for l, m in zip(labels, mean)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nlive", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1]
                                         / "data" / "m14-nested.json"))
    ap.add_argument("--variants", default="fixP,freeP,eccP")
    ap.add_argument("--sample", default="rwalk",
                    help="dynesty sample method: rwalk (robust) or unif")
    ap.add_argument("--priors", default="default", choices=["default", "linjit", "logK"])
    args = ap.parse_args()
    global PRIOR_STYLE
    PRIOR_STYLE = args.priors

    global TT, RV, ERV
    data = load_published(version="nature")
    TT = data.bjd - data.bjd.min()
    RV, ERV = data.rv, data.erv
    print(f"Nature table: n={len(RV)}, baseline {TT.max():.1f} d, "
          f"mean err {ERV.mean():.2f} m/s", flush=True)
    print("paper: logZ(1sat) = -144.323 +- 0.695, logZ(2sat) = -141.701 +- 0.691, "
          "dlogZ = +2.622", flush=True)

    out = {"paper": {"logz1": -144.323, "logz2": -141.701, "dlogz": 2.622},
           "n_epochs": len(RV), "runs": []}
    for name in args.variants.split(","):
        one, two = VARIANTS[name]
        for seed in range(args.seeds):
            r1 = run_one(one, args.nlive, 1000 + seed, args.sample)
            r2 = run_one(two, args.nlive, 2000 + seed, args.sample)
            d = r2["logz"] - r1["logz"]
            ed = float(np.hypot(r1["logzerr"], r2["logzerr"]))
            row = dict(variant=name, seed=seed, logz1=r1["logz"], logz2=r2["logz"],
                       e1=r1["logzerr"], e2=r2["logzerr"],
                       dlogz_two_minus_one=round(d, 3), e_dlogz=round(ed, 3),
                       detail={"one": r1, "two": r2})
            out["runs"].append(row)
            print(f"[{name} seed={seed}] logZ1={r1['logz']:.3f}+-{r1['logzerr']:.3f} "
                  f"({r1['secs']}s)  logZ2={r2['logz']:.3f}+-{r2['logzerr']:.3f} "
                  f"({r2['secs']}s)  dlogZ(2-1) = {d:+.3f} +- {ed:.3f}", flush=True)

    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
