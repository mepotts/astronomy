#!/usr/bin/env bash
# pta-mpta W1b: build the PTA stack in WSL Ubuntu.
# Constraint discovered 2026-08-16: the WSL root disk is 100% full (5.4 GB free),
# so the venv, pip cache, and pip TMPDIR all live on /mnt/c (Windows side, 722 GB free).
# PINT-first strategy (pure Python); tempo2 deferred (compile on /mnt/c is slow, and
# PINT suffices for residuals + enterprise via timing_package='pint').
set -euo pipefail

REPO=/mnt/c/Users/matth/projects/astronomy/pta-mpta
SCRATCH="/mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/861de8f8-5fae-42fe-9bd2-fead2f2e36a7/scratchpad"
export TMPDIR="$SCRATCH/pip-tmp"
export PIP_CACHE_DIR="$SCRATCH/pip-cache"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR"

cd "$REPO"
echo "== python =="
python3 --version

if [ ! -e .venv/bin/activate ]; then
    python3 -m venv .venv || {
        echo "venv module missing; trying virtualenv --user (writes a few MB to WSL home)"
        pip3 install --user --quiet virtualenv
        ~/.local/bin/virtualenv .venv
    }
fi
. .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools 2>&1 | tail -1

echo "== installing PTA stack (wheels only where possible) =="
pip install pint-pulsar 2>&1 | tail -2
pip install enterprise-pulsar 2>&1 | tail -2
pip install enterprise_extensions 2>&1 | tail -2
pip install la-forge corner 2>&1 | tail -2

echo "== import check =="
python - <<'EOF'
import importlib, sys
for m in ["pint", "enterprise", "enterprise_extensions", "la_forge", "corner", "PTMCMCSampler"]:
    try:
        mod = importlib.import_module(m)
        print(f"OK  {m:25s} {getattr(mod, '__version__', '?')}")
    except Exception as e:
        print(f"FAIL {m:25s} {type(e).__name__}: {e}")
import numpy, scipy, astropy
print("numpy", numpy.__version__, "| scipy", scipy.__version__, "| astropy", astropy.__version__)
EOF
echo "== done =="
