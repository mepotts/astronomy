"""M3: J0944 decision package, part 2 - anonymous public services.

All queries are account-free, one call per service, serial. Each section is
independently try/except-ed; failures are recorded, not fatal. Results go to
out/j0944_services.json.

Services (all verified anonymous):
  1. eROSITA upper-limit server (https://erosita.mpe.mpg.de/erodat/apis/#upper-limits,
     method Tubin-Arenas et al. 2024, 2024A&A...682A..35T):
     - J0944 @ DR1_eRASS1 bands 024 (0.2-2.3) + 023 (2.3-5.0): the eRASS1-epoch
       flux bound, independent of the DR1 catalog fit;
     - J0944 @ DR2_eRASSc3 bands 024 + 023: confirms counts at the position in
       the stack (presence = UL_B/UL_S, M2 machinery);
     - the M2 25-steady-pair calibration positions @ DR1_eRASS1 band 024:
       calibrates UL_B(DR1)/F1(DR1) for unchanged sources (the DR1-side
       analogue of M2's fade_frac calibration).
  2. IRSA Galactic dust service (https://irsa.ipac.caltech.edu/applications/DUST/
     docs/dustProgramInterface.html): E(B-V) SFD98 + Schlafly&Finkbeiner 2011.
  3. HEASARC w3nh column-density tool (HI4PI-based).
  4. SkyMapper DR4 public cone search (https://skymapper.anu.edu.au/how-to-access/)
     - the deepest public optical catalog that actually covers Dec -71.
  5. TAPVizieR cones at the position: Gaia DR3 (I/355), CatWISE2020 (II/365),
     VHS DR5 (II/367) - who exactly is (and is not) within 30".
  6. Legacy Surveys DR10 coverage probe (viewer cutout endpoint).
  7. Amplitude algebra from out/j0944_rows.json (r23 reconstruction, M1 caveat).
"""

from __future__ import annotations

import io
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
UL_URL = "https://erosita.mpe.mpg.de/erodat/upperlimit/service_multi"
TAPVIZ = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

RA, DEC = 146.22033015318507, -71.19802286286726
RES: dict = {"target": "3eRASS J094452.8-711152", "ra": RA, "dec": DEC,
             "queried": time.strftime("%Y-%m-%d")}


def section(name):
    def deco(fn):
        def run():
            try:
                RES[name] = fn()
                print(f"[ok] {name}")
            except Exception as e:
                RES[name] = {"error": f"{type(e).__name__}: {e}"}
                print(f"[FAILED] {name}: {type(e).__name__}: {e}")
        return run
    return deco


@section("upper_limits")
def ul_server():
    cal = pd.read_csv(OUT / "m2_ul_calibration.csv")
    body = [{"ra": RA, "dec": DEC, "band": b, "dr_survey": s}
            for s in ("DR1_eRASS1", "DR2_eRASSc3") for b in ("024", "023")]
    body += [{"ra": float(r), "dec": float(d), "band": "024",
              "dr_survey": "DR1_eRASS1"}
             for r, d in zip(cal["RA"], cal["DEC"])]
    resp = requests.post(UL_URL, json=body, timeout=600)
    resp.raise_for_status()
    js = resp.json()
    if js.get("error") not in (None, "None"):
        raise RuntimeError(js["error"])
    lim = js["limits"]
    assert len(lim) == len(body)
    out = {"j0944": lim[:4]}
    cd = pd.DataFrame(lim[4:])
    cal_frac = cd["UL_B"].to_numpy("f8") / cal["ML_FLUX_1_D1"].to_numpy("f8")
    out["dr1_calibration"] = {
        "n": len(cd),
        "ul_b_over_f1_median": float(np.median(cal_frac)),
        "ul_b_over_f1_p16": float(np.percentile(cal_frac, 16)),
        "ul_b_over_f1_p84": float(np.percentile(cal_frac, 84)),
        "note": "UL_B(DR1,024)/ML_FLUX_1(DR1) for the M2 25 steady pairs"}
    return out


@section("irsa_dust")
def irsa_dust():
    r = requests.get("https://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust",
                     params={"locstr": f"{RA} {DEC} equ j2000"}, timeout=120)
    r.raise_for_status()
    t = r.text

    def grab(tag):
        m = re.search(rf"<{tag}>\s*\(?([\d.eE+-]+)\s*\(?mag\)?\s*</{tag}>", t)
        if not m:
            m = re.search(rf"<{tag}>\s*([\d.eE+-]+)", t)
        return float(m.group(1)) if m else None

    return {"E_BV_SandF_mean": grab("meanValueSandF"),
            "E_BV_SandF_refpix": grab("refPixelValueSandF"),
            "E_BV_SFD_mean": grab("meanValueSFD"),
            "E_BV_SFD_refpix": grab("refPixelValueSFD"),
            "service": "https://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust"}


@section("heasarc_nh")
def heasarc_nh():
    r = requests.get(
        "https://heasarc.gsfc.nasa.gov/cgi-bin/Tools/w3nh/w3nh.pl",
        params={"Entry": f"{RA}, {DEC}", "NR": "GRB/SIMBAD+Sesame/NED",
                "CoordSys": "Equatorial", "equinox": "2000",
                "radius": "0.5", "usemap": "0"},
        timeout=120)
    r.raise_for_status()
    m = re.search(r"Weighted average nH \(cm\*\*-2\)\s+([\d.]+E[+-]?\d+)", r.text)
    m2 = re.search(r"h1_nh_(\w+)\.fits", r.text)
    return {"nh_weighted_avg_cm2": float(m.group(1)) if m else None,
            "map": m2.group(1) if m2 else None,
            "service": "https://heasarc.gsfc.nasa.gov/cgi-bin/Tools/w3nh/w3nh.pl"}


@section("skymapper_dr4")
def skymapper():
    r = requests.get("https://skymapper.anu.edu.au/sm-cone/public/query",
                     params={"RA": RA, "DEC": DEC, "SR": 0.01,
                             "RESPONSEFORMAT": "CSV"}, timeout=180)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    if not len(df):
        return {"n_within_36arcsec": 0, "sources": []}
    keep = [c for c in ["object_id", "raj2000", "dej2000", "g_psf", "r_psf",
                        "i_psf", "z_psf", "class_star"] if c in df.columns]
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    cc = SkyCoord(RA * u.deg, DEC * u.deg)
    sc = SkyCoord(df["raj2000"].to_numpy("f8") * u.deg,
                  df["dej2000"].to_numpy("f8") * u.deg)
    df["sep_arcsec"] = cc.separation(sc).arcsec
    df = df.sort_values("sep_arcsec")
    return {"n_within_36arcsec": int(len(df)),
            "sources": json.loads(
                df[keep + ["sep_arcsec"]].head(10).to_json(orient="records"))}


def viz_cone(viz_table: str, radius_arcsec: float) -> list[dict]:
    q = (f"SELECT TOP 50 * FROM \"{viz_table}\" WHERE "
         f"1=CONTAINS(POINT('ICRS',RAJ2000,DEJ2000),"
         f"CIRCLE('ICRS',{RA},{DEC},{radius_arcsec}/3600.))")
    r = requests.get(TAPVIZ, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                     "FORMAT": "csv", "QUERY": q}, timeout=180)
    if r.status_code != 200 or "ERROR" in r.text[:500].upper():
        # many VizieR tables use RA_ICRS/DE_ICRS instead
        q = q.replace("RAJ2000", "RA_ICRS").replace("DEJ2000", "DE_ICRS")
        r = requests.get(TAPVIZ, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                         "FORMAT": "csv", "QUERY": q},
                         timeout=180)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), low_memory=False)
    racol = "RA_ICRS" if "RA_ICRS" in df.columns else "RAJ2000"
    decol = "DE_ICRS" if "DE_ICRS" in df.columns else "DEJ2000"
    if not len(df):
        return []
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    cc = SkyCoord(RA * u.deg, DEC * u.deg)
    sc = SkyCoord(df[racol].to_numpy("f8") * u.deg,
                  df[decol].to_numpy("f8") * u.deg)
    df["sep_arcsec"] = cc.separation(sc).arcsec.round(2)
    df = df.sort_values("sep_arcsec")
    small = df.loc[:, [c for c in df.columns
                       if df[c].notna().any()]].head(8)
    return json.loads(small.to_json(orient="records"))


@section("gaia_dr3_30arcsec")
def gaia_cone():
    rows = viz_cone("I/355/gaiadr3", 30)
    keep = ["Source", "sep_arcsec", "Gmag", "BP-RP", "Plx", "e_Plx", "PM",
            "RUWE"]
    return [{k: r.get(k) for k in keep if k in r} for r in rows]


@section("catwise2020_30arcsec")
def catwise_cone():
    rows = viz_cone("II/365/catwise", 30)
    keep = ["Name", "sep_arcsec", "W1mproPM", "e_W1mproPM", "W2mproPM",
            "e_W2mproPM", "RA_ICRS", "DE_ICRS"]
    return [{k: r.get(k) for k in keep if k in r} for r in rows]


@section("vhs_dr5_30arcsec")
def vhs_cone():
    rows = viz_cone("II/367/vhs_dr5", 30)
    keep = ["Name", "SrcID", "sep_arcsec", "Jap3", "e_Jap3", "Ksap3", "e_Ksap3",
            "Mclass", "RAJ2000", "DEJ2000"]
    return [{k: r.get(k) for k in keep if k in r} for r in rows]


@section("ls10_coverage")
def ls10_probe():
    r = requests.get("https://www.legacysurvey.org/viewer/cutout.fits",
                     params={"ra": RA, "dec": DEC, "layer": "ls-dr10",
                             "size": 32, "pixscale": 1.0}, timeout=120)
    out = {"http_status": r.status_code}
    if r.status_code == 200:
        from astropy.io import fits
        with fits.open(io.BytesIO(r.content)) as h:
            data = h[0].data
        out["all_zero_or_nan"] = bool(
            np.all(~np.isfinite(data) | (data == 0)))
        out["covered"] = not out["all_zero_or_nan"]
    else:
        out["covered"] = False
    return out


@section("amplitude")
def amplitude():
    rows = json.load(open(OUT / "j0944_rows.json"))
    m, d1 = rows["dr2_main_row"], rows["dr1_row"]
    r1, e1 = d1["ML_RATE_1"], d1["ML_RATE_ERR_1"]
    r3, e3 = m["ML_RATE_1"], m["ML_RATE_ERR_1"]
    t1, t3 = d1["ML_EXP_1"], m["ML_EXP_1"]
    scale = 0.979  # M1 bright-pair median R (DR1 vs DR2 scale offset)
    r23 = (r3 * t3 - r1 * t1) / (t3 - t1)
    e23 = np.hypot(e3 * t3, e1 * t1) / (t3 - t1)
    return {
        "r1_ct_s": r1, "r1_err": e1, "t1_s": t1, "mjd1": d1["MJD"],
        "r3_stack_ct_s": r3, "r3_err": e3, "t3_s": t3,
        "stacked_ratio_R": r3 / r1, "stacked_ratio_R_scaled": r3 / r1 / scale,
        "r23_post_erass1_ct_s": float(r23), "r23_err": float(e23),
        "epoch_ratio_r23_over_r1": float(r23 / r1),
        "epoch_ratio_conservative_1sig": float((r23 - e23) / (r1 + e1)),
        "flux_ratio_stacked": m["ML_FLUX_1"] / d1["ML_FLUX_1"],
        "note": ("r23 = (r3*t3 - r1*t1)/(t3-t1) assumes the 030 stack contains "
                 "the eRASS1 counts (M1 Sect.2 caveat); scale 0.979 = M1 "
                 "bright-pair median")}


def main() -> None:
    for fn in (ul_server, irsa_dust, heasarc_nh, skymapper, gaia_cone,
               catwise_cone, vhs_cone, ls10_probe, amplitude):
        fn()
        time.sleep(1)
    with open(OUT / "j0944_services.json", "w", encoding="utf-8") as f:
        json.dump(RES, f, indent=1)
    print("wrote out/j0944_services.json")


if __name__ == "__main__":
    main()
