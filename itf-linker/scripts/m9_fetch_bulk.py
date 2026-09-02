"""M9: bulk orbits for the unconsumed Rubin partitions. Read-only. Nothing submitted.

M8's watcher flagged four partitions no milestone had consumed (2026-06-04, -08-03,
-08-06, -08-10); the bucket listing also carries two smaller ones (2026-06-19,
2026-07-29) that meet the watcher's own >= 1 MB batch rule but were not named in
M8-RESULTS section 8. All six are measured here; every distinct unnumbered provid not
already covered by M8's orbit table becomes an M9 sweep object.

Orbit source: the *cached* 2026-08-16 ``mpcorb_extended.json.gz`` -- deliberately not
re-pulled. It postdates every partition here (newest: 2026-08-10), it is the exact file
M8's 22,636-orbit sweep used (so M9 candidates are directly comparable), and the
fallback + the live get-orb sample verification below measure what that choice costs.

Verification: M8 verified its bulk parse against M7's *cached* get-orb states; M9's
objects have no cached reference, so a stratified sample goes through the live get-orb
API (paced >= 1.1 s), each state carried across any epoch gap by the measured perturbed
integrator before comparison. Two distinct residual populations are expected: element
quantisation (~1e-7 AU) where the MPC orbit is unchanged since 08-16, and genuine orbit
*updates* (fresh 2026 discoveries improve fast) -- a frame or convention error would
read ~0.1-1 AU and cannot hide behind either.

Outputs ``data/raw/rubin/m9-orbits.parquet`` (+ per-orbit partition membership) and
``data/raw/rubin/m9-bulk-verification.json``.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m8_fetch_bulk as m8fb
import numpy as np
import polars as pl

from itf_linker.attrib.bulk import iter_mpcorb_objects, mpcorb_to_orbit

RUBIN_DIR = ROOT / "data" / "raw" / "rubin"
OUT_PARQUET = RUBIN_DIR / "m9-orbits.parquet"
OUT_VERIFY = RUBIN_DIR / "m9-bulk-verification.json"

#: The six >= 1 MB partitions in the bucket that no milestone has consumed
#: (watcher state 2026-08-16; M8 section 8 named the four large ones).
PARTITIONS = [
    "production/rubin/mpc/obs_sbn/daily/2026-06-04/parquet/obs_sbn_X05_2026-06-04.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-06-19/parquet/obs_sbn_X05_2026-06-19.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-07-29/parquet/obs_sbn_X05_2026-07-29.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-08-03/parquet/obs_sbn_X05_2026-08-03.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-08-06/parquet/obs_sbn_X05_2026-08-06.parquet",
    "production/rubin/mpc/obs_sbn/daily/2026-08-10/parquet/obs_sbn_X05_2026-08-10.parquet",
]

VERIFY_SAMPLE = 32


def dominant_desigs(path: Path) -> dict[str, int]:
    """Designation-year histogram of the unnumbered provids (M8 table's last column)."""
    df = pl.read_parquet(path, columns=["provid", "permid"])
    unnumbered = df.filter(
        pl.col("provid").is_not_null() & (pl.col("provid") != "")
        & (pl.col("permid").is_null() | (pl.col("permid") == ""))
    )
    years: dict[str, int] = {}
    for p in unnumbered["provid"].unique().to_list():
        year = p.split()[0] if " " in p else p[:4]
        years[year] = years.get(year, 0) + 1
    return dict(sorted(years.items(), key=lambda kv: -kv[1])[:4])


def main() -> None:
    t0 = time.monotonic()
    report: dict[str, Any] = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # ---- 0. what M8 already covers --------------------------------------------------
    m8df = pl.read_parquet(m8fb.OUT_PARQUET,
                           columns=["primary", "matched_provids", "all_desigs"])
    m8_primaries = set(m8df["primary"].to_list())
    m8_covered: set[str] = set(m8_primaries)
    for col in ("matched_provids", "all_desigs"):
        for lst in m8df[col].to_list():
            m8_covered.update(lst or [])
    report["m8_covered_designations"] = len(m8_covered)

    # ---- 1. partition object lists ---------------------------------------------------
    report["partitions"] = {}
    per_part_objs: dict[str, set[str]] = {}
    for name in PARTITIONS:
        day = name.split("daily/")[1].split("/")[0]
        dest = RUBIN_DIR / f"obs_sbn_X05_{day}.parquet"
        prov = m8fb.download(m8fb.GCS_MEDIA.format(name=name), dest,
                             expect_min_bytes=1 << 20)
        objs, stats = m8fb.batch_objects(dest)
        stats["bytes"] = prov.get("bytes")
        stats["objects_already_in_m8"] = len(objs & m8_covered)
        stats["objects_new"] = len(objs - m8_covered)
        stats["dominant_designations"] = dominant_desigs(dest)
        report["partitions"][day] = stats
        per_part_objs[day] = objs
        print(f"{day}: {stats}", flush=True)

    union_objs = set().union(*per_part_objs.values())
    wanted = union_objs - m8_covered
    report["objects"] = {
        "union": len(union_objs),
        "already_in_m8": len(union_objs & m8_covered),
        "new_wanted": len(wanted),
    }
    print(f"objects: {report['objects']}", flush=True)

    # ---- 2. cached MPCORB scan -------------------------------------------------------
    mpcorb_prov = json.loads(
        (m8fb.MPCORB_GZ.parent / (m8fb.MPCORB_GZ.name + ".provenance.json"))
        .read_text(encoding="utf-8")
    )
    report["mpcorb"] = {k: mpcorb_prov.get(k)
                        for k in ("url", "last_modified", "bytes", "sha256")}
    report["mpcorb"]["note"] = (
        "cached 2026-08-16 file reused deliberately: postdates every partition; "
        "same orbit file as M8's sweep"
    )

    t_parse = time.monotonic()
    rows: list[dict[str, Any]] = []
    seen_primaries: set[str] = set()
    matched_provids: set[str] = set()
    n_scanned = n_unparsable = n_m8_primary = 0
    for obj in iter_mpcorb_objects(m8fb.MPCORB_GZ):
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
        if orbit.primary_desig in m8_primaries:
            n_m8_primary += 1          # provid resolves to an object M8 already swept
            matched_provids |= hit
            continue
        if orbit.primary_desig in seen_primaries:
            continue
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
    report["mpcorb_parse"] = {
        "objects_scanned": n_scanned,
        "matched_orbits": len(rows),
        "matched_provids": len(matched_provids),
        "resolved_to_m8_primary": n_m8_primary,
        "unparsable_matched": n_unparsable,
        "seconds": round(time.monotonic() - t_parse, 1),
    }
    print(f"MPCORB parse: {report['mpcorb_parse']}", flush=True)

    # ---- 3. fallback -----------------------------------------------------------------
    unmatched = sorted(wanted - matched_provids)
    report["fallback"] = {"unmatched_provids": len(unmatched)}
    if len(unmatched) > m8fb.FALLBACK_CAP:
        report["fallback"]["error"] = (
            f"{len(unmatched)} unmatched > cap {m8fb.FALLBACK_CAP}: parse untrustworthy"
        )
        OUT_VERIFY.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(report["fallback"]["error"])
    if unmatched:
        print(f"fallback get-orb for {len(unmatched)} provids...", flush=True)
        fb_orbits, still_missing = m8fb.fetch_getorb_fallback(unmatched)
        report["fallback"]["fetched"] = len(fb_orbits)
        report["fallback"]["no_orbit"] = len(still_missing)
        report["fallback"]["no_orbit_sample"] = still_missing[:20]
        for orbit in fb_orbits:
            if orbit.primary_desig in seen_primaries or orbit.primary_desig in m8_primaries:
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

    # ---- 4. per-orbit partition membership -------------------------------------------
    desig_to_parts: dict[str, list[str]] = {}
    for day, objs in per_part_objs.items():
        for d in objs:
            desig_to_parts.setdefault(d, []).append(day)
    for r in rows:
        parts: set[str] = set()
        for d in [*r["matched_provids"], *(r["all_desigs"] or [])]:
            parts.update(desig_to_parts.get(d, []))
        r["partitions"] = sorted(parts)

    # ---- 5. live get-orb sample verification ------------------------------------------
    # Stratified: the head of each U bucket, mpcorb-sourced rows only (fallback rows
    # ARE live get-orb responses already).
    sample: list[dict[str, Any]] = []
    by_u: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        if r["source"] == "mpcorb":
            by_u.setdefault(r["u_param"], []).append(r)
    while len(sample) < min(VERIFY_SAMPLE, sum(len(v) for v in by_u.values())):
        for u in sorted(by_u):
            if by_u[u]:
                sample.append(by_u[u].pop(0))
            if len(sample) >= VERIFY_SAMPLE:
                break
    print(f"verifying {len(sample)} sampled orbits against live get-orb...", flush=True)
    live, _missing = m8fb.fetch_getorb_fallback([r["primary"] for r in sample])
    live_by_primary = {o.primary_desig: o for o in live}
    from itf_linker.attrib.perturbed import integrate_dense

    diffs = []
    for r in sample:
        ref = live_by_primary.get(r["primary"])
        if ref is None:
            diffs.append({"primary": r["primary"], "error": "no live orbit"})
            continue
        gap = r["epoch_mjd_tt"] - ref.epoch_mjd_tt
        if abs(gap) < 1e-6:
            r_ref = ref.r0
        else:
            traj = integrate_dense(
                ref.r0[None, :], ref.v0[None, :], ref.epoch_mjd_tt,
                min(ref.epoch_mjd_tt, r["epoch_mjd_tt"]) - 1.0,
                max(ref.epoch_mjd_tt, r["epoch_mjd_tt"]) + 1.0,
                h_days=1.0, dense_every=1,
            )
            r_ref, _ = traj.state_at(np.array([r["epoch_mjd_tt"]]), np.array([0]))
            r_ref = r_ref[0]
        dr = float(np.linalg.norm(np.array(r["r0"]) - r_ref))
        diffs.append({"primary": r["primary"], "u": r["u_param"],
                      "dr_au": dr, "epoch_gap_days": round(gap, 3)})
    dr_all = np.array([d["dr_au"] for d in diffs if "dr_au" in d])
    report["verification"] = {
        "sampled": len(sample),
        "compared": int(dr_all.size),
        "dr_au_median": float(np.median(dr_all)) if dr_all.size else None,
        "dr_au_p99": float(np.quantile(dr_all, 0.99)) if dr_all.size else None,
        "dr_au_max": float(dr_all.max()) if dr_all.size else None,
        "quantisation_level_fraction": float(
            (dr_all < 1e-5).sum() / dr_all.size) if dr_all.size else None,
        "rows": sorted((d for d in diffs if "dr_au" in d),
                       key=lambda d: -d["dr_au"])[:10],
    }
    print(f"verification: {report['verification']['compared']} compared, "
          f"median dr = {report['verification']['dr_au_median']}, "
          f"max = {report['verification']['dr_au_max']}", flush=True)

    # ---- write ------------------------------------------------------------------------
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
        "partitions": pl.List(pl.Utf8),
    }
    df = pl.DataFrame(rows, schema=schema, strict=False)
    df.write_parquet(OUT_PARQUET)
    report["orbits_written"] = df.height
    report["u_param_histogram"] = dict(sorted(df.group_by("u_param").len().rows()))
    report["elapsed_s"] = round(time.monotonic() - t0, 1)
    OUT_VERIFY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PARQUET} ({df.height} orbits) and {OUT_VERIFY} "
          f"in {report['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
