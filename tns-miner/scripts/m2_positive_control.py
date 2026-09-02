"""M2 step 3: re-run the M1-04 positive control under each fix, one at a time.

Same rewind, same cutoffs, same objects, same scraped TNS report times -- the only
thing that changes is which M2 fix is switched on.  That is what makes the cost of
each fix in recall a measurement rather than an assertion.

Configurations run:
    M1 baseline           (all fixes off -- must reproduce M1-04's 68.6%)
    + fix a               amplitude + flat-residual veto
    + fix c1              VSX/GCVS veto -> flag
    + fix c2              SIMBAD generic classes veto -> flag
    + fix d               negative-subtraction veto  [POST-HOC]
    M2 full               all four

Also runs the negative control (auto-reporter sample) under M1 baseline and M2
full, because a fix that raises recall by firing on everything is not a fix.

Writes out/m2_positive_control.{csv,json}.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m2_filter as F2  # noqa: E402
from m1_fetch_fink import (  # noqa: E402
    HISTORY_MAX_AGE_SECONDS,
    RESOLVE_MAX_AGE_SECONDS,
    cache_provenance,
    fetch_many,
    history_as_of,
    require_single_jd_ceiling,
    resolve_oid,
)
from m1_positive_control import sex_to_deg, to_jd  # noqa: E402
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

CONFIGS = [
    #                          a      c1     c2     d      c3
    ("M1_baseline",          F2.Config(False, False, False, False, False)),
    ("fix_a_amplitude_flat", F2.Config(True,  False, False, False, False)),
    ("fix_c1_vsx_flag",      F2.Config(False, True,  False, False, False)),
    ("fix_c2_simbad_flag",   F2.Config(False, False, True,  False, False)),
    ("fix_c3_candidate_sfx", F2.Config(False, False, False, False, True)),
    ("fix_d_negsub",         F2.Config(False, False, False, True,  False)),
    ("M2_full",              F2.M2_FULL),
]


def load(tns_csv: Path, label: str) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(tns_csv, dtype=str)
    df["disc_jd"] = df["Discovery Date (UT)"].map(to_jd)
    rt_path = DATA / "tns" / ("report_times_auto.csv" if "auto" in label
                              else "report_times.csv")
    rt = pd.read_csv(rt_path, dtype=str)[["tns_name", "first_report_ut",
                                          "first_report_group"]]
    df = df.merge(rt, left_on="Name", right_on="tns_name", how="left")
    df["report_jd"] = df["first_report_ut"].map(to_jd)

    s = session()
    oids = []
    for _, o in df.iterrows():
        nm = str(o["Disc. Internal Name"])
        if nm.startswith("ZTF"):
            oids.append(nm)
            continue
        try:
            ra, dec = sex_to_deg(o["RA"], o["DEC"])
        except Exception:
            oids.append(None)
            continue
        # Do not turn a Fink outage into a false "unresolved" control object.
        oids.append(
            resolve_oid(
                s,
                ra,
                dec,
                refresh=True,
                max_age_seconds=RESOLVE_MAX_AGE_SECONDS,
            )
        )
    df["ztf_oid"] = oids
    history_jd_ceiling = float(df["report_jd"].fillna(df["disc_jd"]).max())
    hist = fetch_many(
        [x for x in oids if x],
        refresh=True,
        max_age_seconds=HISTORY_MAX_AGE_SECONDS,
        required_coverage_jd=history_jd_ceiling,
    )
    df["history_jd_ceiling"] = history_jd_ceiling
    return df, hist


def run(df: pd.DataFrame, hist: dict, cfg: F2.Config) -> pd.DataFrame:
    rows = []
    for _, o in df.iterrows():
        oid = o["ztf_oid"]
        alerts = (
            pd.DataFrame(
                history_as_of(hist.get(oid, []), o["history_jd_ceiling"])
            )
            if oid else pd.DataFrame()
        )
        disc, rep = o["disc_jd"], o.get("report_jd")
        cutoff = rep if pd.notna(rep) else disc
        none_v = {"passed": False, "reason": "no Fink alerts at all", "channel": None,
                  "first_pass_jd": None}
        v = F2.evaluate(alerts, cfg, jd_cutoff=cutoff) if len(alerts) else none_v
        v_ep = (F2.evaluate(alerts, cfg, jd_cutoff=cutoff, jd_floor=cutoff - 60.0)
                if len(alerts) else none_v)
        n_pre = int((pd.to_numeric(alerts.get("i:jd"), errors="coerce")
                     <= cutoff).sum()) if len(alerts) else 0
        rows.append({
            "tns_name": o["Name"], "ztf_oid": oid,
            "history_jd_ceiling": o["history_jd_ceiling"],
            "obj_type": o.get("Obj. Type", ""),
            "disc_mag": o.get("Discovery Mag/Flux", ""),
            "n_alerts_pre_cutoff": n_pre,
            "recovered": bool(v["passed"]), "channel": v.get("channel"),
            "reason": v.get("reason"),
            "amp": v.get("amp"), "ptp_band": v.get("ptp_band"),
            "neg_frac": v.get("neg_frac"), "hist_span_days": v.get("hist_span_days"),
            "lead_days_vs_report": (round(cutoff - v["first_pass_jd"], 3)
                                    if v.get("first_pass_jd") else None),
            "lead_days_this_episode": (round(cutoff - v_ep["first_pass_jd"], 3)
                                       if v_ep.get("first_pass_jd") else None),
        })
    return pd.DataFrame(rows)


def summarise(res: pd.DataFrame, label: str, cfg_name: str) -> dict:
    n = len(res)
    rec = int(res["recovered"].sum())
    have = int((res["n_alerts_pre_cutoff"] > 0).sum())
    leads = res.loc[res["recovered"], "lead_days_vs_report"].dropna()
    leads_ep = res.loc[res["recovered"], "lead_days_this_episode"].dropna()
    return {
        "set": label, "config": cfg_name, "n": n,
        "n_with_prereport_alerts": have,
        "recovered": rec,
        "recall_of_all": round(rec / n, 4) if n else None,
        "recall_of_those_with_data": round(rec / have, 4) if have else None,
        "median_lead_days": (round(float(leads.median()), 3) if len(leads) else None),
        "median_lead_days_this_episode": (round(float(leads_ep.median()), 3)
                                          if len(leads_ep) else None),
        "n_lead_positive": int((leads > 0).sum()) if len(leads) else 0,
        "channels": res.loc[res["recovered"], "channel"].value_counts().to_dict(),
        "history_cache_policy": {
            "refresh": True,
            "max_age_seconds": HISTORY_MAX_AGE_SECONDS,
            "required_coverage_jd": require_single_jd_ceiling(
                res["history_jd_ceiling"].tolist(), "M2 positive control"
            ),
        },
        "history_cache_provenance": cache_provenance(
            [str(oid) for oid in res["ztf_oid"].dropna().tolist()]
        ),
    }


def main() -> None:
    out, tables = {"configs": [], "novae": {}, "losses": {}}, []
    dcap, dcap_hist = load(DATA / "tns" / "dcap_group195.csv", "DCAP_group195")
    auto, auto_hist = load(DATA / "tns" / "auto_reporter_sample.csv",
                           "auto_reporters")

    base = None
    for name, cfg in CONFIGS:
        r = run(dcap, dcap_hist, cfg)
        s = summarise(r, "DCAP_group195", name)
        if name == "M1_baseline":
            base = r.set_index("tns_name")["recovered"]
        else:
            now = r.set_index("tns_name")["recovered"]
            lost = sorted(base.index[(base) & (~now)].tolist())
            gained = sorted(base.index[(~base) & (now)].tolist())
            s["lost_vs_M1"] = lost
            s["gained_vs_M1"] = gained
            s["n_lost"] = len(lost)
            s["n_gained"] = len(gained)
            out["losses"][name] = {
                "lost": {t: r.set_index("tns_name").loc[t, "reason"] for t in lost},
                "gained": gained}
        # class behaviour on the confirmed novae -- the highest-value class
        nv = r[r["obj_type"].astype(str).str.strip() == "Nova"]
        out["novae"][name] = {
            "n": len(nv), "recovered": int(nv["recovered"].sum()),
            "detail": {t.tns_name: (bool(t.recovered), t.reason)
                       for t in nv.itertuples()}}
        out["configs"].append(s)
        r.insert(0, "config", name)
        r.insert(0, "set", "DCAP_group195")
        tables.append(r)
        print(f"[DCAP] {name:24s} recall {s['recovered']:3d}/{s['n']} = "
              f"{s['recall_of_all']:.3f}  lead {s['median_lead_days']}", flush=True)

    for name, cfg in (("M1_baseline", F2.M1_BASELINE),
                      ("M2_full", F2.M2_FULL)):
        r = run(auto, auto_hist, cfg)
        s = summarise(r, "auto_reporters", name)
        out["configs"].append(s)
        r.insert(0, "config", name)
        r.insert(0, "set", "auto_reporters")
        tables.append(r)
        print(f"[auto] {name:24s} recall {s['recovered']:3d}/{s['n']} = "
              f"{s['recall_of_all']:.3f}", flush=True)

    # contrast: target class vs the class the survey pipelines already own
    d = {c["config"]: c for c in out["configs"] if c["set"] == "DCAP_group195"}
    a = {c["config"]: c for c in out["configs"] if c["set"] == "auto_reporters"}
    out["contrast"] = {k: round(d[k]["recall_of_all"] / a[k]["recall_of_all"], 2)
                       for k in a if a[k]["recall_of_all"]}

    pd.concat(tables, ignore_index=True).to_csv(
        OUT / "m2_positive_control.csv", index=False, lineterminator="\n")
    write_text(OUT / "m2_positive_control.json", json.dumps(out, indent=2))
    print(json.dumps(out["contrast"], indent=2))


if __name__ == "__main__":
    main()
