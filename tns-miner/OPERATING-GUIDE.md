# tns-miner — operating guide

**Everything needed to run this front is in this one file.** You do not need to
read the milestone documents. Where a number appears, the document that measured
it is named so you can check it, not so you have to.

**Last updated 2026-09-02, after the cache-provenance and time-window repair.**

> ## HOUSE LAW, ABSOLUTE
> **No agent ever submits anything to TNS — not a discovery report, not a
> classification, not a bulk report, not a sandbox test. No agent creates an
> account anywhere.** The allowlist guard in `scripts/tnscommon.py` enforces the
> read-only rule in code and must not be weakened. Every candidate row carries
> `STATUS = MATTHEW-GATED -- NOT REPORTED TO TNS`. Submitting is a human act,
> §6 below.

---

## 0. What this front is, in one paragraph

TNS defines the discoverer as *"the reporter/s whose discovery report first turns
to public"* — first to **report**, not first to observe. ZTF's public alert stream
is open and tokenless, and the survey pipelines that report to TNS are tuned for
extragalactic supernovae: they demand a resolved host and cut on star/galaxy
score, so they structurally discard **stellar transients in the galactic plane at
any magnitude**. That is the measured gap: 5.8% of all TNS reports come from
|b| < 15°, but 55% of DCAP's and 68% of XOSS's do (`M1-02`, 30,454 real reports).
This project mines the residue of that filter policy. **ZTF primary operations end
December 2026**, so the window is roughly four months from now.

**The historical state, measured but awaiting a freshness- and input-proved
rerun; its old TNS candidate-veto state is not exactly reconstructible.** The
filter recovered **46%** of DCAP's
designations from data that existed before their report was filed, at a median
lead of 3.1 days and **9.2×** the rate at which it fires on the objects the survey
pipelines already own (`M2-03`). A three-night pass turns ~290,000 alerts into
**37 candidates**. Hand-vetting a pre-registered random sample of those against
image cutouts and six archival catalogues measured **precision at 8.0%, 95% CI
[2.2%, 25.0%]** (`M2-04`) — up from **3.5% [1.1%, 15.6%]** for the M1 filter, with
the image-artifact fraction down from 40% to 12%. A further **32%** of the list is
a *real* dwarf-nova or symbiotic outburst on a star that **already has a
designation**: genuine astrophysics, correctly detected and flagged, and not
reportable.

**So: roughly nine rows in ten are not a new transient. This is a
human-in-the-loop tool that shortens a night's search from ~100,000 alerts to a
handful of objects to look at. It is not, and must not be treated as, an automatic
reporter.**

---

## 1. Run a nightly pass

### 1.1 Setup, once

```bash
cd tns-miner
python -m venv .venv
./.venv/Scripts/python.exe -m pip install requests pandas numpy astropy matplotlib pillow
```

No credentials of any kind. Everything below is tokenless.

Layer 6 also needs a proved TNS registry snapshot. The public export can receive
late reports whose discovery dates lie in older months, so a publication-grade
snapshot refreshes the full rolling 12 months; it does not assemble a newly
dated snapshot from stale closed-month caches. At the unauthenticated 8/60 s
limit this is roughly 8–15 minutes (77 pages / 13.8 minutes on 2026-09-02).
Run it after the alert window closes and before building candidates. It writes
an immutable, hash-named file
under `data/tns/snapshots/` plus the compatible rolling `data/tns/tns_12mo.csv`.
The harvest calendar is UTC, includes the current UTC day even on the first of a
month, and refuses repeated or overlapping TNS IDs across pages rather than
publishing a deduplicated but potentially incomplete scan. A closed month must
contain at least one object; only the explicitly labelled current partial month
may be header-only. IDs must also be disjoint across month windows—final assembly
never hides an overlap with `drop_duplicates`. Every nonempty page is followed
until TNS returns an explicit header-only page—even if the server silently uses
a smaller page size—and every `Discovery Date (UT)` must fall inside that page
request's half-open UTC interval.

### 1.2 The pass

`t1` = the MJD of this morning; `t0` = `t1 - 3`. Three days rather than one
because ZTF needs two detections ≥ 30 minutes apart before the filter can fire,
and a three-day window means a source that erupted the night before last is
already in hand.

For any completeness or publication claim, use the proved campaign entry point,
not the four individual commands below. It holds one whole-run lock, gives the
campaign isolated gitignored `data/runs/<tag>/data` and `out` trees, records the
SHA-256 of every science script, captures detailed output privately, retains the
exact HTTP entity bytes returned by Fink and TNS, and authenticates every cache
and final output before writing `SEALED.json`. The TNS scan runs first so its
start remains within one day of the alert-history ceiling even if Fink takes
hours. A failed source leaves an inspectable private bundle but never a sealed
candidate result or a scientific zero.

The closed TNS corpus is the newest **fully closed** twelve-calendar-month
interval at run time: start of the UTC month one year ago through start of the
current UTC month, half-open. On 2026-09-02 that is
`[2025-09-01, 2026-09-01)`, i.e. all discovery dates from September 2025 through
August 2026. The live registry snapshot additionally includes the current
partial month for duplicate annotation.

```powershell
$tag = "20260902_proved_unique"  # unique immutable run label
$t0 = 61282
$t1 = 61285
./.venv/Scripts/python.exe scripts/run_proved_window.py `
  --tag $tag --mjd-start $t0 --mjd-end $t1 `
  --closed-start 2025-09-01 --closed-end-exclusive 2026-09-01
```

Candidate details and the child log remain private. `SEALED.json` is deliberately
counts-only. A run without `SEALED.json` is incomplete regardless of which
intermediate files exist.

The commands below remain useful for development and diagnosis, but they do not
by themselves create a sealed campaign bundle.

```powershell
$tag = "20260902"  # UTC window-end date; never reuse a tag for another t0/t1

# 1. enumerate + filter
#    ~90 min for arm E2 (it walks ~295 Fink classes, bisecting the ones that hit
#    the 1000-row cap) + ~20 min of Fink history fetches on a cold cache.
#    Both are cached per tag, so a re-run of the same night is minutes.
./.venv/Scripts/python.exe scripts/m2_pool.py <t0> <t1> $tag

# 2. after t1, freeze the current TNS registry scan used for duplicate avoidance
./.venv/Scripts/python.exe scripts/m1_tns_harvest.py

# 3. build the ranked candidate list
./.venv/Scripts/python.exe scripts/m2_candidates.py $tag

# 4. render the evidence sheets you will actually look at
./.venv/Scripts/python.exe scripts/m2_vet_evidence.py build "out/m2_candidates_$tag.csv" $tag
```

Pool and catalogue caches carry SHA-256 sidecars binding them to their exact
window or ordered `(oid, ra, dec)` input. Reusing a label such as `tonight` for a
different window now fails instead of silently relabelling yesterday's rows.
Run tags are strict portable slugs: 1–64 ASCII letters/digits with only internal
`_` or `-`, beginning and ending with a letter/digit. Empty tags, dots, path
separators, whitespace, punctuation, and reserved device names are rejected
before any tag-derived file is opened or written.

Outputs:

| file | what it is |
|---|---|
| `out/m2_candidates_<tag>.csv` | the ranked list, one row per object, every column below |
| `out/m2_candidates_<tag>.json` | counts plus exact Fink-input and TNS-snapshot digests |
| `out/m2_candidates_<tag>.tns-input.json` | crash-safe immutable TNS snapshot pin; never edit or copy across tags |
| `out/vet/<tag>_sheet*.png` | four objects per sheet: science / template / difference cutouts and the per-band light curve |
| `out/m2_pool_<tag>.json` | pool sizes and the top rejection reasons — read this when a night returns nothing |

**Get MJD:** `python -c "import pandas as pd; print(pd.Timestamp.utcnow().to_julian_date()-2400000.5)"`
(or `date -u +%s` → `(unix/86400)+40587`).

### 1.3 What to look at, in order

**Start with the two-column rule.** Filter the CSV to rows where `flag_known_cv`
is empty **and** `atlasvs_sep`, `vsx_sep` and `gaiavar_Class` are all empty. On
the M2 pass that subset was 13 of 37 rows, and a full census of it found **zero
image artifacts and five plausible transients** (`M2-04`). Everything else on the
list is either a real outburst on a star that already has a designation — genuine,
but not reportable — or something a catalogue already knows about.

1. **Sort by `rank_score`** — the file is already sorted. The score is declared in
   `M2-01` B4 and is a presentation order, not a threshold; nothing is removed by it.
2. **Open the evidence sheet** for the top rows and look at the **difference
   stamp**. This is not optional — see §4.1. Half of all artifacts are invisible
   in every column and visible instantly in the image.
3. **Check `gaia_DR3Name`.** Blank is good: no Gaia source within 3″ means the
   quiescent object is fainter than G ≈ 21, which is what a CV or nova progenitor
   looks like. In the M2 vetting sample **39 of 40 contaminants had a Gaia
   counterpart, and the one clean dwarf nova did not** (`M2-02`).
4. **Check `atlasvs_sep` / `vsx_Type` / `gaiavar_Class`.** Any of these populated
   means somebody already catalogues this position as variable. It is not an
   automatic reject — that is the point of fix (c) — but it is a strong prior.
5. **Check `JK` and `gaia_BP-RP`.** `J−K > 1.0` **and** `BP−RP > 2.0` is the Mira
   trap (§4.6). M1's single best-named candidate was one of these.
6. **Read `outburst_history`.** Episodes with a return to non-detection between
   them is a dwarf nova. Continuous detection for years is a variable star or a
   reference-image hole.

---

## 2. The pre-registered thresholds, and why each one is what it is

The rule that fixes every number, unchanged since `M1-03`, in priority order:

> **(i)** the value a published ZTF / AMPEL / ZTF-BTS "real transient" recipe
> already uses for that field; **(ii)** a boundary this project's own documents
> already name; **(iii)** the loosest value that excludes an artifact class by
> construction.
> **No threshold may be chosen by looking at how many candidates it yields.**

### Layer 1 — per-detection hygiene

| cut | value | rule | why |
|---|---|---|---|
| `i:isdiffpos` | `t` | (iii) | positive subtraction: brightening, not fading |
| `i:drb` | ≥ 0.90 | (i) | ZTF deep real-bogus, standard high-purity cut. **Read §4.1 — this does not see a bad subtraction.** |
| `i:rb` fallback | ≥ 0.55 | (i) | legacy score for alerts predating `drb` |
| `i:nbad` | 0 | (iii) | any bad pixel in the stamp → reject by construction |
| `i:fwhm` | ≤ 5.0 | (i) | ZTF standard |
| `i:elong` | ≤ 1.4 | (i) | ZTF standard |
| `abs(i:magdiff)` | ≤ 0.5 | (i) | ZTF standard is 0.1; loosened because PSF-vs-aperture scatter at mag 20 exceeds 0.1 |
| `i:magpsf` | 12.0 – 20.6 | (ii) | 12.0 sits just below DCAP's brightest report and at ZTF saturation; 20.6 is ZTF's practical single-epoch floor |
| `i:ssdistnr` | < 0 or > 5.0″ | (i) | ZTF's own known-minor-planet match radius |
| `d:roid` | not 2 or 3 | (i) | Fink solar-system candidate / MPC match |

### Layer 2 — multiplicity

**≥ 2** clean detections, separated by **≥ 30 min** (0.02083 d). Rule (iii): below
30 minutes a main-belt asteroid has not moved measurably. **This is the cut that
costs the most speed** — the filter cannot fire on the discovery exposure itself,
so a human eyeballing a single alert beats it by up to a night. Non-negotiable: a
false discovery report is a public, permanent, attributed error.

### Layer 3 — catalogue, as amended by M2 fix (c)

- **`d:tns` present → reject.** Already reported.
- **VSX / GCVS → reject only if the type is in the periodic family** (`M`, `SR*`,
  `L*`, `RR*`, `CEP`, `DCEP`, `CW`, `ACEP`, `EA/EB/EW/E/ELL`, `RS`, `BY`, `DSCT`,
  `GDOR`, `ACV`, `SXPHE`, `ROT`, `BCEP`, `SPB`, `ZZ*`, `GCAS`, `LPB`), matched on
  the type string truncated at the first `/ : + (`. **Everything else is a flag,
  not a veto.** Rule (iii): a published periodic variable has nothing new to
  claim; a `YSO:` label does not mean the object is a YSO. This recovered
  **AT 2026lck**, a confirmed nova that `M1-04` lost to exactly that mislabel.
- **CV-family types** (`UG*`, `NA`, `NB`, `NC`, `NL`, `NR`, `N`, `ZAND`, `AM`,
  `DQ`, `CV`) → keep, flag `known_cv`, and **warn in the one-liner: the outburst
  is real but the object is not new, so it must not be filed as an AT report.**
- **SIMBAD**: the specific periodic classes and every extragalactic class
  (AGN, QSO, Blazar, Galaxy, …) stay hard vetoes — the mission scope excludes the
  second group outright. `Star`, `Variable*`, `PulsV*`, `SB*`, `Radio` and `X` are
  **flags**: a nova erupting on a catalogued star is classed `Star` by SIMBAD, so
  vetoing on it rejects the exact case this front exists to find.
- **A trailing `_Candidate` is stripped before every class comparison, on both
  sides.** SIMBAD serves 315 classes and the `_Candidate` form of nearly all of
  them, and Layer 3 compares literal strings — so before M2 fix (c3), `AGN` was
  vetoed while `AGN_Candidate`, `Blazar_Candidate`, `QSO_Candidate`,
  `LongPeriodV*_Candidate`, `Mira_Candidate` and `EclBin_Candidate` all passed.
  `LongPeriodV*_Candidate` alone carries ~2,700 alerts on a representative night.
  The fix costs zero recall on the positive control and introduces no parameter.
- **`"Fail 502"` in any `d:` column is a service error, not a catalogue hit.**
  Treating it as a hit silently vetoes real candidates. It counts as null.

### Layer 4 — nuclear / TDE veto

Reject if `i:sgscore1 ≤ 0.30` **and** `i:distpsnr1 ≤ 1.0″` — sitting on a PS1
galaxy centroid. Rule (i). The mission scope excludes TDEs and nuclear transients
and this is the cut that enforces it. It is also why 9 of 10 SN Ia in the positive
control were correctly rejected.

### Layer 5 — target channels

| channel | condition | hunting |
|---|---|---|
| `B_M31` / `B_M81` | within 1.5° of M31 (10.6847, +41.2687) or 0.5° of M81 (148.8882, +69.0653) | resolved-galaxy novae |
| `A2_nova_like` | no PS1 source within **3.0″**, or the nearest is fainter than 21.0 | classical nova |
| `A1_cv_outburst` | PS1 source within 3.0″ and `sgscore1 ≥ 0.50` | CV / dwarf nova on its own progenitor |
| `D_galactic_plane` | \|b\| < 15°, any magnitude | the measured gap |
| `C_faint_residue` | mag 19.0–20.6, nothing above matched | faint residue |

`sgscore1 = 0.5` is what ZTF writes when PS1 has no opinion, and for this class the
no-opinion side is the side to keep — hence `≥`, not `>`. A1 and A2 tile the axis
at a single radius; a gap between them silently drops every bright in-plane object
with a ~2″ association, which is how `M1-03` v1 rejected a real nova.

### Layer 7 — the M2 additions

| cut | value | rule | why |
|---|---|---|---|
| **per-band amplitude** `amp = max_f [ median(magnr\|f) − min(magpsf\|f) ]` | ≥ **1.0** mag | (ii)+(iii) | ~5× ZTF's single-epoch scatter at mag 20; below it an excursion cannot be told from noise on the reference source. **`magnr` is per-band — computing it across filters makes any constant source with a colour term look variable.** |
| **new-source requirement** (channels A2 / B only, where there is no quiescent source to measure) `jd_trigger − i:jdstarthist` | ≤ **90 d** | (iii) | a position where PS1 shows nothing but ZTF has been detecting for years is a reference-image hole by construction. 90 d is the outer edge of a classical nova's detectable decline. **This one misfires — see §4.2.** |
| **flat-residual veto** | per-band peak-to-peak < **0.30** mag in **every** band with ≥ **3** clean detections in the last **60 d** → reject | (ii)+(iii) | 0.30 is below ZTF's own per-epoch scatter at mag ~20, so there is no variability left to claim. Cannot fire when no band has 3 detections: absence of a measurement is not a measurement. |
| **negative-subtraction veto** `n_negative / n_high_confidence` | > **0.05** → reject | (iii) | a source genuinely *above* its reference cannot subtract negative. A few are reference noise; more than one in twenty means the source spends real time below its reference — variability about a mean, not an outburst. **POST-HOC, see §4.3.** |

### Layer 6 — TNS exclusion

Positional cross-match at **3.0″** (TNS's own duplicate radius), on top of Fink's
per-alert `d:tns`. Candidate membership is fixed by one immutable, SHA-256-named
full-12-month TNS scan that began after the alert-history ceiling and no more
than one day later. Rows whose `Discovery Date (UT)` is after the ceiling are
excluded from that frozen veto. The latest verified snapshot is also matched,
but only into `tns_current_*` annotation columns; it cannot remove an object from
the frozen candidate census.

This is a **conservative duplicate veto, not an exact TNS-registry-as-of
reconstruction**. The public CSV has discovery time but no report-publication
time. A report filed after the ceiling can carry an earlier discovery date, so a
post-window snapshot may contain limited future registry knowledge even after
the discovery-date bound. The exact historical registry state of the 2026-08-24
candidate run is therefore unreconstructible from this export. Its old candidate
counts must not be described as an exact as-of census.

### The enumerator

Two arms, union complete over a night (`M2-03` fix b):

- **E1, new sources** — ALeRCE `/ztf/v1/objects/?firstmjd=[t0,t1]&ndet=2`.
- **E2, known sources erupting** — Fink `/api/v1/latests` **accepts `startdate` /
  `stopdate`**. For every Fink class the Layer-3 veto does not reject, pull the
  window; when a call returns exactly 1000 the cap is binding, so bisect until
  every slice is under cap. An alert enters the pool if `isdiffpos = t`,
  `drb ≥ 0.90`, and (`magnr − magpsf ≥ 1.0` **or** `magnr` is null/≥ 99).

**Which classes get enumerated is derived from the filter's veto list, not
chosen** — no free parameter, and if the veto changes the enumerator follows.
`AMP_ENUM = AMP_MIN = 1.0` deliberately: the enumerator must never cut deeper than
the filter, or it becomes the thing that decides.

---

## 3. Rate limits and etiquette

| service | limit | what this project does |
|---|---|---|
| **TNS** (`/search?…&format=csv`, `/object/<name>`) | **10 requests / rolling 60 s, unauthenticated, ONE SHARED BUCKET across `/api/` and `/search`** | 8 / 60 s (7.5 s spacing), never two TNS jobs at once |
| Fink REST | none published | ≤ 3 concurrent workers; batch `objectId` lists of 60 |
| ALeRCE | none published | serial, 0.3 s between pages |
| CDS X-Match | none published | one call per catalogue per list, 1 s apart |
| ATLAS forced photometry | 60 submissions/min, 500 queued tasks, 100 positions/task | human step |

**TNS reads that do NOT work without credentials:** `/api/get/object`,
`/api/get/search` (401) and the `tns_public_objects` bulk mirror (403). The
tokenless route that does work is the ordinary web search page with
`&format=csv`; `num_page` maxes at **500** (asking for 1000 silently falls back
to 50). The per-object *report time* is not in the CSV — it is on the object page
under **"Time received (UT)"**, and it differs from the discovery epoch by around
a day, which matters for any lead-time claim.

---

## 4. Known failure modes

### 4.1 `drb ≥ 0.90` does not see a bad subtraction. **Look at the image.**

In the M2 vetting sample **16 of 40 candidates (40%) were image artifacts, and
every one carried `drb ≥ 0.913`** (median 0.989). ZTF's real-bogus classifier asks
*"is there a real source in this stamp?"* — and for a registration dipole on a
bright star the answer is yes, there is a genuine positive lobe. It does not ask
whether the *flux excess* is real, which is the question a discovery report rests on.

The negative-subtraction veto (Layer 7) catches about **half** of them from the
alert columns alone. The other half — saturated-star wings, single-epoch bloated
residuals, globally bad subtractions — look clean in every column ZTF publishes.
**There is no column that closes this.** Looking at the difference stamp is a
mandatory step, which is why `m2_vet_evidence.py` is part of the nightly pass and
not an extra.

What to look for, in the ±6σ diverging rendering the tool produces:
- **red lobe with a blue lobe a pixel or two away** → registration dipole. Reject.
- **red blob several times wider than the other point sources** → bright-star
  residual. Reject.
- **white saturation block anywhere near the crosshair** → reject.
- **blue core with a red ring** → PSF-mismatch residual. Reject.
- **a small, round, centred red dot and nothing else** → keep.

### 4.2 The A2/B new-source test misfires on recurrent CVs

`i:jdstarthist` is the earliest epoch of `ndethist`, which counts **every**
spatially-coincident detection back to the start of the survey — including
low-confidence and negative ones. For a recurrent dwarf nova whose quiescent
counterpart is fainter than PS1's limit (common, and squarely on target),
`jdstarthist` reaches back to an eruption years ago even though the current
episode is two days old.

Measured on the 29 DCAP objects that reach channel A2/B (`M2-03`):

| newness test | keeps |
|---|---|
| shipped: `jd_trigger − jdstarthist ≤ 90 d` | **22 / 29** |
| alternative: span of the **current clean-detection episode** ≤ 90 d | **29 / 29** |

The alternative separates the two cases exactly as intended: a reference hole is
detected *continuously*, a recurrent CV is not. **It is deliberately not shipped.**
Changing a cut after seeing what it costs is what the threshold rule exists to
prevent, and its precision has not been checked. If you want it, the change is in
`scripts/m2_filter.py`: replace the `hist_span_days` test in the `needs_new`
branch with the span from the first to the trigger clean detection.
**Its output would be unvetted** — treat any object it adds as needing the full §5
check before it goes anywhere.

### 4.3 The negative-subtraction veto is post-hoc

It was found by looking at the M2 vetting outcomes, not pre-registered. Its
threshold is fixed by rule (iii) rather than by yield, and it is validated
out-of-sample: **0 of 98 DCAP objects has a single high-confidence negative
detection in its entire Fink history**, so the cut cannot fire on the target class
at any threshold from 0.00 to 0.50. It is labelled POST-HOC in the code and in
every table. If a future fresh vetting shows it removing real transients, remove it.

### 4.4 The trigger epoch must be floored to the current episode

Evaluating a candidate pass with no `jd_floor` makes the filter fire at the
object's **all-time** first passing epoch. For a recurrent CV that is an eruption
years ago, and then `mag_at_pass`, `first_pass_jd`, the per-band amplitude, the
peak-to-peak and the flat-residual veto all describe *that* outburst instead of
the one that put the object in tonight's pool. On the first M2 run **41 of 44
candidates had a trigger epoch more than a year before the enumeration window**,
and M1's candidate pass has the same defect. `m2_pool.py` now floors the visible
history at `EPISODE_FLOOR_DAYS = 60` before the window. If you change the
enumeration window, that floor moves with it — do not hard-code a date.

The tell: `first_pass_jd` far from the window, and a flat-residual veto that
almost never fires.

### 4.5 Gaia DR3's variability classification is a column, not a veto — and it should be

Five of the twenty-five objects in the M2 vetting sample carry a Gaia DR3
`vclassre` class of `AGN` within 0.4″, and Fink's SIMBAD cross-match calls all
five `Unknown`. Two more are classed `YSO`. **Gaia's variability classifier knows
things SIMBAD does not, and the filter currently only prints them.**

Promoting `I/358/vclassre` from a printed column to a Layer-3 veto input — vetoing
`AGN`, `QSO`, `BLAP`, `LPV`, `RR`, `CEP`, `ECL`, `SOLAR_LIKE`, `YSO`, and keeping
`CV` as a target-with-flag — is the **single highest-value remaining change** to
this filter. It is not done because the cross-match is currently run at the
candidate stage, after the filter, and moving it earlier means an X-Match call per
pool rather than per candidate. Cost and benefit are both unmeasured.

### 4.6 The Mira trap

Unfiltered and broad-band CCDs over-respond to red objects, so long-period
variables masquerade as novae. In the vetting sample 17 of 39 objects with a Gaia
colour had `BP−RP > 2.0` and 13 of 34 with 2MASS had `J−K > 1.0`. **The filter
still has no colour cut** — the colours are carried as columns and it is your job
to look at them. `J−K > 1.0` **and** `BP−RP > 2.0` **and** variation on ≥ 100-day
timescales is a Mira until proven otherwise.

### 4.7 Latency

The 2-detection / 30-minute gate means the filter cannot fire on the discovery
exposure. Median lead over DCAP is 3.1 days, and DCAP themselves file a median
3.12 days after the discovery exposure. **Against a same-night reporter like LAST
(median 0.19 d) this filter loses every time.** The niche is latitude, not speed.

Measured live on 2026-08-24 against the mainstream rather than against DCAP: of
14 objects from the same three nights that somebody else reported to TNS, our
passing epoch preceded their report in **5**, median lead **−0.55 d**, best
**+1.42 d**. ZTF's own pipeline filed 11 of the 14. Thirteen of the fourteen were
at |b| > 12°, i.e. outside this front's niche entirely.

### 4.8 Enumeration is still the bottleneck, not the filter

E2 covers a night's alerts class by class, but the pool it produces is only as
complete as Fink's class assignment. An object Fink files under a hard-vetoed
SIMBAD class is never enumerated, whatever it actually is. That is a deliberate
consequence of deriving the class list from the veto list, and it is the price of
not having a free parameter there.

### 4.9 Traps that have already cost time

**A failed request must never be cached as an empty result.** This rule was
documented after the first M2 run, but a 2026-09-02 audit found that both writers
still violated it:

- `m1_fetch_fink.py` wrote `[]` after exhausting its retries; and
- `m2_pool.py` fell back to individual requests, then wrote `[]` for every
  object that did not produce a successful response anyway.

That made a transport failure indistinguishable from a real HTTP-200 response
with no alerts. The cache contained 5,133 object histories at audit time, of
which 1,104 were legacy `[]` files with no success provenance. They are
**suspect, not proved failures**: the old representation cannot tell the two
cases apart.

The shared cache client now fails closed. A payload is written only after HTTP
200 and structural validation. Every nonempty alert record must carry the
object ID, finite JD, candid, magnitude, filter, coordinates, subtraction sign,
and at least one numeric real-bogus score. A batch response authenticates only objects it
actually contains; every omitted object is confirmed by a separate
single-object HTTP-200 request before an empty history is accepted. Outages,
non-200 responses, malformed JSON, and wrong-object responses abort the science
pass instead of changing a count. The compatible payload remains
`data/fink/<oid>.json`; `data/fink/_meta/<oid>.json` records status, UTC fetch
time, endpoint, HTTP status, request mode, row count, and a SHA-256 digest.

**Freshness has two independent gates.** Every reusable entry must be no more
than 24 hours old, and its fetch timestamp must be at or later than the caller's
explicit `required_coverage_jd`. The second rule matters even inside the TTL: a
23-hour-old response cannot cover a window ending 12 hours ago. Proved-empty
histories and empty cone searches use the same 24-hour limit, so neither can
suppress an object forever. A timestamp in the future is invalid, not age zero.
Legacy nonempty payloads remain readable for descriptive work, but their file
mtime is not query provenance and can never satisfy `required_coverage_jd`; a
completeness-dependent run refreshes them once. Evidence-sheet builds force a
live refresh. Cone-resolution positives and empties also require a fresh proof
binding the exact coordinate/radius query to the resolved OID (or null), HTTP
status, endpoint, and value digest. An interrupted payload-before-proof update
therefore refetches rather than reusing a new value with old metadata.

**Every alert-history calculation has an inclusive time ceiling.** M1 and M2 pool commands
set `history_jd_ceiling = mjd_end + 2400000.5`; M2 also preserves its 60-day
episode floor. Both filters receive that ceiling. Candidate histories, episode
counts, amplitudes, light curves, and evidence sheets are sliced to the same
ceiling, even when the underlying cache was fetched later. Pool, candidate, and
evidence CSV/JSON outputs record the ceiling, cache policy, exact per-object
payload SHA/fetch/status mapping, and sidecar timestamp range. Old intermediate
CSVs without exactly one ceiling are rejected with an instruction to rebuild
rather than silently mixed with fresh cache data. This claim applies to Fink
alert-derived quantities; the separate TNS limitation is stated above.

Enumeration caches are also proved inputs. M1/E1 ALeRCE rows and M2/E2 Fink rows
are bound to exact `mjd_start`/`mjd_end` sidecars. ALeRCE pagination continues to
a short page, requires the retrieved unique-OID count to equal the API's valid
first-page total, and aborts on a repeated page. Fink E2 validates every alert's
core fields and requested JD bounds; non-200, malformed, and cap-bound slices
abort without writing an empty/incomplete pool. Its class-catalogue response
must be a nonempty, multi-group taxonomy of nonempty class lists satisfying the
versioned baseline-v1 sentinels for SIMBAD target, SIMBAD host-veto, Fink-science,
and solar-system families, plus the observed baseline floor of 250 distinct
non-TNS classes. A real taxonomy rename requires an explicit reviewed
contract-version bump; a plausible one-class HTTP-200 response cannot prove E2
complete. The exact enumerated class list and digest are saved with the arm.
Progress rows use a distinct
`*.checkpoint.csv`; only the atomic final filtered CSV receives a digest/row/
window/ceiling proof, and candidate builders authenticate it against the pool
manifest before reading it. CDS X-Match caches bind the exact ordered
`(oid, ra, dec)` list and require every declared catalogue column plus a finite
separation inside that catalogue's requested radius. Cutout triplets are cached
only after all three images pass shape/content validation; an outage can no
longer become a permanent 1×1 zero image.

Final M1/M2 candidate CSVs are also atomic proved outputs. Their sidecars bind
the payload digest and row count to the exact pool summary, Fink-history input
manifest, frozen/current TNS snapshots, and (for M2) X-Match input. The JSON
summary embeds that identical proof and is replaced atomically last. Evidence
and precision readers require the summary, sidecar, and CSV to agree, so neither
a partial new CSV with an old proof nor a complete same-tag CSV with an old
summary is accepted. Old candidate artifacts without this proof are historical
only and must be rebuilt before reuse.

Before reproducing M1/M2 from an old working cache, run this **offline** migration:

```powershell
python scripts/m1_fetch_fink.py --quarantine-legacy-empty
```

It moves every unproved legacy empty file under `data/fink/_quarantine/`; merely
having a sidecar is not proof—the sidecar must validate the object ID, HTTP 200,
status, timestamp, row count, and payload digest. The migration does not delete
anything or make network calls. The next normal pool/control run
refetches those objects. Existing nonempty arrays remain compatible and acquire
a sidecar when first read. Until the quarantined objects have been refreshed and
the controls/pool rerun, treat the committed M1/M2 completeness-dependent counts
as historical results awaiting a freshness- and input-proved reproduction. The
old candidate-veto state cannot be reconstructed exactly; generate a new window
with a post-window TNS snapshot instead. No filter threshold changed in this
repair.

**ALeRCE's `has_next` is unreliable with `count=false`.** A pagination loop that
trusts it stops after one page and truncates the arm at exactly `page_size` - a
round number in the output is the tell. Page until a page comes back short instead.

**ALeRCE also repeats rows across page boundaries** - dedupe on `oid` or every
downstream count is inflated.

### 4.10 Live proved-run blocker on 2026-09-02

The newest closed-year run was attempted for alert MJD `[61282, 61285]` and TNS
discovery interval `[2025-09-01, 2026-09-01)`. The TNS side completed: the live
snapshot has **28,321 rows**, including 37 rows in the current partial month, and
the closed corpus has **28,284 rows**. Its 77 exact raw CSV responses, including
the explicit terminal pages, are retained and digest-proved in the private
gitignored run bundle. ALeRCE E1 independently completed at **3,041 objects**.

The full campaign did **not** complete. Fink exposed 295 required non-vetoed
classes, but `/api/v1/latests` repeatedly timed out for the required `Em*` class,
including after 14 bounded time bisections down to
`[61282.0, 61282.00018310547]` (about 15.8 seconds). The run authenticated and
retained 87 successful Fink slice responses plus the taxonomy response, then
failed closed. A separate diagnostic requesting only `n=1` over that same
15.8-second slice also timed out, so response size is not the remaining lever.
There is therefore **no defensible E2 total, union-pool count, or
candidate count** for this window; the missing class must not be dropped or
represented as zero.

This is a source-service boundary, not a missing local workaround. The official
[Fink API reference](https://api.ztf.fink-portal.org/) requires `class` for
`/latests`. An audit of the official
[API source at commit `1fbbd0e`](https://github.com/astrolabsoftware/fink-object-api/tree/1fbbd0e37ceb0f8eca647d363e7dbc974e972705)
confirmed that it range-scans a class-keyed table and exposes no all-class
time-range route; `/conesearch` explicitly limits dates by first detection and
cannot recover known sources erupting in the window. Retry the identical
protocol when Fink serves that class, or amend the protocol to a separately
proved complete alert source. A counts-only probe of ALeRCE's all-class
`lastmjd=[t0, now]` filter also returned HTTP 504, so that potential overcomplete
fallback is neither validated nor shipped. It is the first alternative to test
under a new protocol if the service becomes responsive. Do not silently change
the enumerator.

**Windows:**

- `write_text` must be opened with `newline` set to LF, or committed scripts
  silently become CRLF.
- stdout defaults to cp1252 and dies on a degree sign; `tnscommon.py` reconfigures
  it to UTF-8 on import.

---

## 5. Before anything goes anywhere: the per-object check

Run this on any object you are considering. Every step is mandatory.

1. **Difference stamp** — §4.1. If it is not a small round centred positive dot,
   stop.
2. **Per-band light curve** — is there a quiescent floor it returned to, or is it
   detected continuously? Continuous detection for years is a variable star.
3. **`gaia_DR3Name`** — if a Gaia star sits there, ask what fraction of its light
   the excess is. `magnr − magpsf < 1` means a few percent, which is not an event.
4. **`atlasvs_*`, `vsx_*`, `gaiavar_*`** — already catalogued as variable?
5. **`JK`, `gaia_BP-RP`** — Mira trap?
6. **Second broker.** Look the object up independently at
   `https://alerce.online/object/<oid>` and `https://api.antares.noirlab.edu`.
   Two brokers agreeing on the light curve is cheap insurance against one
   broker's ingest bug.
7. **MPChecker.** Fink's `d:roid` and `i:ssdistnr` cover *known* minor planets.
   For anything in the plane, check the position at
   `https://www.minorplanetcenter.net/cgi-bin/checkmp.cgi` by hand.
8. **ATLAS forced photometry** — §6.3. You need it for the report anyway, and it
   is also the best independent confirmation available: a second telescope
   system, a different filter set, and the full survey history at that position.

---

## 6. Submitting: exactly what a human does, end to end

**Three accounts are needed. No agent creates any of them.** Nothing below has
been walked — it is research (`M1-06`), verified against the current documentation
on 2026-08-24.

### 6.1 Account 1 — TNS user account · **gates everything else**

- Register at **`https://www.wis-tns.org/user/register`**.
- TNS states registration *"is open to all professional astronomers as well as to
  amateurs."* Affiliation may be "None"; no group is required (group ID 0 = None).
- Accounts are **human-vetted**, so expect latency. Say plainly that you are an
  amateur data-miner working the public ZTF alert stream, and describe the
  pipeline.
- Nothing downstream can be done until this exists.

### 6.2 Account 2 — TNS bot and API key · **define it on PRODUCTION**

- **`https://www.wis-tns.org/bots`** → "+Add bot".
- The bot carries the `api_key` that authenticates every submission, and a
  `tns_marker` string that goes in the `User-Agent` header.
- **Define the bot on the production site even while you are only experimenting.**
  The sandbox is overwritten from production **every Sunday 04 UT**, and a
  sandbox-only bot definition vanishes with it.
- A new key can be minted later by editing the bot and ticking "Create new API Key".

### 6.3 Account 3 — ATLAS forced photometry · **the blocking dependency**

**A TNS AT report is rejected outright without a pre-discovery non-detection**
(blocking error 6: *"Last non-detection or archival info must be filled"*), and it
must precede the discovery datetime (error 1). Brokers cannot give you photometry
at an arbitrary position *including non-detections*. ATLAS can.

- Register at **`https://fallingstar-data.com/forcedphot/`** — free, amateurs
  accepted.
- Get a token once:

  ```python
  BASEURL = "https://fallingstar-data.com/forcedphot"
  r = requests.post(f"{BASEURL}/api-token-auth/",
                    data={"username": USER, "password": PW})
  token = r.json()["token"]
  headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
  ```

- Queue a position (HTTP **201** = queued; **429** = throttled, the message says
  how long to wait):

  ```python
  r = s.post(f"{BASEURL}/queue/", headers=headers,
             data={"ra": RA_DEG, "dec": DEC_DEG, "mjd_min": DISCOVERY_MJD - 200})
  task_url = r.json()["url"]
  ```

- Poll `task_url` until `finishtimestamp` is set, then fetch `result_url` and
  parse:

  ```python
  df = pd.read_csv(io.StringIO(text.replace("###", "")), sep=r"\s+")
  ```

  Optional: pass `callback_url` (https, public, one attempt, not retried) instead
  of polling; `GET {BASEURL}/queuepositions.json` gives queue positions; an
  OpenAPI schema is at `/api/schema/` with docs at `/api/docs/`.
- Limits: **60 submissions/min, 500 queued tasks, 100 positions per task.**
- ATLAS filters are **cyan (`c`) and orange (`o`)**, AB magnitudes, depth
  `o ≈ 19.5`, whole sky every 1–2 days.
- **What you need out of it:** the last epoch *before* the discovery where the
  forced flux is consistent with zero, and its **limiting magnitude**. That epoch
  and that limit are the `non_detection` block of the report.

### 6.4 Learn the schema on the sandbox first

- **`https://sandbox.wis-tns.org`** · test form `https://sandbox.wis-tns.org/api/test`.
- A replica of production, reset every **Sunday 04 UT**. Anything submitted there
  is gone; so is any sandbox-only bot.
- The manual is blunt: *"Please do not commence sending real Bulk reports to the
  production site before verifying on the sandbox environment that all your codes
  and scripts work flawlessly."*
- It still requires real credentials, which is why no agent has touched it.

### 6.5 The report

Two routes, same schema: the **interactive web form** (right for your first one or
two) or the **bulk API**, `POST https://www.wis-tns.org/api/set/bulk-report`.

**Mandatory POST parameters:** `api_key`, `User-Agent` (the bot's `tns_marker`),
`data` (the JSON below). **Limits:** ≤ 10 entries per repeated item (e.g.
photometry points), ≤ 100 report entries per submission.

```json
{"at_report": {"0": {
  "ra":  {"value": "18:12:49.55", "error": "0.5", "units": "arcsec"},
  "dec": {"value": "-04:47:08.8", "error": "0.5", "units": "arcsec"},
  "reporting_groupid": "0",
  "data_source_groupid": "48",
  "reporter": "M. Potts",
  "discovery_datetime": "2026-08-23.512",
  "at_type": "1",
  "host_name": "", "host_redshift": "",
  "internal_name": "ZTF26abcdefg",
  "internal_name_format": {"prefix": "", "year_format": "YY", "postfix": ""},
  "remarks": "Discovered in public ZTF alerts; no counterpart in VSX/GCVS/SIMBAD/TNS.",
  "non_detection": {"obsdate": "2026-08-19.402", "limiting_flux": "19.4",
                    "flux_unitid": "1", "filterid": "", "instrumentid": "",
                    "exptime": "30", "observer": "", "comments": "ATLAS forced photometry",
                    "archiveid": "", "archival_remarks": ""},
  "photometry": {"0": {"obsdate": "2026-08-23.512", "flux": "17.84",
                       "flux_error": "0.08", "limiting_flux": "20.4",
                       "flux_unitid": "1", "filterid": "110",
                       "instrumentid": "196", "exptime": "30",
                       "observer": "", "comments": ""}},
  "internal_ids": {}
}}}
```

**Things that will bite:**

- **Keys were renamed for TNS 2.0.** `reporting_group_id` → **`reporting_groupid`**,
  `discovery_data_source_id` → **`data_source_groupid`**, `flux_units` →
  `flux_unitid`, `filter_value` → `filterid`, `instrument_value` →
  `instrumentid`. Old names are rejected.
- **Every preset field takes an id, not a label.** Pull the current id tables from
  `https://www.wis-tns.org/api/get/values` (or the "Get AUX tables values id's"
  button on the bulk page) and **do not hard-code the ids in the example above** —
  they drift.
- **Blocking errors**: **2** — the discovery photometry point is mandatory;
  **6** — the non-detection (or archival info) is mandatory; **1** — the
  non-detection must precede the discovery datetime; **5** — duplicate guard on
  (sender, RA/Dec, discovery date, internal_name).
- **File `at_type` honestly.** Do not report as "Nova" what has not been
  classified. Let the spectrum decide the type.

### 6.6 The reply, and after

- `POST https://www.wis-tns.org/api/get/bulk-report-reply` with `api_key`,
  `User-Agent` and the `report_id` the submission returned. Processing is
  immediate but asynchronous; poll every few seconds. The reply says whether a new
  object was created or the coordinates matched an existing one, and gives the
  designated name.
- The object becomes `AT 2026xyz` and the report gets an ADS-indexed bibcode of
  the form `2026TNSTR….1P`.
- **You cannot classify it.** A classification report requires a spectrum, no
  exceptions — which is why 92.1% of TNS objects in the last 12 months are
  unclassified (`M1-02`). A confirming spectroscopist can be found through
  **ARAS**: `https://aras-database.github.io/database/novae.html`.
- **TNS AstroNotes** (`https://www.wis-tns.org/astronotes`) are open to any
  registered user and are ADS-indexed — a legitimate citable output that does not
  require owning a discovery.
- Registering a **reporting group** (DCAP is the precedent, group 195) makes
  discoveries carry a project name.

---

## 7. M31 and M81 — what they need when the field reopens

Channel B returned **zero** candidates in August, and the reason is seasonal, not
broken. ALeRCE reports **0 new ZTF objects in the last 60 days** within 1.5° of
M31 or 0.5° of M81. Over the last 365 days the M31 field produced 173, distributed
like this (`M1-05`):

| 2025-08 | 09 | 10 | 11 | 12 | 2026-01 | 02–03 | 04 | 05 | 06 | 07 | 08 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 42 | 29 | 8 | 19 | 11 | 0 | 8 | 37 | 9 | **0** | **0** |

**M31 (RA 10.7°, Dec +41.3°) is a September-to-January object; M81 (RA 148.9°,
Dec +69.1°) is February-to-May.** Late August is the worst week of the year for
both. **M31 reopens in about a fortnight.**

**What the channel needs before it is pointed at a real M31 season — three things,
none of them done:**

1. **A different enumerator.** Both arms are all-sky. For a 1.5° cone, ALeRCE's
   `ra/dec/radius` cone query is far cheaper and complete, and it should be a
   third arm rather than a filter applied afterwards.
2. **A host-galaxy exemption from Layer 4.** The nuclear/TDE veto rejects anything
   with `sgscore1 ≤ 0.30` within 1.0″ of a PS1 source. Inside M31's disc that
   describes a large fraction of the field, and an M31 nova sits on exactly that
   kind of background. **The channel is currently self-defeating and this has
   never been tested, because there has been nothing to test it on.** Fix it
   before the season, not during it.
3. **Its own positive control.** M31 novae are reported to TNS regularly and are
   spectroscopically confirmed at a far higher rate than the galactic ones.
   Harvest the last three M31 seasons from the TNS CSV, rewind them exactly as
   `M1-04`/`M2-03` do, and measure recall on that class specifically before
   trusting a single candidate the channel produces.

Do not report an M31 candidate until step 3 has a number attached to it.

---

## 8. What this front cannot do

- **It cannot classify.** A classification report needs a spectrum. You can be
  the discoverer; you cannot be the classifier.
- **It cannot beat a same-night reporter.** §4.5.
- **It cannot tell a genuine faint transient from half the artifact classes
  without an image.** §4.1.
- **It cannot be run unattended.** Measured precision is a few percent. Every
  candidate is a suggestion of where to look, and nothing more.
- **It has a deadline.** ZTF primary operations end **December 2026**. After that
  the same architecture — two-arm enumeration, per-band amplitude, sign-history
  veto, image check — transfers to Rubin and LS4 alert streams, but every number
  in §2 will need re-measuring against a different camera.
