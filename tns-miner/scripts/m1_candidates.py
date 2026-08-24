"""M1 step 5: turn a filtered pool into a Matthew-gated candidate list.

NOTHING HERE REPORTS ANYTHING.  This writes a CSV.  No TNS write path is imported,
called, or referenced anywhere in this repository.

Per candidate: position, magnitude and band at the passing epoch, detection
history, nearest catalogued source and separation, why it passed, and a
plain-language guess at what it is.

Also does the final TNS exclusion: a 3" positional cross-match against the full
12-month TNS harvest, on top of Fink's own per-alert d:tns column.

usage: python m1_candidates.py <tag> [--window-tag <tag-for-json>]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as F  # noqa: E402
from m1_fetch_fink import fetch_one  # noqa: E402
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

POOL = DATA / "pool"


def tns_positions() -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    t = pd.read_csv(DATA / "tns" / "tns_12mo.csv", dtype=str)
    c = SkyCoord(t["RA"].values, t["DEC"].values, unit=(u.hourangle, u.deg))
    return c.ra.deg, c.dec.deg, t


def one_liner(r: pd.Series) -> str:
    """Plain language, and honest about the sign of the amplitude.

    outburst_amp = magnr - magpsf: the quiescent reference-image magnitude of the
    nearest source minus the difference-image magnitude of the transient.
    POSITIVE means the new light outshines whatever was there -- a real outburst.
    NEGATIVE means the variation is smaller than the star it sits on, which is a
    much weaker case and must be said so rather than dressed up as a brightening.
    """
    ch = r["channel"]
    b = r.get("gal_b")
    mag = r.get("mag_at_pass")
    amp = r.get("outburst_amp")
    plane = (not pd.isna(b)) and abs(b) < F.GAL_PLANE_ABS_B
    where = (f"galactic plane (|b| = {abs(b):.1f} deg)" if plane
             else f"|b| = {abs(b):.1f} deg" if pd.notna(b) else "unknown latitude")

    if ch == "A1_cv_outburst":
        if pd.notna(amp) and amp >= 1.0:
            what = (f"a catalogued point source has brightened by {amp:.1f} mag "
                    "above its quiescent level")
            guess = ("a dwarf-nova outburst or a classical nova" if plane
                     else "a dwarf-nova outburst or a flare star")
        elif pd.notna(amp) and amp > 0:
            what = f"a catalogued point source is up {amp:.1f} mag"
            guess = "a low-amplitude variable; weak case without a colour or a longer baseline"
        else:
            what = ("a variation on a catalogued point source that is FAINTER than "
                    "the source itself" + (f" ({amp:.1f} mag)" if pd.notna(amp) else ""))
            guess = ("not an outburst on this evidence -- most likely ordinary "
                     "variability or a subtraction residual")
        return f"{what}, {where}; {guess}"

    if ch == "A2_nova_like":
        return (f"a new point source with nothing in Pan-STARRS within 3 arcsec, "
                f"{where}, mag {mag:.1f}; "
                + ("classical-nova shaped" if plane else
                   "could be a nova, a faint CV, or a supernova in an uncatalogued host"))
    if ch and ch.startswith("B_"):
        return (f"inside the {ch[2:]} field at mag {mag:.1f}; "
                "M31/M81 novae peak near this brightness")
    if ch == "D_galactic_plane":
        return (f"{where}, mag {mag:.1f} -- the survey pipelines report almost "
                "nothing from here at any magnitude")
    if ch == "C_faint_residue":
        return f"faint residue at mag {mag:.1f}, {where}, no catalogue counterpart"
    return "unclassified pass"


def build(tag: str) -> pd.DataFrame:
    res = pd.read_csv(POOL / f"filtered_{tag}.csv").drop_duplicates(subset=["oid"])
    cands = res[res["passed"] == True].copy()  # noqa: E712
    print(f"{tag}: {len(res)} pool objects, {int(res['passed'].sum())} pass the filter")
    if not len(cands):
        return cands

    # --- final TNS exclusion by position -------------------------------------
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    tra, tdec, tdf = tns_positions()
    tc = SkyCoord(tra * u.deg, tdec * u.deg)
    cc = SkyCoord(cands["ra"].values * u.deg, cands["dec"].values * u.deg)
    idx, d2d, _ = cc.match_to_catalog_sky(tc)
    cands["tns_nearest"] = tdf["Name"].values[idx]
    cands["tns_sep_arcsec"] = d2d.arcsec.round(2)
    in_tns = cands["tns_sep_arcsec"] <= F.TNS_MATCH_ARCSEC
    print(f"  {int(in_tns.sum())} already have a TNS object within "
          f"{F.TNS_MATCH_ARCSEC}\" -- removed")
    cands = cands[~in_tns].copy()

    # --- detection history + outburst amplitude ------------------------------
    s = session()
    hist_rows = []
    for _, r in cands.iterrows():
        a = pd.DataFrame(fetch_one(s, r["oid"]))
        if len(a):
            a["i:jd"] = pd.to_numeric(a["i:jd"], errors="coerce")
            a["i:magpsf"] = pd.to_numeric(a["i:magpsf"], errors="coerce")
            fid = pd.to_numeric(a.get("i:fid"), errors="coerce")
            bands = {1: "g", 2: "r", 3: "i"}
            hist = "; ".join(
                f"{(row['i:jd']-2400000.5):.4f} {bands.get(int(f), '?')}="
                f"{row['i:magpsf']:.2f}"
                for (_, row), f in zip(a.sort_values("i:jd").iterrows(),
                                       fid[a.sort_values("i:jd").index].fillna(0))
                if pd.notna(row["i:magpsf"]))
            magnr = pd.to_numeric(a.get("i:magnr"), errors="coerce")
            amp = (float(magnr.median() - a["i:magpsf"].min())
                   if magnr.notna().any() else np.nan)
            # Variability diagnostic.  A difference-image source that sits at a
            # CONSTANT magnitude for weeks is not a transient -- it is the
            # signature of a source missing from (or mis-subtracted in) the
            # reference image.  Nothing in the pre-registered filter tests this,
            # and on live data it is the dominant contaminant, so measure it and
            # say so.  Peak-to-peak of magpsf in the passing band over the 60 days
            # ending at the last alert.
            # MUST be computed PER BAND.  Mixing g and r makes any constant
            # source with a 1.5 mag colour look like a 1.5 mag variable -- which
            # is exactly how ZTF26aabkpvd first read as the strongest candidate
            # in the list when it is in fact flat in both filters.
            jd_hi = float(a["i:jd"].max())
            a["_fid"] = pd.to_numeric(a.get("i:fid"), errors="coerce")
            win = a[(a["i:jd"] >= jd_hi - 60) & a["i:magpsf"].notna()]
            ptps, n_win = [], 0
            for _fid, grp in win.groupby("_fid"):
                if len(grp) >= 2:
                    ptps.append(float(grp["i:magpsf"].max() - grp["i:magpsf"].min()))
                n_win = max(n_win, len(grp))
            ptp = max(ptps) if ptps else np.nan
            first_mjd = float(a["i:jd"].min() - 2400000.5)
            last_mjd = float(a["i:jd"].max() - 2400000.5)
            ndet = int(len(a))
            simbad = next((v for v in a.get("d:cdsxmatch", pd.Series(dtype=str))
                           if not F._isnull(v)), "")
        else:
            hist, amp, first_mjd, last_mjd, ndet, simbad = "", np.nan, np.nan, np.nan, 0, ""
            ptp, n_win = np.nan, 0
        hist_rows.append({"detection_history_mjd_band_mag": hist[:900],
                          "ptp_mag_60d": None if pd.isna(ptp) else round(ptp, 2),
                          "n_alerts_60d_maxband": n_win,
                          "outburst_amp": None if pd.isna(amp) else round(amp, 2),
                          "first_alert_mjd": first_mjd, "last_alert_mjd": last_mjd,
                          "n_alerts_total": ndet, "simbad_class": simbad})
    cands = pd.concat([cands.reset_index(drop=True),
                       pd.DataFrame(hist_rows)], axis=1)

    cands["nearest_catalogued_source"] = np.where(
        cands["distpsnr1"].fillna(999) <= 5,
        "PS1 source, sgscore=" + cands["sgscore1"].round(2).astype(str),
        "none within 5 arcsec")
    cands["nearest_sep_arcsec"] = cands["distpsnr1"].round(2)
    cands["probably"] = cands.apply(one_liner, axis=1)
    cands["ztf_link"] = "https://fink-portal.org/" + cands["oid"]
    cands["STATUS"] = "MATTHEW-GATED -- NOT REPORTED TO TNS"

    # --- triage tier -------------------------------------------------------
    # NOT a filter change: the pre-registered filter's output is unaltered and
    # every passing object stays in the CSV.  This is a stated RANKING, applied
    # after the fact and declared here, because the fresh pass exposed something
    # the positive control could not: the filter has no amplitude requirement, so
    # on live data it is dominated by low-amplitude variability sitting on
    # catalogued point sources.  amp = magnr - magpsf; positive means the new
    # light outshines the quiescent source.
    #   tier A -- amp >= 1.5, or channel A2/B (no quiescent source to compare to)
    #   tier B -- 0.5 <= amp < 1.5
    #   tier C -- amp < 0.5 or unmeasurable: passes the filter, weak on its face
    #   FLAT override -- a candidate whose magnitude varies by less than 0.3 mag
    #   peak-to-peak across >=3 alerts in the 60 days ending at its last detection
    #   is a constant residual, not a transient, and drops to tier C whatever its
    #   apparent amplitude.  0.3 mag is below ZTF's own scatter at mag ~20, so
    #   there is no variability left to claim.
    amp = pd.to_numeric(cands["outburst_amp"], errors="coerce")
    ptp = pd.to_numeric(cands["ptp_mag_60d"], errors="coerce")
    nw = pd.to_numeric(cands["n_alerts_60d_maxband"], errors="coerce").fillna(0)
    ch = cands["channel"].astype(str)
    flat = (nw >= 3) & (ptp < 0.3)
    cands["flat_residual"] = flat
    tier = np.where(
        (amp >= 1.5) | ch.str.startswith("A2") | ch.str.startswith("B_"), "A",
        np.where(amp >= 0.5, "B", "C"))
    cands["tier"] = np.where(flat, "C", tier)

    cols = ["oid", "STATUS", "tier", "flat_residual", "ra", "dec", "gal_b",
            "channel", "reason", "ptp_mag_60d", "n_alerts_60d_maxband",
            "mag_at_pass", "band_at_pass", "first_pass_jd",
            "outburst_amp", "n_clean", "n_alerts_total",
            "first_alert_mjd", "last_alert_mjd",
            "nearest_catalogued_source", "nearest_sep_arcsec", "distnr", "magnr",
            "drb", "simbad_class", "tns_nearest", "tns_sep_arcsec",
            "probably", "detection_history_mjd_band_mag", "ztf_link"]
    cands = cands[[c for c in cols if c in cands.columns]]
    cands["_amp"] = pd.to_numeric(cands["outburst_amp"], errors="coerce").fillna(-9)
    cands = cands.sort_values(["tier", "_amp"], ascending=[True, False])                  .drop(columns="_amp")
    return cands


def main() -> None:
    tag = sys.argv[1]
    c = build(tag)
    out = OUT / f"m1_candidates_{tag}.csv"
    c.to_csv(out, index=False, lineterminator="\n")
    summary = {"tag": tag, "n_candidates": int(len(c)),
               "tiers": c["tier"].value_counts().to_dict() if len(c) else {},
               "n_flat_residual": int(c["flat_residual"].sum()) if len(c) else 0,
               "channels": c["channel"].value_counts().to_dict() if len(c) else {},
               "in_galactic_plane": int((c["gal_b"].abs() < F.GAL_PLANE_ABS_B).sum())
               if len(c) else 0,
               "note": "MATTHEW-GATED. Nothing in this list has been reported to TNS."}
    write_text(OUT / f"m1_candidates_{tag}.json", json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
