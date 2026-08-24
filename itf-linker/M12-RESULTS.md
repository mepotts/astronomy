# M12 — The archive read as a series: the ITF is draining, and for five days one survey stopped filling it

**Date:** 2026-08-24 · **Status: COMPLETE** · **Inputs:** the 24 committed snapshots of
the daily archive (2026-07-29 05:26:45 GMT → 2026-08-23 12:26:46 GMT), their
`manifest.json` and `delta.parquet` chain, the six full key sets that still survive on
disk, M9's independent 08-16 reconstruction, and a fresh MPCORB pulled for this milestone
(2026-08-24 02:24:39 GMT, 1,558,557 orbits). **Nothing was submitted anywhere.** Every
input is read-only; M12 writes only its own outputs. Tests: 517 green.

**Scope note.** M11 §9 recommends five things for M12 — the submission decision, a
pre-submission refresh, the shell's arc-extension test, the 20.7 y stopping rule, and
tightening the primary gate. **None of them are done here and all five remain open.**
This milestone answers a different question that nobody had asked: the archive has been
running for 26 days and every previous use of it compared exactly two snapshots. This is
what the *series* says.

**One-line result:** the ITF is not churning, it is **draining** — 168,078 observations
left against 38,319 that arrived, a ratio of **4.4 : 1** and a net loss of **129,759**,
with the file falling 9,322,655 → 9,194,631 observations in 26 days. The drain is
**linkage, not attrition**: only 0.15% of departures are re-labellings, **99.57% of
departed observations belong to designations that vanished entirely** (a whole
tracklet at a time, typically 4 observations), and a random sample of departed tracklets,
attributed against MPCORB and then checked against the objects' own published records,
CROSSWALK_HEADLINE. Underneath that steady drain sits something the archive exists to
catch and nothing else would have: **for five consecutive days, 2026-08-17 → 08-21,
intake from Pan-STARRS collapsed by a factor of 86** — F51+F52 supply **81% of all ITF
intake** at 1,640 observations/day and fell to **19/day** — while removals continued at
full rate. Total intake appears to recover on 08-22, but **it is a different observatory
doing it**: Pan-STARRS is still at 18/day, and the recovery is a single V00 batch. The
MPC regenerated the file every one of those days, so this is not a stalled pull.

---

## 0. Pre-registered decisions (written before the runs they govern)

### 0.1 What the series is allowed to be read from

A delta is an anti-join on `obs_key`, so the chain transports a **distinct key set**, not
a row multiset. Every comparison in this milestone is between distinct key sets. Row
counts are reported where a manifest reports them and are never compared against a walk.

### 0.2 A gap is not a zero, and a broken chain is not a series

2026-08-13's manifest carries `parent_snapshot: null` and
`delta_status.computed: false` — the key set it needed had been pruned before the diff
ran. The walk **must not cross it**. The series is therefore reported as contiguous
segments, and a segment with no surviving key set to anchor on is reported as
**NOT MEASURABLE**, never as an empty result.

### 0.3 The walk must be verified before it is read

The backward walk is exact arithmetic on committed deltas, but "exact" is a claim, not a
property. Before any number derived from it is reported, it must reproduce **every**
independently surviving key set it covers, and M9's independently built 08-16
reconstruction. **Any disagreement means the series is not reported.** This fired twice
(§5).

### 0.4 Attribution proposes; the published record disposes

A sky-position match does not establish that a tracklet was linked into an object. The
claim is only made when the **object's published record contains the departed
observations themselves** — same station, within 2 s and 2″, M9's duplicate rule. A
tracklet whose best attribution is arcseconds away but whose observations are absent from
that record counts as **UNCONFIRMED**, not as a hit.

### 0.5 What M12 may not do

It may not touch the ledger, the review queue, the archive, or the archive's clone. It may
not re-run any sweep or fit. It may not submit anything. Its outputs are new files under
`data/raw/rubin/` plus this document.

---

## 1. The series: 4.4 departures for every arrival

`scripts/m12_series.py`, over 24 snapshots in three contiguous segments. Twenty
transitions are measurable; the 2026-07-29 pair has no surviving key set to anchor on and
is reported as such.

| | |
|---|---:|
| Snapshots | 24 (2026-07-29 → 2026-08-23) |
| Measured transitions | 20 |
| Observations arrived | **38,319** |
| Observations departed | **168,078** |
| Ratio | **4.4 : 1** |
| Net | **−129,759** |
| File: observations | 9,322,655 → **9,194,631** (−128,024, −1.4%) |
| File: designations | 2,602,962 → **2,570,632** |
| File: designations with ≥3 nights | 2,515 → **2,455** |
| Source file on the MPC's server | 134.8 MB → **133.1 MB**, monotonically |

Every step agrees with its own manifest's `appeared`/`disappeared` (20/20).

### 1.1 The confound that had to be paid for first: re-designation

`obs_key` folds `desig` into the hash (`snapshot.py::obs_key`), so an observation the MPC
merely **re-labels** — same station, same instant, same position, new trksub — vanishes
under its old key and reappears under a new one. Read naively that is one departure and
one arrival. **A file that only churned its designations would look exactly like a file
being drained**, and every number above would mean something else.

The test is to match each delta's departed rows against its arrived rows on
`(obscode, mjd)`, ignoring `desig`:

> **249 of 168,078 departures are re-designations — 0.15%.**

Seven of the twenty transitions have exactly zero, and the largest single count is 75.
The drain is real.

### 1.2 Departures are whole designations, not pruned observations

This is the distinction that separates *linkage* from *data loss*. If the MPC were
discarding bad astrometry, designations would shed observations piecemeal. If it were
linking tracklets into objects, whole designations would vanish at once.

| | designations | observations |
|---|---:|---:|
| Lost something | 43,964 | 168,078 |
| **Vanished entirely** | **43,783** | **167,357** |
| Lost only part of themselves | 181 | 721 |

> **99.57% of departed observations belong to designations that vanished entirely**.
> The per-step median size of one of those designations is **2–5 observations**
> (typically 4) — one tracklet's worth.

Zero designations lost observations they did not have in the parent key set, which is the
walk's own internal consistency check.

### 1.3 What leaves is old; what arrives is tonight

The two sides of the file are not the same population.

* **Departures** have a median observation epoch of **2018.8** (per-step medians range
  2014.3 → 2021.8). These are years-old unidentified tracklets.
* **Arrivals** have a median epoch of **2026.6** on every normal day — fresh sky.

The ITF is a queue: new unidentified tracklets enter at the top, old ones leave from
anywhere in it as identifications are made. Over these 26 days the leaving outran the
entering by 4.4 to 1.

---

## 2. The five-day intake collapse, and what it actually was

Read as raw counts, 2026-08-17 → 08-21 looks like the MPC pausing: arrivals fall to
156–348/day against a 1,200–6,300/day baseline, then "recover" on 08-22. Both halves of
that reading are wrong.

The baseline has one other exception, and it turns out to be the same phenomenon for a
single day: **2026-08-11** took 435 arrivals/day, inside the stall's range, and it is
also the one earlier day on which Pan-STARRS contributed **exactly zero**. The five-day
block was preceded by a one-day rehearsal.

### 2.1 It is one observatory pair, not the MPC

Splitting arrivals by station, with every rate normalised by the actual snapshot interval
(they run 15–56 h apart, so raw counts mislead):

| Period | Pan-STARRS (F51+F52) | All other stations | Pan-STARRS share |
|---|---:|---:|---:|
| Normal (08-04 → 08-16) | **1,640/day** | 385/day | **81.0%** |
| **Stall (08-17 → 08-21)** | **19/day** | 248/day | **7.1%** |
| After (08-22 → 08-23) | 18/day | 2,894/day | 0.6% |

**Pan-STARRS supplies 81% of everything that enters the ITF.** Its contribution fell by a
factor of **86**. Every other station carried on within a factor of two of normal. This
was never an MPC-wide pause; it is one pair of telescopes' worth of intake disappearing
from a file that depends on them for four fifths of its input.

### 2.2 The recovery is a different observatory

The obvious reading of 08-22's rebound to 2,158 arrivals is that Pan-STARRS came back. It
did not. On 08-22 and 08-23, Pan-STARRS contributed **20 and 15** observations. The
rebound is **V00** (Kitt Peak-Bok) delivering 1,959 and 3,329 — a batch submission from an
entirely different program that happens to restore the total while the dominant supplier
is still dark.

A count of arrivals would have shown "stall, then recovery". The station split shows
"stall, still stalled, plus an unrelated batch". As of the last snapshot **Pan-STARRS
intake has not returned.**

### 2.3 Removals never paused

Throughout the stall, departures continued at **6,628–13,659/day**, at or above the
period average. Whatever stopped filling the file did not stop the MPC draining it — which
is why the stall shows up so sharply in the net.

### 2.4 What this does and does not say

The measurement is **"observations from F51/F52 stopped arriving in the ITF"**. It does
not identify a cause, and at least four fit:

1. Pan-STARRS was not observing (weather or maintenance at Haleakala — a five-day block is
   entirely ordinary).
2. Pan-STARRS was observing but not submitting.
3. Submissions arrived but were not routed into the ITF.
4. Submissions arrived and were **identified immediately**, so they never reached the ITF
   at all — which would look identical from here and would mean the opposite thing.

M12 does not adjudicate between these and should not be read as doing so. What it
establishes is that the event happened, on which days, at what magnitude, and that it was
confined to one station pair. **The MPC serves only the current ITF**, so absent the daily
archive none of that would be recoverable now — which is the archive's entire premise,
demonstrated on a real event rather than argued.

---

## 3. Where the departures go — a random sample, attributed and confirmed

CROSSWALK_SECTION

---

## 4. What this means for the ledger

The candidate ledger's perishability has been measured from the inside twice: M9 found
3.3% of candidates consumed per 2 days, and M11 corrected M10's "M9 rows lose nothing" to a
106 d PASS half-life against M8's 43.8 d. M12 measures the same clock from outside, on the
whole file rather than on selected rows.

* The mineable population — designations with **≥3 nights** — fell **2,515 → 2,455** in 26
  days, **−2.4%**.
* The file's whole-designation departure rate is **43,783 designations in 26 days**.

**That first number is not an arbitrary statistic.** `DISCOVERY/itf-linker.md` §Milestones
defines the project's internal ground truth as *"the **2,515 designations** that already
span 3+ nights"* — hide their trkSub linkage and confirm the linker rediscovers the
groupings. That set is **2,455 today**. The validation population M0 specified is itself
draining, at the same rate as everything else, and any future re-run of that control is
running on a different set than the one the plan describes.

The same section asks for exactly this analysis and says why it could not be done yet:

> Snapshot diffing (what vanished between two pulls, and which MPEC claimed it) is the
> natural second control — **which requires archiving snapshots starting now.**

That was written on 2026-07-29, the day the archive started. M12 is the first time the
second control has been run, and it needed 26 days of accumulation to say anything.

Neither number changes a gate or a verdict, and neither is a reason to submit anything.
What they do is put a floor under a statement M10 and M11 both make and neither could
size: the review queue is not merely *stale-able*, it is draining at a rate the archive
can now quote. An unreviewed candidate is not waiting indefinitely — the MPC is working
through the same file, from its own side, at 4.4 departures per arrival.

**The one thing §1.2 rules out** is the pessimistic reading of that drain. Departures are
not the MPC deleting data; they are whole tracklets being identified. A candidate that
disappears has almost always been *linked*, not lost — which is exactly the outcome M9 and
M11 measured on ledger rows, now shown to be how the file behaves in general.

---

## 5. Traps hit (all paid for; check before touching this code)

**1. A delta chain transports distinct keys; a snapshot file holds rows.** The ITF ships
~1,130 exactly duplicated records — every manifest reports the count as
`duplicate_observations` and it is not a defect. The first verification pass compared the
walk against on-disk **row counts** and failed all four checks by 1,154, 1,154, 1,131 and
1,131 — precisely the duplicate counts. An off-by-a-constant that looks exactly like a
broken walk and was a broken *comparison*. Both sides of every check now go through
`distinct_keys()`.

**2. M9's "reconstruction" is not the 08-16 key set, and it is not a designation-level
filter either.** `m9_reconstruct_snapshot.py` builds it as 08-18's rows whose `obs_key` is
also in the 08-16 key set, with every **tracklet** that lost any observation dropped
whole — where a tracklet is `(desig, obscode, night)` under `load_tracklets`' night
definition, and unnamed rows pass through untouched. Reading "tracklet" as "designation"
is off by **98 keys**, because a designation can hold several tracklets and lose only one.
Reproducing it exactly required importing M9's own `with_night`.

**3. A prefilter that caps its output must sort first.** The cross-walk keeps the closest
`REFINE_KEEP` candidates for perturbed refinement. The first version returned prefilter
survivors in **catalogue order**, so any tracklet with more survivors than the cap was
refined against an arbitrary subset. It confirmed **1 of 10**, and the one that worked was
the only tracklet whose candidate count happened to fall under the cap. Sorting by
two-body separation took the same pilot to 4 of 10; removing the cap took it to 8 of 10 —
**at no measurable wall-clock cost**, because the prefilter's 1.56M Kepler propagations
dominate and the perturbed refine is nearly free beside them.

**4. `get-obs` will not resolve an ITF trksub.** Querying `P114umu` — a tracklet M9
established was consumed into 2025 OZ431 — returns HTTP 500, `Bad Label from designation
identifier`. There is no trksub → object lookup at the MPC, which is why the cross-walk
has to search the catalogue locally.

**5. The development checkout is not the archive.** The daily task writes key sets into
the development tree but commits manifests and deltas from a separate archive clone, so
**neither tree alone holds the whole series**: the dev tree was missing six snapshots'
manifests that `main` has, and three of its snapshot directories hold a key set with no
manifest beside it. `m12_series.py` takes `--snapshots` for exactly this reason and was
pointed at a merged read-only view.

**6. Hand-built 80-column lines do not parse.** Two attempts at synthesising an OBS80
fixture for the confirmation test were rejected by `mpc80.parse_line` on column
alignment. The test now uses a line lifted verbatim from a real published record, which is
also the repository's existing convention (`tests/conftest.py`).

---

## 6. Tests

**517 passed** (505 before M12, plus 12 in `tests/test_m12.py`), ruff clean.

The new tests pin the two pieces of machinery that failed silently, plus the confound the
whole milestone rests on:

* re-designation is detected when an observation is re-labelled at the same
  `(obscode, mjd)`, and **not** detected when the arrival is a different night;
* whole vs partial departure is classified correctly, and a departure from outside the
  parent key set — which would mean the walk is wrong — is counted rather than dropped;
* `distinct_keys` collapses duplicate records and returns sorted keys, so two walks
  compare directly;
* an uncomputable delta starts a new segment, and pre-`delta_status` manifests still
  segment correctly;
* **the prefilter returns candidates nearest-first** and its radius actually excludes;
* the confirmation rule needs *both* halves — a published row at the same instant but 10″
  away, an hour later at the same place, or at a different station all fail to match,
  which is the pointed-field confound M10 had to screen for.

---

## 7. Outputs

| File | What it is |
|---|---|
| `scripts/m12_series.py` | The verified backward walk and per-step statistics |
| `scripts/m12_crosswalk.py` | Two-stage attribution + published-record confirmation |
| `data/raw/rubin/m12-series.json` | Every transition, with its verification record |
| `data/raw/rubin/m12-crosswalk.json` | The sampled tracklets and their confirmations |
| `data/raw/rubin/m12-departed-window.parquet` | Departures 08-19 → 08-23 with astrometry |
| `data/raw/rubin/m12-orbits-full.parquet` | 1,558,557 MPCORB orbits in sweep layout |
| `tests/test_m12.py` | 12 tests |

Reproduce with:

```
python scripts/m12_series.py --snapshots <merged-view> --out data/raw/rubin/m12-series.json
python scripts/m12_crosswalk.py --departed data/raw/rubin/m12-departed-window.parquet \
    --mpcorb data/raw/mpcorb/mpcorb_extended_20260823.json.gz \
    --orbit-table data/raw/rubin/m12-orbits-full.parquet \
    --cache data/raw/rubin/obs80-m12 --out data/raw/rubin/m12-crosswalk.json --sample 150
```

---

## 8. Recommended next milestone

M11 §9's five items are **all still open and all still rank above this**. In particular
item 1, the submission decision, is Matthew's and is unchanged by anything here — except
that §4 now puts a measured rate on the cost of waiting.

What M12 adds to that list:

1. **Watch whether Pan-STARRS intake returns.** As of 08-23 it has not. The archive will
   answer this for free on whatever days the machine is on; nothing needs to be built. If
   it stays dark, the ITF's growth stops and the file drains monotonically, which changes
   the arithmetic in §4.
2. **The 08-13 hole is the second measurement lost to key-set retention** (M11 §1.0 was
   the first). `KEYSET_KEEP = 4` in `snapshot-local.sh` is what bounds it. Raising it is
   cheap — each asset is ~170 MB and they are release assets, not git objects — and it
   would have prevented both.
3. **The unanchored 07-29 segment can never be recovered.** Its key sets are gone. If the
   earliest days matter, the only fix is to stop pruning, and it has to happen before the
   window rolls, not after.
