"""ESO and NASA Exoplanet Archive TAP queries.

Three ADQL lessons are baked in here; all three cost a failed query to find:

1. ``CONTAINS(POINT('ICRS', ra, dec), CIRCLE(...))`` **fails on ``dbo.raw``** with a
   SQL-Server geography error ("Latitude values must be between -90 and 90"): the table
   holds rows whose coordinates do not validate. A plain ra/dec box works and is faster.
2. ``ORDER BY MIN(col)`` is rejected -- ``MIN`` is a reserved ADQL word in that position.
   Sort client-side instead.
3. ``dbo.raw`` has no ``exptime`` or ``tel_ambi_fwhm``; the exposure column is ``exp_start``.

Every endpoint is anonymous. Nothing here writes to disk.
"""

from __future__ import annotations

import math

import pyvo
from astropy.time import Time

from ..config import ESO_TAP, NEA_TAP, SEARCH_RADIUS_DEG
from .inventory import Frame, Inventory, parse_release, parse_setting, roll_up, utcnow


def _service(url: str) -> pyvo.dal.TAPService:
    return pyvo.dal.TAPService(url)


def _box(ra_deg: float, dec_deg: float, radius_deg: float,
         ra_col: str = "ra", dec_col: str = "dec") -> str:
    """ADQL box predicate. Widened in RA by 1/cos(dec) so it stays a true angular radius.

    Clamped at |dec| > 89.9 to avoid a blow-up at the poles; no direct-imaging target of
    interest sits there, and a too-wide RA range only over-selects.
    """
    dra = radius_deg / max(math.cos(math.radians(dec_deg)), 1e-3)
    return (
        f"{ra_col} BETWEEN {ra_deg - dra:.6f} AND {ra_deg + dra:.6f} "
        f"AND {dec_col} BETWEEN {dec_deg - radius_deg:.6f} AND {dec_deg + radius_deg:.6f}"
    )


def query_raw_frames(
    ra_deg: float, dec_deg: float, radius_deg: float = SEARCH_RADIUS_DEG,
    instrument: str = "CRIRES%",
) -> list[Frame]:
    """Raw science spectra from ``dbo.raw`` -- what the telescope actually took."""
    q = f"""
    SELECT object, date_obs, prog_id, filter_path, release_date
    FROM dbo.raw
    WHERE {_box(ra_deg, dec_deg, radius_deg)}
      AND instrument LIKE '{instrument}'
      AND dp_cat = 'SCIENCE' AND dp_tech LIKE 'SPECTRUM%'
    """
    rows = _service(ESO_TAP).search(q, maxrec=20000)
    return [
        Frame(
            target=str(r["object"]),
            night=str(r["date_obs"])[:10],
            prog_id=str(r["prog_id"]),
            setting=parse_setting(r["filter_path"]),
            release=parse_release(r["release_date"]),
            reduced=False,
        )
        for r in rows
    ]


def query_reduced_products(
    ra_deg: float, dec_deg: float, radius_deg: float = SEARCH_RADIUS_DEG,
    collection: str = "CRIRESplus",
) -> list[Frame]:
    """``calib_level=2`` products from ``ivoa.ObsCore`` -- pipeline-reduced 1D spectra.

    These are the ones that let this project skip esorex entirely. ``ObsCore`` has no
    ``filter_path``; the setting is recovered downstream by matching night against the raw
    inventory, so ``setting`` is left as "?" here rather than guessed from wavelength.
    """
    q = f"""
    SELECT target_name, t_min, obs_release_date, em_min, em_max, access_url, access_estsize
    FROM ivoa.ObsCore
    WHERE {_box(ra_deg, dec_deg, radius_deg, 's_ra', 's_dec')}
      AND obs_collection = '{collection}' AND calib_level = 2
    """
    rows = _service(ESO_TAP).search(q, maxrec=20000)
    return [
        Frame(
            target=str(r["target_name"]),
            night=Time(float(r["t_min"]), format="mjd").iso[:10],
            prog_id="(reduced)",
            setting="?",
            release=parse_release(r["obs_release_date"]),
            reduced=True,
            access_url=str(r["access_url"]),
        )
        for r in rows
    ]


def build_inventory(
    target: str, ra_deg: float, dec_deg: float, radius_deg: float = SEARCH_RADIUS_DEG
) -> Inventory:
    """Raw + reduced, merged into one per-night view.

    Reduced products carry no setting, so each reduced night inherits the settings
    observed that night in the raw table. A reduced night with no raw counterpart keeps
    "?" and will not match a band filter -- deliberately conservative.
    """
    raw = query_raw_frames(ra_deg, dec_deg, radius_deg)
    red = query_reduced_products(ra_deg, dec_deg, radius_deg)

    settings_by_night: dict[str, set[str]] = {}
    for f in raw:
        settings_by_night.setdefault(f.night, set()).add(f.setting)

    red = [
        Frame(f.target, f.night, f.prog_id,
              min(settings_by_night.get(f.night, {"?"})),
              f.release, reduced=True, access_url=f.access_url)
        for f in red
    ]
    return Inventory(target=target, nights=roll_up(raw + red), now=utcnow())


def query_imaged_companions() -> list[dict]:
    """Directly imaged companions from the NASA Exoplanet Archive.

    Known incompleteness: ``pscomppars`` caps companion mass at 30 M_Jup, so the
    CD-35 2722 B class of object is absent. M1 must supplement this. See DATA-SOURCES.md.
    """
    q = """
    SELECT pl_name, hostname, ra, dec, sy_dist, pl_bmassj, pl_orbsmax, st_age, st_mass,
           sy_hmag, sy_kmag
    FROM pscomppars WHERE discoverymethod = 'Imaging'
    """
    rows = _service(NEA_TAP).search(q, maxrec=5000)
    out = []
    for r in rows:
        d = {}
        for c in ("pl_name", "hostname"):
            d[c] = str(r[c])
        for c in ("ra", "dec", "sy_dist", "pl_bmassj", "pl_orbsmax", "st_age", "st_mass",
                  "sy_hmag", "sy_kmag"):
            v = r[c]
            d[c] = None if v is None or str(v) in ("--", "nan") else float(v)
        out.append(d)
    return out
