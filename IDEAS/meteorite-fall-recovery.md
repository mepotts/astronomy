# meteorite-fall-recovery

**One-liner:** An open, reproducible service that ingests the Global Meteor Network's public 6-hourly orbit feed, auto-flags fireballs whose kinematics indicate a likely meteorite dropper, computes the dark-flight strewn field, and emits a machine-readable alert + one-page recovery briefing/map for searchers — turning GMN's "orbit" into "where to walk."

**Scores (U/B/E):** **U=3** (the meteor/fireball subfield was never swept by run 1, but dark-flight/strewn-field is a *mature* technique with strong incumbents — the gap is open productization, not novel science), **B=4** (pure data+software, all inputs account-free, an MIT-licensed dark-flight core exists to wrap, deterministic outputs), **E=4** (a recovered fall *with an orbit* is genuinely publication-grade and rare — "we told them where to look and they found it").

**Status:** proposed

## The wedge

**What exists already (adversarial prior-art check — this field is crowded; do not overclaim):**
- **Desert Fireball Network (DFN) / Global Fireball Observatory (GFO)** — an almost fully automated pipeline that already generates WRF/dark-flight fall predictions for its triangulations; **17 recoveries across GFO, 8 in Australia**. Its dark-flight code, [`desertfireballnetwork/DFN_darkflight`](https://github.com/desertfireballnetwork/DFN_darkflight), is **open source (MIT)** — NRLMSISE-00 atmosphere + wind-profile CSV + mass/density/shape. So the physics is *already solved and freely licensed*. But it is tied to DFN's own cameras (arid Australia + GFO partners), and the end-to-end fall-alert product is internal.
- **FRIPON / Vigie-Ciel** — ~150 cameras + 25 radio receivers over W. Europe (~1.5×10⁶ km²), fully automated pipeline through orbit → dark flight → strewn field, coupled to the Vigie-Ciel citizen-recovery program (e.g. asteroid 2023 CX1 → recovered Normandy meteorites). Own network, region-bound, recovery is region-specific.
- **StrewnLAB / Strewnify** (Jim Goodall) — **the closest direct competitor**: a MATLAB program simulating full entry→landing with IGRA radiosonde winds + Monte-Carlo fragmentation → a shaded probability strewn map *"intended specifically for meteorite hunting,"* plus an **automated meteor-notification service** and public fireball news/strewn maps at strewnify.com. It already occupies the "alert hunters + give them a strewn map" niche — but it's MATLAB, single-maintainer, and driven off manual/AMS fireball reports rather than automated ingestion of GMN's open orbit feed.
- **AllSky7 + AS7 Meteorite Working Group**, **NASA All-Sky Fireball Network** (both use WMPL), **CNEOS/AMS fireball logs**, and the **IMO Meteor Alerter Network** (being stood up in 2026 to alert teams to bright fireballs that may drop meteorites). Reporting/alerting infrastructure already exists.
- **The single biggest risk — the GMN/Western team is already on this.** Public 2026 reporting says a Western University group is "re-measuring the trajectories of *every* mass-dropping fireball observed by GMN and estimating terminal masses of potential meteorite falls." The people who run GMN, hold the raw data, and maintain WMPL are already doing the dropper analysis retrospectively.

**Where the defensible gap is (thin, and stated honestly):**
- The wedge is **not physics and not novelty** — it is **open plumbing + productization + coverage**. GMN is the **widest-footprint, most-open, account-free, CC-BY, 6-hourly** meteor-orbit feed on Earth (450+ cameras, 30 countries), but its **public data product stops at orbits.** It does not emit dark-flight strewn fields or recovery briefings; that translation is left to experts, per-event.
- No **open, reproducible, pip-installable, cross-network** service exists that (a) auto-ingests GMN's public feed, (b) flags droppers with a **transparent, tunable** heuristic, (c) **wraps the already-open MIT DFN dark-flight core** + free GFS winds instead of reinventing it, and (d) publishes an **open machine-readable alert feed + web map + one-page briefing** for the *whole* GMN footprint. Incumbents are network-siloed (DFN/FRIPON), closed-output, MATLAB/single-maintainer (StrewnLAB), or retrospective research (Western).
- An agent fleet fills this cheaply because every dependency is free and deterministic: the hard science is borrowed (MIT dark-flight), the data is account-free HTTP, and the value added is *connective tissue* — exactly the portfolio thesis.

**Why now (2026 catalyst):**
- GMN crossed 450+ cameras / 30 countries and hundreds of thousands of orbits, and the public **6-hourly** `traj_summary` feed + `gmn-python-api` make account-free automation trivial *today*.
- **IMO is building its Meteor Alerter Network in 2026** — a distribution partner arriving exactly now (and a reason to move before it, or a network it, incorporates the incumbents).
- The 2025 literature reframed the problem as a **recovery** bottleneck, not a detection one (Shober et al. 2025, *"What falls versus what we recover"*), sharpening the product's value proposition.
- DFN's dark-flight code is now open (MIT) — the physics is free to wrap rather than rebuild.

## Target user & the "who cites this" test

- **Primary user:** a meteorite-recovery searcher / regional fireball coordinator (IMO/AMS reporter, Meteoritical-Society-adjacent hunter, a GMN camera operator) in the hours after a bright fireball. **The moment:** "GMN just posted an orbit for a slow, deep, massive fireball near me — *where do I actually walk tomorrow morning?*" Today that person waits for an expert or runs MATLAB; the product hands them a strewn-field map + briefing automatically.
- **Secondary user:** researchers studying meteorite–asteroid source-region links and recovery bias, who need a **versioned, machine-readable candidate catalog**.
- **What makes it citable, not just consumable:**
  - **Recovered falls with orbits are precious and rare — only 75 exist** (Jenniskens & Devillepoix 2025, *Review of asteroid, meteor, and meteorite-type links*, MAPS, [doi:10.1111/maps.14321](https://onlinelibrary.wiley.com/doi/10.1111/maps.14321)), sampling only ~15 parent bodies. *Every* additional recovery this pipeline enables is a citable data point and a candidate **RNAAS** + **Meteoritical Bulletin** entry.
  - A **versioned Zenodo-DOI'd catalog** of GMN dropper candidates + their computed strewn fields is directly citable by the recovery-bias / source-region literature (Shober 2025 [doi:10.1111/maps.70041](https://onlinelibrary.wiley.com/doi/10.1111/maps.70041); Jenniskens & Devillepoix 2025) as an open, reproducible sample of "what fell."

## Data sources & access

- **GMN trajectory/orbit data (primary, account-free, CC BY 4.0).** Directory: `https://globalmeteornetwork.org/data/traj_summary_data/` — daily (`traj_summary_latest_daily.txt`, `traj_summary_yesterday.txt`), monthly, and total files in a CSV-style text format, **updated every 6 hours**, **no account/token**. Column dictionary: `https://globalmeteornetwork.org/data/media/GMN_orbit_data_columns.pdf`. Optional convenience client: **`gmn-python-api`** ([PyPI](https://pypi.org/project/gmn-python-api/), v0.0.13 Jan 2024, Python 3.8–3.12, no auth; wraps the data directory + a REST API) — but dev-status is "Planning" and the last release is Jan 2024, so **treat the raw HTTP `traj_summary` CSV as the dependency-free path** and use the client only as a convenience.
  - **Dropper-detection columns we key on** (verified present): `peak_absmag`, `mass_kg_tau_0_7` (photometric mass at τ=0.7%), `htbeg_km`, `htend_km`, `peak_ht_km`, `vinit_km_s` (initial), `vavg_km_s`, `vgeo_km_s`, `duration_sec`, plus full orbital elements. First-pass dropper filter: **low `vinit` (asteroidal, ≲25–30 km/s), low `htend` (deep penetration, ≲35–40 km), sufficient `mass`.** *Caveat:* the summary file does **not** carry a clean terminal-velocity/deceleration column — the sharpest dropper test (terminal speed) needs per-event detailed picks or a WMPL re-solve (deferred to M2). State this limit plainly.
- **Dark-flight physics core.** [`DFN_darkflight`](https://github.com/desertfireballnetwork/DFN_darkflight) — **MIT, pure Python**, NRLMSISE-00 atmosphere + custom wind CSV + optional SRTM terrain; inputs = event file (.ECSV/.CFG/.FITS) + wind CSV + mass/density (default 3500 kg/m³)/shape (sphere/cylinder/brick). **Not pip-installable** (conda + hardcoded paths, ~12 commits, lightly maintained) → packaging it cleanly is real M1 work. NRLMSISE-00 also available via the maintained `pymsis` package.
- **Upper-atmosphere winds (hard physics dependency — winds can shift a fall by several km).** **NOAA GFS via NOMADS** (`https://nomads.ncep.noaa.gov/`), GRIB2, **account-free**, ~0.25° global, forecast + analysis — the operational choice for near-real-time. Alternative/validation: **IGRA radiosonde archive** (what StrewnLAB uses) for point profiles. Read GRIB2 with `cfgrib`/`xarray`.
- **Terrain (optional):** SRTM/Copernicus DEM for impact-elevation correction (DFN_darkflight already supports SRTM).
- **Attribution to ship:** "Meteoroid trajectories/orbits from the Global Meteor Network (Vida et al. 2021, MNRAS 506, 5046), CC BY 4.0. Dark-flight computed with a wrapper around DFN_darkflight (MIT). Winds: NOAA GFS/NOMADS. Independent tool, not affiliated with or endorsed by GMN, DFN, or FRIPON."

## Architecture sketch

Python, pure-functional over inputs → deterministic artifacts (matches the sibling `seti-ellipsoid-broker` pattern: SQLite staging + flat GeoJSON/CSV/Markdown, GitHub Actions cron, GitHub Pages).

```
   GMN traj_summary  ─┐        ┌───────────────── meteorite_fall_recovery ─────────────────┐
   (6-hourly, HTTP)   ├──────► │  INGEST → DROPPER-FLAG → DARK-FLIGHT → BRIEFING/EXPORT     │
   NOAA GFS (NOMADS) ─┘        │  scan.py    detect.py     darkflight.py    export.py       │
   NRLMSISE (pymsis)          │     │           │  (tunable    │ (MIT DFN     │ GeoJSON      │──► artifacts:
   DFN_darkflight (MIT) ─────►│     ▼           ▼   thresholds)▼  wrapper +   ▼ strewn field,  strewn.geojson
                              │  SQLite staging: candidates → strewn fields → Monte-Carlo    │  briefing.md/pdf,
                              │                                                fragmentation) │  alerts feed
                              └──────────────────────────────────────────────────────────────┘
                                         │ (GitHub Actions cron, every 6h)      │
                                         ▼                                      ▼
                                   Leaflet web map (Pages)              open alert feed (GeoJSON/JSON/RSS)
```

- **`scan.py` (ingest)** — pull the latest GMN daily/6-hourly `traj_summary`, normalize rows to a dataclass, stage in SQLite.
- **`detect.py` (dropper flag)** — transparent, tunable heuristic on `vinit` / `htend` / `mass` (+ entry angle); emits ranked candidates with a documented score. This module is the thing to get *right and open*.
- **`darkflight.py`** — for each candidate: fetch the nearest GFS profile, build the wind CSV, call the packaged DFN_darkflight core, run a Monte-Carlo over mass/density/shape/fragmentation → a strewn-field polygon + probability field.
- **`export.py`** — strewn field as **GeoJSON**, a one-page **Markdown/PDF recovery briefing** (map, coordinates, land-access notes template, orbit, mass), and an **open alert feed** (GeoJSON/JSON/RSS). Web map = static Leaflet on Pages.
- Feed layer is mockable so M0 exercises detect→darkflight→export offline.

## Milestones

- **M0 — kill checks + skeleton (cheapest disproofs first).**
  - **Prior-art emails (do first):** (1) **Denis Vida / GMN–Western** — "Are you productizing dropper detection + fall alerts as a *public, maintained* feed?" If yes → **contribute, don't rebuild.** (2) **Jim Goodall (StrewnLAB)** — "Does StrewnLAB ingest GMN's feed / is any of it open?" (3) Ask GMN whether an official dropper/fall-alert product is planned.
  - **Data smoke test:** HTTP-GET a `traj_summary` daily file, parse columns, confirm a *known* deep/slow/massive fireball scores as a dropper.
  - **Physics smoke test:** clone DFN_darkflight, run its example, **reproduce a *published* strewn field** (e.g. Murrili, Winchcombe, or 2023 CX1) from its published entry state — validates the wrapper independent of GMN.
  - **Acceptance:** `mfr scan` prints a mocked dropper row and `mfr predict` a mocked strewn field; DFN_darkflight reproduces a published strewn field within its stated error.
- **M1 — thin end-to-end slice.** Ingest one day of GMN → dropper heuristic → for the top candidate, pull GFS winds → run dark-flight → emit **one strewn-field GeoJSON + one Markdown briefing.**
  - **Acceptance:** feed the published entry state of a *recovered* instrumented fall through the pipeline and land its strewn field **within a few km of the true recovery site** (validation event chosen from a GMN- or FRIPON/DFN-recovered fall — *identifying a clean GMN-observed recovered fall is an explicit M1 dependency*).
- **M2 — continuous + open + versioned.** GitHub Actions **6-hourly cron** aligned to GMN cadence; **open alert feed** (GeoJSON/JSON/RSS) + **Leaflet web map** on Pages; **backfill the historical GMN dropper catalog**; mint a **Zenodo DOI**. Sharpen detection with per-event WMPL re-solve / terminal-mass estimate.
  - **Acceptance:** a public, auto-updating map + feed; a versioned candidate catalog with a DOI.
- **M3 — distribution + first paper.** **PyPI** release; feed into the **IMO Meteor Alerter Network**; coordinate a real recovery + draft an **RNAAS** on a recovered fall with orbit; open a channel to the Meteoritical Society Nomenclature Committee.
  - **Acceptance:** `pip install`-able package + one RNAAS drafted/submitted, or one real recovery coordinated end-to-end.

## First week / first tasks

1. **[kill-check, do FIRST]** Email Denis Vida (GMN/Western) and Jim Goodall (StrewnLAB) with the duplication questions above. This is the cheapest disproof — if GMN is shipping a public dropper-alert product, contribute instead of rebuild.
2. HTTP-GET `traj_summary_latest_daily.txt`, parse against `GMN_orbit_data_columns.pdf`, and confirm the dropper columns (`vinit_km_s`, `htend_km`, `mass_kg_tau_0_7`) are populated and that a hand-picked deep/slow fireball scores high.
3. Clone `DFN_darkflight`, stand up its conda env, run the bundled example end-to-end; confirm MIT license permits wrapping and note the packaging work needed to make it importable.
4. Reproduce **one published strewn field** (Murrili / Winchcombe / 2023 CX1) from its published entry state to validate the physics wrapper.
5. Pull a single **GFS/NOMADS** GRIB2 profile over a test lat/lon with `cfgrib`, build a DFN-format wind CSV, and confirm dark-flight output shifts sensibly with wind.
6. Draft `detect.py` thresholds and write the **first unit test** (TDD): a synthetic deep/slow/massive event flags as a dropper; a fast/high/low-mass one does not.

## Risks & kill criteria

- **Incumbent ships (strongest kill).** If the **GMN/Western** dropper work becomes a public live alert product, or **StrewnLAB** opens/automates on the GMN feed, the wedge closes → **contribute, don't rebuild.** Re-check quarterly; it's a productization bet against groups that already hold the data and expertise.
- **Dark-flight uncertainty too large to be actionable.** Strewn fields are km-to-tens-of-km and **wind-dominated**; the honest deliverable is a *probability strip*, not a pin. If the summary-only inputs yield fields too diffuse to search, the product must communicate uncertainty rather than overpromise — and may need full WMPL re-solves (heavier) to be useful.
- **Detection is coarse without terminal velocity.** The public summary lacks a clean terminal-speed/deceleration column; first-pass flags will over/under-call droppers until M2's per-event re-analysis.
- **Low base rate + human bottleneck.** Recoverable GMN droppers over populated/accessible terrain are rare (a few/year), and recovery is a land-access/boots-on-the-ground problem software can't solve — citations and recoveries accrue slowly.

## Distribution & legitimacy

- **PyPI** — `pip install meteorite-fall-recovery`, a real installable (the DFN core is MIT, so redistributable with attribution).
- **Zenodo DOI** — versioned dropper-candidate catalog + strewn-field archive; the citable artifact for the recovery-bias/source-region literature.
- **RNAAS** — 72-hour, indexed, citable note on each recovered fall with an orbit (the highest-value output; only 75 such orbits exist).
- **Meteoritical Bulletin / Meteoritical Society** — coordinate official naming of any recovery via the Nomenclature Committee.
- **IMO Meteor Alerter Network** — integrate the open feed as a partner source (arriving 2026).
- **HuggingFace dataset** (stretch) — the dropper catalog as an open ML-ready dataset; **astroquery-style client** (stretch) once the API surface stabilizes.

## Rough size

**~2–3 focused weeks to M1** for an agent fleet — most of the effort is *packaging DFN_darkflight into an importable, path-clean module* and *building the GFS/NOMADS → wind-CSV ingestion*, not the GMN read (which is a trivial HTTP GET). **Single biggest uncertainty:** whether GMN's public summary columns alone drive dropper detection *and* dark-flight accurately enough to be **actionable** (a searchable strewn field), or whether every serious candidate needs a full WMPL per-event re-solve — which would push real utility past M1 and narrow the wedge toward "nicely packaged catalog" rather than "live recovery tool."
