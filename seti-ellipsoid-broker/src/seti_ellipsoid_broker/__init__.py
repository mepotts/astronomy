"""SETI Ellipsoid Alert Broker.

A standalone Python service that fuses transient alerts against the SN 1987A SETI
Ellipsoid using Gaia DR3 distances, ranks ellipsoid-crossing candidates, and exports
amateur-facing observing lists.

Status:
  * The offline core is COMPLETE and numerically correct: the SN 1987A ellipsoid math
    (`ellipsoid.py`) is real and externally validated against Nilipour et al. (2023)
    crossing epochs (see tests/test_nilipour.py); ranking and the deterministic CSV/.tgt/
    Markdown exporters are real.
  * A LIVE, ACCOUNT-FREE path exists: `seti-broker run --transients-csv PATH` crossmatches
    an externally-supplied alert list against anonymous Gaia DR3 TAP (no token) and applies
    the Gaia DR3 parallax zero-point correction (Lindegren et al. 2021) before inverting
    distance.
  * Still stubs: Lasair/ASAS-SN/CHIME auto-ingest (account/host-gated) and the Window
    Predictor (`predict`). See README.md / BUILD-PLAN.md.
"""

__version__ = "0.1.0"
