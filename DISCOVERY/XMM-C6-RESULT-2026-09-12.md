# C6 result: missing MOS2 map acquired from ESA

After reviewed freeze `d54ec04`, the single exact ESA GET succeeded at
2026-09-13 02:50:15 UTC. Offline parent/header replay passed. Status
**MOS2_MAP_RETAINED_HEADERS_ONLY**, not source support or burst recovery.
The earlier HEASARC404 remains a STOP; this does not identify its cause.

HTTP200, image/fits, exact safe inline basename, no advertised Content-Length,
ETag or Last-Modified. The separately adopted streaming cap was applied, not
an invented advertised size. Actual gzip410115 bytes expanded with CRC/EOF
verification to1707840 bytes. One primary648-by-648 float32 image, exact
OBS_ID0884250101, EMOS2, S002. Declared pixel payload1679616 bytes at offset25920.
No scientific arrays interpreted; transfer, decompression, hashes and header
reads were real I/O. Parent replay did not decompress again.

| Retained artifact | SHA256 |
| --- | --- |
| Outcome | `8cd766cd9ec4e2a54548248bd6b8aa0805c94678e1e066ba3c560713e03e0caa` |
| Raw gzip | `1db2fad3238cabb71157ac4f39ea10949f7c42842788a363e01f272648721205` |
| Expanded FITS | `a92d6907db2e9e4def19b124c19da6056d20a06e3465da7103a23fb5dcd36983` |
| Full local header | `6cc4bfa1b08d93a31f8f89ba49274511e9ef0052634d64cb1235fdde739e2285` |
| Safe HTTP receipt | `79238e792c75c526c5c138b88ddced37f8b5125e5457395a9dc9db54f27e08d5` |

Worker0, assessment completed, oneOK ledger. Monitored worker67444736 and
parent63692800 bytes, below500000000. Pre-outcome JSON36091 bytes; aggregate
budget includes ignored local full headers; final JSON37762 bytes. Raw products and coordinate-bearing
headers stay ignored; no new publication, correspondence or submission.

The [prospective protocol](XMM-C6-2026-09-12.md) and
[independent preflight review](XMM-C6-REVIEW.md) precede execution. All219 local
XMM tests passed before freeze, including17 C6 tests. Repository verifier passed.
Next: [header compatibility](XMM-MOS2-MAP-COMPATIBILITY-2026-09-12.md), then a
separate unchanged-region static MOS2 value check. C5's pn/MOS1 results and
original pn-plus-MOS recovery requirement remain unchanged.
