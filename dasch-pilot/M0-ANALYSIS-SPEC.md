# M0 Analysis Specification

Date: 2026-09-02

Purpose: decide whether the current public DASCH DR7 API and documented
quality information support a reproducible, non-interactive targeted workflow.
This is a known-control feasibility test, not a discovery analysis.

## Frozen inputs

- Positive control: T CrB at the coordinates recorded in
  `data/provenance.json`.
- Target match: the sole APASS source returned within 30 arcsec.
- Field control: among the APASS `class=0`, `v_flag=0` entries in the frozen
  600-arcsec field query, choose the source with the largest `num_matches`;
  break ties lexicographically by `ref_text`.
- Baseline window: 1924-01-01 through 1937-12-31 (`[1924, 1938)`).
- Published high-state window: 1938-01-01 through 1945-12-31
  (`[1938, 1946)`).
- Preferred magnitude: `magcal_magdep`, as specified by daschlab.

The positive-control threshold and windows were fixed before the first target
analysis. The field-control rule and its thresholds were fixed after inspecting
only field-catalog metadata and before the field-control light curve was first
analyzed. This chronology is recorded because the work is a pilot rather than
a formal preregistered experiment.

## Quality flow

1. Retain detections with finite `magcal_magdep`.
2. Apply the exact five-AFLAG mask in the current daschlab
   `apply_standard_rejections()` implementation: `HIGH_BACKGROUND` (64),
   `LARGE_ISO_RMS` (2048), `LARGE_LOCAL_SMOOTH_RMS` (4096),
   `CLOSE_TO_LIMITING` (8192), and `BIN_DRAD_UNKNOWN` (32768).
3. Require the detection-to-corrected-catalog separation to be at most
   15 arcsec. This is within the 10--20 arcsec range recommended by the DR7
   reduction guide, but it is an additional pilot choice rather than part of
   daschlab's current standard rejection method.
4. Compute the median magnitude and median absolute deviation separately in
   the two frozen windows.

No plate-image morphology rejection is automated. That remains mandatory
manual work for any prospective unknown candidate.

## Acceptance gates

- Positive control: at least 20 retained measurements in each window and a
  median brightening of at least 0.5 mag.
- Field control: at least 10 retained measurements in each window and an
  absolute median shift no larger than 0.3 mag.
- Differential: target brightening minus field-control shift at least 0.7 mag.
- All three gates must pass for `TARGETED_DASCH_FEASIBILITY_PASS`.

Regardless of outcome, the discovery scan is `NOT_RUN` and no candidate
identifier is emitted.
