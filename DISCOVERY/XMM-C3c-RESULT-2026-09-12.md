# C3c: ESA advertises the exact attitude file, without a length

**STOP_SIZE_METADATA is preserved.** The [single-HEAD contract](XMM-C3c-2026-09-12.md)
and [independent review](XMM-C3c-REVIEW.md) were frozen in commit `c3ded5f`
before the request. At 2026-09-13 01:17:35 GMT ESA returned HTTP 200 at the
exact planned URL, Content-Type `image/fits`, and a safely parsed inline
filename `P0884250101OBX000ATTTSR0000.FTZ`. No Content-Length was supplied.
No response body was read; no file or package identity was verified.

The sole slot is FAILED, worker exit 1, parent assessment completed, and
offline replay returns `PASS_OFFLINE_REPLAY STOP`. Worker/parent peak working
sets were 36544512/33329152 bytes. All final JSON totals 4629 bytes, within
the 131072-byte budget. Raw Content-Disposition and cookies are intentionally
not retained: replay checks safe derived fields, not a reparse of that raw
header. [Independent postrun review](XMM-C3c-POSTRUN-REVIEW.md).

## What changed and what follows

This is useful response evidence despite failing the frozen size gate: the
documented alternate returns 200 and advertises the desired raw filename.
It does not prove GET availability or explain either earlier mirror 404.
The earlier C3/C3b outcomes and this C3c outcome remain unchanged.

Adopt a separate C3d bounded GET contract for the same exact URL and filename.
The download will impose its own 2-MiB retained-byte ceiling (at most one extra
overflow-detection byte), independently of missing server length. If a length
is present, it must be valid, within the cap, and match the completed transfer.
Require the exact safe filename, binary media type, identity encoding and
HTTP identity before reading any body. No new HEAD, redirect or retry.
Only gzip or uncompressed FITS is eligible; do not extract an archive or infer
member identity. Gzip expansion is separately capped at 32 MiB with integrity
checks. Structural headers must pass before any later attitude arrays.

This is a new prospective acquisition decision using observed metadata and
the documented client download route, not a retroactive C3c pass. No missing
size or validator is invented. Freeze and independently review C3d before GET.
No photons, recovered control, unknown-source scan or discovery yet.

## Identity

| Artifact | SHA-256 |
| --- | --- |
| Source | `542fce5755d9ff668d4ccd6e199b23780504368603352243d7e6fb7cfa727f90` |
| Tests | `d3fd4d9775c40a094d761dad0f59e4b9e9d556fced7c6c3f7449324b5f4885ed` |
| Protocol snapshot | `cd75f4717291df12bdbc7f34f34b6398dfe36b7aa9885db1849416f60bb9609d` |
| HTTP receipt | `a8d6a7edbe6a0b357401592d4f9a484840fd740e7bf7791de520d097eb493f66` |
| Outcome | `e1d74b048dd68dce51e52bf964d841ac195ca581011fae881f447cdc129c45e3` |
