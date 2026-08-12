#!/bin/bash
# Generic per-target recipe runner — the M15/M17 pattern, parameterized, so new
# targets need a config block rather than a new script.
#   m2x_run_target.sh SLUG TARGNAME TARGLINE DATADIR FTS OSET [K_matched]
# Does: stage -> template ladder (iter0->1->2, kapsig creation) -> RV run
# (kapsig 3, oversampling 2) -> diagnostics -> small-n injections (K=1530 and
# amplitude-matched, P=200 d phase 90) scored by per-epoch ratio.
# Adoption rules ride along: nothing judged on internal look; injection decides.
set -u
SLUG=$1; TARG=$2; TL=$3; SRC=$4; FTS=$5; OSET=$6; KM=${7:-300}
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection

mkdir -p ${SLUG}_data
cp -n $SRC/*.fits ${SLUG}_data/ 2>/dev/null || true
echo "$SLUG staged: $(ls ${SLUG}_data/*.fits | wc -l) files"

for step in 0 1 2; do
  tag=${SLUG}_tpl${step}
  [ -s ${tag}_tpl.fits ] && { echo "have $tag"; continue; }
  prev=""
  [ $step -ge 1 ] && prev=${SLUG}_tpl$((step-1))_tpl.fits
  printf '%s\n' "$TL" > ${tag}.targ.csv
  $PY viper.py "${SLUG}_data/*.fits" $prev -inst CRIRES -fts $FTS \
    -targ "$TARG" -tag $tag -createtpl -nocell -tpl_wave tell -oset $OSET \
    -kapsig 3 > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? tpl=$(ls ${tag}_tpl.fits 2>/dev/null | wc -l)"
  [ -s ${tag}_tpl.fits ] || { tail -3 /tmp/${tag}.log; exit 1; }
done

tag=${SLUG}_RV
printf '%s\n' "$TL" > ${tag}.targ.csv
$PY viper.py "${SLUG}_data/*.fits" ${SLUG}_tpl2_tpl.fits -inst CRIRES -fts $FTS \
  -targ "$TARG" -tag $tag -nocell -oset $OSET -kapsig 3 -oversampling 2 \
  > /tmp/${tag}.log 2>&1
echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
$PY $SC/m15_diag.py ${tag}.rvo.dat
$PY $SC/m19_verdict.py ${tag}.rvo.dat 2>/dev/null || true

for arm in "K15 1530" "K3 $KM"; do
  set -- $arm
  aname=${SLUG}_$1; K=$2
  $PY $SC/mkplan_nod.py ${tag}.rvo.dat $SC/inject_plan_${aname}.json $K 200 90
  $PY $SC/mktpl.py $SC/inject_plan_${aname}.json ${SLUG}_tpl2_tpl.fits ~/inj/$aname
  n=$($PY -c "import json;print(len(json.load(open('$SC/inject_plan_${aname}.json'))))")
  for ((i=0;i<n;i++)); do
    t=$(printf "inj%02d" $i)
    [ -s "${aname}_${t}.rvo.dat" ] && continue
    f=$($PY -c "import json;print(json.load(open('$SC/inject_plan_${aname}.json'))[$i]['file'])")
    printf '%s\n' "$TL" > "${aname}_${t}.targ.csv"
    $PY viper.py "${SLUG}_data/$f" ~/inj/$aname/${t}_tpl.fits -inst CRIRES \
      -fts $FTS -targ "$TARG" -tag "${aname}_${t}" -nocell -oset $OSET \
      -kapsig 3 -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
  done
  $PY $SC/m17_score.py $aname ${tag}.rvo.dat $SC/inject_plan_${aname}.json
done
echo "M2X_${SLUG}_DONE"
