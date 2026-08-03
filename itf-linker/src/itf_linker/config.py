"""Paths and external endpoints. No credentials: every source here is public and anonymous."""

from __future__ import annotations

from pathlib import Path

# Project root = .../itf-linker (this file is src/itf_linker/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"          # gitignored: the ~135 MB ITF snapshot
PARQUET_DIR = DATA_DIR / "parquet"  # gitignored: typed derivatives
MPEC_DIR = DATA_DIR / "mpec"        # gitignored: cached MPEC HTML

ITF_GZ = RAW_DIR / "itf.txt.gz"
ITF_PROVENANCE = RAW_DIR / "itf.provenance.json"
ITF_PARQUET = PARQUET_DIR / "itf_observations.parquet"
TRACKLET_PARQUET = PARQUET_DIR / "itf_tracklets.parquet"

# M2 vetting. The cache is what makes a vetting run reproducible without asking MPChecker,
# SkyBoT and JPL to recompute answers they have already given.
VET_CACHE_DIR = DATA_DIR / "vet-cache"
VET_ASTROMETRY = DATA_DIR / "vet-astrometry.json"

# M3 linking. A proposed link's astrometry cannot be re-extracted by designation the way
# M1's could: the link's identifier does not exist in the ITF, so the assembled and
# relabelled 80-column lines are written once and reused by the vetting stage.
VET_ASTROMETRY_LINKS = DATA_DIR / "vet-astrometry-links.json"

# --- Endpoints (read-only; no writes are ever performed against these) -------------
ITF_URL = "https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz"
OBSCODES_URL = "https://www.minorplanetcenter.net/iau/lists/ObsCodes.html"
MPEC_URL_TEMPLATE = "https://www.minorplanetcenter.net/mpec/K{yy}/{packed}.html"

USER_AGENT = "itf-linker/0.1 (+https://github.com/; matthew.e.potts@gmail.com) read-only"

#: The three July-2026 identification MPECs the M0 kill-check replays.
KILL_CHECK_MPECS = ("K26O40", "K26O57", "K26O86")


def ensure_dirs() -> None:
    for d in (RAW_DIR, PARQUET_DIR, MPEC_DIR):
        d.mkdir(parents=True, exist_ok=True)
