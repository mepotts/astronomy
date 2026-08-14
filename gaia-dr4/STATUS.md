# gaia-dr4 — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

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
