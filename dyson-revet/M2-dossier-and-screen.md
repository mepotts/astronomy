# M2 — retire D, assemble the candidate-I dossier, draft the unit-error note, open the full W4 screen

*2026-08-18 · follows [M1](M1-reproduce-and-vet.md), executing M1 §6's own recommendations.
Every externally-sourced number carries its source; anything unsourced is marked UNSOURCED.
**Nothing in this milestone has been submitted, posted, or sent anywhere.** Candidate-level claims
and the draft note are Matthew-gated.*

---

## 0. Executive summary

1. **D is formally retired** (§1). Its status is now unambiguous in the README, `STATUS.md`, and an
   append-only dated annotation on M1 — contamination-confirmed by JWST (Hephaistos IV), with M1's
   own centroid measurements kept as the *calibration* of why archival vetting graded it "weak":
   a real 1.0″ contaminant moved the AllWISE centroid by only 0.5–1.4″.
2. **The candidate-I dossier is written** ([`I-dossier.md`](I-dossier.md)) and carries **five new
   findings M1 did not have, all pointing the same way — the excess is at the instrument's floor**:
   - **The W3 excess does not survive the earlier WISE reduction.** In the WISE All-Sky Release the
     same photons give `ph_qual` = **AAU**C — W3 flagged **'U'**, a non-detection at S/N 1.3, with a
     null uncertainty. AllWISE promoted it to 'C' at S/N 2.4. One of the two points carrying the
     entire candidacy is release-dependent.
   - **Nothing was ever detected in a single exposure**: AllWISE reports `w3nm = 0`, `w4nm = 1`
     against 11 profile-fit measurements per band. The "detection" exists only in the coadd.
   - **Both bands are sub-5σ against WISE's own sensitivity**, and the target is on the ecliptic
     (β = −6.58°) — the survey's shallowest regime, where the 5σ limits are 0.86 mJy (W3) and
     5.4 mJy (W4). Candidate I is at 0.44× and 0.62× of those.
   - **The "detections" sit inside the 95% upper limits of their own neighbours.** All nine AllWISE
     sources within 60″ have W3 and W4 `ph_qual` = 'U'; their limits are 0.31–0.58 mJy (W3) and
     2.07–3.79 mJy (W4), bracketing candidate I's 0.375 and 3.36 mJy. **The nearest neighbour's W4
     upper limit is brighter than candidate I's detection.**
   - **The independent aperture photometry never detected W4** (`w4flg = 32` = "the magnitude is a
     95% confidence upper limit"; in the All-Sky release `w3flg = w4flg = 32`). Only the profile fit
     ever produced a detection.
   Plus: the excess restated in **flux** rather than magnitudes (W3 **1.3σ**, W4 **3.3σ**, joint
   **3.5σ** before trials — the 4.5-mag W1−W4 "12σ colour excess" is a 3.3σ flux measurement);
   a corrected reading of the centroid instability (W4 genuinely flips by 224°, W3 does **not** flip
   — M1 overstated this); the 6.8″ NE red source demoted to non-evidence with arithmetic; and a
   finder chart (`out/m2_I_finder.png`).
3. **The Ren et al. 2024 unit-error note is drafted and NOT submitted**
   ([`note-ren24-unit-error-DRAFT.md`](note-ren24-unit-error-DRAFT.md)), 1,048 words against RNAAS's
   1,500-word inclusive limit, one table and no figure. **Prior art exists and is credited**:
   Blain (2024, arXiv:2409.11447) footnote 6 already flagged the conversion with "(sic)". What is
   still missing from the record — and what the draft supplies — is the magnitude and nature of the
   slip and the fact that it *inverts* the paper's conclusion. No erratum exists; the sentence
   stands in the version of record, including its abstract.
4. **A third candidate has already been observed by JWST and is unpublished.** MAST shows
   **GO 7199** (Cycle 4, PI Zackrisson, 13.5 h, Completed) has **three** targets, not two: Object_D
   and Object_E — both killed in Hephaistos IV — and **Object_A at 191.30390, −26.86784, which
   matches candidate A to 0.95″** and appears nowhere in that paper. It was observed **14 July
   2026**, four days after Hephaistos IV appeared. The JWST-vetted sample will shortly be 3, not 2.
   *This should be watched; it moves the class prior without anyone doing anything, and it changes
   the timing calculus for any proposal on candidate I.*
5. **W4 is underway and its route has been corrected.** M1's cost plan assumed ~24 anonymous **async**
   ESA strip jobs; **anonymous async is broken** — every job returned HTTP 500 at creation, confirmed
   by raw POST. The screen now runs on **sync with adaptive tiling**, checkpointed per tile and
   resumable with one command. As of writing: **4 of 192 tiles complete, 752 deg² (1.82% of sky), 6,422 W3+W4-detected rows on disk (8.5 deg⁻² ⇒ ~352k sky-wide vs the paper's ~3.2 × 10⁵), ~7 h projected to complete**. Section 4 has the funnel and the
   resume instructions.
6. **New W4 finding — the γ floor is the funnel's selectivity knob, and it is worth ~9×.** Identical
   local pipeline, identical 1,762 fitted stars from the 752 deg² harvested so far:

   | grid | RMSE ≤ 0.2 | + C5 extras | + C6 S/N ≥ 3.5 |
   |---|---|---|---|
   | **γ ≥ 0.10** — the paper's *stated* initial grid (Suazo+24 §2.2) | **97** | **84** | **5** |
   | γ ≥ 0.01 — the floor needed to admit their own candidate F (γ = 0.03) | 850 | 596 | 25 |
   | *paper's published rates, scaled to 752 deg²* | *205* | *94* | *6.7* |

   At the stated grid the pre-visual survivor count (5) is Poisson-consistent with the paper's
   368 sky-wide (6.7 expected here); at γ ≥ 0.01 it is 25, a **3.7× overproduction**, and the RMSE
   stage overshoots the paper's *whole-sample* expectation by 4.1× **from only a third of the
   stars** (see §4.3 for that caveat). M1 found the γ ≥ 0.1 / candidate-F inconsistency; M2 measures
   what it costs. **The screen runs at γ ≥ 0.10**, with γ ≥ 0.01 reported as a sensitivity.

---

## 1. D, retired formally

**Status: CONTAMINATION-CONFIRMED. Closed. No further work.**

Source of the kill: Project Hephaistos IV, Zackrisson et al. 2026
([arXiv:2607.09460](https://arxiv.org/abs/2607.09460), 10 Jul 2026), JWST GO 7199 — MIRI imaging +
MRS attribute D's mid-IR excess to an IR-bright background galaxy at z ≈ 0.9, ~1″ from the star,
point-like, with an AGN-indicating MIRI spectrum, a Hot-DOG-like SED and a ~90 K hot-dust component.
The M dwarf is photospheric in F560W/F1000W/F1500W (the star supplies ≈ 80/10/2% of the MIRI flux).
The same paper also kills candidate **E** (z ≈ 0.4 dusty-starburst-like galaxy, ~1″).

**Where the retirement is now recorded** (append-only, dated, history preserved):

| Location | What changed |
|---|---|
| [`README.md`](README.md) | The "D & I still clean" premise line replaced by a dated **Premise correction** block that says where the original phrasing came from (Ren et al. 2026, submitted ~3 Jul 2026), what superseded it (Heph IV, 10 Jul 2026), and what it leaves standing (I, verdict INDETERMINATE — *not* clean) |
| [`M1-reproduce-and-vet.md`](M1-reproduce-and-vet.md) | Dated annotation block at the head (M1 is annotated, never revised) + a **"Retired 2026-08-18"** note appended directly under the §3.2 verdict |
| [`STATUS.md`](STATUS.md) | M2 entry, newest-first |
| [`I-dossier.md`](I-dossier.md) §7 | D used as the *class prior*, not as a candidate |

**The independent contribution — why archival methods graded D "weak", demonstrated rather than
asserted.** This is the part worth keeping, and it is M1's measurement, not Hephaistos IV's:

| | AllWISE | unWISE | Ren+26 published |
|---|---|---|---|
| D, W1 offset | 0.15″ ± 0.04 | — | 0.53″ |
| D, W2 offset | 0.23″ ± 0.07 | — | 0.46″ |
| D, W3 offset | 1.41″ ± 0.21 | 1.07″ ± 0.22 | 0.75″ ± 0.22 |
| D, W4 offset | 2.55″ ± 0.50 | 2.15″ ± 0.97 | 1.80″ ± 1.80 |

A **JWST-confirmed real contaminant at 1.0″** produced AllWISE centroid offsets of only ~0.5–1.4″ —
below any defensible threshold against the ~0.2–0.5″ control-star floor, and the smallest offsets of
the whole ten-object set. Hephaistos IV §5.2 says it outright: the centroid method "provided no
evidence for interloper contamination in the case of candidate D."

Two corroborating measurements from M1, both independent of Hephaistos IV:

- **The contaminant is invisible to the deepest wide-field optical survey.** My Legacy DR10 pull at
  D's position finds nothing at ~1″; the nearest catalogued source is the known REX galaxy at 2.97″
  SE. It took MIRI.
- **An SED fit cannot tell the two apart.** The photosphere + excess decomposition of D's 147
  archival points from 26 catalogues gives T = 184 K, γ = 0.17, RMSE 0.135 — a perfectly good
  "Dyson sphere" fit to what JWST shows is a z ≈ 0.9 AGN. **Only resolution discriminates.**

**Therefore, as a standing project law:** *centroid vetting has a hard sensitivity floor at roughly
1–2″ separations; blends inside it pass every archival test.* Every W4 verdict must state this floor
per object. D is not a loss — it is the calibration that makes the rest of the screen honest.

---

## 2. The candidate-I dossier

Deliverable: **[`I-dossier.md`](I-dossier.md)** (Matthew-gated). Headline:

> The last Dyson-sphere candidate standing is standing only because nothing in the archive can knock
> it down: its entire infrared excess is two WISE measurements at S/N 2.4 and 3.3 — and the 12 µm one
> is a formal non-detection in the earlier reduction of the same photons — so candidate I is not an
> unrefuted candidate, it is an unvettable one, and about half an hour of JWST/MIRI imaging would
> settle it either way.

What is new in M2 versus M1 (M1's material is in the dossier too, so it stands alone):

**(a) The excess, in flux instead of magnitudes** (`scripts/m2_i_excess.py`, `out/m2_I_excess.json`):

| band | S/N | f_obs (mJy) | f_phot (mJy) | f_excess (mJy) | excess significance |
|---|---|---|---|---|---|
| W2 | 35.0 | 0.854 | 0.836 | 0.018 | **0.5σ** (photospheric — the control) |
| W3 | 2.4 | 0.375 | 0.175 | 0.201 | **1.3σ** |
| W4 | 3.3 | 3.363 | 0.056 | 3.308 | **3.3σ** |

Joint 3.5σ, before trials. The W2 row is the important one: the same machinery finds *no* excess
where there should be none, so the W3/W4 numbers are not a template artefact.
*(A colour-sign bug was found and fixed in this calculation before it was used — the locus columns
are (W1 − W_n), so W_n = W1 − colour. The first run had the sign inverted and produced a spurious
8σ W2 "excess". Recorded because it is exactly the kind of error this project exists to catch.)*

**(b) The W3 excess is release-dependent.** WISE All-Sky Release (`allsky_4band_p3as_psd`, IRSA):
`ph_qual` = **AAUC**, W3 = 'U' — no detection, null uncertainty, S/N 1.3, quoted magnitude 12.015 as
an upper limit. AllWISE: `ph_qual` = **AACB**, W3 = 'C', S/N 2.4, 12.316 ± 0.448. W4 is consistent
between releases (8.594 ± 0.366 at S/N 3.0 vs 8.489 ± 0.326 at S/N 3.3). The two releases do not
contradict each other — the All-Sky upper limit (12.015) is *brighter* than the AllWISE detection and
does not even exclude the photosphere (13.15) — but at this flux level WISE's W3 answer depends on
the pipeline.

**(c) Single-exposure detections: `w3nm = 0`, `w4nm = 1`** against `w3m = w4m = 11` profile-fit
measurements. `nb = 1`, `na = 0` — a clean single-PSF fit, not a deblending outcome;
`w3rchi2 = 1.068`, `w4rchi2 = 1.103`.

**(d) No other facility has ever measured this position above 5 µm.** Zero rows in the Spitzer SEIP
source list (10″), AKARI IRC PSC (15″), IRAS PSC (60″).

**(e) The centroid instability, measured with position angles** — and M1 corrected:

| band | basis | offset | PA | aperture S/N |
|---|---|---|---|---|
| W3 | AllWISE | 2.64″ | 202° | 2.4 |
| W3 | unWISE | 4.29″ | 192° | 1.9 |
| W4 | AllWISE | 5.48″ | 345° | 5.2 |
| W4 | unWISE | 1.11″ | 121° | 2.3 |

**W4 genuinely flips — 224° of direction change and a 5× magnitude change. W3 does *not* flip**
(202° vs 192°); it changes magnitude by 62%. M1 §3.3 said both flip; that is corrected here and in
the annotation on M1. Either way the offsets are noise: at aperture S/N < 2.5 the centroid
uncertainty (1.15–1.43″) is comparable to the offset.

**(f) The 6.8″ NE red PSF source, demoted with arithmetic.** Its Tractor-forced W4 flux (3.72 mJy)
is a deblending split, and the noise on that split is visible in the same file — a third source 7.3″
SE is assigned **−1.42 mJy**. Its position angle (37°) does not match either W4 centroid (345° and
121°). And a source that red within 6.8″ is expected ~250 times over among 5 × 10⁶ stars. Not
evidence; worth one line in a proposal.

**(g) What would settle it, costed** — dossier §8. JWST/MIRI imaging, F2100W + a 10–13 µm anchor,
one visit, **≈1.2 h charged** (2100 s slew + 294 s guide-star acquisition + 16% observatory indirect
is the floor; science time is 14% of the charge). Predicted F2100W flux 3.36 mJy total, of which the
photosphere is 0.056 mJy — the excess *is* the source at 21 µm — against a 10σ/10 ks limit of
4.78 µJy, i.e. **711×** margin; even the bare photosphere reaches S/N 10 in ~73 s. MIRI's measured
on-orbit PSF FWHM is 0.685″ at F2100W and 0.356″ at F1000W against WISE's 12″ and 6.5″, so the ~1″
blends that killed D and E are trivially resolved. Exposure is set by overheads, not depth. All three possible outcomes (resolved contaminant / star-
centred excess / nothing there) are results; there is no wasted-observation branch. §9 records what
would **not** settle it: any ground-based mid-IR facility (the predicted fluxes are below N- and
Q-band limits), SPHEREx, deeper optical/NIR imaging (D's contaminant was invisible to Legacy DR10),
and any further WISE analysis.

---

## 3. The Ren et al. 2024 unit-error note (DRAFT, NOT SUBMITTED)

Deliverable: **[`note-ren24-unit-error-DRAFT.md`](note-ren24-unit-error-DRAFT.md)**. State: draft,
author/affiliation placeholders, **not submitted, not posted, not shown to anyone**.

**RNAAS limits, checked at source** (<https://journals.aas.org/research-note-preparation-guidelines/>,
2026-08-18 — note the URL in common circulation, `/research-notes-instructions/`, 404s):
"1,500 words or fewer, with no more than a single figure or table (but not both)"; "The 1,500 word
count limit includes title, headers, captions, and references with 150 words reserved for the
required abstract". The draft is **1,048 words** by that inclusive counting (abstract 135), **one
table, no figure**. RNAAS's stated scope explicitly includes "comments and clarifications, null
results"; it is not peer reviewed; each note gets a DOI and is indexed by ADS.

**The finding.** Ren, Garrett & Siemion (2024, RNAAS 8, 145, doi:10.3847/2515-5172/ad5017) write:
"Hot DOGs also have a surface density of approximately 1 per 31 square degrees (Assef et al. 2015),
which translates to about 9 × 10⁻⁶ per square arcsecond. This density is therefore sufficient to
explain the levels of contamination observed." The conversion is high by **3616×**:
1/31 deg⁻² = 2.49 × 10⁻⁹ arcsec⁻², and 9 × 10⁻⁶ is the per-square-**arcminute** value.

**The consequence** (`scripts/m2_note_table.py`, `out/m2_note_table.csv`; Poisson, ρπr², N = 5 × 10⁶):

| Population | ρ (deg⁻²) | N expected, r = 3.25″ | r = 1.0″ |
|---|---|---|---|
| Ren et al. 2024 **as printed** | 116.6 | **1493** | 141 |
| Assef et al. 2015 Hot DOGs, **converted correctly** | 0.0323 | **0.41** | 0.039 |
| Blain 2024 full WISE Hot DOG sample | 0.100 | 1.28 | 0.12 |
| Li et al. 2025 z < 0.5 Hot DOGs | 0.0024 | 0.031 | 0.0029 |
| **Suazo et al. 2024 faint red galaxies** (15000 sr⁻¹) | 4.57 | 58.5 | **5.5** |
| *required to produce all seven candidates* | *0.547 / 5.78* | *7* | *7* |

Catalogued Hot DOGs explain ~0.4 of the seven, not all of them. **But the conclusion survives through
a different population**: Suazo et al.'s own faint red-galaxy density (4.57 deg⁻²) predicts 5.5 blends
within 1″ against the 5.78 deg⁻² required — and JWST/MIRI then resolved exactly such ~1″ galaxies at
D and E. The corrected arithmetic is not bookkeeping: it points at a specific fainter population, and
that population is the one that was found.

**Prior art — checked properly, and it exists.** Blain (2024, arXiv:2409.11447) footnote 6:
"Ren, Garrett & Siemion 2024 quote 0.032 deg⁻² = 9 × 10⁻⁶ arcsec⁻² **(sic)**; however, the full
HotDOG catalogue is a little larger, with 2220 found over 70 per cent of the sky, yielding
0.1 deg⁻² = 7.7 × 10⁻⁹ arcsec⁻²." His conversion is correct. So the novelty is **partial**, the draft
credits Blain first and explicitly, and Matthew should weigh that before anything is submitted.

What is *not* in the literature anywhere I could find: the magnitude and nature of the slip; and the
fact that it **inverts** the conclusion — Zackrisson et al. (2026), using the same Assef et al. number
in the correct unit, get "fall short by several orders of magnitude" where Ren et al. got "sufficient".

**State of the record:** no erratum or corrigendum (Crossref record for the DOI has empty `update-to`
and empty `relation`; Oxford ORA record shows none); no v2 of arXiv:2405.14921; the sentence is
identical in preprint and version of record and appears **in the abstract**; no citing paper restates
the correction. Ren et al. (2025) and Ren et al. (2026) carry the *conclusion* forward while
attributing it to Blain's analysis rather than to their own density.

**Fairness.** This is a correction, not an attack, and the draft says so. Two of the three authors —
with Assef, whose catalogue supplied the number — are co-authors of the JWST paper that uses
0.032 deg⁻² correctly; the physical suggestion (red background galaxies) turned out to be right.

**Caveats that must be cleared before any submission** (recorded in the draft's working notes):
IOPscience is bot-blocked, so the live article page was never checked for a correction banner;
PubPeer returns 403, so a post-publication comment there would be invisible; NASA ADS was unreachable
(405/401), so the citing-paper list came from OpenAlex + Semantic Scholar + direct full-text reads and
may be incomplete. **All three need a manual browser check.**

---

## 4. W4 — the full re-screen

### 4.1 The route correction (a measured plan that had an unmeasured leg)

M1 §2.4/§5 costed W4 at 2–4 days via **~24 anonymous ESA async strip jobs**. That leg was never
exercised: M1 measured only the sync endpoint. On 2026-08-18 (`scripts/_w4_diag.py`):

| test | result |
|---|---|
| trivial sync (`SELECT TOP 5`) | **OK, 131 s** — the server is heavily loaded; M1 saw 23–116 s for far larger queries |
| trivial async via pyvo | **FAIL — HTTP 500** at job creation |
| raw POST to `/async` | **HTTP 500**, ESA "SERVICE ERROR" page |
| sync 6-table count, 28.8 deg² band | **OK, 146 s**, 255 rows |
| sync 3-table / 4-table counts, same band | **FAIL — HTTP 500 at 181 s** (a ~180 s server cap) |

So: **anonymous async is unavailable, and sync has a ~180 s hard cap with ~120 s of queue overhead.**
The plan is re-based on sync with **adaptive tiling** — start with tiles sized to fit inside the cap,
and halve any tile that fails.

### 4.2 What the screen does

`scripts/w4_screen.py`, three modes (`pull`, `status`, `select`).

**Server-side** (the only two cuts worth pushing there — together they shrink the payload ~15×):
C1 `r_med_geo < 300`, and C2a W3 **and** W4 have a measured profile-fit uncertainty (= AllWISE
ph_qual ≠ 'U'). The pull is a **6-table join** — `gaia_source` ⋈ `gaiaedr3_distance` ⋈
`allwise_best_neighbour` ⋈ `allwise_original_valid` ⋈ `tmass_psc_xsc_best_neighbour` ⋈
`tmass_original_valid` — which **deletes M1's chunked-PK-lookup stage entirely** (M1 planned ~10⁴
lookup queries for AllWISE + 2MASS photometry; at ~7 s each that was the dominant cost).

**Locally**, in the paper's Table 4 order: cc_flags, the star + Dyson-sphere RMSE ≤ 0.2 grid, Gvar
(from the screen's own flux-matched medians), RUWE, ext_flg, classprob, and S/N ≥ 3.5.
C5a (Hα) is deferred to the survivor list — it needs a PK lookup on `astrophysical_parameters` and
rejects a negligible fraction. **Open caveat carried from the dossier:** the sign convention of
`ew_espels_halpha` has not been verified against the Gaia DR3 documentation; this must be settled
before C5a is applied to the survivors.

**Robustness**, because this run will outlive several sessions:

- every tile is written to `data/w4/tiles/<id>.csv` the instant it lands, and `data/w4/manifest.json`
  is rewritten atomically — a session kill costs at most one tile;
- a failed tile is **retried** rather than split. This was itself measured: the ~181 s wall does
  **not** depend on tile size — 215, 107 and 54 deg² tiles all failed at 181.6 ± 0.3 s while 215 and
  107 deg² tiles succeeded at 93 s and 127 s — so it is queue/load, not compute, and halving a tile
  doubles the query count without improving the odds. (The first launch was configured to split;
  that cost ~4 wasted queries before the pattern was visible, and the driver was relaunched
  retry-heavy. Splitting survives as a last resort via `--min-area`.) A tile that exhausts its
  retries is recorded as `failed` with its area, so lost sky is auditable;
- an interrupted split can orphan sky (children are queued in memory before they are written to the
  manifest). `python scripts/w4_screen.py repair` finds every `split` tile without a complete set of
  done children and re-queues it whole; `select` de-duplicates on `source_id`, so the resulting
  parent/child overlap is harmless;
- tiles are issued in a **deterministic pseudo-random order** (seed 20260818) so that a *partial*
  screen is an unbiased sample of the sky in RA, dec and |b| — the funnel measured on whatever lands
  is directly comparable to the paper's all-sky rates, instead of being a polar cap.

### 4.3 The γ-floor finding — the funnel's selectivity knob

Identical local pipeline, identical 1,762 fitted stars (752 deg² harvested), only the model grid's
γ floor changed:

| grid | fitted | RMSE ≤ 0.2 | + C5 extras | + C6 S/N ≥ 3.5 |
|---|---|---|---|---|
| **γ ≥ 0.10 — the paper's stated initial grid** (Suazo+24 §2.2) | 1,762 | **97** (5.5%) | **84** | **5** |
| γ ≥ 0.01 — the floor needed to admit their own candidate F (γ = 0.03 ± 0.008) | 1,762 | 850 (48%) | 596 | 25 |
| *paper's published rates scaled to 752 deg²* | — | *205* | *94* | *6.7* |

M1 established that the paper's stated grid (γ ≥ 0.1) and its own candidate F (γ = 0.03, 9σ below the
floor) are incompatible. **M2 measures the cost: ~9× in survivor count at the RMSE gate and 3.7× in
pre-visual survivors.** With γ ≥ 0.01 a model can add a token excess and fit almost any photosphere —
the gate stops being a gate (48% pass rate against 5.5%).

**An honest caveat on the RMSE row.** It is not apples-to-apples: I fit only the **1,762 of 5,459**
full-10-band stars that fall inside the empirical template locus's validity window (M_G 6–14.5, i.e.
K/M dwarfs), because the locus was built from nearby dwarfs; the paper's 265 templates spanned
M_G 0–13.6. So my γ ≥ 0.10 RMSE count (97 vs 205 expected) is a **lower bound** and the shortfall is
mostly the missing two-thirds of the stars. That makes the γ ≥ 0.01 row worse, not better: 850 is
**4.1× the paper's whole-sample expectation from a third of the stars**. Extending the locus blueward
is the same query with a wider M_G window and is an M3 task.

The later stages are the clean comparison, because the extra cuts and the S/N cut are
population-independent: **5 pre-visual survivors against 6.7 expected at γ ≥ 0.10** (Poisson-consistent
with the paper's 368 sky-wide), against **25 at γ ≥ 0.01**.

**Decision for the screen: run at γ ≥ 0.10**, and report γ ≥ 0.01 as a sensitivity. Consequence to
state plainly in any writeup: **under the paper's own stated grid, my implementation does not admit
their candidate F** (best RMSE 0.255 against a 0.2 threshold).

### 4.4 Progress, and how to resume

<!--W4PROGRESS-->
**Status when this document was written (2026-08-18). The pull was left running** with a 900-minute
budget, so the real figures at the time of reading are ahead of these; regenerate this block with
`python scripts/m2_fill_progress.py --force`.

| | |
|---|---|
| tiles completed | **4** of 192 base tiles |
| sky covered | **752 deg² = 1.82%** of the sky |
| W3+W4-detected rows harvested | **6,422** (8.5 deg⁻² ⇒ **~352k projected sky-wide**, against the paper's ~3.2 × 10⁵) |
| query time spent | 8 min on successful tiles; mean 120 s/tile |
| tiles outstanding / abandoned | 3 in retry, 3 split, **0 abandoned** |
| projected time to complete | **~7 h** of wall clock at the observed success rate |

The harvest rate (8.5 W3W4-detected sources per deg², ⇒ ~352k
sky-wide) is the first independent check on the parent sample and it lands close to Hephaistos II's
~3.2 × 10⁵. **The screen will not finish inside one session** — ESA's sync endpoint is the binding
constraint, not compute — but it is cleanly underway, every tile is on disk, and it resumes with a
single command.

### The funnel so far, stage by stage against Hephaistos II Table 4

Screen coverage at the time of writing: **1.82% of the sky** (752 deg²). 'Paper expected' = Suazo et al. 2024 Table 4 scaled by that sky fraction.

| stage | this screen, γ ≥ 0.10 | γ ≥ 0.01 | paper expected | note |
|---|---|---|---|---|
| parent sample (Gaia < 300 pc × 2MASS × AllWISE) | — | — | 91,146 | not counted separately — the pull applies the W3/W4 cut server-side |
| **W3 *and* W4 detected** (C2a) | 6,422 | 6,422 | 5,833 | **1.10×** the paper's rate |
| cc_flags clean (C2b) | 5,498 | 5,498 | (folded into the above) | — |
| … with full 10-band photometry | 5,459 | 5,459 | — | — |
| … inside the template locus (M_G 6–14.5) | 1,762 | 1,762 | — | the paper's 265 templates spanned M_G 0–13.6; extending blueward is an M3 task |
| **RMSE ≤ 0.2 grid fit (C3)** | **97** | 850 | 205 | γ ≥ 0.10 gives 0.47× the paper's rate; γ ≥ 0.01 gives 4.1× |
| + Gvar, RUWE, ext_flg, classprob (C5b–e) | **84** | 596 | 94 | γ ≥ 0.10 gives 0.90× |
| **+ W3 & W4 S/N ≥ 3.5 (C6) — the pre-visual survivors** | **5** | 25 | 6.7 | the paper's 368 sky-wide |
| final candidates (their C4 CNN + C7 visual) | n/a | n/a | 0.128 | **not reproduced by design** — replaced by the coded vetting stages of §4.5 |

Read across the **S/N row** — the cleanest comparison, because the extra cuts and the S/N cut are
population-independent whereas the RMSE row is restricted to the template window (§4.3). At the
paper's own stated γ ≥ 0.10 grid the screen yields **5 pre-visual survivors
against 6.7 expected** — consistent with the published 368 sky-wide. At γ ≥ 0.01 it
yields **25**, a
**3.7× overproduction**. This is the funnel-level
statement of §4.3, now measured on real sky rather than on a single test field.
<!--/W4PROGRESS-->

**Resume — one command, no state to reconstruct:**

```
cd dyson-revet
.venv/Scripts/python.exe -u scripts/w4_screen.py repair          # only if a split was interrupted
.venv/Scripts/python.exe -u scripts/w4_screen.py pull --mode sync --tiles 24 --rasplit 8 \
    --join 6 --retries 8 --min-area 100000 --budget-min 900  >> data/w4/pull.log 2>&1
```

(`--min-area 100000` disables splitting and `--retries 8` is the measured-correct response to the
~181 s wall. Run `repair` only with the pull **stopped** — a live pull rewrites the manifest.)

It re-reads `data/w4/manifest.json`, skips every tile marked `done`, and continues. Check progress
with `python scripts/w4_screen.py status`. Run the local cuts on whatever has landed at any time with
`python scripts/w4_screen.py select --gamma-floor 0.10` (add `--tag <name>` to keep variants apart);
this is read-only on the tiles and safe to run while the pull is going. Re-fill the numbers quoted in
this document and in `STATUS.md` from the live manifest with
`python scripts/m2_fill_progress.py --force`.

**Do not parallelise this against ESA.** One anonymous connection is a polite load on a free public
service, and the manifest is single-writer, so a second process would clobber its bookkeeping. If
throughput has to go up, the fix is async (below) or a mirror — not more connections.

**Known outstanding item: run `repair` at the next stop.** The status block below reports **3 tiles
in `split` state**, left over from the first (split-happy) launch. One of them, `d00r05b` (~107 deg²
= 0.26% of the sky), has children that were never attempted and would otherwise be silently lost.
`repair` re-queues it whole; `select` de-duplicates against the done child `d00r05a`, so there is no
double counting. This is bookkeeping, not data loss — the sky is still on the queue as long as
`repair` is run before the screen is declared complete.

**If ESA's load lifts or anonymous async is restored,** re-run the diagnostic
(`python scripts/_w4_diag.py`) and, if async works, switch to `--mode async --rasplit 1`: 24 whole
strips instead of ~200 tiles, which removes essentially all of the per-query queue overhead.

### 4.5 The new vetting stages (built, not yet run at scale)

These are what the project exists for, and they replace the paper's two irreproducible stages
(C4 the CNN, C7 the visual inspection — which together carry most of the late-stage selectivity:
11243 → 5732 and 368 → 7).

1. **Centroid offsets on AllWISE + unWISE, with the JWST-calibrated 1–2″ floor stated per object.**
   Machinery validated in M1 against control C to ≲ 0.2″ (my W3 3.72″ ± 0.30 vs published 3.67″ ±
   0.25). `scripts/w2_centroids.py` runs per target; it needs a batch wrapper for the survivor list.
   **Every verdict must carry the floor**: "no offset detected" means "no contaminant outside ~1–2″",
   never "no contaminant".
2. **Chance-alignment priors fitted from the screen's own W3W4-detected population**, not from
   literature constants — this is the direct lesson of the Ren+24 unit error (§3). The screen's own
   detected-source counts give the faint red-galaxy surface density that the literature does not
   measure.
3. **Release-consistency, new in M2 and cheap**: cross-check every survivor against the WISE All-Sky
   Release. Candidate I's W3 detection evaporates there (§2b). Any survivor whose excess is
   release-dependent should be flagged before it is ever called a candidate. This is a new axis that
   neither Hephaistos nor Ren applied, it costs one IRSA query per survivor, and on the one object
   tested it fired.
4. **`w?nm` single-exposure detection counts**, also new and free — a coadd-only "detection"
   (`w3nm = 0`) is a different object from one detected in individual frames.
5. Legacy DR10 / UKIDSS / VHS neighbour pulls and SPHEREx photosphere anchoring where useful.

---

## 5. Recommended M3

1. **Finish W4 and deliver the funnel.** Resume the pull to completion (§4.4), then run `select` at
   γ ≥ 0.10 and report the full-sky funnel stage-for-stage against Suazo et al. Table 4. Deliverable
   either way: the vetted extreme-IR-excess catalog with per-object contamination priors, or the
   calibrated null on the method's yield.
2. **Run the new vetting stages on the survivor list** (§4.5), batching `w2_centroids.py` and adding
   the release-consistency and `w?nm` axes as coded gates. Expect ~370 pre-visual survivors sky-wide
   at γ ≥ 0.10; the point is that the 368 → 7 step is now *auditable* instead of visual.
3. **Settle the two open method questions before they contaminate results**: the Gaia
   `ew_espels_halpha` sign convention (affects C5a everywhere), and whether the paper's 265 real
   template stars can be approximated well enough that the γ ≥ 0.10 grid admits candidate F. Both are
   cheap and both currently sit as caveats in three documents.
4. **Watch GO 7199's third target.** Candidate A was observed by JWST on 14 Jul 2026 and is not in
   Hephaistos IV (§0.4). When it appears, the JWST-vetted sample goes to 3 and the class prior in the
   I dossier §7 must be rewritten either way. Check the exclusive-access status of the data (GO
   programs normally carry 12 months) — if it is or becomes public, it is directly analysable with
   the machinery already built here.
5. **Matthew's calls, prepared and waiting:** (a) whether the unit-error note is worth submitting
   given Blain's prior "(sic)" — and if so, the three manual browser checks first (IOP page, PubPeer,
   ADS); (b) whether the candidate-I dossier should become a JWST DDT/small-GO proposal, an RNAAS
   note in its own right, or stay internal.
6. **Generalize the SPHEREx axis** (M1 §6.3, still open and still cheap now the extractor exists):
   forced spectrophotometry on all ten candidates plus the F/H/J ambiguity tier. A hot-component
   non-detection across the set is a publishable constraint on the "warm structure" corner of
   Dyson-sphere parameter space.

---

## 6. File index (new in M2)

**Documents:** `M2-dossier-and-screen.md` (this), `I-dossier.md`,
`note-ren24-unit-error-DRAFT.md` (DRAFT — NOT SUBMITTED).

**Scripts:**

- `scripts/w4_screen.py` — the screen: `pull` (adaptive tiled 6-table harvest, checkpointed),
  `status`, `select` (local cuts + funnel, `--gamma-floor`)
- `scripts/w4_probe.py`, `scripts/_w4_diag.py` — the join-feasibility probe and the ESA async/sync
  diagnostic that forced the route correction (kept: they are the evidence for §4.1)
- `scripts/m2_i_excess.py` — flux-space excess significance + archival mid-IR probes (Spitzer SEIP,
  AKARI, IRAS, WISE All-Sky, AllWISE blend detail)
- `scripts/m2_i_figures.py` — `out/m2_I_finder.png` (finder chart), `out/m2_I_sed.png` (dossier SED)
- `scripts/m2_note_table.py` — the note's single table
- `scripts/m2_fill_progress.py` — fills the W4 progress numbers and the stage-by-stage funnel table
  in this document and `STATUS.md` from the live manifest, so the quoted figures are never
  hand-copied (`--force` to regenerate after more sky lands)

**Artifacts:** `out/m2_I_excess.json`, `out/m2_I_finder.png`, `out/m2_I_sed.png`,
`out/m2_note_table.csv`, `out/w4_funnel_g0.1.json`, `out/w4_funnel_g0.01.json`,
`out/w4_rmse_survivors_g0.1.csv`, `out/w4_previsual_candidates_g0.1.csv`.

**Gitignored bulk:** `data/w4/manifest.json`, `data/w4/tiles/*.csv`, `data/w4/pull.log`,
`data/cutouts/I_legacy_dr10.jpg`.
