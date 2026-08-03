"""Read-only downloads of the ITF snapshot and supporting MPC tables.

Provenance matters here: the ITF is *regenerated continuously*, so any count derived
from it is only meaningful alongside the ``Last-Modified`` / ``ETag`` / byte-size of the
exact snapshot it came from. :func:`fetch_itf` records those to
``data/raw/itf.provenance.json`` next to the file.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from .. import config


def _get(url: str, *, stream: bool = False, timeout: int = 300) -> requests.Response:
    resp = requests.get(
        url, headers={"User-Agent": config.USER_AGENT}, stream=stream, timeout=timeout
    )
    resp.raise_for_status()
    return resp


def fetch_itf(dest: Path | None = None, *, force: bool = False) -> dict[str, Any]:
    """Download the ITF snapshot to ``dest`` and write a provenance sidecar.

    Skips the transfer when the file already exists and ``force`` is false, but still
    returns the recorded provenance so callers can quote it.
    """
    dest = dest or config.ITF_GZ
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        existing = load_provenance()
        if existing:
            return existing

    with _get(config.ITF_URL, stream=True) as resp:
        headers = dict(resp.headers)
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
        tmp.replace(dest)

    provenance = {
        "url": config.ITF_URL,
        "path": str(dest),
        "size_bytes": dest.stat().st_size,
        "last_modified": headers.get("Last-Modified"),
        "etag": headers.get("ETag"),
        "content_length": headers.get("Content-Length"),
        "fetched_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    config.ITF_PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    config.ITF_PROVENANCE.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return provenance


def load_provenance(path: Path | None = None) -> dict[str, Any] | None:
    path = path or config.ITF_PROVENANCE
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_mpec(packed: str, dest_dir: Path | None = None, *, force: bool = False) -> Path:
    """Download one MPEC by its packed id (e.g. ``K26O40``) and cache the raw HTML."""
    dest_dir = dest_dir or config.MPEC_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{packed}.html"
    if dest.exists() and not force:
        return dest
    url = config.MPEC_URL_TEMPLATE.format(yy=packed[1:3], packed=packed)
    resp = _get(url, timeout=60)
    dest.write_text(resp.text, encoding="utf-8")
    return dest


def parse_obscodes(text: str) -> dict[str, float]:
    """Extract ``{observatory_code: east_longitude_degrees}`` from the MPC ObsCodes page.

    Columns are fixed-width: code in 1-3, longitude in 5-13. Space telescopes and roving
    observers have blank coordinates and are skipped -- callers fall back to a 0 deg
    (UTC) night boundary for those.
    """
    out: dict[str, float] = {}
    for line in text.splitlines():
        if len(line) < 13:
            continue
        code = line[0:3].strip()
        lon_txt = line[4:13].strip()
        if len(code) != 3 or not lon_txt:
            continue
        try:
            out[code] = float(lon_txt)
        except ValueError:
            continue
    return out


def parse_obscodes_full(text: str) -> dict[str, tuple[float, float, float]]:
    """Extract ``{code: (east_longitude_deg, rho*cos(phi'), rho*sin(phi'))}``.

    The parallax constants are what turn a geocentric ephemeris into a *topocentric* one,
    and they are the reason M3's linker can place an observatory to a few metres without
    ever needing geodetic coordinates: the MPC publishes ``rho cos phi'`` and
    ``rho sin phi'`` in Earth radii, already folding in the flattening.

    Columns are fixed-width and *not* whitespace-separated -- code 1-3, longitude 5-13,
    ``cos`` 14-21, ``sin`` 22-30. Splitting on whitespace works for most rows and fails
    silently on the ones where the fields abut (``005   2.231000.659891+0.748875Meudon``),
    which includes several major survey sites.

    Codes with blank coordinates -- space telescopes (C51) and roving observers (247) --
    are omitted rather than defaulted, so a caller must decide explicitly what to do with
    them.
    """
    out: dict[str, tuple[float, float, float]] = {}
    for line in text.splitlines():
        if len(line) < 30:
            continue
        code = line[0:3].strip()
        if len(code) != 3 or code == "Cod":
            continue
        try:
            lon = float(line[4:13].strip())
            rho_cos = float(line[13:21].strip())
            rho_sin = float(line[21:30].strip())
        except ValueError:
            continue
        out[code] = (lon, rho_cos, rho_sin)
    return out


def obscodes_html(dest: Path | None = None, *, force: bool = False) -> str:
    """Fetch (and cache) the MPC observatory-code table as raw HTML."""
    dest = dest or (config.RAW_DIR / "ObsCodes.html")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or force:
        resp = _get(config.OBSCODES_URL, timeout=120)
        dest.write_text(resp.text, encoding="utf-8", errors="replace")
    return dest.read_text(encoding="utf-8", errors="replace")


def fetch_obscodes(dest: Path | None = None, *, force: bool = False) -> dict[str, float]:
    """Fetch (and cache) observatory east longitudes, used for local-night boundaries."""
    return parse_obscodes(obscodes_html(dest, force=force))


def fetch_obscodes_full(
    dest: Path | None = None, *, force: bool = False
) -> dict[str, tuple[float, float, float]]:
    """Fetch (and cache) longitude plus both parallax constants per observatory."""
    return parse_obscodes_full(obscodes_html(dest, force=force))
