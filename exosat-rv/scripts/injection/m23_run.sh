#!/bin/bash
# M23 analysis: HD 1160 B staring-route RVs on the iteration-0 template.
# (Iteration 1 crashed on a degenerate chunk; the injection arms decide whether
# tpl0 transmits — if they pass, the ladder refinement is optional.)
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
TL='HD 1160 B;HD 1160B;00 15 57.3020 +04 15 04.010;20.150 -14.903 [0.100 0.100 90];8.2721 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 12.60 (Opt) A [0.50] simbad'
OSET="4,7,8,9,10,12,13,14,17,18,19"

printf '%s\n' "$TL" > hd1160_RV.targ.csv
$PY viper.py "hd1160_data/hd*_o8.fits" hd1160_tpl0_tpl.fits -inst CRIRES -fts $FTS \
  -targ "HD 1160 B" -tag hd1160_RV -nocell -oset "$OSET" -kapsig 3 \
  -oversampling 2 > /tmp/hd1160_RV.log 2>&1
echo "hd1160_RV rc=$? rows=$(wc -l < hd1160_RV.rvo.dat 2>/dev/null)"
[ -s hd1160_RV.rvo.dat ] || { tail -5 /tmp/hd1160_RV.log; exit 1; }

echo "=== diag ==="
$PY $SC/m15_diag.py hd1160_RV.rvo.dat
echo "=== verdict ==="
$PY $SC/m19_verdict.py hd1160_RV.rvo.dat
echo "=== blind search ==="
$PY $SC/blind_search.py hd1160_RV.rvo.dat

for arm in "hd1160_K15 1530" "hd1160_K3 300"; do
  set -- $arm
  aname=$1; K=$2
  $PY $SC/mkplan_nod.py hd1160_RV.rvo.dat $SC/inject_plan_${aname}.json $K 200 90
  $PY $SC/mktpl.py $SC/inject_plan_${aname}.json hd1160_tpl0_tpl.fits ~/inj/$aname
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
    printf '%s\n' "$TL" > "${aname}_${t}.targ.csv"
    $PY viper.py "hd1160_data/$f" ~/inj/$aname/${t}_tpl.fits -inst CRIRES -fts $FTS \
      -targ "HD 1160 B" -tag "${aname}_${t}" -nocell -oset "$OSET" -kapsig 3 \
      -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
  done
  $PY $SC/m17_score.py $aname hd1160_RV.rvo.dat $SC/inject_plan_${aname}.json
done
echo M23RUN_DONE
