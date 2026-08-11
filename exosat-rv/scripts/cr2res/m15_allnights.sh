#!/bin/bash
# M15: fetch + reduce every eta Tel B H1567 epoch from raw, per ADP product
# (two nights carry two independent visits; each gets its own reduction dir).
# Reuses the parameterized M14 pieces: urls_for_night.py (ADP_DIR env),
# reduce_one.sh (RAW_BASE/RED_BASE env), strip09.py. Per-nodding products land in
# ~/viper-src/etatel_nod/. Crash-safe: .fetched/.done markers, skip logic.
set -u
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res
PY=$HOME/viperenv/bin/python
export ADP_DIR=/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/spectra_etatel
export RAW_BASE=$HOME/cr2res/raw_etatel
export RED_BASE=$HOME/cr2res/red_etatel
LOG=$HOME/cr2res/logs_etatel
mkdir -p "$LOG" "$RAW_BASE" "$RED_BASE"

# map: et01..etNN in MJD order, H1567 only
$PY - <<'PYEOF' > /tmp/et_map.tsv
import glob, os
from astropy.io import fits
rows = []
for f in sorted(glob.glob(os.path.join(os.environ["ADP_DIR"], "ADP*.fits"))):
    h = fits.getheader(f)
    wlen = h.get("HIERARCH ESO INS WLEN ID") or h.get("ESO INS WLEN ID")
    if wlen != "H1567":
        continue
    rows.append((float(h["MJD-OBS"]), os.path.basename(f)))
rows.sort()
for i, (mjd, adp) in enumerate(rows, 1):
    print(f"et{i:02d}\t{adp}\t{mjd:.5f}")
PYEOF
echo "=== epoch map ==="; cat /tmp/et_map.tsv

FAILED=""
while IFS=$'\t' read -r ep adp mjd; do
  RAW=$RAW_BASE/$ep
  RED=$RED_BASE/$ep

  if [ ! -f "$RAW/.fetched" ]; then
    echo "=== $ep: resolving raw URLs for $adp ==="
    if ! $PY $SC/urls_for_night.py "$adp" /tmp/${ep}_urls.txt > "$LOG/${ep}_urls.log" 2>&1; then
      echo "$ep: URL RESOLUTION FAILED"; tail -3 "$LOG/${ep}_urls.log"
      FAILED="$FAILED $ep(urls)"; continue
    fi
    n_urls=$(wc -l < /tmp/${ep}_urls.txt)
    echo "=== $ep: fetching $n_urls files ==="
    mkdir -p "$RAW"; cd "$RAW" || continue
    n=0; bad=0
    while read -r u; do
      [ -z "$u" ] && continue
      n=$((n+1))
      /usr/bin/curl -sL -OJ --max-time 1800 "$u" || { echo "  FAILED $u"; bad=$((bad+1)); }
    done < /tmp/${ep}_urls.txt
    for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done
    echo "$ep: downloaded $n ($bad failed), $(du -sh "$RAW" | cut -f1)"
    if [ "$bad" -gt 0 ] || [ "$n" -lt 10 ]; then
      FAILED="$FAILED $ep(fetch)"; continue
    fi
    touch "$RAW/.fetched"
  fi

  if [ ! -f "$RED/.done" ]; then
    echo "=== $ep: reducing ==="
    if ! bash $SC/reduce_one.sh "$ep" > "$LOG/${ep}_reduce.log" 2>&1; then
      echo "$ep: REDUCTION FAILED"; tail -8 "$LOG/${ep}_reduce.log"
      FAILED="$FAILED $ep(reduce)"; continue
    fi
    tail -2 "$LOG/${ep}_reduce.log"
  fi

  cd ~/viper-src || exit 1
  mkdir -p etatel_nod
  for arm in A B; do
    cp -f "$RED/cr2res_obs_nodding_extracted${arm}.fits" etatel_nod/${ep}${arm}.fits
  done
  $PY $SC/strip09.py etatel_nod/${ep}A.fits etatel_nod/${ep}B.fits > /dev/null
  rm -f etatel_nod/${ep}A.fits etatel_nod/${ep}B.fits
  echo "$ep: staged etatel_nod/${ep}{A,B}_o8.fits"
done < /tmp/et_map.tsv

echo "=== SUMMARY ==="
ls ~/viper-src/etatel_nod/*_o8.fits 2>/dev/null | wc -l
[ -n "$FAILED" ] && echo "FAILED:$FAILED"
echo M15ALLNIGHTS_DONE
