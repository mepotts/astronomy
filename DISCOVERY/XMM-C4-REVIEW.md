# Independent C4 pre-execution review

September 12, 2026. **Numerical core and prospective protocol accepted for
the specified diagnostic scope; runtime-wrapper review is still pending.**
This is not execution approval. No actual attitude, photon, map or source-list
arrays were read, and no network/product request was made for this review.

## Core and protocol checkpoint

Read `xmm_attitude.py`, `test_xmm_attitude.py` and
`XMM-C4-2026-09-12.md` completely. Eight current synthetic unittest methods and
root-invoked Ruff 0.16.5 pass. An independent synthetic comparison of 1000
random great-circle separations (NumPy seed 1903) with a Cartesian-vector
cross/dot `atan2` oracle passed at 1e-6 arcsec absolute tolerance; the largest
observed difference was approximately 2.10e-9 arcsec. This is an arithmetic
test, not an instrument-accuracy claim.

Two initial boundary findings were repaired by the parent before execution:

- Arbitrary camera/header-counter dictionary fields could previously be echoed
  to output. The core now enforces exact key sets, known camera identifiers,
  numeric time ranges and four nonnegative integer counters, then reconstructs
  only the permitted output metadata.
- NumPy masked-array masks could be lost by `np.asarray`. Such inputs are now
  explicitly rejected before conversion. The planned raw float64 decoder has
  no implicit masked-array interpretation.

The eighth test includes privacy/schema regressions for both repairs.
No absolute input pointing/reference coordinates are intentionally serialized;
only relative separations, relative-offset extrema and quality/count summaries
are returned. Runtime exception/warning/output privacy remains a separate
wrapper obligation, not established by the numerical-core tests.

## Mathematical and scientific interpretation

The core retains per-column finite/NaN/infinite accounting and distinguishes
finite-domain failures from missing values. Zero directions and offsets are
valid values; large finite sentinels are not normalized into plausible angles.
The RA/PA/declination domains are predeclared sanity checks, not measured
attitude quality. Relative-offset columns preserve finite extrema and flag
values outside their separate declared domain before arcsecond conversion.

Pointing differences use spherical geometry. PA steps use the shortest wrapped
absolute difference and are reported separately, not as a full 3D rotation or
detector-footprint movement. Step calculations require consecutive original
rows, eligible angles/times and a positive one-second separation within the
prospective 1e-6-second tolerance. They cannot bridge an invalid row or time gap.
First-reference choice is deterministic and its absolute angles are not output.

The protocol correctly requires exact ten-scalar-D schema, units/order/rows,
no scaling/null/heap ambiguity and one isolated 4,158,000-byte ATTHK payload.
It adopts TT/MJD50814 only as a prospective interpretation because the actual
reference keywords are absent. Camera-range bracketing is explicitly not a
GTI, exposure, simultaneous-good-attitude or clock-reference proof. The core
always reports `clock_reference_verified=false` and
`continuous_motion_bound_established=false`.

Header NATT/NGAHF/NGOM/NGAHFOM values remain separate from independently
measured finite/joint/domain-valid counts. A mismatch is evidence to retain,
not a reason to convert the header contradiction into all-good attitude.
Even fully finite, slowly moving samples cannot bound between-sample motion.

No scientific blocker was found in this deliberately limited aggregate
diagnostic plan. It does not adopt frame-support assumptions, freeze the
counts-recovery test, accept detector geometry or authorize unknown targets.

## Runtime review still required

The wrapper must demonstrate exact frozen provenance, safe schema/offset checks,
bounded direct reads, all failure-byte accounting, exclusive markers, bounded
worker cleanup, privacy-safe errors and exact independent replay. The protocol
allows one worker pass, a distinct parent numerical check and a distinct replay
pass; it must not claim that all verification together reads the payload once.
No numerical replay of real data has occurred at this checkpoint.

## Reviewed checkpoint hashes

| File | SHA-256 |
| --- | --- |
| `xmm_attitude.py` | `df6a49a01d20f6b58c275881fea48a95de158ee6e8c04c272b0ef2ac616f7f4a` |
| `test_xmm_attitude.py` | `1af690f296a88d8e6267d055eb2d17f32e8742d37c68e3f03936fd8e7098027f` |
| C4 protocol | `1c22b0322e750ab291a9910cdaf8209acc37f9d990976e953e619773e45837f0` |

Future runtime/result checkpoints should append to this history; no current
statement asserts successful real-data C4 execution.

## Runtime checkpoint: synthetic review, before final receipt repair

Read the complete C4 `inspect_values.py` and its synthetic test file, plus
the inherited pinned serialization/resource helpers and relevant prior-stage
provenance loader. Independently reran all 14 wrapper tests and eight core
tests successfully; root-invoked Ruff 0.16.5 passed for those four files.
The actual-input smoke test inspected only retained header JSON and outcome
hashes. It did not invoke prior replay, hash/open a science product, or decode
an actual array. Network/old-worker entry points are tripwired in the fixtures.

An additional independent inline harness used the author's isolated temporary
synthetic fixture, ran the complete mocked parent `run` into the real worker,
parent assessment and replay, and counted three separate 4,158,000-byte
read/decode passes. A promoted `photons_or_map_pixels_interpreted` outcome flag
was rejected. The independent probe also exposed one metadata-closure defect:
a nonboolean `assessment_completed` value was accepted by replay. This is not
a numerical error, but requires a strict boolean check before final acceptance.
The author was notified; no real-data execution was used to discover it.

The reviewed decoder seeks only the bound ATTHK span, requests six chunks no
larger than 800,000 bytes, interprets scalar big-endian float64 values, and
stops on a short chunk. Synthetic truncation retains returned-byte counts
separately from successfully decoded full chunks. No EVENTS, source-list or
map array is selected. The successful parent/replay path independently
recomputes the full aggregate summary rather than trusting receipt hashes
alone. Nonzero worker exit cannot promote a successful-looking table, and
late monitored-memory failure remains STOP through replay.

The worker's caught errors serialize only a class identifier and recognized
STOP code, with a fixed safe log message. Header warnings are captured and
ambiguity stops; synthetic absolute-angle sentinels do not occur in saved
JSON. These checks cover the fixed reviewed decoder/core path, not arbitrary
future plug-ins or a guarantee against hostile runtime replacement.

Important accounting clarification sent to the protocol owner: after a hard
termination before a table receipt, exact returned/decoded bytes are unknown.
`INTERRUPTED`/`UNVERIFIED_ATTEMPT` intentionally omit accounting and must not
be interpreted as zero bytes. Caught truncation has exact receipt accounting;
failure-artifact-only replay does not certify numerical results. The
per-pass maximum still follows from the decoder, conditional on bound source.

At this checkpoint wrapper SHA-256 was
`03d7e7fd34e70b7b5223e64e0d9f8434566ad2084d77ff754e54d6297a5cfca0`,
and wrapper-test SHA-256 was
`97b98c9ac00320e8829ec6093a16157059c20dcebfc9677cbb41c52fe194dc9a`.
These are review-history anchors, not final execution pins. Runtime acceptance
remains pending the small receipt-schema repair and final tests.

## Final pre-execution runtime acceptance

The author repaired the strict-boolean finding and added a direct regression
rejecting nonboolean completion flags; the same guard rejects a missing key.
The parent now also refuses
any existing snapshot, worker marker/result or table marker/result before
binding or launching an orphaned attempt; the second new regression covers
each such file. Independently read those changes and reran all 16 wrapper
tests successfully. The unchanged eight numerical tests also passed during
this review, for 24 current author tests in total. Ruff 0.16.5 passed on all
four source/test files. Earlier independent inline checks remain separate
checks, not additional committed test methods.

**Scoped runtime GO for parent freeze/authorization.** No remaining blocking
implementation or scientific-interpretation issue was found for this one
sampled-attitude diagnostic stage. This review does not itself authorize a
real-value read, and did not perform one. The parent must preserve the
hard-termination accounting qualification above in the final protocol/result.
No continuous coverage, good-attitude, clock-validation, detector-geometry or
burst-recovery claim is accepted by this GO.

| Final candidate file | SHA-256 |
| --- | --- |
| C4 runtime | `d53d265ebf3ff82832137da2ee7e0fffcf7f1095f143790c655a8fd0f8915e39` |
| C4 runtime tests | `b37ccf15c5834420c8257b2eb37c4932a8cd14de4bc3449c30a6e8755ffca606` |
| Core | `df6a49a01d20f6b58c275881fea48a95de158ee6e8c04c272b0ef2ac616f7f4a` |
| Core tests | `1af690f296a88d8e6267d055eb2d17f32e8742d37c68e3f03936fd8e7098027f` |
| Protocol at acceptance | `1c22b0322e750ab291a9910cdaf8209acc37f9d990976e953e619773e45837f0` |

The protocol hash above precedes any parent-owned wording clarification about
hard-kill accounting; such a pre-execution clarification is not a changed
payload selection or numerical algorithm and should be recorded separately.

## Final protocol wording verification

Independently reread the final protocol and verified that removing only its
four newly inserted hard-termination accounting lines reproduces the previous
protocol SHA-256 exactly (`1c22b032...737f0`). The addition explicitly states
unknown-not-zero interrupted byte counts, their bound under the decoder,
exact caught-truncation accounting and failure-artifact-only replay. It
resolves the review qualification without changing inputs, algorithm, caps
or scientific interpretation. Runtime and test hashes remain exactly those
in the final candidate table above.

Final protocol SHA-256:
`a4b27125eed686b706126fe502be0147feb18db502cbe3627ef630766a91b4bc`.
**Ready for parent freeze and separately authorized execution.** No actual
array was read for this verification.
