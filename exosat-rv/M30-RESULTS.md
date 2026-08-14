# M30 — the outside sweep's "new public epochs", reconciled against the ledger (2026-08-14)

An archive sweep run outside this repo (`DISCOVERY/run3-prospectus.md`, avenue #1,
2026-08-14) claimed three newly-public CRIRES+ blocks on roster targets. The sweep ran
live ESO TAP queries but **did not read this repo's ledger**. M30's job: reconcile,
verify with this repo's own machinery, pre-check, stage what is genuinely new.

**Headline: none of the sweep's three blocks is a new analyzable epoch set.** Two are
data this project has already consumed or shelved; the third is still embargoed and the
sweep's counts for it are wrong. What the verification pass *did* find, that neither
the sweep nor the ledger had: **three public HiRISE fibre nights of HIP 65426 at H1567**
(the M27 corpus grows a target), a header classification for the public 2024-09
beta Pic deep pair (**M4368 thermal-IR on `bet Pic b`** — shelved class), and a
quantified pre-check verdict on CD-35's embargoed campaign: **useless as a standalone
BERV-robust test (R² = 0.92 at 171.454 d), decisive jointly (R² = 0.06)**.

Machinery: `scripts/m30_verify.py` (TAP, windowed, MAXREC raised) →
`data/m30-verify.json`; `scripts/m30_probe.py` (one raw header per candidate night,
fetch-read-delete); `scripts/m30_precheck.py` → `data/m30-precheck.json`;
`scripts/cr2res/m30_fetch.sh` (staging). All numbers below trace to those outputs
unless marked otherwise.

---

## 1. Reconciliation table

| sweep claim (run3 §Tier-1 #1) | known to ledger? | genuinely new? | verified truth (TAP + headers, 2026-08-14) |
|---|---|---|---|
| (a) HIP 65426: "90 exposures, K/HK settings, Mar 2024–May 2025, public since 2026-05-04" | **YES** — census v2 (2026-08-13) lists all 9 nights public; M20/M22 used the 5 planet nights | **NO** for the slit series — it *is* M22's series. **YES** for a part the sweep didn't distinguish: 3 HiRISE nights | Slit: **5 nights / 134 frames, K2192** (header-verified on the M22 products), OBJECT `HIP65426B`, progs 112.25GC + 115.283F, releases rolled **2025-03-11 → 2026-05-07** (not "since 2026-05-04"; that is one night's release date). Plus **3 HiRISE nights 2025-01-31/02-01/02-02, 27 frames, H1567** (probe §3), prog 114.2712 — **new to the ledger**. Plus 13 host frames from 2022. No "90 exposures" grouping exists; nearest sums are 134 (slit) or 174 (all). |
| (b) CD-35 2722: "300 exposures, Oct 2024, public since 2025-10-19, filter K,LM" | **YES** — M0 inventory (2026-08-10), census v2, M26 verdict, M28 §slit table | **NO** | The **known deep pair**: 2024-10-17 (150) + 2024-10-19 (150), prog 114.27LL.002, releases 2025-10-17/2025-10-19. filter_path "K,LM" is the documented hint; **header truth M4368 thermal-IR (M26), shelved with the L/M class**. The other Oct 2024–Jan 2025 frames are 2-frame H monitoring pairs (114.271E.001) — **the reproduction's own epochs** (M0 usable baseline 2023-10-13 → 2025-01-21; the fatal screened epoch 60604 = 2024-10-21 is one of them). Nothing new is public: the next epochs (116.2AP9, 10 nights) release **2026-12-19 → 2027-05-02**. |
| (c) beta Pic: "360-exposure K-band (HK) series public 2026-10-01; 1,266-exposure L/M campaign 2027-04-07" | **YES in part** — M23 §6 embargo calendar ("beta Pic b's late-2025 K2166 nights"); census v2 has all the dates | **NO** (nothing newly public; counts wrong) | The late-2025 series is **6 nights / 1158 frames** (2025-09-25 → 10-01, prog 115.2820.001), releases **rolling 2026-09-25 → 2026-10-01** — not a 360-exposure block on one date. Its setting is **unverified until release**: filter hints read `KX1E-2,LM` on 4 of 6 nights (hints lie, LESSONS §3.1; the ledger's "K2166" label is also only a hint-level guess). The "1,266-exposure L/M campaign" matches no clean grouping; 1266 = 1158 + 60 + 48 exactly, so the sweep likely lumped this series with two later nights. The actual later LM-hint nights (116.2987/116.290W) are 4 nights / 228 frames releasing 2026-12-19 → 2027-04-07. |

**Correction to the sweep, stated plainly:** its counts (90, 300-as-new, 360, 1,266) and
"public since" dates do not survive per-night verification, and all three blocks were
already in the ledger — (a) consumed by M22, (b) consumed/shelved since M0/M26, (c)
embargoed on the M23 calendar. An archive sweep that does not read the ledger cannot
distinguish "public" from "new".

## 2. Verification detail (2026-08-14, `data/m30-verify.json`)

Coordinate boxes (±60″) around census-resolved positions, every CRIRES science frame,
windowed by year. Frame totals: HIP 65426 **174**, CD-35 2722 **404** (deep pair +
monitoring pairs + pilots + embargoed), beta Pic **3961**.

**HIP 65426, all nine nights, per-night:**

| night | frames | mode | OBJECT | prog | release | disposition |
|---|---:|---|---|---|---|---|
| 2022-03-02 | 13 | slit nodding | HD 116434 | 108.2294 | 2023-03-02 | host science (H1575+K2217 products on disk); not a planet epoch |
| 2024-03-11 | 26 | slit nodding | HIP65426B | 112.25GC | 2025-03-11 | **M22 epoch 1** |
| 2025-01-31 | 9 | **HIRISE** | HD 116434 | 114.2712.001 | 2026-01-31 | **new to ledger** — fibre, H1567 |
| 2025-02-01 | 8 | **HIRISE** | HIP 65426 | 114.2712.002 | 2026-02-01 | **new to ledger** — fibre, H1567 |
| 2025-02-02 | 10 | **HIRISE** | HIP 65426 | 114.2712.002 | 2026-02-02 | **new to ledger** — fibre, H1567 |
| 2025-04-07 | 48 | slit nodding | HIP65426B | 115.283F | 2026-04-07 | M22 epoch 2 |
| 2025-04-15 | 16 | slit nodding | HIP65426B | 115.283F | 2026-04-15 | M22 epoch 3 |
| 2025-05-04 | 16 | slit nodding | HIP65426B | 115.283F | 2026-05-04 | M22 epoch 4 |
| 2025-05-07 | 28 | slit nodding | HIP65426B | 115.283F | 2026-05-07 | M22 epoch 5 |

The M22 five-night identification is confirmed two ways: the products on disk
(`data/spectra_hip65426/`, DATE-OBS + `INS WLEN ID = K2192` read directly) and the
422-day baseline arithmetic (2024-03-11 → 2025-05-07 = 422 d, matching M20 §4 exactly).

**CD-35 2722:** the Oct 2024 deep pair and the monitoring pairs as in §1. The embargoed
116.2AP9 campaign is **10 nights** (M0's summary field listed 8 embargo lifts; its own
nights table already contained all 10 — the two extra, 2026-04-07 and 2026-05-02, carry
K filter hints where the other eight are H hints; setting truth at release). Release
window verified per-file: **2026-12-19 → 2027-05-02**.

**beta Pic:** 54 nights of everything (slit K/H monitoring, the L/M tier, 8 public
HiRISE nights, the embargoed series). Nothing public that the ledger lacks, with one
classification exception — §3.

## 3. Header probes (one frame per candidate night, fetched → read → deleted)

`scripts/m30_probe.py`, longest-DIT frame per night. LESSONS §3.1/§1.10 honoured:
`INS WLEN ID`, `INS MODE`, `DPR TECH`, `TPL ID`, `ORIGFILE` read from the raw header.

| night / target | WLEN | MODE | TPL / ORIGFILE | OBJECT | reading |
|---|---|---|---|---|---|
| 2025-02-01 HIP 65426 | **H1567** | **HIRISE** | `HIRISE_spec_obs` / `HIRISE_SPEC_OBS032_0037` | HIP 65426 | fibre data, same setting as the whole HiRISE corpus — the project's eleven-order H1567 map applies |
| 2025-01-31 HIP 65426 | **H1567** | **HIRISE** | `HIRISE_spec_obs` / `HIRISE_SPEC_OBS031_0057` | HD 116434 | same; DIT structure 200 s ×4 + 1200 s ×5 = acquisition/host + deep, the M29 §16 pattern |
| 2024-09-19 beta Pic | **M4368** | Spectroscopy | `CRIRES_spec_obs_AutoNodOnSlit` / `CRIRES_SPEC_OBS263_0021` | **bet Pic b** | the public 2024-09-19/22 deep pair (2×150 frames, 113.26UN) is **thermal-IR, the shelved L/M class** — same class as CD-35's deep pair; now header-classified, closing a gap the ledger prose never recorded |

The third HiRISE night (2025-02-02) shares prog/template with 2025-02-01 and was not
probed separately (politeness); its TAP metadata is identical in kind.

**HIP 65426 HiRISE is genuinely new to the ledger.** The M27 banner's verified-target
list (HD 1160 B, AF Lep b, 51 Eri b, HIP 81208 B, PDS 70, BET PIC, HD 26820,
HD 19467, HD 206893) never included HIP 65426. The archive's HiRISE corpus
("1739 frames, ~45 targets", M29 §13) contained it in aggregate; nobody had looked.
Value: HIP 65426 b is the **exomoon-regime limit target** (M20 §4), and these are
starlight-suppressed fibre observations of that system — the instrument class the
blending sweep (M29 §12) concluded is *required* below R ≈ 1.

## 4. Phase–BERV pre-checks (`data/m30-precheck.json`)

The m15_inventory step-[3] geometry (R² of BERV regressed on cos/sin at each trial
period over the actual sampling; R² → 1 = a BERV nuisance absorbs any orbit there).
Epoch times are the median frame timestamp per night from the dp_ids.

### 4a. HIP 65426 — M22's five slit nights vs five + three HiRISE

| sampling | n | degenerate fraction (R²>0.5, 5–460 d) | BERV span |
|---|---:|---:|---:|
| 5 slit (M22) | 5 | 0.698 | 20.2 km/s |
| 5 + 3 HiRISE | 8 | 0.616 | 25.4 km/s |

Adding the HiRISE nights clears real lanes below 100 d (e.g. ~14–16, ~22–24, ~30–32,
~42–49, ~70–76, ~84–97 d become non-degenerate) but the three nights are consecutive
days (Jan 31 – Feb 2), so the long-period grid (104–460 d) stays fully degenerate.
Reading: **if the HiRISE nights ever yield planet RVs (M27 route), they strengthen the
P ≤ 100 d exomoon-regime limit — they cannot open the long-period range.** A five-night
sampling with a 3-parameter fit is near-degenerate almost everywhere; this is why M20's
limit was variance-based rather than a blind search.

### 4b. CD-35 2722 — the embargoed 116.2AP9 campaign at P = 171.454 d

The ten embargoed nights are observed; their dates are fixed; only release is pending.
So the out-of-sample geometry is computable today:

| sampling | n | R²(BERV \| 171.454 d) |
|---|---:|---:|
| embargoed 10 alone | 10 | **0.92** |
| existing series (20-night approx.) | 20 | 0.59 |
| existing strict 16 (M14-like: minus K night, gap nights, 60604) | 16 | 0.62 |
| **combined** | 26–30 | **0.05–0.06** |

Phase coverage of the new epochs at 171.454 d is excellent (10 epochs, largest gap
0.21 cycles) — but their sampling alone is almost perfectly BERV-degenerate at the
satellite period (R² = 0.92, worse than the original series' ~0.6 that cost three
milestones). **The embargoed campaign is not a standalone out-of-sample test. Jointly
with the existing series the degeneracy collapses to R² ≈ 0.05** — the combined fit is
the test, and it is a strong one. This sharpens M14 §9 ("decidable when the embargoed
epochs release") into a concrete instruction for the Dec 2026 – May 2027 releases:
*fit jointly, never the new epochs alone.*

### 4c. beta Pic late-2025 series — deferred

Embargoed until 2026-09-25+, setting unverified (hints contradict the ledger's "K2166"
label). Pre-check when the first night releases and a header probe settles the setting.

## 5. Staging (`scripts/cr2res/m30_fetch.sh`)

**A disk incident redirected this step, and the cause is a milestone in itself.** At
session start the data volume had 25 GB free (M29 §17's state). Mid-session it dropped
to **8.5 GB / 100%**: a **concurrent session completed the first HiRISE extraction** —
`red_m26/bpbhi`, the beta Pic b 2025-02-02 night, **39/39 frames extracted**
(`bpbhi HIRISE REDUCED OK`, last product 15:31 local), writing ~17 GB of products
including 201 MB-per-frame `_cal_extrModel.fits`. M27 has effectively begun outside
this session. M30 did not touch that work (house law: no deletions, no interference)
and verified the job had finished before using any disk.

Consequence: full staging (science + calibs ≈ 4.6 GB) was imprudent on a volume another
live campaign is writing to. Staged instead, per the smallest-verified-new-block rule:

- **Science only: the 27 HiRISE frames of HIP 65426's three nights** (~1.5 GB), serial,
  3-try loop with sleeps, size-validated skip-existing, judged by files on disk
  (LESSONS §3.6). Slugs `h65hi1/2/3` under `~/cr2res/raw_m30/`.
- **Calibration URL lists banked, not fetched**: the minimal M29 §16-pattern set
  (darks at the needed DITs ×3, flats ×5, UNE ×2, FPET ×2; the unfiltered CALIB
  fallback would over-fetch ~5 GB/night) written per night to
  `~/cr2res/logs_m30/m30_h65hi*_cal.txt`.
- **Resume**: `M30_SCI_ONLY=0 bash scripts/cr2res/m30_fetch.sh` refetches nothing that
  is size-valid on disk and adds the calibs (~3 GB). Run it only with ≥ 10 GB free.

**Staging outcome (judged by files on disk, LESSONS §3.6 — the runner's exit code was
a cosmetic 1 from the summary loop):**

| slug | night | science frames | size | size-validated | marker |
|---|---|---:|---:|---|---|
| `h65hi1` | 2025-01-31 | **9/9** | 435 MB | yes (`find -size +1M`) | `.sci_fetched` |
| `h65hi2` | 2025-02-01 | **8/8** | 386 MB | yes | `.sci_fetched` |
| `h65hi3` | 2025-02-02 | **10/10** | 483 MB | yes | `.sci_fetched` |

**27/27 frames, 1.3 GB, zero fetch failures** (serial, throttle-safe). Data volume
after staging: 7.2 GB free. Calib-list caveat for M31: three lamp DITs (4.281, 9,
15 s) had no same-day darks — the day-bounded CALIB query misses them; top up from
adjacent days when fetching.

**No reduction was started** — M31 is gated on Matthew seeing this document.

## 6. Surprises and ledger deltas

1. **A concurrent session has run — and validated — the M27 bpbhi extraction** (39/39
   frames, §5). While M30 was in flight it committed the on-sky proof as well
   (M29 §19+, `m29_hirise_ccf.py`): the planet trace shares tellurics with the host at
   **9.8σ** with the CCF peak at exactly 0 km/s — the extraction lands on sky; it is
   not a detection of the planet. Its stated next steps: telluric removal against the
   same-fibre host spectrum, planetary-template CCF, injection gate on the util_ chain.
   M30's scope stays clear of all of that.
2. **HIP 65426 joins the HiRISE corpus** (3 nights, 27 frames, H1567) — new ledger row.
3. **The public beta Pic 2024-09 deep pair is M4368 on `bet Pic b`** — shelved class,
   now recorded with header truth instead of silence.
4. **The ledger's "K2166" label for the embargoed beta Pic series is a hint, not a
   verification** — flagged so nobody pre-commits M31/M32 compute to a series that may
   be L/M-class. Settled by one header probe on 2026-09-25.
5. **cd35d1 is unchanged** — still the queued DROT POSANG SOF-split fix (its latest
   reduction log is the 08-13 crash; raw and H1567 calibs remain on disk).
6. **Disk pressure is structural**: `red_hd1160` 74 GB, `red_etatel` 42 GB, `red` 38 GB,
   `red_bpb` 26 GB, `red_crumbs` 21 GB, `red_m26/bpbhi` 17 GB (of which ~15 GB are
   re-derivable per-frame extraction models). Any cleanup decision is Matthew's;
   nothing was deleted in M30.

## 7. Recommended M31

In order, all gated on Matthew reading this:

1. **Finish HIP 65426 HiRISE staging and extract it through the now-validated path.**
   Calib lists are banked (~3 GB; top up the three missing lamp-DIT darks from
   adjacent days); then `reduce_hirise.sh`-style util_* extraction of the 27 frames.
   Two birds: a second HiRISE target through the chain the concurrent session just
   proved on-sky (M29 §19+), and starlight-suppressed epochs on the exomoon-regime
   limit target. Product-footprint warning: if per-frame extrModels are kept,
   ~200 MB × 27 ≈ 5.4 GB — plan disk first (7.2 GB free now).
2. **Do not duplicate the bpbhi thread.** Telluric removal, planetary-template CCF and
   the util_-chain injection gate are the concurrent session's stated next steps on
   beta Pic b; coordination is Matthew's call.
3. **beta Pic late-2025 series**: header probe + phase-BERV pre-check on 2026-09-25
   release; only then decide whether the M23 calendar item is real (K2166) or
   evaporates (L/M).
4. **CD-35 embargo plan**: pre-register the joint-fit out-of-sample protocol (§4b) for
   the Dec 2026 releases — new epochs never fitted alone (standalone R² = 0.92).
5. Housekeeping: a disk-space decision on the re-derivable extraction models
   (§6.6) — Matthew's call, nothing deleted in M30.

## 8. For the ledger

| item | before M30 | after M30 |
|---|---|---|
| sweep claim (a) HIP 65426 | "90 new exposures" | not new — M22's own series (134 slit frames) + **3 HiRISE nights new to ledger** |
| sweep claim (b) CD-35 | "300 new exposures Oct 2024" | not new — the M4368 deep pair, shelved since M26; monitoring pairs are the reproduction's own epochs |
| sweep claim (c) beta Pic | "360-exp K series 2026-10-01; 1,266-exp L/M 2027-04-07" | embargoed as the ledger knew; true shape 6 nights/1158 frames rolling 2026-09-25→10-01 + 4 nights/228 frames Dec 2026–Apr 2027; setting unverified |
| HiRISE corpus | 8 beta Pic nights + list of other targets | + HIP 65426 ×3 nights (27 frames, H1567, header-verified) |
| beta Pic 2024-09 pair | unclassified in prose | M4368 thermal-IR on `bet Pic b`, shelved class |
| CD-35 embargoed campaign | "decisive epochs Dec 2026–May 2027" | verified 10 nights, releases 2026-12-19→2027-05-02; **standalone R²=0.92 at 171 d (useless alone), joint R²=0.05 (decisive)** |
| M27 status | scoped, not started | **first extraction complete (concurrent session): bpbhi 39/39** |
