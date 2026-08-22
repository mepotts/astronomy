#!/usr/bin/env python3
"""M3 single-run driver: one of the 83 MPTA pulsars, one model variant,
under the M2-hardened harness (scripts/mpta_harness.py, acceptance floor
included). Pre-registered criteria: pta-mpta/M3-noise-criticism.md section 1.

Variants (scripts/mpta_models3.py):
  noise  favoured model, everything sampled  -> the published-table comparison
  table  favoured model, whites fixed        -> seam-(b) control
  fl     favoured + free red, whites fixed   -> the collaboration's CURN config

Usage (inside the WSL venv; launched by scripts/m3_campaign.sh):
    python scripts/m3_run.py J1909-3744 --variant noise --tag n1 \
        --wall-min 240 --gate 100000 --seed 101
    python scripts/m3_run.py J1909-3744 --variant fl --tag f1 \
        --whites-from results/m3/J1909-3744_noise_n1.summary.json
    python scripts/m3_run.py J1909-3744 --bench-only
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PARTIM = REPO / "data" / "partim"
TDBDIR = REPO / "data" / "partim_tdb"
CHAINS = REPO / "chains" / "m3"
RESULTS = REPO / "results" / "m3"
FIGURES = REPO / "figures"

sys.path.insert(0, str(Path(__file__).parent))
import mpta_models3 as M  # noqa: E402


def jump_blocks_for(pta, psr):
    """Per-signal prior-draw jump blocks (the M2 mode-hopping proposals)."""
    blocks = {}
    for stem in ("dm_gp", "chrom_gp", "red_gp", "gw13", "bump", "annual"):
        names = [p for p in pta.param_names if f"_{stem}_" in p
                 or p.replace(f"{psr}_", "").startswith(stem)]
        if names:
            blocks[stem] = names
    sw = [p for p in pta.param_names if "sw_gp" in p or p == "n_earth"]
    if sw:
        blocks["sw"] = sw
    return blocks


def whites_from_summary(path, psr):
    s = json.loads(Path(path).read_text())
    out = {}
    for r in s["chain"]["params"]:
        key = M.map_param(r["param"], psr)
        if key in ("efac", "log10_tnequad", "log10_ecorr"):
            out[key] = r["median"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psr")
    ap.add_argument("--variant", choices=["noise", "table", "fl"],
                    default="noise")
    ap.add_argument("--tag", default="n1")
    ap.add_argument("--wall-min", type=float, default=240.0)
    ap.add_argument("--gate", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--whites-from", default=None)
    ap.add_argument("--chunk-min", type=float, default=10.0)
    ap.add_argument("--cov-scale0", type=float, default=None,
                    help="default 0.25 sampled-white / 0.05 fixed-white")
    ap.add_argument("--min-acc", type=float, default=0.05)
    ap.add_argument("--sw-gamma-prior", default=None,
                    help="lo,hi override for the SW GP spectral index "
                         "(post-hoc supplementary check, M3 section 6)")
    ap.add_argument("--bench-only", action="store_true")
    args = ap.parse_args()

    import mpta_harness as H

    run_id = f"{args.psr}_{args.variant}_{args.tag}"
    whites = None
    if args.variant in ("table", "fl"):
        if not args.whites_from:
            raise SystemExit(f"--whites-from required for {args.variant}")
        whites = whites_from_summary(args.whites_from, args.psr)

    t0 = time.perf_counter()
    swg = (tuple(float(x) for x in args.sw_gamma_prior.split(","))
           if args.sw_gamma_prior else None)
    pta, meta = M.build_pta(args.psr, str(TDBDIR), str(PARTIM),
                            variant=args.variant, whites=whites,
                            sw_gamma_prior=swg)
    meta["build_s"] = round(time.perf_counter() - t0, 1)
    meta["kind"] = args.variant
    meta["whites_fixed"] = whites
    print(f"[model] {run_id}: ndim={len(pta.params)} "
          f"ntoa={meta['ntoa']} build={meta['build_s']}s")

    if args.bench_only:
        x = np.hstack([p.sample() for p in pta.params])
        pta.get_lnlikelihood(x)
        ts = []
        for _ in range(5):
            x = np.hstack([p.sample() for p in pta.params])
            t = time.perf_counter()
            pta.get_lnlikelihood(x)
            ts.append(time.perf_counter() - t)
        rec = dict(psr=args.psr, variant=args.variant, ndim=len(pta.params),
                   ntoa=meta["ntoa"], eval_ms=round(np.median(ts) * 1e3, 2),
                   build_s=meta["build_s"],
                   params=list(pta.param_names))
        d = RESULTS / "bench"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{args.psr}_{args.variant}.json").write_text(
            json.dumps(rec, indent=1))
        print(f"[bench] {args.psr} {args.variant}: {rec['eval_ms']} ms/eval, "
              f"ndim={rec['ndim']}")
        return

    tolerances = {p: M.stability_tol(p, args.psr, meta["tspan_days"])
                  for p in pta.param_names}
    cov0 = args.cov_scale0
    if cov0 is None:
        cov0 = 0.05 if args.variant in ("table", "fl") else 0.25

    RESULTS.mkdir(parents=True, exist_ok=True)
    state = H.run(pta, run_id, RESULTS, CHAINS,
                  wall_min=args.wall_min, gate_raw_postburn=args.gate,
                  tolerances=tolerances, seed=args.seed,
                  chunk_target_s=args.chunk_min * 60.0, meta=meta,
                  jump_blocks=jump_blocks_for(pta, args.psr),
                  cov_scale0=cov0, min_acc=args.min_acc)

    f = H._chain_file(CHAINS / run_id)
    if f is None:
        print("[post] no chain produced")
        return
    chain = np.loadtxt(f, ndmin=2)
    ndim = len(pta.params)
    post = chain[len(chain) // 4:, :ndim]
    lnlike = chain[:, ndim + 1]
    ib = int(np.argmax(lnlike))
    state["best_point"] = {k: float(v) for k, v in
                           zip(pta.param_names, chain[ib, :ndim])}
    state["lnl_best"] = float(lnlike[ib])

    # every variant carries the 13/3 amplitude -> always save its marginal
    i_gw = [i for i, p in enumerate(pta.param_names)
            if p.endswith("gw13_log10_A")][0]
    samp = post[:, i_gw]
    np.save(RESULTS / f"{run_id}.curn.npy", samp.astype(np.float32))
    state["curn"] = dict(median=float(np.median(samp)),
                         ci68=[float(np.percentile(samp, 16)),
                               float(np.percentile(samp, 84))],
                         n=int(len(samp)))

    if args.variant == "noise":
        rows, n_agree, n_comp = M.a2_compare(pta, args.psr, post)
        gate = state.get("gate_met", False)
        verdict = (("CONVERGED-" if gate else "NOT-CONVERGED(A3)-")
                   + ("AGREES" if n_agree == n_comp else "PARTIAL")
                   + f" {n_agree}/{n_comp}")
        state.update(a2=rows, n_agree=n_agree, n_compared=n_comp,
                     verdict=verdict)
        # save the full post-burn posterior for the seam analyses
        np.save(RESULTS / f"{run_id}.post.npy", post.astype(np.float32))
        state["param_names"] = list(pta.param_names)
        print(f"[verdict] {run_id}: {verdict}")
    else:
        print(f"[{args.variant}] {run_id}: log10_A_13/3 median "
              f"{state['curn']['median']:.3f} CI {state['curn']['ci68']}")

    H._atomic_json(RESULTS / f"{run_id}.summary.json", state)


if __name__ == "__main__":
    main()
