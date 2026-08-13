#!/bin/bash
# Generic injection-recovery arm for any template+config.
#   inject_generic.sh ARMNAME TEMPLATE OSET [extra viper flags...]
# Uses inject_plan_big.json (K=1530 m/s Keplerian at the published 171.454 d).
# Shift the TEMPLATE, never the observation (M12 SS8.1: observation shifts are 92%
# absorbed by the telluric-anchored wavelength solution).
# Score afterwards with inject_score2.py ARMNAME REF_RVO OSET.
set -u
ARM=$1; TPL=$2; OSET=$3; shift 3
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
PLAN=$SC/inject_plan_big.json

$PY $SC/mktpl.py "$PLAN" "$TPL" ~/inj/$ARM

n=$($PY -c "import json;print(len(json.load(open('$PLAN'))))")
for ((i=0;i<n;i++)); do
  t=$(printf "inj%02d" $i)
  out="${ARM}_${t}.rvo.dat"
  if [ -s "$out" ] && [ "$(wc -l < "$out")" -ge 2 ]; then echo "skip $t"; continue; fi
  f=$($PY -c "import json;print(json.load(open('$PLAN'))[$i]['file'])")
  cp -f full1.targ.csv "${ARM}_${t}.targ.csv"
  $PY viper.py "cr2res_data/$f" ~/inj/$ARM/${t}_tpl.fits -inst CRIRES -fts "$FTS" \
      -targ "CD-35 2722" -tag "${ARM}_${t}" -nocell -oset "$OSET" "$@" \
      > /tmp/${ARM}_${t}.log 2>&1
  echo "$t rc=$?"
done
echo "INJ_${ARM}_DONE"
