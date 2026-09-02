# M5 — the vetting finished, a reproducible nebular stage built, and the high-latitude catalogue delivered

*2026-08-23 · follows [M4](M4-sky-parent-gvar-jwst.md), executing M4 §7's own recommendations.
Every externally-sourced number carries its source; anything unsourced is marked UNSOURCED.
**Nothing in this milestone has been submitted, posted, or sent anywhere.** The candidate-I dossier
and the Ren+24 note remain Matthew-gated and are unchanged by this document.*

---

## 0. Pre-registrations

*Written and timestamped **before** the runs they govern, per repo law. Nothing in §1–§6 was chosen
after seeing a result. The one place where this milestone deliberately re-opens an earlier choice —
the V5 centroid axis — is a **retirement**, not a retune, and it is argued from M4 §5 rather than
from any M5 measurement.*

### PR-1 — finishing the vetting: nothing is re-chosen, only re-run

M4 §6.3 left the vetting of the 1,545 full-sky pre-visual survivors running. Under M4 §7.1 the
gates and their thresholds are **M3 PR-3's, fixed before any survivor list existed, and must not be
re-chosen now that the list is bigger**. This milestone therefore changes **only the I/O of the
vetting driver**, never its logic:

- the V1/V2 cache is made **incremental** (written per chunk, resumable) — M4 §7.1's practical
  warning;
- a faster catalogue-crossmatch backend may be substituted **only if it passes an acceptance test
  first**: on the identical position list it must return the identical AllWISE and All-Sky rows as
  the existing TAP path, matched designation-for-designation, with the disagreements counted and
  reported whatever they are;
- `verdict()` is not edited. Any change to the verdict counts must be attributable to a row the old
  path failed to fetch, not to a changed rule.

**Reported caveat, fixed now:** V5 is out (PR-5). STILL-CLEAN requires a valid centroid, so
**no object can reach STILL-CLEAN**, and the surviving set must be described as *objects with no
detectable contamination evidence given a method with a known blind spot* — never as "clean".

### PR-2 — the nebular stage: what it is, and how its threshold is chosen

M4 §4 localised the entire 4.2× pre-visual overproduction to the paper's unpublished nebular CNN:
every reproducible stage reproduces (parent 1.03×, RMSE 0.84×, extra cuts 0.84×) and the residual
runs from **20.9× at |b| < 5°** to **1.05× [0.94–1.17] at |b| > 50°**. The stage built here is a
**replacement**, not a reimplementation — the CNN's weights and training set are unpublished, so
nothing about this is a reproduction of theirs.

**Three components, declared in advance, each with its threshold rule fixed before any count is
looked at.**

- **N1 — known-nebula catalogue veto. No free parameter at all.** An object is flagged if it lies
  within the **published angular extent of a catalogued nebular object**, taken from public
  catalogues downloaded anonymously from VizieR. The radius is the *catalogue's own*, never one
  chosen here. Where a catalogue publishes an ellipse, the semi-major axis is used; where a
  catalogue publishes no extent at all, a fixed **60″** is used and those matches are counted
  separately so the choice is auditable. The catalogue list is fixed here, before any cross-match:
  WISE Galactic H II regions (Anderson+ 2014), Sharpless, RCW, Green's SNRs, SECGPN + MASH
  planetary nebulae, Lynds dark and bright nebulae, Barnard dark objects, van den Bergh and
  Magakian reflection nebulae, Cederblad bright diffuse nebulae, and the Planck Galactic Cold
  Clumps. Any catalogue that fails to download is reported as absent, not silently dropped.

- **N2 — the coadd local-background statistic, with a percentile rule.** AllWISE's own pipeline
  measures, per source and per band, the **median background in the profile-fit annulus**
  (`w3sky`, `w4sky`) and the **sky confusion derived from the uncertainty images** (`w3conf`,
  `w4conf`) — i.e. an extended-emission statistic measured *from the coadds*, published as
  catalogue columns (AllWISE Explanatory Supplement §II.2). **Threshold rule, fixed now and not
  negotiable afterwards:**

  > The calibration population is the **parent sample at |b| > 50°** — the latitude band where M4
  > §4.3 measured this screen to reproduce the paper's yield at 1.05×, i.e. sky the screen is
  > already known to handle correctly. Within bins of **|ecliptic latitude|** (10° wide, to absorb
  > the zodiacal gradient that dominates W3/W4 background away from the plane), each object is
  > assigned the **percentile rank** of its `w3sky` and of its `w4sky` in that calibration
  > distribution. Its nebular score is the **larger** of the two ranks. **An object is flagged if
  > its score exceeds 0.99** — a 1% per-band false-positive rate on nebulosity-free sky, chosen
  > because it is a round 1%, before any survivor count was computed. The **combined** false-positive
  > rate of the max-of-two rule is *measured* on the calibration set and reported, not assumed.

  Scores at 0.95 and 0.999 are computed **as a sensitivity band and labelled as such**; the
  delivered funnel is the 0.99 one. If the delivered number is later quoted at a different
  threshold, that is a protocol violation and this paragraph is the record of it.

- **N3 — the local mid-IR source density, replacing a global chance-alignment prior.** V4 currently
  uses a single all-sky faint-red-galaxy density (Suazo et al. 2024's own 15,000 sr⁻¹). The local
  density of AllWISE sources bright enough in W4 to carry the excess is measured directly around
  each object from the same coadd catalogue, and reported per object. **N3 is declared a
  *reported statistic*, not a cut** — it enters no verdict — because no published density
  threshold exists to anchor one, and inventing one here would be exactly the un-pre-registered
  choice this section exists to prevent.

**Validation, all three parts fixed in advance:**

  a. **7/7.** The stage must not flag any of the paper's seven published candidates. **This is a
     weak test and is declared weak here**: M4 §4.3 established all seven lie at |b| > 30°, where
     nebulosity is scarce, so passing it is necessary and nowhere near sufficient. It is run
     because failing it would be disqualifying.
  b. **The plane excess.** The stage must reject a substantial and *latitude-graded* share of the
     plane survivors. The signed prediction, from M4 §4.3: the rejected fraction must **fall
     monotonically with |b|**, and the residual overproduction factor must move **towards 1.0** in
     every band. A stage that removes a latitude-flat fraction is removing something else and will
     be reported as such.
  c. **No count-peeking.** The threshold comes from the rule above. The funnel is computed once
     with it.

**Stated in advance, because it will be true:** this stage will *not* close the 20.9× at |b| < 5°.
A catalogue veto can only remove what somebody has already catalogued, and a background percentile
tuned to a 1% false-positive rate is by construction a conservative cut. The deliverable is a
**measured, reproducible fraction of the gap**, plus the residual, not a claim to have replaced the
CNN. If the residual after the stage is still large, that is the result.

### PR-3 — the high-latitude catalogue: what goes in, and what is claimed

The positive deliverable of the whole project (README's own framing). Fixed before it is built:

- **Footprint**: |b| > 30°, with the |b| > 50° subsample flagged as the **calibrated core** —
  M4 §4.3 measured 1.05× [0.94–1.17] there and 1.36× [1.24–1.49] at 30–50°, so the two are not
  equally defensible and the catalogue must say so per row, not in a footnote.
- **Contents**: every pre-visual survivor in the footprint, **including the ones this project's own
  gates convict**, each carrying its verdict, the evidence behind it, and the new nebular flags.
  A catalogue that silently drops its own rejects cannot be checked.
- **Claims**: completeness and contamination are stated as *measured numbers with their
  provenance*, and the technosignature framing is **not** the headline. The stated scientific uses
  are the ones that do not depend on it — debris disks, white-dwarf pollution, extreme M-dwarf
  excesses.
- **No object in it is a candidate for anything.** Nothing in this catalogue is Matthew-gated,
  because nothing in it reaches STILL-CLEAN (PR-1), and nothing is reported anywhere.

### PR-4 — candidate E, opening 2026-09-09: the procedure and what each outcome means

E's GO 7199 products become public **2026-09-09**, 17 days after this milestone. Declared now, so
that nothing about the analysis is chosen after seeing E's data:

- the procedure is **parameterised from the D chain and validated by re-running D through it**
  before E exists. If the parameterised path does not reproduce M4 §5's D numbers, it is not ready
  and says so;
- the deliverable for E is the same pair M4 PR-5 fixed for D: **(separation, contrast)**, because
  that is what converts into a centroid pull and what turns M4 §5.3's single calibration point into
  a two-point relation;
- **the outcome map is written before the data open** (§5.3), covering all four cases: contaminant
  found and above the archival floor; contaminant found and below it; no contaminant; and data
  unusable. Each is stated with its consequence for the tally *and* for the archival-floor
  calibration, so no result can be re-interpreted after the fact.

### PR-5 — V5 is retired, not retuned

M3 §3.2 disabled the centroid axis and prescribed two fixes (3″ search radius, neighbour-aware
validity check). **M4 §5.3 supersedes that prescription with a measurement**: on candidate D — the
one object where the truth is known from JWST — the archival centroid is wrong in **direction**
(PA 82.9° against the real 33°, pointing where MIRI shows nothing) as well as in **magnitude**
(W4 2.55 ± 0.50″ against a hard geometric ceiling of 1.23″), and Ren et al. 2026's independent
1.8″ overshoots the same ceiling. A smaller search radius cannot repair a measurement whose
direction carries no information.

**V5 is retired for objects near the floor.** The retirement is recorded append-only in §6 with
M4 §5's `sep_thr(ρ) = F · (1 + 1/ρ)` as the statement of what centroid vetting can and cannot do.
It is **not** re-enabled, re-tuned, or re-scored anywhere in this milestone, and the consequence —
that STILL-CLEAN is unreachable — is carried in every verdict table rather than worked around.

---

*(Everything below is written after the runs. Numbers are emitted by the scripts named, never
hand-copied.)*

---

## 0b. What M5 established

1. **The vetting of the 1,545 full-sky survivors is finished**: **719
   CONTAMINATION-CONSISTENT, 584 INDETERMINATE, 242 SUB-THRESHOLD, 0
   STILL-CLEAN** (§2). **The zero is by construction, not by measurement** —
   V5 is retired and STILL-CLEAN requires a valid centroid — so the surviving
   set is stated as what it is: *objects with no detectable contamination
   evidence given a method with a known blind spot*. **No Matthew-gated
   candidate.**
2. **A route finding that changes the economics of every future vetting run:
   IRSA's Gator multi-position upload does the same cross-match at
   0.0027 s/position against TAP's 3.5 s/position — a ~1,300× speedup, and it
   is anonymous.** The 1,545-position V1+V2 pass that cost M4 ~3 hours takes
   **8.1 seconds**. It was accepted only after PR-1's test: **1,545/1,545
   designations identical on both releases, 0 disagreements, photometry equal
   to float32 rounding** (§1.1).
3. **M4 §7.1's checkpointing hazard is fixed anyway** — the V1/V2 cache now
   writes per chunk with a `_chunk` index and resumes exactly (§1.3).
4. **A reproducible nebular stage exists, and it closes 81.6% of the excess
   the paper's CNN was carrying** (§3). Pre-visual survivors **1,545 → 585**
   against the paper's 368: the all-sky overproduction falls from **4.20× to
   1.59×** (1.72× on the conservative area-corrected reading).
5. **It is built from three components, each with its threshold fixed by a
   stated rule before any count was looked at** (§3.1–§3.3): **N1**, a veto on
   the *published angular extent* of 29,462 catalogued nebulae from 14 VizieR
   catalogues — **no free parameter at all**; **N2**, the percentile rank of
   AllWISE's own coadd background (`w3sky`/`w4sky`) against the |b| > 50°
   parent, binned by ecliptic latitude, cut at 0.99; **N3**, the locally
   measured mid-IR source density, **reported and not cut**, exactly as
   pre-registered.
6. **The validation passes on all three of PR-2's criteria** (§3.5).
   **(a) 7/7 of the paper's published candidates are preserved** — and 10/10
   of the labelled objects A–J — with **N1 flagging none and N2 flagging
   none**. **(b) The rejected fraction falls monotonically with |b|: 87.5%,
   61.3%, 59.7%, 37.0%, 3.0%, 0.0%**, and the overproduction moves towards 1.0
   in **every** band. **(c)** The 0.95/0.99/0.999 sensitivity band gives
   557/585/609 survivors — the result does not hinge on the threshold.
7. **The residual overproduction by latitude**: **20.89× → 2.62×** at
   |b| < 5°, 6.82× → 2.64×, 5.41× → 2.18×, 1.72× → 1.08×, 1.36× → 1.32×, and
   **1.05× → 1.05× at |b| > 50°, untouched** — the stage does nothing where
   M4 proved nothing needed doing, which is the strongest single check on it
   (§3.4).
8. **N2 is measuring the Galactic plane, not the zodiacal light, and that is
   shown rather than asserted**: within *every* ecliptic-latitude bin the
   |b| < 5° background sits **2.5–21% above** the clean-sky median of the same
   bin, while |b| > 50° sits **on** it. Among RMSE survivors the median N2
   score runs **1.000 at |b| < 5° to 0.535 at |b| > 50°** (§3.3).
9. **N1 is not merely a sky mask, and the enrichment statistic proves it**: it
   flags 56.4% of the 10–20° survivors while masking 9.5% of that sky —
   **enrichment 5.93** — and 62.4% at |b| < 5° while masking 36.6%
   (enrichment 1.70). The whole veto masks **7.77% of the sky, and 0.03% of
   the |b| > 50° core** (§3.2).
10. **Stated in PR-2 in advance and true: the stage does not close the plane.**
    At |b| < 5° the residual is still 2.62× (4.13× area-corrected). Our stage
    rejects **31.2%** at the RMSE gate where the paper's CNN rejects **49.0%**.
    **What is delivered is a measured, reproducible fraction of the gap, not a
    replacement for the CNN** (§3.6).
11. **The high-latitude catalogue is delivered**: **223 objects at |b| > 30°,
    62 columns, 153 KB**, with the **90-object |b| > 50° calibrated core**
    flagged per row, per-object vetting flags, and completeness/contamination
    statements that are measured numbers rather than adjectives (§4).
12. **V4's chance-alignment prior is measured locally for the first time, and
    a single all-sky constant cannot carry it**: the density of AllWISE
    sources in Suazo et al.'s own colour band at comparable W4 brightness runs
    **1,830 deg⁻² at |b| < 5° to 255 deg⁻² at |b| > 50°** — a 7× gradient —
    against V4's global **4.57 deg⁻²**. Expected interlopers within Suazo's own
    3.25″ aperture: **6.7 among the 1,545, against V4's 0.018 — a factor 372**
    (§3.3). Even as an upper bound, 6.7 is far short of 585: **the interlopers
    that matter are the ones AllWISE never resolves as separate sources**,
    which is exactly candidate D's 1.23″ companion and exactly what the retired
    centroid axis was supposed to catch.
13. **The candidate-E procedure is ready and dated.** The D chain is
    parameterised, and re-running D through it reproduces M4 §5 on **every one of its
    seven checks** — separation 1.233″ vs 1.230″, PA 33.00° vs 33.0°, ρ = 0.236 /
    7.242 / 83.135, ρ(W3) 21.81 vs 21.8, predicted W3 pull 1.179″ vs 1.180″
    (§5). **E's MAST status re-checked today: 39 observations, 0 public, all
    EXCLUSIVE_ACCESS, release MJD 61292.31 = 2026-09-09**, and E's imaging has
    the **same three-filter structure as D's** (F560W/F1000W/F1500W,
    1146.716 s each, on `jw07199-o006_t008`, target `Object_E_background`).
    The outcome map is written **before** the data open.
14. **V5 is formally retired** (§6), append-only, with M4 §5 as the reason and
    `sep_thr(ρ) = F(1 + 1/ρ)` as the statement of what centroid vetting can and
    cannot do.

---

## 1. Finishing the vetting — and a route finding that makes it 1,300× cheaper

*`scripts/m3_vet_survivors.py` (I/O only, `verdict()` untouched),
`scripts/m5_vet_accept.py`; artifacts `out/m5_vet_accept_m4_g0.1.json`,
`out/m3_survivor_table_m4_g0.1.csv`, `out/m3_verdict_counts_m4_g0.1.json`.*

**First, a correction to M4's own status line.** M4 §6.3 reported the vetting as
"RUNNING, not finished" and made the full-sky verdict table an M5 deliverable.
The run in fact **completed after M4's document was written** — the artifacts
are timestamped 19:37 against the document's 19:06 — and all 1,545 rows carry an
AllWISE match, 1,532 of them an All-Sky match. **The verdict table M4 promised
already existed when M4 said it did not.** The numbers in §2 are that run's,
re-verified here.

### 1.1 IRSA's Gator upload does in 4 seconds what TAP does in 3 hours

M3 §3's `tap_chunks` comment records, correctly, that *"IRSA's TAP accepts
exactly ONE `CONTAINS()` per query"* and that anonymous TAP has no upload — so
the cross-match is issued as OR'd coordinate boxes, 40 per query, at a measured
**~3.5 s per position**. At 1,545 positions × 2 releases that is the ~3 hours
M4 §7.1 warned about.

**Gator is a different service, and its multi-position upload *is* anonymous.**
Measured here on the same 1,545 positions:

| route | 1,545 positions, one release | per position |
|---|---|---|
| TAP, OR'd boxes, 40/query (M3/M4) | ~90 min | **3.5 s** |
| **Gator `spatial=Upload`** | **4.1 s** | **0.0027 s** |

**~1,300×.** The V1 + V2 pass costs **8.1 seconds**. The 9,486-position
background pull that §3 needs — **9 hours** by TAP — takes **23 seconds**, and
the 68,511-star calibration sample takes **84 seconds**. *This is what made §3
affordable at all: a nebular stage measured per object was not a realistic
proposal at 3.5 s/position.*

### 1.2 PR-1's acceptance test, before the fast route was allowed to count

PR-1 permits a faster backend **only if it returns the same rows**. Ground truth
is M4's completed TAP run. On the identical 1,545-position list:

| | V1 AllWISE | V2 WISE All-Sky |
|---|---|---|
| designations identical | **1,545 / 1,545** | **1,545 / 1,545** |
| TAP matched, Gator did not | **0** | **0** |
| Gator matched, TAP did not | **0** | **0** |
| disagreeing designations | **0** | **0** |
| both no match within 3″ | 0 | 13 *(the same 13 on both routes)* |
| max abs diff `w3mpro`, `w4mpro` | **0.0** | 4.7 × 10⁻⁷ |
| max abs diff `w3snr`, `w4snr`, `w?nm`, `w?flg` | **0.0** | ≤ 1.5 × 10⁻⁶ |
| `ph_qual` identical | 1,545 / 1,545 | 1,532 / 1,532 |

The All-Sky residuals are float32-versus-float64 serialisation of the same
numbers, not disagreements. **The backend is accepted.** It is selected by
`--backend gator`; `tap` remains the default, so M3's and M4's runs reproduce
exactly as they were issued.

### 1.3 The cache is incremental now, which was M4 §7.1's actual request

M4 §7.1: *"`m3_vet_survivors.py` writes its V1/V2 cache only after **both**
IRSA releases have been queried, so a run killed part-way loses everything."*
Fixed: `tap_chunks` and the new `gator_chunks` both take a `part` path, tag
every returned row with its `_chunk`, write the partial after **every** chunk,
and on restart reload the finished chunks and re-issue only the missing ones.
Nothing about the gates changed; `verdict()` is byte-identical to M3's.

*Both fixes are kept even though the fast route makes the checkpointing nearly
moot — a 1,300× speedup is a property of a service that can go away; the
resumability is a property of the code.*

---

## 2. The verdict table — all 1,545, and what the survivors actually are

*`scripts/m5_catalog.py`; artifacts `out/m5_verdict_table_m4_g0.1.csv`
(1,545 rows, every gate and every flag), `out/m5_verdict_summary_m4_g0.1.json`.*

| verdict | n | % |
|---|---|---|
| **CONTAMINATION-CONSISTENT** | **719** | 46.5% |
| **INDETERMINATE** | **584** | 37.8% |
| **SUB-THRESHOLD** | **242** | 15.7% |
| **STILL-CLEAN** | **0** | **0.0%** |

**The zero is not a measurement.** STILL-CLEAN requires positive evidence on
every axis including a valid centroid, and V5 is retired (§6). **No object can
reach STILL-CLEAN, and none did in M3 or M4 either.** The honest description of
the 584 is therefore:

> **objects with no *detectable* contamination evidence, given a method with a
> known blind spot** — a blind spot with a number: at a 1″ floor ≈10%, and at a
> 2″ floor ≈40%, of chance-aligned contaminants inside Suazo et al.'s own 3.25″
> aperture are invisible **at any brightness** (M4 §5.3).

**Not one of them is a candidate for anything, and there is no Matthew-gated
survivor from this screen.**

### 2.1 By Galactic latitude

| \|b\| | n | CONTAM-CONSISTENT | INDETERMINATE | SUB-THRESHOLD | nebular-flagged |
|---|---|---|---|---|---|
| 0–5° | 670 | 324 (48.4%) | 290 (43.3%) | 56 (8.4%) | 586 |
| 5–10° | 217 | 116 (53.5%) | 82 (37.8%) | 19 (8.8%) | 133 |
| 10–20° | 335 | 150 (44.8%) | 106 (31.6%) | 79 (23.6%) | 200 |
| 20–30° | 100 | 44 (44.0%) | 31 (31.0%) | 25 (25.0%) | 37 |
| 30–50° | 133 | 48 (36.1%) | 47 (35.3%) | 38 (28.6%) | 4 |
| 50–90° | 90 | 37 (41.1%) | 28 (31.1%) | 25 (27.8%) | **0** |

M4 §6.3's third consistency check survives the finished run: the SUB-THRESHOLD
rate **rises** with latitude (8.4% → 27.8%), because in the plane the survivors
are bright nebulosity-boosted objects that clear the 5σ bar easily, while at
high latitude what is left is genuinely marginal. **The high-latitude sample is
smaller and fainter, not cleaner in signal-to-noise.**

*(M4 §6.3 quoted 260 SUB-THRESHOLD, 16.8%, from the fallback S/N path, and
warned it would move by ~1.5 points once the AllWISE `w?snr` columns landed. It
moved to **242, 15.7%** — inside the warning.)*

### 2.2 The verdict axis and the nebular axis are independent

|  | not nebular | nebular-flagged |
|---|---|---|
| CONTAMINATION-CONSISTENT | 246 | 473 |
| INDETERMINATE | 188 | 396 |
| SUB-THRESHOLD | 151 | 91 |

They measure different things — the verdict gates interrogate the **source**
(single-exposure counts, release consistency, its own S/N), the nebular stage
interrogates the **field** — and neither subsumes the other. **396 of the 584
INDETERMINATE objects sit in a flagged field**, which is why the funnel in §3 is
computed with the nebular stage at Table 4's position rather than folded into a
verdict.

---

## 3. The nebular stage — the whole remaining gap, and 81.6% of it closed

*`scripts/m5_nebular.py` (`fetch`, `sky`, `calibrate`, `apply`, `n3`),
`scripts/m5_funnel_nebular.py`; artifacts `out/m5_nebular_catalogs.csv`,
`out/m5_nebular_catalog_report.json`, `out/m5_nebular_thresholds.csv`,
`out/m5_nebular_calibration.json`, `out/m5_nebular_flags_*.csv`,
`out/m5_nebular_skymask.json`, `out/m5_funnel_nebular.json`,
`out/m5_n3_*_density.csv`, `out/m5_n3_interloper_prior_previsual.json`.*

M4 §4 left the project with one unreproduced stage carrying the entire residual.
This section builds a replacement out of public data. **It is not a
reimplementation of the paper's CNN** — those weights and that training set are
unpublished, so nothing here reproduces theirs; it is an independent test of the
same physical thing.

### 3.1 N1 — the known-nebula catalogue veto, with no free parameter

Fourteen catalogues, fixed in PR-2 before any cross-match, downloaded
anonymously from VizieR. **All 14 resolved; none had to be reported absent.**
**29,462 nebular objects.** The veto radius is *the catalogue's own published
extent*, converted with the unit VizieR itself declares — never a radius chosen
here.

| catalogue | source | n | extent column | median r | max r |
|---|---|---|---|---|---|
| HII_WISE | Anderson+ 2014, ApJS 212, 1 | 8,399 | `Rad` (arcsec) | 67″ | 5,689″ |
| PGCC | Planck Collab. 2016, A&A 594, A28 | 13,242 | `maj` (arcmin) | 277″ | 564″ |
| DARK_LDN | Lynds 1962, ApJS 7, 1 | 1,780 | `Area` (deg²) | 450″ | 13,625″ |
| BRIGHT_LBN | Lynds 1965, ApJS 12, 163 | 1,122 | `Area` (deg²) | 592″ | 23,158″ |
| PN_SECGPN | Acker et al. 1992 | 1,143 | *none* → declared 60″ | 60″ | 60″ |
| REFL_MAGAK | Magakian 2003, A&A 399, 141 | 913 | *none* → declared 60″ | 60″ | 60″ |
| PN_MASH1 / MASH2 | Parker+ 2006 / Miszalski+ 2008 | 903 / 335 | `MajDiam` (arcsec) | 11″ / 5.5″ | 900″ / 444″ |
| DARK_BARN | Barnard 1927 | 349 | `Diam` (arcmin) | 300″ | 8,100″ |
| CED | Cederblad 1946 | 330 | `Dim1` (arcmin) | 120″ | 12,000″ |
| HII_SH2 | Sharpless 1959, ApJS 4, 257 | 313 | `Diam` (arcmin) | 360″ | 36,000″ |
| SNR_GREEN | Green 2019, JApA 40, 36 | 294 | `MajDiam` (arcmin) | 540″ | 9,900″ |
| HII_RCW | Rodgers+ 1960, MNRAS 121, 103 | 181 | `MajAxis` (arcmin) | 270″ | 10,800″ |
| REFL_VDB | van den Bergh 1966, AJ 71, 990 | 158 | `BRadMax` (arcmin) | 168″ | 24,600″ |

*The extreme radii are real catalogue entries, not parsing errors — Sh2-276 is
Barnard's Loop at 20° diameter — and they are kept because PR-2 forbids choosing
a radius here. What they cost is measured in §3.2 rather than capped away.*

### 3.2 What N1 costs in sky, and the enrichment that says it is not just a mask

A veto built from large catalogued regions could remove survivors simply by
removing sky. So the sky it masks is measured directly — a seeded Monte Carlo of
**3,000,000 uniform points** through the identical geometry — and set against
the survivors it removes.

| \|b\| | sky masked | pre-visual survivors N1 flags | **enrichment** |
|---|---|---|---|
| 0–5° | 36.63% | 62.4% | **1.70** |
| 5–10° | 16.04% | 42.4% | **2.64** |
| 10–20° | 9.51% | 56.4% | **5.93** |
| 20–30° | 6.99% | 34.0% | **4.86** |
| 30–50° | 1.80% | 0.0% | — |
| **50–90°** | **0.03%** | **0.0%** | — |
| all sky | **7.77%** | 47.4% | **6.10** |

**Enrichment above 1 means the veto is tracking contamination, not geography**,
and it needs no threshold to interpret. It is 5.93 at 10–20°, and 1.70 in the
innermost plane — where a third of the sky genuinely *is* inside a catalogued
nebula, so a larger share of N1's work there is area. **At |b| > 50° the veto
touches 0.03% of the sky and zero survivors**, which is the behaviour a nebular
stage should have where there is no nebulosity. Sh2 (3.04%), LDN (2.79%) and LBN
(2.04%) dominate the mask; the WISE H II catalogue masks only 0.48% but is far
more surgical, flagging 4.0% of the pre-visual survivors from 0.5% of the sky.

Which catalogue does the work, on survivors rather than on sky: Sh2 288, LDN
158, LBN 115, WISE H II 62, PGCC 32, RCW 23, SNR 20, Cederblad 16, Barnard 10,
vdB 9. **The two catalogues with no published extent — SECGPN and Magakian —
flag none**, as do both MASH planetary-nebula catalogues: the declared 60″
fallback changes nothing, and neither does any planetary nebula on the sky.

### 3.3 N2 — AllWISE's own coadd background, and N3's local density

**N2's statistic is not an image download.** AllWISE's pipeline already measures
the median background in each source's profile-fit annulus and publishes it as
`w3sky`/`w4sky` (with `w3conf`/`w4conf`, the confusion derived from the
uncertainty images) — an extended-emission statistic **measured from the
coadds**, available as a catalogue column, and reachable in bulk through §1.1's
route.

**The zodiacal light dominates it, which is why PR-2 bins by ecliptic latitude**
— the 0.99 threshold on `w3sky` runs from 3,456 DN at |β| < 10° to 1,338 DN at
|β| > 60°. The test that what remains tracks the *Galactic* plane has to be
shown, not asserted:

| \|ecliptic\| | n calib | clean-sky median (\|b\|>50°) | \|b\|<5° | \|b\|10–30° | \|b\|>50° | plane/clean |
|---|---|---|---|---|---|---|
| 0–10° | 13,031 | 3,078 | 3,154 | 3,153 | 3,084 | **1.025** |
| 10–20° | 10,343 | 2,646 | 2,868 | 2,630 | 2,657 | **1.084** |
| 20–30° | 11,122 | 2,141 | 2,307 | 2,011 | 2,130 | **1.077** |
| 30–40° | 11,230 | 1,771 | 1,973 | 1,717 | 1,788 | **1.114** |
| 40–50° | 10,325 | 1,523 | 1,744 | 1,457 | 1,510 | **1.146** |
| 50–60° | 8,106 | 1,359 | 1,599 | 1,257 | 1,356 | **1.177** |
| 60–70° | 4,354 | 1,267 | 1,532 | 1,214 | 1,260 | **1.209** |

**In every bin the plane sits above the clean-sky median of the same ecliptic
latitude, and |b| > 50° sits on it.** The amplitude is modest — 2.5% to 21% —
but the *tail* is what the percentile rule selects, and the tail is heavily
populated in the plane. Median N2 score among the 9,486 RMSE survivors:

| \|b\| | 0–5° | 5–10° | 10–20° | 20–30° | 30–50° | 50–90° |
|---|---|---|---|---|---|---|
| median score | **1.000** | 0.649 | 0.277 | 0.303 | 0.303 | 0.535 |
| fraction > 0.99 | **60.6%** | 25.7% | 6.8% | 5.2% | 4.2% | **1.6%** |

**60.6% of |b| < 5° RMSE survivors sit in the top 1% of clean-sky background — a
47× enrichment over the 1.29% baseline — and at |b| > 50° the rate is 1.6%,
i.e. the false-positive rate itself.**

**Calibration, measured and not assumed.** 68,209 parent stars at |b| > 50° with
a background measurement, 4,337–13,031 per ecliptic bin. The two bands are
Spearman **0.9991** correlated, so the max-of-two rule is effectively one band,
and the **measured** combined false-positive rate at 0.99 is **1.29%** (5.89% at
0.95, 0.16% at 0.999) — reported rather than derived from an independence
assumption that does not hold. *The calibration set contains the 90 |b| > 50°
survivors it is later applied to; at 90 of 68,209 that self-inclusion is 0.13%
and cannot matter.*

**N3 — the local mid-IR source density, reported and not cut**, exactly as PR-2
fixed. Around each survivor: AllWISE sources within 60″ with a ≥3.5σ W4
detection at comparable brightness, and separately those inside Suazo et al.'s
own 2.84 < W3−W4 < 3.25 colour band.

| \|b\| | all AllWISE | W4-comparable | **Suazo colour band** | V4's global assumption |
|---|---|---|---|---|
| 0–5° | 24,986 | 7,972 | **1,830** deg⁻² | 4.57 deg⁻² |
| 5–10° | 25,458 | 6,606 | **1,838** | 4.57 |
| 10–20° | 22,183 | 5,928 | **2,364** | 4.57 |
| 20–30° | 20,672 | 3,793 | **1,536** | 4.57 |
| 30–50° | 18,309 | 1,956 | **310** | 4.57 |
| 50–90° | 16,438 | 1,464 | **255** | 4.57 |

**V4 has been using one number where the truth has a factor-7 latitude
gradient.** Expected interlopers inside Suazo et al.'s own 3.25″ aperture among
the 1,545: **6.7 with the local density, 0.018 with V4's constant — a factor
372.**

*Caveat, stated: this counts **sources**, not galaxies — it does not separate
background galaxies from Galactic dusty stars, so it is an **upper bound** on
the interloper density and not a measurement of the galaxy density Suazo et al.
quote. **Which is the point.** Even the upper bound is 6.7 against 585 surviving
objects, so chance alignment with sources AllWISE can **resolve** explains
almost none of this sample. The interlopers that matter are the ones AllWISE
never catalogues separately — precisely candidate D's 1.23″ companion, and
precisely what the retired centroid axis was meant to catch.*

The W4-detection gate in that count is load-bearing, and was found the hard way:
AllWISE publishes a `w4mpro` for undetected sources too, as a 95% upper limit
near mag 8–9, so without the S/N gate essentially every neighbour counts as
"W4-bright" and the density comes out ~1,000× too high. All ten labelled
candidates A–J have **zero** W4-comparable neighbours within 60″.

### 3.4 The funnel with the stage in place, and the residual by latitude

| stage | ours | Hephaistos II Table 4 | ratio |
|---|---|---|---|
| RMSE ≤ 0.2 | 9,486 | 11,243 | 0.84× |
| **+ nebular stage (N1 ∨ N2)** | **6,529** | 5,732 *(their CNN)* | **1.14×** |
| + extra cuts | 5,943 | 5,137 | 1.16× |
| **+ S/N ≥ 3.5 — pre-visual** | **585** | **368** | **1.59×** |

**Our stage rejects 31.2% at the RMSE gate; theirs rejects 49.0%.**

| \|b\| | area deg² | pre | post | rejected | x before | **x after** | x area-corrected |
|---|---|---|---|---|---|---|---|
| 0–5° | 3,595 | 670 | 84 | **87.5%** | 20.89× | **2.62×** | 4.13× |
| 5–10° | 3,568 | 217 | 84 | 61.3% | 6.82× | **2.64×** | 3.14× |
| 10–20° | 6,946 | 335 | 135 | 59.7% | 5.41× | **2.18×** | 2.41× |
| 20–30° | 6,517 | 100 | 63 | 37.0% | 1.72× | **1.08×** | 1.17× |
| 30–50° | 10,975 | 133 | 129 | 3.0% | 1.36× | **1.32×** | 1.34× |
| **50–90°** | 9,651 | 90 | **90** | **0.0%** | 1.05× | **1.05×** | 1.05× |
| all sky | 41,253 | 1,545 | **585** | 62.1% | 4.20× | **1.59×** | **1.72×** |

**Excess over the paper's 368: 1,177 before, 217 after — 81.6% of it removed
(77.4% on the area-corrected reading).**

*Two denominators are given because they answer different questions. `x after`
divides by the full band area, which is the like-for-like comparison — the
paper's CNN removed **objects**, not area. `x areacorr` divides instead by the
area N1 leaves unmasked, which is conservative, because a mask lowers our count
without lowering theirs. **Both are reported; neither is chosen**, and the
honest headline is the range 1.59–1.72×.*

The `x before` column reproduces M4 §4.3 exactly — 20.89, 6.82, 5.41, 1.72,
1.36, 1.05 — which is the arithmetic check that this section is operating on the
same funnel M4 delivered.

### 3.5 PR-2's validation, all three parts

**(a) 7/7 of the paper's published candidates are preserved** — and 10/10 of the
labelled objects A–J. **N1 flags none; N2 flags none.** N2 scores: A 0.568,
B 0.323, C 0.000, D 0.140, E 0.333, F 0.000, G 0.533, H 0.665, I 0.026,
J 0.381 — all far below the 0.99 cut, none even in the top third of clean-sky
background. **PR-2 declared this test weak in advance, and it is**: all ten lie
at |b| > 28.8°, where nebulosity is scarce. Passing it is necessary, nowhere
near sufficient; failing it would have been disqualifying.

**(b) The signed prediction holds.** The rejected fraction falls
**monotonically** with |b| — 87.5%, 61.3%, 59.7%, 37.0%, 3.0%, 0.0% — and the
overproduction moves towards 1.0 in **every** band. A stage removing a
latitude-flat fraction would have been removing something else; this one does
not.

**(c) No count-peeking.** The threshold is PR-2's 0.99. The sensitivity band,
**labelled sensitivity and not selection**: 0.95 → 557 survivors (1.51×),
**0.99 → 585 (1.59×)**, 0.999 → 609 (1.65×). **A ±0.05 move in the threshold
moves the answer by ±5%**, so nothing here rests on the choice.

### 3.6 What the stage does *not* do, stated as PR-2 required

PR-2, in advance: *"this stage will **not** close the 20.9× at |b| < 5°."* It
does not.

- **The residual in the innermost plane is still 2.62×** (4.13× area-corrected).
- **Our stage rejects 31.2% where theirs rejects 49.0%** at the same gate. The
  17.8-point difference is the honest measure of what a catalogue veto plus a
  background percentile cannot see and a trained classifier can: **structure**.
  Nebulosity that nobody has catalogued, and that raises the local background by
  less than the top-1% cut, is invisible to both N1 and N2; a classifier looking
  at image morphology is not restricted that way.
- **A catalogue veto can only remove what somebody has already catalogued.** The
  WISE H II catalogue is itself built from W3/W4 morphology and is the closest
  thing in the list to the CNN — and it flags only 4.0% of the pre-visual
  survivors.
- **The difference is itself the publishable statement** M4 §7.2 asked for: the
  paper's CNN was doing roughly **1.6× more rejection at the RMSE gate than the
  union of every catalogued nebula on the sky plus a 1%-false-positive-rate
  background cut.** That is a quantitative description of what an unpublished
  stage was doing, obtained without its weights.

---

## 4. The high-latitude catalogue — the positive deliverable

*`scripts/m5_catalog.py`; product
`catalog/dyson-revet_highlat_extreme_IR_excess_v1.csv` (**223 rows × 62
columns, 153 KB**), `catalog/README.md`, `catalog/catalog_stats.json`.*

**223 stars within 300 pc whose 12 and 22 μm fluxes exceed any dust-free
photosphere model, at |b| > 30°, from a 100%-of-sky screen.** The `b_band`
column separates the **90-object |b| > 50° calibrated core** — where M4 §4.3
measured 1.05× [0.94–1.17] — from the 133-object 30–50° outer band, which sits
at 1.32× after §3's stage and is *not* equally defensible. **The distinction is
per row, not in a footnote.**

**Every survivor in the footprint is included, including the 148 our own gates
convict**, each carrying its verdict and its evidence. A catalogue that drops
its own rejects cannot be checked — and those rejects are one of the more useful
things in it.

**What is in it**: 85 CONTAMINATION-CONSISTENT, 63 SUB-THRESHOLD, 75
INDETERMINATE, **0 STILL-CLEAN**. M_G 7.5–13.6 (median **10.9** — dominated by
M dwarfs), distances 59–299 pc (median 224), fitted blackbody temperature
100–283 K (median **141 K**), covering fraction 0.100–0.422 (median 0.100, i.e.
**piled against the model grid's own floor**), W4 6.81–9.48. All 223 have 2MASS
photometry. Four carry a nebular flag and are **retained and flagged, not cut**,
because at |b| > 30° the flag rate is the stage's own ~1% false-positive rate
and is not by itself evidence about an object.

**Completeness — measured, and mostly bad, which is the reason for saying it.**
The γ ≥ 0.10 grid floor dominates: M3 measured that dropping it to γ ≥ 0.01
multiplies pre-visual survivors by 2.93×, so **the catalogue misses the majority
of weaker excesses by construction**. The S/N ≥ 3.5 cut removes **92.8%** of the
3,095 objects that reach it in this footprint. Full 10-band photometry is
required (99.27% of the parent has it). Sky coverage is complete, and N1 masks
**0.97%** of the |b| > 30° sky and **0.03%** of the core. **UNMEASURED and
marked as such: no injection-recovery test has been run**, so the fraction of
real extreme-excess objects the RMSE fit recovers is not known.

**Contamination — measured, and high.** 38.1% CONTAMINATION-CONSISTENT, 28.3%
SUB-THRESHOLD. The centroid blind spot applies to every row (§6). Chance
alignment with *catalogued* sources is not the dominant mechanism (§3.3). The
empirical base rate among published candidates of this type is five in ten with
an identified contaminant, two of them by JWST.

**What it is for, beyond technosignatures** — the framing `catalog/README.md`
leads with, because it does not depend on the question this project cannot
answer: extreme debris disks (`t_ds` and `gamma` are in the table); extreme
M-dwarf mid-IR excesses, a regime where WISE-excess samples are sparse; dust
pollution around low-mass and evolved stars; **a measured, position-resolved
false-positive set for anyone building a WISE-excess pipeline** — the catalogued
ways AllWISE manufactures a 22 μm excess; and a test set for
`sep_thr(ρ) = F(1 + 1/ρ)` if imaging becomes available.

**Nothing in this catalogue is a candidate for anything, nothing in it is
Matthew-gated, and nothing has been reported anywhere.**

---

## 5. Candidate E — the procedure, dated, and what each outcome would mean

*`scripts/m5_jwst_target.py`; artifacts `out/m5_jwstD_photometry.csv`,
`out/m5_jwstD_summary.json`, `out/m5_jwstD_validation.json`,
`data/jwst/m5_status_E.csv`.*

### 5.1 E's status, re-checked today (2026-08-23)

Anonymous MAST query, `proposal_id = 7199`:

| | |
|---|---|
| observations of `Object_E` / `Object_E_background` | **39** |
| **PUBLIC** | **0** — all 39 `EXCLUSIVE_ACCESS` |
| release | **MJD 61292.31 / 61292.33 = 2026-09-09** |
| **MIRI imaging** | **3 mosaics — F560W, F1000W, F1500W, 1146.716 s each**, obs `jw07199-o006_t008`, target `Object_E_background` |
| MIRI/IFU cubes | 36 (24 on `Object_E`, 12 on `Object_E_background`) |

**E's imaging has exactly D's structure** — same three filters, same exposure
time, same hosting on the `_background` observation, one observation number
later (`o006` against D's `o005`). The chain transfers without modification.

### 5.2 The procedure — runnable, and validated on D before E exists

```
python scripts/m5_jwst_target.py status  --label E                    # confirm PUBLIC
python scripts/m5_jwst_target.py fetch   --label E                    # anonymous MAST
python scripts/m5_jwst_target.py measure --label E --obsprefix jw07199-o006
```

Three commands, on or after **2026-09-09**. The astrometry comes from
`candidates_gaia_chain.csv` by label and is propagated to each mosaic's own
`EXPSTART`; the CRDS encircled-energy radii come from each L3 catalogue's
`aperture_params` metadata and are never invented; the brighter component of the
pair is **measured** per filter and used for the empirical leak model; the
deblend is the same 2×2 linear system M4 §5 used.

**PR-4's readiness test, run today.** The parameterised path was pointed at D
and graded against M4 §5's hard-coded chain:

| check | M5 parameterised | M4 §5 | tolerance | |
|---|---|---|---|---|
| separation | **1.233″** | 1.230″ | ±0.02 | **PASS** |
| position angle | **32.998°** | 33.0° | ±1.0 | **PASS** |
| ρ F560W | **0.236** | 0.236 | ±0.02 | **PASS** |
| ρ F1000W | **7.242** | 7.242 | ±0.14 | **PASS** |
| ρ F1500W | **83.135** | 83.134 | ±1.66 | **PASS** |
| ρ(W3, 12 μm) | **21.811** | 21.8 | ±1.5 | **PASS** |
| predicted W3 pull | **1.179″** | 1.180″ | ±0.03 | **PASS** |

**Every check passes — 7 of 7. READY for candidate E.** *(One deliberate difference from M4's chain,
and it is an improvement: `BRIGHTER` was a hard-coded per-filter dictionary in
`m4_jwstD_final.py`; here it is measured from the EE50 aperture sums, because
for E nobody knows the answer in advance.)*

**The detection criterion is fixed now, before E's data exist** (PR-4): a second
source is DETECTED if the brightest pixel in the 0.5–2.2″ annulus exceeds the
3.0–4.5″ background annulus by ≥ **5σ** of that annulus, in ≥ **2** of the 3
filters. On D it fires at **229.9σ** in F560W — the criterion is nowhere near
binding on a real contaminant.

### 5.3 The outcome map — written before the data open

**Four cases. Each is stated with its consequence for the tally *and* for the
archival-floor calibration, so that no result can be re-interpreted afterwards.**

**Outcome 1 — a contaminant is detected ABOVE the archival floor**
(sep > F(1+1/ρ), i.e. sep ≳ 1.05″ for a 1″ floor at high contrast).
*Tally:* E stays contamination-confirmed; the JWST-vetted sample becomes **3**
once A follows in 2027; the standing count of five labelled candidates with an
identified contaminant is confirmed by *measurement* rather than citation for a
second object. *Calibration:* **the strongest outcome for this project.** M4 §5.3
rests on **one** (separation, contrast) pair; a second turns
`sep_thr(ρ) = F(1+1/ρ)` from a formula anchored at one point into a two-point
relation, and lets the ~1″ scatter M4 measured across four archival estimates of
D's single truth be tested for repeatability. **The prediction this project is
making is explicit**: E's archival centroid offset should again exceed the
geometric ceiling `sep`, and its direction should again be uninformative. **If
instead E's archival centroid points at the real contaminant, §6's retirement of
V5 is too strong and must be revisited.** That is the falsifier, and it is
written down before the data.

**Outcome 2 — a contaminant is detected BELOW the archival floor** (sep ≲ 1″).
*Tally:* unchanged — E is still contaminated. *Calibration:* **this is the more
consequential result for the method, not the less.** It is a direct measurement
of an object inside the blind spot, and it converts the blind-fraction estimate
(≈10% at a 1″ floor, ≈40% at 2″) from a geometric argument over an assumed
uniform background into something with an empirical anchor. It would also mean
archival vetting could **never** have caught E — the sharpest available
statement about what §3.4's 585 surviving pre-visual objects are worth.

**Outcome 3 — no second source at 5σ in ≥ 2 filters.** *Tally:* E's
contamination attribution would rest entirely on the MRS spectrum, and this
project would record the imaging as **not confirming** it — the same posture it
takes on D's z ≈ 0.9. This would be a **tension with Hephaistos IV**, and must
be reported as one rather than softened. *Calibration:* the deliverable becomes
an **upper limit on ρ at each separation** — the contrast a contaminant could
have had and still escaped MIRI — which bounds the floor from the other side.
*The honest prior: D's contaminant was obvious at 230σ, so a non-detection at E
would be surprising, and surprise is exactly when a pre-registration earns its
keep.*

**Outcome 4 — the data are unusable** (the mosaic does not cover the target, the
`_cat.ecsv` is missing, unrecoverable artefacts). *Tally and calibration:*
unchanged; reported as a data problem, not a science result. The chain fails
loudly on each of these rather than proceeding: it checks the target lands ≥ 60
px inside a mosaic, and it refuses to run without the CRDS aperture metadata.

**In every outcome**: nothing is submitted, posted or sent. E becomes a
Matthew-gated item only if a result contradicts a published claim — Outcome 3 —
and in that case it is gated before anything is written outside this repository.

### 5.4 Also still true, and dated

Candidate **A**'s GO 7199 data remain under exclusive access until
**2027-07-16**. D's **MRS cubes are public and still not reduced** — the one
part of D's story this project takes on citation rather than measurement
(M4 §5.4), and the only route to testing z ≈ 0.922 independently.

---

## 6. V5 — the centroid axis, formally retired

*Append-only. This section is the record. It supersedes M3 §3.2's prescription
and closes what M4 §7.3 asked for. Nothing in M5 re-enables, re-tunes or
re-scores the axis.*

**Status: RETIRED for objects near the archival floor. Dated 2026-08-23.**

**History, so the retirement is auditable.**

- **M1 §3.2** introduced the centroid axis and used it on candidates D and I,
  already noting that a real 1.0″ contaminant moves the AllWISE centroid by only
  0.5–1.4″.
- **M2 §1** stated the floor as a project law: **archival centroid vetting has a
  hard sensitivity floor at ~1–2″ separations.**
- **M3 §3.2** ran it at scale on 845 survivors and **refused it a vote**: its 10″
  peak search locks onto brighter neighbours (a 9.51″ "offset" is a
  2.4×-brighter source at 10.24″; an 11.89″ one is a 14×-brighter source at
  16.36″). M3 disabled it and **prescribed two fixes for M4** — a 3″ search
  radius and a neighbour-aware validity check.
- **M4 §5.3 superseded that prescription with a measurement**, on the one object
  where JWST supplies the truth.

**The reason, from M4 §5.3.** Candidate D's contaminant is at **1.23 ± 0.07″,
PA 33 ± 1°**, measured here from public MIRI mosaics.

1. **The magnitude is impossible.** The flux-weighted pull is `sep·ρ/(1+ρ)`, so
   the geometric ceiling is the separation itself, **1.23″**. This project's
   archival W4 offset is **2.55 ± 0.50″ — +2.6σ above a hard ceiling** — and
   Ren et al. 2026's independent **1.8″** exceeds it too. Four archival
   measurements of one truth of 1.23″ read 0.75″, 1.41″, 1.8″ and 2.55″.
2. **The direction is wrong.** Our W3 offset points at **PA 82.9°, 50° away from
   the real contaminant**, where MIRI shows nothing.

**A smaller search radius cannot repair a measurement whose direction carries no
information.** M3's prescribed fixes address the wrong failure: they would stop
the axis locking onto a *catalogued neighbour*, but D's contaminant was never a
separate AllWISE source at all — §3.3 measures **zero** W4-comparable
neighbours within 60″ of D. Retuning would improve the precision of a quantity
that is not measuring what it is being read as.

**What replaces it — a statement of what centroid vetting can and cannot do:**

> **sep_thr(ρ) = F · (1 + 1/ρ)**

the minimum separation at which a contaminant of contrast ρ can move the
centroid past a floor F. **It asymptotes to F itself**, so no contaminant closer
than the floor is ever detectable, at any brightness — **brightness does not buy
separation.** Applied inside Suazo et al.'s own 3.25″ aperture radius: **≈10% of
chance-aligned contaminants are invisible to a 1″ archival centroid test, and
≈40% to a 2″ one.**

**Consequences, carried everywhere rather than worked around.**

- **STILL-CLEAN is unreachable.** It requires positive evidence on every axis
  including a valid centroid. **0 of 1,545 (M5), 0 of 845 (M3).** The zero is
  reported as a property of the method, never of the objects.
- **INDETERMINATE means "no *detectable* contamination evidence", not "clean".**
  That wording is carried in §2, in the catalogue's per-row
  `v5_centroid = "RETIRED"` column, and in `catalog/README.md`.
- **There is no Matthew-gated candidate from this screen**, and there cannot be
  one on archival evidence alone.
- **The offsets are kept as data**, flagged, in `out/w2_centroid_offsets.csv`.
  They are not deleted; they are not allowed to decide a verdict.

**What would un-retire it.** A second (separation, contrast) pair from candidate
E (§5.3, Outcome 1) in which the archival centroid points at the *real*
contaminant. That is the falsifier, and it is written here before E's data open
on 2026-09-09.

---

## 7. Recommended M6

1. **Close the last 17.8 points of the nebular gap with morphology.** §3.6
   measures exactly what N1 and N2 cannot see: our stage rejects 31.2% at the
   RMSE gate where the paper's CNN rejects 49.0%, and the missing ingredient is
   **image structure**. §1.1 has just made per-object image work affordable for
   the first time. The cheapest honest test: pull WISE W3/W4 coadd cutouts for
   the 2,957 objects the stage flags and the 6,529 it passes, and measure a
   structure statistic that needs no training set — the ratio of annulus flux to
   PSF-core flux, or the background gradient across the beam. Validate it
   identically: 7/7, a monotone latitude gradient, and a threshold set on the
   |b| > 50° control.
2. **Candidate E, on 2026-09-09.** §5's three commands, §5.3's outcome map, and
   the falsifier for §6 written down in advance. Highest information per hour in
   the project, and it has a date.
3. **Reduce D's public MRS cubes.** Unchanged from M4 §7.5 and still the only
   route to testing z ≈ 0.922 independently — the one part of D's story this
   project takes on citation. It would also test the 441 K single-blackbody
   temperature M4 §5.2 infers from three photometric points.
4. **Measure the catalogue's completeness by injection–recovery.**
   `catalog/catalog_stats.json` marks this **UNMEASURED**, and it is the biggest
   hole in the positive deliverable: nobody knows what fraction of real
   extreme-excess objects the 10-band RMSE fit recovers. Inject synthetic
   star + blackbody SEDs across (T, γ) into the real parent photometry with its
   real uncertainties and re-run the fit. This would turn the γ ≥ 0.10 floor
   from a stated limitation into a measured selection function, and it needs no
   network at all.
5. **Separate galaxies from stars in N3.** §3.3's interloper density is an upper
   bound because it counts sources. A Legacy Survey DR10 or Pan-STARRS
   morphology cross-match on the colour-selected neighbours would split them,
   and would turn the 372× discrepancy with V4's constant into a real,
   latitude-resolved chance-alignment prior — which is what V4 has needed since
   M2.
6. **Two small items carried forward.** (a) M4 §7.7's ~3% parent residual is
   still the last unexplained number in the funnel: one measurement, re-running
   the parent with a numerical S/N floor in place of `ph_qual ≠ 'U'`. (b) The
   γ ≥ 0.01 sensitivity has not been re-run on the full sky — M3 measured it on
   48.18% and nothing since has touched the model grid, but the nebular stage
   changes what the floor implies, and it is now cheap to redo.
7. **Matthew's calls, unchanged and still waiting** (M2 §5.5, M3 §7.6, M4 §7.8):
   (a) whether the Ren+24 unit-error note is worth submitting given Blain's
   prior "(sic)", and if so the three manual browser checks first (IOP page,
   PubPeer, ADS); (b) whether the candidate-I dossier becomes a JWST DDT /
   small-GO proposal, an RNAAS note, or stays internal. **M5 adds no new
   Matthew-gated item: no object reached STILL-CLEAN, and none can.** The
   high-latitude catalogue is a repository product, not a submission, and
   nothing in it is candidate-level.

---

## 8. File index (new in M5)

**Document:** `M5-nebular-stage-highlat-catalog.md` (this).

**Product:**

- `catalog/dyson-revet_highlat_extreme_IR_excess_v1.csv` — **the high-latitude
  catalogue**, 223 rows × 62 columns, 153 KB, committed
- `catalog/README.md` — its own README: selection function, completeness,
  contamination, column dictionary, reproduction commands, citations
- `catalog/catalog_stats.json` — the same numbers, machine-readable

**Scripts (new):**

- `scripts/m5_nebular.py` — the nebular stage: `fetch` (14 VizieR catalogues),
  `sky` (the Gator background pull), `calibrate` (PR-2's threshold rule),
  `apply` (N1 ∨ N2 flags), `n3` (the local interloper density)
- `scripts/m5_funnel_nebular.py` — the funnel with the stage in place, the
  seeded sky-mask Monte Carlo, the enrichment statistic, the N2 within-ecliptic
  diagnostic, the latitude table, and PR-2's validation
- `scripts/m5_catalog.py` — the verdict table and the catalogue product
- `scripts/m5_jwst_target.py` — the parameterised JWST chain
  (`status` / `fetch` / `measure`), PR-4's detection criterion, and the D
  validation
- `scripts/m5_vet_accept.py` — PR-1's Gator-versus-TAP acceptance test

**Scripts changed:** `scripts/m3_vet_survivors.py` — **I/O only**: incremental
per-chunk caching with resume (`tap_chunks(part=...)`), the `gator_chunks`
backend, and a `--backend` flag defaulting to `tap`. **`verdict()` and every
threshold are untouched**, so M3's and M4's runs reproduce exactly.

**Artifacts:**

- `out/m5_vet_accept_m4_g0.1.json` — PR-1's acceptance test
- `out/m5_verdict_table_m4_g0.1.csv`, `out/m5_verdict_summary_m4_g0.1.json`
- `out/m5_nebular_catalogs.csv` (29,462 objects),
  `out/m5_nebular_catalog_report.json` (per-catalogue provenance and extents)
- `out/m5_nebular_thresholds.csv`, `out/m5_nebular_calibration.json`
- `out/m5_sky_{calib,rmse,previsual,candidates}_matched.csv` and their Gator
  caches
- `out/m5_nebular_flags_{rmse,previsual,candidates}.csv`
- `out/m5_nebular_skymask.json`, `out/m5_funnel_nebular.json`,
  `out/m5_funnel_nebular.log`
- `out/m5_rmse_survivors_nebular_m4_g0.1.csv`
- `out/m5_n3_{previsual,candidates}_density.csv`,
  `out/m5_n3_interloper_prior_previsual.json`
- `out/m5_jwstD_photometry.csv`, `out/m5_jwstD_summary.json`,
  `out/m5_jwstD_validation.json`, `data/jwst/m5_status_E.csv`
- `data/nebular/*.tsv` — the 14 raw VizieR downloads, and `data/nebular/cache/`
  the raw Gator responses. Both are bulk data under `data/` and therefore
  gitignored per repo convention; what is committed is the normalised union
  (`out/m5_nebular_catalogs.csv`, 29,462 rows) plus
  `out/m5_nebular_catalog_report.json`, which carries each catalogue's VizieR
  identifier, extent column, unit conversion and reference — enough to
  regenerate the raw downloads exactly

**Nothing in this milestone has been submitted, posted, or sent anywhere. No
account was created at VizieR, IRSA, MAST, AIP, ESAC or anywhere else; every
service was used anonymously. The candidate-I dossier and the Ren+24 note remain
Matthew-gated and unchanged.**
