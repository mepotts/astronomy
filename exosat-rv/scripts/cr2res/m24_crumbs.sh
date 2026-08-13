#!/bin/bash
# M24: the staring crumbs — AF Lep b (2 nights) and 51 Eri b (1 public night).
# Same machinery as M23 (raw-first resolver with calib fallback, staring branch).
# Expectation set by the contrast wall: both sit at ~30,000x contrast inside 0.5",
# so these single epochs likely measure star-dominated light — that outcome extends
# the M20 §6 wall table and is worth having either way.
set -u
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res
PY=$HOME/viperenv/bin/python
export RAW_BASE=$HOME/cr2res/raw_crumbs
export RED_BASE=$HOME/cr2res/red_crumbs
LOG=$HOME/cr2res/logs_crumbs
mkdir -p "$LOG" "$RAW_BASE" "$RED_BASE"

# night|objlist|slug
JOBS="2023-11-20|AF LEP|aflep1
2023-11-23|AF LEP|aflep2
2023-11-21|51 ERI|eri51"

FAILED=""
echo "$JOBS" | while IFS="|" read -r night obj slug; do
  [ -z "$night" ] && continue
  ep=${slug}
  RAW=$RAW_BASE/$ep
  RED=$RED_BASE/$ep

  if [ ! -f "$RAW/.fetched" ]; then
    echo "=== $ep ($night, $obj): resolving ==="
    if ! $PY $SC/m19_urls_from_raw.py "$night" "$obj" /tmp/${ep}_urls.txt \
        > "$LOG/${ep}_urls.log" 2>&1; then
      echo "$ep: URL RESOLUTION FAILED"; tail -3 "$LOG/${ep}_urls.log"; continue
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
    echo "$ep: attempted $n ($bad failed), $have on disk"
    if [ "$have" -lt 8 ]; then echo "$ep: too few files"; continue; fi
    touch "$RAW/.fetched"
  fi

  if [ ! -f "$RED/.done" ]; then
    echo "=== $ep: reducing ==="
    if ! bash $SC/reduce_one.sh "$ep" > "$LOG/${ep}_reduce.log" 2>&1; then
      echo "$ep: REDUCTION FAILED"; tail -6 "$LOG/${ep}_reduce.log"; continue
    fi
    tail -1 "$LOG/${ep}_reduce.log"
  fi

  cd ~/viper-src || exit 1
  mkdir -p crumbs_data
  ex=$(ls "$RED"/cr2res_obs_staring_extracted*.fits 2>/dev/null | head -1)
  [ -z "$ex" ] && ex=$(ls "$RED"/cr2res_obs_nodding_extractedA.fits 2>/dev/null)
  [ -z "$ex" ] && { echo "$ep: no extraction"; continue; }
  cp -f "$ex" crumbs_data/${ep}.fits
  $PY - "$HOME/viper-src/crumbs_data/${ep}.fits" <<'PYEOF'
import sys
from astropy.io import fits
KEEP = {f"{o:02d}" for o in range(2, 9)}
src = sys.argv[1]
h = fits.open(src)
out = [fits.PrimaryHDU(header=h[0].header)]
for det in (1, 2, 3):
    cols = [c for c in h[det].columns if c.name.split("_")[0] in KEEP]
    out.append(fits.BinTableHDU.from_columns(cols, name=h[det].name,
                                             header=h[det].header))
dest = src.replace(".fits", "_o8.fits")
fits.HDUList(out).writeto(dest, overwrite=True)
print(dest)
PYEOF
  rm -f crumbs_data/${ep}.fits
  echo "$ep: staged"
done

echo "=== SUMMARY ==="
ls ~/viper-src/crumbs_data/*_o8.fits 2>/dev/null | wc -l
echo M24NIGHTS_DONE
