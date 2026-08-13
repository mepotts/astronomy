#!/bin/bash
# M24: the staring crumbs analyzed — AF Lep b (2 nights, 3 d apart) and 51 Eri b
# (1 night). Single-epoch science: per-target tpl0, RVs, and a matched-amplitude
# injection arm scored by per-epoch ratio. Expectation (contrast wall, M20 §6):
# ~30,000x contrast inside 0.5" — these likely measure star-dominated light, and
# the gates + spectra will say so; that datum extends the wall table either way.
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
OSET="4,7,8,9,10,12,13,14,17,18,19"

TL_AFL='AF Lep b;V* AF Lep;05 27 04.7633 -11 54 03.466;16.915 -49.318 [0.100 0.100 90];37.2539 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 20.61 (Opt) A [0.50] simbad'
TL_ERI='51 Eri b;* 51 Eri;04 37 36.1326 -02 28 24.776;44.049 -64.028 [0.100 0.100 90];33.4390 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 12.60 (Opt) A [0.50] simbad'

run_crumb() {  # run_crumb SLUG TARG TL GLOB
  slug=$1; targ=$2; tl=$3; glob=$4
  echo "=== $slug ==="
  mkdir -p ${slug}_data
  rm -f ${slug}_data/*.fits
  cp -f crumbs_data/$glob ${slug}_data/ || { echo "$slug: no data"; return 1; }
  echo "$slug staged: $(ls ${slug}_data/*.fits | wc -l)"

  tag=${slug}_tpl0
  printf '%s\n' "$tl" > ${tag}.targ.csv
  $PY viper.py "${slug}_data/*.fits" -inst CRIRES -fts $FTS -targ "$targ" \
    -tag $tag -createtpl -nocell -tpl_wave tell -oset 0:21 -kapsig 3 \
    > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? tpl=$(ls ${tag}_tpl.fits 2>/dev/null | wc -l)"
  [ -s ${tag}_tpl.fits ] || { tail -3 /tmp/${tag}.log; return 1; }

  tag=${slug}_RV
  printf '%s\n' "$tl" > ${tag}.targ.csv
  $PY viper.py "${slug}_data/*.fits" ${slug}_tpl0_tpl.fits -inst CRIRES -fts $FTS \
    -targ "$targ" -tag $tag -nocell -oset "$OSET" -kapsig 3 -oversampling 2 \
    > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
  $PY $SC/m15_diag.py ${tag}.rvo.dat

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
      -fts $FTS -targ "$targ" -tag "${aname}_${t}" -nocell -oset "$OSET" \
      -kapsig 3 -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
  done
  $PY $SC/m17_score.py $aname ${tag}.rvo.dat $SC/inject_plan_${aname}.json
  echo "=== $slug done ==="
}

run_crumb aflep "AF Lep b" "$TL_AFL" "aflep*_o8.fits"
run_crumb eri51 "51 Eri b" "$TL_ERI" "eri51_o8.fits"
echo M24RUN_DONE
