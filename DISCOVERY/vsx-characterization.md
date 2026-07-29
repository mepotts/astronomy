# VSX characterization — periods for the 5.47 million variables nobody measured

**One-liner:** Bulk *discovery* of variable stars is over, but **53% of VSX has no period recorded at all**
and 2.35 million entries carry placeholder classifications. Measuring those is explicitly AAVSO-sanctioned
work, needs no new discovery, and converts into citable papers.

**Official recognition: WEAK.** VSX has a public `Discoverer` field and you may coin your own acronym, but
AAVSO states verbatim: *"As opposed to comet or asteroid discovery, you will get little or no credit for
discovering a new variable star. It is pure science and the willingness to contribute to the community."*
Permanent designations are assigned by **GCVS** (Moscow), not by you. **The paper is the credit, not the
VSX row.**

**Scores (U/B/E):** U **2/5** (the work is sanctioned and published, not hidden) · B **5/5** (pure
time-series analysis on open light curves) · E **2/5** — honest score, given the credit policy

**Status:** proposed — **lowest priority of the eight; best as a skills-builder**

**Cost to operate: $0**

---

## The measured opportunity

VSX holds **10,304,607 entries [measured 2026-07-28]** — but **78% (8,016,792) were dumped in by Gaia DR3
alone**. Anyone planning to "find lots of new eclipsing binaries in ZTF" is ~4 years late.

What remains, all live-measured:

| Gap | Count |
|---|---|
| **No period recorded at all** | **5,470,632 (53%)** |
| Typed `ROT` with no period | 1,809,758 |
| Bare `VAR` or `MISC` | 337,413 |
| Type `L` (irregular, catch-all) | 1,604,628 |

AAVSO turns this into seven named projects at **`https://www.aavso.org/vsx-data-mining`** — find periods
for periodless `EA`; reclassify `L`/`SIN`/`VAR`; check "not checked" flags; improve novice discoveries;
the KELT false-positive project.

**Genuinely open niches for *new* objects:** outburst classes that periodogram-ML misses (the most prolific
individual acronym, MGAB with 3,516 entries, skews `UG` dwarf novae, `NL/VY`, `UV` flares, `YSO`) ·
**blend resolution** (deciding *which* star in a blend varies — Gaia at 0.7″ can now adjudicate what
TESS at ~120″ and SuperWASP at ~60″ cannot) · **cross-survey synthesis over a 25-year baseline** (nothing
automatically joins ASAS-SN + ZTF + ATLAS + CRTS + SuperWASP + NSVS + TESS) · southern sky and Galactic
plane.

---

## ⚠️ Three constraints that shape everything

1. **5 submissions per week** reviewed per user/group. Drafts auto-deleted after 60 days; you must have
   <5 drafts before revising another object. **Volume via the web form is deliberately throttled.**
2. **Moderation is essentially one person.** Sebastián Otero, 2026-07-27: *"moderation is mostly a one
   staff member task at this time, so reviewing submissions may take several weeks if the queue grows too
   long, which is the case now."*
3. **AAVSO publicly warned about AI-assisted submissions on 2026-07-27**: *"The use of AI to perform the
   analysis, without properly completing the VSX fields as specified in our supporting material, is causing
   a lot of delays… No matter how good you think AI might be, the VSX guidelines should be followed."*
   Mandatory fields, stricter filters, and a training sandbox are planned.

The guidelines also state an explicit **double standard**: *"we are more critical of data-mined submissions
because we expect the submitter to do some work, such as period analysis, rather than just regurgitating
information already available from a given survey's site."*

**Treat constraint 3 as the binding one.** Given how you'd naturally approach this, the failure mode is
submitting technically-correct AI output that ignores the house style and jams a one-person queue. **The
sanctioned high-volume route is not the web form — it is a paper plus a bulk import** by emailing
`vsx@aavso.org`.

---

## Data access

| Survey | Access | Range |
|---|---|---|
| **ASAS-SN Sky Patrol** | `http://asas-sn.ifa.hawaii.edu/skypatrol/` (**HTTP only**) · `pip install skypatrol` (**not `pyasassn`**, stale 2022) | **109,300,848 light curves**, no auth — docs claiming a token is needed are stale |
| **ZTF** | `https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE+RA+DEC+RAD&BAD_CATFLAGS_MASK=32768&FORMAT=csv` | DR24 (2026-01-22); **use `catflag 0` only** |
| **ATLAS** | `https://fallingstar-data.com/forcedphot/` | Free registration; forced photometry at arbitrary positions |
| **TESS** | MAST / TESSCut / `lightkurve` 2.6.0 | ⚠️ TESSCut cutout area capped at **10,000 px** |
| CRTS | `http://nesssi.cacr.caltech.edu/DataRelease/` (**HTTP only**) | CSDR3; date is MJD |
| SuperWASP | `https://wasp.cerit-sc.cz/` | **17,960,328 objects**, no registration |
| VSX bulk | VizieR `B/vsx/vsx` | AAVSO's **own** recommendation for bulk use, over hammering the API |

⚠️ **VSX API gotchas for any client you write:** returns **HTTP 200 with an empty array** for not-found;
returns **XML** unless you pass `format=json`; and its AWS WAF signals a CAPTCHA block with **HTTP 405 +
`x-amzn-waf-action: captcha`**, not 429.

**Period-finding:** `astropy.timeseries.LombScargle` / `LombScargleMultiband` / `BoxLeastSquares`. Install
**`nifty-ls`** and pass `method="fastnifty"` — **~11× faster than astropy on CPU, ~200× on GPU**, and ~6
orders of magnitude more accurate than astropy defaults. (`gatspy` is dead since 2016; `cuvarbase` is
aging — prefer nifty-ls.)

---

## Milestones

**M0 — read the manual, then mirror an approved submission.** Read `https://vsx.aavso.org/_images/Manual.pdf`
and the guidelines. Take an **already-approved** submission (`BMAM-V930`, `MNO 3`) and reproduce it
field-for-field from raw survey data. *If your output doesn't match the house style, do not spend one of
your five weekly slots.*

**M1 — characterization at scale, not discovery.** Pick one AAVSO data-mining project. Periods for
periodless entries is the obvious start: unlimited supply, zero competition, explicitly requested.

**M2 — cross-survey synthesis.** The 25-year baseline nobody assembles. This is where blend resolution,
long-period variables, eclipse-timing variations and Blazhko modulation live. (Cf. Donev & Ivezić,
arXiv:2504.05434 — a live 2025 research direction on purely archival data.)

**M3 — publish, then bulk-import.** **OEJV** (`https://oejv.physics.muni.cz/`, issue #275 June 2026,
ADS-indexed, open to anyone — ⚠️ the old `var.astro.cz/oejv/` URL is frozen at issue #204 and looks dead
but the journal moved), **JAAVSO**, or **Peremennye Zvezdy**. Then email `vsx@aavso.org` for bulk import.

**M4 — Gaia DR4, 2 December 2026.** A dateable, first-look window on new epoch photometry for ~2B sources.
A pipeline that is already validated on DR3-era data gets first crack. **This is the one time-sensitive
element of this pathway**, and it links directly to [IDEAS/gaia-dr4-diff-auditor](../IDEAS/gaia-dr4-diff-auditor.md).

---

## Honest verdict

Do this **if** you want to learn time-series analysis and submission discipline on low-stakes ground, or
**if** you want to be ready for Gaia DR4. Do **not** do this expecting recognition — AAVSO tells you
plainly in writing that you won't get much. The four official-designation pathways
([itf-linker](itf-linker.md), [tns-alert-miner](tns-alert-miner.md), [plate-archaeology](plate-archaeology.md),
[coronagraph-comets](coronagraph-comets.md)) all pay better for comparable effort.

---

## Sources

- VSX: `https://vsx.aavso.org/` · manual `/_images/Manual.pdf` · guidelines `?view=about.notice` ·
  **data-mining projects `https://www.aavso.org/vsx-data-mining`**
- Bulk import: `vsx@aavso.org` · forums `https://forums.aavso.org/`
- GCVS: `http://www.sai.msu.su/gcvs/` (HTTP only) — GCVS 5.1, Name-List 88, July 2026
- OEJV: `https://oejv.physics.muni.cz/` · JAAVSO: `https://apps.aavso.org/jaavso/`
- nifty-ls: published in **RNAAS** (Oct 2024) — itself a template for this repo's output
