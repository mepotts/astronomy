#!/bin/bash
# viper A/B sweep over every night that has been reduced.
# $HOME/bin must come first: it holds the no-op gnuplot shim, without which viper dies with
# BrokenPipeError in utils/gplot.py. Do NOT source cr2env.sh here (SSL-less libcurl).
export PATH="$HOME/bin:/usr/bin:/bin:$PATH"
cd ~/viper-src || exit 1
SC=/mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/17e10030-3be1-497c-afec-cf77b01ab773/scratchpad
PY=~/viperenv/bin/python
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
OUT=$SC/ab; mkdir -p "$OUT"
CFGS="base: add2:-telluric|add2 add2dw3:-telluric|add2|-deg_wave|3 kap:-kapsig|3 dw3:-deg_wave|3"

for W in $HOME/cr2res/red/night*; do
  N=$(basename "$W")
  [ "$N" = night1 ] && continue                     # already swept as W_*
  [ -f "$W/cr2res_obs_nodding_extractedA.fits" ] || { echo "skip $N (not reduced)"; continue; }
  mkdir -p nod
  cp -f "$W/cr2res_obs_nodding_extractedA.fits" nod/${N}A.fits
  cp -f "$W/cr2res_obs_nodding_extractedB.fits" nod/${N}B.fits
  $PY $SC/strip09.py nod/${N}A.fits nod/${N}B.fits > /dev/null
  ok=0
  for spec in $CFGS; do
    cname=${spec%%:*}; args=$(echo "${spec#*:}" | tr '|' ' ')
    for arm in A B; do
      tag="X${N}_${cname}_$arm"
      cp -f full1.targ.csv "$tag.targ.csv"
      $PY viper.py "nod/${N}${arm}_o8.fits" U_mk_tpl.fits -inst CRIRES -fts "$FTS" \
          -targ "CD-35 2722" -nocell -tag "$tag" $args > /tmp/$tag.log 2>&1
      if [ -s "$tag.rvo.dat" ]; then cp -f "$tag.rvo.dat" "$OUT/"; ok=$((ok+1)); fi
    done
  done
  echo "$N: $ok/10 runs produced RVs"
done
echo SWEEPALLDONE
