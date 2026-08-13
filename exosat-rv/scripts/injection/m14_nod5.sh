#!/bin/bash
# M14 lever 1a: the M13 recipe (M13 template, H_C orders, -kapsig 3) on the per-nodding
# A/B frames of the five from-raw nights (M12 §9b), instead of the combined products.
# The paper's favoured extraction is per-nodding-frame RVs, then binned (its Fig. 4:
# 57.68 vs 60.50 m/s mean error). One viper run over all ten frames.
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
HC="4,7,8,9,10,12,13,14,17,18,19"

# Clean staging dir with exactly the ten per-nodding frames (night1 = nodA/nodB).
mkdir -p nod14
rm -f nod14/*.fits
cp -f nod/nodA_o8.fits nod14/night1A_o8.fits
cp -f nod/nodB_o8.fits nod14/night1B_o8.fits
for n in 2 3 4 5; do
  for arm in A B; do
    cp -f nod/night${n}${arm}_o8.fits nod14/night${n}${arm}_o8.fits
  done
done
ls nod14/

cp -f full1.targ.csv M14_nod.targ.csv
$PY viper.py "nod14/night*_o8.fits" M13tpl_tpl.fits -inst CRIRES -fts $FTS \
  -targ "CD-35 2722" -tag M14_nod -nocell -oset "$HC" -kapsig 3 \
  > /tmp/M14_nod.log 2>&1
echo "M14_nod rc=$? rows=$(wc -l < M14_nod.rvo.dat 2>/dev/null)"
tail -3 /tmp/M14_nod.log
echo M14NOD_DONE
