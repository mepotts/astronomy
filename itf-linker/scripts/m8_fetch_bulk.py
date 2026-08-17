"""M8: bulk orbits for the full Rubin batches -- download, filter, verify. Read-only.

Replaces M7's 400-orbit get-orb loop (>= 1.1 s each -- correct politeness, wrong scale)
with the MPC's own bulk product, in four steps:

1. **Batch object lists.** The Feb 2026-02-06 partition is already cached (M7). The
   April batch lands in six large ``created_at`` partitions (2026-04-10/22/24/25/27/28,
   found by listing the Asteroid Institute's public GCS bucket -- the M7 trap stands:
   partitions key on *created_at*, and the objects designate by discovery date, 2025
   M/N/P..., so nothing here filters on designation half-months). Objects =
   unnumbered rows with a current ``provid``.
2. **MPCORB extended JSON** (``Extended_Files/mpcorb_extended.json.gz``), one download,
   streamed by :func:`itf_linker.attrib.bulk.iter_mpcorb_objects`, filtered to the
   batch provids -- matching ``Principal_desig`` *or* ``Other_desigs``, because a batch
   provid may have been merged under another primary since (M7 trap 8).
3. **Fallback**: provids the bulk file does not carry go through get-orb one by one,
   paced, capped -- if more than ``FALLBACK_CAP`` miss, the bulk parse is wrong and the
   run stops rather than hammering the API to paper over it.
4. **Verification**: every parsed bulk orbit that also exists in M7's cached get-orb
   responses is compared state-to-state (same primary, same epoch expected from both
   routes). The bulk parse is trusted only after that comparison is written down.

Outputs ``data/raw/rubin/m8-orbits.parquet`` (+ ``.provenance.json``) and
``data/raw/rubin/m8-bulk-verification.json``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import polars as pl
import requests

from itf_linker.attrib.bulk import iter_mpcorb_objects, mpcorb_to_orbit
from itf_linker.attrib.core import AttribOrbit, parse_mpc_orb

RUBIN_DIR = ROOT / "data" / "raw" / "rubin"
MPCORB_GZ = ROOT / "data" / "raw" / "mpcorb" / "mpcorb_extended.json.gz"
ORBIT_CACHE = RUBIN_DIR / "orbits"  # M7's per-designation get-orb responses
OUT_PARQUET = RUBIN_DIR / "m8-orbits.parquet"
OUT_VERIFY = RUBIN_DIR / "m8-bulk-verification.json"

MPCORB_URL = "https://www.minorplanetcenter.net/Extended_Files/mpcorb_extended.json.gz"
GCS_MEDIA = "https://storage.googleapis.com/asteroid-institute-public/{name}"
ORB_URL = "https://data.minorplanetcenter.net/api/get-orb"
USER_AGENT = (
    "itf-linker/0.4 attribution (read-only; contact matthew.e.potts@gmail.com) "
    "python-requests"
)

FEB_PARTITION = RUBIN_DIR / "obs_sbn_X05_2026-02-06.parquet"
#: The six large April created_at partitions (production namespace), from the bucket
#: listing of 2026-08-16. Small (11 kB) marker partitions between them are empty days.
APRIL_PARTITIONS = [
    "production/rubin/mpc/obs_sbn/daily/2026-04-10/parquet/obs_sbn_X05_2026-04-10.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-04-22/parquet/obs_sbn_X05_2026-04-22.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-04-24/parquet/obs_sbn_X05_2026-04-24.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-04-25/parquet/obs_sbn_X05_2026-04-25.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-04-27/parquet/obs_sbn_X05_2026-04-27.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-04-28/parquet/obs_sbn_X05_2026-04-28.parquet",
]

FALLBACK_CAP = 2000
MIN_INTERVAL_S = 1.1


def download(url: str, dest: Path, *, expect_min_bytes: int = 1000) -> dict[str, Any]:
    """Stream a file to disk once; returns provenance. Cached by existence."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    prov_path = dest.with_suffix(dest.suffix + ".provenance.json")
    if dest.exists() and dest.stat().st_size >= expect_min_bytes:
        if prov_path.exists():
            return json.loads(prov_path.read_text(encoding="utf-8"))
        return {"url": url, "bytes": dest.stat().st_size, "note": "pre-existing, no sidecar"}
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True,
                      timeout=(30, 300)) as resp:
        resp.raise_for_status()
        sha = hashlib.sha256()
        with tmp.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
                sha.update(chunk)
        prov = {
            "url": url,
            "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_modified": resp.headers.get("Last-Modified"),
            "bytes": tmp.stat().st_size,
            "sha256": sha.hexdigest(),
        }
    if tmp.stat().st_size < expect_min_bytes:
        raise RuntimeError(f"{url}: only {tmp.stat().st_size} bytes -- refusing to keep")
    tmp.replace(dest)
    prov_path.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    return prov


def batch_objects(path: Path) -> tuple[set[str], dict[str, Any]]:
    """Distinct unnumbered provid objects in one partition, plus honest counts.

    The discovery asterisk is the ``disc`` column ('*' per discovery observation) --
    the temptingly-named ``designation_asterisk`` is an all-null Boolean in the current
    replica (measured 2026-08-16; ``disc`` reproduces M7's 17,043 for the Feb
    partition exactly).
    """
    df = pl.read_parquet(path, columns=["provid", "permid", "obstime", "created_at",
                                        "disc"])
    n_obs = df.height
    with_provid = df.filter(pl.col("provid").is_not_null() & (pl.col("provid") != ""))
    unnumbered = with_provid.filter(
        pl.col("permid").is_null() | (pl.col("permid") == "")
    )
    objs = set(unnumbered["provid"].unique().to_list())
    n_ast = int((with_provid["disc"] == "*").sum())
    stats = {
        "observations": n_obs,
        "with_provid": with_provid.height,
        "numbered_obs": with_provid.height - unnumbered.height,
        "distinct_unnumbered_objects": len(objs),
        "discovery_asterisks": n_ast,
        "obstime_span": [str(with_provid["obstime"].min()),
                         str(with_provid["obstime"].max())] if with_provid.height else None,
    }
    return objs, stats


def load_getorb_reference() -> dict[str, AttribOrbit]:
    """M7's cached get-orb responses, parsed, keyed by unpacked primary designation."""
    out: dict[str, AttribOrbit] = {}
    for path in sorted(ORBIT_CACHE.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("status") != 200:
            continue
        orbit = parse_mpc_orb(doc["doc"], requested_desig=doc.get("requested_desig", ""))
        if orbit is not None:
            out[orbit.primary_desig] = orbit
    return out


def fetch_getorb_fallback(desigs: list[str]) -> tuple[list[AttribOrbit], list[str]]:
    """Politely fetch orbits the bulk file misses. Returns (orbits, still_missing)."""
    session = requests.Session()
    got: list[AttribOrbit] = []
    missing: list[str] = []
    last = 0.0
    cache_dir = RUBIN_DIR / "orbits-fallback"
    cache_dir.mkdir(parents=True, exist_ok=True)
    for i, desig in enumerate(desigs):
        dest = cache_dir / (desig.replace(" ", "_").replace("/", "_") + ".json")
        if dest.exists():
            doc = json.loads(dest.read_text(encoding="utf-8"))
        else:
            wait = MIN_INTERVAL_S - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            resp = session.get(ORB_URL, json={"desig": desig},
                               headers={"User-Agent": USER_AGENT}, timeout=90)
            doc = {"status": resp.status_code,
                   "doc": resp.json() if resp.status_code == 200 else resp.text[:400],
                   "requested_desig": desig}
            dest.write_text(json.dumps(doc), encoding="utf-8")
        orbit = None
        if doc.get("status") == 200:
            orbit = parse_mpc_orb(doc["doc"], requested_desig=desig)
        if orbit is None:
            missing.append(desig)
        else:
            got.append(orbit)
        if (i + 1) % 50 == 0:
            print(f"  fallback {i + 1}/{len(desigs)}", flush=True)
    return got, missing


def main() -> None:
    t0 = time.monotonic()
    report: dict[str, Any] = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # ---- 1. batch object lists ----------------------------------------------------
    if not FEB_PARTITION.exists():
        raise SystemExit(f"missing {FEB_PARTITION} -- M7's cached Feb partition")
    feb_objs, feb_stats = batch_objects(FEB_PARTITION)
    report["feb_partition"] = feb_stats
    print(f"Feb 2026-02-06: {feb_stats}", flush=True)

    apr_objs: set[str] = set()
    report["april_partitions"] = {}
    for name in APRIL_PARTITIONS:
        day = name.split("daily/")[1].split("/")[0]
        dest = RUBIN_DIR / f"obs_sbn_X05_{day}.parquet"
        prov = download(GCS_MEDIA.format(name=name), dest, expect_min_bytes=1 << 20)
        objs, stats = batch_objects(dest)
        stats["bytes"] = prov.get("bytes")
        report["april_partitions"][day] = stats
        apr_objs |= objs
        print(f"Apr {day}: {stats}", flush=True)

    apr_new = apr_objs - feb_objs
    wanted = feb_objs | apr_objs
    report["objects"] = {
        "feb": len(feb_objs),
        "apr_total": len(apr_objs),
        "apr_not_in_feb": len(apr_new),
        "union": len(wanted),
    }
    print(f"objects: {report['objects']}", flush=True)

    # ---- 2. MPCORB extended JSON --------------------------------------------------
    prov = download(MPCORB_URL, MPCORB_GZ, expect_min_bytes=100 << 20)
    report["mpcorb"] = {k: prov.get(k) for k in ("url", "last_modified", "bytes", "sha256")}
    print(f"MPCORB: {report['mpcorb']}", flush=True)

    t_parse = time.monotonic()
    rows: list[dict[str, Any]] = []
    seen_primaries: set[str] = set()
    matched_provids: set[str] = set()
    n_scanned = 0
    n_unparsable = 0
    for obj in iter_mpcorb_objects(MPCORB_GZ):
        n_scanned += 1
        principal = str(obj.get("Principal_desig") or "").strip()
        others = [str(d).strip() for d in (obj.get("Other_desigs") or [])]
        hit = ({principal} | set(others)) & wanted
        if not hit:
            continue
        orbit = mpcorb_to_orbit(obj)
        if orbit is None:
            n_unparsable += 1
            continue
        if orbit.primary_desig in seen_primaries:
            continue  # two wanted provids merged under one primary: keep one orbit
        seen_primaries.add(orbit.primary_desig)
        matched_provids |= hit
        rows.append(
            {
                "primary": orbit.primary_desig,
                "matched_provids": sorted(hit),
                "all_desigs": orbit.all_desigs,
                "epoch_mjd_tt": orbit.epoch_mjd_tt,
                "r0": orbit.r0.tolist(),
                "v0": orbit.v0.tolist(),
                "h_mag": orbit.h_mag,
                "g_slope": orbit.g_slope,
                "u_param": -1 if orbit.u_param is None else orbit.u_param,
                "arc_days": orbit.arc_days,
                "n_obs": orbit.n_obs,
                "n_opp": orbit.n_opp,
                "rms": orbit.normalized_rms,
                "orbit_type": orbit.orbit_type,
                "source": "mpcorb",
            }
        )
    parse_s = time.monotonic() - t_parse
    report["mpcorb_parse"] = {
        "objects_scanned": n_scanned,
        "matched_orbits": len(rows),
        "matched_provids": len(matched_provids),
        "unparsable_matched": n_unparsable,
        "seconds": round(parse_s, 1),
    }
    print(f"MPCORB parse: {report['mpcorb_parse']}", flush=True)

    # ---- 3. fallback for provids the bulk file misses -----------------------------
    unmatched = sorted(wanted - matched_provids)
    report["fallback"] = {"unmatched_provids": len(unmatched)}
    if len(unmatched) > FALLBACK_CAP:
        report["fallback"]["error"] = (
            f"{len(unmatched)} unmatched > cap {FALLBACK_CAP}: bulk parse untrustworthy"
        )
        OUT_VERIFY.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(report["fallback"]["error"])
    if unmatched:
        print(f"fallback get-orb for {len(unmatched)} provids...", flush=True)
        fb_orbits, still_missing = fetch_getorb_fallback(unmatched)
        report["fallback"]["fetched"] = len(fb_orbits)
        report["fallback"]["no_orbit"] = len(still_missing)
        report["fallback"]["no_orbit_sample"] = still_missing[:20]
        for orbit in fb_orbits:
            if orbit.primary_desig in seen_primaries:
                continue
            seen_primaries.add(orbit.primary_desig)
            rows.append(
                {
                    "primary": orbit.primary_desig,
                    "matched_provids": [orbit.requested_desig],
                    "all_desigs": orbit.all_desigs,
                    "epoch_mjd_tt": orbit.epoch_mjd_tt,
                    "r0": orbit.r0.tolist(),
                    "v0": orbit.v0.tolist(),
                    "h_mag": orbit.h_mag,
                    "g_slope": orbit.g_slope,
                    "u_param": -1 if orbit.u_param is None else orbit.u_param,
                    "arc_days": orbit.arc_days,
                    "n_obs": orbit.n_obs,
                    "n_opp": orbit.n_opp,
                    "rms": orbit.normalized_rms,
                    "orbit_type": orbit.orbit_type,
                    "source": "get-orb",
                }
            )
        print(f"fallback: {report['fallback']}", flush=True)

    # ---- 4. verification against M7's cached get-orb states -----------------------
    # The two routes quote different standard epochs (get-orb responses cached
    # 2026-08-16 sit at MJD 61000; today's MPCORB at 61200), so a same-epoch state
    # comparison would compare nothing. The get-orb state is carried to the MPCORB
    # epoch with the *perturbed* integrator (measured error ~1e-8 AU over 200 days --
    # scripts/m8_calibration.py), so the residual is the difference between the two
    # published fits plus MPCORB's element quantisation (7 decimals in a, 5 in the
    # angles ~ 1e-6..1e-5 AU). A frame or anomaly-convention mistake in the bulk
    # parse would show as ~0.1-1 AU and cannot hide.
    from itf_linker.attrib.perturbed import integrate_dense

    reference = load_getorb_reference()
    by_primary = {r["primary"]: r for r in rows}
    diffs = []
    n_bridged = 0
    for primary, ref in reference.items():
        row = by_primary.get(primary)
        if row is None or row["source"] != "mpcorb":
            continue
        gap = row["epoch_mjd_tt"] - ref.epoch_mjd_tt
        if abs(gap) < 1e-6:
            r_ref = ref.r0
        else:
            traj = integrate_dense(
                ref.r0[None, :], ref.v0[None, :], ref.epoch_mjd_tt,
                min(ref.epoch_mjd_tt, row["epoch_mjd_tt"]) - 1.0,
                max(ref.epoch_mjd_tt, row["epoch_mjd_tt"]) + 1.0,
                h_days=1.0, dense_every=1,
            )
            r_ref, _ = traj.state_at(
                np.array([row["epoch_mjd_tt"]]), np.array([0])
            )
            r_ref = r_ref[0]
            n_bridged += 1
        dr = float(np.linalg.norm(np.array(row["r0"]) - r_ref))
        diffs.append({"primary": primary, "dr_au": dr,
                      "epoch_gap_days": round(gap, 3)})
    dr_all = np.array([d["dr_au"] for d in diffs]) if diffs else np.array([])
    report["verification"] = {
        "getorb_reference_orbits": len(reference),
        "compared": len(diffs),
        "epoch_bridged_with_perturbed_integrator": n_bridged,
        "dr_au_median": float(np.median(dr_all)) if dr_all.size else None,
        "dr_au_p99": float(np.quantile(dr_all, 0.99)) if dr_all.size else None,
        "dr_au_max": float(dr_all.max()) if dr_all.size else None,
        "worst": sorted(diffs, key=lambda d: -d["dr_au"])[:10],
    }
    print(f"verification: {len(diffs)} compared ({n_bridged} epoch-bridged), "
          f"median dr = {report['verification']['dr_au_median']}, "
          f"max = {report['verification']['dr_au_max']}", flush=True)

    # ---- write --------------------------------------------------------------------
    # Explicit schema, strict=False: MPCORB serialises counts as ints, get-orb as
    # floats (a fallback row's ``nobs_total: 114.0`` crashed inference on the first
    # run) -- declare the types once and coerce, rather than letting a 100-row sample
    # guess.
    schema = {
        "primary": pl.Utf8,
        "matched_provids": pl.List(pl.Utf8),
        "all_desigs": pl.List(pl.Utf8),
        "epoch_mjd_tt": pl.Float64,
        "r0": pl.List(pl.Float64),
        "v0": pl.List(pl.Float64),
        "h_mag": pl.Float64,
        "g_slope": pl.Float64,
        "u_param": pl.Int64,
        "arc_days": pl.Float64,
        "n_obs": pl.Int64,
        "n_opp": pl.Int64,
        "rms": pl.Float64,
        "orbit_type": pl.Utf8,
        "source": pl.Utf8,
    }
    df = pl.DataFrame(rows, schema=schema, strict=False)
    df.write_parquet(OUT_PARQUET)
    report["orbits_written"] = df.height
    report["u_param_histogram"] = dict(
        sorted(
            df.group_by("u_param").len().rows()
        )
    )
    report["elapsed_s"] = round(time.monotonic() - t0, 1)
    OUT_VERIFY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PARQUET} ({df.height} orbits) and {OUT_VERIFY} "
          f"in {report['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
