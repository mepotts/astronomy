# MOS finite-frame boundaries without an invented nominal duration

September 12, 2026. Read the exposure-semantics note, C2 interpretation and
selected retained C1 header metadata. Opened three narrow official SAS pages.
No arrays, photon values, new scientific products or coordinate queries were
accessed. This is a prospective prescription to review/test, not an executed
allocation or a modification of frozen C2 results.

## Decision

**Do not fix every MOS wall-frame duration to 0.9 or 2.7 seconds.** The retained
per-frame TIMEDEL is variable and already excludes transfer time. An exact
physical frame duration would require restoring the appropriate transfer-time
term and confirming its timestamp convention. Neither the scalar FRMTIME nor
the existing aggregate summaries supply that term for every extended frame.

An exact duration is not necessary for a useful, conservative boundary check:
derive outer support envelopes from adjacent retained frame centres, and bound
each bin's exposure by allocating uncertain boundary frames from zero to their
full weight. This needs no photon inspection, fitted rescaling, guessed transfer
constant, or uniform-within-frame allocation. It can yield a conservative
counts diagnostic even if exact exposure allocation remains unresolved.

## Evidence and why centre-only allocation is insufficient

The [C2 interpretation](XMM-C2-INTERPRETATION.md) records central-CCD TIMEDEL
ranges approximately 0.8550–1.8094 s (MOS1) and 0.8429–1.8136 s (MOS2). Outer
widths reach approximately 2.7285 and 2.7391 s. A fixed 0.9/2.7 wall interval
can therefore be shorter than the effective integration it is supposed to
contain. C2's positive ordered timestamps and full-frame weighted sums do not
resolve that contradiction by themselves.

`emframes` explicitly handles extended frames and distinguishes them from
telemetry drops using auxiliary information. One cannot infer that every long
timestamp separation is one long exposure. Missing/dummy-frame handling and
bad-frame rejection also matter.
[MOS frame processing](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emframes/node3.html).

`emevents` PUT_TI assigns the frame midpoint and can randomize photon times
within the frame. Its exported duration subtracts frame-transfer time; the
effective fraction incorporates the frame's cosmic-ray dead-time information.
This supports retaining `w_f = TIMEDEL_f * FRACEXP_f`, not multiplying by a
second generic correction or replacing the width with FRMTIME.
[MOS time/export description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emevents/node3.html).

The output specification distinguishes central frame TIME, integration TIMEDEL,
effective FRACEXP, and RAND_TIM metadata.
[MOS output fields](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emevents/node8.html).
All twelve retained MOS EXPOSU headers (five MOS1, seven MOS2) have RAND_TIM=1
and CCDNODE=0. Thus photons cannot be assumed to retain the exact common frame
centre. The merged EVENTS headers omit RAND_TIM; that omission does not undo
the per-CCD declaration. Current documentation names emevents 8.9.2 versus
retained 8.8, so its broad algorithm is evidence, not an exact binary replay.

## A conservative photon-blind support construction

Work separately per CCD and exposure. Required assumptions are explicit:

- Retained `t_f` is the centre of a physical frame, not a randomized photon
  timestamp. This is an explicit documented EXPOSU definition in the linked
  `emevents` output specification, not an inference from a timestamp histogram.
- Successive frames of this single CCD/node do not overlap in physical
  acquisition time. Bad/omitted intervening frames are allowed; no simultaneous
  node stream may be silently interleaved. This is a **support assumption**:
  `emframes` describes successive frames, start/end times and extended-frame
  sequencing, but the pages inspected do not explicitly prove non-overlap for
  every exported timestamp in the retained older task version. CCDNODE=0
  shows no declared mixture of node identifiers; it is not by itself a
  proof of this temporal assumption. Record the assumption, rather than call
  it independently measured or guaranteed by ordered centres alone.
- The selected photons' assigned times remain within their physical frame,
  and `w_f >= 0` is that frame's total applicable exposure weight. Any further
  time-variable/spatial acceptance remains a separate requirement.

Let the unknown physical frame support be I_f, centered at t_f. For an interior
retained frame, use the deliberately loose envelope

    U_f = [t_(f-1), t_(f+1)).

Under the assumptions, `I_f` lies inside `U_f`: the previous frame's centre
precedes its end, which precedes this frame's start; the next frame gives the
opposite bound. Extended frames need no special nominal-duration guess.
If frames are omitted, the envelope becomes wider but remains conservative.
**Its width is not an exposure:** only the original w_f is ever allocated.

For the first/last retained frame, use an unbounded exterior side unless a
separately justified physical endpoint is available. Represent that state
explicitly in implementation, not as an invented finite timestamp. A one-frame
table has an unconstrained envelope. Do not clip U_f at a GTI edge and pretend
the frame must have ended there merely because its centre is inside.

For a bin or reference union J, intersect J with the applicable GTIs to obtain
A. Define

    E_lower(A) = sum w_f for U_f wholly contained in A
    E_upper(A) = sum w_f for U_f intersecting A.

Boundary contact without positive overlap does not count as intersection.
Subject to the assumptions, any allocation of the frame's effective exposure
within its physical support lies within these bounds. The interval width
`E_upper - E_lower` is an uncertainty budget, not a correction or a fitted
systematic error. Compute it from actual allowed frame/GTI inputs under a new
protocol; C2 aggregate extrema alone cannot produce the per-bin bounds.

Use only the disjoint, accepted whole reference bins completely outside the
prescribed exclusion interval. Apply containment/intersection to their complete
union, not a sum of independently maximized reference bounds: a single frame
must not be counted multiple times in one reference total. Reference lower
exposure includes only weights certainly inside that accepted union and GTIs.
Zero-weight frames remain accounted for and add zero.
Keep ordinary GTI wall coverage separate from these effective-exposure bounds.

## Why this can be useful for 200-second bins

For ordered centres, an interior cut lies within at most two such envelopes.
With only the two exterior bin edges and no internal GTI cuts, at most four
frame weights make the lower/upper bound differ. Based on rounded C2 maximum
widths and FRACEXP <= 1, that illustrative envelope is about 7.3 s for a
central CCD or 11.0 s for an outer CCD, approximately 3.7% or 5.5% of 200 s.
These are deliberately loose absolute illustrations, **not measured per-bin
relative errors**; effective exposures may be smaller than 200 s. Internal GTI
cuts, additional accepted-time exclusions and disconnected references require
their own boundary accounting. Always calculate the actual bound, not a
universal percentage gate.

A long missing-data gap does not acquire a large exposure merely because two
envelopes span it: each contributes at most its original small frame weight.
The true lower bound can be zero near gaps. Such a cell is unmeasured or weakly
bounded, not a full-exposure quiet bin.

For the constant-total-aperture-rate conditional test, let bin/reference
exposure bounds be `[L_j,U_j]` and `[L_r,U_r]`. A conservative probability bound is

    p_max = U_j / (U_j + L_r),

with an explicitly uninformative outcome if positive bin/reference exposure
cannot be established. The binomial upper tail at p_max is the worst-case
one-sided positive-excess tail, since, for the fixed conditioned count total
and fixed tested count, that tail increases with the exposure probability.
Correlations between the bounds can make this loose, not
anti-conservative. No actual counts are needed to define the construction.
The later protocol must require its predeclared reference-exposure minimum
using a defensible lower bound, not a favourable midpoint.

This is a conditional counting diagnostic, not proof of intrinsic source
variability or a globally calibrated discovery false-alarm rate. Unknown
time-variable losses, contaminated background or moving aperture coverage do
not become harmless simply because frame-boundary uncertainty is bounded.

## What remains unresolved, and what need not block this approach

Exact MOS physical frame durations remain `TIMEDEL + transfer-time term` under
the documented export meaning. The appropriate per-mode/extended-frame transfer
term and detailed randomization endpoints are not supplied by the inspected
headers/summaries. They are required for an **exact** overlap allocation, but
not for the outer-envelope bound if the support assumptions above hold.
Do not infer the term by forcing summed weights to EVENTS LIVETInn or by
rounding widths to nominal-frame multiples.

Before adoption, synthetic tests must cover extended frames, missing frames,
GTI cuts through envelopes, first/last frames, disconnected references and
monotonic worst-case tails. A new photon-blind metadata pass can then report
the actual lower/upper exposures and classify insufficiently bounded cells.
No threshold should be tuned to later photon peaks. If support assumptions
cannot be justified, preserve that precise STOP; do not quietly present this
envelope as a measured frame interval. Existing C2 evidence and all raw files
remain unchanged.
