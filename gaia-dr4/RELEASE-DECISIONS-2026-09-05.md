# Gaia DR4 release readiness and exact decision gate — 2026-09-05

## State

**Ready for release; scientific labels still have a recorded human gate.** The
September 2 nine-stage rehearsal passed; rerunning it every day would not create DR4
data. The [Cambridge DPAC team](https://camcead.ast.cam.ac.uk/project_gaia), checked
September 5, still names **2 December 2026** as the planned release. The ESA release
page was not retrievable in this check; this is a second primary team's confirmation,
not a claim of a new ESA response. Recheck ESA's calendar and the actual TAP schema
before the release-day run.

The current user authorization covers execution and tested repository integration.
It does **not** silently amend the explicitly Matthew-frozen
[registration](PREREG-2026-08-23-december-discriminators.md). No frozen rule, sample,
family, configuration, original artifact, or verdict-label implementation was changed.

## Proposed decisions, not adopted amendments

These make the existing [M8 §3c](M8-inflation-zeropoint-rehearsal.md) questions concrete.
Approval must identify the chosen text, and the subsequent implementation must preserve
the original primary output and identify the dated variant wherever reported.

| Issue | Recommended wording for a declared variant | Consequence |
|---|---|---|
| GAP-1: significant, expected direction, insufficient design power | Report `SIGNIFICANT, EXPECTED DIRECTION; NOT DESIGN-DECISIVE`, retaining adjusted p, effect, and power. Do not make significance itself satisfy the power condition. | Completes the vocabulary without retroactively upgrading the sample. |
| GAP-2: nonsignificant pooled secondary | Report `POOLED: UNINTERPRETABLE`; never describe it as a null. | Makes §5 consistent with the more specific §2.2. |
| GAP-3: significant pooled reversal | Report the estimate as a secondary diagnostic, `POOLED REVERSAL: NOT INTERPRETABLE AS A FINDING`; do not substitute it for the scope-pure primary. | Keeps the one-direction pooling restriction. |
| GAP-4: power for rate tests | For a prospective variant, compute Fisher-test power at the **frozen pair** D1=(0.154, 0.000), D4=(0.300, 0.075), using achieved group sizes and the existing power convention. Retain the current literal and observed-baseline-difference results as separately labelled sensitivity outputs. | Decisiveness becomes design power for the stated effect pair, not a moving observed baseline. This is a **new declared choice**, not either existing reading relabelled. |
| Correlated D1/D2 | Two positive activity axes are supporting measurements of one activity-related finding, not two independent discoveries. | Does not alter family sizes, p-values, or the negative-control veto. |

GAP-4 can change `NULL` versus `UNDERPOWERED` (11 disagreements in the recorded
rehearsal). This is therefore not a cosmetic amendment. No new power results have been
generated under this proposal, and no preferred outcome has been selected from DR4.
The existing negative-control veto, scope-pure primary, fixed Holm families, effect
directions, EB26 byte-identical regression check, and KEEP/REMOVE/CARRY rule remain intact.

## Execution boundary and follow-up

The [release-day runbook](DR4-DAY-RUNBOOK.md) remains the executable procedure. Readiness
checks and public schema probes may proceed. Do not issue unqualified scientific labels
under unresolved rules: until a ruling, preserve both current readings and all GAP codes,
exactly as the runbook prescribes. Publication/submission remains separately gated.

The `astronomy-closeout-follow-ups` task will check the release dependency without
repeated unchanged full rehearsals. Scheduling is not completion. Optional Gaia/NOIRLab
accounts are not required by the anonymous runbook. The existing Windows cache-write
retries remain enabled; this campaign did **not** alter antivirus exclusions or disable
security controls. Any such configuration change remains a separate human decision.
