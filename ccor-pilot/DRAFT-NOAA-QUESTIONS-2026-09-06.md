# Draft only - CCOR2 metadata clarification

**NOT SENT.** Suggested recipient from the ReadMe: swx.coronagraph@noaa.gov.
No attachments, account creation, issue filing or email send is authorized by this
draft. Obtain Matthew's approval for the exact message before sending.

Subject: CCOR2 retrospective observer units, WCS conventions and operational quality flag

Hello CCOR team,

We are preparing a small reproducible known-source validation using public CCOR2
data, but have stopped before pixel analysis to clarify metadata. Could you help
with these questions?

1. The June 2 provisional ReadMe Table 7 includes ISVIABLE for operational and
   retrospective products. The June 17 metadata dictionary omits it. Four SWPC
   operational L1A files at September 1, 2026 13:00:14 through 13:45:14 UTC,
   GPA_VER=10.3.0, have no ISVIABLE in either HDU. Their NCEI retrospective
   counterparts (PROC_VER=5.2) all have ISVIABLE=T. Is this an intentional schema
   difference, and where is the operational quality contract documented?
2. In sci_ccor2-l1a_solar1_s20260901T130014Z_e20260901T130043Z_p20260902T081431Z_pub.fits,
   DSUN_OBS=149439008112.9 is labelled metres. HEEX_OBS=149438673.55027124,
   HEEY_OBS=-268457.1212592423 and HEEZ_OBS=167104.98766220413 are also labelled
   metres, but their vector norm is exactly DSUN_OBS/1000. Are the HEE values
   actually kilometres? Is there an authoritative corrected schema or recommended
   SOLAR-1 observer ephemeris source?
3. WCS A has RA---ZPN/DEC--ZPN, but no RADESYS/EQUINOX metadata. Which celestial
   reference frame, equinox, aberration and light-time conventions should an
   external ephemeris use? WCS B in the actual files has HPLN-ZPN/HPLT-ZPN,
   although the documentation describes A and B as celestial. Is A the recommended
   independently calibrated route for stellar/planetary astrometry?
4. Are there published CCOR2 display-to-FITS transform instructions and a named,
   confirmed comet validation sequence after June 2, 2026? We do not treat public
   potential-comet endorsements as confirmation or fit image transformations to
   maximize the candidate signal.

We can provide the small header-only evidence bundle if useful. We have not
decompressed or scored the image data, and make no discovery or calibration claim.

Thank you.
