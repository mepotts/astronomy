# Independently labelled control feasibility - September 6

Freeze before reading the new catalogue table or any new DASCH light curve.
Select the first six stars by numeric SPSSid from Marinoni et al. 2016 Table 3,
https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/462/3616/table3.dat, with Verdict=Accepted,
declination 0 to +60 deg inclusive, amplitude upper limit <=0.010 mag, and no
nonblank Notes. Preserve the table and ReadMe. If fewer than six qualify, use
all qualifying stars without relaxing selection. This is a small feasibility
sample, not the previous proposed 120-star validation sample.

The independent label is ONLY constancy during the published short monitoring
runs (typically 1.24 hours), not century-long constancy. We will report historical
excursion flags, not a measured true false-positive rate. A photometric-standard
designation by itself is not an adequate label; Table 3 rejected 12 standards.

For each selected catalogue position, one APASS query within 30 arcsec; require
exactly one source within 5 arcsec using the existing M0 identity rule. No failed
star replacement or enlarged match cone. Fetch one light curve for each unique
match. Use the unchanged five-AFLAG and 15 arcsec clean-detection cuts. Close the
querycat num_matches/detection accounting before any statistic. Per response cap
16 MiB, max 14 requests (two reference files and up to six catalogue/curve pairs),
no retries or images. No unknown sources ranked.

Useful-coverage gate: at least four of six selected stars have >=100 clean
detections and >=30 years of coverage. Report selection/match/coverage attrition.
An exploratory historical excursion flag is a calendar-year median >=0.5 mag
from the full clean median, with >=5 clean detections in that year. Compute in
both directions, do not tune the threshold, and retain all counts. Shared-plate
systematics, selection bias, and true long-term variability remain alternatives.

Even if this gate passes, do not launch the blind transient search or claim
century-scale FPR calibration: the stopped faint-target gate and the absent
independent long-timescale truth set remain binding. Decide whether this small
labelled sample justifies a larger control study from the observed coverage and
label limitations, not from how few alarms it produces.
