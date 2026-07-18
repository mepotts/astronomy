"""Feed ingest agents. Each module normalizes one external feed to `models.Alert`.

M0: all stubs raising NotImplementedError. See DATA-SOURCES.md for the real endpoints.
  lasair.py  -> ZTF alerts via Lasair REST   (M1)
  asassn.py  -> ASAS-SN Sky Patrol V2         (M2)
  chime.py   -> CHIME/FRB VOEvent stream      (M2/M3)
"""
