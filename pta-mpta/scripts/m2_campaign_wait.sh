#!/usr/bin/env bash
# Campaign wrapper + WSL keepalive (measured trap, M2 doc section 2.1: WSL
# tears the VM down when the last wsl.exe session exits, SIGKILLing nohup'd
# children within seconds — so the launcher session must outlive the runs).
# Launches a campaign mode, then polls the manifests until every expected run
# reaches a terminal state; prints one status line per poll-decade.
# Usage: bash scripts/m2_campaign_wait.sh <noise|fl> <n_expected>
set -u
MODE="${1:-noise}"
NEXP="${2:-12}"
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta

bash scripts/m2_campaign.sh "$MODE"

i=0
while true; do
    sleep 60
    i=$((i + 1))
    # terminal = manifest state done/aborted/error
    NT=$(MODE="$MODE" python - <<'EOF'
import json, glob, os
mode = os.environ["MODE"]
n = 0
for f in glob.glob("results/m2/manifest/*.json"):
    try:
        m = json.load(open(f))
    except Exception:
        continue
    rid = m.get("run_id", "")
    if f"_{mode}_" not in rid or "smoke" in rid:
        continue
    if m.get("state") in ("done", "aborted", "error"):
        n += 1
print(n)
EOF
)
    NRUN=$(pgrep -fc "m2_run.py" || true)
    if [ $((i % 10)) -eq 0 ]; then
        echo "[wait ${i}m] terminal=${NT}/${NEXP} running=${NRUN} load=$(cut -d" " -f1 /proc/loadavg)"
    fi
    if [ "${NT}" -ge "${NEXP}" ]; then
        echo "ALL ${NEXP} RUNS TERMINAL after ${i} min"
        break
    fi
    if [ "${NRUN}" -eq 0 ] && [ "${NT}" -lt "${NEXP}" ]; then
        echo "WARNING: no m2_run.py processes but only ${NT}/${NEXP} terminal (min ${i})"
        # keep waiting a few polls in case of a race, then bail
        sleep 120
        NRUN2=$(pgrep -fc "m2_run.py" || true)
        if [ "${NRUN2}" -eq 0 ]; then
            echo "BAIL: runs died without terminal manifests"
            break
        fi
    fi
done
python scripts/m2_status.py 2>/dev/null || true
