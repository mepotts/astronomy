# C7: fixed-region MOS2 static-sign diagnostic

Prospective September12,2026 contract, to be reviewed and committed before any
MOS2 pixel decode. This appends evidence from the newly acquired camera; it
does not edit C5 pn/MOS1 outcomes or select new regions after their results.

## Exact input and interpretation

Only C6's `P0884250101M2S002EXPMAP8000.fits`, expanded1707840 bytes, SHA256
`a92d6907db2e9e4def19b124c19da6056d20a06e3465da7103a23fb5dcd36983`.
C6 outcome `8cd766cd9ec4e2a54548248bd6b8aa0805c94678e1e066ba3c560713e03e0caa`;
header `6cc4bfa1b08d93a31f8f89ba49274511e9ef0052634d64cb1235fdde739e2285`.
One648-square primary big-endian float32 payload, offset25920,1679616 bytes.
No source-list, attitude, GTI or event values; no network. Prior C6 replay checks
hashes/headers only. Bind C5 outcome hash without its numerical replay:
`58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36`.

The [MOS2 header adjudication](XMM-MOS2-MAP-COMPATIBILITY-2026-09-12.md) permits
the same limited sign interpretation: absent BUNIT/scaling/null cards, primary
CDELT-only degree RA/DEC TAN, verified legacy FK5/equinox2000 explicitly mapped
to RADESYS, fix=False. Reject unsupported primary matrices/distortions/poles,
ambiguous cards or schema/identity changes. Do not select alternate WCS metadata.

## Unchanged numerical experiment

Reuse immutable reviewed `xmm_map_support.py` SHA256
`2c93c225223aacedefd8ce160726c9f363e11626823cb8d9ae34a54dfda2307a`
and its14 tests. Reuse C5's fixed centre construction: the predeclared published
ICRS convention,120arcsec offsets at0/90/180/270degrees, then FK5/J2000 conversion.
The bound original counts-definition hash remains
`7a3e6b99da0a11f547ed43373cb179f90257d9e01a2a2fbdf643cb85bec53c4e`.
Five fixed labels published/north120/east120/south120/west120; each20arcsec circle
and60–90arcsec annulus. All10 regions must survive, including zero/negative or
unavailable results. No coordinates/WCS arrays in public receipts.

Both4and8 midpoint subdivisions per axis are mandatory;8 remains nominal.
Report finite-positive/zero/negative/nonfinite/outside-image categories,
sample counts and parent-pixel counts, approximate spherical areas/fractions,
analytic full-region area comparison, fixed-resolution differences and existing
pixel-centre/border-sampling proximity diagnostics. No favorable-grid choice.
Same conservative bounded TAN geometry,16-row chunks and region-box caps as C5.
No new exclusion masks, source lists, exposure normalization, detector fitting
or post-value recentering. This is the unmasked accumulated-map sign screen.

## Resource, binding and verification contract

One exclusive local attempt with reviewed source/tests/protocol snapshot and
pinned C5/core/C6 dependencies. Composition must use isolated module instances;
do not mutate prior artifacts or invoke old C5 two-map workers/numerical replay.
The C7 worker handles just the new one-map manifest and10regions. Bind actual
runtime, current configuration, exact product/header hashes, definition and
compatibility decision. Require parent independent numerical recomputation of
eligible completed output and full artifact/label/byte closure.

60-second process-tree worker with existing separately bounded cleanup helper;
500000000-byte monitored worker/parent peak, not OS memory enforcement.
Aggregate JSON1048576,65536 terminal reserve; no new stored products.
Read only16primary rows per chunk, at most41472 bytes/chunk,41 chunks.
Track actual read bytes separately from converted/decoded bytes, including
partial failures and conversions before a later copy failure. A complete pass
is1679616 bytes. Worker and parent passes are distinct; every later numerical
replay is an additional pass, not cost-free verification. Hash/header I/O is
separate. Hard interruption before receipts means unknown attempted work, not0.

Exclusive run/worker/map start markers and terminal receipts preserve partial
outcomes. Failed parent validation retains its completed and partial counters;
failed-artifact replay cannot certify numerical summaries or unreported reads.
Nonzero exit, timeout, hash/schema mismatch, missing region or artifact mismatch
cannot become success. Frozen pn/MOS1 results remain unchanged and separate.

Strongest outcome: MOS2 static-support approximation, **not coverage, exposure,
burst recovery or discovery**. Wholly positive sampling is not a continuous
coverage certificate; zero sampling does not prove no physical exposure at
every time. Pixel-centre proximity is not finite-pixel edge clearance, and an
annulus's nearest unsupported centre can be inside its hole. Neither maps nor
sampled attitude establish matched per-bin live exposure. Original pn-plus-MOS,
negative-control, source-confusion and detector-artifact recovery gates remain.
