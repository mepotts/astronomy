# gaia-dr4 — be ready on December 2

**What this is.** Avenue **#4** of [`../DISCOVERY/run3-prospectus.md`](../DISCOVERY/run3-prospectus.md):
Gaia DR4 releases **2026-12-02** ([official date](https://www.cosmos.esa.int/web/gaia/release)) —
epoch astrometry for ~2B sources, a greatly expanded non-single-star (NSS) catalog, the first Gaia
exoplanet list. Nobody gets proprietary access, so the first-weeks papers go to whoever shows up
with a **validated pipeline and credible false-positive triage** — which is this repo's specialty.
ESA published pre-release epoch-astrometry samples and an official Python fitting package
(~Jun 2026, per the [DR4 page](https://www.cosmos.esa.int/web/gaia/dr4)) — that claim is verified
as workstream W1's first act.

**Relationship to the build idea.** [`../IDEAS/gaia-dr4-diff-auditor.md`](../IDEAS/gaia-dr4-diff-auditor.md)
is the *tool* on this drop; this folder is the *discovery axis*. They share plumbing (schema maps,
canned ADQL, TAP client) — build once, use twice.

## Workstreams

- **W1 — epoch-astrometry fitting on the pre-release.** Verify the sample + official package
  exist as described; install; fit a single-star and (if the package supports it) an orbital
  solution end-to-end on sample data. Acceptance: a reproduced fit with plots, committed.
- **W2 — NSS compact-companion triage, validated on DR3.** Implement the triage cut
  (AMRF-style + the lessons of arXiv:2608.06453: ~40–50% of DR3 candidates were spurious);
  acceptance: **recover Gaia BH1 and BH2 from DR3 NSS with the same cut** before DR4 exists.
- **W3 — canned day-one ADQL.** Draft the queries against the published draft DR4 data model
  (NSS compact-companion cut, 6D hypervelocity cut, microlensing-prediction inputs, epoch-data
  fetches for named targets — including the exosat-rv companion hosts). Validate syntax on DR3
  equivalents via anonymous TAP now; keep a table-name mapping file to patch on release day.
- **W4 — microlensing-prediction refresh (later).** Two-group field, prediction itself publishes;
  starts after W1–W3 are green.
- **W5 — HVS 6D rerun (release week).** Marchetti-style cuts parameterized for DR4; epoch
  astrometry as the spurious-solution killer.

## Human tasks (agents must not do these)

- [ ] Gaia Archive account (free — lifts row limits, enables server-side user tables): Matthew.
- [ ] NOIRLab Astro Data Lab account (free — `mydb` + billion-row crossmatch): Matthew.

## Conventions

Same as repo law: results docs `M<N>-*.md`, dated, sourced-or-UNSOURCED; `STATUS.md` is the live
log; bulk data in `data/` (gitignored), venv in `.venv/`; committed scripts are Python with LF
endings; anonymous TAP queries stay small and polite (sync 2,000-row/60 s cap — window or async
for anything bigger); no submissions or accounts created by agents.

## The calendar this folder answers to

| Date | Event |
|---|---|
| now → Nov | W1–W3 built and validated on pre-release + DR3 |
| **2026-12-02** | DR4 lands — run W3 queries, W2 triage, W5 HVS; start the [`../erosita-dr2/`](../erosita-dr2/) × NSS join |
| Dec–Feb | Candidate vetting → whatever survives becomes the first paper target |
