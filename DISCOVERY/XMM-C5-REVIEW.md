# Independent C5 runtime review

September 12, 2026. **Pre-execution review; final receipt-status correlation
repair pending at the initial checkpoint below.** Numerical acceptance is
separately recorded in [the core review](XMM-MAP-SUPPORT-REVIEW.md).
No actual map pixels, FITS-product hashing, event/attitude/source-list values
or network requests were used for this review.

## Complete source and scientific-contract review

Read the complete C5 `inspect_maps.py`, its tests and the evolving prospective
protocol, including the final frame/WCS/decoder/accounting wording. The
runtime binds the two specific C3e maps and retained outcome/header hashes,
the numerical core/tests, the fixed counts-draft definition, runtime and
configuration. Its isolated inherited helpers preserve prior-stage paths.
Metadata-only binding validates the header geometry without reading map
values; the actual-metadata smoke test guards against opening any product.

The published position matches the bound counts draft. Five fixed centres
are generated without recentering: the adopted ICRS published position and
four spherical 120-arcsecond cardinal offsets, then explicit FK5/J2000
conversion. This input path constructs finite numeric coordinates, addressing
the pure core's nonblocking general-centre-input caveat. The source note did
not independently establish ICRS; that convention remains interpretation
uncertainty, not calibrated astrometry.

Header parsing verifies the exact primary layout, camera/exposure identity,
size/span, degree-unit TAN axes and legacy FK5/equinox2000 frame. It rejects
duplicate semantic keys, scaling/blank/unit changes and unsupported primary
matrix/pole/distortion metadata. A minimal selected primary header explicitly
maps verified `RADECSYS=FK5` to `RADESYS=FK5` and constructs WCS with
`fix=False`. This is declared conversion, not silent repair. Alternate linear
coordinates are not merged into the primary transform. Warnings are handled
without exporting coordinate-bearing text. Absent BUNIT is accepted only for
sign classification; no physical map unit is invented.

Every map retains the same five labels and two region kinds: 20 planned
diagnostics across pn/MOS1. MOS2 remains explicitly unavailable. No source-list
exclusions are applied, and annuli are not thereby certified uncontaminated.
Positive accumulated values are not live exposure or matching FLAG-zero
support. Fixed 4/8 midpoint estimates and pixel-centre/sampled-border
distances retain their deliberately limited numerical interpretations.

## Bounded decoding and independent synthetic checks

Each decoder reads only one approved 648-by-648 scalar float32 payload at
its bound offset. Big-endian values are decoded directly into the array,
including zeros, negative values and nonfinite values without sentinel
reinterpretation. A full map takes 41 requests of at most 41,472 bytes
(16 rows), exactly 1,679,616 returned/decoded bytes. Each complete two-map pass
is 3,359,232 bytes. Changed array identity/span, repeat local accounting or
exhausted total budget stops before an unauthorized request.

Independently reran the initial 15 author tests and Ruff 0.16.5 successfully.
The actual metadata-only binding smoke passed under a product-open tripwire;
prior replay/network workers were not invoked. The synthetic 20-region core
benchmark took approximately 0.484 seconds and serialized 60,087 JSON bytes
in this run. That is a fixture measurement, not guaranteed actual runtime
or peak-memory usage.

An additional independent inline harness ran the full mocked parent `run`,
real worker/decoder and real numerical core on isolated synthetic files and
synthetic sky centres. The normal success path performed worker, parent
assessment and replay as three distinct two-map passes, preserving every
label and byte count. Further synthetic replay mutations rejected promotion
of MOS2 to passed, reduction of the planned denominator, and promotion of
the coordinate-persistence flag. Those mutation replays themselves also
performed additional synthetic passes. No absolute synthetic centre values
appeared in saved aggregate JSON. This inline harness is separate from the
committed author test count.

The reviewed normal replay recomputes all eligible numerical summaries rather
than trusting hashes alone. A nonzero worker return cannot promote numerical
success, first-map failure stops the second map, malformed/interrupted
markers remain unverified, and late monitored-memory STOP survives replay.
The 60-second tree helper and resource caps are inherited and hash-bound;
this review did not launch a real-data worker to test them again.

## Prefreeze failure-accounting repairs

The parent found that a caught parent-recomputation failure originally lost
its locally accumulated extra-pass counters. The author replaced this with
a shared validation state, retained in the terminal outcome. The added
synthetic regression completes the worker, then truncates synthetic map 2
before parent recomputation: the parent retains one full map plus seven
returned bytes, with map 1 completed and map 2 failed.

Follow-on review identified two closure obligations: failure-artifact replay
must validate the new accounting schema/sums/caps, and a mismatch after a
completed replay assessment must still report that newly consumed pass.
Both were implemented before execution. The replay comparison now shares
the exception boundary that emits a safe structured extra-pass receipt;
the new regression checks exact full-pass counts and unchanged files.

The remaining initial-checkpoint finding is a narrow status correlation:
the first schema validator accepted impossible top-level FAILED or
COMPLETED_ELIGIBLE_RECEIPTS labels alongside wholly unattempted rows. This
cannot promote a science PASS on the failure-artifact path, but conflicts
with exact receipt semantics. The author has been asked to correlate final
status with per-map states. A legitimate ATTEMPTED state may include one
completed map and a second unattempted map if a later marker check fails;
it must not be rejected merely because no row is currently ATTEMPTED.

Hard termination without a saved receipt remains different from caught
failure: those actual worker bytes are unknown, not zero. Parent validation
can nevertheless be known unattempted with zero bytes if it never began.
Failure-artifact replay validates receipt structure/integrity, not numerical
truth. Read-only replay cannot amend an old receipt; its new-pass failure
accounting is console output and must be retained by the invoking workflow.

## Initial reviewed anchors and scope

| Artifact at this checkpoint | SHA-256 |
| --- | --- |
| Runtime before final status correlation | `7cf79899bcf1804c81db99042c67c2c79bb307202159ee0654a5e01061f38155` |
| Runtime tests at that checkpoint | `753bf83ac74cefdb97dd156f8262d957c24a56a3084671ab1c5f79e2ca19e116` |
| Final prospective protocol wording | `7bed41ff48eaaee04761f49a924ac3dedd14611d41156b4b1048aa41d416b062` |

No scientific-math or frame-selection blocker was found in the restricted
implementation. Final runtime GO awaits the small status fix and final
synthetic rerun. Such GO will authorize only parent freeze/authorization,
not itself a pixel read or a discovery, continuous-coverage, source-free
background or reliable count-exposure claim.

## Final pre-execution runtime acceptance

The author implemented the final top-level/per-map status correlations and
a compact synthetic mutation regression. The legitimate partial-progress
ATTEMPTED case remains accepted. Independently read the final repair and
regression, and reran **all 18 wrapper tests successfully**. These include
the caught-parent-truncation, failure-accounting tamper and post-assessment
replay mismatch regressions. Ruff 0.16.5 passed on the wrapper, wrapper tests,
unchanged numerical core and numerical tests. The separate 14 numerical-core
tests had already passed in the numerical checkpoint; they were not rerun
merely to change this receipt validator.

**Scoped runtime GO for parent freeze and separate execution authorization.**
No remaining blocking scientific-contract, numeric, privacy, scope or
failure-accounting finding was identified for this specific diagnostic stage.
The frozen result must still be interpreted as static accumulated-map
approximation only; none of the stronger scientific gates above is waived.
This review itself performed no actual pixel read or product hash/replay.

| Final candidate | SHA-256 |
| --- | --- |
| Runtime | `5e7af10b0d8ac5ea8272229efb8a618a392c92d802e6efc401e6b3a54cb5a05b` |
| Runtime tests | `51fa37948ea7fcb9a5fd41d1d232a835f7cf04027a6b9d385752b35aac9c3007` |
| Prospective protocol | `7bed41ff48eaaee04761f49a924ac3dedd14611d41156b4b1048aa41d416b062` |

These final anchors supersede the initial runtime/test checkpoint anchors
without erasing the pre-execution findings or their repairs.

Operational freeze condition: the bound counts-draft definition's current
raw-byte SHA-256 is
`7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e`,
independently rechecked here. The parent identified that Git's prior text
normalization produced different blob bytes and is preserving the existing
CRLF bytes with a narrowly scoped attributes rule. Before execution, the
parent must verify that the staged/committed definition blob reproduces this
same hash. This operational condition preserves the reviewed definition and
pin; it does not authorize changing the source position, science settings or
runtime pin to accommodate a different document. This reviewer made no Git
or definition-file changes.
