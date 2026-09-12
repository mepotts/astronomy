# M2p independent orchestration review

2026-09-12. **GO for driver/protocol/test freeze and the single parent-approved
bounded experiment, once the separately assigned numerical-core review is also
accepted.** No open material driver finding remains. This is software/design
readiness, not evidence that any real localization or injection will succeed.

## Review scope and scientific contract

The reviewer read the complete M2p driver, protocol, author tests and numerical
core interface/design, following the M2a, M2n, coordinate-audit and localization
proposal reviews. No real calibration interpolation, fit, injection, preparation
or science execution occurred. Only this document and the new independent test
file were edited. Retained pixels, calibration files and prior frozen stages
were not modified. Numerical-core acceptance is a separate review, not inferred
from mocked orchestration success.

The driver preserves three mandatory known controls, fixed ephemerides/apertures,
primary/M2n prerequisite replay and catalog-independent fitting. Geometry selects
target, nearest other source and finite-G brightest other source within one pixel;
IDs are deduplicated without replacement. Primary fixed-position profiles include
all stamp catalog rows. Geometric nearest-to-free-centroid labels remain distinct
from these profile scores; neither is a probabilistic source association.

Injection subtracts the corner-specific model only from eligible +0.25 in-event
FLUX before the paired estimator, retaining errors and the original day anchor.
Scaling uses that corner's fixed-SAP model response, not crop-to-unity or physical
fractional depth. Twenty seeded day-index draws are reused across every condition
within a field. Signed-mean bias, radial error, wrong-any-row confusion and nominal
ellipse coverage have distinct meanings. All failures and undefined ellipses
remain in the fixed twenty-slot denominator; observed-amplitude gates are not
replaced by favorable lower/higher-amplitude results.

The nominal covariance ellipse is an explicitly diagonal-error, local-linear
stress diagnostic with nuisance coupling, not a calibrated uncertainty region for
correlated pixels/days or PRF/WCS/model errors. Corner shapes are sensitivity
extremes, not an observational distribution of contemporary calibration error.

## Findings resolved before outcome inspection

1. Actual core bound fits carry both success=false and bound_hit=true. The driver
   originally classified these FAILED before checking the bound. It now preserves
   the separate BOUND category, matching the real interface.
2. A condition-wide exception initially erased completed trial records. Individual
   numerical exceptions now retain a STOP_TRIAL slot and subsequent distinct draws
   proceed without retrying the failed draw. Setup failures retain twenty explicit
   unmeasured FAILED slots. Recorded, attempted and completed counts are separate;
   unmeasured placeholders are not described as completed fits.
3. Exhausting the stage-output allowance could also prevent the parent failure
   summary from being saved. Ordinary output now stops at 99 MB, reserving 1 MB
   within the original 100-MB envelope for the bounded terminal summary. Limits
   count the actual indented JSON serialization, including its newline.
4. Receipt review strengthened ordered replay, complete condition checkpoint and
   summary reconstruction, raw worker return-code preservation when parent
   completion fails, bounded UTF-8 output receipts and their self-consistency.
   Raw text hashes/lengths remain available when output is truncated. Successful
   flat/nested worker-output receipts must agree; nontruncated bytes/hashes are
   recomputed. A truncated full-output hash cannot be reconstructed from its
   retained prefix alone and is not claimed to have been so verified.

## Independent synthetic evidence

**29 driver tests pass: 15 author and 14 independent.** Pinned Ruff 0.16.5 passes
for driver and both test files. The independent test file is stable and already
included in the dependency collector.

The full mock-only orchestration exercise covers all three control identifiers
with a synthetic three-row catalog, 36 conditions/720 trials per field and 2,160
total trial slots. It verifies corner ordering, every primary catalog profile,
all twelve negative channel fits per field, unchanged errors, exclusion/anchor
handling, subtraction before the estimator and exact corner-specific SAP scaling.
All twenty paired resampling patterns agree across conditions. These are fixture
counts, not the actual deduplicated scientific sample or actual fit outcomes.

Failure regressions verify preserved successful trials before an exception,
19 completed versus 20 attempted/recorded trials in that fixture, and zero
attempted/completed versus 20 recorded slots for setup failures. They also verify
partial checkpoint retention, no second worker run, read-only replay, exact
600-second launch bounds, required checkpoint closure, and rejection of a wrong
trial summary even when checkpoint and result agree with one another.

Receipt tests include an explicitly valid three-worker replay path, ordered
failure rejection with otherwise valid receipts, digest tampering, reserved
terminal space, UTF-8 prefix limits/full hashes and raw OS return code zero being
retained when missing scientific receipts cause parent validation failure.
All data loading, calibration FITS access, PRF construction, fitting and numerical
measurement channels in the end-to-end fixture are replaced by synthetic stubs.

Commands:

```text
dyson-revet/.venv/Scripts/python.exe -B -m unittest discover -s tess-short-eclipses/tests -p test_m2p*.py -q
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache tess-short-eclipses/scripts/m2p.py tess-short-eclipses/tests/test_m2p.py tess-short-eclipses/tests/test_m2p_review.py
```

Reviewed SHA-256 snapshot to freeze:

- Driver: `312f0dfd8cdd5a4633e6d8dc138ab36d9d322483bdd06f9669b0e6c5b5e5427e`.
- Protocol: `93c8cfef1d8c0a28fc19b0b44f3446b67f7a5a526f5b36fa0166213f32894af0`.
- Author tests: `63cc73c64c830733f1564bbf5dbbd6e64216671e04bb4bed13d81384624660cb`.
- Independent tests: `3e363d9ae8688b312763cf8e180ab0d3afd1726f479ad6df8631a69a3dcfcab2`.

The frozen manifest must bind actual numerical-core files and all prerequisite
inputs/receipts as well. Root-reported metadata-only preparation finds 3+2+3
locations, implying 1,920 planned real trials; the reviewer has not independently
executed that metadata collector or any real fit. Runtime/memory feasibility is
not promised by these mocks. Hard worker deadlines and retained partial outcomes
remain essential. No result from this stage alone authorizes an unknown survey,
publication, physical-depth claim or declaration of discovery.
