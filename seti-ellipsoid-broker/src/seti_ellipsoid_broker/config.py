"""Runtime configuration (tokens, endpoints, output paths).

M0: importable, with sane defaults; reads env vars if present. No secrets committed.
The real pipeline upgrades this to `pydantic_settings.BaseSettings`; for the skeleton a
plain dataclass keeps imports light and avoids requiring pydantic just to run `--help`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    # Lasair ZTF REST API (see DATA-SOURCES.md S1). Token read from env; never hardcode.
    lasair_token: str | None = None
    lasair_endpoint: str = "https://lasair-ztf.lsst.ac.uk/api"

    # Gaia DR3 TAP table (astroquery.gaia default).
    gaia_table: str = "gaiadr3.gaia_source"

    # Where nightly artifacts land.
    output_dir: Path = Path("output")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            lasair_token=os.environ.get("LASAIR_TOKEN"),
            lasair_endpoint=os.environ.get(
                "LASAIR_ENDPOINT", "https://lasair-ztf.lsst.ac.uk/api"
            ),
            output_dir=Path(os.environ.get("SETI_OUTPUT_DIR", "output")),
        )
