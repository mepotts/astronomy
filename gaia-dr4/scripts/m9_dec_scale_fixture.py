#!/usr/bin/env python
"""M9: the December-scale epoch-astrometry FIXTURE for the full-chain rehearsal.

WHAT THIS IS, AND WHAT IT IS NOT
================================
M7 measured the transport half of December at 981-row scale (DR3
EPOCH_PHOTOMETRY, real network, real batching).  M8 measured the analysis
half at 981-row scale (synthetic verdict stores).  Nobody has ever run the
PRODUCTION chain -- harness -> orbital refit arm -> v2 verdict store ->
pre-registered labels -- as one thing, at scale, because the fitting half
needs epoch ASTROMETRY and exactly twelve sources of it exist in the world
(the 2026-06-26 pre-release file; M8 sec.1a).

This script manufactures the only stand-in that is honest: it gives each of
the 981 day-one queue members a DONOR epoch-astrometry table drawn from
those twelve real sources, written into its own cache directory under the
harness's own atomic per-source cache convention.  The harness then runs
`--source cache` over the real 981-row queue and produces a real 981-row
verdict store through the real adjudication code path, and the refit arm
consumes it.

THE FIXTURE IS NOT DATA.  Every artifact it produces is written under a
release tag that says so ("Gaia DR4 M9 rehearsal Dec-scale fixture"), into
`data/epoch_cache/<tag>/` and `out/verdicts_dec_rehearsal/`, and NEVER into
`out/verdicts/` (which is what `--verdicts all` reads on release day) or
`out/verdicts_v2/`.  A fabricated verdict that can reach December's real
analysis is exactly the failure M8 sec.3a refused to ship.

DECLARED GENERATIVE MODEL (written before the run, house rule since M8)
======================================================================
seed 20261202, one deterministic draw per queue member in rank order:

  0.90  FULL donor    -- one of the 12 pre-release sources, uniform.
                         3 of the 12 are orbit sources (Gaia BH3,
                         HD 114762, Gaia-4) and 9 are quiet, so this
                         reproduces the harness's own measured 3:9 split,
                         which is the "0.33:1" ratio the pre-registration
                         (sec.4) already lists as a projected December split.
  0.05  THIN donor    -- a full donor truncated to THIN_TRANSITS *rows*,
                         which must come back INCONCLUSIVE (verdict RULE 1).
  0.05  NO donor      -- no cache file at all, which must come back NO_DATA
                         (verdict RULE 4).

CORRECTION, made after the first chain run and recorded rather than hidden.
THIN_TRANSITS was first set to 30 "CCD transits", and the INCONCLUSIVE arm
NEVER FIRED: all 47 thin rows came back SPURIOUS/CONFIRMED exactly like the
full ones.  The reason is a unit mismatch that the ledger's own column names
invite: **a row of the raw epoch table is one FIELD-OF-VIEW transit, and
gaiasupdate expands each into ~8.5 CCD transits**, so 30 raw rows became 255
`n_transits_used` -- five times the MIN_TRANSITS=50 gate.  This is M8
landmine #13 again (a control that does not change what the test reads is
worse than none), and it was caught the same way: the arm's numbers came out
indistinguishable from the arm it was supposed to differ from.  THIN_TRANSITS
is now **4 raw FoV rows ~= 34 CCD transits**, and the fixture ASSERTS after
the run that every rule actually fired.

The last two exist because the rehearsal is worthless if it only ever walks
the two happy paths.  M6's five verdict rules have never all fired in one
run; at 981 rows they do.

The donor's `source_id` column is rewritten to the queue member's id, so the
frame is internally consistent and `gaiasupdate` is asked about exactly the
source the harness thinks it is fitting.

  .venv\\Scripts\\python.exe scripts\\m9_dec_scale_fixture.py --build
  .venv\\Scripts\\python.exe scripts\\m9_dec_scale_fixture.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epoch_vet_harness as H                                    # noqa: E402

QUEUE = os.path.join(BASE, "out", "epoch_vet_day1_queue.v2.csv")
FIXTURE_RELEASE = "Gaia DR4 M9 rehearsal Dec-scale fixture"
MANIFEST = os.path.join(BASE, "data", "epoch_cache",
                        H.release_tag(FIXTURE_RELEASE), "MANIFEST.json")
NOTE = os.path.join(BASE, "data", "epoch_cache",
                    H.release_tag(FIXTURE_RELEASE), "README.NOTE.md")

SEED = 20261202
P_FULL, P_THIN, P_NONE = 0.90, 0.05, 0.05
THIN_TRANSITS = 4          # raw FoV rows, NOT CCD transits (see the docstring)

# the three pre-release sources that carry a real photocentre orbit (M6
# stage F: 3/3 CONFIRMED, 9/9 SPURIOUS, every f2 agreeing with M3's
# prototype to 0.005)
ORBIT_DONORS = {4318465066420528000, 3937211745905473024, 1457486023639239296}


def _draw(n, seed=SEED):
    rng = np.random.default_rng(seed)
    u = rng.random(n)
    kind = np.where(u < P_FULL, "full",
                    np.where(u < P_FULL + P_THIN, "thin", "none"))
    return kind, rng


def build(queue_path=QUEUE, verbose=True, seed=SEED):
    t0 = time.time()
    q = pd.read_csv(queue_path)
    q["source_id"] = q["source_id"].astype("int64")
    src = H.PrereleaseSource()
    donors = src.all_ids()
    frames = {d: src.fetch([d])[d] for d in donors}
    kind, rng = _draw(len(q), seed=seed)
    pick = rng.integers(0, len(donors), size=len(q))

    d = H.cache_dir(FIXTURE_RELEASE)
    rows = []
    n_written = 0
    for i, (sid, k) in enumerate(zip(q["source_id"].tolist(), kind)):
        donor = int(donors[int(pick[i])])
        rec = {"source_id": int(sid), "queue_rank": int(q["rank"].iloc[i]),
               "kind": str(k), "donor_source_id": donor,
               "donor_is_orbit": donor in ORBIT_DONORS}
        if k == "none":
            # deliberately no file: the harness must answer NO_DATA
            p = H.cache_path(FIXTURE_RELEASE, sid)
            if os.path.exists(p):
                os.remove(p)
            rec["n_ccd"] = 0
            rows.append(rec)
            continue
        df = frames[donor].copy()
        if k == "thin":
            df = df.iloc[:THIN_TRANSITS].reset_index(drop=True)
        df["source_id"] = np.int64(sid)
        H.cache_write(FIXTURE_RELEASE, sid, df)
        n_written += 1
        rec["n_ccd"] = int(len(df))
        rows.append(rec)
        if verbose and i and i % 200 == 0:
            print(f"    {i}/{len(q)} fixture rows, {time.time()-t0:.0f}s",
                  flush=True)

    man = pd.DataFrame(rows)
    expect = {
        "CONFIRMED": int(((man["kind"] == "full") & man["donor_is_orbit"]).sum()),
        "SPURIOUS": int(((man["kind"] == "full") & ~man["donor_is_orbit"]).sum()),
        "INCONCLUSIVE": int((man["kind"] == "thin").sum()),
        "NO_DATA": int((man["kind"] == "none").sum()),
    }
    payload = {
        "what": "M9 December-scale full-chain rehearsal fixture -- NOT DATA",
        "release_tag": FIXTURE_RELEASE,
        "queue": os.path.relpath(queue_path, BASE),
        "n_queue": int(len(q)), "n_cache_files": n_written,
        "seed": int(seed), "p_full": P_FULL, "p_thin": P_THIN, "p_none": P_NONE,
        "thin_transits": THIN_TRANSITS,
        "donors": [int(x) for x in donors],
        "orbit_donors": sorted(int(x) for x in ORBIT_DONORS),
        "declared_expectation": expect,
        "produced_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "build_seconds": round(time.time() - t0, 2),
        "rows_sha256": hashlib.sha256(
            man.to_csv(index=False).encode()).hexdigest()[:16],
    }
    with open(MANIFEST, "w", newline="\n", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    man.to_csv(os.path.join(d, "fixture_rows.csv"), index=False,
               lineterminator="\n")
    with open(NOTE, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(_note_text(payload))
    if verbose:
        print(f"fixture built: {n_written} cache files in {d}")
        print(f"  declared expectation {expect}")
        print(f"  manifest {os.path.relpath(MANIFEST, BASE)} "
              f"({payload['build_seconds']}s)")
    return man, payload


def _note_text(p):
    return f"""# `data/epoch_cache/{H.release_tag(FIXTURE_RELEASE)}/` — a REHEARSAL FIXTURE, not data

**This directory does not contain Gaia data for the sources it is keyed by.**
It is the M9 December-scale full-chain rehearsal fixture: each of the
{p['n_queue']} day-one queue members is given a *donor* epoch-astrometry table
copied from one of the twelve real pre-release sources
(`data/epoch-astrometry/GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml`,
2026-06-26), with the donor's `source_id` column rewritten to the queue
member's id so the frame is internally consistent.

Why it exists: the production chain (harness → orbital refit arm → v2
verdict store → pre-registered labels) has a fitting half that consumes
epoch astrometry, and twelve sources of it exist in the world before
2026-12-02. Running the chain at December's 981-row scale is the only way to
find what breaks at scale; this is the only honest stand-in.

**Nothing here may reach a science artifact.** The verdicts it produces are
written to `out/verdicts_dec_rehearsal/`, never to `out/verdicts/` (which is
what `--verdicts all` reads) or `out/verdicts_v2/`. The release tag on every
record says `{FIXTURE_RELEASE}`.

Declared generative model (fixed before the build, seed {p['seed']}):
{p['p_full']:.2f} full donor / {p['p_thin']:.2f} donor truncated to
{p['thin_transits']} CCD transits (must return INCONCLUSIVE) /
{p['p_none']:.2f} no file at all (must return NO_DATA).

Declared expectation: {json.dumps(p['declared_expectation'])}

Built {p['produced_utc']} by `scripts/m9_dec_scale_fixture.py`.
Delete freely — `--build` regenerates it deterministically.
"""


def check_rules_fired(ledger_path, verbose=True):
    """Every verdict rule must actually fire, or the rehearsal is only
    walking the happy paths.  M8 landmine #13: a control that does not
    change what the test reads is worse than none -- and the way it shows
    up is an arm whose numbers are indistinguishable from the arm it was
    meant to differ from."""
    led = pd.read_csv(ledger_path)
    man = pd.read_csv(os.path.join(H.cache_dir(FIXTURE_RELEASE),
                                   "fixture_rows.csv"))
    got = led["verdict"].value_counts().to_dict()
    p = json.load(open(MANIFEST, encoding="utf-8"))
    want = p["declared_expectation"]
    ok = True
    if verbose:
        print("verdict rules fired (declared -> observed):")
    for k in ("CONFIRMED", "SPURIOUS", "INCONCLUSIVE", "NO_DATA"):
        g, w = int(got.get(k, 0)), int(want.get(k, 0))
        hit = g == w
        ok &= hit
        if verbose:
            print("  %-13s %5d -> %5d  %s" % (k, w, g,
                                              "OK" if hit else "MISMATCH"))
    m = man.merge(led[["source_id", "verdict", "n_transits_used"]],
                  on="source_id", how="left")
    thin = m[m["kind"] == "thin"]
    if verbose and len(thin):
        print("  thin arm: %d rows, n_transits_used median %.0f, "
              "verdicts %s" % (len(thin), thin["n_transits_used"].median(),
                               thin["verdict"].value_counts().to_dict()))
    return ok


def verify(verbose=True):
    if not os.path.exists(MANIFEST):
        print("no manifest -- run --build first")
        return False
    p = json.load(open(MANIFEST, encoding="utf-8"))
    d = H.cache_dir(FIXTURE_RELEASE)
    n = len([f for f in os.listdir(d) if f.endswith(".parquet")])
    ok = n == p["n_cache_files"]
    if verbose:
        print(f"fixture {os.path.relpath(d, BASE)}: {n} cache files "
              f"(manifest says {p['n_cache_files']}) -> "
              f"{'OK' if ok else 'MISMATCH'}")
        print(f"  declared expectation {p['declared_expectation']}")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--queue", default=QUEUE)
    ap.add_argument("--seed", type=int, default=SEED,
                    help="declared-variant seed: re-drawing the donor "
                         "assignment is the falsifier for any apparent "
                         "signal in a store whose verdicts are supposed to "
                         "be independent of every metric")
    ap.add_argument("--check-ledger", default=None,
                    help="assert every verdict rule actually fired")
    a = ap.parse_args(argv)
    if a.build:
        build(queue_path=a.queue, seed=a.seed)
    if a.check_ledger:
        return 0 if check_rules_fired(a.check_ledger) else 1
    if a.verify or not a.build:
        return 0 if verify() else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
