# erosita-dr2 — compact objects and variables in the public X-ray sky

Current status: the bounded vanished-source census is closed for a publication
decision; see [the September 5 corrections and package](PUBLICATION-CLOSEOUT-2026-09-05.md).

**What this is.** Avenue **#5** of [`../DISCOVERY/run3-prospectus.md`](../DISCOVERY/run3-prospectus.md):
eROSITA-DE **DR2** (released **2026-07-31**, eRASS1–3 stacked, ~2M sources, no account needed —
[erosita.mpe.mpg.de/dr2](https://erosita.mpe.mpg.de/dr2/), survey paper arXiv:2607.27772) is the
public cumulative X-ray catalogue used here for a bounded cross-match census.
Novelty must be established for the exact surviving analysis, not inferred from release age.

**Why now.** Every DR1×Gaia selection can be redone at DR2 depth; DR1→DR2 flux comparison via the
consortium's `UID_DR1` cross-walk opens an X-ray variability axis (M1 correction: DR2 is
catalogue-only with *stacked* eRASS:3 values — no per-eRASS epoch columns; the original premise
here was wrong); and on **2026-12-02** Gaia DR4's
non-single-star orbits arrive — X-ray-detected astrometric binaries (dormant compact objects) is a
hunt nobody can start before that date. Building the ingest now means running the join that morning.

## Workstreams

- **W1 — inventory & access (M0 kill checks).** What DR2 actually ships: main/hard/supplementary
  catalogs, per-eRASS fluxes or not, value-added products, versions, sizes, TAP availability vs
  bulk FITS. *Also feeds the [`../IDEAS/erosita-source-classifier.md`](../IDEAS/erosita-source-classifier.md)
  DR2 rebase — same inventory, shared ingest.*
- **W2 — variability slice.** DR1↔DR2 (or intra-DR2 per-eRASS) flux ratios; rank strong variables;
  quantify the comparison's systematics honestly (aperture, likelihood cuts, position matching)
  before believing any single object.
- **W3 — classes via cross-match.** Top variables and outliers × Gaia DR3 (parallax/PM → Galactic;
  BP−RP/absolute-G locus) × ZTF light curves where useful. Candidate classes: CVs/accreting
  binaries, TDE/changing-look candidates, flare stars.
- **W4 — the December join.** DR2 × Gaia DR4 NSS orbits, day one. Prepared here, executed in
  [`../gaia-dr4/`](../gaia-dr4/) coordination.

## Conventions

- Results docs are `M<N>-*.md`, dated, every externally-sourced number carries a source URL or the
  mark UNSOURCED (repo law, exosat-rv LESSONS §5b). Negative results are results.
- `STATUS.md` here is the live log — the working agent updates it; the root
  [`../STATUS.md`](../STATUS.md) row is maintained by the orchestrator.
- Bulk data lives in `data/` (gitignored); committed outputs stay small (candidate CSVs < ~1 MB).
- Python work in `.venv/` (gitignored); scripts are committed Python files with LF endings — no
  ad-hoc shell one-liners (CRLF trap, LESSONS §5).
- No claims leave this folder (papers, posts, submissions) without Matthew's approval.

## Kill checks (from the run-3 avenue + IDEAS rebase)

1. DR2 catalogs actually downloadable + documented columns support a flux-ratio comparison
   (if per-eRASS fluxes are absent and DR1 matching is dominated by systematics, W2 shrinks).
2. Nobody shipped the same variability sweep in the DR2 flagship papers (check the release's
   paper list before claiming novelty).
