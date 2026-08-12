#!/bin/bash
# M23: HD 1160 B — nine H1567 staring nights (DIT 1200 s on the ~35 M_Jup BD at
# ~0.8", ~70x contrast) + the 2022 K pilot night. Serial fetch (m19 resolver),
# reduce via the staring branch of reduce_one.sh, stage the collapsed extraction
# per night into ~/viper-src/hd1160_data/ stripped to orders 02-08.
set -u
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res
PY=$HOME/viperenv/bin/python
export RAW_BASE=$HOME/cr2res/raw_hd1160
export RED_BASE=$HOME/cr2res/red_hd1160
LOG=$HOME/cr2res/logs_hd1160
mkdir -p "$LOG" "$RAW_BASE" "$RED_BASE"

NIGHTS="${*:-2024-10-24 2024-10-25 2024-11-22 2024-11-23 2024-11-28 2024-11-29 2024-12-01 2024-12-02 2024-12-04}"
OBJ="HD  1160,HD 1160"

FAILED=""
for night in $NIGHTS; do
  ep=hd${night//-/}
  RAW=$RAW_BASE/$ep
  RED=$RED_BASE/$ep

  if [ ! -f "$RAW/.fetched" ]; then
    echo "=== $ep: resolving ==="
    if ! $PY $SC/m19_urls_from_raw.py "$night" "$OBJ" /tmp/${ep}_urls.txt \
        > "$LOG/${ep}_urls.log" 2>&1; then
      echo "$ep: URL RESOLUTION FAILED"; tail -3 "$LOG/${ep}_urls.log"
      FAILED="$FAILED $ep(urls)"; continue
    fi
    echo "=== $ep: fetching $(wc -l < /tmp/${ep}_urls.txt) files ==="
    mkdir -p "$RAW"; cd "$RAW" || continue
    n=0; bad=0
    while read -r u; do
      [ -z "$u" ] && continue
      b=$(basename "$u")
      if [ -n "$(find . -maxdepth 1 -name "${b}*" -size +1M -print -quit)" ]; then continue; fi
      rm -f "${b}"* 2>/dev/null
      n=$((n+1))
      /usr/bin/curl -sL -OJ --retry 3 --retry-delay 20 --max-time 1800 "$u" \
        || { echo "  FAILED $u"; bad=$((bad+1)); }
    done < /tmp/${ep}_urls.txt
    for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done
    have=$(ls *.fits 2>/dev/null | wc -l)
    echo "$ep: attempted $n ($bad failed), $have on disk, $(du -sh "$RAW" | cut -f1)"
    if [ "$have" -lt 8 ]; then FAILED="$FAILED $ep(fetch)"; continue; fi
    touch "$RAW/.fetched"
  fi

  if [ ! -f "$RED/.done" ]; then
    echo "=== $ep: reducing (staring) ==="
    if ! bash $SC/reduce_one.sh "$ep" > "$LOG/${ep}_reduce.log" 2>&1; then
      echo "$ep: REDUCTION FAILED"; tail -8 "$LOG/${ep}_reduce.log"
      FAILED="$FAILED $ep(reduce)"; continue
    fi
    tail -2 "$LOG/${ep}_reduce.log"
  fi

  cd ~/viper-src || exit 1
  mkdir -p hd1160_data
  ex=$(ls "$RED"/cr2res_obs_staring_extracted*.fits 2>/dev/null | head -1)
  [ -z "$ex" ] && { echo "$ep: no staring extraction"; FAILED="$FAILED $ep(stage)"; continue; }
  cp -f "$ex" hd1160_data/${ep}.fits
  $PY $SC/strip09.py hd1160_data/${ep}.fits > /dev/null 2>&1 \
    && rm -f hd1160_data/${ep}.fits \
    || mv -f hd1160_data/${ep}.fits hd1160_data/${ep}_o8.fits
  echo "$ep: staged hd1160_data/${ep}_o8.fits"
done

echo "=== SUMMARY ==="
ls ~/viper-src/hd1160_data/*_o8.fits 2>/dev/null | wc -l
[ -n "$FAILED" ] && echo "FAILED:$FAILED"
echo M23NIGHTS_DONE
