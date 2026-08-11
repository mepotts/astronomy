#!/bin/bash
# M15 endgame: the full paper recipe on eta Tel B's per-nodding frames
# (2-iteration template, H_C, -kapsig 3, -oversampling 2, bin A/B), then
# diagnostics, blind search, and a per-frame injection arm at K=300/P=200.
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
HC="4,7,8,9,10,12,13,14,17,18,19"
TL='eta Tel B;* eta Tel B;19 22 51.3580 -54 25 31.570;25.824 -82.965 [0.100 0.100 90];20.6028 [0.0300] A 2020yCat.1350....0G;v:spectroscopic -1.29 (Opt) A [0.50] simbad'

echo "frames staged: $(ls etatel_nod/*_o8.fits | wc -l)"
printf '%s\n' "$TL" > E15_NOD.targ.csv
$PY viper.py "etatel_nod/et*_o8.fits" E15tpl2_tpl.fits -inst CRIRES -fts $FTS \
  -targ "eta Tel B" -tag E15_NOD -nocell -oset "$HC" -kapsig 3 -oversampling 2 \
  > /tmp/E15_NOD.log 2>&1
echo "E15_NOD rc=$? rows=$(wc -l < E15_NOD.rvo.dat 2>/dev/null)"

echo "=== diag ==="
$PY $SC/m15_diag.py E15_NOD.rvo.dat
echo "=== blind search (binned) ==="
$PY $SC/blind_search.py E15_NOD.rvo.dat --nod

echo "=== per-frame injection K=300 P=200 ==="
$PY $SC/mkplan_nod.py E15_NOD.rvo.dat $SC/inject_plan_etnod300.json 300 200
bash $SC/m15_inject.sh ETNOD3 $SC/inject_plan_etnod300.json E15tpl2_tpl.fits etatel_nod "$HC" \
  -kapsig 3 -oversampling 2 2>&1 | tail -2
$PY $SC/inject_score_m14.py ETNOD3 E15_NOD.rvo.dat $SC/inject_plan_etnod300.json
echo M15NODALL_DONE
