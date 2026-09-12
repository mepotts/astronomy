# M1c: one official Gaia mirror attempt, gated by first-field parity

Specified September 12, 2026 before any ARI catalog request. Locally hash-bound,
not publicly preregistered. This is a metadata-only extension of M1b. It changes
no pixel estimator, centroid, period, aperture or original result. No PRF products,
unknown targets, new pixels, submissions or accounts are in scope.

Use the ESA-listed partner ARI's documented sync endpoint
`https://gaia.ari.uni-heidelberg.de/tap/sync`, with REQUEST=doQuery, LANG=ADQL,
FORMAT=votable, and the exact retained data/m1/<TIC>/catalog-query.json ADQL.
Keep all eight columns, gaiadr3.gaia_source, 0.05-degree cones, TOP 5001 and ordering.
[ESA partners](https://www.cosmos.esa.int/web/gaia/data-access),
[ARI query documentation](https://gaia.ari.uni-heidelberg.de/help.html).

First request TIC 450781262 exactly once. Require the same 1,290 unique signed
int64 positive source IDs as retained ESA bytes, hash
d4a1069cfb5244c28db6dfc354df326ab1a5db611e36612b536b7f914d105098.
Compare after source-ID sorting: identical masks in all eight columns; finite
unmasked numerical values; absolute tolerances RA/DEC 1e-10 degree, ref_epoch
1e-9 year, pmra/pmdec 1e-5 mas/year, phot_g_mean_mag and ruwe 1e-5, with rtol=0.
IDs are compared as integers, never floating point. These tolerances concern
serialization, not astrophysical uncertainty. Reject duplicates/missing/extra
columns, non-long or masked IDs, invalid positions, QUERY_STATUS errors or overflow,
empty tables and >=5001 rows. VOTable FIELD NAME takes precedence over FIELD ID.

Require explicit semantic units: RA/DEC degrees, ref_epoch years, pmra/pmdec
mas/year, magnitude mag. Accept alternate spellings only when Astropy parses
exactly the same unit with scale factor one. Missing dimensional units, radians,
arcsec/year, or otherwise scaled units stop rather than silently changing values.
source_id and ruwe must be dimensionless (absent/empty or explicit dimensionless).
Require finite unmasked optional values; retain masks rather than filling zeros.

Only first-field parity PASS authorizes exactly one identical query each for
TIC 53206761 and 2041210548, in that order. A first-field failure stops the entire
stage; either later failure remains recorded without retry. No alternate service,
changed ADQL, async job, upload or automatic HTTP retry/redirect. Each request has
45-second socket timeout, 60-second process-tree deadline and 5,000,000-byte streamed
response cap; at most three requests and 15 MB. Use the existing tested bounded_run
tree cleanup. Existing request markers prevent rerunning any request. Preserve
attempt plans, partial responses, failures, parent worker outcomes and summary.

Store only new data/m1c, scripts/m1c.py, tests/test_m1c.py and out/m1c-* products.
Freeze source/protocol/dependency hashes in a pre-request manifest. Verify unchanged
M1/M1b source/protocol, original query hashes, M0b provenance, and all M1b result
hashes before workers. The mirror is the same Gaia DR3 data, not independent
astrometry. Original results remain immutable.

Reassess catalogs against the existing stored Gaussian centroids using unchanged
M1 catalog geometry. Read retained FITS WCS/time/cadence and finite-selection masks
only to reproduce the original propagation epoch; no pixel differences, fits,
bootstrap or flux statistics are recalculated. Require original selected cadence
count and first-field propagation epoch equality. Retain missing proper motions,
crowding and uncertainty limitations. Catalog availability or a coarse match never
sets unknown_search_authorized=true or validates physical depth/source purity.

Before requests, synthetic tests cover duplicate IDs, int64 precision, wrong/missing
units, unit spelling equivalence, optional masks, altered values/ID sets, malformed
fields/status and parity tolerance boundaries. An offline replay must validate
manifest/response hashes, recompute full first-field parity, and exactly reproduce
each new catalog-only diagnostic from retained inputs, with no network or writes.
Parity failure is STOP_CATALOG_PARITY; unavailable later fields remain
STOP_CATALOG_UNAVAILABLE. Completed metadata remain VALIDATION_INCOMPLETE.
