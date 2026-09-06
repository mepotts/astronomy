# Independent radial-distance check - before ephemeris retrieval

Use NOAA's separate definitive spacecraft ephemeris, discovered through the public
auxiliary inventory, to test the factor-1000 header inconsistency. This is a
header/geometry diagnostic, not a new image recovery protocol.

Fixed input: `SWFO/SOLAR-1/auxiliary/Ephem_Def/2026/08/SWFO_DefEphem_20262380000_20262450000_20262451625.oem`
from `https://archive.data.noaa.gov/satellite-spaceweather/`. Its filename spans
August 26 to September 2 and therefore brackets the four September 1 exposures.
Do not infer a September 1 absence from the lack of a September subdirectory:
definitive files are weekly and organized by start month. Cap 8 MiB, one download.

Read declared object, centre, frame, units/time system and epoch span. If the file
does not identify SOLAR-1/SWFO, Earth centre and a supported geocentric inertial
frame/time system, STOP rather than guess. Preserve original bytes and headers.
Only after these checks specify any conversion and numerical tolerances in a
separate dated record, before evaluating residuals. Do not silently relabel the
retrospective FITS HEE units or waive reference-frame/display-control gates.
