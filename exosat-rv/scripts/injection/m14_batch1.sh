#!/bin/bash
# M14 lever 2: sweep the two config knobs M13 left at guessed defaults —
# template oversampling (-oversampling, default 1) and the IP model (-ip, default bg).
# Everything else pinned at the M13_G winner: M13 template, H_C orders, -kapsig 3.
# Scored afterwards with vs_published.py (the only honest metric, M12 §9b.4).
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
HC="4,7,8,9,10,12,13,14,17,18,19"

run() {
  tag=$1; shift
  if [ -s ${tag}.rvo.dat ] && [ "$(wc -l < ${tag}.rvo.dat)" -ge 2 ]; then
    echo "skip $tag (exists)"; return
  fi
  cp -f full1.targ.csv ${tag}.targ.csv
  $PY viper.py "cr2res_data/*.fits" M13tpl_tpl.fits -inst CRIRES -fts $FTS \
    -targ "CD-35 2722" -tag $tag -nocell -oset "$HC" -kapsig 3 "$@" \
    > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
}

run M14_O2  -oversampling 2
run M14_O4  -oversampling 4
run M14_O8  -oversampling 8
run M14_IPg  -ip g
run M14_IPsg -ip sg
run M14_IPag -ip ag
run M14_IPmcg -ip mcg
run M14_IPbnd -ip bnd
echo M14BATCH1_DONE
