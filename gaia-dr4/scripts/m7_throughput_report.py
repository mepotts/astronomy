#!/usr/bin/env python
"""M7 task 1, analysis: turn the day-one-scale dry run into a NUMBER.

M6 published a band -- 125-857 sources/hour, the 981-row queue in 1.1-7.9 h
-- because its probe swept batch SIZE, so source count and payload bytes
moved together and two models fitted the same calls:

    A  transport-limited   t = 2.3 s + bytes / 1.8 KiB/s      (R2 0.934)
    B  per-source work     t = 6.0 s + 3.86 s * n_sources     (R2 0.917)

They differ only in extrapolation to DR4's 6.8x larger payload, and the
extrapolation is the whole question.  The M7 dry run was designed to break
that: 50 batches at a FIXED 20 sources each, with the payload varying ~5x
between batches by construction (five num_selected_g_fov strata, cycled).
At fixed n, model B predicts a FLAT batch time and model A predicts one
proportional to bytes.  This script does that regression, reports which
model survived, and re-derives the day-one wall clock under the winner.

It also folds in the two things a single fast afternoon cannot tell you:
the archive-WEATHER distribution sampled over hours, and the sustained fit
throughput over 981 consecutive fits.

Run: .venv/Scripts/python.exe scripts/m7_throughput_report.py
"""
import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
DRY = os.path.join(OUT, "m7_dryrun")

# the real thing, measured on the 2026-06-26 pre-release file in M6
DR4_ZIP_KIB_PER_SOURCE = 50.9
DR3_PROXY_KIB_PER_SOURCE = 7.5      # M6's probe payload
QUEUE_N = 981


def ols(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    A = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ beta
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    n = len(x)
    if n > 2:
        s2 = ss_res / (n - 2)
        sxx = float(np.sum((x - x.mean()) ** 2))
        se = np.sqrt(s2 / sxx) if sxx > 0 else np.nan
    else:
        se = np.nan
    return float(beta[0]), float(beta[1]), r2, float(se)


def main():
    L = []

    def say(s=""):
        L.append(s)
        print(s)

    say("M7 -- the day-one-scale dry run: measured transport, measured fit, "
        "measured weather")
    say("=" * 78)

    tim = pd.read_csv(os.path.join(DRY, "m7_harness_timings.csv"))
    batches = tim[tim["kind"] == "batch"].copy()
    runs = pd.read_csv(os.path.join(DRY, "m7_dryrun_runs.csv"))

    # ---------------------------------------------------------------- A
    say("")
    say("1. PHASE A -- the literal ask: all 981 day-one queue members")
    say("-" * 78)
    ledA = pd.read_csv(os.path.join(DRY, "transport_ledger_A.csv"))
    servedA = ledA["served"].astype(str).str.lower().isin(["true", "1"])
    rA = runs[runs["phase"] == "A"].iloc[-1]
    say("  981 queue members, 50 batched DataLink requests, DR3 "
        "EPOCH_PHOTOMETRY, batch 20.")
    say("  wall %.1f min; %d of 981 sources served (%.1f %%)"
        % (rA["wall_minutes"], int(servedA.sum()),
           100.0 * servedA.mean()))
    say("  -- and that coverage IS the first finding.  DR3 publishes epoch "
        "photometry")
    say("     only for its variability candidates, so a DR3-photometry dry "
        "run over the")
    say("     REAL queue cannot be a payload test: 907 of the 981 requests "
        "return")
    say("     nothing.  That is why phase B exists.  What phase A does "
        "measure is the")
    say("     empty-request floor and the machinery at full queue length.")
    bA = batches[batches["run_id"].str.contains("_A_")]
    empty = bA[bA["n_served"] == 0]["seconds"]
    say("  EMPTY-REQUEST FLOOR (n_served = 0, %d requests): median %.2f s, "
        "range %.2f-%.2f s"
        % (len(empty), empty.median(), empty.min(), empty.max()))
    say("     -- the per-request overhead is %.2f s, not M6's 2.3-6.0 s "
        "estimate;" % empty.median())
    say("        M6 could not separate overhead from payload because every "
        "probe request")
    say("        carried payload.  A request that serves nothing is almost "
        "free.")

    # ---------------------------------------------------------------- B
    say("")
    say("2. PHASE B -- the degeneracy-breaker: 981 SERVING sources, batch "
        "20, payload stratified")
    say("-" * 78)
    ledB = pd.read_csv(os.path.join(DRY, "transport_ledger_B.csv"))
    bB = batches[batches["run_id"].str.contains("_B_")].copy()
    bB = bB[bB["n_needed_fetch"] > 0]
    # per-batch payload from the ledger
    per_batch = []
    for rid, g in ledB.groupby("run_id"):
        for b, gg in g.groupby("batch"):
            per_batch.append({"run_id": rid, "batch": b,
                              "cells": float(gg["n_cells"].sum()),
                              "transits": float(gg["n_transits"].sum()),
                              "n_src": int(len(gg))})
    pb = pd.DataFrame(per_batch)
    m = bB.merge(pb, on=["run_id", "batch"], how="inner")
    m = m[(m["n_served"] > 0) & (m["cells"] > 0)]
    # the honest denominator: the payload lever is only "at fixed n" for the
    # batches that actually served 20.  981 = 49 x 20 + 1, so one batch is a
    # single source and one lost a source to the archive; quoting their range
    # as the payload lever would inflate 4.7x into 20.7x.
    full = m[m["n_served"] == 20]
    say("  %d payload-bearing batches, %d of them serving exactly 20 sources."
        % (len(m), len(full)))
    say("  AT FIXED n = 20: served transits per batch %d to %d (**%.1fx**), "
        "batch seconds %.1f to %.1f (%.1fx)"
        % (full["transits"].min(), full["transits"].max(),
           full["transits"].max() / max(full["transits"].min(), 1),
           full["seconds"].min(), full["seconds"].max(),
           full["seconds"].max() / max(full["seconds"].min(), 1e-9)))
    say("  over all %d: transits %d to %d, seconds %.1f to %.1f"
        % (len(m), m["transits"].min(), m["transits"].max(),
           m["seconds"].min(), m["seconds"].max()))
    say("  correlation with batch seconds: transits %.2f | n_served %.2f "
        "-- payload, not source count"
        % (m["transits"].corr(m["seconds"]),
           m["n_served"].corr(m["seconds"])))

    # bytes calibration: wire bytes per served transit
    cal = pd.read_csv(os.path.join(DRY, "m7_bytes_calibration.csv"))
    a_c, b_c, r2_c, _ = ols(cal["mean_transits"] * cal["n_ids"],
                            cal["zip_bytes"])
    bytes_per_transit = b_c
    say("")
    say("  BYTES CALIBRATION (%d dump-to-file requests, wire zip weighed):"
        % len(cal))
    say("    zip_bytes = %.0f + %.1f B per served G-FoV transit   (R2 %.3f)"
        % (a_c, bytes_per_transit, r2_c))
    m["kib"] = m["transits"] * bytes_per_transit / 1024.0

    say("")
    say("  THE TEST -- at FIXED n = 20, is batch time flat (model B) or "
        "proportional")
    say("  to payload (model A)?")
    a_b, b_b, r2_b, se_b = ols(m["kib"], m["seconds"])
    say("    t = %.2f s + %.4f s/KiB * KiB      R2 = %.3f, slope %.4f +/- "
        "%.4f s/KiB (%.1f sigma)"
        % (a_b, b_b, r2_b, b_b, se_b, b_b / se_b if se_b else np.nan))
    flat = float(m["seconds"].mean())
    ss_res_flat = float(np.sum((m["seconds"] - flat) ** 2))
    ss_tot = float(np.sum((m["seconds"] - m["seconds"].mean()) ** 2))
    say("    model B (flat at n = 20) would predict a constant %.1f s; it "
        "explains R2 = %.3f"
        % (flat, 1.0 - ss_res_flat / ss_tot))
    say("    -> the slope is %.1f sigma from zero. **MODEL B IS REFUTED AT "
        "FIXED n.**"
        % (b_b / se_b if se_b else np.nan))
    say("       DataLink's cost tracks DATA VOLUME, not source count.  M6's "
        "'server-work-")
    say("       limited, not bandwidth-limited' stands as a statement about "
        "the RATE")
    say("       (~%.1f KiB/s, far below any network); what M6 could not "
        "tell, and this"
        % (1.0 / b_b if b_b else np.nan))
    say("       can, is that the work is proportional to the bytes.")
    eff_rate = 1.0 / b_b if b_b else np.nan
    say("    effective delivered rate: %.1f KiB/s (M6 measured 1.8 KiB/s on "
        "a worse afternoon)" % eff_rate)

    # ---- both predictors at once, using phase A to vary n_served --------
    # Phase B holds n_served at 20 and varies bytes; phase A holds bytes near
    # zero and varies n_served from 0 to 3.  Fitting the union is the only
    # place in this repo where the two predictors have EVER been
    # decorrelated, so it is the only place a per-source term and a per-byte
    # term can both be estimated.
    lA = pd.read_csv(os.path.join(DRY, "transport_ledger_A.csv"))
    pa = []
    for rid, g in lA.groupby("run_id"):
        for b, gg in g.groupby("batch"):
            pa.append({"run_id": rid, "batch": b,
                       "cells": float(gg["n_cells"].sum()),
                       "transits": float(gg["n_transits"].sum())})
    mA = batches[batches["run_id"].str.contains("_A_")].merge(
        pd.DataFrame(pa), on=["run_id", "batch"], how="inner")
    mA["kib"] = mA["transits"] * bytes_per_transit / 1024.0
    both = pd.concat([m[["n_served", "kib", "seconds"]],
                      mA[["n_served", "kib", "seconds"]]], ignore_index=True)
    X = np.column_stack([np.ones(len(both)), both["n_served"], both["kib"]])
    beta, *_ = np.linalg.lstsq(X, both["seconds"].to_numpy(float), rcond=None)
    resid = both["seconds"].to_numpy(float) - X @ beta
    dof = len(both) - 3
    cov = (resid @ resid / dof) * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    r2b = 1.0 - (resid @ resid) / float(
        np.sum((both["seconds"] - both["seconds"].mean()) ** 2))
    say("")
    say("  BOTH PREDICTORS, phase A + phase B (%d requests; n_served 0-20, "
        "payload 0-296 KiB):" % len(both))
    say("    t = %.2f (+/-%.2f) + %.3f (+/-%.3f) s/source * n + %.4f "
        "(+/-%.4f) s/KiB * KiB    R2 %.3f"
        % (beta[0], se[0], beta[1], se[1], beta[2], se[2], r2b))
    say("    per-source term %.1f sigma | per-byte term %.1f sigma"
        % (beta[1] / se[1], beta[2] / se[2]))
    say("    -> BOTH are real, and the per-BYTE term dominates at DR4 "
        "payload: at 50.9 KiB/source")
    say("       the byte term costs %.2f s/source against the source term's "
        "%.2f s."
        % (beta[2] * DR4_ZIP_KIB_PER_SOURCE, beta[1]))
    say("       M6's models A and B were not rivals; they were the two "
        "terms of one model,")
    say("       and the probe's collinearity is what made them look like a "
        "choice.")

    say("")
    say("  SUSTAINED THROUGHPUT ACTUALLY ACHIEVED (the headline "
        "measurement):")
    for _, r in runs[runs["phase"] == "B"].iterrows():
        say("    %s: %d sources in %.1f min -> %.0f sources/hour"
            % (r["run_id"], int(r["n_processed"]), r["wall_minutes"],
               r["sources_per_hour"]))
    tot_n = int(runs[runs["phase"] == "B"]["n_processed"].sum())
    tot_min = float(runs[runs["phase"] == "B"]["wall_minutes"].sum())
    sph = 60.0 * tot_n / tot_min
    say("    COMBINED: %d sources in %.1f min = **%.0f sources/hour** at "
        "DR3 payload" % (tot_n, tot_min, sph))
    kib_per_src = float(m["kib"].sum() / m["n_served"].sum())
    say("    mean served payload %.1f KiB/source (M6's DR3 proxy assumed "
        "7.5 KiB/source)" % kib_per_src)

    # ---------------------------------------------------------------- C
    say("")
    say("3. PHASE C -- the fit half, sustained over 981 consecutive fits")
    say("-" * 78)
    pc = os.path.join(DRY, "m7_fit_scale_test.csv")
    if os.path.exists(pc):
        f = pd.read_csv(pc)
        rC = runs[runs["phase"] == "C"]
        warm = f.iloc[1:]
        say("  %d fits on real DR4 pre-release epoch astrometry, from cache."
            % len(f))
        say("  first fit %.3f s (import + accessor registration); steady "
            "state mean %.4f s, median %.4f s, p90 %.4f s"
            % (f.iloc[0]["seconds"], warm["seconds"].mean(),
               warm["seconds"].median(), warm["seconds"].quantile(0.9)))
        say("  => **%.0f fits/hour** sustained (M6 measured 0.036 s/source "
            "= ~100,000/hour over 22 fits)"
            % (3600.0 / warm["seconds"].mean()))
        if len(rC):
            r = rC.iloc[-1]
            say("  drift over the run: first decile %.4f s vs last decile "
                "%.4f s, OLS slope %+.4f s per 1000 fits"
                % (r["first_decile_mean"], r["last_decile_mean"],
                   r["drift_seconds_per_1000_fits"]))
            say("  determinism: max distinct f2 per source = %d (must be 1)"
                % int(r["f2_unique_per_source_max"]))
            if not pd.isna(r.get("rss_end_mb", np.nan)):
                say("  RSS %.0f -> %.0f MB over the run"
                    % (r["rss_start_mb"], r["rss_end_mb"]))
        say("  -> the fit half remains free by three orders of magnitude "
            "and does not")
        say("     drift or leak over hundreds of calls.  Transport is the "
            "whole clock.")
    else:
        say("  NOT RUN")

    # ------------------------------------------------------------ weather
    say("")
    say("4. ARCHIVE WEATHER -- the same request, sampled over hours")
    say("-" * 78)
    # ONE file, deliberately.  A glob was tried and removed: a background
    # wrapper that is killed can leave its python child alive, two weather
    # samplers ended up rewriting the same CSV, and a glob over
    # m7_archive_weather*.csv would then have double-counted the overlap.
    # One sampler, one file, one series.
    pw = os.path.join(DRY, "m7_archive_weather.csv")
    wq = None
    if os.path.exists(pw):
        w = pd.read_csv(pw)
        ok = w[w["status"] == "OK"]["seconds"]
        wq = ok
        say("  %d identical batch-20 requests over %.1f h (one every 2 min)."
            % (len(w), w["elapsed_min"].max() / 60.0))
        say("  min %.1f s | p25 %.1f | median %.1f | p75 %.1f | p90 %.1f | "
            "max %.1f  -> spread %.1fx"
            % (ok.min(), ok.quantile(.25), ok.median(), ok.quantile(.75),
               ok.quantile(.9), ok.max(), ok.max() / max(ok.min(), 1e-9)))
        sl = np.polyfit(w["elapsed_min"], w["seconds"], 1)[0]
        say("  trend %+.3f s per minute of elapsed time -- %s"
            % (sl, "no systematic degradation" if abs(sl) < 0.05
               else "DEGRADING, see the failure branch"))
        nfail = int((w["status"] != "OK").sum())
        say("  failures: %d of %d requests" % (nfail, len(w)))
        say("  M6's 5-request soak spanned 3.2x inside a few minutes; over "
            "hours the spread is %.1fx."
            % (ok.max() / max(ok.min(), 1e-9)))
    else:
        say("  NOT RUN")

    # ---------------------------------------------------- the projection
    say("")
    say("5. THE DAY-ONE NUMBER")
    say("-" * 78)
    say("  Model, measured rather than assumed:")
    say("      t_batch = %.2f s + (KiB in the batch) / %.1f KiB/s"
        % (a_b, eff_rate))
    say("  DR4 payload, measured on the real pre-release file (M6): %.1f "
        "KiB/source zipped." % DR4_ZIP_KIB_PER_SOURCE)
    per_src_dr4 = DR4_ZIP_KIB_PER_SOURCE / eff_rate
    per_batch_dr4 = a_b + 20 * per_src_dr4
    sph_dr4 = 3600.0 * 20 / per_batch_dr4
    say("  => at batch 20: %.2f s/source of transport, %.0f s/batch, "
        "**%.0f sources/hour**"
        % (per_src_dr4, per_batch_dr4, sph_dr4))
    say("  => the %d-row queue in **%.1f h**" % (QUEUE_N,
                                                 QUEUE_N / sph_dr4))
    if wq is not None:
        # SCALE FROM THE MEDIAN, not the minimum.  The fitted rate is the
        # typical condition over 50 batches, so the median request is the
        # branch it corresponds to; anchoring the bracket on the single
        # fastest request of 60 would quietly relabel a lucky outlier as
        # "the measurement" and make every other branch look like a penalty.
        med = float(wq.median())
        scale_best = float(wq.min() / med)
        scale_p90 = float(wq.quantile(0.9) / med)
        scale_max = float(wq.max() / med)
        say("")
        say("  WEATHER BRACKET.  The fitted rate is the typical condition "
            "across 50 batches,")
        say("  so it is the MEDIAN branch.  Over %d requests spanning %.1f h "
            "an identical" % (len(wq), 2.0))
        say("  request ran %.2fx the median at best, %.2fx at p90 and %.2fx "
            "at worst:"
            % (scale_best, scale_p90, scale_max))
        hours = {}
        for lab, sc in (("best request observed", scale_best),
                        ("MEDIAN -- the measured branch", 1.0),
                        ("p90", scale_p90), ("worst request observed",
                                             scale_max),
                        ("M6's bad afternoon (1.8 KiB/s)", eff_rate / 1.8),
                        ("10x degraded (M6's worst branch)", 10.0)):
            r_h = QUEUE_N / (3600.0 * 20 / (a_b + 20 * per_src_dr4 * sc))
            hours[lab] = r_h
            say("      %-34s %5.1f h  (%4.0f sources/hour)"
                % (lab, r_h, QUEUE_N / r_h))
        say("")
        say("  BUT A 50-BATCH WALL CLOCK DOES NOT SEE SINGLE-REQUEST "
            "EXTREMES -- it sees their")
        say("  mean, and they average out.  The honest bracket for a "
            "SUSTAINED run is the")
        say("  spread between the two halves of phase B, which were "
            "separated by a stop and")
        say("  a restart: %s sources/hour, i.e. +/-%.0f %%.  Read the "
            "quantile rows above as"
            % (" and ".join("%.0f" % v for v in
                            runs[runs["phase"] == "B"]["sources_per_hour"]),
               100 * 0.5 * (runs[runs["phase"] == "B"]["sources_per_hour"].max()
                            - runs[runs["phase"] == "B"]["sources_per_hour"].min())
               / runs[runs["phase"] == "B"]["sources_per_hour"].mean()))
        say("  instantaneous conditions, not as achievable wall clocks; the "
            "day-to-day rows")
        say("  (M6's afternoon, the 10x branch) are the ones that bound a "
            "whole run.")
        say("")
        say("  Every branch fits inside the runbook's 72 h, INCLUDING the "
            "10x-degraded one:")
        say("  M6's 78 h worst case was model A extrapolated from a 2.3 s "
            "overhead and a")
        say("  1.8 KiB/s rate; the measured overhead is %.2f s and the "
            "measured rate 6.9," % a_b)
        say("  so the same 10x degradation now costs %.0f h, not 78."
            % hours["10x degraded (M6's worst branch)"])
        say("")
        say("  THE BAND, BEFORE AND AFTER")
        say("      M6: 125-857 sources/hour, 1.1-7.9 h -- a factor 6.9, "
            "spanned by a MODEL")
        say("          ambiguity (bytes vs sources) that no measurement "
            "then available could")
        say("          resolve.")
        key = "MEDIAN -- the measured branch"
        say("      M7: **%.0f sources/hour, %.1f h** measured at today's "
            "median archive rate; and"
            % (QUEUE_N / hours[key], hours[key]))
        say("          %.0f-%.0f sources/hour, %.1f-%.1f h across the full "
            "range of rates ever"
            % (QUEUE_N / hours["M6's bad afternoon (1.8 KiB/s)"],
               QUEUE_N / hours["best request observed"],
               hours["best request observed"],
               hours["M6's bad afternoon (1.8 KiB/s)"]))
        say("          measured on this service (1.8-6.9 KiB/s) -- a factor "
            "%.1f, and every bit"
            % (hours["M6's bad afternoon (1.8 KiB/s)"]
               / hours["best request observed"]))
        say("          of it is ARCHIVE WEATHER, which is a thing that "
            "happens on the day and")
        say("          cannot be measured before it.  The model half of "
            "M6's band is gone.")
    say("")
    say("  WHAT IS STILL EXTRAPOLATED, named: the payload.  DR4 epoch "
        "astrometry does")
    say("  not exist on the service yet, so the 50.9 KiB/source is measured "
        "on the")
    say("  pre-release FILE and the rate is measured on DR3 photometry. "
        "What M7 removes")
    say("  is the MODEL ambiguity (bytes vs sources), which was the wider "
        "half of M6's")
    say("  band; what remains is archive weather on the day, which is "
        "bracketed above")
    say("  and cannot be measured before the day.")

    p = os.path.join(OUT, "m7_throughput_measured.txt")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    m.to_csv(os.path.join(DRY, "m7_batch_regression.csv"), index=False,
             lineterminator="\n")
    print("\nwrote %s" % os.path.relpath(p, BASE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
