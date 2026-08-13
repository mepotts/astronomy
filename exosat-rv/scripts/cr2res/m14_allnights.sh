#!/bin/bash
# M14 lever 1b driver: fetch + reduce every archive epoch not yet done from raw,
# then strip09 the per-nodding products into ~/viper-src/nod14/.
# Crash-safe: .fetched / .done markers per night; failed nights are skipped and listed.
# Network stages run WITHOUT cr2env sourced (its libcurl is SSL-less — M12 trap).
set -u
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res
PY=$HOME/viperenv/bin/python
LOG=$HOME/cr2res/logs
mkdir -p "$LOG" "$HOME/cr2res/raw"

$PY $SC/night_map.py > /tmp/night_map.tsv || { echo "MAP FAILED"; exit 1; }
echo "=== night map ==="; cat /tmp/night_map.tsv

FAILED=""
while IFS=$'\t' read -r night adp mjd status; do
  [ "$status" = "todo" ] || continue
  RAW=$HOME/cr2res/raw/$night
  RED=$HOME/cr2res/red/$night

  if [ ! -f "$RAW/.fetched" ]; then
    echo "=== $night: resolving raw URLs for $adp ==="
    if ! $PY $SC/urls_for_night.py "$adp" /tmp/${night}_urls.txt > "$LOG/${night}_urls.log" 2>&1; then
      echo "$night: URL RESOLUTION FAILED"; tail -3 "$LOG/${night}_urls.log"
      FAILED="$FAILED $night(urls)"; continue
    fi
    n_urls=$(wc -l < /tmp/${night}_urls.txt)
    echo "=== $night: fetching $n_urls files ==="
    mkdir -p "$RAW"; cd "$RAW" || continue
    n=0; bad=0
    while read -r u; do
      [ -z "$u" ] && continue
      n=$((n+1))
      /usr/bin/curl -sL -OJ --max-time 1800 "$u" || { echo "  FAILED $u"; bad=$((bad+1)); }
    done < /tmp/${night}_urls.txt
    for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done
    echo "$night: downloaded $n ($bad failed), $(du -sh "$RAW" | cut -f1)"
    if [ "$bad" -gt 0 ] || [ "$n" -lt 10 ]; then
      FAILED="$FAILED $night(fetch)"; continue
    fi
    touch "$RAW/.fetched"
  fi

  if [ ! -f "$RED/.done" ]; then
    echo "=== $night: reducing ==="
    if ! bash $SC/reduce_one.sh "$night" > "$LOG/${night}_reduce.log" 2>&1; then
      echo "$night: REDUCTION FAILED"; tail -8 "$LOG/${night}_reduce.log"
      FAILED="$FAILED $night(reduce)"; continue
    fi
    tail -2 "$LOG/${night}_reduce.log"
  fi

  cd ~/viper-src || exit 1
  mkdir -p nod14
  for arm in A B; do
    cp -f "$RED/cr2res_obs_nodding_extracted${arm}.fits" nod14/${night}${arm}.fits
  done
  $PY $SC/strip09.py nod14/${night}A.fits nod14/${night}B.fits > /dev/null
  rm -f nod14/${night}A.fits nod14/${night}B.fits
  echo "$night: staged nod14/${night}{A,B}_o8.fits"
done < /tmp/night_map.tsv

echo "=== SUMMARY ==="
ls ~/viper-src/nod14/*_o8.fits 2>/dev/null | wc -l
[ -n "$FAILED" ] && echo "FAILED:$FAILED"
echo M14ALLNIGHTS_DONE
