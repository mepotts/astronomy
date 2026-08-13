#!/bin/bash
# M15 injection arm for eta Tel B (the eta Tel targ line; otherwise inject_m14).
#   m15_inject.sh ARMNAME PLAN TEMPLATE DATADIR OSET [extra viper flags...]
# Shift the TEMPLATE, never the observation (M12 §8.1).
set -u
ARM=$1; PLAN=$2; TPL=$3; DATADIR=$4; OSET=$5; shift 5
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
TL='eta Tel B;* eta Tel B;19 22 51.3580 -54 25 31.570;25.824 -82.965 [0.100 0.100 90];20.6028 [0.0300] A 2020yCat.1350....0G;v:spectroscopic -1.29 (Opt) A [0.50] simbad'

$PY $SC/mktpl.py "$PLAN" "$TPL" ~/inj/$ARM

n=$($PY -c "import json;print(len(json.load(open('$PLAN'))))")
for ((i=0;i<n;i++)); do
  t=$(printf "inj%02d" $i)
  out="${ARM}_${t}.rvo.dat"
  if [ -s "$out" ] && [ "$(wc -l < "$out")" -ge 2 ]; then echo "skip $t"; continue; fi
  f=$($PY -c "import json;print(json.load(open('$PLAN'))[$i]['file'])")
  printf '%s\n' "$TL" > "${ARM}_${t}.targ.csv"
  $PY viper.py "$DATADIR/$f" ~/inj/$ARM/${t}_tpl.fits -inst CRIRES -fts "$FTS" \
      -targ "eta Tel B" -tag "${ARM}_${t}" -nocell -oset "$OSET" "$@" \
      > /tmp/${ARM}_${t}.log 2>&1
  echo "$t rc=$?"
done
echo "INJ_${ARM}_DONE"
