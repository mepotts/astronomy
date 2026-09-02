"""M1: harvest the public TNS object list, tokenless, via the web CSV export.

Why not /api/get/: it returns HTTP 401 without an API key (measured 2026-08-24).
The tokenless read route is the ordinary search page with &format=csv, which
returns the same fields the web UI shows.  Rate limit measured on BOTH paths:
x-rate-limit-limit: 10 per rolling 60 s.  We use 8/60 s.

Writes data/tns/<tag>.csv (gitignored).
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import (  # noqa: E402
    atomic_write,
    load_cache_contract,
    sha256_bytes,
    validated_tag,
    write_cache,
)
from tns_snapshot import SNAPSHOT_SCHEMA, datetime_to_jd  # noqa: E402
from tnscommon import DATA, session, tns_get  # noqa: E402

TNS_SEARCH = "https://www.wis-tns.org/search"
PAGE = 500  # max accepted; 1000 silently falls back to 50
TNSDIR = DATA / "tns"
TNSDIR.mkdir(parents=True, exist_ok=True)
SNAPDIR = TNSDIR / "snapshots"
SNAPDIR.mkdir(parents=True, exist_ok=True)


def _month_contract(d0: date, d1: date) -> dict:
    return {
        "source_url": TNS_SEARCH,
        "discovery_start_date": d0.isoformat(),
        "discovery_end_exclusive": d1.isoformat(),
        "page_size": PAGE,
    }


def _read_month_cache(path: Path, d0: date, d1: date) -> pd.DataFrame | None:
    try:
        metadata = load_cache_contract(
            path,
            kind="tns_month_csv",
            expected_contract=_month_contract(d0, d1),
        )
    except RuntimeError as exc:
        # Preserve legacy/unproved bytes before the normal harvest replaces them.
        if path.exists() or path.with_name(path.name + ".meta.json").exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            quarantine = TNSDIR / "_quarantine" / f"{stamp}_{path.stem}"
            quarantine.mkdir(parents=True, exist_ok=False)
            for source in (path, path.with_name(path.name + ".meta.json")):
                if source.exists():
                    os.replace(source, quarantine / source.name)
            (quarantine / "reason.txt").write_text(str(exc) + "\n", encoding="utf-8")
            print(f"{path.stem}: quarantined unproved cache ({exc})", flush=True)
        return None
    if metadata is None:
        return None
    frame = pd.read_csv(path, dtype=str)
    if len(frame) != int(metadata.get("row_count", -1)):
        raise RuntimeError(f"verified month cache row count changed: {path}")
    return frame


def _write_month_cache(
    path: Path,
    frame: pd.DataFrame,
    d0: date,
    d1: date,
    *,
    fetch_started: datetime,
    fetch_finished: datetime,
    raw_page_inputs: list[dict] | None = None,
) -> dict:
    payload = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return write_cache(
        path,
        payload,
        kind="tns_month_csv",
        contract=_month_contract(d0, d1),
        row_count=len(frame),
        metadata_extra={
            "fetch_started_at_utc": fetch_started.isoformat().replace("+00:00", "Z"),
            "fetch_started_at_jd": datetime_to_jd(fetch_started),
            "fetch_finished_at_utc": fetch_finished.isoformat().replace("+00:00", "Z"),
            "fetch_finished_at_jd": datetime_to_jd(fetch_finished),
            "raw_page_inputs": raw_page_inputs or [],
        },
    )


def _publish_snapshot(
    full: pd.DataFrame,
    *,
    discovery_start: date,
    discovery_end_exclusive: date,
    month_provenance: list[dict],
) -> dict:
    payload = full.to_csv(index=False, lineterminator="\n").encode("utf-8")
    digest = sha256_bytes(payload)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    snapshot_id = f"tns12mo-{stamp}-{digest[:12]}"
    snapshot = SNAPDIR / f"{snapshot_id}.csv"
    relative = snapshot.relative_to(TNSDIR).as_posix()
    metadata = {
        "schema_version": SNAPSHOT_SCHEMA,
        "snapshot_id": snapshot_id,
        "snapshot_file": relative,
        "snapshot_sha256": digest,
        "row_count": int(len(full)),
        "harvested_at_utc": now.isoformat().replace("+00:00", "Z"),
        "harvested_at_jd": datetime_to_jd(now),
        "registry_observed_at_utc_min": min(
            item["fetch_started_at_utc"] for item in month_provenance
        ),
        "registry_observed_at_utc_max": max(
            item["fetch_finished_at_utc"] for item in month_provenance
        ),
        "registry_observed_at_jd_min": min(
            item["fetch_started_at_jd"] for item in month_provenance
        ),
        "registry_observed_at_jd_max": max(
            item["fetch_finished_at_jd"] for item in month_provenance
        ),
        "discovery_start_date": discovery_start.isoformat(),
        "discovery_end_exclusive": discovery_end_exclusive.isoformat(),
        "source_url": TNS_SEARCH,
        "month_inputs": month_provenance,
        "date_semantics": (
            "Discovery Date (UT) is available; public-report creation time is not "
            "present in this CSV export"
        ),
    }
    if snapshot.exists():
        if snapshot.read_bytes() != payload:
            raise RuntimeError(f"immutable snapshot collision: {snapshot}")
    else:
        atomic_write(snapshot, payload)
    atomic_write(
        snapshot.with_name(snapshot.name + ".meta.json"),
        (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    # Backward-compatible rolling copy for descriptive scripts; candidate code
    # reads the immutable target named by the pointer, never this mutable file.
    atomic_write(TNSDIR / "tns_12mo.csv", payload)
    atomic_write(
        TNSDIR / "tns_12mo.meta.json",
        (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return metadata


def _preserve_raw_page(
    response,
    frame: pd.DataFrame,
    *,
    raw_dir: Path,
    params: dict,
    page: int,
) -> dict:
    payload = response.content
    if not isinstance(payload, bytes) or not payload:
        raise RuntimeError("TNS response did not expose exact HTTP entity bytes")
    path = raw_dir / f"page_{page:04d}.csv"
    proof = write_cache(
        path,
        payload,
        kind="tns_search_page_raw",
        contract={"source_url": TNS_SEARCH, "query": params},
        row_count=len(frame),
        metadata_extra={"exact_http_entity_bytes": True},
    )
    return {"path": path.relative_to(TNSDIR).as_posix(), "proof": proof}


def fetch_window(
    s,
    d0: date,
    d1: date,
    extra: dict | None = None,
    *,
    raw_dir: Path | None = None,
    raw_provenance: list[dict] | None = None,
) -> pd.DataFrame:
    """All TNS objects with discovery date in [d0, d1), paginated."""
    frames, page = [], 0
    empty_schema: pd.DataFrame | None = None
    seen_ids: set[str] = set()
    while True:
        params = {
            "date_start[date]": d0.isoformat(),
            "date_end[date]": (d1 - timedelta(days=1)).isoformat(),
            "num_page": PAGE,
            "page": page,
            "format": "csv",
        }
        if extra:
            params.update(extra)
        r = tns_get(s, TNS_SEARCH, params=params)
        r.raise_for_status()
        txt = r.content.decode("utf-8", "replace")
        if not txt.lstrip().startswith('"ID"'):
            raise RuntimeError(
                f"unexpected TNS payload at {d0} page {page}: {txt[:200]!r}"
            )
        df = pd.read_csv(io.StringIO(txt), dtype=str)
        print(f"  {d0} page {page}: {len(df)} rows", flush=True)
        required_columns = {"ID", "Discovery Date (UT)"}
        if not required_columns.issubset(df.columns):
            raise RuntimeError(
                f"TNS page {page} lacks columns "
                f"{sorted(required_columns - set(df.columns))}"
            )
        if df.empty:
            if raw_dir is not None:
                entry = _preserve_raw_page(
                    r, df, raw_dir=raw_dir, params=params, page=page
                )
                if raw_provenance is not None:
                    raw_provenance.append(entry)
            empty_schema = df
            break
        if "ID" not in df.columns or df["ID"].isna().any():
            raise RuntimeError(f"TNS page {page} has missing object IDs")
        discovery_column = "Discovery Date (UT)"
        if discovery_column not in df.columns:
            raise RuntimeError(
                f"TNS page {page} is missing required {discovery_column!r}"
            )
        discovery_times = pd.to_datetime(
            df[discovery_column], errors="coerce", utc=True
        )
        if discovery_times.isna().any():
            bad_rows = df.index[discovery_times.isna()].tolist()[:3]
            raise RuntimeError(
                f"TNS page {page} has invalid discovery timestamps at rows {bad_rows}"
            )
        start = pd.Timestamp(d0, tz="UTC")
        end = pd.Timestamp(d1, tz="UTC")
        outside = (discovery_times < start) | (discovery_times >= end)
        if outside.any():
            sample = df.loc[outside, discovery_column].astype(str).tolist()[:3]
            raise RuntimeError(
                f"TNS page {page} returned discovery timestamps outside "
                f"[{d0}, {d1}): {sample}; snapshot completeness is unproved"
            )
        page_ids = [str(value).strip() for value in df["ID"].tolist()]
        if any(not value for value in page_ids):
            raise RuntimeError(f"TNS page {page} has blank object IDs")
        if len(set(page_ids)) != len(page_ids):
            raise RuntimeError(f"TNS page {page} repeats an object ID within the page")
        overlap = seen_ids.intersection(page_ids)
        if overlap:
            sample = sorted(overlap)[:3]
            raise RuntimeError(
                f"TNS pagination repeated or overlapped object IDs at page {page}: "
                f"{sample}; snapshot completeness is unproved"
            )
        seen_ids.update(page_ids)
        if raw_dir is not None:
            entry = _preserve_raw_page(r, df, raw_dir=raw_dir, params=params, page=page)
            if raw_provenance is not None:
                raw_provenance.append(entry)
        frames.append(df)
        page += 1
        if page > 40:
            raise RuntimeError("pagination runaway")
    if frames:
        return pd.concat(frames, ignore_index=True)
    return empty_schema if empty_schema is not None else pd.DataFrame()


def _month_windows(today: date) -> list[tuple[date, date]]:
    """Return contiguous month-bounded windows through all of today's UTC date."""
    start = date(today.year - 1, today.month, 1)
    end_exclusive = today + timedelta(days=1)
    windows: list[tuple[date, date]] = []
    cur = start
    while cur < end_exclusive:
        nxt = date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
        windows.append((cur, min(nxt, end_exclusive)))
        cur = nxt
    return windows


def _window_state(
    frame: pd.DataFrame,
    d0: date,
    d1: date,
    *,
    end_exclusive: date,
) -> str:
    """Classify a harvested window and reject impossible closed-month empties."""
    state = "current_partial" if d1 == end_exclusive else "closed"
    if state == "closed" and frame.empty:
        raise RuntimeError(
            f"closed TNS month [{d0}, {d1}) returned a header-only zero-row CSV; "
            "snapshot completeness is unproved"
        )
    return state


def _add_disjoint_window_ids(
    seen_ids: set[str],
    frame: pd.DataFrame,
    *,
    d0: date,
    d1: date,
) -> None:
    """Reject cross-window duplication instead of hiding it in final dedupe."""
    if frame.empty:
        return
    window_ids = {str(value).strip() for value in frame["ID"].tolist()}
    overlap = seen_ids.intersection(window_ids)
    if overlap:
        raise RuntimeError(
            f"TNS windows overlap object IDs in [{d0}, {d1}): "
            f"{sorted(overlap)[:3]}; snapshot completeness is unproved"
        )
    seen_ids.update(window_ids)


def main() -> None:
    s = session()
    today = datetime.now(timezone.utc).date()
    end_exclusive = today + timedelta(days=1)

    # --- 12 months of everything, month by month (deterministic windows) ------
    start = date(today.year - 1, today.month, 1)
    months = _month_windows(today)

    allf = []
    month_provenance = []
    seen_snapshot_ids: set[str] = set()
    harvest_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    for d0, d1 in months:
        tag = validated_tag(f"month_{d0:%Y%m}")
        cache = TNSDIR / f"{tag}.csv"
        # Validate/quarantine any legacy bytes, but deliberately refresh EVERY
        # month. TNS reports can be filed late with a prior-month discovery date;
        # reusing an old closed-month cache would stamp an incomplete catalogue as
        # current. A full scan is roughly 60 rate-limited requests and is the only honest
        # tokenless registry snapshot contract available from this export.
        _read_month_cache(cache, d0, d1)
        fetch_started = datetime.now(timezone.utc)
        raw_page_inputs: list[dict] = []
        raw_dir = TNSDIR / "raw" / harvest_id / f"{d0:%Y%m%d}_{d1:%Y%m%d}"
        df = fetch_window(
            s,
            d0,
            d1,
            raw_dir=raw_dir,
            raw_provenance=raw_page_inputs,
        )
        fetch_finished = datetime.now(timezone.utc)
        window_state = _window_state(
            df,
            d0,
            d1,
            end_exclusive=end_exclusive,
        )
        _add_disjoint_window_ids(seen_snapshot_ids, df, d0=d0, d1=d1)
        month_meta = _write_month_cache(
            cache,
            df,
            d0,
            d1,
            fetch_started=fetch_started,
            fetch_finished=fetch_finished,
            raw_page_inputs=raw_page_inputs,
        )
        month_provenance.append(
            {
                "window": [d0.isoformat(), d1.isoformat()],
                "window_state": window_state,
                "sha256": month_meta["payload_sha256"],
                "row_count": month_meta["row_count"],
                "fetch_started_at_utc": month_meta["fetch_started_at_utc"],
                "fetch_started_at_jd": month_meta["fetch_started_at_jd"],
                "fetch_finished_at_utc": month_meta["fetch_finished_at_utc"],
                "fetch_finished_at_jd": month_meta["fetch_finished_at_jd"],
                "raw_page_inputs": raw_page_inputs,
            }
        )
        print(f"{tag}: fetched {len(df)}", flush=True)
        allf.append(df)

    full = pd.concat(allf, ignore_index=True)
    snapshot = _publish_snapshot(
        full,
        discovery_start=start,
        discovery_end_exclusive=end_exclusive,
        month_provenance=month_provenance,
    )
    print(
        f"TOTAL 12 months: {len(full)} objects -> {snapshot['snapshot_id']} "
        f"({snapshot['snapshot_sha256'][:12]})"
    )


if __name__ == "__main__":
    main()
