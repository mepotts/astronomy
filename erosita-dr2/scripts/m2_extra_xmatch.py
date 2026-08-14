"""M2: two follow-up X-Match calls prompted by the vetting.

  - SRG/ART-XC all-sky catalog (4-12 keV, surveys 1-8 updated 18-Jul-2025,
    vizier:J/A+A/687/A183/catalog, Sazonov et al.): same platform + epochs as
    eROSITA; an independent detection channel for hard/bright candidates.
  - eRASS1 Galactic transients (vizier:J/MNRAS/544/885/ero-g-t, Maan, Katira &
    Mooley 2025): did they already flag any of our objects?

Appends columns to out/m2_archival_xray.csv (artxc_*, mkm_*).
"""

from __future__ import annotations

import io

from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
XMATCH_URL = "http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync"


def xmatch(t: pd.DataFrame, cat: str, radius: float) -> pd.DataFrame:
    resp = requests.post(
        XMATCH_URL,
        data={"request": "xmatch", "distMaxArcsec": radius, "RESPONSEFORMAT": "csv",
              "colRA1": "RA", "colDec1": "DEC", "cat2": cat},
        files={"cat1": ("cands.csv", t[["tid", "RA", "DEC"]].to_csv(index=False))},
        timeout=600,
    )
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text), low_memory=False)


def main() -> None:
    m = pd.read_csv(OUT / "m2_archival_xray.csv")
    m = m[[c for c in m.columns if not c.startswith(("artxc_", "mkm_"))]]
    t = m[["tid", "RA", "DEC"]]

    g = xmatch(t, "vizier:J/A+A/687/A183/catalog", 30)
    print(f"ART-XC matches: {len(g)} rows; columns: {list(g.columns)[:20]}")
    if len(g):
        g = g.sort_values("angDist").groupby("tid", as_index=False).first()
        keep = {"tid": "tid", "angDist": "artxc_sep"}
        for cand in ["Name", "Flux", "Signi", "CName", "NewXray", "Type", "z"]:
            if cand in g.columns:
                keep[cand] = f"artxc_{cand.lower()}"
        m = m.merge(g[list(keep)].rename(columns=keep), on="tid", how="left")

    g2 = xmatch(t, "vizier:J/MNRAS/544/885/ero-g-t", 30)
    print(f"eRASS1-Galactic-transient matches: {len(g2)} rows; "
          f"columns: {list(g2.columns)[:20]}")
    if len(g2):
        g2 = g2.sort_values("angDist").groupby("tid", as_index=False).first()
        keep = {"tid": "tid", "angDist": "mkm_sep"}
        for cand in ["IAUName", "FeRASS1", "F2RXS", "Dist", "Lum"]:
            if cand in g2.columns:
                keep[cand] = f"mkm_{cand.lower()}"
        m = m.merge(g2[list(keep)].rename(columns=keep), on="tid", how="left")

    m.to_csv(OUT / "m2_archival_xray.csv", index=False)
    print("updated out/m2_archival_xray.csv")
    if "artxc_sep" in m.columns:
        hit = m[m["artxc_sep"].notna()]
        print(f"ART-XC: {len(hit)} touched sources matched")
    if "mkm_sep" in m.columns:
        hit = m[m["mkm_sep"].notna()]
        print(f"MKM eRASS1 transients: {len(hit)} touched sources matched")
        print(hit[["name", "mkm_sep"] +
                  [c for c in hit.columns if c.startswith("mkm_") and c != "mkm_sep"]
                  ].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
