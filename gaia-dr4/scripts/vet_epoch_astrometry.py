#!/usr/bin/env python
"""M2 stretch: prototype of the DR4-day epoch-level vetting loop for AMRF
class-III candidates.

The December workflow (per queries/03_epoch_astrometry_fetch.sql header):
  1. resolve candidate DR3 source_ids -> DR4 ids via dr3_neighbourhood
     (cheap insurance: DR4 rebuilds the source list and ships the crosswalk
     table, draft data model 7.3 -- though the pre-release renumbered
     NOTHING, 12/12 ids identical to DR3; M2 correction of M1 finding #2);
  2. check has_epoch_astrometry, fetch epochs via DataLink
     (retrieval_type='EPOCH_ASTROMETRY'; NOT a TAP table; M1 finding #1);
  3. fit ESA's single-star model (gaiasupdate 'source update');
  4. read the goodness-of-fit f2 (excess_noise is None in gaiasupdate 0.1.2):
       |f2| small  -> NO astrometric wobble beyond a single star: the claimed
                      photocentre orbit has no epoch-level support -> DEMOTE
                      the candidate (spurious-orbit suspect);
       f2 large    -> wobble present -> candidate survives; hand to the
                      orbital refit (scripts/fit_prerelease_orbit_bh3.py
                      pattern) for an independent orbit.

DR3 has no epoch astrometry, so today the loop runs on the only epoch data
that exists: the 2026-06-26 DR4 pre-release sample (12 sources, of which 3
are orbit-category: Gaia BH3, HD 114762, Gaia-4). Expected outcome: exactly
the 3 orbit sources survive the f2 gate, all 9 single-star/QSO sources are
demoted -- which is the loop working end-to-end.

Output: out/epoch_vetting_prototype.csv
Run   : .venv/Scripts/python.exe scripts/vet_epoch_astrometry.py
"""

import os
import sys

import numpy as np
import pandas as pd
from astropy.table import Table

from gaiasupdate.epoch_astrometry import GaiaEpochAstrometryArchive

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(BASE, "data", "epoch-astrometry",
                   "GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml")
OUT = os.path.join(BASE, "out", "epoch_vetting_prototype.csv")

# Pre-release orbit-category sources. Identification verified 2026-08-16:
# each pre-release id exists in gaiadr3.gaia_source at the same position/G
# (all 12 of 12 -- the pre-release file did NOT renumber anything; the
# "BH3 renumbered" claim in M1-prerelease.md was wrong, see M2 doc), and
#   Gaia BH3   4318465066420528000  (Panuzzo et al. 2024 prints exactly this)
#   HD 114762  3937211745905473024  (SIMBAD + DR3 cone search, G=7.15)
#   Gaia-4     1457486023639239296  (SIMBAD: Gaia DR3 1457486023639239296)
ORBIT_SOURCES = {
    4318465066420528000: "Gaia BH3",
    3937211745905473024: "HD 114762",
    1457486023639239296: "Gaia-4",
}

# |f2| gate: single-star fits on quiet sources in this file land at |f2|<1.6
# (M1, out/supdate_results.csv); 5 is a conservative wobble threshold.
F2_GATE = 5.0


def main():
    df = Table.read(XML, format="votable").to_pandas()
    rows = []
    for sid in df["source_id"].unique():
        try:
            res = GaiaEpochAstrometryArchive.supdate(df, sid)
            f2 = float(res["solution_statistic"].f2)
            n = int(res["solution_statistic"].n_measurements)
            parallax = float(res["parameters"][2])
        except Exception as exc:  # noqa: BLE001 - report, never hide
            rows.append({"source_id": sid, "status": f"FIT FAILED: {exc!r}"})
            continue
        verdict = "KEEP (wobble present -> orbital refit)" if abs(f2) > F2_GATE \
            else "DEMOTE (no epoch-level wobble)"
        rows.append({
            "source_id": sid,
            "known_orbit": ORBIT_SOURCES.get(sid, ""),
            "n_epochs": n,
            "parallax_mas": round(parallax, 4),
            "f2_single_star": round(f2, 2),
            "verdict": verdict,
        })
    out = pd.DataFrame(rows).sort_values("f2_single_star", ascending=False)
    out.to_csv(OUT, index=False, lineterminator="\n")
    print(out.to_string(index=False))

    kept = set(out.loc[out["verdict"].str.startswith("KEEP"), "source_id"])
    expected = set(ORBIT_SOURCES)
    ok = kept == expected
    print(f"\nloop check: kept == the 3 known orbit sources -> "
          f"{'PASS' if ok else 'FAIL: ' + str(kept ^ expected)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
