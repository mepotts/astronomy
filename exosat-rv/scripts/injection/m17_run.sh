#!/bin/bash
# M17: K-band spot-check runs on AB Pic b, CT Cha B, beta Pic b (products route).
# Per target: stage -> template ladder (iter0->1->2, kapsig creation, K-band FTS)
# -> RV run (all 18 K2166 segments, kapsig 3, oversampling 2) -> diagnostics ->
# small-n injection (K=1530 and K=300 at P=200 d, phase 90).
# beta Pic b stages ONLY the 8 planet products (2023-01-03); the star's own
# monitoring frames share the coordinate box and must not enter.
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTSK=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN3000-5000_Kband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
DATA=/mnt/c/Users/matth/projects/astronomy/exosat-rv/data
# viper's K-band branch is 1-indexed: order o -> drs 7-(o-1)//3, so K2166's six
# orders (07..02) are viper orders 1..18. oset 0 would seek a nonexistent order 08.
OSET="1:19"

TL_BPB='beta Pic b;* bet Pic b;05 47 17.0877 -51 03 59.441;5.160 84.041 [0.100 0.100 90];50.9307 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 16.84 (Opt) A [0.50] simbad'
TL_ABP='AB Pic b;HD 44627B;06 19 12.9130 -58 03 15.527;14.314 45.234 [0.100 0.100 90];19.9452 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 22.645 (Opt) A [0.50] simbad'
TL_CTC='CT Cha B;V* CT Cha B;11 04 09.0989 -76 27 19.330;-22.223 0.019 [0.100 0.100 90];5.2645 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 15.13 (Opt) A [0.50] simbad'

run_target() {  # run_target SLUG TARGNAME TL SRCDIR FILEGLOB
  slug=$1; targ=$2; tl=$3; src=$4; glob=$5
  echo "=== $slug ==="
  mkdir -p ${slug}_data
  rm -f ${slug}_data/*.fits
  cp -f $src/$glob ${slug}_data/ || { echo "$slug: staging failed"; return 1; }
  echo "$slug staged: $(ls ${slug}_data/*.fits | wc -l) files"

  for step in 0 1 2; do
    tag=${slug}_tpl${step}
    [ -s ${tag}_tpl.fits ] && { echo "have $tag"; continue; }
    prev=""
    [ $step -ge 1 ] && prev=${slug}_tpl$((step-1))_tpl.fits
    printf '%s\n' "$tl" > ${tag}.targ.csv
    $PY viper.py "${slug}_data/ADP*.fits" $prev -inst CRIRES -fts $FTSK \
      -targ "$targ" -tag $tag -createtpl -nocell -tpl_wave tell -oset $OSET \
      -kapsig 3 > /tmp/${tag}.log 2>&1
    echo "$tag rc=$? tpl=$(ls ${tag}_tpl.fits 2>/dev/null | wc -l)"
    [ -s ${tag}_tpl.fits ] || { tail -3 /tmp/${tag}.log; return 1; }
  done

  tag=${slug}_RV
  printf '%s\n' "$tl" > ${tag}.targ.csv
  $PY viper.py "${slug}_data/ADP*.fits" ${slug}_tpl2_tpl.fits -inst CRIRES \
    -fts $FTSK -targ "$targ" -tag $tag -nocell -oset $OSET -kapsig 3 \
    -oversampling 2 > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
  $PY $SC/m15_diag.py ${tag}.rvo.dat

  for arm in "K15 1530" "K3 300"; do
    set -- $arm
    aname=${slug}_$1; K=$2
    $PY $SC/mkplan_nod.py ${tag}.rvo.dat $SC/inject_plan_${aname}.json $K 200 90
    # per-target targ line for the injection arm:
    ( export INJTL="$tl"
      n=$($PY -c "import json;print(len(json.load(open('$SC/inject_plan_${aname}.json'))))")
      $PY $SC/mktpl.py $SC/inject_plan_${aname}.json ${slug}_tpl2_tpl.fits ~/inj/$aname
      for ((i=0;i<n;i++)); do
        t=$(printf "inj%02d" $i)
        [ -s "${aname}_${t}.rvo.dat" ] && continue
        f=$($PY -c "import json;print(json.load(open('$SC/inject_plan_${aname}.json'))[$i]['file'])")
        printf '%s\n' "$tl" > "${aname}_${t}.targ.csv"
        $PY viper.py "${slug}_data/$f" ~/inj/$aname/${t}_tpl.fits -inst CRIRES \
          -fts $FTSK -targ "$targ" -tag "${aname}_${t}" -nocell -oset $OSET \
          -kapsig 3 -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
      done )
    $PY $SC/m17_score.py $aname ${tag}.rvo.dat $SC/inject_plan_${aname}.json
  done
  echo "=== $slug done ==="
}

run_target abpicb "AB Pic b" "$TL_ABP" $DATA/abpicb_cr2res "ADP*.fits"
run_target ctchab "CT Cha B" "$TL_CTC" $DATA/ctchab_cr2res "ADP*.fits"
run_target betapicb "beta Pic b" "$TL_BPB" $DATA/betapicb_cr2res "ADP.2025-06-05T18-22-10.*.fits"
echo M17RUN_DONE
