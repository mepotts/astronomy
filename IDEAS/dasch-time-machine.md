# DASCH Century Time-Machine

**One-liner:** A service that, given any sky position or any live Rubin/ZTF broker alert, returns the century-baseline historical view — a cleaned ~1885–1990 DASCH light curve, a plain-language variability verdict, and plate cutouts — so a transient's "was this doing anything a hundred years ago?" question gets answered automatically at alert time.

**Scores (U/B/E):** U 5 (historical/archival astronomy was untouched by run 1; nobody bridges the century baseline to the live alert stream) · B 4 (pure public data + software, but DASCH plate-photometry cleaning is genuinely fiddly, which caps it below 5) · E 4 (a "century time machine" wired to real-time alerts is evocative and citable; it is an enrichment layer, not a standalone discovery engine)

**Status:** M0 closed to a decision 2026-09-05: stop unconditional faint-field/broker annotation; targeted light curves and known-event images work; only a separately selected, externally vetted bright-star false-positive study is supported next

**2026-09-05 closeout.** [Full results and images](../dasch-pilot/M0-EXTENSION-RESULTS-2026-09-05.md):
R Cnc yields 1,459 clean detections over 99.11 years, while faint/crowded V404 Cyg
has only five and correctly returns `INSUFFICIENT_COVERAGE`. Nine cutouts were
inspected. A shallow nearest-date event selection failed; an explicitly
exploratory same-series/depth-matched triplet qualitatively recovered V404's
published 1938 event and adjacent non-detections. No unknown source was ranked.
The known Mira is `class=0, v_flag=0` in APASS, proving these flags alone cannot
define stable controls. Before any product build, use independent stability
labels, calibration/untouched validation fields, and measured review costs.
The broad novelty/competition claims below are historical hypotheses, not
established findings; public non-interactive access is existing infrastructure.

**2026-09-02 execution update.** The account-free pilot in
[`../dasch-pilot/`](../dasch-pilot/) reproduced the published T CrB 1938--1945
high state after the current documented five-AFLAG mask and a 15-arcsec
astrometric cut. The 1.103-mag target brightening remained 1.089 mag relative
to a frozen nearby field control. This validates targeted scripted light-curve retrieval,
not the original three-position M0, plate-cutout recovery, or a blind alert annotator. It also corrects an assumption below: current
daschlab documentation explicitly supports non-interactive use, so "no batch
mode" is not a defensible novelty claim. The open wedge is now the validated
multi-control cleaning/systematics methodology and alert integration.

## The wedge

**What exists already (adversarial prior-art check):**
- **`daschlab` (the biggest prior-art risk).** The official DASCH analysis package (`pkgw/daschlab`, MIT, **v1.0.0 released 2024-12-30**, pip + conda-forge). It already retrieves century light curves and plate cutouts account-free via `open_session()` / `Session.lightcurve()`, and its `Lightcurve` subclasses `astropy.timeseries.TimeSeries`. **Be honest: re-hosting DASCH light curves is a solved problem.** It is designed primarily for interactive analysis but its current documentation explicitly supports non-interactive use. It does not provide broker-stream ingestion, a calibrated multi-control verdict engine, or a plain-language alert annotation. Those narrower pieces, not generic batch access, are the remaining seam.
- **DASCH web APIs + Starglass.** DR7 (released **2024-12-29**) is cloud-served through Starglass REST endpoints (`querycat`/`queryexps`/`lightcurve`/`cutout`). These are primitives, not a translation layer.
- **Manual DASCH×modern-survey cross-matches happen constantly in the literature** — the science value is *proven*, not speculative. Canonical example: DASCH B-band revealed a **1938 optical bright state in T CrB lasting ~7 yr**, giving context for its 1946 recurrent-nova eruption (Luna et al. 2020, arXiv:2009.11902). Researchers routinely bolt a century of Harvard plates onto ZTF light curves by hand.
- **Brokers already do catalog cross-matching** (Fink and Lasair annotate alerts with SIMBAD, Gaia, ALeRCE/Fink classifiers; Fink has TDE/anomaly/SSO science modules). **None annotates alerts with DASCH century history.** Verified: no DASCH science module on Fink, no DASCH watchlist/annotation on Lasair, and **no `astroquery.dasch` module** — daschlab is standalone and not astroquery-affiliated.

**Where the defensible gap is:** the automated *bridge* — take a broker alert (or a batch of positions), pull the DASCH century record, clean it with the documented rejection paradigm, and emit a machine-readable verdict + human-readable one-liner + cutout thumbnails, at scale and at alert time. The two ends of the century baseline are, as of 2026, *both* programmatically accessible for the first time — but nobody has connected them. An agent fleet can build this cheaply because daschlab already does the hard data-plumbing (cloud auth, calibration files, cutout assembly); the net-new work is the **cleaning-calibration recipe, the verdict logic, the Fink/Lasair wiring, and the summarizer** — all data+software, no telescope, no hardware.

**Why now (2026 catalyst):** DR7 (2024-12-29) is the *first* release where the entire archive is uniformly scanned (429,274 plates) and reduced, and cloud-served behind a stable API — before DR7, coverage was patchy and access was the now-dead `dasch.rc.fas.harvard.edu` site. Simultaneously, Rubin/LSST is in steady-state ops (July 2026) firing ~7M alerts/night to tokenless brokers (Fink, ALeRCE, ANTARES). The century-old end and the tonight end of the same light curve became API-accessible at essentially the same moment.

## Target user & the "who cites this" test

**Primary user:** a transient astronomer or variable-star researcher triaging a new alert — the specific moment is *"I have a fresh ZTF/Rubin candidate at (RA, Dec); before I spend a follow-up night on it, did Harvard's plates already see this thing erupt, fade, or vary sometime in the last century?"* Secondary users: nova/CV and R CrB / long-period-variable hunters doing recurrence and precursor searches, and the DASCH/citizen community who want a "was this star interesting 90 years ago?" lookup without learning the daschlab reduction ritual.

**What makes it citable, not just consumable:**
- A **versioned, DOI'd derived catalog** of century-baseline variability verdicts for a defined alert sample (Zenodo) — the kind of value-added product other papers cite when they justify follow-up.
- An **RNAAS** on a genuine century-baseline find surfaced by the pipeline (e.g. a recurrent-nova precursor bright state, a secular dimmer, a decades-long state change invisible to any modern survey) — a 1-page citable unit.
- A **Fink science module / Lasair annotation** carries a maintainer credit and is referenced by every downstream user of those alerts.
- The plain-language verdicts are quotable provenance ("DASCH: 41 plate detections 1890–1989; historical bright state B≈12.1 ± 0.3 c. 1932; classified ERUPTIVE") that ends up pasted into ATels, TNS comments, and proposals.

## Data sources & access

Account-free path is fully viable: daschlab and the Starglass **public** API need no key; Fink's REST API needs no token. Only higher DASCH rate limits and Lasair need credentials.

| Source | What | Endpoint / entry point | Auth | Notes / limits |
|---|---|---|---|---|
| DASCH DR7 (daschlab) | Century light curves + plate cutouts | `from daschlab import open_session` (pip/conda-forge, v1.0.0) | **None** | Recommended path; MIT. `select_target()` accepts name or coords; `select_refcat("apass")`; `lightcurve()` → astropy TimeSeries |
| DASCH DR7 web API (public) | Same data, REST | `https://api.starglass.cfa.harvard.edu/public/dasch/dr7/{querycat,queryexps,lightcurve,cutout,mosaic_package}` (POST) | **None** | Lower rate limits; JSON list-of-CSV-record-strings, first record = camelCase column names |
| DASCH DR7 web API (full) | Higher limits | `https://api.starglass.cfa.harvard.edu/full/...` | Starglass API key (40-char, `x-api-key` header) | Free account; use for batch |
| Starglass portal | Browser UI (non-scientists too) | `https://starglass.cfa.harvard.edu/` | None (basic) | Human-facing; not the machine path |
| Fink | ZTF (and Rubin) alert → RA/Dec, class, LC | `https://api.fink-portal.org/api/v1/objects` (POST) | **None (tokenless)** | Account-free alert resolver for the recipe |
| Lasair ZTF | Alerts + watchlists/annotations | `https://lasair-ztf.lsst.ac.uk/api/` | Token (100 calls/hr free) | Annotation-push target (M3); see seti-ellipsoid-broker DATA-SOURCES.md |

**DASCH scale / provenance (load-bearing, cite before relying):** DR7 = **~23.57 billion** magnitude measurements of **~252 million** sources, years **~1880–1990**, depth ~B 14–16; ~200 TB plate images + ~16 TB calibrated light curves; photometry referenced to **APASS DR8** (primary) / **ATLAS-refcat2** (secondary). Most stars brighter than B≈15 have hundreds–thousands of detections (arXiv:2501.12977; dasch.cfa.harvard.edu/dr7).

**Key query flow:** `querycat` (refcat=`apass`|`atlas`, `ra_deg`, `dec_deg`, `radius_arcsec` ≤ 3600) → source `ref_number` + `gsc_bin_index` → `lightcurve` for that source → optionally `cutout` (`plate_id`, `solution_number`, center coords) for thumbnails.

**Photometry caveats — this is the whole ballgame, not a footnote.** Plate photometry is noisy and the reduction is a **rejection paradigm**, not a clean catalog read:
- Use `magcal_magdep` for magnitude, `magcal_local_rms` for its uncertainty, `limiting_mag_local` for non-detections (upper limits).
- Reject bad points via AFLAGS bits — **bit 7 HIGH_BACKGROUND, 12 LARGE_ISO_RMS, 13 LARGE_LOCAL_SMOOTH_RMS, 14 CLOSE_TO_LIMITING, 16 BIN_DRAD_UNKNOWN** — plus `lc.apply_standard_rejections()` (still under development), `lc.reject.sep_above()` (astrometric outliers), `lc.reject.meteor()` (low-res trailed/meteor-series plates).
- **False-variability sources to defend against:** undetected plate defects (dust/scratches), undetected **blends** on low-resolution plates (systematically over-brighten, and because plates cluster in time this fakes epoch-correlated trends), non-blue emulsion color terms, mis-identified astrometry across epochs, and database-compilation gaps.
- **Timestamps come from hand-transcribed observing logbooks — accuracy minutes at best.** Do not make intra-night timing claims.
- **Documentation is honestly incomplete:** several flag columns are marked "FIXME: not yet documented" and users are pointed at the legacy guide + email list. Budget real time to nail down the quality cuts empirically.
- **Dead endpoint:** the old `dasch.rc.fas.harvard.edu/lightcurve.php` interface no longer serves data — ignore any snippet or paper pointing there.

## Architecture sketch

Minimal-runnable-first, single Python package `dasch_timemachine`, thin verdict engine on top of daschlab. No standing infra for v0.

- **Resolver** — input is a position `(ra, dec)` *or* a broker id (ZTF `objectId` via Fink `/api/v1/objects`, tokenless → RA/Dec/class). Normalizes to ICRS coords + optional modern light curve for the join.
- **DASCH fetch** — `daschlab.open_session()` in a temp workdir → `select_target(coords)` → `select_refcat("apass")` → `querycat` cone → pick the source (handle split/blended sources) → `lightcurve()`. Public Starglass API as a no-daschlab fallback and for batch.
- **Cleaner** — applies the fixed rejection recipe (AFLAGS 7/12/13/14/16, meteor, sep-above, limiting-mag handling). Emits a cleaned detections+upper-limits table with per-point provenance. This module is the crown jewels and the main test target.
- **Verdict engine** — computes baseline statistics (span, N detections, N plates, median/scatter vs APASS reference mag, max historical excursion, presence of sustained bright/faint states) → categorical verdict `{QUIESCENT, VARIABLE, ERUPTIVE, FADING, INSUFFICIENT_COVERAGE}` + a confidence gated on coverage/quality. Conservative by design: thin/crowded coverage → `INSUFFICIENT_COVERAGE`, never a false "quiet."
- **Renderer** — century light-curve PNG (detections + upper limits, modern survey overlaid when present), a few plate `cutout` thumbnails, and a one-line natural-language summary from a template (LLM optional, not required).
- **Outputs** — JSON verdict record + PNG(s) for M1; a REST endpoint and batch-over-a-nightly-alert-file for M2; a Fink module / Lasair annotation for M3.

Data flow: `alert/position → resolver → DASCH fetch → cleaner → verdict → {JSON, PNG, one-liner}`.

## Milestones

- **M0 — kill checks (cheapest disproofs).**
  - *Data-access smoke test:* from a laptop, account-free, pull and clean a century light curve for a known variable (T CrB, plus a Mira and a faint Galactic-plane target). **Acceptance:** cleaned DASCH LC retrieved with no credentials for ≥3 positions, including one faint/crowded field.
  - *Prior-art disproof:* confirm that Fink/Lasair and daschlab do not already provide a maintained broker-to-DASCH annotation/verdict layer. Generic scripted or batch DASCH access is existing infrastructure, not the wedge. **Acceptance:** the public documentation and code leave the alert-annotation seam open; any roadmap emails are a separate, explicitly approved outward action.
  - *Reliability reality check:* reproduce a published century-baseline result (T CrB 1938 bright state) from cleaned DASCH data. **Acceptance:** the pipeline recovers the known feature; if cleaned photometry can't reproduce a documented result, the automated-verdict thesis is in doubt.

  **Execution status (2026-09-05):** all scientific control/retrieval checks were
  attempted and recorded. The unconditional three-position coverage gate failed
  on V404 Cyg; targeted retrieval and exploratory known-event images succeeded.
  M0 is closed with the narrower decision above, not an unconditional pass.
  External roadmap emails and TNS account actions were not performed. A new
  product investment requires a specific fresh prior-art comparison; no absence
  of competing software is established by this feasibility run.
- **M1 — thin end-to-end slice.** `dasch-timemachine <ZTF objectId | ra dec>` → cleaned century LC PNG + JSON verdict + one cutout, quality cuts applied, deterministic. **Acceptance:** for a known recurrent nova resolved through Fink, the tool emits an `ERUPTIVE`/`VARIABLE` verdict with the historical excursion quantified, reproducibly from a cold checkout.
- **M2 — batch + service + summarizer.** REST endpoint and a "score a night's alert file" batch mode; plain-language summaries ("sustained bright state B≈12, ~1932–1939"); coverage/quality gating tuned so faint fields degrade gracefully. **Acceptance:** annotate a full night of ZTF alerts and correctly surface the subset with real historical variability against a hand-labeled validation set (precision-first).
- **M3 — distribution.** A Fink science module *or* Lasair annotation pushing DASCH flags onto live alerts; a versioned Zenodo verdict catalog; an MCP server exposing the time-machine as a tool; one RNAAS on a genuine find. **Acceptance:** a deployed broker annotation reaching downstream users, and one RNAAS submitted.

## First week / first tasks

1. Completed via the official public API equivalent on T CrB, R Cnc, and V404 Cyg. The old RY Cnc suggestion is not a Mira and was corrected before data retrieval.
2. Codify the cleaning recipe (AFLAGS 7/12/13/14/16, `reject.meteor`, `reject.sep_above`, limiting-mag handling) as a single `clean_lightcurve()` function with fixtures; **benchmark it against the T CrB 1938 bright state** to calibrate the cuts.
3. Wire Fink `/api/v1/objects` (tokenless): ZTF `objectId` → RA/Dec → DASCH fetch, end to end.
4. Draft the verdict schema + coverage/quality gating (`QUIESCENT|VARIABLE|ERUPTIVE|FADING|INSUFFICIENT_COVERAGE` + confidence); write it precision-first so thin coverage never reads as "quiet."
5. Send the adversarial prior-art emails (pkgw / Fink / Lasair) and file their answers in the plan.
6. Ship the M1 CLI producing a PNG + JSON for one recurrent nova; capture it as the acceptance test.

## Risks & kill criteria

- **daschlab/Starglass ships its own alert-integration or batch/annotation service** → wedge closes. Mitigation: confirm roadmap in M0 (email pkgw); if planned, contribute upstream rather than duplicate. This is the analogue of the seti-broker's "Lasair ships distance-aware schema" risk.
- **DASCH photometry is too noisy at the faint, crowded, Galactic-plane positions where most transients live** to yield trustworthy automated verdicts → the annotation becomes misleading, which is worse than absent. This is the real scientific kill risk. Mitigation: hard, conservative `INSUFFICIENT_COVERAGE` gating and precision-first tuning; if we can't hit acceptable false-positive rates on a labeled set, the product is an interactive assistant, not an auto-annotator.
- **Per-alert DASCH calls don't scale to Rubin's ~7M alerts/night** (cloud rate limits; bulk access requires emailing the DASCH list). Mitigation: pre-filter to alerts where a century baseline plausibly helps (bright/nearby/Galactic/known-host), not the full stream; cache by HEALPix cell.
- **Timestamp and systematics caveats undercut precise "flared in 1932" language.** Mitigation: keep verdict wording calibrated to plate-time accuracy and coverage; report ranges, not dates.
- **Kill condition to check before building:** if M0 shows a maintained broker DASCH module already exists, or cleaned DASCH photometry can't reproduce a published century-baseline result, stop or narrow to the interactive-tool framing.

## Distribution & legitimacy

- **PyPI** — `dasch-timemachine` (thin client + cleaner + verdict engine on top of daschlab).
- **Fink science module** or **Lasair filter/annotation** — the real broker surfaces that put DASCH flags in front of alert users; the primary distribution play.
- **MCP server** — expose "century time machine at this position/alert" as a tool; reaches every Claude/LLM-client user, matching the brief's MCP-as-distribution thesis.
- **RNAAS** — a 1-page citable note on a real century-baseline find surfaced by the pipeline.
- **Zenodo DOI** — versioned verdict catalog for a defined alert sample.
- **astroquery affiliation** — no `astroquery.dasch` exists today; an astroquery-style thin accessor (or contributing one) is a genuine, uncontested opening.

## Rough size

**~1.5–2.5 weeks to M1** for one builder or a small agent fleet: daschlab removes the heavy data-plumbing, so the effort concentrates in the cleaning-calibration recipe, the Fink wiring, and the verdict logic. **Single biggest uncertainty:** whether *cleaned* DASCH photometry is reliable enough at the faint, crowded positions where transients actually live to support trustworthy *automated* verdicts — the systematics, not the plumbing, decide whether this is an auto-annotator or merely an interactive assistant.

---

### Sources (verified July 2026)

- DASCH DR7 overview / data products / access — https://dasch.cfa.harvard.edu/dr7/ , https://dasch.cfa.harvard.edu/dr7/data-products/
- DASCH DR7 web API reference (Starglass public/full base URLs, endpoints, payloads) — https://dasch.cfa.harvard.edu/dr7/web-apis/
- Light-curve columns (magcal_magdep, flags, timestamp caveat) — https://dasch.cfa.harvard.edu/dr7/lightcurve-columns/
- Light-curve reduction / rejection paradigm (AFLAGS bits, meteor/sep rejects, false-variability list) — https://dasch.cfa.harvard.edu/dr7/reduce-lightcurve/
- daschlab package (MIT, v1.0.0 2024-12-30, pip/conda) — https://github.com/pkgw/daschlab , https://daschlab.readthedocs.io/
- DASCH DR7 paper (23.57B mags, 252M sources, ~200TB/16TB, ~1880–1990) — https://arxiv.org/abs/2501.12977
- DASCH scanning complete (2024) — https://aas.org/posts/news/2024/03/harvards-dasch-scanning-project-now-complete
- T CrB century-baseline example (1938 bright state, 1946 nova) — https://arxiv.org/abs/2009.11902 (Luna et al. 2020)
- Fink public REST API (tokenless) — https://api.fink-portal.org/api/v1/objects , https://fink-broker.readthedocs.io/
- Lasair (broker annotations) — https://lasair.readthedocs.io/ (and seti-ellipsoid-broker/DATA-SOURCES.md for the ZTF token flow)
