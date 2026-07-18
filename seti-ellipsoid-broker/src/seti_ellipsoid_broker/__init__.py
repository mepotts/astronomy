"""SETI Ellipsoid Alert Broker.

A standalone Python service that fuses ZTF (Lasair), ASAS-SN, and CHIME/FRB alerts
against the SN 1987A SETI Ellipsoid using Gaia DR3 distances, and proactively predicts
upcoming ellipsoid shell crossings (Window Predictor mode).

M0 status: package skeleton. CLI runs and prints MOCKED rows; the real ingest,
crossmatch, and ellipsoid math are stubbed. See BUILD-PLAN.md for milestones.
"""

__version__ = "0.0.1"
