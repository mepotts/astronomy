# ATTTSR time reference and unresolved quality counters

September 12, 2026. Documentation-only follow-up to the parent's C3d header
inspection. No attitude arrays, product requests or coordinates accessed.
Three primary URL opens were attempted: two succeeded; the `atthkgen` algorithm
page returned a retrieval error. No alternative download was performed.

## Time reference: documented candidate, not a recovered header value

The official handbook defines the XMM time system as **TT** and its reference
as **MJD 50814.0**, corresponding to the start of 1998 in TT. Its quoted UTC
offset examples are dated and must not be reused for the 2021 observation.
[XMM time-system definition](https://heasarc.gsfc.nasa.gov/docs/xmm/sas/dfhb/timescale.html).

`atthkgen` obtains observation start/end times through the OAL, then samples
attitude on that observation time axis at its configured timestep. This
supports a mission-time interpretation of its TIME column, but the description
does not explicitly specify missing-keyword defaults or provide an independent
time-reference record for our exact exported file.
[atthkgen description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/node3.html).

The parent reports the retained product is ATTHK with the documented ten
double columns, produced by atthkgen 1.22.1 in SAS 21; neither header contains
TIMESYS, TIMEZERO, MJDREF or TIMEREF. The inspected current task description
is 1.22.2. Therefore **TT/MJD 50814.0 is a documentary candidate, not a keyword
verified in C3d**. Do not silently manufacture TIMEZERO=0 or claim a verified
local/barycentric reference from absence alone.

A later separately frozen metadata-value stage could explicitly adopt and test
the documented mission-time convention: compare attitude TIME range and cadence
with independent C1 event/GTI time ranges, preserving every mismatch and gap.
Range compatibility would support that interpretation, not prove all clock
details. No fitted timestamp offset, first-sample subtraction, UTC leap-second
shortcut or alignment to photon peaks is justified. Such a convention/validation
choice has not been adopted or executed here.

## Quality: the three reported totals cannot all be literal set counts

The parent reports NATT=NGAHF=NGOM=51975 and NGAHFOM=0. If these meant counts
of good AHF rows, good OM rows and their intersection in the same 51975-row
universe, inclusion-exclusion would require

    joint_good >= good_AHF + good_OM - total_rows = 51975,

not zero. Thus the literal common-row interpretation is internally inconsistent;
it does **not** establish all-good rows, no common overlap, or a particular
instrumental failure. Different bookkeeping semantics or an output bug are
possibilities, not explanations verified by the pages inspected.

The documented operational validity representation is NULL attitude triplets
and NULL affected offsets. The task also marks an attitude request bad when
the closest relevant input sample is more than 20 seconds away. Those rules
concern sample quality, not a guaranteed continuous-motion envelope.
[Documented sampling/quality rules](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/node3.html).

Next metadata inspection must count actual finite/NULL AHF and OM triplets,
partial triplets and joint-valid rows separately, then compare with these
headers without forcing agreement. AHF-only diagnostics may still be possible
under an explicit prospective choice even if OM quality is unresolved; do not
require or invent agreement between both streams. Missing/gapped samples and
between-sample motion remain separate limitations.

No additional source in this bounded check resolved the count-key construction
or exact omitted-keyword semantics. C3d's successful retention/header status
remains intact; **time-reference interpretation and row-level quality remain
unverified**, not a discovery or geometry-validation result.
