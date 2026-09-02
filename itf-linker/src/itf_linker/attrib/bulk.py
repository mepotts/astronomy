"""Bulk orbits: the MPCORB extended JSON, streamed, filtered, and turned into states.

M7 pulled 400 orbits through the get-orb API at >= 1.1 s spacing -- correct for a
validation subset, hopeless for ~30k objects (9+ hours of polite requests for data the
MPC already publishes as one file). The bulk route is the MPC's own
``Extended_Files/mpcorb_extended.json.gz``: every orbit they publish, with the fields
the API's ``orbit_fit_statistics`` block carries *plus* ``Other_desigs`` -- which is what
resolves a batch provid that has since been merged into another designation (M7 trap 8:
dedupe on the primary, never the requested name).

Three conventions, verified against the API responses this repo already caches
(``scripts/m8_fetch_bulk.py`` runs the comparison and records it):

* Elements are heliocentric **ecliptic J2000** Keplerian (a, e, i, Node, Peri = argument
  of perihelion, M) at ``Epoch`` given as **JD(TT)**. The state built here is rotated to
  ICRS-equatorial by the same matrix as every other attribution input.
* ``U`` is a string: a digit, or blank/'E'/'D' when no uncertainty parameter applies --
  parsed to ``None`` then, exactly as the API path leaves an absent U_param.
* ``H``/``G`` may be absent (comet-like entries); ``G`` defaults to 0.15 downstream.

The parser is *streaming*: the decompressed file is ~2.6 GB of one JSON array, and
loading it whole would cost ~10 GB of Python objects. ``iter_mpcorb_objects`` walks the
array with ``JSONDecoder.raw_decode`` over a sliding buffer instead -- constant memory,
no third-party dependency, and it either parses an object or raises; there is no
regex-shaped "probably an object boundary" failure mode.
"""

from __future__ import annotations

import gzip
import json
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from ..link.geometry import GM_SUN
from .core import ECL_TO_EQ, AttribOrbit

#: Characters between array elements that the scanner skips without copying.
_SKIP = frozenset(" \t\r\n,")


def iter_mpcorb_objects(path: Path, *, chunk_bytes: int = 8 << 20) -> Iterator[dict[str, Any]]:
    """Yield each object of a (gzipped) JSON array without loading the file whole.

    The scan is **index-based**: ``JSONDecoder.raw_decode(buf, idx)`` parses in place
    and the buffer is compacted only when more bytes are needed. The first version
    sliced the remaining buffer per object, which is O(chunk_bytes) *per object* --
    ~1.5M objects x 8 MB of copying turned a ~1-minute parse into an hours-long one.
    """
    decoder = json.JSONDecoder()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[operator]
        buf = ""
        pos = 0
        started = False
        eof = False
        while True:
            if not eof:
                chunk = fh.read(chunk_bytes)
                if not chunk:
                    eof = True
                else:
                    buf = buf[pos:] + chunk
                    pos = 0
            if not started:
                i = buf.find("[", pos)
                if i < 0:
                    if not eof:
                        pos = len(buf)
                        continue
                    raise ValueError(f"{path}: no JSON array found")
                pos = i + 1
                started = True
            while True:
                while pos < len(buf) and buf[pos] in _SKIP:
                    pos += 1
                if pos >= len(buf):
                    if eof:
                        return
                    break  # refill
                if buf[pos] == "]":
                    return
                try:
                    obj, pos = decoder.raw_decode(buf, pos)
                except json.JSONDecodeError:
                    if eof:  # an unparseable tail at EOF is corruption
                        raise
                    break  # need more bytes
                yield obj


def elements_to_state(
    a_au: float,
    e: float,
    incl_deg: float,
    node_deg: float,
    argperi_deg: float,
    mean_anom_deg: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Heliocentric ICRS-equatorial (r, v) from ecliptic-J2000 Keplerian elements.

    Elliptic orbits only (every MPCORB entry has e < 1); Kepler's equation by Newton
    from the ``M + e sin M`` start, 20 iterations -- overkill at machine precision for
    e <= 0.99, and this runs once per orbit, not per epoch.
    """
    if not (0.0 <= e < 1.0) or a_au <= 0.0:
        raise ValueError(f"not an elliptic orbit: a={a_au}, e={e}")
    inc = math.radians(incl_deg)
    node = math.radians(node_deg)
    omega = math.radians(argperi_deg)
    m_anom = math.radians(mean_anom_deg % 360.0)

    ecc_anom = m_anom + e * math.sin(m_anom)
    for _ in range(30):
        f = ecc_anom - e * math.sin(ecc_anom) - m_anom
        ecc_anom -= f / (1.0 - e * math.cos(ecc_anom))
    if abs(ecc_anom - e * math.sin(ecc_anom) - m_anom) > 1e-9:
        # Newton can cycle at extreme eccentricity; a silently wrong anomaly would be a
        # silently wrong sky position, so refuse instead (caller records the drop).
        raise ValueError(f"Kepler solve did not converge: e={e}, M={mean_anom_deg}")
    ce, se = math.cos(ecc_anom), math.sin(ecc_anom)
    b_over_a = math.sqrt(1.0 - e * e)
    xp = a_au * (ce - e)
    yp = a_au * b_over_a * se
    n_motion = math.sqrt(GM_SUN / a_au**3)
    r_norm = a_au * (1.0 - e * ce)
    vxp = -a_au * n_motion * se * a_au / r_norm
    vyp = a_au * n_motion * b_over_a * ce * a_au / r_norm

    co, so = math.cos(omega), math.sin(omega)
    cn, sn = math.cos(node), math.sin(node)
    ci, si = math.cos(inc), math.sin(inc)
    rot = np.array(
        [
            [co * cn - so * sn * ci, -so * cn - co * sn * ci],
            [co * sn + so * cn * ci, -so * sn + co * cn * ci],
            [so * si, co * si],
        ]
    )
    r_ecl = rot @ np.array([xp, yp])
    v_ecl = rot @ np.array([vxp, vyp])
    return ECL_TO_EQ @ r_ecl, ECL_TO_EQ @ v_ecl


def _u_param(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def _f(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def mpcorb_to_orbit(row: dict[str, Any]) -> AttribOrbit | None:
    """One extended-JSON object -> :class:`AttribOrbit`, or ``None`` if unusable."""
    needed = ("a", "e", "i", "Node", "Peri", "M", "Epoch")
    if any(row.get(k) is None for k in needed):
        return None
    try:
        r0, v0 = elements_to_state(
            float(row["a"]), float(row["e"]), float(row["i"]),
            float(row["Node"]), float(row["Peri"]), float(row["M"]),
        )
    except ValueError:
        return None
    primary = str(row.get("Principal_desig") or row.get("Number") or "").strip()
    if not primary:
        return None
    arc_days = _f(row.get("Arc_length"))
    if arc_days is None and row.get("Arc_years") is not None:
        arc_days = _f(row["Arc_years"])
        arc_days = arc_days * 365.25 if arc_days is not None else None
    return AttribOrbit(
        requested_desig=primary,
        primary_desig=primary,
        packed_primary="",  # the extended file carries unpacked designations only
        all_desigs=[primary]
        + [str(d) for d in (row.get("Other_desigs") or [])],
        epoch_mjd_tt=float(row["Epoch"]) - 2400000.5,
        r0=r0,
        v0=v0,
        h_mag=_f(row.get("H")),
        g_slope=_f(row.get("G")),
        u_param=_u_param(row.get("U")),
        arc_days=arc_days,
        n_obs=row.get("Num_obs"),
        n_opp=row.get("Num_opps"),
        normalized_rms=_f(row.get("rms")),
        orbit_quality=None,
        orbit_type=str(row.get("Orbit_type") or "") or None,
        moid_earth=_f(row.get("Earth_MOID")),
    )
