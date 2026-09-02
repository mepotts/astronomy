"""Shared helpers for tns-miner M1.

Everything here is anonymous / tokenless. No credentials are read, stored or sent.
Windows traps handled: force UTF-8 stdout (cp1252 default kills degree signs),
and never write int64 into VOTable uploads (not used here).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests

# --- Windows trap: cp1252 stdout ---------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent


def _runtime_path(variable: str, default: Path) -> Path:
    """Resolve an optional run-local directory before any science I/O occurs."""
    configured = os.environ.get(variable)
    return Path(configured).expanduser().resolve() if configured else default.resolve()


# A proved live campaign uses isolated, gitignored directories so exact inputs
# cannot be overwritten by a later night and private candidate products cannot
# accidentally appear beneath the tracked historical ``out/`` tree.
DATA = _runtime_path("TNS_MINER_DATA_DIR", ROOT / "data")
OUT = _runtime_path("TNS_MINER_OUT_DIR", ROOT / "out")
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

UA = "tns-miner/0.1 (portfolio research; read-only; contact matthew.e.potts@gmail.com)"

# TNS measured rate limit: x-rate-limit-limit: 10 per rolling 60 s, on BOTH
# /api/get/* and /search?...&format=csv.  We stay at 8/60 s = 7.5 s spacing.
TNS_SPACING_S = 7.5
_last_tns_call = [0.0]


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


# Every TNS path this project is allowed to touch.  Anything else raises.
TNS_READ_ALLOWLIST = ("/search", "/object/", "/api/get/")


def tns_get(s: requests.Session, url: str, **kw) -> requests.Response:
    """Rate-limited GET against wis-tns.org.  Read-only by construction.

    HOUSE LAW: nothing in this repository ever submits anything to TNS -- not a
    discovery report, not a classification, not a bulk report, not a sandbox test.
    This guard is an allowlist rather than a blocklist so that a new write
    endpoint appearing in TNS's API cannot slip through by not being listed.
    """
    if "/api/set/" in url or "bulk-report" in url:
        raise RuntimeError("HOUSE LAW: this tool never touches a TNS write path.")
    if "wis-tns.org" in url and not any(p in url for p in TNS_READ_ALLOWLIST):
        raise RuntimeError(
            f"HOUSE LAW: {url!r} is not on the TNS read allowlist "
            f"{TNS_READ_ALLOWLIST}. Reads only, and only these paths."
        )
    wait = TNS_SPACING_S - (time.time() - _last_tns_call[0])
    if wait > 0:
        time.sleep(wait)
    r = s.get(url, timeout=120, **kw)
    _last_tns_call[0] = time.time()
    return r


def write_text(path: Path, text: str) -> None:
    """LF line endings, UTF-8, explicit -- Windows default newline translation
    silently rewrites committed scripts to CRLF."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
