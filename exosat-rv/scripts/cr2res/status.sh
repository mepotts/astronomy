#!/bin/bash
for n in 1 2 3 4 5; do
  R=$HOME/cr2res/raw/night$n; D=$HOME/cr2res/red/night$n
  u=$(wc -l < "$R/urls.txt" 2>/dev/null || echo 0)
  f=$(ls "$R"/*.fits 2>/dev/null | wc -l)
  s=$(du -sh "$R" 2>/dev/null | cut -f1)
  r=no; [ -f "$D/cr2res_obs_nodding_extractedA.fits" ] && r=yes
  echo "night$n  urls=$u  fits=$f  size=$s  reduced=$r"
done
echo "esorex running: $(pgrep -c esorex 2>/dev/null || echo 0)   curl: $(pgrep -c curl 2>/dev/null || echo 0)"
