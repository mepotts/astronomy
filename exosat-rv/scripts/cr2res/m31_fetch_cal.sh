#!/bin/bash
# M31: fetch the banked minimal-calib list for one HIP 65426 HiRISE night.
# M30 banked the lists (~/cr2res/logs_m30/m30_<slug>_cal.txt, written inside WSL, LF);
# science frames are already staged and size-validated in ~/cr2res/raw_m30/<slug>.
#
# LESSONS rules honoured: serial fetches, 3-try loop with sleeps per file,
# size-validated skip-existing, judge by files on disk never exit status (3.6);
# refuse a CRLF list outright rather than rediscover 5/18 (commit 2e0781b).
#   m31_fetch_cal.sh <slug>
set -u
S=$1
RAW_BASE=${RAW_BASE:-$HOME/cr2res/raw_m30}
LOGD=${LOGD:-$HOME/cr2res/logs_m30}
LIST=$LOGD/m30_${S}_cal.txt
DEST=$RAW_BASE/$S

[ -s "$LIST" ] || { echo "$S: no banked list $LIST"; exit 1; }
if file "$LIST" | grep -q CRLF; then
  echo "$S: $LIST has CRLF line endings -- refusing (LESSONS 5/18)"; exit 1
fi
avail_kb=$(df --output=avail / | tail -1 | tr -d ' ')
if [ "$avail_kb" -lt 3000000 ]; then
  echo "$S: only ${avail_kb} kB free on the data volume -- below the 3 GB floor, refusing"
  exit 1
fi

mkdir -p "$DEST"; cd "$DEST" || exit 1
n=0; bad=0
while read -r u; do
  [ -z "$u" ] && continue
  b=$(basename "$u")
  if [ -n "$(find . -maxdepth 1 -name "${b}*" -size +1M -print -quit)" ]; then
    continue
  fi
  rm -f "${b}"* 2>/dev/null
  n=$((n+1))
  got=""
  for t in 1 2 3; do
    /usr/bin/curl -sL -OJ --max-time 1800 "$u" 2>/dev/null
    if [ -n "$(find . -maxdepth 1 -name "${b}*" -size +1M -print -quit)" ]; then
      got=yes; break
    fi
    sleep $((10 * t))
  done
  [ -z "$got" ] && { echo "  FAILED $b"; bad=$((bad+1)); }
  sleep 2
done < "$LIST"
for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done

want=$(wc -l < "$LIST")
have_total=$(ls *.fits 2>/dev/null | wc -l)
echo "$S: attempted $n, failed $bad; want $want calibs; $have_total fits now in $DEST (sci+cal)"
df -h / | tail -1
echo "M31FETCH_${S}_DONE"
