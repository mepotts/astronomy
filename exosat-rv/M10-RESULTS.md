# M10 — The astrometric route, inventoried

**Question:** M9 measured that the RV extraction gap does not close by any cheap lever. Is
there a second route to the project's actual goal — finding or bounding a *new* exosatellite
— that does not depend on closing it?

**Answer: yes, and its public dataset is better than the RV route's.** VLTI/GRAVITY
astrometry of **beta Pic b** has **28 pipeline-reduced nights over 2987 days**, all public,
against the 18 nights over 466 days on which the published RV detection rests.

Run with `exosat-rv gravity`; machine-readable form in [`data/m10-gravity.json`](data/m10-gravity.json).

**A kill-check remains open.** See §5 — this is the M0-equivalent, not the M1-equivalent.

---

## 1. Why astrometry, and why now

Three independent reasons, none of which the project had noticed before M7:

1. **Lazzoni et al. 2022 rank astrometry above RV.** Their Table 2 gives P(detect at least
   one binary-like satellite) = **0.999 for astrometry** against **0.996 for RV** — the best
   of their four techniques — with an expected 6.1 detections against RV's 5.1.
2. **It reaches deeper.** M7 finds the RV floor on the best imaged companion is ~0.4 M_Jup.
   Blunt et al. 2026 claim GRAVITY feasibility "to detect moons with masses lower than
   Jupiter and potentially down to less than Neptune in optimistic cases".
3. **It is independent of the gap M2/M3/M9 could not close.** Nothing about the astrometric
   route depends on cell-free RV precision, viper, telluric anchoring, or nodding frames.

And it is no longer hypothetical. Blunt et al. 2026
([arXiv:2511.20091](https://arxiv.org/abs/2511.20091), A&A) ran **the first astrometric
exomoon search** on HD 206893 B and found tentative residuals consistent with a **~0.4 M_Jup
companion at P ≈ 0.76 yr**, explicitly flagging possible systematics.

Their detectability scaling (eq. 6) — detectable moon mass ∝ `T_moon^(-2/3) · d ·
M_planet^(2/3)` — prefers short satellite periods, nearby systems and light planets, the same
directions the RV scaling prefers. The two techniques want the same targets.

## 2. The inventory

Blunt et al. §6 cut their sample on K < 20 mag and host–companion contrast < 10⁵, leaving
five viable GRAVITY+ targets. Querying ESO for what is actually public at each:

| Target | Reduced products | Nights | Baseline | Span | Raw sci | Public | Usable? |
|---|---:|---:|---|---:|---:|---:|---|
| **beta Pic b** | **322** | **28** | 2016-10-16 → 2024-12-20 | **2987 d** | 633 | 633 | **YES** |
| **HD 206893 B** | **234** | **22** | 2019-07-17 → 2025-06-08 | **2153 d** | 458 | 458 | **YES** |
| AF Lep b | 34 | 6 | 2023-11-03 → 2025-10-14 | 711 d | 146 | 125 | no |
| HD 155555 (AB) b | 1 | 1 | 2018-04-21 | 0 | 3 | 3 | no |
| 2M1315-2649 b | 0 | 0 | — | 0 | 0 | 0 | no |

Against the RV route:

| Dataset | Nights | Baseline |
|---|---:|---:|
| CD-35 2722 B (the published RV detection) | 18 | 466 d |
| eta Tel B (M5's best RV analogue) | 16 | 800 d |
| **beta Pic b (GRAVITY)** | **28** | **2987 d** |

**beta Pic b has 1.6× the epochs over 6.4× the baseline of the dataset the first
exosatellite was found in**, and every frame is public.

The usability bar is M5's, reused deliberately: ≥ 8 nights over ≥ 100 days. If anything it
should be *higher* here, because a satellite signature is a residual left after the
companion's own orbit is subtracted, so orbital coverage matters as much as epoch count.

## 3. Two findings worth separating

**The candidate is reproducible.** HD 206893 B — where Blunt et al. report their residuals —
has **22 public reduced nights over 2153 days**. Their result is not locked behind
proprietary data. An independent reanalysis is possible, which matters because they
themselves say the origin "remains ambiguous and could be due to systematics". That is
exactly the shape of question this project exists to answer, and it is the same shape as M6:
test someone's inference against their own data.

**beta Pic b is the crossover target.** It is:

- **#2 in M7's RV ranking** (reachable satellite mass 214 M_⊕, second only to CD-35 2722 B);
- one of Blunt et al.'s **two best short-term astrometric targets**;
- the **best public GRAVITY dataset** of the five.

So it is the one object where an RV limit and an astrometric limit could be set
independently and cross-checked. That is the same discipline the GJ 229 B control brought to
M3 — and which M9 showed is what catches a wrong answer — applied *across* techniques rather
than within one.

Note also that M5 **rejected** beta Pic b for the RV route on good grounds: 753 CRIRES+
frames on only 6 nights, no cadence. Its GRAVITY holdings are the opposite shape. **The same
target can be hopeless for one technique and best-in-class for another**, which is an
argument for inventorying per technique rather than maintaining one target list.

## 4. What this does not change

- **It does not close the RV gap.** M9's conclusion stands and step 1 of HANDOFF is
  unaffected.
- **It is not a discovery.** SPEC's non-goals apply unchanged.
- **It is a reanalysis of someone else's survey**, exactly as M5 concluded for the RV
  analogue search. Blunt et al. are actively working these targets.

## 5. The kill-check, which is open

**This is the M0-equivalent, not the M1-equivalent.** It establishes that the data is public
and reduced. It does *not* establish that the data contains what an astrometric fit needs.

M1 is the precedent and the warning: for CRIRES+, the first automated verdict on ESO's
reduced products said `ORDER-MERGED — cr2res may be required`, and acting on it would have
meant rebuilding a pipeline for 20 nights that never needed it. The structure had to be
opened and checked.

The same question is open here. ESO serves GRAVITY `calib_level=2` products as
`dataproduct_type='visibility'`. Whether those carry the **dual-field differential phase**
that companion astrometry is extracted from, at the ~10–50 μas precision the science needs,
is **unverified**. Interferometric astrometry is not recovered the way a spectrum is, and
"reduced visibilities exist" is a weaker claim than "the astrometry is recoverable from
them".

**Do not describe this route as open until a product has been downloaded and inspected.**
That probe is M10's natural successor and it is cheap — one file, one structural check,
exactly as `exosat-rv probe` did for CRIRES+.

## 6. Caveats

- Positions are literature coordinates for the *host*; GRAVITY dual-field observations are
  logged variously against host or companion, so the 0.03° box may over- or under-count.
  M5 established that resolving companions needs two stages (cone, then identifier match)
  and this inventory uses only the first.
- Night counts come from `t_min` in ObsCore and are not filtered for whether the companion
  was actually the science target rather than a calibrator or the host alone.
- AF Lep b's raw holdings are 146 frames of which 125 are public, but only 6 nights — the
  same frames-versus-nights trap M5 documented for beta Pic b in the RV archive.
- Blunt et al. list a sixth target, HD 60584 b, omitted here: it is an unconfirmed candidate
  with no reliable position to query on.
