# C9 result: recorded photons, not calibrated recovery

Executed 2026-09-13 after exact-byte runtime freeze **e4c069d**. Worker,
parent numerical verification and one separate root numerical replay all pass
`RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY`. This is the first EVENTS-value
measurement of the retained known control, observation0884250101. No unknown
field, new product acquisition, catalogue submission or discovery claim.

## Fixed measurement and complete denominator

The [prospective contract](XMM-C9-2026-09-12.md) and
[counts plan](XMM-RECORDED-COUNTS-PLAN-2026-09-12.md) remain unchanged.
All three cameras, five fixed centres, 20arcsec circles, unmasked60-90arcsec
annuli and all254 half-open200second bins are retained, including every zero.
Absolute bin edges are in the [run binding](XMM-C9-2026-09-12-data/run-start.json).
The tables below sum the full grid, not selected episodes or peak bins.

| Camera | Input rows | Accepted | Energy rejection | Pattern rejection | Flag rejection |
| --- | ---: | ---: | ---: | ---: | ---: |
| pn | 2694388 | 1455044 | 576021 | 306704 | 356619 |
| MOS1 | 273441 | 160218 | 82379 | 717 | 30127 |
| MOS2 | 356129 | 195030 | 119134 | 1174 | 40791 |

Rejections are the predeclared ordered, disjoint ledger, not independent cut
failure frequencies. Invalid selected fields, unsupported CCDs and outside
inclusive camera-header interval each reject zero rows in every camera. All
nine selected fields have zero declared-null and zero nonfinite counts. All
1810292 accepted events lie inside the complete bin grid; outside-grid count
is zero. These statements do not establish GTI validity or calibrated quality.

Full-grid region totals, fixed order published/north/east/south/west:

| Camera / shape | Published | North120 | East120 | South120 | West120 |
| --- | ---: | ---: | ---: | ---: | ---: |
| pn circle | 777 | 939 | 972 | 338 | 996 |
| pn annulus | 7924 | 8889 | 9493 | 9651 | 9527 |
| MOS1 circle | 0 | 0 | 78 | 0 | 0 |
| MOS1 annulus | 0 | 643 | 1053 | 0 | 0 |
| MOS2 circle | 146 | 146 | 93 | 0 | 115 |
| MOS2 annulus | 899 | 1539 | 1017 | 133 | 1341 |

All full histogram arrays and per-CCD totals are retained in
[pn](XMM-C9-2026-09-12-data/camera-1-result.json),
[MOS1](XMM-C9-2026-09-12-data/camera-2-result.json) and
[MOS2](XMM-C9-2026-09-12-data/camera-3-result.json). Counts across different
regions need not form an exclusive partition. Circle and annulus of the same
centre are disjoint. No area subtraction, exposure normalization or ranking
of bins was performed.

Source-circle accepted events are assigned to pnCCD5 and MOS2CCD7; no accepted
MOS1 source-circle event. pn region memberships span CCD4/5, MOS1 memberships
CCD5, and MOS2 memberships CCD6/7. These are aggregate event assignments, not
detector-validity certificates or evidence that zero-count sky is inactive.

## Reproducibility, resource and access accounting

Commands, each executed once in this stage:

```
dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/XMM-C9-2026-09-12-data/inspect_counts.py run
dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/XMM-C9-2026-09-12-data/inspect_counts.py replay
```

The run includes worker and parent passes; explicit replay adds the third.
Each pass completes334chunks/3323958rows, returns142652840 opaque row bytes
and decodes93070824 selected bytes. Across exactly three known numerical
passes: **427958520 row bytes and279212472 decoded selected bytes**. All
camera states COMPLETE/COMPLETED; no partial chunk remains. No fourth pass is
authorized for postrun audit or integration.

Separately each pass hashes246890880 whole-product bytes, and structural replay
reads1569600/184320/236160 header bytes for pn/MOS1/MOS2. These opaque and
structural reads are not additional interpreted photon fields. No prior map,
source-list or attitude numerical stage was replayed.

Worker exit0, parent assessment complete. Worker peak78946304 bytes; parent
peak79577088 bytes, under536870912 monitored limit. The worker deadline remained
120s and separate parent/replay cooperative deadlines120s; no timeout or cap
increase. Final678JSON files total709146 bytes, under4194304 cap. Outcome's
pre-outcome resource total634626 bytes is intentionally a different boundary.
No new products or decoded per-event timestamps/pixels/sky positions persisted.

| Artifact | SHA256 |
| --- | --- |
| Runtime | bb8d6d8c8a737e2d8be11d6f489091a1d0f7453fd320ad80a761709d56c81d03 |
| Tests | 9a2cc126dc6e7a48a256f77e99eac5f761651a4680f08269f8874911f3592bff |
| Protocol | 9b805b3fb46b3914550bd9d993302631f2c36d429a9f99cf8a4713bbaa308c4d |
| Counts plan | 141a6cbb7d987c1d2179391e50af9a9c306b21347275856696bf2ccb7e397812 |
| Run binding | d5c85c7046ab15e5d479341a0fed9d4ccd0dfa64fc939f972be756fcf14cf77a |
| Outcome | f27b9848b470cf8adf693f3a106e8b88d85c802f6e1effff67667773eb20d109 |
| pn result | 2965dc30e333fd3dcba8a3a354047d88399000c076ca0cec25465239ec411aa7 |
| MOS1 result | 06aa216a86dd4ed41f7e75130b0628a433963ad8c3064433aad9d14d0e46e8d2 |
| MOS2 result | f0084736361b7ffafe2d46fefecedbc81c8987191591c7ae3ae00fc0017e3959 |

## Scientific decision

The bounded recorded-count experiment is complete. It does not pass the
stronger recovery gate. No source mask, GTI/live-exposure integration,
background subtraction, significance, detector-artifact veto, period or
episode search was performed. Parent/replay agreement establishes computational
reproducibility, not an independent astronomical detection.

[C8](XMM-C8-RESULT-2026-09-12.md) retains north/east/west aperture contacts and
all five annulus contacts. Two usable negative apertures are still not
established. [C5](XMM-C5-RESULT-2026-09-12.md) and
[C7](XMM-C7-RESULT-2026-09-12.md) static-map findings remain unmodified and do
not provide per-bin exposure. MOS1 zero counts do not identify the physical
cause of its zero map support. No attractive curve waives these limitations.

Retain the first control as a completed descriptive diagnostic with stronger
recovery unestablished. Adopt the previously documented
[RXJ1301 next-control metadata preflight](XMM-NEXT-CONTROL-DECISION-2026-09-12.md)
as a separately frozen experiment, not a replacement for this result. No new
field's photons or exact product availability have yet been inspected.

[Independent postrun audit](XMM-C9-POSTRUN-REVIEW.md) passes16dependencies,
1355 overlapping artifact-hash references,334chunk pairs, exact aggregate
arithmetic/privacy schemas and resource closure without any product opens or
additional numerical pass. Root read the complete audit and checked its totals
against the saved camera summaries.
