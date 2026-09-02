#!/usr/bin/env bash
# Resume the six light noise runs killed by the wrapper-session teardown
# (chains on disk; harness H2 resume) + master keepalive until ALL 12 noise
# manifests are terminal.
set -u
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta

bash scripts/m2_campaign.sh one J1713+0747 noise c1 480 100000 101 prior
bash scripts/m2_campaign.sh one J2241-5236 noise c1 480 100000 102 prior
bash scripts/m2_campaign.sh one J1744-1134 noise c1 480 100000 105 prior
bash scripts/m2_campaign.sh one J0125-2327 noise c1 480 100000 106 prior
bash scripts/m2_campaign.sh one J1946-5403 noise c1 480 100000 107 prior
bash scripts/m2_campaign.sh one J2129-5721 noise c1 480 100000 110 prior

i=0
while true; do
    sleep 60
    i=$((i + 1))
    NT=$(python - <<'EOF'
import json, glob
n, ids = 0, []
for f in glob.glob("results/m2/manifest/*_noise_*.json"):
    try:
        m = json.load(open(f))
    except Exception:
        continue
    rid = m.get("run_id", "")
    if "smoke" in rid:
        continue
    if m.get("state") in ("done", "aborted", "error"):
        n += 1
    else:
        ids.append(rid)
print(n)
import sys
print(" ".join(ids), file=sys.stderr)
EOF
)
    NRUN=$(pgrep -fc "m2_run.py" || true)
    if [ $((i % 10)) -eq 0 ]; then
        echo "[noise ${i}m] terminal=${NT}/12 running=${NRUN} load=$(cut -d' ' -f1 /proc/loadavg)"
    fi
    [ "${NT}" -ge 12 ] && { echo "ALL 12 NOISE RUNS TERMINAL after ${i} min"; break; }
done
