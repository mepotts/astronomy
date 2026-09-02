#!/usr/bin/env bash
# Thread-scaling benchmark for the enterprise likelihood (diagnostic).
set -euo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
echo "load average: $(cat /proc/loadavg)"
for T in 1 2 4 8; do
    export OPENBLAS_NUM_THREADS=$T OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T
    export NUMEXPR_NUM_THREADS=$T VECLIB_MAXIMUM_THREADS=$T
    out=$(python scripts/w2_noise_run.py "${1:-J1909-3744}" --bench-only 2>/dev/null | grep bench)
    echo "threads=$T  $out"
done
