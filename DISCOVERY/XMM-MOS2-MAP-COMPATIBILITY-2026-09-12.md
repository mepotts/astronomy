# MOS2 retained map: limited static-sign compatibility

Header-only adjudication after C6; no image or event values decoded. The full
local header SHA256 is `6cc4bfa1b08d93a31f8f89ba49274511e9ef0052634d64cb1235fdde739e2285`.
Product identity/hashes are recorded in [C6 result](XMM-C6-RESULT-2026-09-12.md).

## Adopted narrow decision

The map is compatible with the **same limited fixed-region sign diagnostic**
as C5, under a new one-map contract. It is not a matched regional/per-bin
exposure denominator and has not yet demonstrated positive source support.

One648-square primary image, BITPIX-32, data offset25920, payload1679616 bytes.
No BSCALE, BZERO, BLANK or BUNIT. Primary RA/DEC TAN WCS uses degree units,
CDELT magnitudes4arcsec, legacy RADECSYS FK5, EQUINOX2000; RADESYS absent.
Root compared the12 selected CRPIX/CRVAL/CDELT/CTYPE/CUNIT/frame/equinox fields
with retained MOS1: all exactly equal, without persisting absolute values.
No primary CD/PC/CROTA/PV/PS/SIP or pole/WCSAXES override was identified.
An alternate-frame WCSAXESL card exists; do not import alternate WCS metadata
into the minimal primary WCS. Preserve C5's explicit legacy-frame conversion,
fix=False, fixed ICRS-position convention transformed to FK5/J2000, fixed
20arcsec circle,60–90arcsec annulus,120arcsec cardinal offsets, and4/8 quadratures.

## Why this still cannot calibrate photon exposure

Creator eexpmap4.12.1, SAS xmmsas_20241108_1150-21.0.0. EXPOSURE is
41463.0937838554; TSTART/TSTOP/ONTIME absent. BUNIT absent means no unit or
absolute normalization claim is justified by this header alone. Provenance
records reference-point source PNT and attitude source AHF, not independent
astrometric validation.

Retained DSS lists CCDs1–7, PATTERN`:12`, PI`(200:12000` in CHAN, and two
wildcard FLAG masks identical to MOS1:
`b000x00xxx0x0x0x0x0xxxxxxxxxxxxx` and
`b000x00xx00x0x0x0x0xxxxxxxxxxxxx`. These are broader than the adopted FLAG==0;
the literal PI range is not silently rewritten as strict200<PI<12000.
TIME references GTI00006 through GTI00606. The one-primary map contains none
of these tables; matching regional accepted-event exposure is not established.
The earlier [MOS1/pn adjudication](XMM-MAP-COMPATIBILITY-2026-09-12.md) explains
why an accumulated sign map is a geometric warning diagnostic, not a live-time
fraction, detector-edge certificate or scientific false-alarm calibration.

No aperture adjustment or camera/control removal follows from this decision.
All C5 pn/MOS1 summaries remain part of the evidence. If MOS2 is also zero or
partial at the source, preserve that finding; do not manufacture a second-camera
pass. Source-list confusion and time-dependent detector/exposure checks remain.
