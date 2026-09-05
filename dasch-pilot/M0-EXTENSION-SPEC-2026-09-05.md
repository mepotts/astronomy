# DASCH M0 extension — prospective internal specification

Written 2026-09-05 before retrieving or inspecting the new control light curves
or plate images. This is a feasibility pilot, not an immutable preregistration.
The September 2 T CrB measurements were already known.

## Fixed controls and bounded requests

1. Retain T CrB and the September 2 reference-control inputs unchanged.
2. Add **R Cnc**, a Mira verified in SIMBAD and the STEREO long-period-variable
   paper. A draft copied RY Cnc from the old plan; primary-source checking found
   that it is an eclipsing variable. This correction was made before any new
   DASCH response was retrieved; no outcomes motivated the substitution.
3. Add **V404 Cyg**, a known faint recurrent transient in a Galactic-plane field.
   Its faint quiescence deliberately tests graceful insufficient-coverage behavior;
   it is not selected for a favorable DASCH result.

Resolve the two fixed names through CDS Sesame (SIMBAD resolution), record the
complete resolver responses, then query APASS within 30 arcsec. Select the nearest
catalog source only if it is within 5 arcsec and unique within 5 arcsec; otherwise
record AMBIGUOUS_OR_MISSING and stop that control. Do not replace a failed target.
Query one 300-arcsec field per added control to measure catalog crowding. Fetch
at most one light curve per control and one T CrB exposure list. No unknown-source
light curves will be ranked or fetched.

## Light-curve checks

Use exactly the September 2 finite-detection, five-AFLAG, and <=15 arcsec
astrometric cuts. Report meteor-series counts separately; no new cut will be
tuned to improve recovery. Detection accounting must equal querycat num_matches.
The multi-position access gate requires >=20 clean detections and >=10 years
of clean coverage for each of T CrB, R Cnc, and V404 Cyg. Failure for the faint
control is a failure of the original unconditional three-position gate, not a
reason to return QUIESCENT. A Mira plausibility diagnostic requires a clean
90th-minus-10th percentile range >=1 magnitude; this is not a period search.

## Fixed image selection and interpretation

From the frozen T CrB light curve, select the clean detection closest in time
to each fixed epoch: 1937.0 (before high state), 1942.0 (within high state), and
1947.0 (after the 1946 nova). Each must lie within one year of its target.
Break ties by plate series/number and solution number. Join to queryexps by
plate and solution identity; require a valid solution before requesting the
official cutout. At most three primary cutouts; no fallback chosen for image
appearance. API requests may be retried once for transient HTTP failures.

Cutout acceptance requires a valid FITS image, finite center pixels, compatible
WCS at the requested position, and visual inspection of the target and neighbors
across all three epochs. Display both the full cutout and a fixed central crop;
report mismatches, blends, defects, and differences in plate resolution. These
images are photographic densities, not calibrated flux; display stretches cannot
measure a magnitude change.

T CrB remains a visible star outside its high state. Thus these images can close
API/cross-epoch retrieval feasibility, **not** the older plate-archaeology demand
for a transient visible during an event and absent on adjacent plates. That
original transient-search gate remains open unless a separate known transient
experiment is specified prospectively; do not silently redefine it as passed.

**Separate on/off attempt, fixed before retrieval:** V404 Cyg had a published
1938 photographic outburst (Wachmann 1948; plotted in Casares et al. 1991 and
Muñoz-Darias et al. 2019). The published curve covers approximately JD
2429190--2429250. Query its exposure list even if the APASS identity test fails.
Among valid scanned/WCS-solved exposures, take the nearest to JD 2429200 within
30 days for the event, the latest before JD 2429100 within 365 days for the
pre-event image, and the earliest after JD 2429400 within 365 days for the
post-event image. Break ties by series/plate/solution. At most these three
additional cutouts; missing exposure coverage is a BLOCK, never substitute an
image after seeing its pixels. Inspect positions and morphology; report whether
the event source is distinguishable and the adjacent images sufficiently deep.
A visually absent source on a shallow image does not establish a non-detection.

## Decision

- All access/image checks pass: only advance to a specified stable-star
  false-positive/coverage study, with calibration and untouched validation fields.
- A faint-control failure with useful bright controls: stop the unconditional
  broker-scale verdict concept; optionally propose a brightness/coverage-limited
  study. It is not permission for a blind anomaly hunt.
- Cutouts fail: record the reproducible blocker and park image discovery.

Known-control identifiers may be retained. No unknown candidates, publication,
account creation, emails, or registry writes are part of this work. Record bytes,
SHA-256, UTC retrieval times, exact requests, and this specification's hash for
every run; reject mutated cached inputs.

## Primary references checked before execution

- [Official DR7 API reference](https://dasch.cfa.harvard.edu/dr7/web-apis/)
- [DR7 reduction guide](https://dasch.cfa.harvard.edu/dr7/reduce-lightcurve/)
- [CDS Sesame name resolver](https://cds.unistra.fr/cgi-bin/Sesame)
- [R Cnc SIMBAD record](https://simbad.u-strasbg.fr/simbad/sim-id?Ident=R+Cnc)
- [STEREO observations of long period variables](https://academic.oup.com/mnras/article/426/2/816/976379)
- [V404 Cyg 1938 photographic curve](https://academic.oup.com/mnras/article/488/1/1356/5526250)
- [V404 Cyg observed quiescent B/V magnitudes](https://academic.oup.com/mnras/article/481/2/2646/5090411)
