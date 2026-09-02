#!/usr/bin/env bash
# W2 reproduction slice: sequential PTMCMC runs, budgets within the
# pre-registered A3 cap (90 min sampling per pulsar).
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
mkdir -p results
echo "=== J2241-5236 start $(date -u +%H:%M:%S) ==="
python scripts/w2_noise_run.py J2241-5236 --minutes 50 2>&1 | grep -vE "DEBUG|WARNING"
echo "=== J1909-3744 start $(date -u +%H:%M:%S) ==="
python scripts/w2_noise_run.py J1909-3744 --minutes 85 2>&1 | grep -vE "DEBUG|WARNING"
echo "=== done $(date -u +%H:%M:%S) ==="
