"""Shared TNS matching with frozen historical membership and live annotation."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from tns_snapshot import read_snapshot, rows_discovered_as_of


def verified_provenance(
    reference: dict[str, Any] | None, jd_ceiling: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the frozen dedupe snapshot and latest operational snapshot."""
    _rows, historical = read_snapshot(
        required_coverage_jd=jd_ceiling,
        reference=reference,
    )
    _current_rows, current = read_snapshot(
        required_coverage_jd=jd_ceiling,
        max_lag_days=math.inf,
    )
    return historical, current


def _nearest(candidates: pd.DataFrame, rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    if not len(candidates):
        return np.array([], dtype=object), np.array([], dtype=float)
    if not rows:
        return (
            np.full(len(candidates), "", dtype=object),
            np.full(len(candidates), np.inf, dtype=float),
        )
    from astropy import units as u
    from astropy.coordinates import SkyCoord

    catalogue = pd.DataFrame(rows)
    tc = SkyCoord(
        catalogue["RA"].values,
        catalogue["DEC"].values,
        unit=(u.hourangle, u.deg),
    )
    cc = SkyCoord(
        pd.to_numeric(candidates["ra"], errors="raise").values * u.deg,
        pd.to_numeric(candidates["dec"], errors="raise").values * u.deg,
    )
    indices, distances, _ = cc.match_to_catalog_sky(tc)
    return catalogue["Name"].values[indices], distances.arcsec


def apply_tns_contract(
    candidates: pd.DataFrame,
    *,
    frozen_reference: dict[str, Any] | None,
    jd_ceiling: float,
    match_arcsec: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Remove only frozen discovery-date-as-of matches; annotate latest matches.

    The immutable candidate-pinned snapshot determines reproducible membership. The
    rolling latest snapshot is deliberately annotation-only, so a later TNS
    report cannot rewrite an already frozen candidate census.
    """
    frozen_rows, frozen = read_snapshot(
        required_coverage_jd=jd_ceiling,
        reference=frozen_reference,
    )
    current_rows, current = read_snapshot(
        required_coverage_jd=jd_ceiling,
        max_lag_days=math.inf,
    )
    historical_rows = rows_discovered_as_of(frozen_rows, jd_ceiling)
    out = candidates.copy()
    asof_name, asof_sep = _nearest(out, historical_rows)
    current_name, current_sep = _nearest(out, current_rows)
    out["tns_frozen_nearest"] = asof_name
    out["tns_frozen_sep_arcsec"] = np.round(asof_sep, 2)
    out["tns_current_nearest"] = current_name
    out["tns_current_sep_arcsec"] = np.round(current_sep, 2)
    out["tns_current_match"] = current_sep <= float(match_arcsec)
    out["tns_snapshot_id"] = frozen["snapshot_id"]
    out["tns_snapshot_jd"] = frozen["harvested_at_jd"]
    out["tns_current_snapshot_id"] = current["snapshot_id"]
    historical_match = asof_sep <= float(match_arcsec)
    kept = out.loc[~historical_match].copy()
    contract = {
        "historical": frozen,
        "operational_current": current,
        "n_input": int(len(out)),
        "n_removed_frozen_discovery_date_bounded": int(historical_match.sum()),
        "n_current_matches_among_frozen_candidates": int(
            kept["tns_current_match"].sum()
        ),
        "membership_rule": (
            "conservative dedupe: remove <= match radius only when Discovery Date "
            "(UT) <= history_jd_ceiling in the immutable candidate-pinned snapshot"
        ),
        "current_rule": "latest verified snapshot is annotation-only",
        "report_time_caveat": (
            "The public CSV lacks report-publication time. This uses limited future "
            "registry knowledge for conservative duplicate avoidance and is not an "
            "exact reconstruction of historical TNS membership. The pinned snapshot "
            "must be within one day after the history ceiling."
        ),
    }
    return kept, contract
