#!/usr/bin/env bash
# M3: run the C3 mode-vs-model diagnostic for every gated noise run.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
. .venv/bin/activate
mkdir -p results/m3/diag logs/m3
python - > logs/m3/diag_list.txt <<PY
import glob, json, pathlib
out=[]
for f in sorted(glob.glob("results/m3/*_noise_n1.summary.json")):
    s=json.loads(pathlib.Path(f).read_text())
    p=s["meta"]["psr"]
    if s.get("gate_met") and not pathlib.Path(f"results/m3/diag/{p}.json").exists():
        out.append(p)
print("\n".join(out))
PY
echo "diag pending: $(wc -l < logs/m3/diag_list.txt)"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  xargs -a logs/m3/diag_list.txt -P "${NPROC:-4}" -I{} nice -n 19 \
  python scripts/m3_diag.py {}
