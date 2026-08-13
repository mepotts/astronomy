#!/bin/bash
# Pull every raw frame + master calibration needed to reduce one CRIRES+ night.
# dataPortal sets the real filename in Content-Disposition, so -OJ is required; files
# arrive .Z (Unix compress) and gzip -d handles them.
D=$HOME/cr2res/raw/night1
mkdir -p "$D" && cd "$D" || exit 1
n=0
while read -r u; do
  [ -z "$u" ] && continue
  n=$((n+1))
  curl -sL -OJ --max-time 1800 "$u" || echo "FAILED $u"
done < /mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/17e10030-3be1-497c-afec-cf77b01ab773/scratchpad/night1_urls.txt
echo "downloaded $n"
for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done
ls -la | tail -30
du -sh "$D"
touch "$D/.fetched"
