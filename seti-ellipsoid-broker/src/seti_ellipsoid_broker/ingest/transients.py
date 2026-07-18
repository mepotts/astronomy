"""Account-free transient input: read an externally-exported alert list from a CSV.

This is the primary UNBLOCK for live use. Because Lasair-ZTF accounts do not transfer to
the Rubin era and registration has moved to the (account-gated) Lasair-LSST instance, the
auto-ingest path (``ingest/lasair.py``) is effectively unavailable. Instead, a user exports
an alert list from ANY broker (Lasair, Fink, ALeRCE, ANTARES, TNS) or hand-builds their own
and feeds it here; the rest of the pipeline (live anonymous Gaia crossmatch + zero-point ->
ellipsoid -> rank -> export) then runs end to end with NO account and NO token.

CSV schema (header-driven, case-insensitive; common aliases accepted):
    name / id / source_ref / objectId ......... REQUIRED  transient identifier
    ra  / ra_deg / ramean ..................... REQUIRED  ICRS right ascension, degrees
    dec / dec_deg / decmean ................... REQUIRED  ICRS declination, degrees
    gaia_source_id / source_id / gaia_dr3 ..... optional  pre-resolved Gaia DR3 id
    mjd / discovery_mjd ....................... optional  detection time (MJD)
    discovery_date / date ..................... optional  ISO date (parsed to MJD if no mjd)
    survey / broker ........................... optional  origin label (default "CSV")
    mag / gmag / mag_or_dm / dm ............... optional  magnitude (or DM for FRBs)

Only name/ra/dec are required; everything else is optional. ``mjd`` is not used by the
ellipsoid crossing math (which depends only on position + Gaia distance), so a missing
detection time is harmless and defaults to 0.0.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

from ..models import Alert

# header alias -> canonical field
_ALIASES: dict[str, str] = {
    "name": "name", "id": "name", "source_ref": "name", "objectid": "name",
    "object_id": "name", "iau_name": "name", "tns_name": "name",
    "ra": "ra", "ra_deg": "ra", "ramean": "ra", "radeg": "ra", "raj2000": "ra",
    "dec": "dec", "dec_deg": "dec", "decmean": "dec", "decdeg": "dec", "dej2000": "dec",
    "gaia_source_id": "gaia", "source_id": "gaia", "gaia_dr3": "gaia",
    "gaia_dr3_source_id": "gaia", "gaiadr3": "gaia", "gaia_id": "gaia",
    "mjd": "mjd", "discovery_mjd": "mjd", "mjd_discovery": "mjd", "disc_mjd": "mjd",
    "discovery_date": "date", "date": "date", "disc_date": "date", "discoverydate": "date",
    "survey": "survey", "broker": "survey", "origin": "survey",
    "mag": "mag", "gmag": "mag", "magnitude": "mag", "mag_or_dm": "mag", "dm": "mag",
}


def _canon_header(field: str) -> str | None:
    return _ALIASES.get(field.strip().lower().lstrip("﻿"))


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return float(value)


def _date_to_mjd(value: str) -> float:
    """Parse an ISO date/datetime to MJD (astropy imported lazily)."""
    from astropy.time import Time

    return float(Time(value.strip(), format=None, scale="utc").mjd)


def iter_transients_csv(path: str | Path) -> Iterator[Alert]:
    """Yield one :class:`~seti_ellipsoid_broker.models.Alert` per data row of ``path``."""
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            return
        header = [_canon_header(h) for h in raw_header]
        canon_set = {h for h in header if h}
        for req in ("name", "ra", "dec"):
            if req not in canon_set:
                raise ValueError(
                    f"transients CSV {path} is missing a required '{req}' column "
                    f"(header was {raw_header!r}); need name, ra, dec at minimum."
                )
        for lineno, row in enumerate(reader, start=2):
            if not any(cell.strip() for cell in row):
                continue  # skip blank lines
            fields: dict[str, str] = {}
            for key, cell in zip(header, row):
                if key is not None:
                    fields[key] = cell
            try:
                ra = _to_float(fields.get("ra"))
                dec = _to_float(fields.get("dec"))
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: bad ra/dec ({exc})") from exc
            name = (fields.get("name") or "").strip()
            if not name or ra is None or dec is None:
                raise ValueError(f"{path}:{lineno}: name/ra/dec are required, got {fields!r}")

            mjd = _to_float(fields.get("mjd"))
            if mjd is None and fields.get("date", "").strip():
                mjd = _date_to_mjd(fields["date"])
            if mjd is None:
                mjd = 0.0  # unused by the ellipsoid math; a harmless placeholder

            gaia_raw = (fields.get("gaia") or "").strip()
            gaia_source_id = int(gaia_raw) if gaia_raw else None

            yield Alert(
                source_ref=name,
                survey=(fields.get("survey") or "CSV").strip() or "CSV",
                ra_deg=ra,
                dec_deg=dec,
                mjd=mjd,
                mag_or_dm=_to_float(fields.get("mag")),
                gaia_source_id=gaia_source_id,
            )


def read_transients_csv(path: str | Path) -> list[Alert]:
    """Eagerly read ``path`` into a list of Alerts (see module docstring for the schema)."""
    return list(iter_transients_csv(path))
