#!/bin/bash
# M13 batch: full-coverage telluric-free template + oset/config sweep, scored honestly.
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python

# 1. telluric-free template over ALL 21 segments (one iteration, published wave option)
cp -f full1.targ.csv M13tpl.targ.csv
$PY viper.py "cr2res_data/*.fits" cd35_2722B_tpl.fits -inst CRIRES -fts $FTS \
  -targ "CD-35 2722" -tag M13tpl -createtpl -nocell -tpl_wave tell -oset 0:21 \
  > /tmp/M13tpl.log 2>&1
if [ ! -f M13tpl_tpl.fits ]; then echo "TEMPLATE FAILED"; tail -5 /tmp/M13tpl.log; exit 1; fi
echo "template done"

run() {
  tag=$1; oset=$2; shift 2
  cp -f full1.targ.csv ${tag}.targ.csv
  $PY viper.py "cr2res_data/*.fits" M13tpl_tpl.fits -inst CRIRES -fts $FTS \
    -targ "CD-35 2722" -tag $tag -nocell -oset "$oset" "$@" > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
}

HC="4,7,8,9,10,12,13,14,17,18,19"
HA="2,5,6,7,8,10,11,12,15,16,17"

run M13_A "7:17"
run M13_B "$HC"
run M13_C "$HA"
run M13_D "0:21"
run M13_E "$HC" -chunks 2
run M13_F "$HC" -telluric add2
run M13_G "$HC" -kapsig 3
run M13_H "7:17" -chunks 2
run M13_I "$HC" -telluric add2 -chunks 2
run M13_J "$HC" -deg_wave 3
echo ALLDONE
