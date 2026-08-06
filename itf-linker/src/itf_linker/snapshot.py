"""Snapshot archive: answer "what disappeared from the ITF between date A and date B?".

M0 established that the only genuine ITF ground truth available is **what vanishes**. The
ITF is the MPC's file of observations no pipeline ever linked; when someone links them --
including the MPC itself, and including any future submission of ours -- the observations
leave the file and an MPEC says why. A snapshot series is therefore the one control that
directly observes the process this project is trying to join.

That control can only be built forward in time, which is why this ships in M1 even though
nothing consumes it until M2.

Storage
-------
Keeping the raw file is not an option: 135 MB/day of ~99.99% identical text is 48 GB/year
for a signal measured in thousands of rows. Nor is keeping a full key set per snapshot --
measured, that is 178 MB, *larger than the compressed source*, because a 64-bit digest is
by construction incompressible and sorting by it destroys the locality that would let the
designation and epoch columns compress.

So the archive is a **baseline plus a delta chain**, and only a rolling window of full
files:

``manifest.json``   kept forever, kilobytes. Provenance of the pull (URL, byte size,
                    ``Last-Modified``, ``ETag``, fetch time) plus counts, so a snapshot is
                    quotable on its own.
``delta.parquet``   kept forever. Every observation that **appeared** or **disappeared**
                    since the previous snapshot, with its designation, observatory and
                    epoch. Thousands of rows, not millions. The chain answers "what
                    disappeared between A and B" for any pair, for all time.
``observations.parquet``  rolling window (:data:`FULL_KEEP`). The complete key set,
                    ~178 MB. Lets any recent pair be diffed directly rather than by
                    replaying deltas, which is both a faster path and an audit of the
                    chain.
``designations.parquet``  rolling window. Per-designation tracklet/night/arc summary.
``itf.txt.gz``      rolling window (:data:`RAW_KEEP`), the original bytes.

Steady-state cost is therefore a few kilobytes per snapshot plus a fixed window, instead
of 48 GB/year.

The observation key
-------------------
An MPC observation has no identifier. The key here is a 64-bit digest of
``designation, observatory, MJD to 1e-6 d, RA to 1e-7 deg, Dec to 1e-7 deg`` -- the full
information content of the 80-column record's astrometry at its own precision.

*Quantised fields*, not the raw line. The MPC re-reduces observations against new star
catalogues; a changed magnitude or catalogue code would otherwise read as "this
observation vanished and a different one appeared", which is precisely the signal the
archive exists to measure.

*Not polars' built-in ``.hash()``*, whose algorithm is an implementation detail and may
change between versions -- which would silently break every comparison against an older
snapshot. The digest here is BLAKE2b for the string fields and a fixed splitmix64 fold for
the numeric ones, both pinned by tests. :func:`obs_key` (scalar, readable) and
:func:`obs_keys` (vectorised over 9.3M rows) are two implementations of one definition and
are pinned against each other, the same way the 80-column parsers are.

Two observations of genuinely different objects can only collide if they share a
designation, an observatory, a time to 0.09 s **and** a position to 0.36 mas -- which is
the same observation. Collisions from the 64-bit truncation are a separate matter: over
9.3M keys the birthday probability is ~2.3e-6. Any that occur show up as duplicate keys,
which :func:`build_snapshot` counts rather than assumes away.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from . import config

#: Number of most-recent snapshots whose raw ``itf.txt.gz`` is retained.
RAW_KEEP = 1

#: Number of most-recent snapshots keeping their full key set and designation summary.
FULL_KEEP = 3

OBS_FILE = "observations.parquet"
DESIG_FILE = "designations.parquet"
DELTA_FILE = "delta.parquet"
MANIFEST_FILE = "manifest.json"
RAW_FILE = "itf.txt.gz"

#: ``delta.parquet`` change codes.
APPEARED = 1
DISAPPEARED = -1

_MJD_SCALE = 1_000_000        # 1e-6 d = 0.0864 s
_DEG_SCALE = 10_000_000       # 1e-7 deg = 0.36 mas


def snapshot_root() -> Path:
    return config.DATA_DIR / "snapshots"


_U64 = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15
_SPLIT1 = 0xBF58476D1CE4E5B9
_SPLIT2 = 0x94D049BB133111EB


def string_digest(text: str) -> int:
    """Stable 64-bit digest of a string. BLAKE2b, so it cannot drift with a dependency."""
    return int.from_bytes(
        hashlib.blake2b(text.strip().encode("utf-8", "replace"), digest_size=8).digest(), "big"
    )


def _fold(state: int, value: int) -> int:
    """One splitmix64 round, folding ``value`` into ``state``. Pure integer, exact."""
    x = ((state ^ (value & _U64)) * _GOLDEN) & _U64
    x ^= x >> 30
    x = (x * _SPLIT1) & _U64
    x ^= x >> 27
    x = (x * _SPLIT2) & _U64
    return x ^ (x >> 31)


def quantise(mjd: float, ra_deg: float, dec_deg: float) -> tuple[int, int, int]:
    """Round the astrometry to the precision the 80-column record actually carries."""
    return (
        round(mjd * _MJD_SCALE),
        round(ra_deg * _DEG_SCALE),
        round(dec_deg * _DEG_SCALE),
    )


def obs_key(desig: str, obscode: str, mjd: float, ra_deg: float, dec_deg: float) -> int:
    """Scalar reference implementation of the observation key."""
    state = _GOLDEN
    state = _fold(state, string_digest(desig))
    state = _fold(state, string_digest(obscode))
    for value in quantise(mjd, ra_deg, dec_deg):
        state = _fold(state, value)
    return state


def _fold_vec(state: np.ndarray, value: np.ndarray) -> np.ndarray:
    """Vectorised :func:`_fold`. numpy uint64 arithmetic wraps, which is what is wanted."""
    x = (state ^ value) * np.uint64(_GOLDEN)
    x ^= x >> np.uint64(30)
    x = x * np.uint64(_SPLIT1)
    x ^= x >> np.uint64(27)
    x = x * np.uint64(_SPLIT2)
    return x ^ (x >> np.uint64(31))


def obs_keys(frame: pl.DataFrame) -> np.ndarray:
    """Vectorised observation keys for a parsed-observation frame.

    String digests are computed over the *distinct* designations and observatory codes
    (2.6M and ~880 of them) and then gathered, rather than once per row.
    """
    with np.errstate(over="ignore"):
        state = np.full(frame.height, np.uint64(_GOLDEN), dtype=np.uint64)
        for column in ("desig", "obscode"):
            values = frame[column].fill_null("")
            lookup = {s: string_digest(s) for s in values.unique().to_list()}
            digests = np.fromiter(
                (lookup[v] for v in values.to_list()), dtype=np.uint64, count=frame.height
            )
            state = _fold_vec(state, digests)
        for column, scale in (("mjd", _MJD_SCALE), ("ra_deg", _DEG_SCALE), ("dec_deg", _DEG_SCALE)):
            quantised = (frame[column].fill_null(0.0) * scale).round(0).cast(pl.Int64).to_numpy()
            state = _fold_vec(state, quantised.astype(np.uint64))
    return state


@dataclass(frozen=True, slots=True)
class Snapshot:
    """One archived pull of the ITF."""

    snapshot_id: str
    path: Path

    @property
    def manifest(self) -> dict[str, Any]:
        return json.loads((self.path / MANIFEST_FILE).read_text(encoding="utf-8"))

    def observations(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.path / OBS_FILE)

    def designations(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.path / DESIG_FILE)

    def delta(self) -> pl.DataFrame:
        if not (self.path / DELTA_FILE).exists():
            return pl.DataFrame(schema=_DELTA_SCHEMA)
        return pl.read_parquet(self.path / DELTA_FILE)

    @property
    def has_raw(self) -> bool:
        return (self.path / RAW_FILE).exists()

    @property
    def has_full(self) -> bool:
        return (self.path / OBS_FILE).exists()


def snapshot_id_for(provenance: dict[str, Any] | None) -> str:
    """Name a snapshot after the file's ``Last-Modified``, not after the day we fetched it.

    The ITF is regenerated continuously and ``Last-Modified`` moved twice within one hour
    during M0. Naming by fetch date would let two pulls of *different* files share an id,
    or one file archived twice occupy two.
    """
    lm = (provenance or {}).get("last_modified")
    if lm:
        for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S GMT"):
            try:
                # HTTP Last-Modified is GMT by definition (RFC 9110), so attaching UTC is
                # a statement of fact, not an assumption.
                stamp = datetime.strptime(lm, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
            return stamp.strftime("%Y%m%dT%H%M%SZ")
    fetched = (provenance or {}).get("fetched_at_utc")
    if fetched:
        return fetched.replace("-", "").replace(":", "").replace("+0000", "Z")
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def list_snapshots(root: Path | None = None) -> list[Snapshot]:
    root = root or snapshot_root()
    if not root.exists():
        return []
    return [
        Snapshot(snapshot_id=p.name, path=p)
        for p in sorted(root.iterdir())
        if p.is_dir() and (p / MANIFEST_FILE).exists()
    ]


def build_snapshot(
    observations: pl.DataFrame,
    tracklets: pl.DataFrame,
    provenance: dict[str, Any] | None,
    *,
    root: Path | None = None,
    raw_source: Path | None = None,
    raw_keep: int = RAW_KEEP,
    full_keep: int = FULL_KEEP,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write one snapshot, record its delta against the previous one, and prune.

    Returns the manifest.
    """
    root = root or snapshot_root()
    root.mkdir(parents=True, exist_ok=True)
    sid = snapshot_id_for(provenance)
    path = root / sid
    if path.exists() and not overwrite:
        return {**json.loads((path / MANIFEST_FILE).read_text(encoding="utf-8")),
                "already_present": True}

    previous = [s for s in list_snapshots(root) if s.snapshot_id < sid]
    path.mkdir(parents=True, exist_ok=True)

    base = observations.select("desig", "obscode", "mjd", "ra_deg", "dec_deg")
    keyed = (
        base.with_columns(pl.Series("obs_key", obs_keys(base), dtype=pl.UInt64))
        .select("obs_key", "desig", "obscode", "mjd")
        .sort("obs_key")
    )
    keyed.write_parquet(path / OBS_FILE, compression="zstd")

    # Choose the newest ancestor that still has a full key set, not merely the newest
    # ancestor. Retention prunes key sets on a rolling window, so the immediate parent's
    # may be gone -- and diffing against an older one widens the interval but preserves
    # the signal, which is the whole point of the archive.
    #
    # This previously took `previous[-1]` and, when that parent had been pruned, wrote an
    # EMPTY delta and recorded nothing about why. On 2026-08-06 that silently logged
    # {appeared: 0, disappeared: 0} across a step where 21,627 observations had in fact
    # left the ITF -- indistinguishable from the genuine no-change of 2026-07-29. A
    # measurement that cannot be taken must never be recorded as a measurement of zero.
    parent = next((s for s in reversed(previous) if s.has_full), None)
    immediate = previous[-1] if previous else None
    delta_status: dict[str, Any]

    if parent is not None:
        delta = _delta_between(parent.observations().collect(), keyed)
        delta_status = {
            "computed": True,
            "against": parent.snapshot_id,
            "skipped_pruned_ancestors": [
                s.snapshot_id for s in previous if s.snapshot_id > parent.snapshot_id
            ],
        }
    else:
        delta = pl.DataFrame(schema=_DELTA_SCHEMA)
        delta_status = {
            "computed": False,
            "against": None,
            "reason": (
                "baseline snapshot -- no earlier snapshot exists"
                if immediate is None
                else "no ancestor retains a full key set; the delta could NOT be computed "
                "and the empty delta below is absence of measurement, not absence of change"
            ),
        }
    delta.write_parquet(path / DELTA_FILE, compression="zstd")

    per_desig = (
        tracklets.lazy()
        .group_by("desig")
        .agg(
            pl.len().alias("n_tracklets"),
            pl.col("night").n_unique().alias("n_nights"),
            pl.col("obscode").n_unique().alias("n_obscodes"),
            pl.col("n_obs").sum().alias("n_obs"),
            pl.col("night").min().alias("first_night"),
            pl.col("night").max().alias("last_night"),
        )
        .with_columns(
            (pl.col("last_night") - pl.col("first_night")).cast(pl.Float64).alias("arc_days")
        )
        .sort("desig")
        .collect()
    )
    per_desig.write_parquet(path / DESIG_FILE, compression="zstd")

    if raw_source and raw_source.exists():
        shutil.copy2(raw_source, path / RAW_FILE)

    n_unique = int(keyed["obs_key"].n_unique())
    manifest = {
        "snapshot_id": sid,
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "provenance": provenance,
        "observations": keyed.height,
        "distinct_obs_keys": n_unique,
        # Verified to be genuine byte-identical duplicate records in the MPC's own file,
        # not digest collisions: on the 2026-07-29 snapshot, 476 groups (mostly 6x repeats
        # from W84/DECam) account for all 1,161. See M1-RESULTS.md.
        "duplicate_observations": keyed.height - n_unique,
        "designations": per_desig.height,
        "tracklets": int(per_desig["n_tracklets"].sum()),
        "designations_3plus_nights": int((per_desig["n_nights"] >= 3).sum()),
        "parent_snapshot": parent.snapshot_id if parent is not None else None,
        "immediate_predecessor": immediate.snapshot_id if immediate is not None else None,
        "is_baseline": parent is None and immediate is None,
        "delta": {
            "appeared": int((delta["change"] == APPEARED).sum()) if delta.height else 0,
            "disappeared": int((delta["change"] == DISAPPEARED).sum()) if delta.height else 0,
        },
        # Always present, so a reader never has to infer whether a zero delta means
        # "nothing changed" or "nothing could be measured".
        "delta_status": delta_status,
        "bytes": {
            OBS_FILE: (path / OBS_FILE).stat().st_size,
            DESIG_FILE: (path / DESIG_FILE).stat().st_size,
            DELTA_FILE: (path / DELTA_FILE).stat().st_size,
            RAW_FILE: (path / RAW_FILE).stat().st_size if (path / RAW_FILE).exists() else 0,
        },
    }
    (path / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manifest["pruned"] = prune(root, raw_keep=raw_keep, full_keep=full_keep)
    return manifest


_DELTA_SCHEMA = {
    "obs_key": pl.UInt64,
    "change": pl.Int8,
    "desig": pl.String,
    "obscode": pl.String,
    "mjd": pl.Float64,
}


def _delta_between(earlier: pl.DataFrame, later: pl.DataFrame) -> pl.DataFrame:
    """Rows that left the ITF (``DISAPPEARED``) or joined it (``APPEARED``)."""
    cols = ["obs_key", "desig", "obscode", "mjd"]
    gone = earlier.select(cols).join(later.select("obs_key"), on="obs_key", how="anti")
    new = later.select(cols).join(earlier.select("obs_key"), on="obs_key", how="anti")
    return pl.concat(
        [
            gone.with_columns(pl.lit(DISAPPEARED, dtype=pl.Int8).alias("change")),
            new.with_columns(pl.lit(APPEARED, dtype=pl.Int8).alias("change")),
        ]
    ).select(list(_DELTA_SCHEMA))


def prune(
    root: Path | None = None, *, raw_keep: int = RAW_KEEP, full_keep: int = FULL_KEEP
) -> dict[str, list[str]]:
    """Drop raw files and full key sets outside their rolling windows.

    ``manifest.json`` and ``delta.parquet`` are never removed: together they are the
    permanent record, and dropping either would break the chain that answers "what
    disappeared between A and B" for pairs older than the window.
    """
    snaps = list_snapshots(root)
    dropped: dict[str, list[str]] = {"raw": [], "full": []}
    for snap in snaps[: -raw_keep] if raw_keep > 0 else snaps:
        raw = snap.path / RAW_FILE
        if raw.exists():
            raw.unlink()
            dropped["raw"].append(snap.snapshot_id)
    for snap in snaps[: -full_keep] if full_keep > 0 else snaps:
        for name in (OBS_FILE, DESIG_FILE):
            target = snap.path / name
            if target.exists():
                target.unlink()
        if snap.snapshot_id not in dropped["full"]:
            dropped["full"].append(snap.snapshot_id)
    return dropped


def _by_desig(frame: pl.DataFrame) -> pl.DataFrame:
    return (
        frame.group_by("desig")
        .agg(
            pl.len().alias("n_obs"),
            pl.col("obscode").n_unique().alias("n_obscodes"),
            pl.col("mjd").min().alias("first_mjd"),
            pl.col("mjd").max().alias("last_mjd"),
        )
        .sort("n_obs", descending=True)
    )


def diff(
    a: Snapshot, b: Snapshot, *, sample: int = 20, root: Path | None = None
) -> dict[str, Any]:
    """What changed between two snapshots. ``a`` is the earlier pull, ``b`` the later.

    **Disappeared** observations are the point of the whole archive: an observation leaves
    the ITF when someone links it to an orbit, so this is the MPC's own record of what got
    solved and when -- and, eventually, whether one of ours was among them.

    Uses the full key sets when both snapshots still have them (exact, and a check on the
    chain); otherwise replays ``delta.parquet`` from ``a`` forward to ``b``, which is
    equivalent and survives pruning.
    """
    if a.has_full and b.has_full:
        left = a.observations().select("obs_key", "desig", "obscode", "mjd").collect()
        right = b.observations().select("obs_key", "desig", "obscode", "mjd").collect()
        gone = left.select("obs_key", "desig", "obscode", "mjd").join(
            right.select("obs_key"), on="obs_key", how="anti"
        )
        new = right.select("obs_key", "desig", "obscode", "mjd").join(
            left.select("obs_key"), on="obs_key", how="anti"
        )
        method = "full-key-set"
        totals = (left.height, right.height)
    else:
        gone, new = _replay(a, b, root=root)
        method = "delta-chain"
        totals = (a.manifest.get("observations"), b.manifest.get("observations"))

    gone_desig, new_desig = _by_desig(gone), _by_desig(new)
    return {
        "method": method,
        "from": {"snapshot_id": a.snapshot_id, "observations": totals[0],
                 "provenance": a.manifest.get("provenance")},
        "to": {"snapshot_id": b.snapshot_id, "observations": totals[1],
               "provenance": b.manifest.get("provenance")},
        "disappeared_observations": gone.height,
        "appeared_observations": new.height,
        "net_change": (totals[1] - totals[0]) if None not in totals else None,
        "disappeared_designations": gone_desig.height,
        "appeared_designations": new_desig.height,
        "top_disappeared": gone_desig.head(sample).to_dicts(),
        "top_appeared": new_desig.head(sample).to_dicts(),
    }


def _replay(a: Snapshot, b: Snapshot, *, root: Path | None = None) -> tuple[pl.DataFrame, ...]:
    """Fold the delta chain (a, b] into net disappearances and net appearances.

    An observation that vanished and later came back nets out, which is why the chain is
    folded rather than concatenated: the question is what is *no longer there* at ``b``,
    not what was ever touched in between.
    """
    chain = [s for s in list_snapshots(root) if a.snapshot_id < s.snapshot_id <= b.snapshot_id]
    frames = [s.delta() for s in chain]
    combined = (
        pl.concat(frames) if frames else pl.DataFrame(schema=_DELTA_SCHEMA)
    )
    if not combined.height:
        empty = pl.DataFrame(schema={k: v for k, v in _DELTA_SCHEMA.items() if k != "change"})
        return empty, empty
    net = (
        combined.group_by("obs_key")
        .agg(
            pl.col("change").sum().alias("net"),
            pl.col("desig").last(),
            pl.col("obscode").last(),
            pl.col("mjd").last(),
        )
    )
    cols = ["obs_key", "desig", "obscode", "mjd"]
    return (
        net.filter(pl.col("net") < 0).select(cols),
        net.filter(pl.col("net") > 0).select(cols),
    )
