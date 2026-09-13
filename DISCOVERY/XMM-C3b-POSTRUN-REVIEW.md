# C3b independent post-run review

Audit date: 2026-09-12 local / 2026-09-13 UTC. Review scope was retained
receipts, hashes, request ordering and resource accounting only. No new HTTP,
product reads, array interpretation or acquisition/replay execution was made
by this audit. The parent separately reports `PASS_OFFLINE_REPLAY STOP`.

## Outcome

**The C3b STOP is supported; the geometry bundle was not acquired.**
The only new request was the attitude-file HEAD. Its retained receipt records
HTTP 404 at `Sun, 13 Sep 2026 00:53:35 GMT`, for the exact planned URL and
filename. The worker stopped with `STOP_HTTP_IDENTITY_OR_STATUS`, return code
1. Parent assessment completed and retained STOP, not the success label.

The complete four-slot worker and parent ledgers agree:

| Slot | Planned request | Retained status |
| --- | --- | --- |
| 1 | Attitude HEAD | FAILED, HTTP 404 |
| 2 | pn exposure-map GET | NOT_ATTEMPTED |
| 3 | MOS1 exposure-map GET | NOT_ATTEMPTED |
| 4 | Attitude GET | NOT_ATTEMPTED |

Only slot 1 has request/HTTP/result receipts. Its start elapsed time is
0.203 seconds, within the configured worker deadline. The frozen HEAD
collector never reads a response body; the error response's advertised
`Content-Length: 19` is not an accepted product size or retained body.
There are no products or headers directories and no downloaded/expanded bytes.

## Independent verification

- All **7 C3b outcome artifact hashes**, **6 worker artifact hashes** and
  **9 dependency hashes** match the retained files. Source, tests and protocol
  snapshot match the pre-execution review; the current protocol matches its
  snapshot. Inventory/index hashes match the bound C0c2 evidence.
- The worker-start binding hash matches run-start. The two imported successful
  prior HEAD HTTP records and result records match the originals exactly,
  including hashes, URLs, validators and sizes 503855 / 275217 bytes. No
  successful prior HEAD was refreshed or converted into a downloaded product.
- The original C3 outcome hash remains the protocol-pinned value below.
  All **13 C3 outcome artifact hashes**, **12 worker artifact hashes** and
  **7 dependency hashes** also verify, as do its source, tests and snapshot.
  Its original MOS2-HEAD STOP remains unchanged.
- All **28 files** in the C3 and C3b data directories had identical hashes
  before and after these read-only checks. No frozen artifact was edited.

Resource receipts are consistent with the actual JSON file sizes:

| Quantity | Bytes |
| --- | ---: |
| Compressed / expanded products | 0 / 0 |
| Worker JSON snapshot, excluding worker-result and outcome | 7359 |
| Parent JSON snapshot, excluding outcome | 8433 |
| Complete final JSON set | 9854 |
| Recorded worker peak memory | 50999296 |
| Recorded parent peak memory | 50266112 |

JSON is below 10 MiB and both recorded peaks are below 500000000 bytes.
These are retained acceptance receipts, not an independent measurement of
process lifetime or proof of an OS-enforced memory allocation limit. The
source/helper/configuration hashes retain the specified 120-second worker
and separate cleanup contract.

## Provenance and scientific boundary

| Artifact | SHA-256 |
| --- | --- |
| C3b source | `bc8f6ab039234e98347329412e706547c0c91e543ebffbfe9d8a4d1f5a4b7b92` |
| C3b tests | `e3295401c6801193a11a2d046acecfc80ceabb9348a685984203e970f7cefaff` |
| C3b protocol/snapshot | `7025a0af3a2714528b8a4360487760972e5977c48eb232a236c8ec239a2ff18a` |
| C3b outcome | `b785146094702538ff8c2ef2300ba243133f44309bf0f1f63c7af0aa90fe7229` |
| Original C3 outcome | `62dedbf1b55a48210f447e454f0f1f574b7b8b073a873f48bce2c587cdf7fa5e` |

This establishes endpoint/request failure, not physical absence of attitude
data from every archive, unusable scientific coverage, or a negative burst
result. A directory listing is not proof that each listed entity can currently
be retrieved. The control bundle still lacks these verified geometry inputs;
no aperture, pointing-stability, counts, recovery or discovery claim follows.

Researching a documented official individual-product source is a reasonable
next step. Any subsequent acquisition needs its own prospective identity,
transport, size and provenance contract. This audit does **not** authorize
retry, direct GET after a failed required HEAD, assumed exposure/attitude
values, or weakened geometry/negative-control/statistical gates. Preserve both
STOPs and the original unavailable-camera/multiplicity accounting.
