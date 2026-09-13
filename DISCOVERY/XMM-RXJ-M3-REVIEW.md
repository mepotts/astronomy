# RXJ M3 independent prospective review

**Scoped GO for root's exact-byte freeze and one separately approved summary-
only plain-TAR request.** Completed 2026-09-13. No actual request, archive,
summary body, science product, run preparation or earlier-stage replay was
performed by this reviewer. All archive/value probes used synthetic bytes.

## Final anchors

| File | SHA256 |
| --- | --- |
| `XMM-RXJ-M3-2026-09-13-data/listing.py` | `01564aff6d0873eb7a8bda42ddd408f085e85489e7410b739a1dfd9d40978472` |
| `XMM-RXJ-M3-2026-09-13-data/test_listing.py` | `d6ee89793f0b09ad1c53a240423c5c421048d1130f07922e16fab9ca344a8e8b` |
| `XMM-RXJ-M3-2026-09-13.md` | `230a900079e8220a7a29a5ceeb16a714cdfae684e525f83b783f7a26925a245a` |
| `xmm_summary_tar.py` | `f9ce311d0e70c3aa264ca885bd202f71f79f91e92c01c62affbaa9f68a11dfa9` |
| `test_xmm_summary_tar.py` | `eab791a332c26452e6ecd748ec7d349c3f22c54cafe93cc137276e1063b54ad4` |
| Stage `.gitignore` | `e661d747f8674d18ca00fca29f7cc1bb396be422b291695835bd30720afc5790` |
| Stage `.gitattributes` | `d6b49fe7b75027b320f3679bb020ad3deaa02986352176915829b44920a770e0` |

Read the complete adopted decision, helper/tests, runtime/tests and protocol,
including final changed sections. Also read the local Python implementation
of `TarInfo.frombuf` to check its normalization and extension behavior.
Independent commands:

```
# In DISCOVERY/XMM-RXJ-M3-2026-09-13-data
../../dyson-revet/.venv/Scripts/python.exe -B -m unittest test_listing -q
# In DISCOVERY
../dyson-revet/.venv/Scripts/python.exe -B -m unittest test_xmm_summary_tar -q
# Repository root, Ruff 0.16.5
dasch-pilot/.venv/Scripts/ruff.exe check --no-cache DISCOVERY/XMM-RXJ-M3-2026-09-13-data DISCOVERY/xmm_summary_tar.py DISCOVERY/test_xmm_summary_tar.py
```

**10 runtime tests + 11 helper tests PASS; Ruff PASS.** The final actual
metadata-only binding/JSON round trip independently passed **20 dependencies**
plus the two private-storage rule hashes. Requests Session/collect/worker
tripwires and product/`summary.tar`/`summary.html` open guards were active.
The root separately reports Git ignore checks for both private paths; this
reviewer inspected and hash-verified the rules. Neither private file is meant
for publication; ignore rules are not filesystem encryption.

## Pure TAR contract

The helper has no filesystem, network or extraction operation. At most 1 MiB
of caller-supplied bytes is admitted. It walks physical 512-byte headers itself,
checks each checksum with `TarInfo.frombuf`, caps non-terminator headers at16,
and rejects unsupported types before any library-driven extension traversal.
There is no `TarFile` member iterator hiding PAX/GNU longname records, no
`extract`/`extractall`, and no creation of member-named paths.

Exactly one positive regular member at most262,144 bytes is allowed, plus
zero-sized directories. Payload/padding bounds, duplicate normalized names,
basename observation/SUMMAR/HTM positions, two zero end blocks and all-zero
trailing blocks are checked. An extra regular file, concatenated archive,
truncated tail or unsupported special/link/extension record is not ignored.
Alignment padding within a member need not be zero in the final contract;
the earlier extra zero-padding gate was removed before execution and is
covered by an acceptance regression. End-of-archive zero requirements remain.

Path handling is lexical: relative ASCII, bounded length/components, harmless
dot/empty separator normalization, no traversal, drive syntax, backslashes,
percent interpretation or OS resolution. USTAR prefixes and ordinary legacy/GNU
headers are supported without requiring a particular magic brand or directory
prefix. Owner/group text is irrelevant and never serialized.

The review explicitly identified `TarInfo.frombuf`'s legacy NUL-type trailing-
slash directory conversion and directory slash stripping. The final protocol
admits that legacy interpretation only with size0. Parsed-name hashes refer to
the library-resolved name, not literal raw name-field bytes; complete header
hashes preserve the raw representation. This distinction is documented before
seeing any archive. No hidden extension semantics are admitted by that choice.

The sole accepted payload slice is copied only after the entire archive has
validated. It is returned privately, alongside a safe inventory of hashes,
sizes, offsets and types. No raw path, owner text or HTML enters that inventory.
Input/output caps bound work and buffers, not Python object overhead or an OS
memory quota.

## Runtime composition, access and failure handling

The new verified-buffer M2 composition substitutes exactly three raw-body
literals to `summary.tar` before the already reviewed isolated M0 composition.
Inherited source files are unmodified; source buffers and helper are hash-bound.
Stage/source/configuration and child entrypoint resolve to M3. Inherited one-
shot guards, safe response/exception schemas, reserve and replay closure remain.
No prior-stage command or scientific replay is invoked.

The sole unchanged selector is the adopted observation/PPS/SUMMAR/HTM AIO URL.
No HEAD, redirect, retry, Range, broadened selector, second request, archive
link or M1 wildcard is used. Anonymous-session and framing checks remain;
only plain-TAR MIME is admitted without content compression. Outer disposition
classification is deliberately non-authoritative: REJECTED does not infer a
package name or reject an otherwise valid inner summary. Raw disposition text
is never retained.

Streaming retains at most1MiB plus one unretained overflow-detection byte.
EOF is separately recorded. Positive declared length must be within cap and
match the complete response. The same 30-second worker tree deadline covers
transfer and inspection. Parent/replay each perform another input-size-bounded
local archive validation; this is not a new request or a separate asserted OS
time/memory limit. The caller hashes raw bytes before helper inspection and
checks the helper's raw digest.

Only the worker-active path may create fixed-name private `summary.html`.
Parent/replay recompute the archive inventory and compare the existing HTML's
exact size/hash; they never recreate or repair it. Success requires a complete
nonempty admitted file. The initial read raised a zero-byte partial-copy
concern; the final source already permits such a bounded failed artifact, and
a new targeted regression proves an exclusive-open/write failure remains STOP
with its empty file retained and replayable. This is not acceptance of an empty
summary as success. Unsupported archives likewise retain raw bytes without
creating a summary. No automatic retry follows either failure.

## Independent synthetic evidence

The final helper was also exercised with **17 hand-built raw TAR cases**, not
archives produced by the same `tarfile` writer: payload sizes1/511/512/513/
262144, explicit USTAR prefix and root directory, legacy NUL directory, and10
unsupported extension/link/special types. Separate checksum construction,
expected offsets, exact payload bytes and SHA256 checks passed. These complement
the author suite's duplicate/path/cap/truncation/checksum/terminator cases.

Five additional full-runtime fixtures passed:

- A valid TAR padded to exactly1MiB completes one mocked GET, exact EOF,
  worker/parent verification and the expected fixed private copy.
- Replace private HTML with equal-length different bytes and rehash the outer
  inventory: replay stops at `STOP_PRIVATE_HTML_REPLAY` without repair.
- Change the inventory canonical-path digest and rehash receipt artifacts:
  replay stops at `STOP_INDEX_REPLAY` after recomputation.
- Remove EOF evidence and update outer hashes: replay rejects the private
  artifact as ungrounded, without creating transport evidence.
- After an unsupported extra-member STOP, a second run is rejected as
  `STOP_ALREADY_ATTEMPTED` with no second mocked GET.

All tamper replays had network tripwires and left fixture files byte-identical.
Author runtime tests additionally cover seven-byte partial transfer, cap-plus-
one overflow, packaging/framing rejection before body, optional malformed
disposition, safe receipts, nonzero worker code, missing-copy rejection,
prelaunch STOP and the zero-byte write-failure regression. The terminal reserve
is inherited from hash-bound M2; its separate budget regression was reviewed
and is not falsely counted as a new M3 budget fixture.

## Scientific boundary

The strongest result is `SUMMARY_MEMBER_RETAINED_UNADJUDICATED`. Successful
transport and a correctly named member do not establish body observation
identity, a usable exposure table, mode, complete inventory, available photons,
live exposure, clean negatives or source recovery. No HTML semantics, footer,
coordinates, links or time-series analysis are inspected by this stage. An
error page can remain inside an otherwise valid named member.

M2's raw-HTML STOP and M1/M0 outcomes remain unchanged. An unsupported archive
can motivate only a separately reviewed offline decision, not a repaired
success or another GET. This review authorizes neither a science-product
acquisition nor a discovery claim.
