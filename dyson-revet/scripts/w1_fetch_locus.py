"""W1 helper: empirical M-dwarf photospheric WISE color locus.

The Pecaut & Mamajek 2013 dwarf table has no W1-W2 / W1-W3 / W1-W4 colors for
K6V-M4.5V, and blackbody colors are wrong by ~0.2 mag there (checked at K5V:
blackbody W1-W3 = +0.20 vs PM13 empirical -0.029). Hephaistos II built its
star+DS models from 265 in-sample template stars with clean photometry
(Sec 2.2, Appendix A) -- not published. This script builds the equivalent:
nearby dwarfs with clean, significant W3/W4 detections, giving median
(W1-W2), (W1-W3), (W1-W4) vs M_G.

Query (ESA Gaia TAP, anonymous): parallax > 33.3 mas (<30 pc), RUWE < 1.4,
AllWISE match with W3/W4 measured, cc_flags 0000, ext_flag 0; local
sigma-clipping per M_G bin rejects genuine-excess stars (debris disks).

Output: data/photometry/mdwarf_wise_locus_raw.csv, .../mdwarf_wise_locus.csv
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyvo

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "photometry"
RAW = DATA / "mdwarf_wise_locus_raw.csv"
OUT = DATA / "mdwarf_wise_locus.csv"

# distance for these <30 pc template stars: 1000/parallax (Bailer-Jones and
# 1/plx agree to <1% at plx>33 mas; avoids the slow external-table join)
Q = """
SELECT g.source_id, g.phot_g_mean_mag, g.phot_bp_mean_mag, g.phot_rp_mean_mag,
       g.parallax, g.ruwe,
       w.w1mpro, w.w2mpro, w.w3mpro, w.w4mpro,
       w.w1mpro_error, w.w2mpro_error, w.w3mpro_error, w.w4mpro_error,
       w.cc_flags, w.ext_flag, w.ph_qual
FROM gaiadr3.gaia_source AS g
JOIN gaiadr3.allwise_best_neighbour AS ab ON ab.source_id = g.source_id
JOIN gaiadr1.allwise_original_valid AS w ON w.allwise_oid = ab.allwise_oid
WHERE g.parallax > 33.3 AND g.ruwe < 1.4
  AND w.w3mpro_error IS NOT NULL AND w.w4mpro_error IS NOT NULL
  AND w.ext_flag = 0
"""


def main() -> None:
    if RAW.exists():
        df = pd.read_csv(RAW)
        print(f"cached raw locus sample: {len(df)}")
    else:
        svc = pyvo.dal.TAPService("https://gea.esac.esa.int/tap-server/tap")
        df = svc.run_async(Q).to_table().to_pandas()
        df["r_med_geo"] = 1000.0 / df["parallax"]
        df.to_csv(RAW, index=False)
        print(f"pulled {len(df)} nearby dwarfs with W3+W4 detections")

    df = df[df["cc_flags"].astype(str).str.strip().isin(["0000", "0"])]
    df["mg"] = df["phot_g_mean_mag"] + 5 - 5 * np.log10(df["r_med_geo"])
    df["snr3"] = 1.0857 / df["w3mpro_error"]
    df["snr4"] = 1.0857 / df["w4mpro_error"]
    df = df[(df["mg"] > 6.5) & (df["mg"] < 14.0)
            & (df["snr3"] > 8) & (df["snr4"] > 4)]
    df["w12"] = df["w1mpro"] - df["w2mpro"]
    df["w13"] = df["w1mpro"] - df["w3mpro"]
    df["w14"] = df["w1mpro"] - df["w4mpro"]
    print(f"clean locus sample after cuts: {len(df)}")

    rows = []
    bins = np.arange(6.5, 14.01, 0.5)
    for lo, hi in zip(bins[:-1], bins[1:]):
        s = df[(df["mg"] >= lo) & (df["mg"] < hi)]
        if len(s) < 5:
            continue
        rec = {"mg": 0.5 * (lo + hi), "n": len(s)}
        for c in ("w12", "w13", "w14"):
            v = s[c].to_numpy()
            med, mad = np.median(v), 1.4826 * np.median(np.abs(v - np.median(v)))
            keep = np.abs(v - med) < 2.0 * max(mad, 0.05)   # clip real excesses
            rec[c] = float(np.median(v[keep]))
            rec[c + "_scatter"] = float(np.std(v[keep]))
            rec[c + "_nkeep"] = int(keep.sum())
        rows.append(rec)
    locus = pd.DataFrame(rows)
    locus.to_csv(OUT, index=False)
    print(locus.to_string(index=False))


if __name__ == "__main__":
    main()
