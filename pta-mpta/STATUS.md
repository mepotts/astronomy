# pta-mpta — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-18** — **M2 complete** ([`M2-converge-scale.md`](M2-converge-scale.md)).
  **J1909-3744 CONVERGED 9/9** — and *both blind chains found the mode unaided* (the informed
  chain, started at the published MAP, only confirms it stays and mixes); M1's ΔlnL = +22.4
  shortfall closed by sampler machinery alone (per-signal jump groups + per-block prior draws +
  an enforced wall-clock budget), likelihood untouched (digit-identical lnL at the reference
  point). All three chains beat the published MAP's own likelihood (97,308.3 vs 97,306.1); the
  chromatic block lands dead-on (A_DM −13.600 vs −13.60; n_earth 4.94 vs 4.96).
  **Top-10 campaign: 10/10 cleared the gate, 9/10 full agreement, 76/78 parameters agree** —
  including every hard structure (free-β chromatic GPs, two chromatic Gaussian events, an annual
  chromatic term). The only miss, J1017-7156's chromatic A–γ pair, is diagnosed the M1 way and
  is **the mirror of M1's case: our likelihood prefers OUR point by ΔlnL = +4.8** → a
  prior/convention finding on a flat A–β ridge, not a sampling failure, and far too small to
  contradict the table. **Factorised-likelihood CURN (10 psr): log10 A_CURN = −14.46 MAP /
  −14.53 median [−14.92, −14.31] — consistent with the published 83-psr −14.28 ± 0.21**;
  no detection/evidence claim (γ fixed at 13/3, no HD/CW). **Near-miss caught:** a frozen chain
  (acceptance 0.016) *passed* the pre-registered gate — not moving is maximally "stable" — and
  would have published −14.95 [−16.47, −14.54], flagged inconsistent; rerun at a tighter jump
  scale gave 0.189 acceptance and the number above. All 23 runs audited (others 0.167–0.489); the
  gate now carries an acceptance floor. **Harness hardened and proven:** wall-clock chunking,
  checkpoint/resume (six runs recovered from mid-flight kills), summary-on-every-exit, nice-19 +
  thread pinning, manifest inventory. **Three environment/library defects found and fixed:** an
  **enterprise 3.5.0 bug** (varying-basis params zero the GP prior matrix → guaranteed crash when
  sampling a chromatic index), e_e 3.0.3 jump proposals broken under numpy 2, and WSL killing
  detached campaigns (two layers). A1 extended to all top-10: 10/10 PASS (J0437's tempo2-`T2`
  binary and 12 pars' inert `TRACK -2` cleared). **Economics remeasured: M1's J1909 eval was 4.5×
  pessimistic** (97 ms 1-thread / 43 ms 4-thread, not 436 ms) → all-83 noise campaign is an
  overnight job; full-array CURN 2.5–5 d. **M3 rec:** cross-PTA noise criticism (the two seams M2
  exposed) → all-83 campaign → 83-pulsar FL → full-PTA CURN; CW/HD still behind the sparse stack.
  No commits, no accounts, no submissions.

- **2026-08-16/17** — **M1 complete** ([`M1-access-reproduction.md`](M1-access-reproduction.md)).
  **W1a access: PASSED** — the 4.5-yr release is fully public, account-free at Data Central
  (DOI 10.57891/j0vh-5g31): 83 par + 83 tim (245,907 sub-banded ToAs, 32-ch), 10,014 epoch
  PSRFITS archives (85 psr incl. 2 profile-only extras), 83 portraits; **no noise/common-signal
  chains ship at all** (the "anisotropy supplement" is 9 MP4 movies) → chain-level lanes are
  MPTA-dead, likelihood-level lanes are wide open; no license stated. **W1b stack: BUILT** in WSL
  without sudo (PINT 1.1.6 + enterprise 3.5.0 via --no-deps + loud-failure sksparse shim +
  e_e 3.0.3 + PTMCMC; WSL root disk was 100% full → venv on /mnt/c). **A1 PASS:** PINT weighted
  RMS matches tempo2's in-release TRES to +0.35% (J1909-3744) / +0.51% (J2241-5236). **W2
  (pre-registered): J2241-5236 5/5 parameters agree** with the published noise table (posterior
  widths match nearly edge-for-edge; SW conventions validated); **J1909-3744 5/9** — whites +
  A_13/3 dead-on (-14.288 vs -14.28), the chromatic DM↔SW block stuck in a local mode, and the
  post-run diagnostic shows our own likelihood prefers the published solution by ΔlnL = +22 →
  sampling shortfall, not model error; both formally land the pre-registered A3 feasibility
  verdict (chains under the sample gate; host ran a game at 100% CPU most of the session).
  **Economics measured:** fixed-white eval 1.4 ms (64× cheaper than free-white) → full-83 CURN
  ~1.3 d/1M iters, no sksparse needed; all-83 noise campaign ~1 day wall at 16-way parallel; CW/HD
  needs the sparse-stack upgrade first. **Recommended M2:** converge J1909 + scale to top-10 +
  factorised-likelihood CURN amplitude; W3 = cross-PTA noise criticism first, full-array CURN
  campaign second, CW/HD deferred. Data 1.25 GiB in `data/` (gitignored); scripts LF,
  committed-ready; no commits made (Matthew's call), no accounts, no submissions.
