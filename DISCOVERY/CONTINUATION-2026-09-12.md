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

Final C9 candidate now has [independent scoped GO](XMM-C9-REVIEW.md), 19 wrapper
tests, all332 XMM tests, scoped Ruff and repository verification PASS. CI includes
C9. Root's [final-source physical synthetic fit](XMM-C9-RESOURCE-PREFLIGHT.md)
passes actual subprocess/parent/replay in8.859s/2.891s,709463JSONbytes and under
75MB monitored peaks; zero actual science-product opens. Actual metadata-only
binding separately passes all16dependencies under a products-open prohibition.
Runtime bb8d6d8c8a737e2d8be11d6f489091a1d0f7453fd320ad80a761709d56c81d03;
tests9a2cc126dc6e7a48a256f77e99eac5f761651a4680f08269f8874911f3592bff.
Root adopts the reviewed bounded execution under the user's ongoing authority,
after an exact-byte commit freeze. Execute C9 once, then one numerical replay;
retain all fixed histograms and failure accounting, with no implicit fourth
pass. Strongest label remains RECORDED_COUNTS_UNCALIBRATED_NOT_RECOVERY.

[C9 executed](XMM-C9-RESULT-2026-09-12.md) after runtimefreeze e4c069d onSep13.
Worker0,parentcomplete and one root numerical replay PASS; exactly three known
passes427958520rowbytes/279212472decodedbytes. All334chunks/3cameras complete,
no partial state. Published circle777pn/0MOS1/146MOS2; every fixed histogram
retained, no top-bin/episode/rate/significance search. Final678JSON709146bytes;
worker78946304,parent79577088 peakbytes. Outcome
f27b9848b470cf8adf693f3a106e8b88d85c802f6e1effff67667773eb20d109.
No fourth numerical pass for audit/integration. Stronger recovery remains
unestablished; first-control descriptive diagnostic complete. Next bounded
task is separately frozen RXJ1301/0851180501 metadata-only preflight, no new
field photons. Independent reviewer is auditing C9 receipts/aggregate closure.

Independent [C9 postrun audit](XMM-C9-POSTRUN-REVIEW.md) now PASS:16deps,
1355overlappingartifactreferences,334pairs, allhistogram/CCD/rejection closure,
resource/privacy checks. Root read the full report. No product opens or fourth
pass. C9 result and dashboard updated; tested integration is next.

C9 PR24 head991625230fed06ff341944f302b1b373476f7095 initially passes10of11
CI jobs but discovery-pilots fails all19C9tests at STOP_MEMORY_RUNTIME on
Linux (run34737875548). The frozen tests call the real Windows-only sampler.
No merge proceeded. Move that unchanged suite to an explicit Windows CI job,
retain Linux core tests/lint, and require all12jobs green. No executed source,
test, protocol, dependency or receipt is changed; no safety sampler bypass.

PR24 merged2026-09-13T04:31:24Z as1afd75d9f1b4eb1ace47463cd7455bb06f96b09d
after all12checks passed on1e7b451cf8fd0bb569720b47c0b915848ce9c879.
On switching through localmain to new `codex/xmm-rxj-control-sep13`, Git's
checkout converted root prospective C9protocol/counts-plan/next-control
decision LF bytes to CRLF. Postmerge binding correctly STOPPED before photons.
Verified all three differed only in line endings, then restored their exact
committed bytes and pinned explicitLF attributes. No scientific text, runtime,
tests or receipts changed. C9 postmerge binding/artifact/ledger now PASS under
products-open prohibition, no fourth numerical pass.

[RXJ M0](XMM-RXJ-M0-2026-09-13.md) now has
[independent scoped GO](XMM-RXJ-M0-REVIEW.md),17synthetic tests/Ruff and root
4dependency metadata-only binding PASS after restoration. Runtime
fe664f73447eae02345358b03c6c7754628e7d9f240028c8720ed2786b462a38;
tests963e082830d97ce2c743d2003799c2d846e0ead7139ea670a7f5ba8df0e9fdb6;
protocolb864f9daee136bb27da7d0a94bcd095fdc86c6ea92636ac337f4aab3a1209e18.
Root read full source/tests/protocol/review and adopts the oneanonymousGET,
64KiB+1,30s bounded index request under ongoing execution authority, only
after exact-byte commit freeze. No linked request or product acquisition.
The [ancillary-first calibration decision](XMM-CALIBRATION-NEXT-DECISION-2026-09-13.md)
is adopted for later separately bounded work; no gate waiver or photon search.

[RXJ M0 executed](XMM-RXJ-M0-RESULT-2026-09-13.md) once after6512188.
HTTP404, STOP_HTTP_STATUS beforebodyreading; noindex.html, nullbodyrecord,
worker1,parentassessmentcomplete. Root one offline replay PASS_OFFLINE_REPLAY
STOP.5JSON2518bytes; outcome57e0e1ec8a149a6e90a1e1847f089c1a4d3529480f1416704f3ac964f37d82c7.
No retry, PPS/HEAD/products or targetsubstitution. The19byte Content-Length is
declared, not read. Do not infer observation unavailable from this route404.
Independent reviewer is auditing savedreceipts; research agent is identifying
one documented same-observation structuredmetadata alternative, no query yet.

Independent RXJ M0 postaudit now PASS5artifactreferences/4deps/5JSON2518bytes,
exact safeHTTP/workerSTOP schema and unchangedstagehashes, no request or replay.
Root read the full appended audit. Tests17/Ruff/repositoryverifier PASS again
afterexecution. M0 is closed, not discovery-blocked or proof of missingdata.

Root adopts [next ESA structured query](XMM-RXJ-M0-NEXT-2026-09-13.md) after
reading the full note, three primarydocs and retained verifiedschema:
SELECT obsid,filename FROM xsa.data_product WHERE obsid = '0851180501'.
One prospective1MiB/30sanonymousTAPGET, no newtarget/products/automaticretry.
Next implementation must bind the schema and M0 lineage, validate safe scalar
rows, retain duplicatecounts and avoid claiming completeness without evidence.
No actual query for RXJ has been made. Exact runtime/protocol/tests and review
still need freezing before execution; later joint-region calibration remains.

PR25 merged2026-09-13T04:42:35Z as5650df46df8db506943f134e902a2bafea563895
after all12CIchecks passed on dac736f9e6bda51ce54248b65a3aeab0821020b1.
Current branch `codex/xmm-rxj-products-sep13`. Postmerge rootC9 binding/artifact/
ledger and M0 binding/HTTP/STOP closure PASS underproduct/request tripwires;
no extra numerical pass or network request. ExplicitLF attrs preserveplanhashes.
Author is preparing M1's bounded ESAproduct-name runtime; no query yet.

Read-only calibration-environment check: owner-context WSL lists Ubuntu and
docker-desktop. In Ubuntu's login-shell PATH, command-v found no sas,evselect,
epiclccorr or cifbuild; /opt was empty and /usr/local/bin held cagent/kubectl.
This is limited command/standard-location inventory, not an exhaustive absence
proof or installation requirement. No software/calibration data installed and
no calibration task executed. The sandbox's initial WSL listing was access
denied; authorized owner-context enumeration succeeded.

[M1 prospective protocol](XMM-RXJ-M1-2026-09-13.md) and
[independent review](XMM-RXJ-M1-REVIEW.md) now complete:11tests/Ruff PASS,
12dependency metadata-only binding/JSONroundtrip PASS; root also verified all
dependency bytes against their committed versions. Root read full finalsource,
tests/protocol/review. Initial seven-literal adapter assumption repaired to
six before any request, C1controls rejected, M0NEXT restored to committedLF
b4358d05d0d1cd4cf945867514b9c5bd3c6bd859dfe17069b5b52d86a8842e14.
ExplicitLF attrs cover both newboundrootdocs. Runtime
953d28ef3c079faf11a660bdae8c7c32cd1d8e0259c72bde9c0f794d30b5fb91;
tests0885a3b200f4a4f1bd8281b963e19362b2bce41e995ebc7aafc0d79df5ae57ae;
protocol64fe04e56f8dac954a1394ab65934fd8eb4d88797d0b4701fe645d0a2c009fc4.
Root adopts one1MiB+1/30sESAmetadataGET after exact-bytecommitfreeze under
ongoing authority. No products/secondcountquery/unknownsource search.
Maximumlabel RETURNED_PRODUCT_NAME_RECORDS_ONLY_COMPLETENESS_UNKNOWN.

[M1 executed](XMM-RXJ-M1-RESULT-2026-09-13.md) afterb787a9e:oneESAHTTP200,
application/json363bytes, STOP_COLUMN_SCHEMA at obsidarraysize'10' vsrequired'*'.
Worker1,parentcomplete,one rootoffline replayPASSSTOP. Noacceptedrowsbyfrozen
parser. Separate rootmanualinspectionfinds2rows:0851180501.tar.gz and*/*,
notindividualPPSnames; wildcardwouldalsofailbasenamegate. No parseramendment,
retry/countquery/products/bundledownload.5JSON4608bytes, raw363; outcome
159ee0322ae964ec20e4f79471e927dc7dc93a08adcb0a1f8b2b751ca843b384.
Reviewer is auditing savedreceipts only. Research next is documented tightly
filtered summary-metadata selector for sameobs, not another namequery/parserloop.

M1 independent postrun audit now PASS: 12 dependencies, six artifact references,
five JSON receipts (4,608 bytes), retained body (363 bytes), exact HTTP/STOP
closure and unchanged stage hashes. No additional request, product access or
replay. Root read the full appended review and next-step research note.

Root adopts the separately bounded [summary-selector decision](XMM-RXJ-M1-NEXT-2026-09-13.md)
after checking the primary stable API and client implementation. This is a
prospective raw-HTML-only request, not yet implemented/frozen/executed; package
media stop before body access. Offline labelled observation identity and all
exposure-table rows must be adjudicated before a later narrow PPS decision.
The [FRB contingency](NEXT-DISCOVERY-CONTINGENCY-2026-09-13.md) remains research
only; it does not displace XMM or authorize bulk radio data acquisition.

PR26 merged 2026-09-13T05:04:07Z as
8bc30ffb967f5db494d5e1e4bb2068896e0f2542 after all 12 CI checks passed on
8132b26a648c18f753e6e4e11b196aa5942bc4f7. Local main fast-forwarded; next branch
is `codex/xmm-rxj-summary-sep13`. Postmerge M0/M1 binding, HTTP and artifact
closure pass; C9 binding/artifact closure also passes under product/network
guards. Root's first ad-hoc C9 comparison mistakenly included outcome.json
itself; inspected the executed source's explicit self-exclusion and used that
same rule. No stage or receipt changed, no request or numerical replay ran.

This goal continuation is progress from the merged M1 result, not a blocked
wait. Root adopts [M2 raw summary acquisition](XMM-RXJ-M2-2026-09-13.md) after
full source/tests/protocol/helper and [independent review](XMM-RXJ-M2-REVIEW.md).
11 synthetic tests/Ruff, 12 exact committed dependency bindings and extra
cap/EOF/package fixtures pass. Git confirms private summary.html is ignored;
explicit LF attributes cover all newly bound configuration/protocol files.
Source a4620e9d991761276be1b32a6dc693d4a1846999d368bdddb928ab4ff5df24e6,
tests 12c782baacff8e29b160feb4c197ccf2df335a6403d35623c0c80a322d91d186,
protocol d26c216910fc9c72f9134e439b012f77d6e2acfc09f3df74eec61f560a5e0871.
One anonymous 30-second, 262144+1-byte request may execute after exact-byte
commit freeze. No retries, packages or semantic success are implied.
The [source-specific recovery draft](XMM-RXJ-RECOVERY-DRAFT-2026-09-13.md)
proposes a separately named soft-band experiment, not an executable photon
contract: numerical scientific acceptance and calibration choices remain open.

[M2 executed once](XMM-RXJ-M2-RESULT-2026-09-13.md) after e38e438: HTTP200
application/x-tar, STOP_NOT_HTML before explicit body access, no HTML/EOF,
worker1, parent assessment complete. Root one offline replay PASS STOP.
Independent postrun receipt-only audit passes 12 dependencies, privacy bindings,
five artifact references and five JSON receipts totaling 4,495 bytes. Outcome
f57b43c9a551a7812afed2be845e1dc88b579251ef36f6e1cceceba3cf20705a.
The disposition's retained REJECTED classification does not reveal its discarded
raw value. Next is a separately bounded metadata-only TAR contract for the same
selector, not another raw-HTML attempt or broad observation bundle.

Root adopts [M3 summary-only TAR acquisition](XMM-RXJ-M3-2026-09-13.md) after
full source/tests/helper/protocol and [independent review](XMM-RXJ-M3-REVIEW.md).
10 wrapper plus 11 pure-helper tests/Ruff pass, with 17 independent hand-built
archive cases and runtime mutation/boundary checks. Root also tested full1MiB
success/replay, checked all20 bindings (18 existing committed files plus the
two new helpers), and confirmed both private paths are ignored by Git. The
final wrapper permits zero-byte partial HTML under STOP without repairing it.
Source01564aff6d0873eb7a8bda42ddd408f085e85489e7410b739a1dfd9d40978472;
tests d6ee89793f0b09ad1c53a240423c5c421048d1130f07922e16fab9ca344a8e8b;
protocol230a900079e8220a7a29a5ceeb16a714cdfae684e525f83b783f7a26925a245a.
Execute one request only after exact-byte commit freeze, then one root offline
replay. Any retained package/HTML remains private and unadjudicated; no science
product or unknown-source search is authorized by this metadata stage.

[M3 executed once](XMM-RXJ-M3-RESULT-2026-09-13.md) after56819bc. HTTP200,
application/x-tar, completeEOF1,044,480 bytes retained privately; worker1,
STOP_TAR_HTML_SIZE, parentcomplete, noHTMLcopy. Root one offline replay PASS
STOP; no retry. ArchiveSHAfa3c45838875c61f68e07508d862fc56d32e83f0b39ed3f6b1bef2207b9ccbe2;
outcome1a897ff9dbf74f0b88c7428b2dbd63dc16944036191256374204056d3b3f5678;
sixJSON6295bytes. Separate root header-only diagnosis after verifiedarchivehash
finds4matchingregular headers sized872917/48229/25265/86689 beforefirstzero
at1036288, with8192remainingbytesnotallzero. No payloadsemantics inspected;
capincreasealonewouldnotresolve multiplefiles/tail. Reviewer is auditing only
receipts; research is comparing safeheader roles/provenance and proposing one
boundedoffline-only adjudication of retainedbytes. No newGET or parserrepair.

M3 receipt-only postrun audit passes20bindings/sevenartifactreferences:
six non-archive hashes recomputed, TARhashcross-references/stat only; no extra
archive/helper/replay byreviewer. Root readfullpostrun and
[next offline decision](XMM-RXJ-M3-NEXT-2026-09-13.md). Root independently
verifiedprimaryPPSdefinitions and fourheaderroles EP/OB/RG/OM, headerhashes,
twozero terminatorblocks andsuffixSHAc304f59f74ff1408146b797c68f001e4284f7bb014ae2267d98e60f44de040f9.
The7,168-byte suffix is heterogeneous and uninterpreted, not declared harmless.
Adopt fixed-member offline adjudication of allfourpayloads, total1,033,100 bytes
per complete selected pass, after reviewed code/privacy/resource freeze. No
payloadsemantics or scientific photons yet; no furtherGET is needed here.

PR27 merged2026-09-13T05:40:30Z asdc6a36898f4ffe397fa8b974782f5dc6874b0339
after all12CIchecks passed on51d67a78a9b4221ed6539a7af0e4c2afe1f12310.
Local main fast-forwarded; next branch `codex/xmm-rxj-metadata-offline-sep13`.
Postmerge M0/M1/M2/M3 binding/HTTP/artifact hashes and C9 binding/artifact
closure PASS under network/scientific-product guards. The M3 archive was
opaquely rehashed, not parsed or semantically read; no new replay/request.
Its private ignore rule remains effective. Next meaningful work is the adopted
all-four-member offline adjudication, not another download or a discovery claim.

Root adopts [M4 fixed-member metadata inspection](XMM-RXJ-M4-2026-09-13.md)
after complete source/parser/tests/protocol and [independent review](XMM-RXJ-M4-REVIEW.md).
The 10 runtime and 14 parser tests/Ruff pass; all163 XMM helper tests also pass.
Reviewer adds16 parser and8 runtime adverse cases. Full-size synthetic runtime
fits the30s/256MiB/1MiB JSON envelope. No actual HTML payload was read in preflight.
Freeze runtime c9c987d5207d3f65da80b4c875df9815b6dcb0632c72b3296f8398a1c3de2529,
tests c0493369dac0bdd86c0e386f153be61efbd56ab187d21a8670d33664f849fabd,
protocol bbbde7fa9a235c00688754761e280cfda55b3522296390c80c3f6f752645c274.
Authorize one offline worker plus parent verification and one explicit root
replay after exact-byte commit freeze. Each complete pass selects1,033,100 bytes;
opaque hashing/header/tail I/O is additional. No requests or scientific arrays.
The [geometry-access note](XMM-RXJ-GEOMETRY-ACCESS-NOTE-2026-09-13.md) identifies
the conditional next supported-calibration boundary; it does not request data.
