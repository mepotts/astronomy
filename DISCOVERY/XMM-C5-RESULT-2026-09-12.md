# C5 result: static maps expose a missing confirming camera

Executed after freeze `9cef69c`; **no burst recovery or discovery**. The worker,
parent numerical validation and one subsequent numerical replay all completed.
The [independent receipt audit](XMM-C5-POSTRUN-REVIEW.md) accepted artifact and
aggregate integrity without a fourth map decode.

The pn published-source circle has positive accumulated-map values at every
sampled subpixel at both fixed resolutions. MOS1's source circle and background
annulus have zero values at every sampled subpixel at both resolutions. Thus
these files do not supply affirmative pn-plus-MOS source support. This does not
prove zero MOS1 exposure at all times, a physical detector cause, or missing photons.

| Fixed region | pn positive area estimate, nominal8 | MOS1, nominal8 |
| --- | ---: | ---: |
| Published circle | 100.0000% | 0.0000% |
| Published annulus | 95.3370% | 0.0000% |
| North circle | 100.0000% | 0.0000% |
| North annulus | 100.0000% | 32.8269% |
| East circle | 100.0000% | 50.9640% |
| East annulus | 99.1441% | 50.3244% |
| South circle | 84.5863% | 0.0000% |
| South annulus | 96.9689% | 0.0000% |
| West circle | 99.9801% | 0.0000% |
| West annulus | 96.7490% | 0.0000% |

These are sampled spherical-area sign classifications, not live exposure
fractions or certified continuous coverage. Remainders are zero-classified;
none of these sampled regions has negative, nonfinite or outside-image samples.
The audit retains the complete four/eight-resolution table. The west pn circle
has one fine-grid zero sample despite no coarse-grid zeros and a positive
unsupported-pixel-centre margin: neither coarse sampling nor centre-distance
clearance proves a clean finite-area aperture. No region or resolution was chosen
after seeing results; no aperture, centre, frame convention or denominator changed.

Outcome `STATIC_SUPPORT_APPROXIMATION_NOT_COVERAGE`, SHA256
`58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36`.
All20 fixed region summaries completed. Two648-square float32 arrays contribute
3359232 decoded/read bytes per pass, **10077696 across three known passes**.
Opaque input hashing/header I/O is separate. Worker/parent peaks78749696 each;
final JSON77712 bytes, below fixed limits. No network or photon, GTI, attitude,
source-list array interpretation occurred in C5. MOS2 remains unavailable in
these immutable receipts.

Next decision: the [documented exact ESA MOS2 alternate](XMM-MOS2-ALTERNATE-2026-09-12.md)
supports a separately frozen one-product acquisition, not retrying the failed
HEASARC request. Do not waive the second-camera gate. Source-list confusion,
matched regional exposure, detector checks and published burst recovery remain
necessary before any unknown-source search. The [source geometry proposal](XMM-SOURCE-GEOMETRY-NEXT-2026-09-12.md)
and [event decoder plan](XMM-EVENT-DECODER-NEXT-2026-09-12.md) are unexecuted next-stage
designs, not additional evidence.
