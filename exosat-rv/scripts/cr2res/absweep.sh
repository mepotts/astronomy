#!/bin/bash
# Sweep the forward model against the A-B null test: same star, 10.6 min apart, true
# dRV = 0. Signal-free, so unlike epoch rms it cannot be improved by deleting the signal,
# and unlike GJ 229 B it needs no proxy target.
cd ~/viper-src || exit 1
export PATH="$HOME/bin:$PATH"
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
PY=~/viperenv/bin/python
SC=/mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/17e10030-3be1-497c-afec-cf77b01ab773/scratchpad
OUT=$SC/ab; mkdir -p "$OUT"
go () {
  name="$1"; shift
  for arm in A B; do
    tag="W_${name}_$arm"
    cp -f full1.targ.csv "$tag.targ.csv"
    $PY viper.py "nod/nod${arm}_o8.fits" U_mk_tpl.fits -inst CRIRES -fts "$FTS" \
        -targ "CD-35 2722" -nocell -tag "$tag" "$@" > /tmp/$tag.log 2>&1
    cp -f "$tag.rvo.dat" "$OUT/" 2>/dev/null
  done
  echo "done $name :: $*"
}
go base
go add2      -telluric add2
go tsig      -telluric sig
go tmask     -telluric mask
go dw3       -deg_wave 3
go dw4       -deg_wave 4
go ch2       -chunks 2
go ch4       -chunks 4
go ipag      -ip ag
go ipbg      -ip bg
go ipsg      -ip sg
go iphs70    -iphs 70
go add2dw3   -telluric add2 -deg_wave 3
go add2ch2   -telluric add2 -chunks 2
go dw3ch2    -deg_wave 3 -chunks 2
go tell1     -telluric add -molec H2O
go kap       -kapsig 3
echo ABSWEEPDONE
