"""M1 positive control -- the acceptance test.

Take transients somebody ELSE reported to TNS, rewind the alert stream to the
data that existed before their report was filed, and ask whether our filter would
have flagged the object, and how much earlier.

A filter that finds nothing and a filter that is broken look identical from the
candidate list alone.  This is the only test that tells them apart.

Rewind discipline:
  * the filter sees only alerts with i:jd <= cutoff;
  * cutoff = the discovery epoch the reporter themselves claimed (strict: we must
    fire on the same data they had, not on anything later);
  * Fink's d:tns column is stamped at ingest and is not back-filled, so pre-report
    alerts genuinely carry no TNS name -- verified on ZTF26abfokua.

Writes out/m1_positive_control.csv and out/m1_positive_control.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as F  # noqa: E402
from m1_fetch_fink import fetch_many, resolve_oid  # noqa: E402
from tnscommon import DATA, OUT, session, write_text  # noqa: E402


def sex_to_deg(ra: str, dec: str) -> tuple[float, float]:
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    c = SkyCoord(str(ra), str(dec), unit=(u.hourangle, u.deg))
    return float(c.ra.deg), float(c.dec.deg)


def to_jd(s: str) -> float:
    """UT string -> JD.  TNS gives 'YYYY-MM-DD HH:MM:SS.sss'."""
    t = pd.to_datetime(s, utc=True, errors="coerce")
    if pd.isna(t):
        return np.nan
    return float(t.to_julian_date())


def run(tns_csv: Path, label: str, limit: int | None = None) -> dict:
    df = pd.read_csv(tns_csv, dtype=str)
    if limit:
        df = df.head(limit)
    df["disc_jd"] = df["Discovery Date (UT)"].map(to_jd)
    rt_path = (DATA / "tns" / ("report_times_auto.csv" if "auto" in label
                                        else "report_times.csv"))
    if rt_path.exists():
        rt = pd.read_csv(rt_path, dtype=str)
        rt = rt[["tns_name", "first_report_ut", "first_report_group"]]
        df = df.merge(rt, left_on="Name", right_on="tns_name", how="left")
        df["report_jd"] = df["first_report_ut"].map(to_jd)
    else:
        df["report_jd"] = np.nan
        df["first_report_ut"] = None

    # Most reporters file their OWN internal name (DCAP uses "DCAP<n>"), so the
    # ZTF objectId has to be recovered by position.  3" = TNS's duplicate radius.
    s = session()
    oids = []
    for _, o in df.iterrows():
        nm = str(o["Disc. Internal Name"])
        if nm.startswith("ZTF"):
            oids.append(nm)
            continue
        try:
            ra, dec = sex_to_deg(o["RA"], o["DEC"])
            oids.append(resolve_oid(s, ra, dec))
        except Exception:
            oids.append(None)
    df["ztf_oid"] = oids
    n_res = sum(1 for x in oids if x)
    print(f"[{label}] {len(df)} TNS objects, {n_res} resolved to a ZTF objectId",
          flush=True)

    hist = fetch_many([x for x in oids if x])

    rows = []
    for _, o in df.iterrows():
        oid = o["ztf_oid"]
        alerts = pd.DataFrame(hist.get(oid, [])) if oid else pd.DataFrame()
        disc = o["disc_jd"]
        rep = o.get("report_jd")
        # the deadline we had to beat is when the winning report was FILED.
        cutoff = rep if pd.notna(rep) else disc
        none_v = {"passed": False, "reason": "no Fink alerts at all", "channel": None,
                  "first_pass_jd": None, "n_clean": 0, "n_alerts": 0}

        # (1) primary rewind: everything Fink held at the instant the report landed
        v_pre = F.evaluate(alerts, jd_cutoff=cutoff) if len(alerts) else none_v
        # (2) strict rewind: only the reporter's own discovery exposure and earlier
        v_strict = F.evaluate(alerts, jd_cutoff=disc + 1e-3) if len(alerts) else none_v
        # (3) this-episode-only: CVs recur, so the all-time first pass can be an
        #     eruption years back.  Floor at 60 d for the lead time of THIS event.
        v_epi = (F.evaluate(alerts, jd_cutoff=cutoff, jd_floor=cutoff - 60.0)
                 if len(alerts) else none_v)
        # (4) unrestricted: does the object EVER pass?  separates "filter rejects
        #     this class" from "the data was not there yet at the cutoff".
        v_all = F.evaluate(alerts) if len(alerts) else none_v

        n_pre = int((pd.to_numeric(alerts.get("i:jd"), errors="coerce")
                     <= cutoff).sum()) if len(alerts) else 0

        rows.append({
            "tns_name": o["Name"],
            "ztf_oid": oid,
            "reporting_groups": o["Reporting Group/s"],
            "obj_type": o.get("Obj. Type", ""),
            "disc_mag": o.get("Discovery Mag/Flux", ""),
            "disc_filter": o.get("Discovery Filter", ""),
            "disc_ut": o["Discovery Date (UT)"],
            "disc_jd": disc,
            "report_ut": o.get("first_report_ut"),
            "report_jd": rep,
            "report_lag_days": (round(rep - disc, 3) if pd.notna(rep) else None),
            "n_alerts_total": len(alerts),
            "n_alerts_pre_cutoff": n_pre,
            "recovered_pre_report": v_pre["passed"],
            "channel_pre": v_pre.get("channel"),
            "reason_pre": v_pre.get("reason"),
            "first_pass_jd": v_pre.get("first_pass_jd"),
            "lead_days_vs_report": (
                round(cutoff - v_pre["first_pass_jd"], 3)
                if v_pre.get("first_pass_jd") else None),
            "lead_days_this_episode": (
                round(cutoff - v_epi["first_pass_jd"], 3)
                if v_epi.get("first_pass_jd") else None),
            "recovered_at_discovery_epoch": v_strict["passed"],
            "mag_at_pass": v_pre.get("mag_at_pass"),
            "ever_passes": v_all["passed"],
            "channel_ever": v_all.get("channel"),
            "reason_ever": v_all.get("reason"),
            "tns_internal_name": o["Disc. Internal Name"],
        })

    res = pd.DataFrame(rows)
    n = len(res)
    rec = int(res["recovered_pre_report"].sum())
    ever = int(res["ever_passes"].sum())
    have_data = int((res["n_alerts_pre_cutoff"] > 0).sum())
    leads = res.loc[res["recovered_pre_report"], "lead_days_vs_report"].dropna()
    leads_ep = res.loc[res["recovered_pre_report"], "lead_days_this_episode"].dropna()
    strict = int(res["recovered_at_discovery_epoch"].sum())

    summary = {
        "label": label,
        "n_objects": n,
        "n_with_prereport_alerts_in_fink": have_data,
        "n_recovered_pre_report": rec,
        "recovery_fraction_of_all": round(rec / n, 3) if n else None,
        "recovery_fraction_of_those_with_data": round(rec / have_data, 3) if have_data else None,
        "n_ever_passes": ever,
        "n_recovered_at_discovery_epoch_strict": strict,
        "recovery_fraction_strict": round(strict / n, 3) if n else None,
        "median_lead_days_vs_report": (round(float(leads.median()), 3)
                                       if len(leads) else None),
        "mean_lead_days_vs_report": (round(float(leads.mean()), 3)
                                     if len(leads) else None),
        "median_lead_days_this_episode": (round(float(leads_ep.median()), 3)
                                          if len(leads_ep) else None),
        "n_lead_positive": int((leads > 0).sum()) if len(leads) else 0,
        "channels": res.loc[res["recovered_pre_report"], "channel_pre"]
                       .value_counts().to_dict(),
        "top_rejection_reasons": res.loc[~res["recovered_pre_report"], "reason_pre"]
                                    .str.replace(r"[\d.]+", "N", regex=True)
                                    .value_counts().head(10).to_dict(),
    }
    return {"summary": summary, "table": res}


def main() -> None:
    out_all = {}
    tables = []
    for tag, path in [("DCAP_group195", DATA / "tns" / "dcap_group195.csv"),
                      ("auto_reporters", DATA / "tns" / "auto_reporter_sample.csv")]:
        if not path.exists():
            print(f"skip {tag}: {path} missing")
            continue
        r = run(path, tag)
        out_all[tag] = r["summary"]
        t = r["table"]
        t.insert(0, "set", tag)
        tables.append(t)
        print(json.dumps(r["summary"], indent=2))

    if tables:
        full = pd.concat(tables, ignore_index=True)
        full.to_csv(OUT / "m1_positive_control.csv", index=False, lineterminator="\n")
    write_text(OUT / "m1_positive_control.json", json.dumps(out_all, indent=2))


if __name__ == "__main__":
    main()
