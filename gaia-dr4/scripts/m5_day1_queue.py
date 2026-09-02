#!/usr/bin/env python
"""M5 task 3: the day-one epoch-vet queue, as a REUSABLE builder.

M4 built out/epoch_vet_day1_queue.csv by hand inside
scripts/m4_acceptance_and_queue.py -- a side artifact of a one-off script.
On 2026-12-02 the queue has to fall out of the rehearsed driver, not out of
someone remembering to run a second script.  This module is the single
implementation; it is called by

  scripts/m5_acceptance_and_queue.py   (production: the DR3 v2 list)
  scripts/rehearse_dr4_day.py stage H  (the dress rehearsal, from the day's
                                        own triage output)

Queue semantics (unchanged from M4):
  rows   = main class-III list + the retrieval bin's Pr(III|corr) >= 0.999
  order  = Pr(III|corr) desc, M2_min desc as tiebreak
  cargo  = every caution flag Phase 3 needs: 1-yr alias, low-|b|,
           sigma_TI^2 > 20, X-ray-active, EB26 verdict where known,
           dust-unresolved-south, plus (M5) whichever activity flags the
           M5 discriminator test validated -- none, if it validated none.

Acceptance built INTO the builder (it refuses to write a queue that has
lost the two known systems): Gaia BH1 and BH2 must be present and be the
top two by M2_min.
"""

import os

import numpy as np
import pandas as pd

BH1, BH2 = 4373465352415301632, 5870569352746779008
KEY = ["source_id", "nss_solution_type"]
PR_RETRIEVAL_MIN = 0.999

BASE_COLS = ["p_class3_corr", "m2_min", "period", "significance",
             "sigma_ti2", "phot_g_mean_mag", "flag_alias_1yr",
             "flag_low_lat"]


def build_queue(main_df, retrieval_df, eb, xray_keys=frozenset(),
                south_unresolved=frozenset(), extra_flags=None,
                out_path=None, verbose=True):
    """Assemble the day-one epoch-vet queue.

    main_df, retrieval_df : DataFrames carrying KEY + BASE_COLS
                            (`m2_min` already renamed by the caller).
    eb                    : the EB26 verdict table (source_id, verdict).
    xray_keys             : set of (source_id, nss_solution_type) tuples
                            with an eROSITA counterpart (caution tag only).
    south_unresolved      : source_ids whose far-star dust is still
                            bracketed for lack of a southern 3D map (M5's
                            Vergely+2022 arbitration emptied this set; the
                            parameter stays so December can refill it).
    extra_flags           : optional DataFrame with source_id + boolean
                            columns to carry as extra caution flags; the
                            column names are used verbatim.  This is where
                            an ACTIVITY flag would go if the M5
                            discriminator test had validated one -- it did
                            not, so on 2026-08-18 it carries only the dust
                            robustness flag.
    Returns the queue DataFrame; writes it if out_path is given.
    """
    for name, df in (("main", main_df), ("retrieval", retrieval_df)):
        missing = [c for c in KEY + BASE_COLS if c not in df.columns]
        assert not missing, f"{name} frame missing {missing}"

    qa = main_df[KEY + BASE_COLS].copy()
    qa["queue_bin"] = "v2_main"
    qb = retrieval_df[KEY + BASE_COLS].copy()
    qb = qb[qb["p_class3_corr"] >= PR_RETRIEVAL_MIN]
    qb["queue_bin"] = "retrieval_pr999"
    q = pd.concat([qa, qb], ignore_index=True)

    q["flag_hi_sigma_ti2"] = q["sigma_ti2"] > 20.0
    qk = q[KEY].apply(tuple, axis=1)
    q["flag_xray_active"] = qk.isin(xray_keys) & (q["queue_bin"] == "v2_main")
    q["xray_tested"] = q["queue_bin"] == "v2_main"
    q["flag_dust_unresolved_south"] = q["source_id"].isin(south_unresolved)
    q = q.merge(eb[["source_id", "verdict"]], on="source_id", how="left") \
         .rename(columns={"verdict": "eb26_verdict"})
    if extra_flags is not None and len(extra_flags):
        q = q.merge(extra_flags, on="source_id", how="left")
        for c in extra_flags.columns:
            if c != "source_id":
                q[c] = q[c].astype("boolean").fillna(False).astype(bool)

    q = q.sort_values(["p_class3_corr", "m2_min"],
                      ascending=[False, False]).reset_index(drop=True)
    q.insert(0, "rank", np.arange(1, len(q) + 1))

    # ---- acceptance, inside the builder ---------------------------------
    for name, sid in (("BH1", BH1), ("BH2", BH2)):
        assert (q["source_id"] == sid).any(), \
            f"QUEUE ACCEPTANCE FAIL: {name} absent"
    top2 = set(q.sort_values("m2_min", ascending=False)
                .head(2)["source_id"].tolist())
    assert top2 == {BH1, BH2}, \
        f"QUEUE ACCEPTANCE FAIL: top-2 by M2_min is {top2}, not BH1+BH2"

    if verbose:
        print(f"  queue: {len(q)} rows "
              f"({int((q['queue_bin']=='v2_main').sum())} main + "
              f"{int((q['queue_bin']=='retrieval_pr999').sum())} retrieval); "
              f"acceptance BH1+BH2 top-2 by M2_min: PASS")
        print(f"  cautions: alias {int(q['flag_alias_1yr'].sum())}, "
              f"low-|b| {int(q['flag_low_lat'].sum())}, "
              f"sigma_TI2>20 {int(q['flag_hi_sigma_ti2'].sum())}, "
              f"X-ray {int(q['flag_xray_active'].sum())}, "
              f"EB26-spurious {int((q['eb26_verdict']=='SPURIOUS').sum())}, "
              f"dust-unresolved-south "
              f"{int(q['flag_dust_unresolved_south'].sum())}")
        head = q.head(3)[["rank", "source_id", "p_class3_corr", "m2_min",
                          "eb26_verdict"]]
        print("  head:\n" + head.to_string(index=False))
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        q.to_csv(out_path, index=False, lineterminator="\n")
        print(f"  wrote {out_path}")
    return q


def load_xray_keys(xmatch_csv):
    if not os.path.exists(xmatch_csv):
        return frozenset()
    xm = pd.read_csv(xmatch_csv)
    xr = xm[xm["route"].astype(str).str.startswith("positional")]
    return frozenset(map(tuple, xr[KEY].itertuples(index=False)))
