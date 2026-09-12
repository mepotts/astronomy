# XMM C0c2 independent pre-execution review

2026-09-12: **GO for the separately authorized single metadata-index request and
subsequent offline inventory parsing.** No reviewer network request, product
download or scientific measurement was performed. This does not change the
frozen C0c STOP or authorize additional requests after another failure.

The complete wrapper, protocol, seven wrapper tests, offline inventory parser
and six parser tests were independently read. All 13 tests passed in the
reviewer's run; pinned Ruff passed for the four Python files. The original
transport and its independent review remain the basis for unchanged request,
anonymous-session, timeout, marker, receipt and partial-retention behavior.

## Transport scope and loading

Only the retained-body limit changes from 262144 to 1048576 bytes, with one extra
read byte for overflow detection. The exact URL, anonymous session, no redirects
or retry, 5/15-second socket timeouts and 30-second worker-tree deadline remain
unchanged. Separate paths keep old artifacts out of the new write destinations.
Both parent and child dispatch first verify the original core's literal SHA-256.
The source receipt identifies the new wrapper, which transitively binds that
core hash; the child command points to the wrapper.

An intermediate ordinary import-loader alternative was rejected because source
hash checks alone do not establish the identity of cached bytecode. The final
small loader compiles the already verified byte buffer through `get_code` and
uses standard `exec_module`; it does not reread source or cached bytecode. The
regression forbidding loader `get_data` confirms this behavior. This is still
intentional execution of trusted, pinned local code, not a claim that module
loading avoids code execution.

Tests cover both entry points rejecting a changed core, verified-buffer loading,
unchanged URL/helper/functions, separate paths, the exact new cap, cap-plus-one
STOP, anonymous request options and safe headers. No additional harness was
introduced by this reviewer.

## Offline inventory scope

The parser requires expected directory title/header, a closing HTML footer and
preformatted-section closure. A separate HTML anchor parser cross-checks every
regex-parsed anchor. Only explicitly known navigation links are ignored. File
names must be plain same-directory names without traversal, escaping, queries,
fragments, mismatched labels or duplicates; no link is followed. Unrecognized
PPS naming fields remain null rather than being guessed.

Two findings were corrected before this signoff:

- Every artifact named by the successful outcome is now hash-verified, and
  body/HTTP/worker receipt inclusion is mandatory. A semantically successful but
  modified HTTP receipt is rejected by regression.
- All `exact_bytes` values remain null. Unsuffixed numeric displays are retained
  separately as `display_integer`; neither those values nor K/M/G displays are
  promoted to independently verified product lengths.

The parser accepts only a successful transport outcome, successful worker/body
receipt and exact HTTP URL/status. Its completeness checks are conservative
checks of this retained index representation, not proof that the archive lists
every possible scientific product. `OFFLINE_DIRECTORY_INVENTORY` establishes no
instrument mode, exposure overlap, good-time interval, event content, viable
control bundle or discovery. A changed archive layout may legitimately STOP.

## Reviewed SHA-256 snapshot

| File | SHA-256 |
| --- | --- |
| `XMM-C0c2-2026-09-12-data/listing.py` | `52dc2505e5adc7f0d09ca3fe017b1da1ad8fe482172d933f91a9a8658388f489` |
| `XMM-C0c2-2026-09-12-data/test_amendment.py` | `1e3cfa5fa6a9b9d62716022000c053c897940a4098ef26057d9fde2fa2ba104d` |
| `XMM-C0c2-2026-09-12.md` | `12e192f1daae9712c7c631ba88b578fd982b306ea7315276eb807b4f0c8e51d2` |
| `xmm_inventory.py` | `fe6b178e6f66793dcfd703b22850f296a226bc8a1acf314676c68a72534ba9c6` |
| `test_xmm_inventory.py` | `82fc7ba4efecccc8ff74ed70998533f5a6c5ecc945d22919a3207e84f3df00b7` |

Implementation, tests and protocol are author-owned and were not edited by this
reviewer. No remaining material pre-execution blocker was identified.
