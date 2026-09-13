# C8 result: unique control association, comparison contacts unresolved

Executed locally after runtime freeze `860115a`, September13 UTC2026, under
the user's ongoing experiment authority. Worker, independent parent comparison
and one additional numerical replay completed. Strongest status:
`SOURCE_GEOMETRY_SCREEN_NOT_CLEAN_SKY`. No photons, map pixels, new products or
network queries were used. This is not recovery or discovery.

## Actual fixed-catalogue result

All151 catalogue rows have valid original/corrected coordinates and positive,
unique IDs. Exactly one corrected position falls within the fixed5arcsec
association radius. Its original position is2.8441692831480774arcsec from the
unchanged published centre, inside20arcsec. This is positional association,
not physical identification or a fitted astrometric correction.

Only that uniquely associated row is exempted from the published aperture's
other-source counts. No exemption applies to negatives or annuli.

| Fixed region | Other centres within20arcsec | 30arcsec disks contacting aperture | 30arcsec disks contacting annulus |
| --- | ---: | ---: | ---: |
| published | 0 | 0 | 1 |
| north120 | 0 | 1 | 2 |
| east120 | 0 | 1 | 1 |
| south120 | 0 | 0 | 3 |
| west120 | 0 | 2 | 5 |

All contact-counted rows have zero point-model extent, not a measured enclosing
radius. Across the full catalogue,145 extents are zero and6 positive; all extent
values are finite/nonnegative.145 extent errors are nonfinite and6 positive;
we do not infer why errors are nonfinite or erase them. Position-error fields
are finite/positive. No region is certified clean by catalogue absence.

## Consequence before viewing photons

The source position is usable for a fixed raw-event diagnostic without
recentering. North/east/west have potential aperture contacts under the already
declared30arcsec disk rule; all five annuli need source-exclusion treatment for
the stronger background analysis. Contact alone is not measured contamination
or positive overlap area. South has no aperture-disk contact, but previous maps
show missing MOS source-circle sampling there. **Two usable negative regions
have not been established.** Preserve these outcomes; do not move apertures,
drop failed cameras or redefine the original recovery gate after seeing counts.

A separately frozen descriptive recorded-event histogram can now answer what
photons were recorded in the fixed regions. It must not be labelled calibrated
rate, clean background, statistical recovery or a passed discovery-search gate.
Exposure, exclusion-mask support and detector-artifact requirements remain.

## Accounting and immutable evidence

Each successful pass made755 selected reads and decoded7,852bytes, retaining
all151rows and all ten fixed region summaries. Worker plus parent =15,704bytes;
one root read-only replay adds7,852, for **three known passes /23,556bytes**.
Opaque whole-file hashes and structural-header checks are separate I/O.
No fourth numerical pass is needed for receipt review or Git integration.

Worker peak69,726,208bytes; parent70,422,528, below268,435,456monitored cap.
Worker returned0; parent assessment and numerical validation completed.
Final six JSON artifacts total60,118bytes; worker pre-result accounting57,060,
parent pre-outcome58,181. The [independent postrun audit](XMM-C8-POSTRUN-REVIEW.md)
verified dependency/artifact/schema/aggregate closure without another data pass.

| Artifact | SHA-256 |
| --- | --- |
| Outcome | `82cd6df3d673c86059494e9d38a3bfd1312ee9ce8b19301873309dfc995ad16e` |
| Table result | `719afedaca93f82f85a5e7003564bab7f02bf1c23065d871d80b3bae53f16cfa` |
| Run start | `a9ec6186835d402a41b2483518be45b43a47cd218cf4bdc37c556320ed7d2e6a` |
| Source | `bd76ab70fb36ca2ea9c350401ab36991baa8fd30b3bf160c546c788a536ad0e3` |
| Tests | `0bd5ba02add739318553de6029147e79d625b8dcde8c5180b3674c9088370733` |
| Protocol snapshot | `9b4a86517fdafcccf16c1004808a87a457c4c05b63b51f6e9da5163675330c14` |

See the [prospective contract](XMM-C8-2026-09-12.md),
[preflight review](XMM-C8-REVIEW.md) and
[saved aggregate result](XMM-C8-2026-09-12-data/table-result.json).
