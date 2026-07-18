"""Feed ingest agents. Each module normalizes one external feed to `models.Alert`.

  transients.py -> account-free CSV alert list (any broker / your own)   REAL (live path)
  lasair.py     -> ZTF alerts via Lasair REST   account-gated stub (see DATA-SOURCES.md S0)
  asassn.py     -> ASAS-SN Sky Patrol V2         stub (M2)
  chime.py      -> CHIME/FRB VOEvent stream       stub (M2/M3)

See DATA-SOURCES.md for the real endpoints and the account-free path.
"""
