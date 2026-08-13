# HANDOFF — exosat-rv

> ## ⚠ M29 (2026-08-13) — READ BEFORE TRUSTING ANY NUMBER IN THIS REPO
>
> A day spent checking old work against its actual sources found **14 wrong citations
> across 60+ sites** and **34 conflicting object properties**, and **not one was found by
> producing a new result**. Before using any externally-sourced number here, check
> [`docs/REFERENCE-AUDIT.md`](docs/REFERENCE-AUDIT.md) and
> [`docs/PROPERTY-AUDIT.md`](docs/PROPERTY-AUDIT.md). The traps are
> [`LESSONS.md`](LESSONS.md) §5b.
>
> Three things that will bite immediately:
> - **All 39 shell scripts were CRLF and unrunnable under WSL** (a "completed" reduction
>   reported exit 0 and did nothing). Fixed by `.gitattributes`. Diagnose with
>   `file script.sh` **from inside WSL** — git-bash will tell you they are LF and be wrong.
> - **The "contrast wall" is superseded.** Its 2000×/5000×/30 000× figures were never
>   derived, and the axis itself was wrong. Outcomes are ordered by **S = contrast/θ²**
>   (M29 §§6–8) — and that is consistent with the data, not yet tested by it.
> - **YSES 1 b is a 2-night series.** The 2022 night reduces once the frame count is even,
>   then fails a pre-committed order screen. The "4-night/290-d prize" never existed.
>
> ## ⚠ START AT [`LESSONS.md`](LESSONS.md) — the consolidated trap catalog + map of all conclusions
> Then [`docs/target-queue.md`](docs/target-queue.md) for the roster and the
> **HiRISE revelation (M27 pending)**: the entire "staring" tier is fiber-fed
> HiRISE data, three verdicts were corrected, and six public starlight-suppressed
> beta Pic b nights are waiting on a fiber-appropriate reduction.

> ## ⚠ READ [`M15-RESULTS.md`](M15-RESULTS.md) and [`M14-RESULTS.md`](M14-RESULTS.md) FIRST (then M13, M12); [`M17`](M17-RESULTS.md) adds the K-band tier; [`M20`](M20-RESULTS.md) the census harvest; [`M23`](M23-RESULTS.md) closes the roster
>
> **M23–M24 (2026-08-12, THE PLAN IS WALKED):** HD 1160 B — first multi-epoch series
> via the new staring branch, quality-limited (725 m/s / 41 d; one ±37 m/s night
> shows the ceiling), no claim. AF Lep b (68% transmission — dilution) and 51 Eri b
> (3 of 11 orders) land on the far side of the contrast wall, as predicted.
> CT Cha B: screened series leaves a 3.3σ variability candidate, undecidable at
> n=3. **PDS 70's nine-night upgrade FAILED its injection gate (−62%) — a
> fake-quiet series caught by machinery; the validated six-night state restored
> and reproduced exactly.** Final roster in M23 §5: eleven systems — one
> confirmation, one contradiction, four limits, one contamination case, four
> data-limited. Next levers are all dated (embargoes, M23 §6) or decisions
> (HIP 65426 b priority; the proposal case, now fully measured).
>
> **M20–M22 (2026-08-12):** the coordinate census's three host-name campaigns
> resolved. **HIP 65426 b**: 5 clean planet nights / 422 d at 131 m/s → companions
> ≥ ~0.4 M_Jup (~115 M⊕) excluded at P ≤ 100 d (90%), gates 98–101% — the
> exomoon-regime constraint (priority caveat: another team's active-programme data;
> M20 §5). **PDS 70**: the star, not the planet — flat at 130 m/s, ~3 M_Jup stellar
> limit. **beta Pic b**: km/s starlight contamination (Br-γ in the halo of a
> naked-eye star at 0.55″), diagnosed and halved; v3 (masked orders) pending. The
> **contrast wall is measured** (clean at 0.8″/2000×, flooded at 0.55″/5000×; M20
> §6). Correction log in M20 §5: "first RVs of beta Pic b" was wrong (2024 CRIRES+
> paper); all firsts now hedged. Two permanent rules: never single-night templates;
> product headers are the only band truth (six filter_path lies).
>
> **M17 (2026-08-11):** K-band spot-checks on the tier-2 targets — first-ever RVs of
> **beta Pic b** (162 m/s within-night on the planet, injection 100±0% in all 18
> K2166 orders → a campaign could reach ~100 M⊕ exomoons), **AB Pic b** (~120–190
> m/s over 2 nights, gates pass), and **CT Cha B** (usable only with per-order
> screening; disk emission suspected). viper's K-band branch is 1-indexed
> (`oset 1:19` for K2166); filter_path is now at five documented lies. The paper
> draft ([docs/paper/](docs/paper/)) carries the CD-35 + eta Tel story with
> figures/tables; beta Pic b's raw K-nights (night-to-night repeatability of a
> planet RV) are the next queue item.
>
> **M15 (2026-08-11, COMPLETE):** the validated recipe transferred to **eta Tel B**
> — which shares CD-35's exact H1567 setting — and produced the **first RV
> constraint ever placed on the object**: 127–129 m/s per epoch (beats the 163
> forecast), r(RV,BERV) ≈ 0, injection gates at 94–101% ±1–3 with 12–26 m/s
> residuals (4× cleaner than CD-35, both routes), **no credible detection** on
> either the archive or the full per-nodding route (all 20 epochs reduced from raw,
> zero failures), and an injection-calibrated 90% limit of **msini ≳ 0.5–1.2 M_Jup
> across P = 20–300 d** — sub-Jupiter over most of the range, 3× deeper than
> forecast. The machinery detects its own end-to-end K=300 injection at rank 1, so
> the null is meaningful. A weak <20 d comb moves periods between routes and
> combines — alias behavior, not claimed. The phase–BERV geometry check (ten
> minutes) confirmed 150–300 d is fully BERV-clean *before* any compute was spent —
> permanent practice from here on. Writeup-ready: "First RV constraints on
> eta Tel B."
>
> **M14 (2026-08-11, COMPLETE):** (1) **The second-satellite flip survives nested
> sampling**: dynesty on the Nature table gives ΔlogZ(2sat−1sat) between −0.8 and
> −6.6 across three model pairings × three prior styles × two seeds — never positive —
> against the paper's claimed +2.622. The M13 proxy (−0.51) was conservative.
> (2) **The drift floor is closed and the conclusion reproduces from raw data.**
> `-oversampling 2` (147→133) + a **second template iteration** (→ **85 m/s** mean,
> archive route; guard passes 105% ± 4%, every order 92–112%, o18 healed) + the
> paper's per-nodding-binned recipe on all 18 nights reduced from raw (→ **90 raw /
> 70–76 centered-robust**). The **blind period search finds ~169–171 d at rank 1 in
> every combine, ΔBIC +40 alone and +25 to +28 WITH a BERV nuisance covariate**, the
> fatal 60604 epoch excluded by a fully internal 3×-spread screen. Attribution is
> clean: at template iteration 1 the detection still collapses under BERV even
> per-nodding — iteration 2 is the decisive change. Success criterion (rms_pub ≤ 90
> AND BERV-robust blind detection) **met on both routes**. Amplitude runs 20–40% high
> (confound-limited hint, M13 §4's rules still apply). All of it injection-validated,
> including per-frame arms and an amplitude-matched K≈306 arm (9/11 orders 98–105%,
> rms 5–29 m/s).
>
> **M13 (2026-08-11):** the paper's **eleven orders are identified** —
> `oset 4,7,8,9,10,12,13,14,17,18,19`, confirmed three ways. The best config
> (`-kapsig 3` on that set, robust order combine) reaches **147–218 m/s against the
> published Nature RVs** (from 382 at M12 best), passes injection-recovery at
> **100% ± 5%**, and recovers **K = 304 ± 69 m/s against the published 306.0** at the
> published period — the amplitude reproduces from raw data. Re-running the inference on
> the **Nature** table: the 87.35 d period choice reproduces, but the second satellite's
> evidence **flips to −0.51** (paper: +2.62) under the same BIC/2 proxy that still
> reproduces the v1 comparison. `exosat-rv orbits` now defaults to the Nature table
> (`--version v1` for the superseded one). The scoring truth for any extraction change is
> [`data/published/hoy2026_nature_table2_rvs.csv`](data/published/hoy2026_nature_table2_rvs.csv)
> via [`scripts/injection/vs_published.py`](scripts/injection/vs_published.py).
>
> ## The M12 ground (still load-bearing)
>
> 1. **The paper was published in *Nature* on 22 July 2026 and M0–M11 all used the
>    pre-peer-review arXiv v1**, which its own comments field asks readers not to draw
>    conclusions from. The precision target moved **31.44 → 57.68 m/s**, the RV table
>    20 → 23 epochs with **timestamps corrected by 0.87 d**, the period 169.45 → 171.11 d,
>    Msini 0.743 → 0.918 M_Jup, and the second satellite's evidence
>    **delta-logZ 6.64 → 2.62**. `config.py` is pinned to superseded values throughout and
>    M6 fitted the superseded table.
> 2. **`viper` has been modelling a gas cell that was not in the beam** since M2 — `-nocell`
>    was never set, on data with `INS1 OPTI1 ID = FREE`. And **the template is a raw
>    observation with tellurics in it**, where the published recipe requires a telluric-free
>    one. Fixing both takes the paper's own error statistic 763 → 480 m/s and removes an
>    **RV–BERV correlation the authors explicitly report they do not have**.
> 3. **The gap is 8.3x, not 25x**, and it is now decomposed: of the baseline 823 m/s,
>    **522 m/s was BERV-correlated and is now 150 m/s**, while **~620 m/s of non-BERV
>    per-order systematic is untouched by any of it.** That residual is the real problem.
> 4. **Both fixes are adopted, and the GJ 229 B control has been overturned on evidence.**
>    An injection-recovery test on CD-35 2722 B itself (M12 §8) returns **95% ± 7%** of an
>    injected signal under the corrected model, where the control predicted **46%** — a 7σ
>    disagreement on the object that matters. Per-order recovery is **81–112%** corrected
>    against **−4% to 493%** at baseline. **Use injection recovery, not GJ 229 B, to judge
>    any forward-model change** — the control's signal is ~70x the target's, so it screens
>    the wrong regime. Build on `scratchpad/inject_run.sh`; and note M12 §8.1 — shift the
>    *template*, never the observation, or 92% of the injection vanishes into the telluric
>    anchor.
> 5. Two of M11's open suspects are closed for free: the ADP→cr2res conversion is **correct**
>    (checked against ESO's own `CWLEN` header values), and `-tpl_wave tell` is a **no-op**
>    for RV runs.

## Where the project stands

**The primary satellite now reproduces from raw data; the second satellite is
contradicted on the authors' own table.** (The project's verdict has inverted three
times — M12, M13, and now M14 — each time on evidence.)

- ✅ **The conclusion reproduces from raw data.** Blind period search on our own
  from-raw series: **~169–171 d, rank 1 in every combine, ΔBIC +40 alone, +25 to +28
  with a BERV nuisance covariate**, fatal epoch excluded by an internal screen. Both
  routes (archive-combined and per-nodding-binned) agree. ([M14](M14-RESULTS.md) §6, §8)
- ✅ Per-epoch precision **70–90 m/s vs 57.68 claimed** (1.2–1.6×, from 25× at start);
  the decisive changes were the second template iteration and `-oversampling 2`, both
  injection-validated. ([M14](M14-RESULTS.md) §2, §5, §8)
- ❌ **The second satellite is disfavoured on the paper's own Nature table**: ten
  nested-sampling integrals, ΔlogZ −0.8 to −6.6, never positive, vs their +2.622.
  The 87.35 d period *choice* still reproduces; the *existence* evidence does not
  survive their own data revision. ([M14](M14-RESULTS.md) §1, §7)
- ✅ On the superseded v1 table the same code still prefers two satellites (+3.04), as
  M6 found — the flip is in the data revision, not the code. ([M6](M6-RESULTS.md), M13 §5)
- ⚠ **Amplitude runs 20–40% high** (K 360–440 vs their 306; slope 1.19–1.24) — a hint
  that rhymes with M11's measured template-absorption, not claimable while phase and
  BERV are −0.71 entangled. Decidable when the embargoed epochs release. ([M14](M14-RESULTS.md) §9)

**M7 read the paper's reference list and the project's assumptions moved.** Read
[`M7-RESULTS.md`](M7-RESULTS.md) §0 before planning anything: the method was *proposed* in
2018, its detectability was *forecast* in 2022 by four of Hoy et al.'s own co-authors, and
**three published nulls preceded this detection**, not one. There is now a `papers/`
archive; use [`scripts/fetch_paper.py`](scripts/fetch_paper.py) to add to it.

**This is what a new agent should do next**, in order:

0. **M14 closed all three of M13's successors** (nested sampling ✓, floor ✓,
   amplitude-matched injection ✓) — see [M14 §10](M14-RESULTS.md): (a) update the
   author query with the evidence integrals and the independent detection; (b) **M15 —
   eta Tel B** with the full validated recipe (per-nodding, 2-iteration template with
   `-kapsig 3` creation, telluric-selected orders, `-kapsig 3`, `-oversampling 2`,
   robust combine, injection-validate, internal 3×-spread epoch screen), checking the
   target's phase–BERV geometry first; (c) when the embargoed epochs release
   (Dec 2026 – May 2027), settle the amplitude overshoot and the second satellite on
   data the confound cannot reach. The full target order — including the young
   self-luminous planetary-mass class (beta Pic b, PDS 70 b, and the limits tier) —
   is now in [docs/target-queue.md](docs/target-queue.md): eta Tel B is the only
   orbit-capable archive today; beta Pic b's 753 frames are 6 nights (spot-check, not
   orbit); PDS 70 b is the flagship proposal target.

1. ~~**Establish why *this project's* extraction sits 25x above 31.44 m/s.**~~ **Answered
   across M12–M13**: superseded source + phantom gas cell + telluric template (M12), then
   wrong order set + no spectral outlier rejection + mean-over-orders combine (M13). What
   is left of the gap (~2.5–3.8×) is night-to-night per-order drift, unexplained but
   characterised.
2. ~~**Fix the per-order forward model — the template first.**~~ **DONE, and it failed —
   [`M11`](M11-RESULTS.md).** Rebuilding the template the published way (Köhler et al. 2025
   §2.2, two iterations, `-tpl_wave tell`) makes CD-35 2722 B *look* better (776 → 620 m/s)
   and **collapses the control**: recovered amplitude on GJ 229 B's undisputed binary falls
   to **41% of correct after one iteration** and does not recover. Self-templating absorbs
   the signal. **Two suspects remain and the order has changed:**

   **2a. Check the ADP→cr2res conversion — now the leading suspect, and never tested.** M2
   verified it is *lossless* (max difference 0), which proves the numbers arrived, not that
   they arrived in the right order/detector slots. A mis-slotted segment gives viper a wrong
   starting wavelength per chunk, the telluric fit never locks, and `atm0` stays
   unconstrained — which M9 measured in **6 of 10 orders**.

   **2b. Score `-tpl_wave tell` on its own.** M11 changed it together with template
   iteration and cannot separate them. One run with zero iterations isolates the only part
   of M11 that might be real.

3. ~~Re-extract the individual nodding frames~~ — **last, not first.** M9 measured both
   cheap levers: the nodding frames are worth **10%** (the authors' own Fig. 4, 31.44 vs
   34.49 m/s) and order screening/reweighting **6%** (823 → 776 m/s), against a factor of 25.
   The combination stage already works; **the whole shortfall is per-order.** See
   [`M9-RESULTS.md`](M9-RESULTS.md) §7.
4. **Only then** apply the pipeline to **eta Tel B** — 16 usable H-band nights over an
   800-day baseline, no published RVs, nobody has looked. ([M5](M5-RESULTS.md)) M7 confirms
   it independently: it ranks **4th of 38** in Lazzoni et al. 2022's physics-based detection
   probability, having been ranked **1st** by M5 on archive holdings alone. Two rankings
   sharing no assumptions agree. But note M7 §5 — a null there limits satellites to
   ~3 M_Jup, a *binary-companion* limit, not an exomoon one.

Any new detection requires step 2 to succeed. M6 contributes nothing to it: fitting
someone's published velocities cannot find a new satellite.

4. **In parallel, and independent of all of the above: probe a GRAVITY product.**
   [`M10`](M10-RESULTS.md) found that **beta Pic b has 28 public pipeline-reduced VLTI/GRAVITY
   nights over 2987 days** — 1.6x the epochs over 6.4x the baseline of the dataset the
   published RV detection rests on — and that HD 206893 B, where Blunt et al. 2026 report a
   tentative astrometric exomoon candidate, has 22 public nights. **Astrometry outranks RV in
   Lazzoni et al.'s own table (P = 0.999 vs 0.996) and reaches below RV's ~0.4 M_Jup floor.**
   The kill-check is open and cheap: download one `calib_level=2` visibility product and
   verify it carries the dual-field differential phase astrometry needs. **M1's precedent
   applies — the first automated verdict on ESO's CRIRES+ products was wrong and nearly cost
   a needless pipeline rebuild.** See [`M10-RESULTS.md`](M10-RESULTS.md) §5.

**Three new lines exist that need no CRIRES+ precision at all:**

- [`M7`](M7-RESULTS.md) — the generalisation framework (`exosat-rv survey`), with the
  detection threshold recalibrated on the achieved 31.44 m/s rather than a forecast.
- [`M8`](M8-RESULTS.md) — satellites of **young close-in giants** (`exosat-rv closein`).
  3-8 real targets survive both a tidal-survival and a cross-correlation-observability cut,
  depending on the planetary tidal Q. The prize is not the moon: a limit at 10-30 M_Earth
  around a young hot Jupiter **discriminates between hot-Jupiter migration channels**.
- [`M10`](M10-RESULTS.md) — the **astrometric route** (`exosat-rv gravity`). Better public
  data than the RV route has, and **beta Pic b is the crossover target**: #2 in M7's RV
  ranking, one of Blunt et al.'s two best astrometric targets, and the best public GRAVITY
  dataset. The one object where two independent techniques could be cross-checked.

## Reading order

0. [`papers/`](papers/) — the source and its citation chain, as PDFs and extracted text.
   **Read `papers/text/hoy2026_v1.txt` in full before forming any view.** It did not exist
   until M7; six milestones ran on two papers and an appendix.
1. [`SPEC.md`](SPEC.md) — what is being tested and why it is worth testing.
2. [`M0-RESULTS.md`](M0-RESULTS.md) — what the archive contains. **Its arithmetic is corrected
   by M1 and M2; do not quote it alone.**
3. [`M1-RESULTS.md`](M1-RESULTS.md) — the source read properly, and two retractions of M0.
4. [`M2-RESULTS.md`](M2-RESULTS.md) — RV extraction, and why it falls short. Carries two
   corrections of its own.
5. [`M3-RESULTS.md`](M3-RESULTS.md) — the positive control that makes M2's null readable.
6. [`M6-RESULTS.md`](M6-RESULTS.md) — **the reproduction of the conclusion.** Read before
   forming any view on whether the paper holds up.
7. [`M4-RESULTS.md`](M4-RESULTS.md) — the alias structure of the second signal.
8. [`M5-RESULTS.md`](M5-RESULTS.md) — analogue targets, and the control's provenance.
8b. [`M7-RESULTS.md`](M7-RESULTS.md) — the literature this method came from, three
    attribution corrections, and the generalisation framework.
8c. [`M8-RESULTS.md`](M8-RESULTS.md) — young close-in giants, and why satellite survival
    and cross-correlation observability trade as an inverse cube.
8d. [`M9-RESULTS.md`](M9-RESULTS.md) — **order screening falsified, and the reweighting that
    fooled the target and was caught by the control.** Read §5 before touching order weights.
8e. [`M10-RESULTS.md`](M10-RESULTS.md) — the astrometric route, inventoried. Read §5: its
    kill-check is open.
8f. [`M11-RESULTS.md`](M11-RESULTS.md) — **the template rebuilt the published way, and why
    it suppresses the signal.** Third change running that improved the target and failed
    the control. **Read M12 §5.3 alongside it: M11 changed three things at once and ran
    with the cell error present, so its verdict is conditional.**
8g. [`M12-RESULTS.md`](M12-RESULTS.md) — **read this first, not last.** The published Nature
    version, the gas cell that was never switched off, the telluric-contaminated template,
    and the RV–BERV correlation that ties them together.
9. [`BUILD-PLAN.md`](BUILD-PLAN.md) — stack, architecture, milestones.
10. [`DATA-SOURCES.md`](DATA-SOURCES.md) — endpoints, and the traps in each.
11. [`docs/viper-runbook.md`](docs/viper-runbook.md) — **rebuild the RV pipeline from
    scratch.** Nothing in it is documented upstream for archive data.

The rest of this file is the expensive part: claims that turned out false, approaches
measured and rejected, and silent failures that cost data. The code is not the expensive
part.

---

## 1. Claims published here and later found false

### "The paper's Hill radius of 1.07 au cannot be true" (M0) — **FALSE, retracted in M1**

M0 published a disproof of a value in a peer-reviewed paper. The disproof was wrong twice:

1. **Wrong quantity.** 1.07 au is a Domingos et al. (2006) satellite *stability limit*, not
   a Hill radius. The paper computes the Hill radius separately and notes it varies over the
   companion's orbit.
2. **Wrong orbit.** M0 used the projected separation (2.8" = 62.6 au) as a circular
   semi-major axis. The companion has **e > 0.9** and P ~ 5000 yr, so a ~ 222 au, and the
   Domingos eccentricity term collapses the stable zone by more than 10x.

Recomputed with the paper's own parameters, 1.07 au falls out at e_host ~ 0.93–0.94 —
inside the published ">0.9". **The paper was right.** Full working in
[`M1-RESULTS.md`](M1-RESULTS.md) §1.1.

**Root cause, and the lesson that outlives the specific error:** M0 reasoned from an AI
summary of a source it had not read, all the way to a public claim. It *had* tagged the
value unverified — and tagging it did not stop the reasoning. **An unverified value must
not be an input to any conclusion, not merely absent from tests.**

### "The paper's evidence for a second satellite is delta-log-Z = 2.6" (M0) — **FALSE, retracted in M1**

2.6 compares the **88-day model against the 115-day model** — two candidate *periods* for
the second signal. The evidence that a second satellite exists at all is **delta-log-Z =
6.9**, against an eccentric one-satellite alternative. M0 understated the existence
evidence and overstated the period certainty. See M1 §1.3.

### "The detection is neither confirmed nor contradicted" as a statement about the paper (M3) — **TOO BROAD, corrected in M6**

M3 established that the *radial velocities* could not be re-derived from the archive at the
required precision. True, and it still stands. But it was written as the project's verdict on
the **paper's conclusion**, which M3 never tested.

Reproducing an analysis has two independent halves — obtaining the same measurements, and
drawing the same inference from them. Failing the first says nothing about the second.

**The preprint publishes its full RV table** (Table 2, appendix A). Feeding it to an
independent fitter reproduces the conclusion: the ~169 d signal above the 0.1% FAP level, an
~88 d second satellite preferred over 14/70/115 d, K₂ agreeing to 0.1%, and both model
comparisons in the same direction as the paper's. See [`M6-RESULTS.md`](M6-RESULTS.md).

**General lesson: before concluding a result cannot be reproduced, check whether the authors
published the intermediate data.** Many papers do, in an appendix nobody reads. Three
milestones were spent re-deriving numbers that were printed on page 23.

### "The GQ Lup B null is Köhler et al. 2024, the first dedicated RV exosatellite search" (SPEC, M5) — **FALSE on both counts, corrected in M7**

Found by extracting Hoy et al.'s reference list — something no earlier milestone did.

1. **Wrong author.** arXiv:2408.10299 is **Horstman et al. 2024**. Köhler is not an author
   on it. SPEC had already corrected the *instrument* (Keck/KPIC, not viper/CRIRES+) and
   still kept the wrong name, then propagated it to M5-RESULTS.
2. **Wrong priority.** It is not the first. **Ruffio et al. 2023** (HR 7672 B,
   arXiv:2301.04206) and **Vanderburg & Rodriguez 2021** (HR 8799, arXiv:2110.14650)
   precede it, and **Vanderburg, Rappaport & Mayo 2018** (arXiv:1805.01903) proposed the
   method. **Three published nulls preceded Hoy et al.'s detection**, not one.

**Root cause:** the project cited a paper by its arXiv number without opening it, twice,
and corrected the detail that was challenged rather than re-deriving the claim. The
reference list of the source paper was never extracted in six milestones.

**Rule: when a citation is found to be wrong in one respect, re-check every other claim
attached to it.** A partial correction is how the wrong author survived M5.

### "The individual nodding frames are the lever that closes the precision gap" (HANDOFF, runbook) — **WRONG BY 2 ORDERS OF MAGNITUDE, corrected in M9**

HANDOFF §next-actions and `docs/viper-runbook.md` §7 both put re-extracting the nodding
frames first, on the grounds that it is "the only remaining difference the authors
themselves name". True — and the authors also **quantify** it, in their own Fig. 4:
**31.44 m/s vs 34.49 m/s, a ~10% gain.** Against a factor of 25 it cannot be the answer, and
nothing in the project had checked the size of a lever before ranking it first.

M9 then measured the other cheap lever, order screening: **6%** (823 → 776 m/s).

**Rule: before ranking a fix, find the number the source attaches to it.** Both of these
were quantified in the paper we are reproducing.

### "Weighting orders by their measured scatter improves the RVs" (M9, briefly) — **FALSE, caught by the control before publication**

Empirical weighting (1/rms_order²) gives **514 m/s on CD-35 2722 B, the best number M9
produced and a 1.6x gain on viper's own output.** It also drops the GJ 229 B control from
Δχ² = 63.8 to **5.8**, and the recovered amplitude from 6165 to 1825 m/s.

For a target with a real signal, an order's scatter *is* the signal, so inverse-scatter
weighting downweights exactly the orders carrying it. On a target with no detected signal
the pathology is invisible.

**This is the case HANDOFF's control rule was written for, and it is the first time the rule
has actually caught something.** Without GJ 229 B the screen would have been adopted and
every subsequent null would have been deeper and more wrong. Pinned by
`test_empirical_weighting_looks_best_on_target_and_destroys_the_control`.

### "M2's co-added template failed because it skipped RV alignment" (M9 §7) — **FALSE, disproved in M11 by reading the source**

M9 named this the leading suspect: the co-added template made things worse (823 → 1638 m/s),
which is the signature of co-adding without aligning spectra in velocity first.

**viper does align.** `viper.py` line 624 divides by `(1 + par.rv/c)` before co-adding, and
line 630 applies exactly Köhler et al.'s eq. 14 weighting, `w = T_atm/ε²`. The published
recipe is implemented faithfully.

**Reading the code cost minutes; testing the hypothesis cost an afternoon.** When a suspicion
is about what a program does, read the program.

### "Rebuilding the template per the published recipe will close the gap" (M9 §7) — **FALSE, and it suppresses signal, M11**

Two template iterations with `-tpl_wave tell`, exactly as Hoy et al. describe, takes
CD-35 2722 B from 776 to 620 m/s — and collapses the GJ 229 B control from Δχ² 76.5 to 23.7,
with recovered amplitude falling from 5948 to **2452 m/s, 41% of correct, after a single
iteration**.

**Self-templating absorbs the signal**: the template is co-added from the target's own
spectra aligned by RVs measured against a template that already contains the signal, so the
residual is baked in and later velocities are partly the star measured against itself.
Köhler et al. §2.2 flag the hazard for targets with real Doppler shifts; their prescribed
workaround is what viper implements and was not sufficient at our precision.

**Do not iterate a self-built template on a target whose signal you are trying to measure,
without verifying amplitude recovery on a known signal.** Pinned by
`test_self_templating_suppresses_a_known_signal`.

## 2. Inherited claims that do not survive checking

### Table 1's log-evidence difference does not match the quoted value — minor, real

Table 1 gives logZ = −122.654 ± 0.952 and −129.295 ± 0.920, differing by **6.641**, while
the text quotes **6.9**. Both are recorded in `config.py` and pinned by
`test_table1_logz_difference_does_not_match_the_quoted_delta`. Small, and noted rather than
made much of — unlike §1, this one was checked against the actual PDF.

## 3. Approaches measured and rejected

| Approach | Why rejected |
|---|---|
| Working from a source paper without archiving it or its references | Six milestones ran on the Hoy PDF read once and discarded, plus two hand-picked citations. The reference list named the framework paper (Lazzoni+2022), the method's proposal (Vanderburg+2018) and two unnoticed prior nulls. `papers/` and `scripts/fetch_paper.py` now exist; **extract the reference list first.** |
| Reading a null result on the close-in case as "hot Jupiter moons are impossible" | The naive tidal argument (all stable orbits inside corotation) assumes a *synchronised* planet. Young planets are not synchronised, and tau_spin-down goes as a^6 — the answer flips over a factor of 3 in orbital distance. See [`M8-RESULTS.md`](M8-RESULTS.md) §2. |
| Defaulting a host's density to Jupiter's when computing a Roche limit | A 37 M_Jup object in 1.2 R_Jup is ~27 g/cm^3, not 1.3. The wrong default returns 3.1 R_host against the paper's 8.4 — a plausible-looking number, no error raised. Densities are now computed from mass and radius and pinned by a test. |
| Weighting viper's per-order RVs by inverse **formal** variance | Not merely useless but **actively harmful**: 2620 m/s against 823 for a plain mean. Order 8 has the largest scatter (4130 m/s) and the smallest formal error (101 m/s), so it dominates. M2 knew the errors were untrustworthy; M9 measured the cost of using them anyway. |
| Applying the paper's telluric-order rule to ESO's combined product | Keeping only orders where viper constrains the telluric abundance (12/14/15/16) makes the target **worse** (1142 vs 823 m/s) and weakens the control (63.8 → 46.7). Either our `atm0` errors do not mean what they appear to, or the rule needs the per-nodding data. |
| Masking per-order RVs on the RV value alone | An order counts only if its RV *and* its error are finite and positive — what viper itself does. Masking on RV alone shifts the plain mean from 823 to 878 m/s: it looks like rounding and is a silent failure to reproduce M2. |
| Populating `config.py` from AI summaries of the paper body | Produced three wrong values and one false published claim (§1). The `[SUMM]` tier is now **eliminated**, not merely flagged. |
| Extracting the PDF via WebFetch, then via poppler under WSL | WebFetch returned only compressed streams; poppler is not installed in WSL and would need sudo. **`pypdf` in the project venv did it in one call** — 27 pages, 55,679 chars. Try the pure-Python route first. |
| Framing M4 as "is the 87-day signal a harmonic of the 169-day orbit?" | The paper asks exactly this, fits the eccentric one-satellite model (e = 0.29), and rejects it by delta-log-Z = 6.9. Re-scoped to the **alias structure**, which the paper states openly is unresolved. See M1 §3-4. |
| Assuming ESO's reduced products are what the paper used | They are not. The authors kept **individual nodding frames** rather than the combined spectrum, buying 31.44 m/s against 34.49 m/s. Working from archived products costs ~10% precision by construction. M1 §2. |
| `CONTAINS(POINT(...), CIRCLE(...))` on ESO `dbo.raw` | Hard-fails with a SQL-Server geography error — the table holds rows whose coordinates do not validate. A plain ra/dec box works and is faster. |
| `astroquery.eso` for archive access | Wraps the web form; awkward for the `dbo.raw` / `ivoa.ObsCore` comparison that is the whole of M0. `pyvo` gives direct ADQL against both. |
| Reducing all 20 nights from raw with esorex/cr2res | M0 measured that 17 are already reduced by ESO. Building cr2res to recover 3 nights is a late optimisation, not a prerequisite. |
| Using `EMPEROR` (the paper's sampler) for M3 | Would make the reproduction circular. `radvel` is used instead so that agreement means something. |
| Using `sy_hmag` from the NASA Exoplanet Archive as the companion brightness cut | It is the **system** magnitude, dominated by the primary. Useless for a companion flux cut. |
| Treating "could not re-derive the measurements" as "could not reproduce the result" | They are separate claims. M2-M3 spent three milestones on the extraction while the paper's own RV table sat in appendix A. **Check for published intermediate data first.** |
| Reading a null result without a positive control | M2's null was equally consistent with an imprecise pipeline and a broken one. Only the GJ 229 B control (M3) distinguished them. **Never report a null from this pipeline without re-running the control.** |
| Using a spectrally mismatched template | The GJ 229 B control returns reduced chi2 = 0.53 (nothing) with an L-dwarf template on a T dwarf, and 5.36 with a matched one. Template match is the difference between working and broken, not a refinement. |
| Trusting viper's formal RV errors | Per-order rms exceeds the formal error by factors of 2-42. Measure precision from within-night repeats instead. |
| Believing `-createtpl` or `-telluric add` would fix M2's precision | Both were tried. The co-added template changed nothing. `-telluric add` is a **no-op on CRIRES** — `config_viper.ini`'s `[CRIRES]` section already sets it, along with `oset = 7:17` and `kapsig = 15 6`. **Read `config_viper.ini` before claiming any viper setting is off.** |
| Adding `-tellshift` for cell-free data | It frees the telluric wavelengths, which for cell-free CRIRES+ *are* the wavelength reference and must stay fixed (Köhler+2025 §5.4). It tripled the scatter. |
| Treating M6 as an independent test of the detection | Fitting the authors' published RVs tests their **inference**, not their **measurement**. A systematic in their extraction would reproduce perfectly. M6 rules out "they fit the model wrong"; it cannot rule out "the velocities are wrong". |
| Trusting the NASA Exoplanet Archive alone for the M5 target list | It caps companion mass at 30 M_Jup and therefore **does not contain CD-35 2722 B**. M5 was rebuilt archive-first, with CD-35 2722 B's rediscovery as the control. |
| Resolving companions by SIMBAD **name** | Identifiers are unforgiving about spacing: `CD-35  2722B` resolves, `CD-35 2722 B` and `BET PIC B` do not. Normalise and match against *all* identifiers instead. |
| Resolving companions by **position alone** | A cone search finds the system, not the component. It resolved `BET PIC B` to beta Pic **c** and `PZ TEL B` to the G9IV primary. Two stages are needed: cone for the system, identifier match for the component. |
| Ranking M5 targets by **frame count** | beta Pic b has 753 frames — on 6 nights. AB Pic B's 64 frames span 3 days. An RV orbit needs epochs spread over time; rank by nights and baseline. |
| Filtering companions by SIMBAD `otype` alone | `tau Boo B` (M3V) and `HD 149274B` (M5) are typed `*` and pass as "borderline". Spectral type is the more specific statement and must override. |

## 4. Silent failures that cost data

### `pathlib.Path.write_text()` truncated `README.md` to zero bytes

On Windows, `write_text()` defaults to the cp1252 locale encoding. Writing a string
containing `→` raised `UnicodeEncodeError` — **but only after opening the file in write
mode**, which had already truncated it. The exception looked like "nothing happened"; the
file was in fact destroyed. A follow-up read-modify-write then read the now-empty file,
found nothing to replace, and wrote the emptiness back.

**Rule: always pass `encoding="utf-8"` explicitly to both `read_text` and `write_text` on
this platform.** The read side is worse than the write side — cp1252 is a single-byte codec
that decodes almost any byte without raising, so reading a UTF-8 file with it produces
silent mojibake rather than an error.

Damage was limited to `README.md`, rewritten from source. Nothing else round-tripped
through Python text I/O.

### A hand-written night count that disagreed with the pipeline

An ad-hoc scoping script counted **18** public reduced nights; the pipeline reports **17**
in H band. The pipeline is right — the extra night (2024-01-03) was taken in the **K**
setting. The ad-hoc script had no band filter. Cross-check band before quoting an epoch
count.

## 5. Things that look like problems and are not

- **`access_estsize` is 0** for every CRIRES+ product in ObsCore. The column is unpopulated,
  not the products empty. Download size is unknown until M1 fetches one.
- **`sorted(...)[0]` on a settings set** looks arbitrary but is deliberate: reduced products
  carry no setting, so they inherit the night's raw settings, and a stable pick is needed.
  Now written as `min(...)`.
- **`nan pc` distances** were SIMBAD returning NaN rather than NULL for a missing parallax,
  which a bare truthiness check lets through as though it were a measurement. Now filtered
  with `math.isfinite`.
- **`archive.eso.org` timing out** is not a code fault. It served M0's queries, then went
  unreachable for all of M1 (connect timeout, HTTP 000) while `www.eso.org` returned 302 and
  other TAP services 200. Retry before debugging.
- **Two extra public nights (2023-01-04, 2023-02-01)** exist that the paper does not use.
  They are J/YJ band, not H, so they are not a discrepancy — see M0 §3. They may still be
  useful to M4 for baseline leverage.

## 5b. The literature that should have been read first

Reading these two before M2 would have saved most of it:

- **Köhler et al. 2025, [arXiv:2505.08315](https://arxiv.org/abs/2505.08315)** (A&A 698 A44)
  — the viper instrument paper. States that CRIRES+ is **not stabilised** and drifts up to
  **1 km/s** without proper wavelength correction (which is precisely M2's ~800 m/s), that
  telluric lines are the cell-free wavelength reference and must be held **fixed**, and that
  the achievable cell-free precision is **10–16 m/s in K band on bright stars** (3 m/s with a
  gas cell). It does **not** characterise cell-free H-band precision, which is the regime
  this project needs.
- **arXiv:2408.10299** — *"RV Measurements of Directly Imaged Brown Dwarf GQ Lup B to Search
  for Exosatellites"*, using **Keck/KPIC**. The first dedicated RV exosatellite search around
  a directly imaged companion, and the right prior for M5 — but SPEC wrongly described it as
  a viper/CRIRES+ paper by the same group. Corrected.

## 6. Values still unverified

**None.** The last one — CD-35 2722 B's H magnitude — was sourced in M3 to Wahhaj et al.
2011 (arXiv:1101.2893): **H = 12.78 ± 0.12** MKO, J = 13.63, K = 12.01. SPEC had estimated
~14 and was wrong by 1.2 mag, in the favourable direction.

Companion magnitudes in hand for M5 calibration: DH Tau b 14.96, kappa And b 15.01,
HN Peg b 15.40, TYC 8998-760-1 b 15.87, GU Psc b 17.70, 51 Eri b 18.99.

One value is *inferred rather than measured* and labelled as such: the GJ 229 Bb/Ba
luminosity ratio ≈ 0.45 in M3 §4 is derived from the amplitude it explains, so it is a
consistency check, not evidence.

## 7. Risk register

**DOWNGRADED (M7) — "cell-free H-band RV precision may not reach ~31 m/s at all."**
The register said every published characterisation of the cell-free regime (Köhler et al.
2025 §5.4) is K band on bright standards, and that nothing established H band on a faint
companion. **The paper under reproduction is that characterisation**: 31.44 m/s, H band,
cell-free, S/N ~ 18 companion, same instrument, same code. It was in hand the whole time and
was never read as evidence about the instrument.

The risk as worded is therefore closed. What replaces it is narrower and entirely ours:
**why does this project's extraction sit 25x above a precision the same configuration is
documented to reach?** M2 §5 lists what remains untried. This is a reproduction gap, not a
physics limit — a materially better position, and it means a null from this pipeline cannot
be published as "the archive route is closed".

**RETIRED (M1) — whether ESO's `calib_level=2` products preserve what `viper` needs.**
If they had been order-merged or resampled, forward-modelling RV extraction would have been
impossible from them and the project would have reverted to building cr2res for all 20
nights. The products are per-order extractions with native wavelength solutions
(7 orders x 3 detectors x 2048 pixels, labelled by `ORDER`/`DETEC`/`XPOS`, curved dispersion
within each segment). `viper` can use them. See M1-RESULTS §5.

Note the first automated verdict said the opposite — `describe()` counted wavelength columns,
saw one, and reported ORDER-MERGED. **Acting on it would have meant rebuilding cr2res for 20
nights that never needed it.** Structural columns beat statistical heuristics; the classifier
now keys on ORDER/DETEC and `tests/test_fetch.py` pins both shapes.

Residual cost, known in advance: the archived product is the *combined* one (ESO serves one
per night; the paper used individual nodding frames), so it carries a ~10% precision penalty
— 34.49 vs 31.44 m/s. M3 must not read that offset as disagreement.
