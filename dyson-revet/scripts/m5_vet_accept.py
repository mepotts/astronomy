"""M5 PR-1's acceptance test: does the Gator upload backend return the SAME
V1/V2 rows as the TAP route M3 and M4 actually ran?

PR-1 permits a faster cross-match backend "only if it passes an acceptance
test first: on the identical position list it must return the identical
AllWISE and All-Sky rows as the existing TAP path, matched
designation-for-designation, with the disagreements counted and reported
whatever they are."

Ground truth is `out/m3_vet_cache_{tag}.csv`, which M4 produced through the
TAP path on the full 1,545-position survivor list.  This script re-fetches the
same positions through Gator and compares.  It changes nothing and decides
nothing; it prints and files the comparison.

Run:
    python scripts/m5_vet_accept.py --tag m4_g0.1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "out"

from m3_vet_survivors import gator_chunks, nearest_match   # noqa: E402

V1_COLS = ("designation,ra,dec,w3mpro,w3sigmpro,w4mpro,w4sigmpro,w3snr,w4snr,"
           "w3nm,w4nm,w3m,w4m,w3flg,w4flg,nb,na,w3rchi2,w4rchi2,ph_qual,"
           "cc_flags,ext_flg,var_flg")
V2_COLS = ("designation,ra,dec,w3mpro,w3sigmpro,w4mpro,w4sigmpro,w3snr,w4snr,"
           "ph_qual,cc_flags,w3flg,w4flg")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m4_g0.1")
    a = ap.parse_args()

    truth = pd.read_csv(OUT / f"m3_vet_cache_{a.tag}.csv")
    surv = pd.read_csv(OUT / f"w4_previsual_candidates_{a.tag}.csv")
    if len(truth) != len(surv):
        raise SystemExit(f"cache has {len(truth)} rows, survivor list {len(surv)}")
    ra, dec = surv["ra"].to_numpy(), surv["dec"].to_numpy()
    print(f"acceptance test on {len(surv):,} positions "
          f"(truth = out/m3_vet_cache_{a.tag}.csv, the TAP run M4 completed)")

    rep: dict[str, object] = {"n_positions": int(len(surv))}
    for rel, table, cols, sfx in [
            ("V1 AllWISE", "allwise_p3as_psd", V1_COLS, "_aw"),
            ("V2 All-Sky", "allsky_4band_p3as_psd", V2_COLS, "_as")]:
        g = gator_chunks(table, cols, ra, dec, 3.0, tag=f"accept{sfx}",
                         part=(ROOT / "data" / "nebular" / "cache"
                               / f"m5_vet_accept_{a.tag}{sfx}.part.csv"))
        # namespace exactly as the vetting driver does, so the comparison is
        # of the SAME quantity the verdicts are computed from
        got = nearest_match(surv.copy(), g[[c for c in cols.split(",")]],
                            sfx, 3.0)
        dt, dg = truth.get(f"designation{sfx}"), got.get(f"designation{sfx}")
        dt = pd.Series([""] * len(truth)) if dt is None else dt.fillna("")
        dg = pd.Series([""] * len(got)) if dg is None else dg.fillna("")
        same = (dt.astype(str).str.strip().to_numpy()
                == dg.astype(str).str.strip().to_numpy())
        both_null = (dt.astype(str).str.strip() == "") & (dg.astype(str).str.strip() == "")
        tap_only = int(((dt.astype(str).str.strip() != "")
                        & (dg.astype(str).str.strip() == "")).sum())
        gat_only = int(((dt.astype(str).str.strip() == "")
                        & (dg.astype(str).str.strip() != "")).sum())
        r: dict[str, object] = {
            "matched_designation": int(same.sum()),
            "both_no_match": int(both_null.sum()),
            "tap_matched_gator_did_not": tap_only,
            "gator_matched_tap_did_not": gat_only,
            "disagreeing_designations": int((~same & ~both_null).sum()
                                            - tap_only - gat_only),
        }
        # photometric agreement on the rows both matched
        num = [c for c in ("w3mpro", "w4mpro", "w3snr", "w4snr", "w3nm", "w4nm",
                           "w3flg", "w4flg") if f"{c}{sfx}" in truth.columns
               and f"{c}{sfx}" in got.columns]
        for c in num:
            x = pd.to_numeric(truth[f"{c}{sfx}"], errors="coerce").to_numpy()
            y = pd.to_numeric(got[f"{c}{sfx}"], errors="coerce").to_numpy()
            ok = np.isfinite(x) & np.isfinite(y) & same
            r[f"max_abs_diff_{c}"] = (float(np.nanmax(np.abs(x[ok] - y[ok])))
                                      if ok.sum() else None)
        pq_t = truth.get(f"ph_qual{sfx}")
        pq_g = got.get(f"ph_qual{sfx}")
        if pq_t is not None and pq_g is not None:
            m = same & pq_t.notna() & pq_g.notna()
            r["ph_qual_identical"] = int((pq_t[m].astype(str).str.strip()
                                          == pq_g[m].astype(str).str.strip()).sum())
            r["ph_qual_compared"] = int(m.sum())
        rep[rel] = r
        print(f"\n== {rel} ==")
        for k, v in r.items():
            print(f"  {k:34s} {v}")

    (OUT / f"m5_vet_accept_{a.tag}.json").write_text(json.dumps(rep, indent=2))
    print(f"\nwrote out/m5_vet_accept_{a.tag}.json")


if __name__ == "__main__":
    main()
