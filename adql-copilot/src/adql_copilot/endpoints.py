"""Verified public VO TAP endpoints (June 2026). All anonymous — no auth required.

See DATA-SOURCES.md for per-endpoint quirks (row caps, schema naming, result retention).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    key: str
    name: str
    tap_url: str
    note: str


ENDPOINTS: dict[str, Endpoint] = {
    "gaia": Endpoint(
        key="gaia",
        name="Gaia (ESA)",
        tap_url="https://gea.esac.esa.int/tap-server/tap",
        note="DR3/DR4. Sync capped at 2000 rows; anonymous async results kept 3 days.",
    ),
    "vizier": Endpoint(
        key="vizier",
        name="VizieR (CDS)",
        tap_url="https://tapvizier.cds.unistra.fr/TAPVizieR/tap",
        note="Tens of thousands of slash-coded catalog tables; UCD-rich. Hardest target.",
    ),
    "mast": Endpoint(
        key="mast",
        name="MAST CAOM (STScI)",
        tap_url="https://mast.stsci.edu/vo-tap/api/v0.1/caom",
        note="HST/JWST/TESS observations; ObsCore-style columns (s_ra, s_dec, s_region).",
    ),
    "desi": Endpoint(
        key="desi",
        name="DESI (via NOIRLab Astro Data Lab)",
        tap_url="https://datalab.noirlab.edu/tap",
        note="Select schema desi_dr1 (or desi_edr). No first-party DESI TAP; this is canonical.",
    ),
}

# Sandbox used in the PyVO docs — handy for development.
SANDBOX_TAP_URL = "http://dc.g-vo.org/tap"

DEFAULT_ENDPOINT = "gaia"  # M1 first target (see BUILD-PLAN Open Questions #1)
