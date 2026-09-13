# RXJ M1: JSON metadata retained, individual-name profile STOP

One ESA TAP request executed after exact-byte freeze **b787a9e** on2026-09-13.
HTTP200 returned363bytes of JSON; the frozen parser stopped at
**STOP_COLUMN_SCHEMA**. Worker exit1, parent assessment complete. One root
offline replay passes `PASS_OFFLINE_REPLAY STOP`, preserving the failure.
No retry, count query, linked request or scientific product acquisition.

## Transport evidence and the actual first failure

The exact query/encoded URL remain in the
[run binding](XMM-RXJ-M1-2026-09-13-data/run-start.json) and
[HTTP receipt](XMM-RXJ-M1-2026-09-13-data/http.json). HTTP200,
application/json, no retained Content-Length or Content-Encoding; server Date
`Sun, 13 Sep 2026 04:51:51 GMT`. The complete363byte body is retained and hashed.
Neither the1MiB body cap nor30second worker deadline was exceeded.

The [unchanged protocol](XMM-RXJ-M1-2026-09-13.md) requires arraysize `*` for
both character columns. The response instead declares obsid as char/arraysize
`10`, and filename as char/arraysize `*`. The initial schema check therefore
stops **before any row is accepted by the frozen parser**. A fixed-width string
declaration is not itself evidence of bad archive metadata or scientific absence.
The successful metadata-record label was not earned.

## Separate manual inspection, not a changed parser outcome

Root inspected the tiny [retained response](XMM-RXJ-M1-2026-09-13-data/response.body)
after STOP. It contains two rows for0851180501, with filename values
`0851180501.tar.gz` and `*/*`. These are an observation archive name and a
wildcard-style entry, **not an individual PPS product inventory**. The wildcard
also violates the predeclared ASCII-basename rule; merely allowing fixed-width
obsid metadata would not make this response pass the full profile.

No individual event/source-list/map/summary filename, exact byte size, public
access, observing mode, exposure, calibrated control or discovery is established.
The archive name is not permission to fetch its bundle. This inspection does
not retroactively label M1 successful, and no protocol/source/test was edited.

## Reproducibility and limits

Five JSON receipts total4608bytes, plus363raw-body bytes and the protocol
snapshot. Worker-output receipt is53 encoded bytes and a SHA256 only. Raw
metadata and safe response headers are retained; no arbitrary exception text,
cookies or scientific coordinates are introduced. All stage dependencies and
the M0 mirror404 remain bound and unchanged.

| Artifact | SHA256 |
| --- | --- |
| Outcome | 159ee0322ae964ec20e4f79471e927dc7dc93a08adcb0a1f8b2b751ca843b384 |
| Run binding | e507b4885dca255f13003bee22c3d8827ae2748d4f0ac0e7627ec79bf2eaf085 |
| Raw response | 75d75114d209795f7177124f3eb44fc5c6f6d15e3aa4f485d36364df9aeab635 |
| HTTP receipt | 1b81554f350f3b78a2a3cb74dc628cb3291c3b9d23814764a60a57e3caaea356 |
| Worker result | cd634e91e4a68013572f4666a6842145cceb34c5657b8e43b6822d8c90b10e8b |
| Runtime | 953d28ef3c079faf11a660bdae8c7c32cd1d8e0259c72bde9c0f794d30b5fb91 |
| Tests | 0885a3b200f4a4f1bd8281b963e19362b2bce41e995ebc7aafc0d79df5ae57ae |
| Protocol | 64fe04e56f8dac954a1394ab65934fd8eb4d88797d0b4701fe645d0a2c009fc4 |

Run and replay commands, each executed once:

```
dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/XMM-RXJ-M1-2026-09-13-data/listing.py run
dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/XMM-RXJ-M1-2026-09-13-data/listing.py replay
```

Eleven synthetic tests/Ruff and12dependency binding checks passed before
freeze; [independent review](XMM-RXJ-M1-REVIEW.md) records the bounded preflight.
An offline STOP replay does not constitute an additional network request or
successful product-name interpretation.

Independent postrun review also passes: all 12 dependency bindings, six
artifact references, safe HTTP fields and the preserved STOP were checked
without another request, product access or replay. The stage bytes are unchanged.

## Next decision

Close this used attempt; do not build a parser amendment just to accept two
package-level entries. Investigate a documented, tightly filtered ESA summary
metadata-product selector for the same observation. Its packaging, member
identity, transfer/expansion bounds and interpretation must have a separate
prospective contract; no broad observation archive is authorized here. Preserve
the first control's completed C9 and the new field's unmet calibration gates.

The [next-step decision](XMM-RXJ-M1-NEXT-2026-09-13.md) specifies one separately
frozen raw-HTML summary request, followed by offline identity/table adjudication.
That request has not executed. A package response would stop, not trigger a
bundle download or automatic extraction.
