# DR11 incremental-imaging pilots

**September 7: [full footprint, published-stream overlap and paired-pixel depth test completed](RESULTS-2026-09-07.md).**
8,468 qualifying bricks; selected ESO197-018 gains six r exposures. Its empirical
aperture scatter drops only 5.47%, below the frozen 10% gate. No unknown-stream
search or known-stream recovery claim. Nine offline tests; full local replays pass.

## Original known-stream preflight - closed September 6

**STOP_NO_NEW_R_INPUTS.** The independently selected NGC 4651 east-stream brick
`1910p165` gains no CCD inputs in any band from DR10 south to DR11 south.

| Band | DR10 CCDs / exposures | DR11 CCDs / exposures | Added / removed CCDs |
|---|---:|---:|---:|
| g | 32 / 8 | 20 / 5 | 0 / 12 |
| r (primary) | 32 / 8 | 20 / 5 | 0 / 12 |
| i | 30 / 7 | 0 / 0 | 0 / 30 |
| z | 32 / 8 | 20 / 5 | 0 / 12 |

All 60 DR11 CCD keys occur in DR10; 66 keys are removed. All used rows have
ccd_cuts=0 and identities are unique. CCDs are not independent exposures and
brick overlap does not prove aperture coverage. This does not measure actual
depth, stream recovery, processing improvement, or DR11-wide incremental area.

The [specification](SPEC-2026-09-06.md) was frozen before retrieving the two tables.
No science image arrays were acquired. The selected known stream is independently
documented by [Foster et al. 2014](https://arxiv.org/abs/1406.5511), Figures 1-2;
the downloaded source paper and its relevant pages were visually checked. This
control's stop means do not substitute another galaxy until success. A future
DR11 project must first select a genuinely added-exposure footprint prospectively,
then validate usable diffuse-light depth and check prior searches. No broad scan
or new candidate list is justified by this result.

Evidence: [result](results/preflight-20260906.json),
[exact public CCD tables](evidence/ccds-20260906.zip) (32,064-byte ZIP, 129,600
uncompressed bytes). Both downloads completed September 6 at 20:33:44 UTC
(local download completion timestamps, not archive modification times); raw table
hashes and URLs are in the result. Native-product definitions:
[Legacy Surveys files](https://www.legacysurvey.org/dr11/files/).

Replay with Astropy and NumPy, no network:

```powershell
& erosita-dr2/.venv/Scripts/python.exe dr11-pilot/scripts/preflight.py
python -m unittest discover -s dr11-pilot/tests -v
```

The byte-frozen specification is protected from checkout newline conversion.
