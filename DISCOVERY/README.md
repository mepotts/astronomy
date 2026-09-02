# Discovery pathways — download data, find something new, submit it for review

Where the rest of this repo builds the **usability/translation layer** for other people's science,
this folder is the **discovery axis**: routes where a person with a laptop, no telescope, and no
institutional affiliation can download public data, find a genuinely new object, and submit it to a
body that reviews and credits the find.

Researched **2026-07-28** by an 8-agent fan-out. Every URL below was live-fetched; live-measured
numbers are marked **[measured]**. Anything that could not be confirmed says **unverified** rather
than guessing. Facts here have a shelf life — re-verify before acting on a dated claim.

> **Current execution record (2026-09-02):** see
> [**CAMPAIGN-2026-09-02.md**](CAMPAIGN-2026-09-02.md) for the six fronts executed in
> discovery order, their fail-closed outcomes, and their exact next gates. The older ranking
> below is retained as planning history and is not the live queue.

> **Run 3 addendum (2026-08-14).** A third sweep mapped the *publishable-science* axis (papers, not
> designations) — see [**run3-prospectus.md**](run3-prospectus.md) for the ranked avenues, the Q4 2026
> release calendar (eROSITA-DE DR2 out 07-31; Euclid DR1-Foundation Nov; **Gaia DR4 Dec 2**), the
> cross-match matrix, and the agent-leverage lens. Facts below that moved since 2026-07-28:
> **(a)** Rubin's 6-month DR1 was cancelled — DR1 is now the full year-1 release, ~June 2028; alerts +
> MPC astrometry stay the only public windows. **(b)** Rubin does *not* flood the ITF with orphans
> (2-detection tracklets withheld by design); the opportunity is attribution against its bulk
> designation batches. **(c)** **ZTF primary ops end Dec 2026** — the TNS/DCAP-style niche in §2
> compresses on a hard date; migrate filters to Rubin brokers / LS4. **(d)** LS4 shows signs of life
> (survey paper published, public >5σ alerts claimed) — re-verify before building; the table below is
> stale on it. **(e)** SARC now runs a formal verification process for archival submitters (Dec 2025
> newsletter). **(f)** SOHO's "at least until September 2026" funding line is now due — weight the
> CCOR-1/PUNCH hedge in §3. **(g)** The ExoFOP cTOI pause recorded below conflicts with process pages
> found live in run 3 — check before relying either way.

---

## The eight, ranked by whether they produce an OFFICIAL discovery record

The first cut is not difficulty — it is **does a recognised body issue you a designation.** Four of these
end in a permanent IAU-recognised record. Two end in a semi-official catalogue entry. Two end in a paper
and nothing else. That distinction matters more than realism scores, because it determines what you
actually have at the end.

### Tier A — official IAU-recognised designation ⭐ *start here*

| # | Pathway | Download | Submit to | The record you get |
|---|---|---|---|---|
| 1 | [**MPC Isolated Tracklet File**](itf-linker.md) | 135 MB, no auth | MPC identifications API | **Provisional designation + your name on an MPEC `Id.` line.** 3 individuals credited in July 2026 alone |
| 2 | [**TNS alert miner**](tns-alert-miner.md) | ZTF public alerts, 8–16 GB/night | Transient Name Server | **`AT 2026xyz` IAU designation + ADS bibcode + public discovery certificate** |
| 3 | [**Plate archaeology**](plate-archaeology.md) | DASCH DR7, POSS/SERC scans | Transient Name Server | **IAU designation for a transient from decades ago.** Near-zero competition |
| 4 | [**DAD triage**](dad-triage.md) | `dad_dr2` anonymous ADQL | MPC, **after SARC clears it** | MPC designations under obs code W84 |
| 5 | [**Coronagraph comets**](coronagraph-comets.md) | SOHO/SWAN, CCOR-1, PUNCH | Sungrazer → MPC/CBAT | **Real IAU comet designation** — but named for the *instrument*, never you |

### Tier B — semi-official catalogue entry

| # | Pathway | Submit to | The record you get |
|---|---|---|---|
| 6 | [**Nebula hunt**](nebula-hunt.md) | HASH / French 2SPOT group | **Your-initials designation** forwarded to CDS. Not IAU; permanent ID is `PN GLLL.l±BB.b` on confirmation |
| 7 | [**VSX characterization**](vsx-characterization.md) | AAVSO VSX (5/week cap) | Catalogue row with a `Discoverer` field. AAVSO states in writing you get *"little or no credit"* |

### Tier C — no registry exists; publication is the only claim

| # | Pathway | Submit to | The record you get |
|---|---|---|---|
| 8 | [**LSB survey**](lsb-survey.md) | RNAAS, or A&A via collaboration | **Named co-authorship only.** ⚠️ No priority mechanism exists for static objects — you can be scooped silently |

**If official recognition is the goal, work Tier A and ignore Tiers B–C** except as skills-building.
Tier A pathways 1–4 are all pure software with no telescope and no data-rights gate; #5 is image analysis.

---

## 1. MPC Isolated Tracklet File — the cleanest discovery loop in astronomy

Full sprint plan: **[itf-linker.md](itf-linker.md)**.

`https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz` — **134,758,290 bytes [measured]**, no auth, no
registration, `Last-Modified` regenerating continuously. Contains **9,359,693 observations [measured]**
that were never linked to any orbit, across **882 observatory codes**. Top sources: F51 Pan-STARRS-1
(2.75M), W84 DECam (1.20M), G96 Catalina (1.08M), F52 (1.04M), T09 Subaru (0.87M). 248,810 added
during 2026 alone.

The astrometry is already done by professional pipelines. What remains is **pure computation** —
linking tracklets across nights into a valid orbit. Surveys do not do this exhaustively across each
other's data.

**Credit is real, named, and current.** Identification MPECs carry an `Id.` line. July 2026 alone:

| MPEC | Date | Object | Credit |
|---|---|---|---|
| 2026-O40 | Jul 20 | `2017 SC33 = 2026 NY1` | Id. **A. Lowe** |
| 2026-O57 | Jul 22 | `2009 AC16` (**PHA**) | Id. **P. VanWylen** |
| 2026-O86 | Jul 27 | `2011 YD40 = 2026 OO3` | Id. **R. Matson, F. Manca, B. Engebreth** |

Roughly 2 identification MPECs per week, to individuals working from a computer.

---

## 2. TNS — "discoverer" means first to *report*, not first to observe

Verbatim from TNS: *"the formal 'discoverer' of a transient is defined to be the reporter/s whose
discovery report first turns to public."* If ZTF's camera recorded it and nobody filed it, and you
file it, **you are the discoverer**.

**The proof case — DCAP.** TNS group 195, *"The Daily CV Alert Project… the pipeline for analyzing the
public ZTF alert stream and for resulting TNS submissions."* Two people: **Minrui Ning** (Urumqi) and
**Huixuan Lin** (National Central University). **~100 TNS discovery reports in 12 months, no
telescope.** They found **2 of the 6 galactic novae discovered in all of 2026**. Site:
`https://dcap-minruining.github.io/DCAP/`.

Registration is explicitly open to amateurs: *"This registration will be open to all professional
astronomers as well as to amateurs."* Affiliation may be "None". Sandbox at `sandbox.wis-tns.org`
resets Sundays 04 UT. Reads are `/api/get/…`, writes are `/api/set/…` (changed 2025-01-01). Measured
rate limit: **`x-rate-limit-limit: 10` per rolling 60 s** unauthenticated; bulk reports exempt.

**Where the gap is.** ~80% of TNS reports come from five automated pipelines (Pan-STARRS 26%, ZTF 17%,
ALeRCE 14%, ATLAS 13%, Gaia 10%). The bright end is dead — ZTF's Bright Transient Survey classifies
everything brighter than 18.5. But auto-reporters filter on real-bogus score, host separation and
detection multiplicity, not the full 5σ stream. DCAP lives at mag 19–20.6.

**Open niches:** galactic and **M31/M81 novae** (CBAT estimates *"roughly a couple dozen novae brighter
than about mag 20 in M31 each year"*; TOCP `PSN` postings collapsed 201→10 at the 2016 TNS handover and
hit **zero in 2026**, while `PNV` held flat at ~45–60/yr); CVs and dwarf novae; faint ZTF residue.
**Avoid:** TDEs (~10 classified in 12 months), nuclear transients, anything needing a spectrum.

**The one hard gate:** classification reports require a spectrum, no exceptions. ~90% of TNS objects
(178,927 of 198,524) sit unclassified. You can be the discoverer; you cannot be the classifier.

**Archival plate mining is the zero-competition variant.** `AT 1994au` — Filipp Romanov mined a POSS-II
F plate from 1994-12-28, found a missed **magnitude 12.3** supernova in ESO 157-27, and got a permanent
IAU designation plus bibcode `2025TNSTR4419....1R`. Nobody's bot reads glass.

---

## 3. Coronagraph comets — the only route where zero-equipment amateurs still discover

**The naming rule governs everything here.** IAU Comet-Naming Guideline 3.4(b), verbatim:

> "Comets that are discovered from data or images made public through printed publication or electronic
> posting (e.g., World Wide Web) are not eligible for individual names of people and generally will not
> be named unless there is an established program name for the origin of the images."

You get discovery credit in the MPEC/CBET and the permanent discoverer column. You do not get your name
on the sky. This is exactly why 5,204 SOHO comets are all "SOHO".

| Feed | Access | State |
|---|---|---|
| **SOHO/LASCO** C2/C3 | `soho.nascom.nasa.gov/data/REPROCESSING/Completed/{YYYY}/{c2\|c3}/{YYYYMMDD}/` — ~165 MB/day for both cameras **[measured]**, 12-min cadence | **5,204 comets.** Poll no faster than every 15 min. ⚠️ ESA funding phase-out; ops extended "at least until September 2026" |
| **GOES-19 CCOR-1** | `services.swpc.noaa.gov/products/ccor1/` — FITS 8.8 MB each, rolling ~24-day window; JPEGs at 15-min cadence **[measured]** | **~30 sungrazers in its first two months (2025).** Newest and least picked-over. ⚠️ ~9-month confirmation backlog |
| **SOHO/SWAN** | `swan.projet.latmos.ipsl.fr` (HTTP only) | Lyman-α, sees down to a few tens of degrees solar elongation — **sky ground surveys structurally cannot reach** |
| **PUNCH** | `punch.space.swri.edu` — *"fully open to anyone for use with no restrictions"* | Launched Mar 2025. **Zero comets discovered in it yet.** Genuinely unexplored |
| PSP/WISPR | `wispr.nrl.navy.mil/wisprdata/` — L3 products need no preparation | 8 confirmed comets; ~3-month release cadence removes time pressure |

**Verified no-telescope discoveries:** **C/2025 F2 (SWAN)** — Michael Mattiazzo analysed downloaded SWAN
data using *Guide 9 planetarium software* just to convert ecliptic→equatorial coordinates; confirmed by
Quicheng Zhang with a **40 mm refractor**; co-discoverers Vladimir Bezugly and Rob Matson; reached APOD.
**C/2025 R2 (SWAN)** — Bezugly, *"a rather obvious blob"*. **C/2026 B4** — Hanjie Tan, SWAN, later
confirmed in PUNCH.

Report via `sungrazer.nrl.navy.mil/report` after registering at `/contributors/request_form`. Minimum
**2 positions in C2 or 3 in C3**; *"credit will be given to the first person to provide two or more
accurate positions"* — single positions get nothing.

⚠️ **TOCP is the wrong route for comets** — it states it is *"designed for use with stationary,
extra-solar-system objects only."* Comets go to MPC's **PCCP**
(`minorplanetcenter.net/iau/NEO/pccp_tabular.html`) or by plain-ASCII email to `cbatiau@eps.harvard.edu`.

---

## 4. Low-surface-brightness structures — the best co-authorship route

**The proof case.** arXiv:2510.24836, **RNAAS 9, 292 (2025)** — *"A stellar stream around the spiral
galaxy Messier 61 in Rubin First Look imaging"*. Five authors, one an unaffiliated Italian amateur
(**Giuseppe Donatiello**). First stellar stream ever found with Rubin. **Found in a public
press-release image** — the 15.1 GB Virgo "Cosmic Treasure Chest" TIFF.

**Donatiello is the template to copy:** no affiliation, now a routine A&A co-author. Donatiello II/III/IV
(A&A 652, A48) came from *visual inspection of DECam images in the DESI Legacy Surveys* — and
Donatiello II was **missed by the detection algorithm**.

**The open door:** David Martínez-Delgado (IAA-CSIC) has given amateurs full co-authorship for 15 years —
arXiv:2504.02071, **A&A 701, A182 (2025)**, 28 authors including eight amateurs.

**Sobering counterpoint** that tells you where the real edge is: professional David Sand found three
dwarf galaxies by *"watching TV and scrolling through the DESI Legacy Survey viewer, focusing on areas I
knew hadn't been searched."* **Your differentiator is not tooling — it is solving the "which sky is
unsearched" database problem.**

**A clean structural gap:** an arXiv search for `"ultra-diffuse" AND "citizen science"` and
`"low surface brightness" AND "citizen science"` returns **0 results each**. A citizen-science UDG/LSBG
project has never existed, while the best professional pipeline (SMUDGes) still terminates in two-person
by-eye vetting with ~15% inter-reviewer disagreement.

---

## 5–6. Solar-system triage and planetary nebulae

**NOIRLab DAD** (DECam Asteroid Database, `dad_dr2` via anonymous ADQL) — **662,154 tracklets** with
digest2 NEO-rarity scores and pre-generated MPC-format records in `dad_dr2.movmpc` **[measured]**.
**6,856 tracklets with digest2 ≥ 65 were never submitted to the MPC**; 50,163 were never submitted at
all. Coverage stops **2018-04-20**, and **425,309 DECam instcal images postdate 2019-11-01** with no
NSC DR3 to fold them in. ⚠️ Coordinate with NOIRLab/MODS before submitting — these may be knowingly
withheld as unvetted, and duplicate MPC submissions are actively harmful.

**Planetary nebulae** — amateurs found ~**5% of the entire Galactic PN inventory** in one paper
(Le Dû et al. 2022, **A&A 666, A152**, 11 of 13 authors amateur). Only ~3,500–4,000 Galactic PNe are
known against an estimated ~25,000. Submission runs through `pascal.ledu@2spot.org` → CDS + HASH
(`hashpn.space`, free registration, open to anyone). ⚠️ There is **no `hash-pn.org`**.

**Where the professionals say the ground is open:** Li, Parker & Jia (**A&A 692, A103**) state in print
that VPHAS+ *"has not yet undergone extensive manual, systematic searching"* — their ML prototype hit
**70.97% spectroscopic success** on >800 candidates. Also unmined: **MDW Hα Sky Survey** (DR1 = entire
northern sky, **DR2 = first full-sky release, end of 2026**) and Ziegenbalg's `simg.de` narrowband survey.

**The wall:** "True PN" grade needs spectroscopy, and confirmation exposures are brutal — StDr 140 took
~76 h, JAM 2 took **131 h in [OIII]**. You can be discoverer-of-record and co-author; you must hand off
confirmation.

---

## 7. Variable stars — read this before investing

**Bulk discovery is over.** VSX now holds **10,304,607 entries [measured]**, of which **8,016,792 (78%)
are Gaia DR3** — one machine catalogue. Anyone planning to "find lots of new EWs in ZTF" is ~4 years late.

**But the characterization frontier is enormous and explicitly sanctioned.** Measured against the live
catalogue: **5,470,632 entries (53%) have no period at all**; 1,809,758 are typed `ROT` with no period;
337,413 are bare `VAR` or `MISC`. AAVSO turns this into seven named projects at
`https://www.aavso.org/vsx-data-mining`.

**Three constraints that shape any approach:**
1. **5 submissions per week** reviewed per user/group. Drafts auto-deleted after 60 days.
2. Moderation is **essentially one person** (Sebastián Otero, 2026-07-27: *"moderation is mostly a one
   staff member task at this time"*).
3. ⚠️ **AAVSO publicly warned about AI-assisted submissions on 2026-07-27**: *"The use of AI to perform
   the analysis, without properly completing the VSX fields as specified in our supporting material, is
   causing a lot of delays… No matter how good you think AI might be, the VSX guidelines should be
   followed."* Mandatory fields and stricter filters are planned. **Treat this as the binding constraint.**

Guidelines also state a **double standard**: *"we are more critical of data-mined submissions because we
expect the submitter to do some work, such as period analysis, rather than just regurgitating information
already available from a given survey's site."*

**Credit, verbatim:** *"As opposed to comet or asteroid discovery, you will get little or no credit for
discovering a new variable star."* There **is** a public `Discoverer` field and you may coin your own
acronym — but **the paper is the credit**, not the VSX row. Venues: **OEJV** (moved to
`oejv.physics.muni.cz`; the old `var.astro.cz/oejv/` is frozen at issue #204 and looks dead but isn't),
JAAVSO, Peremennye Zvezdy.

---

## Two procedural gates that will bite you

### SARC — contact before you submit archival astrometry

`https://www.minorplanetcenter.net/mpcops/documentation/sarc/` — the Singleton and Archival observations
Committee exists because *"the scale and accessibility of public data archives… has significantly lowered
the barriers to finding, extracting and submitting archival data to the MPC."*

> "If you are planning to submit archival observations from one of these archives, please contact the
> corresponding SARC member **before** submitting the data to the MPC."

| Archive | Obs code | Contact |
|---|---|---|
| ZTF / WISE-NEOWISE | I41 / C51 | Joe Masiero |
| Pan-STARRS | F51, F52 | Rob Weryk |
| DECam / SDSS | W84 / 645 | Tyler Linder |
| Catalina | 703, G83, G96, I52, V06 | David Rankin |
| ATLAS | M22, R17, T05, T08, W68 | Larry Denneau |
| Rubin/LSST | X05 | Mario Jurić |
| SOHO / STEREO | 249, C49, C50 | SARC Chair |

**The upside is large:** archival measurements submit under the **originating facility's** obs code, which
dissolves the otherwise-hard requirement to earn your own (10 numbered NEAs, 2 nights each, 3–5 positions
per night, tied to a physical location).

### ADES is effectively mandatory

January 2026 MPC Newsletter, verbatim: *"This is our monthly reminder to please submit your observations
in ADES format, using **ADES version 2022**… The MPC does not plan to maintain support for the MPC 1992
80-column format indefinitely."* No hard cutoff published, but new observatory codes cannot use MPC1992
at all. **ADES cannot be emailed** — use `submit_psv` / `submit_xml`, and validate against
`submit_psv_test` first.

---

## Publication and credit

**RNAAS is the answer to "where do I publish without a grant."**

| | |
|---|---|
| **Cost** | **$0** — *"no article publication charges."* (Compare ApJ Tier 1 at $1,425, ApJL at $2,978) |
| **Peer reviewed?** | **No** — *"not peer reviewed; they are, however, moderated by an editor."* |
| **Limit** | **≤1,500 words** including title, headers, captions, references; 150 reserved for the required abstract |
| **Figures** | **One figure OR one table — not both** |
| **Speed** | *"typically published within 72 hours of receipt"* |
| **Citable** | *"searchable in ADS and fully citable," "archived for perpetuity."* DOI via IOP |
| **Cap** | 20 Notes per 12 months per first author |
| **Scope limit** | *"unable to publish substantially novel theories"* — good for observations, null results, comments |

**AAS style guide, verbatim:** *"If an author is not currently at an institution and prefers not to
include a personal address, then affiliations such as **'Planet Hunter,' 'Private Astronomer,' or
'Independent Researcher'** are acceptable."* AAS membership is not required to submit.

RNAAS is real currency, not a consolation prize: **`nifty-ls`, the fastest Lomb-Scargle implementation
in astronomy, was published in RNAAS.**

⚠️ **The real gate is arXiv, not the journal.** First submission to a category needs **endorsement**;
automatic endorsement requires an institutional email, which is exactly what an unaffiliated person
lacks. The documented workaround is the Donatiello path: **claim co-authorship on someone else's paper
first.** Whether arXiv accepts RNAAS-length notes in 2026 is **unverified** (they rejected them in 2019
under a short-submission guideline; current moderation docs are silent on length). **Plan on ADS as your
permanent index, not arXiv.**

**There is no TNS for static objects.** TNS is *"the official IAU mechanism for reporting new
astronomical **transients**"* and excludes non-transients. There is no registry, timestamping service, or
priority-claiming mechanism for streams, UDGs or nebulae — **priority is established only by
publication.** You cannot claim a find and work it up later. Real consequence: 559 PN candidates sit
unpublished on planetarynebulae.net right now, and JAM 2 was already privately in HASH, entered by
D. J. Frew and never made public.

---

## Closed, dormant, or dead — don't waste time here

| Thing | State |
|---|---|
| **ExoFOP cTOI upload** | **PAUSED since 2026-03-31**, no restoration date. The find→submit→TOI loop is broken at the submission step. Solo amateurs converted at ~1% vs ~90% for institutional ML pipelines anyway |
| **Rubin/LSST images + catalogs** | Proprietary until **~June 2028**. Only the **alert stream** is public — and it has *no* proprietary period, but reaches you only via brokers. US amateurs may petition for data rights under RDO-13 §4.1 |
| **Gaia DR4** | Not until **2 December 2026**. No `gaiadr4` schema exists **[measured]** |
| **Gaia Science Alerts** | **Frozen.** Last alert `Gaia25aeh`, 2025-01-15; spacecraft passivated Mar 2025. The status light still says "ON" — it is lying |
| **Backyard Worlds: Planet 9** | Paused, 100% complete, out of data, blog silent since 2023. Use Cool Neighbors or Binaries |
| **Active Asteroids** | Paused, 100% complete. URL moved: `/fulsdavid/` is **404**, use `/orionnau/` |
| **Dark Energy Explorers, Space Warps HSC, RGZ LOFAR, Stellar Stream ID, DELVE Dwarf Quest** | All 100% complete, out of data |
| **SDSS Moving Object Catalog** | Frozen at 2007 data; page still promises a release "probably during Spring 2009" |
| **APASS** | Effectively frozen at **DR10 (Nov 2018)**. DR11 announced at annual meetings since 2022, never shipped. DR10 has documented quality problems — missing fields, a reported whole-magnitude offset above V=14. **Prefer DR9 via VizieR `II/336`** |
| **LS4** | Designed as 90% public with SCiMMA alerts, but site stale since Jan 2025, **zero LS4 topics among SCiMMA's 222 public topics**, not a registered TNS group. Watch; don't build against |
| **BlackGEM, GOTO, WINTER, MeerLICHT** | Operating, no public data. TNS is the only window. Exception: **Kilonova Seekers** (Zooniverse) serves GOTO difference images and volunteers contributed **48 of GOTO's 2,557 discoveries in 2025** |
| **Zooniverse volunteer co-authorship** | **Degraded.** The 2026 Euclid Space Warps lensing paper credited 1,800 volunteers in a single footnote; the 2015 papers named moderators as co-authors |

**Dead URLs to purge from any notes:** `dasch.rc.fas.harvard.edu` (→ `dasch.cfa.harvard.edu`) ·
`occultation.tug.tubitak.gov.tr` (→ `opop.obspm.fr`) · `lasair.roe.ac.uk` (404) ·
`api.fink-portal.org` (→ per-survey `api.ztf.fink-portal.org` / `api.lsst.fink-portal.org`) ·
`registry.g-vo.org` (NXDOMAIN, → `dc.g-vo.org/tap`) · `var2.astro.cz/ETD/` (→ `var.astro.cz/en/Exoplanets`) ·
`ls4.science` (NXDOMAIN) · `hash-pn.org` (never existed) · `simbad.cfa.harvard.edu` (13 months stale,
TAP returns 500 — use Strasbourg).

⚠️ **CBAT works over `http://` only** — its cert chain is broken and it runs Apache 2.2.3 on Scientific
Linux. It is alive (CBET 5719 issued 2026-07-28) but **no longer an IAU centre**, and several of its
static pages (nova list, SN list, TOCP cross-reference, reporting instructions) are 10–15 years stale.

---

## The clock

Rubin submitted **~20,000 candidate asteroid discoveries / ~246,000 observations in a single batch** on
the night of 2026 Feb 5, and issued its first **800,000 alerts** on Feb 24, scaling toward ~7M/night.
Finding a bright new main-belt asteroid in fresh survey data is over.

What survives Rubin is structural, not incidental:
- **Linking what the surveys never linked** (the ITF) — Rubin adds to this problem, it doesn't solve it.
- **Precovery** — extending arcs of Rubin discoveries *backward* into 2012–2019 DECam epochs. Its value
  **increases** as Rubin ramps.
- **Coronagraph sky** — Rubin cannot see within tens of degrees of the Sun.
- **Glass** — nobody's bot reads photographic plates.

Treat **2026–2027 as the window** for the faint-transient niche specifically; it compresses hard once
Rubin reaches full cadence.

---

## Origin

8-agent research fan-out, 2026-07-28, ~1.2M subagent tokens across ~900 tool calls. Search budgets were
exhausted partway through several threads, so late-stage findings rest on direct HTTP fetches and live
API queries rather than keyword search — which produced *stronger* evidence but thinner forum/mailing-list
coverage. Items marked **unverified** were genuinely not confirmable at the time; they are not hedges.
