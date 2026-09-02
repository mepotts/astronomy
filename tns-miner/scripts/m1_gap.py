"""M1: measure the gap on the TNS side.  Do not take the sweep's word for it.

Claims under test (from ../DISCOVERY/README.md §2 and tns-miner/README.md):
  C1  "~80% of TNS reports come from five automated pipelines
       (Pan-STARRS 26%, ZTF 17%, ALeRCE 14%, ATLAS 13%, Gaia 10%)"
  C2  "the bright end is dead -- ZTF BTS sweeps everything brighter than ~18.5"
  C3  "DCAP lives at mag 19-20.6" / the faint end is under-reported
  C4  "~90% of TNS objects sit unclassified"

Report-lag proxy: TNS object IDs are handed out in report order, so
    report_clock(ID) = running max of discovery epoch over all objects with ID <= that ID
is a lower bound on when ID was filed, tight wherever same-night auto-reporters
dominate the ID sequence.  lag = report_clock(ID) - discovery_epoch is therefore a
LOWER BOUND on each object's report lag.  Validated against the true "Time
received (UT)" scraped from TNS object pages for the DCAP set.

Reads data/tns/tns_12mo.csv.  Writes out/m1_gap.json and out/m1_gap_groups.csv.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tnscommon import DATA, OUT, write_text  # noqa: E402

FIVE = ["Pan-STARRS", "ZTF", "ALeRCE", "ATLAS", "Gaia"]


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA / "tns" / "tns_12mo.csv", dtype=str)
    df["id"] = pd.to_numeric(df["ID"], errors="coerce")
    df["mag"] = pd.to_numeric(df["Discovery Mag/Flux"], errors="coerce")
    df["disc"] = pd.to_datetime(df["Discovery Date (UT)"], utc=True, errors="coerce")
    df["groups"] = df["Reporting Group/s"].fillna("(none)")
    df["objtype"] = df["Obj. Type"].fillna("")
    return df.dropna(subset=["id"]).sort_values("id").reset_index(drop=True)


def group_shares(df: pd.DataFrame) -> pd.DataFrame:
    """A report can name several groups.  Count two ways: 'credit' (every named
    group gets one) and 'sole' (only reports naming exactly one group)."""
    credit: dict[str, int] = {}
    for v in df["groups"]:
        for p in str(v).split(","):
            p = p.strip()
            credit[p] = credit.get(p, 0) + 1
    sole = df.loc[~df["groups"].str.contains(","), "groups"].value_counts()
    rows = []
    for g, c in sorted(credit.items(), key=lambda x: -x[1]):
        rows.append({"group": g, "credit_count": c,
                     "credit_pct": round(100 * c / len(df), 2),
                     "sole_count": int(sole.get(g, 0)),
                     "sole_pct": round(100 * sole.get(g, 0) / len(df), 2)})
    return pd.DataFrame(rows)


def report_clock(df: pd.DataFrame) -> pd.Series:
    """Lower bound on report time for each ID (see module docstring)."""
    return df["disc"].cummax()


def main() -> None:
    df = load()
    out: dict = {}
    out["window"] = {
        "n_objects": int(len(df)),
        "discovery_date_min": str(df["disc"].min()),
        "discovery_date_max": str(df["disc"].max()),
        "id_min": int(df["id"].min()), "id_max": int(df["id"].max()),
        "source": "https://www.wis-tns.org/search?...&format=csv (tokenless), harvested 2026-08-24",
    }

    # --- C1: who reports -----------------------------------------------------
    gs = group_shares(df)
    gs.to_csv(OUT / "m1_gap_groups.csv", index=False, lineterminator="\n")
    top5 = gs.head(5)
    five_named = gs[gs["group"].isin(FIVE)]
    out["C1_who_reports"] = {
        "claim": "~80% from five pipelines: Pan-STARRS 26, ZTF 17, ALeRCE 14, ATLAS 13, Gaia 10",
        "n_distinct_groups": int(len(gs)),
        "top5_measured": top5[["group", "credit_pct"]].to_dict("records"),
        "top5_credit_pct_sum": round(float(top5["credit_pct"].sum()), 1),
        "the_claimed_five_credit_pct_sum": round(float(five_named["credit_pct"].sum()), 1),
        "gaia_present": bool((gs["group"] == "Gaia").any()),
        "sole_reporter_share_top5": top5[["group", "sole_pct"]].to_dict("records"),
    }

    # --- C2/C3: the magnitude distribution -----------------------------------
    m = df["mag"].dropna()
    out["C2_C3_magnitudes"] = {
        "n_with_mag": int(len(m)),
        "median": round(float(m.median()), 2),
        "quantiles": {q: round(float(m.quantile(q)), 2)
                      for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
        "frac_brighter_than_18.5": round(float((m < 18.5).mean()), 3),
        "frac_19.0_to_20.6": round(float(((m >= 19.0) & (m <= 20.6)).mean()), 3),
        "frac_fainter_than_20.6": round(float((m > 20.6).mean()), 3),
    }
    by_group = []
    for g in list(gs["group"].head(14)):
        sel = df[df["groups"].str.contains(g, regex=False)]["mag"].dropna()
        if len(sel) < 20:
            continue
        by_group.append({
            "group": g, "n": int(len(sel)),
            "median_mag": round(float(sel.median()), 2),
            "frac_19_to_20.6": round(float(((sel >= 19) & (sel <= 20.6)).mean()), 3),
            "frac_gt_20.6": round(float((sel > 20.6).mean()), 3),
        })
    out["C2_C3_magnitudes"]["by_group"] = by_group

    # --- C4: classification --------------------------------------------------
    classified = df["objtype"].str.strip() != ""
    out["C4_classification"] = {
        "n": int(len(df)),
        "n_classified": int(classified.sum()),
        "frac_unclassified": round(float((~classified).mean()), 3),
    }

    # --- report lag ----------------------------------------------------------
    df = df.copy()
    df["clock"] = report_clock(df)
    df["lag_days_lb"] = (df["clock"] - df["disc"]).dt.total_seconds() / 86400.0
    lag_rows = []
    for g in list(gs["group"].head(14)) + ["DCAP"]:
        sel = df[df["groups"].str.contains(g, regex=False)]["lag_days_lb"].dropna()
        if len(sel) < 5:
            continue
        lag_rows.append({"group": g, "n": int(len(sel)),
                         "median_lag_days_lb": round(float(sel.median()), 3),
                         "p90_lag_days_lb": round(float(sel.quantile(0.9)), 3)})
    out["report_lag_lower_bound"] = {
        "method": "running max of discovery epoch over TNS ID order; a LOWER bound",
        "all_median_days": round(float(df["lag_days_lb"].median()), 3),
        "by_group": lag_rows,
    }

    # --- validate the clock against scraped truth ----------------------------
    rt_path = DATA / "tns" / "report_times.csv"
    if rt_path.exists():
        rt = pd.read_csv(rt_path, dtype=str)
        rt["t_report"] = pd.to_datetime(rt["first_report_ut"], utc=True, errors="coerce")
        j = df.merge(rt[["tns_name", "t_report"]], left_on="Name",
                     right_on="tns_name", how="inner").dropna(subset=["t_report"])
        if len(j):
            j["true_lag"] = (j["t_report"] - j["disc"]).dt.total_seconds() / 86400.0
            j["clock_err"] = (j["t_report"] - j["clock"]).dt.total_seconds() / 86400.0
            out["clock_validation_on_DCAP"] = {
                "n": int(len(j)),
                "true_median_lag_days": round(float(j["true_lag"].median()), 3),
                "lower_bound_median_lag_days": round(float(j["lag_days_lb"].median()), 3),
                "median_clock_underestimate_days": round(float(j["clock_err"].median()), 3),
                "frac_clock_not_after_true_report": round(
                    float((j["clock_err"] >= -1e-6).mean()), 3),
            }

    write_text(OUT / "m1_gap.json", json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
