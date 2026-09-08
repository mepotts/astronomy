# Real-event transfer test - September 8

Prospective internal protocol, before these three DR7 catalogue queries or light
curves. This is a new validation experiment, not an enlargement of September 7's
closed 42-source screen. No new object, publication, or population rate is sought
from the controls themselves. Freeze the protocol and executed source hashes.

## Question and independent labels

Can the unchanged September 7 matched-colour detector and catalogue selection
recover real, published long-duration dimming, rather than only artificial
five-year magnitude offsets conditional on existing detections?

Use **all three**, without replacement, from Tang et al. (2010), ApJL 710 L77,
[primary paper](https://hea-www.harvard.edu/DASCH/papers/apjl_710_1_77.pdf),
[arXiv record](https://arxiv.org/abs/1001.1395). Section 2.2, Figure 1 on L78,
and Table 1 on L79 were read, including visual inspection of the latter two pages.
The public coordinate names define J2000 query centres; no fitted positions.

| Published name | RA degrees | Dec degrees | Positive (fainter) five-year window starts eligible for recovery credit |
|---|---:|---:|---|
| J083038.5+140713 | 127.66041666666666 | 14.120277777777778 | 1965, 1970, 1975, 1980, 1985 |
| J075445.9+164141 | 118.69125 | 16.69472222222222 | 1930, 1935 |
| J073606.5+211411 | 114.02708333333334 | 21.23638888888889 | 1930, 1935, 1940, 1945, 1950 |

These broad intervals are literature-defined tests, not new fits to DR7. Do not
equate the old GSC B-R colours with the DR7 APASS colour. Photometric systems and
reductions differ; failure here would not invalidate the original paper. These
are three selected positive examples sharing an original survey, not a random
population sample, independent instruments, or false-positive controls.

## Acquisition and analysis

- Exactly one APASS `querycat` (30 arcsec box half-width) per named position.
  Accept only the unique match within 5 arcsec, as in the prior controls. No
  widening, blending entries, proper-motion fitting, or replacement after outcomes.
- For each unique match retrieve its light curve and its own `queryexps` list
  at the published centre. At most nine sequential request attempts, <=16 MiB
  each, 30-second socket timeout, >=1 second between calls. No automatic retries.
  Every attempt is recorded before network; failures stop, never become zero rows.
  Reuse only request-bound, byte/hash-verified cached successes. Offline replay
  must never contact the service. No credentials or private target payloads.
- Enforce catalogue/detection-count and row-source accounting using `summarize`.
  Reject duplicate clean imaging keys within each light curve rather than count
  them as independent evidence. Use unchanged `joined(..., quarantine=True)` and
  `window` from September 7: same series, colour tolerance, baseline exclusion,
  0.5-mag two-series criterion, 1880..1985 five-year start grid.
- Original source coverage requirements remain: >=100 joined clean detections,
  >=30-year span, <=2% exposure-number conflicts, >=1 eligible window. Keep
  missing support separate from an eligible non-recovery.
- Report original catalogue membership separately: B=9..13.5, APASS colour
  -0.3..1.5, >=500 catalogue matches, `v_flag=mag_flag=0`. The old field-centre
  exclusion/rank cap is irrelevant to explicitly named public controls. Retrieve
  excluded controls too, **for diagnosis only**, never count them as recovered by
  the full search selection.
- Recovery requires a positive flag in a listed event window and source coverage.
  Report any-window flags separately; wrong epochs or signs earn no credit.

## Diagnostic sensitivity, not a second chance at a pass

For every successfully joined star also record unchanged-detector responses to
the existing +1 mag injection in 1950..1955, and +1 mag rectangular 20-year
injections in 1930..1950 and 1950..1970, evaluated at every five-year window wholly
inside the injected interval. This tests baseline contamination by sustained
events at actual sampling/colour support. Existing physical variability remains
in these curves; report unmodified flags beside injections. The injections do
not count towards real-event recovery and are not population completeness.

## Fixed decision and next step

Require **at least two of the three** published objects to recover their specified
events AND meet the original catalogue/coverage cuts to return
`PASS_REAL_EVENT_TRANSFER_ONLY`. Even then a broader unknown campaign needs its
own fixed sample, false-alarm/near-neighbour controls and image/novelty vetting.
Otherwise `STOP_REAL_EVENT_TRANSFER`: do not scale this detector or weaken its
thresholds in this experiment. Diagnose catalogue exclusion, insufficient
support, or eligible non-recovery explicitly. No claim that a failed detector
means an absence of astrophysical events. Keep the earlier 16/16 injections and
42-source null unchanged, with their narrower interpretation.

Track the public known-control responses, manifests and complete results. Keep
the copyrighted paper local (SHA256
`7abea24ec36ba99c50aeddc9dbc009bb2fff868dc380c82db6b64175593f274b`).
No unknown search, candidate query, scheduler change or outward scientific action
is part of this test.
