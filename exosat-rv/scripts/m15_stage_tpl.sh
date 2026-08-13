#!/bin/bash
# M15: stage eta Tel B archive-route data in WSL and build the template ladder.
#   iter0: -createtpl from a flat stellar reference (no template argument)
#   iter1: -createtpl from tpl0        iter2: -createtpl from tpl1
# All creations use -kapsig 3 (the M14 lesson: identical-flag creation crashed
# curve_fit; kapsig stabilises it) and -tpl_wave tell over all 21 segments.
# Then RV runs at each iteration with the transferred config: H_C order set
# (same H1567 grid as CD-35, so the telluric-density criterion selects the same
# segments), -kapsig 3, -oversampling 2.
# NO published RVs exist for this target: adoption decisions run on the injection
# harness, never on internal look (M9/M12 rules).
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
HC="4,7,8,9,10,12,13,14,17,18,19"
SRC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/etatel_cr2res

mkdir -p etatel_data
cp -n $SRC/ADP*.fits etatel_data/ 2>/dev/null || true
echo "staged: $(ls etatel_data/*.fits | wc -l) files"

# targ line: eta Tel B, SIMBAD astrometry of the co-moving primary (parser reads
# tokens 6,7,11,16 after the first two ;-fields: pmra pmde, plx, rv).
TL='eta Tel B;* eta Tel B;19 22 51.3580 -54 25 31.570;25.824 -82.965 [0.100 0.100 90];20.6028 [0.0300] A 2020yCat.1350....0G;v:spectroscopic -1.29 (Opt) A [0.50] simbad'

run_tpl() {  # run_tpl <tag> [tplfile]
  tag=$1; tpl=${2-}
  [ -s ${tag}_tpl.fits ] && { echo "have ${tag}_tpl.fits"; return; }
  printf '%s\n' "$TL" > ${tag}.targ.csv
  $PY viper.py "etatel_data/ADP*.fits" $tpl -inst CRIRES -fts $FTS \
    -targ "eta Tel B" -tag $tag -createtpl -nocell -tpl_wave tell -oset 0:21 \
    -kapsig 3 > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? tpl=$(ls -la ${tag}_tpl.fits 2>/dev/null | wc -l)"
  tail -2 /tmp/${tag}.log
}

run_rv() {  # run_rv <tag> <tplfile>
  tag=$1; tpl=$2
  [ -s ${tag}.rvo.dat ] && [ "$(wc -l < ${tag}.rvo.dat)" -ge 2 ] && { echo "have $tag"; return; }
  printf '%s\n' "$TL" > ${tag}.targ.csv
  $PY viper.py "etatel_data/ADP*.fits" $tpl -inst CRIRES -fts $FTS \
    -targ "eta Tel B" -tag $tag -nocell -oset "$HC" -kapsig 3 -oversampling 2 \
    > /tmp/${tag}.log 2>&1
  echo "$tag rc=$? rows=$(wc -l < ${tag}.rvo.dat 2>/dev/null)"
}

run_tpl E15tpl0
run_tpl E15tpl1 E15tpl0_tpl.fits
run_tpl E15tpl2 E15tpl1_tpl.fits
run_rv  E15_R1  E15tpl1_tpl.fits
run_rv  E15_R2  E15tpl2_tpl.fits
echo M15STAGE_DONE
