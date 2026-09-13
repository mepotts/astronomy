# RXJ M3: private package retained, summary profile STOP

One request executed after exact-byte freeze **56819bc**. HTTP200 returned a
complete **1,044,480-byte** entity, within the 1 MiB cap. The frozen worker
stopped at **STOP_TAR_HTML_SIZE**; no summary.html was created. Worker exit1,
parent assessment complete, one invocation and zero scientific products.
Root's one offline replay passes STOP. No retry or further acquisition.

## Transport and failure evidence

The [HTTP receipt](XMM-RXJ-M3-2026-09-13-data/http.json) records the exact
unchanged four-selector URL and matching final URL, `application/x-tar`, and
server Date `Sun, 13 Sep 2026 05:30:53 GMT`. Content-Length and Content-Encoding
were absent from the retained safe headers. Outer disposition remains REJECTED
but is non-authoritative in M3; no raw disposition or inferred filename is saved.

The separate [EOF receipt](XMM-RXJ-M3-2026-09-13-data/transport.json) records
the complete byte count. The archive stays locally ignored as summary.tar.
It is not linked or committed because it may include contacts or coordinates.
Its SHA256 is
`fa3c45838875c61f68e07508d862fc56d32e83f0b39ed3f6b1bef2207b9ccbe2`.
No member body was copied or semantically interpreted by the frozen stage.

Six JSON receipts total **6,295 bytes**, plus a 4,641-byte protocol snapshot.
Worker output is a 53-byte encoded length and digest, not raw exception text.
The parent/replay preserve failure without running successful-member validation
or manufacturing an HTML copy. Complete transfer is not a valid package profile.

| Artifact | SHA256 |
| --- | --- |
| Outcome | 1a897ff9dbf74f0b88c7428b2dbd63dc16944036191256374204056d3b3f5678 |
| Run binding | e0a6eeb2f29c519f44f41086ea9eb7686dea6c15aebdc35d20985a1ee1c494f2 |
| HTTP receipt | 6b2e62f84d8412f00e8ca60f73bcbc400f1009010f21556c381a5fb0cf5924f0 |
| Worker result | 990ffc01f4964e33061b31c1928ce7ee93fb3f1de2e3f1eac4fe584c6c080c6d |
| EOF receipt | ce59925f72d7675fd155eced7c5b6d0c1465258254c468bedf2046b7d249b2a0 |

## Separate header-only diagnosis after STOP

Root hash-checked the retained package and inspected bounded physical headers,
without invoking the frozen validator again or reading HTML semantics. Four
regular, checksum-valid headers occur before the first zero block. All four
basenames match the requested observation/SUMMAR/HTM field-position pattern.
This is not the frozen parser's accepted inventory, nor a proof that everything
after the first zero block is valid padding.

| Header offset | Payload offset | Declared member bytes |
| ---: | ---: | ---: |
| 0 | 512 | 872917 |
| 873472 | 873984 | 48229 |
| 922624 | 923136 | 25265 |
| 948736 | 949248 | 86689 |

The first member exceeds the frozen 262,144-byte inner cap and explains the
reported failure. Merely increasing that cap would not satisfy the separate
exactly-one-file condition. At offset1,036,288 a zero block begins, but the
remaining8,192 bytes are not all zero, also inconsistent with M3's tail rule.
Do not silently discard that ambiguity, choose the smallest member or label
the entire package accepted. Names, paths, owner fields and payload text remain
private; roles/version relationships are a subsequent offline question.

## Verification and next step

Ten wrapper tests, eleven helper tests and Ruff pass; the independent
[review](XMM-RXJ-M3-REVIEW.md) covers runtime bindings, synthetic TAR cases,
failure preservation and private-copy replay. Postrun receipt audit is separate
from the header diagnosis. The executed source/tests/protocol and all earlier
results remain unchanged.

The completed postrun audit verifies all20 dependencies and seven artifact
references. Six non-archive artifacts were rehashed; the reviewer cross-checked
the TAR digest between receipts and its size by stat without reopening it.
Root separately rehashed the archive during header diagnosis. The subsequent
[offline decision](XMM-RXJ-M3-NEXT-2026-09-13.md) identifies distinct documented
EP/OB/RG/OM roles and two zero terminator blocks followed by7,168 heterogeneous,
uninterpreted bytes. This is neither a duplicate-version diagnosis nor proof
of harmless padding/corruption. All four payloads remain semantically unread.

Next: specify bounded **offline-only** inspection of all four retained members
and the trailing-data issue. No new download is needed to investigate these
bytes. Any later semantic reading must account for every member and establish
explicit observation identity, role/provenance and exposure-table consistency;
it cannot promote M3's STOP or imply calibrated recovery. No photon acquisition,
unknown-source scan, discovery or scientific submission has occurred.
