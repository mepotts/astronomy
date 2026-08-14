# Run 3 — the publishable-science axis

Where [`../IDEAS/`](../IDEAS/README.md) catalogs **things to build** and the rest of this folder catalogs
**routes to an official designation**, this document maps the third axis: **publishable science results
from public data** — new planets in archival RVs, new compact objects in catalog cross-matches, new
statistics on brand-new public datasets. The credit here is a paper, not an MPEC line.

Researched **2026-08-14** by a 5-agent verification fan-out (optical/time-domain, Gaia/astrometry,
radio/multimessenger, spectroscopy archives, solar system; ~390k subagent tokens, ~190 tool calls).
Every load-bearing claim was checked against a primary source that week; archive queries marked
**[measured]** were run live (ESO TAP, ITF download). Facts decay — re-verify anything older than a few
months before acting. A formatted version lives at
[claude.ai/code/artifact/e773c4e4-3225-4985-995e-7e011fbf6b4b](https://claude.ai/code/artifact/e773c4e4-3225-4985-995e-7e011fbf6b4b).

---

## The lens this run adds: agent labor is cheap for us

The operating assumption for this portfolio is that **AI agents do the work** — pipeline construction,
archival reduction, cross-matching, injection-recovery, reproduction, watching. That shifts the
economics of every avenue below relative to a typical outsider:

**Where agent labor compounds** (weight these up):
- **Archival pipelines and reruns** — the exosat-rv model: agents rebuilt a Nature result from raw
  public spectra over ~29 milestones. Every avenue whose bottleneck is "someone has to process the
  pile" (CRIRES+ epochs, MWA/ASKAP imaging, SPHEREx forced photometry, DASCH controls) is
  effectively discounted for us.
- **Cross-match sweeps** — joins are embarrassingly parallel and verification-heavy; agents excel at
  both. The matrix below is the shopping list.
- **False-positive triage at scale** — the house specialty (M9's control catching a fake win, the
  blending sweep, the 82-run defect closure). Post-DR4, *vetting* is the community bottleneck, and
  it is pure agent work.
- **Standing watchers** — agents can hold minute-cadence or daily watches indefinitely (see the
  watchers table). Humans doing this burn out; pipelines doing it without judgment miss things.

**Where the advantage stops** (respect these gates):
- **Human-gated submission is house law** — nothing goes to the MPC, TNS, Sungrazer, VSX, ExoFOP, or
  a journal without Matthew's explicit per-item approval. Agents prepare; a human submits.
- **AI-hostile or AI-throttled venues** — AAVSO publicly warned about AI-assisted VSX submissions
  (2026-07-27, see [README](README.md#7-variable-stars--read-this-before-investing)); its 5/week cap
  and one-person moderation don't scale with our labor. TNS/MPC, by contrast, are *built* for
  pipelines (~80% of TNS reports are automated; MPC processes 500–1,000 identification submissions
  a day) — automation there is the norm, not a red flag.
- **Referee wars and reputation games** — the exomoon-candidate knife-fight, first-discovery claims
  against incumbent groups. Agent labor doesn't buy standing; rigor and modest claims do (the
  RNAAS/collaborate-first route from the [README](README.md#publication-and-credit) applies).
- **Anything needing a telescope or a spectrum** — unchanged; hand off, as with PN confirmation.

Net: the ranking below already bakes this in. Tier 1–2 are almost entirely agent-compounding;
the human's job is target selection, judgment calls at gates, and submission.

---

## The clock

Q4 2026 is a release pileup with no precedent in this portfolio's lifetime. **eROSITA-DE DR2 landed
2026-07-31 essentially unmined. Euclid's first big world-public drop is November. Gaia DR4 — the
largest catalog event of the decade, with no proprietary head start for anyone — is 2 December.**
August–November is for building and validating against pre-release data; December is for running.

| Date | Event | Access |
|---|---|---|
| rolling now | Rubin alerts via 7 brokers (world-public since 2026-02-24); Rubin solar-system astrometry → MPC immediately (X05); [SPHEREx QR2](https://irsa.ipac.caltech.edu/Missions/spherex.html) weekly; ESO 1-yr expirations monthly; MWA 18-mo / MeerKAT 12-mo / FAST 12-mo embargo exits; Einstein Probe survey data exiting its first proprietary year | open |
| already out 2026 | [eROSITA-DE DR2](https://erosita.mpe.mpg.de/dr2/) (Jul 31, ~2M sources) · [LoTSS DR3](https://lofar-surveys.org/dr3.html) (Feb) · [GWTC-5.0](https://www.ligo.caltech.edu/news/ligo20260526) (May, 390 events) · IceTracks-DR2 (May) · CHIME/FRB Catalog 2 (4,539 bursts) · ZTF DR24 · MPTA 4.5-yr · [Gaia DR4 pre-release samples + official fitting package](https://www.cosmos.esa.int/web/gaia/dr4) (~Jun) · final Legacy Surveys map (Aug) | open |
| **2026-10-01** | β Pic CRIRES+ K-band 360-exposure series exits ESO proprietary **[measured]** (per-file release date) | open |
| **2026-11** | [Euclid DR1-Foundation](https://www.cosmos.esa.int/web/euclid/dr1-timeline) — ~1,900 deg² images/catalogs/spectra, world-public | open |
| **2026-12-02** | [**Gaia DR4**](https://www.cosmos.esa.int/web/gaia/release) — epoch astrometry/photometry/spectra for ~2B sources, expanded NSS catalog, first Gaia exoplanet list, 436k SSOs | open |
| 2026-12 | **ZTF primary operations end** (DR25 follows 2027-01-20) — last chance to tune live-alert filters before the niche migrates to Rubin/LS4 streams | closing |
| 2026-12→2027-03 | JWST Cycle-4 exoplanet programs exit exclusive access en masse via MAST | open |
| 2027 | IPTA DR3 (116 pulsars, no firm date) · LVK O4c catalog+strain · DESI DR2 spectra (TBA) · Euclid DR1 complete (~mid-2027) · β Pic CRIRES+ L/M 1,266-exposure campaign (Apr 7) **[measured]** | open |
| late 2027 | LVK O5 begins · (PLATO launched Mar 2027, first LCs ~2028) | open |
| ~2028-06 | Rubin DR1 (full year 1 — the 6-month DR1 was [cancelled](https://community.lsst.org/t/rubin-observatory-plans-for-early-science-v7-0-released/11252/4)) · eROSITA-DE DR3 (H2 2028) · SPHEREx legacy catalogs | rights-gated / late |

---

## The fourteen, ranked

Ordered by expected discovery-per-effort **for this portfolio under the agent-leverage lens**. Tier 1
reuses validated pipelines on fresh public data; Tier 2 is new datasets with strong method fit;
Tier 3 is new domains worth a scoped pilot.

### Tier 1 — validated pipelines, fresh data

**1. New public CRIRES+ epochs on the exosat-rv roster** · *extends exosat-rv · competition: no known
outside pipeline · live now + Oct 1*
Live ESO TAP queries **[measured]** found time-series that exited proprietary *after* the roster
closed: a **300-exposure block on CD-35 2722** (Oct 2024, public since 2025-10-19 — logged "K,LM",
verify per-file settings; if K-band, an out-of-sample epoch test for the 171-d satellite signal), **90
exposures on HIP 65426 B** (public 2026-05-04, extends the M20 limit), and the dated **β Pic K-band
drop on Oct 1**. Also now public: LkCa 15 (170 exp), UX Tau A (136), HD 1160 (101), WASP-39 K-band
transit series (173), TWA 5 (400, L/M). Unclaimed niche: an
[archive paper of reduced CRIRES+ L/M spectra](https://arxiv.org/abs/2604.24466) appeared April 2026 —
the **K/H-band equivalent has no such paper** and we own the only validated outside pipeline. NIRPS
twist **[verified]**: public NIRPS RV products are deliberately scrambled ±100 m/s for 2 years, but
**raw frames follow the normal 1-year rule** — a moat that only blocks people without their own
extraction pipeline. *First step:* rerun the M20 recipe on the HIP 65426 B block; pull CD-35 2722 and
check settings against H1567/K2166.

**2. Independent analyses of public PTA data — MPTA first, IPTA DR3 next** · *extends the pta
pipeline · competition: thin outside collaborations · live now → 2027*
All four flagship datasets are public: [NANOGrav 15-yr](https://zenodo.org/records/7967585) (with
noise chains), EPTA DR2, PPTA DR3, and the [MeerKAT MPTA 4.5-yr release](https://mpta-gw.github.io/)
— **83 MSPs, the most sensitive PTA, barely exploited outside the collaboration**. Open lanes:
CW/single-source searches on MPTA, cross-PTA noise-model criticism (chromatic/solar-wind
misspecification is the live methodological fight —
[NG15 chromatic noise](https://arxiv.org/pdf/2606.28571)), new-physics constraints on the public NG15
free-spectrum chains. IPTA DR3 (~2027) is the payoff event a working independent pipeline should be
waiting for. *First step:* reproduce MPTA's common-signal posterior, then the first independent CW
sky map on it.

**3. ITF linking in the Rubin era — attribution against the bulk batches** · *extends itf-linker ·
competition: ~5 named individuals at scale · live now; window to ~DR1 2028*
ITF at 9,308,366 observations **[measured 2026-08-14]**. Rubin does **not** dump orphans into it —
two-detection tracklets are withheld by design
([Heinze, Feb 2026](https://community.lsst.org/t/method-of-report-to-minor-planet-center-by-rubin/11548));
instead HelioLinc3D **bulk designation batches** (~20k candidates Feb 5; 11k+ new asteroids Apr 2)
create thousands of fresh orbits to attribute old ITF tracklets against — ITF-to-DES territory the
validated gate can attack now. MPC accepted **58,116 ITF-ITF + 49,986 ITF-DES linkages in 2025**
([docs](https://www.minorplanetcenter.net/mpcops/documentation/identifications/)) — outsider
throughput is welcomed. Durable niches: **TNO-rate gating** (everyone tunes for main-belt rates; MPC
hand-processes TNO linkages) and **Dec > +30°**, which Rubin barely covers. Bolt-ons: SARC
verification (now a formal QC process, Dec 2025 MPC newsletter) + the
[ADAM precovery API](https://b612foundation.org/asteroid-institute-precovery-api-announced/); a NEOCP
high-eccentricity watcher so the 4I precovery race (TESS/ZTF shift-stack, proven fast-ApJL on
3I/ATLAS — [arXiv:2507.21967](https://arxiv.org/abs/2507.21967)) starts the hour a candidate posts.
*First step:* diff today's ITF against the last pull; attribution runs against the Feb–Apr Rubin
batches.

**4. Gaia DR4 day-one hunts — build the vetting now** · *extends adql-copilot + house statistics ·
competition: elite but out-throughput'd · prep Aug–Nov → Dec 2*
Beyond the [diff-auditor tool](../IDEAS/gaia-dr4-diff-auditor.md), DR4 is a **discovery dataset**:
epoch astrometry for everything, expanded NSS, ~1,900±540 predicted astrometric planets
([arXiv:2511.04673](https://arxiv.org/abs/2511.04673)). The community bottleneck is exactly the house
specialty — false-positive triage:
[El-Badry's Aug 2026 follow-up](https://arxiv.org/abs/2608.06453) finds only ~60% of DR3 astrometric
compact-object candidates real and ~50% of spectroscopic ones spurious, and BH3 *failed* DR3's
quality cuts (more are hiding below them). Pre-buildable on the official pre-release samples +
Python package: compact-companion triage validated by recovering BH1/BH2; a 6D hypervelocity rerun
(epoch astrometry kills the spurious-astrometry FPs that plague "fastest star" claims); a
predicted-astrometric-microlensing refresh (a two-group field — Klüter/Wambsganss, McGill/Evans —
where **the prediction itself publishes**, no telescope). *First step:* register Gaia Archive +
NOIRLab Data Lab accounts (unlimited-row async + server-side joins); fit a known DR3 NSS orbit
end-to-end on the pre-release sample.

### Tier 2 — new public datasets, strong method fit

**5. eROSITA-DE DR2 cross-matches** · *~2M X-ray sources, two weeks old · re-cross with DR4 in Dec*
[DR2](https://erosita.mpe.mpg.de/dr2/) (2026-07-31) stacks eRASS1–3, nearly doubling DR1; no account
needed. Redo every DR1×Gaia compact-binary/CV selection at DR2 depth
(template: [X-ray Main Sequence](https://iopscience.iop.org/article/10.1088/1538-3873/ada185),
[22 accreting binaries via X-ray/optical ratio + ZTF periodicity](https://arxiv.org/abs/2505.10478));
eRASS1-vs-3 flux ratios open an X-ray variability axis (TDE / changing-look-AGN candidates); and the
December re-cross against **DR4 NSS orbits** — X-ray-detected astrometric binaries — is a
compact-object hunt nobody can start before us. Best immediate pre-DR4 catalog project. *First
step:* TAP query DR2-vs-DR1 flux ratios; rank >10× variables with Gaia counterparts.

**6. CHIME/FRB Catalog 2 repeater statistics** · *PTA-grade machinery transfers · open now*
[Public](https://chime-frb-open-data.github.io/): 4,539 bursts, 83 repeaters, 138 ~10″ baseband
localizations, plus the injection set. Only one repeater period (16.35 d) is known and **no rigorous
population-level periodicity analysis of Catalog 2 exists** — burst-time periodicity with honest
false-alarm calibration is laptop-scale and exactly the shape of the PTA/exosat statistics. Second
lane: hosts — 138 positions × DESI Legacy/DELVE with PATH. ⚠️ Outrigger voltage and Cat-2 per-event
baseband are *not* public. *First step:* `cfod`, Catalog 2, periodicity machinery on the ten most
active repeaters.

**7. The Dyson-candidate re-vet — Gaia × WISE with real false-positive control** · *extends the seti
thread · competition: two small groups · SPHEREx adds a new axis*
Hephaistos II's 7 candidates are dying one by one (radio imaging
[killed G](https://arxiv.org/abs/2501.05152); a
[Jul 2026 diagnostics paper](https://arxiv.org/abs/2607.03619) finds B & C contaminated, **D & I
still clean** — and says vetting is incomplete). **Nobody has redone the full 5M-star screen** with
blend forward-modeling and hot-DOG surface-density priors. That is the house method — kill the fake
wins — and the deliverable is valuable either way: a quantified null on the method's yield, or a
defensibly clean extreme-IR-excess catalog (debris disks, WD pollution — the
[100 pc WD IR-excess volume was claimed Mar 2026](https://www.aanda.org/articles/aa/full_html/2026/03/aa57709-25.html),
beyond 100 pc was not). *First step:* reproduce the Hephaistos selection via CDS X-Match
(Gaia DR3 × CatWISE2020 × 2MASS); add the centroid-offset test on D and I first.

**8. SPHEREx before its catalogs exist** · *~1-year window · low competition until 2027*
All-sky 102-band spectral images flow to [IRSA](https://irsa.ipac.caltech.edu/Missions/spherex.html)
weekly (QR2, no account, [AWS bucket](https://registry.opendata.aws/spherex-qr/)) — >2 full sky
passes down, but **no official source catalog until 2027**. Forced spectrophotometry at scale now
owns the window: cold brown dwarfs via 3–5 µm colors, unusual SEDs, ices — and the vetting axis for
#7. *First step:* extract 102-band SEDs for a WISE-selected brown-dwarf candidate list.

### Tier 3 — new domains, scoped pilots

**9. Long-period radio transients in public archives + the SMART pulsar backlog** · *GPU + gates
transfer · field is 4 years old*
A genuinely new source class (~12–15 known; two confirmed WD+M binaries) still being found in
*archival* imaging ([review](https://arxiv.org/abs/2601.10393)). Archives public:
[MWA ASVO](https://asvo.mwatelescope.org/) (>18 months, server-side processing), ASKAP/CASDA, MeerKAT
after 12 months, LoTSS DR3. **P > 1 hr and low duty cycles are demonstrably under-searched** (a
6.45-hr source found this year). Sibling: MWA SMART's ~3 PB public voltage data, where the P > 10 s
fold-search regime is nearly virgin ([SMART IV](https://arxiv.org/abs/2607.08106)) — a plausible
independent pulsar discovery with GPUs. *First step:* reproduce the GLEAM-X J1627 detection from one
public drift-scan night, then design the >30-min matched-filter search on unsearched epochs.

**10. Archival-RV planet work — the optical twin of exosat-rv** · *alias-breaking lane thin · RVBank
frozen at Jan 2022*
Journals accept outsider archival-RV results
([GJ 536 c, A&A Oct 2025](https://www.aanda.org/articles/aa/full_html/2025/10/aa55731-25/aa55731-25.html)).
The [HARPS RVBank](https://github.com/3fon3fonov/HARPS_RVBank) stops at Jan 2022 — post-2022 HARPS +
newly-public ESPRESSO is unmined at compilation scale. Sharpest lane: **TESS single/duotransit giants
whose period aliases break against archival RVs** (RVBank + DACE + California Legacy Survey), no
telescope. Cheap bolt-on: ExoClock / Exoplanet Watch accept archival-analysis contributions with
guaranteed authorship. Also feeds Paper II: pull every public optical RV of the exosat companion
hosts for outer-architecture constraints. ⚠️ ExoFOP CTOI status conflicted — see corrections.

**11. DASCH century-scale statistics, done soberly** · *extends plate-archaeology +
dasch-time-machine · low competition, noisy incumbents*
The full plate century is public ([DR7](https://dasch.cfa.harvard.edu/) + `daschlab`). The VASCO
"vanishing stars" community is mired in replication disputes — which is the opening: a rigorously
**artifact-controlled** long-timescale anomaly search (exosat-rv gate discipline pointed at glass)
would be the credible entry in a field that lacks one. December: cross DASCH baselines with DR4 epoch
photometry. *First step:* `pip install daschlab`; recover a known century-scale variable end-to-end;
design the control framework *before* any anomaly hunt.

**12. Meteor-orbit mining — hyperbolics and new showers in GMN** · *2.85M public orbits, CC-BY*
Two real routes: new-shower discovery (registered with the IAU MDC via CBET/WGN — outsiders do this
now) and the interstellar-meteoroid search —
[Wiegert & Vida 2025](https://iopscience.iop.org/article/10.3847/1538-4357/adc44f) found **no
conclusive hyperbolics in the top 57% of events and explicitly left the deeper cut as future work**.
A compute-shaped, named-methodology problem sitting open. *First step:* reproduce the published
quality cuts, extend below the 57% threshold.

**13. Neutrino stacking on IceTracks-DR2 × 2026's new catalogs** · *dataset 3 months old*
[IceTracks-DR2](https://icecube.wisc.edu/science/data-releases/) (May 2026, 2008–2022 tracks)
supersedes the 10-year set behind dozens of papers; public SkyLLH tooling runs stacking on a laptop.
Nobody has stacked it against this year's catalogs: eROSITA DR2 AGN, CHIME Catalog 2 repeaters, the
LPT list. *First step:* SkyLLH + the eROSITA DR2 blazar sample.

**14. Automated comet hunting on CCOR-1** · *updates [coronagraph-comets](coronagraph-comets.md) ·
thin competition vs minutes-fast LASCO veterans*
GOES-19/CCOR-1 joined Sungrazer in 2025 (~30 comets in its first two months) and is the least
picked-over feed; automated detection is explicitly legitimate, claims go through the same per-comet
form (human-gated, per house law). Standing caveats hold: comets named for the instrument, never
you; ESA's SOHO commitment ran "at least until September 2026" — **now due** — which makes the
CCOR-1/PUNCH hedge the right allocation. *First step:* register as a contributor; point a detection
stack at the public CCOR-1 FITS feed.

---

## Cross-match matrix

Pairings of public datasets where **the join itself is the discovery instrument** — verified unrun or
barely run as of 2026-08-14.

| Join | What falls out | State |
|---|---|---|
| eROSITA DR2 × Gaia × ZTF periodicity | CVs, accreting compact binaries at new depth | DR1 template exists; DR2 fresh |
| eROSITA DR2 × VLASS 3 epochs | joint X-ray/radio slow transients | unrun per this sweep |
| Gaia DR4 NSS × eROSITA DR2 | X-ray-detected astrometric binaries (dormant compact objects) | possible Dec 2 |
| Gaia × CatWISE × 2MASS + SPHEREx spectra | vetted extreme-IR-excess catalog; technosignature nulls | re-vet open (#7) |
| CHIME Cat 2 baseband × DESI Legacy / DELVE | FRB host associations (PATH) | 21 hosts done; 138 positions public |
| IceTracks-DR2 × {eROSITA AGN, CHIME repeaters, LPTs} | neutrino source classes | unrun; data 3 months old |
| Fermi 4FGL-DR4 unassociated (2,428) × SMART / LoTSS | pulsar candidates in public radio data | started elsewhere; gaps remain |
| TESS mono/duotransits × RVBank / DACE / CLS | alias-broken long-period giants, no telescope | thin competition (#10) |
| Rubin MPC batches × ITF | attributions, provisional designations | new territory (#3) |
| DASCH × Gaia DR4 epoch photometry | century-baseline secular variables | possible Dec 2 |
| SDSS-V DR19 BHM epochs × ZTF / ATLAS | changing-look quasars, binary-SMBH candidates | lightly mined |
| GWOSC O4 strain × EP / CHIME alert timestamps | subthreshold multimessenger coincidences | BBH lane taken; bursts thinner |

---

## Standing watchers to automate

The agent-native advantage: monitors that hold indefinitely and page a human only at a gate.
**All submission steps stay human-approved.**

| Watcher | Feed / cadence | Fires when |
|---|---|---|
| ITF diff + Rubin-batch attribution | `itf.txt.gz` on MPC monthly batches | new bulk designation batch lands → attribution run queued |
| NEOCP high-eccentricity watcher | public `neocp.txt`, minute-cadence | e>1 / hyperbolic candidate posts → precovery pipeline armed (the 4I race) |
| ESO release-date watcher | TAP `archive.eso.org/tap_obs`, weekly | named datasets go public (β Pic 2026-10-01; CRIRES+/NIRPS rolling) |
| Gaia DR4 countdown | DR4 page + archive schema, weekly | pre-release drops, schema appears, 2026-12-02 |
| eROSITA variability recheck | DR2 vs DR1 catalogs, quarterly | new >10× X-ray variables with Gaia counterparts |
| CCOR-1 comet detector | SWPC FITS/JPEG, 15-min cadence | moving-object candidate → human review → Sungrazer claim |

---

## Corrections to the standing catalogs (2026-08-14)

Facts in [`README.md`](README.md) and [`../IDEAS/`](../IDEAS/README.md) that this sweep found
changed, refined, or in conflict:

1. **Rubin DR1 slipped to ~June 2028.** The 6-month DR1 was cancelled outright; DR1 is now the full
   year-1 release. Alerts + MPC astrometry remain the only public Rubin windows for ~2 years.
2. **Rubin does not flood the ITF.** Two-detection tracklets are withheld by design; the opportunity
   is attribution against bulk designation batches, not a ballooning orphan file.
3. **ZTF primary ops end Dec 2026** (DR25 2027-01-20). The [tns-alert-miner](tns-alert-miner.md)
   niche compresses on a hard date; filters should migrate to Rubin brokers and LS4.
4. **LS4 looks alive after all** — survey paper published (PASP), >5σ public Avro alerts operational
   per its site. The README's "stale, don't build against" deserves a live re-check of broker
   ingestion.
5. **SARC verification is now formal** (Dec 2025 MPC newsletter): archival submitters pass a QC
   process. Get verified before Rubin TNO batches make precovery industrial. Affects
   [dad-triage](dad-triage.md) too.
6. **ExoFOP CTOI conflict unresolved.** README records uploads paused 2026-03-31; this sweep's
   sources describe a working route. Verify live before any TESS candidate plan.
7. **eROSITA idea needs a DR2 rebase** — [the IDEAS entry](../IDEAS/erosita-source-classifier.md)
   was scoped on eRASS1; DR2 (2026-07-31) doubles the catalog.
8. **SOHO's "at least Sept 2026" funding line is now due.** The CCOR-1/PUNCH hedge (#14) is the
   answer.

---

## Not actually public — don't build against

- Rubin DP1/DP2/DR1 images & catalogs (data-rights holders; alerts + MPC astrometry are the public windows)
- GOTO, BlackGEM, WINTER bulk survey data · TAOS II photometry · OVRO-LWA transient data · CHIME raw pulsar data
- KM3NeT analysis-grade data (alerts only) · CHIME Outrigger voltage / Catalog-2 baseband (positions in papers only)
- DESI DR2 spectra (cosmology products out; spectra pending) · NIRPS RV products <2 yr (**raw frames are the workaround**) · MPC MAQI (beta, testers only)

---

## Origin

5-agent verification fan-out, 2026-08-14, ~390k subagent tokens across ~190 tool calls, each agent
instructed to verify against primary sources rather than memory and to flag anything not actually
public. Two inter-agent conflicts were resolved by depth of sourcing (Rubin DR1 date) or left
explicitly open (ExoFOP CTOI). Complements the 2026-07-28 8-agent `DISCOVERY/` fan-out and the
`IDEAS/` run-2 brief; supersedes neither.
