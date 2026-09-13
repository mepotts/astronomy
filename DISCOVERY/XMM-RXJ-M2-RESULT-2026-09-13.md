# RXJ M2: filtered summary route advertises TAR

One request executed after exact-byte freeze **e38e438** on 2026-09-13.
The response was HTTP 200 with `application/x-tar`; the frozen raw-HTML
contract stopped at **STOP_NOT_HTML before body access**. No summary or
archive body was retained, and no transport-EOF receipt exists. Worker exit
1, parent assessment complete; root's one offline replay passes STOP.

## Direct evidence

The [HTTP receipt](XMM-RXJ-M2-2026-09-13-data/http.json) records the exact
four-selector URL, matching final URL, and server Date
`Sun, 13 Sep 2026 05:15:05 GMT`. No Content-Length or Content-Encoding was
retained. Disposition classification is REJECTED, with no raw value or filename
digest retained. Its precise rejection reason cannot be reconstructed; it must
not be reported as an observed particular archive filename.

The first frozen failure is MIME, not disposition. That response establishes
the advertised packaging of this request, not package validity, member count,
summary identity, file availability, observation mode or scientific recovery.
It does not authorize a broad observation bundle. No retry, redirect, HEAD,
linked request, decompression, extraction or scientific-product access occurred.
The statement about zero body access concerns the explicit body-reading code;
socket-level buffering was not separately instrumented.

Five JSON receipts total **4,495 bytes**, plus the 4,147-byte protocol snapshot.
No private HTML exists to publish. Worker output is represented by its encoded
length (53 bytes) and digest, not raw text.

| Artifact | SHA256 |
| --- | --- |
| Outcome | f57b43c9a551a7812afed2be845e1dc88b579251ef36f6e1cceceba3cf20705a |
| Run binding | f7a8821ce4a71bcfb0ec508bfa1f835016fecf1af3488ec19f5aee77f1aed02b |
| HTTP receipt | ec3da2ce6dcd0de66e30e6b18cbb96e5d14aa5ad902083bf4104da5c7a5254fc |
| Worker result | cbedbee2f12f7219d03887b8490633aed651f890ed48f1911aa4fdb88c82c3df |
| Protocol snapshot | d26c216910fc9c72f9134e439b012f77d6e2acfc09f3df74eec61f560a5e0871 |

## Verification and next action

Eleven synthetic tests and Ruff pass. The [independent review](XMM-RXJ-M2-REVIEW.md)
includes the postrun receipt-only audit: 12 dependencies, privacy bindings,
five artifact references and the preserved STOP all match. Root read the full
preflight and postrun evidence. No additional request or numerical replay was
made by that review.

Preserve the executed protocol/runtime/tests and failed result. The next
prospective route is a separately bounded, **summary-only plain-TAR** request
with the same selector, followed by offline member validation and HTML
adjudication. The body and any derived HTML must stay private; links, special
members, ambiguous identity and excess content must not become an automatic
extraction or broader download. The first control's uncalibrated counts and
the RXJ calibration/recovery draft's open gates remain unchanged.
