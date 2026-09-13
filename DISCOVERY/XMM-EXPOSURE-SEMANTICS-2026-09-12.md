# XMM exposure semantics: practical C2 interpretation

September 12, 2026. Four official SAS documentation pages plus selected timing
cards from the retained C1 header JSON were inspected. No FITS arrays, photon
values, science-product download or coordinates were accessed. This note does
not change the [header review](XMM-C1-HEADER-REVIEW.md) or freeze a counts test.

## Decision

The defensible next step is **per-CCD frame-weight validation**, not use of a
global LIVETIME or another blanket dead-time multiplier. pn TIMEDEL already
contains a mode-dependent integration factor. Its retained per-frame FRACEXP
can potentially supply the remaining time-variable loss, but the inspected
pages do not establish every final PPS processing term. MOS has a different
frame-processing path, and SETDEADT=1 means a correction was already applied.
Retain these distinctions when interpreting the forthcoming C2 value summaries.

For a same-region timing test, a constant unknown multiplicative efficiency
cancels. Thus a remaining constant correction need not prevent a relative
counts-control. What must be established is that no unaccounted **time-variable**
loss changes the bin/reference exposure ratio. No full SAS/ARF requirement
follows from that narrower question.

## Direct algorithm evidence

1. The `epframes` algorithm initializes pn exposure TIME from corrected frame
   timestamps, TIMEDEL from nominal frame duration times mode livetime factor
   FC0, and FRACEXP to unity for subsequent tasks to modify. Its GTI construction
   uses half a nominal frame on either side of the first/last frame timestamp.
   Therefore nominal frame width and effective integration width are distinct.
   Do not apply FC0 again to a TIMEDEL-weighted sum.
   [epframes algorithm](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epframes/node15.html).
2. `epexposure` describes per-frame fractional-exposure calculation using
   counter/discarded-line information. Some counters are integrated across
   cycles and supplied per quadrant, not per CCD. Consequently neither a
   per-CCD naming convention nor an instantaneous housekeeping row establishes
   an independent per-frame loss measurement.
   [epexposure description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epexposure/node3.html).
3. Its loss inventory distinguishes mode readout, onboard discarded columns,
   ground MIP rejection, untransmitted frames and bad-frame losses. This gives
   concrete possible missing terms; it is not proof that the final PPS FRACEXP
   includes each term in a particular product.
   [epexposure basic idea](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/epexposure/node4.html).
4. MOS `emframes` computes frame timing, handles extended/missing/duplicated
   frames and calculates cosmic-ray-related dead time. It writes ONTIME and
   LIVETIME with different correction meanings and constructs GTIs excluding
   bad frames. A nominal camera-wide frame duration cannot replace each
   retained TIMEDEL when extended frames or different CCD submodes are possible.
   This description concerns the frame-processing output; it does not fully
   specify the later PPS EXPOSU serialization of its dead-time information.
   [emframes description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emframes/node3.html).

These pages describe SAS 22 task versions, while the retained products identify
a SAS 21 pipeline build. They supply algorithm evidence, not a source-code replay
of that older processing. Product-specific consistency checks remain necessary.

## What the retained cards actually settle

For pn EXPOSU, FRMTIME=73 ms is explicitly nearest-integer frame time, while
FRAMETIM=73.36496 ms is nominal. STDGTI FRMTIME carries the latter value.
The rounding discrepancy is explained; 73 ms must not replace the nominal
duration in a high-precision integration. The stored TIMEDEL is
0.0687021985650063 s. Their arithmetic ratio is

    TIMEDEL / (FRAMETIM / 1000) = 0.9364442993631604.

Under the documented pn construction, this is consistent with TIMEDEL encoding
the mode integration duty, not an additional gap to mark as a failed observing
bin. A nominal frame interval should not be assigned width TIMEDEL and then
treated as though it covers the full readout cadence.

There is a separate, unresolved scalar inconsistency. EXPOSU01 ONTIME is
47192.7177839279 s and LIVETIME 47148.1782433158 s; the latter's card describes
good time multiplied by FC0, but their ratio is approximately 0.999056, not
0.936444. This means that card comment, scalar and exposure width cannot all be
substituted as the same numerical duty correction without explaining the
processing history. Stale/inherited metadata is a possible explanation, **not
established here**. Do not repair this by rescaling the arrays to either scalar.

The pn EVENTS header additionally supplies LIVETI01–12 (about 39.9–40.8 ks).
Its global LIVETIME=40781.9239473082 s is explicitly the **central CCD** live
time and equals LIVETI04. This is not a camera-average versus per-CCD difference:
even the matched EXPOSU04 LIVETIME=47319.6904707273 s differs. Match the exact
CCD first, then compare processing/exposure definitions.

For MOS, global LIVETIME likewise equals the central CCD's LIVETI01. EXPOSU01
LIVETIME is 49228.1517583842 s (MOS1) or 49399.133352041 s (MOS2), versus EVENTS
LIVETI01 of 48809.9667203426 s or 48977.7934885025 s. SETDEADT=1 records that
the dead-time option was applied. These are not evidence to multiply every
frame by another generic correction. Central CCD FRMTIME is 900 ms; outer CCDs
use 2700 ms, and their actual TIMEDEL column remains unread.

## Candidate formula, with explicit conditions

For CCD c and frame f, let `t_f` be its verified central timestamp, `F_f` its
nominal wall-frame duration, `delta_f` its effective integration duration before
the retained fractional loss `q_f`. Define

    C_f = [t_f - F_f/2, t_f + F_f/2)
    E_cj = sum_f delta_f * q_f
                 * duration(C_f intersect bin_j intersect GTI_c) / F_f.

This is a **candidate coarse-bin allocation**, not a frozen exact SAS clone.
For full accepted frames the weight is simply `delta_f*q_f` seconds. pn
TIMEDEL is the candidate delta and FRACEXP the candidate q; no second FC0.
For MOS, establish whether exported TIMEDEL and FRACEXP partition the already
applied losses this way before assigning them those meanings. Do not reuse a
pn correction constant for MOS.

Fractional boundary allocation assumes uniform effective exposure within a
frame; photon timestamp assignment/randomization and asymmetric live/readout
segments can matter at cut boundaries. The final counts protocol must either
justify that approximation with a bounded boundary-error diagnostic or use a
consistent whole-frame selection/count convention. Do not call it exact merely
because the chosen 200-s bins are much longer than frames. Missing frames and
GTI gaps are not inferred by stretching an interval to the next timestamp.

If `E_cj = k_c * L_cj` with constant unknown k_c for the fixed region, use
`L_cj/(L_cj+L_cref)` in the conditional counts diagnostic: k_c cancels. This
does not excuse unknown changes in onboard loss, telemetry, discarded columns
or aperture footprint. Different source/background CCDs require separate
exposure ratios; a single camera-wide scalar is insufficient.

## Concrete C2 diagnostics and remaining decision

Without EVENTS access, summarize per CCD: finite/sorted timestamps, repeated
and missing-frame patterns, actual width/fraction ranges, valid GTI union,
nominal-frame boundary consistency and all interval overlaps. Preserve zero
fractions and failed intervals, not just accepted means. Compute labelled
diagnostic totals `sum(delta)`, `sum(delta*q)` and their explicitly defined
GTI-restricted versions; compare them separately with EXPOSU ONTIME/LIVETIME
and the **matching EVENTS ONTIMEnn/LIVETInn**. Agreement is a consistency check,
not proof of unique semantics; disagreement must remain visible.

C2 can identify which interpretation is numerically compatible, but must not
select a formula merely because it reproduces one scalar. Before a count freeze,
the exact remaining calibration question is: **does the retained per-frame q
encode all time-variable losses relevant to this CCD/aperture, and which
already-applied MOS losses reside in q versus delta?** If the metadata and
direct output semantics do not settle it, obtain that narrow algorithm/source
evidence next. Reading every HKAUX/DLIMAP value, installing SAS, or applying a
global renormalization is not an automatic remedy.

Until resolved, report exposure diagnostics rather than calibrated relative
rates. Counts-control feasibility remains plausible; exposure validity,
background stability, source recovery and discovery remain unestablished.

## Parent follow-up: exported columns and a documentation warning

The parent separately inspected `emevents`' description and output specification.
Its PUT_TI section explicitly creates the exposure table: TIME is frame centre,
TIMEDEL excludes frame-transfer time, and effective fractions account for
cosmic-ray dead time using the frame CRRATIO. This supplies the missing MOS
partition evidence: candidate full-frame weight is TIMEDEL times FRACEXP,
without another transfer or generic cosmic-ray factor. The output specification
names these three columns and their roles. The pages describe emevents 8.9.2;
retained header history identifies 8.8. This is documentary support to check
against C2, not a replay of that older binary or proof of calibration accuracy.
[emevents PUT_TI description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emevents/node3.html),
[exposure output specification](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/emevents/node8.html).

An accessible SAS-21 `epexposure` manual describes FC0 in TIMEDEL, FC1/FC2 in
FRACEXP, bad-frame losses through GTIs, and a separate exposure-constant
chopper factor. Crucially, its abstract explicitly warns that section 3 is
outdated and mentions subsequent column removal, DLIMAP handling and time
randomization. Thus its detailed historical loss inventory must not be sold
as a complete current PPS specification. It supports the proposed weight
diagnostic but leaves spatially varying losses and exact exported behavior
to the retained metadata and further narrowly targeted checks. Several ESA
subsection/index and HEASARC versioned HTML requests failed; this PDF was the
successful fallback, not a different scientific input.
[SAS-21 epexposure manual, abstract and sections 3, 7–9](https://heasarc.gsfc.nasa.gov/docs/xmm/sas/help/epexposure.pdf).

A regex-only version extraction from the existing header reports found pn
epexposure-0.16/epframes-8.116, MOS emevents-8.8/emframes-5.11 and all event
products evlistcomb-4.20. No arbitrary history cards or coordinates were printed.
No arrays were decoded in this follow-up. The C2 protocol remains a diagnostic
comparison, not a decision to normalize a mismatch or claim validated exposure.

Further refinement from the exposure-map task: `eexpmap` explicitly states that
pn TIMEDEL incorporates mode-dependent out-of-time-event corrections and that
the map's OOTCORR flag prevents applying them twice. Therefore the measured
0.936444 ratio must not be labelled solely as electronic readout dead time.
This offers a documented distinction relevant to the differing scalar ratios,
not proof of their exact processing history. The OOTCORR/OOTFRAC description is
for the exposure-map output; presence in our event files is not assumed.
[eexpmap effective-frame-time and OOT treatment](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).
