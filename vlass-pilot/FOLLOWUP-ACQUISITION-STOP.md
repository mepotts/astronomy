# Follow-up transport stop

The separately specified QL2.1/3.1/4.1 acquisition ended at
2026-09-12T20:09:28.880983Z with **STOP_ACQUISITION**. The final QL4.1 RMS
SODA request exceeded its configured 75-second subprocess deadline. The launcher
was terminated by Python's subprocess wrapper; whole-process-tree termination
was **not established at that time** (see TRANSPORT-AUDIT.md). The missing file
was not created, no partial image was substituted and the timeout was not increased.

Retained and hash-bound inputs: QL2.1 science/RMS, QL3.1 science/RMS, QL4.1
science. Follow-up metadata plus FITS total **41,839,728 bytes**; initial metadata
adds 9,295 bytes. There is no complete fourth-epoch pair, no measured target
flux, and no empirical recovery verdict. Header-only inspection of QL2.1 showed
Jy/beam units, a 3.085 x 2.279 arcsec beam, and the expected observing date.

`acquisition-followup.json` preserves this stopped attempt. A parent-authorized
single retry of precisely the failed idempotent request, with unchanged timeout,
cutout, byte cap and scientific criteria, would be a transport recovery, not a
new scientific hypothesis. It must have a separate receipt/manifest and preserve
this record. No automatic retry loop is permitted.
