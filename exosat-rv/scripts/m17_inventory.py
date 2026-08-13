"""M17: inventory + product fetch for the tier-2 spot-check targets.

Targets: beta Pic b, AB Pic b, CT Cha B, GSC 08047-00232 B (docs/target-queue.md).
For each: resolve coordinates (SIMBAD TAP), query dbo.raw by OBJECT name (the
coordinate box would drown beta Pic b in beta Pic A frames), query ivoa.ObsCore
calib_level=2 in a tight box, download products, and read the authoritative
setting from each header (filter_path lies — M2/M15 trap, thrice confirmed).

Writes data/m17-<slug>-inventory.json and data/spectra_<slug>/ per target.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TAP = "https://archive.eso.org/tap_obs/sync"

TARGETS = [
    # slug, simbad main_id, ESO OBJECT names to match in dbo.raw
    ("betapicb", "* bet Pic b", ["BET PIC B", "BETA PIC B", "BETA-PIC-B"]),
    ("abpicb", "HD  44627B", ["AB PIC B", "AB-PIC-B"]),
    ("ctchab", "V* CT Cha B", ["CT CHA B", "CT-CHA-B"]),
    ("gsc8047b", "CD-52   381B", ["GSC 08047-00232 B", "GSC-08047-00232-B",
                                  "GSC 8047-232 B"]),
]


def tap(query: str, tries: int = 5) -> list[dict]:
    for k in range(tries):
        try:
            r = requests.get(TAP, params={"REQUEST": "doQuery", "LANG": "ADQL",
                                          "FORMAT": "json", "QUERY": query},
                             timeout=120)
            r.raise_for_status()
            j = r.json()
            cols = [c["name"] for c in j["metadata"]]
            return [dict(zip(cols, row)) for row in j["data"]]
        except Exception as e:  # noqa: BLE001
            print(f"    TAP retry {k + 1}: {e}", flush=True)
            time.sleep(10 * (k + 1))
    raise RuntimeError("TAP unreachable")


def simbad_coords(main_id: str) -> tuple[float, float]:
    r = requests.get("https://simbad.cds.unistra.fr/simbad/sim-tap/sync", params={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
        "QUERY": f"SELECT ra, dec FROM basic WHERE main_id = '{main_id}'"},
        timeout=60)
    d = r.json()["data"]
    return float(d[0][0]), float(d[0][1])


def main() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from exosat_rv.archive.fetch import download, _safe_name
    from astropy.io import fits

    for slug, main_id, objnames in TARGETS:
        print(f"\n=== {slug} ({main_id}) ===", flush=True)
        try:
            ra, dec = simbad_coords(main_id)
        except Exception as e:  # noqa: BLE001
            print(f"  SIMBAD failed: {e}; skipping", flush=True)
            continue
        print(f"  RA={ra:.5f} Dec={dec:.5f}", flush=True)

        names_sql = " OR ".join(f"object = '{n}'" for n in objnames)
        raw = tap(f"""
            SELECT object, date_obs, prog_id, filter_path, release_date, dp_cat
            FROM dbo.raw
            WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE' AND ({names_sql})
            """)
        nights: dict[str, dict] = {}
        for f in raw:
            night = (f.get("date_obs") or "?")[:10]
            n = nights.setdefault(night, {"n": 0, "bands": set(), "progs": set(),
                                          "rel": []})
            n["n"] += 1
            n["bands"].add((f.get("filter_path") or "?").split(",")[0])
            n["progs"].add(f.get("prog_id") or "?")
            if f.get("release_date"):
                n["rel"].append(f["release_date"])
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for n in nights.values():
            n["public"] = bool(n["rel"]) and min(n["rel"]) <= now
            n["bands"] = sorted(n["bands"])
            n["progs"] = sorted(n["progs"])
            del n["rel"]
        print(f"  raw: {len(raw)} frames over {len(nights)} nights "
              f"({sum(1 for x in nights.values() if x['public'])} public)", flush=True)
        for d in sorted(nights):
            x = nights[d]
            print(f"    {d} n={x['n']:3d} {'/'.join(x['bands']):10s} "
                  f"public={x['public']} {','.join(x['progs'])}", flush=True)

        box = 0.01
        prods = tap(f"""
            SELECT target_name, t_min, obs_release_date, access_url, dp_id
            FROM ivoa.ObsCore
            WHERE obs_collection = 'CRIRESplus' AND calib_level = 2
              AND s_ra BETWEEN {ra - box} AND {ra + box}
              AND s_dec BETWEEN {dec - box} AND {dec + box}
            """)
        print(f"  ObsCore products in box: {len(prods)}", flush=True)

        dest = ROOT / "data" / f"spectra_{slug}"
        dest.mkdir(parents=True, exist_ok=True)
        settings = []
        for p in prods:
            dp = p.get("dp_id") or p["access_url"].rsplit("/", 1)[-1]
            f = dest / _safe_name(f"{dp}.fits" if not str(dp).endswith(".fits") else dp)
            if not (f.exists() and f.stat().st_size > 0):
                try:
                    download(p["access_url"], f)
                except Exception as e:  # noqa: BLE001
                    print(f"    FAIL {dp}: {e}", flush=True)
                    continue
            try:
                h = fits.getheader(f)
                wlen = (h.get("HIERARCH ESO INS WLEN ID")
                        or h.get("ESO INS WLEN ID") or "?")
                obj = h.get("OBJECT", "?")
                settings.append({"file": f.name, "date": str(h.get("DATE-OBS"))[:10],
                                 "mjd": float(h.get("MJD-OBS", 0)),
                                 "wlen": str(wlen), "object": str(obj)})
            except Exception as e:  # noqa: BLE001
                print(f"    unreadable {f.name}: {e}", flush=True)
        for s in sorted(settings, key=lambda s: s["mjd"]):
            print(f"    {s['date']} {s['wlen']:8s} obj={s['object'][:24]:24s} "
                  f"{s['file']}", flush=True)

        out = ROOT / "data" / f"m17-{slug}-inventory.json"
        out.write_text(json.dumps({
            "generated_utc": now, "main_id": main_id, "ra": ra, "dec": dec,
            "nights": {k: nights[k] for k in sorted(nights)},
            "products": settings}, indent=2), encoding="utf-8")
        print(f"  wrote {out.name}", flush=True)


if __name__ == "__main__":
    main()
