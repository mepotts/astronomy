#!/bin/bash
# M26 batch 2 — the remaining staged census targets, each through the standard
# chain (tpl0 -> RV -> diag -> verdict -> matched injection arm):
#   h81208k   HIP 81208 B, 3 K2166 nodding nights / ~105 d (second setting)
#   hd206893k HD 206893, 1 deep K2166 nodding night (single-epoch datum)
#   hd206893h HD 206893, 2 H staring nights (1 d apart)
#   hd19467   HD 19467 B, 2 H staring nights (1 d apart)
#   pds70h    PDS 70, 3 H1567 staring nights / 32 d (the system's H side)
#   m0103a    2M0103AB b, 1 K2166 pilot night
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
FTSH=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
FTSK=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN3000-5000_Kband.dat
HC="4,7,8,9,10,12,13,14,17,18,19"

TL_H81='HIP 81208 B;HD 149274B;16 35 13.8393 -35 43 28.726;-9.701 -25.913 [0.100 0.100 90];6.8424 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 0.00 (Opt) A [0.50] simbad'
TL_206='HD 206893;HD 206893;21 45 21.9053 -12 47 00.061;94.112 -0.463 [0.100 0.100 90];24.5275 [0.0300] A 2020yCat.1350....0G;v:spectroscopic -12.45 (Opt) A [0.50] simbad'
TL_194='HD 19467 B;HD 19467;03 07 18.5751 -13 45 42.418;-8.694 -260.642 [0.100 0.100 90];31.2191 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 6.95 (Opt) A [0.50] simbad'
TL_PDS='PDS 70;CD-40 8434;14 08 10.1546 -41 23 52.573;-29.697 -24.041 [0.100 0.100 90];8.8975 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 3.13 (Opt) A [0.50] simbad'
TL_M01='2M0103AB b;SCR J0103-5515C;01 03 35.6551 -55 15 56.243;100.200 -47.000 [0.100 0.100 90];21.1800 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 4.00 (Opt) A [0.50] simbad'

run_one() {  # run_one SLUG TARG TL GLOB FTS OSET
  slug=$1; targ=$2; tl=$3; glob=$4; fts=$5; oset=$6
  echo "=== $slug ==="
  mkdir -p ${slug}_data
  rm -f ${slug}_data/*.fits
  cp -f m26_data/$glob ${slug}_data/ || { echo "$slug: no data"; return 1; }
  echo "$slug staged: $(ls ${slug}_data/*.fits | wc -l)"
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

run_one h81208k "HIP 81208 B" "$TL_H81" "h81208k*_o8.fits" $FTSK "1:19"
run_one hd206893k "HD 206893" "$TL_206" "hd206893k*_o8.fits" $FTSK "1:19"
run_one hd206893h "HD 206893" "$TL_206" "hd206893h*_o8.fits" $FTSH "$HC"
run_one hd19467 "HD 19467 B" "$TL_194" "hd19467*_o8.fits" $FTSH "$HC"
run_one pds70h "PDS 70" "$TL_PDS" "pds70h*_o8.fits" $FTSH "$HC"
run_one m0103a "2M0103AB b" "$TL_M01" "m0103a*_o8.fits" $FTSK "1:19"
echo M26RUN2_DONE
