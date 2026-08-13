"""M15 kickoff: eta Tel B archive inventory + the phase-BERV geometry check.

Standing rule 4 from docs/target-queue.md (M13 §4b design rule): before spending any
compute on a new target, map where in period space a BERV covariate is degenerate with
an orbit, given the actual epoch sampling. On CD-35 the -0.71 entanglement at the
satellite's own period cost three milestones; this check is the ten-minute version.

Steps:
  1. dbo.raw:      every CRIRES frame with OBJECT in (ETA TEL B, HR-7329-B) ->
                   nights, band (filter_path, a hint not truth), public status.
  2. ivoa.ObsCore: calib_level=2 CRIRESplus products at those coordinates ->
                   ADP list with access URLs (the archive route's input).
  3. Geometry:     BERV at Paranal for each public H-band night; per trial period
                   P in the blind-search grid (5..460 d), R^2 of BERV regressed on
                   [cos, sin](2 pi t / P) -> the degeneracy map. R^2 -> 1 means a
                   BERV nuisance term absorbs any orbit at that period, as it did
                   on CD-35 at 171 d.

Writes data/m15-eta-tel-inventory.json and prints the tables.
TAP traps honoured (DATA-SOURCES.md): no CONTAINS on dbo.raw (plain ra/dec box),
no ORDER BY MIN(), s_ra/s_dec on ObsCore, product header is authoritative for band.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import requests

TAP = "https://archive.eso.org/tap_obs/sync"
OUT = Path(__file__).resolve().parents[1] / "data" / "m15-eta-tel-inventory.json"

# eta Tel = HR 7329; SIMBAD fallback coordinates (deg). The companion sits 4.2" away,
# far inside the query box.
RA_FALLBACK, DEC_FALLBACK = 290.71364, -54.42375


def tap(query: str, tries: int = 6) -> list[dict]:
    """Sync TAP query with retries; archive.eso.org is historically intermittent."""
    for k in range(tries):
        try:
            r = requests.get(TAP, params={
                "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
                "QUERY": query}, timeout=120)
            r.raise_for_status()
            j = r.json()
            cols = [c["name"] for c in j["metadata"]]
            return [dict(zip(cols, row)) for row in j["data"]]
        except Exception as e:  # noqa: BLE001 - retry on any transport/parse failure
            print(f"  TAP attempt {k + 1} failed: {e}", flush=True)
            time.sleep(min(15 * (k + 1), 60))
    raise RuntimeError("TAP unreachable after retries")


def resolve_coords() -> tuple[float, float]:
    try:
        r = requests.get("https://simbad.cds.unistra.fr/simbad/sim-tap/sync", params={
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json",
            "QUERY": "SELECT ra, dec FROM basic WHERE main_id = '* eta Tel'"},
            timeout=60)
        d = r.json()["data"]
        if d:
            return float(d[0][0]), float(d[0][1])
    except Exception as e:  # noqa: BLE001
        print(f"  SIMBAD resolve failed ({e}); using fallback coords", flush=True)
    return RA_FALLBACK, DEC_FALLBACK


def main() -> None:
    ra, dec = resolve_coords()
    print(f"eta Tel: RA={ra:.5f} Dec={dec:.5f}", flush=True)
    box = 0.02  # deg; ~72 arcsec

    print("\n[1] dbo.raw frames (CRIRES, science)...", flush=True)
    raw = tap(f"""
        SELECT object, ra, dec, date_obs, prog_id, filter_path, release_date,
               dp_cat, dp_tech, exp_start
        FROM dbo.raw
        WHERE instrument = 'CRIRES'
          AND ra  BETWEEN {ra - box} AND {ra + box}
          AND dec BETWEEN {dec - box} AND {dec + box}
          AND dp_cat = 'SCIENCE'
        """)
    print(f"  {len(raw)} science frames", flush=True)

    nights: dict[str, dict] = {}
    for f in raw:
        night = (f.get("date_obs") or f.get("exp_start") or "?")[:10]
        n = nights.setdefault(night, {"n_frames": 0, "bands": set(), "objects": set(),
                                      "progs": set(), "releases": []})
        n["n_frames"] += 1
        n["bands"].add((f.get("filter_path") or "?").split(",")[0])
        n["objects"].add(f.get("object") or "?")
        n["progs"].add(f.get("prog_id") or "?")
        if f.get("release_date"):
            n["releases"].append(f["release_date"])

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for n in nights.values():
        n["public"] = bool(n["releases"]) and min(n["releases"]) <= now
        n["bands"] = sorted(n["bands"])
        n["objects"] = sorted(n["objects"])
        n["progs"] = sorted(n["progs"])
        del n["releases"]

    print(f"  {len(nights)} nights; "
          f"{sum(1 for n in nights.values() if n['public'])} public", flush=True)
    for d in sorted(nights):
        n = nights[d]
        print(f"    {d}  frames={n['n_frames']:3d} bands={'/'.join(n['bands']):8s} "
              f"public={n['public']} progs={','.join(n['progs'])}", flush=True)

    print("\n[2] ivoa.ObsCore calib_level=2 products...", flush=True)
    prods = tap(f"""
        SELECT target_name, t_min, obs_release_date, em_min, em_max,
               access_url, dp_id
        FROM ivoa.ObsCore
        WHERE obs_collection = 'CRIRESplus'
          AND calib_level = 2
          AND s_ra  BETWEEN {ra - box} AND {ra + box}
          AND s_dec BETWEEN {dec - box} AND {dec + box}
        """)
    print(f"  {len(prods)} reduced products", flush=True)

    print("\n[3] phase-BERV geometry over the public nights...", flush=True)
    from astropy.coordinates import EarthLocation, SkyCoord
    from astropy.time import Time
    import astropy.units as u

    pub_nights = sorted(d for d, n in nights.items() if n["public"])
    if len(pub_nights) < 5:
        print("  <5 public nights; geometry check deferred", flush=True)
        geometry = None
    else:
        loc = EarthLocation.of_site("paranal")
        sc = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
        t = Time([f"{d}T05:00:00" for d in pub_nights], scale="utc", location=loc)
        berv = sc.radial_velocity_correction("barycentric", obstime=t).to_value("m/s")
        tt = t.mjd
        periods = np.exp(np.linspace(np.log(5), np.log(460), 2000))
        r2 = np.empty_like(periods)
        b = berv - berv.mean()
        for i, P in enumerate(periods):
            w = 2 * np.pi / P
            A = np.column_stack([np.cos(w * tt), np.sin(w * tt), np.ones_like(tt)])
            coef, *_ = np.linalg.lstsq(A, b, rcond=None)
            resid = b - A @ coef
            r2[i] = 1 - resid.var() / b.var()
        bad = r2 > 0.5
        # contiguous degenerate windows, reported in days
        windows, start = [], None
        for i, flag in enumerate(bad):
            if flag and start is None:
                start = periods[i]
            if not flag and start is not None:
                windows.append((round(start, 1), round(periods[i - 1], 1)))
                start = None
        if start is not None:
            windows.append((round(start, 1), round(periods[-1], 1)))
        geometry = {
            "n_public_nights": len(pub_nights),
            "baseline_d": round(float(tt.max() - tt.min()), 1),
            "berv_span_ms": round(float(berv.max() - berv.min()), 1),
            "frac_period_grid_degenerate_r2_gt_0.5":
                round(float(bad.mean()), 3),
            "degenerate_windows_d": windows,
            "berv_by_night": {d: round(float(v), 1)
                              for d, v in zip(pub_nights, berv)},
        }
        print(f"  nights={len(pub_nights)} baseline={geometry['baseline_d']} d "
              f"BERV span={geometry['berv_span_ms']} m/s", flush=True)
        print(f"  degenerate fraction of period grid (R^2>0.5): "
              f"{geometry['frac_period_grid_degenerate_r2_gt_0.5']}", flush=True)
        print(f"  degenerate windows (d): {windows}", flush=True)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "generated_utc": now, "ra": ra, "dec": dec,
        "nights": {d: nights[d] for d in sorted(nights)},
        "products": prods, "geometry": geometry}, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
