# M3 — linking

**Run date:** 2026-08-02 · **Reports:** `m3-linking.json` (the search), `m3-fits.json`
(the orbits and gates), `m3-validation.json` (the ground truth), `m3-vet.json` (catalogue
cross-match)

M1 fitted the cheap population: designations that already spanned three or more nights
under one trkSub, where a survey had already done the association. M3 does the association
itself — it proposes that tracklets carrying *different* trkSubs, often from *different
observatory codes*, are one object.

**Nothing here is a discovery.** Everything below is reported as "linked candidates
surviving gates", which is the strongest claim the evidence supports and is much weaker
than "new object". Nothing was submitted anywhere; all network use was cached, read-only
GET against public MPC, IMCCE and JPL endpoints.

Every number came from code in this repo. Reproduce with `itf-linker m3 --out
m3-report.json` (which does all of it in one pass) and `itf-linker link-validate --out
m3-validation.json`.

---

## 1. Provenance

| | |
|---|---|
| ITF snapshot | `Last-Modified` **Wed, 29 Jul 2026 05:26:45 GMT**, ETag `"8084534-657b9338b6bcf"`, 134,759,732 B |
| Find_Orb | `~/bin/fo`, built 2026-07-29 from `find_orb@143c823`; `PERTURBERS=000007fe`, JPL DE-440 |
| Ephemeris for the linker | ERFA `epv00`, via astropy's `builtin` solar-system ephemeris |
| Tests | **321 passing** (250 at the end of M2), ruff clean |

---

## 2. The algorithm, and why it is the one M0 demanded

M0's headline measurement fixed M3's architecture before a line of it existed: at
nside=64 × 3 days the ITF yields **1.5 × 10⁷ candidate pairs but 7.5 × 10⁸ triplets**, and
coarser partitions reach 10¹¹ — while the MPC auto-rejects any link with fewer than three
nights. **No triplet is enumerated anywhere in this milestone.**

The linker is **HelioLinC** (Holman et al. 2018; Heinze et al. 2022). Angles-only
astrometry plus one *assumed* heliocentric distance is a complete state vector: the line of
sight from the observer pierces the sphere of radius `r` about the Sun at a definite point,
an assumed radial velocity `ṙ` closes the velocity, and two-body propagation carries every
tracklet to one epoch where members of the same object coincide. Linking becomes
clustering, at `O(tracklets × hypotheses)`. A five-night link costs exactly what a
three-night link costs, and no three-way loop exists.

Each tracklet is promoted to an **arrow** — position *and* sky-plane rate, from an ordinary
least-squares line through its own detections. The observer is placed topocentrically from
the MPC's published parallax constants; light time is corrected; the propagation is
universal-variable Kepler about the Sun.

### 2.1 The geometry is checked against M1's independent orbit fits

The chain observer → distance solve → velocity solve → propagation → elements is verified
against Find_Orb solutions produced by a completely different code path in M1. Nothing is
shared: the observer, the distance solve, the propagation and the element conversion are
all this repo's numpy, against a DE-440 differential correction. Taking M1's eight
best-conditioned designations, scanning `(r, ṙ)` for the hypothesis that makes their own
tracklets agree best, and converting the resulting state to elements:

| desig | `a` here | `a` Find_Orb | `e` here | `e` Find_Orb | `i` here | `i` Find_Orb | Δa/a |
|---|---:|---:|---:|---:|---:|---:|---:|
| `RL00XSM` | 2.898 | 2.899 | 0.014 | 0.024 | 0.89 | 0.91 | 0.0% |
| `RL00YHG` | 2.853 | 2.861 | 0.123 | 0.083 | 0.94 | 0.96 | 0.3% |
| `RL00adt` | 2.172 | 2.186 | 0.068 | 0.121 | 3.44 | 3.79 | 0.6% |
| `RL00d8o` | 2.344 | 2.370 | 0.087 | 0.201 | 1.92 | 2.08 | 1.1% |
| `RL00Zz9` | 3.197 | 3.154 | 0.187 | 0.212 | 2.72 | 2.48 | 1.4% |
| `RL00iMW` | 2.463 | 2.374 | 0.123 | 0.135 | 6.87 | 6.07 | 3.7% |
| `RL00eAJ` | 2.338 | 2.169 | 0.025 | 0.192 | 6.65 | 5.17 | 7.8% |
| `RL00hfG` | 1.613 | 2.585 | 0.033 | 0.199 | 3.37 | 9.97 | **37.6%** |

No least squares, no perturbations, one assumed distance — and the **median** `a` error is
**1.25%**. That is ample for a proposal stage.

**The outlier is the point, not an embarrassment.** `RL00hfG` locks onto a hypothesis
1 AU from the truth: for one object at one epoch, "the tracklets agree" can be satisfied by
a wrong distance. This is precisely why a cluster is never treated as an orbit and why
every proposal in §6 goes through Find_Orb before anything is claimed. The check is pinned
as a slow test that bounds each designation at 15% and the *median* at 5% — a systematic
error in the observer or the propagation would move every row, not one.

### 2.2 The failure that check exposed: the r ≈ 1 AU degeneracy

The first version of that check had no such guard, and four designations out of the twelve
scanned came back with `a ≈ 1.04 AU` against Find_Orb's 2.27–2.59 — every one of them at a
hypothesised `r` of 1.02–1.08 AU. The cause is geometric and would have poisoned
the whole milestone silently: **as the hypothesised heliocentric distance approaches the
observer's own, the topocentric distance `ρ → 0` and every tracklet collapses onto the
observer's own state vector.** Every tracklet then clusters with every other tracklet, at
spreads *tighter* than any real object's — so a tightness-ranked search prefers the
degeneracy to the truth.

`geometry.MIN_TOPOCENTRIC_DISTANCE_AU = 0.05` rejects those states, and the guard is pinned
by a test. The production hypothesis grid starts at 1.4 AU, so it does not bind there, but
nothing in the code assumed that.

---

## 3. Calibrating the clustering radius on in-file ground truth

The one free parameter that decides recall is the six-dimensional clustering radius (with
velocity multiplied by a 5-day characteristic time). It was **measured, not chosen**: for
each of the 1,201 designations in the MJD > 60000 slice that already span 3+ nights with an
arc inside one window, sweep the production hypothesis grid and record the smallest
**maximum pairwise** separation their tracklets achieve.

| radius (AU) | ground-truth groups whose tracklets all fit inside |
|---:|---:|
| 0.0010 | 85.1% |
| 0.0015 | 94.3% |
| 0.0020 | 96.7% |
| **0.0025** | **98.1%** |
| 0.0030 | 98.5% |
| 0.0040 | 99.1% |

Median required separation is 4.6 × 10⁻⁴ AU, p90 1.2 × 10⁻³. **0.0025 AU is the production
value**: it covers 98% of the reachable ground truth, and going wider makes results *worse*
rather than better — see §5.2.

---

## 4. Validation: hide the trkSub linkage, and see whether it comes back

M0 established that the obvious validation cannot work. All three July-2026 identification
MPECs link previously *designated* objects, and the ITF contains zero designated and zero
numbered objects, so their observations were never in the file on any day; a 200/200
sensitivity control proved the absence was real rather than a lookup failure. M0's
replacement is the test run here.

**Hiding is a property of the design, not a code path.** `link/heliolinc.py` never reads a
designation. Tracklets enter as an epoch, a direction, a rate and an observer; the trkSub
is used afterwards, and only to mark the answer sheet.

### 4.1 The population, and how much of it is even reachable

| | |
|---|---:|
| Designations spanning 3+ nights (M0's figure, reproduced exactly) | **2,515** |
| …surviving arrow construction | 2,072 |
| …with an arc inside one 14-day window | 1,546 |
| …**minus** those M1's trkSub-collision screens flag | −12 |
| **Clean and reachable — the set scored against** | **1,534** |

The 443 lost to arrow construction are accounted for exactly: 2,248 space-based `S`
observations dropped (the observer is a spacecraft, and putting it at the geocentre would
misplace it by up to 0.01 AU — four times the clustering radius), 515 single-detection
tracklets (no rate, so no state vector), 65 tracklets with an implausible fitted rate, 38
observations from sites with no published coordinates.

**The ground truth is not clean, and treating it as clean would overstate recall.** M1
flagged 538 of the 2,515 as trkSub *collisions* — `des278` spans 17 nights over 1,154 days,
`soho183` 12 nights over 3,555 days, and the longest-arc names are `T00001`, `object`,
`UNK`, `obj01`. A correct linker must **fail** to recover those, so recall is reported
against both the raw reachable set and the collision-screened subset. (Only 12 collision
suspects survive the 14-day arc cut, because the screen's main criterion *is* a long arc.)

### 4.2 Result

Isolated run — only the ground-truth designations' own 6,780 tracklets are present, so a
cluster mixing two trkSubs is very unlikely to be a genuine undiscovered link:

| | against all 1,546 reachable | against the 1,534 collision-screened |
|---|---:|---:|
| Recovered **exactly** | 1,340 | 1,340 |
| Recovered in part, uncontaminated | 14 | 14 |
| Only ever seen mixed with a stranger | 81 | 81 |
| Never touched at all | 111 | 99 |
| **Recall (exact set match)** | **0.867** | **0.874** |
| Recall (exact or clean partial) | 0.876 | 0.883 |
| Recall (touched at all) | 0.928 | 0.936 |
| **Precision (lower bound)** | **0.746** | **0.746** |

**87.4% of the groupings a survey pipeline made are re-derived from positions and epochs
alone, to the exact tracklet.**

### 4.2b The same test inside the real population

The isolated run measures the algorithm. The number that matters operationally is what
happens when the same groupings are buried in the **511,274 arrows of the production
slice**, sharing the sky with everything else. The MJD > 60000 slice contains 1,199
collision-screened, in-window ground-truth groups; 827 of those would themselves pass the
MPC's published pre-fit gate.

| | exact | touched |
|---|---:|---:|
| Isolated (6,780 arrows) | **0.874** | 0.936 |
| Embedded, all proposals (511,274 arrows) | **0.758** | 0.971 |
| Embedded, restricted to the 827 gate-passing groups | **0.784** | — |

**Real confusion costs 9–12 points of exact recall**, and *nothing* in "touched at all" —
which actually rises, to 0.971, because with 511,274 arrows present there are simply more
ways to touch a group. The groups are still found; they just more often pick up a
neighbour and stop being an exact match. That is the honest measure of what a
half-million-tracklet field does to a linker, and 0.758 is the figure to quote.

Of the 17,060 proposals the production run made, **14,960 touch no ground-truth group at
all**. Those are the genuinely novel associations, and §6 is about what happens to them.

Reproduce with `itf-linker link-validate --embedded-links data/link-candidates.parquet`,
which scores a saved production link set against the ground truth buried inside it.

### 4.3 Why precision here is a *lower bound*, and cannot be anything else

Of the 1,824 links produced, 1,360 carry a single trkSub (counted as "pure"), 444 join a
ground-truth group to something else, and 20 touch no ground-truth group. **A link that
joins two trkSubs is not a false positive — it is the thing M3 exists to find.** So
"precision" measured against trkSub agreement counts every genuine discovery as an error,
and 0.746 is a floor, not an estimate.

The real precision filter is the orbit fit, and §6 shows how sharp it is: a chance
alignment does not survive a least-squares solution with a 0.25″ RMS ceiling.

### 4.4 What the misses are made of

The 99 missed groups have a median arc of 3.0 days — so this is not a window-length effect.
Two mechanisms account for most of them, and both are honest limits rather than bugs:

- **Objects outside the hypothesis grid.** `0073P-C` — comet 73P/Schwassmann-Wachmann 3
  fragment C, the known object M1 found sitting in the ITF — is among the misses. In
  April–May 2006 it was ~0.07 AU from Earth. The grid runs 1.4–5.6 AU. It *cannot* be
  found, and finding it would mean the grid was admitting geometry it should not.
- **Crowded fields, where the linker declines.** 81 groups are only ever seen mixed with
  strangers; 52,756 neighbourhoods were refused outright as non-discriminating, and 3,740
  clusters were rejected by the global isolation check (§5.3).

Doubling the hypothesis-grid density (r step 0.10 → 0.05 AU, 387 → 765 hypotheses, twice
the compute) moves exact recall by **0.06 percentage points** (0.8722 → 0.8716 under
identical conditions). **The grid is not the limiting factor**, which is worth knowing
before anyone spends compute there.

---

## 5. Design decisions that only real data could settle

### 5.1 Single-linkage clustering fails catastrophically, in one measurable place

The first implementation used single-linkage connected components inside each cell — the
textbook choice. On the densest window of the slice (MJD 60553–60567, 24,076 arrows) it
produced clusters of **fifty tracklets carrying fifty different trkSubs**, spanning F52,
G96 and W84, with fitted eccentricities up to 0.91.

It is not a bug in the geometry. Those tracklets are real, and they really are close: a
Pan-STARRS/DECam field at RA 349°, Dec −3° holds a main-belt population near opposition
where dozens of objects sit within 0.07° of each other moving at −0.20, −0.10 °/day. Single
linkage chains them into one absurd object.

Three structural rules replaced it, and none of them is a tuned threshold:

- **One tracklet per (observatory, night).** The tracklet key *is*
  `(trkSub, observatory, night)`, so a genuine object contributes exactly one per slot —
  this costs zero recall on the ground truth by construction.
- **Diameter, not radius.** A ball of radius `r` can hold two members `2r` apart. The
  calibration in §3 measured *maximum pairwise* separation, so that is what is enforced.
- **Decline when ambiguous.** If more than 3 tracklets compete for one slot, or more than
  16 sit inside one neighbourhood, no link is emitted and the refusal is counted.

That cut the densest window from 673 clusters to 488.

### 5.2 A wider radius makes the answer worse, not merely noisier

The intuition that a larger clustering radius trades precision for recall is wrong here:

| radius | exact recall | links produced | precision (lower bound) |
|---:|---:|---:|---:|
| 0.0025 AU | **0.872** | 1,987 | 0.683 |
| 0.0040 AU | 0.772 | 2,637 | 0.453 |

Widening *lowers* exact recall by 10 points, because groups stop being recovered cleanly —
they acquire an extra member from a neighbouring object and are no longer the grouping the
survey made. Only "touched at all" improves (0.936 → 0.950). (These two rows were measured
under identical pre-isolation-check conditions so the comparison is fair; the production
figure in §4.2 is slightly better than the 0.872 shown here.)

### 5.3 The cell-local ambiguity guard is evadable, and had to be backed by a global one

Spatial hashing uses 2³ half-cell-offset lattices, which guarantees that any two points
within the radius share a cell in at least one lattice. It does **not** guarantee that a
point's whole neighbourhood is ever in one cell — so a lattice boundary can slice a crowded
blob into sub-cells that each look uncontested, and the ambiguity guard is evaded precisely
where it is needed. A unit test constructs exactly that case and shows the cell-local guard
leaking.

`heliolinc.isolated_groups` closes it: for every surviving cluster it measures the distance
from the cluster centroid to **every** state in the window under the same hypothesis, and
discards the cluster if the neighbourhood is crowded. It is exact, lattice-independent, and
affordable because it runs once per *cluster* rather than once per seed.

It also **improves recall**, which was not the intent: 0.8722 → 0.8735, because removing a
contaminated superset stops it from suppressing the clean subset via the subset rule.
Precision (lower bound) rose from 0.683 to 0.746 and the link count fell from 1,987 to
1,824.

### 5.4 Windows overlap 4×, because 2× loses real links

Windows are 14 days long — the point at which the linear `r(t)` model's neglected curvature
(`GM·W²/8r²` ≈ 0.001 AU at 13 days, 0.005 AU at 29 days) reaches the clustering radius.
Stepping them by half a window means a group with an arc between 7 and 14 days can straddle
every boundary — and 682 of the recovered ground-truth groups have arcs longer than 3.5
days, so this is not a corner case. Measured on the same 1,534 groups, everything else
fixed: step 7.0 d → exact recall **0.819**; step 3.5 d → **0.872**. The production run uses
3.5 days, and each arrow is therefore visited by four windows.

---

## 6. The production run

### 6.1 The search space actually explored

M0's recommended sandbox, unchanged: **MJD > 60000** (2023-02-25 onward), where follow-up
is still physically possible.

| | |
|---|---:|
| Observations in the slice | 1,831,784 |
| Tracklets built | 512,005 (M0 counted 512,106 before the excluded observations below) |
| …**arrows** (tracklets with a usable rate) | **511,274** |
| Nights spanned | 1,140 (MJD 60000–61248) |
| Windows swept (14 d long, 3.5 d apart) | 359, so every arrow is visited four times |
| Hypotheses per window | 387 (43 distances × 9 radial velocities) |
| Window-hypothesis sweeps | 1.4 × 10⁵ |
| **Tracklet states computed, propagated and clustered** | **≈ 7.9 × 10⁸** |
| Wall clock, 20 worker processes | **3 min 31 s** |

Arrows lost, and why: 610 tracklets with an implausible fitted rate, 248 space-based `S`
observations, 121 single-detection tracklets, 114 observations from sites with no published
coordinates. Total loss 0.14%.

**No triplet was enumerated.** For scale, M0 measured 7.5 × 10⁸ triplets at nside=64 × 3
days over the whole file; the clustering approach never forms one.

### 6.2 Proposals, and the published pre-fit gate

The sweep produced 1,669,476 raw clusters across all windows and hypotheses. **1,427,490
neighbourhoods were refused** as non-discriminating and 103,780 further clusters were
rejected by the global isolation check, leaving 32,552 per-window candidates that merge to
17,060 distinct links. The refusals outnumber the survivors 84 to 1: in the deepest survey
fields this linker reports that it cannot link, and that is by far its commonest verdict.

> **Reproducibility.** The whole sweep was run twice, in separate processes with different
> worker counts (16 and 20). Both produced **17,060 candidates**, identical link for link.
> The parallel window sweep is order-preserving and the clustering has no stochastic
> component.

| Stage | Links | Cross-observatory | Same-observatory |
|---|---:|---:|---:|
| Clusters proposed (merged, deduplicated) | **17,060** | 11,767 | 5,293 |
| Pass the MPC's published pre-fit gate | **13,618** | **10,169** | 3,449 |

Before the gate, 16,136 of the 17,060 join more than one trkSub and 11,738 are both
cross-observatory *and* a new association — so the raw proposal set is overwhelmingly
composed of associations nobody had made.

The gate rejected 3,442 links, **all of them for arc < 3 days** — not one failed on
"exactly 3 nights with arc > 15 days", "singleton tracklet at both ends", or the ≥ 2
observations-per-night rule, and none for having fewer than three nights. Each of those is
structurally impossible here rather than luckily absent: a 14-day window cannot produce a
15-day arc; an arrow needs two detections to have a rate at all, so no link can contain a
single-detection tracklet; and three nights is a precondition of cluster extraction. The
one rule that *can* bite is the arc, and it bites 20% of the time.

Of the 13,618 gated links, **12,958 join more than one trkSub** (the rest re-derive an
association that already existed), and **10,161 do both — cross-observatory *and* a new
association.** That intersection is M3's actual target.

| | |
|---|---:|
| Nights per link | 3: 12,065 · 4: 1,387 · 5: 155 · 6: 9 · 7: 2 |
| Observatory codes per link | 1: 3,449 · 2: 6,484 · 3: 3,522 · 4: 160 · 5: 3 |
| Median arc | 6.69 d |
| Median observations | 10 |

The observatory pairings are exactly the cross-survey combinations the ITF makes possible
and no single survey can make:

| Codes | Links |
|---|---:|
| F51 + F52 (Pan-STARRS 1 + 2) | 1,578 |
| F51 + F52 + G96 (+ Catalina) | 782 |
| F52 + G96 | 731 |
| F52 + V00 (+ Bok/Kuiper) | 622 |
| F51 + F52 + V00 | 539 |
| F51 + V00 | 447 |
| F51 + G96 | 389 |
| F52 + G96 + V00 | 388 |
| F51 + O18 | 371 |
| N94 + O18 | 264 |

### 6.3 Fitting, and what survives

All 13,618 gated links were fitted with Find_Orb — 55 minutes of wall clock on 26
concurrent workers, no invocation failures. **The orbit fit, not the linker, is the filter
that matters:**

| Stage | Links | | |
|---|---:|---|---|
| Submitted to Find_Orb | 13,618 | | |
| Converged | **5,950** | 43.7% | 7,573 produced no covariance, 95 were unbound |
| …with RMS ≤ 0.25″ | 2,388 | 17.5% of submitted | |
| Rejected by the "one orbit fits all of it" guard | **4,413** | | M1's supplementary check, §6.4 |
| **Pass every gate — published and supplementary** | **209** | **1.5%** | |
| …minus links contesting a tracklet with a better fit | −10 | | conflict resolution |
| **Survivors** | **199** | | |

| | Survivors |
|---|---:|
| **Cross-observatory** | **73** |
| Same-observatory | 126 |
| Join more than one trkSub (a new association) | 127 |
| Re-derive an association that already existed | 72 |
| **Cross-observatory *and* a new association** | **73** |

Every cross-observatory survivor is also a new association — unsurprising, since a single
trkSub rarely spans two sites. **73 is the milestone's actual yield.**

The 72 that merely re-derive an existing association are **not spread across the ITF**:
63 are X05 (Rubin) alone under the `RL` naming family and 9 are O18 alone. That is M1's
`RL00…` population and M2's composition warning showing up again from a completely
different direction — the linker independently rediscovers the groupings Rubin's own
pipeline made, which is a nice check on the linker and worth nothing as a candidate.

The survivors are ordinary main-belt orbits: median `a` = 2.68 AU (range 1.42–203.6),
median `e` = 0.146, median arc 8.14 d, median RMS 0.111″. Three nights: 136; four: 58;
five: 5.

The best-conditioned cross-observatory links:

| id | codes | nights | arc (d) | RMS (″) | a (AU) | e | i (°) | σ(a) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `lnk04iy` | F51+F52 | 3 | 9.92 | 0.063 | 2.300 | 0.156 | 6.42 | 0.046 |
| `lnk00ir` | N94+O18 | 4 | 6.08 | 0.082 | 2.947 | 0.097 | 5.98 | 0.023 |
| `lnk00f9` | F52+X05 | 4 | 10.34 | 0.090 | 3.668 | 0.065 | 2.23 | 0.048 |
| `lnk00vr` | F52+G96+V00 | 3 | 4.93 | 0.094 | 3.114 | 0.171 | 17.52 | 0.014 |
| `lnk03vs` | F52+N94 | 3 | 4.13 | 0.095 | 2.698 | 0.225 | 6.70 | 0.023 |
| `lnk011a` | F51+N94+V00 | 3 | 7.37 | 0.109 | 3.018 | 0.223 | 2.32 | 0.026 |
| `lnk050y` | F51+F52 | 3 | 10.93 | 0.112 | 2.307 | 0.205 | 4.95 | 0.019 |
| `lnk05c9` | F52+G96 | 3 | 9.20 | 0.117 | 2.133 | 0.127 | 6.34 | 0.002 |

### 6.4 The subset guard is doing most of the work

**4,413 of 5,950 converged fits — 74% — were rejected because Find_Orb did not use
essentially all of the observations it was given.** That is M1's supplementary check, not
the MPC's: a wrong link does not merely raise the residuals, it lets the solver converge on
the subset belonging to *one* of the objects and report a perfectly respectable RMS.

M1 measured this rejecting 59 of 917 fits (6%) on trkSub-grouped designations. On *proposed*
links it rejects 74%. That difference is the entire reason the check exists: when the input
associations were made by a survey they are mostly right, and when they were made by a
hypothesis grid they are mostly wrong. **An RMS gate alone would have passed thousands of
subset fits here**, and the candidate list would have been worthless.

### 6.4b A harness lesson, recorded because it cost an hour

Fitting 13,618 links is **55 minutes on 26 workers**, and the first attempt was killed at
150 of 341 chunks by an unrelated timeout. Nothing about that was recoverable: the run
wrote its report only at the end, so 150 chunks of completed `fo` output sat on disk and
would have been recomputed from scratch.

Two changes make the milestone finishable on a laptop, and both are now shipped:
`m3` writes the gated links to Parquet **before** fitting starts, and `--fit-resume`
re-reads any chunk directory a previous run completed. The resume check is strict — it
requires a parseable `total.json` covering *every* designation in the chunk, because half a
chunk silently converts "not fitted" into "did not converge" — and chunk membership is
deterministic because designations are sorted before chunking. Three tests pin it.

A second failure was a real scaling bug, not a harness one. `isolated_groups` built a
`clusters × arrows × 6` distance array in one allocation: 167 MB for 151 clusters against a
23,000-arrow window, times two dozen worker processes. The run died with a `MemoryError`
while asking for 26 MB. It is batched now.

### 6.5 The published criteria are still not sufficient — again

M1's §7 finding reproduces exactly. The MPC's σ limits are scoped to *exactly*-three-night
links, so a four- or five-night fit is judged on RMS alone:

- **All 136 three-night survivors meet all four σ limits** — as they must, because the gate
  tests them.
- **Only 5 of the 63 four-and-five-night survivors do.** 39 exceed σ(a) = 0.05 AU alone.
  Four survivors have a > 10 AU — 18.3, 23.7, 84.4 and **203.5 AU**, the last on a 10-day
  arc, which is a statement about the arc rather than about the object.

Applying the same four σ limits to *every* survivor regardless of night count leaves **141
of 199**, and **60 of the 73 cross-observatory ones**. The numbers are **reported rather
than filtered**: the criteria are the MPC's and the ranking is ours, and a five-night link
with a = 203 AU sorts to the bottom on its own.

**The defensible headline is therefore: 60 cross-observatory links are both acceptable to
the MPC's published filter and numerically well constrained.** Whether any of them is an
object nobody has already reported is §6.6's question, and the answer there is not "yes".

### 6.6 Vetting the survivors

The 199 survivors were **not** all vetted. At ~44 s per link against rate-limited public
services, all 199 would take ~2.4 hours of live requests; the **top 30 by rank** were vetted
instead — the best-conditioned cross-observatory links, the ones any submission would draw
from first. This is a deliberate subset and the numbers below describe it, not the whole set.

Settings differ from M2's candidate run and are recorded so the two are not confused: a
**300″ search radius** (wider, because a linked orbit's predicted position carries more
error than a single fitted designation's), `max_epochs` 3, MPChecker limit magnitude 25.0,
and SBIDENT on escalation only.

| Category | Links |
|---|---:|
| unmatched | **26** |
| known | 2 |
| ambiguous | 2 |

All 26 unmatched carry the same reason: `no_catalogue_object_near_astrometry`. None was
unmatched for a poorly-constrained orbit — unsurprising, since these are the best-fitted 30.

**The two identifications are the most informative result in this section.**

| Link | Resolves to |
|---|---|
| `lnk00do` | **2026 OB4** |
| `lnk00dm` | **2026 DK65** |

Both are *recently designated* minor planets. That matters twice over. It is direct evidence
the linker assembles **real objects rather than statistical noise** — a chance cluster does
not resolve to a catalogued minor planet. And it demonstrates the specific failure mode M2
warned about, now observed rather than hypothesised: **these objects were designated after
the ITF snapshot was taken.** Their observations sat unlinked in the file precisely because
nobody had linked them *yet*, and somebody has since.

That is the honest reading of the other 26. "No catalogue object near the astrometry" is
consistent with an unreported object, but `lnk00do` and `lnk00dm` show it is also
consistent with an object designated between the snapshot and the query — and this snapshot
is from 2026-07-29.

The two ambiguous links resolved toward `26114` and `775733` without meeting the ≥2-epoch
agreement rule, so they are recorded as ambiguous rather than promoted.

**Service health.** SkyBoT: 82 requests, 13 retries, 2 failures. MPChecker: 71 requests,
6 failures. SBDB: 51 requests, clean. No service was disabled and the failure budget was
not exhausted, but the failure rate is higher than M2's run and the 26 should be read with
that in mind.

**What this section does not establish.** Not that 26 links are new objects. Not that the
other 169 survivors would behave the same way — they are worse-conditioned by construction,
so a higher `orbit_too_poorly_constrained` rate is expected if they are ever vetted.

---

## 7. What M3 did not do

- **No submission.** No submission code exists in this repo, sandbox or otherwise.
- **No claim of novelty.** Every survivor is a candidate that has not been ruled out.
- **No pairs, no triplets.** The pair-enumeration branch M0 also allowed was not built;
  HelioLinC made it unnecessary.
- **No slice before MJD 60000.** 2.1M of the ITF's 2.6M tracklets are older than the
  sandbox. They are reachable by the same code — `--mjd-min` is a flag — but follow-up on
  a 2015 candidate is no longer physically possible, which is why M0 chose this slice.
- **No DAD cross-match.** NOIRLab's `dad_dr2` is a second, disjoint pool feeding the same
  pipeline and is untouched.

## 8. Assessment

**The milestone works, and it is not the linker that limits it.**

M0 said pairs are cheap and triplets are the wall, and predicted the architecture that
follows. That prediction held exactly: HelioLinC swept 511,274 tracklets across 359
overlapping windows and 387 distance hypotheses in **three and a half minutes**, computing
~8 × 10⁸ states and forming no triplet. Linking a half-million-tracklet slice of the ITF is
not a computational problem on a laptop in 2026.

**The validation is real and the number is respectable.** 87.4% of the ITF's own trkSub
groupings are re-derived exactly from positions and epochs alone in isolation, 75.8% inside
the full population. Those are measured against 1,534 and 1,199 in-file ground-truth
groupings respectively, using ground truth that was itself screened for the trkSub
collisions M1 identified. The residual misses are explained rather than waved at: objects
outside the 1.4–5.6 AU hypothesis grid (including the ITF's known comet, at 0.07 AU in
2006), and crowded fields where the linker declines to guess.

**The orbit fit is the real filter, by two orders of magnitude.** 13,618 gated proposals
became 199 survivors — 1.5%. And within that, M1's supplementary subset guard did more work
than the MPC's published criteria: **74% of converged fits were rejected because Find_Orb
had not used all the observations**, against 6% when M1 applied the same check to
survey-made associations. That contrast is the strongest single argument in this milestone
for keeping supplementary checks that the MPC does not publish: without it, thousands of
subset fits would have been indistinguishable from good ones.

**73 cross-observatory links survive every gate, and 60 of those are also numerically
well constrained.** They join F51 to F52, F52 to G96, N94 to O18, F52 to V00 — associations
that no single survey is positioned to make and that are the ITF's specific value. They are
ordinary main-belt orbits, a ≈ 2.7 AU, e ≈ 0.15, and by construction that is the population
an all-sky survey re-detects constantly.

**None of them is a discovery, and the prior that any given one is unreported is low.**
Three reasons, all measured rather than asserted:

1. **The vetting result** (§6.6) says "not identified by these services", which M2
   established is a much weaker statement than "new" — it is equally consistent with a
   known object whose fitted orbit is not precise enough to be recognised, or with an object
   linked and designated by someone else since this snapshot was taken.
2. **The composition warning that shaped M3 has not gone away.** 72 of the 199 survivors
   are X05 (Rubin) alone and 38 are O18 alone, and 63 of those X05 links merely re-derive a
   grouping that already existed under one `RL00…` trkSub. That is one survey's unlinked
   internal tracking, which Rubin will link itself. Demoting it is exactly why the ranking
   puts cross-observatory first.
3. **Precision at the clustering stage is only bounded, never estimated.** A link joining
   two trkSubs cannot be scored against trkSub agreement without counting every genuine
   discovery as an error, so 0.746 is a floor. The fit is what converts a proposal into a
   candidate, and it rejects 98.5% of them.

**What would most improve the yield, in order.** Not the hypothesis grid — doubling its
density moved recall by 0.06 points. Not the clustering radius — widening it made results
*worse*. The three things that would:

1. **Widen the distance grid downward and upward.** 1.4–5.6 AU excludes NEOs entirely and
   everything beyond Jupiter. Those populations are where an unreported object is most
   likely to be hiding, precisely because surveys link main-belt objects well.
2. **Handle the crowded fields instead of declining them.** 1.4 million neighbourhoods were
   refused as non-discriminating. A deep-drilling field near opposition genuinely cannot be
   linked at this radius, but a second pass with tighter astrometric weighting might.
3. **Run the older slice.** 2.1M of the ITF's 2.6M tracklets predate MJD 60000. Follow-up
   is no longer possible for them, but an identification does not require follow-up.

**The honest bottom line.** M3 produces **73 linked candidates that span two or more
observatories, join tracklets nobody had associated, and survive every published and
supplementary gate**. That is a real result and the pipeline that produced it is validated
end to end. It is *not* 73 discoveries, and the next step is not submission — it is the
snapshot delta chain, which M2 already identified as free validation: any of these
tracklets that leave the ITF were linked by someone else, and that is a zero-cost test of
whether "unmatched" ever meant "unknown".
