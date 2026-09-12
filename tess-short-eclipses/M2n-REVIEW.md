# M2n independent pre-execution review

2026-09-12. Review of the new fixed-phase negative-window stage. No retained
LC/TPF data was loaded for new measurements, no actual stage prepare/run/execute
was invoked, and no network request or scientific outcome was examined. The
reviewer owns only this document and `tests/test_m2n_review.py`.

## Design and implementation inspected

Read the project instructions, README, localization proposal, original M1
protocol and paired-event/day-summary implementation, followed by the complete
new M2n source, protocol and author tests. Confirmed the intended scope is a
within-field feasibility diagnostic, not PRF fitting or a survey false-alarm
calibration. The original signed linear estimator remains unchanged.

The reviewed implementation applies a distance-to-half-period-lattice exclusion
of <= one full retained duration before every phase's in/side windows. It retains
the original first common-valid timestamp as day anchor, separately applies
FLUX/BKG error and pixel-validity rules, and requires primary reproduction before
new phases. Absolute phase SNR uses the inherited three-error flag; background
coherence uses the original primary decrement as its amplitude reference.
Undefined/nonfinite errors cannot imply a quiet result. There is no aperture,
ephemeris, phase or duration optimization and no centroid fit.

## Initial synthetic findings, before any real outcome

Two accountability gaps were reported to the author:

1. A failed background channel discarded an already computed flux result;
   a failed flux channel suppressed the predetermined background measurement.
   The reported cadence support could therefore look jointly measured while
   belonging only to flux. Both channel outcomes must remain explicit, and
   unavailable support must not be presented as measured zero overlap.
2. Replay verified only the artifact names listed by the saved summary, without
   requiring the complete expected receipt set or checking original worker-output
   identity/status. An omitted runtime hash or changed worker-output TIC/status
   could go unchecked. Require exact artifact closure and outcome consistency
   before any replay worker launch.

The eight initial independent tests use synthetic inputs and mocked data loading,
measurement channels and workers; no retained data enters them. Four directly
reproduce the issues above. Other checks cover primary-failure short circuit,
exclusion-before-channel/original-anchor preservation, nonfinite summary failure
and integer CADENCENO precision above 2^53. An initial anchor fixture used an
out-of-eclipse first timestamp; the reviewer corrected the fixture to place it at
primary epoch. That was a test error, not a code finding.

**Status at initial review:** execution signoff pending fixes and independent
regression rerun. Fixed offsets remain six per mandatory field and failures
remain in the planned denominator. Overlapping samples/day blocks preclude
interpreting eighteen phase slots as independent nonvariable stars. Passing
synthetic tests will establish software behavior only, not empirical validity.

## Final pre-execution signoff

**GO for code/protocol/test freeze and the parent-approved bounded M2n run.**
Both initial findings were fixed before any real outcome. Each phase now attempts
and retains both channel outcomes, including successful partial measurements;
shared support and overlap are null when not jointly established. Replay requires
complete artifact keys, every successful worker's result/runtime/start files,
valid runtime caps, ordered outcomes and matching original worker-output TIC,
status and manifest identity. Failed/unlaunched workers remain retained failures
and are not measured again.

Independent verification passes **20 tests** (11 author and nine independent)
using the existing Python runtime. Pinned Ruff 0.16.5 passes for source and both
test files. The added ninth test also demonstrates the positive replay path:
three mocked 180-second bounded launches, with every temporary fixture file
byte-identical afterward. This guards against “passes by rejecting everything.”
The synthetic channel regressions additionally prove null overlap for partial
phases and preservation of the successful channel regardless of which fails.

Commands:

```text
dyson-revet/.venv/Scripts/python.exe -B -m unittest discover -s tess-short-eclipses/tests -p test_m2n*.py -q
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache tess-short-eclipses/scripts/m2n.py tess-short-eclipses/tests/test_m2n.py tess-short-eclipses/tests/test_m2n_review.py
```

Reviewed SHA-256 snapshot, to bind before execution:

- Source: `1c7c4ff549b6aa580c749117c3db84a16371e929b14de57dde5161a8f86f4e94`.
- Protocol: `618b7c46155bc34eec7b92afb730ed1423ac6712314f2a47b36a43e51bae8df0`.
- Author tests: `48b71de1555bfa7c06a5d9f1994e91bd9285c3ffa964e10e142249f470895f7c`.
- Independent tests: `468ebe0b4ad361a3fca995ae0a3ddbacadaee32d5148c8237a1a49652510eec5`.

No open blocking implementation finding remains within this scope. A field-level
input/primary-replay failure is a STOP_INPUT_OR_MEASUREMENT result, rather than
six observed null phases; it cannot be counted as clean or silently excluded from
the three-field/eighteen-planned-slot accounting. Whole-field resource failures
are likewise separate from empirical phase outcomes. The memory limit remains
a measured peak-working-set acceptance cap, not an OS allocation quota.

The review did not call actual data loading or stage execution. All calls to the
measurement orchestration used mocked load_data, channel and metadata reads.
No frozen scientific files were changed. This signoff establishes readiness to
measure the preselected diagnostic, not confidence that the negative windows
will be quiet, a calibrated false-positive rate, or discovery/search permission.

## Independent post-result audit

2026-09-12. **All three frozen fields and all eighteen preselected phases are
accounted for; all thirty-six FLUX/background channels were measured.** Each
phase is QUIET_DIAGNOSTIC under the frozen descriptive thresholds. The reviewer
ran exactly one `m2n.py replay` through the owner-context Windows parent harness,
with the unchanged 180-second process-tree bound for each of three serial workers.
All returned exit 0 with exact deterministic reproduction. No new phase, pixel
estimator, fit, request or threshold was introduced.

All 28 dependency and ten artifact hashes were independently checked against the
frozen manifest/summary. Forty unique bound files, including manifest and summary,
were hash-identical before and after replay. Manifest SHA-256 is
`bf1e1b949a03422981d175991bdfcbf1f9a32544df6bbe48cedc76a483846b98`.
The exact result hashes remain:

- TIC 450781262: `56f4e526c0bc004dd130184484007d9dd8b2a1509c39de2a4fabf1ccd06c2b25`.
- TIC 53206761: `a98e4df9bcd39fca19d8b4069f7d01ed8540741fd1cd4b47dcbf19eb33946734`.
- TIC 2041210548: `a7b275012b99777d59bc2e1a8f4054b6acaf60e2e296dced538bca2ec777fa94`.

### Independent cadence and summary reconstruction

Separate audit code, without importing the M2n estimator, reconstructed the
LC/TPF common-valid cadence set using retained time, cadence, quality and required
LC validity columns. It independently used the nearest half-period center for
primary/secondary exclusion, rather than calling safe_times. Original anchors,
point counts and excluded counts agree. No observed sample lay exactly on an
exclusion boundary (minimum margin approximately 6.96e-8 days), so the independently
written equivalent distance calculation produced the same membership.

For all phases, time-only reconstruction recovered every stored eligible event
center, window's two-cadence support and day label. Sorted int64 cadence hashes,
counts, all intersections and all Jaccard values match exactly. Both channels use
the same temporal support. Every channel meets >=20 events, >=10 days, >=25 valid
collected pixels and complete fixed-SAP-pixel coverage. Signed amplitudes, positive
finite errors and SNRs independently reconstructed from retained day amplitudes
agree to absolute 1e-12; all phase/background flags are consistent.

| TIC | Common points | Excluded | Events per phase | Days | Largest off-diagonal Jaccard |
|---|---:|---:|---:|---:|---:|
| 450781262 | 14,077 | 3,327 | 204–209 | 22 | 0.313791 |
| 53206761 | 12,570 | 2,089 | 131–132 | 19 | 0.255396 |
| 2041210548 | 17,991 | 2,736 | 85–87 | 26 | 0.146067 |

Maximum absolute FLUX SNR is **2.7423788584** and maximum absolute background SNR
is **2.4780099429**. These are descriptive block-error ratios, not Gaussian
significance levels or false-alarm probabilities. No failed channel or phase was
dropped to obtain the quiet result. Primary reproduction remains exact and
unknown_search_authorized and physical_depth_validated remain false.

This supports feasibility of these particular fixed within-field windows for a
subsequent separately frozen diagnostic. Shared samples (Jaccard up to 0.314),
shared days, known binary variability and common instrumental systematics prevent
interpreting 18 quiet slots as 18 independent negative stars. It does not validate
PRF localization, source confusion, unseen blends, population false positives,
novelty or any astrophysical discovery. This append is the only file changed by
the reviewer in the post-result audit.
