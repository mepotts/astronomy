# XMM / EXOD eligibility: a verified three-observation increment

Date: 2026-09-12. Bounded primary-source, metadata-only research. No event lists,
images, light curves, unknown coordinates, accounts, science implementation or
publication. This extends [the earlier leverage decision](NEXT-LEVERAGE-2026-09-12.md)
with actual identifier-level evidence; it does not erase its prior STOP.

## Decision

**A small, public, post-EXOD-paper observation increment is now verified.** The
three observations below were taken after the paper's final arXiv revision and
are absent from the authors' pinned 15,105-ID list. This supports one concrete
fallback: a metadata-only product/mode eligibility check on these exact three
observations plus two published recovery controls. It does **not** yet authorize
event acquisition or establish that any observation is unsearched by everyone.

This is **not a demonstrated 5XMM-minus-EXOD increment**. ESA's 5XMM documentation
describes 14,616 observations public by 2024-11-01. Its June 2026 release date
does not make those photons new. The public IRAP interface calls the release
**5XMM-DR15**, dated 2026-06-05; I did not verify a distinct product named
`5XMM-DR1`. Use the verified release name rather than guessing an endpoint.
[ESA catalogue description](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/node137.html),
[IRAP interface](https://xmm-catalog.irap.omp.eu/).

The stronger increment comes from current **XSA observation metadata**, not from
5XMM membership. It requires an explicit scope decision if adopted: a small
post-paper archive increment rather than reprocessing the newer catalogue.

## What was actually verified

EXOD II v1 was submitted 2025-03-18; v2 was revised **2025-03-19 15:23:23 UTC**.
The paper attempted 15,105 observations; its abstract reports 12,926 successes,
while section 3.1 gives 12,923. Neither successful subtotal is a complete attempt
ledger. Previously searched failures are not fresh exposure simply because no
detection was reported. The paper's processed inputs include EPIC `EVLI` event
lists and `OBSMLI` source lists; unsupported modes and missing products matter.
[Author paper and version history](https://arxiv.org/abs/2503.14208),
[paper methods/accounting](https://arxiv.org/html/2503.14208v2).

The current public author repository was pinned to commit
`5bf41535af44b8efd318d03f1fc9ea7045013cb5`, dated 2025-04-16. Its
`data/all_obsids.txt` contains **15,105 unique, valid ten-decimal-digit strings**.
The two published recovery controls, `0884250101` and `0886121001`, are present.
The file's count agrees with the paper's attempted count, but that agreement is
not proof of a final-run receipt. The inspected `exod/main.py` is a single-
observation example, not a binding of this list to the final paper run.
[Pinned ID list](https://raw.githubusercontent.com/nx1/EXOD2/5bf41535af44b8efd318d03f1fc9ea7045013cb5/data/all_obsids.txt),
[pinned example](https://github.com/nx1/EXOD2/blob/5bf41535af44b8efd318d03f1fc9ea7045013cb5/exod/main.py).

An anonymous synchronous XSA TAP query then returned these exact rows. No
coordinates, target names, photon counts or fluxes were requested.

| Observation ID | Start UTC | End UTC | Proprietary expiry UTC | In pinned EXOD list? |
|---|---|---|---|---|
| `0942190201` | 2025-03-20 20:07:46 | 2025-03-21 03:07:46 | 2026-04-07 00:00:00 | No |
| `0940541201` | 2025-03-21 05:20:03 | 2025-03-21 09:13:23 | 2026-04-07 00:00:00 | No |
| `0943750401` | 2025-03-21 18:57:07 | 2025-03-22 01:37:07 | 2026-04-07 00:00:00 | No |

All three came from `xsa.v_public_observations`, with `with_science=true`,
PPS version `21.51_20241115_1113`, and SAS version
`xmmsas_20241108_1150-21.0.0`. PPS processing timestamps were respectively
2025-04-26 18:49:54, 18:49:29 and 18:41:02 UTC. These are observation-level
metadata, **not usable EPIC exposure or good-time durations**. In particular,
`with_science=true` does not prove the needed camera modes or product set.
[ESA archive documentation](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/xsa.html),
[retained query response](XMM-EXOD-ELIGIBILITY-2026-09-12-data/public-post-paper-three.json).

Two separate statements are supported: (1) exact absence from the pinned list,
and (2) actual observing dates later than the paper. Statement (2), a causal
inference from those dates, establishes that these photons could not have been
processed in the March 2025 publication even without authenticating every
legacy ledger entry. It does not exclude unpublished or later EXOD runs,
standard pipeline variability analysis, other transient searches, or papers
about these observations. No such comprehensive later-literature audit was
performed. Being outside 5XMM's public cutoff is weaker evidence by itself.

## Reproducible query and selection

Endpoint: `https://nxsa.esac.esa.int/tap-server/tap/sync`.
GET parameters: `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=json`, and the following
`QUERY`. The endpoint is documented by the installed ESA astroquery client;
actual anonymous table-schema and data queries succeeded here.

```sql
SELECT TOP 3 observation_id,start_utc,end_utc,proprietary_end_date,
             with_science,pps_version,pps_proc_date,sas_version
FROM xsa.v_public_observations
WHERE start_utc >= '2025-03-20' AND start_utc < '2025-04-01'
ORDER BY start_utc,observation_id
```

This is an intentionally tiny ordered sample, not complete enumeration of that
date interval. The UTC lower bound is after v2; the fixed upper bound limits
the first probe. No earlier-date or additional-row fallback was used. Future
archive changes can alter a live `TOP 3` result; the retained response and exact
three IDs above define the proposed sample, not whatever later query happens
to return. Keep IDs as strings with leading zeros. Require valid parsed dates,
unique IDs, ascending order, true public/science metadata and exact list
exclusion. All three passed these metadata checks on this snapshot.

The first row-query version included `AND with_science = true` and returned
HTTP 400. Its response body was not retained, so the exact server diagnostic
is unknown. The only change in the successful diagnostic query was removal of
that predicate; the science flag was still requested and checked locally for
all returned rows. This establishes a compatibility issue with that query
form, **not** that the service lacks Boolean data or a precise parser cause.
This was one deliberate query revision, not a blind retry or scientific cut
relaxation. The failed exact query is the block above with
`AND with_science = true` immediately before `ORDER BY`.

The queried column schema types observation ID and UTC dates as `char`, science
availability as `boolean`, and provides expiry/PPS/SAS fields. Its `duration`
description is exposure on-time but declares no unit; do not silently assume
seconds or substitute it for cleaned event exposure. The successful schema
discovery also exposes `xsa.v_exposure`, `xsa.v_instrument_mode` and
`xsa.data_product`. Their **column schemas and joins remain unverified**.

## Next executable stage: XMM-C0b, still metadata only

Recommend this as the next alternative if the current TESS fixed confusion/
calibration test fails. It has better-established incremental coverage than
the generic 5XMM idea, but still no demonstrated discovery yield. It does not
justify displacing a nearly complete TESS test or claiming XMM is calibrated.

**Smallest adopted unit should be C0b-1: one known-control availability check.**
Use at most two metadata requests / 256 KiB total / 30 seconds per hard-bounded
worker: first the schema query below, then a separately frozen product/exposure
query for **`0884250101` only**. Require public EPIC event-list and source-list
identities, camera modes and complete advertised sizes. If the schema does not
support a verifiable bounded second query, stop there. No file HEAD/GET, second
control or new-observation expansion is implied. The five-observation C0b plan
below is the next proposed envelope, only after a parent review of C0b-1.

Freeze exactly the three IDs above and the two published control observations
`0884250101` and `0886121001`. No replacement field, date expansion or unknown-
coordinate query. The immediate executable operation is this schema query:

```sql
SELECT table_name,column_name,datatype,unit,description
FROM TAP_SCHEMA.columns
WHERE table_name IN ('xsa.v_exposure','xsa.v_instrument_mode',
                     'xsa.data_product','xsa.v_publication_observation')
ORDER BY table_name,column_name
```

This statement is proposed, **not executed**. Table names were observed in the
service schema; column/join keys must come from this response, not invention.
Then freeze the exact five-ID product/exposure metadata query before running
it. Include only identifiers, camera/submode, acquisition/release/processing
dates, advertised product type/size and public access locator; do not request
source coordinates or science arrays. A publication association query for
these IDs is a useful flag, not a complete proof of literature novelty.

Prospective C0b limits: at most eight synchronous metadata requests, one attempt
each, at most 1 MiB response bytes total, 30-second tree-aware wall limit per
worker. No event/LC/image GETs, async archive jobs or unbounded product bundles.
This is a proposed budget, not a measured archive cost. Existing audited bounded
transport should be reused if adopted, not a new science pipeline built now.

Acceptance is deliberately narrow:

1. Account for all five frozen observations, including empty, missing,
   proprietary, failed and unsupported cases. Do not drop any and replace it.
2. For at least one of the three new observations, verify public, explicitly
   identified EPIC imaging event products for PN and at least one MOS camera,
   plus the required source-list product. Document time coverage/overlap in
   metadata if available; metadata overlap is not validated good-time overlap.
   Verify usable supported modes against the published method before acceptance.
3. Verify complete product identity and advertised sizes for that observation
   and both known controls, with an aggregate proposed acquisition cap of
   **1 GiB**. This is a resource gate, not a sensitivity or science threshold.
   If sizes, modes, required joins or product completeness cannot be established
   under C0b's budget, record `STOP_METADATA_INCOMPLETE`. Do not download just to
   find out. A mode/product-ineligible three-row sample is `STOP_NO_ELIGIBLE_ROW`.
4. The result may be `PASS_PRODUCT_METADATA_FOR_CONTROL_PROTOCOL`, never
   `PASS_DISCOVERY_READY`. A separate prospective protocol must fix scientific
   control recovery, real-background/CCD-artifact negatives, camera concordance,
   multiple-testing accounting, compute/storage caps and stopping rules before
   any event acquisition or measurements. Later-literature coverage must be
   assessed before claiming a new transient, class or physical mechanism.

These are proposed gates, not enacted thresholds or a permission request to
launch unknown-source work. No unknown scan has begun.

### Photon-processing feasibility is a separate gate

The paper uses processed EPIC event and source-list products, and ESA documents
public PPS access. That supports checking a small **PPS control bundle** before
considering raw-ODF reprocessing; it does not prove that the present workstation
can execute EXOD or that no SAS-dependent preparation is needed. The inspected
author `main.py` imports its own `Pipeline`; it is not a standalone executable
recipe, environment lock or successful run on this Windows workstation.
[Published method](https://arxiv.org/html/2503.14208v2),
[ESA archive/PPS documentation](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/xsa.html).

Only bounded Python/HTTP metadata access was demonstrated locally. No installed
SAS tools, EXOD dependency compatibility, calibration assets, event-processing
RAM/storage cost or scientific wall time were verified. In particular, neither
ESA's archive bulk-reprocessing SAS version nor the PPS `sas_version` field
means that version is installed here. Do not automatically install multi-GB
SAS/calibration packages, use remote RISA processing or deploy another runtime.

After C0b-1, the smallest *possible* actual photon experiment would be a new,
separately reviewed **single published-control PPS recovery contract**, with a
manifest/cap derived from verified sizes, fixed published time/energy tests,
camera/background artifact checks, one bounded execution and complete failed-
product accounting. It must first demonstrate that retained PPS inputs suffice
for the selected implementation without unapproved environment changes. Failure
to establish that is `STOP_RUNTIME_FEASIBILITY`, not a reason to acquire more
observations. The second published control and empirical negatives would still
be required before any unknown search; a single positive recovery is inadequate.
No photon protocol or software was developed or authorized in this research.

Thus the recommendation is **GO for a tiny metadata-only known-control
availability decision; NOT GO for photon search**. XMM requires its own frozen
science/negative-control contract. TESS controls, permissions and nominal
uncertainty gates do not transfer to a different detector or counting process.

## Evidence retention and bounded-access receipt

The final retention tranche was frozen to exactly three metadata GETs and
300 KiB total response bytes: pinned list, exact date query, and product-table
name discovery. All returned HTTP 200. **168,544 response bytes** were retained;
the receipt itself adds bookkeeping bytes. The list and row response were
re-read once specifically to retain originals after the parent authorized
small metadata artifacts; both byte hashes matched their initial probes.
These were provenance snapshots, not retries after a transport failure.

| Retained response | Bytes | SHA-256 |
|---|---:|---|
| `exod-all-obsids.txt` | 166155 | `f55667e7d593915a65510833afff19fc32bbeae43dc35b640f5e512451333e0e` |
| `public-post-paper-three.json` | 1855 | `2ec6657f170a17ff7ac6a4ff91c0b59d081e84fda72813f48229cab8751690db` |
| `product-table-schema.json` | 534 | `88e13f868f7487e78a147aec13f5a2280881c3f276350da79e8d75a8e4062fb3` |

[Raw responses and request URLs](XMM-EXOD-ELIGIBILITY-2026-09-12-data/receipt.json)
are preserved without newline conversion. The three final requests used
5-second connect / 15-second read timeouts, streamed byte caps and a 25-second
elapsed check between chunks; measured durations were 0.250, 0.594 and 0.563
seconds. This probe is **not proof of a hard process-tree deadline**: a blocking
read can delay the elapsed check. C0b requires the separately tested hard runner.

Earlier successful probes (not retained as raw artifacts) read the GitHub commit
record, pinned tree metadata, initial ID list, 303-byte example source, observation
table-name schema, 2164-byte column schema and initial successful three-row query.
The first malformed local Python quoting attempt stopped at syntax parsing
before network. The Boolean-predicate row query failed HTTP 400 as recorded
above. Web views included author paper/repository and ESA/IRAP documentation;
the detailed IRAP release page and some GitHub web/API fetches were unavailable,
and the NXSA web UI exposed only a JavaScript shell. No failed web view was used
as evidence that data did not exist. Direct public metadata access, not those UI
failures, supplied the concrete membership result.

This is a bounded follow-up, not exhaustive internet research. The scientifically
important remaining uncertainty is **usable, independently checkable exposure
and later prior art**, not whether the 2026 catalogue's headline count is larger.
