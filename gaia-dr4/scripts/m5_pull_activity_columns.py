#!/usr/bin/env python
"""M5 task 1 (data): pull the Gaia DR3 activity / variability / astrometric-
quality columns the M4-recommended all-sky discriminator test needs.

Why a new pull: the M2 input pull carried `ruwe`, `ipd_frac_multi_peak`,
`astrometric_excess_noise*`, `ipd_gof_harmonic_amplitude` and
`phot_bp_rp_excess_factor` (family C below) but NOT the photometric-scatter
columns (`phot_*_mean_flux_over_error`, `phot_*_n_obs`,
`phot_variable_flag`), and no `astrophysical_parameters` /
`vari_summary` join at all.  Those are families A and B.

Scope (union, deduplicated):
  - fixtures/elbadry2026_astrometric_candidates.csv    (76 EB26 ground truth)
  - out/amrf_class3_candidates_v2.csv                  (949 v2 candidates)
  - out/amrf_class3_lowsig_retrieval.csv               (239 retrieval bin)
The EB26 76 are the *test* sample; the rest are pulled so that any flag the
test validates can actually be attached to the day-one queue without a
second trip to the archive on 2026-12-02.

Tables and columns
------------------
gaiadr3.gaia_source          family B (photometric scatter) + family C
                             (astrometric quality) + confound covariates
gaiadr3.astrophysical_parameters   family A: activityindex_espcs
                             (ESP-CS Ca II IRT chromospheric index; DR3
                             data model unit nm)
gaiadr3.vari_summary         family B: the variability-pipeline statistics
                             (only populated for sources the variability
                             pipeline processed -- coverage is part of the
                             result, not an error)

ENDPOINT FAILOVER (new landmine, 2026-08-18)
--------------------------------------------
The ESAC endpoint https://gea.esac.esa.int/tap-server/tap/sync stopped
answering entirely today: a TOP-1 indexed single-source query on
gaiadr3.gaia_source read-timed-out at 90 s, repeatedly, from a machine that
had been pulling 169k rows from it two days earlier.  Two official Gaia
partner-data-centre DR3 mirrors answer the identical ADQL in < 2 s:
  https://gaia.ari.uni-heidelberg.de/tap/sync   (ARI Heidelberg, CSV)
  https://gaia.aip.de/tap/sync                  (AIP, VOTable-only output)
This script tries ESAC first and falls back, recording which endpoint
served each table in the NOTE.

MIRROR VALIDATION GATE (runs before anything is written): for all 76 EB26
targets, `ruwe`, `phot_g_mean_mag` and `ipd_frac_multi_peak` from the
serving endpoint must reproduce the values already in the M2 triage parquet
(pulled from ESAC in August) to within float32 tolerance.  A mirror that
fails the gate is not used.

Output: data/dr3_activity_columns.parquet (+ .NOTE.md provenance)
Run   : .venv/Scripts/python.exe scripts/m5_pull_activity_columns.py
"""

import datetime
import hashlib
import io
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PARQUET = os.path.join(BASE, "data", "dr3_activity_columns.parquet")
OUT_NOTE = os.path.join(BASE, "data", "dr3_activity_columns.NOTE.md")
TRIAGE_PARQUET = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")

ENDPOINTS = [
    ("esac", "https://gea.esac.esa.int/tap-server/tap/sync"),
    ("ari", "https://gaia.ari.uni-heidelberg.de/tap/sync"),
    ("aip", "https://gaia.aip.de/tap/sync"),
]
CHUNK = 400
PAUSE_S = 0.5
PROBE_TIMEOUT = 45
QUERY_TIMEOUT = 240

GS_COLS = [
    "source_id",
    # --- family B: photometric scatter, available for every source --------
    "phot_g_mean_flux_over_error", "phot_bp_mean_flux_over_error",
    "phot_rp_mean_flux_over_error",
    "phot_g_n_obs", "phot_bp_n_obs", "phot_rp_n_obs",
    "phot_variable_flag",
    # --- family C: astrometric quality (NOT activity) ---------------------
    "ruwe", "ipd_frac_multi_peak", "ipd_frac_odd_win",
    "ipd_gof_harmonic_amplitude",
    "astrometric_excess_noise", "astrometric_excess_noise_sig",
    "astrometric_gof_al", "astrometric_chi2_al",
    "astrometric_n_good_obs_al", "astrometric_sigma5d_max",
    "astrometric_params_solved",
    "visibility_periods_used", "duplicated_source", "non_single_star",
    "phot_bp_rp_excess_factor",
    # --- covariates for the pre-registered confound check ------------------
    "phot_g_mean_mag", "bp_rp", "parallax", "parallax_over_error",
]

AP_COLS = ["source_id", "activityindex_espcs",
           "activityindex_espcs_uncertainty", "activityindex_espcs_input"]

VS_COLS = [
    "source_id", "num_selected_g_fov", "mean_mag_g_fov", "median_mag_g_fov",
    "std_dev_mag_g_fov", "range_mag_g_fov", "trimmed_range_mag_g_fov",
    "iqr_mag_g_fov", "mad_mag_g_fov", "skewness_mag_g_fov",
    "kurtosis_mag_g_fov", "std_dev_over_rms_err_mag_g_fov",
    "stetson_mag_g_fov", "abbe_mag_g_fov", "time_duration_g_fov",
    "std_dev_mag_bp", "std_dev_mag_rp",
    "in_vari_classification_result", "in_vari_rotation_modulation",
    "in_vari_eclipsing_binary", "in_vari_compact_companion",
    "in_vari_short_timescale", "in_vari_long_period_variable",
]

TABLES = [("gaiadr3.gaia_source", GS_COLS, "gs"),
          ("gaiadr3.astrophysical_parameters", AP_COLS, "ap"),
          ("gaiadr3.vari_summary", VS_COLS, "vs")]


def _post(url, query, timeout):
    return requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                    "FORMAT": "csv", "QUERY": query},
                         timeout=timeout)


def pick_endpoint():
    """First endpoint that answers a trivial indexed query AND returns CSV."""
    probe = ("SELECT TOP 1 source_id, ruwe FROM gaiadr3.gaia_source "
             "WHERE source_id = 4373465352415301632")
    for name, url in ENDPOINTS:
        t0 = time.time()
        try:
            r = _post(url, probe, PROBE_TIMEOUT)
        except Exception as e:
            print(f"  endpoint {name}: {type(e).__name__} after "
                  f"{time.time()-t0:.0f}s -- skipping")
            continue
        dt = time.time() - t0
        if r.status_code != 200:
            print(f"  endpoint {name}: HTTP {r.status_code} -- skipping")
            continue
        if not r.text.lstrip().lower().startswith("source_id"):
            print(f"  endpoint {name}: HTTP 200 in {dt:.1f}s but ignores "
                  f"FORMAT=csv (returns {r.text.lstrip()[:20]!r}) -- skipping")
            continue
        print(f"  endpoint {name}: OK in {dt:.1f}s -> using {url}")
        return name, url
    raise RuntimeError("no TAP endpoint answered the probe")


def pull(url, table, cols, ids, timeout=QUERY_TIMEOUT, served=None):
    """Chunked sync pull with per-chunk retry and endpoint failover.

    ESAC intermittently answers HTTP 500 / read-timeout mid-pull today
    (2026-08-18), so a chunk that fails twice on the current endpoint is
    retried on the next endpoint in ENDPOINTS that speaks CSV.  Which
    endpoint served which chunk is recorded in `served`.
    """
    frames = []
    order = [url] + [u for _, u in ENDPOINTS if u != url]
    cur = 0
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        q = (f"SELECT {', '.join(cols)} FROM {table} WHERE source_id IN "
             f"({','.join(str(x) for x in chunk)})")
        df = None
        for attempt in range(2 * len(order)):
            u = order[cur % len(order)]
            t0 = time.time()
            try:
                r = _post(u, q, timeout)
                r.raise_for_status()
                if not r.text.lstrip().lower().startswith(cols[0].lower()):
                    raise RuntimeError(
                        f"non-CSV reply {r.text.lstrip()[:20]!r}")
                df = pd.read_csv(io.StringIO(r.text))
            except Exception as e:
                print(f"    {table} chunk {i//CHUNK + 1} on "
                      f"{u.split('/')[2]}: {type(e).__name__} after "
                      f"{time.time()-t0:.0f}s -- retry", flush=True)
                time.sleep(2.0)
                if attempt % 2 == 1:
                    cur += 1          # two strikes on this endpoint -> next
                continue
            print(f"    {table} chunk {i//CHUNK + 1}/"
                  f"{(len(ids)+CHUNK-1)//CHUNK}: {len(df)} rows "
                  f"({time.time()-t0:.1f}s, {u.split('/')[2]})", flush=True)
            if served is not None:
                served.add(u.split("/")[2])
            break
        if df is None:
            raise RuntimeError(f"{table} chunk {i//CHUNK + 1} failed on "
                               f"every endpoint -- ABORT")
        frames.append(df)
        time.sleep(PAUSE_S)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=cols)
    out.columns = [c.lower() for c in out.columns]
    if "source_id" in out.columns:
        out["source_id"] = out["source_id"].astype(np.int64)
    return out


def main():
    eb = pd.read_csv(os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))
    v2 = pd.read_csv(os.path.join(BASE, "out",
                                  "amrf_class3_candidates_v2.csv"))
    ret = pd.read_csv(os.path.join(BASE, "out",
                                   "amrf_class3_lowsig_retrieval.csv"))
    eb_ids = set(eb["source_id"].astype(np.int64))
    ids = sorted(eb_ids | set(v2["source_id"].astype(np.int64))
                 | set(ret["source_id"].astype(np.int64)))
    print(f"id list: {len(ids)} distinct source_ids "
          f"(eb26={len(eb_ids)}, v2={v2['source_id'].nunique()}, "
          f"retrieval={ret['source_id'].nunique()})")

    print("\nselecting a TAP endpoint...")
    ep_name, ep_url = pick_endpoint()

    t_start = time.time()
    served = set()
    print(f"\npulling gaia_source ({len(GS_COLS)} cols)...")
    gs = pull(ep_url, "gaiadr3.gaia_source", GS_COLS, ids, served=served)

    # ---- mirror validation gate (before anything else is trusted) --------
    tri = pd.read_parquet(TRIAGE_PARQUET,
                          columns=["source_id", "ruwe", "phot_g_mean_mag",
                                   "ipd_frac_multi_peak"]).drop_duplicates(
        "source_id")
    chk = gs[gs["source_id"].isin(eb_ids)][
        ["source_id", "ruwe", "phot_g_mean_mag", "ipd_frac_multi_peak"]] \
        .merge(tri, on="source_id", how="inner", suffixes=("_new", "_m2"))
    assert len(chk) == len(eb_ids), (
        f"validation gate: only {len(chk)} of {len(eb_ids)} EB26 targets "
        f"matched the M2 parquet")
    bad = []
    for c in ("ruwe", "phot_g_mean_mag", "ipd_frac_multi_peak"):
        a = chk[f"{c}_new"].astype(float).values
        b = chk[f"{c}_m2"].astype(float).values
        d = np.nanmax(np.abs(a - b) / np.maximum(np.abs(b), 1e-6))
        print(f"  gate {c}: max relative diff vs M2 parquet = {d:.3e}")
        if not (d < 1e-5):
            bad.append(c)
    assert not bad, f"ENDPOINT {ep_name} FAILED THE VALIDATION GATE on {bad}"
    print(f"  MIRROR VALIDATION GATE PASS ({ep_name})")

    print(f"\npulling astrophysical_parameters...")
    ap = pull(ep_url, "gaiadr3.astrophysical_parameters", AP_COLS, ids,
              served=served)
    print(f"\npulling vari_summary...")
    vs = pull(ep_url, "gaiadr3.vari_summary", VS_COLS, ids, served=served)

    print(f"\nrow counts: gaia_source {len(gs)} (of {len(ids)} ids), "
          f"astrophysical_parameters {len(ap)}, vari_summary {len(vs)}")
    assert gs["source_id"].is_unique and len(gs) == len(ids), \
        "gaia_source must return exactly one row per source_id"
    assert ap["source_id"].is_unique, "astrophysical_parameters fanned out"
    assert vs["source_id"].is_unique, "vari_summary fanned out"

    full = gs.merge(ap, on="source_id", how="left", suffixes=("", "_ap")) \
             .merge(vs, on="source_id", how="left", suffixes=("", "_vs"))
    full["in_astrophysical_parameters"] = full["source_id"].isin(
        set(ap["source_id"]))
    full["in_vari_summary"] = full["source_id"].isin(set(vs["source_id"]))
    full = full.sort_values("source_id").reset_index(drop=True)
    full.to_parquet(OUT_PARQUET, index=False)

    sha = hashlib.sha256(open(OUT_PARQUET, "rb").read()).hexdigest()
    dt = time.time() - t_start
    n_esp = int(full["activityindex_espcs"].notna().sum())
    with open(OUT_NOTE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            f"# dr3_activity_columns.parquet\n\n"
            f"- pulled: "
            f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} "
            f"(sync CSV chunks of <= {CHUNK} ids, {PAUSE_S}s pause; "
            f"{dt:.0f}s total)\n"
            f"- endpoint chosen by probe: **{ep_name}** ({ep_url}) "
            f"-- anonymous\n"
            f"- endpoint host(s) that actually served chunks: "
            f"{', '.join(sorted(served))}\n"
            f"- endpoint order tried: "
            f"{', '.join(n for n, _ in ENDPOINTS)}\n"
            f"- mirror validation gate: ruwe / phot_g_mean_mag / "
            f"ipd_frac_multi_peak reproduce the M2 ESAC pull for all "
            f"{len(eb_ids)} EB26 targets to < 1e-5 relative -- PASS\n"
            f"- rows: {len(full)} (one per source_id; "
            f"gaia_source {len(gs)}, astrophysical_parameters {len(ap)}, "
            f"vari_summary {len(vs)})\n"
            f"- id-list provenance: EB26 {len(eb_ids)}, v2 "
            f"{v2['source_id'].nunique()}, retrieval "
            f"{ret['source_id'].nunique()} (union {len(ids)})\n"
            f"- activityindex_espcs non-null: {n_esp} of {len(full)}\n"
            f"- in vari_summary: {int(full['in_vari_summary'].sum())} of "
            f"{len(full)}\n"
            f"- sha256: {sha}\n")
    print(f"\nwrote {OUT_PARQUET} ({len(full)} rows, {len(full.columns)} "
          f"cols) in {dt:.0f}s")
    print(f"  activityindex_espcs non-null: {n_esp}/{len(full)}; "
          f"in vari_summary: {int(full['in_vari_summary'].sum())}/{len(full)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
