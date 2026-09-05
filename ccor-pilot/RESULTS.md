# CCOR2 M0 result — 2026-09-05

## Outcome

**STOP_METADATA_QUALITY.** Access works; recovery feasibility remains untested.
The pilot did not find a new object, recover a confirmed comet, or show that
the previously reported object is absent. No real image pixels were
decompressed or scored. The planned real-data injection and negative controls
were not run because the premeasurement gate failed. No cutout fixture was
created under an unverified coordinate transform.

The freeze was recorded at **2026-09-05T14:13:13.1603228Z**, before the first
FITS download. The unchanged specification SHA-256 is
`71c8aeab33090c0cb76c4ee64e9c248d9435c749eeb92e2b1b0aaff3d9d792f8`.
The four downloads completed by 14:13:14.6819253Z. Their exact hashes, sizes,
URLs, timestamps and extension headers are in
[header-evidence.json](results/header-evidence.json). Total raw FITS size is
36,581,760 bytes (34.89 MiB), below the frozen four-frame/48 MB cap.

## What stopped it

| Independent issue | Evidence | Consequence |
| --- | --- | --- |
| Missing required quality metadata | ISVIABLE absent from both HDUs in all four files; remaining frozen metadata checks pass | First frozen gate stops; do not equate missing with true or declare the data physically bad |
| Non-flip-only WCS | Default HPLN/HPLT cross-axis ratios 0.02045–0.02052 (rotation 1.172–1.175 degrees) | Exceeds the frozen 0.01 tolerance; a future transform needs independently justified rotation/resampling or report-native coordinates |
| Report display provenance unresolved | NRL supplies upper-left origin and 2048x1920 size, but not viewer/calibration/rotation provenance | A FITS WCS cannot establish the reporter's transform; no parity/rotation search for a brighter source |
| Control is not confirmed truth | NRL status is Potential Comet, with endorsements | Even conditional recovery could not estimate comet precision or count as discovery |

The [official provisional ReadMe](https://archive.data.noaa.gov/satellite-spaceweather/SWFO/docs/CCOR/SWFO_CCOR-2_Provisional_ReadMe_V1.0.pdf)
Table 7 documents ISVIABLE. Sections 4–5 warn of loose-lens shifts,
interpolation and detector artifacts; the operational data do not include
the retrospective pixel-quality extension. The actual files identify GPA
10.3.0 and STATUS Operational. Missing metadata may reflect a documentation/
pipeline-version mismatch: this test does not diagnose which. Astropy also
warned that BLANK is invalid for the floating-point image header and ignored
it; no pixel-level conclusion was drawn from that warning.

The first outcome is preserved in [result.json](results/result.json).
[header-audit.json](results/header-audit.json) is a subsequent **header-only**
audit of the primary HDUs and the independent WCS issue, not a second recovery
attempt. The [source evidence](results/source-evidence.json) records the
bounded public inputs and the ReadMe hash. The empty `fits.json` index remains
an input failure, not a valid no-data result; only the frozen directory-resolved
four filenames were fetched.

## Checks and meaning

Before the real-header run: 11 tests passed and the then-unavailable recorded
evidence test was skipped. After collection, all 12 tests passed, including
offline replay; two audit/source-provenance regressions were then added,
bringing the final suite to 14 passing tests. The seeded
synthetic point source passes the fixed engineering recovery gate, a no-source
synthetic field does not, and the fixed injection passes. These demonstrate
software plumbing only. The contrast statistic is not calibrated Gaussian
significance, and eight shifted tracks cannot establish a survey error rate.

The [NRL source report](https://sungrazer.nrl.navy.mil/report/reportmk20260901100943)
is already public and credited to its reporter; this repository makes no
discovery-credit claim. A bounded check of current NRL confirmations did not
establish a confirmed source for these four timestamps. It was not an
exhaustive search of all known comets or all public data.

## Exact restart requirements

1. Resolve the operational ISVIABLE schema/version discrepancy using primary
   documentation or obtain suitable retrospective data with the required
   documented quality information. Do not silently weaken this frozen gate.
2. Establish the report-native image transform, including rotation,
   reflection, origin and processing level, or choose a positively identified
   control with a reproducible ephemeris-to-image mapping. Specify the WCS
   transform and interpolation before seeing recovery scores.
3. Freeze a **new**, bounded known/reported-control pilot with the appropriate
   quality/geometry criteria, artifact checks, and real-data controls. This
   stopped attempt must remain in the record. A confirmed comet control is
   required before calling it comet-recovery validation.

No broader search or scheduled detector should start from this result alone.
