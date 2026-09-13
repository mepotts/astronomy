# PPS attitude: additional format facts before product inspection

September 12, 2026. Read the existing
[attitude-semantics note](XMM-ATTITUDE-SEMANTICS-2026-09-12.md) first. This narrow
follow-up adds export-schema details, not a repeat of the motion argument.
No product requests, arrays, coordinate queries or calibration execution.

## New directly documented details

The `atthkgen` output specification describes one binary table named **ATTHK**.
Its ten columns are TIME; AHFRA/AHFDEC/AHFPA; OMRA/OMDEC/OMPA; and
DAHFPNT/DOMPNT/DAHFOM. All are real64. TIME is seconds; **all nine attitude and
offset columns are degrees**, including the three offset magnitudes.

Quality is represented by NULL/INDEF in the attitude triplets and affected
offsets. No separate QUALITY column is specified by this output description.
DAHFPNT and DOMPNT are differences from their respective median pointing;
DAHFOM compares the two attitude sources. Primary A-prefixed and M-prefixed
summary keys are means and medians, respectively. The page also lists NATT,
NGAHF, NGOM and NGAHFOM, without defining their counting rules here.
[Official atthkgen output specification](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/node7.html).

## Consequences for the pending PPS ATTTSR

`P0884250101OBX000ATTTSR0000.FTZ` is the observation-level product already
identified in the retained inventory. A filename identifying an attitude
timeseries is **not** proof that its table is the unmodified `atthkgen` export.
The pending headers must establish creator/version, extension, complete schema,
units, time reference and any additional quality fields. A different legitimate
PPS schema requires explicit interpretation, not blind renaming to ATTHK.

In particular, do not require an invented QUALITY field or interpret a zero
offset as bad. Conversely, do not discard a partially null triplet while
declaring the row fully good: retain per-source/per-component validity and the
actual null representation. Offset units need checking before an arcsecond
comparison; raw degree offsets are not arcseconds. Inspect count-key comments
before using their names as a row-accounting assertion.

The earlier note's sampling warning is unchanged: full-observation coverage in
a file description does not promise complete raw measurements or valid samples
at every time. AHF and OM may have different null/gap patterns. Neither median
offsets nor maximum sampled offsets bound motion between samples. A proposed
interpolation is a model; absent a justified between-sample error/rate bound,
report sampled-motion diagnostics and coverage gaps, not guaranteed continuous
aperture stability. No such bound was found in this format specification.

## Documentation boundary

Three primary-document URL opens were attempted: an initial `atthkgen/node8`
lookup and the official PPS-format ICD PDF returned tool retrieval errors;
the correct `atthkgen/node7` output page above succeeded. No PDF or product bytes
were downloaded through another route. Therefore a separate PPS-format
definition was **not successfully verified** in this follow-up. The new schema
facts apply to the documented SAS export until the actual retained product's
headers establish compatibility. No scientific readiness or discovery follows.
