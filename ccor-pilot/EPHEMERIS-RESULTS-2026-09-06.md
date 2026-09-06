# Independent ephemeris diagnostic - September 6

**The HEE-as-kilometres interpretation is independently corroborated. The image
recovery gate is NOT passed.** [Numerical result](results/radial-ephemeris-20260906.json).

NOAA's separate definitive spacecraft ephemeris was found in the auxiliary
inventory, under the weekly file's August start month. It spans August 26 to
September 2; looking only for a September 1 directory would have incorrectly
missed it. The 170,048-byte OEM declares SWFO/Earth/EME2000/UTC, has 1,009 states
and specifies degree-7 Lagrange interpolation. Exact source is retained in
[this ZIP](results/solar1-ephemeris-20260906.zip); SHA256 of OEM:
`f8e2a5e881a9b2561d925c78e8a7629c1e68bd582f8778d337a7005ad45151af`.
Download completed September 6, 20:47:03 UTC (local completion timestamp).

Both [access](EPHEMERIS-SPEC-2026-09-06.md) and
[numerical](EPHEMERIS-RADIAL-SPEC-2026-09-06.md) stages were specified before their
respective evaluation. Interpolation plus the built-in geometric Earth-Sun
ephemeris yields Sun-spacecraft distances 149,439,015.53 to 149,437,818.45 km.
The FITS DSUN_OBS in metres and HEE norm interpreted as kilometres agree with
these independent values to **7.42-7.58 km**, about 5e-8 fractionally. Literal
HEE metres disagree by 99.9%. The fixed coarse tolerance was 1%, not tuned to
these residuals. Approximate EME2000/ICRS axis alignment is sufficient for that
radial diagnostic, not for certifying subpixel celestial astrometry.

**Decision:** a future protocol may explicitly adopt the externally corroborated
km interpretation as a declared assumption, retaining raw cards. Do not describe
this as an official metadata correction. The outstanding obstacles are full WCS
reference/apparent-position conventions, display-to-FITS mapping for the original
reported source, and a genuinely confirmed or independently predicted control.
The original potential comet is still not truth. A separate star/planet geometry
calibration experiment could bypass dependence on the reporter's display, but
has not been run. No image pixels were decompressed or fitted in this diagnostic.
No NOAA message was sent; the old unsent draft should be revised with this evidence
before asking for exact send approval.

Replay with Astropy/NumPy:

```powershell
& erosita-dr2/.venv/Scripts/python.exe ccor-pilot/scripts/radial_ephemeris.py
python -m unittest discover -s ccor-pilot/tests -v
```

23 offline tests pass. Radial corroboration is an actual resolved subquestion,
not a reason to waive the original pixel-analysis stop.
