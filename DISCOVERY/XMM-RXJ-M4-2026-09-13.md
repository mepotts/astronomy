# RXJ M4: four fixed metadata members, quarantined trailer

Prospective offline-only implementation of the adopted
[M3 next decision](XMM-RXJ-M3-NEXT-2026-09-13.md). No requests, extraction,
decompression, rendering, linked resources or scientific product/array access.
The immutable M3 archive/STOP and earlier failed gates are not edited or regraded.

## Fixed input and before-payload proof

Exactly1,044,480 retained bytes, SHA256
fa3c45838875c61f68e07508d862fc56d32e83f0b39ed3f6b1bef2207b9ccbe2.
No raw archive is opened by binding/manifest preparation. Each execution pass
first hashes these opaque bytes in≤65,536-byte reads, then checks the four512-byte
headers by exact hash, stdlib checksum/type/name/size/role and layout. The fixed
header hashes and complete member definition are in the adopted note and source
PLAN, not dynamically discovered. Names must be distinct and have the previously
verified observation/PPS prefix categories and exact role/X000/SUMMAR0000/HTM
identity; no raw path is printed. These are observed fixed records, not a
generic TAR admission profile.

| Slot | Role | Header offset | Payload offset | Payload bytes | Next boundary |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | EP | 0 | 512 | 872917 | 873472 |
| 2 | OB | 873472 | 873984 | 48229 | 922624 |
| 3 | RG | 922624 | 923136 | 25265 | 948736 |
| 4 | OM | 948736 | 949248 | 86689 | 1036288 |

Read the8,192-byte tail at1,036,288 only for exact hash and checking its first
1,024 zero bytes. Entire tail SHA256
e3c5d4864109c463b69f6f7b124995ae36b2082f40e972339da26f0e9200a0ea;
remaining7,168-byte uninterpreted trailer SHA256
c304f59f74ff1408146b797c68f001e4284f7bb014ae2267d98e60f44de040f9.
No trailer text, extra header or payload interpretation. Never call the M3
generic TAR validator or attempt to repair its size/member/tail policy.

## Exact per-pass work and semantics

Only after that complete proof, read all four fixed payloads sequentially through
unbuffered streams in≤65,536-byte chunks. A full pass returns exactly1,033,100
selected bytes. Separately account1,044,480 opaque hash bytes,2,048 header bytes
and8,192 tail bytes. Each slot has exclusive start/result receipts, known returned
bytes, unknown-read flag, content hash and separate parse-attempt/completion
state. Count returned bytes before later parsing/checkpoint failure. A raised read
with no returned buffer leaves that invocation's returned count unknown, never
invented. Ordinary caught read/parser failures remain in their slot and later
roles are attempted; resource/deadline or global provenance failure stops later
work, leaving the four-slot ledger explicitly unattempted where appropriate.

Call only hash-pinned parse_summary(raw,role,obsid). Metadata-incomplete results
are accounted documents, not runtime failures. The parser owns allowlisted
encoding/identity/exposure/mode/filter/timing/processing/product-reference results;
unrecognized values are hashed, duplicate columns retain ambiguity, source-level
science and coordinates are not interpreted. No private HTML copies are needed.
Safe per-document receipts retain parser output and digest. Compare successfully
parsed documents using its pure compare_summaries API; absent/failed roles remain
explicit, common values establish consistency only, not a preferred version.
No exact closing HTML tag or required common exposure roster is imposed.

Runtime label FOUR_FIXED_METADATA_DOCUMENTS_ACCOUNTED_UNADJUDICATED means four
bounded parses returned, including METADATA_INCOMPLETE. It does not assert four
verified identities, valid mode eligibility, complete inventory, live exposure,
public event accessibility, clean negatives or a discovery. The subsequent human/
root interpretation must report each missingness/conflict before another proposal.

## Runtime, provenance and failure accountability

One30-second worker, enforced by the pinned audited process-tree helper. Parent
verification and explicitly invoked replay each permit one additional30-second
cooperative bounded pass; they have no network and no process-tree helper of their
own. Deadlines reset in finally before terminal reporting.256MiB monitored Windows
lifetime peak is an acceptance cap, not an allocation quota. Source reuses only
the fresh hash-pinned C1 peak sampler and pinned deadline helper; no old scientific
worker, plan or measurement function is invoked. Sample after terminal JSON
serialization; excess peak can only downgrade to STOP.

JSON aggregate≤1MiB,64KiB reserved for outcome; individual ordinary receipt≤192KiB,
terminal outcome≤64KiB. Compact per-pass ledgers retain result hashes, not duplicate
large parsed metadata; each document and cross-document result has its own bounded
artifact. Archive is already locally ignored and immutable. Stage privacy ignores
any unintended HTML/TAR copies; the artifact allowlist rejects them regardless.
No arbitrary errors, private text or child stdout are public: safe STOP codes and
child-output byte count/hash only.

Bind exact source/tests/protocol/privacy/runtime, parser/tests, C1 source/tests/
deadline helper, M3 source/tests/protocol/outcome/HTTP/transport and adopted LF
decision. Parent compares all four recomputed records, comparison and compact
pass ledger with worker evidence. Missing completion/nonzero worker returncode
cannot promote success. Retain partial verification counters on every failure;
explicit replay failure reports its additional pass without modifying artifacts.
Unassessed failure replay is labelled artifact-only and cannot claim metadata
recomputation. Four marker/result presence pairs expose unknown interrupted worker
work independently of the parent-pass ledger. Strict typed receipt closure rejects
invented statuses, bool/int aliases, missing/extra/nested artifacts and changed
digests. Synthetic full-size four-document tests, partial/continuation/resource/
tamper tests, independent review and exact-byte freeze precede any actual payload.

Run tests from the repository root (not the stage directory, whose inspect.py
name would shadow Python's standard-library inspect module in unittest.mock):
`dyson-revet/.venv/Scripts/python.exe -B -m unittest discover -s DISCOVERY/XMM-RXJ-M4-2026-09-13-data -p test_inspect.py`.
