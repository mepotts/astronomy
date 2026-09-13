# Independent XMM timing-primitives review

September 12, 2026. **Scoped GO for the arithmetic primitives on validated
inputs**, not approval of a real-data counts experiment. Reviewed current
`xmm_timing.py` and `test_xmm_timing.py` completely. No real photons, FITS
arrays or network access; only this review document was added by the reviewer.

## Checks and repairs

Eight author unittest methods pass, including exact small-count binomial tails,
zero counts, constant-efficiency cancellation, empty/unsorted event input,
half-open boundaries, unioned GTIs and reference-mask validation. Independently
rerun with `../dyson-revet/.venv/Scripts/python.exe -m unittest test_xmm_timing -v`
from `DISCOVERY`. Root-invoked Ruff 0.16.5 also passes for both files with
`check --no-cache`.

The first review found two input-validation gaps: malformed empty GTI arrays
were silently accepted, and boolean exposures were converted to seconds. The
parent repaired both and added cases to the existing eight test methods.
Current code accepts only the intentional empty representations `(0,)` and
`(0,2)`, rejects `(2,0)` and `(0,3)`, and rejects Python/NumPy boolean values in
either exposure argument. The full suite passes after these changes.

An additional **200 deterministic synthetic cases** passed both before and after
the fixes. These were inline review experiments, not 200 additional committed
unittest methods. NumPy `default_rng(7381)` generated ten increasing bins
(widths uniform 0.1–5), eight possibly overlapping intervals, 100 unsorted
timestamps plus every bin edge, and a random Boolean acceptance mask per case.
Separate scalar oracles checked:

- GTI coverage by partitioning each bin at every interval endpoint and summing
  segments whose midpoint belongs to any interval; tolerance 1e-12.
- Integer counts by direct `left <= time < right` enumeration, including the
  excluded final edge; in-range plus outside counts equal input length.
- Whole accepted reference bins by direct endpoint comparisons against the
  tested interval expanded by a random 0–10 exclusion. The tested bin cycled
  through all ten positions.

## Scientific meaning and remaining caller obligations

Half-open binning is correct, and overlapping/touching GTIs do not double-count
coverage. `wall_coverage` measures **GTI wall-clock seconds**, not detector
effective exposure. It does not apply GTIs to the timestamps supplied to
`half_open_counts`; the eventual caller must perform and verify the appropriate
event selection separately.

The reference mask includes whole accepted bins outside the fixed exclusion,
including bins that merely touch its outer boundaries without overlapping.
It does not enforce minimum reference exposure or decide whether the tested
bin is eligible; those remain explicit orchestration requirements.

The binomial survival function correctly conditions independent Poisson counts
on their sum under a common **total-aperture rate**, with positive fixed
exposures. This is not a background-subtracted intrinsic-source significance
or calibrated astrophysical false-alarm probability. Correct exposure ratios,
photon-independent acceptance/selection rules, source/background controls,
multiple-test accounting and detector geometry remain outside this helper.
No implementation here establishes quiet background or recovers a burst.

## Current reviewed bytes

| File | SHA-256 |
| --- | --- |
| `xmm_timing.py` | `2ca2433b09dfc00661e68c58c6750495f77186eb07c00674615aee7bddb9ca76` |
| `test_xmm_timing.py` | `7a92f552a8896d798c1bb423093f502c1235af9d7c8e6ffb72b0b35bbbfaac37` |

No remaining correctness blocker was found within this synthetic, bounded
review. These tests are not exhaustive numerical validation for arbitrary
floating-point extremes or an executed scientific recovery protocol.
