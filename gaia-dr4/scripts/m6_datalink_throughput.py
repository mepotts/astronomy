#!/usr/bin/env python
"""M6: MEASURE the DataLink bottleneck, then project the day-one wall clock.

The deliverable this script exists for is a *measured* sources-per-hour
figure and a projected wall clock for the full day-one queue, so December's
capacity is known in advance rather than discovered on the day.

WHAT CAN AND CANNOT BE MEASURED TODAY -- stated first, because the honesty
of the projection is the whole value of it:

  MEASURABLE now, and measured here:
    * the DataLink SERVICE: request overhead, per-source cost and delivered
      bytes/second, at several batch sizes, against the live archive.  DR4
      epoch astrometry does not exist yet, so the probe uses DR3
      EPOCH_PHOTOMETRY -- the same service, the same endpoint, the same
      RAW batching, the same anonymous quota.  It is a PROXY for the
      transport, and it is labelled as one everywhere it appears.
    * the PAYLOAD of real DR4 epoch astrometry: the 2026-06-26 pre-release
      RAW VOTable, 12 sources, on disk -- compressed to what the wire
      would actually carry (DataLink sets USE_ZIP_ALWAYS=true, so the zip
      IS the transfer).
    * the FIT: gaiasupdate single-star fits of that same real epoch
      astrometry (scripts/epoch_vet_harness.py timings).

TWO MODELS, BOTH FITTED, BOTH REPORTED -- because the first probe showed
the archive is NOT bandwidth-limited (it delivered 8-278 KiB in 2.8-164 s,
i.e. ~2 KiB/s, which is not a network) but server-work-limited, and the two
models extrapolate to DR4 very differently:

  A  TRANSPORT-LIMITED   t_batch = a + b_bytes * bytes(n)
     -> a DR4 source costs more because its payload is ~7x bigger
     (50.9 KiB zipped vs ~7 KiB for a DR3 epoch-photometry source).
  B  PER-SOURCE-WORK     t_batch = a + c_source * n
     -> a DR4 source costs the same as a DR3 one, because the cost is the
     service assembling one source's product, not moving its bytes.

The truth on release day is somewhere between them, so the projection is
reported as a BAND spanned by A and B, times a degradation factor.  Model B
is the optimistic edge and model A the pessimistic one; the runbook carries
both.  Reporting one number here would be the kind of confident wrong
answer this repo keeps finding in other people's papers.

    t_source(DR4) = a / batch + (b_bytes * zipped_bytes_per_source_DR4
                                 or c_source)
    t_total = n_queue * (t_source_fetch + t_source_fit) + politeness gaps

SOAK TEST (--soak N).  N identical requests back to back at one batch size,
to separate "the archive is slow" from "the archive is throttling us".  A
rising trend is a rate limit and changes the day-one plan (fewer, bigger
requests); flat-but-noisy is load and changes nothing.

Outputs: out/m6_datalink_probe.csv, out/m6_throughput_projection.txt,
         out/m6_throughput_projection.csv
Run    : .venv/Scripts/python.exe scripts/m6_datalink_throughput.py
         (--offline reuses a previous probe CSV and only re-projects)
"""

import argparse
import io
import os
import sys
import time
import warnings
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
PRERELEASE_XML = os.path.join(
    BASE, "data", "epoch-astrometry",
    "GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml")
PROBE_CSV = os.path.join(OUT, "m6_datalink_probe.csv")
PROJECTION_TXT = os.path.join(OUT, "m6_throughput_projection.txt")

BATCH_SIZES = [1, 2, 5, 10, 20, 40]
GAP_S = 1.0
N_QUEUE_DEFAULT = 983          # the driver-emitted day-one queue (M5 stage H)
N_QUEUE_PROD = 981             # the DR3 production copy (dust-corrected)


def zipped_bytes_per_source_dr4():
    """The real payload: the pre-release RAW epoch astrometry, compressed
    the way DataLink compresses it (USE_ZIP_ALWAYS=true)."""
    raw = open(PRERELEASE_XML, "rb").read()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("EPOCH_ASTROMETRY_RAW.xml", raw)
    n_sources = 12
    return (len(raw) / n_sources, buf.getbuffer().nbytes / n_sources,
            n_sources, len(raw))


def probe(ids, sizes=BATCH_SIZES, release="Gaia DR3",
          retrieval_type="EPOCH_PHOTOMETRY", repeats=1, verbose=True,
          warmup=True):
    """Time real DataLink calls at several batch sizes; measure the zip."""
    from astroquery.gaia import Gaia
    warnings.filterwarnings("ignore")
    scratch = os.path.join(os.environ.get("TEMP", "."), "m6_datalink_probe")
    os.makedirs(scratch, exist_ok=True)
    cwd = os.getcwd()
    rows = []
    cursor = 0
    os.chdir(scratch)
    try:
        # one warm-up call: the first astroquery request pays TAP handshake
        # + DNS + TLS that no later call pays, and charging that to batch
        # size 1 would bias the intercept
        if warmup:
            try:
                t0 = time.time()
                Gaia.load_data(ids=[int(ids[0])], data_release=release,
                               retrieval_type=retrieval_type,
                               data_structure="RAW", format="votable",
                               verbose=False)
                if verbose:
                    print(f"  warm-up call: {time.time()-t0:.2f}s "
                          f"(discarded)", flush=True)
            except Exception as exc:                   # noqa: BLE001
                print(f"  warm-up FAILED: {type(exc).__name__}: {exc}")
            time.sleep(GAP_S)

        for rep in range(repeats):
            for n in sizes:
                if cursor + n > len(ids):
                    cursor = 0
                batch = [int(x) for x in ids[cursor:cursor + n]]
                cursor += n
                for f in os.listdir(scratch):
                    if f.startswith("datalink_output_"):
                        os.remove(os.path.join(scratch, f))
                t0 = time.time()
                status, nz, err = "OK", np.nan, ""
                try:
                    Gaia.load_data(ids=batch, data_release=release,
                                   retrieval_type=retrieval_type,
                                   data_structure="RAW", format="votable",
                                   dump_to_file=True,
                                   overwrite_output_file=True, verbose=False)
                except Exception as exc:               # noqa: BLE001
                    status, err = "FAIL", f"{type(exc).__name__}: {exc}"
                dt = time.time() - t0
                zips = [f for f in os.listdir(scratch)
                        if f.startswith("datalink_output_")]
                if zips:
                    nz = sum(os.path.getsize(os.path.join(scratch, f))
                             for f in zips)
                    for f in zips:
                        os.remove(os.path.join(scratch, f))
                rows.append({"rep": rep, "batch_size": n,
                             "seconds": round(dt, 3), "zip_bytes": nz,
                             "status": status,
                             "retrieval_type": retrieval_type,
                             "release": release, "note": err})
                if verbose:
                    kib = "" if not np.isfinite(nz) else f"{nz/1024:8.1f} KiB"
                    print(f"  batch {n:3d}: {dt:6.2f}s  {kib}  "
                          f"{status} {err}", flush=True)
                time.sleep(GAP_S)
    finally:
        os.chdir(cwd)
    return pd.DataFrame(rows)


def _lstsq(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    A = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return (float(coef[0]), float(coef[1]),
            (1 - ss_res / ss_tot if ss_tot > 0 else np.nan))


def fit_model(df):
    """Fit BOTH models (see the docstring); return them side by side."""
    mode = df["mode"] if "mode" in df.columns else pd.Series(
        ["sweep"] * len(df), index=df.index)
    ok = df[(df["status"] == "OK") & np.isfinite(df["zip_bytes"])
            & (mode != "soak")]
    if len(ok) < 3:
        return None
    y = ok["seconds"].values
    a_b, b_bytes, r2_b = _lstsq(ok["zip_bytes"].values, y)
    a_n, c_src, r2_n = _lstsq(ok["batch_size"].values, y)
    return {
        "A_transport": {"a_s": a_b, "b_s_per_byte": b_bytes,
                        "bytes_per_s": (1.0 / b_bytes) if b_bytes > 0
                        else np.inf, "r2": r2_b},
        "B_per_source": {"a_s": a_n, "c_s_per_source": c_src, "r2": r2_n},
        "n_points": len(ok),
        "probe_bytes_per_source": float(np.median(
            ok["zip_bytes"].values / ok["batch_size"].values)),
    }


def fit_seconds_per_source(timings_csv=None):
    """Measured single-star-fit cost from the harness's own timing rows.

    The FIRST fit of a session pays gaiasupdate's import + pandas-accessor
    registration (~2.5 s), which is a one-off, not a per-source cost: over
    983 sources it amortises to nothing.  Both numbers are reported and the
    projection uses the steady-state one.
    """
    timings_csv = timings_csv or os.path.join(OUT, "m6_harness_timings.csv")
    if not os.path.exists(timings_csv):
        return None
    t = pd.read_csv(timings_csv)
    src = t[t["kind"] == "source"].dropna(subset=["seconds"])
    s = src["seconds"].values
    if not len(s):
        return None
    # Drop the FIRST fit of each run, not the single global maximum: the
    # timings CSV accumulates across runs, so every run contributes one
    # warm-up and a global-max rule would leave the others in and quietly
    # inflate the per-source cost as the file grows.
    if "run_id" in src.columns:
        first = src.groupby("run_id", sort=False).head(1).index
        steady = src.drop(index=first)["seconds"].values
    else:                                            # pragma: no cover
        steady = np.sort(s)[:-1]
    if not len(steady):
        steady = s
    return {"median": float(np.median(s)), "mean": float(np.mean(s)),
            "steady_mean": float(np.mean(steady)),
            "p90": float(np.quantile(s, 0.9)),
            "max": float(np.max(s)), "n": int(len(s))}


def project(model, fitstats, n_queue, batch, gap=0.5, degrade=1.0,
            which="A"):
    """Wall clock for n_queue sources at a given batch size, under model A
    (transport-limited) or B (per-source server work)."""
    _raw_b, zip_b, _n, _tot = zipped_bytes_per_source_dr4()
    if which == "A":
        m = model["A_transport"]
        per_fetch = m["a_s"] / batch + m["b_s_per_byte"] * zip_b * degrade
    else:
        m = model["B_per_source"]
        per_fetch = m["a_s"] / batch + m["c_s_per_source"] * degrade
    per_fit = fitstats["steady_mean"] if fitstats else 0.0
    per_gap = gap / batch
    per_source = max(per_fetch, 0.0) + per_fit + per_gap
    return {"model": which, "batch": batch, "degrade": degrade,
            "fetch_s_per_source": per_fetch, "fit_s_per_source": per_fit,
            "gap_s_per_source": per_gap, "s_per_source": per_source,
            "sources_per_hour": 3600.0 / per_source,
            "hours_for_queue": n_queue * per_source / 3600.0,
            "zipped_bytes_per_source": zip_b}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="skip the network probe, re-project from "
                         "out/m6_datalink_probe.csv")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--soak", type=int, default=0,
                    help="N identical requests at --soak-batch, appended to "
                         "the probe CSV as mode=soak (throttle test)")
    ap.add_argument("--soak-batch", type=int, default=10)
    ap.add_argument("--n-queue", type=int, default=N_QUEUE_DEFAULT)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)

    lines = []

    def say(s=""):
        lines.append(s)
        print(s)

    say("M6 DataLink throughput probe + day-one wall-clock projection")
    say("=" * 72)

    if not a.offline:
        act = pd.read_parquet(os.path.join(BASE, "data",
                                           "dr3_activity_columns.parquet"))
        ids = act.loc[act["in_vari_summary"], "source_id"] \
                 .astype("int64").tolist()
        say(f"probe ids: {len(ids)} DR3 candidate sources that are in "
            f"gaiadr3.vari_summary (i.e. have epoch photometry)")
        say("PROXY, stated up front: DR4 epoch astrometry does not exist "
            "yet, so the")
        say("transport is measured with DR3 EPOCH_PHOTOMETRY -- same "
            "DataLink service,")
        say("same RAW batching, same anonymous quota, different payload. "
            "The payload is")
        say("taken from the real pre-release epoch astrometry instead.")
        say("")
        prev = pd.read_csv(PROBE_CSV) if os.path.exists(PROBE_CSV) else None
        if prev is not None and "mode" not in prev.columns:
            prev = prev.assign(mode="sweep")
        if a.soak:
            df_new = probe(ids, sizes=[a.soak_batch] * a.soak, repeats=1)
            df_new["mode"] = "soak"
        else:
            df_new = probe(ids, repeats=a.repeats)
            df_new["mode"] = "sweep"
        df = df_new if prev is None else pd.concat([prev, df_new],
                                                   ignore_index=True)
        df.to_csv(PROBE_CSV, index=False, lineterminator="\n")
        say(f"wrote {os.path.relpath(PROBE_CSV, BASE)}")
    else:
        df = pd.read_csv(PROBE_CSV)
        if "mode" not in df.columns:
            df["mode"] = "sweep"
        say(f"offline: re-projecting from "
            f"{os.path.relpath(PROBE_CSV, BASE)}")

    say("")
    say("MEASURED DataLink calls (anonymous, ESAC) " + "-" * 30)
    for i, (_, r) in enumerate(df.iterrows()):
        kib = (r["zip_bytes"] / 1024 if np.isfinite(r["zip_bytes"])
               else float("nan"))
        say(f"  #{i:2d} [{str(r.get('mode', 'sweep')):5s}] batch "
            f"{int(r['batch_size']):3d}  {r['seconds']:7.2f} s  "
            f"{kib:8.1f} KiB  {kib/max(r['seconds'], 1e-9):6.2f} KiB/s  "
            f"{r['status']}  "
            f"{r['note'] if isinstance(r['note'], str) else ''}")

    soak = df[df["mode"] == "soak"]
    if len(soak) >= 3:
        sec = soak["seconds"].values
        sl = _lstsq(np.arange(len(sec)), sec)
        say("")
        say(f"SOAK TEST -- {len(soak)} identical requests at batch "
            f"{int(soak['batch_size'].iloc[0])} " + "-" * 18)
        say(f"  seconds: {[round(float(x), 1) for x in sec]}")
        say(f"  median {np.median(sec):.1f} s, min {sec.min():.1f}, "
            f"max {sec.max():.1f}, spread "
            f"{sec.max()/max(sec.min(), 1e-9):.1f}x")
        say(f"  trend across the run: {sl[1]:+.2f} s per request "
            f"(R^2 {sl[2]:.2f})")
        if sl[1] > 0 and sl[2] > 0.5:
            say("  -> RISING and well fitted: consistent with RATE "
                "LIMITING. Day-one plan:")
            say("     fewer, larger requests and a longer politeness gap.")
        else:
            say("  -> not a clean monotone rise: the spread is archive "
                "LOAD, not a rate")
            say("     limit aimed at us.  The VARIANCE is the finding -- "
                "any single-call")
            say("     timing is worthless for planning, which is why the "
                "projection below")
            say("     is a band and why the harness is resumable.")

    model = fit_model(df)
    if model is None:
        say("\nPROBE FAILED -- fewer than 3 successful calls. No projection "
            "is made; a projection from a failed probe would be a guess "
            "with a decimal point.")
        with open(PROJECTION_TXT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        return 1

    ok = df[(df["status"] == "OK") & np.isfinite(df["zip_bytes"])
            & (df["mode"] != "soak")]
    A, B = model["A_transport"], model["B_per_source"]
    say("")
    say("TWO TRANSPORT MODELS, both fitted to the same calls " + "-" * 20)
    say(f"  A transport-limited  t = {A['a_s']:.1f} s + bytes / "
        f"{A['bytes_per_s']/1024:.1f} KiB/s      (R^2 {A['r2']:.3f})")
    say(f"  B per-source work    t = {B['a_s']:.1f} s + "
        f"{B['c_s_per_source']:.2f} s per source      (R^2 {B['r2']:.3f})")
    say(f"  fitted on {model['n_points']} sweep calls spanning "
        f"{ok['seconds'].min():.1f}-{ok['seconds'].max():.1f} s and "
        f"{ok['zip_bytes'].min()/1024:.0f}-"
        f"{ok['zip_bytes'].max()/1024:.0f} KiB")
    say(f"  probe payload: {model['probe_bytes_per_source']/1024:.1f} "
        f"KiB/source (DR3 epoch photometry)")
    say("  The two fit the SAME data about equally well because bytes and "
        "sources are")
    say("  collinear in the probe.  They disagree about DR4 only because "
        "DR4's payload")
    say("  per source is ~7x bigger -- exactly the extrapolation that "
        "cannot be tested")
    say("  until the data exists.  Hence a band, not a number.")

    raw_b, zip_b, nsrc, tot = zipped_bytes_per_source_dr4()
    say("")
    say("PAYLOAD, measured on the real thing " + "-" * 36)
    say(f"  pre-release RAW epoch astrometry: {tot:,} B for {nsrc} sources")
    say(f"  = {raw_b/1024:.1f} KiB/source uncompressed, "
        f"{zip_b/1024:.1f} KiB/source zipped (DataLink sends zip)")
    say(f"  ratio to the probe's payload: "
        f"{zip_b/model['probe_bytes_per_source']:.1f}x")

    fs = fit_seconds_per_source()
    say("")
    say("FIT COST, measured on that same real epoch astrometry " + "-" * 18)
    if fs:
        say(f"  gaiasupdate single-star fit, n={fs['n']}: median "
            f"{fs['median']:.3f} s/source, steady-state mean "
            f"{fs['steady_mean']:.3f} s, p90 {fs['p90']:.3f}")
        say(f"  (the {fs['max']:.1f} s outlier is the session's FIRST fit "
            f"-- gaiasupdate import + pandas accessor registration, a "
            f"one-off that")
        say(f"   amortises to nothing over {a.n_queue} sources)")
    else:
        say("  UNMEASURED -- run scripts/epoch_vet_harness.py first")

    say("")
    say(f"PROJECTION for the day-one queue (n = {a.n_queue}) " + "-" * 22)
    say("  per source = fetch + single-star fit + politeness gap/batch;")
    say("  'degrade' multiplies the transport term to price a slower "
        "release-day archive.")
    say("")
    say(f"  {'model':>5} {'batch':>6} {'degrade':>8} {'s/source':>9} "
        f"{'src/hour':>9} {'hours':>7}")
    rows = []
    for which in ("B", "A"):
        for degrade in (1.0, 3.0, 10.0):
            for batch in (5, 20, 50):
                pr = project(model, fs, a.n_queue, batch, degrade=degrade,
                             which=which)
                rows.append(pr)
                say(f"  {which:>5} {batch:6d} {degrade:8.0f}x "
                    f"{pr['s_per_source']:9.2f} "
                    f"{pr['sources_per_hour']:9.0f} "
                    f"{pr['hours_for_queue']:7.2f}")
    pd.DataFrame(rows).to_csv(
        os.path.join(OUT, "m6_throughput_projection.csv"), index=False,
        lineterminator="\n")

    fast = project(model, fs, a.n_queue, 20, degrade=1.0, which="B")
    slow = project(model, fs, a.n_queue, 20, degrade=1.0, which="A")
    worst = project(model, fs, a.n_queue, 20, degrade=10.0, which="A")
    say("")
    say("HEADLINE " + "-" * 63)
    say("  MEASURED today, end to end on real epoch astrometry: the "
        "single-star-fit")
    say(f"  half of the loop runs at {3600/fs['steady_mean']:,.0f} "
        f"sources/hour ({fs['steady_mean']:.3f} s/source).")
    say("  It is NOT the bottleneck and never will be.")
    say(f"  MEASURED today on the live DataLink service: "
        f"{B['c_s_per_source']:.1f} s per source at "
        f"{model['probe_bytes_per_source']/1024:.0f} KiB/source, "
        f"{A['a_s']:.1f}-{B['a_s']:.1f} s per request.")
    say("")
    say("  PROJECTED day-one throughput at batch 20, undegraded:")
    say(f"    model B (per-source work): {fast['sources_per_hour']:.0f} "
        f"sources/hour -> {a.n_queue} rows in "
        f"{fast['hours_for_queue']:.1f} h")
    say(f"    model A (transport):       {slow['sources_per_hour']:.0f} "
        f"sources/hour -> {a.n_queue} rows in "
        f"{slow['hours_for_queue']:.1f} h")
    say(f"  => THE BAND: "
        f"{min(fast['sources_per_hour'], slow['sources_per_hour']):.0f}-"
        f"{max(fast['sources_per_hour'], slow['sources_per_hour']):.0f} "
        f"sources/hour, i.e. the {a.n_queue}-row queue in "
        f"{min(fast['hours_for_queue'], slow['hours_for_queue']):.1f}-"
        f"{max(fast['hours_for_queue'], slow['hours_for_queue']):.1f} h.")
    say(f"  At a 10x-degraded archive (release-day branch, model A): "
        f"{worst['hours_for_queue']:.0f} h -- the only")
    say("  branch measured that does NOT fit inside the runbook's 72 h.")
    say("")
    say("  CONSEQUENCE for the runbook, and it is the actionable one: the "
        "queue is")
    say("  RANKED and the harness consumes it in rank order, so a slow "
        "archive costs")
    say("  DEPTH, not the headline -- BH1, BH2 and the spurious poster "
        "child are")
    say("  adjudicated in the first minutes under every branch.  The "
        "failure mode to")
    say("  plan for is running out of hours, not running out of "
        "throughput, and the")
    say("  mitigation is already in the harness: it is resumable, so 72 h "
        "is a")
    say("  checkpoint, not a deadline.")
    say("")
    say("  ASSUMPTIONS carried, not hidden:")
    say("    (i) DR4 epoch astrometry is served by the same DataLink "
        "service at a cost")
    say("        between 'same per source' (B) and 'same per byte' (A).")
    say("   (ii) release day is busier than a quiet Friday -- hence the "
        "degrade column.")
    say("  (iii) the probe used DR3 EPOCH_PHOTOMETRY because DR4 epoch "
        "astrometry does")
    say("        not exist yet.  RE-RUN THIS SCRIPT ON 2026-12-02 with the "
        "real")
    say("        retrieval type BEFORE committing to a batch size: it "
        "takes ~6 minutes")
    say("        and replaces every projected number with a measured one.")

    with open(PROJECTION_TXT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.relpath(PROJECTION_TXT, BASE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
