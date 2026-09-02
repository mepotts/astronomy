#!/usr/bin/env bash
# M4 supervisor. A campaign pool is a single xargs pass over the order file:
# when every pulsar has either gated or hit its per-launch wall cap, the pass
# ENDS and nothing restarts it.  M3's `table`/`fl` had a rolling loop for this;
# `noise` and the M4 `swwide` variant did not.  This supervises all four:
# whenever a variant is short of its target and has no driver alive, it starts
# one.  Idempotent -- runs already gated are skipped by the campaign script.
#
#   bash scripts/m4_supervise.sh            # loop until targets met
# Env: N_NOISE, N_SW, N_FL, N_TAB, MAX_ROUNDS
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
mkdir -p logs/m4

gated () {  grep -l '"gate_met": true' results/m3/*_$1.summary.json 2>/dev/null | wc -l; }
alive () {
  for d in /proc/[0-9]*; do
    c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
    case "$c" in (*$1*) return 0;; esac
  done
  return 1
}

for round in $(seq 1 "${MAX_ROUNDS:-40}"); do
  n=$(gated noise_n1); s=$(gated swwide_s1)
  f=$(gated fl_f1);    t=$(gated table_t1)
  w=$(pgrep -fc "[m]3_run.py" || echo 0)
  echo "[$(date -u +%H:%M:%SZ) round $round] noise $n/83  swwide $s/26  fl $f/83  table $t/83  workers $w"

  if [ "$n" -lt 83 ] && ! alive "m3_campaign.sh noise"; then
    echo "  -> relaunching noise"
    setsid nohup bash -c "GATE_RULE=relative NPROC=${N_NOISE:-12} THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh noise # M4POOL=noise" >> logs/m4/pool_noise.log 2>&1 &
  fi
  if [ "$s" -lt 26 ] && ! alive "m4_swwide.sh"; then
    echo "  -> relaunching swwide"
    setsid nohup bash -c "NPROC=${N_SW:-6} THREADS=1 CHUNK_MIN=5 bash scripts/m4_swwide.sh # M4POOL=swwide" >> logs/m4/pool_swwide.log 2>&1 &
  fi
  if [ "$f" -lt 83 ] && ! alive "m3_campaign.sh fl"; then
    echo "  -> relaunching fl"
    setsid nohup bash -c "GATE_RULE=relative NPROC=${N_FL:-8} THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh fl # M4POOL=fl" >> logs/m4/pool_fl.log 2>&1 &
  fi
  if [ "${N_TAB:-0}" -gt 0 ] && [ "$t" -lt 83 ] && ! alive "m3_campaign.sh table"; then
    echo "  -> relaunching table"
    setsid nohup bash -c "GATE_RULE=relative NPROC=${N_TAB} THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh table # M4POOL=table" >> logs/m4/pool_table.log 2>&1 &
  fi

  if [ "$n" -ge 83 ] && [ "$s" -ge 26 ] && [ "$f" -ge 83 ]; then
    echo "ALL TARGETS MET"; break
  fi
  sleep 300
done
echo "supervisor exiting"
