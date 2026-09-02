#!/usr/bin/env bash
# Phase 3: pyarrow (enterprise.pulsar dep) + the sksparse loud-failure shim.
# Rationale in scripts/sksparse_shim/sksparse/__init__.py and M1 doc section 4.
set -euo pipefail

REPO=/mnt/c/Users/matth/projects/astronomy/pta-mpta
SCRATCH="/mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/861de8f8-5fae-42fe-9bd2-fead2f2e36a7/scratchpad"
export TMPDIR="$SCRATCH/pip-tmp"
export PIP_CACHE_DIR="$SCRATCH/pip-cache"

cd "$REPO"
. .venv/bin/activate

pip install pyarrow 2>&1 | tail -1

SP=$(python -c 'import site; print(site.getsitepackages()[0])')
cp -r scripts/sksparse_shim/sksparse "$SP/"
find "$SP/sksparse" -name '*.py' -exec sed -i 's/\r$//' {} \;

python - <<'EOF'
import importlib
ok = True
for m in ["enterprise.pulsar", "enterprise.signals.signal_base",
          "enterprise_extensions.chromatic.solar_wind",
          "enterprise_extensions.blocks"]:
    try:
        importlib.import_module(m)
        print("OK  ", m)
    except Exception as e:
        ok = False
        print("FAIL", m, type(e).__name__, e)
raise SystemExit(0 if ok else 1)
EOF
echo "== phase 3 done =="
