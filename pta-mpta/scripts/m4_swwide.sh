#!/usr/bin/env bash
# M4 registered variant: the favoured noise model of every SW_Full pulsar under
# a WIDE solar-wind spectral-index prior, gamma_SW ~ U(-4,4), instead of the
# U(0,7) the registered campaign inherited from M1.
#
# Pre-registration: pta-mpta/M4-finish-the-array.md section 1.3 (V1-V7).
#   - V2 fixes the affected set at ALL 26 SW_Full pulsars (not just the 19 M3
#     flagged), so the 7 unaffected ones are the variant's own control.
#   - V6: this NEVER overwrites the registered noise run.  Run id is
#     <psr>_swwide_s1; the registered run is <psr>_noise_n1.
#
#   bash scripts/m4_swwide.sh
# Idempotent: re-issuing resumes; already-gated pulsars are skipped.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
mkdir -p results/m3/manifest logs/m4 chains/m3

NPROC=${NPROC:-8}
THREADS=${THREADS:-1}
WALL=${WALL:-300}
GATE=${GATE:-100000}
TAG=s1
ORDER_FILE=${ORDER_FILE:-logs/m4/order_swwide.txt}

if [ ! -s "$ORDER_FILE" ]; then
python - > "$ORDER_FILE" <<'PY'
import json, pathlib
t = json.loads(pathlib.Path("results/m3/published_table.json").read_text())
psrs = sorted(p for p, r in t.items() if r["model"]["sw"] == "full")
# the 7 pulsars whose published gamma_SW is negative first: they are the ones
# the variant exists to test.  The rest follow (V5's control set included).
neg = {"J0900-3144", "J1327-0755", "J1643-1224", "J1652-4838",
       "J1730-2304", "J1751-2857", "J1811-2405"}
psrs.sort(key=lambda p: (p not in neg, p))
assert len(psrs) == 26, len(psrs)
print("\n".join(psrs))
PY
fi

run_one () {
  local psr=$1
  local id="${psr}_swwide_${TAG}"
  if [ -f "results/m3/${id}.summary.json" ] && \
     python -c "import json,sys;s=json.load(open('results/m3/${id}.summary.json'));sys.exit(0 if s.get('gate_met') else 1)" 2>/dev/null; then
    echo "skip ${id} (gate already met)"; return 0
  fi
  OMP_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS \
  NUMEXPR_NUM_THREADS=$THREADS VECLIB_MAXIMUM_THREADS=$THREADS \
  nice -n 19 python scripts/m3_run.py "$psr" --variant noise --tag "$TAG" \
      --run-label swwide --sw-gamma-prior=-4,4 \
      --wall-min "$WALL" --gate "$GATE" --seed $((RANDOM)) \
      --chunk-min "${CHUNK_MIN:-10}" --gate-rule relative \
      > "logs/m4/${id}.log" 2>&1
  echo "done ${id} rc=$?"
}
export -f run_one
export TAG WALL GATE THREADS CHUNK_MIN

xargs -a "$ORDER_FILE" -P "$NPROC" -I{} bash -c 'run_one "$@"' _ {}
echo "swwide campaign finished"
