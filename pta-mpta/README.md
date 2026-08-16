# pta-mpta — independent analyses of the MeerKAT Pulsar Timing Array's public data

**What this is.** Avenue **#2** of [`../DISCOVERY/run3-prospectus.md`](../DISCOVERY/run3-prospectus.md):
the MPTA 4.5-yr release (83 millisecond pulsars, the most sensitive PTA;
[mpta-gw.github.io](https://mpta-gw.github.io/), [arXiv:2412.01148](https://arxiv.org/pdf/2412.01148))
is public and barely exploited outside the collaboration. Open, publishable outsider lanes:
independent continuous-wave/single-source searches, cross-PTA noise-model criticism, and
new-physics constraints on public free-spectrum chains. IPTA DR3 (~2027) is the payoff event a
validated independent pipeline should be waiting for.

**Honest scoping note.** The portfolio's `pta-explainer/` is a *pedagogy* site (real Hellings–Downs
physics in TypeScript) — it is **not** a timing-analysis pipeline. This front builds the analysis
stack from standard public tooling (PINT/tempo2, enterprise, enterprise_extensions), with every
capability claim earned by a reproduction against the collaboration's published numbers before any
"independent search" is attempted.

## Workstreams

- **W1 — access + environment (M1 kill checks).** Verify what the MPTA release actually ships
  (TOAs? par files? noise chains? DM series?), that it downloads account-free, and that the
  standard stack runs on this machine (WSL expected; tempo2 install is the classic blocker —
  document whatever it takes). Kill check: if the released products can't support an independent
  likelihood (e.g., TOAs withheld), this front pivots to chain-level work or dies — say so.
- **W2 — reproduction slice (M1 acceptance).** Pre-registered: reproduce a published MPTA result
  at defensible scale — per-pulsar noise values or the common-signal posterior on a best-timed
  subset — and state plainly what subset-scale does and doesn't establish.
- **W3 — the first independent product.** Candidates (pick after W2, with runtime measurements in
  hand): a CW upper-limit map on the full array, a cross-PTA noise-consistency study, or
  free-spectrum new-physics constraints. Publishability standard: RNAAS/short-paper grade with
  every number reproducible from committed scripts.
- **W4 — IPTA DR3 readiness.** Whatever W3 builds, parameterized so the ~2027 combination drops in.

## Conventions

Repo law applies: results docs `M<N>-*.md`, dated, sourced-or-UNSOURCED; `STATUS.md` newest-first;
bulk data in `data/` (gitignored), envs in `.venv/`/WSL (gitignored); committed scripts LF; no
accounts, no submissions, no pushes by agents; blockers are findings, not failures.
