#!/bin/bash
# M26: serial fetch+reduce of every census-v2-verified public night.
# Same machinery as M23/M24 (raw-first resolver + calib fallback, nodding or
# staring branch as tagged, staged to ~/viper-src/m26_data/<slug>_o8.fits).
set -u
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res
PY=$HOME/viperenv/bin/python
export RAW_BASE=$HOME/cr2res/raw_m26
export RED_BASE=$HOME/cr2res/red_m26
LOG=$HOME/cr2res/logs_m26
mkdir -p "$LOG" "$RAW_BASE" "$RED_BASE"

# night|objlist|slug
JOBS="2022-05-14|TYC 8998-760-1B,YSES 1BC|yses1a
2022-05-15|TYC 8998-760-1B,YSES 1BC|yses1b
2023-02-27|TYC 8998-760-1B,YSES 1BC|yses1c
2023-02-28|TYC 8998-760-1B,YSES 1BC|yses1d
2024-04-18|HIP 81208 B|h81208a
2024-08-21|HIP 81208 B|h81208b
2024-08-22|HIP 81208 B|h81208c
2024-08-23|HIP 81208 B|h81208d
2025-04-04|HIP 81208 B,NO NAME|h81208e
2025-04-05|HIP 81208 B,NO NAME|h81208f
2025-04-14|HD 149274|h81208k1
2025-07-26|HD 149274|h81208k2
2025-07-28|HD 149274|h81208k3
2021-11-16|HD 206893|hd206893k
2024-08-22|HD 206893|hd206893h1
2024-08-23|HD 206893|hd206893h2
2024-08-22|HD 19467,HD19467|hd19467a
2024-08-23|HD 19467,HD19467|hd19467b
2025-04-04|CD-40 8434|pds70h1
2025-04-05|CD-40 8434|pds70h2
2025-05-06|CD-40 8434|pds70h3
2024-10-17|CD-35 2722B,CD-35 2722 B,CD-35 2722|cd35d1
2024-10-19|CD-35 2722B,CD-35 2722 B,CD-35 2722|cd35d2
2022-11-05|2M0103AB B|m0103a"

echo "$JOBS" | while IFS="|" read -r night obj slug; do
  [ -z "$night" ] && continue
  ep=$slug
  RAW=$RAW_BASE/$ep
  RED=$RED_BASE/$ep

  if [ ! -f "$RAW/.fetched" ]; then
    echo "=== $ep ($night, $obj): resolving ==="
    if ! $PY $SC/m19_urls_from_raw.py "$night" "$obj" /tmp/${ep}_urls.txt \
        > "$LOG/${ep}_urls.log" 2>&1; then
      echo "$ep: URL RESOLUTION FAILED"; tail -2 "$LOG/${ep}_urls.log"; continue
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
    if [ "$have" -lt 6 ]; then echo "$ep: too few"; continue; fi
    touch "$RAW/.fetched"
  fi

  if [ ! -f "$RED/.done" ]; then
    echo "=== $ep: reducing ==="
    if ! bash $SC/reduce_one.sh "$ep" > "$LOG/${ep}_reduce.log" 2>&1; then
      echo "$ep: REDUCTION FAILED"; tail -5 "$LOG/${ep}_reduce.log"; continue
    fi
    tail -1 "$LOG/${ep}_reduce.log"
  fi

  cd ~/viper-src || exit 1
  mkdir -p m26_data
  ex=$(ls "$RED"/cr2res_obs_staring_extracted*.fits 2>/dev/null | head -1)
  suffix=""
  if [ -z "$ex" ]; then
    for arm in A B; do
      exN=$(ls "$RED"/cr2res_obs_nodding_extracted${arm}.fits 2>/dev/null)
      [ -z "$exN" ] && continue
      cp -f "$exN" m26_data/${ep}${arm}.fits
      $PY - "$HOME/viper-src/m26_data/${ep}${arm}.fits" <<'PYEOF'
import sys
from astropy.io import fits
KEEP = {f"{o:02d}" for o in range(2, 9)}
src = sys.argv[1]
h = fits.open(src)
out = [fits.PrimaryHDU(header=h[0].header)]
ok = True
for det in (1, 2, 3):
    cols_all = getattr(h[det], "columns", None)
    if cols_all is None:
        ok = False
        break
    cols = [c for c in cols_all if c.name.split("_")[0] in KEEP]
    out.append(fits.BinTableHDU.from_columns(cols, name=h[det].name,
                                             header=h[det].header))
if ok:
    fits.HDUList(out).writeto(src.replace(".fits", "_o8.fits"), overwrite=True)
    print("stripped", src)
PYEOF
      rm -f m26_data/${ep}${arm}.fits
    done
    echo "$ep: staged (nodding A/B)"
  else
    cp -f "$ex" m26_data/${ep}.fits
    $PY - "$HOME/viper-src/m26_data/${ep}.fits" <<'PYEOF'
import sys
from astropy.io import fits
KEEP = {f"{o:02d}" for o in range(2, 9)}
src = sys.argv[1]
h = fits.open(src)
out = [fits.PrimaryHDU(header=h[0].header)]
ok = True
for det in (1, 2, 3):
    cols_all = getattr(h[det], "columns", None)
    if cols_all is None:
        ok = False
        break
    cols = [c for c in cols_all if c.name.split("_")[0] in KEEP]
    out.append(fits.BinTableHDU.from_columns(cols, name=h[det].name,
                                             header=h[det].header))
if ok:
    fits.HDUList(out).writeto(src.replace(".fits", "_o8.fits"), overwrite=True)
    print("stripped", src)
PYEOF
    rm -f m26_data/${ep}.fits
    echo "$ep: staged (staring)"
  fi
done

echo "=== SUMMARY ==="
ls ~/viper-src/m26_data/*_o8.fits 2>/dev/null | wc -l
echo M26FETCH_DONE
