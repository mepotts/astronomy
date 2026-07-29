from __future__ import annotations

from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_lines() -> list[str]:
    """Eleven real lines lifted verbatim from the ITF snapshot of 2026-07-29.

    Deliberately includes the awkward cases: a space-based S/s pair from C51, a
    discovery-asterisk record, records at two different RA/Dec precisions, and the one
    genuinely malformed record in the whole file (947, Dec seconds ``39 8``).
    """
    text = (DATA / "itf_sample.txt").read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip()]


@pytest.fixture(scope="session")
def itf_snapshot():
    """The full parsed snapshot, or skip. Gates the ``slow`` tests."""
    pl = pytest.importorskip("polars")
    from itf_linker import config

    if not config.ITF_PARQUET.exists():
        pytest.skip("no parsed ITF snapshot; run `itf-linker fetch && itf-linker parse`")
    return pl.read_parquet(config.ITF_PARQUET)


@pytest.fixture(scope="session")
def mpec_dir() -> Path:
    """Cached MPEC HTML, or skip."""
    from itf_linker import config

    if not (config.MPEC_DIR / "K26O57.html").exists():
        pytest.skip("no cached MPECs; run `itf-linker killcheck`")
    return config.MPEC_DIR
