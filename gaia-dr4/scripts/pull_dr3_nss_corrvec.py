#!/usr/bin/env python
"""M3: targeted pull of DR3 NSS `corr_vec` (+ the full parameter/error set
nsstools needs) for the sources whose class-III probabilities must be
covariance-aware.

Why a second pull: the M2 input pull (78 cols) deliberately skipped
`corr_vec` (an array column, CSV-unfriendly, unused by the deterministic
triage).  M2 Sec. 4 measured the cost: the independent-Gaussian MC
overestimates sigma(A) by a median 2.27x vs Shahaf+23's covariance-aware
e_A.  M3 closes that seam.

Source list (union, deduplicated):
  - out/amrf_class3_candidates.csv          (951 screened class-III)
  - out/amrf_class3_lowsig_retrieval.csv    (239 retrieval bin)
  - fixtures/elbadry2026_astrometric_candidates.csv (76 EB26 ground truth)
  - a seeded random validation sample of S23 table1 sources present in the
    M2 triage parquet with m1_source == 'binary_masses' (default 3000) --
    used ONLY to validate sigma(A)_corr against S23's published e_A.

Format: FORMAT=votable (corr_vec is an array; CSV would mangle it), chunks
of <= 400 source_ids per sync request, 0.5 s politeness gap, anonymous.

Exact-count guard (M2 law): the number of returned (source_id,
nss_solution_type) rows must equal the number of matching solution rows in
the M2 input parquet -- dual-solution sources (98 exist) return BOTH rows.

Output: data/dr3_nss_corrvec.parquet (+ .NOTE.md provenance).
Run   : .venv/Scripts/python.exe scripts/pull_dr3_nss_corrvec.py
"""

import datetime
import hashlib
import io
import os
import sys
import time

import numpy as np
import pandas as pd
from astropy.io.votable import parse_single_table

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"
OUT_PARQUET = os.path.join(BASE, "data", "dr3_nss_corrvec.parquet")
OUT_NOTE = os.path.join(BASE, "data", "dr3_nss_corrvec.NOTE.md")
TRIAGE_PARQUET = os.path.join(BASE, "data", "dr3_amrf_triage.parquet")

CHUNK = 400
PAUSE_S = 0.5
N_VALIDATION = 3000
SEED = 20261202

TYPES = ("'Orbital','AstroSpectroSB1','OrbitalAlternative',"
         "'OrbitalAlternativeValidated','OrbitalTargetedSearch',"
         "'OrbitalTargetedSearchValidated'")

# every column nsstools.NssSource can ask for on the 6 astrometric types
COLS = ["source_id", "nss_solution_type", "bit_index",
        "ra", "ra_error", "dec", "dec_error",
        "parallax", "parallax_error", "pmra", "pmra_error",
        "pmdec", "pmdec_error",
        "a_thiele_innes", "a_thiele_innes_error",
        "b_thiele_innes", "b_thiele_innes_error",
        "f_thiele_innes", "f_thiele_innes_error",
        "g_thiele_innes", "g_thiele_innes_error",
        "c_thiele_innes", "c_thiele_innes_error",
        "h_thiele_innes", "h_thiele_innes_error",
        "eccentricity", "eccentricity_error",
        "period", "period_error",
        "t_periastron", "t_periastron_error",
        "center_of_mass_velocity", "center_of_mass_velocity_error",
        "corr_vec"]


def sync_votable(query, timeout=300):
    import requests
    r = requests.post(ENDPOINT, data={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "votable",
        "QUERY": query}, timeout=timeout)
    r.raise_for_status()
    tab = parse_single_table(io.BytesIO(r.content)).to_table()
    # the Gaia archive returns source_id as SOURCE_ID in VOTable output
    for c in list(tab.colnames):
        if c != c.lower():
            tab.rename_column(c, c.lower())
    return tab


def build_id_list():
    ids = set()
    provenance = {}
    for tag, path in (
            ("class3", os.path.join(BASE, "out", "amrf_class3_candidates.csv")),
            ("retrieval", os.path.join(BASE, "out",
                                       "amrf_class3_lowsig_retrieval.csv")),
            ("eb26", os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))):
        s = set(pd.read_csv(path)["source_id"].astype(np.int64))
        provenance[tag] = len(s)
        ids |= s

    # validation sample: S23 table1 (has e_A) x triage parquet, tier bm
    import s23_reference
    t1 = s23_reference.load_table1()
    t1 = t1[np.isfinite(t1["e_A"]) & np.isfinite(t1["A"])]
    tri = pd.read_parquet(TRIAGE_PARQUET,
                          columns=["source_id", "m1_source"])
    bm = set(tri.loc[tri["m1_source"] == "binary_masses",
                     "source_id"].astype(np.int64))
    pool = sorted(set(t1["source_id"].astype(np.int64)) & bm - ids)
    rng = np.random.default_rng(SEED)
    val = rng.choice(np.array(pool, dtype=np.int64),
                     size=min(N_VALIDATION, len(pool)), replace=False)
    provenance["validation"] = len(val)
    ids |= set(int(x) for x in val)
    return sorted(ids), provenance, set(int(x) for x in val)


def main():
    ids, prov, val_ids = build_id_list()
    print(f"id list: {len(ids)} distinct source_ids "
          f"({', '.join(f'{k}={v}' for k, v in prov.items())})")

    # expected row count from the M2 parquet (dual-solution fan-out included)
    tri = pd.read_parquet(TRIAGE_PARQUET,
                          columns=["source_id", "nss_solution_type"])
    tri_sel = tri[tri["source_id"].isin(ids)]
    expected = len(tri_sel)
    print(f"expected solution rows (from M2 parquet): {expected}")

    frames = []
    t_start = time.time()
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        q = (f"SELECT {', '.join(COLS)} FROM gaiadr3.nss_two_body_orbit "
             f"WHERE nss_solution_type IN ({TYPES}) "
             f"AND source_id IN ({','.join(str(x) for x in chunk)})")
        t0 = time.time()
        tab = sync_votable(q)
        # corr_vec: variable-length double array -> list per row
        d = {}
        for c in COLS:
            if c == "corr_vec":
                col = tab[c]
                d[c] = [np.asarray(row).astype(float).tolist()
                        if row is not None and np.size(row) else []
                        for row in col]
            elif c in ("source_id", "bit_index"):
                d[c] = np.asarray(tab[c]).astype(np.int64)
            elif c == "nss_solution_type":
                d[c] = [str(x) for x in tab[c]]
            else:
                col = np.ma.filled(tab[c].astype(float), np.nan) \
                    if hasattr(tab[c], "mask") else np.asarray(tab[c], float)
                d[c] = col
        frames.append(pd.DataFrame(d))
        n_so_far = sum(len(f) for f in frames)
        print(f"chunk {i//CHUNK + 1}/{(len(ids)+CHUNK-1)//CHUNK}: "
              f"{len(tab)} rows in {time.time()-t0:.1f}s "
              f"(total {n_so_far}/{expected})")
        time.sleep(PAUSE_S)

    full = pd.concat(frames, ignore_index=True)
    # exact-count guard
    if len(full) != expected:
        got = set(zip(full["source_id"], full["nss_solution_type"]))
        want = set(zip(tri_sel["source_id"], tri_sel["nss_solution_type"]))
        missing = want - got
        extra = got - want
        raise RuntimeError(
            f"pull {len(full)} rows != expected {expected}; "
            f"missing={list(missing)[:5]} extra={list(extra)[:5]} -- ABORT")
    full["is_validation_sample"] = full["source_id"].isin(val_ids)
    full = full.sort_values(["source_id", "nss_solution_type"]) \
               .reset_index(drop=True)
    full.to_parquet(OUT_PARQUET, index=False)

    sha = hashlib.sha256(open(OUT_PARQUET, "rb").read()).hexdigest()
    dt = time.time() - t_start
    with open(OUT_NOTE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            f"# dr3_nss_corrvec.parquet\n\n"
            f"- pulled: {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
            f" (sync VOTable chunks of <= {CHUNK} ids, {PAUSE_S}s pause; "
            f"{dt:.0f}s total)\n"
            f"- endpoint: {ENDPOINT} (anonymous)\n"
            f"- rows: {len(full)} (hard-checked == matching solution rows in "
            f"the M2 input parquet: {expected})\n"
            f"- distinct sources: {full['source_id'].nunique()}\n"
            f"- id-list provenance: {prov}\n"
            f"- validation-sample seed: {SEED} (n={prov['validation']}, "
            f"S23 table1 x triage parquet, m1_source=binary_masses, "
            f"excluding candidate/retrieval/EB26 ids)\n"
            f"- columns: {len(full.columns)} (corr_vec kept as list column)\n"
            f"- sha256: {sha}\n")
    print(f"wrote {OUT_PARQUET} ({len(full)} rows) in {dt:.0f}s")
    print(f"solution types: {full['nss_solution_type'].value_counts().to_dict()}")


if __name__ == "__main__":
    sys.exit(main())
