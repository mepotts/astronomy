#!/usr/bin/env python3
"""M2 single-run driver: one pulsar, noise-campaign or FL-CURN model, under
the hardened harness (scripts/mpta_harness.py). Pre-registered criteria:
pta-mpta/M2-converge-scale.md section 1.

Usage (inside the WSL venv; launched via scripts/m2_campaign.sh which sets
niceness and thread pinning):
    python scripts/m2_run.py J2241-5236 --kind noise --tag c1 \
        --wall-min 480 --gate 100000 --seed 101 --start prior
    python scripts/m2_run.py J1909-3744 --kind noise --tag informed \
        --start published
    python scripts/m2_run.py J1909-3744 --kind fl --tag fl1 \
        --whites-from results/m2/J1909-3744_noise_c1.summary.json
"""
import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PARTIM = REPO / "data" / "partim"
TDBDIR = REPO / "data" / "partim_tdb"
CHAINS = REPO / "chains" / "m2"
RESULTS = REPO / "results" / "m2"
FIGURES = REPO / "figures"

import sys
sys.path.insert(0, str(Path(__file__).parent))
import mpta_models as M


def jump_blocks_for(pta, psr):
    """Per-signal prior-draw jump blocks (mode-hopping proposals)."""
    blocks = {}
    for stem in ("dm_gp", "chrom_gp", "red_gp", "gw13", "bump", "annual"):
        names = [p for p in pta.param_names if f"_{stem}_" in p
                 or p.replace(f"{psr}_", "").startswith(stem)]
        if names:
            blocks[stem] = names
    sw = [p for p in pta.param_names
          if "sw_gp" in p or p == "n_earth"]
    if sw:
        blocks["sw"] = sw
    return blocks


def whites_from_summary(path, psr):
    s = json.loads(Path(path).read_text())
    rows = s["chain"]["params"]
    out = {}
    for r in rows:
        key = M.map_param(r["param"], psr)
        if key in ("efac", "log10_tnequad", "log10_ecorr"):
            out[key] = r["median"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psr", choices=M.TOP10)
    ap.add_argument("--kind", choices=["noise", "fl"], default="noise")
    ap.add_argument("--tag", default="c1")
    ap.add_argument("--wall-min", type=float, default=480.0)
    ap.add_argument("--gate", type=int, default=100_000,
                    help="raw post-burn iterations required (C1/F2)")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--start", choices=["prior", "published"],
                    default="prior")
    ap.add_argument("--whites-from", default=None,
                    help="noise summary JSON supplying fixed whites (FL)")
    ap.add_argument("--chunk-min", type=float, default=10.0)
    ap.add_argument("--cov-scale0", type=float, default=0.25,
                    help="initial jump scale as fraction of prior std")
    args = ap.parse_args()

    import mpta_harness as H

    run_id = f"{args.psr}_{args.kind}_{args.tag}"
    whites = None
    if args.kind == "fl":
        if not args.whites_from:
            raise SystemExit("--whites-from required for --kind fl")
        whites = whites_from_summary(args.whites_from, args.psr)
        print(f"[fl] whites fixed at campaign medians: {whites}")

    pta, meta = M.build_pta(args.psr, str(TDBDIR), str(PARTIM),
                            fl=(args.kind == "fl"), whites=whites)
    meta["kind"] = args.kind
    meta["whites_fixed"] = whites
    print(f"[model] {run_id}: ndim={len(pta.params)}")
    for p in pta.param_names:
        print(f"    {p}")

    tolerances = {p: M.stability_tol(p, args.psr, meta["tspan_days"])
                  for p in pta.param_names}

    x0, x0_kind = None, "prior-draw"
    if args.start == "published":
        x0, missing = M.published_vector(pta, args.psr)
        if x0 is None:
            raise SystemExit(f"no published value for {missing}; "
                             "--start published unavailable")
        x0_kind = "published-MAP"

    state = H.run(pta, run_id, RESULTS, CHAINS,
                  wall_min=args.wall_min, gate_raw_postburn=args.gate,
                  tolerances=tolerances, seed=args.seed, x0=x0,
                  x0_kind=x0_kind, chunk_target_s=args.chunk_min * 60.0,
                  meta=meta, jump_blocks=jump_blocks_for(pta, args.psr),
                  cov_scale0=args.cov_scale0)

    # ---- post-run: A2 comparison, best point, mode fraction, corner ----
    f = H._chain_file(CHAINS / run_id)
    if f is None:
        print("[post] no chain produced; nothing to compare")
        return
    chain = np.loadtxt(f, ndmin=2)
    ndim = len(pta.params)
    rows_n = len(chain)
    post = chain[rows_n // 4:, :ndim]
    lnlike = chain[:, ndim + 1]
    ib = int(np.argmax(lnlike))
    state["best_point"] = {k: float(v) for k, v in
                           zip(pta.param_names, chain[ib, :ndim])}
    state["lnl_best"] = float(lnlike[ib])

    if "n_earth" in pta.param_names:
        i_ne = pta.param_names.index("n_earth")
        state["frac_n_earth_lt_15"] = float(
            np.mean(post[:, i_ne] < 15.0))

    if args.kind == "noise":
        rows, n_agree, n_comp = M.a2_compare(pta, args.psr, post)
        full = (n_agree == n_comp)
        gate = state.get("gate_met", False)
        verdict = (("CONVERGED-" if gate else "NOT-CONVERGED(A3)-")
                   + ("AGREES" if full else "PARTIAL")
                   + f" {n_agree}/{n_comp}")
        state.update(a2=rows, n_agree=n_agree, n_compared=n_comp,
                     verdict=verdict)
        print(f"[verdict] {run_id}: {verdict}")
    else:
        i_gw = [i for i, p in enumerate(pta.param_names)
                if p.endswith("gw13_log10_A")][0]
        samp = post[:, i_gw]
        np.save(RESULTS / f"{run_id}.curn.npy", samp)
        state["curn"] = dict(
            median=float(np.median(samp)),
            ci68=[float(np.percentile(samp, 16)),
                  float(np.percentile(samp, 84))],
            n=len(samp))
        print(f"[fl] {run_id}: log10_A_CURN slice median "
              f"{state['curn']['median']:.2f} CI {state['curn']['ci68']}")

    H._atomic_json(RESULTS / f"{run_id}.summary.json", state)

    # corner plot of the compared parameters (presentation only)
    try:
        import corner
        import matplotlib
        matplotlib.use("Agg")
        pub = M.PUBLISHED[args.psr]
        idx = [i for i, p in enumerate(pta.param_names)
               if M.map_param(p, args.psr) in pub]
        if args.kind == "fl":
            idx = [i for i, p in enumerate(pta.param_names)]
        labels = [pta.param_names[i].replace(f"{args.psr}_", "")
                  for i in idx]
        sub = post[:, idx]
        fig = corner.corner(sub, labels=labels,
                            quantiles=[0.16, 0.5, 0.84], show_titles=True,
                            title_fmt=".2f", label_kwargs={"fontsize": 8})
        if args.kind == "noise":
            axes = np.array(fig.axes).reshape(len(idx), len(idx))
            for ii, i in enumerate(idx):
                t = pub[M.map_param(pta.param_names[i], args.psr)][0]
                for jj in range(ii + 1):
                    axes[ii, jj].axvline(t, color="#C4552D", lw=1.2)
        FIGURES.mkdir(exist_ok=True)
        fig.savefig(FIGURES / f"m2_{run_id}_corner.png", dpi=120)
        print(f"[saved] figures/m2_{run_id}_corner.png")
    except Exception as e:
        print(f"[warn] corner skipped: {e}")


if __name__ == "__main__":
    main()
