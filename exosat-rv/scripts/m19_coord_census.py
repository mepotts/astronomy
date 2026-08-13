"""The watertight census: coordinate-clustered CRIRES+ holdings vs every companion
we care about — names never enter, so host-name filing, typos, and unknown
programmes cannot hide a campaign.

1. One ESO TAP pull: all CRIRES SCIENCE frames since 2021-06 (CRIRES+ era) with
   ra/dec/date/mode/release.
2. Target list: the M7 survey's 38 companions (coordinates resolved via SIMBAD,
   using the M5 simbad_id where known) PLUS the young self-luminous planets
   discovered after the survey's source list (AF Lep b, HD 206893 c, GQ Lup b,
   kappa And b, GJ 504 b, HD 95086 b).
3. For each target: frames within 20 arcsec -> nights, modes, bands, public split.

Prints every target with >=2 nights and flags ones absent from all previous
sweeps. Read-only; single heavy query with patient retries (the portal is busy
serving our own downloads).
"""
import json
import time
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TAP = "https://archive.eso.org/tap_obs/sync"
SIMBAD = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"

EXTRA = ["AF Lep b", "HD 206893c", "GQ Lup b", "* kap And b", "GJ  504b",
         "HD 95086b"]
KNOWN = {"CD-35 2722 B", "ETA TEL B", "BET PIC", "BET PIC B", "AB PIC B",
         "CT CHA B", "GSC 08047-00232 B", "HD  1160", "HD 26820", "HD 42581 B",
         "HR-7329-B", "2M0103AB B", "HIP 64892B", "CD-26 8623B"}


def get(url, params, tries=6, timeout=240):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            print(f"  retry {k + 1}: {str(e)[:100]}")
            time.sleep(20 * (k + 1))
    raise RuntimeError(f"unreachable: {url}")


def simbad_coords(ident):
    q = (f"SELECT ra, dec FROM basic JOIN ident ON oidref = oid "
         f"WHERE id = '{ident}'")
    j = get(SIMBAD, {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                     "QUERY": q})
    d = j["data"]
    return (float(d[0][0]), float(d[0][1])) if d else None


def main():
    # target list
    targets = {}
    m5 = json.loads((ROOT / "data" / "m5-targets.json").read_text(encoding="utf-8"))
    id_by_eso = {r["eso_object"]: r.get("simbad_id") for r in m5}
    m7 = json.loads((ROOT / "data" / "m7-survey.json").read_text(encoding="utf-8"))
    names = [r["name"] for r in m7["targets"]] + EXTRA
    for n in names:
        ident = id_by_eso.get(n) or n
        try:
            c = simbad_coords(ident)
            if c is None and ident != n:
                c = simbad_coords(n)
            if c is None:
                print(f"  unresolved: {n}")
                continue
            targets[n] = c
        except Exception as e:  # noqa: BLE001
            print(f"  SIMBAD fail {n}: {str(e)[:80]}")
    print(f"resolved {len(targets)} targets")

    print("pulling full CRIRES+ era frame list (yearly windows beat the row cap)...")
    frames = []
    for y0, y1 in (("2021-06-01", "2022-06-01"), ("2022-06-01", "2023-06-01"),
                   ("2023-06-01", "2024-06-01"), ("2024-06-01", "2025-06-01"),
                   ("2025-06-01", "2026-06-01"), ("2026-06-01", "2027-06-01")):
        j = get(TAP, {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                      "MAXREC": "1000000",
                      "QUERY": f"""
            SELECT object, ra, dec, date_obs, filter_path, dp_tech, release_date
            FROM dbo.raw
            WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE'
              AND date_obs >= '{y0}' AND date_obs < '{y1}'
            """}, timeout=420)
        cols = [c["name"] for c in j["metadata"]]
        chunk = [dict(zip(cols, row)) for row in j["data"]]
        print(f"  {y0[:4]}/{y1[:4]}: {len(chunk)} frames")
        frames.extend(chunk)
    print(f"{len(frames)} frames total")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    box = 20.0 / 3600.0
    report = []
    for name, (ra, dec) in targets.items():
        hits = [f for f in frames
                if f["ra"] is not None and abs(f["dec"] - dec) < box
                and abs(f["ra"] - ra) < box / max(abs(__import__("math").cos(
                    __import__("math").radians(dec))), 1e-3)]
        if not hits:
            continue
        nights = defaultdict(lambda: {"n": 0, "modes": set(), "bands": set(),
                                      "objs": set(), "pub": False})
        for f in hits:
            d = (f["date_obs"] or "?")[:10]
            x = nights[d]
            x["n"] += 1
            x["modes"].add((f["dp_tech"] or "?").split(",")[1]
                           if "," in (f["dp_tech"] or "") else (f["dp_tech"] or "?"))
            x["bands"].add((f["filter_path"] or "?").split(",")[0])
            x["objs"].add((f["object"] or "?").strip())
            if (f["release_date"] or "9") <= now:
                x["pub"] = True
        objs = sorted({o for x in nights.values() for o in x["objs"]})
        report.append((name, nights, objs))

    report.sort(key=lambda t: -len(t[1]))
    print(f"\n{'target':<24}{'nights':>7}{'public':>8}  filed as / modes")
    for name, nights, objs in report:
        if len(nights) < 2:
            continue
        pub = sum(1 for x in nights.values() if x["pub"])
        modes = sorted({m for x in nights.values() for m in x["modes"]})
        new = "" if any(o.upper() in KNOWN for o in objs) else "  <-- NEW"
        print(f"{name:<24}{len(nights):>7}{pub:>8}  {', '.join(objs)[:44]} | "
              f"{'/'.join(modes)[:22]}{new}")

    out = ROOT / "data" / "m19-coord-census.json"
    out.write_text(json.dumps(
        [{"target": n, "nights": {k: {"n": v["n"],
                                      "bands": sorted(v["bands"]),
                                      "objs": sorted(v["objs"]),
                                      "public": v["pub"]}
                                  for k, v in sorted(ns.items())},
          "filed_as": o} for n, ns, o in report], indent=2), encoding="utf-8")
    print(f"\nwrote {out.name}")


if __name__ == "__main__":
    main()
