#!/usr/bin/env bash
# Relaunch J0437-4715 + J1017-7156 after the enterprise phi-cache fix
# (M2 doc 2.1); keepalive session for the pair.
set -u
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
rm -rf chains/m2/J0437-4715_noise_c1 chains/m2/J1017-7156_noise_c1
rm -f results/m2/J0437-4715_noise_c1.summary.json \
      results/m2/J1017-7156_noise_c1.summary.json

bash scripts/m2_campaign.sh one J0437-4715 noise c1 480 100000 103 prior
bash scripts/m2_campaign.sh one J1017-7156 noise c1 480 100000 109 prior

i=0
while true; do
    sleep 60
    i=$((i + 1))
    NT=$(python - <<'EOF'
import json
n = 0
for rid in ("J0437-4715_noise_c1", "J1017-7156_noise_c1"):
    try:
        m = json.load(open(f"results/m2/manifest/{rid}.json"))
    except Exception:
        continue
    if m.get("state") in ("done", "aborted", "error"):
        n += 1
print(n)
EOF
)
    if [ $((i % 15)) -eq 0 ]; then
        echo "[pair ${i}m] terminal=${NT}/2 load=$(cut -d' ' -f1 /proc/loadavg)"
    fi
    [ "${NT}" -ge 2 ] && { echo "PAIR TERMINAL after ${i} min"; break; }
done
