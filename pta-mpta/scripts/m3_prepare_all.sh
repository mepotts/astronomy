#!/usr/bin/env bash
# M3: A1 + TDB par for all 83 released pulsars, parallel.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
mkdir -p results/m3/a1 logs
ls data/partim/*.par | xargs -n1 basename | sed "s/\.par$//" | \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  xargs -P 12 -I{} nice -n 19 python scripts/m3_prepare.py {}
echo "prepare done: $(ls results/m3/a1 | wc -l) records"
