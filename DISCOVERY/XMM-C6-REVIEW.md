# Independent C6 acquisition preflight review

September 12, 2026. **Scoped GO for parent freeze and separate execution
authorization: one exact documented MOS2 request, acquisition/headers only.**
No live request, product download, real FITS-product hash, map/attitude/event
array read or new coordinate query was performed by this reviewer.

## Reviewed evidence and tests

Read the complete C6 source/tests, the reused C3d transport source and relevant
inherited disposition, expansion, header-reader and helper-isolation code.
Read the exact-selector evidence note and final prospective C6 protocol
completely. Independently ran all **17 synthetic/receipt-only tests** and
root-invoked Ruff 0.16.5 successfully. The retained-prior smoke test passed
with product-open and network tripwires; it invokes only original C3's
receipt-only replay and hashes C5's outcome, not C5 numerical replay.

Three additional independent inline full-worker failure probes passed:

- A mocked connection failure retained a FAILED request receipt, no raw body,
  and only its exception class, not deliberately private exception text.
- A declared-length body truncated to 17 bytes stopped with
  `STOP_ACTUAL_LENGTH`, retained exactly those bytes and could not pass parent
  assessment.
- A body exceeding the raw cap stopped with `STOP_RAW_BYTE_CAP`, retained
  exactly 2,097,152 bytes and inspected only one additional overflow byte.

An independent fresh-module isolation probe also passed: a separately loaded
original C3d instance retained its ATT paths/selector/slot/product function;
C6's rebinding affected only its own new module and helper instances. The
delegated ledger and original product-record function resolve their globals
through that C6-owned instance, so C6's additional MOS2 identity validation
is reached during replay. No old worker, plan or ATT-prior function was invoked.
These inline probes are separate from the 17 committed test methods.

## Request and transport contract

The source's exact URL matches the bound selector note and protocol: only
observation 0884250101, PPS M2 scheduled S002, EXPMAP subset 8, source field
000, FTZ. The required returned basename is
`P0884250101M2S002EXPMAP8000.FTZ`. Documentation establishes selector semantics,
not present archive availability or assurance of a one-file raw response.

The reviewed path makes one anonymous streamed GET with no preliminary HEAD,
redirect, retry, Range or package fallback. It clears cookies, disables
environment proxy/auth inheritance and requires the exact final URL, HTTP200,
identity/absent content encoding, allowed media and unambiguous safe basename
before reading the body. Synthetic tests cover wrong instrument/filename,
package names, absent/ambiguous disposition, unsafe paths, rejected media,
HTTP403/404/redirect and contradictory length headers.

The 2-MiB raw and 32-MiB expanded limits, one-byte overflow probes, one-MiB
chunks, 5/15-second socket timeouts and 60-second process-tree worker are
fixed. The reused gzip path verifies CRC/EOF while expanding; raw FITS copies
require equal hashes. Damaged gzip and expanded-cap tests preserve partials
and STOP. No ZIP/TAR extraction is available. Monitored peak, free-space and
JSON/terminal-reserve checks remain active; they are not OS allocation quotas.

The final protocol correctly distinguishes retained file sizes from exact
received/decompressed bytes on failure. An overflow probe is not retained;
catastrophic interruption can leave attempted work unknown. Artifact-only
failure replay is labelled and cannot establish product validity. Successful
parent replay checks format, sizes/hashes, header reproduction and exactly
one raw, one expanded and one header file. It is not another decompression;
gzip completion rests on the bound worker's successful CRC/EOF path and
immutable artifacts.

## Header identity and scientific boundary

The pinned structural reader seeks past declared image payloads. C6 requires
one primary float32 image, exact observation/EMOS2/S002 identity, no parser
warnings or duplicate non-commentary cards, and two positive integer
dimensions whose declared byte arithmetic fits under the expanded cap.
It correctly does **not** infer 648-square dimensions from pn/MOS1. The
synthetic 4-by-5 image demonstrates that the intended positive-2D rule is
implemented rather than a hidden fixed-shape assumption.

This is storage/entity validation, not acceptance of physical units, scaling,
WCS, map band/FLAG/GTI selection, exposure calibration or positive source
support. Those remain separate header-compatibility and prospectively frozen
value-stage questions. As in the structural-reader review, malformed headers
may require bounded scanning of unknown bytes before STOP; no general claim
that arbitrary malformed input involves zero payload I/O is justified.

Public receipts contain only the permitted structural identity, safe HTTP
metadata, hashes and sizes. Full local header cards and both products remain
ignored before execution. No coordinate-bearing warning/exception text is
intentionally serialized. Opaque transfer/decompression/hash I/O is real I/O
even though no scientific array values are interpreted in this stage.

Original C3 HEAD404 STOP and C5's results remain unchanged. A C6 success means
only `MOS2_MAP_RETAINED_HEADERS_ONLY`; it does not satisfy the pn-plus-MOS
recovery gate, establish contemporaneous source exposure, remove a control,
or authorize a broader request if this exact selection fails.

## Final reviewed anchors and freeze condition

| File | SHA-256 |
| --- | --- |
| C6 source | `4ed7d10e229a38f4356f34386ee70e510915049c1468b006841908ecaf1cbfdb` |
| C6 tests | `f46468825846e68649ccb48d2592163b0151476de6a49609f315af2141c31ccf` |
| C6 protocol | `464a53d8ce733ce080a1962f2245a80a11a7593b1c5c1045c9f70898c7cbd9cb` |
| Selector evidence note | `a816fd84aece2eb4acd4c4cf0dd630416a9563a26af46a4deee24ce33a393760` |

No remaining scoped implementation blocker was found. Before authorization,
the parent must preserve these raw bytes in the freeze and verify that the
selector note's Git blob matches its pinned hash, including the deliberate
CRLF-preservation rule. Product/header ignore rules must be in place. The
reviewer made no Git, source, test, protocol or previous-result modifications.
This review is not itself permission to issue the GET.
