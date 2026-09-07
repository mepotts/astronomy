# Independent known-star geometry control

Frozen before Hipparcos query and retrospective pixel decompression. Use exactly
the four September 1 13:00--13:45 retrospective files and their source URLs from
`results/retrospective-preflight-20260906.json`; <=12 MiB each, 30-second sockets.
Preserve original operational/report-mapping stops. No reporter coordinates,
reflection search, or unknown-object measurement enters this control.

Query public Hipparcos I/239/hip_main for RAICRS 150..170, DEICRS -2..18, Vmag<=7,
at most 1000 records / 2 MiB. Propagate the ICRS epoch-1991.25 positions linearly
with pmRA*cos(dec) and pmDE to DATE-AVG. Use WCSA ZPN with zero-based FITS pixels.
Absent RADESYS is provisionally interpreted as ICRS; no precession to equinox of
date. This is a coarse <=2-pixel empirical geometry test, not subarcsecond
astrometry: stellar parallax and annual aberration (<~1 pixel) are not fitted.
The previously corroborated spacecraft kilometre interpretation is retained but
not needed for distant-star angular positions. No planet ephemeris is asserted.

Select eight stars by increasing Vmag then HIP, whose predicted positions in
all four frames lie >=50 pixels from image edges and 180..800 pixels from
CRPIX. No replacements after pixels. First four are translation training,
remaining four held-out geometry controls. Fewer than eight stops selection.

Require the seven true quality booleans and two zero block counts from the
original protocol, abs(SHIFT_X/Y)<7, three retrospective HDUs, 1920x2048 image
and integer PQF of same shape. NOAA ReadMe Table5-6 (pages24-25) defines PQF=0 as
linear unflagged pixels; exclude ALL nonzero PQF in source/measurement support.
Retain header values and raw checksums. Use stored FITS orientation, no resampling.

For each prediction take a 41x41 raw cutout. Estimate background median and
1.4826*MAD in radius12..18. Find highest unflagged pixel within radius6 of
prediction, require peak-background>=5*MAD. Compute positive-background-weighted
centroid in radius2.5 around that maximum, all its pixels finite/PQF=0. Require
>=80% annular support, positive scale/flux, centroid within6 of prediction.
This is an engineering contrast score, not a Gaussian significance.

Per frame fit ONLY median x/y translation from >=3/4 training stars. Require
translation norm<=5 pixels, >=3/4 held-out stars recovered, held-out residual
RMS<=2 pixels and each residual<=3 pixels. Every frame must pass. Report all
stars including failures. Four fixed offset locations (+/-32,0),(0,+/-32) per
star undergo identical measurement; report their recovery count as diagnostics,
not a survey FAP. Do not select the WCS convention by optimizing holdout results.

If passed, this validates local coarse star geometry and can inform a *new*
motion-search protocol; it does not confirm a comet, reporter mapping, absolute
photometry, or full-field distortion. Keep full FITS ignored; retain known-star
cutouts, hashes, selection and all measurements for offline replay.

Sources: NOAA provisional ReadMe https://archive.data.noaa.gov/satellite-spaceweather/SWFO/docs/CCOR/SWFO_CCOR-2_Provisional_ReadMe_V1.0.pdf ;
Hipparcos ESA1997 https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=I/239/hip_main .
