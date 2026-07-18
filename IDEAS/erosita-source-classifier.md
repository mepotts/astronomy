# eROSITA Source Dossier Layer

**One-liner:** An account-free "what is this X-ray source?" service that resolves any eRASS1 X-ray detection to a plain-language dossier — best-guess class (flare star / AGN / X-ray binary / cataclysmic variable / cluster) plus the multiwavelength evidence — by unifying and translating the dozen-plus scattered eROSITA-DE DR1 value-added catalogs into one per-source answer.

**Scores (U/B/E):** U 4/5 (X-ray/high-energy got zero run-1 coverage and no per-source *translation* layer exists — but the underlying classification science is crowded, so the novelty is in the layer, not the labels) · B 5/5 (data + software only, account-free VO endpoints, reuses published verdicts, rule engine is small) · E 4/5 (real catalog, genuine oddball/disagreement discovery angle, MCP + HF distribution, Gaia DR4 refresh catalyst — but it is mostly repackaging published science, and that must stay honest)

**Status:** proposed

## The wedge

**What exists already (adversarial prior-art check).** The honest headline: *the eROSITA-DE teams have already classified most of the sky, and as of mid-2026 it is all public.* This is not a greenfield classifier.

- **Salvato et al. 2025** (arXiv:2509.02842) — the big one. Bayesian NWAY cross-match with trained priors + a machine-learning Galactic/extragalactic split, delivering optical/IR counterparts for **all 656,614** eRASS1 sources inside the Legacy Survey DR10 footprint, of which **~570,000 are likely AGN**, with photo-z from CircleZ. Released on the eROSITA page (`Salvato_etal2025_DR1_LS10.colfits.tgz`, plus Gaia-DR3 and CatWISE2020 variants), Zenodo, and VizieR — **the counterpart catalogs landed 2026-06-09.** If your pitch is "classify AGN," this already exists at scale.
- **HamStar** (Freund et al. 2024, arXiv:2401.17282) — a Bayesian coronal-probability framework that tags **138,800 coronal (stellar) eRASS1 sources** at ~91.5% completeness/reliability. This *is* the flare-star / coronal classifier, released as a DR1 catalog (`HamStar_eRASS1_Main_Likely_Identifications`).
- **Clusters** — Kluge et al. 2024 / Bulbul et al. 2024 (arXiv:2402.08452; VizieR 2024yCat..36850106B): **12,247** optically confirmed clusters (primary) + a 5,259-cluster cosmology sample, plus superclusters (Liu+ 2024) and morphology catalogs.
- **A ready-made rule-based recipe** — the Canis Major study (arXiv:2407.12583, A&A aa50637-24) already published a *transparent multiwavelength decision tree* (star / binary / AGN / symbiotic / accreting-white-dwarf / LMXB) keyed on hardness ratio, X-ray-to-optical flux ratio, Gaia parallax + proper motion, and WISE/Pan-STARRS/2MASS colors — exactly the evidence set this idea would use. But it was run on **one 8,311-source field** and shipped **no general package or all-sky catalog**.
- **A long tail of single-class papers**: variability (Boller+ 2024, arXiv:2401.17280), eRO-ExTra extragalactic transients (arXiv:2501.04208), blazars (BlazEr1), LMC HMXBs, ULXs, ultracool dwarfs, symbiotics, planetary nebulae (arXiv:2508.12895), AGB stars (arXiv:2407.10552), compact-object binaries via ZTF (arXiv:2606.01085). Each is its own FITS table with its own schema and jargon.
- **Viewers, not translators**: ESASky already ingests `eRASS1 main` and `eRASS1 hard` as clickable catalog *overlays*; HEASARC exposes them via Xamin. Neither reconciles the value-added catalogs into a per-source verdict or explains the evidence in words.

**Where the defensible gap is.** The classifications exist but are **fragmented across ~15 bulk FITS/VizieR catalogs and dozens of single-class papers, each with its own schema, probability column, and dense jargon.** To answer the one question a non-specialist actually asks — *"there's an eROSITA source here; what is it, and how confident should I be?"* — you today must know that the coronal answer lives in HamStar, the AGN answer in Salvato, the cluster answer in Bulbul/Kluge, the variability flag in Boller, and then download and join multi-hundred-thousand-row tables. Nobody ships the **usability/translation layer**: a per-source, plain-language dossier that (1) **unifies** every value-added verdict for a given source, (2) **translates** the evidence (HR, log Fx/Fopt, parallax/PM, WISE colors) into words with the *published locus/threshold that justifies each call*, (3) **reconciles conflicts honestly** (HamStar says coronal, Salvato says AGN → surface the disagreement, don't hide it) and says "unknown" when the evidence is thin, and (4) is queryable **account-free by position or name** over web + API + MCP, with no FITS-joining required. An agent fleet fills this cheaply because it is schema-mapping + a small transparent rule engine + templating — connective tissue, not new science — and it inherits the portfolio's proven translation-layer pattern (cf. adql-copilot: "reuse the always-correct foundation first; the model layers on top").

There is even a genuine coverage gap to exploit: **Salvato only covers the ~656k sources inside LS10; roughly a quarter of the ~930k eRASS1-DE sources sit outside that footprint** and carry no released extragalactic classification. For those, the transparent rule-based fallback (the Canis Major loci) is not repackaging — it is the *only* per-source verdict available.

**Why now (2026 catalyst).** Three dated hooks: (a) the **Salvato counterpart catalogs only became public 2026-06-09** and the **Main DR1 catalogue reached v1.2 on 2026-01-12** — the raw material for the dossier just finished landing; (b) **Gaia DR4 releases 2 December 2026**, re-deriving parallax/proper motion for ~2B sources, which directly sharpens the Galactic-vs-extragalactic and flare-star evidence and gives the dossier dataset a natural, citable versioned refresh; (c) MCP tooling is proliferating, so a "what is this X-ray source?" tool reaches every LLM-client user as a distribution surface.

## Target user & the "who cites this" test

- **Primary user & the moment they reach for it.** A multiwavelength or time-domain astronomer (or an advanced student) who finds *one* eROSITA source coincident with their object — a new transient, a variable star, a radio/optical source, a cluster field — and needs, in seconds and without becoming an X-ray specialist, a defensible answer to "what is this, and what's the evidence?" Secondary users: broker/alert pipelines wanting an X-ray context tag for a candidate; educators; and LLM agents answering source-identification questions via the MCP surface.
- **What makes it citable, not just consumable.** Three currencies: (1) a **versioned HuggingFace dataset of dossiers** (one uniform, reproducible, multiwavelength-evidence record per eRASS1-DE source) with a **Zenodo DOI** — the kind of value-added product people cite for their sample selection; (2) an **RNAAS** on the genuinely new output — sources where the value-added catalogs *disagree*, stars with anomalously high Fx/Fopt, and classifiable-but-unclassified sources outside the LS10 footprint — none of which any single existing catalog surfaces; (3) a **pyvo/astroquery-style package** that becomes the canonical way to pull an eRASS1 source's cross-identified, human-readable context.

## Data sources & access

Everything below has an **account-free path**. Bulk downloads from the eROSITA-DE portal need no login (usage policy is simply "acknowledge eROSITA-DE DR1 / eSASS"); the VO endpoints are anonymous.

- **eRASS1 main catalog** — ~930,203 sources, 0.2–2.3 keV, detection_likelihood > 6 (Merloni et al. 2024, arXiv:2401.17274; VizieR 2024yCat..36820034M). Covers the **Western Galactic hemisphere only** (359.94° > l > 179.94° = the **eROSITA-DE** half, public since 31 Jan 2024); the Eastern hemisphere belongs to the Russian consortium and is **not** public — a hard scope boundary, not a bug.
  - Key columns: `DET_LIKE` / `B0_Detect_Likelihood`; positional error `RADEC_ERR` / `POS_ERR` (**mean ~4.6″, median ~2″, 99% of point sources within ~10″** — small, but large enough that optical cross-ID is inherently *probabilistic*, which is why NWAY exists); per-band count rates/fluxes (`erg/s/cm²`) from which **hardness ratios** are computed; `Source_Extent` + `Extent_Likelihood` (`EXT`, `EXT_LIKE`) separating extended (cluster) from point sources.
  - Also: **hard-band** catalog (`eRASS1_Hard`, 2.3–5 keV) and a supplementary catalog (`eRASS1_Supp`).
- **Value-added DR1 catalogs to unify** (all under `erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/`, account-free FITS; most also on VizieR): `Salvato_etal2025_DR1_{LS10,GDR3,CW2020}` (counterparts + Gal/extragal + AGN + photo-z), `HamStar_eRASS1_Main_{Likely,Possible}_Identifications` (coronal), `erass1cl_primary`/`erass1cl_cosmology`/`erass1_cluster_morphology`/`erass1sc` (clusters + superclusters), `BlazEr1` (blazars), `eRASS1_HMXB_LMC`, `ulx_erass1_*` (ULX), plus the variability / eRO-ExTra tables.
- **Programmatic VO access (account-free):**
  - HEASARC **Xamin TAP** `https://heasarc.gsfc.nasa.gov/xamin/vo/tap` and cone `https://heasarc.gsfc.nasa.gov/xamin/vo/cone` — `ERASS1MAIN`/`ERASS1HARD` tables (added Sept 2024), anonymous, VOTable, driven via `pyvo.dal.TAPService`.
  - **VizieR TAP** `https://tapvizier.cds.unistra.fr/TAPVizieR/tap` (anonymous) — the main catalog and the value-added catalogs that are mirrored to VizieR (Salvato, HamStar, Bulbul/Kluge).
  - **GAVO** `dc.g-vo.org` mirrors `erass1main` via VO (registry-discoverable).
  - **eRODat** interactive basket/shopping-cart tool for bulk product download from the DR1 portal.
- **Counterpart photometry / cross-match tooling (account-free):** Legacy Survey DR10, Gaia DR3 (→ DR4 in Dec 2026), CatWISE2020/AllWISE — reachable via their own anonymous TAP or the **CDS X-Match** service; **NWAY** (Salvato et al., open source) is the reference Bayesian cross-matcher. `astroquery`/`pyvo` cover all of it.
- **Rate/format notes:** VO TAP services are anonymous but politeness-limited — batch with uploaded-VOTable joins rather than 900k per-row cone queries (same lesson as the seti-broker Gaia layer). Everything is VOTable/FITS; a one-time local ingest into Parquet/DuckDB gives fast per-source lookup without hammering the services.

## Architecture sketch

Minimal-runnable-first, deterministic core, model/ML strictly optional and layered on top.

- **Stack:** Python (`pyvo`, `astropy`, `astroquery`, `pandas`/`polars`, `duckdb`), FastAPI for the REST/web lookup, a small Jinja/JSON template layer for the dossier, later an MCP server wrapper. No GPU, no telescope time.
- **Components / data flow:**
  1. **Ingest & normalize** — pull the eRASS1 main catalog + each value-added catalog once; map every catalog's idiosyncratic schema onto a common **`Verdict` record** `{source, class, probability, evidence_columns, provenance, catalog_version}`. Store as Parquet/DuckDB keyed on the eRASS1 source name (`IAUNAME`/`DETUID`) and position.
  2. **Resolver** — position (RA/Dec + radius) or source name → the eRASS1 row(s), using `RADEC_ERR` for the search radius.
  3. **Evidence builder** — compute/collect the human-facing diagnostics: hardness ratio(s), **log Fx/Fopt** (the classic AGN-vs-star discriminator, Maccacaro et al. 1988 locus), Gaia parallax/proper motion (Galactic vs extragalactic), WISE `W1−W2` (Stern AGN wedge) and `W2−W3`, extent likelihood (cluster).
  4. **Classifier = reuse-then-fallback.** First, adopt the **published verdict** from the value-added catalogs (HamStar coronal_prob, Salvato Gal/extragal + AGN, Bulbul cluster membership, variability/transient flags). Where a source has *no* released verdict (notably the ~25% outside LS10), apply the **transparent, cited rule engine** (Canis Major loci, arXiv:2407.12583). Every rule carries its threshold and citation — nothing is asserted that a catalog value or a published locus doesn't support.
  5. **Reconciler** — combine verdicts into one headline class + confidence; when catalogs disagree or evidence is thin, emit an explicit **conflict/low-confidence** flag rather than a false certainty.
  6. **Renderer** — plain-language dossier (Markdown/HTML/JSON): "*Most likely a coronally active star. Evidence: Gaia parallax 24 mas (≈42 pc), high proper motion, log Fx/Fopt = −2.1 (stellar regime), soft spectrum; HamStar coronal probability 0.97. No AGN-like WISE colors.*" — each line traceable to a value or citation.
  7. **Surfaces** — CLI/notebook (M1) → FastAPI web + API (M2) → MCP server + PyPI package (M3).

## Milestones

- **M0 — kill checks (cheap disproofs).**
  - *Prior-art disproof:* confirm no one already ships a **unified, plain-language, per-source** eROSITA dossier that reconciles the value-added catalogs. Sweep the MPE DR1 portal, ESASky, VizieR, GitHub, HF; email the Salvato/HamStar teams describing the layer and asking if it exists or is planned. **Acceptance:** a one-page memo concluding "no unified per-source translator exists" (ESASky = overlays only; the catalogs remain separate) — or a decision to pivot/kill if it does.
  - *Data-access smoke test:* an **account-free** notebook that, with no login, cone-searches eRASS1 main (HEASARC Xamin TAP), and for one known source pulls ≥2 value-added verdicts (e.g. HamStar `coronal_prob`, Salvato class) + ≥1 Gaia/WISE counterpart. **Acceptance:** runs end-to-end anonymously; if any value-added catalog is bulk-FITS-only (not on TAP), note the local-ingest fallback cost.
  - *Value-of-reconciliation check:* on 100 random sources, measure how often a single catalog already gives an unambiguous class vs. how often coverage gaps / disagreements exist. **Acceptance:** ≥~20% of sources are outside LS10 or show cross-catalog ambiguity — enough to justify the unification (kill/rethink if essentially every source is trivially classified by Salvato alone).
- **M1 — thin end-to-end slice.** CLI/notebook: given RA/Dec or an eRASS1 name, emit a plain-language dossier — headline class + confidence + evidence lines (HR, log Fx/Fopt, parallax/PM, WISE colors) + which catalogs voted + provenance. Reuse-then-fallback classifier; deterministic. **Acceptance:** on a hand-labeled test set (~50 sources: bright Seyferts, coronal/flare stars, a cluster, a CV, an XRB, several LS10-exterior sources), the headline class matches the published class for **≥90%**, and **every** numeric claim in every dossier is traceable to a catalog value or a cited locus (zero fabricated numbers — automated check).
- **M2 — expansion & web surface.** FastAPI **web lookup + REST API** (position/name → JSON + HTML dossier); batch mode; the **disagreement/oddball finder** (cross-catalog conflicts, high-Fx/Fopt "stars," classifiable LS10-exterior sources); generate the full **HuggingFace dataset of dossiers** for the eRASS1-DE catalog with a **Zenodo DOI**. **Acceptance:** the public API returns a correct dossier for an arbitrary eRASS1-DE source in < ~2 s; the HF dataset is published and loads; the oddball finder yields a vetted candidate list.
- **M3 — distribution & refresh.** **MCP server** ("what is this X-ray source?"), **PyPI** package (pyvo-based) targeting astroquery-affiliated status, and an **RNAAS** on the curated oddball/disagreement sample. On **Gaia DR4 (Dec 2026)**, re-derive parallax/PM-dependent evidence and ship dossier dataset **v2**. **Acceptance:** MCP tool callable from a Claude client; package `pip`-installable; RNAAS submitted; DR4 refresh pipeline runs.

## First week / first tasks

1. **Account-free VO smoke test** — `pyvo` against HEASARC Xamin TAP (`ERASS1MAIN` cone) + VizieR TAP for HamStar/Salvato/Bulbul + CDS X-Match for a Gaia/WISE counterpart, all anonymous. Confirm no login anywhere; record which value-added catalogs are TAP-queryable vs bulk-FITS-only.
2. **Pull the DR1 value-added manifest** and write the schema map: each catalog → the common `Verdict` record (class, probability, evidence columns, provenance, version). This mapping is the bulk of the real work.
3. **Adversarial prior-art memo** — ESASky, MPE portal, GitHub, VizieR, HF; draft the email to the Salvato/HamStar teams. Decide alive/pivot/kill.
4. **Encode the rule-based fallback** — transcribe the Canis Major loci (arXiv:2407.12583) + Maccacaro log Fx/Fopt + Stern WISE wedge into a transparent, unit-tested, citation-carrying ruleset.
5. **Ten hand-built dossiers** — a Seyfert, a flare star, a cluster, a CV, an XRB, and several LS10-exterior sources end-to-end in a notebook; freeze the dossier JSON schema + plain-language template from what these need.
6. **Value-of-reconciliation experiment** (M0 kill check #3) on 100 random sources.

## Risks & kill criteria

- **"It's just repackaging published catalogs."** The sharpest critique, and partly fair. Mitigation: lead with the parts that are *not* repackaging — cross-catalog **reconciliation/disagreement** surfacing, the **rule-based coverage of the ~25% LS10-exterior remainder**, and the **accessibility/translation** value (per-source, plain-language, account-free). If reviewers still see zero added value over Salvato's class column (M0 check #3 fails), **kill or narrow to the API/MCP utility.**
- **A first party ships the unified portal.** If the eROSITA/MPE team or ESASky releases a reconciled per-source classification view with evidence, the wedge collapses — **pivot** to the developer surfaces (API, MCP, PyPI dataset) or **kill**. Monitor the DR1 portal and ESASky release notes.
- **Value-added catalogs are bulk-FITS-only, not on TAP.** Raises ingest cost; mitigated by a one-time local DuckDB/Parquet join (still account-free) — a cost risk, not a blocker.
- **Rule-based fallback is unreliable in the Galactic plane** (crowding, high N_H, Salvato's own conservative cuts there). Be honest: flag crowded/absorbed fields as **low-confidence**; never overclaim a class the evidence can't carry.
- **Scope creep into "better classification."** The moment this competes with HamStar/Salvato on label accuracy it loses — it is a *translation layer*, not a rival classifier. Kill that temptation early.

## Distribution & legitimacy

- **HuggingFace dataset** of per-source dossiers (uniform multiwavelength-evidence records) + a small classification **eval/leaderboard** against the published labels — the citable, versioned product.
- **Zenodo DOI** for the dossier dataset (and each Gaia-DR-versioned refresh).
- **RNAAS** (1-page, citable) on the newly surfaced oddballs: cross-catalog disagreements, anomalous-Fx/Fopt stars, classifiable LS10-exterior sources.
- **MCP registry** — a "what is this X-ray source?" server reaching every Claude/LLM client (a 2026 distribution surface the brief calls out).
- **PyPI** package (pyvo-based), aiming at **astroquery-affiliated** status as the canonical eRASS1 source-context lookup; **JOSS** paper if the package matures.
- **Web app** on HF Spaces for the demo/lookup UI.

## Rough size

**~1.5–2.5 weeks to M1 for an agent fleet.** The dossier renderer and the rule engine are small; the labor is (a) mapping ~15 heterogeneous value-added catalog schemas onto one `Verdict` record, and (b) getting the reconciliation logic honest. **Single biggest uncertainty:** whether cross-catalog reconciliation + the LS10-exterior rule-based coverage add enough value over simply reading Salvato's class column to justify the project (the M0 value-of-reconciliation kill check) — closely followed by whether all value-added catalogs are reachable via account-free TAP or force a local-ingest step.

---

**Sources (load-bearing facts, verified July 2026):**
- eROSITA-DE DR1 portal & access model — https://erosita.mpe.mpg.de/dr1/ ; catalogues dir `.../AllSkySurveyData_dr1/Catalogues_dr1/`
- eRASS1 first catalogues & DR1 paper (Merloni et al. 2024) — https://arxiv.org/abs/2401.17274 ; VizieR 2024yCat..36820034M ; HEASARC ERASS1MAIN https://heasarc.gsfc.nasa.gov/W3Browse/catalog/erass1main.html
- Counterparts + classification (Salvato et al. 2025; released 2026-06-09) — https://arxiv.org/abs/2509.02842 ; A&A aa56142-25
- HamStar coronal identification (Freund et al. 2024) — https://arxiv.org/abs/2401.17282 ; DR1 catalog `.../FreundS_DR1/HamStar_eRASS1_Main_Likely_Identifications_v1.1.html`
- eRASS1 cluster catalog (Kluge et al. 2024 / Bulbul et al. 2024) — https://arxiv.org/abs/2402.08452 ; VizieR 2024yCat..36850106B
- Rule-based multiwavelength classifier, Canis Major (2024) — https://arxiv.org/abs/2407.12583 ; A&A aa50637-24
- Variability catalogue (Boller et al. 2024) — https://arxiv.org/abs/2401.17280 ; eRO-ExTra — https://arxiv.org/abs/2501.04208
- HEASARC Xamin VO TAP/cone — https://heasarc.gsfc.nasa.gov/xamin/vo/tap , https://heasarc.gsfc.nasa.gov/xamin/vo/cone ; GAVO mirror https://dc.g-vo.org/rr/q/lp/custom/nasa.heasarc/erass1main
- ESASky eROSITA catalog overlays — https://www.cosmos.esa.int/web/esdc/esasky-catalogues
