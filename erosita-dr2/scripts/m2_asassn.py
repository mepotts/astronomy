"""M2: ASAS-SN Sky Patrol v2 light curves at priority-candidate positions.

Service: ASAS-SN Sky Patrol v2 (public, account-free; https://asas-sn.osu.edu/,
client docs http://asas-sn.ifa.hawaii.edu/skypatrol/), python client `skypatrol`
(pyasassn). Cone searches on the master_list, r=15", light curves downloaded and
summarized per target; serial + polite.

For each target: number of ASAS-SN sources within 15", and per source the g/V-band
coverage, median mag, and any excursion (>0.5 mag brightening from the median with
>=2 points) inside two windows:
  eRASS1 window   MJD 58800-59000 (2019-12 .. 2020-05, covers eRASS1 visits)
  eRASS2-3 window MJD 59000-59400 (2020-05 .. 2021-06)
plus the overall min/max epochs. Output: out/m2_asassn_summary.csv + printed notes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pyasassn.client import SkyPatrolClient

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

TARGETS = [
    # (label, ra, dec, note)
    ("3eRASS J094452.8-711152", 146.22033, -71.19802, "x57 riser, no cp, hard-detected"),
    ("3eRASS J155100.8-453347", 237.75365, -45.56327, "new-bright >=x49, M-dwarf cp?"),
    ("3eRASS J060622.5-624814", 91.59384, -62.80399, "TDE-like fader, faint galaxy"),
    ("1eRASS J034852.6-552534", 57.21948, -55.42629, "vanished = WTP 15abymdq MIR flare"),
    ("1eRASS J050338.2-304513", 75.90941, -30.75362, "fade-candidate DL242"),
    ("1eRASS J131400.5-190157", 198.50243, -19.03264, "fade-candidate DL223"),
    ("1eRASS J051910.4-253443", 79.79373, -25.57881, "fade-candidate DL157"),
    ("1eRASS J064759.4-441943", 101.99742, -44.32873, "fade-candidate DL113"),
    ("1eRASS J024930.1-274958", 42.37544, -27.83297, "fade-candidate DL106"),
    ("1eRASS J121547.0-173140", 183.94609, -17.52791, "fade-candidate DL105"),
    ("3eRASS J040311.3-023207", 60.79709, -2.53538, "riser x16, optical-faint"),
    ("3eRASS J082731.8-694520", 126.88290, -69.75563, "riser x14, optical-faint"),
]

W1 = (58800.0, 59000.0)  # ~eRASS1 era
W2 = (59000.0, 59400.0)  # ~eRASS2-3 era


def main() -> None:
    client = SkyPatrolClient(verbose=False)
    rows = []
    for label, ra, dec, note in TARGETS:
        try:
            lcs = client.cone_search(ra, dec, radius=15, units="arcsec",
                                     catalog="master_list", download=True)
        except Exception as e:
            print(f"{label}: QUERY FAILED {type(e).__name__}: {e}")
            rows.append({"label": label, "note": note, "n_sources": -1})
            continue
        data = getattr(lcs, "data", None)
        if data is None or not len(data):
            print(f"{label}: no ASAS-SN source within 15\"")
            rows.append({"label": label, "note": note, "n_sources": 0})
            continue
        for src_id, g in data.groupby("asas_sn_id"):
            g = g[np.isfinite(g["mag"]) & (g["mag_err"] < 90)]
            # detections only (ASAS-SN reports non-detections with mag ~ limit;
            # keep all, but excursions require mag_err finite)
            med = float(np.median(g["mag"]))
            r = {"label": label, "note": note, "n_sources": data["asas_sn_id"].nunique(),
                 "asas_sn_id": src_id, "n_epochs": len(g),
                 "mjd_min": float(g["jd"].min() - 2400000.5),
                 "mjd_max": float(g["jd"].max() - 2400000.5),
                 "median_mag": round(med, 3)}
            for wname, (lo, hi) in [("w1", W1), ("w2", W2)]:
                m = g[(g["jd"] - 2400000.5 >= lo) & (g["jd"] - 2400000.5 < hi)]
                r[f"{wname}_n"] = len(m)
                if len(m):
                    r[f"{wname}_min_mag"] = round(float(m["mag"].min()), 3)
                    bright = m[m["mag"] < med - 0.5]
                    r[f"{wname}_n_bright05"] = int(len(bright))
            rows.append(r)
            print(f"{label}: id={src_id} n={len(g)} med={med:.2f} "
                  f"w1_n={r.get('w1_n')} w1_min={r.get('w1_min_mag')} "
                  f"w2_n={r.get('w2_n')} w2_min={r.get('w2_min_mag')}")
    pd.DataFrame(rows).to_csv(OUT / "m2_asassn_summary.csv", index=False)
    print(f"wrote out/m2_asassn_summary.csv ({len(rows)} rows)")


if __name__ == "__main__":
    main()
