# DAD triage — the 6,856 NEO-likely tracklets nobody submitted

**One-liner:** NOIRLab's DECam Asteroid Database is a public, anonymously-queryable table of 662,154
moving-object tracklets produced by a professional pipeline — and **50,163 of them were never submitted
to the Minor Planet Center**, including **6,856 scoring digest2 ≥ 65 (NEO-likely)**, with MPC-format
records already generated and sitting in an adjacent table.

**Official recognition: YES.** Accepted submissions produce MPC designations and MPEC credit, same
registry as [itf-linker](itf-linker.md).

**Scores (U/B/E):** U **3/5** (the data is public and the gap is measurable, but it exists for a reason —
see the kill-check) · B **5/5** (anonymous ADQL, pre-formatted records, no pixel work) · E **4/5** (highest
value-per-effort of any pathway *if* the kill-check passes)

**Status:** proposed — **gated on an M0 that may kill it outright**

**Cost to operate: $0** — anonymous TAP, no account.

---

## The measured gap

All figures live-queried from `https://datalab.noirlab.edu/tap` on 2026-07-28:

| Table | Rows | Content |
|---|---|---|
| `dad_dr2.movgrp` | **662,154** | main tracklet table — carries `digest` (digest2 NEO-rarity score 0–100), `mpcid`, `mpcsent` |
| `dad_dr2.movobs` | 2,974,302 | individual detections |
| `dad_dr2.movmpc` | 2,974,297 | **MPC-format records, ready to read** |
| `dad_dr2.movexp` | 23,622 | exposures |
| `dad_dr2.movds` | 5,335 | datasets/pointings |

**The openings, measured:**
- **50,163 tracklets never submitted to the MPC** (no `mpcsent`)
- **6,856 with digest2 ≥ 65** (NEO-likely) never submitted
- **8,581 with digest2 ≥ 65** have no `mpcid` at all
- Coverage **stops 2018-04-20**; NSC DR2 stops Oct 2019
- **425,309 DECam instcal images postdate 2019-11-01** — 37% of the archive, covered by neither DAD nor
  NSC, and **there is no NSC DR3** to fold them in
- DAD covers only 23,622 exposures ≈ **2% of the 1.14M DECam instcal images**, because MODS requires ≥3
  same-field exposures in one night. The other 98% has never been through a tracklet finder.

The table literally tells you what has and hasn't been reported. That is unusual and it is the whole
opportunity.

---

## ⚠️ Read this before writing any code

**The gap may be deliberate.** These tracklets were produced by NOIRLab's MODS pipeline and *not* submitted.
Plausible reasons: known contamination, known duplication with other surveys, failed internal vetting, or
simply un-triaged backlog. **You do not know which**, and the difference determines whether this project is
valuable or actively harmful.

**Duplicate or bad MPC submissions are not a neutral failure.** They pollute a shared scientific registry,
consume MPC staff time, and damage submitter reputation such that *future* reports get disregarded.

**Therefore M0 is a correspondence step, not a code step**, and the project does not proceed without an
answer. This is the one plan in `DISCOVERY/` where the first milestone might legitimately end it.

---

## The SARC gate

`https://www.minorplanetcenter.net/mpcops/documentation/sarc/` — the Singleton and Archival observations
Committee exists precisely because *"the scale and accessibility of public data archives… has significantly
lowered the barriers to finding, extracting and submitting archival data to the MPC."*

> "If you are planning to submit archival observations from one of these archives, please contact the
> corresponding SARC member **before** submitting the data to the MPC."

**DECam (obs code W84) → Tyler Linder**, who also chairs SARC and covers SDSS (645).

**The upside of going through SARC:** archival measurements submit under the **originating facility's**
observatory code. You never need to earn your own code (which would otherwise require 10 numbered NEAs
across 2 nights each, 3–5 positions per night, tied to a fixed physical location — impossible without a
telescope).

Also flagged on MPC's own docs: `https://www.minorplanetcenter.net/mpcops/documentation/program-codes-policy/`
says archival program-code assignment **is still being refined**. Policy is live-changing; re-check before
investing effort.

---

## Data access

**Anonymous ADQL, no account:**

```bash
curl -G "https://datalab.noirlab.edu/tap/sync" \
  --data-urlencode "REQUEST=doQuery" --data-urlencode "LANG=ADQL" \
  --data-urlencode "FORMAT=csv" \
  --data-urlencode "QUERY=SELECT TOP 100 * FROM dad_dr2.movgrp
                          WHERE digest >= 65 AND mpcsent IS NULL"
```

⚠️ **ADQL dialect gotchas confirmed live on this service:** `COUNT(DISTINCT …)`, `CASE` in `GROUP BY`,
and `EXTRACT(YEAR FROM …)` are rejected by the parser; `q3c_radial_query` is not exposed through TAP; and
`CONTAINS(POINT(…), CIRCLE(…))` fails with `function point(unknown, double precision, double precision)
does not exist`. **Use `TOP n` + `BETWEEN` bounding boxes over TAP**, or use `queryClient` with native SQL
inside a Data Lab notebook, which *does* have q3c.

```bash
pip install astro-datalab   # imports as `dl`; NOT the unrelated `datalab` package
```

**Supporting cross-checks:** MPChecker `https://minorplanetcenter.net/cgi-bin/checkmp.cgi` · SkyBoT
`https://ssp.imcce.fr/webservices/skybot/api/conesearch.php` · JPL SBIDENT
`https://ssd-api.jpl.nasa.gov/sb_ident.api` · CATCH `https://catch.astro.umd.edu/`

**Related but distinct:** the MPC's own solicited backlog at
`https://www.minorplanetcenter.net/mpcops/orbits/no-orbits-astrometry/` — `no_orbit_desigs.obs` (14.6 MB),
`c51_desigs.txt` (440 NEOWISE designations lacking orbits). **The MPC is explicitly asking for this work**,
which makes it a safer starting point than DAD if the DAD kill-check stalls.

---

## Guardrails

1. **No submission before SARC replies.** Not "no bulk submission" — *no submission*.
2. **Never auto-submit.** Per-batch human review, permanently.
3. **Dedupe against `mpcid`/`mpcsent` first, then against MPChecker/SkyBoT/SBIDENT.** A tracklet with no
   `mpcid` in DAD may still be a known object submitted by another survey.
4. **Sandbox the format** (`submit_psv_test`) before the live endpoint.
5. **ADES 2022, not MPC1992.** ADES cannot be emailed — use `submit_psv`/`submit_xml`.
6. **≥2 observations per object per night** or the whole batch is auto-rejected, often silently.

---

## Architecture sketch

```
dad-triage/
  pull/      anonymous ADQL → Parquet: movgrp ⋈ movobs ⋈ movmpc, filtered on mpcsent IS NULL
  score/     re-derive digest2 independently; flag disagreement with the stored `digest`
  dedupe/    mpcid check → MPChecker → SkyBoT → SBIDENT → CATCH; "is this actually unknown?"
  fit/       Find_Orb; residual RMS, covariance, arc quality vs published MPC acceptance criteria
  review/    per-batch packet for human + SARC review
  submit/    ADES emit; sandbox-first; blocked until SARC sign-off recorded in the repo
```

Shares `fit/`, `vet/`, `review/`, `submit/` with [itf-linker](itf-linker.md) — **build that one first and
this is largely a new front-end on the same pipeline.**

---

## Milestones

**M0 — the correspondence kill-check (do this before anything else).**
Email the SARC contact for DECam/W84 (Tyler Linder), state plainly: you have identified 6,856 unsubmitted
digest2 ≥ 65 tracklets in the public `dad_dr2` tables, you intend to vet and submit them, and you want to
know (a) whether they were withheld deliberately, (b) whether MODS/NOIRLab intends to submit them, and
(c) whether SARC wants this work done by an outside party at all.

**Three possible outcomes:**
- *"They're unvetted backlog, go ahead with review"* → proceed to M1, and this is the highest-value
  pathway in the folder.
- *"We're handling it"* → **stop.** Redirect to the MPC's solicited `no-orbits-astrometry` backlog instead,
  which carries no such ambiguity.
- *No reply after a reasonable interval* → **stop, and redirect.** Silence is not consent for a shared
  registry.

**M1 — independent verification.** Re-derive digest2 and orbit fits yourself; do not trust the stored
`digest` blindly. Quantify how many of the 6,856 survive independent scoring plus full catalogue dedupe.
Publish that number — it is interesting whether it is 6,000 or 60.

**M2 — vetting + review packet.** As per itf-linker M2.

**M3 — sandbox, then one SARC-reviewed batch.**

**M4 — the citable artifact.** *"The unsubmitted residue of the DECam Asteroid Database"* is a legitimate
**RNAAS** note whether or not you submit a single observation — it characterises a public dataset nobody
has audited.

---

## What success looks like

MPC designations under obs code **W84**, with your name credited on the submission, and a measured,
published account of how much real signal was sitting unexamined in a public table.

**Timing note:** Rubin will resurvey this sky far deeper on a moving-object-optimised cadence. Archival
DECam *discovery* has a closing window for anything Rubin will trivially re-find. The durable niche is
**precovery** — extending arcs of Rubin discoveries backward into 2012–2019 DECam epochs. That value
*increases* as Rubin ramps.

---

## Sources

- DAD: `https://datalab.noirlab.edu/data/dad` · `https://datalab.noirlab.edu/dad.php`
- Data Lab TAP: `https://datalab.noirlab.edu/tap` · client `https://github.com/astro-datalab/datalab`
- NOIRLab Astro Data Archive: `https://astroarchive.noirlab.edu/` · API `https://astroarchive.noirlab.edu/api/docs/`
- SARC: `https://www.minorplanetcenter.net/mpcops/documentation/sarc/`
- Program codes policy (**changing**): `https://www.minorplanetcenter.net/mpcops/documentation/program-codes-policy/`
- MPC solicited backlog: `https://www.minorplanetcenter.net/mpcops/orbits/no-orbits-astrometry/`
- ADES: `https://minorplanetcenter.net/iau/info/ADES.html` · `https://github.com/IAU-ADES/ADES-Master`
- NSC DR2 paper: `https://arxiv.org/abs/2011.08868` · THOR/NSC: `https://b612.ai/thor-nsc/`
- YOSO (proof new objects are still being found in DECam data, May 2026): `https://arxiv.org/abs/2605.06913`
