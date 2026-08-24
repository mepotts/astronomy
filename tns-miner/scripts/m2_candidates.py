"""M2 step 4: the final candidate list.

NOTHING HERE REPORTS ANYTHING.  This writes a CSV and a set of evidence sheets.
No TNS write path is imported, called or referenced anywhere in this repository;
the allowlist guard in tnscommon.py is untouched.

Per candidate: position, galactic latitude, magnitude and band at the passing
epoch, per-band amplitude above quiescence, the outburst history broken into
episodes, six archival cross-matches, every catalogue flag, the negative-fraction
diagnostic, the reason it passed, a plain-language one-liner, and the
pre-registered rank score of M2-01 B4.

usage: python m2_candidates.py <tag>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m1_filter as M1  # noqa: E402
import m2_filter as F2  # noqa: E402
from m2_pool import fetch_batch  # noqa: E402
from m2_vet_evidence import XCATS, summarise_xmatch, xmatch  # noqa: E402
from tnscommon import DATA, OUT, session, write_text  # noqa: E402

POOL = DATA / "pool"
EPISODE_GAP_DAYS = 30.0     # a gap longer than this separates outburst episodes


def episodes(a: pd.DataFrame) -> tuple[str, int, float]:
    """Split the clean detection history into outburst episodes.

    This is the thing M1 could not report: whether a source has erupted before,
    how often, and how bright it got each time.  Descriptive only -- no threshold.
    """
    if not len(a):
        return "", 0, float("nan")
    d = a.copy()
    d["_mjd"] = pd.to_numeric(d["i:jd"], errors="coerce") - 2400000.5
    d["_mag"] = pd.to_numeric(d["i:magpsf"], errors="coerce")
    d = d.dropna(subset=["_mjd", "_mag"]).sort_values("_mjd")
    if not len(d):
        return "", 0, float("nan")
    grp = (d["_mjd"].diff().fillna(0) > EPISODE_GAP_DAYS).cumsum()
    out, peaks = [], []
    for _g, e in d.groupby(grp):
        out.append(f"MJD {e['_mjd'].min():.1f}-{e['_mjd'].max():.1f} "
                   f"peak {e['_mag'].min():.2f} ({len(e)} det)")
        peaks.append(float(e["_mag"].min()))
    return " | ".join(out[-8:]), len(out), (min(peaks) if peaks else float("nan"))


def one_liner(r: pd.Series) -> str:
    ch, b, amp = r["channel"], r.get("gal_b"), r.get("amp")
    mag, ptp = r.get("mag_at_pass"), r.get("ptp_band")
    plane = pd.notna(b) and abs(b) < M1.GAL_PLANE_ABS_B
    where = (f"in the galactic plane (|b| = {abs(b):.1f} deg)" if plane
             else f"at |b| = {abs(b):.1f} deg" if pd.notna(b) else "at an unknown latitude")
    bits = []
    if str(r.get("flag_known_cv") or "") not in ("", "nan"):
        bits.append("ALREADY CATALOGUED AS A CV -- the outburst is real but the "
                    "object is not new; do NOT file an AT report")
    if pd.isna(r.get("gaia_DR3Name")) or not str(r.get("gaia_DR3Name") or ""):
        bits.append("no Gaia DR3 counterpart within 3 arcsec, so the quiescent "
                    "source is fainter than G~21 -- consistent with a CV or nova "
                    "progenitor")
    else:
        bits.append(f"a Gaia DR3 star sits at this position (G={r.get('gaia_Gmag')})")
    if pd.notna(r.get("atlasvs_sep")):
        bits.append(f"ATLAS variable-star counterpart {r['atlasvs_sep']}\" away "
                    f"(class {r.get('atlasvs_Class')})")
    jk = r.get("JK")
    if pd.notna(jk) and jk > 1.0 and pd.notna(r.get("gaia_BP-RP")) \
            and float(r["gaia_BP-RP"]) > 2.0:
        bits.append("VERY RED (J-K > 1, BP-RP > 2) -- the classic Mira false "
                    "positive; colour-check before doing anything")

    if ch == "A1_cv_outburst":
        head = (f"a point source has brightened by {amp:.1f} mag above its "
                f"quiescent level {where}, now at mag {mag:.1f}")
        guess = ("dwarf-nova outburst or classical nova" if plane
                 else "dwarf-nova outburst or a flare star")
    elif ch == "A2_nova_like":
        head = (f"a new point source with nothing in Pan-STARRS within 3 arcsec "
                f"{where}, mag {mag:.1f}, first detected "
                f"{r.get('hist_span_days')} d ago")
        guess = ("classical-nova shaped" if plane else
                 "a nova, a faint CV, or a supernova in an uncatalogued host")
    elif str(ch).startswith("B_"):
        head = f"inside the {str(ch)[2:]} field at mag {mag:.1f}"
        guess = "M31/M81 novae peak near this brightness"
    elif ch == "D_galactic_plane":
        head = f"{where}, mag {mag:.1f}"
        guess = "the survey pipelines report almost nothing from here at any magnitude"
    else:
        head = f"faint residue at mag {mag:.1f} {where}"
        guess = "no catalogue counterpart"
    if pd.notna(ptp):
        head += f", varying {ptp:.2f} mag peak-to-peak within one band"
    return f"{head}; {guess}. " + ". ".join(bits) + "."


def rank_score(c: pd.DataFrame) -> pd.Series:
    """M2-01 B4, declared before the list existed.  A presentation order, not a
    threshold -- nothing is removed by the score."""
    amp = pd.to_numeric(c["amp"], errors="coerce").fillna(0).clip(0, 5)
    ptp = pd.to_numeric(c["ptp_band"], errors="coerce").fillna(0).clip(0, 2)
    b = pd.to_numeric(c["gal_b"], errors="coerce").abs()
    ndet = pd.to_numeric(c["ndethist"], errors="coerce").fillna(0)
    ch = c["channel"].astype(str)
    uncat = (c["atlasvs_sep"].isna() & c["vsx_sep"].isna()
             & c["gaiavar_Class"].isna())
    knowncv = c["flag_known_cv"].astype(str).replace("nan", "") != ""
    return (2.0 * amp / 5
            + 1.5 * (b < M1.GAL_PLANE_ABS_B).astype(float)
            + 1.0 * (ch.str.startswith("A2") | ch.str.startswith("B_")).astype(float)
            + 1.0 * ptp / 2
            + 0.5 * uncat.astype(float)
            - 2.0 * knowncv.astype(float)
            - 1.0 * (ndet > 100).astype(float)).round(3)


def build(tag: str) -> pd.DataFrame:
    res = pd.read_csv(POOL / f"m2_filtered_{tag}.csv").drop_duplicates(subset=["oid"])
    c = res[res["passed"] == True].copy()  # noqa: E712
    print(f"{tag}: {len(res)} pool objects, {len(c)} pass the M2 filter "
          f"({int(res['m1_passed'].sum())} would pass the M1 baseline)")
    if not len(c):
        return c

    # --- Layer 6: positional TNS exclusion against the full 12-month harvest ---
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    t = pd.read_csv(DATA / "tns" / "tns_12mo.csv", dtype=str)
    tc = SkyCoord(t["RA"].values, t["DEC"].values, unit=(u.hourangle, u.deg))
    cc = SkyCoord(c["ra"].values * u.deg, c["dec"].values * u.deg)
    idx, d2d, _ = cc.match_to_catalog_sky(tc)
    c["tns_nearest"] = t["Name"].values[idx]
    c["tns_sep_arcsec"] = d2d.arcsec.round(2)
    in_tns = c["tns_sep_arcsec"] <= M1.TNS_MATCH_ARCSEC
    print(f"  {int(in_tns.sum())} already have a TNS object within "
          f"{M1.TNS_MATCH_ARCSEC}\" -- removed")
    c = c[~in_tns].copy().reset_index(drop=True)
    if not len(c):
        return c

    # --- archival cross-match, the panel M2-02 proved the filter needs ---------
    s = session()
    pos = pd.DataFrame({"id": range(len(c)), "ra": c["ra"].values,
                        "dec": c["dec"].values})
    xres = xmatch(s, pos, f"cand_{tag}")
    xs = summarise_xmatch(xres, {i: o for i, o in enumerate(c["oid"])})
    c = c.merge(xs, on="oid", how="left")
    for name, _cat, _rad, cols in XCATS:
        for col in [f"{name}_sep"] + [f"{name}_{x}" for x in cols]:
            if col not in c.columns:
                c[col] = np.nan
    c["JK"] = (pd.to_numeric(c["2mass_Jmag"], errors="coerce")
               - pd.to_numeric(c["2mass_Kmag"], errors="coerce")).round(2)

    # --- flags out of the JSON blob ------------------------------------------
    fl = c["flags"].fillna("{}").map(json.loads)
    for k in ("flag_vsx", "flag_gcvs", "flag_known_cv", "flag_simbad",
              "flag_simbad_target"):
        c[k] = [d.get(k, "") for d in fl]

    # --- outburst history -----------------------------------------------------
    hist = fetch_batch(s, c["oid"].tolist())
    ep, nep, pk = [], [], []
    for oid in c["oid"]:
        a = hist.get(oid, pd.DataFrame())
        e, n, p = episodes(a)
        ep.append(e[:700]); nep.append(n); pk.append(None if pd.isna(p) else round(p, 2))
    c["outburst_history"] = ep
    c["n_outburst_episodes"] = nep
    c["brightest_ever_mag"] = pk

    c["fink_link"] = "https://fink-portal.org/" + c["oid"]
    c["STATUS"] = "MATTHEW-GATED -- NOT REPORTED TO TNS"
    c["rank_score"] = rank_score(c)
    c["probably"] = c.apply(one_liner, axis=1)

    cols = ["rank_score", "oid", "STATUS", "arm", "ra", "dec", "gal_b", "channel",
            "reason", "mag_at_pass", "band_at_pass", "amp", "ptp_band",
            "n_outburst_episodes", "brightest_ever_mag", "hist_span_days",
            "neg_frac", "n_neg", "n_conf", "n_clean", "n_alerts", "ndethist",
            "drb", "sgscore1", "distpsnr1", "distnr", "magnr",
            "gaia_DR3Name", "gaia_Gmag", "gaia_Plx", "gaia_BP-RP", "JK",
            "gaiavar_Class", "vsx_Name", "vsx_Type", "vsx_sep",
            "atlasvs_Class", "atlasvs_sep", "ps1_sep",
            "flag_vsx", "flag_gcvs", "flag_known_cv", "flag_simbad", "simbad",
            "tns_nearest", "tns_sep_arcsec", "probably", "outburst_history",
            "fink_link", "first_pass_jd"]
    c = c[[x for x in cols if x in c.columns]]
    return c.sort_values("rank_score", ascending=False).reset_index(drop=True)


def main() -> None:
    tag = sys.argv[1]
    c = build(tag)
    out = OUT / f"m2_candidates_{tag}.csv"
    c.to_csv(out, index=False, lineterminator="\n")
    summary = {
        "tag": tag, "n_candidates": int(len(c)),
        "by_arm": c["arm"].value_counts().to_dict() if len(c) else {},
        "channels": c["channel"].value_counts().to_dict() if len(c) else {},
        "in_galactic_plane": (int((c["gal_b"].abs() < M1.GAL_PLANE_ABS_B).sum())
                              if len(c) else 0),
        "no_gaia_counterpart": (int(c["gaia_DR3Name"].isna().sum()) if len(c) else 0),
        "with_archival_variable_match": (
            int(((c["atlasvs_sep"].notna()) | (c["vsx_sep"].notna())
                 | (c["gaiavar_Class"].notna())).sum()) if len(c) else 0),
        "flagged_known_cv": (int((c["flag_known_cv"].astype(str) != "").sum())
                             if len(c) else 0),
        "note": "MATTHEW-GATED. Nothing in this list has been reported to TNS.",
    }
    write_text(OUT / f"m2_candidates_{tag}.json", json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
