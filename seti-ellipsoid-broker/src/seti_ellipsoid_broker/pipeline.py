"""Offline, deterministic broker pipeline (M1 core).

Wires the full reactive path WITHOUT any network or credentials, so `seti-broker run`
can produce real CSV / .tgt / Markdown artifacts in an offline/mock mode:

    synthetic alerts  ->  SQLite staging  ->  ellipsoid math  ->  ranking  ->  export

The shape mirrors the live pipeline exactly; only the two external legs are swapped for
deterministic fakes:

  * `synthetic_alerts()`         stands in for `ingest.lasair.fetch_recent_alerts`
                                 (live path blocked on LASAIR_TOKEN + network).
  * `synthetic_gaia_fields()`    stands in for `gaia.crossmatch`
                                 (live path is an anonymous astroquery.gaia TAP join).

Everything between staging and export is the *real* M1 code (`ellipsoid`, `ranking`,
`export`). The live ingest/crossmatch modules remain clean stubs whose NotImplementedError
names the Lasair-token requirement; `run_offline()` never touches them.

SQLite staging is a real, on-disk (or in-memory) table `alerts_staging`, matching the
dossier's "write normalized alert records to a SQLite staging table" design. Results are
deterministic: synthetic data is fixed, scoring uses a fixed reference epoch, and ordering
is stable.
"""

from __future__ import annotations

import hashlib
import math
import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from . import ellipsoid, ranking
from .models import Alert, RankedTarget

# --- staging schema -----------------------------------------------------------------

_STAGING_DDL = """
CREATE TABLE IF NOT EXISTS alerts_staging (
    source_ref   TEXT NOT NULL,
    survey       TEXT NOT NULL,
    ra_deg       REAL NOT NULL,
    dec_deg      REAL NOT NULL,
    mjd          REAL NOT NULL,
    mag_or_dm    REAL,
    -- Gaia DR3 enrichment (filled by the crossmatch leg; NULL until enriched):
    gaia_source_id        INTEGER,
    parallax_mas          REAL,
    parallax_over_error   REAL,
    ruwe                  REAL,
    neighbor_count        INTEGER,
    PRIMARY KEY (survey, source_ref)
)
"""


@dataclass(slots=True)
class GaiaFields:
    """Synthetic Gaia DR3 astrometry for one alert (offline stand-in for a TAP crossmatch)."""

    gaia_source_id: int
    parallax_mas: float
    parallax_over_error: float
    ruwe: float
    neighbor_count: int  # quality Gaia stars in the local field -> density bin


# --- synthetic feed + crossmatch (the only fake legs) -------------------------------

def synthetic_alerts() -> list[Alert]:
    """A fixed, deterministic batch of fake ZTF-style alerts near the SN 1987A field.

    Positions are spread in declination off SN 1987A so the resulting angular separations
    (and therefore crossing epochs) span a useful range. Stand-in for live Lasair ingest.
    """
    ra = ellipsoid.SN1987A_RA_DEG
    dec0 = ellipsoid.SN1987A_DEC_DEG
    # (objectId, dec offset deg == angular sep from SN, mjd, gmag). The dec offsets are the
    # angular separations used to size each star's distance (see synthetic_gaia_fields) so the
    # crossings land across the documented ~2024-2029.5 live window.
    specs = [
        ("ZTF26aaaaaaa", 6.0, 60800.1, 17.9),
        ("ZTF26aaaaaab", 9.0, 60801.2, 18.3),
        ("ZTF26aaaaaac", 12.0, 60802.3, 16.8),
        ("ZTF26aaaaaad", 4.0, 60803.4, 19.1),
        ("ZTF26aaaaaae", 16.0, 60804.5, 18.0),
        ("ZTF26aaaaaaf", 3.0, 60805.6, 15.9),
    ]
    return [
        Alert(
            source_ref=oid,
            survey="ZTF",
            ra_deg=ra,
            dec_deg=dec0 + ddec,
            mjd=mjd,
            mag_or_dm=gmag,
        )
        for (oid, ddec, mjd, gmag) in specs
    ]


def synthetic_gaia_fields(alert: Alert) -> GaiaFields | None:
    """Deterministic synthetic Gaia astrometry for one alert (offline crossmatch stand-in).

    The distance is chosen, per alert, so that the star's ellipsoid crossing lands in a
    plausible spread around the live window; one alert is deliberately given a failing RUWE
    to exercise the quality-cut path (returns enrichment that `ranking` will reject), and one
    returns ``None`` to model "no Gaia counterpart within the cone".

    Distances are encoded directly (then converted to parallax) so the offline fixture is
    self-consistent: distance_pc = 1000 / parallax_mas.
    """
    # source_ref -> (distance_pc, parallax_over_error, ruwe, neighbor_count) or None.
    # Distances are sized (closed-form inversion of crossing_epoch at each star's angular
    # separation) so the crossings land across the live ~2024-2029.5 window:
    #   aaaa @6deg ->~2026.5,  aaab @9 ->~2027.5,  aaac @12 ->~2028.0,
    #   aaad @4 ->~2025.5,     aaae @16 ->FAILS RUWE,  aaaf @3 ->~2024.0.
    table: dict[str, tuple[float, float, float, int] | None] = {
        "ZTF26aaaaaaa": (2112.4, 11.0, 1.05, 140),
        "ZTF26aaaaaab": (985.8, 25.0, 0.98, 480),
        "ZTF26aaaaaac": (567.0, 8.0, 1.22, 60),
        "ZTF26aaaaaad": (4413.6, 40.0, 1.31, 12),
        "ZTF26aaaaaae": (333.1, 6.0, 1.55, 30),   # RUWE 1.55 -> FAILS quality cut
        "ZTF26aaaaaaf": (7106.3, 30.0, 0.90, 8),
    }
    spec = table.get(alert.source_ref)
    if spec is None:
        return None
    distance_pc, p_over_e, ruwe, neigh = spec
    parallax_mas = 1000.0 / distance_pc
    # Deterministic, real-format Gaia DR3 id derived from the objectId (no network).
    # Use a STABLE hash (md5), not builtin hash(), so the id is reproducible across runs
    # regardless of PYTHONHASHSEED -- artifacts must be byte-for-byte deterministic.
    digest = int(hashlib.md5(alert.source_ref.encode("utf-8")).hexdigest(), 16)
    gaia_id = 4657700000000000000 + (digest % 1_000_000_000)
    return GaiaFields(
        gaia_source_id=gaia_id,
        parallax_mas=parallax_mas,
        parallax_over_error=p_over_e,
        ruwe=ruwe,
        neighbor_count=neigh,
    )


# --- SQLite staging -----------------------------------------------------------------

def open_staging(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open (creating if needed) the SQLite staging DB with the `alerts_staging` table."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(_STAGING_DDL)
    conn.commit()
    return conn


def stage_alerts(
    conn: sqlite3.Connection,
    alerts: Iterable[Alert],
    crossmatch=synthetic_gaia_fields,
) -> int:
    """Insert alerts (with their crossmatched Gaia fields) into `alerts_staging`.

    ``crossmatch`` maps an Alert -> GaiaFields | None; defaults to the offline synthetic
    stand-in. Alerts with no Gaia counterpart are still staged (Gaia columns NULL) so the
    staging table faithfully records the night's ingest. Returns the row count inserted.
    Idempotent on (survey, source_ref) via INSERT OR REPLACE.
    """
    n = 0
    for a in alerts:
        g = crossmatch(a)
        conn.execute(
            "INSERT OR REPLACE INTO alerts_staging "
            "(source_ref, survey, ra_deg, dec_deg, mjd, mag_or_dm, "
            " gaia_source_id, parallax_mas, parallax_over_error, ruwe, neighbor_count) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                a.source_ref, a.survey, a.ra_deg, a.dec_deg, a.mjd, a.mag_or_dm,
                None if g is None else g.gaia_source_id,
                None if g is None else g.parallax_mas,
                None if g is None else g.parallax_over_error,
                None if g is None else g.ruwe,
                None if g is None else g.neighbor_count,
            ),
        )
        n += 1
    conn.commit()
    return n


# --- ellipsoid + ranking over staged rows -------------------------------------------

def rank_staged(
    conn: sqlite3.Connection,
    now_jyear: float = ranking.DEFAULT_NOW_JYEAR,
) -> list[RankedTarget]:
    """Read enriched staged alerts, apply quality cuts, compute crossing + score, rank.

    This is the real M1 ellipsoid+ranking leg (no fakes): for every staged alert that has a
    Gaia counterpart passing the quality cuts, compute the crossing epoch, uncertainty
    window, density bin, and score; sort by descending score.
    """
    sn = ellipsoid.sn1987a_skycoord()
    out: list[RankedTarget] = []
    rows = conn.execute(
        "SELECT * FROM alerts_staging ORDER BY survey, source_ref"
    ).fetchall()
    for r in rows:
        if r["gaia_source_id"] is None or r["parallax_over_error"] is None:
            continue  # no Gaia counterpart -> cannot place on the ellipsoid
        p_over_e = float(r["parallax_over_error"])
        ruwe = float(r["ruwe"])
        if not ranking.passes_quality_cuts(p_over_e, ruwe):
            continue
        distance_pc = 1000.0 / float(r["parallax_mas"])
        sep_deg = ellipsoid.separation_from_sn_deg(
            _icrs(r["ra_deg"], r["dec_deg"], sn)
        )
        t_cross = float(ellipsoid.crossing_epoch(distance_pc, float(sep_deg)))
        window = float(
            ellipsoid.crossing_window_years(distance_pc, float(sep_deg), p_over_e)
        )
        dbin = ranking.density_bin(int(r["neighbor_count"]))
        sc = ranking.score(window, dbin, crossing_epoch_jyear=t_cross, now_jyear=now_jyear)
        out.append(
            RankedTarget(
                source_ref=r["source_ref"],
                gaia_source_id=int(r["gaia_source_id"]),
                ra_deg=float(r["ra_deg"]),
                dec_deg=float(r["dec_deg"]),
                distance_pc=distance_pc,
                parallax_over_error=p_over_e,
                ruwe=ruwe,
                crossing_epoch_jyear=t_cross,
                crossing_window_yr=window,
                density_bin=dbin,
                score=sc,
                survey=r["survey"],
                notes="offline synthetic pipeline",
            )
        )
    return ranking.rank(out)


def _icrs(ra_deg: float, dec_deg: float, _sn):
    """Tiny helper: build an ICRS SkyCoord (kept local to avoid re-importing astropy here)."""
    from astropy import units as u
    from astropy.coordinates import SkyCoord

    return SkyCoord(ra=float(ra_deg) * u.deg, dec=float(dec_deg) * u.deg, frame="icrs")


# --- top-level offline orchestrator -------------------------------------------------

@dataclass(slots=True)
class PipelineResult:
    n_staged: int
    n_ranked: int
    targets: list[RankedTarget]
    artifacts: dict[str, Path]


def run_offline(
    out_dir: str | Path,
    datestamp: str,
    db_path: str | Path = ":memory:",
    alerts: Sequence[Alert] | None = None,
    now_jyear: float = ranking.DEFAULT_NOW_JYEAR,
) -> PipelineResult:
    """Run the full offline pipeline end to end and write the artifact set.

    synthetic alerts -> SQLite staging -> ellipsoid -> ranking -> CSV/.tgt/.md.
    Returns a `PipelineResult` (counts, ranked targets, and the artifact paths).
    """
    from . import export  # local import keeps astropy off the hot import path until needed

    if alerts is None:
        alerts = synthetic_alerts()
    conn = open_staging(db_path)
    try:
        n_staged = stage_alerts(conn, alerts)
        targets = rank_staged(conn, now_jyear=now_jyear)
    finally:
        conn.close()
    artifacts = export.write_all(targets, Path(out_dir), datestamp)
    return PipelineResult(
        n_staged=n_staged,
        n_ranked=len(targets),
        targets=targets,
        artifacts=artifacts,
    )


# Re-export so callers can reason about the angle->time first-order relation in tests.
def _first_order_depth_ly(distance_pc: float, sep_deg: float) -> float:
    r_ly = distance_pc * ellipsoid._PC_TO_LY
    return r_ly * (1.0 - math.cos(math.radians(sep_deg)))
