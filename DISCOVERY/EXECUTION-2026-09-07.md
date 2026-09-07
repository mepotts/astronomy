# Remaining experiments and actual discovery screen - September 7

Executed the three non-dated follow-ons from September 6, then a bounded unknown
search where controls permitted. **No new astronomical discovery was found.**
This closes these specific experiments, not every possible research programme.
Publication, registry submissions, messages and private-coordinate payloads remain
separately human-gated. Tested repository integration remains authorized.

| Front | Work actually executed | Result / decision |
|---|---|---|
| DASCH | Continuous-colour/series matching, six prospectively selected held-outs, signed injections, then two-field unknown screen | Four held-outs usable;16/16 eligible injections recovered;34 unmodified holdout windows without flags. All42 selected search sources usable;361 windows, zero leads. Close this fixed screen. |
| CCOR | Four retrospective image/PQF products, eight independently selected Hipparcos stars, training/held-out translation check and128 offset controls | Surviving held-out RMS0.29--0.45pixels, but training counts3/1/3/2 fail two frames. No motion search earned. |
| DR11 | Full DR10/11 footprint comparison, published-stream overlap, physical CCD verification, then six native image/ivar/mask products |8,468 qualifying bricks; first of two overlaps has six added r exposures.2,258 paired apertures improve empirical scatter only5.47%, short of the frozen10% gate. No new-stream search earned. |

Detailed scientific limits, exact requests and outcomes:
[DASCH](../dasch-pilot/RESULTS-2026-09-07.md),
[CCOR](../ccor-pilot/STARS-RESULTS-2026-09-07.md),
[DR11](../dr11-pilot/RESULTS-2026-09-07.md).

## What changed scientifically

DASCH moved from metadata feasibility to an actual exploratory search. The first
strict exposure join stopped on inconsistent metadata; a separately frozen
quarantine variant excluded conflicts before any held-out outcomes, leaving the
original stop intact. The matching method is deliberately conditional on observed
detections and supported colour response. It does not turn short SPSS stability
labels into century-long negative truth or estimate a population false-alarm rate.
The zero-lead search is not evidence that no new variables exist. All screened
identities and full results remain local/ignored; tracked output is aggregate only.

CCOR now has measured known-star pixels, not just header promises. Local celestial
geometry looks consistent, but the frozen recovery requirement genuinely failed.
No convenient star replacement, frame deletion, lower contrast threshold or
reporter-coordinate optimization was used to manufacture a pass. No comet claim.

DR11 now has a complete prospective qualifying-footprint array, not one failed
galaxy and a vague suggestion to look elsewhere. ESO197-018 really gains input
exposures, but local diffuse-light scatter improves only modestly. A published
stream location could not be fixed independently from the inspected material, so
the pixel test measures depth only and does not claim known-stream recovery.

## Remaining queue: explicit decisions

1. **Keep ITF daily operations running.** At 06:56 UTC September 7 the latest
   scheduled GitHub watch is September 6 run 34041245835, successful. September 7's
   08:30 ET publisher and later GitHub watch are not due yet; no stale/failure claim
   or competing publisher. A sandboxed scheduler-info read was denied; this turn
   does not claim a new local scheduler acceptance. Existing20-ready/6-held status
   is the September6 accepted result, not a new September7 measurement.
2. **Execute Dyson E only after September9 public release** under the existing
   frozen protocol. Gaia DR4 remains behind its planned December2 release/schema
   gates. No early E analysis or change to either experiment.
3. **Do not enlarge today's samples until something flags.** A larger DASCH
   campaign is possible, but it is a new sample/completeness/validation design,
   not a missing command in this completed screen. CCOR needs stronger independent
   training controls; DR11 needs an independently designed multi-field depth and
   upstream sky-subtraction completeness study. Neither failing pilot authorizes
   an unknown-object scan.
4. **Publication-ready work stays available, not auto-submitted.** PTA full paper
   remains the selected unit. eROSITA/SPHEREx remain deferred; TNS/Rubin and CHIME
   remain parked on their documented missing scientific inputs. No new deep-research
   phase is claimed and no assertion that every internet idea has been exhausted.

## Verification

- 34 DASCH, 28 CCOR, 9 DR11 tests pass, including 17 new tests. Original tests/stops
  remain active; CI now also cold-replays the public colour-control bundle.
- Public DASCH validation cold replay passed. Full local private search replay
  reproduces all 42 per-source outcomes and the identity-free summary exactly.
- Full-source DR11 footprint replay and full-pixel paired-depth replay passed.
  CI tests the compact footprint invariants and paired-result arithmetic; it does
  not redownload228MB catalogues or46MB image products.
- CCOR CI replays all 32 central known-star measurements from a 193 KB fixture;
  full FITS/PQF retain the negative-control source pixels locally. No Gaussian
  significance or full-image replay is implied by compact CI.
- [Executed acquisition/analysis source snapshot](evidence/executed-scripts-20260907.zip)
  preserves the versions used before adding replay CLI modes. Later changes add
  tests/replay paths and do not alter the measured statistics.

The actual remote CI/merge result is reported in the task handoff, not inferred
from local tests. No scientific submission, email, DOI, private-coordinate query,
account change, automation change or destructive operation occurred.
