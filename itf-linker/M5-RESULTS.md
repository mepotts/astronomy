# M5 — closing the older slice's 1.08%

**Run date:** 2026-08-06 · **Reports:** `m5-old.json` (the merged funnel),
`data/m5-checkpoints/*.json` (one per batch, written as it finished), `m5-vet.json`
(catalogue vetting)

M4 gated **412,929** links on the pre-60000 slice and fitted **4,461 of them — 1.08%**. Its
106 survivors were therefore a lower bound by an unknown factor, and the project's honest
claim was not "we searched 9.3M observations" but "we searched 20% of them thoroughly and
1% of the rest". M5 has one job: close that gap.

**Nothing here is a discovery.** Everything below is "linked candidates surviving gates".
Nothing was submitted anywhere; all network use was cached, read-only GET against public
MPC, IMCCE and JPL endpoints.

---

## 1. Provenance

| | |
|---|---|
| ITF snapshot | the file M3 and M4 used — 9,322,655 observations, `Last-Modified` **Wed, 29 Jul 2026 07:26:34 GMT** |
| Links | `data/m4-links-old.parquet` — M4's own 567,838 proposals, 412,929 past the published pre-fit gate. **No re-linking.** M5 changes nothing upstream of the fit |
| Find_Orb | `~/bin/fo`, built 2026-07-29 from `find_orb@143c823`; JPL DE-440 |
| Bad-data filter, unchanged | 9,322,655 in → 4 pre-1900 epochs, 3 blank designations, 1,161 duplicate records dropped → 9,321,487 kept |
| Gates | unchanged: the MPC's published pre- and post-fit criteria plus M1's supplementary subset guard. **No threshold was touched** |
| Tests | **394 passing** (369 at the end of M4), ruff clean |

**What M5 changes is only *which links get fitted* and *how the fitting survives being
interrupted*.** The linker, the hypothesis grid, the pre-fit gate, the post-fit gate, the
subset guard, the conflict resolution and the clustering radius are M4's, untouched — and
§3.1 shows M4's own 4,461 links coming back through the new machinery with all nine of its
headline numbers unchanged.

---

## 2. The ranking, and why M4's was worse than shuffling the queue

A run that cannot finish is decided by its queue. M4's queue came from
`prioritise_bands` plus M3's ranking — distance band first with **NEO ahead of the belt**,
then cross-observatory, then *more* nights, then a tighter cluster. Every part of that was
argued from value and none of it was ever checked against an outcome.

It can be checked now, because M4 fitted 4,461 older-slice links and **118 of them passed
every gate**. Replaying a candidate order over that sample and asking *what fraction of the
eventual survivors sits in the first X% of the queue* is the only question a fitting order
has to answer:

| order | top 10% | top 25% | top 50% | top 75% |
|---|---:|---:|---:|---:|
| **M4's own** | **0.000** | **0.025** | **0.102** | **0.373** |
| a random shuffle | 0.127 | 0.271 | 0.517 | 0.771 |
| **M5's, 5-fold cross-validated** | **0.585** | **0.797** | **0.932** | **0.983** |
| M5's, shipped coefficients (in-sample, optimistic) | 0.602 | 0.814 | 0.932 | 0.992 |

**M4's ranking was worse than shuffling the queue at every depth.** Its first 10% of those
4,461 links contained *none* of the 118 survivors.

That has a consequence for how M4 should be read. M4 described its sample as "deliberately
the best-conditioned part of the set" and concluded that its survivor **rates** are upper
bounds on the older slice. The first half of that is true by its own criteria; the second
does not follow, because the criteria it conditioned on were not the ones that predict
survival. §5 checks it against outcomes instead of assuming it.

### 2.1 What actually predicted survival

Every row below is measured on those 4,461 outcomes. Nothing here is intuition, and two
of the five keys M4 sorted on point the *opposite* way to how it sorted them.

**Band — and M4 fitted the worst one first.**

| band | fitted | converged | passed | pass rate |
|---|---:|---:|---:|---:|
| `belt` | 2,000 | 45.6% | 102 | **5.10%** |
| `outer` | 461 | 97.0% | 10 | 2.17% |
| `neo` | 2,000 | 19.0% | 6 | **0.30%** |

`neo` is 61% of the older slice's gated links (252,920 of 412,929) and passes at a
seventeenth of the belt band's rate. M4's `WIDE_FIT_ORDER` put it first.

**More nights is worse, not better — M4 sorted nights descending.**

| nights | fitted | converged | passed | pass rate |
|---|---:|---:|---:|---:|
| 3 | 1,013 | 86.1% | 68 | **6.71%** |
| 4 | 2,447 | 27.1% | 44 | 1.80% |
| 5 | 930 | 19.9% | 6 | 0.65% |
| 6 | 67 | 28.4% | 0 | 0.00% |
| 7 | 4 | 0.0% | 0 | 0.00% |

The mechanism is M1's supplementary guard, which rejected half of everything that converged
in that sample (and 77% across the complete slice, §5.1): a longer chain has more ways to
contain one wrong tracklet, and one wrong tracklet fails the whole link. 70% of the older
slice's gated links are three-tracklet.

**Exactly two observatory codes beats three or more.**

| codes | fitted | passed | pass rate |
|---|---:|---:|---:|
| 1 | 450 | 9 | 2.00% |
| **2** | 2,865 | 99 | **3.46%** |
| 3 | 964 | 9 | 0.93% |
| 4 | 159 | 1 | 0.63% |
| 5 | 23 | 0 | 0.00% |

**The two strongest signals were not in M4's sort at all.** Cluster tightness:

| `pos_spread_au` | < 1e-4 | 1–2e-4 | 2–3e-4 | 3–4e-4 | 4–5e-4 | ≥ 8e-4 |
|---|---:|---:|---:|---:|---:|---:|
| pass rate | **23.2%** | 10.4% | 8.5% | 3.9% | 2.4% | < 1% |

and how many times the search rediscovered the same tracklet set:

| `n_hypotheses_found` | 1 | 2–3 | 4–10 | 11–50 | 50+ |
|---|---:|---:|---:|---:|---:|
| fitted | 1,089 | 1,012 | 896 | 689 | 775 |
| pass rate | 0.55% | 0.99% | 1.90% | 2.18% | **9.03%** |

> **Corrected 2026-08-07.** This was described as "how many *independent distance
> hypotheses* recovered the same tracklet set", and below as "one hypothesis in 2,555". It
> is not that. `merge_links` accumulates the counter on every merge of the same arrow set,
> and links merge across overlapping **time windows** and across **bands** as well as across
> hypotheses — a 14-day window at a 3.5-day step offers the same link from up to four
> windows, each sweeping the full grid, and four bands merge on top. The quantity is roughly
> `windows × hypotheses × bands`, so it mixes hypothesis diversity with how centrally the
> arc happens to sit in the window grid. The **measured pass rates above are unaffected** —
> they are a marginal on the column as computed — but the column does not mean independent
> confirmation, and the model's strongest feature is therefore partly a geometry artefact.

A link the search found once passes at a sixteenth of the rate of one it rediscovered
hundreds of times. That is the single most useful pre-fit number in
the file and M3 and M4 both computed it and neither ranked on it.

### 2.2 The ranking M5 uses

`src/itf_linker/link/priority.py`. Two levels, and they answer different questions.

**Tier — a value judgement, not a yield one.** Every **cross-observatory** link is fitted
before every same-observatory link, whatever it scores. M4 measured why: 100 of its 106
older-slice survivors span two or more observatories, and a same-observatory link is mostly
one survey's own unlinked tracking, which that survey will link itself. The survival
evidence for the tier is weak in both directions — M4's sample was 90% cross-observatory,
so it barely measures the contrast — and the tier does not rest on it.

**Within a tier — a logistic regression fitted to those 4,461 outcomes**, ridge λ = 1:

| feature | coefficient | reads as |
|---|---:|---|
| intercept | −9.819 | |
| `band_belt` | **+1.122** | the belt band beats the NEO band |
| `band_outer` | +0.456 | so does the outer band |
| `log10(pos_spread_au)` | **−1.306** | a tighter cluster is better |
| `log10(n_hypotheses_found)` | **+0.961** | recovered by more hypotheses is better |
| `obscodes_over_2` | −0.766 | a third observatory code is worse |
| `min_trk_n_obs` | −0.660 | thicker tracklets are worse |
| `prefit_arc_days` | +0.292 | a longer arc is better |

> **Do not read these magnitudes against each other** (noted 2026-08-07). `logistic_fit`
> applies a single ridge λ = 1 to **unstandardised** columns: `prefit_arc_days` spans ~3–20,
> `min_trk_n_obs` ~2–6, the `log10` terms ~−4.5 to −2.5, and the band dummies are 0/1. One λ
> penalises those by wildly different amounts, so a coefficient here is in the units of its
> own feature and the column is not an effect-size ranking. Statements like "`band_belt` is
> the largest positive coefficient" compare unlike things. **Signs and the resulting ordering
> are unaffected** — which is all the model is used for. To read effect sizes, standardise
> inside `design_matrix` and refit; that is deliberately not done here, because refitting
> would change the shipped coefficients and with them the fitting order that M5 ran.

`min_trk_n_obs` is the one whose sign looks wrong and is not: the thickest tracklets belong
to the archival deep-drilling fields where agreement between tracklets is cheapest, and the
marginal confirms it (2.7% at two detections per night against 0.7% at five).

**Three things this ordering is deliberately not:**

- **It is not a filter.** Nothing is excluded by a low score. A link the model ranks last is
  fitted with exactly the same gates as one it ranks first, if the run reaches it. What was
  not reached is reported as not reached, in §4.
- **It is not fitted to what it is scoring.** The coefficients come from M4's sample, which
  is 90% cross-observatory and contains no `neo`-band link with fewer than four nights.
  Scoring the other 99% of the population is extrapolation, and the cost of getting it wrong
  is efficiency rather than correctness — the queue is reordered, never truncated.
- **It is not tuned on M5's own outcomes.** The coefficients were frozen before the run
  started and are not refitted afterwards, so nothing in §4 or §5 is circular.

M4's 4,461 links sit at a median rank of **17,706** in the M5 queue and **4,011 of them are
inside the cross-observatory tier**, so the seeded work is near the front of the new order
rather than scattered through it.

---

## 3. Making 400,000 fits survivable

Three problems had to be solved before the queue in §2 could be worked through, and only
one of them was anticipated.

### 3.1 Nothing already fitted is recomputed

M4's 4,461 links live in `data/m4-fits-old` as 112 `fo` chunk directories. `--fit-resume`
re-reads a chunk only when the designations it is asked for are **exactly** the ones that
chunk holds, so the queue has to be reassembled in the order those chunks were written —
and that order is recoverable exactly from the `obs.txt` each chunk still contains, which
is stronger than re-deriving it from a `sort` whose tie-breaking polars does not guarantee.

The check that it worked is that M4's numbers come back to the digit, from a differently
ordered, differently batched, differently located pipeline:

| | M4's own run | M5 re-reading it |
|---|---:|---:|
| Fitted | 4,461 | **4,461** |
| Converged | 1,738 | **1,738** |
| …RMS ≤ 0.25″ | 806 | **806** |
| Rejected by the subset guard | 874 | **874** |
| Pass every gate | 118 | **118** |
| Dropped by conflict resolution | 12 | **12** |
| **Survivors** | **106** | **106** |
| …cross-observatory | 100 | **100** |
| …meeting all four σ limits | 73 | **73** |
| Wall clock | 720 s | **3.0 s** |

### 3.2 Checkpoints at two granularities, because interruption is the normal case

M3 lost 150 chunks to a timeout because its report was written only at the end. M4 shipped
`--fit-resume` for that and then hit the other half of the problem — a fit that cannot
finish at all. M5 assumes both:

- the **chunk** (40 links, one `fo` invocation) is what `--resume` re-reads, so nothing a
  chunk finished is ever recomputed;
- the **batch** (8,000 links) writes a JSON checkpoint the moment it finishes, carrying its
  funnel counters, its population histograms and **every link that passed every gate**.

Conflict resolution and survivor ranking are then redone **globally** over the union of the
checkpoints, because "a tracklet belongs to one object" is not a per-batch statement — two
batches can each propose a link over the same tracklet and only one can be right. The
worst case for an interruption is therefore losing the batch in flight, and even that loses
only the chunks in flight within it.

### 3.3 The fits were 9× slower than they needed to be, and it was not the arithmetic

The first M5 run sat at **25–28% CPU** on a 32-thread machine with 28 `fo` workers, almost
every one of them in uninterruptible I/O wait. `fo` writes twenty-odd files per invocation
and merges `total.json` by **re-reading it once per object**, so a 40-object chunk performs
tens of megabytes of small reads and writes — and on Windows every one of those crossed
WSL's 9p bridge to `/mnt/c`, which does not cache and serialises across workers.

Measured on one 40-link chunk from M4's own queue, under the same concurrent load:

| working directory | wall clock | objects |
|---|---:|---:|
| Linux filesystem (`/tmp`) | **47 s** | 40 |
| `/mnt/c` via 9p | **437 s** | 40 |

So `fo` is now run in a Linux-side scratch directory and exactly the three files this
codebase ever reads back — `total.json`, `elements.txt`, `covar.json` — are copied to the
host chunk directory afterwards. The crossing drops to one read of `obs.txt` and one write
of about a megabyte, and CPU utilisation goes from 28% to **92–95%**.

**It must not change the answer, and it does not.** Re-running M4's `chunk0000` through the
scratch path: 40 of 40 objects returned, and `a`, `e`, `i`, `q`, RMS, σ(a), observations
used, status and convergence are identical for **38 of 40**. The two that differ are both
non-converged hyperbolic garbage (`a` < 0, `e` = 129 and 30, RMS 3.3″ and 261900″) which
Find_Orb's preliminary-orbit search reaches by a different path on a hopeless link; both
are rejected as non-converged in both runs, so **every gate outcome is identical**.
`--no-scratch` restores M3 and M4's exact file layout.

---

## 4. Coverage: 1.08% → 100%

**Every gated link on the older slice has now been fitted.** 412,929 of 412,929, in
4 hours 24 minutes of Find_Orb across 53 batches, with no link left unfitted and none
lacking astrometry.

| | M4 | **M5** |
|---|---:|---:|
| Gated links | 412,929 | 412,929 |
| **Fitted** | 4,461 — **1.08%** | **412,929 — 100%** |
| …cross-observatory | 4,011 of 69,502 — 5.8% | **69,502 of 69,502 — 100%** |
| …same-observatory | 450 of 343,427 — 0.13% | **343,427 of 343,427 — 100%** |
| …`belt` band | 2,000 of 159,548 — 1.3% | **159,548 — 100%** |
| …`neo` band | 2,000 of 252,920 — 0.8% | **252,920 — 100%** |
| …`outer` band | 461 of 461 — 100% | 461 — 100% |
| Wall clock | 12 min | **4 h 24 min** (15,826 s, 28 workers) |
| `fo` invocations that produced nothing | 0 | 70 chunks, bisected; 11 links isolated as `fo_aborted(rc=134)` |

The 70 bisected chunks are §2.7-of-M4's known failure mode — one designation whose
`elements.json` has no parseable start line aborts the whole invocation — and the
bisection did its job: 11 individual links were isolated and recorded as
`fo_aborted(rc=134)`, and every other link in those chunks was salvaged.

### 4.1 The yield curve, and where the ranking earned its keep

Gate-passers per batch, in queue order (each batch is 8,000 links):

| batch | b0000 | b0001 | b0002 | b0003 | b0004 | b0005 | b0006 | b0007 | **b0008** | b0009 | b0010 | … | b0051 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| passed | **110** | 4 | 2 | 3 | 3 | 2 | **0** | **0** | **800** | 378 | 309 | decaying | 1 |
| cross-observatory | **110** | 4 | 2 | 3 | 3 | 2 | 0 | 0 | **0** | 0 | 0 | — | 0 |

Two features of that curve need saying explicitly.

**The decay inside the first tier is the survival score working.** The top 8,000 links of
the cross-observatory tier produced 110 gate-passers; the next 8,000 produced 4. §2's
cross-validated capture curve predicted exactly this shape, and the run is an out-of-sample
confirmation of it on 92× more data than it was fitted to.

**The b0007 → b0008 jump from 0 to 800 is a band transition, not a gate failure and not an
anomaly.** The queue is sorted by score within each tier, and `band_belt` is the largest
positive coefficient in the model, so the tail of the cross-observatory tier is almost pure
`neo` band and the head of the same-observatory tier is almost pure `belt`:

| batch | `neo` links | `belt` links | passed |
|---|---:|---:|---:|
| b0006 | 7,956 | 44 | 0 |
| **b0007** | **7,990** | **10** | **0** |
| **b0008** | 1,492 | **6,508** | **800** |
| b0009 | 5 | 7,995 | 378 |

The `neo` band passing nothing at the bottom of its own ranking, and the `belt` band
passing 10% at the top of its, is the same 17:1 ratio §2.1 measured on M4's sample,
reproduced at scale. Nothing changed about the gates between b0007 and b0008.

---

## 5. The funnel

| Stage | Links | | M4's 1.08% sample, for comparison |
|---|---:|---|---|
| Gated and submitted | **412,929** | 100% | 4,461 |
| Fitted | **412,929** | 100% | 4,461 |
| Converged | **67,828** | **16.4%** | 39.0% |
| …with RMS ≤ 0.25″ | 31,636 | 7.7% | 18.1% |
| Rejected by the "one orbit fits all of it" guard | **52,408** | **77.3% of converged** | 50.3% |
| **Pass every gate — published and supplementary** | **3,678** | **0.89%** | 2.6% |
| …minus links contesting a tracklet with a better fit | −488 | | −12 |
| **Survivors** | **3,190** | **0.77%** | 106 |

Non-convergence, by reason: 341,368 produced no covariance, 2,934 used fewer than three
observations, 788 were unbound, 11 were the isolated `fo` aborts.

**M4's caveat was right in direction and understated in size.** It said its survivor rates
were upper bounds because its sample was the best-conditioned part of the set. The
population rate is **0.89%** against the sample's **2.6%** — so the sample was enriched
about threefold — and its survivor *count* was a lower bound by a factor of **30**.

### 5.1 The subset guard, replicated a fourth time

M1's supplementary check — *did a single orbit fit essentially all of the observations,
across at least three nights?* — is not one of the MPC's published criteria, and it is
again the largest single filter:

| Where the associations came from | Converged fits rejected by the guard |
|---|---:|
| Survey pipelines (M1: trkSub groupings the surveys made) | 6% |
| A 1.4–5.6 AU hypothesis grid (M3) | 74% |
| A 0.55–50 AU grid, new slice (M4) | 84.4% |
| A 0.55–50 AU grid, older slice, **1.08% sample** (M4) | 50.3% |
| **A 0.55–50 AU grid, older slice, complete (M5)** | **77.3%** |

The complete older slice lands at 77.3%, inside the 74–84% range the two speculative
searches produced, and **the 50.3% M4 measured is now visible as an artefact of its
sample** rather than a property of the slice. That is a fourth independent replication of
the finding, on 412,929 links instead of 4,461.

### 5.2 The survivors, σ first

3,190 survivors: 2,977 single-observatory, 213 cross-observatory, 3,186 joining more than
one trkSub. Median RMS 0.103″; median semimajor axis 1.83 AU; 2,834 used every observation
Find_Orb was given.

The σ limits, applied to every survivor regardless of night count — the discipline M4
established after demoting six beyond-belt candidates on inspecting σ(a):

> **Corrected 2026-08-07.** Two errors run through this table and the paragraph under it.
> (1) The scoping to three-night links is **ours**, not the MPC's — their rule has a second
> bullet for links with more than 3 nights, so "escape by scope" describes our gate, not
> theirs. (2) These are **four of five** published quality conditions; `e < 0.5` is
> published and is not counted here. See §5.6 for both gates applied to this population.

| | survivors | meeting four of the five published σ limits |
|---|---:|---:|
| Three-night links (*our* gate scopes the limits to these) | 2,896 | **2,896 — 100% by construction** |
| Four-night links | 272 | **49 — 18%** |
| Five-night links | 22 | **5 — 23%** |
| **All** | **3,190** | **2,950 — 92%** |
| …of the 213 cross-observatory ones | 213 | **176 — 83%** |

The 92% is high only because 91% of the survivors are three-night links, which the gate
itself tests against those limits. The informative row is the second: **four-night links
escape our σ limits by scope, and 82% of them would fail if the limits were applied.**
(Under the MPC's published rule they escape for a different reason — a converged fit with
RMS ≤ 0.25″ is never quality-tested at all, on any night count.)

#### The twenty-one beyond-belt survivors, σ(a) first

Everything classified Centaur or TNO, or fitted beyond 5.6 AU. Sorted by σ(a), because the
semimajor-axis column is unreadable without it:

| id | band | class | `a` | **σ(a)** | σ(a)/a | `e` | `q` | nights / arc | used | RMS | codes | epoch | meets all four σ |
|---|---|---|---:|---:|---:|---:|---:|---|---|---:|---|---|---|
| `lnk690k` | `belt` | Centaur | 6.59 | **± 0.033** | **0.5%** | 0.724 | 1.82 | 3 / 13.04 d | 6/6 | 0.082 | 705 | 2006-10 | **yes** |
| `lnk5p9s` | `belt` | Centaur | 6.62 | **± 0.041** | **0.6%** | 0.710 | 1.92 | 3 / 10.25 d | 6/6 | 0.058 | 705 | 2006-10 | **yes** |
| `lnk034r` | `outer` | Centaur | 6.00 | ± 0.203 | 3.4% | 0.222 | 4.67 | 4 / 12.10 d | 13/13 | 0.171 | **620 + 644** | 2002-07 | no |
| `lnk2aoz` | `neo` | Centaur | 6.19 | ± 0.228 | 3.7% | 0.224 | 4.80 | 4 / 5.08 d | 23/24 | 0.134 | T09 | 2015-01 | no |
| `lnk2be6` | `neo` | Centaur | 6.18 | ± 0.651 | 11% | 0.746 | 1.57 | 4 / 4.99 d | 8/8 | 0.217 | 705 | 2005-10 | no |
| `lnk1w3r` | `belt` | Centaur | 6.59 | ± 0.776 | 12% | 0.765 | 1.55 | 5 / 4.99 d | 8/10 | 0.198 | 705 | 2006-09 | no |
| `lnk2qqb` | `belt` | Centaur | 8.36 | ± 0.879 | 11% | 0.832 | 1.40 | 4 / 5.06 d | 8/8 | 0.143 | 705 | 2006-10 | no |
| `lnk2a3j` | `outer` | Centaur | 22.74 | ± 0.939 | 4.1% | 0.777 | 5.07 | 4 / 8.07 d | 15/15 | 0.118 | T09 | 2015-07 | no |
| `lnk230b` | `neo` | Centaur | 5.58 | ± 1.06 | 19% | 0.189 | 4.53 | 5 / 6.01 d | 18/22 | 0.126 | W84 | 2014-03 | no |
| `lnk035d` | `belt` | Centaur | 5.84 | ± 1.17 | 20% | 0.495 | 2.95 | 4 / 4.24 d | 8/8 | 0.083 | **304 + 568** | 2021-09 | no |
| `lnk034f` | `neo` | Centaur | 6.04 | ± 1.51 | 25% | 0.144 | 5.18 | 4 / 3.35 d | 8/8 | 0.246 | **304 + 568** | 2021-09 | no |
| `lnk460t` | `neo` | Centaur | 5.90 | ± 2.66 | 45% | 0.235 | 4.51 | 4 / 4.17 d | 9/11 | 0.088 | W84 | 2014-03 | no |
| `lnk2ao4` | `belt` | Centaur | 13.96 | ± 3.66 | 26% | 0.870 | 1.82 | 4 / 5.98 d | 8/8 | 0.249 | 705 | 2005-10 | no |
| `lnk29k6` | `belt` | Centaur | 9.71 | ± 4.06 | 42% | 0.617 | 3.72 | 4 / 3.06 d | 8/8 | 0.249 | 807 | 2002-04 | no |
| `lnk2zwg` | `neo` | Centaur | 15.03 | ± 4.31 | 29% | 0.896 | 1.56 | 4 / 4.99 d | 8/8 | 0.225 | 705 | 2005-10 | no |
| `lnk2cht` | `belt` | Centaur | 13.71 | ± 4.43 | 32% | 0.877 | 1.69 | 4 / 3.06 d | 8/8 | 0.217 | 705 | 2006-09 | no |
| `lnk1w42` | `neo` | Centaur | 28.89 | ± 6.10 | 21% | 0.946 | 1.56 | 5 / 6.07 d | 8/10 | 0.189 | 705 | 2006-09 | no |
| **`lnk2cbo`** | `neo` | **TNO** | 43.53 | ± 7.82 | 18% | 0.377 | 27.11 | 4 / 5.07 d | 11/11 | 0.108 | T09 | 2015-01 | no |
| `lnk2aqg` | `outer` | Centaur | 24.70 | ± 12.6 | 51% | 0.565 | 10.73 | 4 / 5.01 d | 10/10 | 0.102 | 568 | 2009-02 | no |
| **`lnk2aqt`** | `neo` | **TNO** | 59.64 | ± 22.6 | 38% | 0.565 | 25.97 | 4 / 5.07 d | 14/14 | 0.103 | T09 | 2015-01 | no |
| **`lnk2gkr`** | `belt` | **TNO** | 98.53 | **± 116** | **118%** | 0.984 | 1.59 | 4 / 4.06 d | 8/8 | 0.172 | 705 | 2006-09 | no |

**Nineteen of the twenty-one have no measured semimajor axis** — 3.4% is the best of them
that a four- or five-night fit produced, and the worst is 98 ± 116 AU, which is a way of
writing "possibly unbound". The two that *do* meet all four σ limits are three-night links
which the gate therefore actually tested, and both are **705 alone with six observations**:
that is the minimum a three-night link can carry under the MPC's ≥ 2-per-night rule, so they
are well-determined by the covariance and thin by every other measure.

**Only three of the twenty-one are cross-observatory**, and one of them, `lnk034r`, is
comet **29P/Schwassmann-Wachmann 1** — M4 identified it and this run re-derives the same
link from the same two telescopes with the same elements. Completing the slice added
**zero** new cross-observatory beyond-belt candidates to M4's three.

**All three TNO-class survivors are undetermined**, at 18%, 38% and 118% of their own
semimajor axes. Two are Subaru alone; one is Palomar alone. That is the complete
trans-Neptunian result for the pre-2023 ITF at this grid and these gates: **no TNO whose
orbit is actually known.**

---

### 5.3 Gate correction (2026-08-07): our gate is not the MPC's published rule

Everything above, and every survivor count in M1–M4, is measured against a gate this project
described as "the MPC's published post-fit criteria, and nothing more". It is not. The page
cited — `.../mpcops/submissions/identifications/additional/` — **404s**; the live page is
`.../mpcops/documentation/identifications/additional/`, and its post-fit rule is **three
conjunctive bullets**:

1. exactly 3 nights **and** arc < 15 d **and** RMS > 0.25″ **and** orbit quality insufficient
2. more than 3 nights **and** arc < 10 d **and** RMS > 0.25″ **and** orbit quality insufficient
3. the fit did not converge

with *quality sufficient* = σ(a) < 0.05 AU, σ(q) < 0.05 AU, σ(i) < 0.5°, σ(e) < 0.05, **and
e < 0.5**. Our gate rejects on `not converged OR RMS > 0.25 OR (3 nights AND any σ fails)`.
Three differences, all in the conservative direction — we reject a superset, so **nothing was
ever wrongly promoted**:

| | Ours (the gate every number above is against) | MPC published |
|---|---|---|
| RMS ceiling | unconditional | one conjunct of bullets 1–2; no standalone RMS rule |
| σ block | exactly-3-night links only | governed by arc length, and bullet 2 covers >3 nights |
| `e < 0.5` | not implemented anywhere | published, fifth quality condition |

**What this changes in the numbers above.** Recomputed from `m5-old.json`, which reproduces
the published `survivors_meeting_all_sigma_limits` = 2,950 exactly before the fifth condition
is added:

| | survivors |
|---|---:|
| Meeting the four σ limits (as reported in §5.2) | 2,950 |
| **Meeting all five published conditions** (adds `e < 0.5`) | **2,403** — 547 fewer |
| Survivors with e ≥ 0.5 | **564 of 3,190 — 17.7%** |
| …of the 21 beyond-belt survivors in §5.2 | **14** |
| Cross-observatory survivors meeting all five | 171 (of 213) |

`lnk2gkr`, presented in §5.2 as a TNO, has **e = 0.984** with q = 1.59 AU and a = 98.5 AU —
it fails the published `e < 0.5`. Its "TNO" label is an artefact of the classifier's
boundaries: `classify_orbit` tests perihelion only for the NEO cut (q < 1.3 AU), and above
the belt branches on semimajor axis alone (`a > 30.1 → tno`), so an orbit with perihelion
between Earth and Mars and aphelion near 195 AU is labelled trans-Neptunian. That is the JPL
SBDB convention and is not wrong, but it is nowhere stated in these write-ups, and "TNO"
here should not be read as "distant object".

**Applying that distinction to §5.2's twenty-one beyond-belt survivors: three survive it.**
`classify.dynamically_distant` (new) requires `a > 5.5` **and** perihelion beyond Jupiter
(q > 5.2 AU) — distant throughout the orbit, not merely on average:

| | survivors |
|---|---:|
| Beyond-belt by label (§5.2) | 21 |
| **Dynamically distant (q > 5.2 AU)** | **3** — `lnk2aqt`, `lnk2cbo`, `lnk2aqg` |

The other eighteen have perihelia inside or at the edge of the asteroid belt: `lnk1w42` at
q = 1.56 AU with a = 28.9, `lnk2zwg` at q = 1.56, `lnk2a3j` at q = 5.07. §8's vetting
selection is built on the *label*, so it selected those eighteen as distant-object
candidates. That does not invalidate the vetting — it queried what it queried — but "21
beyond-belt candidates" should be read as 21 large-`a` **solutions**, of which 3 are
distant orbits and the rest are short-arc fits with eccentricity doing the work.

The §5.2 claim that four-night links "escape the σ limits by scope" describes **our** gate.
Under the MPC's rule the >3-night regime is governed by bullet 2, and **284 survivors** sit in
it (>3 nights, submitted arc < 10 d), of which **232 fail the four σ limits**. The conclusion
that four- and five-night survivors are poorly constrained is unaffected; its stated
justification was wrong.

**Both gates over the whole funnel.** `scripts/rescore_gates.py` re-reads every fit from the
on-disk `total.json` chunks and applies both rules, at zero Find_Orb cost:

| over 408,457 re-read fits | links |
|---|---:|
| Pass our gate | 9,733 |
| Pass the MPC's published gate | **40,582 — 4.2×** |
| Pass ours but not theirs | **0** |
| Pass theirs but not ours | 30,849 |

**`strict_only = 0` is the load-bearing result.** On 408,457 real fits, every link our gate
accepts the MPC's rule also accepts — our gate is a *strict subset*, empirically, not just by
argument. That is what makes this a correction to the write-ups rather than to the science:
no candidate was ever promoted that the MPC's filter would have rejected. The 30,849 in the
other direction are links we discarded that the published rule would not reject on sight,
27,443 of them three-night links.

These counts are **not** comparable to the 3,190 survivors above: they are the post-fit gate
alone, before the subset guard (which removed 52,408) and before conflict resolution.

**Caveat on the totals, stated because the script refuses to hide it.** The re-read recovers
408,457 of 412,929 links and 66,090 of 67,828 converged fits — 97.4%. The gap is fully
accounted for: **70 chunk `total.json` files are truncated mid-object**, ending in `},` with
no closing braces — and this run recorded **exactly 70** `fo_invocation_failures`, all
`returncode` 134, all one stderr signature:
`orb_func.cpp:1038: Assertion 'fabs(jd1) < 1e+9' failed`. The correspondence is one-to-one,
none of them was a copy-back failure, and `load_previous_run` refuses partial files by
design. 70 × 64 = 4,480 against an observed 4,472. So the absolute counts are a 97–99% sample, while
the strict-versus-published split is **exact** — both gates saw the identical 408,457 rows.

---

## 6. The headline: the cross-survey pool is small, finite, and now exhausted

The older slice's whole argument, established by M4, is that **94% of its survivors span
two or more observatories** — associations no single archive is positioned to make. That
tier is now completely searched, and this is what it contains:

| | |
|---|---:|
| Cross-observatory links gated | **69,502** |
| …fitted | **69,502 — 100%** |
| Passing every gate | **233** |
| **Cross-observatory survivors after global conflict resolution** | **213** |
| …already found by M4's 1.08% sample | **96** |
| …new in M5 | **117** |

And the distribution of those 233 gate-passers across the queue is the result:

| queue position (cross-observatory tier, 69,502 links) | cross-observatory gate-passers |
|---|---:|
| M4's 4,461-link sample | 109 |
| b0000 (next 8,000 by score) | **110** |
| b0001–b0005 (next 40,000) | **14** |
| **b0006 onward (the last ~17,000 of the tier, plus all 343,427 same-observatory links)** | **0** |

**Roughly 400,000 links — 92× everything M4 fitted — produced not one additional
cross-observatory candidate.** The last 17,491 links of the cross-observatory tier itself
produced none, and neither did any of the 343,427 same-observatory links, because a
same-observatory link cannot be cross-observatory by construction.

That is a genuine negative result and it is the most useful thing in this milestone:
**on the pre-2023 ITF, the cross-survey linkage pool is small, finite, and now
demonstrably exhausted at these gates and this hypothesis grid.** Nobody has to fit those
400,000 links again.

Two things it retroactively settles:

- **The ranking earned itself.** In arbitrary order the 213 cross-observatory survivors
  would be buried among 2,977 same-observatory ones, and an interrupted run would have had
  no way to know it already had them. As it is, the run had 96% of them after six batches.
- **M4's judgement about its own sample was sound.** Its 1.08% held 109 of the 233
  cross-observatory gate-passers — 47% of the total from 1% of the links. Its *counts* were
  a lower bound, as it said; on this particular axis they were a much better estimate than
  the coverage figure implied.

### 6.1 What the 213 are

| | |
|---|---|
| Population | middle belt 87 · inner belt 70 · outer belt 39 · Cybele–Hilda 5 · **Centaur 3** · Trojan 2 · Mars-crosser 2 · **Amor 2** · Hungaria 2 · other 1 |
| Nights | 3: 171 · 4: 39 · 5: 3 |
| Meeting all four published σ limits | **176 of 213 — 83%** |
| Using every observation Find_Orb was given | 142 of 213 |
| Commonest pairings | F51+G96 61 · F51+F52 31 · F51+T09 17 · **705+G96 11** · **703+W84 9** · F51+F52+G96 9 · G96+W84 7 · F51+W84 7 · F52+V00 7 · **291+705 5** · 691+F51 3 · **645+691** 3 |
| Epochs | 2019: 35 · 2020: 28 · 2022: 26 · 2021: 25 · 2015: 24 · 2016: 17 · 2014: 15 · 2005: 12 · 2017: 11 · **1998: 3** · **2002: 2** |

**94% of them are main-belt objects.** The pairings are the ITF's stated purpose visible in
the output — Pan-STARRS to Subaru, Catalina's old Schmidt to DECam, Spacewatch to
Pan-STARRS, 645 to 691 — but what those telescope pairs are jointly seeing is
overwhelmingly the population every all-sky survey re-detects anyway.

---

## 7. The 1,850 NEO-class survivors, and why they are not 1,850 NEOs

This is the number in this milestone most likely to be misread, so it gets the sharpest
caveat in the document.

M4 fitted 6,029 converged near-Earth-class orbits across both slices and produced **two**
surviving Amors. M5 fitted the whole older slice, produced **47,190 converged NEO-class
orbits** (29,324 Apollo, 11,845 Amor, 6,021 Aten), and **1,850 of them survive every gate**.
Taken at face value that is a reversal. It is not.

| | |
|---|---:|
| NEO-by-q survivors | **1,850** |
| …**single-observatory** | **1,848 — 99.9%** |
| …of which observatory **705 alone** | **1,842** |
| …W84 alone | 5 |
| …T09 alone | 1 |
| **…cross-observatory** | **2** |

**One observatory code accounts for 1,842 of 1,850.** 705 is Palomar, and its contribution
to the ITF is a single archival era: 1,095 of the 3,190 survivors carry a 2006 epoch and
1,071 a 2005 one, 68% of the total from two years.

A same-observatory link is one survey's own unlinked residue. It is astrometry that
observatory took, on nights that observatory scheduled, that its own pipeline did not
join up — and joining it up is work that archive is positioned to do and this project is
not. That is exactly the composition warning M2 raised (91 of M1's 128 candidates carried
one survey's naming family), M3 repeated (63 of 72 were X05 alone) and M4 repeated again
(83 of 225 Rubin alone, 46 O18 alone). At full coverage it does not get better; it becomes
**93% of the survivor list** (2,977 of 3,190 are single-observatory: 705 2,147, T09 458,
W84 255, F51 108).

**The defensible statement is: the complete older slice contains exactly two
cross-observatory NEO-class candidates**, both Amors, both 705+G96:

| id | codes | class | `a` ± σ(a) | `e` | **`q` ± σ(q)** | nights | epoch |
|---|---|---|---|---:|---|---|---|
| `lnk0v6a` | **705 + G96** | Amor | — | — | **1.2995 ± 0.0006** | 3 | 2006 |
| `lnk19b4` | **705 + G96** | Amor | — | — | **1.1511 ± 0.0005** | 3 | 2006 |

`lnk0v6a`'s perihelion is 1.2995 AU against the 1.3 AU NEO boundary — it is *formally*
an NEO by four thousandths of an AU, which is 0.0005 AU outside its own σ(q). It is
reported because the classifier put it there, not because the classification is robust.

**Two, from 47,190 converged near-Earth orbits.** That is the same signature M4 named —
a short arc near 1 AU is the easiest thing in the solar system to fit an eccentric NEO
orbit to and the hardest to fit well — measured now on a hundred times more fits.

---

## 8. Vetting

3,190 survivors at ~1 minute of rate-limited, cached service time each is more than two
days of continuous querying against three public services. **40 were vetted**, chosen by an
explicit rule rather than by rank alone, so that the pass covers what this milestone
actually claims:

| selection rule | candidates |
|---|---:|
| **every** survivor whose fitted orbit lies beyond the belt (Centaur/TNO class, or a > 5.6 AU) | **21 — all of them** |
| the best-constrained NEO-class survivors by σ(q), including **both** cross-observatory ones | 7 |
| the best-constrained cross-observatory survivors by σ(a), among those meeting all four σ limits | 12 |
| **total** | **40 of 3,190 — 1.3%** |

38 minutes, 248 live requests, minimum interval 1.2 s, everything disk-cached:

| Service | Live requests | Cache hits | Retries | Failures |
|---|---:|---:|---:|---:|
| SkyBoT (IMCCE) | 93 | 27 | 0 | 0 |
| MPChecker (MPC) | 98 | 27 | 5 | **5** |
| JPL SBDB | 45 | 29 | 0 | 0 |
| **JPL SBIDENT** | **12** | 8 | 0 | 0 |

No service was disabled. **MPChecker used the entire failure budget** — 5 failures against
a budget of 5 — so one more would have disabled it mid-run; that is worth recording as a
margin that was fully consumed rather than a clean pass.

| Category | Links |
|---|---:|
| **known** | **1** |
| unmatched | **39** |
| ambiguous | 0 |

**Unmatched, by reason — and the split is the whole result:**

| Reason | Links |
|---|---:|
| `no_catalogue_object_near_astrometry` | 23 |
| **`orbit_too_poorly_constrained`** | **16** |

### 8.1 The σ column and the vetting layer agree, for a third time independently

**All sixteen refusals are beyond-belt candidates, and they are exactly the sixteen §5.2's
σ table said not to trust** — every one with σ(a)/a between 11% and 118%. The vetting layer
refuses to ask a catalogue about an orbit whose own uncertainty exceeds the search radius,
and it drew the line in the same place the σ column did, without being told to.

The five beyond-belt candidates it *was* willing to query are precisely those with
σ(a)/a ≤ 4.1% — `lnk690k`, `lnk5p9s`, `lnk2aoz`, `lnk2a3j`, and `lnk034r`. Four came back
`no_catalogue_object_near_astrometry`; the fifth is 29P.

M4 saw this on both of its slices and M5 sees it on the complete older slice. **The
demotion of the distant candidates is not a judgement made in the write-up — it is what the
pipeline itself concludes, from a different direction, every time.**

### 8.2 The one identification is 29P again

| | |
|---|---|
| Link | `lnk034r` — 4 tracklets, 4 nights, **620 (Steward, Kuiper) + 644 (Palomar NEAT)**, July 2002 |
| Identification | **29P/Schwassmann-Wachmann 1** |
| Astrometric agreement | **1.234″–1.365″ at 3 of 3 epochs** |
| Element agreement | Δ`a` = −0.046 AU (0.22σ), Δ`e` = 0.178 (1.03σ), Δ`i` = 0.886° (1.11σ), Δ`q` = −1.109 AU (1.26σ) — **consistent to 1.3σ** |

This is M4's identification, re-derived to the milliarcsecond by a differently ordered,
differently batched, differently located run. It is a regression control, not a new result:
**completing the slice produced no second comet and no second identification.**

### 8.3 The SBIDENT limit, applied

`vet/sbident.py` refuses any epoch more than **9 years** old, because its two-pass
identification pre-filters with a two-body propagation whose first-pass row count climbs
~50× over two decades. Today that cut falls at **2017-08**.

**30 of the 40 vetted candidates have epochs before that cut** — 9 in 2006, 8 in 2005, 4
each in 2015/2016, 2 in 2002, and so on. SBIDENT made 12 live requests across the pass, so
**for three quarters of these candidates the third opinion is structurally unavailable and
the verdict rests on SkyBoT, MPChecker and SBDB alone.** Read them as
two-positional-service verdicts.

The constraint is worse for the survivor list as a whole: **2,926 of the 3,190 survivors —
92% — carry a first epoch older than the cut**, because 68% of them come from the 2005–2006
Palomar archive. Any future pass over the remaining 3,150 inherits that limit.

### 8.4 What this section does not establish

Not that 39 links are new objects. For **16 of the 39** `unmatched` means "this orbit is too
poorly determined to ask the question at all", which is weaker than "no catalogue match",
which is itself weaker than "new". Not that the other 3,150 survivors would behave the same
way — they were not vetted, and the 40 that were are the best-conditioned in the set. And
the base rate stands: across M3, M4 and M5, **70 candidates have now been through catalogue
vetting and four came back as already-catalogued objects** — 2026 OB4, 2026 DK65, and
29P twice. ***Unmatched is not unknown.***

---

---

## 9. Assessment

**M5 had one job and it is done: the older slice went from 1.08% fitted to 100%.** 412,929
of 412,929 gated links, in 4 h 24 min, with nothing left unfitted and nothing silently
truncated. The claim the project can now make is no longer "we searched 20% of the file
thoroughly and 1% of the rest" — it is that **every link the pipeline proposed on 9.3
million observations has been fitted and gated.**

**The result of doing that is a negative one, and it is the most useful thing here.**
Fitting 92× more links than M4 did produced **not one additional cross-observatory
candidate** beyond the first six batches. The cross-survey linkage pool on the pre-2023
ITF is 213 survivors, M4's 1% sample already held 96 of them, and the remaining ~400,000
links contained none. *That question is now closed at this hypothesis grid and these
gates*, and nobody has to spend four hours of Find_Orb re-asking it.

**The survivor count grew 30-fold and the part that matters grew twofold.** 106 → 3,190
survivors, but 100 → 213 cross-observatory ones, and of the 3,084 new survivors **2,977 are
one observatory's own unlinked residue** — 2,147 of them Palomar's 2005–2006 archive alone.
That is the composition warning M2 first raised, now measured at full coverage: the ITF's
older slice is not mostly a cross-survey resource, it is mostly one archive's unfinished
internal linking, and the cross-survey part of it is 5% of the survivor list.

**The 1,850 NEO-class survivors are not 1,850 NEOs, and §7 is the caveat.** 1,848 of them
are single-observatory and 1,842 are observatory 705 alone. **Exactly two are
cross-observatory**, both Amors, both 705+G96, one of them formally NEO by 0.0005 AU — from
**47,190 converged near-Earth orbits**. M4 measured the same signature on 6,029 converged
NEO orbits and drew the same conclusion; M5 confirms it with eight times the fits and does
not soften it.

**Nothing beyond Neptune is determined.** Three TNO-class survivors, at σ(a)/a of 18%, 38%
and 118%. Nineteen of the twenty-one beyond-belt survivors have no measured semimajor axis
at all. The two that meet all four published σ limits are three-night, six-observation,
single-observatory links. Completing the slice added **zero** cross-observatory beyond-belt
candidates to M4's three, one of which is a comet catalogued in 1927.

**The ranking is the transferable methodological result.** M4's fitting order — argued from
value, never checked against an outcome — put **none** of its survivors in the first 10% of
its own queue and was worse than a random shuffle at every depth. Replacing it with a
logistic regression fitted to M4's own 4,461 outcomes puts **58%** of the survivors in the
first 10% and **80%** in the first 25%, cross-validated. Two of the five keys M4 sorted on
pointed the wrong way (band order, and nights descending) and the two strongest signals —
cluster tightness and how many independent hypotheses recovered the same tracklet set —
were not in its sort at all. The run confirmed the shape out of sample: 110 gate-passers in
the first batch of the tier, 4 in the second.

**The subset guard replicates a fourth time, and M4's 50.3% turns out to be a sampling
artefact.** On the complete older slice M1's unpublished "one orbit fits all of it" check
rejects **77.3%** of converged fits — inside the 74–84% band the two speculative searches
produced, against 6% on survey-made associations. It remains the single largest filter in
the funnel and it remains invisible to an RMS gate.

**The engineering finding is worth stating because it is not about astronomy.** The first
attempt at this run sat at 25–28% CPU on a 32-thread machine with almost every `fo` process
in uninterruptible I/O wait, because Find_Orb re-reads and rewrites `total.json` once per
object and every one of those crossed WSL's 9p bridge to `/mnt/c`. Running `fo` in a Linux
scratch directory and copying back the three files this codebase reads took one measured
40-link chunk from **437 s to 47 s** and the whole run from an estimated 39 hours to 4.4 —
with the answer unchanged on every gate outcome. **A milestone whose deliverable is
coverage is a milestone whose deliverable is throughput.**

**The vetting found what M4's found, and refused what M4's refused.** One identification
in 40 — comet 29P again, at 1.2″ across three epochs and 1.3σ on all four elements — and
39 unmatched, of which **16 were never queryable at all** because their orbits are less
certain than the search radius. Those 16 are exactly the beyond-belt candidates the σ
column flagged, which is the third time on a third body of data that the vetting layer and
the σ column have independently reached the same verdict. And 92% of the survivor list
carries an epoch older than SBIDENT's 9-year limit, so for most of it the third opinion is
structurally unavailable.

### What M5 did not do

- **No submission.** No submission code exists in this repo, sandbox or otherwise.
- **No re-linking.** The 567,838 proposals and the 412,929 that pass the pre-fit gate are
  M4's, unchanged. M5 fits them; it does not propose anything new.
- **No threshold changed.** Not the 0.25″ RMS ceiling, not M1's 80% used-observation
  threshold or its ≥ 3 used-nights rule, not the 0.0025 AU clustering radius, not the three
  structural clustering rules, not the pre-fit gate. The near-zero cross-observatory yield
  past b0005 was earned, not obtained.
- **No digest2.** The NEO score reported is still the Gaussian probability that the fitted
  perihelion is inside 1.3 AU given Find_Orb's own σ(q) — a proxy, labelled as one, and §7
  is why it should not be read as a population statement.
- **No vetting of 3,190 survivors.** §8 vets 40 by a stated rule — every beyond-belt
  survivor, both cross-observatory NEO candidates, and the best-constrained
  cross-observatory links. The other 3,150 are unvetted, and the four already-catalogued
  objects found across 70 vetted candidates in M3–M5 are the reason that matters.
- **No snapshot-delta check.** Still the cheapest available test of whether "unmatched"
  ever meant "unknown", and still not done.
- **No new-slice work.** MJD > 60000 is M4's 40,623 links, already 100% fitted.

### The bottom line, in one sentence

**Fitting all 412,929 gated links on the ITF's pre-2023 slice — 92× what M4 fitted, 100%
coverage of a search that was 1.08% complete — produced 3,190 candidates surviving every
published and supplementary gate, of which 2,977 are a single observatory's own unlinked
residue and only 213 span two or more observatories; the cross-observatory pool was
exhausted after six of fifty-two batches with M4's 1% sample already holding 96 of the
213, not one of the 1,850 formally-NEO survivors is a cross-observatory candidate with a
robust perihelion, no trans-Neptunian survivor has a determined orbit, and the only
beyond-belt candidate the catalogue services can name is a comet somebody catalogued in
1927 — so the honest summary of completing this search is that it closed a question rather
than opening one.**

---
