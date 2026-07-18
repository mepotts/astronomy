# SETI Ellipsoid Alert Broker — SPEC

> Source of truth for pitch / landscape / MVP / kill criteria.
> Section 1 reproduces the verified research dossier
> (`idea-research/astronomy/shortlist/04-seti-ellipsoid-alert-broker.md`) verbatim.
> Section 2 is the tightened **"What we build first"** v0 scope.
> Web research (June 2026) that informed this spec lives in `DATA-SOURCES.md`.

---

## 1. Research dossier (verbatim)

### SETI Ellipsoid Alert Broker [sources: IOPscience-2025, alert_seti-github, Gaia-DR3-SETI-github, CHIME-VOEvent, arxiv-2308.00066]

**Pitch (refined):** A hardened, standalone Python service that nightly ingests the ZTF alert stream (via Lasair API), ASAS-SN transient feed, and CHIME/FRB VOEvent stream; computes each alerted object's distance against the SN 1987A SETI Ellipsoid (using Gaia DR3 parallaxes from the `astroquery.gaia` TAP endpoint); ranks crossing candidates by stellar density and Gaia astrometric quality; and exports a nightly observing list in both ACP/FITS target format and a human-readable CSV suitable for amateur follow-up with Breakthrough Listen BL-Cadence scheduling. The service would be distinct from the Fink/Lasair filter prototypes by being self-contained, installable, and public-API-first.

**Landscape (verified):** Adversarial search found three prior-art threads, none of which close the gap cleanly.

1. **Gallay et al. 2025 (IOPscience, AJ)** — "Technosignature Searches with Real-time Alert Brokers." This is the June 2025 paper the shortlist brief cited. The authors deployed 44 public Lasair filters (watchmaps) for planetary transit zones and prototyped an Ellipsoid filter querying Lasair's Gaia crossmatch. The code lives in `github.com/eleanorgallay/alert_seti`, which is 98% Jupyter notebooks, has no API, no deployment, no README, and no release. The paper itself acknowledges two structural blockers: Lasair's alert schema lacks distance metadata for the full Gaia catalog (~90% of future Rubin stars will have no useful parallax in current broker schemas), and the minimum ZTF alert amplitude threshold is unpublished, making completeness estimation impossible. This is a prototype demonstrating feasibility, not a maintained tool.

2. **Nilipour et al. 2023 (IOPscience, AJ) + `anilipour/Gaia-DR3-Time-Domain-SETI`** — The foundational Gaia DR3 Ellipsoid paper. Repo last released April 2023, archived research code, no live service.

3. **CHIME/FRB VOEvent Service** — Live, broadcasting ~2 detections/day since October 2021. Provides sky position and DM in near-real-time. No downstream Ellipsoid crossing computation service consumes this feed.

The gap is real and verified: no public, standalone, continuously-running broker that (a) fuses the three feeds above, (b) carries its own Gaia DR3 distance layer, and (c) exports amateur-facing observing lists.

**Agent-MVP (1 week):** A fleet of three specialized agents can deliver a working daily pipeline.

- **Ingest agent**: polls Lasair REST API (ZTF alerts, free tier), ASAS-SN Sky Patrol JSON feed, and CHIME/FRB VOEvent XML stream on a 24h cron. Writes normalized alert records (ra, dec, MJD, survey, mag/DM) to a SQLite staging table.
- **Ellipsoid agent**: for each new alert, queries Gaia DR3 via `astroquery.gaia` TAP to retrieve parallax and pmRA/pmDec within 5 arcsec; computes 3D distance; evaluates position against the SN 1987A ellipsoid shell (semi-major axis ~168,000 ly, expanding at c, reference epoch 1987-02-23); flags stars with crossing uncertainty window < 2 yr. Output: ranked CSV with Gaia source_id, crossing MJD window, parallax_over_error filter, stellar density bin.
- **Export agent**: converts ranked list to ACP target format (.tgt), machine-readable VOTable, and a human-readable Markdown digest emailed or posted to a GitHub Pages site nightly. Artifact: `ellipsoid_targets_YYYYMMDD.csv` + `.tgt` + digest `.md`.

Total dependencies: `astroquery`, `astropy`, `requests`, `voevent-parse`, `sqlite3`. No proprietary data access required.

**90-day arc:**

- **Weeks 1-2:** Core pipeline running locally; SQLite → daily CSV; validate against Nilipour et al. star list (32 known TESS-zone targets should appear). Fix edge cases in Lasair API pagination.
- **Weeks 3-6:** Add ASAS-SN feed; add Gaia parallax quality cuts (RUWE < 1.4, parallax_over_error > 5); build GitHub Actions cron to run nightly and publish CSV to GitHub Pages. Post to Breakthrough Listen GitHub Discussions and SETI Institute community Slack.
- **Weeks 7-10:** Add CHIME VOEvent ingest; compute DM-distance consistency check for FRB events against ellipsoid (speculative but tractable with Macquart relation); write a 3-page technical note for arXiv describing the system. Reach out to Gallay/Davenport (UW) and Steve Croft (BL Berkeley) — they are the natural community owners and collaborators.
- **Day 90:** If BL engagement materializes, transfer maintenance or co-author a short instruments note. If no engagement after posting to BL and SETI forums, reassess. Public artifact is already useful to citizen astronomers via AAVSO and the AAVSOnet scheduler.

**Risks / kill criteria:**

- **Strongest kill risk:** Lasair introduces distance-aware alert schema (they acknowledged this gap in the 2025 paper; Rubin/LSST commissioning pressure makes this likely in 2026-2027), which would obsolete the custom Gaia TAP lookup and allow the prototype filters to do the same job natively. Check Lasair changelog quarterly.
- **Scientific kill risk:** The SN 1987A ellipsoid crossing window for the densest Gaia stellar targets peaks ~2026-2028 (per Nilipour et al. Figure 4). After 2030 the interesting-star-per-year crossing rate drops sharply. The project has a natural sunset.
- **Completeness problem:** ~90% of ZTF/Rubin stars lack usable Gaia parallaxes. The broker is not a complete sky survey; it is a high-quality-parallax-star monitor. This must be stated plainly in any publication.
- **Kill condition to check before starting:** Email Gallay (first author, UW) asking if `alert_seti` is being actively developed into a public service. If yes, contribute rather than duplicate.

**Tag:** solo-side-project  ·  **Underexplored:** 4/5  ·  **Agent-buildable:** 4/5  ·  **Excitement:** 4/5

**Sources:**
- https://iopscience.iop.org/article/10.3847/1538-3881/ade4bb (Gallay et al. 2025, "Technosignature Searches with Real-time Alert Brokers")
- https://github.com/eleanorgallay/alert_seti (research prototype repo, no maintained deployment)
- https://github.com/anilipour/Gaia-DR3-Time-Domain-SETI (Nilipour et al. 2023 code, archived)
- https://arxiv.org/abs/2308.00066 (Nilipour et al. 2023 foundational paper)
- https://phys.org/news/2022-01-real-time-heralds-era-fast-radio.html (CHIME/FRB VOEvent service announcement)
- https://www.researchgate.net/publication/392766301_Technosignature_Searches_with_Real-time_Alert_Brokers (ResearchGate mirror with abstract details)

---

## 2. Dossier verification notes (web research, June 2026)

These are light-touch corrections / confirmations from fresh lookups. They do not change
the dossier's thesis; they sharpen the build.

- **`eleanorgallay/alert_seti` — CONFIRMED a prototype, not a tool.** Repo is 98.9% Jupyter
  notebooks (`PlanetTransitZones.ipynb`, `Dippers.ipynb`, `Simulated_dips.ipynb`, plus
  `possible_workflow.py` / `jrad_workflow.py`). It *does* have a README, but it is a database
  schema dump, not product docs. 1 star, 0 forks, no releases, no license, no API, no
  deployment. The dossier's "feasibility prototype, not a maintained tool" verdict stands.
- **Schema-distance blocker — CONFIRMED current as of June 2026.** Both the Lasair RASTI 2024
  paper and Gallay 2025 state plainly: (1) no broker currently carries distances for the full
  Gaia catalog usable as a ZTF/Rubin alert filter, and (2) ~90% of Rubin-stream stars are too
  faint for precise Gaia distances. No evidence Lasair has shipped a distance-aware alert
  schema yet → **strongest kill risk is still OPEN, not triggered.** Keep checking quarterly.
- **Lasair is now dual-broker.** A ZTF instance (`lasair-ztf.lsst.ac.uk`) and a Rubin/LSST
  instance (`lasair-lsst.lsst.ac.uk`) both exist. v0 targets the ZTF instance (stable, public).
- **SN 1987A distance.** Modern value d ≈ 51.4 kpc ≈ 168,000 ly (consistent with dossier).
  Ellipsoid semi-major axis A = (d + c·T)/2; the *near-side shell radius* relevant for crossings
  grows at ~c/2 in look-back terms. Reference epoch (Earth observation) 1987-02-23. Geometry
  detail in `DATA-SOURCES.md`.

---

## 3. What we build first (v0 scope)

**v0 is a single-source, offline-reproducible reactive broker.** We build one Python package
(`seti_ellipsoid_broker`) exposing a CLI that, on demand, pulls the last N days of ZTF transient
alerts from the **Lasair ZTF REST API** (free token, cone/SQL query), enriches each alert with a
**Gaia DR3** parallax + RUWE via a single batched `astroquery.gaia` TAP query, computes each
object's geocentric distance and its signed offset from the **SN 1987A SETI ellipsoid shell** at
the current epoch, applies astrometric quality cuts (RUWE < 1.4, parallax_over_error > 5), ranks
surviving objects by crossing-window proximity × local stellar-density bin, and writes one
deterministic artifact set — `ellipsoid_targets_YYYYMMDD.csv` + an ACP `.tgt` + a Markdown digest.
ASAS-SN and CHIME/FRB ingestion, the GitHub Actions nightly cron + Pages publish, and the
**Window-Predictor** forward-calendar/iCal mode are explicitly *out* of v0 and scheduled for
M2/M3 (see `BUILD-PLAN.md`). M0 (this commit) is the runnable skeleton with mocked data only.
