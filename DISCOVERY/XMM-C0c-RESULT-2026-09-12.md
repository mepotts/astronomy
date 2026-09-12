# XMM C0c result — partial directory response, STOP

Independent offline audit, 2026-09-12. The single permitted metadata GET returned
HTTP 200 but exceeded the frozen 262144-byte retained-body cap. The worker
reported `ValueError: STOP_BYTE_CAP`, returned code 1, and the parent correctly
reported `STOP` / `STOP_WORKER`. The body is **partial**, not an accepted complete
inventory. No retry or linked science-product request was made by this reviewer.

The exact requested public PPS URL is present consistently in the HTTP receipt
and both exclusive attempt markers. The response declares
`text/html;charset=ISO-8859-1`; no Content-Length was advertised in the retained
safe headers. The HTML title/header identify the expected observation directory,
but the retained body ends inside a product href. Thus HTTP success and matching
directory identity do not establish inventory completeness.

The worker retained exactly 262144 bytes, SHA-256
`598c5279333b45e8ac3c35bb4ccab45cd55a58ec2ca5d5aac862c967a38c862e`.
Frozen code detects overflow by permitting one extra read byte but retains no
more than the cap. The complete response length is unknown. Both worker and
parent receipts record zero science products fetched; the worker records one
request attempt. Parent elapsed time was approximately 0.719 seconds.

All ten artifact hashes in `outcome.json` were independently recomputed and
matched. The source, byte-preserved protocol snapshot and pinned process-tree
helper match the identities in `run-start.json`. No frozen C0c file was changed.
The audited outcome SHA-256 is
`54f2b5bc721877494714242d590780c13cada9196ef0aab42d0144fff880c73a`.

Do not use this truncated response to assert absence of a product, total product
counts, exact download bytes or a usable control bundle. Human-readable directory
sizes remain rounded/ambiguous rather than exact byte lengths. A separately
frozen cap-only C0c2 protocol may authorize one new bounded metadata request; it
must preserve this STOP and does not itself authorize any product download or
scientific measurement.
