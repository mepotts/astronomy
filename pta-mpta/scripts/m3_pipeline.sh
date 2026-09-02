#!/usr/bin/env bash
# M3: the whole analysis pipeline, run on whatever coverage exists.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
NPROC=${NPROC:-4} bash scripts/m3_diag_all.sh 2>&1 | grep -E "dlnL|pending|ERROR|SKIP"
echo "=== C2/C3 =========================================="
python scripts/m3_analyze.py
echo "=== seam (a) ======================================"
python scripts/m3_seam_a.py
echo "=== seam (b) ======================================"
python scripts/m3_seam_b.py
echo "=== FL CURN (all) ================================="
python scripts/m3_fl_combine.py --subset all
echo "=== FL CURN (M2 top-10) ==========================="
python scripts/m3_fl_combine.py --subset top10
echo "=== M2-vs-M3 repeat control ======================="
python scripts/m3_m2_repeat.py
echo "=== figures ======================================="
python scripts/m3_figures.py
