# M2-03 — The five fixes, and what each one cost

**Date:** 2026-08-24 · thresholds frozen first in
[`M2-01`](M2-01-preregistration.md) Part B ·
`scripts/m2_filter.py`, `scripts/m2_positive_control.py`, `scripts/m2_pool.py` →
`out/m2_positive_control.{csv,json}`

Three fixes were mandated by M1's own recommendations. Two more were found while
doing the work and are labelled as such everywhere they appear:

- **fix (d)** came out of the precision measurement and is labelled **POST-HOC**,
  because it was identified by looking at outcomes rather than pre-registered —
  which the project's own threshold rule forbids as a way of *choosing* a value.
  Its value is still fixed by rule (iii) and not by yield, and it is validated
  out-of-sample on the positive control.
- **fix (c3)** is a **structural symmetry fix with no threshold at all**, found
  while deriving the enumerator's class list from the veto list. It cannot be
  "tuned" because there is nothing to tune, and it can only ever remove objects,
  so its cost is directly measurable.

Every fix is measured by re-running the `M1-04` positive control with **only that
fix switched on** — same 102 DCAP designations, same scraped TNS report times,
same rewind, same cutoffs. The M1 baseline configuration reproduces `M1-04`
exactly at **70/102 = 68.6%**, which is what licenses the comparison.

---

## The table

| configuration | recall (DCAP, n=102) | median lead | this-episode lead | lost | gained | novae |
|---|---|---|---|---|---|---|
| **M1 baseline** | **70 (68.6%)** | 4.15 d | 2.13 d | — | — | 2/3 |
| + fix (a) amplitude + flat | 46 (45.1%) | 3.10 d | 1.78 d | 24 | 0 | 2/3 |
| + fix (c1) VSX/GCVS → flag | **71 (69.6%)** | 4.21 d | 2.15 d | 0 | **1** | **3/3** |
| + fix (c2) SIMBAD generic → flag | 70 (68.6%) | 4.15 d | 2.13 d | 0 | 0 | 2/3 |
| + fix (c3) `_Candidate` suffix | 70 (68.6%) | 4.15 d | 2.13 d | **0** | 0 | 2/3 |
| + fix (d) negative-subtraction **[POST-HOC]** | **70 (68.6%)** | 4.15 d | 2.13 d | **0** | 0 | 2/3 |
| **M2 full (a + c1 + c2 + c3 + d)** | **47 (46.1%)** | 3.12 d | 1.89 d | 24 | 1 | **3/3** |

Negative control, the auto-reporter sample that a filter must *not* fire on:

| configuration | recall (auto-reporters, n=60) | **contrast** |
|---|---|---|
| M1 baseline | 6 (10.0%) | **6.9×** |
| M2 full | 3 (5.0%) | **9.2×** |

**The filter got more selective in the right direction.** Recall against DCAP's
designations fell by 22.5 points; recall against the class the survey pipelines
already own fell by half; the contrast between them rose from 6.9× to 9.2×.

---

## Fix (a) — amplitude and per-band variability · **cost: 24 objects, 23.5 points**

### A mixed-filter bug inside M1's own amplitude

`M1-05` computed `outburst_amp = median(magnr over ALL bands) − min(magpsf over
ALL bands)`. **`magnr` is per-band** — it is the reference-image magnitude of the
nearest source in *that filter's* reference image. Mixing g and r is the same
mixed-filter trap `M1-05` documented for peak-to-peak, one column to the left, and
it went unnoticed. M2 computes

```
amp_f = median(magnr | fid = f, clean) − min(magpsf | fid = f, clean)
amp   = max over bands with at least one clean detection
```

### What the cut costs, and what it does not

`AMP_MIN = 1.0`, pre-registered. Sensitivity, as promised in `M2-01` B1.1:

| `AMP_MIN` | 0.0 | 0.5 | **1.0** | 1.5 | 2.0 | 3.0 |
|---|---|---|---|---|---|---|
| DCAP recall | 55 | 50 | **46** | 42 | 38 | 32 |

The 15 objects lost at `AMP_MIN = 0.0` are not lost to amplitude at all — they are
the flat-residual veto, the A2/B new-source requirement, and the objects where
`magnr` is absent so no amplitude is measurable.

**The important number is not in that table.** All 24 objects fix (a) discards are
**unclassified** DCAP reports. Not one is a confirmed nova or a confirmed CV:

| class | M1 baseline | fix (a) |
|---|---|---|
| Nova (spectroscopically confirmed) | 2/3 | **2/3** |
| CV | 0/2 | 0/2 |
| unclassified | 66/86 | 42/86 |

So the honest statement of the trade is: **fix (a) costs 23.5 points of recall
against DCAP's *designation list*, and zero recall against the confirmed
astrophysical events in it.** Given that `M2-02` measured DCAP-shaped
low-amplitude candidates to be overwhelmingly non-transients on fresh data, losing
the unclassified low-amplitude tail is the point of the exercise, not a side
effect. It is still a real cost and it is stated as one: some of those 24 are
presumably genuine.

### Where the losses fall

| reason | n |
|---|---|
| per-band amplitude below 1.0 mag | 16 |
| channel A2/B but ZTF has detected the position for > 90 d | **7** |
| flat in every band with ≥ 3 detections in 60 d | 1 |

### The known flaw in this fix, measured

The 7 A2/B losses are the pre-registered new-source test misfiring, and the cause
is specific. `M2-01` B1.1 justified it as *"a position where PS1 shows nothing but
ZTF has been detecting a source for years is a reference-hole artifact by
construction"*, and implemented it with `jd_trigger − i:jdstarthist`. But
`jdstarthist` is the earliest epoch of `ndethist`, which counts **every**
spatially-coincident detection back to the start of the survey, including
low-confidence and negative ones. For a **recurrent** dwarf nova whose quiescent
counterpart is fainter than PS1's limit — a very common object, and squarely on
target — `jdstarthist` reaches back to an eruption years ago even though the
current episode is two days old.

Measured, on the 29 DCAP objects that pass the M1 baseline in channel A2/B:

| newness test | keeps |
|---|---|
| pre-registered: `jd_trigger − jdstarthist ≤ 90 d` | **22 / 29** |
| intent-faithful: span of the *current clean-detection episode* ≤ 90 d | **29 / 29** |

The intent-faithful version separates the two cases exactly as the pre-registration
described — a reference hole is detected *continuously*, a recurrent CV is not.
**It is not applied here.** Changing a cut after seeing what it costs is the
behaviour the threshold rule exists to prevent, and its precision has not been
checked. It is written up as the single named change in the operating guide, with
this measurement attached, so a human can make the call with the numbers in front
of them.

---

## Fix (b) — a real outburst enumerator · **cost: none; it only adds**

**The defect.** ALeRCE's `firstmjd` window enumerates only objects whose *first
ever* ZTF detection lies inside it. A catalogued CV going into a new outburst is
structurally invisible to it. `M1-05` patched around this with Fink
`latests?class=Unknown&n=1000` — the newest 1000 alerts of a single class, which
is a few hours of one night and only the class with no SIMBAD match at all.

**What was found.** Fink's `/api/v1/latests` **accepts `startdate` and `stopdate`**.
That was not known at M1 and it changes what is possible: the whole alert stream
of a night is reachable tokenless, class by class, with the raw `i:magnr` and
`i:magpsf` fields attached.

**The enumerator, as pre-registered:**

- **Arm E1 — new sources.** ALeRCE `firstmjd ∈ [t0,t1]`, `ndet ≥ 2`. M1's, kept.
- **Arm E2 — known sources erupting.** For every Fink class that the frozen
  Layer 3 does **not** veto, pull the window; when a call returns exactly 1000 the
  cap is binding, so bisect the window until every slice is under cap. An alert
  enters the pool if

  ```
  isdiffpos = t  and  drb ≥ 0.90  and
  ( magnr − magpsf ≥ AMP_ENUM = 1.0   or   magnr is null / ≥ 99 )
  ```

  The amplitude test is per-band by construction — one alert is one filter.

**Which classes get enumerated is derived from the filter's own veto list, not
chosen.** No new free parameter; if the veto list changes the enumerator follows
it. `AMP_ENUM = AMP_MIN` deliberately, so the enumerator can never cut deeper
than the filter and quietly become the thing that decides.

**Cost to recall: none.** An enumerator can only add objects to the pool; it
cannot reject one the filter would have kept. Its effect is measured in `M2-04` as
the number of candidates found by arm E2 that arm E1 structurally could not see.

---

## Fix (c1) — VSX/GCVS from hard veto to flag · **gain: +1, and it is a nova**

`M1-04` lost **AT 2026lck**, a spectroscopically confirmed nova, because VSX
catalogues that position as `YSO:`. A catalogue error had become a filter error on
the highest-value class in the project.

A VSX or GCVS match now rejects **only** if the catalogued type is in the
pre-registered periodic family (`M`, `SR*`, `L*`, `RR*`, `CEP`, `EA/EB/EW`, `RS`,
`BY`, `DSCT`, `ROT`, …), matched on the type string truncated at the first
`/ : + (`. Everything else — `YSO`, `VAR`, `UNKNOWN`, blank, and the whole CV
family — becomes a flag carried on the row.

| | M1 baseline | fix (c1) |
|---|---|---|
| DCAP recall | 70 (68.6%) | **71 (69.6%)** |
| confirmed novae | **2/3** | **3/3** |
| objects lost | — | **0** |

**AT 2026lck is recovered**, in channel `A1_cv_outburst` on a PS1 point source
0.14″ away, in the galactic plane. This is the cleanest fix in the milestone: it
costs nothing and it recovers exactly the object it was designed to recover.

CV-family types (`UG*`, `NA`, `NL`, `ZAND`, `AM`, `DQ`, `N`, …) get a separate
`known_cv` flag and a fixed warning in the candidate one-liner: **the outburst is
real, but the object is already catalogued — it is not a new object and must not
be filed as an AT report.**

## Fix (c2) — SIMBAD's generic classes from veto to flag · **cost: zero, gain: zero here**

The same defect one column over. `M1-03`'s `KNOWN_VARIABLE_SIMBAD` list contains
`Star` and `Variable*`. A nova erupting on a catalogued star is classed `Star` by
SIMBAD, so the filter vetoed the exact case it exists to find. `Star`,
`Variable*`, `PulsV*`, `SB*`, `Radio` and `X` are moved to flags; the specific
periodic classes and every extragalactic class stay hard vetoes, because the
mission scope excludes the second group outright.

**Measured effect on the positive control: none — 70/102 either way.** No DCAP
object in the window was vetoed by a generic SIMBAD class. The fix is kept anyway
because the failure mode is structural rather than statistical: it costs nothing,
and the one time it fires it will be on the object that matters most. Reported as
a null result rather than dressed up.

## Fix (c3) — the `_Candidate` suffix · **not pre-registered · no threshold · cost: zero**

Found while implementing fix (b), because the enumerator's class list is derived
from the veto list and the list turned out to be full of things that should not
have been on it.

`M1-03` handled the `_Candidate` suffix **on the target side** and said so
explicitly: *"SIMBAD classes `CataclyV*`, `Nova`, `DwarfNova`, `Symbiotic*` and
their `_Candidate` forms are targets, not vetoes."* It never did the same on the
**veto** side. SIMBAD serves 315 classes and the `_Candidate` form of nearly every
one of them, and Layer 3 compares literal strings — so `AGN` was vetoed while

> `AGN_Candidate` · `Blazar_Candidate` · `BLLac_Candidate` · `QSO_Candidate` ·
> `LongPeriodV*_Candidate` · `Mira_Candidate` · `EclBin_Candidate` ·
> `RRLyr_Candidate` …

all passed. On a representative night `LongPeriodV*_Candidate` alone carries
**2,742 alerts** — the third-largest non-vetoed class in the stream. And the
`M2-02` vetting sample contains two objects whose Gaia DR3 variability
classification is `AGN`.

The fix strips one trailing `_Candidate` before every class comparison, on both
sides. **It introduces no parameter, so there is nothing to tune**, and it can
only remove objects.

| | M1 baseline | fix (c3) |
|---|---|---|
| DCAP recall | 70 (68.6%) | **70 (68.6%)** |
| objects lost | — | **0** |
| confirmed novae | 2/3 | 2/3 |

**Zero cost, and it closes a leak that was feeding the single largest
extragalactic and long-period-variable contaminant classes straight into the
candidate list.** It is not pre-registered and that is stated; the reason it is
still applied is that a bug with no free parameter cannot be tuned toward a
desired count, which is the specific abuse the threshold rule exists to prevent.

---

## Fix (d) — the negative-subtraction veto · **POST-HOC · cost: zero. Removes 40% of the contaminant.**

**Where it came from.** `M2-02` found that 16 of 40 candidates are image
artifacts, that all 16 carry `drb ≥ 0.913`, and that nothing in the three mandated
fixes touches them. That is a 40% contaminant with no cut pointed at it.

**The observation.** A source whose light is genuinely *above* its reference level
cannot produce a **negative** difference detection. A registration dipole can — its
sign flips with the seeing and the rotation angle — and so can a variable star
that spends part of its cycle *below* its own reference. Both are rejects. And the
sign of every detection is already in the alert packet: `i:isdiffpos`.

**The cut.** Over high-confidence detections (`drb ≥ 0.90`, or `rb ≥ 0.55` where
`drb` is absent), reject if

```
n_negative / n_high_confidence  >  NEG_FRAC_MAX = 0.05
```

Rule (iii), not yield: a handful of negatives is reference noise; more than one in
twenty means the source spends real time below its reference, which is variability
about a mean, not an outburst above quiescence.

**What it costs, measured two ways.**

| | |
|---|---|
| positive control, pre-report rewind | **70/102 — identical to baseline at every threshold from 0.00 to 0.50** |
| **full Fink history** of all 98 DCAP objects that have one | **0 of 98 has a single high-confidence negative detection.** Not one. |

The second measurement is the fair analogue of a candidate pass, where the whole
history is available, and it is unambiguous: **the cut cannot fire on DCAP's
objects because the physics forbids it.**

**What it catches**, on the `M2-02` vetting sample:

| `NEG_FRAC_MAX` | flagged / 40 | artifacts caught | known variables caught | **plausible transients caught** |
|---|---|---|---|---|
| 0.02 | 16 | 8 / 16 | 8 / 21 | **0 / 2** |
| **0.05** | **16** | **8 / 16** | **8 / 21** | **0 / 2** |
| 0.10 | 15 | 7 / 16 | 8 / 21 | **0 / 2** |
| 0.20 | 15 | 7 / 16 | 8 / 21 | **0 / 2** |

Sixteen of forty rejected, **all sixteen non-transients, neither plausible
transient touched**, and the result is flat across an order of magnitude in the
threshold — which is what a threshold fixed by construction looks like, as opposed
to one fitted to a sample.

**Its provenance travels with it.** It is post-hoc, it is labelled POST-HOC in the
code and in every table, and the out-of-sample checks are the positive control
(zero cost on 98 objects it was not derived from) and the fresh vetting in
`M2-04`. If it fails the fresh check, it should be removed.

---

## What is *not* fixed, and cannot be by this route

**Roughly half the artifacts remain invisible without an image.** Fix (d) catches
8 of the 16 artifacts in the vetting sample. The other 8 — saturated-star wings,
single-epoch bloated residuals, globally bad subtractions — produced no negative
detections and look, in every column the alert packet carries, like clean
brightening point sources. `drb` scores them ≥ 0.91.

**There is no column that closes this.** The operating guide therefore makes
cutout inspection a mandatory step before any report, not an optional one, and
`M2-04` ships the evidence sheets alongside the list so that step costs a minute
per object rather than an afternoon.
