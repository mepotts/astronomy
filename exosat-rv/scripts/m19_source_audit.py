"""Audit: is there ANY other orbit-capable companion archive we missed?

Two probes against ESO TAP (dbo.raw, CRIRES, SCIENCE, 2021-06 onward = CRIRES+ era):

1. The full target lists of every programme known to observe companions for RVs
   (the Hoy pilot + its successors + the 2025 survey programme that observed
   CT Cha B / GSC 08047-00232 B). If those teams have banked nights on targets we
   have not inventoried, this finds them.
2. A name-pattern sweep: every OBJECT observed >= 4 distinct nights, flagged if it
   looks like a companion designation (endswith ' B'/' b'/'-B' etc.) — catching
   companion campaigns filed under names outside the M5/M7 lists.

Prints night counts per object with public/embargo split. Purely read-only.
"""
import time
from collections import defaultdict

import requests

TAP = "https://archive.eso.org/tap_obs/sync"
PROGS = ["110.23RW", "111.24M0", "111.24KV", "113.268Y", "113.26UN", "113.26DT",
         "115.285K", "115.287U", "114.27C6"]


def tap(query, tries=5):
    for k in range(tries):
        try:
            r = requests.get(TAP, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                          "FORMAT": "json", "QUERY": query},
                             timeout=180)
            r.raise_for_status()
            j = r.json()
            cols = [c["name"] for c in j["metadata"]]
            return [dict(zip(cols, row)) for row in j["data"]]
        except Exception as e:  # noqa: BLE001
            print(f"  retry {k+1}: {e}")
            time.sleep(10 * (k + 1))
    raise RuntimeError("TAP down")


def night_table(rows):
    per = defaultdict(lambda: {"nights": set(), "pub": set(), "progs": set(),
                               "bands": set()})
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        o = (r.get("object") or "?").strip()
        d = (r.get("date_obs") or "?")[:10]
        per[o]["nights"].add(d)
        per[o]["progs"].add((r.get("prog_id") or "?")[:8])
        per[o]["bands"].add((r.get("filter_path") or "?").split(",")[0])
        if (r.get("release_date") or "9") <= now:
            per[o]["pub"].add(d)
    return per


print("[1] full target lists of the known companion-RV programmes")
clauses = " OR ".join(f"prog_id LIKE '{p}%'" for p in PROGS)
rows = tap(f"""
    SELECT object, date_obs, prog_id, filter_path, release_date
    FROM dbo.raw
    WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE' AND ({clauses})
    """)
per = night_table(rows)
print(f"{'object':<26}{'nights':>7}{'public':>8}  bands / progs")
for o in sorted(per, key=lambda o: -len(per[o]["nights"])):
    p = per[o]
    print(f"{o:<26}{len(p['nights']):>7}{len(p['pub']):>8}  "
          f"{'/'.join(sorted(p['bands']))} | {','.join(sorted(p['progs']))}")

print("\n[2] any companion-looking OBJECT with >=4 nights, whole CRIRES+ era")
rows = tap("""
    SELECT object, date_obs, prog_id, filter_path, release_date
    FROM dbo.raw
    WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE'
      AND date_obs > '2021-06-01'
    """)
per = night_table(rows)
KNOWN = {"CD-35 2722 B", "ETA TEL B", "HR-7329-B", "BET PIC B", "AB PIC B",
         "CT CHA B", "GSC 08047-00232 B", "HD 42581 B", "GJ 229 B", "2M0103AB B"}


def companion_like(o):
    u = o.upper().rstrip()
    return (u.endswith(" B") or u.endswith("-B") or u.endswith(" B2")
            or u.endswith("B") and ("PIC" in u or "CHA" in u or "TEL" in u)
            or " B " in u)


cands = [(o, p) for o, p in per.items()
         if len(p["nights"]) >= 4 and companion_like(o) and o.upper() not in KNOWN]
print(f"{'object':<30}{'nights':>7}{'public':>8}  bands / progs")
for o, p in sorted(cands, key=lambda t: -len(t[1]["nights"])):
    print(f"{o:<30}{len(p['nights']):>7}{len(p['pub']):>8}  "
          f"{'/'.join(sorted(p['bands']))} | {','.join(sorted(p['progs']))}")
if not cands:
    print("  (none beyond the known set)")
