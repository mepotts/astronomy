# Satellite-Streak Forecaster + Impact Observatory

**One-liner:** Two linked tools — (1) a per-exposure "will a satellite cross my field tonight?" forecaster that adds honest TLE-uncertainty and session planning on top of account-free ephemeris data, and (2) a maintained, versioned, cross-survey *contamination-rate index* dashboard that quantifies how badly satellite streaks are polluting astronomical imagery over time.

**Scores (U/B/E):** U=3 (satellites/SSA is white space for *this* portfolio, but the raw capability is externally partly covered — the real gap is the uncertainty layer + a longitudinal rate index, not the propagation) · B=5 (pure data+software, account-free APIs, mature propagation libraries, no hardware) · E=4 (Rubin-era, policy-relevant, tangible observer utility plus a citable open dataset)

**Status:** proposed

## The wedge

- **What exists already (adversarial prior-art check):**
  - **IAU CPS SatHub — SatChecker** (`satchecker.cps.iau.org`, docs `satchecker.readthedocs.io`, `github.com/iausathub/satchecker`) is the direct competitor to piece (1). Its `/fov/satellite-passes/` endpoint already returns every satellite crossing a field, and it has a React web app. But verified against its own docs: it is **circular-FOV only** (`ra`, `dec`, `fov_radius` in degrees — no rectangular CCD, no alt/az input), it returns **no probability, no uncertainty, no error bars**, and it does **no night-wide planning, target-list ranking, or per-exposure risk**. It is a deterministic point-query. It is backed by CelesTrak + Space-Track and is account-free.
  - **Trailblazer** (`trailblazer.dirac.dev`, `github.com/dirac-institute/trailblazer`, DiRAC/UW, also a SatHub cornerstone) is the closest thing to piece (2). But it is a **crowdsourced upload repository** of streaked FITS images (c. 2020–present), queryable by date/site/sky-position/telescope/band, in prototype stage. It stores images and "aims to enable" quantitative studies — it does **not itself publish a maintained, cross-survey contamination-*rate* time series**.
  - **Consumer pass predictors** — Heavens-Above, N2YO, ISS-Transit-Finder, CalSky (defunct). These predict bright single-object passes / Sun-Moon transits for the naked eye or a mount; none does field-of-view exposure risk for a science camera.
  - **Published streak-rate studies** exist but are one-off snapshots, not a living index: Mróz et al. 2022 (ZTF; ApJL 924 L30, arXiv:2201.05343), Kruk et al. 2023 (HST; Nature Astronomy 7, 262, doi:10.1038/s41550-023-01903-3), Tyson et al. 2020 (Rubin mitigation; AJ 160, 226, doi:10.3847/1538-3881/abba3e) and the Rubin constellation-avoidance analysis (arXiv:2211.15908), plus the spectroscopy-contamination study (A&A 2024, arXiv:2401.09976).
- **Where the defensible gap is, and why an agent fleet can fill it cheaply:**
  - **Forecaster wedge (modest, utility-driven):** a thin value-add *layer* — not a re-implementation — that adds (a) a **calibrated probability** that a streak actually lands in-frame, with error bars derived from TLE staleness; (b) **rectangular/real-CCD FOV and alt/az** input; (c) a **session planner** ("rank my target list / find the cleanest window tonight / expected streaks per exposure"); (d) distribution as an **MCP tool** and observer-software hook. Built either on skyfield+CelesTrak locally or on SatChecker's API — ideally offered *to* SatHub, not against it.
  - **Impact-observatory wedge (stronger, citable core):** a single **maintained, versioned contamination-rate index** — fraction of exposures streaked over time, sliced by survey / constellation / twilight, with projections vs constellation size — seeded from the published studies above and later extended by systematic archive re-derivation. This is complementary to Trailblazer (which holds images but not a rate index) and is the piece policy bodies and survey papers would cite.
  - Both halves are connective-tissue work (data plumbing + geometry + a dashboard), exactly what an agent fleet builds cheaply: account-free APIs, no telescope time, no institutional data-rights wall.
- **Why now (2026 catalyst):** Rubin/LSST is in steady-state ops (~7M alerts/night) so streaks are a *live*, not projected, contamination source; a 2025 Nature analysis warns megaconstellations threaten even space-based astronomy (doi:10.1038/s41586-025-09759-5); and on **2026-07-11 CelesTrak exhausted the 5-digit catalog** (object "Saramago"), so new objects get 6-digit catalog numbers (100000+) with **no GP data in legacy TLE format** — every naive TLE pipeline is breaking right now, and OMM-native tooling is suddenly the correct path.

## Target user & the "who cites this" test

- **Primary users & the moment they reach for it:**
  - *Forecaster:* an observer (pro or advanced amateur) planning tonight's run — pointing, camera FOV, site, time window — asking "will a Starlink train ruin this exposure, and when is my cleanest slot?" The reach-for moment is proposal/queue planning and at-the-eyepiece scheduling.
  - *Impact observatory:* a survey scientist, IAU CPS / dark-sky policy analyst, journalist, or funding-committee member asking "how bad is streak contamination now, and how fast is it growing?"
- **What makes it citable, not just consumable:** the forecaster is *consumed* (utility, adoption), but the **contamination-rate index is the citation hook** — a versioned open dataset with a Zenodo DOI, an RNAAS note documenting the methodology, and a HuggingFace dataset of the rate statistics + projections. Policy submissions, survey impact sections, and press all need a single sourced number-over-time; there isn't one live today.

## Data sources & access

- **CelesTrak GP data (account-free, primary):** `https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json` (also `oneweb`, `active`, per-`CATNR`, `NAME`, `INTDES`). Formats: TLE/3LE/2LE and **OMM** as XML/KVN/JSON/CSV (CCSDS 502.0-B-3). **Usage policy:** data refresh every 2 h — do not poll more often; IPs over ~100 MB/day may be firewalled. **2026 caveat (load-bearing):** since 2026-07-11 new objects use 6-digit catalog numbers and are **not available in TLE format** — the loader must be OMM-native (JSON/CSV), not a TLE line-parser.
- **Space-Track.org (account required, secondary):** free registration; richer history, decay, and Supplemental GP. Rate-limited to **<20 requests/min** (clients target ≤19). Account-free fallback for everything we need at M1 = CelesTrak.
- **Propagation libraries:** **skyfield** (`EarthSatellite`, wraps python-`sgp4`, TEME frame, Vallado "Revisiting Spacetrack Report #3", supports OMM) — the workhorse; **python-sgp4** for low-level speed. Note: **astropy has no TLE propagation** — skyfield/sgp4 is required.
- **SatChecker API (account-free, optional backend):** `/fov/satellite-passes/` — inputs `ra`,`dec`,`fov_radius` (deg), `start_time_jd`/`mid_obs_time_jd`+`duration` (s), site by lat/lon/elev or astropy name; filters `constellation`, `illuminated_only`, `group_by`, `include_tles`; async by default. We can call this for the candidate list and add our uncertainty/planning layer, avoiding re-propagation.
- **Impact-index data:** Phase 1 = curated meta-analysis of the published rate studies (Mróz/Kruk/Tyson/Rubin/A&A — exact figures + DOIs below). Phase 2 (optional) = systematic re-derivation from public survey cutouts (ZTF via IRSA, DECam, HSC) using existing streak detectors (`acstools.satdet`, Hough/LSD, or published U-Net models, e.g. arXiv:2407.19461 / 2509.16771) — no raw re-detection needed to launch.

## Architecture sketch

- **Stack:** Python; skyfield + python-sgp4; a thin geometry core; FastAPI for the API; a small React/HTMX front end; DuckDB/SQLite for the cached ephemerides and the rate index; an MCP server wrapping the API. Minimal-runnable-first.
- **Forecaster data flow:** nightly OMM pull from CelesTrak (handle 6-digit CATNR) → local cache → skyfield propagation to topocentric alt/az + RA/Dec for the observer/time grid → **geometry test** of each satellite track against the FOV polygon (circular *or* rectangular CCD) → **Monte-Carlo over a TLE-error covariance** (staleness-driven, see caveat) yielding *P(streak intersects frame)*, expected streak count, and a timing window → **illumination test** (sunlit vs Earth shadow) for a brightness flag. Optionally source the candidate list from SatChecker instead of local propagation.
- **Planner layer:** given a target list + a night, sweep exposures and rank by streak risk; surface the lowest-risk window and expected streaks/exposure.
- **Impact observatory:** a separate pipeline + static/interactive dashboard. Phase 1 renders the curated meta-analysis as a contamination-rate time series + projection-vs-constellation-size; Phase 2 appends re-derived 2026 rates from archive cutouts. Output is a **versioned dataset** (Zenodo/HF) plus the dashboard.

## Milestones

- **M0 — kill checks (cheapest disproofs):**
  - *Prior-art disproof:* confirmed from docs that SatChecker has no uncertainty/planning and Trailblazer has no maintained rate index — but **email IAU CPS SatHub + DiRAC/Trailblazer** to confirm roadmaps and offer collaboration. Kill/pivot if either ships our exact wedge imminently.
  - *Data smoke test:* pull CelesTrak `GROUP=starlink&FORMAT=json`, parse OMM incl. a 6-digit CATNR object, propagate one Starlink with skyfield, and **reproduce a SatChecker `/fov/satellite-passes/` query within tolerance**. If we can't reproduce SatChecker's geometry, our propagation is wrong.
  - *Precision reality check:* measure predicted-vs-actual timing/position spread using fresh-vs-day-old TLEs to validate the honest error budget. Kill the "precise pointing" framing if field-level (~degree) prediction isn't even reliable to a few seconds near epoch.
  - **Acceptance:** a one-pager documenting confirmed gaps, a reproduced pass list within tolerance, and a measured error budget.
- **M1 — thin end-to-end slice:** library + CLI: site + **circular** FOV + time window → ranked crossings, each with sunlit flag, timing window, and a **calibrated P(in-frame)** with error bars from TLE staleness. **Acceptance:** for a fixed query the output cross-validates against SatChecker's satellite list (same satellites, times within tolerance) *and* emits a probability; reproducible from `pip install` + a `celestrak pull`.
- **M2 — expansion:** rectangular CCD FOV + alt/az input + **session planner** (target-list ranking, "cleanest window tonight", expected streaks/exposure); FastAPI + web app; **MCP server**. **Acceptance:** given a target list + a night, returns per-target streak-risk ranking and a recommended low-risk window; the MCP tool is callable from Claude.
- **M3 — impact observatory + distribution:** contamination-rate index v1 = curated meta-analysis (Mróz/Kruk/Tyson/Rubin/A&A) → interactive dashboard + versioned Zenodo/HF dataset; **RNAAS** methodology note; formally offer the forecaster + index to IAU CPS SatHub. **Acceptance:** public dashboard renders a sourced contamination-rate time series + projection; dataset has a Zenodo DOI; RNAAS submitted.
- **M4 (optional) — re-derivation:** extend the index with fresh 2026 rates from ZTF/IRSA/DECam cutouts via an existing streak detector. **Acceptance:** ≥1 survey's 2026 streak rate computed by us and appended, matching the published-trend order of magnitude.

## First week / first tasks

1. Build the **OMM-native CelesTrak loader** (starlink + oneweb, JSON/CSV, 6-digit CATNR safe) with a 2-hour-respecting cache.
2. Propagate with skyfield for a known site/time and **reproduce a SatChecker `/fov/satellite-passes/` query**, diffing satellite set and times.
3. Draft the **TLE-staleness error model** (position→angular/timing) from the Starlink-TLE study's power law → a `P(in-frame)` function.
4. **Contact IAU CPS SatHub + Trailblazer/DiRAC**: confirm roadmaps, propose contributing the uncertainty/planning layer and the rate index (kill-check + distribution in one move).
5. Assemble the **published-rate meta-analysis table** (Mróz 18%-twilight/5,301 streaks; Kruk 2.7%/8.9±1.1%/5.8±0.7%; Rubin >½ sky at 48k sats / mag-7 floor) with exact figures + DOIs — the dashboard seed.
6. Write the **cross-validation acceptance test** (our propagation vs SatChecker).

## Risks & kill criteria

- **Forecaster wedge is thin:** the core capability already ships in SatChecker. If SatHub adds uncertainty + planning, our forecaster wedge collapses — mitigated by building it *as a contribution/layer* and by leaning on the index as the citable core. **Kill the forecaster half** if it can't reach adoption or add value over SatChecker.
- **Honest precision ceiling (the load-bearing caveat):** TLE+SGP4 gives ~3 km position error at epoch and tens of km over 2–3 days; the Starlink-specific study (arXiv:2605.19850, 2026) finds pooled median error growing from ~1 km at 6 h to ~38 km at 7 d, with a high-fidelity propagator **not beating SGP4** on public TLEs (SGP4 wins ~65–75% of pairs). Translating ~1–3 km at ~550–1500 km slant range: **~0.05–0.3° angular and sub-second timing near epoch, ballooning to degrees / many seconds with day-old or maneuvering-Starlink TLEs.** So the tool can honestly say "a satellite will likely cross your ~1° field within a few-second window" but **cannot promise an arcsecond target hit at a sub-second time**. Kill the tool's value prop only if users require arcsec/sub-second guarantees — they can't be met and we won't claim them.
- **Dashboard wedge overlap:** if Trailblazer/SatHub ships a maintained rate index first, the dashboard wedge collapses — mitigated by collaborating and seeding with a meta-analysis they don't currently publish.
- **Data operational risk:** over-polling triggers CelesTrak's firewall (respect the 2 h cadence); the 6-digit/OMM migration breaks naive TLE parsers (we treat this as a feature — OMM-native from day one).
- **Scope creep:** M4 re-derivation is real image-processing effort; if it balloons, stop at the M3 meta-analysis index (still citable).

## Distribution & legitimacy

- **PyPI** — the forecaster library (propagation + uncertainty + planning), OMM-native.
- **MCP registry** — "will a satellite cross my field" as an LLM-callable tool (2026 distribution surface reaching every Claude/LLM client).
- **RNAAS** — a 1-page citable note on the contamination-rate index methodology + headline trend.
- **Zenodo DOI** — the versioned contamination-rate dataset.
- **HuggingFace dataset** — streak-rate statistics + projections vs constellation size.
- **IAU CPS SatHub contribution** — offer the forecaster's uncertainty/planning layer and the Trailblazer-complementary index into the CPS toolset (arXiv:2408.16026 shows the collaboration surface); this doubles as the strongest legitimacy signal.
- *(JOSS later if the library matures; not astroquery — this is not a new archive, though the index can expose a simple REST.)*

## Rough size

- **Effort to M1:** small — skyfield + CelesTrak OMM loader + FOV geometry + a probability + a SatChecker cross-validation test is roughly 1–2 weeks of agent time; the fiddly parts are the calibrated staleness error model and the cross-validation tolerance. The M3 meta-analysis dashboard is quick; the optional M4 re-derivation is the main effort sink.
- **Single biggest uncertainty:** not technical feasibility but **whether the uncertainty + planning + MCP wedge is differentiated enough to matter given SatChecker already exists** — i.e., adoption/novelty risk. The citable contamination-rate index is the hedge: it stands on its own even if the forecaster is judged a wrapper.
