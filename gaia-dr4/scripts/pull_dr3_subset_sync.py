#!/usr/bin/env python
"""M2 fallback/de-risk: sync-TAP pull of the *named* sources the milestone
depends on (BH1, BH2, El-Badry 2026's 76 candidates, S23's 177 class-III),
with exactly the column list of pull_dr3_nss_orbits.QUERY, so the triage
pipeline can run on this subset while the full async pull waits in the queue.

Sync limits (M1-verified): 2,000 rows / 60 s -- this is ~250 rows. One call.

Output: data/dr3_nss_amrf_subset.parquet
Run   : .venv/Scripts/python.exe scripts/pull_dr3_subset_sync.py
"""

import io
import os
import sys

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pull_dr3_nss_orbits import QUERY  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "dr3_nss_amrf_subset.parquet")
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"


def main():
    ids = {4373465352415301632, 5870569352746779008}  # BH1, BH2
    eb = pd.read_csv(os.path.join(BASE, "fixtures",
                                  "elbadry2026_astrometric_candidates.csv"))
    ids |= set(eb["source_id"].astype("int64"))
    import s23_reference
    ids |= set(s23_reference.load_table2()["source_id"].astype("int64"))
    print(f"{len(ids)} named sources")

    in_list = ", ".join(str(i) for i in sorted(ids))
    q = QUERY.replace(
        "WHERE n.nss_solution_type IN ('Orbital', 'AstroSpectroSB1',\n"
        "                              'OrbitalAlternative', 'OrbitalAlternativeValidated',\n"
        "                              'OrbitalTargetedSearch', 'OrbitalTargetedSearchValidated')",
        f"WHERE n.source_id IN ({in_list})")
    assert "source_id IN" in q, "WHERE replacement failed"

    r = requests.post(ENDPOINT, data={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q,
    }, timeout=120)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    print(f"sync returned {len(df)} rows, {len(df.columns)} cols")
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
