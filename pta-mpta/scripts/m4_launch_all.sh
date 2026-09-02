#!/usr/bin/env bash
# M4 master launcher: resume the three M3 campaigns under the pre-registered
# scale-relative gate (M4 doc 1.2 R1) and start the registered gamma_SW
# wide-prior variant (M4 doc 1.3) alongside them.
#
# WSL2 tears the VM down when the last wsl.exe session exits, and children die
# with their launching session despite nohup (M2 doc 5.6).  Both layers are
# used here: every pool is `setsid nohup`-ed, and the CALLER of this script must
# stay alive (the agent runs it as a background Bash task, which holds a
# wsl.exe session open).
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
mkdir -p logs/m4 results/m3/manifest
rm -f results/m3/manifest/STOP_ALL

start () {  # name, command
  local name=$1; shift
  if pgrep -f "M4POOL=${name}" > /dev/null 2>&1; then
    echo "pool ${name} already running"; return 0
  fi
  # the marker must be in the COMMAND LINE (pgrep does not see the
  # environment), so it is appended as a shell comment
  setsid nohup bash -c "$* # M4POOL=${name}" \
      > "logs/m4/pool_${name}.log" 2>&1 &
  echo "started pool ${name} (pid $!)"
}

start noise  "GATE_RULE=relative NPROC=${N_NOISE:-12} THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh noise"
start swwide "NPROC=${N_SW:-6} THREADS=1 CHUNK_MIN=5 bash scripts/m4_swwide.sh"
start table  "GATE_RULE=relative NPROC=${N_TAB:-3} CHUNK_MIN=5 bash scripts/m3_rolling.sh table t1"
start fl     "GATE_RULE=relative NPROC=${N_FL:-3} CHUNK_MIN=5 bash scripts/m3_rolling.sh fl f1"

sleep 20
echo "--- launched, live worker count: $(pgrep -fc '[m]3_run.py' || echo 0)"
