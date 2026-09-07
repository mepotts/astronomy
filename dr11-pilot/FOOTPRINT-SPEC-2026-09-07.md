# Prospective incremental-footprint screen

Before downloading summary catalogues: compare the full DR10/DR11 south
`survey-bricks-<release>-south.fits.gz` tables from the official NERSC archive.
Two requests, <=160 MiB compressed each, 30-second socket timeout, total elapsed
cap 10 minutes each. Keep raw catalogues ignored, with URL/size/hash provenance.
Require unique brick names. Match by name; no missing DR10 brick becomes zero
depth silently. Retain counts of new-only and old-only bricks separately.

Select *metadata* incremental footprint where both releases mark survey_primary,
DR10 median nexp_r>=1, DR11 nexp_r>=DR10+3 and >=1.5*DR10. Rank lexicographically
by brick name, not galaxy appearance. Keep a full compact qualifying table and
first 20 ranked examples. Median exposure counts are not physical CCD identities
or diffuse-light depth. Subsequent known-stream overlap selection must use this
frozen footprint; it cannot replace the failed NGC4651 experiment in hindsight.
No image pixels, candidates, galaxy rankings or discovery claims at this stage.

Primary documentation: https://www.legacysurvey.org/dr11/files/ and
https://www.legacysurvey.org/dr10/files/ .
