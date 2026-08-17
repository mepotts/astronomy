# pta-mpta — status log

*Newest first. Updated by the working agent each session; root [`../STATUS.md`](../STATUS.md)
carries the one-line summary.*

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
