# M5-writeup — the fader census turned into a draft, and every number in it re-derived

*2026-08-18. Labelled **M5-writeup** so it does not collide with the classifier-rebase **M5**
(thin-slice dossier CLI), which is still queued behind Matthew's acceptance of the M4 §2.4
pivot — see root [`../STATUS.md`](../STATUS.md) ("eROSITA M5 (classifier thin slice) stays
queued"). Scripts: [`scripts/m5w_audit.py`](scripts/m5w_audit.py),
[`scripts/m5w_faint_validation.py`](scripts/m5w_faint_validation.py),
[`scripts/m5w_figure.py`](scripts/m5w_figure.py). Deliverables:
[`draft-rnaas-vanished-census.md`](draft-rnaas-vanished-census.md),
[`writeup-audit.md`](writeup-audit.md). Numbers computed here are marked **[computed]**;
external claims carry a source URL or the mark UNSOURCED. Negative results are results.*

**Hard rules honoured**: nothing submitted anywhere, no accounts created, no commits (the
orchestrator's job). **J0944 stays fenced** — it is a *riser*, so it has no place in a fader
census, and the draft does not name it, cite it, or use any of its numbers.

---

## 1. What this milestone did

Three things, in this order — because the second changed what the third could say.

1. **Prior art, adversarially** (§4). A dedicated sweep of arXiv, ADS, the DR2 release pages
   and the DR1-era comparators, briefed to *find the paper that kills this*.
2. **Audit** (§5, full table in [`writeup-audit.md`](writeup-audit.md)). Every headline number
   in M1–M4 re-derived from committed artifacts; every external value checked against its
   actual source. 107 quantities: **93 VERIFIED, 14 CORRECTED, 0 NOT-RE-DERIVABLE**, plus one
   number found **UNSOURCED** and dropped. The audit also exposed an untested assumption in
   the census method, which was then measured (§3.2).
3. **Draft** (§3), written to the audited numbers only.

## 2. Venue decision: **one RNAAS note**, not a short paper

**Recommendation: Research Notes of the AAS.** The material is one clean measurement with one
decisive figure and no confirmed individual object — an A&A/MNRAS-shaped paper could only
reach length by padding a 261-source census with per-object dossiers that no follow-up
supports, and every candidate that would carry such a paper is either fenced (J0944) or
explicitly unconfirmed. RNAAS is also the correct *register*: this is a short, useful,
partly-negative result that changes how other people should read a catalogue they are using
right now, which is exactly what the venue exists for.

**Limits verified 2026-08-18** at <https://journals.aas.org/research-notes/> (not taken from
memory): *"1,500 words or fewer"*; *"no more than a single figure or table (but not both)"*;
abstract required since 2020-05-01; references permitted; *"non-peer reviewed"* and
*"moderated but not edited"*. The draft uses **one figure, no table**, and runs **1,376
words** including abstract, figure caption and data-availability statement **[computed]** —
124 words of headroom.

The LMC null and the OGLE scoping law are a *second* independent result with a different
audience. They are drafted as **companion note B** at the foot of the draft file rather than
diluted into the census note. Taking both, one, or neither is Matthew's call.

## 3. The draft

[`draft-rnaas-vanished-census.md`](draft-rnaas-vanished-census.md) — **DRAFT — NOT SUBMITTED**,
author and affiliation as placeholders (AAS accepts "Independent Researcher").

### 3.1 Headline claim, one sentence

> Of the 261 bright (DET_LIKE_0 ≥ 30) eRASS1 sources absent from the eROSITA DR2 catalogue,
> **57% still have flux at their position and are catalogue artifacts, 41% sit on demonstrably
> blank sky and are real faders** — so the DR2 release paper's working assumption that
> unmatched implies spurious breaks down at the bright end, and it breaks down more the
> brighter the source.

### 3.2 The measurement this milestone added

The audit asked a question M1–M4 had not: the census calls a source a fader when the DR2
upper-limit server returns presence *P* = UL_B/UL_S ≤ 1.5, but that threshold was calibrated
on **25 steady sources selected at ≥ 20σ** — far brighter than the faders themselves (median
eRASS1 flux 6.8 × 10⁻¹⁴ erg cm⁻² s⁻¹, median DET_LIKE_0 = 40). If *P* stopped discriminating
down there, the census would be measuring detectability, not variability.

[`scripts/m5w_faint_validation.py`](scripts/m5w_faint_validation.py) settles it with **60
steady sources drawn to match the faders in both eRASS1 flux and DET_LIKE_0**, queried at the
same service (one anonymous POST; no account, nothing submitted) [all computed →
[`out/m5w_faint_validation.csv`](out/m5w_faint_validation.csv)]:

| population | n | presence *P* | in the fader class (*P* ≤ 1.5)? |
|---|---|---|---|
| fade candidates | 107 | 1.00 – **1.49** (median 1.04) | all, by construction |
| steady flux-matched controls | 60 | **2.03** – 3.78 (median 2.60) | **0 of 60** |

**The populations are disjoint**, with the adopted cut sitting inside the empty interval
between them: the threshold is not tuned, the data put a gap there. False-positive rate
< 4.9% (95% one-sided) → **fewer than 6 of the 107 faders can be sources that are still
there**. This is the strongest result in the note and it did not exist before this milestone.

### 3.3 Figure

[`out/m5w_vanished_census.png`](out/m5w_vanished_census.png) (+ `.pdf`), generated by
[`scripts/m5w_figure.py`](scripts/m5w_figure.py) from committed `out/` CSVs only. One figure,
two panels: (a) the presence-ratio distribution of the 261 with the 60-source control
overlaid, showing the gap; (b) presence against eRASS1 detection likelihood, showing that
every dropout brighter than DET_LIKE_0 = 242 is an artifact.

### 3.4 Limitations the draft carries (mission-required, all present)

Epoch-space reconstruction (the stacked ratio compresses fades to ≳ 1/3; the epoch
reconstruction assumes 030 preserved the eRASS1 counts, which fails for the brightest
transients — so **no amplitude is claimed anywhere**); the threshold band (now **+17/−8**,
§5.1); footprint (western Galactic hemisphere only); depth (DET_LIKE_0 ≥ 30, well above the
~14%-spurious catalogue threshold — the note explicitly concedes that the release paper's
spurious framing is probably right at faint likelihoods); the upper limits being cumulative
over eRASS:3 only, so "faded" means stack-averaged and a fade-plus-rebrightening inside the
window is not distinguished; the positional-only cross-walk making 107 a **lower** bound; no
individual fader confirmed by follow-up; and the consortium holding five epochs and able to
supersede the whole axis at will.

## 4. Prior-art verdict: **NOT SCOOPED** — but the release paper pre-empts the *premise*

Swept 2026-08-18: arXiv API `all:eROSITA` (complete coverage 2026-07-28 → 2026-08-17),
`abs:eRASS`, `abs:"eRASS:3"`, ADS, plus the DR2 catalogues/FAQ/upper-limits/publications pages.

**Nobody has published an eRASS1↔eRASS:3 variability, transient, or vanishing-source census —
ever, and nothing since 2026-07-31.** Fifteen DR2-based papers appeared in the release window
(AGN XLF, optical loading, three CV catalogues, cluster and SNR work, Gammapy tooling); none
touches inter-release variability. There is **no DR2 variability VAC** and none is announced
([Catalogues_dr2](https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/) ships
exactly one Galactic VAC, the CV catalogue).

**But — the one thing that must be cited, and now is.** Ramos-Ceja et al. 2026 **§5.1**,
"An independent assessment of spurious source contamination in eRASS1", already runs the
DR1↔DR2 match through `UID_DR1` and publishes the unmatched fractions (Fig. 10 caption,
verbatim): *"While in the entire catalogue the fraction of point sources not matched to
eRASS:3 is about 21%, this drops to about 3.5% for DET_LIKE>10 and 0.15% for DET_LIKE>50."*
It interprets **every** non-match as spurious and **never mentions variability**. That is not
a scoop — it is the thing this note tests — but uncited it would be fatal in review. The draft
now opens on it and frames the census as the measurement of where that assumption fails.
(It also means M1's "12.6% spurious + 8.4% variability/Poisson" gloss was never in the paper:
UNSOURCED, dropped — see [`writeup-audit.md`](writeup-audit.md) §1.5.)

**Precisely what is new versus the named comparators:**

| prior work | what it did | what it did **not** do |
|---|---|---|
| **Ramos-Ceja et al. 2026 §5.1** (A&A 712, A171; arXiv:2607.27772) | the same DR1↔DR2 cross-walk; unmatched **fractions** at three likelihood cuts | no variability allowance, no upper limits, no artifact-vs-real forensics, no absolute bright-source counts, and **no flux comparison between matched eRASS1/eRASS:3 sources** — so the 2% scale offset appears unpublished |
| **Boller et al. 2025** (A&A 700, A61; arXiv:2401.17280) — *note: 2025, not 2024* | *intra*-eRASS1 variability on the ~4 h eROday cadence; 128,669 sources, 1,709 variable | no inter-survey comparison at all |
| **eRO-ExTra**, Grotova et al. 2025 (A&A 693, A62) | 304 extragalactic non-AGN transients, **eRASS1↔eRASS2**, LS10 footprint | no eRASS:3/DR2; no Galactic sources; no non-detection census |
| **MKM** = Maan, Katira & Mooley 2025 (MNRAS staf1752; arXiv:2510.12982) | 738 Galactic transients across 2RXS↔eRASS1, ~30 yr baseline | its "true transients" **appear** in eRASS1; it never runs the reverse direction, never uses eRASS2/3, never uses upper limits |
| Bogensberger et al. 2024 (A&A 687, A37) | eROSITA SEP field, ~4 h cadence, 3° radius | small-area, not all-sky, not a vanishing census |
| Ramos-Ceja et al. 2026 §5.2 | 2RXS sources unmatched to eRASS:3 | different epoch pair; spuriousness framing; ⚠ its numbers could not be extracted and are **UNSOURCED** here — read §5.2 directly before writing about ROSAT analogues |
| VASCO, Villarroel et al. 2020 (AJ 159, 8) | the canonical "vanishing sources" survey | optical, USNO-B1.0 vs Pan-STARRS |
| Kaltenbrunner et al. 2026 (A&A 707, A225) | 53 LMC HMXBs, eRASS1–4 products, OGLE light curves used directly, Gaia **eDR3** CMD screen | no OCVS/XROM cross-match, no fade census — the companion note credits the CMD screen as their method applied to a new sample |

**Genuinely new here**: the 2% DR1↔DR2 flux scale offset; the vanished-source census with a
forensic artifact/fader split; upper-limit calibration of non-detections in a DR1→DR2 fade
census; the fader demographics; the faint-end validation of §3.2; the LMC 0/25 null; and the
OGLE scoping law. **Not new**: the cross-walk itself, the `UID_DR1` column, the
unmatched⇒spurious idea, cross-epoch transient censuses in general, and the "vanishing
sources" framing.

**Residual risk, stated plainly**: the consortium holds five eRASS epochs and can run this
internally at any time. The novelty is *access-based*, not idea-based, and the draft leans on
the public-data framing rather than claiming priority. DR3 is not due until H2 2028.

## 5. Audit summary

Full table: [`writeup-audit.md`](writeup-audit.md); machine-readable
[`out/m5w_audit.csv`](out/m5w_audit.csv). **107 quantities: 93 VERIFIED, 14 CORRECTED, 0
NOT-RE-DERIVABLE.** Nothing that failed re-derivation entered the draft.

The corrections that changed the science:

### 5.1 The threshold band is **+17/−8**, not the +35/−12 M2 published

Replaying M2's own classification tree at presence cuts of 1.3 and 2.0 gives 99 and 124
faders, not 95 and 142 **[computed]**. M2's ±numbers counted every row in the presence
interval, but the tree tests split/halo **before** the presence branch and the 40″ PSF
confuser **after** it, so 18 of the "+35" and 4 of the "−12" never change class. The census
systematic is *smaller and tighter* than M2 claimed. The full cut→count curve (1.2 → 94, 1.3 →
99, 1.4 → 103, 1.5 → 107, 1.75 → 119, 2.0 → 124, 2.5 → 137) is in the audit.

### 5.2 One of the 25 UL calibrators is degenerate, and the "median" is a mean

`3eRASS J114550.9-552043` returned `UL_S = inf` → presence 0.0, so M2's "steady calibrators
are all ≫1" holds for 24 of 25 (valid range 5.68–13.87) **[computed]**. Separately, M2's
"calibration median 1.13 ± 0.07" is the **mean ± sd**; the median is 1.14. Neither matters
downstream, because §3.2's 60-source flux-matched control supersedes the whole 25-source
calibration — but both were stated wrongly and are now stated right.

### 5.3 `fade_frac` never was a fade diagnostic

Re-derivation shows the faders' `fade_frac` (median 1.25) barely differs from the steady
calibrators' (1.13) **[computed]** — the metric is background-dominated at these fluxes and
does not separate the populations. Only `presence` does. M2 presented both as diagnostics; the
draft uses only `presence`, and the audit records why.

### 5.4 Smaller corrections carried into the draft

Scale offset 2.06% (quoted as ~2%); exposure ratio t₃/t₁ = **2.84** over all clean pairs, not
2.9; nearest XROM object **49.8′** and nearest known LMC HMXB **12.9′**, both of which M4
rounded *up* into "≥50′" and "≥13′"; the "stellar fader" count is definition-dependent
(23 at |W1−W2| < 0.3, 25 at < 0.5) and the draft now states the cut; and M1's eRASS:3 span is
internally inconsistent — 2019-12-12 → 2021-06-16 is 552 days, not the 556 quoted — so the
draft gives the epoch range only and never the span.

### 5.5 What verified cleanly

The load-bearing numbers all held: 632,668 clean pairs; 1,975,540 / 930,203 catalogue rows;
1,911,744 point + 63,796 extended (matching the release paper's own Table 15); zero epoch
columns among DR2's 250; 118,253 bright clean DR1 point sources; 261 vanished (0.22%);
148/107/6; the 85/36/25 artifact sub-modes; 0.09% genuine switch-off rate; the whole LMC
sub-study including 0/25 in four catalogues, 0.19 chance matches from 400 control positions,
24/25 with no Be-donor-capable star, the 217,725-variable OCVS pool, and the 886-day OGLE-IV
dark interval; and the 104/123/153/1 verdict tallies.

## 6. What Matthew must decide before this could ever be submitted

Nothing here is actionable without him. In rough order of blocking-ness:

1. **Whether to submit at all**, and under what name and affiliation. AAS accepts
   "Independent Researcher"; an ORCID is needed. Sole authorship on public-catalogue work is
   normal for RNAAS.
2. **A citable data archive.** The note's data-availability statement needs a DOI (Zenodo or
   equivalent) for the 261-row forensic table, the 60-source control, and the scripts. The
   repo is public but a GitHub URL is not a citable archive. *This is the same open item as
   itf-linker C5.* Note the archive should be scoped to the census products — the wider `out/`
   tree contains the fenced J0944 material.
3. **Confirm the DR2 journal reference against ADS.** A&A 712, A171 comes from the consortium
   publication list; the arXiv page carries no journal-ref, and aanda.org blocks automated
   access. One manual lookup.
4. **Read §5.2 of the release paper directly** if he wants the ROSAT analogue mentioned — the
   sweep could not extract its numbers and they are UNSOURCED here. The draft as written does
   not depend on it.
5. **Companion note B, if he wants it**: it additionally requires contacting the XROM team
   (their page asks to be contacted before publication use — **not done**), and its OGLE gap
   dates must stay worded as *measured by us*, since 2022-08-16 is unsourced in the published
   record.
6. **The J0944 Swift ToO gate is unchanged and untouched** by this milestone
   ([`J0944-decision-package.md`](J0944-decision-package.md) §9, DRAFT — his account, his
   call). It is deliberately absent from the draft.

## 7. Recommended next

1. **Matthew's calls**: the two gates above (submission decision + J0944 ToO). Everything
   public is exhausted on both.
2. **Classifier rebase M5 (thin slice)** — still queued behind acceptance of the M4 §2.4
   pivot; unaffected by this milestone.
3. **W4 (Gaia DR4 NSS × DR2, 2026-12-02)** — on schedule, ingest layer unchanged; still the
   calendar-fixed priority.
4. **If the note is submitted**, the natural follow-up is the *riser* side of the same
   cross-walk (286 new-bright sources, `out/m2_new_bright_full.csv`) with the same
   upper-limit forensics run in reverse — but that is where J0944 lives, so it stays behind
   his gate.

## 8. Files

- [`draft-rnaas-vanished-census.md`](draft-rnaas-vanished-census.md) — the RNAAS draft
  (1,376 words) + companion note B, both DRAFT — NOT SUBMITTED
- [`writeup-audit.md`](writeup-audit.md) — the full number → source → verdict table
- `out/m5w_audit.csv` — 107 audited quantities, machine-readable
- `out/m5w_faint_validation.csv` / `.json` — the 60-source faint-end control (§3.2)
- `out/m5w_vanished_census.png` / `.pdf` — Figure 1
- `scripts/m5w_audit.py` — re-derives every number in one command
- `scripts/m5w_faint_validation.py` — the control experiment (one anonymous POST, cached)
- `scripts/m5w_figure.py` — the figure, from committed `out/` CSVs only
