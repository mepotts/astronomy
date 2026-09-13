# Attitude and map semantics for the next fixed-region check

September 12. Parent inspected four official SAS documentation pages while
C3 was being implemented. No attitude/map arrays or photon coordinates read.
These are SAS 22 descriptions; retained products' actual task versions must
be checked before treating the descriptions as exact processing provenance.

`atthkgen` samples attitude at a configured timestep rather than exporting every
raw attitude measurement. It obtains AHF and OM values through the OAL; inputs
more than 20 seconds away make quality bad. TIME and AHFRA/AHFDEC/AHFPA plus
OM equivalents are expected columns. Invalid attitude is represented by NULLs;
offset columns also become NULL for bad quality. Mean/median header pointing
values are not a bound on instantaneous motion. A later array check must retain
nulls, establish sampling/gaps and distinguish AHF from possibly incomplete OM
coverage. It cannot claim a continuous-motion bound just from sample extrema.
[atthkgen description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/node3.html).

`attcalc` projects detector positions into an aspect-corrected tangent plane,
including instrument boresight corrections from calibration. Event X/Y are sky
coordinates, not a substitute for RAW detector geometry. Its event attitude
comes from OAL/AHF or OM (or an explicitly fixed setting), not directly from
the atthkgen table. Thus a downloaded ATTTSR can diagnose motion but is not
automatically an exact replay of every event's attitude correction. Invalid
pointing produces NULL X/Y. Check processing settings, null conventions and
time coverage; do not align a map using measured photons.
[attcalc description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/attcalc/node3.html).

`eexpmap` accumulates attitude-binned, per-chip effective exposure and calibrated
spatial efficiency. It reads TIME/GTI/CCDNR/FLAG selections; source-detection
map masks may differ from a prospective event selection. Its broad-band
efficiency uses a representative energy, so map amplitude is not a purely
geometric area fraction. Positive support is an accumulated-coverage diagnostic,
not proof of every-bin stability. This preserves the distinction already in
the [geometry proposal](XMM-GEOMETRY-NEXT-2026-09-12.md).
[eexpmap algorithm](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node3.html).

Exact map/event edge correspondence depends on coordinate randomization and
attitude rebinning. Current documentation recommends very fine attrebin for
exact sky-map correspondence; older quoted typical pixel offsets are not a
universal bound for this observation. The eventual fixed-region test needs
actual pixel scale, processing settings and a justified uncertainty margin.
A failed edge test must not lead to shifting the map or aperture to fit counts.
[map/event coordinate matching](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/eexpmap/node4.html).

The practical next decision remains data-driven but photon-blind: inspect C3
headers, then specify static support and movement diagnostics with explicit
limitations. Do not silently upgrade sampled pointing extrema into guaranteed
continuous detector acceptance or demand an unnecessary absolute-flux model
for a same-region relative timing test.
