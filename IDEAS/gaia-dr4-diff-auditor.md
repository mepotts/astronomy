# Gaia DR4 diff auditor

**One-liner:** Point it at a published paper's Gaia target list (or a bare list of `source_id`s) and it reports, source by source, what the newest data release changed — parallaxes that moved beyond their quoted error bars, new/changed RUWE, new non-single-star orbits, new variability or astrophysical-parameter flags, new exoplanet-list membership — with the cross-release `source_id` remapping resolved and confidence-scored for you.

**Scores (U/B/E):** U 4/5 (Gaia is the most-worked catalog in astronomy, but a *per-user, paper-centric release-diff* is genuinely empty white space) · B 5/5 (pure TAP + pandas + report-gen; no hardware, no gated data) · E 5/5 (a tool pros run on their own papers within days of a hard, dated catalyst — high citation surface)

**Status:** proposed

## The wedge

**What exists already (adversarial prior-art check):**
- **The ESA Gaia Archive itself** ships the *raw material* but no product. It publishes precomputed cross-release neighbour tables — `gaiadr3.dr2_neighbourhood` (2,113,600,501 rows; columns `dr2_source_id`, `dr3_source_id`, `angular_distance` [mas], `magnitude_difference` [mag], `proper_motion_propagation` [bool]) — and, near-certainly, a DR4↔DR3 equivalent at release. It gives you a 2-billion-row join table, not "here is what changed for the 47 stars in your Table 1, and does it matter."
- **pyia** (Adrian Price-Whelan, astropy-affiliated) is the closest prior art for the *mechanic*: `GaiaData.from_source_id(source_id, source_id_dr="dr2", data_dr="dr3")` resolves an ID across releases via the neighbourhood table and hands back a convenient data wrapper. It is a data-access convenience library — no uncertainty-normalized diffing, no NSS/variability/flag change detection, no paper-level report.
- **astroquery.gaia** exposes the primitives (`Gaia.cross_match()`, `Gaia.upload_table()`, async TAP). **gaia_tools** (Bovy) and **Astro Data Lab** (NOIRLab) do bulk access. All are ingredients, none is a diff.
- Adversarial ADS/PyPI/GitHub sweep found **no maintained tool that takes a paper's target table and reports uncertainty-aware, release-over-release changes**. Confirmed empty.

**The defensible gap:** the missing layer is *per-user, paper-centric, uncertainty-aware diffing with a human-readable "what changed and does it matter" verdict* — and, critically, honest handling of `source_id` instability turned into an auditable provenance record. pyia resolves one ID; this turns the messy 0/1/N neighbourhood of a *whole table* into a confidence-scored change report. An agent fleet fills this cheaply because it is entirely TAP queries, deterministic diff arithmetic, and report rendering — no modelling, no telescope time, no ML.

**Why now:** **Gaia DR4 releases 2 December 2026** — a full astrometric re-derivation of ~2B sources, plus non-single-star solutions, an exoplanet list, source classifications and astrophysical parameters, and (new) epoch/transit time series for all sources; DR4 astrometry is expected ~1.7× more precise than DR2 and proper motions ~4.5× (cosmos.esa.int/web/gaia/dr4). Thousands of results rest on DR3 astrometry. The day DR4 drops, every author wants to know if their result survived — and there is nothing to tell them. Build **now** against the DR3-vs-DR2 case (the neighbourhood table and both source catalogs are live and anonymous today) as a proving ground that validates the diff logic end-to-end, then "flip it on" when DR4 lands.

## Target user & the "who cites this" test

**Primary user:** a working astronomer (or their student) who published a result built on a Gaia DR3 target sample — a cluster membership list, a binary/exoplanet host sample, a distance ladder anchor, a SETI/nearby-star selection. **The moment they reach for it:** the week DR4 releases, asking "did DR4 move any of my stars enough to change the conclusion, give any of them a new NSS orbit, or reclassify them?" Secondary user: a referee or a follow-up author checking whether a cited DR3-based sample still holds under DR4.

**Why it is citable, not just consumable:**
- It produces a **reproducible, versioned audit** (a DOI'd report + machine-readable diff table) that a follow-up paper can cite as "we re-verified the DR3 sample against DR4 using [tool] and N/M sources shifted <3σ."
- **Two RNAAS shots** (1-page, citable): a methods note at M2, and an **aggregate note post-DR4** — "how far DR4 moved published DR3 parallaxes across N papers" — which is itself a novel, citable measurement of release-to-release impact.
- Provenance value is evergreen: the same tool audits DR2→EDR3→DR3 diffs, so it is useful and citable *before* DR4 too.

## Data sources & access

- **TAP endpoint:** `https://gea.esac.esa.int/tap-server/tap` — **anonymous access works** (no account needed) via `astroquery.gaia` (`Gaia.launch_job_async(adql)`). ADQL queries are capped at the service's **3,000,000-row `outputLimit`**, timeout 90 min (anon) / 120 min (registered). Note the widely-repeated "sync caps at 2000 rows" is **wrong as a server limit** — verified 2026-07-28, a raw sync query with no `TOP` returned **50,000 rows**; the 2000 figure describes the Archive web UI's *basic* mode and some client defaults. Anonymous job results are retained **3 days**. Output in VOTable / CSV / FITS (cosmos.esa.int Gaia-users programmatic-access; astroquery.readthedocs.io/en/stable/gaia).
- **Tables (all public, all TAP-queryable anonymously):**
  - `gaiadr3.gaia_source` — `parallax`, `parallax_error`, `pmra/pmdec` (+errors), `ruwe`, `phot_g_mean_mag`, `non_single_star` (bit-encoded modelling flag), plus `in_qso_candidates`/`in_galaxy_candidates` etc.
  - `gaiadr3.dr2_neighbourhood` — the cross-release matcher described above (also `gaiaedr3.dr2_neighbourhood`).
  - NSS: `gaiadr3.nss_two_body_orbit`, `nss_acceleration_astro`, `nss_non_linear_spectro`, `nss_vim_fl` (~813,000 NSS solutions in DR3).
  - Variability: `gaiadr3.vari_summary` (boolean `in_vari_*` membership columns; ~10M variable sources; light curves via DataLink).
  - Astrophysical parameters: `gaiadr3.astrophysical_parameters` (+`_supp`) — ~470M sources.
  - Previous-release catalogs for the proving ground: `gaiadr2.gaia_source`, `gaiaedr3.gaia_source`.
- **Account-free path (default):** the entire DR3-vs-DR2 proving ground runs anonymously — the neighbourhood table and all catalogs are public. The tool resolves an input ID list by **chunked `WHERE source_id IN (...)`** async ADQL (or an uploaded VOTable) rather than depending on the server-side `cross_match()`/`upload_table()`, which require a (free) archive login and per-user storage. Registered login is an *optional* fast path for very large uploads only.
- **Input formats accepted:** a CSV/VOTable of `source_id`s; a scraped machine-readable target table (**AAS MRT**, **VizieR** catalog, or arXiv source); or an ADS **bibcode** → resolved object/target list.
- **DR4 unknown (state plainly):** the exact DR4 schema and the **DR4↔DR3 neighbourhood table name/columns are not yet published**. Design to the established DR3 pattern (each release ships a neighbour table to the previous release) and adapt on release; keep a position+proper-motion client-side crossmatch as a fallback so the tool is not blocked if the official DR4 table is late.

## Architecture sketch

Minimal-runnable-first Python package (working name `gaia-diff`): `astroquery` + `pyvo` + `pandas`/`pyarrow` + `astropy`. Single entrypoint `audit(source_ids, from_release="dr2", to_release="dr3") -> Report`.

Components and data flow (`bibcode/CSV → resolver → matcher → per-release fetch → diff → report`):
1. **Input resolver** — paper table / CSV / bibcode → a clean `source_id` list tagged with its release-of-origin.
2. **Cross-release matcher** — query the neighbourhood table; for each input ID return the **0 / 1 / N** candidate set with `angular_distance`, `magnitude_difference`, `proper_motion_propagation`, and a derived **match-confidence**. Never silently pick one of N.
3. **Release fetchers** — pull the relevant columns from each release's `gaia_source` + NSS + `vari_summary` + `astrophysical_parameters`.
4. **Diff engine (deterministic)** — the core value:
   - **parallax sigma-shift** = `|plx_to − plx_from| / sqrt(err_to² + err_from²)`, flagged against a user threshold (default 3σ), with an explicit note that zero-point/correlated systematics mean this is a *flag for review*, not a significance claim.
   - **RUWE** crossing (e.g., through 1.4), new/changed value.
   - **new `non_single_star` bits** (source gained an NSS orbit/acceleration/spectro/VIM solution).
   - **new `in_vari_*` membership** and **new/changed astrophysical-parameter flags**.
   - **new exoplanet-list membership** (activated when DR4's exoplanet list lands).
5. **Report renderer** — per-source rows plus a **paper-level summary** ("N of M sources moved >3σ in parallax; K gained NSS orbits; J newly flagged variable"), emitted as HTML / Markdown / notebook **and** machine-readable JSON/CSV for citation.

Layered later: an **MCP server** wrapper (audit a bibcode from any Claude/LLM client) and a small Streamlit/Gradio web form.

**Handling `source_id` instability (the central design problem, head-on):** `source_id` is **not stable across releases** — merging, splitting, and deletion of identifiers during E/DR3 processing means there is *no guaranteed one-to-one correspondence* between releases (GDR3 docs, chap. 16 Cross-match with DR2). The tool therefore **never joins on `source_id` across releases.** Every input ID is resolved through the neighbourhood table into one of three cases, each handled explicitly: **0 counterparts** → reported as "no counterpart in target release (possibly deblended/removed) — needs positional follow-up"; **1 counterpart** → accepted but still validated against `angular_distance` + `magnitude_difference` + `proper_motion_propagation` thresholds; **N counterparts** → *all* candidates surfaced with their separations and Δmag and a confidence score, never auto-collapsed. A position+proper-motion propagation crossmatch is the fallback/override where the user supplies coordinates. This 0/1/N provenance record — not just "the parallax changed" — is the moat.

## Milestones

- **M0 — kill checks (cheapest disproofs).**
  - *Prior-art:* email Adrian Price-Whelan / open a pyia issue asking whether a DR4 release-diff is planned; check DPAC DR4 plans and GaiaUnlimited; sweep ADS/PyPI/GitHub for any paper-level diff tool. *Data smoke test:* anonymously TAP-query `gaiadr3.dr2_neighbourhood` for 100 known DR2 IDs and confirm the 0/1/N distribution, then compute DR2→DR3 parallax sigma-shifts end-to-end.
  - **Acceptance:** a one-page landscape memo naming every adjacent tool + a notebook that resolves 100 DR2 IDs to DR3 and prints their parallax sigma-shifts. **Kill if** a maintained tool already emits paper-level release diffs, or the neighbourhood match fails for a large fraction of ordinary targets.
- **M1 — thin end-to-end slice.** `audit()` takes a CSV of DR2 `source_id`s, resolves them via `gaiadr3.dr2_neighbourhood` with confidence scoring, pulls `parallax`/`parallax_error`/`ruwe`/`non_single_star` from DR2 and DR3, and emits a per-source diff + summary.
  - **Acceptance:** on a frozen fixture of ~50 real `source_id`s from a known published table, the tool reproduces hand-verified sigma-shifts and correctly classifies the 0/1/N cases; enforced by a golden-file test in CI.
- **M2 — expansion + first distribution.** Add NSS-orbit, variability (`in_vari_*`), and astrophysical-parameter diffing; add paper ingest (AAS MRT / VizieR / arXiv scraping, bibcode → target list); HTML/notebook report; publish to PyPI; methods RNAAS.
  - **Acceptance:** run end-to-end from **bibcode → report** on 3 real DR3 papers.
- **M3 — DR4 flip + full distribution.** Within days of 2 Dec 2026, swap in the DR4↔DR3 neighbourhood table + DR4 schema; add exoplanet-list membership; ship the MCP server + web form; write the aggregate RNAAS.
  - **Acceptance:** within a week of DR4 release, produce a correct audit of a real DR3 paper *and* a submitted aggregate RNAAS draft.

## First week / first tasks

1. **Anonymous TAP smoke test:** query `gaiadr3.dr2_neighbourhood` + `gaiadr2/gaiadr3.gaia_source` for a 100-ID sample; confirm the 0/1/N split and that all needed columns are present.
2. **Prototype the matcher:** given a DR2 `source_id`, return DR3 candidates with `angular_distance`, `magnitude_difference`, `proper_motion_propagation`, and a confidence score; codify the accept/ambiguous/miss thresholds.
3. **Prototype the diff metric:** implement and document the parallax sigma-shift and RUWE-crossing semantics (with the zero-point caveat written down).
4. **Prior-art memo + outreach:** write the wedge paragraph; email pyia / check DPAC DR4 plans.
5. **Pick the M1 fixture:** choose a real DR3-based paper with a machine-readable target table; hand-verify ~5 sources as ground truth.
6. **Skeleton the package:** `pyproject.toml`, `audit()` entrypoint, golden-file test harness.

## Risks & kill criteria

- **pyia or the archive ships an official paper-level diff.** Biggest risk; would shrink the wedge. *Mitigate:* build *on* pyia rather than reinvent the resolver, and own the differentiators — the paper-centric report, the uncertainty-normalized change semantics, and the RNAAS. **Kill** if a maintained, freely accessible tool produces citable per-paper release diffs first.
- **`source_id` remapping is worse than expected** for crowded fields / N-counterpart ambiguity dominates. *Mitigate:* honesty over coverage — surface ambiguity, never guess. But if a large fraction of typical paper targets are unresolvable, the value proposition weakens.
- **DR4 diverges from the DR3 pattern** — no DR4↔DR3 neighbourhood table at release, or it is delayed/differently-shaped. *Mitigate:* the client-side position+proper-motion crossmatch fallback keeps the tool working without the official table.
- **Uncertainty semantics are contestable** (parallax zero-point, spatially correlated systematics). A naive sigma-shift over-claims significance. *Mitigate:* incorporate the zero-point correction, present results as "flag for review," never as a detection. **Kill** if the diff can't be made defensible to a referee.
- **Interest evaporates after the DR4 news cycle.** *Mitigate:* the evergreen proving-ground use (DR2/EDR3/DR3 provenance/reproducibility) gives the tool a life independent of the launch spike.

## Distribution & legitimacy

- **PyPI:** `gaia-diff` package; pursue **astropy-affiliated** status and stay astroquery-adjacent; optionally propose it to **pyia** as a submodule rather than compete.
- **RNAAS ×2:** a methods note at M2, and the **aggregate impact note** post-DR4 ("how much DR4 moved published DR3 parallaxes across N papers") — a citable original measurement.
- **Zenodo DOI** for the versioned tool and for the aggregate diff dataset; optional **HuggingFace dataset** for the aggregate release-diff table with a small leaderboard of "most-moved" published samples.
- **MCP server** on the registry so any Claude/LLM client can audit a bibcode conversationally.
- **JOSS** paper once the package and test suite mature.
- Optional small **web form** (Streamlit/Gradio): paste a bibcode or upload a CSV → get an audit.

## Rough size

**To M1:** ~1–2 focused agent/desk weeks — TAP queries, the neighbourhood matcher with confidence scoring, the sigma-shift diff, and a golden-file test on a frozen fixture are all mechanical. **Single biggest uncertainty:** the DR4↔DR3 cross-match provenance — whether ESA ships a DR4 neighbourhood table promptly and how severe N-counterpart ambiguity is for real published target tables. That one factor decides whether both the "flip on in December" promise and the match-confidence story hold up; everything else (schema, TAP access, report rendering) is known and low-risk.

## Sources
- Gaia DR4 date/contents/precision — https://www.cosmos.esa.int/web/gaia/dr4 ; https://www.cosmos.esa.int/web/gaia/data-release-4
- `source_id` not stable across releases (merge/split/delete; use neighbourhood matching) — https://gea.esac.esa.int/archive/documentation/GDR3/Catalogue_consolidation/chap_cu9dr2xm/sec_cu9dr2xm_motivation/
- `dr2_neighbourhood` schema (2.11B rows; 5 columns) — https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_cross-matches/ssec_dm_dr2_neighbourhood.html ; https://gaia.aip.de/metadata/gaiadr3/dr2_neighbourhood/
- TAP endpoint, anonymous access, 3M-row async / 2000-row sync limits, 3-day retention — https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access ; https://astroquery.readthedocs.io/en/stable/gaia/gaia.html ; https://www.cosmos.esa.int/web/gaia-users/archive/faq
- NSS tables (~813k solutions) — https://www.aanda.org/articles/aa/full_html/2023/06/aa43940-22/aa43940-22.html ; https://arxiv.org/pdf/2206.05595
- Variability (`vari_summary`, `in_vari_*`, ~10M variables) — https://www.aanda.org/articles/aa/full_html/2023/06/aa44242-22/aa44242-22.html
- Astrophysical parameters (~470M) + RUWE — https://www.aanda.org/articles/aa/full_html/2023/06/aa43800-22/aa43800-22.html
- Real DR2→EDR3/DR3 parallax shifts (~15 μas median, +30% precision) — https://www.aanda.org/articles/aa/full_html/2021/05/aa39657-20/aa39657-20.html ; https://arxiv.org/pdf/2402.10714
- pyia cross-release resolver (`from_source_id`, dr2→dr3) — https://pyia.readthedocs.io/en/latest/index.html
- astroquery cross_match/upload_table primitives — https://astroquery.readthedocs.io/en/latest/gaia/gaia.html
