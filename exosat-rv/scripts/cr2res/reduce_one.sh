#!/bin/bash
# Parameterized M12 reduce_night.sh: full CRIRES+ cascade from raw for ONE night.
#   reduce_one.sh <nightname>     (expects raw in ~/cr2res/raw/<night>, writes ~/cr2res/red/<night>)
# cal_dark -> cal_flat -> cal_wave -> obs_nodding; the point is extractedA/extractedB.
N=$1
source /mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/cr2env.sh
RAW=${RAW_BASE:-$HOME/cr2res/raw}/$N
W=${RED_BASE:-$HOME/cr2res/red}/$N
CLS=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/classify.py
PY=~/viperenv/bin/python
mkdir -p "$W" && cd "$W" || exit 1

$PY "$CLS" "$RAW" > tags.tsv 2> tags.err
echo "=== $N frame inventory ==="; cut -f2 tags.tsv | sort | uniq -c
# pick TAG [WLEN] -- the optional second argument filters by wavelength setting
# (column 3 of tags.tsv). A night carrying two settings otherwise feeds both into one
# SOF, which crashes obs_nodding ("Expect only one DROT POSANG") or writes empty
# extractions (LESSONS section 4). Set WLEN=H1567 to reduce one setting of a mixed
# night; leave it unset and behaviour is exactly as before.
pick () { awk -F'	' -v t="$1" -v w="${2:-}" '$2==t && (w=="" || $3==w){print $1}' tags.tsv; }
WLEN=${WLEN:-}

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
# BPM is optional downstream ([0 to 1] in both obs recipes): a failed master
# dark degrades the reduction, it should not kill the night (M26: h81208f)
run cr2res_cal_dark dark.sof dark || echo "   ($N continuing without master dark)"
BPM=$(ls -S "$W"/cr2res_cal_dark_*bpm.fits 2>/dev/null | head -1)

{ for f in $(pick FLAT "$WLEN"); do echo "$f FLAT"; done
  for f in $(pick UTIL_WAVE_TW); do echo "$f UTIL_WAVE_TW"; done
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > flat.sof
run cr2res_cal_flat flat.sof flat || exit 1
FTW=$(ls "$W"/cr2res_cal_flat_*tw*.fits 2>/dev/null | head -1)
FMAS=$(ls "$W"/cr2res_cal_flat_*master*.fits 2>/dev/null | head -1)
FEXT=$(ls "$W"/cr2res_cal_flat_*extract*.fits 2>/dev/null | head -1)

{ for f in $(pick WAVE_UNE "$WLEN"); do echo "$f WAVE_UNE"; done
  for f in $(pick WAVE_FPET "$WLEN"); do echo "$f WAVE_FPET"; done
  [ -n "$FTW" ] && echo "$FTW CAL_FLAT_TW"
  for f in $(pick EMISSION_LINES); do echo "$f EMISSION_LINES"; done
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > wave.sof
run cr2res_cal_wave wave.sof wave || echo "   ($N continuing with flat TW)"
WTW=$(ls "$W"/cr2res_cal_wave_tw*.fits 2>/dev/null | head -1)
[ -z "$WTW" ] && WTW="$FTW"

N_NOD=$(pick OBS_NODDING_OTHER "$WLEN" | wc -l)
N_STARE=$(pick OBS_STARING_OTHER "$WLEN" | wc -l)
if [ "$N_NOD" -gt 0 ]; then
  { for f in $(pick OBS_NODDING_OTHER "$WLEN"); do echo "$f OBS_NODDING_OTHER"; done
    [ -n "$WTW" ]  && echo "$WTW CAL_WAVE_TW"
    [ -n "$FMAS" ] && echo "$FMAS CAL_FLAT_MASTER"
    [ -n "$FEXT" ] && echo "$FEXT CAL_FLAT_EXTRACT_1D"
    [ -n "$BPM" ]  && echo "$BPM CAL_DARK_BPM"
    for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
    for f in $(pick PHOTO_FLUX); do echo "$f PHOTO_FLUX"; done; } > nod.sof
  run cr2res_obs_nodding nod.sof nod || exit 1
  [ -f "$W/cr2res_obs_nodding_extractedA.fits" ] && [ -f "$W/cr2res_obs_nodding_extractedB.fits" ] \
    && touch "$W/.done" && echo "$N REDUCED OK (nodding)" || { echo "$N missing extractedA/B"; exit 1; }
elif [ "$N_STARE" -gt 0 ]; then
  # staring-mode science: one collapsed extraction per night (cr2res_obs_staring)
  { for f in $(pick OBS_STARING_OTHER "$WLEN"); do echo "$f OBS_STARING_OTHER"; done
    [ -n "$WTW" ]  && echo "$WTW CAL_WAVE_TW"
    [ -n "$BPM" ]  && echo "$BPM CAL_DARK_BPM"
    for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done; } > stare.sof
  run cr2res_obs_staring stare.sof stare || exit 1
  ls "$W"/cr2res_obs_staring_extracted*.fits > /dev/null 2>&1 \
    && touch "$W/.done" && echo "$N REDUCED OK (staring)" || { echo "$N missing staring extraction"; exit 1; }
else
  echo "$N: no science frames tagged"; exit 1
fi
