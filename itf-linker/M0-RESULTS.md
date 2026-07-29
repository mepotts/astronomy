# M0 — kill-check results

**Verdict: GO WITH CHANGES.** The data layer is sound and cheap; the *validation* the plan
specified turned out not to test what it was meant to test, and must be replaced before M1
generates any candidate. Details in [§5](#5-the-kill-check) and [§7](#7-verdict).

Every number below came from code in this repo, run against the snapshot identified in §1.
Reproduce with `itf-linker m0 --out m0-report.json`.

---

## 1. Provenance

The ITF is regenerated continuously, so a count means nothing without the snapshot it came
from. Recorded automatically to `data/raw/itf.provenance.json` at fetch time:

| Field | Value |
|---|---|
| URL | `https://www.minorplanetcenter.net/iau/ITF/itf.txt.gz` |
| Size | **134,759,732 bytes** |
| `Last-Modified` | **Wed, 29 Jul 2026 05:26:45 GMT** |
| `ETag` | `"8084534-657b9338b6bcf"` |
| Fetched | 2026-07-29T05:30:09Z |
| Auth | none — anonymous HTTP GET, exactly as the plan states |

The file moved twice during this session (`Last-Modified` 04:26:46 → 05:26:45, ETag changed)
while byte size and line count stayed identical. The download itself took ~6 s.

Parse: **9.1 s**, 9.36M lines → 189 MB Parquet (zstd). The plan's "laptop-scale" claim holds
comfortably; nothing here needed more than a few seconds or a couple of GB.

---

## 2. Measured counts vs the plan

The plan's figures were measured one day earlier (2026-07-28). Agreement is far closer than
daily drift would predict — every headline number lands within 0.01%.

| Metric | Plan (2026-07-28) | **Measured (2026-07-29)** | Delta |
|---|---|---|---|
| Gzipped size | 134,758,290 B | **134,759,732 B** | +1,442 B (+0.001%) |
| Lines in file | 9,359,693 | **9,359,688** | −5 (−0.00005%) |
| *Observations* | — | **9,322,655** | see §3 |
| Distinct observatory codes | 882 | **882** | **exact** |
| Observations dated 2026 | 248,810 | **248,819** | +9 (+0.004%) |
| F51 Pan-STARRS-1 | 2.75M | **2,752,362** | ✓ |
| W84 DECam | 1.20M | **1,196,646** | ✓ |
| G96 Catalina | 1.08M | **1,083,646** | ✓ |
| F52 Pan-STARRS-2 | 1.04M | **1,041,621** | ✓ |
| T09 Subaru | 0.87M | **872,715** | ✓ |
| X05 Rubin | 64,362 | **64,362** | **exact** |
| 645 SDSS | 28,120 | **28,120** | **exact** |
| C51 NEOWISE | 69,886 | **34,943** | **exactly ½** |

**Nothing here exceeds the 1% "possible parse bug" threshold.** Three codes match to the
unit, which is stronger evidence of a correct parser than the aggregate agreement is.

Two codes appear in my top-10 that the plan does not mention — **V00** Bok/Kuiper (484,879)
and **705** (462,094) — but the plan only ever claimed to list the top five plus a few
notable others, so this is a gap in the plan's prose, not a discrepancy.

---

## 3. The one real semantic difference: lines are not observations

**C51 measured exactly half the plan's figure (34,943 vs 69,886).** That factor of two is
not drift, and it is the single most important parsing finding in M0.

A space-based observation occupies **two** physical lines in the MPC 80-column format: the
`S` line carries the sky position, and a following `s` line carries the *spacecraft's*
geocentric x/y/z **in the RA/Dec columns**. The `s` line is not an observation. Counting it
both inflates the total and, if parsed naively, injects a garbage sky position (e.g.
`+1272.5482` in the RA field) into the astrometry.

Full line accounting for the snapshot:

```
9,359,688  lines in file
  −37,032  note-2 continuation lines   (36,860 's' + 172 'v'; zero radar)
       −1  malformed record            (see below)
─────────
9,322,655  observations
```

So the plan's 9,359,693 is a **line count**; the true observation count is **9,322,655**
(0.40% lower). Every C51 observation is an `S`/`s` pair, which is why that code halves
exactly. 1,282 `S` observations have *no* partner `s` line — those lack the spacecraft
position needed to reduce them and should be treated as unusable in M1.

**The one malformed record** in all 9.36 million lines:

```
     BCH0108  C2004 03 28.97460 11 59 13.60 +13 04 39 8                c     947
                                                       ^^^^
```

Declination seconds read `39 8` — a space where the decimal point belongs. This is a defect
in the MPC's file, not in the parser. It is rejected rather than coerced, and the rejection
is pinned by a test.

**Other data-quality findings** worth carrying into M1:

- **4 observations dated before 1900**, three of them within 0.0003 d of MJD 0
  (1858-11-17) — from observatory **705**, a modern CCD survey. These are sentinel/corrupt
  epochs, not real 19th-century astrometry, and would badly distort any temporal
  partitioning. Filter them.
- **3 observations carry no designation at all** (columns 1–12 entirely blank). Negligible,
  but they cannot be grouped and must not be silently merged into one pseudo-object.
- **Zero records carry a minor-planet number** in columns 1–5. This matters a lot — see §5.

---

## 4. Tracklet reconstruction

A tracklet is keyed `(designation/trkSub, observatory code, local night)`.

**Local** night is not optional. `floor(mjd)` cuts in half every night that straddles UTC
midnight — for observatories near Greenwich that is *every* night. The index used is
`floor(mjd + lon_signed/360 + 0.5)`, placing the boundary at local noon, with longitudes
from the MPC's `ObsCodes.html`. Longitude is wrapped to (−180, +180]: both wrappings group
a night correctly, but only the signed one makes the index equal the UTC date that the
night is conventionally labelled with — unwrapped, Mauna Kea lands a full day late and stops
lining up with the dates printed in an MPEC. Both properties are pinned by tests.

| Quantity | Value |
|---|---|
| Observations | 9,322,655 |
| **Tracklets** | **2,628,838** |
| Mean observations / tracklet | 3.55 |
| Median / p90 / p99 / max | 3 / 4 / 8 / 221 |
| Singleton tracklets | 6,377 (**0.24%**) |
| Distinct nights | 10,215 |
| Distinct designations (trkSubs) | 2,602,962 |
| Tracklet span, median / p99 | 0.64 h / 4.56 h |

Observations per tracklet: **3 (1,148,426) and 4 (943,191) dominate**, together 80% of all
tracklets — exactly the "typically three lines per tracklet" the plan describes.

Two structural findings:

**(a) The trkSub already *is* the tracklet.** 2,602,962 designations produce 2,628,838
tracklets — 1.01 tracklets per designation. Reconstruction is therefore nearly free, and
the real problem is not building tracklets but **linking them to each other**.

**(b) The ITF is overwhelmingly single-night**, which is precisely why it is unlinked:

| Nights per designation | Count |
|---|---|
| 1 night | 2,581,159 (99.2%) |
| 2 nights | 19,288 |
| **3+ nights** | **2,515** |

Only 6,377 tracklets (0.24%) are single-detection, so the MPC's "≥2 observations per object
per night" rule costs almost nothing: **2,580,036 of the 2,581,159 single-night designations
already have ≥2 detections.**

**Tracklets spanning >12 h: 1,901 — and 1,861 of them are C51.** Those are space telescopes
in low Earth orbit, where "night" has no meaning. Not a bug; a population that needs its own
handling.

---

## 5. The kill-check

### 5.1 What was asked, and what the answer is

All three MPECs were retrieved successfully (HTTP 200, URLs exactly as the plan predicted)
and parsed. Identity, credit, and constituent-observation inventory were recovered from each:

| MPEC | Object | `Id.` credit | Constituent obs | Tracklets | Nights | Arc (d) |
|---|---|---|---|---|---|---|
| 2026-O40 | 2017 SC33 = 2026 NY1 | A. Lowe | 25 | 8 | 7 | 3,220 |
| 2026-O57 | 2009 AC16 | P. VanWylen | 49 | 16 | 10 | 6,397 |
| 2026-O86 | 2011 YD40 = 2026 OO3 | R. Matson, F. Manca, B. Engebreth | 51 | 13 | 11 | 5,322 |

All three pass the MPC's published acceptance criteria under my implementation of that gate
(≥3 nights, arc ≥3 d, not-3-nights-with-arc>15 d, not singleton-ended) — as they must, since
the MPC accepted them. The gate is separately tested to *reject* each failure mode, so this
is not a vacuous pass.

**Are their observations in the ITF snapshot? No — none of them.**

- **0 of 9** exact observation matches for 2026-O57 (the only one of the three that prints
  full 80-column astrometry), matched on observatory + epoch + sky position within 10″.
- **0 ITF rows** carry any of the five packed designations (`K17S33C`, `K26N01Y`,
  `K09A16C`, `K11Y40D`, `K26O03O`).

**The absence is real, not a broken matcher.** A sensitivity control re-queries 200 randomly
sampled known-present ITF rows through the *identical* code path: **200/200 found, hit rate
1.00.** Negative controls (wrong observatory, wrong epoch, 1° offset) all correctly return
nothing. Without that control, "not found" would be worthless.

### 5.2 Why they are absent — and why this invalidates the test as designed

The obvious reading is the plan's own: linking is what removes observations from the ITF, so
of course they are gone. **That reading is wrong here, and the real reason matters.**

**The ITF contains no designated objects at all.** Measured:

- **0** of 9,322,655 records carry a minor-planet number in columns 1–5.
- Only **28** of 2,602,962 distinct designations even pattern-match a packed provisional
  designation — and those are coincidences: they are W84/DECam survey trkSubs such as
  `J90O1JA` and `K02P1KD`, whose observation dates (2019–2025) never match the designation
  year the pattern implies (1990, 2002). Zero survive that consistency check.

The ITF is **trkSub-only by construction**. But all three of these MPECs link objects that
*already had designations* — `2017 SC33`, `2009 AC16`, `2011 YD40` were designated in 2017,
2009 and 2011 respectively. Their observations were therefore never in the ITF; they sat in
the MPC's ordinary observation database as designated-but-unlinked apparitions.

**These three MPECs are designation-to-designation identifications, not ITF-to-ITF links.**
They are excellent evidence for the *credit mechanism* the plan is built on — a private
individual's name on an IAU circular, weekly, which is the project's actual thesis — but
they are **not** evidence that an ITF mining pipeline works, and re-deriving them would not
have exercised one. The plan's M0 instruction to "confirm their constituent observations are
present" could not have succeeded for any snapshot, on any day.

This is a flaw in the validation design, not a failure of the pipeline. It is the main
reason the verdict is GO **WITH CHANGES**.

### 5.3 What was validated instead

Per the fallback the task specifies, the parser and grouping were validated end-to-end
against the MPEC's own astrometry — which is real MPC-formatted data of exactly the kind the
ITF contains.

MPEC 2026-O57's nine `Additional Observations` lines were pushed through the **production**
parser and the **production** tracklet builder (not test-only code). Result:

| | Observatory | Observations | Night (MJD) | Span |
|---|---|---|---|---|
| 1 | F51 | 4 | 61241 | <1 h |
| 2 | T14 | 3 | 61242 | <1 h |
| 3 | M21 | 2 | 61243 | <1 h |

Exactly three tracklets, on three consecutive distinct nights, correctly split by
observatory, with `K09A16C` recovered as the designation and the discovery asterisk found on
the right record.

**This is independently corroborated.** The same three tracklets are recoverable from the
MPEC's *residuals table*, a completely separate extraction path (`YYMMDD` + observatory
inventory rather than 80-column astrometry). Both paths agree exactly:
`{F51: 4, T14: 3, M21: 2}`. A parser or grouping error would have to corrupt two unrelated
code paths identically to hide.

That cross-check also caught a genuine bug: MPECs can carry a *second*, two-row residual
table ("First and last observations above in comparison with prediction") whose entries
duplicate the main one. Counting both reported 51 constituent observations for 2026-O57
instead of 49, and inflated the F51 tracklet from 4 observations to 5. The disagreement
between the two paths is what surfaced it; it is fixed and pinned by a test.

### 5.4 Would the partitioning have reached them?

For the MPEC nights where the ITF still holds contemporaneous material from the same
telescope, the answer is yes — there is plenty of ITF material in exactly those cells:

| MPEC | Night cells with ITF material | Example |
|---|---|---|
| 2026-O40 | 4 / 8 | 2017-09-24 F51: 3,440 ITF tracklets / 11,619 obs |
| 2026-O57 | 1 / 16 | 2026-07-20 F51: 1,405 ITF tracklets / 4,816 obs |
| 2026-O86 | 8 / 13 | 2011-12-31 G96: 402 ITF tracklets / 1,547 obs |

The empty cells are all small follow-up telescopes (568, T14, M21, H01, T12) whose data is
always linked promptly and which contribute essentially nothing to the ITF. The survey
codes that dominate the ITF — F51, F52, G96 — are well represented on the right nights.

---

## 6. Partitioning feasibility

Brute force is `C(2,628,838, 2)` = **3.46 × 10¹²** pairs. Measured exactly (not estimated
from a uniform-sky assumption — the ITF is heavily clustered on survey footprints), for
same-pixel candidates separated by more than 0.5 d (same-night pairs are useless) and at
most the window:

| nside | Pixel | Window | Pairs | Triplets | Pixel ≥ motion? |
|---:|---:|---:|---:|---:|:--:|
| 16 | 3.67° | 3 d | 1.69 × 10⁸ | 6.14 × 10¹⁰ | yes |
| 16 | 3.67° | 7 d | 3.11 × 10⁸ | 1.62 × 10¹¹ | yes |
| 32 | 1.83° | 3 d | 5.44 × 10⁷ | 8.59 × 10⁹ | yes |
| 32 | 1.83° | 15 d | 1.53 × 10⁸ | 4.26 × 10¹⁰ | no |
| **64** | **0.92°** | **3 d** | **1.54 × 10⁷** | **7.53 × 10⁸** | **yes** |
| 64 | 0.92° | 15 d | 4.41 × 10⁷ | 3.72 × 10⁹ | no |
| 128 | 0.46° | 3 d | 4.36 × 10⁶ | 9.41 × 10⁷ | no |

"Pixel ≥ motion?" is the recall constraint: a main-belt object moves ~0.3°/day, so over a
window `W` it travels `0.3W` degrees. If the pixel is smaller than that, genuine links fall
outside the partition and are **never proposed** — a silent recall failure that no amount of
downstream vetting can recover. The seductive bottom row (4.4M pairs at nside=128) is
exactly the trap: it is cheap because it is throwing away real links.

### The actual conclusion

**Pairs are cheap; triplets are the wall.** Pair generation is 10⁷–10⁸ at every usable
setting — minutes of laptop compute. Naive triplet enumeration is 10⁸–10¹¹ and is
**not** tractable. Since the MPC auto-rejects anything with fewer than 3 nights, triplets
are what the project actually needs.

That single fact determines the M1 architecture: **do not enumerate triplets.** Use the
pair→predict→confirm approach (FindPOTATOs) or hypothesis-propagation clustering
(HelioLinC): fit a preliminary orbit to each *pair* under an assumed heliocentric distance,
propagate to a third night, and look up a small predicted region. That is `O(pairs)`, not
`O(triplets)`, and it turns a 10¹¹ problem into a 10⁷ one.

### Recommended M1 partition

**nside=64 (0.92° pixels) × 3-day windows: 15.4M pairs.** The pixel just covers 3 days of
main-belt motion (0.92° ≥ 0.90°), so it is the smallest safe choice. Budget ~9× for
neighbouring-pixel search across boundaries → ~1.4 × 10⁸ pair evaluations, still trivial.
Faster-moving NEOs need either a coarser nside or a shorter window.

**Better first target — the recent slice.** Restricting to MJD > 60000 (2023-02 onward,
where follow-up is still physically possible) gives **512,106 tracklets**, and at
nside=64 / 15 d only **1.3M pairs and 9.2M triplets** — small enough to enumerate triplets
directly, no clever algorithm required. This is the natural M1 sandbox.

For scale, the single busiest nside=32 pixel holds 12,314 tracklets spanning 1991–2025 and
yields 14.0M pairs in a 30-day window on its own — worth knowing before pointing a linker at
a deep-drilling field and assuming uniformity.

### The finding that most changes M1's shape

**2,515 designations already have 3+ nights *inside the ITF*, under a single trkSub —
1,046 of them pass the MPC's night/arc/≥2-per-night gates, 976 from a single observatory,
median arc 7 days.** These require **no linking at all**: the multi-night association already
exists in the file and merely lacks an orbit. They are the obvious first thing to fit.

Caveat, and it is a real one: trkSubs are *not* globally unique. Some multi-night groups are
clearly reused generic names (`des278` — 17 nights over 1,154 d; `soho183` — 12 nights over
3,555 d) and are name collisions, not objects. The gated subset above is filtered to plausible
arcs and single observatories, but each candidate still needs verification.

**19,288 designations sit at exactly 2 nights** (15,067 with ≥2 observations on both).
Those need exactly one more night to clear the MPC's threshold — a far better-conditioned
search than blind 3-way linking, because a 2-night arc constrains where to look.

---

## 7. Verdict

### GO WITH CHANGES

**What is proven.** Ingest, parse, and tracklet reconstruction work and are cheap: 6 s to
download, 9 s to parse 9.36M lines, seconds to build 2.6M tracklets. Counts reproduce the
plan to within 0.01% on every headline figure and exactly on three observatory codes. The
parser handles the format's genuinely awkward corners — space-based `S`/`s` pairs, mixed
RA/Dec precision, a malformed record, blank designations — and is pinned by 60 passing
tests, including agreement between two independent implementations. The zero-cost,
zero-auth, laptop-scale premise of the plan is **confirmed exactly as written**.

**What is not proven, and must change.** The plan's chosen kill-check cannot validate an ITF
pipeline. All three July-2026 identification MPECs link previously-*designated* objects,
whose observations were never in the ITF (which contains zero designated objects and zero
numbered objects). Re-deriving them would not have exercised the ITF path on any snapshot,
on any day. The parser and grouping were instead validated end-to-end on real MPC astrometry
from MPEC 2026-O57, corroborated by a second independent extraction path — but that is a
weaker claim than "we re-derived a known ITF link", and it should not be reported as one.

**Required changes before M1 generates candidates:**

1. **Replace the validation with a real ITF ground truth.** Use the ITF's own internal
   structure: hide the trkSub linkage on the 2,515 designations that already span 3+ nights,
   and confirm the linker rediscovers those groupings from positions and epochs alone. That
   is genuine, available, in-file ground truth and it exercises exactly the code path M1
   depends on. Snapshot diffing (what disappeared between two ITF pulls, and which MPEC
   claimed it) is the natural second control, and requires starting to archive snapshots
   **now** — today's is already saved.
2. **Architect around pairs, never triplets.** 10⁷ vs 10¹¹. Non-negotiable.
3. **Pick the recent slice (MJD > 60000) as the M1 sandbox** — 512k tracklets, 1.3M pairs,
   and follow-up still physically possible.
4. **Start with the 1,046 gated 3+-night designations**, which need fitting rather than
   linking — but verify each against trkSub collision first.
5. **Filter the known bad data**: 4 pre-1900 sentinel epochs, 1,282 unpaired `S`
   observations, 3 blank designations, 1 malformed record.

**Effort estimate — the question M0 was meant to answer.** A weekend, not a month, for a
first ranked candidate list, *conditional on* Find_Orb integration being the only genuinely
new component. The data layer took hours. The combinatorics are not the bottleneck the plan
worried about. The bottleneck is orbit fitting and vetting discipline — which is where the
plan already says the real work is, and where its guardrails are correctly aimed.

**Nothing was submitted anywhere.** All network access was read-only HTTP GET against public
MPC URLs.
