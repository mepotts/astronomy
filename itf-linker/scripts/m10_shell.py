"""M10: sweep the 15-25 year main-belt shell — the window M9's calibration opened.

M8 bounded attribution at 15 years because that is where its calibration stopped
(``MAX_LOOKBACK_DAYS``, "measured, not preferred"). M9 section 8 extended the Horizons
calibration to 28 years and found the perturbed main-belt envelope holds **<= 150"
through 25 years** before breaking at 28 (303.8"). That measurement makes a new shell
available, and this script sweeps it — **only** the shell, 15 y < |dt| <= 25 y, because
the 0-15 y interior is already in the ledger and re-sweeping it would re-propose rows
Matthew is about to review.

Everything else is M8's machinery unchanged, deliberately: the same perturbed backend,
the same gate formula, the same half-period decoy, the same checkpointed fit queue,
the same in-loop stopping rule. The only substitutions are the ones the new window
forces, and each is a *measured* quantity rather than a chosen one:

* ``MIN_LOOKBACK_DAYS`` / ``MAX_LOOKBACK_DAYS`` -> the shell.
* ``CALIBRATION`` -> ``m9-calibration.json``, key
  ``perturbed_envelope_arcsec_mainbelt_25y``. The main-belt and TNO envelopes are kept
  strictly apart (M9 section 8): 28 y is a TNO number and applying it here would be
  inventing a bound, not measuring one.
* the orbit table -> the union of M8's and M9's, at the frozen U <= 6 cut.
* fit tags -> ``m10a``/``m10b``... **no**: seven characters is the trkSub field width,
  so ``mAa####``/``mAb####`` (HANDOFF section 2, the ``_relabel`` truncation trap).

Writes ``m10-shell.json`` (root, gitignored), checkpoints to
``data/m10-shell-fit-state.jsonl``, fits under ``data/m10-shell-fits/``. The M8 and M9
reports, ledgers and fit state are untouched.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import m8_attribution as m8a
import polars as pl

ORBITS_UNION = ROOT / "data" / "raw" / "rubin" / "m10-orbits.parquet"
RECONSTRUCTED = (
    ROOT / "data" / "parquet" / "itf_observations_20260816_reconstructed.parquet"
)

SHELL_MIN_YEARS = 15.0
SHELL_MAX_YEARS = 25.0


def build_union_orbits() -> dict[str, int]:
    """M8's and M9's swept orbit tables, unioned on the common schema."""
    a = pl.read_parquet(ROOT / "data" / "raw" / "rubin" / "m8-orbits.parquet")
    b = pl.read_parquet(ROOT / "data" / "raw" / "rubin" / "m9-orbits.parquet")
    cols = [c for c in a.columns if c in b.columns]
    union = pl.concat([a.select(cols), b.select(cols)], how="vertical")
    before = union.height
    union = union.unique(subset=["primary"], keep="first")
    union.write_parquet(ORBITS_UNION)
    return {
        "m8_orbits": a.height,
        "m9_orbits": b.height,
        "union_rows": union.height,
        "duplicates_dropped": before - union.height,
        "u_le_6": int((union["u_param"] <= 6).sum()),
    }


def main() -> None:
    stats = build_union_orbits()
    print(f"orbit union: {json.dumps(stats)}", flush=True)

    # ---- the substitutions, all measured ------------------------------------------
    m8a.ORBITS_PARQUET = ORBITS_UNION
    m8a.CALIBRATION = ROOT / "data" / "raw" / "rubin" / "m9-calibration.json"
    m8a.CALIBRATION_KEY = "perturbed_envelope_arcsec_mainbelt_25y"
    m8a.MIN_LOOKBACK_DAYS = SHELL_MIN_YEARS * 365.25
    m8a.MAX_LOOKBACK_DAYS = SHELL_MAX_YEARS * 365.25
    m8a.OUT = ROOT / "m10-shell.json"
    m8a.FIT_STATE = ROOT / "data" / "m10-shell-fit-state.jsonl"
    m8a.FIT_ROOT = ROOT / "data" / "m10-shell-fits"
    m8a.TAG_FIT = "mAa"
    m8a.TAG_BASE = "mAb"

    env = m8a.envelope_fn()
    import numpy as np

    probe = np.array([SHELL_MIN_YEARS, 20.0, SHELL_MAX_YEARS]) * 365.25
    for u in (0, 2, 5, 6):
        radii = m8a.gate_radius_arcsec(probe, np.full(probe.size, u), env)
        print(f"  derived gate, U={u}: "
              + ", ".join(f"{y:.0f}y={r:.0f}\"" for y, r in
                          zip(probe / 365.25, radii)), flush=True)

    t0 = time.monotonic()
    m8a.main()
    print(f"shell sweep+fits complete in {time.monotonic() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
