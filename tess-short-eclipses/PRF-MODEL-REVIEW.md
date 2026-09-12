# Independent PRF numerical-core review

Date: 2026-09-12. Scope: synthetic numerical implementation only. No actual PRF
array interpolation, normalization, fitting, injection, new network product,
scientific manifest or unknown target is authorized by this review.

## Pre-code review plan (not signoff)

Read project instructions, current README, the localization proposal, coordinate
audit and completed M2a/M2n results. The official exporter and release README were
read directly as text during the preceding independent M2a review. M2a validates
the acquired input structure, not the numerical model. M2n's eighteen fixed
off-phase checks remain correlated within-field diagnostics, not population
negatives. Neither changes the independent absolute-registration caveat.

The author supplied this provisional interface contract before code review:
corners ordered `(rowlo,collo), (rowlo,colhi), (rowhi,collo), (rowhi,colhi)`;
origin `(native_column,native_row)`; dense-array sample coordinates
`58 + 9 * (pixel - source)` in array `(y,x)` order; bilinear field interpolation
at `origin + source`. A zero nodal extension tapers the finite array edge over
one ninth-pixel. Complete integer-detector support is normalized before cropping,
with lost-wing accounting. Position fitting uses signed amplitude plus a plane,
catalogue-independent initial positions, and bounded optimization.

Independent tests will use asymmetric synthetic arrays and explicit arithmetic
oracles rather than actual calibration arrays or agreement between two wrappers
of the author's sampler. Planned checks include all 81 exact subpixel phases,
source-offset sign and row/column order, integer and support-edge continuity,
field corners/brackets, and full-support normalization versus crop sums.
Fitting review will check both signs, rank deficiency, optimizer failures,
deterministic bounds, and fixed-hypothesis completeness/score interpretation.
Zero-amplitude convergence is not source identification, and an improvement in a
weighted residual score is not a calibrated chi-square probability.

No preflight acceptance is given by this plan. Final findings, exact reviewed
hashes and independently executed test results will be appended after code exists.

## Implementation review and independent checks

The completed source and design were read in full, together with the author
tests. The final algorithm uses one plane-subtracted absolute-peak seed with
deterministic row-major tie breaking; the initial unimplemented 25-point seed
suggestion was superseded explicitly before any real-data evaluation. A single
bounded local fit is not claimed to find a global optimum. The source has no
network, file loading, catalogue selection or scientific-stage entry point.

Nineteen independent tests now supplement the author suite. They include:

- All 81 phase combinations, using an asymmetric scalar four-node interpolation
  oracle and an independently enumerated full detector lattice, not the author's
  interpolation routine. These cover normalization as well as exact samples.
- Asymmetric impulse/sign/row-column tests, zero-edge and corner tapering,
  integer/support-transition continuity, field-corner weights and rejected
  extrapolation, immutable input copies, and identical retained pixels across
  different crop sizes. Flux normalization occurs before cropping; the finite
  support is not an infinite-flux estimate.
- Positive and negative amplitude/position recovery, exact deterministic
  repetition, explicit invalid-mask/error/rank failures, retained null residuals
  for masked pixels, wrong-position residual comparisons, and error-scale tests.
- An independent six-parameter finite-difference Jacobian/normal-matrix inverse
  reproduces the centroid covariance, including sign invariance and fourfold
  covariance scaling when errors double. This verifies algebra, not actual
  diagonal-noise assumptions, astrophysical confidence or empirical coverage.
- A synthetic runaway optimizer reaches the hard 480 residual-model-call limit;
  attempt 481 is rejected before another model call. Postfit evaluation and
  covariance are separate bounded extra computations, not included in that
  residual counter. Parent process/memory limits remain required.
- Optimizer exhaustion, an exact mocked boundary solution, zero-amplitude
  covariance failure, and the low-SNR boundary counterexample below.

Every reported residual score remains descriptive, not a chi-square probability.
The module supports one fixed hypothesis at a time. It **does not itself prove
that every catalogue hypothesis was evaluated**: the future stage must freeze
the complete input ledger and preserve identities, invalid/outside cases, counts
and failures. Likewise it must count failed fits or missing covariance as failed
trials where required, never silently omit them from coverage/confusion statistics.

## Preserved numerical boundary counterexample

Using the reviewer synthetic Gaussian, true position `(-0.5,5.71)`, amplitude 7,
unit pixel errors and the documented fitted plane, the solver returns:

```text
x = -0.49995382769411173
y = 5.710000222368933
amplitude = 6.999780058573569
weighted_residual_sum = 3.603411187116661e-10
optimizer termination = gtol
nfev = 15; residual evaluations = 45
bound_hit = false; localization_validated = false
```

The true source is exactly at the permitted boundary, but the fitted position is
about 4.62e-5 pixel inside it, beyond the literal 1e-5 fitted-distance flag.
The initial reviewer test wrongly expected that flag to classify the *true*
position and failed. Inspection established this distinction; the counterexample
is now explicitly preserved in a test, alongside a direct exact-bound branch
test. No numerical threshold was changed to make it pass. The parent accepted
the literal numerical criterion and required the limitation in the later stage.

Consequently, `bound_hit=false` must never mean the true source or its uncertainty
region is away from an edge. A stronger uncertainty-region rule requires its own
prospective scientific definition, not a retrospective adjustment to this case.
Zero-amplitude convergence and a small covariance are likewise not identification.

No actual PRF, uncertainty image or science array was loaded/evaluated during
these tests; all model inputs were generated synthetically in memory. No existing
scientific protocol, input, result or STOP was changed by the reviewer.

## Pre-union synthetic checkpoint (superseded below)

Final pre-output refinements were also reviewed: the solver's `active_mask` is
retained as `optimizer_active_mask` without being silently unioned into the
literal fitted-distance rule; covariance perturbation work arrays explicitly use
floating dtype, including when a caller supplies integer x/y; and nonfinite
weighted residual scores fail explicitly. The author added integer-coordinate
covariance and high-SNR bound regressions. The reviewer exact-bound mock also
checks the retained solver mask. No real-output criterion was tuned.

Independently executed with the existing runtime:

```text
dyson-revet/.venv/Scripts/python.exe -B -m unittest discover \
  -s tess-short-eclipses/tests -p "test_prf_model*.py" -q
34/34 PASS: 15 author + 19 independent; 0.341 seconds reported test runtime

dasch-pilot/.venv/Scripts/ruff.exe check \
  tess-short-eclipses/scripts/prf_model.py \
  tess-short-eclipses/tests/test_prf_model.py \
  tess-short-eclipses/tests/test_prf_model_review.py
Ruff 0.16.5: PASS
```

No skipped tests or expected failures. The runtime is a synthetic test-suite
timing, not a cost estimate for actual PRFs or the proposed experiment.

| Reviewed artifact | SHA-256 |
|---|---|
| `scripts/prf_model.py` | `37500bdd5897bbf8b205d61b47c7340dd0b0309b995243644c85aab540fe7adc` |
| `PRF-MODEL-DESIGN.md` | `ae7a9e6f1f84d681892d52189866a6350b38bccd9a1c5c1ff68b7895b1d9ce30` |
| `tests/test_prf_model.py` | `6e7750dc2e7719b008cccb81dfe78109f8f41a4b2bab062ab39188a5430488b0` |
| `tests/test_prf_model_review.py` | `bde1c2add743950d8450efa91a0dd87df7eea05cd4d79fbe8ebc56ad5c5b0941` |

**Scoped conclusion: numerical core accepted for inclusion in a separately
reviewed prospective experiment; no remaining implementation-contract blocker
identified.** This does not authorize real PRF evaluation, real-data fitting or
injections, catalogue-hypothesis selection, unknown targets, or a scientific GO.
The future driver/protocol must bind input hashes, preserve every hypothesis and
trial, impose execution budgets, freeze thresholds, and distinguish numerical
convergence, nominal coverage and empirical localization/confusion acceptance.
Absolute registration, correlated errors, PRF/model mismatch, real negative-field
validation, physical depth and source-specific novelty remain separate gates.

## Final signoff: explicit solver-active or fitted-distance rule

Before any real-array use, the parent clarified that the root experiment protocol
requires `bound_hit = any(solver active_mask) OR distance_to_bound <= 1e-5`.
The author implemented that explicit union and updated the design. This
supersedes the output-only solver-mask interpretation in the preceding checkpoint;
the distance threshold itself was not adjusted to the synthetic counterexample.
Both author and reviewer added independent tests with a synthetic interior
position but an active solver-bound flag. The low-SNR true-boundary counterexample
still passes as a preserved limitation: neither flag establishes true position.

The revised lines, design and new tests were independently read. The same test
and pinned Ruff commands above now give **36/36 PASS (16 author + 20 reviewer)**,
with no skipped tests or expected failures; reported suite time was 0.349 seconds.
Ruff 0.16.5 passes. No actual calibration/science arrays or network products were
accessed, and the reviewer changed only the review document and review tests.

These are the **final reviewed hashes**, replacing the earlier checkpoint hashes:

| Reviewed artifact | SHA-256 |
|---|---|
| `scripts/prf_model.py` | `dc9ebf3c94c8e5742b598012031d8f10d1d74d1898993bb7ce9dbe27355da9e7` |
| `PRF-MODEL-DESIGN.md` | `9c79ac8395f028280f97b348e7931867f68d011baf4717bc5633a63806b54635` |
| `tests/test_prf_model.py` | `9b50df6d894efa52830230f15a02109a3bff68c3967011edd05025ba6f052350` |
| `tests/test_prf_model_review.py` | `3f98a54bb488104daed575bbeaafd256f045a0be616b44972596549d10b6d332` |

**Final scoped acceptance: GO to freeze this numerical core within the separately
reviewed experiment.** All scientific, provenance, complete-ledger, execution
budget and unknown-search boundaries stated above remain. No real-data experiment
or astrophysical claim is authorized by synthetic correctness alone.
