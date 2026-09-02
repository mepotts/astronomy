#!/usr/bin/env bash
# M3: build + single-eval bench for every pulsar/variant (validates that all
# 83 models construct, and sizes the campaign). Variant given as $1.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
V=${1:-noise}
mkdir -p results/m3/bench logs/m3
python - <<'PY' > /tmp/m3_psrlist.txt
import json,pathlib
print("\n".join(sorted(json.loads(pathlib.Path("results/m3/published_table.json").read_text()))))
PY
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
xargs -a /tmp/m3_psrlist.txt -P 14 -I{} nice -n 19 \
  python scripts/m3_run.py {} --variant "$V" --bench-only \
  > "logs/m3/bench_${V}.log" 2>&1
echo "bench done: $(ls results/m3/bench | wc -l) records"
