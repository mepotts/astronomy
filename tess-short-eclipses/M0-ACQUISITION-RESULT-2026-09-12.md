# M0 acquisition: STOP_NO_LC

The fixed metadata-first acquisition was run September 12. Two selected controls
(TIC 450781262, sector 99; TIC 2041210548, sector 57) downloaded and passed FITS
identity/time/cadence checks. **No flux was searched or plotted.**

TIC 53206761 failed before download: the greatest obsid in its newest public
120-second sector is 208734076, observation
`tess2018235142541-s0002-s0072-0000000053206761`. Its product list contains data
validation products (DVT/DVR/DVM/DVS), not a SCIENCE LC. The original fixed selector
incorrectly treated multi-sector validation records as interchangeable with
single-sector light-curve records. This is **not no TESS coverage or no eclipses**.

Full observation and product metadata are retained under ignored `data/53206761/`;
the attempted-run receipt is `data/fetch-run.json`. The same observation table
contains actual single-sector sector-72 120-second record 198789561:
`tess2023315124025-s0072-0000000053206761-0267-s`.

Original M0 acquisition is stopped; its criteria are not silently edited. A
separate M0b selector may exclude multi-sector validation observations before
choosing the newest single-sector SPOC record. All three targets, sectors, search
rules and thresholds remain fixed. This correction is made before reading fluxes,
not to make a measured eclipse pass. The two already acquired valid products may
be reused only after exact identity/hash and amended-selection agreement checks.

Fifteen offline tests pass (13 independently written). They do not turn this
failed acquisition into successful scientific control recovery.
