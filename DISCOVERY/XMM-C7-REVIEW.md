# Independent C7 one-map runtime review

September 12, 2026. **Scoped GO for parent freeze and separate execution
authorization: one MOS2 map, ten unchanged static-sign regions.** No actual
map/attitude/source-list/event values, product content hashes or network
requests were used for this review.

## Review and synthetic verification

Read the complete C7 adapter, all tests, prospective protocol and bound MOS2
header-compatibility note. Revisited the relevant frozen C5 functions and
their final hash rather than relying on a prefreeze implementation. All
**12 current C7 synthetic/metadata-only tests** independently passed, as did
root-invoked Ruff 0.16.5 on source/tests. The actual metadata-binding smoke
passed under a product-open prohibition; it did not run C6 product replay or
decode a map. The inherited numerical core is unchanged from its independent
[numerical review](XMM-MAP-SUPPORT-REVIEW.md).

Tests exercise isolated original/current globals, one-map byte limits and
endianness, untouched padding, forbidden second-map artifacts, one-map status
correlations, full worker/parent/replay accounting, missing-region/nonzero-exit
rejection, caught worker and parent truncation, prelaunch STOP, read-only
replay mismatch accounting, coordinate-free receipts and ten-region synthetic
evaluation with the real core at both fixed subdivisions. The mocked parent
launch checks the actual C7 source path and 60-second worker argument.

Two additional independent inline probes passed:

- A synthetic destination-copy failure after the first decoded chunk retains
  **41,472 returned and decoded bytes** in both local and total accounting.
- Successful validation of initial and completed one-map states does not
  mutate the caller's record or append a persisted second slot.

These probes are not additional committed unittest methods. An initial
decoder-order concern came from stale prefreeze C5 text and was withdrawn:
the actual frozen `5e7af10b...5a05b` implementation already increments decoded
counters before copying decoded values into the destination. No decoder
change was needed or made for that concern.

## Composition and the virtual validation slot

The adapter loads a new C5 module instance and rebinds its paths, source,
protocol, prior evidence, manifest, accounting callbacks and map tuple in
that instance only. A separately loaded original retains its two-map tuple,
original source and 3,359,232-byte total. C7's actual tuple contains only the
C6 MOS2 map, its total cap is 1,679,616 bytes, and its child entry point is the
C7 file. Function code reused from C5 dispatches through those isolated
current globals; this is not invocation of the archived two-map run.

The temporary second slot exists **only inside validation of a saved state**.
It is unattempted with zero accounting, permitting the frozen two-row validator
to check the one real row without weakening caps or status correlations.
The narrowed total cap still applies to the entire temporary record. That
slot is not measured, written, returned in the ledger, added to a region
denominator or printed in replay accounting. The C7 ledger rejects any real
map-2 artifact before numerical work. Success and failure tests confirm one
persisted map and ten planned regions, not a fictitious second camera.

The inherited worker's selected loop therefore reads only MOS2. C6 verification
is header/hash replay; C5's outcome is hash-only evidence. No C5 numerical
replay or earlier pn/MOS1 image read is requested by this adapter. Imports of
frozen helpers do not themselves invoke their workers or prior science runs.

## Inputs, WCS and scientific alignment

The one image is bound by C6 outcome/product/header hashes, exact observation,
EMOS2/S002 identity, 648-square float32 schema and offset 25,920. A complete
pass is 1,679,616 bytes in 41 reads of at most 41,472 bytes. Per-pass accounting
is distinct for worker, parent recomputation and every later replay. Caught
partial validation survives in terminal counters; hard interruption without
a receipt is unknown, not zero. Failure-artifact replay is not numerical
validation, and failed numerical replay reports its additional pass without
rewriting old evidence.

The immutable C5 header/WCS construction and centre conversion remain in use:
primary CDELT-only degree TAN, explicit verified legacy FK5/J2000 label
conversion, `fix=False`, and fixed ICRS-convention offsets transformed to FK5.
There is no map-dependent astrometric fit, aperture change or choice between
the required 4/8 grids. The newly added compatibility-note dependency resolves
the initial missing decision-document binding before execution. The original
counts-definition and C5/C6 source/test/outcome dependencies remain bound.

All five labels, the 20-arcsecond circle and 60–90-arcsecond annulus are kept.
Negative-control regions are not asserted source-free, and no contamination
mask or FLAG-matched exposure correction is added. The compatibility decision
permits only the unmasked accumulated-map sign diagnostic, not a calibrated
per-bin live-exposure denominator. Proximity remains pixel-centre/sampled-border
distance, not guaranteed clearance; even wholly positive sampling is not
continuous coverage. Existing C5 pn/MOS1 outcomes remain part of the scientific
evidence and are not erased by this one-camera continuation.

## Final reviewed anchors

| Artifact | SHA-256 |
| --- | --- |
| C7 source | `52eec788c55df46c3ba884c42b73e2fb8a573bdb2a2ae188f90b0b51b3007778` |
| C7 tests | `9f63df22dd072452b00fb0e90cea49b365fd516d3739387c9d36837b530a1176` |
| C7 protocol | `0ce140a2d42a5f820b29ada831174b30242cf3d395e1caaeb34591cc49df15b5` |
| MOS2 compatibility decision | `edfb5068c498826077c85580fa22b5c34e5249a749244e9202d4522848f87f43` |

No remaining blocking finding was identified in this scoped prospective
implementation. The parent must preserve the exact bound bytes in the freeze
before execution, including previously pinned CRLF-sensitive definitions.
This review makes no Git or frozen-source changes and does not itself issue
execution approval. The strongest permitted result is static MOS2 support
approximation, not exposure, multi-camera burst recovery or discovery.
