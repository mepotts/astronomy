# C3d independent post-run review

September 12, 2026 local / September 13 UTC. **The retained
`ATT_PRODUCT_RETAINED_HEADERS_ONLY` result is supported within its scope.**
This audit checked retained metadata, hashes, exact file sets, configuration
and accounting. It made no HTTP request, decoded no scientific arrays and
did not rerun acquisition, decompression or header replay. The parent separately
reports successful owner-context offline replay.

## Acquisition and product evidence

Exactly one GET is accounted for, at the fixed AIO URL and expected ATTTSR
filename. The request-start marker records elapsed 0.188 seconds. HTTP 200 is
retained with `image/fits`, date `Sun, 13 Sep 2026 01:30:25 GMT`, and parsed
inline disposition naming `P0884250101OBX000ATTTSR0000.FTZ`. Content-Length,
ETag and Last-Modified remain absent; no invented size/validator is used.

Worker return code is 0; worker and parent ledgers both contain the sole slot
as OK. Parent assessment completed, with no worker error. Exactly one raw,
one expanded and one local full-header report exist:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Raw ATTTSR entity | 151713 | `963a0188c833a74fbe2d86f3288e9f1b6e70e038135dc05e57daa8d4256d7ccc` |
| Expanded FITS | 4173120 | `ff251ab4e22655bc02b612a599160e40cfe3176cf8de90ce4514668e5bcf7a17` |
| Local header report | 13563 | `a5c5d3a9113b88b63e560be09dc72df0ece14b35c8e91fdefcbc73c77a8d8409` |

The independent raw three-byte signature check is `1f8b08`, agreeing with
`GZIP_WRAPPED_FITS`. The frozen worker records completed gzip CRC/EOF checking;
this audit does not claim independent re-decompression. Expanded/raw hashes
were independently computed without interpreting their contents. The report
contains two HDUs, agreeing with the public product receipt. No coordinates,
full cards or attitude values were printed by the audit.

## Closure, preservation and limits

- All **10 C3d outcome artifact hashes**, **9 worker artifact hashes** and
  **9 dependency hashes** verify. The exact outcome artifact path set matches
  the retained receipt/product/header set. Source/tests/protocol snapshot match
  pre-execution review; the current protocol matches the snapshot. Worker-start
  binds the exact run-start hash.
- Imported C3c safe HTTP metadata equals the original record exactly; its
  HTTP/outcome hashes match. All **7 prior outcome hashes**, **6 prior worker
  hashes** and **3 prior dependency hashes** verify, including prior source,
  tests and snapshot. Its `STOP_SIZE_METADATA` is preserved, not promoted.
- All **25 files** across the C3c/C3d data directories had identical hashes
  before and after the bounded file/receipt audit. No frozen artifact was edited.
- Actual raw/expanded sizes agree with the resource receipts and are below
  2097152 / 33554432 bytes. JSON totals reproduce the recorded snapshots:
  **18720 bytes** before worker result, **19898 bytes** before outcome and
  **21476 bytes** final, below the 1048576-byte aggregate limit.
- Recorded worker/parent peaks are **62509056 / 59228160 bytes**, below the
  500000000-byte acceptance ceiling. Bound configuration retains 60-second
  worker, 1-MiB chunks, 64-MiB pre-request free-space requirement and 65536-byte
  terminal reserve. This audits retained receipts/configuration, not an
  independent reconstruction of elapsed runtime, historical free space or an
  OS-enforced memory quota.

| Additional provenance | SHA-256 |
| --- | --- |
| C3d source | `87caca0e856065d33ff4f60404399915eed8a4b50a9afa7d0106f98fb691f825` |
| C3d tests | `8d313d56946a5f68fb30af8b39c41910121a079d646ccff9e074dcbfc809cf56` |
| C3d protocol/snapshot | `8bee82d6c849bd94479f40615817cc2d14776d439b80b62a8b47c84871beed6a` |
| C3d outcome | `2a1a7340c89292882f2b205ff48f4babbada46ed4dde210b45ec1bdd4a6bed0d` |
| Preserved C3c outcome | `e1d74b048dd68dce51e52bf964d841ac195ca581011fae881f447cdc129c45e3` |

## Scientific boundary

This successfully retains an input for further adjudication. It is not proof
of compatible attitude time/coordinate conventions, sampling/quality flags,
simultaneous camera coverage, accepted source/background geometry, recovered
bursts or discovery. The correct next step is actual header/schema adjudication
and, if supported, a separately specified bounded value-reading experiment.
Do not infer a clean pointing history or usable aperture merely from the
successful transport and two-HDU structural result. The earlier C3/C3b/C3c STOPs
and the original scientific selection/multiplicity rules remain unchanged.
