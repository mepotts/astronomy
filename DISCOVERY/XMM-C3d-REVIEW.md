# C3d independent pre-execution review

September 12, 2026. **GO for the separately frozen, one capped GET and
header-only inspection contract.** No remaining material blocker identified.
This does not change C3c's missing-length STOP or authorize any scientific
array interpretation, extra request, archive extraction or publication.

## Independent checks

The reviewer read the complete protocol, source and all final tests, plus the
reused C1 expansion, header, path, hash, JSON/resource and deadline interfaces.
Only this review document was added; no source, tests or frozen artifacts were
edited. No live HTTP or real product payload was read.

- **15 authored tests independently PASS**, with pinned Ruff also PASS.
  Both raw FITS and gzip fixtures exercise missing-length GET, expansion,
  header inspection, worker/parent assessment and offline replay. Each positive
  fixture makes exactly one mocked GET; nonzero helper status cannot pass.
- Tests verify optional duplicate-equivalent lengths, premature EOF, advertised
  length overrun and unknown-length overflow. They retain exactly the applicable
  cap and consume only one additional overflow-detection byte in the fixtures.
  Invalid HTTP/encoding/media/disposition stops before body reads. CRC failure,
  expansion overflow and unknown magic preserve bounded evidence and stop.
- Exact file-set and header-replay mutations are rejected. Prior/current helper
  isolation, JSON binding roundtrip, failed-receipt values, prelaunch accounting,
  timeout/truncated markers and exclusive repeat blocking are covered.
- **8 additional independent in-memory hostile metadata/filename checks PASS**,
  together with absent-length/equivalent-duplicate acceptance, actual helper
  isolation and reduced-cap assertions.
- Executed the **actual prior C3c metadata-only replay and complete C3d binding**
  under a network-forbidden Session mock: PASS. All nine dependency hashes bind;
  binding is exactly JSON-roundtrip stable. Prior replay retains its original
  directory and 30-second configuration, while the current helper has the new
  directory and 60-second configuration. No C3d attempt/output marker exists.

## Transport and provenance assessment

The exact fixed URL uses a fresh anonymous session without environment
credentials/proxies, cookie reuse, redirects, Range or a retry adapter. Safe
metadata and exact expected basename are checked before streaming. No missing
HEAD length or validator is invented. Optional GET Content-Length must be
positive, unambiguous, within the local cap and equal to retained bytes.

The streaming loop caps retained raw data at 2097152 bytes (or the smaller
advertised length) and uses one extra byte only to detect overflow. HTTP
decompression is disabled. Format is determined from actual magic, not FTZ
suffix or media type: only the specified raw FITS primary-card prefix or gzip
signature is admitted. TAR/ZIP and alternative filenames are not extracted.

Raw FITS is copied with matching byte/hash records. Gzip expansion invokes the
verified bounded CRC/EOF-checking helper and retains no more than 33554432
expanded bytes, including a failed partial. Parent verification repeats actual
magic, file sizes/hashes, raw-copy equality and header inspection, with exactly
one raw, one expanded and one header file. Gzip CRC completion is the bound
worker's recorded expansion check, **not independent re-decompression on replay**.
The frozen structural reader's header/seek and conformance/checksum limitations
remain; this is not interpretation of the skipped arrays.

Source/tests/protocol, prior outcome/safe HTTP, nine dependencies, runtime and
actual configuration are bound. The verified process-tree helper limits the
worker to 60 seconds with separate cleanup. The 500000000-byte peak is monitored
acceptance, not OS-enforced allocation. Free space is checked before the request.
The 1-MiB aggregate JSON budget, including private full headers, overrides the
larger nominal per-header ceiling; 65536 bytes remain reserved for terminal
receipts. Earlier reviewed terminal memory/failure handling is reused.

Failed receipts retain exact keys and safe identifier/STOP-code values. Exclusive
markers and the one-slot ledger account for partial/prelaunch/timeout outcomes.
Catastrophic replay is explicitly failure-artifact-only, never product validation.
Raw disposition, cookies and arbitrary warning/exception output are not public
receipts. Root ignore rules for the new `products/` and `headers/` directories
are present; the parent owns final pre-execution Git verification and freeze.

## Final reviewed identities

The author incorporated the minor failed-receipt value-validation consistency
suggestion before the final suite. No additional implementation change is needed
by this review and no rule was selected from a live C3d outcome.

| Reviewed file | SHA-256 |
| --- | --- |
| `XMM-C3d-2026-09-12-data/acquire.py` | `87caca0e856065d33ff4f60404399915eed8a4b50a9afa7d0106f98fb691f825` |
| `XMM-C3d-2026-09-12-data/test_acquire.py` | `8d313d56946a5f68fb30af8b39c41910121a079d646ccff9e074dcbfc809cf56` |
| `XMM-C3d-2026-09-12.md` | `8bee82d6c849bd94479f40615817cc2d14776d439b80b62a8b47c84871beed6a` |

Even `ATT_PRODUCT_RETAINED_HEADERS_ONLY` will not establish compatible attitude
times/coordinates, pointing quality, accepted aperture geometry, recovered
bursts or discovery. Actual header adjudication and a separate prospective
value-reading contract must precede those questions.
