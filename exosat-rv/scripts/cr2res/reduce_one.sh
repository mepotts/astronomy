#!/bin/bash
# Parameterized M12 reduce_night.sh: full CRIRES+ cascade from raw for ONE night.
#   reduce_one.sh <nightname>     (expects raw in ~/cr2res/raw/<night>, writes ~/cr2res/red/<night>)
# cal_dark -> cal_flat -> cal_wave -> obs_nodding; the point is extractedA/extractedB.
N=$1
source /mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/cr2env.sh
RAW=$HOME/cr2res/raw/$N
W=$HOME/cr2res/red/$N
CLS=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/classify.py
PY=~/viperenv/bin/python
mkdir -p "$W" && cd "$W" || exit 1

$PY "$CLS" "$RAW" > tags.tsv 2> tags.err
echo "=== $N frame inventory ==="; cut -f2 tags.tsv | sort | uniq -c
pick () { awk -F'\t' -v t="$1" '$2==t{print $1}' tags.tsv; }

run () {  # run <recipe> <sof> <label>
  echo "--- $N $1 ---"
  esorex --output-dir="$W" "$1" "$2" > "$3.log" 2>&1
  rc=$?
  echo "   exit=$rc  products: $(grep -c 'Created product' "$3.log" 2>/dev/null)"
  [ $rc -ne 0 ] && { echo "   FAILED, tail:"; tail -12 "$3.log"; return 1; }
  return 0
}

for f in $(pick DARK); do echo "$f DARK"; done > dark.sof
[ -s dark.sof ] || { echo "$N: no DARK frames"; exit 1; }
run cr2res_cal_dark dark.sof dark || exit 1
BPM=$(ls -S "$W"/cr2res_cal_dark_*bpm.fits 2>/dev/null | head -1)

{ for f in $(pick FLAT); do echo "$f FLAT"; done
  for f in $(pick UTIL_WAVE_TW); do echo "$f UTIL_WAVE_TW"; done
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > flat.sof
run cr2res_cal_flat flat.sof flat || exit 1
FTW=$(ls "$W"/cr2res_cal_flat_*tw*.fits 2>/dev/null | head -1)
FMAS=$(ls "$W"/cr2res_cal_flat_*master*.fits 2>/dev/null | head -1)
FEXT=$(ls "$W"/cr2res_cal_flat_*extract*.fits 2>/dev/null | head -1)

{ for f in $(pick WAVE_UNE); do echo "$f WAVE_UNE"; done
  for f in $(pick WAVE_FPET); do echo "$f WAVE_FPET"; done
  [ -n "$FTW" ] && echo "$FTW CAL_FLAT_TW"
  for f in $(pick EMISSION_LINES); do echo "$f EMISSION_LINES"; done
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > wave.sof
run cr2res_cal_wave wave.sof wave || echo "   ($N continuing with flat TW)"
WTW=$(ls "$W"/cr2res_cal_wave_tw*.fits 2>/dev/null | head -1)
[ -z "$WTW" ] && WTW="$FTW"

{ for f in $(pick OBS_NODDING_OTHER); do echo "$f OBS_NODDING_OTHER"; done
  [ -n "$WTW" ]  && echo "$WTW CAL_WAVE_TW"
  [ -n "$FMAS" ] && echo "$FMAS CAL_FLAT_MASTER"
  [ -n "$FEXT" ] && echo "$FEXT CAL_FLAT_EXTRACT_1D"
  [ -n "$BPM" ]  && echo "$BPM CAL_DARK_BPM"
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  for f in $(pick PHOTO_FLUX); do echo "$f PHOTO_FLUX"; done; } > nod.sof
run cr2res_obs_nodding nod.sof nod || exit 1
[ -f "$W/cr2res_obs_nodding_extractedA.fits" ] && [ -f "$W/cr2res_obs_nodding_extractedB.fits" ] \
  && touch "$W/.done" && echo "$N REDUCED OK" || { echo "$N missing extractedA/B"; exit 1; }
