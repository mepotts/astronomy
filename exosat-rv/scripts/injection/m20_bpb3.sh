#!/bin/bash
# M20 v3: beta Pic b with the stellar-contamination orders masked.
# Template: the v2 multi-epoch build (bpb2_tpl2). Orders dropped: o8 (the host's
# Br-gamma line lives at 2166 nm — physics, a priori) and o3,o4,o6,o7,o15,o16
# (unstable in the v2 injection arms — the sanctioned M13 drop rule).
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
FTSK=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN3000-5000_Kband.dat
TL='beta Pic b;* bet Pic b;05 47 17.0877 -51 03 59.441;5.160 84.041 [0.100 0.100 90];50.9307 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 16.84 (Opt) A [0.50] simbad'
OSET="1,2,5,9,10,11,12,13,14,17,18"

printf '%s\n' "$TL" > bpb3_RV.targ.csv
$PY viper.py "bpb2_data/*.fits" bpb2_tpl2_tpl.fits -inst CRIRES -fts $FTSK \
  -targ "beta Pic b" -tag bpb3_RV -nocell -oset "$OSET" -kapsig 3 \
  -oversampling 2 > /tmp/bpb3_RV.log 2>&1
echo "bpb3_RV rc=$? rows=$(wc -l < bpb3_RV.rvo.dat 2>/dev/null)"
[ -s bpb3_RV.rvo.dat ] || { tail -5 /tmp/bpb3_RV.log; exit 1; }

echo "=== diag ==="
$PY $SC/m15_diag.py bpb3_RV.rvo.dat
echo "=== verdict ==="
$PY $SC/m19_verdict.py bpb3_RV.rvo.dat
echo "=== blind search (binned) ==="
$PY $SC/blind_search.py bpb3_RV.rvo.dat --nod

for arm in "bpb3_K15 1530" "bpb3_K3 300"; do
  set -- $arm
  aname=$1; K=$2
  $PY $SC/mkplan_nod.py bpb3_RV.rvo.dat $SC/inject_plan_${aname}.json $K 200 90
  $PY $SC/mktpl.py $SC/inject_plan_${aname}.json bpb2_tpl2_tpl.fits ~/inj/$aname
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
    $PY viper.py "bpb2_data/$f" ~/inj/$aname/${t}_tpl.fits -inst CRIRES -fts $FTSK \
      -targ "beta Pic b" -tag "${aname}_${t}" -nocell -oset "$OSET" -kapsig 3 \
      -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
  done
  $PY $SC/m17_score.py $aname bpb3_RV.rvo.dat $SC/inject_plan_${aname}.json
done
echo BPB3_DONE
