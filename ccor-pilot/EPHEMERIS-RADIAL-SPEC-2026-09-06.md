# Radial comparison specification - before computing residuals

The retrieved OEM declares SWFO, EARTH centre, EME2000, UTC, ten-minute samples,
LAGRANGE degree 7, August 26 through September 2. SHA256
`f8e2a5e881a9b2561d925c78e8a7629c1e68bd582f8778d337a7005ad45151af`.
CCSDS 502.0-B-2 section 6.6.2.1 specifies implicit km and km/s for OEM position
and velocity: https://www.nasa.gov/wp-content/uploads/2023/09/ccsds-orbit-data-messages.pdf.

For each of the four original retrospective DATE-OBS timestamps, interpolate
geocentric xyz with the eight nearest bracketing samples (degree-7 Lagrange),
never extrapolate or cross metadata blocks. Add Astropy's built-in geometric
Earth-minus-Sun barycentric position at the same UTC epoch, in kilometres.
Treat EME2000 and ICRS axes as approximately aligned ONLY for this coarse radial
test; their frame bias is far below the fixed 1% tolerance. This is explicitly
not an arcsecond WCS validation, and uses no apparent/light-time-corrected position.

Compare the resulting Sun-spacecraft norm with (a) DSUN_OBS interpreted as m,
(b) the HEE xyz norm with the literal FITS m label, and (c) HEE xyz as km.
The km interpretation is independently supported only if (a) and (c) agree to
within 1% at all four epochs while (b) disagrees by >90% at all four. Otherwise
return unresolved. No original card is changed. No image, display coordinate,
known-comet status or candidate signal enters this check.

This can corroborate a unit interpretation, not certify the complete WCS or
replace NOAA's authoritative metadata clarification. The original STOP remains.
