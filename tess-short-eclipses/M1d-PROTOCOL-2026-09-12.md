# M1d: offline binary decoding and unchanged first-field parity

Specified before numerical decoding of the retained ARI rows. This is a new
software/metadata experiment, not a rerun or repair of the frozen M1c result.
No network, new fields, pixel measurements, PRF files or unknown targets.

Inputs are the exact first-field ESA and ARI XML responses identified in M1c:
ESA SHA256 d4a1069cfb5244c28db6dfc354df326ab1a5db611e36612b536b7f914d105098;
ARI SHA256 17c3c8a22488bb9b40a37d77b47807aa900decc28486e04bc5a48c0739ad2639.
Preserve the original bytes, integer null declaration, masks and M1c STOP.
Freeze this protocol, new source/tests and existing dependency hashes in a new
manifest before execution. No environment or installed-library modifications.

Implement only the observed eight-scalar-column BINARY schema: source_id long,
ra/dec/ref_epoch/pmra/pmdec double, phot_g_mean_mag/ruwe float, in that order.
Accept VOTable 1.4 with the standard v1.3 namespace, one results RESOURCE and one
TABLE, all QUERY_STATUS values OK, one inline base64 BINARY stream. Reject DTDs,
entities, external streams, arrays, extra tables/fields/data, other datatypes,
BINARY2 and unsupported null declarations. This is deliberately not a general
VOTable implementation. Accept a signed-64-bit integer null sentinel; floats
use NaN masks, with no finite floating null sentinel silently ignored.

The [IVOA specification](https://www.ivoa.net/documents/VOTable/20250116/REC-VOTable-1.5.html)
sections 5.3--5.6 and 6 define sequential binary fields, signed integers,
big-endian IEEE floats and null representations. Use a 56-byte unpadded row;
validate canonical base64 strictly after removing ASCII XML whitespace. Accept
only UTF-8 XML without embedded NULs. Reject truncated
rows, zero rows, >=5001 rows or a mismatched declared row count. Bound each XML
input to 5 MB before parsing. No remote resources are resolved.

Primary decoding uses stdlib struct; an independent NumPy structured-buffer
interpretation must agree exactly on every integer and finite floating value,
NaN placement and signed-zero representation before catalog validation. This
checks two numeric implementations, not two independent scientific datasets.
Construct each column separately; never coerce a mixed row to floating point.

Apply M1c's unchanged units, positive unique int64 IDs, finite required positions,
optional masks and first-field comparison. Require 1290 exact IDs, exact masks,
same unit scales and unchanged absolute tolerances (rtol zero). Invalid metadata,
decoder disagreement or failed parity is STOP_M1D. Passing means only
OFFLINE_CATALOG_PARITY_PASS, with unknown_search_authorized=false. Neither
catalog-only localization nor missing-field acquisition is part of this stage.

Before real decoding, synthetic tests cover integer extremes/precision/nulls,
float NaNs and signed zeros, duplicate/masked IDs, required/optional masks,
wrong units/schema/order/counts, malformed/truncated base64, external streams,
DTD/entities and later overflow status. Use current pinned Ruff 0.16.5 before
freezing; the prior source's lint exceptions do not apply to this new source.
Independent review is required before execute. Use the existing tested Windows
owner-context process-tree helper for a 60-second hard worker deadline. Require
the Windows peak-working-set receipt to be <=1 GB before/after computation (an
acceptance cap, not an OS allocation quota) and <=1 MB derived scientific JSON;
this input is only about 100 KB. Timing/memory receipts stay separate from the
exact scientific replay. Tests are portable; actual execution uses this Windows runtime.
Write exclusive parent-attempt and worker-start markers before decoding; reruns
stop before another numerical decode. Persist the parent worker outcome including
tracebacks/deadlines even when no scientific result can be produced. Provenance
and resource failures are worker STOPs, not empty scientific comparisons.
Record every failure without retry/threshold change. Full read-only replay must
verify hashes, repeat both decoders and exactly reproduce the new result.
