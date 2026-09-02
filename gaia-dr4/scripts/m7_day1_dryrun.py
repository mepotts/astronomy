#!/usr/bin/env python
"""M7 task 1: the DAY-ONE-SCALE DRY RUN of the epoch-vet harness.

M6 left the day-one clock as a BAND -- 125-857 sources/hour, the 981-row
queue in 1.1-7.9 h -- and said exactly why: its DataLink probe swept batch
SIZE, so source count and payload bytes moved together, and the two models
fitted to those calls

    A  transport-limited   t = 2.3 s + bytes / 1.8 KiB/s      (R2 0.934)
    B  per-source work     t = 6.0 s + 3.86 s * n_sources     (R2 0.917)

fit equally well and disagree only about the extrapolation to DR4's 6.8x
bigger payload.  A band is the honest answer to a degenerate design.  It is
not the honest answer to a design that can be de-degenerated, and this one
can: hold n_sources FIXED at the production batch size and vary payload
across batches.  Then A predicts a several-fold spread in request time and
B predicts a flat line, and one measurement chooses.

THREE PHASES, all anonymous, all polite, all through the production harness
(scripts/epoch_vet_harness.py -- same batching, same per-source atomic
parquet cache, same append-only ledger + resume, same 6x retry with
Retry-After, same per-batch checkpoint, same timings CSV):

  A  the literal ask: all 981 members of out/epoch_vet_day1_queue.v2.csv
     against DR3 EPOCH_PHOTOMETRY.  Exercises resume, the cache and the
     served-nothing path at real scale on the real queue.
  B  the payload-stratified control: 981 DR3 astrometric-binary sources
     that DO serve epoch photometry, arranged in payload-homogeneous
     batches of 20 cycling five transit-count strata.  This is the run
     that replaces the band with a number.
  C  the fit half, sustained: 981 consecutive gaiasupdate single-star fits
     over the real DR4 pre-release epoch astrometry, from cache.  M6
     measured 0.036 s/source over 22 fits in short probes; a day-one claim
     needs to know the fit does not drift or leak over hundreds of calls.

WHY A TRANSPORT REHEARSAL WRITES NO VERDICTS.  DR3 epoch photometry carries
no astrometric epochs, so there is no f2 and no adjudication is possible.
Writing a placeholder verdict into out/verdicts/ would be a provenance lie
in a schema whose entire purpose is provenance, so phases A and B write the
harness's TRANSPORT ledger (out/m7_dryrun/*.csv), which has its own columns
and lives outside the verdict store.  The resume contract is identical.

Run:
  .venv/Scripts/python.exe scripts/m7_day1_dryrun.py --phase A
  .venv/Scripts/python.exe scripts/m7_day1_dryrun.py --phase B
  .venv/Scripts/python.exe scripts/m7_day1_dryrun.py --phase C
  .venv/Scripts/python.exe scripts/m7_day1_dryrun.py --phase calib
"""
import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import epoch_vet_harness as H                                    # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out", "m7_dryrun")
SETA = os.path.join(OUT, "setA_queue981.csv")
SETB = os.path.join(OUT, "setB_payload_stratified981.csv")
TIMINGS = os.path.join(OUT, "m7_harness_timings.csv")
DR3_RELEASE = "Gaia DR3"


class PhotometryDataLinkSource(H.DataLinkSource):
    """DR3 EPOCH_PHOTOMETRY through the production DataLink fetch layer.

    Everything that matters for the rehearsal -- batching, the retry /
    backoff / Retry-After policy, the fail-fast on deterministic 500s -- is
    inherited verbatim from DataLinkSource._call_with_retries.  Only the
    product parser differs, because an epoch-photometry table is not an
    epoch-astrometry table and must not be pushed through gaiasupdate's
    astrometry adapter.
    """

    name = "gaia_datalink_photometry_dryrun"

    def __init__(self, release=DR3_RELEASE):
        super().__init__(release=release, retrieval_type="EPOCH_PHOTOMETRY")

    def _frames_from(self, res):
        frames = []
        for _key, val in (res or {}).items():
            for item in (val if isinstance(val, list) else [val]):
                try:
                    df = item.to_table().to_pandas()
                except AttributeError:
                    df = item.to_pandas()
                frames.append(df)
        return frames


def _phase_run(phase, queue, ids_note, batch, gap, limit, progress_every):
    ledger = os.path.join(OUT, f"transport_ledger_{phase}.csv")
    src = PhotometryDataLinkSource()
    print(f"=== PHASE {phase}: {ids_note}")
    print(f"    release '{src.release}', retrieval_type "
          f"'{src.retrieval_type}', batch {batch}, gap {gap}s")
    print(f"    ledger {os.path.relpath(ledger, BASE)} (transport, NOT a "
          f"verdict store file)")
    t0 = time.time()
    led, stats = H.run(source="datalink", epoch_source=src, queue=queue,
                       limit=limit, batch=batch, gap=gap,
                       ledger=ledger, timings=TIMINGS,
                       run_id=f"m7_dryrun_{phase}_"
                              f"{time.strftime('%Y%m%dT%H%M%S')}",
                       transport_only=True, progress_every=progress_every)
    stats["phase"] = phase
    stats["wall_minutes"] = round((time.time() - t0) / 60.0, 2)
    served = int(led["served"].astype(str).str.lower().isin(
        ["true", "1"]).sum()) if len(led) else 0
    stats["n_served"] = served
    stats["n_rows_total"] = int(pd.to_numeric(led["n_rows"],
                                              errors="coerce").fillna(0).sum())
    stats["cache_bytes_total"] = int(pd.to_numeric(
        led["cache_bytes"], errors="coerce").fillna(0).sum())
    print(f"    PHASE {phase} done: {len(led)} in ledger, {served} served, "
          f"{stats['n_rows_total']} rows, {stats['wall_minutes']:.1f} min")
    _append_stats(stats)
    return stats


def _append_stats(stats):
    """Append one run's stats, ALIGNING TO THE EXISTING HEADER.

    A plain `mode='a', header=False` write puts the new dict's values under
    the old file's column names positionally.  Phases A/B and phase C report
    different quantities, so the first phase-C append silently filed
    `n_fits` under `n_processed` and `wall_minutes` under `n_queued`.  Caught
    only because the resulting row was obvious nonsense; an appender that
    does not align columns is a data-corruption bug waiting for a run whose
    numbers happen to look plausible.
    """
    p = os.path.join(OUT, "m7_dryrun_runs.csv")
    df = pd.DataFrame([stats])
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        df.to_csv(p, index=False, lineterminator="\n")
        return
    old = pd.read_csv(p)
    cols = list(old.columns) + [c for c in df.columns
                                if c not in old.columns]
    if len(cols) != len(old.columns):
        pd.concat([old, df], ignore_index=True).reindex(
            columns=cols).to_csv(p, index=False, lineterminator="\n")
    else:
        df.reindex(columns=old.columns).to_csv(
            p, mode="a", header=False, index=False, lineterminator="\n")


def phase_C(n=981, seed=20261202):
    """The fit half, sustained: N consecutive single-star fits on real DR4
    pre-release epoch astrometry.  Answers the only question a short probe
    cannot: does the fit drift, slow, or leak over hundreds of calls?"""
    print(f"=== PHASE C: {n} sustained single-star fits (real DR4 "
          f"pre-release epoch astrometry, from cache)")
    src = H.PrereleaseSource()
    ids = src.all_ids()
    rng = np.random.default_rng(seed)
    order = [int(ids[i]) for i in rng.integers(0, len(ids), size=n)]
    cache = {sid: src.fetch([sid])[sid] for sid in ids}
    try:
        import psutil
        proc = psutil.Process()
    except Exception:                                            # noqa: BLE001
        proc = None
    rows, t0 = [], time.time()
    for k, sid in enumerate(order):
        t1 = time.time()
        res = H.fit_single_star(cache[sid], sid)
        dt = time.time() - t1
        rows.append({"i": k, "source_id": sid, "seconds": dt,
                     "f2": float(res["solution_statistic"].f2),
                     "n_used": int(res["n_measurements"]),
                     "rss_mb": (round(proc.memory_info().rss / 2**20, 1)
                                if proc else np.nan)})
        if k and k % 200 == 0:
            print(f"    {k}/{n} fits, {time.time()-t0:.0f}s elapsed",
                  flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "m7_fit_scale_test.csv"), index=False,
              lineterminator="\n")
    warm = df.iloc[1:]
    # drift: first vs last decile, and an OLS slope over the run
    d1 = warm.iloc[:len(warm) // 10]["seconds"].mean()
    d10 = warm.iloc[-len(warm) // 10:]["seconds"].mean()
    slope = np.polyfit(warm["i"], warm["seconds"], 1)[0]
    # determinism: the same source must give the same f2 every time
    g = df.groupby("source_id")["f2"].nunique()
    stats = {
        "phase": "C", "n_fits": len(df),
        "first_fit_seconds": round(float(df.iloc[0]["seconds"]), 4),
        "mean_seconds": round(float(warm["seconds"].mean()), 5),
        "median_seconds": round(float(warm["seconds"].median()), 5),
        "p90_seconds": round(float(warm["seconds"].quantile(0.9)), 5),
        "first_decile_mean": round(float(d1), 5),
        "last_decile_mean": round(float(d10), 5),
        "drift_seconds_per_1000_fits": round(float(slope * 1000), 5),
        "fits_per_hour": round(3600.0 / float(warm["seconds"].mean()), 0),
        "f2_unique_per_source_max": int(g.max()),
        "rss_start_mb": float(df.iloc[0]["rss_mb"]) if proc else None,
        "rss_end_mb": float(df.iloc[-1]["rss_mb"]) if proc else None,
        "wall_minutes": round((time.time() - t0) / 60.0, 2),
    }
    for k, v in stats.items():
        print(f"    {k}: {v}")
    _append_stats(stats)
    return stats


def phase_calib(n_batches=6, batch=20):
    """Rows -> wire bytes.  The harness measures served ROWS; M6's models
    are written in KiB.  This measures the conversion on the same service,
    by asking for the zip and weighing it (M6 landmine #8: astroquery writes
    it into the CWD, ignoring output_file -- so chdir)."""
    from astroquery.gaia import Gaia
    import tempfile
    b = pd.read_csv(SETB)
    print(f"=== PHASE calib: {n_batches} batches of {batch}, wire bytes vs "
          f"served rows")
    rows = []
    cwd = os.getcwd()
    tmp = tempfile.mkdtemp(prefix="m7_calib_")
    try:
        os.chdir(tmp)
        for k in range(n_batches):
            sel = b[b["batch_at_20"] == k * (50 // max(n_batches, 1))]
            ids = [int(x) for x in sel["source_id"].head(batch)]
            if not ids:
                continue
            before = set(os.listdir(tmp))
            t0 = time.time()
            Gaia.load_data(ids=ids, data_release=DR3_RELEASE,
                           retrieval_type="EPOCH_PHOTOMETRY",
                           data_structure="RAW", format="votable",
                           dump_to_file=True, verbose=False)
            dt = time.time() - t0
            new = [f for f in os.listdir(tmp) if f not in before]
            nbytes = sum(os.path.getsize(os.path.join(tmp, f)) for f in new)
            rows.append({"batch_at_20": int(sel["batch_at_20"].iloc[0]),
                         "n_ids": len(ids), "seconds": round(dt, 3),
                         "zip_bytes": nbytes,
                         "mean_transits": float(
                             sel["num_selected_g_fov"].head(batch).mean())})
            print(f"    calib {k}: {len(ids)} ids, {nbytes} B, {dt:.1f}s, "
                  f"mean transits {rows[-1]['mean_transits']:.0f}", flush=True)
            time.sleep(1.0)
    finally:
        os.chdir(cwd)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "m7_bytes_calibration.csv"), index=False,
              lineterminator="\n")
    print(df.to_string(index=False))
    return df


def phase_weather(n=60, every_s=120, batch=20):
    """Archive WEATHER: the same request, repeated across hours.

    M6's soak was five identical requests inside a few minutes and found a
    3.2x spread with no monotone trend -- enough to prove the archive is
    load-limited, not throttling us, but not enough to plan a day around.
    A day-one wall clock is an integral over hours of weather, so the
    distribution has to be sampled over hours.  One request every two
    minutes is two orders of magnitude below any plausible rate limit.
    """
    b = pd.read_csv(SETB)
    ids = [int(x) for x in b[b["batch_at_20"] == 22]["source_id"].head(batch)]
    src = PhotometryDataLinkSource()
    print(f"=== PHASE weather: {n} identical batch-{len(ids)} requests, one "
          f"every {every_s}s ({n*every_s/3600.0:.1f} h)")
    rows, t0 = [], time.time()
    p = os.path.join(OUT, "m7_archive_weather.csv")
    for k in range(n):
        t1 = time.time()
        status, cells = "OK", 0
        try:
            served = src.fetch(ids)
            cells = int(sum(H.payload_cells(d) for d in served.values()))
            nserved = len(served)
        except Exception as exc:                                 # noqa: BLE001
            status, nserved = f"{type(exc).__name__}: {str(exc)[:120]}", 0
        dt = time.time() - t1
        rows.append({"rep": k, "utc": H.vs.utcnow(),
                     "elapsed_min": round((time.time() - t0) / 60.0, 2),
                     "n_ids": len(ids), "n_served": nserved,
                     "n_cells": cells, "seconds": round(dt, 3),
                     "status": status})
        pd.DataFrame(rows).to_csv(p, index=False, lineterminator="\n")
        if k % 5 == 0:
            print(f"    weather {k}/{n}: {dt:.1f}s ({status}) at "
                  f"+{rows[-1]['elapsed_min']:.0f} min", flush=True)
        if k < n - 1:
            time.sleep(max(0.0, every_s - dt))
    df = pd.DataFrame(rows)
    ok = df[df["status"] == "OK"]["seconds"]
    print(f"    weather done: n={len(ok)} OK, min {ok.min():.1f}s, median "
          f"{ok.median():.1f}s, p90 {ok.quantile(0.9):.1f}s, max "
          f"{ok.max():.1f}s, spread {ok.max()/max(ok.min(),1e-9):.1f}x")
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--phase", required=True,
                    choices=["A", "B", "C", "calib", "weather", "AB", "all"])
    ap.add_argument("--weather-n", type=int, default=60)
    ap.add_argument("--weather-every", type=int, default=120)
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--gap", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--progress-every", type=int, default=5)
    ap.add_argument("--n-fits", type=int, default=981)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    os.makedirs(OUT, exist_ok=True)

    todo = {"AB": ["A", "B"], "all": ["A", "B", "C", "calib"]}.get(
        a.phase, [a.phase])
    for ph in todo:
        if ph == "A":
            _phase_run("A", SETA,
                       "all 981 day-one queue members (the literal ask)",
                       a.batch, a.gap, a.limit, a.progress_every)
        elif ph == "B":
            _phase_run("B", SETB,
                       "981 payload-stratified serving sources (the "
                       "degeneracy-breaker)",
                       a.batch, a.gap, a.limit, a.progress_every)
        elif ph == "C":
            phase_C(n=a.n_fits)
        elif ph == "calib":
            phase_calib()
        elif ph == "weather":
            phase_weather(n=a.weather_n, every_s=a.weather_every)
    return 0


if __name__ == "__main__":
    sys.exit(main())
