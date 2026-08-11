#!/bin/bash
# Unattended: for each extra night, resolve -> download -> reduce -> viper A/B sweep.
# Resumable: every stage drops a marker and is skipped if already done.
SC=/mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/17e10030-3be1-497c-afec-cf77b01ab773/scratchpad
# NOTE: do NOT source cr2env.sh here. The minimal libcurl built into the cr2res prefix
# has no SSL and sits on LD_LIBRARY_PATH, which shadows the system libcurl for EVERY
# binary in the shell -- even /usr/bin/curl returns HTTP 000. Network stages must run in
# a clean shell; reduce_night.sh sources the env itself for esorex.
PY=~/viperenv/bin/python
export PATH=/usr/bin:/bin:$PATH
FTS=lib/CRIRES/FTS/CRp_SGC2_FTStmpl-HR0p007-WN5000-10000_Hband.dat
OUT=$SC/ab; mkdir -p "$OUT"
CFGS="base: add2:-telluric_add2 add2dw3:-telluric_add2|-deg_wave_3 kap:-kapsig_3 dw3:-deg_wave_3"

declare -A ADP=( [night2]=ADP.2025-05-26T13-07-19.921.fits
                 [night3]=ADP.2025-05-26T12-01-48.920.fits
                 [night4]=ADP.2025-05-26T11-57-49.667.fits
                 [night5]=ADP.2025-05-26T11-52-33.101.fits )

for N in night2 night3 night4 night5; do
  D=$HOME/cr2res/raw/$N; W=$HOME/cr2res/red/$N
  mkdir -p "$D" "$W"
  echo "########## $N (${ADP[$N]})"

  # 1. resolve
  if [ ! -s "$D/urls.txt" ]; then
    $PY $SC/urls_for_night.py "${ADP[$N]}" "$D/urls.txt" || { echo "$N resolve FAILED"; continue; }
  fi
  echo "  urls: $(wc -l < "$D/urls.txt")"

  # 2. download (hardlink anything already fetched for another night)
  if [ ! -f "$D/.fetched" ]; then
    ( cd "$D" || exit 1
      while read -r u; do
        [ -z "$u" ] && continue
        nm=$(basename "${u%%\?*}")
        prev=$(ls $HOME/cr2res/raw/*/${nm}*.fits 2>/dev/null | head -1)
        if [ -n "$prev" ]; then ln -f "$prev" "./$(basename "$prev")" 2>/dev/null && continue; fi
        curl -sL -OJ --max-time 1800 "$u"
      done < urls.txt
      for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done )
    touch "$D/.fetched"
  fi
  echo "  files: $(ls "$D"/*.fits 2>/dev/null | wc -l)  size: $(du -sh "$D" | cut -f1)"

  # 3. reduce
  if [ ! -f "$W/.done" ]; then
    sed "s|raw/night1|raw/$N|g; s|red/night1|red/$N|g" $SC/reduce_night.sh > /tmp/red_$N.sh
    bash /tmp/red_$N.sh > "$HOME/cr2res/reduce_$N.log" 2>&1
  fi
  if [ ! -f "$W/cr2res_obs_nodding_extractedA.fits" ]; then
    echo "  REDUCTION FAILED"; tail -4 "$HOME/cr2res/reduce_$N.log"; continue
  fi
  echo "  reduced OK"

  # 4. viper A/B sweep
  cd ~/viper-src || exit 1
  mkdir -p nod
  cp -f "$W/cr2res_obs_nodding_extractedA.fits" nod/${N}A.fits
  cp -f "$W/cr2res_obs_nodding_extractedB.fits" nod/${N}B.fits
  $PY $SC/strip09.py nod/${N}A.fits nod/${N}B.fits > /dev/null
  for spec in $CFGS; do
    cname=${spec%%:*}; argstr=${spec#*:}
    args=$(echo "$argstr" | tr '|' ' ' | tr '_' ' ')
    for arm in A B; do
      tag="X${N}_${cname}_$arm"
      cp -f full1.targ.csv "$tag.targ.csv"
      $PY viper.py "nod/${N}${arm}_o8.fits" U_mk_tpl.fits -inst CRIRES -fts "$FTS" \
          -targ "CD-35 2722" -nocell -tag "$tag" $args > /tmp/$tag.log 2>&1
      cp -f "$tag.rvo.dat" "$OUT/" 2>/dev/null
    done
  done
  echo "  viper sweep done"
  touch "$W/.swept"
done
echo ALLNIGHTSDONE
