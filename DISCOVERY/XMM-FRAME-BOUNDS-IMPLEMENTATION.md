# Synthetic frame-bound implementation checkpoint

September 12, 2026. Implemented only the mathematical construction in
[the prospective boundary note](XMM-FRAME-BOUNDARIES-2026-09-12.md).
**Not adopted for scientific execution; physical support assumptions remain
unvalidated.** No real frame/photon arrays, network requests or frozen-file
changes accompanied this work.

## Interface and algorithm

`FrameBounds(centres, weights, chunk_size=262144)` validates and copies one
CCD/exposure's ordered finite centres and matching nonnegative finite weights.
Reuse `.bounds(accepted_intervals, gtis)` for multiple bin/reference queries;
`exposure_bounds(...)` is the one-query convenience wrapper. Zero weights and
empty inputs are explicitly supported. Invalid shapes, ordering, nonnumeric
types, Boolean inputs and overflowing result sums raise rather than pass.
Mixed Boolean/numeric Python sequences are checked before coercion; an already
coerced numeric ndarray cannot reveal its original source types.

Accepted intervals and GTIs are separately unioned and intersected. Chunked
`searchsorted` tests support-envelope containment and positive overlap. A frame
is counted at most once per query even across disconnected reference intervals.
The first/last exterior bounds are infinite internally, not invented finite
endpoints or exposure. Returned JSON-compatible scalars include lower/upper
exposure seconds, contained/uncertain/outside frame counts, interval count and
an explicit `MATHEMATICAL_BOUNDS_SUPPORT_ASSUMED` status/endpoint policy.

Preparing arrays takes O(n) storage/work; query work is O(n log m), plus union
sorting, for n frames and m accepted-GTI components. Query temporaries are
chunk-bounded; prepared arrays still reside in memory. There is no frame-by-
interval nested loop and no physical frame duration inferred from missing gaps.
Ordinary float64 sums are **not certified outward-rounded interval arithmetic**;
last-bit chunk differences are possible. No physical uncertainty is estimated
from floating-point residuals.

## Verification

Fifteen author test methods pass: known weights, touching endpoints, GTI cuts,
overlapping/adjacent unions, disconnected queries, long gaps, single/empty
tables, zero weights, invalid inputs, overflow and caller-mutation isolation.
They include variable-duration physical examples and 50 scalar-oracle trials
at four chunk sizes. Parent's independent test adds 100 realizable variable-
frame examples with random omissions, interval unions and three chunk sizes;
it passes unchanged. Review found a mixed-Boolean validation gap; author fixed
it and extended regressions before this checkpoint.

Combined with the eleven current timing tests, **27 unittest methods pass**:
from `DISCOVERY`, run `../dyson-revet/.venv/Scripts/python.exe -m unittest
test_xmm_frame_bounds test_xmm_frame_bounds_review test_xmm_timing -q`.
Root-invoked Ruff 0.16.5 passes all five source/test files.

A synthetic scaling probe used one million centres `arange(1000000)`, weights
0.5, accepted interval [100,900000), GTI [0,1000000), default chunk size.
Preparation took approximately 0.0041 s and one query 0.0232 s on this runtime;
expected bounds 449949.5/449950.5 s matched. This single simple query is not a
many-bin benchmark, real-data time guarantee or measured peak-memory claim.

## Independent review of the parent's bounded-tail wrapper

Read current `bounded_constant_rate_tail` and its tests. It correctly evaluates
the existing one-sided binomial tail at bin-upper/reference-lower exposure,
which maximizes the exposure probability for fixed observed counts and total.
It rejects nonpositive lower bounds, malformed/unordered/nonfinite bounds and
Boolean bounds; exact bounds reduce to the original diagnostic. All eleven
timing methods pass, including three wrapper methods. No blocking finding.

The caller must still establish support assumptions, valid exposure weights,
disjoint fixed count/time selections, whole reference bins outside exclusion,
minimum reference lower exposure, Poisson assumptions and detector/background
validity. Neither helper verifies those conditions or supplies a discovery
false-alarm probability. No real exposure/count pair was evaluated.

## Current reviewed identities

| File | SHA-256 |
| --- | --- |
| `xmm_frame_bounds.py` | `516ddf003c39f399a3b82128a990aa88d920ea7d7483dcfd622cf171dd6ba0f1` |
| `test_xmm_frame_bounds.py` | `616bfa900c14935c59be6103ac1bc2c802e1801f1755ea602122dc3d83cc972b` |
| Parent `xmm_timing.py` reviewed | `ac04e0e830924c4dd271365fe1288c695d4db6c16f940f4a9dc38cb9df5438ec` |
| Parent `test_xmm_timing.py` reviewed | `0bd92a7411645fe504afd7aae4dc9b2b6a9f5cdf28347fbf15f35b348885b567` |
