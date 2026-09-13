# RXJ M5 result: first event-product transfer interrupted at deadline

**STOP; incomplete download, not a scientific negative result.** Executed once
after freeze commit `d76223b` under the [reviewed protocol](XMM-RXJ-M5-2026-09-13.md).
All 17 bound files matched their committed bytes before the acquisition.
No retry, replacement selector or further request was issued.

## What actually happened

The first pn request returned HTTP200, exact final URL, `image/fits`, and the
expected disposition basename `P0851180501PNS001PIEVLI0000.FTZ`. The response
Date is `Sun, 13 Sep 2026 06:40:10 GMT`. No Content-Length, ETag or Last-Modified
was supplied in the retained safe headers. These facts identify the response
metadata; they do not authenticate an incomplete FITS product.

The single worker reached its 300-second tree-enforced deadline, return code124.
The deadline helper's 30-byte output is its timeout sentinel, not captured
scientific output. The parent could not complete assessment and retained
`STOP_INTERNAL`, rather than a completed slot or worker result. Do not rewrite
that stored code into a more specific result after execution.

| Slot | Retained evidence | Result |
| --- | --- | --- |
| pn / EPN S001 | Start marker, HTTP receipt, 28,311,552-byte raw partial | UNVERIFIED_ATTEMPT |
| M1 / EMOS1 S002 | None | NOT_ATTEMPTED |
| M2 / EMOS2 S003 | None | NOT_ATTEMPTED |

The raw partial is 27 MiB, retained privately in ignored `products/`, SHA256
`8e5e6b07f836967030e05594d519527829c7ea4429c442a21317d0f8a81f233d`.
No expanded file, header report or identity derivative exists. Exact bytes
returned by interrupted network calls, unread buffered bytes, complete response
size and worker peak memory are unknown. Retained file size is not a received-
byte total, compression validation or EOF. Early file-size observations were
zero; they do not prove the server had sent no bytes. No cause such as server
throttling, a broken product or a network outage has been established.

## Verification and limits

Root executed exactly one explicit local `replay`, which returned
`PASS_FAILURE_ARTIFACT_REPLAY STOP; product verification incomplete`.
This checks retained artifact hashes and safe binding/HTTP structure, not
successful product/header verification. The parent and replay performed no
header pass; all three parent started/completed flags are false. There was
no FITS semantic parsing, decompression, EVENTS/ancillary array decoding,
calibration measurement or source-recovery test.

Outcome SHA256:
`9eb6912a34cabdfad6c5da42d751e7be25c249ed72ec2910f194bdbca59119bb`.
The five public JSON files total 6,169 bytes. The separately retained protocol
snapshot is 7,602 bytes. Parent lifetime peak was 47,800,320 bytes; this does
not establish the hard-killed worker's peak. No complete worker receipt exists.
The [independent review](XMM-RXJ-M5-REVIEW.md) distinguishes preflight synthetic
verification from the subsequent receipt-only audit.

## Next decision

Preserve the frozen attempt and partial unchanged. Determine whether a separately
bounded continuation can authenticate byte-range reuse despite absent response
validators; do not append speculatively or call the partial a valid gzip/FITS
file. If that cannot be established, explicitly choose a new, separately named
acquisition with a justified larger wall-clock allowance and unchanged identity,
privacy and size constraints. A previous deadline is not a scientific rejection.
The conditional [post-header calibration draft](XMM-RXJ-POST-HEADERS-DECISION-DRAFT.md)
has not become executable: it first needs authenticated complete products.
No discovery is claimed; the discovery goal remains active.
