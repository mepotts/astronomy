# Published-stream overlap selection

Before computing overlap: use all Table1 host coordinates in Miro-Carretero et
al. arXiv:2407.20483v1 (DES stream catalogue), from the primary arXiv HTML. Require
63 rows, retaining multiple stream rows per host. Select hosts lying within
0.10 deg in declination and 0.10 deg in RA*cos(dec) of a qualifying brick centre
in the already-frozen 8,468-brick footprint. This interior cut leaves a margin
to brick boundaries; no use of stream signal, published DSI, or brightness to
rank. Sort by (brick name, host name), take the first overlap for native CCD
identity verification. No substitution if the selected object's native products
fail. If no overlap, this catalogue yields no control under this footprint;
do not describe it as absence of streams or lack of new DR11 data.

Retrieve one HTML <=4 MiB and two selected native CCD tables <=4 MiB each.
After verifying added physical r-band exposures, independently fix the known
stream aperture from the published image/description before DR10/11 pixels.
This is a distinct prospectively footprint-selected control, not a rerun or
replacement of NGC4651's failed original specification.

Source: https://arxiv.org/html/2407.20483v1 .
