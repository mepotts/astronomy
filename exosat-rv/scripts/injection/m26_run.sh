#!/bin/bash
# M26 analyses on the staged census-v2 data:
#   hip81208 — 5 H-family staring nights / ~351 d on the ~67 M_Jup companion
#   yses1    — the 2023 K2166 nodding pair (2 nights, A/B each) of the 2-planet system
# Standard chain per target: tpl0 (staring/few-epoch grade) -> RV -> diag ->
# verdict -> matched injection arm, scored by per-epoch ratio.
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
FTSH=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
FTSK=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN3000-5000_Kband.dat

TL_H81='HIP 81208 B;HD 149274B;16 35 13.8393 -35 43 28.726;-9.701 -25.913 [0.100 0.100 90];6.8424 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 0.00 (Opt) A [0.50] simbad'
TL_YS1='YSES 1 bc;TYC 8998-760-1B;13 25 12.1263 -64 56 20.689;-40.996 -17.734 [0.100 0.100 90];10.6124 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 12.90 (Opt) A [0.50] simbad'

run_one() {  # run_one SLUG TARG TL GLOB FTS OSET
  slug=$1; targ=$2; tl=$3; glob=$4; fts=$5; oset=$6
  echo "=== $slug ==="
  mkdir -p ${slug}_data
  rm -f ${slug}_data/*.fits
  cp -f m26_data/$glob ${slug}_data/ || { echo "$slug: no data"; return 1; }
  echo "$slug staged: $(ls ${slug}_data/*.fits | wc -l)"

  # creation must use the band's own index convention (K is 1-indexed — the
  # 0:21 H-band range seeks a phantom order and crashes template creation)
  case "$fts" in *Kband*) coset="1:19";; *) coset="0:21";; esac
  tag=${slug}_tpl0
  if [ ! -s ${tag}_tpl.fits ]; then
    printf '%s\n' "$tl" > ${tag}.targ.csv
    $PY viper.py "${slug}_data/*.fits" -inst CRIRES -fts $fts -targ "$targ" \
      -tag $tag -createtpl -nocell -tpl_wave tell -oset $coset -kapsig 3 \
      > /tmp/${tag}.log 2>&1
    echo "$tag rc=$? tpl=$(ls ${tag}_tpl.fits 2>/dev/null | wc -l)"
    [ -s ${tag}_tpl.fits ] || { tail -3 /tmp/${tag}.log; return 1; }
  fi

  tag=${slug}_RV
  printf '%s\n' "$tl" > ${tag}.targ.csv
  $PY viper.py "${slug}_data/*.fits" ${slug}_tpl0_tpl.fits -inst CRIRES -fts $fts \
    -targ "$targ" -tag $tag -nocell -oset "$oset" -kapsig 3 -oversampling 2 \
    > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
  $PY $SC/m15_diag.py ${tag}.rvo.dat
  $PY $SC/m19_verdict.py ${tag}.rvo.dat 2>/dev/null || true

  aname=${slug}_K3
  $PY $SC/mkplan_nod.py ${tag}.rvo.dat $SC/inject_plan_${aname}.json 300 200 90
  $PY $SC/mktpl.py $SC/inject_plan_${aname}.json ${slug}_tpl0_tpl.fits ~/inj/$aname
  n=$($PY - <<PYEOF
import json
print(len(json.load(open("$SC/inject_plan_${aname}.json"))))
PYEOF
)
  for ((i=0;i<n;i++)); do
    t=$(printf "inj%02d" $i)
    [ -s "${aname}_${t}.rvo.dat" ] && continue
    f=$($PY - <<PYEOF
import json
print(json.load(open("$SC/inject_plan_${aname}.json"))[$i]["file"])
PYEOF
)
    printf '%s\n' "$tl" > "${aname}_${t}.targ.csv"
    $PY viper.py "${slug}_data/$f" ~/inj/$aname/${t}_tpl.fits -inst CRIRES \
      -fts $fts -targ "$targ" -tag "${aname}_${t}" -nocell -oset "$oset" \
      -kapsig 3 -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
  done
  $PY $SC/m17_score.py $aname ${tag}.rvo.dat $SC/inject_plan_${aname}.json
  echo "=== $slug done ==="
}

run_one hip81208 "HIP 81208 B" "$TL_H81" "h81208*_o8.fits" $FTSH "4,7,8,9,10,12,13,14,17,18,19"
run_one yses1 "YSES 1 bc" "$TL_YS1" "yses1*_o8.fits" $FTSK "1:19"
echo M26RUN_DONE
