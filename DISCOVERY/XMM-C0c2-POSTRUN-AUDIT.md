# XMM C0c2 independent post-run audit

2026-09-12: **PASS for retained directory metadata and offline inventory only.**
The reviewer made no network request, followed no product link and changed no
executed artifact. This note is the only file written by this audit.

## Independent checks

- All ten original C0c outcome artifact hashes still match. Its HTTP-200,
  cap-truncated `STOP` is preserved, not reclassified.
- All nine C0c2 outcome artifact hashes match. The worker and parent both report
  `HTTP_INDEX_RETAINED`, worker return code 0, one request attempt and zero science
  products fetched. The response body is 319808 bytes; safe HTTP metadata records
  status 200, the exact authorized PPS directory URL and ISO-8859-1 HTML content.
- Read-only `wrapper.load_core().validate_completion()` passes, checking the
  pinned original core, source/protocol/helper identities, attempt markers,
  body receipt, cap and HTTP contract. No `run`, `_worker` or `collect` was called.
- The frozen offline parser reproduces the saved `inventory.json` object exactly.
- A separately implemented HTML anchor collector finds 2198 anchors: five known
  navigation links and 2193 unique file hrefs. Their ordered names match every
  saved inventory entry. Every entry has `exact_bytes: null`.
- All 22 stage files present at the audit's start were byte-identical afterward.

## Filename-only inventory findings

There is exactly one matching FTZ filename in each of these four categories:

| Category | Filename | Displayed size |
| --- | --- | --- |
| PN event-list name | `P0884250101PNS003PIEVLI0000.FTZ` | `104M` |
| MOS1 event-list name | `P0884250101M1S001MIEVLI0000.FTZ` | `7.3M` |
| MOS2 event-list name | `P0884250101M2S002MIEVLI0000.FTZ` | `9.5M` |
| EP observation source-list name | `P0884250101EPX000OBSMLI0000.FTZ` | `118K` |

These are naming-pattern matches, not inspected file contents. Displayed sizes
are retained verbatim, not exact bytes or verified bounds. No claim is made
about valid FITS structure, camera modes, simultaneous coverage, good-time
intervals, photon availability, source identities, a usable control bundle or a
discovery. The retained index is complete under the reviewed transport/HTML
contract; that does not prove the archive exposes every possible product.

## Audit identities

| Artifact | SHA-256 |
| --- | --- |
| Original C0c `outcome.json` | `54f2b5bc721877494714242d590780c13cada9196ef0aab42d0144fff880c73a` |
| C0c2 `outcome.json` | `2af0b075c8ba2aa035ce29a1e84706760f5bc42a658ac3e1183d0a61dce34412` |
| C0c2 `index.html` | `97f9372b999b354ebcbff51a4b42af885433de598795a6a58656ef1e09bac258` |
| C0c2 `inventory.json` | `6ddb4a357439922dbefaa51e365b53802e6d031d079348706274555f4e063c23` |

Any product acquisition requires its own explicit file selection and bounded
transport contract. This successful metadata step does not expand that authority.
