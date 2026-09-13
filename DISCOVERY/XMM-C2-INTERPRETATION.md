# C2 interpretation: frame weights are coherent; local timing exposure is not yet validated

September 12, 2026. This note uses only retained C2 JSON summaries and their
header-only manifest, plus the existing exposure-semantics and geometry notes.
No scientific payload was reopened, no photon values were inspected, no network
request was made, and no correction was fitted or applied.

## Decision

**Advance to the already proposed exposure-map/attitude metadata and geometry
check; do not substitute a global LIVETIME or renormalize the frame weights.**
C2 substantially strengthens the case for `TIMEDEL * FRACEXP` as a descriptive
full-frame weight. Its total is much closer to the matching EVENTS CCD live time
than to the earlier EXPOSU scalar LIVETIME. However, small nonzero differences
remain, and a total over the observation does not establish the correct relative
exposure of each fixed aperture in each prospective time bin.

The remaining blocker is not a bad-value or ordering failure in these tables.
It is **unbounded local, time-dependent acceptance and frame-boundary treatment**:
we have not yet established that the fixed source/background/negative regions
stay in usable coverage or that their bin/reference exposure ratio captures all
relevant losses. This is a tractable control-validation step, not evidence for a
discovery or a reason to acquire another field.

## What the saved diagnostics establish

All 24 GTI tables have finite, positive, ordered, non-overlapping intervals:
564 pn rows, 114 MOS1 rows and 155 MOS2 rows, totaling 833. Their union durations
agree with the matching EXPOSU ONTIME headers to at most approximately
`5.1e-11` seconds in the retained arithmetic comparison. This is numerical
consistency, not meaningful timing accuracy at that precision.

The exposure tables contain 7,693,686 pn rows, 128,045 MOS1 rows and 165,171 MOS2
rows. All satisfy the frozen finite-time/finite-positive-width/fraction-[0,1]
predicate, with no global repeated finite times or non-increasing adjacent
times. All row centres lie in their matching valid GTI union. Consequently,
**the unrestricted and GTI-centre-member weighted sums are identical for every
CCD**. Selecting whichever of those totals agrees better cannot explain or
remove any residual here: they are the same measurement.

Zero pn fractions occur and remain valid zero-weight rows, not rejected rows.
The pn fractions span 0 to 0.9765625 across the tables; MOS1 spans approximately
0.86217 to 1, MOS2 approximately 0.83272 to 1. This rules out treating the
retained fraction column as universally unity. Aggregate extrema alone do not
describe where its variation occurs in time.

The pn candidate width is the fixed header value `0.0687021985650063` seconds.
Actual MOS widths vary: central-CCD ranges are approximately 0.8550–1.8094 s
(MOS1) and 0.8429–1.8136 s (MOS2); outer-CCD ranges are approximately 2.6703–2.7285 s
and 2.6655–2.7391 s respectively. Consecutive time gaps reach roughly 121–135 s.
These are observed spacings, not permission to stretch a frame's width across
a missing-data gap.

## Quantitative comparison with the correct CCD scalar

Define `W = sum(TIMEDEL * FRACEXP)` over the explicit valid rows. Width is the pn
header value or MOS per-row column as frozen. Every W below also equals the
separately recorded half-open GTI-centre-member sum. No scalar multiplier has
been fitted. The central CCD is pn CCDNR 04 and MOS CCDNR 01, not a camera average.

| Central detector | Sum of widths (s) | W (s) | EVENTS CCD LIVETI (s) | W minus EVENTS (s) | EXPOSU LIVETIME (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| pn 04 | 44351.322603 | 40781.971897 | 40781.923947 | +0.047949 | 47319.690471 |
| MOS1 01 | 49000.798621 | 48817.975191 | 48809.966720 | +8.008471 | 49228.151758 |
| MOS2 01 | 49165.070705 | 48987.591543 | 48977.793489 | +9.798055 | 49399.133352 |

For completeness, the residual `W - matching EVENTS LIVETInn` for every retained
CCD is below. A dash means that CCD was not in this camera's frozen input set;
it is neither zero exposure nor an inferred missing measurement.

| CCDNR | pn residual (s) | MOS1 residual (s) | MOS2 residual (s) |
| --- | ---: | ---: | ---: |
| 01 | +0.128363 | +8.008471 | +9.798055 |
| 02 | +0.128362 | +7.989856 | +0.000014 |
| 03 | +0.128363 | — | +10.671593 |
| 04 | +0.047949 | +10.697347 | +8.034097 |
| 05 | +0.047949 | +13.327628 | +5.375031 |
| 06 | +0.047949 | — | +16.025666 |
| 07 | +0.130418 | +10.656779 | +8.005629 |
| 08 | +0.130418 | — | — |
| 09 | +0.130418 | — | — |
| 10 | +0.319368 | — | — |
| 11 | +0.319367 | — | — |
| 12 | +0.319368 | — | — |

Relative to each corresponding EVENTS scalar, pn residuals are approximately
0.000118–0.000798%; MOS1 0.016407–0.027431%;
MOS2 approximately 0.000000029–0.03282%. MOS2 CCD02's near equality must not be
used to claim all CCDs agree exactly. Conversely, there is no justification for
treating the small remaining positive residual as an arbitrary efficiency to
divide out.

The older EXPOSU LIVETIME comparison is materially different: W is lower by
6,537.7–6,896.9 s for pn, 108.2–410.2 s for MOS1 and 108.8–411.5 s for MOS2.
The closer EVENTS agreement, together with the documented exported-column
meaning, supports retaining the frame weights. It does not prove the exact
history of either scalar or make an inherited-header explanation certain.

## Scientific interpretation and limits

The [existing semantics assessment](XMM-EXPOSURE-SEMANTICS-2026-09-12.md) records
official algorithm evidence: MOS exported TIMEDEL excludes transfer time and
FRACEXP describes cosmic-ray losses; pn's effective TIMEDEL includes
mode-dependent treatment, including the exposure-map documentation's OOT
distinction. Applying another generic transfer/dead-time/OOT factor would risk
counting a correction twice. The task-version differences and the explicitly
outdated section of the pn manual remain real limitations. See the already
reviewed [MOS export description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emevents/node3.html)
and [exposure-map effective-time description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).
These sources were not fetched again for this note.

C2 does not identify the cause of the residuals. Partial-frame/GTI boundary
conventions and later processing bookkeeping are possibilities, not measured
explanations. Every centre being inside a GTI says nothing about whether every
nominal frame interval lies completely inside it. C2 did not calculate those
interval intersections. The equality of GTI-centre and unrestricted totals
cannot settle that separate question.

Nor does the very small full-observation relative discrepancy bound a short
bin's error: a similar total can result from different temporal allocations.
A truly constant unknown efficiency for the same fixed region cancels from a
conditional bin/reference ratio; an unaccounted time-variable loss or moving
edge does not. C2 has not shown that any unresolved term is constant.

Finally, frame tables are CCD-level information. They do not establish a
fixed sky aperture's intersections with windows, chip gaps, bad pixels or
spatially varying discarded-column losses. Photon emptiness cannot supply
that missing exposure geometry.

## Smallest next geometry/exposure step

Follow the finite four-product proposal in
[XMM-GEOMETRY-NEXT-2026-09-12.md](XMM-GEOMETRY-NEXT-2026-09-12.md): exact-size
metadata checks, then separately bounded retention and header inspection of
the already observed pn/MOS1/MOS2 per-exposure band-8 EXPMAPs and the observation
ATTTSR. Do not acquire additional bands or fields because a geometry check fails.

Before any map or attitude array inspection, freeze a small known-control
geometry contract. It must verify observation/camera/exposure, numerical band,
units, WCS, processing and GTI/FLAG compatibility; keep all coordinates local and
the previously fixed aperture/annulus/negative offsets unchanged. Header mismatch
or unknown provenance is a specific STOP, not a reason to align maps using counts.

The ensuing geometry calculation should report static support/edge margins
and a conservatively justified attitude/rotation envelope for every required
region. Accumulated positive map exposure alone is not continuous coverage, and
an integrated exposure map is not a 200-second exposure curve. Different GTIs
in source-detection maps must remain explicit rather than silently substituted
for C2's event-list GTIs.

In the same prospective decision, finish the narrow temporal check: use the
already retained frame/GTI inputs under a new allowlist to count frame-boundary
intersections and bound how the chosen allocation convention changes candidate
bin/reference exposure ratios. Nominal wall-frame duration and effective weight
must remain distinct. This check needs no photon values, no renormalization to
EVENTS scalars, and no acquisition of all housekeeping arrays. Any wider
time-variable/spatial loss still not explained by the product semantics must
remain a named limitation rather than be fitted away.

Only compatible fixed-region coverage plus a defensible temporal exposure
ratio can support a separately frozen known-burst/negative counts experiment.
No unknown-target scan, burst recovery claim or discovery follows from C2.

## Evidence identity

The 99 artifact hashes listed by the saved C2 outcome were independently
recomputed using JSON files only; all matched. This note did not rerun the
payload-reading replay. Technical outcome remains
`ANCILLARY_VALUES_SUMMARIZED_UNCALIBRATED`, with all 48 table receipts OK.

- C2 `outcome.json`: `bd69d5df9effd0a4097016a324f971467b4934b9ff048d1dd58eb17a1b8fff39`
- C2 `run-start.json`: `1f4cf7af9ccce935acef668586d9b5083dff08af86c72dd2f23aa07afb22ada5`
- C2 `worker-result.json`: `b7f1d7b687fee20728c18fe8117a4d60e32d8e6dd3dd0c4e8de10590e2649e69`
- Read exposure-semantics note: `a65bb2f30d8eed483f3221840a3ca00617d126604c700aae1c9e72c1934a882f`
- Read geometry proposal: `5663df2c9358fb61679f11347b2d58abb38dc28558b3538b4ea0530a3fc04e7b`

Reported decimals are rounded summaries, not new precision claims. All frozen
source, protocol, results and raw inputs remain unchanged.
