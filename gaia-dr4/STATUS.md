# gaia-dr4 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-18** — **M4 done** ([`M4-xray-discriminator.md`](M4-xray-discriminator.md)):
  **(1) the activity-vs-spuriousness test** — all 76 EB26 targets × eROSITA-DE DR2+DR1
  with shifted controls (rules pre-registered): in-footprint detections **2/13 SPURIOUS
  vs 0/16 CONFIRMED** (+0/7 other verdicts; chance 0.12), both real counterparts
  (p_any ≥ 0.98), both coronal-soft, 0 hard-band, 0 accretors, 0 DR1-only faders —
  direction consistent with M3's n=1 (which reproduces as the loudest), but Fisher
  **p = 0.19: UNDERPOWERED** (only a spurious rate ≥ 0.40 was detectable at 80 % power
  on the half-sky footprint; observed 0.154). **No X-ray flag enters the config**; the
  hypothetical cut measured and rejected (drops 30 rows: 0 confirmed, 1 spurious, 29
  unverdicted). Bonus: the 2nd X-ray spurious (6281…) is class III but already killed by
  the frozen F2 screen — gate and tag agree. **(2) dust dozen** — the Bayestar19 chain
  M3 refused to guess is now paper-exact (Green19 line 399 + table: 1 unit =
  E(gP1−rP1) 0.901 = **1.000 × E(B−V)_SFD** by construction, SF11 Table 6 PS1 g−r;
  → 2.742 → ZGR23 ratios; EB26's 2.66/1.33 chain run in parallel): of the **13** (not
  12 — M3 count corrected, the 13th is a dust mover-in) ambiguous rows, **9 SURVIVE
  under both chains** (B19 ≈ Edenhofer floor ≪ SFD: the SFD ceiling was mostly
  background dust), 4 are south of the B19 footprint (stay bracketed + flagged),
  **0 movements → the v2 list stands, no v3 CSV**. Argonaut web API is DEAD (HTTP 500
  both formats) — local bayestar2019.h5 (0.73 GB, md5-pinned) + healpy-free reader.
  **(3) acceptance re-run PASS** (BH1/BH2 Pr 1.0000, top-2; EB26 operating point
  re-measured 39/42 + 7/23 identical) gating **config v3** (selection/membership
  identical to v2; adds `bayestar19_chain` + `xray_policy` caution-tag). **(4) day-one
  queue built**: `out/epoch_vet_day1_queue.csv` — 981 rows (949 v2 + retrieval bin's 32
  at Pr ≥ 0.999, incl. 4 never-vetted Pr = 1.0000 objects at M₂_min 2.9–3.6), all
  caution flags; runbook updated (v3 config, B19 arbitration step, queue pointer, M4
  baselines in the 24-h bulletin). M3's "retrieval bin headed by the probable-NS"
  corrected: it rides at rank 276; four bin members outrank it at Pr 1.0000. Human
  TODOs unchanged (accounts).
- **2026-08-16** — **M3 done** ([`M3-corrvec-rehearsal.md`](M3-corrvec-rehearsal.md)):
  the two M2 seams are closed and December 2 is rehearsed. **(1) corr_vec**: `nsstools`
  0.1.12 (PyPI, verified) rebuilds the full NSS covariance; validation vs S23's e_A goes
  from 2.27× overestimate to **median ratio 1.027** (the residual fat tail is confined to
  TI-degenerate solutions, marker = S23's own σ_TI² — the candidate list lives at median
  0.95, i.e. in the validated regime); the 951's **Pr≥99.9 % core doubles 147 → 293**,
  **0 dissolve** below 50 %, the retrieval bin yields 32 more at ≥ 99.9 % (headed by the
  EB26 probable-NS at 0.9997), BH1/BH2 = 1.0000/1.0000 — and a clean negative: **Pr
  thresholds don't improve the EB26 operating point** (precise wrong orbits have Pr ≈ 1;
  the frozen screen stands, Pr is a ranking tier in config **v2**, v1 untouched).
  **(2) dust tier**: Edenhofer23 3D (≤ 1.25 kpc, all-sky, healpy-free reader) + far-star
  Edenhofer-floor/SFD bracketing (Bayestar rejected: unsourced Gaia-band chain; the 12
  dust-ambiguous rows are counted instead); only 91 of the 270 flagged are even movable
  (179 are binary_masses-tier) — **8 out / 6 in** at best estimate → **v2 list = 949**
  (one knife-edge entrant honestly at Pr 0.495); top-3 unchanged (BH1 12.81, BH2 9.76,
  then the EB26-refuted spurious at Pr 1.0000 — still the epoch-vet poster child).
  **(3) rehearsal**: schema-pin → rename-patch (live-probed) → plan-B ranged pull re-run
  in full (38.7 min, **byte-identical sha256 to the M2 production pull**; the raw ranges
  over-count by exactly the histogram wobble + the bm fan-out and the guard chain
  assembles 169,227 on the nose) → triage acceptance **PASS** (BH1+BH2, 65 s) →
  epoch-vet **PASS** (3/3 keep, 9/9 demote) → bulletin; **40 min end-to-end**, timings in
  `out/rehearsal_timings.csv`; the operational playbook is **`DR4-DAY-RUNBOOK.md`**.
  **(4) eROSITA join** (471 of 949 in-footprint): **30 X-ray counterparts vs 1.38
  chance** (8 shifted controls), 0 hard-band, all in the coronal f_X/f_opt locus
  (−4.3…−1.2) — **no accretor found** down to a median L_X reach 3.8×10²⁹ erg/s; the
  X-ray-loudest-relative match is the EB26-refuted 1-yr-alias spurious (p_any 0.9995):
  on this sample X-ray = activity/spurious-risk tag, not compact-companion evidence.
  New landmines: VOTable `SOURCE_ID` upper-casing; duplicate `GDR3_source_id` column in
  eRASSc3; dustmaps' wrong ZGR23-curve DOI; sfdmap2's silent 0.86 rescale; healpy has no
  Windows build. Human TODOs unchanged (accounts).
- **2026-08-16** — **M2 done** ([`M2-amrf-triage.md`](M2-amrf-triage.md)): the AMRF triage
  exists, is validated, and its DR4 config is frozen (`queries/dr4-triage-config.json`).
  **Acceptance PASS on the first end-to-end run**: BH1 class III (𝒜 = 2.265, margin 3.38×,
  M₂_min = 12.81 M☉), BH2 class III via the evolved-primary bracket (worst-case margin
  2.44×, M₂_min ≥ 9.76) — the two designed-around landmines were S23's P < 1000 d cut
  (BH2 is at 1352 d) and MS-only M₁ (BH2's primary is a giant **and has no binary_masses
  row**). Implementation = S23 digit-for-digit (𝒜 ratio 1.0000 on every shared source;
  177/177 of their class-III recovered at the frozen boundary). Calibration vs El-Badry
  2026's follow-up verdicts (42 confirmed / 23 spurious): frozen config keeps **39/42
  (92.9%)** and passes **7/23 (30.4%)** spurious; the strictest screen (significance > 20)
  would have rejected **Gaia BH1 itself** (sig 13.6) — frozen at 10 with the tradeoff
  table on record. DR3-wide yield: **951 class-III solutions** (147 also at MC
  Pr(III) ≥ 99.9% — the S23-comparable core; 270 low-|b| extinction-flagged) + a 239-row
  low-significance retrieval bin; ranked by M₂_min the list's top two are BH1 and BH2, and
  #3 is a known EB26-refuted spurious at significance 76 — the epoch-vet loop's poster
  child. Stretch PASS: the epoch-vetting loop on the pre-release file keeps exactly the
  3 orbit sources (f2 894/187/32) and demotes all 9 quiet ones — the DR4-day
  false-positive killer works end-to-end. **M1 correction**: the "BH3 renumbered DR3→DR4"
  claim is REFUTED (Panuzzo prints `...000`; all 12 pre-release ids are unchanged DR3 ids;
  crosswalk stays as insurance). New landmines: **source_id is a key in neither
  `nss_two_body_orbit` (98 sources carry two astrometric solutions) nor `binary_masses`
  (join fans out +76)**, and ADQL bucket arithmetic on source_id rounds in double
  precision past 2^53. Operational: the anonymous async queue sat >100 min on two jobs;
  the range-partitioned sync fallback (`scripts/pull_dr3_nss_orbits_ranged.py`: 3-s bucket
  histogram + 94 indexed range pulls, exact-count-guarded) delivered the 169,227-row pull
  in ~35 min — assume the queue is worse on 2026-12-02. Human TODOs unchanged (accounts).
- **2026-08-14** — **M1 done** ([`M1-prerelease.md`](M1-prerelease.md)): all four pre-release
  claims CONFIRMED (release 2026-12-02; 12-source epoch-astrometry sample of 2026-06-26; official
  package = `gaiasupdate` 0.1.2 on PyPI; draft data model = 1231-pp PDF). ESA tooling runs
  end-to-end on Windows: 12/12 single-star fits, and the BH3 orbital refit reproduces the
  published orbit (P 11.45 vs 11.6 yr, e 0.728 vs 0.729, M2 34.7 vs 32.70±0.82 M☉) —
  `out/*.png`. Three day-one ADQL queries drafted in `queries/` and their DR3 twins validated on
  anonymous TAP (all HTTP 200); rename map in `queries/dr3-to-dr4-tables.md`. W2 fixtures pulled:
  BH1/BH2 DR3 NSS + gaia_source rows in `fixtures/`. Landmines found: DR4 `epoch_astrometry` is
  **DataLink-only** (no TAP joins), and **source_ids are not stable DR3→DR4** (BH3 renumbered in
  the pre-release file) — resolve via `dr3_neighbourhood`. Next: M2 = AMRF triage, acceptance =
  recover BH1+BH2 (note BH2 is `AstroSpectroSB1`, not `Orbital`). Human TODOs still open:
  Gaia Archive + Data Lab accounts (Matthew).
- **2026-08-14** — Folder created from run-3 avenue #4. First agent launched: W1 (verify +
  install pre-release sample and official fitting package, run a demo fit) and W3 (draft the
  day-one ADQL, syntax-validated on DR3 via anonymous TAP). W2 acceptance target on record:
  recover Gaia BH1/BH2 from DR3 NSS before December. Human TODOs open: Gaia Archive +
  Data Lab accounts (see README).
