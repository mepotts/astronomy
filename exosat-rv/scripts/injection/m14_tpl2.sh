#!/bin/bash
# M14 lever 3: SECOND template iteration, with the M9/M11 injection guard.
# M13tpl was iteration 1 (created against the M12-era cd35_2722B_tpl). This creates
# iteration 2 with IDENTICAL creation flags (only the input template changes), then
# scores the M13_G+O2 config on it, then runs the K=1530 injection arm.
# ADOPTION RULE: reject if injection recovery falls below ~95% (M11's absorption mode),
# no matter how good rms_pub looks — that is exactly how M9's fake win worked.
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
HC="4,7,8,9,10,12,13,14,17,18,19"

if [ ! -f M14tpl2_tpl.fits ]; then
  cp -f full1.targ.csv M14tpl2.targ.csv
  # NOTE first attempt with creation flags identical to M13tpl crashed curve_fit on
  # 7 segments (maxfev). -kapsig 3 added to stabilise the creation fit; this makes
  # "iteration count" not the only changed variable, and is reported as such.
  $PY viper.py "cr2res_data/*.fits" M13tpl_tpl.fits -inst CRIRES -fts $FTS \
    -targ "CD-35 2722" -tag M14tpl2 -createtpl -nocell -tpl_wave tell -oset 0:21 \
    -kapsig 3 > /tmp/M14tpl2.log 2>&1
  if [ ! -f M14tpl2_tpl.fits ]; then echo "TPL2 FAILED"; tail -5 /tmp/M14tpl2.log; exit 1; fi
fi
echo "tpl2 done"

cp -f full1.targ.csv M14_T2.targ.csv
$PY viper.py "cr2res_data/*.fits" M14tpl2_tpl.fits -inst CRIRES -fts $FTS \
  -targ "CD-35 2722" -tag M14_T2 -nocell -oset "$HC" -kapsig 3 -oversampling 2 \
  > /tmp/M14_T2.log 2>&1
echo "M14_T2 rc=$? rows=$(wc -l < M14_T2.rvo.dat 2>/dev/null)"
$PY $SC/median_test.py M14_T2.rvo.dat

bash $SC/inject_m14.sh T2K15 $SC/inject_plan_big.json M14tpl2_tpl.fits cr2res_data "$HC" \
  -kapsig 3 -oversampling 2 2>&1 | tail -2
$PY $SC/inject_score_m14.py T2K15 M14_T2.rvo.dat $SC/inject_plan_big.json
echo M14TPL2_DONE
