#!/bin/bash
# M30: stage the verified genuinely-new block — HIP 65426's three public HiRISE
# H1567 nights (2025-01-31/02-01/02-02, prog 114.2712, header-verified M30) —
# science frames + the MINIMAL calibration set (M29 §16 pattern: darks at the
# DITs actually needed, flats, UNE, FPET; the raw calSelector route returns zero
# for HiRISE and the unfiltered CALIB fallback over-fetches ~5 GB/night).
#
# FETCH ONLY — no reduction here (M31 is gated on Matthew seeing M30).
# LESSONS rules honoured: serial fetches, 3-try loop with sleeps per file,
# size-validated skip-existing, judge by files on disk never exit status,
# URL lists generated INSIDE WSL (LF; §5/§18 CRLF traps).
set -u
export RAW_BASE=$HOME/cr2res/raw_m30
LOG=$HOME/cr2res/logs_m30
mkdir -p "$RAW_BASE" "$LOG"

# night|objname|slug|sci_dits (comma-sep, for dark matching)
JOBS="2025-01-31|HD 116434|h65hi1|200,1200
2025-02-01|HIP 65426|h65hi2|600,1200
2025-02-02|HIP 65426|h65hi3|600,1200"

resolve () {  # night obj sci_dits out_prefix  -> writes ${out}_sci.txt ${out}_cal.txt
python3 - "$1" "$2" "$3" "$4" <<'PYEOF'
import json, subprocess, sys, time, urllib.parse
night, obj, dits, out = sys.argv[1:5]
TAP = "https://archive.eso.org/tap_obs/sync"

def tap(q, tries=6):
    qs = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL",
                                 "FORMAT": "json", "MAXREC": "5000", "QUERY": q})
    for k in range(tries):
        p = subprocess.run(["/usr/bin/curl", "-s", "--max-time", "240",
                            f"{TAP}?{qs}"], capture_output=True)
        if p.returncode == 0 and p.stdout:
            try:
                j = json.loads(p.stdout)
                cols = [c["name"] for c in j["metadata"]]
                return [dict(zip(cols, r)) for r in j["data"]]
            except ValueError:
                pass
        time.sleep(10 * (k + 1))
    raise SystemExit(f"TAP unreachable for {night}")

sci = tap(f"SELECT dp_id FROM dbo.raw WHERE instrument='CRIRES' "
          f"AND dp_cat='SCIENCE' AND object='{obj}' "
          f"AND date_obs BETWEEN '{night}' AND '{night}T23:59:59'")
sci_ids = sorted(r["dp_id"] for r in sci)
print(f"{night}: {len(sci_ids)} science frames")

from datetime import date, timedelta
d0 = date.fromisoformat(night)
d1 = d0 + timedelta(days=1)
cal = tap(f"SELECT dp_id, dp_type, exposure, filter_path FROM dbo.raw "
          f"WHERE instrument='CRIRES' AND dp_cat='CALIB' "
          f"AND date_obs BETWEEN '{d0}' AND '{d1}T20:00:00' "
          f"AND (dp_type LIKE 'DARK%' OR dp_type LIKE 'FLAT%' "
          f"OR dp_type LIKE '%UNE%' OR dp_type LIKE '%FPET%')")

def h_first(rows):  # prefer H-band filter hints for lamp frames (hint, not truth)
    hs = [r for r in rows if str(r.get("filter_path") or "").upper().startswith("H")]
    return hs or rows

def take(rows, n):
    return sorted(r["dp_id"] for r in rows)[:n]

flats = h_first([r for r in cal if str(r["dp_type"]).startswith("FLAT")])
unes  = h_first([r for r in cal if "UNE" in str(r["dp_type"])])
fpets = h_first([r for r in cal if "FPET" in str(r["dp_type"])])
darks = [r for r in cal if str(r["dp_type"]).startswith("DARK")]

need_dits = {float(x) for x in dits.split(",")}
for grp in (flats, unes, fpets):
    need_dits |= {float(r["exposure"]) for r in grp[:5] if r.get("exposure")}

cal_ids = []
for dit in sorted(need_dits):
    dd = [r for r in darks if abs(float(r.get("exposure") or -1) - dit) < 0.01]
    cal_ids += take(dd, 3)
    if not dd:
        print(f"  WARNING: no darks at DIT={dit}")
cal_ids += take(flats, 5) + take(unes, 2) + take(fpets, 2)
cal_ids = sorted(set(cal_ids))
print(f"{night}: minimal calib set {len(cal_ids)} of {len(cal)} available "
      f"(DITs needed: {sorted(need_dits)})")

base = "https://dataportal.eso.org/dataPortal/file/"
with open(f"{out}_sci.txt", "w") as f:
    f.write("\n".join(base + d for d in sci_ids) + "\n")
with open(f"{out}_cal.txt", "w") as f:
    f.write("\n".join(base + d for d in cal_ids) + "\n")
PYEOF
}

fetch_list () {  # list_file dest_dir  — serial, 3 tries/file, size-validated skip
  local list=$1 dest=$2 n=0 bad=0
  mkdir -p "$dest"; cd "$dest" || return 1
  while read -r u; do
    [ -z "$u" ] && continue
    local b; b=$(basename "$u")
    if [ -n "$(find . -maxdepth 1 -name "${b}*" -size +1M -print -quit)" ]; then
      continue
    fi
    rm -f "${b}"* 2>/dev/null
    n=$((n+1))
    local got=""
    for t in 1 2 3; do
      /usr/bin/curl -sL -OJ --max-time 1800 "$u" 2>/dev/null
      if [ -n "$(find . -maxdepth 1 -name "${b}*" -size +1M -print -quit)" ]; then
        got=yes; break
      fi
      sleep $((10 * t))
    done
    [ -z "$got" ] && { echo "  FAILED $b"; bad=$((bad+1)); }
    sleep 2
  done < "$list"
  for f in *.Z; do [ -e "$f" ] && gzip -d -f "$f"; done
  echo "  attempted $n, failed $bad, on disk now: $(ls *.fits 2>/dev/null | wc -l)"
}

echo "$JOBS" | while IFS="|" read -r night obj slug dits; do
  [ -z "$night" ] && continue
  RAW=$RAW_BASE/$slug
  if [ -f "$RAW/.fetched" ]; then echo "=== $slug: already fetched ==="; continue; fi
  echo "=== $slug ($night, $obj): resolving ==="
  if ! resolve "$night" "$obj" "$dits" "/tmp/m30_${slug}" > "$LOG/${slug}_urls.log" 2>&1; then
    echo "$slug: URL RESOLUTION FAILED"; tail -3 "$LOG/${slug}_urls.log"; continue
  fi
  cat "$LOG/${slug}_urls.log"
  cp -f "/tmp/m30_${slug}_sci.txt" "/tmp/m30_${slug}_cal.txt" "$LOG/" 2>/dev/null
  nsci=$(wc -l < "/tmp/m30_${slug}_sci.txt")
  echo "=== $slug: fetching $nsci science ==="
  fetch_list "/tmp/m30_${slug}_sci.txt" "$RAW"
  ncal=$(wc -l < "/tmp/m30_${slug}_cal.txt")
  if [ "${M30_SCI_ONLY:-0}" = "1" ]; then
    echo "=== $slug: SCI-ONLY mode; $ncal calib URLs banked in $LOG/m30_${slug}_cal.txt ==="
  else
    echo "=== $slug: fetching $ncal calibs ==="
    fetch_list "/tmp/m30_${slug}_cal.txt" "$RAW"
  fi
  have=$(ls "$RAW"/*.fits 2>/dev/null | wc -l)
  echo "$slug: $have size-validated files on disk (want $nsci sci + $ncal cal)"
  if [ "$have" -ge "$nsci" ]; then
    if [ "${M30_SCI_ONLY:-0}" = "1" ]; then touch "$RAW/.sci_fetched"
    else touch "$RAW/.fetched"; fi
  fi
done

echo "=== M30 STAGING SUMMARY ==="
for d in "$RAW_BASE"/*/; do
  [ -d "$d" ] || continue
  echo "$d: $(ls "$d"*.fits 2>/dev/null | wc -l) fits, $(du -sh "$d" | cut -f1), marker=$([ -f "$d/.fetched" ] && echo yes || echo no)"
done
df -h "$HOME" | tail -1
echo M30FETCH_DONE
