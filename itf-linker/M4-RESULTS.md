# M4 — widening the distance grid, and the older 80% of the file

**Run date:** 2026-08-03 · **Reports:** `m4-new.json` (the MJD > 60000 slice),
`m4-old.json` (the pre-60000 slice), `data/m4-validate-*.json` (ground truth),
`data/m4-populations-*.json` (population reachability), `m4-vet.json` (catalogue vetting)

M3 searched **1.4–5.6 AU** of the MJD > 60000 slice and said plainly what that excluded:
every NEO, and everything beyond Jupiter. It also left 2.1M of the ITF's 2.6M tracklets
untouched. M4 does those two things.

**Nothing here is a discovery.** Everything below is "linked candidates surviving gates".
Nothing was submitted anywhere; all network use was cached, read-only GET against public
MPC, IMCCE and JPL endpoints.

---

## 1. Provenance

| | |
|---|---|
| ITF snapshot | `Last-Modified` **Wed, 29 Jul 2026 07:26:34 GMT**, ETag `"8084534-657bae00ec6dd"`, 134,759,732 B — the same content M3 used (9,322,655 observations; M1 measured the two 2026-07-29 pulls byte-identical) |
| Find_Orb | `~/bin/fo`, built 2026-07-29 from `find_orb@143c823`; JPL DE-440 (`linux_p1550p2650.440`) |
| Ephemeris for the linker | ERFA `epv00`, via astropy's `builtin` solar-system ephemeris |
| Bad-data filter, every run | 9,322,655 in → 4 pre-1900 epochs, 3 blank designations, **1,161 duplicate records** dropped → 9,321,487 kept |
| Tests | **369 passing** (321 at the end of M3), ruff clean |

---

## 2. Widening the grid is seven changes, not one

M3's grid was 43 distances × 9 radial velocities over 1.4–5.6 AU, swept in 14-day windows.
Setting `r_min=0.5, r_max=50` and leaving everything else alone would have been wrong in
seven separate ways. Each was found by measurement, and each had to be fixed before the
widened grid was worth pointing at the ITF at all.

### 2.1 A uniform distance step is the wrong rule across two decades

The quantity that decides whether a wrong hypothesis breaks a cluster is not the distance
error itself. An error `δr` in the assumed heliocentric distance perturbs the topocentric
distance by about the same amount, which mis-scales the implied *transverse* velocity by
`δr · μ` (μ = the tracklet's sky-plane rate) and therefore displaces the propagated state by
`δr · μ · Δt`. Requiring that to stay inside the clustering radius gives

> **δr < radius / (μ · Δt)** — the admissible step scales as **1/μ**.

At opposition `μ ≈ v⊕(1 − r^−1/2)/(r − 1)`, so `δr` grows very nearly linearly with `r`.
Evaluated at the production radius (0.0025 AU) and Δt = 7 days:

| r (AU) | 1.4 | 2.5 | 5.6 | 10 | 30 | 50 |
|---|---:|---:|---:|---:|---:|---:|
| admissible δr (AU) | 0.054 | 0.085 | 0.165 | 0.27 | 0.74 | 1.19 |
| **δr / r** | **0.039** | **0.034** | **0.029** | **0.027** | **0.025** | **0.024** |

Constant to 25% across two decades. **The natural grid is geometric**, and M3's 0.10 AU
step is simply the value that rule takes in the middle of the main belt. A uniform 0.10 AU
step over 0.55–50 AU would be 500 samples, most of them redundant past 10 AU and too coarse
inside 1 AU.

### 2.2 The near root: half the NEO parameter space M3's solver could not express

`solve_rho` returns the intersection of the line of sight with the sphere of radius `r`
about the Sun. M3 took the **far** root, which is correct and complete for `r > 1 AU`: the
observer is inside the sphere, and the near root is behind them.

Inside 1 AU the observer is **outside** the sphere, and the geometry is different in kind.
The line of sight either misses the sphere entirely — which is why an object at 0.7 AU can
only be seen at solar elongation < 44° — or it pierces it **twice**, at two positive
distances that are both perfectly good positions. Taking only the far root silently
discards every object caught on the near side of its orbit while interior to the Earth.

In the Horizons check of §3, **(163693) Atira — the archetype of the interior-to-Earth
class — is recovered on the near branch**, at a hypothesised 0.771 AU against a true
0.700 AU: that is where the tightest hypothesis for it lives.

**It does not follow that the near branch was strictly necessary for that object, and the
measurement says so.** Sweeping a synthetic Atira-class orbit (a = 0.74, e = 0.32) over
0.5–0.95 AU at 0.5% steps, the best cluster diameter is 0.00108 AU on the near branch and
0.00154 AU on the far one — *both* inside the 0.0025 AU radius. A wrong-branch hypothesis
at a wrong distance can still make three tracklets agree, which is the same phenomenon M3
documented for `RL00hfG` and the reason a cluster is never treated as an orbit.

What the near root *is*, then, is half the physically valid states inside 1 AU that the
far-root-only solver could not express at all. It costs nothing outside 1 AU because it is
not swept there, and the run shows it doing real work: the best description of a genuine
Atira came from it. `tests/test_link_bands.py` pins the geometry — two distinct positive
roots, both exactly on the hypothesised sphere — and the band behaviour, without
overstating the second as the first.

The branch is swept only below 1.02 AU (Earth's own heliocentric distance runs 0.983–1.017
AU over the year), because above that it is guaranteed to produce nothing.

### 2.3 One window length per band, and the rule that fixes it

The hypothesis models `r(t)` as linear. The neglected term is the radial acceleration
`GM/r²`, which over a window `W` accumulates to `GM·W²/(8r²)`. Setting that equal to the
clustering radius gives the longest usable window:

| r (AU) | 0.5 | 0.55 | 0.95 | 1.0 | 1.4 | 2.5 | 5.6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| max window (days) | 4.1 | 4.5 | 7.8 | 8.2 | 11.5 | 20.6 | 46.0 |

**A 14-day window at 1 AU puts the model error at 7 × 10⁻³ AU — three times the clustering
radius.** The tracklets of a real NEO would simply not land on each other. So the bands do
not share a window:

| band | r (AU) | spacing | ṙ samples | window / step (d) | hypotheses | max a (AU) |
|---|---|---|---:|---|---:|---:|
| `inner` | 0.55–0.94 | geometric, 1.0% | 13 × ±0.85 v_esc | 5.00 / 1.25 | 1,430 | 100 |
| `neo` | 0.95–1.44 | geometric, 3.0% | 13 × ±0.85 v_esc | 7.75 / 1.94 | 234 | 100 |
| `belt` | 1.40–5.60 | **uniform 0.10 — M3's, unchanged** | 9 × ±0.55 v_esc | **14.00 / 3.50** | 387 | 100 |
| `outer` | 5.60–48.42 | geometric, 4.0% | 9 × ±0.55 v_esc | 21.00 / 5.25 | 504 | **1,000** |

2,555 hypotheses against M3's 387. Two bands knowingly exceed the curvature rule and both
are recorded rather than hidden: `inner` is floored at 5 days because the MPC rejects any
link with an arc under 3 days and a 4.5-day window cannot hold one with a night at each
end (model error there is ~1.5× the radius); `belt` is M3's own 14 days, kept byte-identical
so M3's numbers stay reproducible (M3 justified 14 days at 2.5 AU, where the limit is 20.6).

The outer band's semimajor-axis ceiling moves from 100 AU to 1,000. At 100 AU the ceiling is
generous for a 2.5 AU hypothesis and is a **hard rejection of every scattered-disc object**
for a 40 AU one.

### 2.4 The radial-velocity range was measurably wrong inside 1.5 AU

M3 sampled ṙ as ±0.55 of the local escape speed. The reachable fraction for an orbit `(a, e)`
observed at `r` is `e·√(r / (2a(1−e²)))` — under a half for a low-eccentricity belt object,
and not for an eccentric NEO. **(3200) Phaethon at 0.84 AU sits at 0.715, outside M3's range
entirely.** It was the one target the first widened run failed to recover, and this was why.
The NEO bands use ±0.85 with 13 samples, so the *resolution* is unchanged at 0.14 v_esc and
only the range grows.

### 2.5 The distance step inside 1 AU needs the amplification factor

The 1/μ rule assumes `δρ ≈ δr`. That holds at opposition and fails for an interior object:
`∂ρ/∂r = r / (r⃗·ρ̂)`, and the denominator is the square root taken in `solve_rho`, which
shrinks towards the grazing ray. At the geometry that recovers Atira it is 0.32 AU, so a
distance error is amplified threefold before it reaches the transverse velocity.

Measured on Horizons astrometry of four real NEOs — the tightest cluster diameter any
hypothesis in a 0.5–1.5 AU grid achieves, against a 0.0025 AU production radius:

| object | sky rate | f = 0.03 | f = 0.02 | f = 0.01 | f = 0.002 |
|---|---:|---:|---:|---:|---:|
| (3200) Phaethon | 3.0 °/d | 0.0103 | 0.0052 | **0.0020** | 0.0021 |
| (163693) Atira | 1.1 °/d | 0.0011 | 0.0009 | 0.0009 | 0.0009 |
| (2062) Aten | 1.1 °/d | 0.0001 | 0.0002 | 0.0001 | 0.0001 |
| (433) Eros | 0.9 °/d | 0.0005 | 0.0005 | 0.0005 | 0.0005 |

Below about 1 °/day the step does not matter at all. At 3 °/day a 3% step misses by
fourfold and a 1% step just fits — **and going finer stops helping**, because ~0.002 AU is
the irreducible spread the linear `r(t)` model leaves over a 5-day window at that speed.
1% is therefore where the grid stops being the limit, and the `inner` band is cheap enough
(13 s over the whole production slice) that there is no reason not to pay it.

### 2.6 The r ≈ 1 AU degeneracy is no longer a corner case

M3 found that as the hypothesised distance approaches the observer's own, `ρ → 0` and every
tracklet collapses onto the observer's own state vector — clustering with everything, at
spreads tighter than any real object's. M3's guard is
`geometry.MIN_TOPOCENTRIC_DISTANCE_AU = 0.05`, and M3 noted it did not bind because the grid
started at 1.4 AU.

**It binds on every window now.** The grid steps across the observer's own distance
hundreds of times per night, and the near branch reaches the same singularity from *below*
(at zero elongation `ρ_near = r_obs − r`). Three things pin it:

- a test asserting that every hypothesis within 0.05 AU of the observer's own heliocentric
  distance is rejected, on **both** branches, at three offsets;
- a functional test that puts three genuinely different objects (1.1, 2.6, 3.1 AU) in one
  window, sweeps a 0.55–1.45 AU grid at 2% steps, and asserts no link mixes two of them;
- a new guard the near branch made necessary: `|r⃗·ρ̂| > 0.05 AU`. That quantity is ± the
  square root in `solve_rho`, so it measures how close the line of sight is to *grazing*
  the hypothesised sphere. Where it vanishes the two roots have merged and the ρ̇ solve is
  ill-conditioned — a different singularity from the ρ → 0 one, and one the existing guard
  does not catch because the grazing ray has a perfectly large ρ. On a 1.4–5.6 AU grid it
  never binds (`|r⃗·ρ̂| ≥ 0.96 AU` there), so M3 is unaffected.

### 2.7 Three scaling faults the widened grid exposed

All three were latent in M3, correct at M3's scale, and unfinishable at M4's. Each was
replaced by something **exact** rather than approximate, and each replacement is pinned by
a randomised test against the implementation it replaced — because an optimisation that
changes the answer is not an optimisation, and M3's numbers had to survive it (§4.1 shows
they did).

**`drop_subsets` was quadratic.** It tested every candidate against every candidate already
kept. That is fine at M3's 17,060 links and is not fine at the NEO band's ~60,000
pre-merge: 2 × 10⁹ set comparisons. A proper superset must contain *every* one of a
candidate's tracklets, so comparing against the links sharing one arbitrary tracklet — a
list of a few dozen — is sufficient and exact. A randomised test pins the indexed
implementation against the naive one it replaced.

**Window slicing was a full scan per window.** `Arrows.slice_window` filtered the whole
table. The number of windows grows with the *span* of a slice while the table grows with its
*size*, so this is invisible on MJD > 60000 (359 windows × 511k arrows) and fatal on the
pre-60000 slice with a 5-day window: ~35,000 windows × 2.1M arrows, 7 × 10¹⁰ rows scanned
to build slices that mostly hold a few hundred arrows. `build_arrows` already leaves the
table sorted by epoch, so it is now a binary search and a zero-copy slice. A randomised
test pins the two against each other on the edge cases — window boundaries falling exactly
on an arrow, between arrows, before everything and after everything.

**The global isolation check scanned every state for every group.** This is M3's §5.3
guard, the exact lattice-independent one that closes the hole the cell-local ambiguity
rule leaves — and it is the single most important structural rule in the linker, so it
could not be weakened, sampled or skipped. Built as a `groups × arrows × 6` distance array
(in batches, which is M3's own memory fix) it is fine against M3's densest window: 23,000
arrows and ~1,200 groups per hypothesis. The pre-60000 slice has archival deep-drilling
fields with **41,068 arrows in one window** and thousands of groups per hypothesis, which
is ~10⁸ six-dimensional distances *per hypothesis* — **measured at about an hour for a
single window**, against 387 hypotheses. That is not a slow run, it is a run that does not
end, and it is why the first attempt at the older slice had to be abandoned after the belt
band sat on three windows for over an hour.

The replacement is a spatial hash over positions with a cell edge of one clustering radius.
Any state within the radius in six dimensions is within it in three, so every true
neighbour lies in one of the 27 cells around the centroid's own; those candidates are then
tested with the true six-dimensional distance. Nothing is approximated — the hash only
decides which distances are worth computing, and a hash collision can only add a candidate
to the exact test, never remove one.

Two independent checks that it is exact, one on ground truth and one on production data:

- re-running the full hidden-trkSub validation returns **1,340 exact / 14 partial /
  81 contaminated / 99 missed, 1,824 links, recall 0.8735, precision 0.7456** — every figure
  identical to the run before the change;
- the pre-60000 slice's `neo` band, swept before and after on the same 2.1M arrows, produced
  **372,191 candidates both times** — and took **3,202.6 s before and 1,304.6 s after**.

A 2.5× speedup with a bit-identical candidate set on 372,191 links is the strongest
available evidence that the replacement is a different way of computing the same answer.

---

## 3. Does the widened grid actually reach those populations?

That is a claim about geometry, and it is checkable without waiting for an ITF candidate to
turn up. `itf-linker link-populations` runs M1's Horizons loop pointed at the linker:
ask **JPL Horizons** for astrometric RA/Dec of *real* objects of known class, from a real
observatory code, on real observable nights; hand the linker nothing but directions, rates,
epochs and observer codes; see which come back. All thirteen are observed **jointly**, in
one arrow set, so the run also measures whether a wider grid starts merging unrelated
objects.

NEO targets have their observing run placed at the object's own closest approach — an NEO
spends most of its orbit at main-belt distances, and (1862) Apollo sits at 2.20 AU in March
2024, so testing "can the NEO band find an NEO" at an arbitrary date tests nothing.

| object | class | true r (AU) | M3's grid (1.4–5.6) | M4's bands | found in | hypothesis r |
|---|---|---:|---|---|---|---:|
| (163693) Atira | Atira | 0.70 | **missed** | **exact** | `inner`, **near branch** | 0.771 |
| (2062) Aten | Aten | 0.97 | **missed** | **exact** | `neo` | 0.978 |
| (3200) Phaethon | Apollo | 0.84 | **missed** | **missed** | — | — |
| (433) Eros | Amor | 1.17 | **missed** | **exact** | `neo` | 1.069 |
| (1036) Ganymed | Amor | 1.34 | exact | exact | `belt` | 1.400 |
| (1862) Apollo | Apollo | 1.57 | exact | exact | `belt` | 1.800 |
| (7) Iris | inner belt | 2.64 | exact | exact | `belt` | 2.700 |
| (324) Bamberga | mid belt | 3.39 | exact | exact | `belt` | 3.300 |
| (588) Achilles | Trojan | 4.54 | partial | partial | `belt` | 4.500 |
| (10199) Chariklo | Centaur | 17.29 | **missed** | **exact** | `outer` | 17.464 |
| (2060) Chiron | Centaur | 18.67 | **missed** | **exact** | `outer` | 18.890 |
| (50000) Quaoar | TNO | 42.69 | **missed** | **exact** | `outer` | 43.045 |
| (20000) Varuna | TNO | 44.16 | **missed** | **exact** | `outer` | 44.767 |
| | | | **4 / 13 exact** | **11 / 13 exact** | | |

**Zero objects were merged with a stranger in either run.** The widened grid produces 13
links from 46 arrows where the belt grid produces 6; the extra links are the extra objects,
not extra noise.

**The one genuine miss is (3200) Phaethon, and §2.5 measured why.** At 3 °/day and 0.84 AU
the tightest cluster diameter any hypothesis achieves is ~0.0020–0.0021 AU against a
0.0025 AU radius — *at* the radius rather than inside it, and dominated by the irreducible
spread of the linear `r(t)` model rather than by the grid. Whether a particular grid
alignment recovers it is luck. **The honest statement is that the widened grid reaches NEOs
robustly up to about 1 °/day and marginally at 3 °/day**, and that is reported rather than
tuned away: loosening the radius to catch Phaethon is exactly the move M3 measured as making
everything else worse.

(588) Achilles is "partial" in *both* runs — 3 of its 4 tracklets, on a 16-day arc — so it
is a property of the cadence, not of the widening.

Reproduce with `itf-linker link-populations --bands wide` and `--bands belt`.

---

## 4. Re-validation: does widening cost main-belt recall?

The test is M3's, unchanged: hide the trkSub linkage on the ITF's own designations that
already span 3+ nights, and see whether it comes back. The only difference is which grid
does the re-deriving.

### 4.1 The belt band reproduces M3 exactly

Run first, as a regression check on everything §2.7 changed:

| | M3 | M4 `--bands belt` |
|---|---:|---:|
| Reachable groups (arc inside one window) | 1,546 | 1,546 |
| Collision-screened | 1,534 | 1,534 |
| Recovered exactly | 1,340 | **1,340** |
| Recovered in part, uncontaminated | 14 | **14** |
| Only ever seen mixed with a stranger | 81 | **81** |
| Never touched | 99 | **99** |
| **Recall (exact set match)** | **0.874** | **0.8735** |
| Links produced | 1,824 | **1,824** |
| Precision (lower bound) | 0.746 | **0.7456** |

Identical, row for row. This run was repeated **after** the hashed isolation check of §2.7
landed and returned the same nine numbers again, so all four changes — the indexed
`drop_subsets`, the binary-search window slicing, the hashed isolation check and the new
grazing-ray guard — are confirmed to have changed nothing about M3's answer, which is what
they were required to do.

### 4.2 The first widened run *lost* 20 points of recall, and why

Scored against the **same** 1,534 collision-screened groups, arc cut at 14 days so the
comparison is like for like:

| | M3 / `belt` | wide, cross-band subsets dropped |
|---|---:|---:|
| Recovered exactly | 1,340 | 1,038 |
| Only ever seen mixed with a stranger | 81 | **462** |
| Never touched | 99 | 28 |
| **Recall (exact)** | **0.8735** | **0.6767** |
| Recall (touched at all) | 0.9355 | **0.9817** |
| Links produced | 1,824 | 4,091 |

The shape of that is diagnostic and it is not "the widened grid finds worse groups". *More*
groups are touched, not fewer — 0.982 against 0.936 — while five times as many end up
contaminated. That is the signature of **suppression**, and §2.7's subset rule is the
suppressor: a NEO-band proposal that is the true group *plus one neighbour* is a proper
superset of the correct belt-band link, so the correct link is deleted and the contaminated
one kept. M3 saw the same mechanism from the other side in its §5.3, where removing
contaminated supersets *improved* recall by 0.0013.

The fix is to stop adjudicating between bands before any orbit exists (§2.7). Subsets are
still dropped **within** a band, exactly as M3 had it.

### 4.3 With that fixed, widening *raises* recall by 5.7 points

| | M3 / `belt` | M4 `--bands wide` |
|---|---:|---:|
| Truth groups (collision-screened, arc ≤ 14 d) | 1,534 | 1,534 |
| Recovered exactly | 1,340 | **1,427** |
| Recovered in part, uncontaminated | 14 | 25 |
| Only ever seen mixed with a stranger | 81 | 72 |
| **Never touched** | **99** | **28** |
| **Recall (exact set match)** | **0.8735** | **0.9302** |
| Recall (exact or clean partial) | 0.8827 | 0.9348 |
| Recall (touched at all) | 0.9355 | 0.9817 |
| Links produced | 1,824 | 4,609 |
| **Precision (lower bound)** | **0.7456** | **0.3205** |

**87 more of the ITF's own groupings are re-derived exactly, and the never-touched set falls
from 99 to 28.** That was not the aim of widening — the aim was to reach populations M3
could not — but it is a real effect with a plain cause: the bands do not share a window
length, so a group that straddles every 14-day boundary at a 3.5-day step is offered a
different set of boundaries by the 7.75-day and 21-day bands. Overlapping windows were
already worth 5 points of recall in M3 (§5.4); overlapping *bands* are worth another 6.

**The cost is real and is in the last row.** 4,609 links against 1,824, and the precision
floor drops from 0.746 to 0.321. As M3 established in its §4.4 that figure counts every
genuine cross-trkSub link as an error, so it is a floor rather than an estimate — but the
2.5× link count is not a measurement artefact. **It is 2.5× as much Find_Orb time**, and
that is the price of the extra recall.

### 4.4 The known comet in the ITF, which M3 said could not be found

M3's §4.5 named `0073P-C` — comet 73P/Schwassmann-Wachmann 3 fragment C, the object M1
independently found sitting in the ITF — as a miss it could explain but not fix: *"In
April–May 2006 it was ~0.07 AU from Earth. The grid runs 1.4–5.6 AU. It cannot be found,
and finding it would mean the grid was admitting geometry it should not."*

It is recovered. Run on its own three tracklets:

| grid | links | verdict |
|---|---:|---|
| `belt` (M3's 1.4–5.6 AU) | 0 | not found, exactly as M3 predicted |
| `wide` (M4) | 1 | **exact — all 3 tracklets, 3 nights, 4.96-day arc**, `neo` band, hypothesis r = 1.038 AU |

Its true heliocentric distance in May 2006 was ~1.03 AU and its sky motion 2.5–4.2 °/day,
so this is simultaneously the fastest mover in this milestone and the clearest evidence
that the widened band reaches real geometry rather than merely more of it. It is also why
`0073P-C` disappears from the missed list in §4.3.

It is worth reconciling with §3, where a 3 °/day Phaethon was *not* recovered: **sky rate
alone is not what decides this**. The quantity that matters is the transverse velocity
error, `δρ · μ`, and 73P-C sat at a topocentric distance of 0.07 AU where `δρ · μ` is small
however fast it appears to move, while Phaethon sat at 0.15 AU in a geometry that amplifies
`δr` into `δρ` threefold (§2.5). A fast mover very close to the observer is easy; a fast
mover near the grazing ray is not.

---

## 5. The new slice (MJD > 60000), widened

Same 511,274 arrows M3 swept, same bad-data filter, same clustering radius. Only the
hypothesis space changed.

### 5.1 The sweep

| | M3 (`belt` only) | M4 (`wide`) |
|---|---:|---:|
| Arrows | 511,274 | **511,274** |
| Hypotheses | 387 | **2,555** |
| Window–hypothesis sweeps | 1.4 × 10⁵ | **1.8 × 10⁶** |
| Tracklet states computed, propagated, clustered | ≈ 7.9 × 10⁸ | **≈ 5.2 × 10⁹** |
| Wall clock | 3 min 31 s (20 workers) | **7 min 31 s** (16 workers) |
| Raw clusters | 1,669,476 | 3,556,851 |
| Neighbourhoods refused as non-discriminating | 1,427,490 | **129,149,057** |
| Clusters rejected by the global isolation check | 103,780 | 1,277,383 |
| **Distinct links proposed** | **17,060** | **50,236** |

**No triplet is enumerated anywhere**, exactly as in M0's constraint and M3's
implementation. Five billion states in seven and a half minutes on a laptop.

Per band, and the number that explains all of it — how many of a window's arrows produce a
*valid* state under one hypothesis of that band (busiest window of each):

| band | windows | hypotheses | raw clusters | refused | links | valid states / arrows | elapsed |
|---|---:|---:|---:|---:|---:|---|---:|
| `inner` | 987 | 1,430 | 66 | 0 | **1** | 3.1 / 907 = **0.3%** | 16 s |
| `neo` | 646 | 234 | 1,802,838 | 127,721,567 | 38,671 | 2,859 / 6,636 = 43% | 185 s |
| `belt` | 359 | 387 | 1,669,476 | 1,427,490 | **17,060** | 21,834 / 23,425 = 93% | 220 s |
| `outer` | 240 | 504 | 84,471 | 0 | 640 | 1,748 / 14,821 = 12% | 29 s |

**The belt band produced 17,060 links and refused 1,427,490 neighbourhoods — M3's numbers
to the digit.** That is the strongest available check that the widened pipeline did not
disturb what M3 measured.

Three things in that table are worth saying out loud.

**The `inner` band is essentially empty, and that is physics rather than a bug.** An object
at 0.55–0.94 AU is only visible at solar elongation below about 50°, and 0.3% of the arrows
in a window can be placed there at all. 1,430 hypotheses over 987 windows produced **66 raw
clusters and one link**, which did not survive the pre-fit gate. Searching interior to the
Earth costs 16 seconds and finds nothing, because the ITF barely contains twilight
astrometry.

**The refusal count explodes in the NEO band — 127.7 million neighbourhoods declined,
90× the belt band's** — and that is the honest answer to "should the crowded fields be
handled instead of declined?" (M3's own ranked improvement #2). At 1.0–1.44 AU the
topocentric distance is small, so propagated states compress and *every* neighbourhood
becomes contested. Widening the grid makes the crowded-field problem substantially worse,
not better. Nothing here weakened the three structural rules, and the numbers are why.

**The `outer` band is cheap and quiet.** 12% state validity, 84,471 raw clusters, zero
refusals and zero isolation rejections in 29 seconds: at 5.6–48 AU, tracklets that
propagate to a common state are genuinely rare, so the neighbourhoods are never crowded.

### 5.2 The published pre-fit gate

| Stage | Links | Cross-observatory | Joins > 1 trkSub |
|---|---:|---:|---:|
| Proposed (merged, deduplicated) | **50,236** | 35,515 | 49,190 |
| Pass the MPC's published pre-fit gate | **40,623** | **30,145** | 39,901 |

Rejections: **9,612 for arc < 3 days**, and — for the first time in this project — **one
for "exactly 3 nights with an arc over 15 days"**. M3 called that rule structurally
impossible to trigger, correctly: a 14-day window cannot produce a 15-day arc. The outer
band's 21-day window can, and once in 50,236 links it did.

Gated links by band: `neo` 29,579 · `belt` 10,939 · `outer` 105 · `inner` none (its single
proposal was also found, more tightly, by the `neo` band).

Those band labels are *post-merge* and should be read as "which band's hypothesis described
this link best", not "which band found it". The belt band produced M3's 17,060 proposals;
13,463 of them still carry the belt label afterwards and 3,597 are relabelled, because when
two bands propose the identical tracklet set the merge keeps the tighter one and its label.
Nothing is deleted by that — the total is still 50,236 = 56,372 per-band proposals minus
6,136 exact duplicates across bands.

**30,134 links are both cross-observatory and an association nobody had made** — against
M3's 10,161. That is the raw target set, before any orbit exists.

### 5.3 Fitting, and what survives

All 40,623 gated links were fitted with Find_Orb — **90 minutes of wall clock on 18–20
concurrent workers**, no invocation failures. Coverage is complete; nothing in this section
is a sample.

| Stage | Links | | |
|---|---:|---|---|
| Gated and submitted | 40,623 | | |
| Fitted | **40,623** | 100% | |
| Converged | **11,113** | 27.4% | 29,293 produced no covariance, 217 were unbound |
| …with RMS ≤ 0.25″ | 4,801 | 11.8% of submitted | |
| Rejected by the "one orbit fits all of it" guard | **9,383** | **84.4% of converged** | M1's supplementary check |
| **Pass every gate — published and supplementary** | **254** | **0.63%** | |
| …minus links contesting a tracklet with a better fit | −29 | | conflict resolution |
| **Survivors** | **225** | | |

**The funnel is steeper than M3's at every stage, and that is the honest cost of the widened
grid.** M3's proposals converged 43.7% of the time and 1.5% survived; these converge
**27.4%** and **0.55%** survive. The proposals are worse on average because most of the new
hypotheses sit at distances where the geometry is less discriminating — tracklets that agree
at 1.1 AU agree for many more reasons than tracklets that agree at 2.7 AU.

| | M4 survivors | M3, same slice |
|---|---:|---:|
| Total | **225** | 199 |
| **Cross-observatory** | **80** | 73 |
| Same-observatory | 145 | 126 |
| Join more than one trkSub (a new association) | 150 | 127 |
| **Cross-observatory *and* a new association** | **80** | 73 |
| Nights per link | 3: 134 · 4: 79 · 5: 12 | 3: 136 · 4: 58 · 5: 5 |
| Observatory codes per link | 1: 145 · 2: 57 · 3: 23 | 1: 126 · 2: … |
| Median RMS | 0.117″ | 0.111″ |
| Median `a` | 2.71 AU (range 1.42–84.4) | 2.68 AU (range 1.42–203.6) |

**Three times the hypotheses bought 26 extra survivors and 7 extra cross-observatory ones.**
That is the plainest statement of what widening the distance grid is worth on this slice,
and it is far smaller than §4.3's recall gain would suggest. The reason is in the next two
tables.

#### The population breakdown — the question the widened grid was built to answer

| Population | Survivors | Converged fits | |
|---|---:|---:|---|
| **NEO (q < 1.3 AU)** — Aten 0 / Apollo 0 / **Amor 2** | **2** | **5,547** (147 Aten, 3,688 Apollo, 1,712 Amor) | **both found by the `belt` band** |
| Mars-crosser | 1 | 582 | |
| Hungaria | 5 | 41 | |
| Main belt (inner 47 / middle 88 / outer 59) | 194 | 4,317 | the population all-sky surveys re-detect constantly |
| Cybele–Hilda | 5 | 404 | |
| Jupiter Trojan | 4 | 54 | |
| **Centaur** | **5** | 67 | ⚠ σ(a) = 1.05–24.6 AU |
| **TNO** | **6** | 24 | ⚠ σ(a) = 10.6–96.1 AU |
| other bound | 3 | 77 | |

#### Two NEO-class survivors, and neither came from a NEO band

| id | codes | class | `a` ± σ(a) | `e` | **`q` ± σ(q)** | nights / arc | RMS | used | hypothesis r |
|---|---|---|---|---:|---|---|---:|---|---:|
| `lnk0c2l` | **F51 + O18** | Amor | 1.4245 ± 0.0074 | 0.230 | **1.0966 ± 0.0021** | 3 / 9.30 d | 0.125″ | 11/12 | **1.40 AU (`belt`)** |
| `lnk0uhl` | F51 | Amor | 3.3622 ± 0.0265 | 0.663 | **1.1348 ± 0.00038** | 3 / 10.93 d | 0.203″ | 9/11 | **1.70 AU (`belt`)** |

These carry the best-constrained perihelia in the entire survivor set — σ(q) of 0.0021 and
0.00038 AU against the MPC's 0.05 AU limit — and both meet all four σ limits. One is
cross-observatory (Pan-STARRS-1 + O18).

**Both were found by hypotheses at 1.40 and 1.70 AU, inside M3's own grid.** An Amor
observed away from perihelion sits at a main-belt *distance* even though its perihelion is
inside 1.3 AU, so it was always reachable: M3's survivor set had the same minimum semimajor
axis (1.42 AU) and simply never classified its output by population. **The NEO-distance
bands are not what found these — the orbit classifier is.** That is a real M4 contribution
and a different one from the one the milestone set out to make.

**The NEO bands themselves produced 3,835 converged Aten and Apollo orbits and zero
surviving NEOs.** §9 is about why.

#### The eleven beyond-belt survivors, σ first

Sorted by σ(a), because the semimajor-axis column is unreadable without it:

| id | band | class | `a` | **σ(a)** | σ(a)/a | `e` | `q` | nights / arc | codes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| `lnk11zn` | `belt` | TNO | 84.37 | **± 96.1** | **114%** | 0.934 | 5.60 | 5 / 6.85 d | X05 |
| `lnk11zo` | `neo` | TNO | 58.13 | **± 37.5** | 65% | 0.584 | 24.19 | 5 / 6.01 d | X05 |
| `lnk1208` | `neo` | TNO | 47.39 | **± 25.6** | 54% | 0.448 | 26.15 | 4 / 6.10 d | X05 |
| `lnk0ruy` | `belt` | Centaur | 20.84 | **± 24.6** | **118%** | 0.900 | 2.09 | 4 / 3.12 d | O18 |
| `lnk11zm` | **`outer`** | TNO | 42.49 | **± 18.1** | 43% | 0.102 | 38.15 | 5 / 9.04 d | X05 |
| `lnk1209` | `neo` | TNO | 41.08 | **± 17.3** | 42% | 0.137 | 35.47 | 4 / 6.08 d | X05 |
| `lnk11zj` | `neo` | TNO | 34.14 | **± 10.6** | 31% | 0.664 | 11.48 | 5 / 4.04 d | X05 |
| `lnk1205` | `belt` | Centaur | 18.30 | ± 8.06 | 44% | 0.545 | 8.32 | 4 / 4.02 d | X05 |
| `lnk1207` | `belt` | Centaur | 23.72 | ± 7.71 | 33% | 0.714 | 6.79 | 4 / 6.79 d | X05 |
| `lnk0rl2` | `neo` | Centaur | 5.54 | ± 1.51 | 27% | 0.163 | 4.64 | 5 / 5.07 d | O18 |
| `lnk0ru6` | `belt` | Centaur | 5.69 | ± 1.05 | 18% | 0.375 | 3.56 | 4 / 4.03 d | O18 |

**Not one of these has a measured semimajor axis.** The best is uncertain by 18% of its own
value and two by more than 100% — `lnk11zn` is 84 ± 96 AU, which is a way of writing
"possibly unbound". None meets the MPC's σ(a) < 0.05 AU limit, and none has to, because that
limit is scoped to *exactly*-three-night links and every one of these is a four- or
five-night link (§5.4). **They survive the published criteria on how those criteria are
scoped, not because their orbits are known.**

Two further facts finish the picture:

- **Nine of the eleven are single-observatory, and eight of those are X05 — Rubin.** That is
  the composition warning M2 raised (91 of M1's 128 carried the Rubin `RL` prefix) and M3
  repeated (63 of its 72 re-derived associations were X05 alone). A single-observatory Rubin
  link is that survey's own unlinked internal tracking, which Rubin will link itself.
- **Only `lnk11zm` was both proposed at a distant hypothesis and fitted to a distant orbit.**
  The rest were proposed inside 5.6 AU and the fit ran away to a large, unconstrained `a` —
  M3 recorded the identical shape in its §6.6 with a five-night link at *a* = 203.5 AU.

So the defensible statement is **not** "M4 found eleven distant objects". It is: **the outer
band produced exactly one link whose distant hypothesis and distant fit agree, it is
Rubin-only, and its semimajor axis is uncertain by 43%.** The vetting layer reached the same
verdict independently — §7.3 shows nine of the seventeen unmatched candidates were rejected
as `orbit_too_poorly_constrained` rather than for having no catalogue neighbour, and they
are these.

#### The survivors whose fitted arc is shorter than their link's

M1's guard credits a solution that used ≥ 80% of the observations and still spans three
nights. Across the 225 survivors, 154 used **every** observation they were given; but 27
have a fitted arc under 60% of the link's arc, which means Find_Orb discarded a whole end
tracklet and still passed. That is M1's threshold behaving as specified — it was not changed
here — and it is a weakness of those links rather than a defect of the guard. It is reported
because a reader comparing `arc_days` (Find_Orb's, over the observations it used) against
`prefit_arc_days` (the link's) would otherwise think the pre-fit gate had leaked.

### 5.4 The published σ limits, applied to every survivor

M1's §7 and M3's §6.6 both found the same thing and it reproduces exactly: the MPC's σ
limits are scoped to **exactly**-three-night links, so a four- or five-night fit is judged
on RMS alone.

| | M4 | M3 |
|---|---:|---:|
| Three-night survivors meeting all four σ limits | **134 of 134** | 136 of 136 |
| Four- and five-night survivors meeting them | **6 of 91** | 5 of 63 |
| **All survivors meeting all four σ limits** | **140 of 225** | 141 of 199 |
| …of the cross-observatory survivors | **60 of 80** | 60 of 73 |

The three-night rows are 100% by construction — the gate tests them. The interesting row is
the last: **the widened grid added 26 survivors and not one additional well-constrained
one.** 140 against M3's 141, and 60 cross-observatory against M3's 60. Every extra survivor
the widened grid produced is a four- or five-night link that the σ limits never examine.

**The numbers are reported rather than filtered**, as M3 did: the criteria are the MPC's,
the ranking is ours, and a five-night link with σ(a) = 96 AU sorts to the bottom on its own.

---

## 6. The older slice (MJD < 60000)

M3 left it alone for a stated reason: follow-up on a 2015 candidate is no longer physically
possible. **Identification does not require follow-up**, and the older slice is 4× the
search space already covered — 7,489,703 of the ITF's 9.3M observations against the new
slice's 1,831,784.

Two things about it are different in kind, not just in size, and both had to be handled
before a single window could be swept.

**It spans 122 years, not 3.4.** The earliest surviving observation is MJD 15431
(1900-11-27), though 99.3% of the slice is after 2000. The number of windows scales with
that *span* while the arrow table scales with the slice's *size*, which is what made the
full-scan window slicing of §2.7 fatal here and merely invisible on MJD > 60000.

**Its densest fields are denser than anything M3 saw.** The archival deep-drilling era puts
**41,068 arrows inside a single 14-day window**, against 23,425 for the busiest window of
the new slice, and the group count per hypothesis rises with it. That is what broke the
old `groups × arrows` isolation check (§2.7) — the first attempt at this slice was abandoned
after the belt band sat on three windows for over an hour — and it is why the hashed
replacement was necessary rather than merely nice.

### 6.1 The sweep

| | new slice (MJD > 60000) | **older slice (MJD < 60000)** |
|---|---:|---:|
| Observations | 1,831,784 | **7,489,703** |
| Tracklets built | 512,005 | 2,103,056 |
| …**arrows** | 511,274 | **2,098,373** |
| Hypotheses | 2,555 | 2,555 |
| Wall clock | 7 min 31 s (16 workers) | **49 min** (12 workers) |
| Raw clusters | 3,556,851 | **36,555,745** |
| Neighbourhoods refused as non-discriminating | 129,149,057 | **899,854,715** |
| Clusters rejected by the global isolation check | 1,277,383 | 16,315,668 |
| **Distinct links proposed** | 50,236 | **567,838** |
| **Past the MPC's published pre-fit gate** | 40,623 | **412,929** |
| …cross-observatory | 30,145 | **69,502** |

Arrows lost, and why: 37,894 space-based `S` observations (150× the new slice's 248 —
NEOWISE and other spacecraft dominate the archival record), 2,737 single-detection
tracklets, 1,944 with an implausible fitted rate, 63 observations from sites with no
published coordinates, 2 tracklets spanning more than 12 hours. Total loss 0.22%.

Per band:

| band | windows | links | refusals | elapsed |
|---|---:|---:|---:|---:|
| `inner` | 8,161 | **8** | 48 | 112 s |
| `neo` | 5,557 | 372,191 | 832,259,783 | 1,305 s |
| `belt` | 3,293 | 263,828 | 67,195,259 | 1,325 s |
| `outer` | 2,260 | 5,640 | 399,625 | 180 s |

**The older slice is where the linkable structure is, by an order of magnitude.** 11.3× the
proposals and 10.2× the gated links of the slice M3 searched, from 4.1× the observations —
because those observations are packed into fewer, deeper fields. Every one of the 154,909
gate rejections was for arc < 3 days; nothing failed any other published criterion.

The `inner` band produced **8 links from 8,161 windows and 1,430 hypotheses**, of which none
passed the gate. Combined with the new slice's 1, that is the complete answer for
0.55–0.94 AU: **nine proposals and no candidates from the entire 9.3-million-observation
file.** Searching interior to the Earth costs about two minutes and finds nothing, because
the ITF barely contains twilight astrometry — only 0.3% of the arrows in a window can be
placed at those distances at all.

The observatory pairings are quite different from the new slice's, and are the reason this
slice was worth sweeping at all:

| Codes | Links | | Codes | Links |
|---|---:|---|---|---:|
| F51 + G96 | 15,632 | | 691 + G96 | 4,373 |
| F51 + F52 | 6,179 | | F51 + W84 | 2,875 |
| F51 + F52 + G96 | 5,653 | | 691 + F51 | 2,211 |
| F52 + G96 | 5,238 | | 703 + G96 | 1,772 |

691 (Spacewatch), 703 (Catalina's older Schmidt), 705 (Palomar), W84 (DECam) and T09
(Subaru) appear here and essentially not at all in the post-2023 slice. **These are
cross-survey, cross-decade associations that no single archive is positioned to make**, and
they are exactly what the ITF exists to make possible.

### 6.2 Fitting: a stated 1.1% sample, not a search

**412,929 gated links is roughly 15 hours of Find_Orb on this machine, which was not
available.** Rather than truncate silently, a **prioritised subset of 4,461 links — 1.08% of
the gated set — was selected by an explicit rule and fitted**: every `outer`-band link
(461, i.e. all of them), plus the 2,000 best-ranked `neo`-band and 2,000 best-ranked
`belt`-band links, ranking within each band by the production criteria (cross-observatory
first, then a new association, then more nights, then a tighter cluster).

**This is a sample of the best-conditioned links, not a random one, and the numbers below
describe it and nothing else.** Two consequences follow and are stated rather than left to
inference:

- **Survivor *counts* below are lower bounds on the older slice** by a large and unknown
  factor — the unfitted 99% contains links of the same kind.
- **Survivor *rates* below are upper bounds**, because the sample is deliberately the
  best-conditioned part of the set.

The `outer` band is the one exception: **all 461 of its gated links were fitted**, so its
result is a result about the older slice and not about a sample of it.

To be unambiguous about the two different senses of "complete" in play: **the 4,461-link
sample was itself fitted to completion** — 112 of 112 `fo` chunks, every one carrying a
parseable `total.json`, nothing truncated and nothing silently half-fitted. What is a sample
is *which links were fitted*, not *how thoroughly they were fitted*.

### 6.3 What survived, and why the older slice is the better half of the file

12 minutes of Find_Orb on 24 workers, 112 of 112 chunks, none truncated.

| Stage | Links | | new slice, for comparison |
|---|---:|---|---|
| Submitted and fitted | 4,461 | 100% | 40,623 |
| Converged | **1,738** | **39.0%** | 27.4% |
| …with RMS ≤ 0.25″ | 806 | 18.1% | 11.8% |
| Rejected by the "one orbit fits all of it" guard | **874** | **50.3% of converged** | 84.4% |
| **Pass every gate — published and supplementary** | **118** | **2.6%** | 0.63% |
| …minus links contesting a tracklet | −12 | | −29 |
| **Survivors** | **106** | | 225 |

**The older slice converges better, survives better, and fails M1's subset guard at half the
rate.** That is the opposite of what "older, harder, unfollowable data" would predict, and
the reason is in the next table.

| | older slice | new slice |
|---|---:|---:|
| **Cross-observatory survivors** | **100 of 106 — 94%** | 80 of 225 — 36% |
| Same-observatory survivors | **6** | 145 |
| Join more than one trkSub | 106 — **all of them** | 150 |
| Meeting all four σ limits | **73 of 106 — 69%** | 140 of 225 — 62% |
| …of the cross-observatory ones | **69 of 100** | 60 of 80 |
| Nights per link | 3: 66 · 4: 35 · 5: 5 | 3: 134 · 4: 79 · 5: 12 |

**Ninety-four per cent of the older slice's survivors span two or more observatories, against
thirty-six per cent of the new slice's.** Only six are single-observatory at all — four T09
(Subaru), one W84, one 568 (Mauna Kea). Every single one of the 106 joins tracklets carrying
different trkSubs, so there is no re-derivation of an association somebody had already made.

That is the ITF's stated purpose finally showing up in the output. The post-2023 slice is
dominated by two surveys that already link their own data — 83 of its 225 survivors are
Rubin alone and 46 are O18 alone — whereas the archival record is genuinely multi-survey, and
its links join F51 to T09, 703 to W84, 705 to G96, 620 to 644, 291 to 691. **M3's ranking put
cross-observatory links first on the argument that they are the part nobody else is
positioned to make; the older slice is where they actually are.**

#### Population breakdown

| Population | Survivors | Converged fits |
|---|---:|---:|
| **NEO (q < 1.3 AU)** — Aten 0 / Apollo 0 / Amor 0 | **0** | **482** (35 Aten, 291 Apollo, 156 Amor) |
| Mars-crosser | 0 | 68 |
| Hungaria | 1 | 8 |
| Main belt (inner 32 / middle 47 / outer 15) | 94 | 976 |
| Cybele–Hilda | 3 | 82 |
| Jupiter Trojan | 2 | 34 |
| **Centaur** | **5** | 39 |
| **TNO** | **0** | 2 |
| other bound | 1 | 47 |

**Zero NEO survivors again, from 482 converged near-Earth orbits** — 35 Aten, 291 Apollo,
156 Amor. The pattern of §9 repeats exactly on a completely different population of
observations, spanning 1995–2023 instead of 2023–2026, and with a subset guard rejecting
half rather than five-sixths. **Two independent slices, 6,029 converged NEO-class orbits
between them, and two surviving Amors, both of which M3's narrower grid could already
reach.**

**Zero TNO survivors** — only two TNO-class orbits converged at all, and neither passed.

#### The five beyond-belt survivors, σ first

| id | band | class | `a` | **σ(a)** | σ(a)/a | `q` ± σ(q) | nights / arc | used | codes | epoch |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| `lnk2a3j` | **`outer`** | Centaur | 22.74 | **± 0.94** | **4.1%** | 5.071 ± 0.017 | 4 / 8.07 d | **15/15** | T09 | 2015-07 |
| `lnk034r` | **`outer`** | Centaur | 6.00 | **± 0.20** | **3.4%** | 4.666 ± 0.88 | 4 / 12.10 d | **13/13** | 620 + 644 | 2002-07 |
| `lnk035d` | `belt` | Centaur | 5.84 | ± 1.17 | 20% | 2.951 ± 0.93 | 4 / 4.24 d | 8/8 | 304 + 568 | 2021-10 |
| `lnk034f` | `neo` | Centaur | 6.05 | ± 1.51 | 25% | 5.176 ± 0.71 | 4 / 3.35 d | 8/8 | 304 + 568 | 2021-10 |
| `lnk2aqg` | `outer` | Centaur | 24.70 | ± 12.6 | 51% | 10.73 ± 2.32 | 4 / 5.01 d | 10/10 | 568 | 2008-07 |

**`lnk2a3j` is the best-constrained distant candidate in the entire milestone**: a Centaur
at 22.74 ± 0.94 AU — 4.1% — found by the `outer` band at a distant hypothesis, fitted with
**every one of its 15 observations used**, RMS 0.118″, on an 8-day four-night arc. Its
perihelion is determined to 0.017 AU. Compare the new slice's best distant candidate, which
is uncertain by 43%.

`lnk034r` is second and is **cross-observatory** — 620 (Steward's Kuiper telescope) and 644
(Palomar NEAT) in July 2002, a 12-day arc, all 13 observations used, σ(a)/a = 3.4%. Two
telescopes, one object, twenty-four years ago, never previously associated — **and §7.4
identifies it as comet 29P/Schwassmann-Wachmann 1**, matched to 1.2″ at every epoch and
agreeing with JPL's catalogue orbit to 1.3σ on all four elements. It is therefore not an
unreported candidate; it is the second known comet this linker has assembled, and the
strongest single piece of evidence in this milestone that the older slice's links are real
objects.

The remaining three are weaker and are labelled as such: 20%, 25% and 51% in σ(a)/a. The
last, `lnk2aqg`, is single-observatory and uncertain by half its own value; it is reported
because it survived, not because it is convincing.

None of the five is a TNO and none is an NEO. **They are Centaurs at 5.8–24.7 AU**, which is
the population the `outer` band was built for, and two of them are genuinely well determined
— which is more than the new slice produced. One of those two turns out to be a comet
somebody catalogued in 1927.

#### The caveat that governs all of these numbers

Every figure in §6.3 describes **4,461 links, 1.08% of the 412,929 the older slice gated**,
selected as the best-ranked within each band. Survivor **counts** are therefore lower bounds
on the older slice by a large and unknown factor; survivor **rates** are upper bounds,
because the sample was deliberately the best-conditioned part of the set. The one exception
is the `outer` band, all 461 of whose gated links were fitted: **7 survivors from 461 links
is a complete result about Centaur and TNO distances in the pre-2023 ITF**, and it contains
two well-determined Centaurs and no TNOs.




---

## 7. Vetting

### 7.1 The controls, first and from cache

M2's positive controls were re-run before anything else, entirely from the disk cache:
**7 of 7 pass**, with the same separations M2 and M3 measured — including `0073P-C`, the
known comet sitting in the ITF, at 32.842″ (large because the astrometry is from the 2006
disintegration and drifts from the catalogue ephemeris across the arc). A vetting layer
that cannot identify an object whose identity is already known has nothing useful to say
about one whose identity is not.

| Control | Expected | Identified | Best separation |
|---|---|---|---:|
| `0073P-C` (the ITF's known comet) | 73P-C | **73P-C** | 32.842″ |
| (433) Eros [NEO] | 433 | **433** | 1.986″ |
| (7) Iris [inner main belt] | 7 | **7** | 0.893″ |
| (588) Achilles [Jupiter Trojan] | 588 | **588** | 0.261″ |
| (7) Iris via X05 Rubin, 2025 | 7 | **7** | 0.921″ |
| (433) Eros via W84 DECam, 2025 | 433 | **433** | 0.878″ |
| (588) Achilles via O18, 2025 | 588 | **588** | 0.122″ |

### 7.2 SBIDENT was run this time, and it has a hard epoch limit

M3 skipped JPL SBIDENT entirely for throughput, and flagged that as a real gap: element-based
identification catches what positional cone searches miss. It was run here.

**It cannot be run on most of the older slice, and that is a measured limit rather than a
choice.** SBIDENT's two-pass identification pre-filters with a two-body propagation whose
positional error grows without bound, so the number of first-pass rows the second pass must
integrate climbs by ~50× over two decades — 5,355 rows at a 2023 epoch, 93,390 at 2014,
308,897 at 2006 (measured in M2). `vet/sbident.py` refuses any epoch more than **9 years**
old before sending the request, because past that the query does not return inside 200 s.

Today that cut falls at **2017-08**. The MJD > 60000 slice is entirely inside it, so every
new-slice candidate gets the third opinion. The pre-60000 slice is **55.7% outside it** —
4,169,172 of its 7,489,703 observations predate MJD 57900 (2017-05), which brackets the cut
closely enough for the conclusion — so for most older-slice candidates the third opinion is
structurally unavailable and the verdict rests on SkyBoT, MPChecker and SBDB alone. That is
stated on every older-slice verdict below.

### 7.3 The new slice: what the vetting found

**20 of the 225 new-slice survivors were vetted**, chosen by a stated rule rather than by
rank alone so that the pass covers what M4 actually claims: **every** survivor from a band
M3 could not search (`outer`, 2), **every** survivor with a fitted orbit beyond the belt
(8 more), **every** NEO-class survivor by fitted perihelion (0 at the time of selection),
the 6 best-conditioned cross-observatory links from the `neo` band, and the 4
best-conditioned cross-observatory links from the `belt` band for comparability with M3.

**All four services ran on all 20, SBIDENT included.** 68 minutes, 132 live requests:

| Service | Live requests | Cache hits | Failures |
|---|---:|---:|---:|
| SkyBoT (IMCCE) | 38 | 22 | 0 |
| MPChecker (MPC) | 38 | 22 | 2 |
| **JPL SBIDENT** | **28** | 8 | 0 |
| JPL SBDB | 28 | 34 | 0 |

No service was disabled and the failure budget was not touched — a materially cleaner run
than M3's, which saw 13 SkyBoT retries, 2 SkyBoT failures and 6 MPChecker failures. **M3 ran
no SBIDENT at all and named that a real gap; it is closed here.**

| Category | Links |
|---|---:|
| unmatched | **17** |
| known | **2** |
| ambiguous | 1 |

**Unmatched, by reason — and the split is the informative part:**

| Reason | Links |
|---|---:|
| `no_catalogue_object_near_astrometry` | 8 |
| **`orbit_too_poorly_constrained`** | **9** |

**Nine of the seventeen were never even queryable.** The vetting layer refuses to ask a
catalogue about an orbit whose own uncertainty exceeds the search radius, and those nine are
exactly the beyond-belt links of §5.3 — the ones with σ(a) between 1.5 and 96 AU. **That is
an independent instrument reaching the same verdict this report reached from the σ column**,
and it is worth more than either alone: the demotion of those candidates is not a judgement
call made in the write-up, it is what the pipeline itself concluded.

#### The two identifications, re-derived

| Link | Codes | Nights | Resolves to | Best separation | Epochs matched |
|---|---|---:|---|---:|---|
| `lnk01ki` | F51 + O18 | 4 | **2026 OB4** | **0.536″** | 3 of 3 |
| `lnk01kg` | F51 + O18 | 4 | **2026 DK65** | **0.693″** | 3 of 3 |

**These are M3's two identifications, found again by a differently-configured pipeline.**
M3 reported `lnk00do` → 2026 OB4 at 0.536″ and `lnk00dm` → 2026 DK65 at 0.693″; the link
identifiers differ because they are assigned by position in a run's output, but the
observatory pairs, the night counts, the resolved objects and the separations are identical
to the milliarcsecond. A grid three times denser, a different merge rule, four rewritten
routines and a re-run vetting pass reproduced both.

That matters twice over. It is the strongest regression evidence in the milestone that the
widened pipeline still assembles the same real objects. And it carries M3's warning forward
undiluted: **two of the twenty best candidates in this pass are catalogued minor planets.**
There is no evidence the other eighteen differ in kind rather than only in how well three
catalogue services could recognise them from a short arc.

The one ambiguous verdict, `lnk0ry0`, resolved toward `733050` at 16.3″ on 1 of 3 epochs —
well short of the ≥ 2-epoch agreement rule — and is recorded as ambiguous rather than
promoted.

#### What this section does not establish

Not that 17 links are new objects. `unmatched` is the weakest claim the evidence supports,
and for 9 of the 17 it means "this orbit is too poorly determined to ask the question at
all", which is weaker still. Not that the other 205 survivors would behave the same way —
they were not vetted, and the 20 that were are the best-conditioned in the set. And not that
the ITF's own composition has stopped mattering: **83 of the 225 survivors are X05 (Rubin)
alone and 46 are O18 alone**, which is one survey's unlinked internal tracking in both
cases, and is exactly why the ranking puts cross-observatory links first.


### 7.4 The older slice: a second known comet, and the SBIDENT limit in practice

**10 of the 106 older-slice survivors were vetted** — all five whose fitted orbit lies
beyond the belt, plus the five best-constrained cross-observatory links by σ(a). 24 minutes,
97 live requests, no service disabled:

| Service | Live requests | Cache hits | Retries |
|---|---:|---:|---:|
| SkyBoT (IMCCE) | 29 | 1 | 0 |
| MPChecker (MPC) | 30 | 1 | 1 |
| **JPL SBIDENT** | **10** | 0 | 0 |
| JPL SBDB | 28 | 7 | 0 |

| Category | Links |
|---|---:|
| unmatched | **9** |
| **known** | **1** |
| ambiguous | 0 |

**Unmatched, by reason:** `no_catalogue_object_near_astrometry` 6 · `orbit_too_poorly_constrained` 3.
The three refused as poorly constrained are `lnk035d`, `lnk034f` and `lnk2aqg` — precisely
the three beyond-belt survivors §6.3 flagged at σ(a)/a of 20%, 25% and 51%. **The vetting
layer refused to query exactly the candidates the σ column said not to trust**, on both
slices independently.

#### `lnk034r` is comet 29P/Schwassmann-Wachmann 1

| | |
|---|---|
| Link | `lnk034r` — 4 tracklets, 4 nights, **620 (Steward, Kuiper) + 644 (Palomar NEAT)** |
| Epochs | **2002-07-06 to 2002-07-18**, a 12.10-day arc |
| Fit | all **13 of 13** observations used, RMS 0.171″ |
| Fitted orbit | `a` = 6.000 ± 0.203 AU, `e` = 0.222, `q` = 4.666 ± 0.88 AU, `i` = 10.25° |
| Identification | **29P/Schwassmann-Wachmann 1**, a Jupiter-family comet |
| Astrometric agreement | **1.234″–1.365″ at 3 of 3 epochs** |
| Element agreement | Δ`a` = −0.046 AU (0.22σ), Δ`e` = 0.178 (1.03σ), Δ`i` = 0.886° (1.11σ), Δ`q` = −1.109 AU (1.26σ) — **consistent to 1.3σ of the fitted orbit** |

This is the second known comet the linker has recovered, and it is a stronger result than
73P-C in two respects: it is **cross-observatory**, joining two telescopes that observed it
twelve days apart in 2002 and never associated the tracklets; and it is corroborated in
**element space as well as position space** — the fitted orbit agrees with JPL's catalogue
orbit to within the fit's own uncertainties on all four elements, which a chance alignment
of four tracklets does not do.

**One tempting claim about it is wrong, and worth stating so it is not repeated.** 29P sits
near 6 AU, and it would be neat to say M3's 1.4–5.6 AU grid could not have reached it. The
hypothesis that actually found this link is at **r = 5.6 AU — the exact shared ceiling of
M3's grid and M4's `outer` band** — so the distance was available to M3's grid too. The
`outer` band owns the link only because its version of the cluster was tighter and won the
merge. **What made 29P findable is that M4 searched the pre-2023 slice at all**, which M3
explicitly did not; it is the slice, not the band, that did the work here.

One of the link's four constituent trkSubs is literally `000029P`, so the ITF already knew
what one of those tracklets was — and the other three, from a different observatory, were
never joined to it. That is the shape of the job: the identification is real, and it is an
identification rather than a discovery.

#### The SBIDENT limit, applied

SBIDENT ran on all 10 older-slice candidates and returned for all 10. That is not in tension
with §7.2's 9-year cut: the vetting layer queries SBIDENT at the candidate's *own* epochs,
refuses any older than the budget, and these ten happen to include several post-2017 links.
**But the constraint stands for the slice as a whole** — 4,169,172 of the older slice's
7,489,703 observations (55.7%) predate MJD 57900, so for the majority of the 412,929 gated
links a third opinion is structurally unavailable, and any future pass over that bulk rests
on SkyBoT, MPChecker and SBDB alone. Of the ten vetted here, five have epochs before
2017-08: `lnk034r` (2002), `lnk2aqg` (2008), `lnk2a3j` (2015), `lnk0ne7` (2016) and
`lnk0nih` (2016). **Their verdicts should be read as two-positional-service verdicts.**

#### What this section does not establish

Not that 9 links are new objects. Three of the nine are `orbit_too_poorly_constrained`,
which is weaker than "no catalogue match" — it means the question could not be asked. And
the 106 survivors are themselves 1.08% of the older slice's gated links, so this is a sample
of a sample.

---

## 8. What M4 did not do

- **No submission.** No submission code exists in this repo, sandbox or otherwise.
- **No claim of novelty.** Every survivor is a candidate that has not been ruled out.
- **No triplets, no pairs.** The clustering never forms one; §5.1's five billion states are
  all one-tracklet-at-a-time.
- **No digest2.** The MPC's own NEO-likelihood scorer is not installed here, so the NEO
  score reported is the Gaussian probability that the *fitted* perihelion is inside 1.3 AU
  given Find_Orb's own σ(q) — labelled as a proxy everywhere it appears. digest2 works from
  the astrometry rather than from a converged fit and carries a population prior; where it
  is available it should replace this.
- **No crowded-field second pass.** M3 ranked this second among improvements and §5.1/§6.1
  measure why it was not attempted: widening the grid raises the refusal count from M3's
  1.4 million neighbourhoods to **129 million on the new slice and 900 million on the older
  one — 1.03 billion in total**. The population that "a second pass with tighter astrometric
  weighting" would have to handle grew by nearly three orders of magnitude, and the NEO band
  alone accounts for 83% of it. The three structural rules were not weakened and no
  threshold inside them was touched; the measured cost of that discipline is recorded
  instead.
- **No DAD cross-match.** NOIRLab's `dad_dr2` remains untouched.
- **No snapshot-delta check** on the new candidates. M3 named this as the next step and it
  remains the cheapest available test of whether "unmatched" ever meant "unknown".

---

## 9. Assessment

**Widening the grid was not a parameter change, and the evidence for that is that six of
the seven changes in §2 were found by measurement after the obvious one had been made.**
The uniform distance step is wrong across two decades (§2.1); the solver could not express
half the physically valid states inside 1 AU (§2.2); one window length is wrong when the
curvature limit runs from 4 days to 46 (§2.3); the radial-velocity range excluded
(3200) Phaethon outright (§2.4); the distance step inside 1 AU needs a threefold
amplification factor the opposition rule does not contain (§2.5); the degeneracy M3 found
and guarded now sits inside the production grid on every window, and reaches it from both
sides (§2.6); and three routines that were correct at M3's scale do not finish at M4's
(§2.7). A one-line `r_min` / `r_max` edit would have produced a run that looked entirely
plausible and was wrong in six independent ways — three of them (the near root, the window
length, the radial-velocity range) outright correctness failures rather than resolution
ones, and the seventh problem would have stopped the older slice from finishing at all.

**The widened grid reaches the populations it claims to, measured against JPL Horizons.**
Eleven of thirteen real objects — an Atira, an Aten, an Amor, two Centaurs, two TNOs and
four main-belt controls — are re-derived from astrometry alone, against four of thirteen
for M3's grid, with zero objects merged with a stranger in either run. The two that are not
are explained rather than waved at: (3200) Phaethon sits *at* the clustering radius rather
than inside it at 3 °/day and 0.84 AU, and (588) Achilles is partial in both runs, so it is
a cadence property and not a grid one.

**It also recovers the one object M3 said its grid could not.** Comet 73P-C, which M1 found
sitting in the ITF and M3 named as an unfixable miss, comes back exactly — three tracklets,
three nights, a 4.96-day arc — at a hypothesised 1.038 AU. That is the clearest single
piece of evidence that the new bands describe real geometry.

**Widening costs nothing in main-belt recall and gains 5.7 points, once the cross-band
subset rule is removed.** Exact recall on the ITF's own groupings goes **0.8735 → 0.9302**
and never-touched groups fall from 99 to 28, because the bands do not share a window length
and therefore offer a group whose arc straddles every 14-day boundary a different set of
boundaries. **The price is 2.5× the links to fit**, and that is the real cost of this
milestone — not the compute of the sweep itself, which is seven and a half minutes for five
billion propagated states.

**The first widened run measured a 20-point *loss*, and reporting that is the point.** It
came from a set-inclusion rule adjudicating between bands before any orbit existed —
a NEO-band proposal that is the true group plus one neighbour deleting the correct
belt-band link. The signature was unmistakable in the numbers (touched-at-all *rose* while
exact recall collapsed) and the fix was structural rather than a threshold.

**The belt band reproducing M3 to the digit is a regression-control result and not a
coincidence.** Four separate routines underneath it were rewritten — `drop_subsets`, window
slicing, the isolation check and the ρ̇ solve — and every one of the nine numbers M3
published for that configuration came back unchanged: 17,060 proposals, 1,427,490 refusals,
1,340 exact recoveries, 14 clean partials, 81 contaminated, 99 missed, 1,824 links, recall
0.8735, precision floor 0.7456. An optimisation that changes the answer is not an
optimisation, and this is the evidence that none of them did.

### The yield, and the NEOs that are not in it

**The NEO-distance bands searched 29,579 gated links and produced no near-Earth object.**
The two NEO-class survivors in the whole run are Amors found by hypotheses at 1.40 and
1.70 AU — inside M3's own 1.4–5.6 AU grid, because an Amor away from perihelion sits at a
main-belt *distance*. M3's survivor set had the same minimum semimajor axis, 1.42 AU, and
never classified its output by population. **What found those two is the orbit classifier
this milestone added, not the distances it added.**

That is a finding about the method rather than an absence in the analysis, and three
measured facts support it:

1. **The NEO bands searched properly.** 0.95–1.44 AU across 646 windows and 234 hypotheses,
   plus 0.55–0.94 AU at a 1% step measured to be fine enough to hold a 3 °/day mover
   (§2.5) — 29,579 gated links, the largest band in the run. The reachability check (§3)
   confirms independently that this geometry recovers real Atens, Amors and Atiras.
2. **The fit produced near-Earth orbits in quantity: 5,547 converged NEO-class solutions**,
   being **147 Aten, 3,688 Apollo and 1,712 Amor**. The pipeline is entirely capable of
   fitting an eccentric Earth-crossing orbit to ITF astrometry.
3. **All but two were rejected by the gates**, and the two that survived came from
   main-belt-distance hypotheses.

The reading that fits all three is that **a short arc near 1 AU is the easiest thing in the
solar system to fit an eccentric NEO orbit to, and the hardest to fit well**. The same four
tracklets that admit an Apollo solution also admit a main-belt one; the guard keeps whichever
used all the observations, and that is essentially never the Apollo. **Thousands of converged
NEO orbits beside two surviving Amors — neither of which needed the NEO grid — is the
signature of a filter working, not of a population found.**

### 6% → 74% → 84.4%: how proposal quality degrades as the hypothesis space grows

M1's subset guard asks one question — *did a single orbit fit essentially all of the
observations, across at least three nights?* — and it is **not** one of the MPC's published
criteria. Applied to three progressively weaker sources of associations, it rejects:

| Where the associations came from | Converged fits rejected by the guard |
|---|---:|
| **Survey pipelines** (M1: trkSub groupings the surveys themselves made) | **6%** |
| **A 1.4–5.6 AU hypothesis grid** (M3: 387 hypotheses, main belt only) | **74%** |
| **A 0.55–50 AU hypothesis grid** (M4: 2,555 hypotheses, NEO to TNO) | **84.4%** |

Nothing about the guard changed between those rows; only the provenance of its input did.
**This is the most quantitative statement this project has produced about anything, and it
generalises past this pipeline:** each time the hypothesis space widened, the fraction of
converged solutions that were fitting a *subset* of their own input rose, and an RMS gate
cannot see any of it — a subset fit reports a respectable RMS precisely because it discarded
the observations that did not fit.

The practical consequence for anyone doing this work is that **a supplementary check the MPC
does not publish is rejecting more solutions than every published criterion combined**, and
its importance scales with how speculatively the links were generated. A pipeline that
widens its search without adding a check of this kind will not notice it has stopped
producing objects.

### What was deliberately not done to produce a larger NEO count

A longer list of marginal NEO candidates was available and was not taken. Each of the
following would have produced them on demand, and **none was touched**:

- **the 0.25″ RMS ceiling** — the MPC's published post-fit limit, unchanged;
- **M1's 80% used-observation threshold** (`MIN_USED_FRACTION`) and its ≥ 3 used-nights
  rule — unchanged, and the guard rejecting 84.4% of converged fits is exactly what lowering
  it would have undone;
- **the 0.0025 AU clustering radius** — unchanged, and M3 had already measured that widening
  it makes results *worse*, not merely noisier;
- **the three structural clustering rules** (one tracklet per observatory-night, diameter
  rather than radius, decline when ambiguous) — unchanged, and no threshold inside them
  altered, despite the refusal count rising to 129 million neighbourhoods;
- **the MPC's pre-fit gate** — unchanged, including the 3-day minimum arc that rejected
  9,612 links.

The one threshold that *was* changed is the radial-velocity **range** (±0.55 → ±0.85 of
escape speed for the NEO bands), widened on a measurement that it excluded a real object —
(3200) Phaethon at 0.715 — with the sampling *resolution* held constant so nothing was
traded for it. **The near-zero was earned, not merely obtained.**

### What the widened grid actually bought, in one table

| | M3 (1.4–5.6 AU) | M4 (0.55–50 AU) |
|---|---:|---:|
| Hypotheses | 387 | 2,555 |
| Links proposed | 17,060 | 50,236 |
| Gated | 13,618 | 40,623 |
| Survivors | 199 | **225** |
| Cross-observatory survivors | 73 | **80** |
| Survivors meeting all four σ limits | 141 | **140** |
| …cross-observatory *and* well constrained | 60 | **60** |
| Recall on in-file ground truth (exact) | 0.8735 | **0.9302** |
| Real objects recovered from Horizons astrometry | 4 / 13 | **11 / 13** |

**Six and a half times the hypotheses bought 26 more survivors, 7 more cross-observatory
ones, and not one additional well-constrained candidate.** The capability gain is real and
independently measured — the grid now reaches NEOs, Centaurs and TNOs, and recovers comet
73P-C, which M3 stated in print it could not. The *candidate* gain **on this slice** is close
to nothing, because the gates that decide what survives were never the distance grid. The
gain that did materialise came from the other axis M3 named: the slice.

### The older slice is the better half of the file, and it is barely searched

The pre-60000 slice was M3's third-ranked improvement and it turns out to be the most
productive thing in this milestone — not because it yields more candidates per link, but
because of what kind of candidate it yields.

| | new slice (2023–2026) | **older slice (1995–2023)** |
|---|---:|---:|
| Observations | 1,831,784 | **7,489,703** |
| Links past the MPC's pre-fit gate | 40,623 | **412,929** |
| Fitted | 40,623 (100%) | **4,461 (1.08%)** |
| Survivors | 225 | **106** |
| **Cross-observatory survivors** | 80 — **36%** | **100 — 94%** |
| Survivors that are one survey's own tracklets | 145 | **6** |
| Meeting all four σ limits | 62% | **69%** |
| Best distant candidate, σ(a)/a | 43% | **4.1%** |

**Ninety-four per cent against thirty-six.** The post-2023 slice is dominated by two surveys
that link their own data — 83 of its survivors are Rubin alone, 46 are O18 alone — so most
of what it yields is work somebody else will do anyway. The archival record is genuinely
multi-survey, and its links join Pan-STARRS to Subaru, Catalina's old Schmidt to DECam,
Palomar to Catalina, Steward's Kuiper telescope to Palomar NEAT in 2002. **Those are
associations no single archive is positioned to make, which is the entire argument for the
ITF existing, and they are almost all in the part of the file M3 chose not to search.**

M3 skipped it because follow-up on a 2015 candidate is no longer possible. That reasoning is
sound for *discovery* and irrelevant for *identification*, which is what this pipeline does —
and the older slice proved the point directly by handing back **comet
29P/Schwassmann-Wachmann 1**, assembled from four tracklets taken by two telescopes twelve
days apart in July 2002 and never previously associated, matched to 1.2″ at every epoch and
agreeing with JPL's catalogue orbit to 1.3σ on all four elements. No follow-up was required
or possible; the identification stands on twenty-four-year-old astrometry alone.

**And it is 1.08% searched.** 4,461 of 412,929 gated links were fitted, so the 106 survivors
are a lower bound by a large and unknown factor. The one complete answer is the `outer`
band: all 461 of its gated links fitted, 7 survivors, two of them well-determined Centaurs
and none of them a TNO.

### The bottom line, in one sentence

**Across 9.3 million observations, both slices, 2,555 distance hypotheses spanning
0.55–50 AU and 45,084 orbit fits, M4 produced 331 linked candidates that survive every
published and supplementary gate — 180 of them spanning two or more observatories — of which
exactly two are near-Earth objects (both Amors that M3's narrower grid already reached), not
one is a trans-Neptunian object whose orbit is actually determined, and of the 30 put through
catalogue vetting three came back as already-catalogued objects: the minor planets 2026 OB4
and 2026 DK65 at half an arcsecond, and comet 29P/Schwassmann-Wachmann 1 at 1.2 arcseconds
across four tracklets from two telescopes in 2002 — so the count of survivors that might be
unreported is at most 27 of the 30 examined, none of them verified as new, from a search that
has fitted 1.08% of what the older slice alone has already proposed.**

Unpacking that into the five numbers that matter:

- **331 survivors** (225 new slice + 106 older slice), **180 cross-observatory**.
- **2 NEOs**, from **6,029 converged near-Earth orbits** across both slices — and the
  NEO-distance bands contributed neither of them.
- **0 determined TNOs.** Every trans-Neptunian-class survivor has a semimajor axis uncertain
  by 31% to 114% of its own value.
- **1 well-determined distant candidate that is not already catalogued** — `lnk2a3j`, a
  Centaur at 22.74 ± 0.94 AU from Subaru astrometry in 2015. The only other well-determined
  one turned out to be 29P.
- **3 of 30 vetted candidates are catalogued objects.** M3 measured 2 of 30; M4 measures 3 of
  30 while reaching further. The warning is unchanged and now has three instances behind it:
  ***unmatched is not unknown***.

**Nothing here is a discovery, and after §7.3 and §7.4 the prior is that much of it is not
even new.** The next step is not submission. It is the snapshot delta chain M2 identified as
free validation — these 331 links name specific tracklets, and any that leave the ITF were
linked by somebody else — and, on the evidence of §6, **finishing the older slice**, which is
99% unfitted and is where the cross-observatory candidates actually are.
