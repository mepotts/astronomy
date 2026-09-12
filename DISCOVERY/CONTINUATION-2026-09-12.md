# Discovery continuation: close the TESS localization test, check XMM feasibility

**No new discovery. This pass made scientific progress, not a dated wait.**
The three-agent team separated numerical implementation, independent experiment
review and next-route primary-source research; the parent integrated the work and
executed the frozen real-data experiment. Publication, registry submissions and
scientific correspondence remain separately gated.

## Completed measurement

[TESS M2p](../tess-short-eclipses/M2p-RESULT-2026-09-12.md) has now run all
1,920 planned real-noise injection trials across three mandatory published controls.
Two fields fail localization stress rules; the cleaner field completes only the
specified limited diagnostics, with uncalibrated nominal ellipses. The method
cannot be scaled to unknown crowded sources on this evidence. Failed conditions
are preserved, not rewritten, discarded or replaced by the successful field.

All three primary catalogue profile rankings favor the known target. That is
useful recovery evidence, but injected nearby eclipses demonstrate why it is not
sufficient source-identification validation. Further TESS work needs materially
new calibration evidence and independent negatives, not more fine-tuning on
these same three observations. The current method is parked for scientific
reasons, not until a calendar date.

## Adopted next direction

The [XMM identifier-level investigation](XMM-EXOD-ELIGIBILITY-2026-09-12.md)
verified three public observations taken after the March 2025 EXOD paper and
absent from its pinned 15,105-ID list. The parent independently
checked all three retained response hashes, exact string IDs, observing/public
dates, list absence and the two published controls' list membership. The final
three-response provenance snapshot is 168,544 bytes; it contains no photon
arrays or source coordinates.

This supports a concrete archive increment relative to that paper, **not proof
that no later researcher has searched it**. It also corrects the weaker generic
5XMM-release idea: a new catalogue release does not imply newly observed photons,
and attempted-minus-successful counts do not identify unsearched exposures.

Adopt **C0b-1: the two-request, 256-KiB known-control metadata check** as the next
bounded operation. First inspect observed archive product/exposure schema, then
freeze the exact query for published control observation `0884250101` using
verified join keys. Determine public supported-camera modes, required event/source
products and advertised sizes before choosing a photon-recovery protocol.
Use the existing hard process-tree deadline helper; retain complete responses,
hashes and missing/unsupported/error outcomes. No replacement control or silent
extension of the request/sample budget.

The [first C0b-1 schema request](XMM-C0b1-SCHEMA-2026-09-12.md) has now executed:
one HTTP-200 response, 2,034 bytes. Its frozen validator stops on a mismatch
between Python string sorting and the archive's quoted column-name order. The
failure is preserved without changing the validator or retrying. Read-only
inspection also establishes that the exposed product table lacks advertised file
sizes. This does not prove absent products or an unusable telescope archive.
The second query was not executed: a product-name-only response could not meet
the size/completeness gate. Next metadata work needs a documented official
manifest, directory listing or appropriately bounded size request, under a new
explicit contract; there is no reason to repair the sort check merely to call
this incomplete schema a pass.

The HTTP receipt also contains an anonymous session cookie. Its frozen original
remains local and ignored; a separate public derivative omits the cookie. No
scientific input or failed outcome was overwritten for this privacy treatment.

The larger five-observation product check in the research note remains a later
scope decision, not an already launched query. No XMM science products, SAS
installation, calibration deployment, remote processing or unknown-source
measurements are authorized by the metadata result alone. A separately reviewed
control-recovery and empirical-negative experiment must establish scientific and
local-runtime feasibility first. If product sizes or modes cannot be established,
stop with that concrete evidence rather than acquiring a bulk bundle speculatively.

## Unchanged operations and authority

The separately reviewed [C0c2 directory amendment](XMM-C0c2-RESULT-2026-09-12.md)
has now executed: 319808 bytes and 2193 complete parsed entries. The earlier
C0c request stopped at 262144 bytes and remains frozen. Exact pn/MOS event and
EPIC source-list filenames are now observed; displayed sizes remain rounded,
not acquisition-budget evidence. Next is a bounded exact-size/summary metadata
batch for these same control inputs. The counts-recovery design is still a
draft with mode, time, exposure and screening blockers, not a launched experiment.

[C0d](XMM-C0d-RESULT-2026-09-12.md) has since completed four successful
size-only HEADs (126982449 compressed bytes total) and one fully retained
summary GET that failed its frozen closing-tag rule. That STOP is unchanged.
Separate offline interpretation establishes the selected exposure modes and
nominal time overlap, not live exposure. The coordinate-bearing raw summary
is retained locally and ignored; public notes omit those values.

Adopt the separately reviewed [C1 contract](XMM-C1-2026-09-12.md) for exactly
four known-control product downloads and headers-only structural inspection.
Freeze implementation/tests/review before execution. No photon selection or
unknown search follows from transport success alone. The bounded
[later-work check](XMM-LATER-WORK-2026-09-12.md) leaves precise later-search
coverage unknown; it does not warrant abandoning the control experiment or
claiming novelty.

[C1 has now executed](XMM-C1-RESULT-2026-09-12.md): all four fixed known-control
files retained, gzip/header checks and parent replay passed, 247141440 expanded
bytes and 68190208-byte worker peak. No scientific arrays were interpreted.
The actual headers confirm selected camera/exposure modes and shared local
satellite TT references. Per-CCD exposure, GTI and bad-pixel metadata are present,
but their values and aperture coverage remain unvalidated. Next is a bounded
ancillary-metadata inspection followed by the separately frozen counts test;
neither acquisition success nor this continuation authorizes an unknown scan.

[ITF](ITF-NOTIFICATIONS-2026-09-12.md) still has its daily archive publisher and
existing-queue watch, not a fresh automated discovery search. No dedicated
SMS/email delivery was configured or tested. Existing daily/weekly follow-ups
were not changed. A future external alert needs an approved recipient/channel
and a verified test delivery; queue movements must not be described as discoveries.

Repository commits, tested pushes and merges remain authorized. Scientific
publication/submission and private-coordinate disclosure remain human decisions.
The overall discovery goal remains active; finishing this measured failure does
not satisfy it, and useful next work is available now.
