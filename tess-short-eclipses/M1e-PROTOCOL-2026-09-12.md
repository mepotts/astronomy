# M1e: conditional missing-field metadata continuation

Prepared before requests; not executed or publicly preregistered. This stage
requires authoritative M1d2 OFFLINE_CATALOG_PARITY_PASS and explicit parent GO
after code, synthetic tests and pinned Ruff 0.16.5 review. Preparation alone is
not authorization. Preserve every M1/M1b/M1c/M1d/M1d2 source, protocol and result.

Before freezing the exclusive M1e manifest, validate M1d2's manifest/dependencies,
successful worker outcome and <=1 GB runtime receipt; independently rerun its
offline execute function and require equality with its entire retained result.
Require 1290 exact positive int64 IDs, exact masks, validated semantic units and
the unchanged M1c tolerances (rtol zero). Bind M1d2 and original M1d source, tests,
protocol, manifest, result, outcome and runtime hashes, all inherited dependency hashes,
M1e source/tests/protocol, original query/result hashes and bounded-run helper.
The authoritative M1d2 result now passes: all 1290 IDs/masks/units match and all
unmasked numeric differences are zero. Explicitly require frozen M1d2 source
SHA256 6415e4f371a203a2cce7bbf13f356ed0e8beafa90054a57bfee173fa95a71db8 and
manifest SHA256 5a90493fc17e08200c79bb7e12ee9c1c7676bd859f8b66e0e583d7969e1efab0.
Use M1d2.dependencies and M1d2.execute with explicit M1d2 result/outcome/runtime
paths; never call M1d2.main or rebind its preserved base-stage globals. Require
numeric_decoders=unchanged_m1d_struct_and_numpy and full retained-result equality.
Original M1d STOP_TABLE_STRUCTURE is preserved and verified through dependencies.

Only then permit exactly one request each for TIC 53206761 and 2041210548, in
that order. Never request TIC 450781262 again. Use the exact retained eight-column
ADQL in data/m1/<TIC>/catalog-query.json, unchanged TOP 5001, Gaia DR3, 0.05-degree
cone and source-ID order. Use only https://gaia.ari.uni-heidelberg.de/tap/sync
with REQUEST=doQuery, LANG=ADQL, FORMAT=votable. No redirects, HTTP retries,
alternative endpoint, alternate format, asynchronous job or new coordinates.

Each request: 45-second connect/read socket timeout, 60-second process-tree
deadline for the complete worker, maximum 5,000,000 streamed bytes; at most two
requests/10,000,000 bytes total. HTTP status must be 200. The byte cap applies
to decoded response bytes retained; no compressed-response bypass. Reuse the
tested Windows owner-context bounded_run helper. The parent's launcher writes
an exclusive per-field attempt before launch; worker writes an exclusive start
marker before network. Exclusive run-start and attempt files block reruns even
after a crash. All writes are new isolated data/m1e receipts and out/m1e products;
retain partial bytes, failure traceback, parent outcome and artifact hashes on
failure or timeout. An unsuccessful first missing-field query does not authorize
retry and does not prevent the one already authorized second-field attempt.
Launcher-import or attempt-reservation failure instead stops launching the queue,
recording STOP_NOT_LAUNCHED per-field outcomes and STOP_PRELAUNCH summary. Existing
reservation files are never replaced. Unwritable storage itself cannot guarantee
receipts; such an OS failure is reported directly and does not authorize rerun.

Use only M1d2.decode, which validates the exact table-free ARI DataLink service
descriptor in memory and delegates to unchanged M1d's two numeric decoders and
validator. This is a function-only adapter, not a new serialization or fallback.
The service URL is never fetched; unknown descriptor structures stop. Require the same
eight scalar BINARY fields, same column order, declared types, namespace/version,
int64 integer null sentinel and NaN optional masks. Reject all unsupported
schemas, malformed input, overflow, duplicate/nonpositive/masked IDs, wrong
semantic unit scales, nonfinite unmasked values, missing required coordinates,
empty or >=5001-row responses. No installed-library patch or format fallback.
Hash and size receipts are saved before decode, so unsupported complete responses
remain auditable. Validated catalog receipts are written only after decoding.

Reassessment calls unchanged M1 catalog geometry against fixed M1b centroids,
target header positions, image shape and original propagation-epoch selection.
M1c.context reads existing cadence/time/quality and finite-selection masks only;
no new pixel fit, difference image, bootstrap or flux statistic. M0b provenance,
LC and TPF hashes and selected cadence counts must still match. The adapter
temporarily replaces DATA and Table only in its fresh dynamically imported M1
module within the worker process; a finally block restores both even on failure.
No frozen source or installed module is rewritten. Preserve optional masks and
all original geometry limitations; no new threshold, fit or purity assertion.

Success is METADATA_DIAGNOSTIC_VALIDATION_INCOMPLETE; failed fields are
STOP_CATALOG_UNAVAILABLE. Neither is a discovery or calibrated localization.
unknown_search_authorized remains false. No PRF FITS, pixels, unknown targets,
submissions, accounts or outward scientific claims are authorized.

Synthetic tests before queries exercise conditional parity gating, exact request
identity/no first field, replay/provenance checks, int64 precision and masks,
bad units/schema/duplicates, redirects/timeouts/byte caps, exclusive attempts,
failure receipts and adapter restoration. Pinned Ruff 0.16.5 must pass without
new frozen-source exceptions. After authorized execution, read-only replay must
revalidate the M1d2 gate, manifests, every retained attempt/outcome/artifact hash,
all successful decoded catalogs and full metadata diagnostics. No replay network
or writes. An explicit --approved-manifest-sha256 matching the reviewed manifest
is additionally required to run; it documents parent GO, not scientific acceptance.

## Unexecuted draft revision checkpoint

The initial M1e draft correctly blocked on M1d's STOP. Its review checkpoint is
preserved in M1e-REVIEW-2026-09-12.md; no M1e manifest, run or query existed.
Before this M1d2 adaptation, source hash was
133b985b5a683ef7df3dd7fdd7148cb666bd0e4c523b37fcdc77360af317bf00,
protocol hash 43b54c33b36085a6ada68fe84adcd80584c61ef818a7bae55e90bfd0dae3b93c,
author-test hash f69208eb4f3adc3bab8d34cfa8adac2d0ca45fa5317f111150014d8e94eef85d.
This pre-execution revision changes only the prerequisite proof and validated
descriptor adapter. Query identity, two-field scope, geometry, thresholds,
transport caps and one-attempt rules stay unchanged. Review and GO remain pending.
