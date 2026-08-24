#!/usr/bin/env bash
# M3 campaign launcher. Pre-registered criteria: M3-noise-criticism.md section 1.
#   scripts/m3_campaign.sh noise            # all-83 favoured-model campaign (C1)
#   scripts/m3_campaign.sh table            # seam-(b) control (whites fixed)
#   scripts/m3_campaign.sh fl               # seam-(b) + CURN config (whites fixed)
# Runs are ordered heaviest-first (measured bench) and executed by a fixed-width
# worker pool; every run is nice -19 with BLAS threads pinned, checkpointed and
# resumable, so re-running this script resumes rather than restarts.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
mkdir -p results/m3/manifest logs/m3 chains/m3

MODE=${1:-noise}
# GATE_RULE: absolute = the M1/M2/M3 stability rule; relative = M4's
# pre-registered scale-relative rule (M4-finish-the-array.md 1.2 R1).
GATE_RULE=${GATE_RULE:-absolute}
NPROC=${NPROC:-15}
THREADS=${THREADS:-2}
case "$MODE" in
  noise) WALL=300; GATE=100000; TAG=n1 ;;
  table) WALL=120; GATE=50000;  TAG=t1 ;;
  fl)    WALL=120; GATE=50000;  TAG=f1 ;;
  *) echo "unknown mode $MODE" >&2; exit 2 ;;
esac

# ORDER_FILE lets a caller pin an explicit pulsar list (used to guarantee the
# seam-critical sets - the 13 free-beta chromatic pulsars and the 12 that
# already carry a free red process - are covered even if the window ends
# early; shortest-first alone would leave them all to last and bias coverage
# towards simple models).
ORDER_FILE=${ORDER_FILE:-logs/m3/order_${MODE}.txt}
if [ "${ORDER_FILE}" = "logs/m3/order_${MODE}.txt" ]; then
python - "$MODE" > "$ORDER_FILE" <<'PY'
import glob, json, os, pathlib, sys
mode = sys.argv[1]
bench = {}
for f in glob.glob("results/m3/bench/*_noise.json"):
    r = json.loads(pathlib.Path(f).read_text())
    bench[r["psr"]] = r["eval_ms"]
psrs = sorted(json.loads(pathlib.Path("results/m3/published_table.json").read_text()))
psrs.sort(key=lambda p: -bench.get(p, 0.0))
# Schedule: the HEAVY_FIRST most expensive pulsars start immediately (they are
# wall-cap limited and need every minute); everything else runs SHORTEST-FIRST.
# Aggregate throughput is core-limited and order-invariant, but shortest-first
# minimises MEAN completion time, so the dependent fixed-white runs (`table`,
# `fl`, which need each pulsar's own noise-campaign medians) can start as early
# as possible and coverage degrades gracefully if the window ends.
HEAVY_FIRST = int(os.environ.get("HEAVY_FIRST", "5"))
psrs = psrs[:HEAVY_FIRST] + psrs[HEAVY_FIRST:][::-1]
print("\n".join(psrs))
PY
fi

run_one () {
  local psr=$1
  local id="${psr}_${MODE}_${TAG}"
  # already gated? skip (idempotent resume)
  if [ -f "results/m3/${id}.summary.json" ] && \
     python -c "import json,sys;s=json.load(open('results/m3/${id}.summary.json'));sys.exit(0 if s.get('gate_met') else 1)" 2>/dev/null; then
    echo "skip ${id} (gate already met)"; return 0
  fi
  local extra=()
  if [ "$MODE" != "noise" ]; then
    # the whites source must itself have cleared the C1 gate: a provisional
    # median from a still-running noise chain must never be frozen into a
    # fixed-white run (M2 doc 5.1's lesson, applied to the dependency)
    local ns="results/m3/${psr}_noise_n1.summary.json"
    extra=(--whites-from "$ns")
    python -c "import json,sys;s=json.load(open('$ns'));sys.exit(0 if s.get('gate_met') else 1)" 2>/dev/null \
      || { echo "skip ${id}: noise run not gated"; return 0; }
  fi
  OMP_NUM_THREADS=$THREADS OPENBLAS_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS \
  NUMEXPR_NUM_THREADS=$THREADS VECLIB_MAXIMUM_THREADS=$THREADS \
  nice -n 19 python scripts/m3_run.py "$psr" --variant "$MODE" --tag "$TAG" \
      --wall-min "$WALL" --gate "$GATE" --seed $((RANDOM)) \
      --chunk-min "${CHUNK_MIN:-10}" --gate-rule "${GATE_RULE:-absolute}"       "${extra[@]}" \
      > "logs/m3/${id}.log" 2>&1
  echo "done ${id} rc=$?"
}
export -f run_one
export MODE TAG WALL GATE THREADS CHUNK_MIN GATE_RULE

xargs -a "$ORDER_FILE" -P "$NPROC" -I{} bash -c 'run_one "$@"' _ {}
echo "campaign ${MODE} finished"
