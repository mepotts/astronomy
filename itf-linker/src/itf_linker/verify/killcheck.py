"""The M0 kill-check: can we locate a *known* link's observations in the ITF snapshot?

Three questions are asked of each published identification MPEC:

1. **Exact-observation presence.** For MPECs that print full 80-column astrometry, is each
   of those observations in the ITF snapshot (matched on observatory + time + sky position,
   never on designation -- ITF records carry survey trkSubs, not MPC designations)?
2. **Designation presence.** Does the ITF still contain the object's packed designation?
3. **Night occupancy.** For every (night, observatory) the MPEC used, how much ITF material
   sits in that same cell? This bounds the haystack even when the needle has been removed.

Absence is an expected and informative outcome -- publishing a link is precisely what
removes its observations from the ITF. Absence is only meaningful if the matcher can
*find* things, so :func:`sensitivity_control` re-queries known-present ITF rows through
the identical code path and asserts a 100% hit rate.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from ..mpc80 import Observation

HALF_MONTH_LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXY"
_BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def pack_designation(desig: str) -> str | None:
    """Pack a provisional designation, e.g. ``2009 AC16`` -> ``K09A16C``.

    Verified against MPEC 2026-O57, which prints ``2009 AC16`` astrometry under the
    packed form ``K09A16C``.
    """
    parts = desig.strip().split()
    if len(parts) != 2 or not parts[0].isdigit():
        return None
    year = int(parts[0])
    tail = parts[1]
    if len(tail) < 2 or not tail[0].isalpha() or not tail[1].isalpha():
        return None
    century = {18: "I", 19: "J", 20: "K"}.get(year // 100)
    if century is None:
        return None
    first, second = tail[0].upper(), tail[1].upper()
    cycle_txt = tail[2:]
    cycle = int(cycle_txt) if cycle_txt else 0
    if cycle < 100:
        packed_cycle = f"{cycle:02d}"
    elif cycle < 620:
        packed_cycle = _BASE62[cycle // 10] + str(cycle % 10)
    else:
        return None
    return f"{century}{year % 100:02d}{first}{packed_cycle}{second}"


def angular_sep_arcsec(
    ra1: np.ndarray, dec1: np.ndarray, ra2: float, dec2: float
) -> np.ndarray:
    """Small-angle great-circle separation in arcseconds."""
    d_ra = (ra1 - ra2) * np.cos(np.radians(dec2))
    d_dec = dec1 - dec2
    return np.hypot(d_ra, d_dec) * 3600.0


def find_observation(
    itf: pl.DataFrame,
    obs: Observation,
    *,
    mjd_tol_days: float = 1.0 / 86400.0 * 5.0,
    radius_arcsec: float = 10.0,
) -> pl.DataFrame:
    """Locate an observation in the ITF by observatory + epoch + position (never designation)."""
    near = itf.filter(
        (pl.col("obscode") == obs.obscode)
        & ((pl.col("mjd") - obs.mjd).abs() <= mjd_tol_days)
    )
    if near.height == 0:
        return near
    sep = angular_sep_arcsec(
        near["ra_deg"].to_numpy(), near["dec_deg"].to_numpy(), obs.ra_deg, obs.dec_deg
    )
    return near.with_columns(pl.Series("sep_arcsec", sep)).filter(
        pl.col("sep_arcsec") <= radius_arcsec
    )


def sensitivity_control(
    itf: pl.DataFrame, n: int = 200, seed: int = 20260729, **kwargs: Any
) -> dict[str, Any]:
    """Round-trip known-present ITF rows through :func:`find_observation`.

    Establishes that a "not found" verdict elsewhere reflects real absence rather than a
    broken matcher. Must be 100%.
    """
    sample = itf.sample(n=min(n, itf.height), seed=seed)
    from ..mpc80 import Observation as Obs

    hits = 0
    for row in sample.iter_rows(named=True):
        probe = Obs(
            number="", desig=row["desig"], discovery=False, note1="", note2="",
            year=row["year"], month=row["month"], day=row["day"], mjd=row["mjd"],
            ra_deg=row["ra_deg"], dec_deg=row["dec_deg"], mag=row["mag"],
            band="", catalog="", reference="", obscode=row["obscode"],
        )
        if find_observation(itf, probe, **kwargs).height > 0:
            hits += 1
    return {
        "probed": sample.height,
        "found": hits,
        "hit_rate": round(hits / sample.height, 4) if sample.height else 0.0,
        "passes": hits == sample.height,
    }


def check_mpec_against_itf(
    mpec: Any,
    itf: pl.DataFrame,
    tracklets: pl.DataFrame,
    *,
    radius_arcsec: float = 10.0,
) -> dict[str, Any]:
    """Run all three presence questions for one MPEC. See module docstring."""
    from .mpec import acceptance_summary, residual_tracklets

    trk = residual_tracklets(mpec)

    # (1) exact-observation presence, where the MPEC printed full astrometry
    obs_results = []
    for obs in mpec.observations:
        hit = find_observation(itf, obs, radius_arcsec=radius_arcsec)
        obs_results.append(
            {
                "desig": obs.desig,
                "obscode": obs.obscode,
                "mjd": round(obs.mjd, 6),
                "ra_deg": round(obs.ra_deg, 6),
                "dec_deg": round(obs.dec_deg, 6),
                "in_itf": hit.height > 0,
                "itf_desig": hit["desig"].to_list()[:3] if hit.height else [],
            }
        )

    # (2) designation presence
    desig_probe: dict[str, Any] = {}
    if mpec.headline:
        for name in [p.strip() for p in mpec.headline.split("=")]:
            packed = pack_designation(name)
            if packed:
                desig_probe[name] = {
                    "packed": packed,
                    "itf_rows": itf.filter(pl.col("desig") == packed).height,
                }

    # (3) night occupancy: how much ITF material shares each (night, observatory) cell
    occupancy = []
    for t in trk:
        night = int(np.floor(t["mjd_midnight"] + 0.5))
        cell = tracklets.filter(
            (pl.col("obscode") == t["obscode"])
            & ((pl.col("night") - night).abs() <= 1)
        )
        occupancy.append(
            {
                "obs_date": t["obs_date"],
                "obscode": t["obscode"],
                "mpec_n_obs": t["n_obs"],
                "itf_tracklets_same_night_same_obs": cell.height,
                "itf_obs_same_night_same_obs": int(cell["n_obs"].sum()) if cell.height else 0,
            }
        )

    return {
        "packed": mpec.packed,
        "mpec_id": mpec.mpec_id,
        "headline": mpec.headline,
        "identified_by": mpec.identified_by,
        "constituent_observations": mpec.n_constituent,
        "eighty_col_lines": len(mpec.observations),
        "reconstructed_tracklets": trk,
        "acceptance": acceptance_summary(trk),
        "exact_observation_matches": obs_results,
        "n_exact_found": sum(1 for r in obs_results if r["in_itf"]),
        "designation_probe": desig_probe,
        "night_occupancy": occupancy,
    }
