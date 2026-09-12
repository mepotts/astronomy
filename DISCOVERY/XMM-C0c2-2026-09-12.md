# XMM C0c2: cap-only amendment, not yet executed

Prospective resource-only amendment, 2026-09-12. C0c returned HTTP 200 but stopped
at its 262144-byte retained-body cap. Its source, protocol, partial index and
failure receipts remain byte-identical. No scientific selection or acceptance
criterion changes. This is a separately authorized single attempt, not an
automatic retry of C0c.

Parent review/freezing must precede execution. Authoring this amendment does not
execute a network request. The only permitted URL remains:

`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/`

One anonymous directory-index GET, **1048576 retained response bytes**, plus
**one read byte** solely to detect overflow. No linked product, HEAD, second
request, redirect, retry, private coordinate, account, credential or cookie use.
The 5/15-second socket timeouts and audited 30-second process-tree worker
deadline remain unchanged; termination/reporting has the helper's separate
cleanup allowance. Use the previously verified owner execution context.

## Frozen-core reuse

The thin wrapper imports the exact byte-hash-pinned C0c core at
`XMM-C0c-2026-09-12-data/listing.py`:

`6dfc1715fa477a69687fd54a01a6cd61abd26be99519f18fd4e9297cd3091e31`.

The wrapper verifies the core byte hash, then uses a small import-loader override
whose `get_code` compiles that same verified byte buffer. It does not re-read
source or trust a timestamp-based cached bytecode file. The normal `exec_module`
entry point loads the compiled local module. Both parent `run` and child
`_worker` enter through that verification. A mismatch raises
`STOP_FROZEN_CORE_HASH` before core execution, markers or network. The
existing core then independently verifies the unchanged helper hash
`11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd`.

Only the core's output directory, source identity, protocol identity and cap are
rebound to C0c2. Its request, authentication isolation, streaming, safe-header
allowlist, one-attempt markers, partial retention, deadlines, receipt validation
and STOP behavior are reused unchanged. The child command points to the wrapper,
not the old core's command-line entry point. The wrapper's receipt-bound source
hash transitively binds the literal core hash; the protocol snapshot also names
that hash. No monkey-patch of a scientific or transport function is used.

The new directory is `XMM-C0c2-2026-09-12-data/`; original C0c files are never
destinations. Preserve exclusive run/worker markers, the new protocol snapshot,
safe HTTP receipt, complete or partial index, worker and parent outcomes and
artifact hashes. Never retain Set-Cookie or authentication headers. Any failure,
including another cap failure, stops this amendment without another attempt.

## Acceptance boundary

`HTTP_INDEX_RETAINED` means only a bounded complete HTTP HTML body was retained
and receipts validated. It does not establish complete product selection, exact
file sizes, supported cameras, scientific contents or discovery readiness.
Rounded/missing directory sizes retain their previous interpretation. Offline
listing inspection and any product acquisition need separate review/authority.

Focused offline tests cover unchanged URL/helper/functions, separate paths,
parent and child core-hash rejection, exact new cap success, cap-plus-one STOP,
anonymous request settings and safe headers. Existing frozen C0c transport tests
remain applicable; tests are not a live archive or scientific validation.

Parent execution, only after review and freeze:
`python -B DISCOVERY/XMM-C0c2-2026-09-12-data/listing.py run`.
Do not execute `_worker` independently. This note may later receive a result
appendix; the executed local `protocol.snapshot.md` remains immutable.

Pre-execution checks: seven focused offline tests pass, including a loader test
that forbids unverified source/bytecode reads; pinned Ruff 0.16.5 passes. The
parent reviewed and accepted the narrow verified-buffer import adapter. No
real request, run marker, protocol snapshot or result exists at this handoff.
Independent review and the parent's final freeze remain required.
