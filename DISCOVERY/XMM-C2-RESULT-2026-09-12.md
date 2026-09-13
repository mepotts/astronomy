# XMM C2: real exposure and good-time values summarized

**ANCILLARY_VALUES_SUMMARIZED_UNCALIBRATED. No photons or discovery.**
The [protocol](XMM-C2-2026-09-12.md), implementation, 17 tests and
[independent GO review](XMM-C2-REVIEW.md) were committed as `61d7bee` before
one offline execution. Worker exit was zero, parent assessment completed,
and a separate read-only replay reproduced every table summary exactly.
No network request, new product, parameter adjustment or earlier-artifact edit.

## Measured result

| Camera | EXPOSU tables / rows | STDGTI tables / rows | Exposure-row quality flags |
| --- | ---: | ---: | --- |
| pn S003 | 12 / 7693686 | 12 / 564 | None under the declared checks |
| MOS1 S001 | 5 / 128045 | 5 / 114 | None under the declared checks |
| MOS2 S002 | 7 / 165171 | 7 / 155 | None under the declared checks |
| Total | 24 / 7986902 | 24 / 833 | All exposure rows valid and GTI members |

All 48 slots completed. GTI rows are finite, positive-length, ordered and
non-overlapping under the declared diagnostics. Exposure times are finite and
strictly increasing with no global duplicates; declared widths are finite and
positive, and fractions lie in [0,1]. Zero pn fractions remain valid measured
losses, not missing data. These checks establish numerical usability, not
calibration accuracy or a usable aperture.

Exactly **97029016 bytes** were read and interpreted per measurement pass:
97015688 EXPOSU and 13328 STDGTI. Parent verification and the explicit replay
each read the same selected payload again; this number is not aggregate disk
traffic across all integrity hashes and replays. No EVENTS, source-list,
bad-pixel or other forbidden array was interpreted.

Worker peak working set was **131837952 bytes**, parent **131719168 bytes**,
below the monitored 500000000-byte ceiling. Final aggregate JSON is
**162891 bytes**, below 1 MiB. The fixed helper enforced the 120-second worker
deadline. It is a monitored memory acceptance check, not an OS allocation cap.

## Scientific interpretation and next action

Full-frame TIMEDEL times FRACEXP sums are close to the matching EVENTS
LIVETInn values without any fitted scale: differences range from +0.047949
to +0.319368 s for pn, +7.989856 to +13.327628 s for MOS1, and +0.000014
to +16.025666 s for MOS2. Both unrestricted and GTI-timestamp-member sums
are retained and are equal here because every valid frame timestamp is a
member. That equality does not prove frame intervals are fully inside GTIs.

For pn central CCD4, the weighted sum is 40781.971896643 s versus EVENTS
LIVETI04 40781.923947308 s, while EXPOSU04's own LIVETIME is
47319.690470727 s. Those metadata are demonstrably different quantities;
do not renormalize away the distinction or apply another generic dead-time
factor. Remaining MOS differences must likewise remain visible rather than
being declared exact closure.

The [documentary semantics](XMM-EXPOSURE-SEMANTICS-2026-09-12.md) support
these frame weights as a candidate relative-exposure input. C2 does not
integrate finite frames at bin/GTI boundaries or establish spatial stability,
background validity, published-burst recovery or calibrated false positives.
The [interpretation note](XMM-C2-INTERPRETATION.md) records those distinctions.

Next adopt the [small geometry continuation](XMM-GEOMETRY-NEXT-2026-09-12.md):
exact-size checks for three already indexed per-camera exposure maps and one
attitude timeseries, then bounded acquisition/header inspection under a frozen
contract. Keep the fixed published-control apertures; do not optimize them
from photons. Actual map/attitude values and frame-boundary treatment must
have explicit tests before a counts-control can claim reliable exposure.
The [timing primitives review](XMM-TIMING-REVIEW.md) covers synthetic arithmetic
only, not an executed photon experiment. No unknown-source search is launched.

## Reproducibility

Run `dyson-revet/.venv/Scripts/python.exe -B
DISCOVERY/XMM-C2-2026-09-12-data/inspect_values.py replay` locally with the
unchanged ignored C1 inputs. Public CI runs synthetic tests and skips only
the actual-header-only manifest test when those local headers are absent.
The [postrun audit](XMM-C2-POSTRUN-REVIEW.md) checks retained artifact closure.

| Artifact | SHA-256 |
| --- | --- |
| Source | `357edd17ee84755011e9adb41ecf523063be9303501d060bbfc416ceecd23f68` |
| Tests | `358714cd6998d3a53bf579cfe99ff31fa5d9b5b3bae7c79f8d28b8b482075273` |
| Protocol snapshot | `ba74dd568f177de9f04042b34c9ac3cfac1ef3f9af6009fd66552370bc956f6a` |
| Run start | `1f4cf7af9ccce935acef668586d9b5083dff08af86c72dd2f23aa07afb22ada5` |
| Worker result | `b7f1d7b687fee20728c18fe8117a4d60e32d8e6dd3dd0c4e8de10590e2649e69` |
| Outcome | `bd69d5df9effd0a4097016a324f971467b4934b9ff048d1dd58eb17a1b8fff39` |

Repository pushes/merges are authorized after testing. Publication, submission
and private-coordinate disclosure remain gated. The discovery goal is active.
