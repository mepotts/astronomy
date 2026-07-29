# TNS alert miner — reporting transients nobody bothered to report

**One-liner:** Consume the public ZTF alert stream, filter for the transient classes the survey
auto-reporters structurally ignore (galactic novae, M31/M81 novae, CVs, faint residue at mag 19–21),
and file discovery reports to the Transient Name Server — which awards an IAU designation to whoever
reports first, regardless of whose camera took the photons.

**Scores (U/B/E):** U **2/5** (DCAP is doing exactly this and doing it well — the method is proven, not
novel) · B **5/5** (public Avro stream or a broker REST API, no account gating, no telescope) · E **5/5**
(permanent IAU designation + citable ADS bibcode per discovery, and the credit rule is unusually
favourable)

**Status:** proposed

**Cost to operate: $0** — public alert stream, free broker APIs, free TNS account.

---

## The rule that makes this work

TNS, verbatim:

> "the formal 'discoverer' of a transient is defined to be the reporter/s whose discovery report first
> turns to public."

**Not first to observe. First to report.** ZTF's camera records far more than ZTF's pipeline reports.
If a real transient sits in the public stream and nobody files it, the first person to file it is the
discoverer of record, with a public discovery certificate and an ADS bibcode.

## Be honest about the wedge

**There is no wedge.** DCAP — TNS group 195, two people, **Minrui Ning** (Urumqi) and **Huixuan Lin**
(National Central University) — logged **~100 TNS discovery reports in twelve months** doing precisely
this, with no telescope. They found **2 of the 6 galactic novae discovered in all of 2026**. Their site:
`https://dcap-minruining.github.io/DCAP/`.

So this is not white space. It is a **demonstrated, repeatable, currently-open method** that roughly two
people in the world are working seriously. The question is not "can this work" — it demonstrably does —
but "is there room for a second team." Evidence says yes: the stream is far larger than DCAP's throughput,
and the niches below are defined by *filter policy*, not by competition.

## Where the actual gap is

~80% of TNS reports come from five automated pipelines: Pan-STARRS 26%, ZTF 17%, ALeRCE 14%, ATLAS 13%,
Gaia 10%. The bright end is dead — ZTF's Bright Transient Survey aims to classify **everything** brighter
than 18.5 mag.

But the auto-reporters filter on **real-bogus score, host separation, and detection multiplicity** — not
on the full 5σ stream. DCAP lives at mag 19–20.6, below where the SN-tuned filters bite.

**Defensible niches, in order of openness:**

1. **Galactic novae.** ~10/yr confirmed. In 2026, **100% were survey-found and a third were found by desk
   mining**. SN-tuned filters actively deprioritise the galactic plane (high extinction, crowded fields,
   high surface brightness). The TOCP record is the cleanest proof of the structural shift: `PSN` postings
   collapsed 201 → 10 at the 2016 TNS handover and hit **zero in 2026**, while `PNV` held flat at ~45–60/yr.
2. **M31 / M81 novae.** CBAT estimates *"roughly a couple dozen novae brighter than about mag 20 in M31
   each year."* The TOCP is now dominated by `PNV J0042…+41…` entries.
3. **CVs and dwarf novae.** Outburst morphology is non-sinusoidal, which is exactly what periodogram-and-ML
   classification pipelines discard.
4. **Faint ZTF residue, mag 19.5–21.**

**Avoid:** TDEs (only ~10 classified in 12 months — the vetting burden is disproportionate), nuclear
transients, and anything requiring a spectrum.

## The one hard gate

**Classification reports require a spectrum. No exceptions.** This is why ~90% of TNS objects (178,927 of
198,524) sit unclassified. You can be the **discoverer**; you cannot be the **classifier** without
telescope access or a collaborator.

Encouraging counter-note: amateur spectroscopists now routinely fill this gap. **Claudio Balcon** submitted
the first classification spectrum of AT 2026stb on 2026-07-12 — *ahead of* the SOAR 4.1 m spectrum later
the same day. **ARAS** (`https://aras-database.github.io/database/novae.html`, 83 stars / 4,826 spectra,
updated 2026-07-24) is the organising body and is the natural place to find a confirming partner.

---

## Data sources & access

| Source | Endpoint | Notes |
|---|---|---|
| **ZTF public alerts** (raw) | `https://ztf.uw.edu/alerts/public/` | 2,963 nightly tarballs, no auth. **8–16 GB/night** compressed **[measured]**. Gzipped **Avro**, 30-day photometric history + three 63×63 px cutouts per alert |
| **ALeRCE** | `https://api.alerce.online/ztf/v1/` | **No API key.** Mind the trailing slash (308 without). Also the 3rd-largest TNS reporting group — proof the broker route earns credit at scale |
| **Fink** | `https://api.ztf.fink-portal.org/api/v1/` | REST unauthenticated; Kafka needs free registration |
| **ANTARES** | `https://api.antares.noirlab.edu/v1/` | Unauthenticated JSON:API, live and ingesting ZTF + LSST. `pip install antares-client` |
| **Babamul** | `https://babamul.caltech.edu/` | **Uniquely cross-matches ZTF and LSST in real time** — cheapest way to attach ZTF's 8-year baseline to a fresh Rubin detection |
| **ATLAS forced photometry** | `https://fallingstar-data.com/forcedphot/` | Free registration, amateurs accepted. **Photometry at arbitrary positions including non-detections** — brokers cannot give you this. Limits: 60 submissions/min, 500 queued tasks, 100 positions/task |
| **TNS** | `https://www.wis-tns.org` | Reads `/api/get/…`, **writes `/api/set/…`** (changed 2025-01-01). Measured limit: `x-rate-limit-limit: 10` per rolling 60 s; **bulk reports exempt** |
| **TNS sandbox** | `https://sandbox.wis-tns.org/` | Resets Sundays 04 UT |
| Cross-match mirror | `tns_public_objects.csv.zip` + hourly deltas | TNS explicitly asks you to use this rather than hammering cone-search |

**Start with a broker, not the raw stream.** 8–16 GB/night is a bandwidth problem you do not need in M1;
ALeRCE/ANTARES give you filtered candidates over HTTP with no account. Move to raw Avro only if broker
filtering proves too coarse.

**Registration lead time is real** — TNS accounts are human-vetted. State plainly that you are an amateur
data-miner and describe the pipeline. Affiliation may be "None"; no group is required (group ID 0 = "None").
**Do this on day one**, because it gates everything downstream.

---

## Guardrails

1. **Sandbox everything first.** `sandbox.wis-tns.org` exists precisely so you never learn the report
   schema against the live registry.
2. **A false discovery report is a public, permanent, attributed error.** Every candidate must clear:
   VSX, SIMBAD, MPChecker (asteroid contamination), the ZTF `catflag` mask, and a cross-epoch check for
   detector artifacts.
3. **The classic false positive is a Mira.** CBAT warns explicitly that unfiltered CCDs over-respond to
   red objects, so long-period variables masquerade as novae. Colour-check before reporting.
4. **Do not report as a "Nova" what you have not had classified.** File `at_type` honestly; let the
   spectrum decide the type.
5. **Respect the rate limit.** 10 requests per 60 s unauthenticated; use the bulk CSV mirror for
   cross-matching rather than per-object cone searches.

---

## Architecture sketch

```
tns-miner/
  stream/    broker poll (ALeRCE/ANTARES) → normalized candidate records; raw Avro reader as M3 option
  filter/    class-targeted cuts: galactic-plane novae, M31/M81 field, CV outburst morphology, faint residue
  context/   VSX + SIMBAD + MPChecker + TNS-mirror cross-match; ZTF catflag hygiene; colour/extinction cuts
  history/   ATLAS forced photometry at candidate position — the non-detection is what makes a report credible
  review/    per-candidate packet: light curve, cutout triplet, catalogue verdicts, why-it's-new argument
  report/    TNS bulk-report JSON; sandbox-first; per-batch human confirmation
```

**Stack:** Python. `alerce` / `antares-client` / `fink-client` (all current, 2026 releases). `astropy`,
`polars`/`duckdb` for the TNS mirror. `fastavro` only if you go to the raw stream. Fits the repo's
existing per-project `.venv` + pytest + typer conventions.

---

## Milestones

**M0 — kill-check (~1 day).** Register the TNS account (it has vetting latency — start the clock). Then
take **three 2026 nova discoveries that DCAP or ASAS-SN reported** and confirm the alerts were present and
reachable in the public broker feed at the time, with your intended filter. *If your filter would not have
surfaced a known discovery, the filter is wrong — fix it before generating candidates.*

**M1 — candidate generation, no reporting.** Broker poll + class-targeted filters + full catalogue
cross-match. Success metric: a ranked nightly candidate list where you can articulate, per object, why it
is not a known variable, not an asteroid, and not an artifact.

**M2 — the credibility layer.** ATLAS forced photometry for the pre-discovery non-detection, plus the
review packet. A report without a defensible non-detection is a weak report; this milestone is what makes
submission responsible.

**M3 — sandbox round-trip, then one real report.** Bulk-report schema against the sandbox, then a single
hand-reviewed live submission.

**M4 — the citable layer.** Register a **TNS reporting group** (DCAP is the precedent) so discoveries
carry a project name. TNS **AstroNotes** (`https://www.wis-tns.org/astronotes`) are open to all registered
users and ADS-indexed — cross-match and analysis notes on existing unclassified ATs are legitimate,
citable output *without* needing your own discovery.

---

## What success looks like

`AT 2026xyz` with your name on the discovery certificate and a bibcode of the form `2026TNSTR….1X`. If a
spectrum follows and the object is a nova, a CBAT CBET naming it *"Nova <Con> 2026"* and, later, a
permanent GCVS designation assigned in Moscow.

**The clock:** TNS group `Rubin` has only 52 objects so far, all from a 5-day commissioning window in
Nov 2025. When Rubin reaches full cadence (~7M alerts/night) the faint niche compresses hard. **Treat
2026–2027 as the window.**

---

## Sources

- TNS: `https://www.wis-tns.org` · getting started `/content/tns-getting-started` · bots `/bots` ·
  AstroNotes `/astronotes` · sandbox `https://sandbox.wis-tns.org/`
- ZTF public alerts: `https://ztf.uw.edu/alerts/public/` · ZTF at IRSA `https://irsa.ipac.caltech.edu/Missions/ztf.html`
- Brokers: `https://api.alerce.online/ztf/v1/` · `https://api.ztf.fink-portal.org/api/v1/` ·
  `https://api.antares.noirlab.edu/v1/` · `https://babamul.caltech.edu/`
- ATLAS forced photometry: `https://fallingstar-data.com/forcedphot/`
- DCAP (the model to copy): `https://dcap-minruining.github.io/DCAP/`
- ARAS spectroscopy network: `https://aras-database.github.io/database/novae.html` · forum `https://www.spectro-aras.com/forum/`
- Nova reference list (the authoritative one — **not** CBAT's, which stopped in 2010):
  `https://asd.gsfc.nasa.gov/Koji.Mukai/novae/novae.html`
- CBAT (HTTP only): `http://www.cbat.eps.harvard.edu/` · reporting `cbatiau@eps.harvard.edu`
