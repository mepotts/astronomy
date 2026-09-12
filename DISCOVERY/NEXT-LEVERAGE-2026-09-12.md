# Near-term discovery leverage: bounded portfolio triage

Date: 2026-09-12. Research only; no pipeline, new scientific inputs, unknown
coordinates, accounts, publication or Git actions. This is a bounded comparison,
not an exhaustive literature or internet search.

## Decision

**Keep TESS localization and empirical negatives as the lead experiment. No
alternative demonstrated materially better near-term discovery leverage in this
review.** This is a decision about the next falsifiable measurement, not a claim
that TESS has a measured higher discovery yield or will produce a discovery.

The one concrete challenger is an **incremental XMM-Newton fast-transient search
outside the actual EXOD II processing footprint**. A June 2026 catalogue release
is genuinely changed evidence relative to the earlier generic-XMM dismissal.
However, its unsearched, usable exposure increment is not established. Do not
start event processing or infer that increment by subtracting catalogue counts.
Current disposition: **STOP at unverified coverage/novelty membership**, with a
metadata-only next step proposed below, not executed or adopted.

## Repository basis and opportunity cost

Read the first 120 lines of `STATUS.md`, current search and direction records,
the September 5 new-work record, relevant prospectus sections, TNS status, ITF
M14 results/M15 identity repair, and TESS README/operating rules. The live records
supersede older aspirational research priorities.

| Existing route | Evidence that matters now | Near-term decision |
|---|---|---|
| TESS short eclipses | Three published periods and near-target pixel signals recovered; all three catalogues now available. One coarse consistency pass, two crowded fields; even the cleaner field has a brighter neighbour outside the one-pixel diagnostic. | Finish calibrated localization and empirical negatives. These address a measured failure mode using an existing tested acquisition/measurement chain. Not yet an unknown search. |
| ITF | Daily archive/watch is active. M15 exact-identity matcher has synthetic tests, but the real exporter's debiasing, duplicate reconciliation and identity contract remain unproven. M14 failed mandatory accounting. | Maintain monitoring; identity repair remains useful correctness work, not evidence of an immediately discovery-ready campaign. Do not reinterpret M14's stopped output. |
| VLASS / DASCH / CCOR / DR11 | Real controls or fixed validation gates failed; VLASS specifically failed known-source recovery and held-out null scatter despite reference/injection successes. | No scaling or threshold relaxation. A new method would need evidence beyond a desire to keep searching. |
| Dyson E / eROSITA | E measurement/deblend validity failed; eROSITA is a corrected selection census, not confirmed physical disappearances. | Neither becomes a discovery by drafting a paper or enumerating existing rows again. |
| TNS / CHIME / dated projects | Missing complete enumeration, observing sensitivity, actual release or future observations remain the documented dependencies. | No new evidence found here that changes those gates; no endpoint polling or dated-gate replay performed. |

Local evidence: [current search](SEARCH-2026-09-12.md),
[direction](DIRECTION-2026-09-06.md),
[TESS current state](../tess-short-eclipses/README.md),
[M1e result](../tess-short-eclipses/M1e-RESULT-2026-09-12.md),
[ITF identity contract](../itf-linker/M15-IDENTITY-REPAIR.md),
[VLASS M2 STOP](../vlass-pilot/m2-results-2026-09-12.md).
No future TESS PRF or negative-control result is presumed by this comparison.

## Challenger: what changed, and what did not

ESA documents 5XMM's June 2026 release: 14,616 observations public by
2024-11-01, 818,656 unique sources and 2,578,752 **detections or upper limits**.
Thus neither the release date nor the row count measures new observing exposure.
ESA warns about spurious-detection features and recommends summary-flag filtering.
[ESA 5XMM handbook](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/node137.html).

The IRAP public interface identifies the release as **5XMM-DR15**, dated
2026-06-05, and exposes search/download documentation and legacy DR9–DR14 access.
The landing page was readable without authentication. A linked detailed release
page timed out; no catalogue response or event product was retrieved. A visible
web interface establishes availability of documentation, not verified complete
machine-readable access.
[IRAP catalogue interface](https://xmm-catalog.irap.omp.eu/).

EXOD II already attempted **15,105 observations**; its abstract reports 12,926
successful observations while section 3.1 says 12,923. Failures include missing
source lists and unsupported observing modes. Its input types are processed
EPIC `EVLI` event lists and `OBSMLI` source lists. It searches 5/50/200-second
bins in three energy bands, including high-background intervals; these are not
new search ideas. Published recovery controls include 4XMM J235440.7-373019 in
observation `0884250101` and 4XMM J175136.9-275858 in `0886121001`. Their proposed
QPE/magnetar classifications are candidates, not secure class labels. Detector
artifacts and background modelling remain important limitations.
[EXOD II, sections 2–4](https://arxiv.org/html/2503.14208v2).

Consequently, `14,616 - 12,926` is **not** a count of newly unsearched observations.
We need identifier-level attempted/successful/ineligible sets, their provenance,
and observation/product versions. An observation missing from a detection
catalogue can simply have produced no detections; it is not necessarily unsearched.
The inconsistent successful totals are another reason to use actual membership
and run outcomes instead of headline arithmetic.

The authors' public repository is readable and links documentation. Its visible
data directory lists `all_obsids.txt`, `dr14_obsids.txt`, `observations.txt`,
`obs_ccd_check.txt` and `unsuccessful_obsids_7k_run.txt`. I did **not** fetch those
files or authenticate them against the paper's final run. In particular, a file
explicitly naming a 7k run must not silently stand in for all final failures.
The mutable default branch is not a release-bound membership receipt.
[Author repository](https://github.com/nx1/EXOD2),
[visible metadata filenames](https://github.com/nx1/EXOD2/tree/main/data).

## Smallest next experiment, if separately adopted

**XMM-C0: coverage ledger, metadata only.** This is the single proposed alternative
experiment, not a generic new transient pipeline or an observation download plan.

1. Freeze a public EXOD revision and identify the final attempted-observation
   ledger, per-mode success/failure semantics, and catalogue version used. If the
   available files cannot be tied to the published run, record that unresolved
   provenance and stop; do not replace the ledger with a list of detections.
2. Establish a documented current XSA observation/product metadata schema and a
   reproducible public-release cutoff. Preserve observation IDs as strings,
   exposure/submode, release status, processing version and advertised input
   sizes. Use IDs and service metadata only, not source cones or unknown fluxes.
3. Report three distinct sets: already attempted; demonstrably outside the
   authenticated attempt ledger; indeterminate. Do not count failed or unsupported
   prior runs as fresh observations. Additional literature coverage would still
   have to be checked before labelling the second set unsearched by everyone.
4. Before any event download, verify metadata for the two published controls
   above, including available instruments and complete product sizes. Their
   identifiers are fixed positive-control choices, not unknown candidates. A
   separate protocol would then specify recovery, detector/background negatives,
   independent-camera tests where available, runtime limits and scientific gates.

Suggested metadata preflight budget, **not measured resource costs**: at most
eight new metadata/page requests, 30 seconds per request, 2 MiB retained response
bytes in total, one attempt each, no asynchronous archive jobs, no catalogue bulk
download and no event/LC/image products. Require a bounded, tree-aware request
runner and complete failure receipts. Stop rather than extend the budget to make
coverage appear complete. Event-processing CPU, memory and storage costs are
currently **unmeasured**; there is no honest runtime or discovery-yield forecast.

Promotion would require an authenticated nonempty eligible increment, accessible
control products within a prospectively chosen cap, reproducible positive and
real-noise negative controls, and a distinct novelty/confirmation plan. No such
promotion is established in this review. Even convincing archival X-ray
variability would not by itself establish a magnetar, QPE, host galaxy, distance
or new physical mechanism. Independent detectors/archival epochs can corroborate
some signals, but a follow-up-free physical classification is not guaranteed.

## Why this does not displace TESS now

TESS has measured positive controls, retained pixels, independently checked
catalogue decoding and actual crowding information. Its next question is narrow:
can the signal be assigned to the correct source and distinguished from real
instrumental/background negatives? The XMM challenger still needs to establish
its experimental population and verify input access before reaching comparable
controls. This is not merely preference for sunk work: completing the current
TESS check can decisively reject or support the actual method on hand.

Keep XMM-C0 as a bounded fallback proposal. Reconsider allocation after TESS's
fixed localization/negative gates, or if a verified XMM membership ledger supplies
new evidence. Do not repeatedly redesign controls until one passes, and do not
promise that either route will yield a discovery.

## Public-source access receipt

Eight distinct primary URLs were opened/attempted after one two-query discovery
search batch. Re-reading sections of the same pages added no new endpoints.
Results are tool-observed page availability on this review, not a claim of live
service completeness or an uptime test. No retry loop was used.

| # | Primary URL | Result |
|---|---|---|
| 1 | https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/node137.html | Readable ESA 5XMM documentation. |
| 2 | https://arxiv.org/abs/2503.14208 | Readable author paper abstract/version metadata. |
| 3 | https://www.cosmos.esa.int/web/xmm-newton/xsa | Web fetch reported HTTP 451; access not verified. |
| 4 | https://arxiv.org/html/2503.14208v2 | Readable primary paper; methods, accounting and control sections inspected. |
| 5 | https://github.com/nx1/EXOD2 | Readable author repository landing page; no clone/install. |
| 6 | https://xmm-catalog.irap.omp.eu/ | Readable primary catalogue interface and June release notice. |
| 7 | https://xmmssc.irap.omp.eu/Catalogue/5XMM-DR15/5XMM_DR15.html | Fetch timed out; release details not verified here. |
| 8 | https://github.com/nx1/EXOD2/tree/main/data | Readable filename listing; file contents and final-run binding not checked. |

No unknown pixels/photometry or candidate coordinates were acquired or sent.
Only this note was created. Existing scientific STOPs, dated gates and publication
boundaries remain unchanged.
