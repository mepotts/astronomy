#!/bin/bash
# M31: HIP 65426 HiRISE reduction -- the M29-validated fibre chain, unchanged in every
# recipe, parameter and SOF line from reduce_hirise.sh (commit 198ef74, on-sky-validated
# on bpbhi: 39/39 frames, host-telluric CCF 9.8 sigma at 0 km/s), plus footprint
# management because the data volume sits at 100% with another campaign's products on it
# (M31 disk decision -- documented in M31-RESULTS.md):
#
#   - dark MASTERS (201 MB per DIT) are deleted right after the BPM is selected:
#     nothing downstream consumes them -- util_calib takes BPM + master flat only
#   - each frame's _cal.fits + _cal_extrModel.fits (403 MB together) are deleted as
#     soon as its extr1D exists and is non-trivially sized; the extr1D (1.4 MB) and
#     slit function (0.14 MB) are kept
#   - the two large diagnostics (flat slit_model, wave map, 201 MB each) go at night end
#
# Re-derivation path if M32 needs the 2D frames: science raw stays in $RAW_BASE and the
# masters are kept, so util_calib + util_extract rebuild any deleted intermediate in
# ~30 s per frame.
#
# Note on util_trace: the validated script never calls it -- extraction rides the
# cal_wave (else cal_flat) trace-wave, which the bpbhi run proved lands on sky.
# SMOOTH_Y/MIN_CLUSTER are kept for interface parity but are unused on this path.
#
#   m31_reduce.sh <slug>     raw in $RAW_BASE/<slug>, writes $RED_BASE/<slug>
N=$1
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
source /mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/cr2env.sh
set -u
RAW=${RAW_BASE:-$HOME/cr2res/raw_m30}/$N
W=${RED_BASE:-$HOME/cr2res/red_m31}/$N
CLS=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res/classify.py
PY=~/viperenv/bin/python
SMOOTH_Y=${SMOOTH_Y:-9}          # fibre-scale, against the 401 default (unused: no util_trace on this path)
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
# footprint: dark masters are consumed by nothing in this chain -- only the BPM is
nmast=$(ls "$W"/cr2res_cal_dark_*master.fits 2>/dev/null | wc -l)
rm -f "$W"/cr2res_cal_dark_*master.fits
echo "   dark masters removed ($nmast); BPM kept: $(basename "${BPM:-none}")"

# ---- 2. flat + its trace wave ------------------------------------------------
{ for f in $(pick FLAT); do echo "$f FLAT"; done
  for f in $(pick UTIL_WAVE_TW); do echo "$f UTIL_WAVE_TW"; done
  for f in $(pick CAL_DETLIN_COEFFS); do echo "$f CAL_DETLIN_COEFFS"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > flat.sof
run cr2res_cal_flat flat.sof flat || exit 1
FTW=$(ls "$W"/cr2res_cal_flat_*tw*.fits 2>/dev/null | head -1)
FMAS=$(ls "$W"/cr2res_cal_flat_*master*.fits 2>/dev/null | head -1)

# ---- 3. wavelength solution --------------------------------------------------
# the emission-lines catalog is a STATIC calibration shipped with cr2res, chosen by
# setting; without it cal_wave exits 255 with "The emission lines catalog is needed".
SETTING=$(awk -F'	' 'NR==1{print $3}' tags.tsv)
LINES=$(ls $HOME/cr2res/calib/*/cal/lines_*_${SETTING}.fits 2>/dev/null | head -1)
echo "emission lines catalog: ${LINES:-NONE FOUND for $SETTING}"
{ for f in $(pick WAVE_UNE); do echo "$f WAVE_UNE"; done
  for f in $(pick WAVE_FPET); do echo "$f WAVE_FPET"; done
  [ -n "$FTW" ] && echo "$FTW CAL_FLAT_TW"
  [ -n "$LINES" ] && echo "$LINES EMISSION_LINES"
  for f in $(pick EMISSION_LINES); do echo "$f EMISSION_LINES"; done
  [ -n "$BPM" ] && echo "$BPM CAL_DARK_BPM"; } > wave.sof
run cr2res_cal_wave wave.sof wave || echo "   (continuing with flat TW)"
WTW=$(ls "$W"/cr2res_cal_wave_tw*.fits 2>/dev/null | head -1)
[ -z "$WTW" ] && WTW="$FTW"
echo "trace wave in use: $(basename ${WTW:-NONE})"

# ---- 4. calibrate + extract each science frame -------------------------------
# The bright short-DIT frames are the HOST down the same fibre (M29 section 16); the
# fibre output does not move, so the same trace applies to host and deep frames.
mkdir -p ext
nsci=0; next=0
for f in $(pick OBS_STARING_OTHER) $(pick OBS_NODDING_OTHER); do
  b=$(basename "$f" .fits); nsci=$((nsci+1))
  { echo "$f OBS_STARING_OTHER"
    [ -n "$BPM" ]  && echo "$BPM CAL_DARK_BPM"
    [ -n "$FMAS" ] && echo "$FMAS CAL_FLAT_MASTER"; } > ext/$b.calib.sof
  esorex --output-dir="$W/ext" cr2res_util_calib ext/$b.calib.sof > ext/$b.calib.log 2>&1
  # util_calib names its product after the INPUT frame, not a fixed product name.
  CAL=$(ls -t "$W"/ext/${b}*calibrated*.fits 2>/dev/null | head -1)
  [ -z "$CAL" ] && { echo "  $b: util_calib produced nothing"; tail -3 ext/$b.calib.log; continue; }
  [ "$CAL" != "$W/ext/${b}_cal.fits" ] && mv -f "$CAL" "ext/${b}_cal.fits"
  { echo "$W/ext/${b}_cal.fits UTIL_CALIB"
    [ -n "$WTW" ] && echo "$WTW UTIL_WAVE_TW"; } > ext/$b.ext.sof
  esorex --output-dir="$W/ext" cr2res_util_extract \
      --height=$EXT_HEIGHT --method=$EXT_METHOD --smooth_slit=1.0 \
      ext/$b.ext.sof > ext/$b.ext.log 2>&1
  E=$(ls -t "$W"/ext/*extr1D*.fits 2>/dev/null | grep -v "_extr1D.fits$" | head -1)
  [ -z "$E" ] && E=$(ls -t "$W"/ext/${b}*extr*.fits 2>/dev/null | grep -v "extrModel\|extrSlitFu" | head -1)
  ok=""
  if [ -n "$E" ] && [ "$E" != "$W/ext/${b}_extr1D.fits" ]; then
    mv -f "$E" "ext/${b}_extr1D.fits"; next=$((next+1)); ok=yes
  elif [ -f "$W/ext/${b}_extr1D.fits" ]; then next=$((next+1)); ok=yes
  else echo "  $b: no extraction"; tail -3 ext/$b.ext.log; fi
  # footprint: drop the 403 MB of per-frame intermediates once the extr1D exists and
  # is non-trivially sized (an empty-table product would be far under 200 kB).
  if [ -n "$ok" ] && [ -n "$(find "$W/ext" -maxdepth 1 -name "${b}_extr1D.fits" -size +200k -print -quit)" ]; then
    rm -f "$W/ext/${b}_cal.fits" "$W/ext/${b}_cal_extrModel.fits"
  else
    [ -n "$ok" ] && echo "  $b: extr1D SUSPICIOUSLY SMALL -- keeping _cal/_extrModel for diagnosis"
  fi
done
echo "=== $N: $nsci science frames, $next extracted ==="
ls "$W"/ext/*_extr1D.fits 2>/dev/null | wc -l
# footprint: the two large diagnostics are re-derivable and consumed by nothing downstream
[ $next -gt 0 ] && rm -f "$W"/cr2res_cal_flat_*slit_model.fits "$W"/cr2res_cal_wave_wave_map*.fits
df -h / | tail -1
[ $next -gt 0 ] && touch "$W/.done" && echo "$N HIRISE REDUCED OK" || echo "$N NO EXTRACTIONS"
