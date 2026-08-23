set -x
P=./.venv/Scripts/python.exe
$P scripts/m7_day1_dryrun.py --phase A --batch 20 --gap 1
$P scripts/m7_day1_dryrun.py --phase B --batch 20 --gap 1 --limit 400
$P scripts/m7_day1_dryrun.py --phase B --batch 20 --gap 1
$P scripts/m7_day1_dryrun.py --phase calib
$P scripts/m7_day1_dryrun.py --phase C
$P scripts/m7_day1_dryrun.py --phase weather --weather-n 60 --weather-every 120
echo "ALL PHASES DONE"
