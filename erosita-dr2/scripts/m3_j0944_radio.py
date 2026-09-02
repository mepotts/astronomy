"""M3: J0944 decision package, part 3 - radio + gamma-ray archival cones.

Closes the blazar/jetted hypothesis loop for 3eRASS J094452.8-711152: a
radio-loud AGN bright enough to reach F_X ~ 1.6e-12 with no optical/IR
counterpart would normally be a radio source. Dec -71 is covered by:
  - SUMSS (843 MHz Molonglo survey, rms ~ 1-2 mJy): VizieR VIII/81B/sumss212
  - RACS-low DR1 (887 MHz ASKAP, rms ~ 0.25 mJy): VizieR J/other/PASA/38.58
  - Fermi-LAT 4FGL-DR4 (gamma): VizieR J/ApJS/271/27/gll_psc (r=10 arcmin -
    LAT positions are arcmin-scale)
Anonymous TAPVizieR cones; results appended into out/j0944_services.json.
"""

from __future__ import annotations

import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
TAPVIZ = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
RA, DEC = 146.22033015318507, -71.19802286286726

CONES = [
    # tag, vizier table candidates (first that works wins), radius arcsec
    ("sumss", ["VIII/81B/sumss212"], 60),
    ("racs_low", ["J/other/PASA/38.58/gausscut", "J/other/PASA/38.58/gaussreg",
                  "J/other/PASA/38.58/racs_dr1"], 60),
    ("fgl4", ["IX/72/4fgldr4"], 600),
]


def cone(table: str, radius: float) -> pd.DataFrame | None:
    for racol, decol in (("RAJ2000", "DEJ2000"), ("RA_ICRS", "DE_ICRS")):
        q = (f"SELECT TOP 20 * FROM \"{table}\" WHERE "
             f"1=CONTAINS(POINT('ICRS',{racol},{decol}),"
             f"CIRCLE('ICRS',{RA},{DEC},{radius}/3600.))")
        r = requests.get(TAPVIZ, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                         "FORMAT": "csv", "QUERY": q},
                         timeout=180)
        if r.status_code == 200 and "ERROR" not in r.text[:400].upper():
            df = pd.read_csv(io.StringIO(r.text), low_memory=False)
            df.attrs["racol"], df.attrs["decol"] = racol, decol
            return df
    return None


def main() -> None:
    res = json.load(open(OUT / "j0944_services.json"))
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    cc = SkyCoord(RA * u.deg, DEC * u.deg)

    for tag, tables, radius in CONES:
        entry = None
        for t in tables:
            df = cone(t, radius)
            if df is None:
                continue
            if not len(df):
                entry = {"table": t, "radius_arcsec": radius, "n": 0,
                         "matches": []}
                break
            sc = SkyCoord(df[df.attrs["racol"]].to_numpy("f8") * u.deg,
                          df[df.attrs["decol"]].to_numpy("f8") * u.deg)
            df["sep_arcsec"] = cc.separation(sc).arcsec.round(1)
            df = df.sort_values("sep_arcsec").head(5)
            df = df.loc[:, [c for c in df.columns if df[c].notna().any()]]
            entry = {"table": t, "radius_arcsec": radius, "n": int(len(df)),
                     "matches": json.loads(df.to_json(orient="records"))}
            break
        if entry is None:
            entry = {"error": f"no queryable table among {tables}"}
        res[tag] = entry
        print(f"[{tag}] {entry.get('table', 'FAILED')}: "
              f"n={entry.get('n', '?')} within {radius}\"")
        time.sleep(1)

    with open(OUT / "j0944_services.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("updated out/j0944_services.json")


if __name__ == "__main__":
    main()
