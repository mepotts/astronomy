#!/bin/bash
# M21 restore: the 9-night PDS 70 rebuild FAILED its injection gate (recovery
# -62% +- 197% — the 14-file template lost its stellar lever; the quiet series it
# produced is fake-quiet and REJECTED). Re-stage exactly the original 8 products
# whose run gated at 99 +- 1% and rebuild, confirming the validated state returns.
set -u
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
SRC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/pds70_cr2res
ORIG="ADP.2025-06-06T12-42-46.834.fits ADP.2025-06-06T12-42-46.837.fits \
ADP.2025-11-12T14-02-53.421.fits ADP.2025-06-06T12-50-25.974.fits \
ADP.2025-11-12T14-25-11.813.fits ADP.2025-06-06T13-07-01.940.fits \
ADP.2025-06-06T13-07-01.934.fits ADP.2025-11-17T16-36-29.654.fits"

rm -f pds70_tpl*_tpl.fits pds70_tpl*.rvo.dat pds70_RV.rvo.dat
rm -f pds70_K15_inj*.rvo.dat pds70_K3_inj*.rvo.dat
rm -rf pds70_data
mkdir -p pds70_data
for f in $ORIG; do cp -f $SRC/$f pds70_data/; done
echo "staged $(ls pds70_data/*.fits | wc -l) (validated 6-night set)"

TL='PDS 70;CD-40 8434;14 08 10.1546 -41 23 52.573;-29.697 -24.041 [0.100 0.100 90];8.8975 [0.0300] A 2020yCat.1350....0G;v:spectroscopic 3.13 (Opt) A [0.50] simbad'
bash /mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/injection/m2x_run_target.sh \
  pds70 "PDS 70" "$TL" /mnt/c/Users/matth/projects/astronomy/exosat-rv/data/pds70_cr2res_UNUSED \
  lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN3000-5000_Kband.dat "1:19" 300
echo M21RESTORE_DONE
