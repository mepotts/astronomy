#!/usr/bin/env python3
"""M2 hardened sampling harness (pre-registered H-criteria, M2 doc section 1.3).

Wall-clock-bounded PTMCMC sampling as a sequence of resume-continued chunks:

- H1 wall-clock bound: chunks sized from measured throughput (~chunk_target_s
  each, iteration totals kept multiples of 1000 = isave); the run stops within
  one chunk of its budget. STOP file in the run dir (or a global STOP_ALL next
  to the manifests) aborts at the next chunk boundary; SIGTERM/SIGINT abort
  immediately (summary still written; at most one isave block of samples lost).
- H2 checkpoint/resume: PTMCMC resume=True replays the on-disk chain (cheap,
  no likelihood evals) rebuilding the adaptive-jump state, then continues.
  Chain files whose row count violates PTMCMC's alignment requirement
  (1 + k*(isave/thin) rows, e.g. after SIGKILL mid-write) are trimmed to the
  last valid block before resuming; malformed trailing lines are dropped.
- H3 summary-on-every-exit: <results>/<run_id>.summary.json is rewritten after
  every chunk and in a finally: block on every exit path, with state, exit
  reason, gate status, per-parameter medians/CIs, max lnL, and economics.
- H4 inventory: <results>/manifest/<run_id>.json heartbeat, updated per chunk
  (pid, state, elapsed, iterations, host load). Niceness is applied by the
  launcher (nice -n 19, OMP/BLAS threads pinned); the harness records it.

Convergence gate (pre-registered): raw post-burn iterations >= gate_raw
(burn = first 25%) AND per-parameter last-half vs full-chain median stability
within the tolerances supplied by the caller.
"""
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path

import numpy as np

ISAVE = 1000
THIN = 10
BLOCK = ISAVE // THIN  # valid chain files have 1 + k*BLOCK rows


class AbortRequested(Exception):
    pass


def _install_signal_handlers():
    def handler(signum, frame):
        raise AbortRequested(f"signal {signum}")
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, handler)


def _atomic_json(path: Path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2))
    os.replace(tmp, path)


def _loadavg():
    try:
        return float(open("/proc/loadavg").read().split()[0])
    except Exception:
        return None


def _chain_file(outdir: Path):
    cands = sorted(outdir.glob("chain_1*.txt"))
    return cands[0] if cands else None


def _trim_chain(outdir: Path, ncol: int):
    """Drop malformed trailing lines, then trim to 1 + k*BLOCK rows so
    PTMCMC's resume alignment check passes. Returns valid row count."""
    f = _chain_file(outdir)
    if f is None or not f.exists():
        return 0
    lines = f.read_text().splitlines()
    while lines and len(lines[-1].split()) != ncol:
        lines.pop()
    rows = len(lines)
    if rows == 0:
        f.unlink()
        return 0
    valid = ((rows - 1) // BLOCK) * BLOCK + 1
    if valid != rows:
        f.write_text("\n".join(lines[:valid]) + "\n")
    return valid


def _prior_draw_factory(pta, par_names, tag):
    """Self-contained single-parameter prior-draw jump proposal.

    Replaces enterprise_extensions.sampler.JumpProposal draws, whose
    closures do float(array-of-size-1) and crash on numpy >= 2.x
    (e_e 3.0.3 + numpy 2.5.2 in this venv — measured, not assumed).
    All our parameters are scalars, so index arithmetic is direct.
    """
    pobj = {p.name: p for p in pta.params}
    items = [(pta.param_names.index(n), pobj[n]) for n in par_names
             if n in pobj]
    if not items:
        raise ValueError(f"no scalar params matched for block {tag}")

    def draw(x, iter, beta):
        q = x.copy()
        i, p = items[np.random.randint(len(items))]
        q[i] = p.sample()
        old = np.asarray(p.get_logpdf(float(x[i]))).ravel()
        new = np.asarray(p.get_logpdf(float(q[i]))).ravel()
        return q, float(old[0] - new[0])

    draw.__name__ = f"draw_prior_{tag}"
    return draw


def _summarize(chain, param_names, tolerances):
    """Medians/CIs, max lnL, stability check on the thinned chain."""
    ndim = len(param_names)
    rows = len(chain)
    burn = rows // 4
    post = chain[burn:, :ndim]
    lnlike = chain[:, ndim + 1]
    half = post[len(post) // 2:]
    params, stable = [], True
    for i, name in enumerate(param_names):
        med = float(np.median(post[:, i]))
        mh = float(np.median(half[:, i]))
        lo, hi = (float(np.percentile(post[:, i], q)) for q in (16, 84))
        tol = tolerances.get(name, 0.1)
        ok = abs(med - mh) <= tol
        stable &= ok
        params.append(dict(param=name, median=med, ci68=[lo, hi],
                           halfshift=round(abs(med - mh), 4),
                           tol=tol, stable=bool(ok)))
    return dict(rows=rows, post_burn_rows=len(post),
                raw_iters=(rows - 1) * THIN,
                raw_postburn=(len(post)) * THIN,
                lnl_max=float(np.max(lnlike)),
                acc_rate=float(chain[-1, ndim + 2]),
                stable=bool(stable), params=params)


def run(pta, run_id, results_dir, chains_dir, wall_min=480.0,
        gate_raw_postburn=100_000, tolerances=None, seed=1234,
        x0=None, x0_kind="prior-draw", chunk_target_s=600.0,
        meta=None, jump_blocks=None, max_raw_iters=4_000_000,
        cov_scale0=0.25, min_acc=0.05):
    """Run one wall-clock-bounded, resumable PTMCMC sampling campaign.

    Returns the final summary dict (also on disk however the run ends).
    """
    from PTMCMCSampler.PTMCMCSampler import PTSampler
    from enterprise_extensions.sampler import get_parameter_groups

    _install_signal_handlers()
    results_dir = Path(results_dir)
    chains_dir = Path(chains_dir)
    outdir = chains_dir / run_id
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_dir = results_dir / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / f"{run_id}.summary.json"
    manifest_path = manifest_dir / f"{run_id}.json"
    stop_local = outdir / "STOP"
    stop_global = manifest_dir / "STOP_ALL"

    tolerances = tolerances or {}
    ndim = len(pta.params)
    ncol = ndim + 4
    param_names = list(pta.param_names)
    groups = get_parameter_groups(pta)
    proposals = [(_prior_draw_factory(pta, param_names, "all"), 10)]
    for blkname, parlist in (jump_blocks or {}).items():
        proposals.append((_prior_draw_factory(pta, parlist, blkname), 5))

    np.random.seed(seed % (2**32 - 1))
    rng = np.random.default_rng(seed)
    if x0 is None:
        x0 = np.hstack([p.sample() for p in pta.params])

    # measured single-eval cost (also warms enterprise caches)
    t0 = time.perf_counter()
    pta.get_lnlikelihood(x0)
    t_first = time.perf_counter() - t0
    evals = []
    for _ in range(5):
        x = np.hstack([p.sample() for p in pta.params])
        t0 = time.perf_counter()
        pta.get_lnlikelihood(x)
        evals.append(time.perf_counter() - t0)
    t_eval = float(np.median(evals))

    state = dict(
        run_id=run_id, state="running", exit_reason=None, error=None,
        pid=os.getpid(), seed=seed, ndim=ndim, x0_kind=x0_kind,
        x0=[float(v) for v in x0],
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        wall_budget_min=wall_min, gate_raw_postburn=gate_raw_postburn,
        nice=os.nice(0), omp_threads=os.environ.get("OMP_NUM_THREADS"),
        min_acc=min_acc, cov_scale0=cov_scale0,
        eval_ms=round(t_eval * 1e3, 2), first_eval_s=round(t_first, 2),
        meta=meta or {}, chunks=[], gate_met=False, chain=None,
    )

    def flush(reason=None, err=None):
        state["exit_reason"] = reason
        state["error"] = err
        state["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime())
        _atomic_json(summary_path, state)
        _atomic_json(manifest_path, dict(
            run_id=run_id, pid=state["pid"], state=state["state"],
            exit_reason=reason, started=state["started_utc"],
            updated=state["updated_utc"], wall_budget_min=wall_min,
            elapsed_min=round(sum(c["seconds"] for c in state["chunks"]) / 60,
                              1),
            raw_iters=(state["chain"] or {}).get("raw_iters", 0),
            gate_met=state["gate_met"], eval_ms=state["eval_ms"],
            psr=(meta or {}).get("psr"), kind=(meta or {}).get("kind"),
            loadavg=_loadavg(),
        ))

    flush()
    t_start = time.perf_counter()
    sustained = 1.0 / t_eval  # it/s, refined per chunk
    exit_reason = None
    err_txt = None

    try:
        while True:
            elapsed = time.perf_counter() - t_start
            remaining = wall_min * 60.0 - elapsed

            rows = _trim_chain(outdir, ncol)
            done_raw = max(0, (rows - 1) * THIN)

            # min_acc added AFTER M2's campaign (M2 doc 5.1): a frozen chain
            # (acc 0.016) passed the raw-iteration + median-stability gate
            # because not moving is maximally "stable". M2's reported
            # verdicts stand as pre-registered; this protects later runs.
            if state["chain"] and state["chain"]["stable"] \
                    and state["chain"]["acc_rate"] >= min_acc \
                    and state["chain"]["raw_postburn"] >= gate_raw_postburn:
                state["gate_met"] = True
                exit_reason = "gate_met"
                break
            if done_raw >= max_raw_iters:
                exit_reason = "max_iters"
                break
            if remaining < 60.0:
                exit_reason = "wall_clock"
                break
            if stop_local.exists() or stop_global.exists():
                exit_reason = ("stop_file" if stop_local.exists()
                               else "stop_all")
                break

            chunk_s = min(chunk_target_s, remaining - 30.0)
            chunk_iters = int(max(1, round(chunk_s * sustained / 1000.0))
                              ) * 1000
            niter_target = done_raw + chunk_iters
            # keep totals multiples of ISAVE so clean chunk ends stay aligned
            niter_target = int(np.ceil(niter_target / ISAVE)) * ISAVE

            resume = rows > 0
            cov_path = outdir / "cov.npy"
            if resume and cov_path.exists():
                cov = np.load(cov_path)
            else:
                # cov_scale0 sets the initial jump scale as a fraction of the
                # prior std; fixed-white FL posteriors are far tighter than
                # priors and need ~0.05 (measured: 0.25 froze J1909's FL
                # chain at acceptance 0.016).
                draws = np.array([[p.sample() for p in pta.params]
                                  for _ in range(200)])
                cov = np.diag((cov_scale0 * draws.std(axis=0)) ** 2 + 1e-12)

            sampler = PTSampler(ndim, pta.get_lnlikelihood, pta.get_lnprior,
                                cov=cov, groups=groups, outDir=str(outdir),
                                resume=resume,
                                seed=int(rng.integers(0, 2**31)),
                                verbose=False)
            for func, weight in proposals:
                sampler.addProposalToCycle(func, weight)

            t_c = time.perf_counter()
            sampler.sample(x0, niter_target, SCAMweight=30, AMweight=15,
                           DEweight=50, burn=10_000, isave=ISAVE, thin=THIN)
            dt = time.perf_counter() - t_c
            new_iters = niter_target - done_raw
            sustained = max(new_iters / dt, 1e-3)

            state["chunks"].append(dict(
                iters=new_iters, seconds=round(dt, 1),
                it_per_s=round(sustained, 2), loadavg=_loadavg(),
                total_raw=niter_target))

            chain = np.loadtxt(_chain_file(outdir), ndmin=2)
            state["chain"] = _summarize(chain, param_names, tolerances)
            flush()

    except AbortRequested as e:
        exit_reason = f"abort:{e}"
    except Exception:
        exit_reason = "error"
        err_txt = traceback.format_exc()
    finally:
        try:
            # recompute from disk on every exit path (kills, errors included)
            f = _chain_file(outdir)
            if f is not None:
                rows = _trim_chain(outdir, ncol)
                if rows > 4:
                    chain = np.loadtxt(f, ndmin=2)
                    state["chain"] = _summarize(chain, param_names,
                                                tolerances)
                    if state["chain"]["stable"] \
                            and state["chain"]["acc_rate"] >= min_acc \
                            and state["chain"]["raw_postburn"] >= gate_raw_postburn:
                        state["gate_met"] = True
        except Exception:
            err_txt = (err_txt or "") + "\n" + traceback.format_exc()
        state["state"] = "done" if exit_reason in (
            "gate_met", "wall_clock", "max_iters") else "aborted" \
            if exit_reason and exit_reason.startswith(
                ("abort", "stop")) else "error" \
            if exit_reason == "error" else "done"
        state["elapsed_min"] = round((time.perf_counter() - t_start) / 60, 1)
        flush(exit_reason, err_txt)

    return state
