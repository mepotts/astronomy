# M2-01 — Pre-registration: the vetting protocol and the three fixes

**Date:** 2026-08-24 · **Written and frozen BEFORE any candidate was looked at and
before any fixed-filter run was made.** Nothing below was chosen by looking at an
outcome. Where a number is arbitrary, that is said so and a sensitivity table is
promised instead of a silent choice.

Two pre-registrations live here because they must both precede their measurement:

- **Part A** — the vetting protocol that measures **precision**, M2's headline and
  the thing `M1-04` explicitly could not claim.
- **Part B** — the thresholds for the three filter fixes, fixed under the same
  rule `M1-03` used, before any recall or precision number was recomputed.

---

# Part A — the vetting protocol

## A0. What precision means here, stated before measuring it

> **Precision = the fraction of a candidate list that is a *plausible real
> transient a human could take to the next step*.**

Three definitional choices that change the number, all made now:

1. **An already-catalogued CV in a normal outburst counts AGAINST precision.**
   It is a real astrophysical event, but TNS AT reports name *new* objects; filing
   one on a star that already has a VSX designation is a duplicate, not a
   discovery. It is tallied separately as `known_cv_outburst` so the operating
   guide can treat it differently, but it is not in the precision numerator.
2. **A reference-image hole counts AGAINST precision.** A source absent from the
   template produces a permanent positive difference-image residual. It is an
   artifact of the subtraction, not an event.
3. **Precision is measured on the list as published**, not on a hand-picked top
   slice. Stratified so that the top slice can also be quoted separately.

## A1. Population and sample

**Population:** the **184 rows** of `out/m1_candidates_recent.csv` exactly as M1
left them. No re-run, no re-tier, no edit.

**Strata** are M1-05's declared triage tiers, which exist in the file already:

| stratum | N |
|---|---|
| tier A | 3 |
| tier B | 5 |
| tier C | 176 |
| **total** | **184** |

**Draw:**

- **Tiers A and B are vetted exhaustively** (8 of 8). No sampling error on the
  slice a human would actually read.
- **Tier C: a simple random sample of n = 32 without replacement**, drawn as

  ```python
  rng = numpy.random.default_rng(20260824)
  oids = sorted(tierC_oids)                 # sort fixes the draw
  sample = rng.choice(oids, size=32, replace=False)
  ```

  The seed `20260824` is the date and is fixed here. **The draw is executed once.
  It is not re-rolled, and no object may be swapped out for being awkward** — an
  object whose evidence cannot be assembled is classified `undecidable`, which is
  a defined outcome, not an exclusion.

**Total vetted: 40.**

**Why 32 and not more:** honestly, because 40 objects at the evidence depth in A2
is what fits in this milestone. The statistical consequence is stated up front: at
n = 32 the Wilson 95% interval is at most ±0.17 wide at p = 0.5 and much tighter at
the extremes — if tier-C precision is near zero, as `M1-05`'s own caveat predicts,
the upper bound lands near 0.11, which is enough to settle the submittability
question either way.

**Not blind.** The vetter (this agent) can see the tier and M1's one-liner. That
is a real limitation and it is why the rubric in A3 is written down *first*, in
mechanical form, rather than left to judgement at the moment of classifying.

## A2. Evidence assembled per object — identical for all 40, assembled before any classification

| id | evidence | source |
|---|---|---|
| **E1** | ZTF cutout **triplet** — science / template / difference, 63×63 px, at the alert nearest the passing epoch, all three rendered on the same zscale stretch | Fink `POST /api/v1/cutouts` (tokenless) |
| **E2** | full-baseline light curve, `magpsf` vs MJD **split by `fid`**, with the per-band `magnr` quiescent level drawn as a line | Fink `POST /api/v1/objects` |
| **E3** | alert diagnostics at the trigger: `drb`, `nbad`, `fwhm`, `elong`, `distnr`, `magnr`, `sgscore1`, `distpsnr1`, `ndethist`, `jdstarthist` | Fink alert packet |
| **E4** | archival cross-match, 3″ (VSX and ATLAS-VS also at 5″): **Gaia DR3** (`I/355/gaiadr3` — Plx, PM, G, BP−RP), **Gaia DR3 variability class** (`I/358/vclassre`), **VSX** (`B/vsx/vsx`), **ATLAS variable stars** (`J/AJ/156/241/table4`), **2MASS** (`II/246/out`, J−K), **PS1 DR1** (`II/349/ps1`) | CDS X-Match (tokenless) |

E4 is deliberately **independent of Fink's own cross-matches**. Fink's `d:vsx`
already ran; if the filter's catalogue layer is leaking, an independent match at a
wider radius is what shows it.

## A3. The rubric — four classes, mechanical decision rules, first rule that fires wins

**R1 → `artifact`** if any of:

- **a.** the difference stamp shows a **bipolar residual** (adjacent positive and
  negative lobes), a diffraction spike, a ghost/halo, a bleed trail, or the source
  sits on the wing of a saturated star;
- **b.** the **reference-hole signature**: the template stamp is blank, NaN, or
  shows no source where the science stamp shows an ordinary star, **and** the
  per-band difference light curve is flat (peak-to-peak < 0.3 mag over ≥ 3 epochs
  in a single band);
- **c.** the difference-stamp source is **not a clean PSF** — extended, streaked,
  truncated at a stamp edge, or split.

**R2 → `known_variable`** if any of:

- **a.** a match within 3″ (5″ for VSX / ATLAS-VS) whose catalogued type is in the
  **periodic / pulsating / eclipsing / rotational** families — Mira, SR\*, L\*,
  RR\*, CEP/DCEP/CW/ACEP, EA/EB/EW/E/ELL, RS, BY, DSCT, GDOR, ACV, SXPHE, ROT,
  BCEP, SPB, ZZ, LPV — in VSX, ATLAS-VS, or Gaia DR3 `vclassre`;
- **b.** the full-baseline per-band light curve shows **repeated comparable-amplitude
  excursions with no quiescent floor** — persistent variability, not
  outburst-and-return;
- **c.** the **Mira trap**: 2MASS J−K > 1.0 **and** Gaia BP−RP > 2.0 **and**
  variation on ≥ 100 d timescales.

  *Sub-tally:* a match whose catalogued type is in the **CV / nova family**
  (UG\*, NA, NB, NC, NL, NR, ZAND, AM, DQ, CV, N) is recorded as
  **`known_cv_outburst`**. Per A0 it counts against precision (it is not a new
  object) but it is reported separately because it is a real event.

**R3 → `plausible_transient`** if **all** of:

- **a.** clean, centred, PSF-like **positive** source in the difference stamp with
  no residual structure;
- **b.** R2a does not fire — no periodic-variable catalogue match;
- **c.** the per-band light curve shows an excursion of **≥ 0.5 mag above a
  definable quiescent baseline**, *or* there is no prior detection at the position
  at all (a genuinely new source);
- **d.** it is not the nucleus of a resolved galaxy in the template stamp.

**R4 → `undecidable`** — everything else: cutouts unavailable, evidence in
conflict, or too few epochs to evaluate R2b / R3c.

Every classification is written to `out/m2_vetting.csv` with the rule that fired
and a free-text evidence note, so any human can re-check the call that was made.

## A4. Statistics — fixed now

- Per-stratum precision `p_h = plausible_transient / vetted_h`.
- **Interval: Wilson score, 95%**, computed as
  `(p + z²/2n ± z·sqrt(p(1−p)/n + z²/4n²)) / (1 + z²/n)`, `z = 1.959964`.
- **Whole-list precision: stratified**, `P = Σ_h (N_h/N)·p_h`, with
  `Var(P) = Σ_h (N_h/N)²·(p_h(1−p_h)/n_h)·(1 − n_h/N_h)`; 95% interval
  `P ± 1.96·sqrt(Var)`, clipped to [0, 1]. Tiers A and B are censuses so their
  finite-population correction is 1 − n/N = 0 and they contribute no variance.
- **Two figures reported, both pre-registered:**
  - **lenient** — `undecidable` removed from the denominator;
  - **strict** — `undecidable` counted as not-a-transient.
  The **strict** figure is the headline.

## A5. The decision rule, written before the count

> **If the strict whole-list precision has a 95% upper bound below 0.20, the M1
> candidate list is declared NOT SUBMITTABLE as a list, and that failure is the
> headline of M2.**

A second, separate rule for the top slice:

> **If tiers A+B (n = 8, a census) yield fewer than 2 `plausible_transient`, the
> declared triage of `M1-05` is reported as not working either.**

## A6. Precision of the *fixed* filter's output

The same rubric, the same evidence, applied to the final list produced in `M2-04`:
vet **all** of it if it holds ≤ 25 objects, otherwise a random sample of 25 drawn
with seed `20260825` under the identical procedure. Reported with the same two
figures and the same interval.

---

# Part B — the three fixes, thresholds fixed before recounting

Same threshold rule as `M1-03`, unchanged, in priority order:

> **(i)** the value a published ZTF / AMPEL / ZTF-BTS recipe already uses for that
> field; **(ii)** a boundary this project's own documents already name; **(iii)**
> the loosest value that excludes an artifact class by construction.
> **No threshold may be chosen by looking at how many candidates it yields.**

Every fix is validated by re-running the `M1-04` positive control **and** the
`M2-02` precision protocol, so the cost of each is visible in both directions.

## B1 — Fix (a): amplitude and per-band variability

### B1.1 The amplitude cut, and a mixed-filter bug inside M1's own amplitude

`M1-05` computed `outburst_amp = median(magnr over ALL bands) − min(magpsf over ALL
bands)`. **`magnr` is per-band** — it is the reference-image magnitude of the
nearest source in *that filter's* reference. Mixing them is the same mixed-filter
trap `M1-05` documented for peak-to-peak, one column to the left, and it went
unnoticed. Corrected definition, pre-registered:

```
amp_f  = median(magnr | fid = f, clean) − min(magpsf | fid = f, clean)
amp    = max over bands f that have ≥ 1 clean detection
```

**`AMP_MIN = 1.0` mag.** Rule (ii) + (iii): 1.0 is the boundary `M1-05` already
named as the tier A/B line before M2 opened, and it is ~5× ZTF's single-epoch
photometric scatter at mag 20 (≈ 0.2 mag), below which an excursion cannot be
told from noise on the reference source. **A sensitivity table at
0.5 / 1.0 / 1.5 / 2.0 will be reported** so the choice is visible rather than
hidden.

**Exemption, because amplitude is undefined there.** Channels `A2_nova_like` and
`B_M31`/`B_M81` have no quiescent source to measure against — `magnr` is null or
99. For those channels the amplitude cut is replaced by a **new-source
requirement**:

```
jd_trigger − i:jdstarthist  ≤  NEW_SOURCE_MAX_HIST_DAYS = 90 d
```

Rule (iii): a position where PS1 shows nothing but ZTF has been detecting a source
for years is a reference-hole artifact **by construction**, not a new star. 90 d
is chosen as the outer edge of a classical nova's detectable decline (t₃ runs days
to ~100 d), so a real nova cannot be cut by it.

### B1.2 The flat-residual veto (per-band variability)

`M1-05`'s declared "flat override" is **promoted from a post-hoc ranking rule to a
filter cut**, unchanged in value:

```
FLAT_PTP_MAX     = 0.30 mag
FLAT_MIN_ALERTS  = 3
FLAT_WINDOW_DAYS = 60
```

Reject the object if **every** band that has ≥ 3 clean detections in the 60 days
ending at the trigger has per-band peak-to-peak < 0.30 mag. Rule (ii) + (iii):
0.30 mag is below ZTF's own per-epoch scatter at mag ~20, so there is no
variability left to claim; and it is the number `M1-05` already declared.

**The veto cannot fire when no band has ≥ 3 clean detections in the window.** A
genuinely new nova with two detections must not be rejected for lack of evidence
of variability — absence of a measurement is not a measurement.

## B2 — Fix (b): the outburst enumerator

**The defect.** ALeRCE's `firstmjd` window enumerates only objects whose *first
ever* ZTF detection falls in the window. A catalogued CV going into a new
outburst — `M1-02` names this as most of DCAP's actual business — has a first
detection years ago and is **structurally invisible** to it. `M1-05` patched
around it with Fink `latests?class=Unknown&n=1000`, which returns only the newest
1000 alerts of one class: a few hours of one night, and only the class with no
SIMBAD match at all.

**The fix.** A two-arm enumerator whose union is complete over a night:

- **Arm E1 — new sources (kept from M1).** ALeRCE `/ztf/v1/objects/` with
  `firstmjd ∈ [t0, t1]`, `ndet ≥ 2`.
- **Arm E2 — known sources erupting (new).** Fink
  `GET /api/v1/latests` **does accept `startdate` / `stopdate`** (verified today;
  undocumented in M1). For each Fink class, one call over the night with
  `n = 1000`; if the call returns exactly 1000 the cap is binding and the night is
  re-sliced hour by hour until every slice is under cap. An alert enters the pool
  if:

  ```
  i:isdiffpos = t          and    i:drb ≥ 0.90
  and (  i:magnr − i:magpsf ≥ AMP_ENUM = 1.0        # a known source, now brighter
      or i:magnr is null / ≥ 99 )                   # no reference source at all
  ```

  The amplitude test is **per-band by construction** — one alert is one filter —
  which is why it is safe to apply this early.

  **Which classes are enumerated is derived from the frozen filter, not chosen:**
  every Fink class that Layer 3 of `M1-03` (as amended by B3) does not veto. No
  new free parameter, and if the veto list changes the enumerator follows it.

`AMP_ENUM = AMP_MIN = 1.0` deliberately — **the enumerator must never cut deeper
than the filter**, or the filter's own thresholds stop being the thing that
decides.

## B3 — Fix (c): VSX/GCVS from hard veto to flag

**The defect.** `M1-04` lost **AT 2026lck**, a spectroscopically confirmed nova,
because VSX catalogues that position as a YSO. A catalogue error became a filter
error, on the single highest-value class.

**The fix, in two parts.**

**(c1) VSX / GCVS.** A match no longer rejects. It rejects **only** if the
catalogued type is in the pre-registered periodic family:

```
PERIODIC_VETO_TYPES = {M, SR, SRA, SRB, SRC, SRD, SRS, L, LB, LC, LPV,
                       RR, RRAB, RRC, RRD, CEP, DCEP, DCEPS, CW, CWA, CWB,
                       ACEP, BCEP, EA, EB, EW, E, ED, ESD, EC, ELL, RS, BY,
                       DSCT, HADS, GDOR, ACV, SXPHE, ROT, SPB, ZZ, ZZA, ZZB,
                       ZZO, GCAS, LPB}
```

matched on the type string **truncated at the first `/`, `:`, `+` or `(`**, upper-cased.
Rule (iii): these are exactly the classes whose variability is *already known and
already published*; nothing new can be claimed there. Every other type — YSO,
UNKNOWN, VAR, MISC, blank, and the whole CV family — becomes a **flag carried on
the row**, not a rejection.

CV-family types (`UG*`, `NA`, `NB`, `NC`, `NL`, `NR`, `ZAND`, `AM`, `DQ`, `CV`,
`N`) get their own flag, `known_cv`, and a fixed warning in the one-liner:
**an outburst here is real but the object is already catalogued — it is not a new
object and must not be filed as an AT report.**

**(c2) SIMBAD's generic classes — the same defect, one column over.** `M1-03`'s
`KNOWN_VARIABLE_SIMBAD` veto contains `Star` and `Variable*`. A nova erupting on a
catalogued star is classed `Star` by SIMBAD, so the filter vetoes the exact case it
exists to find. `Star`, `Variable*`, `PulsV*`, `SB*` and `Radio` are moved from
veto to flag; the specific periodic classes (RRLyr, Mira, LongPeriodV\*, EclBin,
Cepheid, δ Sct, RS CVn, BY Dra, rotational) and the extragalactic classes (AGN,
QSO, Blazar, Galaxy, …) **stay hard vetoes** — the mission scope excludes the
second group outright.

This is reported as its own before/after line so its cost is separable from (c1).

## B4 — Ranking of the final list, fixed before the list exists

Rank descending on a declared score, not on a hand-pick:

```
score = 2.0·min(amp, 5)/5                    # how far above quiescence
      + 1.5·[|b| < 15°]                      # the measured gap (M1-02)
      + 1.0·[channel A2 or B]                # nothing was there before
      + 1.0·min(ptp_band, 2)/2               # genuine per-band variability
      + 0.5·[no VSX/GCVS/ATLAS-VS match]     # uncatalogued
      − 2.0·[known_cv flag]                  # real, but not a new object
      − 1.0·[ndethist > 100]                 # long-known ZTF source
```

Weights are declared, not fitted; they encode `M1-02`'s measured niche
(latitude first) and `M1-05`'s measured contaminants (long-known sources, flat
residuals). They are a **presentation order**, not a threshold — nothing is
removed by the score.

## B5 — What is NOT changed

`DRB_MIN`, `RB_MIN`, `NBAD_MAX`, `FWHM_MAX`, `ELONG_MAX`, `MAGDIFF_MAX`,
`N_DET_MIN`, `DT_MIN_DAYS`, `SSDIST_MAX_ARCSEC`, `MAG_BRIGHT`, `MAG_FAINT`,
`FAINT_RESIDUE_MIN`, the nuclear/TDE veto, the A1/A2 radii, the M31/M81 cones,
`GAL_PLANE_ABS_B`, `TNS_MATCH_ARCSEC` — all stay at their `M1-03` values. M2 adds
cuts and changes a veto to a flag; it does not re-tune M1.

---

## House law, restated

**Nothing is ever submitted to TNS. No account is created anywhere.** The
allowlist guard in `scripts/tnscommon.py` stays in force and is not weakened by
any M2 code. Every candidate row carries
`STATUS = MATTHEW-GATED -- NOT REPORTED TO TNS`.
