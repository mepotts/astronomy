#!/bin/bash
# HiRISE (fibre-fed) reduction driver.
#
# The obs_* recipes are slit-geometry wrappers and neither applies to HiRISE data:
# obs_nodding needs A/B pairs (SEQ NODPOS is None here) and obs_staring fits a slit
# profile across the full ~180 px order height, while a fibre trace is 2-9 px.
# cr2res ships the pieces underneath, so this drives them directly:
#
#   cal_dark -> cal_flat -> cal_wave        (slit-independent, unchanged)
#   util_calib -> util_trace -> util_extract  (fibre-scale parameters)
#
# The trace defaults are the whole problem: util_trace smooths by 401 px in y before
# detection, which erases a 5 px trace. See LESSONS section 4 and M29-RESULTS section 15.
#
#   reduce_hirise.sh <nightname>
# expects raw in $RAW_BASE/<night>, writes $RED_BASE/<night>
set -u
N=$1
source /mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/cr2env.sh
RAW=${RAW_BASE:-$HOME/cr2res/raw_m26}/$N
W=${RED_BASE:-$HOME/cr2res/red_m26}/$N
CLS=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/classify.py
PY=~/viperenv/bin/python
SMOOTH_Y=${SMOOTH_Y:-9}          # fibre-scale, against the 401 default
MIN_CLUSTER=${MIN_CLUSTER:-20}
EXT_HEIGHT=${EXT_HEIGHT:-9}
EXT_METHOD=${EXT_METHOD:-SUM}

mkdir -p "$W" && cd "$W" || exit 1
$PY "$CLS" "$RAW" > tags.tsv 2> tags.err
echo "=== $N inventory ==="; cut -f2 tags.tsv | sort | uniq -c
pick () { awk -F'\t' -v t="$1" -v d="${2:-}" '$2==t && (d=="" || $4==d){print $1}' tags.tsv; }

run () {  # run <recipe> <sof> <label> [extra args...]
  local r=$1 sof=$2 lab=$3; shift 3
  echo "--- $N $r ---"
  esorex --output-dir="$W" "$r" "$@" "$sof" > "$lab.log" 2>&1
  local rc=$?
  echo "   exit=$rc  products=$(grep -c 'Created product' "$lab.log" 2>/dev/null)"
  [ $rc -ne 0 ] && { echo "   FAILED, tail:"; tail -8 "$lab.log"; return 1; }
  return 0
}

# ---- 1. darks, one master per DIT -------------------------------------------
for f in $(pick DARK); do echo "$f DARK"; done > dark.sof
[ -s dark.sof ] || { echo "$N: no darks"; exit 1; }
run cr2res_cal_dark dark.sof dark || echo "   (continuing without master dark)"
BPM=$(ls -S "$W"/cr2res_cal_dark_*bpm.fits 2>/dev/null | head -1)

# ---- 2. flat + its trace wave ------------------------------------------------
{ for f in $(pick FLAT); do echo "$f FLAT"; done
  for f in $(pick UTIL_WAVE_TW); do echo "$f UTIL_WAVE_TW"; done
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > flat.sof
run cr2res_cal_flat flat.sof flat || exit 1
FTW=$(ls "$W"/cr2res_cal_flat_*tw*.fits 2>/dev/null | head -1)
FMAS=$(ls "$W"/cr2res_cal_flat_*master*.fits 2>/dev/null | head -1)

# ---- 3. wavelength solution --------------------------------------------------
{ for f in $(pick WAVE_UNE); do echo "$f WAVE_UNE"; done
  for f in $(pick WAVE_FPET); do echo "$f WAVE_FPET"; done
  [ -n "$FTW" ] && echo "$FTW CAL_FLAT_TW"
  for f in $(pick EMISSION_LINES); do echo "$f EMISSION_LINES"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > wave.sof
run cr2res_cal_wave wave.sof wave || echo "   (continuing with flat TW)"
WTW=$(ls "$W"/cr2res_cal_wave_tw*.fits 2>/dev/null | head -1)
[ -z "$WTW" ] && WTW="$FTW"
echo "trace wave in use: $(basename ${WTW:-NONE})"

# ---- 4. calibrate + extract each science frame -------------------------------
# The bright short-DIT frames are the HOST down the same fibre (M29 section 16); they
# locate the trace far more easily than the faint deep frames, and the fibre output does
# not move, so the same trace applies to both.
mkdir -p ext
nsci=0; next=0
for f in $(pick OBS_STARING_OTHER) $(pick OBS_NODDING_OTHER); do
  b=$(basename "$f" .fits); nsci=$((nsci+1))
  { echo "$f OBS_STARING_OTHER"
    [ -n "$BPM" ]  && echo "$BPM CAL_DARK_BPM"
    [ -n "$FMAS" ] && echo "$FMAS CAL_FLAT_MASTER"; } > ext/$b.calib.sof
  esorex --output-dir="$W/ext" cr2res_util_calib ext/$b.calib.sof > ext/$b.calib.log 2>&1
  CAL=$(ls -t "$W"/ext/cr2res_util_calib_calibrated_collapsed.fits 2>/dev/null | head -1)
  [ -z "$CAL" ] && { echo "  $b: util_calib produced nothing"; continue; }
  mv -f "$CAL" "ext/${b}_cal.fits"
  { echo "$W/ext/${b}_cal.fits UTIL_CALIB"
    [ -n "$WTW" ] && echo "$WTW UTIL_WAVE_TW"; } > ext/$b.ext.sof
  esorex --output-dir="$W/ext" cr2res_util_extract \
      --height=$EXT_HEIGHT --method=$EXT_METHOD --smooth_slit=1.0 \
      ext/$b.ext.sof > ext/$b.ext.log 2>&1
  E=$(ls -t "$W"/ext/cr2res_util_extract_extr1D.fits 2>/dev/null | head -1)
  if [ -n "$E" ]; then mv -f "$E" "ext/${b}_extr1D.fits"; next=$((next+1)); fi
done
echo "=== $N: $nsci science frames, $next extracted ==="
ls "$W"/ext/*_extr1D.fits 2>/dev/null | wc -l
[ $next -gt 0 ] && touch "$W/.done" && echo "$N HIRISE REDUCED OK" || echo "$N NO EXTRACTIONS"
