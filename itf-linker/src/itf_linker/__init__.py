"""itf-linker -- mine the MPC's Isolated Tracklet File for linkable minor-planet tracklets.

M0 scope (the kill-check): ingest the ITF, parse the MPC 1992 80-column format into a
typed columnar store, reconstruct tracklets, and replay three already-published
identification MPECs against the snapshot. No linking, fitting, or submission code lives
here yet -- and nothing in this package ever writes to an external service.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
