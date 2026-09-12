# TESS incremental-data lead: Sector 106

Metadata/documentation check only, September 12. No unknown light curves were
downloaded, searched or selected from their fluxes for this note.

The [MAST bulk-product index](https://archive.stsci.edu/tess/bulk_downloads/bulk_downloads_ffi-tp-lc-dv.html)
lists `tesscurl_sector_106_lc.sh` under Lightcurve, plus Sector 106 pixel and
validation products. It lists Sector 107 calibrated full-frame images, which is
not the same as availability of its 120-second light curves. No downloaded shell
script was executed. A listing is not a per-product availability/header audit.

[NASA's Sector 106 page](https://heasarc.gsfc.nasa.gov/docs/tess/sector106_summary.html)
dates the observations July 11--August 9, 2026. Those observations postdate
[the June control paper](https://arxiv.org/abs/2606.03850). **Inference:** the July
photons could not be part of that June version's search. This establishes an
incremental observing interval, not an unsearched population or object novelty.
The same stars may already have older detections and later papers may overlap.

The [data-release-note index](https://archive.stsci.edu/tess/tess_drn.html) exposed
notes only through Sector 104 in this check, despite the later bulk listings.
Do not infer quality documentation for Sector 106 from an unrelated release number
or waive its processing/quality assessment. Sector number and release-note number
are different identifiers.

## Bounded next coverage test, conditional on method validation

1. Obtain the published Sector 106 LC manifest as data, never execute its commands.
   Parse only documented filenames/MAST URIs, preserve bytes and hash, account for
   duplicates, and verify a bounded metadata sample's PUBLIC rights, sector,
   cadence, product type and observation dates.
2. Cross-match that public target universe with an explicitly sourced WD catalogue
   using exact identifiers and a declared population rule. Do not transfer the
   June paper's approximate sample size into an assertion about this sector.
3. Freeze a small deterministic sample and input/resource caps before any unknown
   flux inspection. Establish instrument localization and empirical negative
   controls first; quantify selection/coverage losses and trial count.
4. For survivors, check earlier sectors and existing literature/catalogues before
   describing anything as new. Independent angular-resolution evidence is still
   required where TESS cannot distinguish competing sources.

This is a specific next data opportunity, not an unknown-scan authorization or a
promise of discovery. It does not amend the frozen M0b/M1 scientific protocols.
