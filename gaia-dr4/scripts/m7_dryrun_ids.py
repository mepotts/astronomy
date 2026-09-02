#!/usr/bin/env python
"""M7 task 1, step 0: build the id sets for the day-one-scale DataLink dry run.

TWO id sets, for two different questions.

SET A -- the literal ask: all 981 members of out/epoch_vet_day1_queue.v2.csv.
  Answers "what happens when the production harness is pointed at the real
  day-one queue at real scale".  DR3 epoch photometry, however, is published
  only for the ~11.7M sources flagged `has_epoch_photometry` -- so the
  coverage of the queue is itself a measurement, and it is taken here from
  the authoritative gaia_source flag rather than assumed from vari_summary.

SET B -- the payload-stratified control, same size (981), drawn from DR3
  sources that DO serve epoch photometry, in five strata of
  vari_summary.num_selected_g_fov.  This exists because of a specific,
  named defect in M6's projection: the DataLink probe varied batch SIZE and
  therefore varied source count and payload bytes TOGETHER, leaving models A
  (transport-limited, t ~ bytes) and B (per-source server work, t ~ n) fitted
  to collinear predictors and disagreeing only in extrapolation -- which is
  what makes M6's answer a 125-857/hour band instead of a number.  Holding
  n_sources FIXED at the production batch size while payload varies several-
  fold across batches breaks that collinearity, and it is the only way to
  choose between the two models with data that exists today.

  Drawn from gaiadr3.nss_two_body_orbit JOIN gaiadr3.vari_summary so the
  control population is astrometric-binary sources -- the same kind of object
  the queue holds -- not an arbitrary variable-star sample.

Anonymous TAP only, chunked sync CSV with the M5 endpoint failover.
Run: .venv/Scripts/python.exe scripts/m7_dryrun_ids.py
"""
import io
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out", "m7_dryrun")
QUEUE = os.path.join(BASE, "out", "epoch_vet_day1_queue.v2.csv")

ENDPOINTS = [("esac", "https://gea.esac.esa.int/tap-server/tap/sync"),
             ("ari", "https://gaia.ari.uni-heidelberg.de/tap/sync"),
             ("aip", "https://gaia.aip.de/tap/sync")]
CHUNK = 400
PAUSE_S = 0.5
TIMEOUT = 300

# five payload strata, chosen to span the DR3 epoch-photometry payload range
# (num_selected_g_fov = G FoV transits served per source).  ~220 per stratum
# -> 981 after composition.
STRATA = [(20, 35), (35, 50), (50, 70), (70, 100), (100, 400)]
PER_STRATUM = 220
BATCH = 20


def _post(url, adql, timeout=TIMEOUT):
    return requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL",
                                    "FORMAT": "csv", "QUERY": adql},
                         timeout=timeout)


def query(adql, first_col, label=""):
    """Sync CSV query with endpoint failover; returns a DataFrame."""
    for name, url in ENDPOINTS:
        for _attempt in range(2):
            t0 = time.time()
            try:
                r = _post(url, adql)
                r.raise_for_status()
                if not r.text.lstrip().lower().startswith(first_col.lower()):
                    raise RuntimeError("non-CSV " + repr(r.text.lstrip()[:40]))
                df = pd.read_csv(io.StringIO(r.text))
                print("    %s %d rows in %.1fs (%s)"
                      % (label, len(df), time.time() - t0, name), flush=True)
                df.columns = [c.lower() for c in df.columns]
                return df
            except Exception as exc:                       # noqa: BLE001
                print("    %s on %s: %s after %.0fs -- retry"
                      % (label, name, type(exc).__name__, time.time() - t0),
                      flush=True)
                time.sleep(2.0)
    raise RuntimeError(label + ": every endpoint failed")


def main():
    os.makedirs(OUT, exist_ok=True)
    q = pd.read_csv(QUEUE)
    ids = q["source_id"].astype("int64").tolist()
    print("SET A: the day-one queue, %d sources" % len(ids))

    # ---- authoritative epoch-photometry coverage of the queue -------------
    frames = []
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        adql = ("SELECT source_id, has_epoch_photometry, phot_g_n_obs, "
                "phot_variable_flag, phot_g_mean_mag "
                "FROM gaiadr3.gaia_source WHERE source_id IN (%s)"
                % ",".join(str(x) for x in chunk))
        frames.append(query(adql, "source_id", "queue chunk %d" % (i // CHUNK + 1)))
        time.sleep(PAUSE_S)
    gs = pd.concat(frames, ignore_index=True)
    gs["source_id"] = gs["source_id"].astype(np.int64)
    hep = gs["has_epoch_photometry"]
    if hep.dtype == object:
        hep = hep.astype(str).str.lower().isin(["true", "t", "1"])
    gs["has_epoch_photometry"] = hep.astype(bool)
    n_ep = int(gs["has_epoch_photometry"].sum())
    print("  queue coverage: %d of %d have DR3 epoch photometry (%.1f%%)"
          % (n_ep, len(gs), 100.0 * n_ep / len(gs)))

    setA = q[["rank", "source_id", "queue_bin"]].merge(
        gs[["source_id", "has_epoch_photometry", "phot_g_n_obs",
            "phot_g_mean_mag"]], on="source_id", how="left")
    setA.to_csv(os.path.join(OUT, "setA_queue981.csv"), index=False,
                lineterminator="\n")

    # ---- SET B: payload-stratified NSS sources that DO serve --------------
    print("SET B: payload-stratified NSS + epoch-photometry control")
    parts = []
    for lo, hi in STRATA:
        adql = ("SELECT TOP %d v.source_id, v.num_selected_g_fov "
                "FROM gaiadr3.vari_summary AS v "
                "JOIN gaiadr3.nss_two_body_orbit AS n "
                "ON n.source_id = v.source_id "
                "WHERE v.num_selected_g_fov >= %d "
                "AND v.num_selected_g_fov < %d" % (PER_STRATUM, lo, hi))
        d = query(adql, "source_id", "stratum %d-%d" % (lo, hi))
        d["stratum"] = "%d-%d" % (lo, hi)
        parts.append(d)
        time.sleep(PAUSE_S)
    b = pd.concat(parts, ignore_index=True)
    b["source_id"] = b["source_id"].astype(np.int64)
    b = b.drop_duplicates("source_id")
    print("  drew %d sources across %d strata" % (len(b), b["stratum"].nunique()))
    print(b.groupby("stratum")["num_selected_g_fov"].describe()[
        ["count", "min", "50%", "max"]])

    # Compose 981 in PAYLOAD-HOMOGENEOUS batches of 20: each batch of 20 is
    # drawn from a single stratum, and the strata are cycled.  That is what
    # makes bytes-per-request vary several-fold at a FIXED source count.
    per_stratum = {s: list(g["source_id"]) for s, g in b.groupby("stratum")}
    cursor = {s: 0 for s in per_stratum}
    strata_cycle = ["%d-%d" % (lo, hi) for lo, hi in STRATA]
    order, si, target = [], 0, 981
    while len(order) < target:
        s = strata_cycle[si % len(strata_cycle)]
        si += 1
        avail = per_stratum.get(s, [])[cursor.get(s, 0):cursor.get(s, 0) + BATCH]
        cursor[s] = cursor.get(s, 0) + len(avail)
        if not avail:
            if all(cursor[k] >= len(v) for k, v in per_stratum.items()):
                break
            continue
        order.extend(avail[:min(BATCH, target - len(order))])
    setB = pd.DataFrame({"source_id": order})
    setB = setB.merge(b[["source_id", "num_selected_g_fov", "stratum"]],
                      on="source_id", how="left")
    setB.insert(0, "rank", np.arange(1, len(setB) + 1))
    setB["batch_at_20"] = (setB["rank"] - 1) // BATCH
    setB.to_csv(os.path.join(OUT, "setB_payload_stratified981.csv"),
                index=False, lineterminator="\n")
    print("  SET B written: %d sources, %d batches at batch=%d"
          % (len(setB), setB["batch_at_20"].nunique(), BATCH))
    chk = setB.groupby("batch_at_20")["num_selected_g_fov"].mean()
    print("  per-batch mean transits spans %.0f to %.0f (%.1fx) -- this is "
          "the lever that breaks M6's model degeneracy"
          % (chk.min(), chk.max(), chk.max() / max(chk.min(), 1)))

    with open(os.path.join(OUT, "id_sets.NOTE.md"), "w", newline="\n") as fh:
        fh.write(
            "# M7 dry-run id sets\n\n"
            "- built: %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            + "- SET A `setA_queue981.csv`: the %d day-one queue members; "
              "**%d (%.1f%%) have DR3 epoch photometry** "
              "(`gaiadr3.gaia_source.has_epoch_photometry`).\n"
              % (len(setA), n_ep, 100.0 * n_ep / len(gs))
            + "- SET B `setB_payload_stratified981.csv`: %d DR3 sources in "
              "`nss_two_body_orbit` that also serve epoch photometry, "
              "composed into payload-homogeneous batches of %d cycling five "
              "`num_selected_g_fov` strata (%s).\n"
              % (len(setB), BATCH,
                 ", ".join("%d-%d" % (lo, hi) for lo, hi in STRATA))
            + "- Why SET B exists: M6's throughput band is a two-model "
              "ambiguity created by a probe in which source count and "
              "payload bytes moved together. Holding n fixed at %d while "
              "payload varies across batches decorrelates them.\n" % BATCH)
    print("wrote", os.path.join(OUT, "id_sets.NOTE.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
