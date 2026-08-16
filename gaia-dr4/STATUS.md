# gaia-dr4 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

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
