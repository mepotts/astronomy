# M2-04 — The fixed chain, the final list, and the precision it earns

**Date:** 2026-08-24 · **MATTHEW-GATED, nothing reported to anyone** ·
`scripts/m2_pool.py`, `scripts/m2_candidates.py`, `scripts/m2_precision_final.py` →
`out/m2_candidates_recent.{csv,json}`, `out/m2_pool_recent.json`,
`out/m2_vetting_final.csv`, `out/m2_vetting_supplementary.csv`,
`out/m2_livefire.{csv,json}`, `out/vet/m2list_sheet*.png`, `out/vet/m2clean_sheet*.png`

> ## NOTHING IN THIS LIST HAS BEEN REPORTED TO ANYONE
> No discovery report, no classification, no bulk report, no sandbox submission.
> No account was created anywhere. The read-only allowlist in
> `scripts/tnscommon.py` is unchanged and was re-verified today: it refuses
> `/api/set/`, `bulk-report`, the sandbox equivalent, and any wis-tns.org path
> outside `/search`, `/object/` and `/api/get/`.

---

## The headline

| | M1 list | **M2 list** |
|---|---|---|
| candidates | 184 | **37** |
| **precision (strict, pre-registered)** | 3.5% [1.1%, 15.6%] | **8.0% [2.2%, 25.0%]** |
| image artifacts | **40%** (16/40) | **12%** (3/25) |
| known / evident variables | 52.5% | 44% |
| real outburst on an already-catalogued CV | 0% | **32%** (8/25) |
| plausible new transients | 5% (2/40) | 8% (2/25) |
| **any real astrophysical outburst found** | 5% | **40% [23%, 59%]** |

**Precision roughly doubled and the artifact fraction fell by a factor of three,
but the confidence intervals overlap and 8% is still low.** The change that
matters more than the point estimate is *what the failures now are*: M1's list
failed because it was full of bad subtractions and red long-period variables; the
M2 list fails mostly because it finds **real dwarf-nova outbursts on stars that
already have a designation** — which the filter now detects, flags, and warns
about in plain language, rather than presenting as discoveries.

**Submission-grade count: five objects across the whole milestone have been
hand-vetted as plausible new transients. None of them is submittable today**,
because a TNS AT report is rejected without a pre-discovery non-detection and
nobody holds an ATLAS forced-photometry account (`OPERATING-GUIDE.md` §6.3).

---

## The pass

| | |
|---|---|
| window | MJD **61274 – 61277** (2026-08-21 → 2026-08-24) |
| **arm E1** — ALeRCE `firstmjd`, new sources | 2,881 objects |
| **arm E2** — Fink `latests` over the window, all non-vetoed classes, amplitude ≥ 1.0 | 161 objects |
| overlap | 3 |
| **pool** | **3,039** |
| pass a generic hygiene gate | 107 |
| **pass the M2 filter** | **51** |
| ...of which arm E2 found | **46** |
| ...of which arm E1 found | 5 |
| minus objects already in TNS within 3″ | **−14** |
| **final candidates** | **37** |
| in the galactic plane (\|b\| < 15°) | 14 |
| flagged `known_cv` (real, already catalogued) | 13 |
| with any archival variable match | 24 |
| with **no** Gaia DR3 counterpart within 3″ | 6 |

**Fix (b) is what produced this list. 46 of the 51 passing objects came from the
outburst arm, which M1's enumerator structurally could not see; the new-source
arm — the whole of M1's enumeration — contributed 5.** The measured claim in
`M1-02` that a re-erupting known source is most of DCAP's business is borne out on
live data.

## A bug found while vetting, and fixed: the trigger epoch

The first M2 list had **41 of 44 candidates whose passing epoch lay more than a
year before the enumeration window.** Evaluating a candidate pass with no
`jd_floor` makes the filter fire at the object's *all-time* first passing epoch,
so `mag_at_pass`, `first_pass_jd`, the per-band amplitude, the peak-to-peak, and
the flat-residual veto all described an outburst from 2019 rather than the one
that put the object in tonight's pool. **M1's candidate pass has the same
defect.** The fix floors the visible history at 60 days before the window — the
same episode convention `M1-04` already used — and moves no threshold. It took
the list from 44 to 37 and tripled the number of flat residuals the veto catches
(4 → 12).

## Live fire: 14 objects other people reported from the same window

The 14 objects removed by the TNS cross-match are not a loss — they are an
independent, unrewound check. Somebody else looked at the same sky in the same
three nights and filed a report; our filter found the same objects.

| | |
|---|---|
| passing objects independently reported to TNS from this window | **14** |
| of which channel `A2_nova_like` | **11 of 11 A2 objects that passed** |
| our passing epoch **preceded** their report | **5 / 14** |
| median lead | **−0.55 d** · best **+1.42 d** |
| who filed first | ZTF 11 · ALeRCE 1 · ATLAS 1 · GOTO 1 |

Two things follow, and they point in opposite directions.

**The A2 channel works.** Every single object that reached `A2_nova_like` and
passed every cut was a real transient that a professional pipeline reported. That
is 100% precision on that channel for this window — an unrewound, unblinded,
live-fire measurement.

**And it is not where the niche is.** Thirteen of the fourteen sit at |b| > 12°
and most at |b| > 35°: they are extragalactic supernovae, and the competition
there is ZTF's own supernova pipeline, which filed 11 of them. On latency we
roughly break even (5 wins, 9 losses). `M1-04` predicted exactly this — *"against
a same-night reporter the same filter would lose"* — and now it is measured
against the mainstream rather than against DCAP.

## Precision on the fixed list (M2-01 A6, pre-registered)

Random sample of **25 of 37**, drawn with `default_rng(20260825)` over the sorted
oids, same rubric, same evidence, same four classes.

| class | n | share |
|---|---|---|
| **known_variable** | 11 | 44% |
| **known_cv_outburst** *(real outburst, already catalogued)* | **8** | **32%** |
| **artifact** | **3** | **12%** |
| **plausible_transient** | 2 | 8% |
| undecidable | 1 | 4% |

- **Strict precision 0.080, Wilson 95% [0.022, 0.250].**
- Lenient (undecidable dropped) 0.083 [0.023, 0.258].
- **Real-event rate** (plausible + known-CV outburst, reported separately and
  never inside precision, exactly as `M2-01` A0 required): **0.40 [0.234, 0.593]**.

### What changed, class by class

**Artifacts collapsed from 40% to 12%** — three of the sixteen contaminant types
survive. Two are bipolar residuals on VSX-catalogued CVs whose stamps at the
trigger epoch are genuinely bad; one is a bloated bright-star residual on an
r = 12–14 long-period variable. Fix (d) and the trigger-epoch fix did the work.

**Eight of the twenty-five are real dwarf-nova and symbiotic outbursts on stars
that already carry a VSX designation.** `ZTF18aafeggh` is the clearest: VSX type
`UG`, Gaia DR3 variability class `CV`, and **only four alerts, all from MJD
61274.5–61275.5** — an outburst caught in the act, 3.8 mag above quiescence, on
the night the pass was run. That is precisely what the outburst enumerator was
built for. It is also, correctly, not submittable, and the row says so in words.

**The remaining variables are now AGN and YSOs, not Miras.** Five carry a Gaia DR3
`vclassre` class of `AGN` and two a class of `YSO`, all within 0.4″. Only one red
long-period variable survived to the sample, and it was caught as an artifact
first. That is fix (c3) plus the amplitude cut working.

**A leak this exposes:** Gaia DR3's variability classification identified five AGN
that Fink's SIMBAD cross-match calls `Unknown`. **`I/358/vclassre` is currently
carried as a column but is not a veto input.** Making it one is the single
highest-value remaining filter change and it is named as such in the operating
guide.

## The clean subset — a declared, non-random census

**This is not part of the precision estimate and must not be read as one.** Of the
37, exactly **13** carry no `known_cv` flag *and* no match in VSX, ATLAS-VS or
Gaia variability. Six fell in the random sample; the other seven were vetted
afterwards under the same rubric so the subset is a complete census
(`out/m2_vetting_supplementary.csv`).

| class | n of 13 |
|---|---|
| **plausible_transient** | **5** |
| known_variable | 6 |
| undecidable | 2 |
| artifact | **0** |

**Two columns the pipeline already emits — "no known-CV flag" and "no archival
variable match" — select a subset in which zero of thirteen objects is an image
artifact and five are plausible transients.** That is the operational rule the
guide leads with.

---

## The three best objects

**1. `ZTF18accebtg` — 19:04:52.95 +09:15:02.8 (286.22061, +9.25077), |b| = +1.25°**
**The best object in the milestone.** Deep in the galactic plane, where 94% of TNS
reporting never goes. **No Gaia DR3 counterpart within 3″** and no VSX, ATLAS-VS
or Gaia-variability match of any kind, against a PS1 reference at **21.73** — so
the quiescent star is fainter than G ≈ 21. Eleven r-band alerts in **four separate
episodes** (MJD 59894, 60245, 60705, and 61274–61275 now), each reaching 18.9–19.7
with non-detection in between, i.e. **2.8 mag above quiescence, recurring**. The
difference stamp is a clean centred PSF with no dipole. An uncatalogued recurrent
dwarf nova is the obvious reading.

**2. `ZTF19acbplek` — 17:48:04.22 +08:03:39.7 (267.01759, +8.06103), |b| = +17.73°**
The only object vetted as a plausible transient **twice, independently** — once in
the `M2-02` sample from the M1 list and again in the `A6` sample from the M2 list.
No Gaia counterpart, no archival match, PS1 reference **21.73**, **13 outburst
episodes** over seven years peaking at 17.71, currently 3.69 mag above quiescence.

**3. `ZTF19aampgvg` — 17:31:07.59 −05:02:35.1 (262.78161, −5.04307), |b| = +15.32°**
No Gaia counterpart, no archival match, PS1 reference **21.60**, **21 episodes**
over seven years reaching 17.52, now 3.30 mag up. The weakest part of the case is
the difference stamp, where the source is faint; everything else fits an
uncatalogued frequently-erupting CV.

Also vetted plausible, and both far out of the plane so a faint supernova is at
least as likely: `ZTF24abuzrht` (00:25:10.93 −18:32:28.9, |b| = −79.5°, 2.57 mag
up) and `ZTF22aavufkm` (22:38:59.03 −17:34:06.3, |b| = −58.0°, 1.84 mag up).

## How many are submission-grade

**Five, and none of them today.**

- **Five** objects have been hand-vetted as plausible new transients across the
  whole milestone. Three of them (`ZTF18accebtg`, `ZTF19acbplek`, `ZTF19aampgvg`)
  share the same profile: no Gaia counterpart, a PS1 reference fainter than 21.5,
  and repeated outburst episodes with non-detection between.
- Applying the measured precision to the list as a whole, **37 × 0.080 ≈ 3
  expected genuine new transients (95% interval ≈ 1 to 9)**.
- **Zero can be reported now.** A TNS AT report is rejected outright without a
  pre-discovery non-detection (blocking error 6), which requires an ATLAS
  forced-photometry account. That, the TNS account, and the TNS bot key are the
  three human steps in `OPERATING-GUIDE.md` §6.
- **Before any of the five is reported, each still needs the full §5 per-object
  check**, including an independent second-broker look and a by-hand MPChecker
  query. Nothing in this document substitutes for that.

## Caveats that travel with this list

1. **8% precision means roughly nine in ten rows are not new transients.** The
   list is a place to look, not a queue to file from.
2. **`n = 25`.** The interval reaches 25% at the top and the improvement over the
   M1 list is not statistically separated from it. What *is* separated is the
   artifact fraction and the composition of the failures.
3. **The supplementary census of the clean subset is not random** and cannot be
   used as a precision estimate, however tempting its 5-of-13 looks.
4. **Nothing has been eyeballed at higher resolution than a 63×63 ZTF stamp**, and
   no forced photometry exists for any of these positions.
5. **Channel B (M31/M81) contributed nothing**, for the seasonal reason `M1-05`
   measured. It reopens in September and needs the three changes in
   `OPERATING-GUIDE.md` §7 before it is pointed at a real season.
6. **One night's window.** Whether 8% holds across the season is unmeasured.
