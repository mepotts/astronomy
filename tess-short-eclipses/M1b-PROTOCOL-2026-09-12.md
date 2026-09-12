# M1b: metadata parser repair and exactly one bounded query retry

Authorized and specified after [M1's retained failures](M1-RESULT-2026-09-12.md),
before the retry requests. This is locally hash-bound, not public preregistration.
M1's pixel estimator, three controls, sectors, ephemerides, uncertainty method,
fit configuration and thresholds are unchanged. No new pixels are acquired.

Read the eight Gaia fields using their VOTable NAME, not the optional FIELD ID.
Require unique exactly matching names: source_id, ra, dec, ref_epoch, pmra, pmdec,
phot_g_mean_mag, ruwe; source_id must be VOTable long and a non-masked signed
64-bit integer column. Require QUERY_STATUS OK and no overflow. Never round source
IDs through floating point or silently rename ambiguous fields.

Reuse the existing first Gaia response by verified hash. For each of the two
failed Gaia queries, make exactly ONE identical ADQL request to the same ESA
endpoint with the same 45-second socket timeout, 60-second process-tree deadline
and 5-MB response cap. No fallback catalogs, query changes, alternate endpoints,
or further retries. Preserve original query/failure receipts; use data/m1b/ for
new metadata, out/m1b-* for new results. All three TP files remain at their original
paths and must match their original hashes.

A separate adapter invokes unchanged M1 pixel computation and changes only catalog
field parsing/path selection and separately labelled output/provenance. It must
verify that TIC 53206761 and TIC 2041210548 reproduce every persisted pixel metric,
map and bootstrap centroid exactly. A mismatch stops that replay rather than being
accepted as a scientific change. The first control obtains its first serialized
result only because its original catalog-parser error prevented result serialization.
Preserve M1 source, protocol and all results unchanged. Record adapter/protocol
hashes in every new receipt/result. Synthetic malformed/duplicate/precision parser
tests precede requests. No unknown-target search, publication or submission follows
from this repair, even if all coarse control-consistency checks pass.
