# M4 — the activity-vs-spuriousness test, the Bayestar-arbitrated dust dozen, and the day-one queue

*2026-08-18. Tests M3's n = 1 observation (the X-ray-loudest class-III match was a known
spurious solution) on the full El-Badry 2026 ground truth; pins the Bayestar19 → Gaia-band
unit chain M3 refused to guess and re-triages the dust-ambiguous rows; queues the
retrieval bin's high-Pr members into day one. Repo law: sourced-or-UNSOURCED; negative
results are results. Anonymous HTTP only; `../erosita-dr2/data/` consumed strictly
READ-ONLY. No accounts, no commits, no submissions.*

---

## 1. The activity-vs-spuriousness test (task 1) — direction confirmed, power not there

**Design** (`scripts/m4_eb26_erosita_test.py`; verdict rules pre-registered in the
docstring before running): all **76** EB26 followed-up astrometric candidates
(42 CONFIRMED / 23 SPURIOUS / 1 MARGINAL / 2 NOT_CO / 1 OTHER / 7 UNKNOWN;
`fixtures/elbadry2026_astrometric_candidates.csv`, all 76 present in the M2 triage
parquet) crossed against **eROSITA-DE DR2** (eRASS:3 Main v1.3 positional at
3.44 × POS_ERR ∈ [1, 10]″, PM-propagated 2016.0 → 2020.5; NWAY GDR3 id lookup; Hard
v1.2) **and DR1** (eRASS1 Main v1.2 — the independent shallower epoch), with 8
shifted-position controls (dec ± 0.5–2.0°). WORKS = Fisher p < 0.05 on detection rate or
Mann-Whitney p < 0.05 on log f_X/f_opt (≥ 3 detections/side); else DOESN'T (well-powered
null) or UNDERPOWERED, with the achievable power stated.

**Footprint is half the test, as feared**: only **16/42 confirmed and 13/23 spurious**
lie in the eROSITA-DE hemisphere (36/76 overall) — the sample the statistics get to see.

**Result** (`out/m4_eb26_erosita_xmatch.csv`, `out/m4_eb26_discriminator_stats.txt`):

| in-footprint group | eRASS:3 detected | rate (95 % Wilson) |
|---|---|---|
| CONFIRMED (16) | **0** | 0.000 (0.000–0.194) |
| SPURIOUS (13) | **2** | 0.154 (0.043–0.422) |
| other verdicts (7) | 0 | — |
| chance (8 shifted controls, 36 targets) | 0.12 expected | 0.0035/target |

- **Both detections are real counterparts** (NWAY p_any 0.9995 / 0.9786, seps 0.36″/3.35″,
  FLAG_OPT 0) and both are **EB26-SPURIOUS**:
  **5839182174066052224** (M3's cautionary object, reproduced: log f_X/f_opt = −2.43,
  the loud end of the coronal locus; 1-yr-alias flag; **in the v2 list**) and
  **6281177228434199296** (new: log f_X/f_opt = −3.29, sig 24.3 — class III on the AMRF
  plane but **already killed by the frozen F2 screen**, F2 = 8.05 at G = 11.3: the
  goodness-of-fit gate and the X-ray tag agree on it).
- Both are **soft** (HR2 = −0.32/−0.55, 0 hard-band matches anywhere) — coronal activity,
  nothing accreting among all 76. Both are DR1-detected too, stack/DR1 rate ratio ≈ 1.3
  (mild, active-star-variability-sized); **0 DR1-only faders**.
- Confound check: the two groups match in brightness and distance (median G 13.7 vs 12.9,
  d 638 vs 601 pc) — the 2-vs-0 split is not a reach-artifact.
- f_X/f_opt and hardness as discriminators: **untestable** — 0 confirmed detections to
  compare against (needs ≥ 3/side by the pre-registered rule).

**Statistics: Fisher exact two-sided p = 0.192.** NOT significant. **Power, computed
exactly** (binomial enumeration at the achieved n): against confirmed at 0/16, the
smallest spurious detection rate detectable at 80 % power is **≈ 0.40** — the observed
0.154 (CI 0.04–0.42) is *below* what this footprint and sample can establish.

> **VERDICT: UNDERPOWERED, direction consistent.** Every X-ray detection among the 76
> (2/2) is a spurious solution and no confirmed compact-object host is detected — the
> M3 reading ("X-ray = activity/spurious-risk tag") gains a second independent case and
> loses none, but a p = 0.19 effect is not a discriminator anyone may freeze.

**Config consequence: NO X-ray flag column enters the candidate list, and there is no
X-ray *selection* change in config v3.** The tag stays where M3 put it — in the eROSITA
xmatch artifact and the runbook's caution list — now with its evidence base measured. The
hypothetical *cut* was also measured and rejected (`scripts/m4_acceptance_and_queue.py`):
removing X-ray-matched rows would drop 30 of 949 — **0 EB26-confirmed, 1 EB26-spurious,
29 unverdicted** including the top NS-range active-binary candidates. Zero measured
purity gain; the epoch-vet loop stays the false-positive killer. Where the power will
come from on 2026-12-02: the epoch-vet loop itself adjudicates hundreds of candidates in
72 h — re-running this test with epoch-vet verdicts as ground truth is pre-wired into the
runbook's first-24h bulletin (match rate + direction vs today's DR3 baselines).

## 2. The dust-ambiguous dozen (task 2) — 9 resolved alive, 4 out of reach, 0 movements

**Counting correction first**: M3 reported **12** dust-ambiguous rows (originally-class-III
far stars that survive the Edenhofer floor but die under the SFD full column). The v2 list
actually carries **13** rows with `class_det_dust_upper ≠ 3` — the 13th
(3344044498533737216) is one of M3's six dust movers-IN, outside its "was class III"
accounting. All 13 are arbitrated here.

**The unit chain M3 refused to guess, now pinned from the papers** (local copies
`data/papers/1905.02734/`, `data/papers/1012.4804/`):

> **1 Bayestar19 unit ≡ E(gP1−rP1) = 0.901 mag** — Green, Schlafly, Finkbeiner et al.
> 2019 (ApJ 887, 93; arXiv:1905.02734), source line 399: *"requiring … that
> E(gP1 − rP1) = 0.901 mag when E = 1 mag. The latter choice puts our measure of
> reddening on a similar scale as SFD"*; extinction-vector table (src lines 331–338):
> R_gP1 = 3.518, R_rP1 = 2.617 (difference 0.901); explicit conversion
> E(g−r) = (0.901 mag)·E at src lines 1007–1009.
> **1 E(B−V)_SFD ≡ E(gP1−rP1) = 3.172 − 2.271 = 0.901 mag** — Schlafly & Finkbeiner
> 2011 (ApJ 737, 103; arXiv:1012.4804), Table 6 ("F99 Reddening in Different
> Bandpasses"), R_V = 3.1 column, rows PS1 g and PS1 r.
> ⇒ **1 Bayestar19 unit = 1.000 × E(B−V)_SFD**, exact in the colour the map measures —
> equality *by construction* (Green19 chose the normalization to match the SFD scale).
> Then A_V = 2.742 × E(B−V) (SF11 Table 6 Landolt V — the constant the M3 SFD tier
> already uses) and Gaia bands via the ZGR23-curve ratios: **the Bayestar19 value enters
> the re-triage through the same conversion as the SFD ceiling**, so the arbitration
> compares maps, not coefficient conventions. A_G per Bayestar19 unit = 2.243 (house).
> **Independent published cross-check chain**: EB26 itself used the Green19 map with
> A_G = 2.66·E(B−V), E(BP−RP) = 1.33·E(B−V) (arXiv:2608.06453 src lines 169–172, their
> Teff ≈ 6000 K convention) — 18 % steeper in A_G; **run in parallel; a movement verdict
> counts only if both chains agree** (they do, on every arbitrated row).

**Access landmine**: the Argonaut web API (`api/v2/bayestar2019/query`) returns
**HTTP 500 on both documented wire formats** (plain l/b and serialized-SkyCoord;
2026-08-18) — the remote route is dead. Local file instead:
`data/dustmaps/bayestar2019.h5` (Harvard Dataverse doi:10.7910/DVN/2EJ9TX, 0.73 GB,
**md5 ab815d2fd3068d1b81a1bd61fb18a722 verified**); reader = healpy-free replica of
dustmaps 1.0.14 `BayestarQuery` (multi-nside nested lookup, linear DM interpolation,
median of the 5 samples) on `astropy_healpix` (`scripts/m4_bayestar_dozen.py`).

**Arbitration** (policy: best estimate = max(B19 at the star's distance, Edenhofer
floor); `out/m4_bayestar_dozen.csv`):

| outcome | n | note |
|---|---|---|
| **SURVIVES class III** (both chains) | **9** | B19 column at the star ≈ the Edenhofer floor (5/9 even below it — map tension, clamped) and far below the SFD ceiling: for these low-\|b\| far sightlines **most of the SFD 2D column is background dust behind the star** — the upper bound was the pessimist |
| UNRESOLVED (dec < −30, outside B19) | 4 | 5547414810758429056, 5541388898616068224, 5984963087901124352, 5858664081383081600 — stay bracketed, now flagged `flag_dust_unresolved_south` in the queue |
| dies / chain-dependent | **0** | — |

All 9 arbitrated values are inside the pixels' reliable distance range
(`DM_reliable_max`). **Membership consequence: none — the v2 list (949 rows) stands
unchanged; no v3 candidate CSV is needed** (versioned-outputs law: the arbitration lives
in `m4_bayestar_dozen.csv`, `amrf_class3_candidates_v2.csv` is untouched).

## 3. Acceptance re-run and config v3

Because a config version is issued (even documentation-only), the acceptance was re-run
against the standing list (`scripts/m4_acceptance_and_queue.py`), and it gates the config
write:

- **Gaia BH1**: present, Pr(III|corr) = 1.0000, M₂_min = 12.81 — **PASS**
- **Gaia BH2**: present, Pr(III|corr) = 1.0000, M₂_min = 9.76 — **PASS**
- top-2 by M₂_min = BH1 + BH2 (and #3 is still the EB26-refuted spurious at Pr 1.0000)
- **EB26 operating point re-measured on the list: 39/42 confirmed kept, 7/23 spurious
  passed** — identical to M2's frozen numbers, as it must be (membership unchanged).

**`queries/dr4-triage-config.v3.json`** (v1 and v2 untouched on disk): selection, screen,
probability method, and membership **identical to v2**. v3 adds two measured policies:
`extinction_tier.d_gt_1250pc` now names the Bayestar19 arbitration (+ the full sourced
chain in `extinction_tier.bayestar19_chain`), and a new `xray_policy` block — caution
tag, never a flag-as-selection, never a cut, with the EB26 test numbers and the
rejected-cut measurement on record.

## 4. The day-one queue and the runbook (task 3)

**`out/epoch_vet_day1_queue.csv`** — the Phase-3 consumption format, built and rehearsed
on DR3: **981 rows = 949 v2 + the retrieval bin's 32 at Pr ≥ 0.999**, one ranking
(Pr(III|corr) desc, M₂_min tiebreak), carrying `queue_bin` and every caution flag
(1-yr alias 7, low-|b| 286, σ_TI² > 20 58, X-ray-active 30, EB26 verdict where known —
8 spurious total, dust-unresolved-south 4). Ranks 1–2 = BH1/BH2; rank 3 = the spurious
poster child (the loop's designed first kill); ranks 4–6 = **retrieval-bin members at
Pr = 1.0000 with M₂_min 2.9–3.6 that no one has ever epoch-vetted** — the freshest
objects in the queue. The retrieval-bin EB26-spurious 5593444799901901696 rides at
rank 240 (Pr 0.9999) — one more precise-wrong-orbit exhibit.

`DR4-DAY-RUNBOOK.md` updated: header → config v3; Phase 2 dust step gains the Bayestar19
arbitration (+ Argonaut-down warning); Phase 3 header points at the queue file; Phase 3
step 4 and the first-24h bulletin carry the M4 baselines (30/471 list match rate; EB26
2/13 vs 0/16 direction) and the epoch-vet-first routing for X-ray matches; the 72-h
section no longer double-counts the 32 (they are in the day-one queue). Rehearsed stage
timings unchanged (nothing in Phases 0–1 was touched); the one timing addition is the
~1 min Bayestar load inside the Phase-2 dust step.

## 5. Files

| artifact | what |
|---|---|
| `scripts/m4_eb26_erosita_test.py` | the discriminator test (pre-registered rules) → `out/m4_eb26_erosita_xmatch.csv` (per-target, all 76), `out/m4_eb26_discriminator_stats.txt` |
| `scripts/m4_bayestar_dozen.py` | sourced B19 chain + healpy-free local reader + arbitration → `out/m4_bayestar_dozen.csv` |
| `scripts/m4_acceptance_and_queue.py` | acceptance re-run (gates the config write) + hypothetical-cut measurement + queue build → `out/epoch_vet_day1_queue.csv`, `queries/dr4-triage-config.v3.json` |
| `data/dustmaps/bayestar2019.h5` | Bayestar19 (Dataverse doi:10.7910/DVN/2EJ9TX, md5-verified; gitignored) |
| `data/papers/1905.02734/`, `data/papers/1012.4804/` | Green+19 and SF11 LaTeX sources (the chain's citations) |
| `queries/dr4-triage-config.v3.json` | config v3 — selection/membership identical to v2; adds `bayestar19_chain` + `xray_policy` |

M2/M3 outputs untouched (`amrf_class3_candidates.csv`, `…_v2.csv`, config v1/v2 all
byte-identical to their milestones).

## 6. Corrections and new landmines

1. **M3's "12 dust-ambiguous rows" is corrected to 13** carried in v2: the mover-in
   3344044498533737216 also dies under the SFD ceiling but sat outside M3's
   was-class-III accounting. (All 13 arbitrated; §2.)
2. **M3's "retrieval bin … headed by the EB26 probable-NS at 0.9997" overstated its
   rank**: four retrieval-bin members sit at Pr = 1.0000 (M₂_min up to 3.56); the
   probable-NS is the bin's *headline identification*, not its Pr head — it rides at
   rank 276 of 981 in the combined queue.
3. **The Argonaut/Bayestar web API is dead** (HTTP 500 on both documented wire formats,
   2026-08-18) — any December plan that assumed remote dust queries must use the local
   `bayestar2019.h5`.
4. **dustmaps installs with `--no-deps` but its `bayestar` module imports healpy at
   module level** — only its serializers are usable on Windows; the local reader had to
   be replicated (done, ~90 lines, validated against the dustmaps interpolation logic
   read side-by-side).
5. The Bayestar19 h5 is **0.73 GB** (best_fit + 5 samples × 120 DM bins × 4.2 M pixels) —
   small enough to keep on disk permanently; no reason to ever depend on the web API.

## 7. Recommended M5

1. **The activity axis without the footprint penalty**: the X-ray test is
   footprint-starved (29 usable verdicts of 65). Gaia DR3 itself carries all-sky activity
   proxies — `astrophysical_parameters.activityindex_espcs` (Ca II IRT chromospheric
   index) and the photometric-variability tables — testable against **all 65** EB26
   verdicts today. If chromospheric activity discriminates where X-ray couldn't reach
   power, that is the day-one spurious-risk tier, and it needs no telescope.
2. **Southern dust closure**: the 4 unresolved rows sit inside the Vergely/Lallement 2022
   all-sky 3D volume (CDS J/A+A/664/A174, anonymous) — one sourced A0(550 nm) unit link
   away from closing the last dust ambiguity.
3. **Fold the queue into the rehearsal driver** (`rehearse_dr4_day.py` stage G → also
   emit `epoch_vet_day1_queue.csv`) so December 2 produces it mechanically, not manually.
4. Human TODOs unchanged: Gaia Archive + Data Lab accounts (Matthew).
