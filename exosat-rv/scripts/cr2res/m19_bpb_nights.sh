#!/bin/bash
# M19: beta Pic b's three raw K-family nights, fetched (raw-first resolver) and
# reduced through the cr2res cascade. Per-nodding products stage to
# ~/viper-src/bpb_nod/, stripped to the K2166 template's order set (02-07).
# The 2023-01-03 night is NOT re-reduced: its 8 sub-exposure products are already
# staged as betapicb_data/ in viper-src (M17). H-family nights skipped: one is
# staring-mode, leaving a 1-epoch H "series" with no leverage.
set -u
SC=/mnt/c/Users/matth/projects/astronomy/exosat-rv/scripts/cr2res
PY=$HOME/viperenv/bin/python
export RAW_BASE=$HOME/cr2res/raw_bpb
export RED_BASE=$HOME/cr2res/red_bpb
LOG=$HOME/cr2res/logs_bpb
mkdir -p "$LOG" "$RAW_BASE" "$RED_BASE"

# nights may be passed as arguments; the default list is the 114.27DX K2166
# campaign (verified by header: the planet, filed under the star's name).
# Downloads run SERIAL by design — parallel lanes saturated the portal (M19 lesson).
NIGHTS="${*:-2024-10-17 2024-10-21 2024-11-17 2025-01-08 2025-01-11 2025-01-13 2025-01-27 2025-02-06 2025-03-09 2025-03-21 2025-03-25 2025-03-26}"
OBJ="${OBJ_OVERRIDE:-BET PIC,BET PIC B,BETA PIC B}"

FAILED=""
for night in $NIGHTS; do
  ep=bpb${night//-/}
  RAW=$RAW_BASE/$ep
  RED=$RED_BASE/$ep

  if [ ! -f "$RAW/.fetched" ]; then
    echo "=== $ep: resolving ==="
    if ! $PY $SC/m19_urls_from_raw.py "$night" "$OBJ" /tmp/${ep}_urls.txt \
        > "$LOG/${ep}_urls.log" 2>&1; then
      echo "$ep: URL RESOLUTION FAILED"; tail -3 "$LOG/${ep}_urls.log"
      FAILED="$FAILED $ep(urls)"; continue
    fi
    n_urls=$(wc -l < /tmp/${ep}_urls.txt)
    echo "=== $ep: fetching $n_urls files ==="
    mkdir -p "$RAW"; cd "$RAW" || continue
    n=0; bad=0
    while read -r u; do
      [ -z "$u" ] && continue
      b=$(basename "$u")
      # skip files already landed intact (>1 MB; failed curls can leave partials)
      if [ -n "$(find . -maxdepth 1 -name "${b}*" -size +1M -print -quit)" ]; then
        rm -f "${b}"*.tmp 2>/dev/null; continue
      fi
      rm -f "${b}"* 2>/dev/null
      n=$((n+1))
      /usr/bin/curl -sL -OJ --retry 3 --retry-delay 20 --max-time 1800 "$u" \
        || { echo "  FAILED $u"; bad=$((bad+1)); }
    done < /tmp/${ep}_urls.txt
    for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done
    have=$(ls *.fits 2>/dev/null | wc -l)
    echo "$ep: attempted $n ($bad failed), $have files on disk, $(du -sh "$RAW" | cut -f1)"
    # judge the night by what is on disk, not by this pass's attempts (retries skip)
    if [ "$have" -lt 20 ]; then FAILED="$FAILED $ep(fetch)"; continue; fi
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
  mkdir -p bpb_nod
  for arm in A B; do
    cp -f "$RED/cr2res_obs_nodding_extracted${arm}.fits" bpb_nod/${ep}${arm}.fits
  done
  $PY - "$HOME/viper-src/bpb_nod/${ep}A.fits" "$HOME/viper-src/bpb_nod/${ep}B.fits" <<'PYEOF'
import sys
from astropy.io import fits
# strip to the K2166 template's DRS orders (02..07); refuse non-K2166 nights
KEEP = {f"{o:02d}" for o in range(2, 8)}
for src in sys.argv[1:]:
    h = fits.open(src)
    wlen = h[0].header.get("HIERARCH ESO INS WLEN ID") or h[0].header.get("ESO INS WLEN ID")
    if wlen != "K2166":
        print(f"SKIP {src}: setting {wlen} (not K2166)")
        continue
    out = [fits.PrimaryHDU(header=h[0].header)]
    ok = True
    for det in (1, 2, 3):
        cols_all = getattr(h[det], "columns", None)
        if cols_all is None:
            print(f"SKIP {src}: HDU {det} has no table")
            ok = False
            break
        cols = [c for c in cols_all if c.name.split("_")[0] in KEEP]
        out.append(fits.BinTableHDU.from_columns(cols, name=h[det].name,
                                                 header=h[det].header))
    if not ok:
        continue
    dest = src.replace(".fits", "_k6.fits")
    fits.HDUList(out).writeto(dest, overwrite=True)
    print(dest, "orders:", sorted({c.name.split("_")[0] for c in fits.open(dest)[1].columns}))
PYEOF
  rm -f bpb_nod/${ep}A.fits bpb_nod/${ep}B.fits
  echo "$ep: staged bpb_nod/${ep}{A,B}_k6.fits"
done

echo "=== SUMMARY ==="
ls ~/viper-src/bpb_nod/*_k6.fits 2>/dev/null | wc -l
[ -n "$FAILED" ] && echo "FAILED:$FAILED"
echo M19NIGHTS_DONE
