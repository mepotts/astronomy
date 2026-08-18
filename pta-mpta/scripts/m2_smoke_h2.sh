#!/usr/bin/env bash
# H2 smoke test: SIGKILL mid-run, then resume; then STOP-file abort (H1).
set -u
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
ID="J2241-5236_noise_smoke2"
rm -rf "chains/m2/${ID}" "results/m2/${ID}.summary.json" \
      "results/m2/manifest/${ID}.json"

echo "=== phase 1: launch, SIGKILL after 75 s ==="
OMP_NUM_THREADS=2 nohup nice -n 19 python scripts/m2_run.py J2241-5236 \
    --kind noise --tag smoke2 --wall-min 10 --gate 300000 --seed 901 \
    --chunk-min 1 > logs/smoke2.log 2>&1 &
PID=$!
echo "pid=${PID}"
sleep 75
kill -9 "${PID}" 2>/dev/null
sleep 2
ROWS1=$(wc -l < "chains/m2/${ID}/chain_1.txt")
echo "rows after SIGKILL: ${ROWS1}"

echo "=== phase 2: resume, verify monotonic growth, then STOP ==="
OMP_NUM_THREADS=2 nohup nice -n 19 python scripts/m2_run.py J2241-5236 \
    --kind noise --tag smoke2 --wall-min 10 --gate 300000 --seed 902 \
    --chunk-min 1 >> logs/smoke2.log 2>&1 &
PID2=$!
sleep 80
touch "chains/m2/${ID}/STOP"
echo "STOP dropped; waiting for clean exit"
wait "${PID2}"
ROWS2=$(wc -l < "chains/m2/${ID}/chain_1.txt")
echo "rows after resume+STOP: ${ROWS2}  (phase-1 rows: ${ROWS1})"
grep -c "Resuming with" logs/smoke2.log
python - <<'EOF'
import json
s = json.load(open("results/m2/J2241-5236_noise_smoke2.summary.json"))
print("state:", s["state"], "| exit:", s["exit_reason"],
      "| chunks:", len(s["chunks"]),
      "| raw:", (s["chain"] or {}).get("raw_iters"))
EOF
rm -f "chains/m2/${ID}/STOP"
