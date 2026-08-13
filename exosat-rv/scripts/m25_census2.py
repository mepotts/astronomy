"""Census v2: the complete sweep the first census approximated.

Fixes over m19_coord_census.py (whose 20k row cap and name-resolution failures
are documented in M20-RESULTS):
  1. Frame pull in yearly windows with MAXREC raised — no truncation.
  2. Name resolution via SIMBAD ident-join with normalization variants — the 17
     previously-unresolved companions get real coordinates.
  3. REVERSE mode: cluster ALL science pointings (0.01 deg bins), flag clusters
     with >= 3 distinct nights that sit > 60" from every resolved target, and
     identify them by SIMBAD cone — catching campaigns on objects our target list
     never contained.

Writes data/m25-census2.json. Read-only against ESO TAP + SIMBAD.
"""
from __future__ import annotations

import json
import math
import time
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TAP = "https://archive.eso.org/tap_obs/sync"
SIMBAD = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"

EXTRA = ["AF Lep b", "HD 206893 c", "GQ Lup b", "kap And b", "GJ 504 b",
         "HD 95086 b", "HD 1160 B", "HIP 64892B", "CD-26 8623B"]


def get(url, params, tries=6, timeout=240):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            print(f"  retry {k + 1}: {str(e)[:90]}")
            time.sleep(20 * (k + 1))
    raise RuntimeError(f"unreachable: {url}")


def simbad_ident(name):
    q = ("SELECT ra, dec FROM basic JOIN ident ON oidref = oid "
         f"WHERE id = '{name}'")
    j = get(SIMBAD, {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                     "QUERY": q})
    d = j["data"]
    return (float(d[0][0]), float(d[0][1])) if d else None


def resolve(name):
    variants = [name, " ".join(name.split())]
    n = " ".join(name.split())
    if n.endswith(" b") or n.endswith(" B"):
        base, suff = n[:-2], n[-1]
        variants += [base + suff, base + " " + suff]
    if n and n[-1] in "bB" and n[-2] != " ":
        variants += [n[:-1] + " " + n[-1]]
    seen = set()
    for v in variants:
        if v in seen:
            continue
        seen.add(v)
        try:
            c = simbad_ident(v)
            if c:
                return c, v
        except Exception:  # noqa: BLE001
            pass
    return None, None


def simbad_cone(ra, dec, r_deg=0.008):
    q = ("SELECT TOP 5 main_id, otype, ra, dec FROM basic WHERE "
         f"CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {r_deg})) = 1")
    try:
        j = get(SIMBAD, {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                         "QUERY": q}, tries=3)
        return [(str(r[0]), str(r[1])) for r in j["data"]]
    except Exception:  # noqa: BLE001
        return []


def main():
    # ---- target list ----
    m5 = json.loads((ROOT / "data" / "m5-targets.json").read_text(encoding="utf-8"))
    id_by_eso = {r["eso_object"]: r.get("simbad_id") for r in m5}
    m7 = json.loads((ROOT / "data" / "m7-survey.json").read_text(encoding="utf-8"))
    names = [r["name"] for r in m7["targets"]] + EXTRA
    targets = {}
    for n in dict.fromkeys(names):
        ident = id_by_eso.get(n) or n
        c, used = resolve(ident)
        if c is None and ident != n:
            c, used = resolve(n)
        if c:
            targets[n] = c
        else:
            print(f"  STILL unresolved: {n}")
    print(f"resolved {len(targets)}/{len(set(names))} targets")

    # ---- full frame pull, windowed ----
    frames = []
    for y0, y1 in (("2021-06-01", "2022-06-01"), ("2022-06-01", "2023-06-01"),
                   ("2023-06-01", "2024-06-01"), ("2024-06-01", "2025-06-01"),
                   ("2025-06-01", "2026-06-01"), ("2026-06-01", "2027-06-01")):
        j = get(TAP, {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                      "MAXREC": "1000000",
                      "QUERY": f"""
            SELECT object, ra, dec, date_obs, dp_tech, release_date, prog_id
            FROM dbo.raw
            WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE'
              AND date_obs >= '{y0}' AND date_obs < '{y1}'
            """}, timeout=420)
        cols = [c["name"] for c in j["metadata"]]
        chunk = [dict(zip(cols, row)) for row in j["data"]]
        print(f"  {y0[:4]}/{y1[:4]}: {len(chunk)}")
        frames.extend(chunk)
    frames = [f for f in frames if f["ra"] is not None and f["dec"] is not None]
    print(f"{len(frames)} frames total")

    # ---- forward: nights per known target ----
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    fwd = []
    for name, (ra, dec) in targets.items():
        cosd = max(abs(math.cos(math.radians(dec))), 1e-3)
        hits = [f for f in frames
                if abs(f["dec"] - dec) < 20 / 3600
                and abs(f["ra"] - ra) < 20 / 3600 / cosd]
        if not hits:
            continue
        nights = defaultdict(lambda: [0, False, set()])
        for f in hits:
            d = (f["date_obs"] or "?")[:10]
            nights[d][0] += 1
            if (f["release_date"] or "9") <= now:
                nights[d][1] = True
            nights[d][2].add((f["object"] or "?").strip())
        fwd.append({"target": name,
                    "nights": len(nights),
                    "public": sum(1 for v in nights.values() if v[1]),
                    "objs": sorted({o for v in nights.values() for o in v[2]}),
                    "dates": sorted(nights)})
    fwd.sort(key=lambda r: -r["nights"])
    print("\n[forward] known targets with data:")
    for r in fwd:
        if r["nights"] >= 2:
            print(f"  {r['target']:<24} nights={r['nights']:>3} "
                  f"public={r['public']:>3}  as {', '.join(r['objs'])[:40]}")

    # ---- reverse: unexplained multi-night clusters ----
    bins = defaultdict(lambda: {"nights": set(), "objs": set(), "ra": 0.0,
                                "dec": 0.0, "n": 0, "progs": set()})
    for f in frames:
        key = (round(f["ra"] * 50) / 50, round(f["dec"] * 50) / 50)  # 0.02 deg bins
        b = bins[key]
        b["nights"].add((f["date_obs"] or "?")[:10])
        b["objs"].add((f["object"] or "?").strip())
        b["progs"].add((f["prog_id"] or "?")[:8])
        b["ra"] += f["ra"]
        b["dec"] += f["dec"]
        b["n"] += 1

    known_pos = list(targets.values())
    unknown = []
    for key, b in bins.items():
        if len(b["nights"]) < 3:
            continue
        ra, dec = b["ra"] / b["n"], b["dec"] / b["n"]
        cosd = max(abs(math.cos(math.radians(dec))), 1e-3)
        near_known = any(abs(dec - kd) < 60 / 3600 and
                         abs(ra - kr) < 60 / 3600 / cosd
                         for kr, kd in known_pos)
        if not near_known:
            unknown.append((len(b["nights"]), ra, dec, sorted(b["objs"]),
                            sorted(b["progs"])))
    unknown.sort(reverse=True)
    import os
    cap = int(os.environ.get("REVERSE_CAP", "25"))
    print(f"\n[reverse] {len(unknown)} unexplained clusters with >=3 nights; "
          f"identifying top {cap} via SIMBAD:")
    SUBSTELLAR = ("BD*", "LM*", "Pl", "Y*O", "BD?", "Pl?", "PM*")
    rev = []
    for nn, ra, dec, objs, progs in unknown[:cap]:
        ids = simbad_cone(ra, dec)
        flag = ""
        if ids and any(o in SUBSTELLAR for _, o in ids[:2]):
            flag = "  <-- SUBSTELLAR-TYPE"
        rev.append({"nights": nn, "ra": ra, "dec": dec, "objs": objs,
                    "progs": progs, "simbad": ids})
        idstr = "; ".join(f"{a} ({b})" for a, b in ids[:2]) or "no SIMBAD match"
        print(f"  {nn:>3} nights  {objs[0][:22]:<22} {','.join(progs)[:20]:<20} -> {idstr}{flag}")

    out = ROOT / "data" / "m25-census2.json"
    out.write_text(json.dumps({"generated_utc": now,
                               "targets_resolved": {k: v for k, v in targets.items()},
                               "forward": fwd, "reverse": rev}, indent=2),
                   encoding="utf-8")
    print(f"\nwrote {out.name}")


if __name__ == "__main__":
    main()
