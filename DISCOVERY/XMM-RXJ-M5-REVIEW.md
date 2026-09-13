# RXJ M5 independent review

**Current disposition: scoped preflight GO for parent exact-byte freeze and
separately authorized M5 execution at the final hashes below.** Earlier HOLD
checkpoints are retained as review history. No actual request, private product
or retained private header was accessed by this reviewer.

## Initial design checkpoint — 2026-09-13

**HOLD for implementation, final protocol and synthetic tests.** No material
objection was found to the adopted three-product, header-only direction. This
checkpoint is not authority to issue requests or interpret scientific values.

The reviewer read the complete adopted M4-NEXT note, C3d transport source,
relevant C1 expansion/header/resource helpers, the structural reader and old
public header-summary helper. No actual product, private header, archive,
request or prior-stage replay was accessed. Source and public notes only.

M4's incomplete HTML identity does not need retrospective repair to define
three exact requests from its observed EP references. The new FITS primary and
EVENTS identities must authenticate observation 0851180501 and the prescribed
EPN/S001, EMOS1/S002 and EMOS2/S003 camera/exposure mappings. Returned mode/filter
metadata must be reported, including missingness or disagreement with OB, rather
than silently inherited from that provisional summary.

The finite design specifies three exact anonymous GET selectors in fixed order,
stop at first failure, no HEAD, redirect, retry or fallback. Missing response
length is allowed only under the local byte cap; supplied length, exact final
URL and disposition basename must be checked before body work. Magic dispatch
admits raw FITS or complete CRC-checked gzip only, not TAR extraction. Aggregate
remaining budgets, the overflow probe byte, retained partials and skipped slots
need explicit implementation tests. Public receipts must distinguish retained
bytes from received/expanded overflow bytes and uncertain interrupted reads.

Concrete inherited-helper seams were sent to the runtime author:

- C3d's original binding calls `prior_evidence` and a prior-stage replay, and its
  worker is fixed to an old attitude slot. New M5 composition must not call those
  old stage behaviors merely to reuse bounded transport/structure functions.
- The old public header helper whitelists keys but copies arbitrary string
  values and column names. M5's new public derivative needs value validation or
  hashing; a key allowlist alone does not exclude private text or coordinates.
- The structural reader certifies `HEADER_LAYOUT_ONLY`, seeking past declared
  data regions. It does not validate FITS checksums or table payloads, and malformed
  unterminated headers can consume unknown bytes during a bounded scan. The
  final protocol must not promote this to full FITS or scientific validity.

The full private card inventory may be retained ignored; the public derivative
must expose only validated identity/mode/filter/time/schema diagnostics without
raw cards, coordinates, contact text or arbitrary errors. There is no EVENTS,
GTI, exposure, BADPIX, CALINDEX or image value decoding in this stage. A future
header-only success cannot by itself establish live exposure, aperture support,
clean negatives, counts, recovered QPEs or a discovery.

Final review remains pending the author-ready runtime and pure header helper.
It will be limited to their actual contract and concrete synthetic adverse
cases, not a new transport framework or an expanded scientific gate.

## Header identity core checkpoint — synthetic only

The complete new `xmm_rxj_header_identity.py` and author tests were read.
No material blocker was found in the pure core. Required OBS_ID, INSTRUME and
EXPIDSTR must each be explicitly matched somewhere across primary and the sole
EVENTS HDU. Redundant placement is not required; missing placement remains
visible. A contradictory or duplicate identity in either selected HDU causes
STOP, including an optional EXP_ID when present. Numeric EXP_ID is only
corroboration and cannot supply the missing scheduled/unscheduled flag.

Independent checks passed **12 author tests**, Ruff 0.16.5 and **229 additional
synthetic cases**: 192 exhaustive primary/EVENTS/both/missing placement choices
for the three mandatory keys across three cameras; 24 wrong present identity
values; nine duplicate mandatory keys; three invalid EVENTS roster/type cases;
and one mixed privacy canary spanning identity, optional strings, column metadata
and coordinate cards. No actual retained headers or scientific arrays were read.

Checkpoint SHA256:

- Core: `93d1b524f92857a348b3cda465962b8ec6f6cf9c31a31385f77d8320cbdfd23e`.
- Tests: `2fea0a61834e3bcd14e5371d9d09084fbff3a29f83f151f39a7691632bc6f95e`.

The input is explicitly a caller-verified structural report; this is not a
second complete FITS layout/provenance validator. Public optional metadata uses
finite vocabularies, numeric/type checks or hash-only unknown values. Identity
failures themselves disclose only expected identities and candidate hashes.
Mode/filter/time metadata remains a separate diagnostic: a known-format value
does not establish temporal validity, live exposure or scientific eligibility.
Ancillary schemas are inventoried without inheriting missing identity or reading
their values. This is a core-only checkpoint, **not M5 runtime execution GO**.

## Runtime draft checkpoint

The initial runtime draft was read while identity path/pins, protocol and tests
were still pending. It creates a fresh pinned C1 module and does not invoke the
old C3d binding or worker. Exact planned selectors, disposition matching, magic
dispatch and stop-first-failure logic are present; final behavior is not yet
accepted without the completed tests.

A concrete reserve risk was sent to the author and parent: the draft saves all
slot results with terminal privilege, including large successful identity
inventories. Such receipts could consume the JSON space intended for final
worker/outcome failure reporting. Ordinary and failure slot budgets must leave
that reserve available and demonstrate preservation in a synthetic near-cap
case. A remaining aggregate raw budget of zero should also be rejected before
issuing a GET rather than after its response headers. These are prospective
implementation findings, not observed failures on real products.

## Final runtime review checkpoint

The final runtime and full prospective protocol were read, including all changes
from the earlier draft. The reserve issue is fixed: identity derivatives are
separate ordinary, capped artifacts; successful slot receipts cannot consume
terminal reserve. Failed slot receipts are compact and capped. Zero remaining
raw budget is rejected before a session GET. Two final consistency fixes enforce
that an uncertain write's actual retained bytes lie between known retained and
returned bytes, and that a successful outcome cannot also carry a parent error.
The protocol's earlier inaccurate phrase about checksum-validated FITS card
parsing was corrected to syntax/layout validation; no FITS checksum claim remains.

The header core's last prospective change adds CREATOR/SAS_VER/SAS_CCF as
intentionally hashed provenance only, preserving missing/duplicate counts with
no raw text. The delta and its focused test were read; **13 core tests passed**.
This does not interpret calibration contents or resolve their availability.

Independent runtime verification completed:

- **14 author runtime tests passed**, covering three-slot gzip/raw success,
  metadata-only binding under private-input guards, wrong identities, HTTP
  rejection before body reads, first-failure gating, overflow/CRC/socket/write
  accounting, terminal reserve, nonzero worker status and immutable local replay.
- **Ten additional inline adverse cases passed**, using generated products only:
  empty body; mismatched response URL; absent disposition; supplied length
  mismatch; truncated gzip; non-gzip junk after gzip; wrong raw magic; remaining
  raw and expanded aggregate caps; and late parent serialization peak overflow
  with a retained STOP and offline replay. Pre-body failures consumed no response
  body, and later mock GETs remained uncalled after failure. Unknown or overflow
  work was not promoted to clean EOF. No actual network session was used.
- An independently invoked physical-file synthetic benchmark passed on the
  final numerical/transport source: three generated products with 64-MiB image
  payloads, **201,355,200 expanded bytes**, **67,249,680 raw bytes** and **63,983
  JSON bytes**. Worker-plus-parent took 1.734 seconds; replay took 0.890 seconds;
  the real Windows lifetime peak was **256,212,992 bytes**. HTTP bodies, launch
  and metadata binding were mocked; physical files, gzip/copy, opaque hashes,
  structure, identity helper, peak sampling and receipt replay were real.
  These measurements are not archive-network performance, worst-case maximum
  product timing, or an independent process-tree-kill test.

All generated products were temporary test fixtures. No real archive/product,
private header, scientific array, actual request or historical replay was read
or invoked during this review. The completed private-input binding guard does
not authenticate any future response before it is acquired.

At this checkpoint the only outstanding item is the author test's B023 closure
binding lint fix; runtime and scientific scope findings are resolved. Final
acceptance and exact test hash follow once that small test-only correction is
verified. No request is authorized by this checkpoint.

The test closure correction is now verified: **14 runtime tests and Ruff pass**
at runtime `e0da2b17e8fdedf5426764526996898ee8481c826e50c95cc1dadef560281e14`,
tests `1ee730a824257a2038e14ac5ef9f34c4298313e3d790cf03071f391065df3d97`,
and protocol `6a02a7bafda55fd05fc615f5d0605881f3e6dcdde63b666ba6d6c6871971c9bf`.
Parent subsequently requested a compact per-slot parent/replay header-pass
started/completed ledger that survives verification failure. **Final runtime GO
remains HOLD only for that prospective delta and its regression review.** This
does not reopen completed checks or add permission for any actual acquisition.

## Final acceptance — compact header-pass delta

The final delta and protocol explanation were read in full. Parent assessment
passes a shared three-slot ledger through header verification. `started` is set
immediately before header inspection; `completed` follows the layout and available
identity comparison, not overall acquisition success. Parent exceptions retain
that ledger. Explicit replay uses a fresh ledger and reports it on inspection,
identity or late outcome-comparison failure without modifying stored artifacts.
The flags do not measure all opaque hash I/O, header bytes, or unknown hard-killed
work. The protocol states these limits rather than claiming complete physical
read accounting.

The final runtime suite passed **16 tests**, including both new focused failure
tests, and Ruff 0.16.5 passed. An additional **65 independent synthetic cases**
passed: all 64 combinations of three started/completed boolean pairs against a
separate sequential-prefix oracle, and a replay whose second header inspection
succeeds but identity comparison fails. The latter records first slot complete,
second started/incomplete, third unstarted and preserves all original artifacts.
No material blocker remains in this specific acquisition/header-only scope.

Final SHA256 anchors:

| Artifact | SHA256 |
| --- | --- |
| Runtime | `e8597327a7cbe4f6ca975d88d2e4b2584fef1afa21a4bf16c388daa046be2b12` |
| Runtime tests | `d387056f90bac2eed0f9480ef16a381f9d35e8f468f9f04449e64d1964dd50a9` |
| Protocol | `7273718a789146accd9ecd5c51b9b36cea698a25234b093fc419216cb16a425e` |
| Header identity core | `22d05a66a9afaeee8dc4ceb781ddc9f54354dafcf7eb139535456f773b9e947a` |
| Header identity tests | `891569eba7c9d1fcd5199b3e64c796e470bda64fd2e8924532bacb376683d6ee` |
| Stage attributes | `805ac80d2520f7a8f224ec68cb639663af574872866680a623d86c5f06aa21e8` |
| Stage ignore rules | `6567d61f6c56523a1af8103f3af2db07f6859b799ada7db68895139e211f28c3` |

The earlier 13 core tests, 229 independent core cases, ten independent runtime
adverse cases and physical-file benchmark remain completed checkpoints. The
benchmark source was `e0da2b17...`, immediately before this small receipt-ledger
delta; it was not represented as a fresh final-hash maximum-size benchmark.
No transfer, decompression, identity criterion or scientific setting changed in
the final delta. The final metadata-only binding test also passed; it does not
open private prior inputs or run historical stages.

Acceptance is for at most the three exact planned GETs, stopping on first failure,
followed by the declared bounded header-only verification. It is not permission
for replacement selectors, retries, metadata repair, calibration-index reads,
photon counts or discovery claims. Raw/expanded products and full cards remain
private and ignored; only the safe derivative is public. Actual returned headers
must still authenticate identities and preserve mode/filter conflicts or
missingness. All earlier STOPs and scientific coverage/background/control gates
remain in force.

## Postrun receipt-only audit — 2026-09-13

**The preserved outcome is STOP, not completed acquisition or header
authentication.** Parent reports one execution after freeze `d76223b`, terminated
by the 300-second tree-aware worker deadline, and exactly one later CLI
failure-artifact replay. This reviewer did not repeat that replay, open/hash the
partial product, inspect any private header or issue a request.

Independent public-only checks passed: **five public artifact hashes**, **12
dependency hashes**, all five current source/test/protocol/privacy/attributes
anchors and current protocol/snapshot equality. Five JSON files total **6,169
bytes**. The worker marker binds the run receipt; the sole slot marker matches
the first frozen selector. The private artifact's hash was checked only for
receipt shape, not recomputed. Its retained size was read with filesystem stat.

Relevant SHA256 anchors:

- Outcome: `9eb6912a34cabdfad6c5da42d751e7be25c249ed72ec2910f194bdbca59119bb`.
- Run binding: `47185082c08cc19584e3f7c56445dae1a580b4b581d6dec00514fd4f7ab75bc6`.
- First HTTP receipt: `9defa91737820d025299806875c86b81d9aa8c989eed4786851f065bdc29af33`.
- Partial-product hash **recorded by the parent, not verified in this audit**:
  `8e5e6b07f836967030e05594d519527829c7ea4429c442a21317d0f8a81f233d`.

The first HTTP receipt records 200, exact URL match, `image/fits`, no supplied
Content-Length and an exact expected-disposition filename hash. Its Date is
2026-09-13 06:40:10 GMT. Those headers do not establish raw-format magic, FITS
identity, total product size or completion. The pn partial is retained at
**28,311,552 bytes**, below the frozen raw caps. There is no expanded FITS file,
private header report, identity derivative, slot-result or worker-result. There
are no second/third slot markers. The ledger correctly leaves pn
`UNVERIFIED_ATTEMPT` and both MOS slots `NOT_ATTEMPTED`.

Worker return code is 124. Parent assessment is false with `STOP_INTERNAL`;
that parent error code alone is not an archive diagnosis. All three additional
header-pass started/completed flags are false. No authenticated FITS header or
scientific value was produced. Parent lifetime peak is recorded as 47,800,320
bytes; **worker peak is unknown** because no worker-result survived. Exact raw
returned-byte counters, possible in-flight buffering/write work and verified
EOF are also **unknown**, not zero and not equal by assertion to the stat size.
The normal slot `request_invocations` counter was not serialized; evidence is
the one first-slot HTTP receipt and frozen one-attempt control flow, not a
completed per-request measurement receipt. No CRC/expansion completion follows.

The current ignored-products rule and its exact bound bytes were checked. A
read-only `git check-ignore` attempt was blocked by the sandbox's repository
ownership check; no Git configuration was changed. Parent owner-context ignore
confirmation remains an operational check separate from byte retention. The
partial was not removed, overwritten, resumed or interpreted by this reviewer.

Parent subsequently confirmed the exact retained partial is ignored by the
stage `.gitignore` line 1, `/products/`, using a command-local safe-directory
setting for `git check-ignore -v`. This is attributed to the parent's check,
not a successful Git invocation by this reviewer; no global configuration was
changed. The privacy-retention operational check is therefore complete.

Parent's reported `PASS_FAILURE_ARTIFACT_REPLAY STOP` confirms its failure
receipt/artifact check only; it is not a header replay or a completed download.
This audit adds no raw hash pass. The stop does not show that the source or
product is unavailable, that the instrument lacks exposure, or that a QPE is
absent. It authorizes no retry, range-resume, fallback or changed budget. M4's
incomplete metadata, earlier STOPs and all scientific recovery gates remain
unchanged.
