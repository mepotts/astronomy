# RXJ M0 result: observation-index HTTP 404, no body or products

One request executed on2026-09-13 after exact-byte freeze **6512188** under
the [prospective contract](XMM-RXJ-M0-2026-09-13.md). Outcome **STOP_HTTP_STATUS**:
the fixed HEASARC observation-directory URL returned404. Parent assessment
completed with worker exit1. Read-only replay passes `PASS_OFFLINE_REPLAY STOP`;
it validates the retained failed request, not a complete index.

The exact request was the constructed metadata-only URL
`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0851180501/`.
No redirect, retry, PPS request, HEAD, alternative observation or scientific
product request followed. The worker's one invocation marker is retained.

## What was actually retained

[Safe HTTP receipt](XMM-RXJ-M0-2026-09-13-data/http.json): status404,
Content-Type `text/plain; charset=utf-8`, Content-Length19, server Date
`Sun, 13 Sep 2026 04:35:10 GMT`. Validation stopped on status before body
reading: no `index.html` exists and worker body record is null. The declared
19bytes is **not** a count of body bytes consumed by this program. HTTP
library/socket buffering is not instrumented, so zero retained/read body
does not claim zero network transport bytes.

Five JSON files total2518 bytes; the protocol snapshot is separately retained.
No header outside the six-field allowlist or arbitrary worker error text is
saved. The parent captured only worker-output encoded byte count53 and hash,
not raw text. No memory-limit or astronomical availability conclusion.

| Artifact | SHA256 |
| --- | --- |
| Outcome | 57e0e1ec8a149a6e90a1e1847f089c1a4d3529480f1416704f3ac964f37d82c7 |
| Run binding | 7bc6f5658753058f9369cabca6aa33b962b2739f5855c44046d07637f653dbed |
| HTTP receipt | decbfbc7e9ed32a3fde544849b6cc5bb2e40f02c64998f24a85bee4225f76ff8 |
| Worker result | ba6024fa3818880f96e7bb7fc7bc2b40fce5a7bcc120bae7e6e320770c6df81f |
| Source | fe664f73447eae02345358b03c6c7754628e7d9f240028c8720ed2786b462a38 |
| Tests | 963e082830d97ce2c743d2003799c2d846e0ead7139ea670a7f5ba8df0e9fdb6 |
| Protocol/snapshot | b864f9daee136bb27da7d0a94bcd095fdc86c6ea92636ac337f4aab3a1209e18 |

Commands each executed once:

```
dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/XMM-RXJ-M0-2026-09-13-data/listing.py run
dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/XMM-RXJ-M0-2026-09-13-data/listing.py replay
```

Seventeen synthetic tests, Ruff and four-dependency binding checks passed
before freeze; [independent prospective review](XMM-RXJ-M0-REVIEW.md) has the
failure/privacy evidence. This successful failure replay does not reverse STOP.

## Decision

The one-shot experiment is closed with its failure preserved. A404 for this
constructed route is not proof that observation0851180501 is absent, private,
or unavailable from another documented archive interface. No camera modes,
exact product sizes, region usability, photons or discovery were established.
Do not reopen this stage or silently substitute a different target.

Next is a bounded documentation-only check for a structured same-observation
metadata alternative, followed by a separate prospective request contract if
justified. Preserve the [ancillary-first calibration direction](XMM-CALIBRATION-NEXT-DECISION-2026-09-13.md)
and the unchanged first control's [C9 recorded counts](XMM-C9-RESULT-2026-09-12.md).

Independent receipt-only postrun review (appended to the linked review) passes
all five artifact references, four dependencies, exact STOP/HTTP schema and
resource totals. No request, replay or product open by the reviewer. Root read
the full postrun section; it leaves both the failed attempt and interpretation
limits unchanged.
