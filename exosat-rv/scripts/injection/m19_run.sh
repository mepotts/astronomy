#!/bin/bash
# M19 endgame: the beta Pic b 4-epoch K2166 series (901 d) — the first
# multi-epoch RV constraint on a directly imaged planet.
# Stages the 2023-01-03 sub-exposure products (M17) plus the three from-raw
# nights' A/B frames, one viper run on the M17 iteration-2 template, then the
# verdict (chi2 + variance K-exclusion) and per-frame injection arms.
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTSK=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN3000-5000_Kband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection
OSET="1:19"
TL='beta Pic b;* bet Pic b;05 47 17.0877 -51 03 59.441;5.160 84.041 [0.100 0.100 90];50.9307 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 16.84 (Opt) A [0.50] simbad'

mkdir -p bpb_all
rm -f bpb_all/*.fits
cp -f betapicb_data/ADP*.fits bpb_all/
cp -f bpb_nod/*_k6.fits bpb_all/ 2>/dev/null || true
echo "frames staged: $(ls bpb_all/*.fits | wc -l)"

printf '%s\n' "$TL" > M19_BPB.targ.csv
$PY viper.py "bpb_all/*.fits" betapicb_tpl2_tpl.fits -inst CRIRES -fts $FTSK \
  -targ "beta Pic b" -tag M19_BPB -nocell -oset $OSET -kapsig 3 -oversampling 2 \
  > /tmp/M19_BPB.log 2>&1
echo "M19_BPB rc=$? rows=$(wc -l < M19_BPB.rvo.dat 2>/dev/null)"

echo "=== diag ==="
$PY $SC/m15_diag.py M19_BPB.rvo.dat
echo "=== verdict ==="
$PY $SC/m19_verdict.py M19_BPB.rvo.dat

for arm in "M19K15 1530" "M19K3 300"; do
  set -- $arm
  aname=$1; K=$2
  $PY $SC/mkplan_nod.py M19_BPB.rvo.dat $SC/inject_plan_${aname}.json $K 200 90
  $PY $SC/mktpl.py $SC/inject_plan_${aname}.json betapicb_tpl2_tpl.fits ~/inj/$aname
  n=$($PY -c "import json;print(len(json.load(open('$SC/inject_plan_${aname}.json'))))")
  for ((i=0;i<n;i++)); do
    t=$(printf "inj%02d" $i)
    [ -s "${aname}_${t}.rvo.dat" ] && continue
    f=$($PY -c "import json;print(json.load(open('$SC/inject_plan_${aname}.json'))[$i]['file'])")
    printf '%s\n' "$TL" > "${aname}_${t}.targ.csv"
    $PY viper.py "bpb_all/$f" ~/inj/$aname/${t}_tpl.fits -inst CRIRES -fts $FTSK \
      -targ "beta Pic b" -tag "${aname}_${t}" -nocell -oset $OSET -kapsig 3 \
      -oversampling 2 > /tmp/${aname}_${t}.log 2>&1
  done
  $PY $SC/m17_score.py $aname M19_BPB.rvo.dat $SC/inject_plan_${aname}.json
done
echo M19RUN_DONE
