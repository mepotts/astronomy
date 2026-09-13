# Discovery continuation: close the TESS localization test, check XMM feasibility

**No new discovery. This pass made scientific progress, not a dated wait.**
The three-agent team separated numerical implementation, independent experiment
review and next-route primary-source research; the parent integrated the work and
executed the frozen real-data experiment. Publication, registry submissions and
scientific correspondence remain separately gated.

## Completed measurement

[TESS M2p](../tess-short-eclipses/M2p-RESULT-2026-09-12.md) has now run all
1,920 planned real-noise injection trials across three mandatory published controls.
Two fields fail localization stress rules; the cleaner field completes only the
specified limited diagnostics, with uncalibrated nominal ellipses. The method
cannot be scaled to unknown crowded sources on this evidence. Failed conditions
are preserved, not rewritten, discarded or replaced by the successful field.

All three primary catalogue profile rankings favor the known target. That is
useful recovery evidence, but injected nearby eclipses demonstrate why it is not
sufficient source-identification validation. Further TESS work needs materially
new calibration evidence and independent negatives, not more fine-tuning on
these same three observations. The current method is parked for scientific
reasons, not until a calendar date.

## Adopted next direction

The [XMM identifier-level investigation](XMM-EXOD-ELIGIBILITY-2026-09-12.md)
verified three public observations taken after the March 2025 EXOD paper and
absent from its pinned 15,105-ID list. The parent independently
checked all three retained response hashes, exact string IDs, observing/public
dates, list absence and the two published controls' list membership. The final
three-response provenance snapshot is 168,544 bytes; it contains no photon
arrays or source coordinates.

This supports a concrete archive increment relative to that paper, **not proof
that no later researcher has searched it**. It also corrects the weaker generic
5XMM-release idea: a new catalogue release does not imply newly observed photons,
and attempted-minus-successful counts do not identify unsearched exposures.

Adopt **C0b-1: the two-request, 256-KiB known-control metadata check** as the next
bounded operation. First inspect observed archive product/exposure schema, then
freeze the exact query for published control observation `0884250101` using
verified join keys. Determine public supported-camera modes, required event/source
products and advertised sizes before choosing a photon-recovery protocol.
Use the existing hard process-tree deadline helper; retain complete responses,
hashes and missing/unsupported/error outcomes. No replacement control or silent
extension of the request/sample budget.

The [first C0b-1 schema request](XMM-C0b1-SCHEMA-2026-09-12.md) has now executed:
one HTTP-200 response, 2,034 bytes. Its frozen validator stops on a mismatch
between Python string sorting and the archive's quoted column-name order. The
failure is preserved without changing the validator or retrying. Read-only
inspection also establishes that the exposed product table lacks advertised file
sizes. This does not prove absent products or an unusable telescope archive.
The second query was not executed: a product-name-only response could not meet
the size/completeness gate. Next metadata work needs a documented official
manifest, directory listing or appropriately bounded size request, under a new
explicit contract; there is no reason to repair the sort check merely to call
this incomplete schema a pass.

The HTTP receipt also contains an anonymous session cookie. Its frozen original
remains local and ignored; a separate public derivative omits the cookie. No
scientific input or failed outcome was overwritten for this privacy treatment.

The larger five-observation product check in the research note remains a later
scope decision, not an already launched query. No XMM science products, SAS
installation, calibration deployment, remote processing or unknown-source
measurements are authorized by the metadata result alone. A separately reviewed
control-recovery and empirical-negative experiment must establish scientific and
local-runtime feasibility first. If product sizes or modes cannot be established,
stop with that concrete evidence rather than acquiring a bulk bundle speculatively.

## Unchanged operations and authority

The separately reviewed [C0c2 directory amendment](XMM-C0c2-RESULT-2026-09-12.md)
has now executed: 319808 bytes and 2193 complete parsed entries. The earlier
C0c request stopped at 262144 bytes and remains frozen. Exact pn/MOS event and
EPIC source-list filenames are now observed; displayed sizes remain rounded,
not acquisition-budget evidence. Next is a bounded exact-size/summary metadata
batch for these same control inputs. The counts-recovery design is still a
draft with mode, time, exposure and screening blockers, not a launched experiment.

[C0d](XMM-C0d-RESULT-2026-09-12.md) has since completed four successful
size-only HEADs (126982449 compressed bytes total) and one fully retained
summary GET that failed its frozen closing-tag rule. That STOP is unchanged.
Separate offline interpretation establishes the selected exposure modes and
nominal time overlap, not live exposure. The coordinate-bearing raw summary
is retained locally and ignored; public notes omit those values.

Adopt the separately reviewed [C1 contract](XMM-C1-2026-09-12.md) for exactly
four known-control product downloads and headers-only structural inspection.
Freeze implementation/tests/review before execution. No photon selection or
unknown search follows from transport success alone. The bounded
[later-work check](XMM-LATER-WORK-2026-09-12.md) leaves precise later-search
coverage unknown; it does not warrant abandoning the control experiment or
claiming novelty.

[C1 has now executed](XMM-C1-RESULT-2026-09-12.md): all four fixed known-control
files retained, gzip/header checks and parent replay passed, 247141440 expanded
bytes and 68190208-byte worker peak. No scientific arrays were interpreted.
The actual headers confirm selected camera/exposure modes and shared local
satellite TT references. Per-CCD exposure, GTI and bad-pixel metadata are present,
but their values and aperture coverage remain unvalidated. Next is a bounded
ancillary-metadata inspection followed by the separately frozen counts test;
neither acquisition success nor this continuation authorizes an unknown scan.

[C2 has now executed](XMM-C2-RESULT-2026-09-12.md) after freeze commit `61d7bee`:
all 24 EXPOSU and 24 STDGTI tables summarized, exact replay, no declared
quality flags and no photons. The real frame weights closely approximate
EVENTS per-CCD live times without a fitted scale, but do not validate finite
frame allocation or spatial/temporal aperture stability. Adopt the
[minimal geometry continuation](XMM-GEOMETRY-NEXT-2026-09-12.md) next: three
already indexed camera exposure maps and the observation attitude product,
starting with exact-size metadata and separately frozen acquisition/header
checks. No automatic unknown scan, aperture optimization or threshold changes.
Synthetic timing primitives are reviewed; they have not counted real photons.

[C3 stopped](XMM-C3-RESULT-2026-09-12.md) on HTTP 404 for the exact indexed MOS2
map URL. Two successful HEADs establish pn/MOS1 sizes; the attitude HEAD and
all GETs were unattempted. Preserve the STOP and do not infer the cause or
permanent absence. Adopt [C3b](XMM-C3b-2026-09-12.md) as a separate prospective
one-HEAD/three-GET continuation using the accepted pn/MOS1 receipts. The original
counts design already permits pn plus one eligible MOS. Keep all geometry,
negative-control, simultaneous-coverage and multiplicity rules unchanged.
The [frame-boundary proposal](XMM-FRAME-BOUNDARIES-2026-09-12.md) offers
conservative exposure bounds with explicit support assumptions; it has not
been applied to real frames. [FLAG zero](XMM-SCREENING-DECISION-2026-09-12.md)
is adopted prospectively, pending map-mask compatibility. No photon run yet.

[C3b also stopped](XMM-C3b-RESULT-2026-09-12.md): the unattempted attitude HEAD
returned 404 at its exact indexed URL, so no conditional GET was sent. The
prior C3 STOP and two successful HEADs remain unchanged. Investigate a documented
official alternate individual-PPS source before proposing further transport;
no blind method/URL retry, dropped pointing requirement or unknown scan.
Both failures are archive-response evidence, not a scientific rejection of
the published control. Useful photon-blind temporal-method work remains.

Bounded research now identifies a documented
[ESA XSA AIO alternate](XMM-ALTERNATE-PPS-SOURCE-2026-09-12.md): its official
client uses HEAD and supports narrow PPS selectors. No product request was
made. Next, separately freeze and review one ATTTSR-filtered metadata request;
successful metadata would still need a distinct bounded package contract before
download. Availability, sole-member identity and compatibility remain unknown.

Adopt the separately reviewed [C3c one-HEAD contract](XMM-C3c-2026-09-12.md)
for this exact known-control product selection. Freeze its code/tests/review
before execution, preserve the metadata outcome, and do not infer authorization
for a body request from successful advertised metadata alone. In parallel,
[frame-bound numerical helpers](XMM-FRAME-BOUNDS-IMPLEMENTATION.md) now implement
the conservative exposure construction and worst-case counting diagnostic.
Their synthetic checks do not validate the physical frame-support assumptions
or authorize a real-frame/photon run.

[C3c has executed](XMM-C3c-RESULT-2026-09-12.md): ESA advertises HTTP 200,
image/fits and the exact requested attitude filename, but supplies no length.
Preserve its STOP_SIZE_METADATA and zero body reads. Adopt a separate C3d
one-GET contract with a local 2-MiB transfer ceiling and 32-MiB expansion cap,
identity/format/header validation and no retry. An absent Content-Length need
not block an independently byte-limited transfer; it cannot become an invented
size or a retroactive C3c pass. Review/freeze precedes that request.

[C3d has now executed](XMM-C3d-RESULT-2026-09-12.md) after freeze `a6c7911`:
one successful capped GET, gzip integrity, 151713 raw / 4173120 expanded bytes,
two structurally checked HDUs and parent replay. Actual ATTHK matches the
ten-column documented schema, but header time-reference and joint-quality
interpretation remain unresolved. Next is a separately frozen local attitude
value diagnostic and the two outstanding pn/MOS1 map downloads using earlier
size receipts. Retain original camera missingness, region/test denominator,
geometry and control-recovery gates. No actual photons or discovery yet.

[C3e](XMM-C3e-RESULT-2026-09-12.md) now retains both pn/MOS1 maps:
779072 compressed / 3432960 expanded bytes, two exact-validator GETs,
header/hash replay and independent postrun audit. No map pixels yet.
[C4](XMM-C4-RESULT-2026-09-12.md) then measured all 51975 attitude rows:
all columns finite, one-second cadence throughout, all camera header ranges
bracketed, maximum sampled direction displacement 1.704147 arcsec. The
joint-good header counter remains inconsistent with finite rows; no continuous
motion or clock-certification claim follows. Map/FLAG/GTI compatibility and
fixed-region geometry are next, then the frozen published-control photon test.
No unknown-source scan, photon count or discovery has occurred.

[Map compatibility adjudication](XMM-MAP-COMPATIBILITY-2026-09-12.md) finds
the MOS1 map's FLAG masks are broader than zero and its referenced GTIs are
not retained in either the map or event product. The pn combined map lacks
surviving DSS selections. Adopt a separate static support/proximity diagnostic
next; do not use these maps as matched per-bin live exposures. This is a
practical route to geometry evidence without full ODF reprocessing. A later
descriptive known-control count screen may be useful even if calibrated
recovery remains incomplete, but needs its own explicit prospective contract;
it cannot be called a pass of the unchanged stronger recovery draft.

PR20 merged as `dd0e0295d8dba2492f4e7878e74a9ee9ea6c1496` after all eleven
CI jobs passed. Local C3e header replay and C4 binding/receipt checks also pass
after merge; the latter did not add a fourth attitude decoding pass. The
[C5 draft](XMM-C5-2026-09-12.md) now specifies a fixed 4/8-subdivision static
support experiment. Its pure numerical core has 14 synthetic tests and an
[independent arithmetic review](XMM-MAP-SUPPORT-REVIEW.md); the bounded reader
and full execution review are still pending. No actual map pixels yet.
The [counter follow-up](XMM-ATTITUDE-COUNTERS-2026-09-12.md) does not resolve
the joint-counter semantics or establish independent OM measurements. It
corrects the interpretive offset reference to median, not nominal, pointing;
all frozen numerical results remain unchanged.

[ITF](ITF-NOTIFICATIONS-2026-09-12.md) still has its daily archive publisher and
existing-queue watch, not a fresh automated discovery search. No dedicated
SMS/email delivery was configured or tested. Existing daily/weekly follow-ups
were not changed. A future external alert needs an approved recipient/channel
and a verified test delivery; queue movements must not be described as discoveries.

Repository commits, tested pushes and merges remain authorized. Scientific
publication/submission and private-coordinate disclosure remain human decisions.
The overall discovery goal remains active; finishing this measured failure does
not satisfy it, and useful next work is available now.

## Latest measured update: C5 and missing MOS support

[C5 completed](XMM-C5-RESULT-2026-09-12.md) after freeze9cef69c: all20 fixed
regions, both4/8 quadratures, worker/parent and one numerical replay agree.
Three known decoded passes total10077696 bytes. Independent receipt/aggregate
audit added no fourth decode. pn source circle is entirely positive sampled;
MOS1 source circle and annulus entirely zero sampled. This does not diagnose
no exposure at every time, but cannot supply the required confirming camera.
The west pn fine grid also detects a zero missed by coarse sampling despite
positive unsupported-pixel-centre margin: no certified clean-aperture claim.

Adopt the [C6 one-product ESA request](XMM-C6-2026-09-12.md) using verified
instrument/exposure/subset selectors. Preserve original HEASARC404 and all C5
results. The prospective source is implemented with17 synthetic/receipt tests;
review and committed freeze precede the single bounded GET. Positive2D image
shape under the32MiB cap is allowed for acquisition, not guessed648-square
compatibility. No map values in C6. Source-list geometry and event decoder
metadata proposals are available, unexecuted. Do not waive pn-plus-MOS recovery.

[C6 executed](XMM-C6-RESULT-2026-09-12.md) after d54ec04: one ESA GET HTTP200,
410115 gzip/1707840 expanded bytes, exact648-square MOS2S002 primary, successful
offline replay. Final JSON37762 bytes. [Header compatibility](XMM-MOS2-MAP-COMPATIBILITY-2026-09-12.md)
supports only the same limited sign diagnostic. C7 will read oneMOS2map at the
unchanged10regions and both4/8 subdivisions; no changes to pn/MOS1 evidence.
The [partial-window note](XMM-PARTIAL-WINDOW-INTERPRETATION-2026-09-12.md)
correctly identifies MOS W3 as Large Window; it does not prove the source's
detector location or explain zero maps. If MOS2 also lacks support, a separately
frozen raw recorded-event screen can provide evidence without first inventing
calibrated rates or claiming the stronger recovery passed.

PR21 merged2026-09-13T02:57:03Z as619324d457bbff32353d41e4614e37ab6999f1e3
after all11CI jobs passed. C6 header-only replay and C5 binding/artifact/accounting
checks pass after merge; no extra C5 numerical pass. C7 one-map composition has
12synthetic tests, unchanged core and centre construction, and independent
review underway before a new committed freeze. A synthetic-only event-row
decoder is being built in parallel; no actual photons have been read.

[C7 now executed](XMM-C7-RESULT-2026-09-12.md) after6c7d456: MOS2 sourcecircle
positive at all4/8samples, sourceannulus65.1064%positive nominally. North/west
MOS2circles/annuli positive sampled; eastpartial,southcirclezero. The worker,
parent and one numerical replay pass,3knownpasses5038848bytes,totalJSON42284.
This resolves the specific lack of affirmative second-camera static sampling,
not calibrated simultaneous exposure or the stronger recovery gate. Stop map
endpoint exploration for this question. Next is the [7852-byte source geometry
screen](XMM-SOURCE-GEOMETRY-IMPLEMENTATION-PLAN.md), then a separately frozen
descriptive photon test using the synthetic-only eventdecoder now under review.
Raw count reporting need not wait indefinitely for full exposure calibration,
but cannot be labelled calibrated rates, significance or discovery.

PR22 merged2026-09-13T03:08:48Z as0b15c38e4435ac1f4906cdba0b9c9adc23f9deeb
after all11CI jobs passed. C7 postmerge binding/receipt/ledger checks pass with
no fourth numerical pass. The [EVENTS scalar decoder](XMM-EVENT-ROWS-IMPLEMENTATION.md)
is now integrated with16synthetic tests and independent514-row oracle/failure
review. No actual event arrays yet. Sourcegeometry pure-core and exact7852-byte
selected-span reader are the next implementation components; their synthetic
tests/review do not authorize real source-list values without a bounded wrapper,
fixed manifest, protocol and pre-execution freeze. Keep that distinction explicit.

The pure `xmm_source_geometry.summarize(columns, centres)` core now passes
13synthetic tests and [independent review](XMM-SOURCE-GEOMETRY-CORE-REVIEW.md),
including1500contact-count comparisons over100synthetic151-row catalogues.
It preserves corrected-position association versus original-position geometry,
complete identity/coordinate conditions before unique exemption, unchanged
region labels and all invalid-row denominators. It reports contacts only,
never source-wing boundaries, mask areas or clean sky. Exact selected-span
reader and bounded C8 wrapper remain to be finalized before real catalogue work.

Current local branch `codex/xmm-source-geometry-sep12`, core checkpoint014faa4,
based on mergedPR22. [C8 prospective protocol](XMM-C8-2026-09-12.md) is now
written but not frozen or executed. The root rederived all266 column widths
and9 selected offsets from the pinned header JSON: exactly1131bytes/row,
52selectedbytes/row,151rows. Repeated unselected strings include10A/12A/7A;
the reader must not assume all columns scalar. Exact extent units are
`image pixels`. PRIMARY carries observation/EPIC/FK5/equinox identity;
SRCLIST carries POSCOROKtrue/REFCATUSNO, not its own frame cards.
Selected-span reader and C8 wrapper tests are in progress in separate agent
work areas; no real source-list values, photons, masks or new map values.
Finalize/read/review those components and protocol, freeze exact bytes, then
execute C8 once. Earlier C7 map work is complete and must not be rerun casually.

Selected-span `xmm_source_rows` now passes11synthetic tests, rootRuff and
[independent reader review](XMM-SOURCE-ROWS-REVIEW.md), including755short-read
positions and5storage-failure probes. Source33acfedec1328cac1517abc703ee9644c653330648630edb8d96b6235562a927;
tests4fd4b13b5698c2d40a476d390b780b47cc8e899c2ad6fe39024d6cff9f0ef272.
Final lint repair changes buffered-stream rejection toTypeError, no accepted
scientific input change. Root reread the repair and reran tests/lint. C8 wrapper
is present but still under development/review: preserve replay-failure additional
pass counters, reject unexpected/nested artifacts and enforce exact151row/10region
closure. No C8 run marker or real selected-column decoding yet.

C8 now has a scoped [independent preflight GO](XMM-C8-REVIEW.md), with all16
wrapper tests,112 root XMM-core tests, scoped Ruff and repository verifier
passing. Final source bd76ab70fb36ca2ea9c350401ab36991baa8fd30b3bf160c546c788a536ad0e3,
tests 0bd5ba02add739318553de6029147e79d625b8dcde8c5180b3674c9088370733,
protocol 9b4a86517fdafcccf16c1004808a87a457c4c05b63b51f6e9da5163675330c14.
This checkpoint freezes the reviewed runtime before the separately executed
local selected-column screen under the user's ongoing execution authority.
No source-list values have yet been interpreted. CI now includes C8.
The [EVENTS geometry plan](XMM-EVENT-GEOMETRY-IMPLEMENTATION-PLAN.md) establishes
unchanged X/Y with FITS origin1; its pure implementation and independent review
are proceeding with synthetic data only.

[C8 executed](XMM-C8-RESULT-2026-09-12.md) after860115a: one unique corrected
association, original offset2.8441692831480774arcsec; no other centres within20
in any aperture.30arcsec disk contacts in published/north/east/south/west are
0/1/1/0/2 for apertures and1/2/1/3/5 for annuli. All151 coordinate/ID rows valid;
145extent errors nonfinite retained. Worker+parent+one numerical replay PASS,
three known passes23556selectedbytes; outcome82cd6df3d673c86059494e9d38a3bfd1312ee9ce8b19301873309dfc995ad16e.
No extra array pass for postrun review or integration. The stronger recovery
has not established two usable negatives; do not silently waive that gate.
Proceed to separately frozen descriptive photon counts, not calibrated recovery.

PR23 merged2026-09-13T03:37:45Z as26df8a40e7ba824a845a6bda605b9d8270510162
after all11CI jobs passed on256815b8c559d9485975f19791be438a1afec208,
run34735850315. Postmerge C8 binding/artifact/ledger checks pass under a
products-open guard: no fourth numerical pass. Current branch
`codex/xmm-recorded-counts-sep12`. [Recorded-counts plan](XMM-RECORDED-COUNTS-PLAN-2026-09-12.md)
fixes254 half-open200second bins anchored at pnTSTART, all three cameras and
five circle/unmasked-annulus pairs, no rates/significance/recovery claim.
Pure EVENTS geometry, pure count core and bounded C9 wrapper are under
implementation/review, with synthetic data only. Root's actual header-only
geometry smoke caught overbroad TS/DP keyword rejection (TSTART/TSTOP/DPSCORRF);
that prefreeze implementation needs repair and regression before use. No real
photons have yet been read; no runtime freeze or C9 execution is authorized
by the implementation plan alone.

The geometry prefix finding is repaired before freeze: indexed TS/DP families
remain rejected, harmless TSTART/TSTOP/DPSCORRF accepted.13synthetic tests,
Ruff and all3pinned header-only smoke checks pass; root and independent reviewer
confirmed no product/value access. [Review](XMM-EVENT-GEOMETRY-REVIEW.md) records
the failed initial compatibility assumption and the final source
8adcb227f61c2f86855652ada4d66b5f677e84caa0cb16b5dd182be3081de9da,
tests e1e1d41daffec25ada03fd155f958082c62f09c62cef4cdd83ee2cd8fa14f538.
[C9 prospective contract](XMM-C9-2026-09-12.md) is written, not a runtime freeze:
120sworker/120scooperativeparent,512MiBmonitored,4MiBJSON/256KiBreserve,
334chunks per fullpass. Pure counter tests and independent review are underway;
bounded runtime needs syntheticfull-size fit/failure tests and review before
actual photon access. No stronger scientific gate has changed.

Pure recorded counter now passes13synthetic tests and
[independent review](XMM-RECORDED-COUNTS-REVIEW.md):2913synthetic rows through
the real decoder, all255edges and neighboring floats, scalar-loop cut/bin/CCD
oracle and1/37row chunk invariance. Root reread full source/tests/review and
reran13tests/Ruff. Root also checked all3actual HEADER-ONLY schema row/stride/
selected-null profiles against counter constants; PASS, no photons.
Counter source5094b15b735619c5de25f7c6fe7a4f5207f82c8c7bc64cac6565678f8975090c;
tests5e5b1bc15646ab12c856582142cad6331019ff9e23455a961761b3e4d374df9c.
Geometry/plan checkpoint3a731bd is not a C9 runtime freeze. C9 author is building
the three-camera334chunk wrapper and synthetic tests; reviewer is assigned
its independent review next. Keep every executed C1–C8 artifact immutable.

Bounded [next-control comparison](XMM-NEXT-CONTROL-DECISION-2026-09-12.md)
now prioritizes RXJ1301.9+2747/0851180501 metadata preflight after C9 terminal
result, over the shorter/off-axis0886121001 stress test. Root read the complete
decision and primary papers: published pnfull-frame/thin, threecamera eruptions
and~1200s morphology fit200s diagnostic better. This is a conditional next
metadata choice, not verified current availability, calibrated recovery or
permission to weaken negatives. No archive/product request for the newcontrol.

C9 initial wrapper is on disk but **unfrozen/not execution-ready**; no run,
worker or camera markers and no real photons. Root/reviewer independently
passed its3camera metadata-only manifest under products-open prohibition.
Prefreeze findings require exact per-chunk progress/digest comparison in parent,
complete component semantics, completed-prefix/current byte reconciliation,
C1/C8test dependency pins and stage-file allowlist. Author is applying these
and preparing wrapper tests. Final cameraOK/lastchunkSTOP must fail before
numerical work. Reviewer owns `XMM-C9-REVIEW.md` when candidate is ready.

Root [pure-kernel resource check](XMM-C9-RESOURCE-PREFLIGHT.md) completes all
334chunks/3323958synthetic rows through decoder+geometry+counter in1.218s,
peak74665984bytes,0actualproductbytes. It explicitly does not cover disk,
producthash/header,receipt serialization/closure or parent replay; fullwrapper
synthetic budget/failure tests remain required.138root coretests pass. Current
committed code checkpoints3a731bd/4cffe9c; next-control research19a0710. Do not
freeze or run C9 until finalsource/tests/protocol read, independent review,
fullwrapper benchmark and exactindexbyte checks are complete. CI still needs
its C9wrappertest/lint entry. No extra C8 numerical pass is authorized by audit.
