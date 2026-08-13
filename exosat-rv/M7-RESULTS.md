# M7 — Generalising the method, by reading the literature it came from

**Question:** how do you apply the Hoy et al. method to other candidate exosatellites?

**Answer: the question was already answered in print, by four of their own co-authors, and
this project had not read it.** Hoy et al. cite **Lazzoni et al. 2022**,
*Detectability of satellites around directly imaged exoplanets and brown dwarfs*
([MNRAS 516, 391](https://arxiv.org/abs/2207.07569)) — a population study that simulates
satellites around 38 directly imaged companions and computes RV detection probabilities for
every one. It is the framework M5 was groping toward from the archive side.

Run with `exosat-rv survey`; machine-readable form in [`data/m7-survey.json`](data/m7-survey.json).

---

## 0. The actual failure this milestone fixes

The project had read **two** papers in six milestones (HANDOFF §5b) and stored **none** of
them. There was no `papers/` directory, no PDF, no reference list. Hoy et al.'s citation
list was never extracted, so the following went unnoticed:

| Reference | What it is | Status before M7 |
|---|---|---|
| **Lazzoni et al. 2022** | detectability of satellites around DI companions — *the* framework | never mentioned |
| **[32] Vanderburg, Rappaport & Mayo 2018** | **proposed this method**, and enumerates its false positives | never mentioned |
| **[14] Ruffio et al. 2023** | prior null on HR 7672 B + instrument forecasts to TMT | never mentioned |
| **[15] Vanderburg & Rodriguez 2021** | prior null on HR 8799 | never mentioned |
| **[13] Horstman et al. 2024** | prior null on GQ Lup B | cited, **misattributed** |

There is now a `papers/` archive with the PDFs and extracted text, and
[`scripts/fetch_paper.py`](scripts/fetch_paper.py) to add to it.

### Three corrections to SPEC, all from the reference list alone

1. **The GQ Lup B paper is Horstman et al. 2024, not "Köhler et al. 2024".** Köhler is not
   an author on it. SPEC had already corrected the *instrument* (Keck/KPIC, not CRIRES+)
   but kept the wrong first author, and repeated it in M5-RESULTS.
2. **It is not "the first dedicated RV exosatellite search around a directly imaged
   companion".** Ruffio et al. 2023 (HR 7672 B) and Vanderburg & Rodriguez 2021 (HR 8799)
   both precede it. **Three published nulls existed before this detection**, not one.
3. **The method was proposed in 2018**, by Vanderburg, Rappaport & Mayo, motivated by the
   Kepler-1625b I candidate. SPEC's framing of the technique as "the paper's" is right
   about the *execution* and wrong about the *idea*.

**The lesson is the one M1 and M6 already taught in different clothes.** M1: don't reason
from an unread source. M6: check whether the authors published the intermediate data. M7:
**read the reference list — it names the papers that already did the work you are about
to redo.** Each time the cost was measured in milestones.

## 1. What the framework actually says

Lazzoni et al. split candidate satellites into two populations and reach opposite verdicts:

| Population | Formation | Mass ratio q | P(RV detection) | Expected N |
|---|---|---:|---:|---:|
| **planet-like** (Titan, Galilean) | core accretion, circumplanetary disc | ~1e-4 | **0.08** | 0.08 |
| **binary-like** | disc instability / fragmentation / capture | ≥ 0.01 | **0.996** | 5.1 |

Their RV detection threshold (§4.3.2) is a flux scaling anchored to a forecast:

> K_lim = 0.1 × 10^(0.2 (K_p − 13.5)) km/s

— 100 m/s at K = 13.5, degrading 1.585× per magnitude. That 1.585 is where SPEC's number
came from; it had been carried without its source.

**Hoy et al.'s satellites are binary-like**, at q = 0.020 and 0.007 against a
circumplanetary-disc expectation of q ≈ 6e-4 for a 37 M_Jup host — thirty times larger.
The paper reaches the same conclusion from formation theory and cites Inderbitzi et al.
2020 for it. So the detection landed exactly where the framework said detections would
land, and nowhere near where solar-system-like moons live.

## 2. The forecast was beaten, and the threshold should be recalibrated

At CD-35 2722 B's K = 12.01, Lazzoni's curve predicts **50.3 m/s**. Hoy et al. achieved
**31.44 m/s** — better by 1.6×.

`satellites.hoy_calibrated_threshold_ms` re-anchors the same magnitude scaling on the
achievement rather than the forecast. Using the forecast would *under*-admit targets by
that factor, which is the wrong direction for a triage cut.

## 3. CD-35 2722 B is not in the framework's own sample

Checked, not assumed: **the 38 companions in Lazzoni et al.'s Table 1 do not include
CD-35 2722 B.** Hoy et al. write that "it has been calculated that, given the existence of
satellites orbiting CD-35 B, the radial velocity method would be relatively likely to find
them [10]" (published wording; the preprint reads "given the existence of
satellites" and numbers the same reference [11]) — but that study evaluated the
*class*, not this object.

**The first exosatellite was found on a target the predictive study never scored.** That is
not a criticism of either paper; it is a caution about how much weight any ranking of this
kind can bear, including the one below.

## 4. Two independent rankings agree on eta Tel B

M5 ranked analogue targets **archive-first** — usable nights and baseline of public CRIRES+
data — with no physics in the ordering at all. Lazzoni et al. ranked them **physics-first**
— simulated satellite populations and detection probability — with no reference to whether
data exists.

| | M5 (archive) | Lazzoni (physics) |
|---|---|---|
| **eta Tel B** | **#1** — 16 usable H nights over 800 d | **#4 of 38** — P(RV) = 0.229 |
| GJ 229 B | #2 — 11 nights, and a known binary | not in sample |
| beta Pic b | rejected — 753 frames, only 6 nights | P(RV) = 0.091 |

The three targets above eta Tel B in Lazzoni's ranking (HD 19467 B, HD 1160 c, PZ Tel B)
are old field brown dwarfs with little or no CRIRES+ time series. **eta Tel B is the best
target on both criteria simultaneously**, reached by two methods sharing no assumptions.
That is a considerably stronger endorsement than M5 alone could give, and it survives the
"not white space" caveat: nobody has published RVs of it.

## 5. The feasibility conjunction, and what it returns

`exosat-rv survey` evaluates four conditions per companion rather than M5's two:

1. **wobble** — K = (m_s/M_p)·√(G M_p/a_s) (Lazzoni eq. 2)
2. **flux** — the recalibrated threshold above, plus Ruffio et al.'s **~13 M_Jup
   deuterium-burning cliff**, below which a young companion is far fainter and RV precision
   collapses
3. **dynamics** — Roche limit < a_s < Domingos limit
4. **survival** — has anything at a_s survived tides (new in M8, decisive only for close-in
   hosts)

Top of the ranking, by the smallest satellite each target could yield:

| Companion | M_host | K_mag | σ_RV | min m_sat | Reachable class |
|---|---:|---:|---:|---:|---|
| **CD-35 2722 B** | 37.0 | 12.01 | 94 | **129 M_⊕** | sub-Jovian |
| beta Pic b | 12.8 | 14.90 | 357 | 214 M_⊕ | sub-Jovian |
| PDS 70 b | 7.9 | 15.20 | 410 | 292 M_⊕ | sub-Jovian |
| HD 72946 B | 72.4 | 13.50 | 187 | 332 M_⊕ | binary-like only |
| eta Tel B | 47.0 | 13.20 | 163 | 1053 M_⊕ | binary-like only |

**CD-35 2722 B comes out first** — the correct answer, since it is where the detection
happened, and it is a control on the ranking rather than a result.

**No target reaches planet-like satellites (≤ 30 M_⊕).** That reproduces Lazzoni et al.'s
central conclusion independently: this method finds binary-like satellites or nothing.
Reporting it as "0 pass, 38 fail" would hide the actual result, so the survey names the
*class* reachable at each target instead.

Note eta Tel B's position. It is the best target *to observe* — most data, best cadence,
highest independent detection probability — while reaching only large satellites, because
its 47 M_Jup mass suppresses the wobble (K ∝ M_host^(−2/3)) and its wide 199 au orbit puts
the stable zone far out. **Best target and best sensitivity are different questions**, and
M5 answered only the first.

## 6. What this changes for the project

- HANDOFF's step 3 ("apply the pipeline to eta Tel B") is **confirmed as the right target**
  by an independent line of argument, and now carries a quantitative expectation: any null
  there constrains satellites down to roughly 1000 M_⊕ ≈ 3 M_Jup, i.e. it is a
  *binary-companion* limit, not an exomoon limit. That is what an upper-limit paper would
  be able to claim, and SPEC's "most likely upper limits" framing is right.
- HANDOFF's **step 1 is partly answered**. It asks whether cell-free H-band precision can
  reach ~31 m/s, noting no paper characterises it. Hoy et al. *are* that characterisation —
  31.44 m/s, H band, cell-free, on an S/N ≈ 18 companion — which is the regime the risk
  register calls uncharacterised. The open question is narrower than stated: not "is it
  possible" but "why does this project's own extraction sit 25× above it".

## 6b. There is now a second exosatellite candidate, by a different technique

Found while answering "what else is worth pulling on", and it postdates every other paper
in `papers/`: **Kral et al. 2026, *Exomoon search with VLTI/GRAVITY around the substellar
companion HD 206893 B*** ([arXiv:2511.20091](https://arxiv.org/abs/2511.20091), A&A Jan 2026)
— "the first application of high-precision astrometry to search for exomoons".

They report **tentative astrometric residuals** around HD 206893 B (~28 M_Jup) consistent
with a companion of **~0.4 M_Jup at P ≈ 0.76 yr**, explicitly cautioning that the origin
"remains ambiguous and could be due to systematics". They demonstrate feasibility "to detect
moons with masses lower than Jupiter and potentially down to less than Neptune in optimistic
cases" — **below what RV reaches on any target in §5**.

Three consequences for this project:

1. **The regime is nearly identical to Hoy et al.'s** — 0.4 M_Jup at 278 d around a 28 M_Jup
   brown dwarf, against 0.743 M_Jup at 169 d around a 37 M_Jup one. **Two independent
   tentative exosatellite candidates now exist around substellar companions**, by two
   techniques, within a year. SPEC's prior-art section names only the RV lineage.
2. **Astrometry is the better-ranked technique and this is the first time it has been
   tried.** Lazzoni et al. 2022 Table 2 puts astrometry at P = 0.999 for binary-like
   satellites against RV's 0.996 — nominally the best of the four — and until now nobody had
   run it.
3. **They name their own follow-up targets: AF Lep b and beta Pic b.** beta Pic b is **#2 in
   §5's RV ranking**. It is therefore the one object where an RV limit and an astrometric
   limit could be set independently and cross-checked — the same discipline the GJ 229 B
   positive control brought to M3, applied across techniques rather than within one.

## 7. Caveats

- Lazzoni's Table 1 values are transcribed from the PDF text layer, not from a machine-
  readable table. Masses and separations are literature values from ~2022 and some have
  moved.
- The survey probes a single semi-major axis (0.4 × the stability limit) rather than
  integrating over a population, so its `min m_sat` is a sensitivity indicator, not a
  detection probability. Lazzoni's Table A1 has the properly marginalised numbers.
- Seven companions have only upper limits on K (`> 21`) and cannot be ranked at all.
