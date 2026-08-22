# pta-mpta — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

- **2026-08-21** — **M3 in progress → reported** ([`M3-noise-criticism.md`](M3-noise-criticism.md)).
  **The all-83 campaign is 48/83 gated and agrees with the published table on 296 of 299
  parameters (99.0%), 46 of 48 pulsars in full** — including 9 chromatic Gaussian events, 4 annual
  chromatic terms, 7 free-β chromatic GPs, 21 DM GPs and 10 free red processes, all rebuilt from
  public data. **The mode-vs-model diagnostic was run on every gated pulsar, not just the misses:
  ΔlnL(ours − published) median +0.40, 45 positive / 3 negative, range −0.67 to +8.56** — our
  sampler never under-performs the published solution anywhere, and the largest ΔlnL values sit on
  pulsars that agree on everything (the diagnostic's noise floor).
  **All 3 misses are the same parameter, γ_SW, on the 2 pulsars whose published value is NEGATIVE
  and therefore outside the prior we declared.** Root cause found and measured: the paper tabulates
  **no prior ranges at all**, M1's blanket γ ~ U(0,7) was applied to the solar-wind GP, and
  **enterprise_extensions' own `solar_wind_block` defaults to γ_SW ~ U(−2,1)** — so **7 of 26
  tabulated γ_SW values (27%) cannot be reached by a good-faith reproducer** (19 of 26 affected once
  interval-crossings are counted). A declared post-hoc rerun with γ_SW ~ U(−4,4) turns J1327-0755
  from **3/5 to 5/5**. **Table audit (no sampling): 26 of 588 published values (4.4%, 22 pulsars)
  have a MAP outside their own printed 68% interval** — 13 of them in the A_13/3 column, 5 of 20 in
  E_Q, zero in every non-amplitude column — **and 66 of 83 A_13/3 rows are bounded by the prior**
  (68% interval reaching below −16.5, the paper's own "clearly disfavoured" point); only **6** are
  constrained to better than 0.7 dex. **Seam (a): the A–β ridge is universal** (median r = −0.90,
  slope −0.21 dex per unit β) **but only 2 of 9 free-β pulsars are prior-driven** — J0437-4715
  (A_Chrom moves 0.38 dex, and its A_13/3 0.17 dex, under a U(0,7) β prior) and J1802-2124.
  **This corrects M2: J1017-7156 is data-driven, not the prior finding M2 called it** (0.00 dex
  under every alternative prior). Exploratory bonus: the amplitude–β covariance vanishes at a
  **reference frequency of ~855 MHz, not the tabulated 1400** — re-quoting there halves the
  amplitude uncertainty (0.46 → 0.21 dex) for free. **Seam (b): real, one-directional, and smaller
  than M2 thought.** With a proper whites-fixed control isolating the added red process, Δ(A_13/3)
  has median −0.03 dex, range −0.77 to +0.12, **8 of 26 above the 6-pulsar null control's 0.144 dex
  threshold, 18 of 26 moving DOWN**; the two biggest movers (J1721-2457, J1547-5709) are among the
  six best-constrained rows in the table. **M2's "J1600's A_13/3 drops 1.3 dex" is withdrawn** — it
  was confounded by simultaneously fixing the white noise. **CURN: FL product −14.30 (36 psr, `fl`
  config) and −14.18 (33 psr, `table` config), both consistent with the published −14.28 ± 0.21;
  on the 32 pulsars gated in both, ΔMAP = +0.14 dex** — inside the published 1σ, but flagged
  significant by the pre-registered exclusion clause, and **the real effect is the width**:
  [−14.63,−14.12] → [−16.85,−14.31]. Adding the collaboration's own mitigation costs sensitivity,
  and this is a number for that cost. **83-pulsar FL NOT reached** (coverage 48/83).
  **A1 extended to all 83: 82/83 PASS**; the 63 pulsars whose release is internally complete match
  tempo2's own TRES to a median of **0.02%**, and every material discrepancy traces to the 20 that
  ship fewer ToAs than their par fitted. Three ephemeris defects found: 8 pars miss their own TRES
  until one WLS refit (7 recovered), **J1825-0319 ships an unphysical negative Shapiro amplitude**
  (H3 = −2.98e−7 s ⇒ M2 < 0; PINT refuses to build it), `TRACK -2` confirmed inert array-wide.
  Economics corrected: **86 CPU-hours** so far; the binding cost is not the likelihood but the
  **absolute** stability tolerance applied to 3-dex-wide prior-limited posteriors (a relative rule
  would have passed 52 rather than 48). **Venue: bar NOT yet cleared** — coverage fails, the CURN
  result is a width not a shift; the table audit alone is an RNAAS-sized, finished product.
  **M4 rec: finish the array (60–100 more core-hours), register the relative gate, run γ_SW wide as
  a registered variant, then write up.** No commits, no accounts, no submissions.

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
