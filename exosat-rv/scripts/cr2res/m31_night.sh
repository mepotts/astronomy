#!/bin/bash
# M31 per-night driver: banked-calib fetch -> validated reduction -> content verification.
# No cleanup in here: raw deletions are a separate, logged, human-visible step
# (LESSONS 4 sanction; M31-RESULTS.md carries the record).
#   m31_night.sh <slug>
set -u
S=$1
BASE=/mnt/c/Users/matth/projects/astronomy/exosat-rv
LOGD=$HOME/cr2res/logs_m31
mkdir -p "$LOGD"
echo "=== M31 night $S: fetch ==="
bash "$BASE/scripts/cr2res/m31_fetch_cal.sh" "$S" || { echo "M31_${S}_FETCH_FAILED"; exit 1; }
echo "=== M31 night $S: reduce ==="
bash "$BASE/scripts/cr2res/m31_reduce.sh" "$S" || { echo "M31_${S}_REDUCE_FAILED"; exit 1; }
echo "=== M31 night $S: verify contents ==="
~/viperenv/bin/python "$BASE/scripts/m31_verify.py" \
  "${RED_BASE:-$HOME/cr2res/red_m31}/$S" "$LOGD/m31_${S}_verify.json"
rc=$?
[ $rc -eq 0 ] && echo "M31_${S}_NIGHT_OK" || echo "M31_${S}_VERIFY_FAILED"
exit $rc
