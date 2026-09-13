# RXJ M4 independent review

**Current disposition: scoped preflight GO for parent freeze and separately
authorized offline execution, at the final hashes below.** The earlier HOLD
checkpoints are retained as review history. No actual archive or payload has
been read by this reviewer during preflight.

## Design checkpoint — 2026-09-13

**HOLD for implementation and synthetic review; this is not execution GO.**
The adopted offline, fixed-member metadata adjudication is appropriately
separate from M3. No material objection to that bounded design was found.
The runtime, parser, final protocol and adverse fixtures remain to be reviewed.

The reviewer read the complete adopted M3-NEXT note and the safe M3 outcome,
HTTP, transport and worker receipts. No archive, HTML payload, trailer, product
or science array was opened; no request or prior-stage replay was performed.
Header/trailer facts below are inherited recorded evidence, not a fresh
independent interpretation of the private bytes.

Current evidence anchors (SHA256):

- M3-NEXT: `2034068945bb923710b7c0df081580f0fcbd53cd9d5975d5cf0c03e4e6de8267`.
- M3 outcome: `1a897ff9dbf74f0b88c7428b2dbd63dc16944036191256374204056d3b3f5678`.
- M3 HTTP: `6b2e62f84d8412f00e8ca60f73bcbc400f1009010f21556c381a5fb0cf5924f0`.
- M3 transport: `ce59925f72d7675fd155eced7c5b6d0c1465258254c468bedf2046b7d249b2a0`.

The receipts preserve one successful HTTP transport of 1,044,480 bytes followed
by `STOP_TAR_HTML_SIZE`, worker return code 1 and completed parent assessment.
They do not establish validated HTML metadata. The four documented roles are
EP, OB, RG and OM, not four proven duplicate versions. The adopted four payload
lengths sum to 1,033,100 bytes per complete selected pass. Their distinct roles
must not be reduced to choosing the smallest or most convenient document.

The original archive hash, four exact header checksums/hashes and fixed layout,
two zero terminator blocks and quarantined nonzero suffix must be checked
before selected payload interpretation. That exception is observation-specific;
it does not pass M3 or establish that arbitrary trailing bytes are harmless.

## Required implementation review

- Establish observation identity from explicit labelled metadata, not a matching
  filename or stray observation digits in arbitrary text or links. Missing,
  duplicate and contradictory evidence needs distinct accounting.
- Restrict interpretation and serialization to declared metadata contexts and
  validated field types. A familiar column word alone must not admit a source
  science table. Do not emit raw cells, unknown labels, contact details,
  coordinates, fluxes, variability, arbitrary URLs or parser exception text.
- Account for all four roles and every recognized exposure row, including
  duplicates and missing fields/units. Neither a particular exposure roster,
  literal footer nor a table count from another observation is a validity gate.
- Treat encoding declarations and absent/conflicting evidence explicitly. The
  parser must not load resources, render, execute HTML or follow links.
- Retain failed/skipped slots and separate returned selected bytes, decoding
  and completed semantic work. Full selected reads are exactly 1,033,100 bytes
  per pass; opaque hashing and header/tail reads are additional labelled I/O.
- Verify one worker and one parent pass, with later replay explicitly counted;
  include failure and post-comparison mismatch accounting. Review the 30-second,
  256-MiB and JSON-budget/reserve enforcement without claiming an unimplemented
  operating-system memory guarantee.

Synthetic adverse fixtures should cover identity decoys/conflicts, metadata
versus source-table context, duplicate/missing exposure values, privacy canaries,
malformed/nested HTML and encoding evidence, plus runtime partial failures,
artifact tampering, one-shot behavior and exact pass accounting. Final review
will record which cases were actually tested rather than treating this list as
completed work.

The strongest prospective result is bounded, attributed metadata with explicit
missingness. It is not archive-wide validity, inventory completeness, product
availability, calibrated exposure, source recovery or a discovery.

## Parser checkpoint — synthetic only

The reviewer read the complete parser and tests, then the pre-freeze correction.
Initial review reproduced a duplicate-column defect: two distinct validated
Mode values generated a flag but silently retained only the final value. The
author corrected this before any real payload interpretation. Duplicate fields
now retain every safe candidate and give the canonical field `AMBIGUOUS` with
no selected value; duplicate identity columns are consequently unjoinable.

Independent reruns passed all **14 author tests** and Ruff 0.16.5. An additional
**16 inline synthetic cases** passed: five identity decoys (comment, link,
contact, style and script), contradictory labelled identities, entity-decoded
identity, duplicate exposure IDs, three duplicate mode candidates including an
unknown privacy canary, source/contact/URL canaries across all four roles,
complete role accounting, nested-table contradictory identity and a short row.
These probes used generated strings only, not retained HTML or an archive.

Parser SHA256:
`6cd64cc7f465780df8e883e9d46e05e52fde5dde706e0d4bedaf9f227ae827ef`.
Author-test SHA256:
`bd72321dc9edce735998d0115281edfc37ca556aea53cb88f5e4d4e7d3455bc3`.

No remaining concrete blocker was found in this bounded parser. It identifies
exposure tables only from recognized instrument and exposure-ID headers;
unsupported layouts remain `NOT_IDENTIFIED`, not proof of no exposures. The
finite label/unit vocabulary may leave fields missing or unrecognized. An
ASCII-only document without encoding declarations remains provisional; failed
or conflicting decoding does not invent text. Cross-role aliases join exposure
keys only. Processing fields remain attributed to their role rather than
being assumed to describe the same processing event. Product basenames are
observed references, not fetched products or a complete inventory.

## Runtime review in progress

The initial runtime draft had an unsafe replay reporting gap: terminal status
was printed without consistency validation, truthy non-boolean assessment
flags were accepted, and unassessed failure replay lacked binding and safe
receipt-schema checks. This was reported directly to the runtime author and
parent while the implementation was still explicitly a draft. The author is
adding receipt/state validation and tests. No runtime execution GO is given
at this checkpoint; the final fixes and synthetic harness remain to be read
and independently exercised.

## Final preflight acceptance — 2026-09-13

The complete final runtime, protocol and runtime tests were independently read.
The parser's final small delta was also read: each exposure group now explicitly
distinguishes `CROSS_ROLE` from `SINGLE_ROLE_UNMATCHED` and separately reports
missing duration/start/stop label units. Equal unknown units do not become known
units. These reporting changes do not add a new metadata interpretation rule.

The draft replay findings are resolved. Exact terminal scalar types, allowed
status/error fields, digest shape, marker/result ordering, per-slot/pass byte
closure and outcome consistency are checked. A failure-artifact replay remains
explicitly unassessed metadata, not a substitute for a successful repeated parse.
Successful parent and replay paths recompute all four records and comparison;
they do not trust just the stored metadata digest. Partial and completed
additional-pass accounting is preserved when comparisons subsequently fail.

Independent checks:

- **10 runtime tests and 14 parser tests passed**, plus Ruff 0.16.5 for both
  sources and both test files. Runtime fixtures use a complete generated TAR
  with the actual fixed sizes/offsets, all four generated HTML slices and 400
  exposure rows, real archive/header checks, parser and Windows peak sampler.
  The child-launch helper is mocked to invoke the worker locally in that suite;
  this is not a claim of an independent new process-tree-kill test.
- **Eight additional inline runtime adverse cases passed** using only generated
  archives: a late outcome mismatch after a full 1,033,100-byte additional pass;
  mismatched trailer; a checksum-invalid header with its fixture hash updated;
  actual stream wrappers returning seven bytes or raising before a buffer on
  the second slot; a simulated interrupted worker without completion; a rehashed
  boolean/int worker-marker mutation; and a nested unexpected artifact. Header/
  trailer failures read no selected payload. Both read failures retain the
  second slot and continue the other roles; a raised read stays unknown rather
  than becoming an invented count. Failure replay leaves artifacts unchanged.
- Metadata-only binding passed in the author fixture with TAR opening blocked.
  The reviewed artifact allowlist rejects private TAR/HTML copies; the stage
  ignore rules also cover them. Binding records their privacy/line-ending files.

One operational issue was found and documented without a source change: running
unittest from inside the stage causes its `inspect.py` to shadow the Python
standard-library module. The repository-root `unittest discover` invocation in
the final protocol passes; the failed stage-directory invocation was not a
failed scientific execution. The final protocol change documents that command
only, superseding its earlier `409d838a...` hash.

Final SHA256 anchors:

| Artifact | SHA256 |
| --- | --- |
| M4 runtime | `c9c987d5207d3f65da80b4c875df9815b6dcb0632c72b3296f8398a1c3de2529` |
| M4 runtime tests | `c0493369dac0bdd86c0e386f153be61efbd56ab187d21a8670d33664f849fabd` |
| M4 protocol | `bbbde7fa9a235c00688754761e280cfda55b3522296390c80c3f6f752645c274` |
| Metadata parser | `bca91205c9983986f7bfac2b596a03d8da7d92af8b343fba70e3d82a31148f0d` |
| Parser tests | `6f26a135c792f442c20a3e31bdbadbe30e399464e165a0bdf54039709e8d64a1` |
| Stage attributes | `12965522a4195898e35ac66fe6042197159a35cd80d2250364318efd36b1207e` |
| Stage ignore rules | `a72467eca601f80066f6b4b0779900414da2615c40e68c50eb1a7e79a97723c5` |

No remaining material preflight blocker was found for this precise offline
stage. Freeze must preserve these bytes and the pinned dependencies. Runtime
success still means four accounted, possibly incomplete metadata parses: it is
not four verified identities, exposure eligibility, complete inventory or a
discovery. M3's original STOP and the quarantined trailer remain unchanged.
The parent/replay deadlines are cooperative, and 256 MiB is a monitored lifetime
peak acceptance cap, not an allocation quota. Every complete pass adds exactly
1,033,100 selected bytes plus the separately declared opaque/header/tail work;
no subsequent pass or request is authorized merely by this review.
