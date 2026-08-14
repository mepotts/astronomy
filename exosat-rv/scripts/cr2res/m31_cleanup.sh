#!/bin/bash
# M31 sanctioned cleanup, one night: delete the night's fetched CALIB raw only --
# and only after its own reduction has verified BY CONTENTS (LESSONS 4; the
# house rule "delete raw once its reduction verifies -- the archive is the backup").
#
# Science raw is KEPT deliberately: with the masters kept in red_m31, science raw
# is what lets M32 re-run util_calib + util_extract at a different height without
# any re-fetch. Calib raw is pure archive copy (the URL list is banked).
# Nothing outside $RAW_BASE/<slug> is touched; every deletion is printed.
#   m31_cleanup.sh <slug>
set -u
S=$1
RAW=${RAW_BASE:-$HOME/cr2res/raw_m30}/$S
LOGD=$HOME/cr2res/logs_m31
VJ=$LOGD/m31_${S}_verify.json
SCI_LIST=${LOGD_M30:-$HOME/cr2res/logs_m30}/m30_${S}_sci.txt

[ -f "$VJ" ] || { echo "$S: no verify JSON at $VJ -- refusing"; exit 1; }
grep -q '"gates_failed": \[\]' "$VJ" || { echo "$S: verify gates NOT clean -- refusing"; exit 1; }
[ -s "$SCI_LIST" ] || { echo "$S: no science list $SCI_LIST -- refusing"; exit 1; }

declare -A KEEP
while read -r u; do
  [ -z "$u" ] && continue
  KEEP["$(basename "$u").fits"]=1
done < "$SCI_LIST"

ndel=0; bytes=0
for f in "$RAW"/*.fits; do
  [ -e "$f" ] || continue
  b=$(basename "$f")
  if [ -z "${KEEP[$b]:-}" ]; then
    sz=$(stat -c %s "$f")
    echo "  rm $b ($sz bytes)"
    rm -f "$f"
    ndel=$((ndel+1)); bytes=$((bytes+sz))
  fi
done
nkeep=$(ls "$RAW"/*.fits 2>/dev/null | wc -l)
echo "$S: deleted $ndel calib raw files ($((bytes/1024/1024)) MB); kept $nkeep science fits"
df -h / | tail -1
echo "M31CLEANUP_${S}_DONE"
