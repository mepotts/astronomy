# Next experiment: fixed recorded-event histograms, not calibrated recovery

Prospective implementation decision after C8 and before any EVENTS values.
This is not a runtime freeze or photon execution. Preserve the original
[recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md) unchanged: its exposure,
two usable negative regions, source exclusion and defect requirements remain
unmet. The following limited diagnostic cannot satisfy them by relabelling.

## Question and immutable scope

What recorded counts fall in the published20arcsec aperture and the four fixed
negative apertures, separately for pn, MOS1 and MOS2, on the already chosen
200-second grid? Also retain the full, **unmasked**60–90arcsec annuli as raw
diagnostics. C8 contacts must accompany every interpretation; these are not
clean backgrounds. No subtraction, area/exposure scaling, significance, peak
selection, episode detection or new source search is part of this experiment.

Use only the three retained C1 expanded EVENTS tables and pinned header reports.
No acquisition, source-list reread, map/attitude/GTI/EXPOSU/BADPIX arrays,
SAS installation or extra observation. C8's aggregate contact result is enough
to label the unresolved backgrounds; no source mask is silently approximated.

| Camera | Expanded file bytes | Expanded SHA-256 | EVENTS rows / stride / offset |
| --- | ---: | --- | --- |
| pn | 219988800 | `7fc15ff164943acadcea741457ccd2fba529883677e3d7693d35d01136097570` | 2694388 /45 /63360 |
| MOS1 | 11707200 | `7703a0c2475225b02bc44134eab033cf39ba11cc28a4a1843d0105b47afc294a` | 273441 /34 /40320 |
| MOS2 | 15194880 | `203a7b798558ab6c895a0fa0cdecef9c3936d81578549fb235a43c65beb26150` | 356129 /34 /40320 |

These numbers were independently rechecked from C1 receipt/header JSON only,
not from photon occupancy. Runtime must verify exact products/receipts/headers
and bind the reviewed scalar decoder and selected X/Y geometry components.

## Fixed time grid and selections

Metadata: TIME seconds, TT, MJDREF50814, TIMEZERO0, TIMEREF LOCAL,
TASSIGN SATELLITE, CLOCKAPPtrue in all three EVENTS headers. No new barycentric
correction or inference of absolute timing accuracy. Header ranges:

| Camera | TSTART | TSTOP |
| --- | ---: | ---: |
| pn | 738530124.914825 | 738579196.505283 |
| MOS1 | 738528580.207049 | 738578603.890584 |
| MOS2 | 738528600.951524 | 738578795.595291 |

Anchor A=pn TSTART. Derive edges once as `A + 200*k` for integer k=-8..246,
giving254 half-open bins. This covers all three header intervals and preserves
MOS pre-pn time without reanchoring the grid. Persist every absolute edge and
all254 bins for every camera and region, including zeros. Zero recorded counts
never imply exposure; header intersection duration may be labelled only
`header_interval_overlap_seconds`, not GTI or live exposure. Do not manufacture
missing-camera availability. No temporal hypothesis tests are performed.

Apply a declared disjoint rejection ledger in this order:

1. Any null/nonfinite selected field under the reviewed decoder's `row_valid`.
2. CCDNR not in the retained camera's header-supported set: pn1..12;
   MOS1{1,2,4,5,7}; MOS2{1..7}.
3. TIME outside the inclusive camera-header interval [TSTART,TSTOP].
4. Not strictly200<PI<12000; numeric MOS PI uses the already documented C1
   calibrated-eV interpretation, not a newly fitted conversion.
5. PATTERN>4 for pn or>12 for MOS.
6. FLAG !=0, preserving its signed-J interpretation.

Do not call these events GTI-filtered, EXOD-equivalent or defect-free. In
particular, the published EXOD central-MOS-partial-mode removal is **not**
implemented by these generic cuts. All rejected rows remain counted, including
per-field null/nonfinite diagnostics that may overlap. Unexpected schema or
geometry failure is STOP, not another adjustable rejection category.

Geometric membership uses unchanged X/Y, FITS origin1 and the reviewed selected
TAN adapter, with all null positions removed before projection. Centres retain
the exact C5 function/AST and ICRS-to-FK5 convention. Literal inclusive20arcsec
circles and60–90arcsec annuli. No recentering, fitted offset or constant-radius
pixel approximation. Keep all five fixed regions even when C8/map warnings
make them unavailable for the stronger recovery. A row may belong to different
centres' regions; do not demand their sum equal total events.

## Minimal synthetic implementation and outputs

A pure per-chunk counting component should accept the decoder result plus
geometry membership, verified camera/time configuration and fixed edges; no I/O.
It validates lengths, masks, integer domains and the fixed configuration before
using them. It returns integer254x5 circle and annulus increments plus the
disjoint rejection ledger, accepted-inside/outside-grid counts and aggregate
per-CCD region counts. The wrapper accumulates checked integers, without
retaining event arrays. Empty chunks and all-rejected chunks remain defined.
Avoid any adaptive detection threshold or top-bin summary in this component.

Synthetic tests must cover every energy/pattern/time boundary, invalid and
unknown CCDs, all missingness, half-open adjacent bin edges, unsorted times,
duplicate times, masks/shape/dtype corruption, overlapping regions, overflow
guards, and split-chunk invariance. Exact integer totals must agree with an
independent scalar-loop oracle. No real-event performance benchmark before a
separate runtime freeze; repeated synthetic chunks can size the budget.

Runtime streams at most10000 complete rows/chunk from unbuffered handles.
Per complete pass:3,323,958rows;142,652,840returned opaque row bytes;
93,070,824decoded selected-field bytes. Nine selected fields total28bytes/row;
full-row reads physically include unselected bytes, which are not interpreted.
Every parent verification/replay is another separately accounted pass. Capture
short-read bytes, decoder partial-conversion state and geometry partial state;
hard-kill work without a receipt remains unknown. No zero-filled replacement.

Before execution, finalize a bounded wrapper, safe aggregate JSON schema,
dependency manifest, process-tree deadline and memory/output caps from synthetic
tests; obtain independent review and commit exact runtime/test/protocol bytes.
The wrapper owns durable exclusive camera/chunk progression and failure
receipts, separate full-product hash/header I/O and numerical comparison.
No public source IDs, absolute sky coordinates, photon positions/times or
detector-pixel lists. Fixed histogram edges/counts and aggregate CCD labels are
allowed. Do not equate a successful receipt with scientific recovery.

## Stop after answering this narrow question

Strongest label: `RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY`.
Report all cameras/regions/bins, not only an attractive curve. A visible burst
pattern is a known-control diagnostic, not new astrophysics. If counts are
promising, decide a separate exposure/defect/control experiment explicitly;
do not optimize this observation indefinitely or waive the failed negative
requirements to open an unknown-source scan. If counts do not show the expected
pattern, preserve that result without moving apertures or shifting the grid.
