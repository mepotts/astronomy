#!/bin/bash
# M14 endgame on the FULL per-nodding frame set (18 nights x A/B).
# T2 variant FIRST (the adopted config and the decisive result; single-frame probe
# timed <4 min/frame), then the M13tpl comparison variant (observed to grind on some
# frames — it comes last so it cannot block the criteria-relevant runs), then the
# per-frame injection validation of the adopted per-nodding pipeline.
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
HC="4,7,8,9,10,12,13,14,17,18,19"

echo "frames staged: $(ls nod14/night*_o8.fits | wc -l)"

echo "=== NODT2: per-nodding + 2-iter template + O2 (the full paper recipe) ==="
cp -f full1.targ.csv M14_NODT2.targ.csv
$PY viper.py "nod14/night*_o8.fits" M14tpl2_tpl.fits -inst CRIRES -fts $FTS \
  -targ "CD-35 2722" -tag M14_NODT2 -nocell -oset "$HC" -kapsig 3 -oversampling 2 \
  > /tmp/M14_NODT2.log 2>&1
echo "M14_NODT2 rc=$? rows=$(wc -l < M14_NODT2.rvo.dat 2>/dev/null)"
$PY $SC/m14_score.py M14_NODT2.rvo.dat --nod --both --ref M14_T2.rvo.dat
echo "=== blind search NODT2 (binned) ==="
$PY $SC/blind_search.py M14_NODT2.rvo.dat --nod

echo "=== per-frame injection validation (K=1530, T2 template) ==="
$PY $SC/mkplan_nod.py M14_NODT2.rvo.dat $SC/inject_plan_nod.json 1530
bash $SC/inject_m14.sh NODK15 $SC/inject_plan_nod.json M14tpl2_tpl.fits nod14 "$HC" \
  -kapsig 3 -oversampling 2 2>&1 | tail -2
$PY $SC/inject_score_m14.py NODK15 M14_NODT2.rvo.dat $SC/inject_plan_nod.json

echo "=== NODALL: M13tpl comparison variant (may grind; non-blocking) ==="
cp -f full1.targ.csv M14_NODALL.targ.csv
timeout 7200 $PY viper.py "nod14/night*_o8.fits" M13tpl_tpl.fits -inst CRIRES -fts $FTS \
  -targ "CD-35 2722" -tag M14_NODALL -nocell -oset "$HC" -kapsig 3 -oversampling 2 \
  > /tmp/M14_NODALL.log 2>&1
echo "M14_NODALL rc=$? rows=$(wc -l < M14_NODALL.rvo.dat 2>/dev/null)"
if [ -s M14_NODALL.rvo.dat ]; then
  $PY $SC/m14_score.py M14_NODALL.rvo.dat --nod --both --ref M14_O2.rvo.dat
  $PY $SC/blind_search.py M14_NODALL.rvo.dat --nod
fi
echo M14NODALL_DONE
