# XMM later-work overlap check — 2026-09-12

**The three-observation post-EXOD increment survives this bounded check, but
“unsearched” and “novel” remain unproved.** No verified later search was found
that explicitly processes these three March 2025 observations. Later STONKS
deployment and substantial 5XMM processing changes make a general claim that
the XMM archive lacks modern variability searches untenable.

This does not change the immediate control-first priority: demonstrate that
the selected PPS products and counts method work on the published control.
It does not authorize unknown-source acquisition. A future candidate requires
its own precise literature/alert comparison before any novelty claim.

## Exact observation ledger

The existing [eligibility evidence](XMM-EXOD-ELIGIBILITY-2026-09-12.md) establishes
these dates and absence from the authors' pinned 15,105-ID input list. Those
retained data were not downloaded again in this study.

| Observation | Observed | Exact later-search inclusion verified here? |
|---|---|---|
| `0942190201` | 2025-03-20/21 | No; unknown |
| `0940541201` | 2025-03-21 | No; unknown |
| `0943750401` | 2025-03-21/22 | No; unknown |

An exact-ID web query returned no relevant indexed publication match, and
the inspected STONKS paper text contains none of the three strings. Neither
operation checks supplementary catalogues comprehensively, unpublished work,
PI analyses, private alerts, or papers indexed without observation IDs. They
are **not negative coverage certificates**.

## 1. EXOD: no verified later observation ledger

The current arXiv history still lists v2 on **2025-03-19**, after v1 on March 18;
no later version is shown there. That supports the earlier publication boundary,
not a claim about all later executions of the software.
[EXOD II version history](https://arxiv.org/abs/2503.14208).

The search-index rendering of the authors' catalogue landing page describes
EXOD DR1, 15,105 inputs spanning 2001-08-19–2023-11-16, with a displayed update
date of 2024-10-17. Direct HTTPS and HTTP opens both failed through the web
reader. Treat this as **indexed, potentially stale author-site information**,
not a newly verified live catalogue state or a 2026 completeness statement.
No linked FITS catalogue was downloaded.
[Author EXOD catalogue landing page](https://xmm-ssc.irap.omp.eu/exod/).

The author repository opened, but its rendered releases section supplied no
usable version/coverage record. The rendered README contains research tasks,
not an authenticated later all-observation execution receipt. I did not infer
that an empty rendered releases section means no updates exist.
[Author EXOD2 repository](https://github.com/nx1/EXOD2).

Thus no new EXOD coverage ledger replaces the retained pinned membership
evidence. Equally, this check cannot rule out an unpublished or unindexed rerun.

## 2. STONKS: important later competitor, different tested coverage

Webbe et al.'s **2026** first-results paper examines 231 Galactic-plane
observations acquired **2021-03-13–2024-10-10**; 213 had source lists processed
by STONKS. It studies long-term variability by comparison with archival fluxes,
then examines selected alerts' light curves and spectra. It reports 78 screened
alerts associated with 70 sources. Its introduction says STONKS is applied to
all XMM observations from AO24, with alerts shared with PIs and, with approval,
the community. The paper also revisits our published magnetar control.
[STONKS first results, §§1–3 and 5.1](https://arxiv.org/html/2601.19328v1).

**Inference:** the stated 2024 end date excludes the three later exposures from
this paper's survey input sample. Broader deployment nevertheless weakens a
claim that new public observations receive no transient scrutiny. The inspected
text is not a per-observation processing ledger for March 2025, and this study
did not map those dates to AO24 or obtain alert receipts. An exposure missed by
a long-term alert method is not thereby proven unexplored on short timescales.

## 3. 5XMM-DR15: new processing, not these new photons

ESA's current handbook identifies the June 2026 release and a public-data
cutoff in 2024. HEASARC specifies observations acquired through **2024-10-14**,
14,616 observations, and processing with pipeline 21.51. Consequently this
catalogue's observation population cannot include the three March 2025 inputs.
[ESA 5XMM description](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/uhb/node137.html),
[HEASARC 5XMM-DR15 documentation](https://heasarc.gsfc.nasa.gov/W3Browse/all/xmmssc.html).

The latter documents meaningful later work: revised effective-area/CCD-layout
calibration, products extracted above 50 EPIC counts, stacked processing and a
STONKS multi-mission baseline compiled in February 2026. These are reasons to
check current pipeline products and prior variability information, not evidence
that March 2025 event lists entered the catalogue. Its public-cutoff text differs
between sections (October 31 versus November 30); the common 2024 acquisition
endpoint is sufficient for the narrow exclusion above. No catalogue rows or
observation-list files were fetched in this task.
[HEASARC processing and long-term-variability sections](https://heasarc.gsfc.nasa.gov/W3Browse/all/xmmssc.html).

## 4. Other 2026 work: leads, not established coverage

A publisher-indexed article, *Discovering Periodic and Repeating Nuclear
Transients in the XMM-Newton Archives*, has an indexed first-publication date
of 2026-04-24 and describes preliminary periodic searches plus STONKS in the
automatic reduction pipeline. Its direct publisher page failed to open, so
I did not verify its complete sample, processing dates or input identifiers.
This is an unresolved primary-literature lead, not evidence that the three
observations were processed.
[Publisher article](https://onlinelibrary.wiley.com/doi/10.1002/asna.70102).

Other results included individual 2026 transient/pulsation papers, but no result
established a newer systematic short-timescale search covering the specified
three observations. Those search snippets were not promoted into coverage
evidence, and unrelated source details were not followed up. This bounded
sample of results must not be described as an exhaustive literature review.

## Consequence for route priority

Keep the route narrowly described as **a small post-paper observation increment
with unknown later-search overlap**, not a generic new-catalogue discovery
opportunity. The date/membership evidence supports a potential search unit;
it predicts neither recoverable exposure nor discovery yield. STONKS and modern
pipeline processing mean any later source should be checked against both
short-timescale detections and long-term/source-specific work, even if absent
from EXOD DR1.

No verified exact-coverage finding here warrants abandoning the current
published-control structural/recovery work. Conversely, control success alone
would not settle the three observations' novelty. Before selecting an unknown
field, require a bounded exact-input/alert/publication comparison using the
then-authorized metadata interfaces. If exact later coverage is found, record
what timescales, bands, screening and source populations it tested; do not
automatically equate any prior analysis with complete exclusion of all possible
new science. Any decision to revisit a searched field needs a specific,
testable methodological or physical difference, not relabeling old photons.

## Search/inspection receipt

Exactly six targeted web search queries were used:

1. `EXOD XMM transient search 2026 2025 catalogue update`
2. `XMM short timescale transient search 2026 observations 2025`
3. `"0942190201" OR "0940541201" OR "0943750401"`
4. `site.arxiv.org "XMM" "transients" "2026" search archive`
5. `"EXOD" "2026" catalogue search`
6. `"STONKS" "first results" XMM 2026 2025`

Seven distinct primary documents/pages were targeted for opening: the two
5XMM documentation pages, EXOD landing page, EXOD arXiv history, author GitHub
repository, STONKS full HTML paper and Wiley article. Five opened; the EXOD
landing page and Wiley article did not. Reopening/finding within those sources
did not expand the document set. Some search results were irrelevant matches
to the name EXOD; they supplied no scientific evidence.

No event files, science/catalogue arrays, catalogue FITS files, new observation
queries, external messages, accounts or software changes occurred. Only this
local note was written. All statements are bounded to what was verifiable on
September 12, 2026, with failed views and unknown coverage retained explicitly.
