"""M9: reconstruct the M7/M8 ITF snapshot (2026-08-16) from the archive. Read-only inputs.

The problem this solves: between M8 (ITF pulled 2026-08-16 20:27:01 GMT, 9,255,644
observations) and M9 (today), the daily archive refreshed ``data/raw/itf.txt.gz`` and
``data/parquet/itf_observations.parquet`` to the 2026-08-18 pull -- ~22k observations
left the ITF in between (the MPC consuming tracklets). M8's fit queue, its ledger, and
its published coarse counts are all statements about the 08-16 universe; "resume the
queue at rank 901" is only meaningful on that universe.

The archive makes an exact reconstruction possible without re-downloading anything:

* ``data/snapshots/20260816T202701Z/observations.parquet`` is the slim per-observation
  table of the M8 snapshot -- ``obs_key`` (a content hash of desig, obscode, and the
  quantised mjd/ra/dec -- :mod:`itf_linker.snapshot`), so a key match *is* a content
  match at 80-column precision.
* Today's full table carries the astrometry for every observation that survived.

Reconstruction = today's rows whose ``obs_key`` appears in the 08-16 key set. Rows that
disappeared in between cannot be reconstructed (the slim table has no astrometry), so
every tracklet that lost *any* observation is dropped whole and enumerated -- a
partially-reconstructed tracklet would have different endpoints, rates and means than
the one M8 swept, which is worse than an honestly-missing one.

Night definition and desig filter are ``m7_attribution.load_tracklets``'s exactly, so
"tracklet" here means what it means in every attribution sweep.

Outputs:
* ``data/parquet/itf_observations_20260816_reconstructed.parquet`` (full schema)
* ``data/raw/rubin/m9-snapshot-reconstruction.json`` (counts, the honest deficit)
* ``data/raw/rubin/m9-dropped-tracklets.parquet`` (every dropped (desig, obscode, night))
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl

from itf_linker import config
from itf_linker.ingest.fetch import fetch_obscodes
from itf_linker.snapshot import obs_keys

SNAP_DIR = ROOT / "data" / "snapshots" / "20260816T202701Z"
SLIM = SNAP_DIR / "observations.parquet"
MANIFEST = SNAP_DIR / "manifest.json"
CURRENT = config.ITF_PARQUET
OUT_PARQUET = ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
OUT_REPORT = ROOT / "data" / "raw" / "rubin" / "m9-snapshot-reconstruction.json"
OUT_DROPPED = ROOT / "data" / "raw" / "rubin" / "m9-dropped-tracklets.parquet"


def with_night(df: pl.LazyFrame, lon_df: pl.DataFrame) -> pl.LazyFrame:
    """The load_tracklets night: local night from the observatory's signed longitude."""
    return (
        df.join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
    )


def main() -> None:
    t0 = time.monotonic()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report: dict = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_provenance": manifest["provenance"],
        "snapshot_observations": manifest["observations"],
        "current_parquet": str(CURRENT),
        "current_provenance": json.loads(
            config.ITF_PROVENANCE.read_text(encoding="utf-8")
        ),
    }

    slim = pl.read_parquet(SLIM)  # obs_key, desig, obscode, mjd
    current = pl.read_parquet(CURRENT)
    report["current_observations"] = current.height

    t = time.monotonic()
    cur_keys = obs_keys(current)
    report["obs_keys_seconds"] = round(time.monotonic() - t, 1)
    current = current.with_columns(pl.Series("obs_key", cur_keys, dtype=pl.UInt64))

    snap_key_set = slim["obs_key"]
    kept = current.filter(pl.col("obs_key").is_in(snap_key_set))
    appeared_since = current.height - kept.height
    # Which 08-16 observations are gone from today's table?
    slim_flagged = slim.with_columns(
        pl.col("obs_key").is_in(current["obs_key"]).alias("survives")
    )
    n_missing = int((~slim_flagged["survives"]).sum())
    report["kept_observations"] = kept.height
    report["appeared_since_snapshot"] = appeared_since
    report["disappeared_since_snapshot"] = n_missing
    # kept + missing == snapshot total, up to duplicate-key collisions (~1,150 known
    # duplicate observations in the file). A large residue would mean the key join is
    # not doing what this script claims.
    report["accounting_residue"] = manifest["observations"] - (kept.height + n_missing)

    # ---- tracklet-level accounting, load_tracklets' definitions -------------------
    lon = fetch_obscodes()
    lon_df = pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )
    slim_named = slim_flagged.lazy().filter(pl.col("desig") != "")
    per_trk = (
        with_night(slim_named, lon_df)
        .group_by("desig", "obscode", "night")
        .agg(
            pl.len().alias("n_obs_0816"),
            pl.col("survives").sum().alias("n_obs_survive"),
        )
        .collect()
    )
    report["tracklets_0816_named"] = per_trk.height
    dropped = per_trk.filter(pl.col("n_obs_survive") < pl.col("n_obs_0816"))
    report["tracklets_dropped"] = dropped.height
    report["tracklets_dropped_fully_gone"] = int(
        (dropped["n_obs_survive"] == 0).sum()
    )
    report["tracklets_exact"] = per_trk.height - dropped.height
    dropped.sort("desig", "obscode", "night").write_parquet(OUT_DROPPED)

    # ---- write the reconstructed observation table --------------------------------
    # Drop every observation belonging to a dropped tracklet, so that load_tracklets
    # on this file yields *only* tracklets whose observation set is bit-identical to
    # the 08-16 snapshot. Unnamed (desig == "") rows pass through untouched -- the
    # sweeps never see them.
    kept_named = with_night(
        kept.lazy().filter(pl.col("desig") != ""), lon_df
    )
    kept_named = kept_named.join(
        dropped.lazy().select("desig", "obscode", "night"),
        on=["desig", "obscode", "night"],
        how="anti",
    ).drop("lon_deg", "night")
    kept_unnamed = kept.lazy().filter(pl.col("desig") == "")
    out = pl.concat([kept_named, kept_unnamed]).drop("obs_key").collect()
    out.write_parquet(OUT_PARQUET)
    report["reconstructed_observations"] = out.height
    report["reconstructed_parquet"] = str(OUT_PARQUET)
    report["elapsed_s"] = round(time.monotonic() - t0, 1)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
