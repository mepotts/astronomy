#!/usr/bin/env bash
# Phase 2: enterprise without sudo.
# Finding (2026-08-16): `pip install enterprise-pulsar` fails at scikit-sparse,
# which needs system SuiteSparse headers (libsuitesparse-dev) -- and this WSL
# has no passwordless sudo. Route-around: enterprise guards its sksparse and
# libstempo imports (both optional for the PINT backend), so install
# enterprise/e_e with --no-deps and pull the remaining deps explicitly.
set -euo pipefail

REPO=/mnt/c/Users/matth/projects/astronomy/pta-mpta
SCRATCH="/mnt/c/Users/matth/AppData/Local/Temp/claude/c--Users-matth-projects-astronomy/861de8f8-5fae-42fe-9bd2-fead2f2e36a7/scratchpad"
export TMPDIR="$SCRATCH/pip-tmp"
export PIP_CACHE_DIR="$SCRATCH/pip-cache"

cd "$REPO"
. .venv/bin/activate

echo "== explicit deps (wheels) =="
pip install ephem healpy scikit-learn h5py ptmcmcsampler 2>&1 | tail -1
pip install la-forge 2>&1 | tail -1

echo "== enterprise + extensions, --no-deps =="
pip install --no-deps enterprise-pulsar 2>&1 | tail -1
pip install --no-deps enterprise_extensions 2>&1 | tail -1

echo "== import check =="
python - <<'EOF'
import importlib
ok = True
for m in ["pint", "enterprise", "enterprise.pulsar", "enterprise.signals.signal_base",
          "enterprise_extensions", "enterprise_extensions.chromatic.solar_wind",
          "la_forge", "corner", "PTMCMCSampler"]:
    try:
        mod = importlib.import_module(m)
        print(f"OK   {m:45s} {getattr(mod, '__version__', '')}")
    except Exception as e:
        ok = False
        print(f"FAIL {m:45s} {type(e).__name__}: {e}")
raise SystemExit(0 if ok else 1)
EOF
echo "== phase 2 done =="
