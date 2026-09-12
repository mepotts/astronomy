# M2n: fixed real-data off-phase feasibility

Prospective new stage; no outcome read before code/test/protocol freeze. This
executes the negative-window prerequisite in NEXT-LOCALIZATION-PROPOSAL, not its
PRF fits or injections. All three published controls remain mandatory, in order
450781262, 53206761, 2041210548. No unknowns, requests or new pixels. Preserve all
earlier stages unchanged. This is not public preregistration.

## Inputs and measurement

Bind source, author and independent tests, this protocol, unchanged M1 source and
protocol, M0 source and both protocols, M0b/M1b results, original TPF receipts,
LC/TPF bytes and the existing process-tree helper by SHA-256. Require M1's fixed
source hash 22c46cbfd34877ac66d7b1fcd411ecb8b323aca5ea987da58d62ea141ed29115.
Use M1.read_solution/check_header and exactly its LC/TPF cadence intersection,
finite-value/positive-error/QUALITY=0 selection and SAP reproduction tolerance.
Replay original primary paired-event count, day labels, aperture/block statistics
and difference image exactly against M1b before measuring any new phase.
Retain original M0b period, epoch, duration, SAP aperture and collected pixels.

Use phase offsets 0.20, 0.25, 0.30, 0.70, 0.75, 0.80, without replacements.
Remove every timestamp within <= one retained duration of a primary or half-period
center before passing time/flux/error arrays to unchanged M1.paired_events. Thus
these samples cannot appear in either in-window or comparison side-window.
No eclipse subtraction, clipping, detrending or phase refinement. This does not
assume absence of other binary variability or eccentric secondary eclipses.
Preserve the ORIGINAL first usable timestamp as the day-block anchor even after
exclusion. Keep inverse-variance window means, weighted-time linear interpolation,
out-minus-in sign, two samples per window, >=20 events and >=10 populated days.

Apply separately to FLUX and FLUX_BKG with their own retained errors. Each channel
must have >=25 collected pixels finite for every accepted event and all SAP pixels
valid. Missing pixels stay missing. Attempt both channels even if one fails and
retain each successful measurement and each channel-specific failure. Unavailable
cadence support is null, not an empty set or jointly measured support.
Save signed SAP amplitudes, block errors/SNR,
per-day SAP amplitudes, mean/error/valid-pixel maps, event centers and day labels.
No centroid fit is attempted: sign symmetry is in the unchanged signed linear
estimator. Gaussian/PRF location is not needed to determine null feasibility.

For each phase flag PHASE_CONTROL_STRUCTURE if FLUX absolute SNR >=3; zero,
nonfinite or undefined error is a failure, not a clean null. Flag
BACKGROUND_COHERENCE if absolute background SNR >=3 AND absolute background
amplitude >10% of the retained primary SAP decrement, exactly M1's definition.
Undefined background error also fails. These inherited thresholds are descriptive
diagnostics, NOT probability statements or a survey-level false-alarm calibration.
Report all six phases even if one fails; do not select good phases afterward.

## Correlation accounting and statuses

Retain counts/hash of original CADENCENO values used in any accepted in/side window
at each phase, and the six-by-six intersections and Jaccard matrix. Hash sorted
little-endian int64 CADENCENO bytes. The same temporal membership applies to both
channels; individual invalid pixels may use fewer samples and remain explicit.
Shared day labels and observation baselines cause correlation even when overlap is
zero. These are three known variable fields, not a population of negative stars.

Any coverage, input, finite-statistic or phase/background failure gives
STOP_NULL_STRUCTURE_OR_COVERAGE (with exact subordinate reason). A resource or
worker failure is separate. Otherwise report
WITHIN_FIELD_DIAGNOSTICS_COMPLETE_VALIDATION_INCOMPLETE. Always retain
unknown_search_authorized=false and physical_depth_validated=false. A passing
result does not validate source identity, PRF errors, unseen blends, population
negatives or novelty. A failing result means these fixed windows cannot supply
the proposed injection/null calibration without a new justified experiment.

## Execution and verification

New scripts/m2n.py, tests/test_m2n*.py, data/m2n and out/m2n-* only. Prepare an
exclusive manifest, commit reviewed source/protocol/tests, then explicit parent
approval of its SHA-256 is required for run. Exclusive parent run-start and per-field
worker-start markers forbid reruns. Three serial process-tree workers, 180 seconds
each (540 total), <=1,000,000 scientific JSON bytes per field. Inherited Windows
peak-working-set acceptance <=1 GB before/after measurement (not an allocation
quota); conservative input cubes are bounded by retained hashes. Runtime receipts
are separate from deterministic science. A nonzero worker stops further launches
and records remaining fields as unlaunched. Scientific STOPs remain valid results
and do not suppress the other controls. No automatic retry or fallback.

Replay verifies dependencies, run/worker markers, outcomes, result/runtime hashes
and recomputes complete deterministic successful results, using the same bounded worker
helper but writing no files. Failed/unlaunched workers are verified as retained
failures and are not executed again; such replay exits nonzero rather than claiming
full measurement reproduction. Require the exact artifact-key set and valid runtime
receipts for every successful worker. Synthetic tests cover exclusion boundaries, phases
and wraparound, signed/linear-drift recovery, gaps, original day anchoring, missing
pixels/errors, all failure flags, phase overlap and preservation of earlier data.
Review tests are independent harness checks, not empirical scientific evidence.
