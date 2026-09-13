# C9 resource preflight: synthetic only, final runtime fit passed

Root independently exercised the three frozen pure components using invented
coordinates and repeated synthetic packed rows, not retained science products.
Camera lengths, strides and fixed selection/time configuration match C9's
prospective declared workload; fixture photons are synthetic and deliberately
accepted. This is a kernel throughput check, not a numerical experiment.

Across334chunks/3,323,958synthetic rows:142,652,840buffer bytes supplied to the
decoder and93,070,824selected bytes decoded. Each chunk passes decoder, true
TAN/spherical geometry and fixed counter; accepted/source-aperture counts agree
exactly with the generated fixture size. No full-table array is allocated.
Elapsed1.218seconds; process peak74,665,984bytes (Windows peak sampler).
Actual science-product bytes read:0. Frozen component hashes are those in
their [geometry](XMM-EVENT-GEOMETRY-REVIEW.md) and
[counter](XMM-RECORDED-COUNTS-REVIEW.md) reviews and the C9 manifest proposal.

This does **not** include full-product hashing, structural replay, disk row
reads,334durable chunk receipt pairs, JSON artifact closure or parent replay.
Those costs need the author's full-wrapper synthetic fixture before final
120second/512MiB/4MiBJSON feasibility acceptance. A kernel timing is not a
guarantee of real-data runtime or a reason to waive a timeout.

## Initial full-size wrapper fixture

Root also ran the author's then-current `benchmark()` with all334chunks and
the declared camera lengths. Synthetic worker and parent both complete exact
142,652,840returned row bytes and93,070,824decoded selected bytes per pass.
The fixture exercises the real stream/chunk/geometry/counting path,334durable
chunk start/result pairs, camera summaries, parent chunk-hash comparison and
artifact closure. Worker+parent including fixture setup:8.703seconds; final
JSON703,129bytes; process peak76,787,712bytes. All remain below proposed caps.

Important: this fixture generates returned row bytes lazily and **mocks product
hash/header verification and the subprocess launcher**. Its verification byte
counters describe the fixture's mocked contract, not bytes read from disk.
Worker and parent execute sequentially in one process; no numerical replay is
included in this particular benchmark. It is therefore stronger than the pure
kernel check, but still not independent evidence of whole-product disk I/O or
the real process-tree deadline. The same11initial runtime tests pass separately;
additional failure tests and independent physical-synthetic-file fit remain
underway. No actual science products or photon values were read.

## Final exact-source physical synthetic fit (2026-09-13)

Root reran the independently authored `c9_independent_synthetic_fit.py`
(SHA256 b95f3739abbe51b0db39d8053c5c484d7c3e92842dbe09f29f1fe543a96b2697)
against final runtime bb8d6d8c8a737e2d8be11d6f489091a1d0f7453fd320ad80a761709d56c81d03.
The earlier [independent report](XMM-C9-INDEPENDENT-SYNTHETIC-FIT.md) remains
attributed to its earlier source; this is a separate final-source run.

Temporary fixture directory: `C:/Users/matth/AppData/Local/Temp/xmm-c9-independent-n8x0dzwy`.
Outcome SHA256 14dd052fb0187301a5ade86958bed9531fe230784932cf8c601499d57c48b044.
Real synthetic FITS disk reads, full-file hashing, structural replay, the actual
subprocess/deadline helper, parent assessment and one numerical replay PASS.
Run plus parent: 8.859 seconds; replay: 2.891 seconds. JSON: 709463 bytes;
334 start/result pairs; worker peak 73277440 bytes, parent peak 74829824 bytes.
Each of the three complete passes returns 142652840 row bytes and decodes
93070824 selected bytes. Whole-product opaque hashing is separately
246890880 bytes per pass. No actual retained science product was opened.

The fixture substitutes synthetic provenance and centres and has three HDUs
per file, not the full actual header families. It establishes resource fit,
not actual-input validity or scientific recovery; real-run caps remain fixed.
Root separately passed actual metadata-only binding for all 16 dependencies
under a products-open prohibition. Final independent review is a scoped GO;
all 332 XMM tests (138 core, 175 C1-C8, 19 C9), scoped Ruff and repository
verification pass. CI includes the C9 wrapper. Exact-byte commit freeze still
precedes the first actual photon run.
