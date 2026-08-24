#!/usr/bin/env bash
# M5 supervisor.  Successor to scripts/m4_supervise.sh, which is left untouched
# as the M4 artifact.  Three defects of that script are fixed here, all of them
# things that actually happened:
#
#   1. MAX_ROUNDS defaulted to 40 (~3.3 h).  A campaign longer than that expired
#      SILENTLY -- the supervisor printed "supervisor exiting" and stopped, with
#      work outstanding, and nothing on disk distinguished that from success.
#      Default is now 4000 rounds (~14 days) and the exit reason is recorded.
#   2. No completion sentinel.  A future reader could not tell "finished" from
#      "stopped".  This writes results/m4/CAMPAIGN_STATE.json every round
#      (heartbeat + coverage) and results/m4/CAMPAIGN_COMPLETE.json exactly once,
#      when every target is met.  Absence of the COMPLETE file now MEANS
#      unfinished; a stale heartbeat now MEANS the supervisor is dead.
#   3. `table` was gated behind N_TAB and excluded from the "ALL TARGETS MET"
#      test, so the supervisor could declare success with a table run missing.
#      All four variants are targets here.
#
# THE LOCK PROBLEM, stated because it is the dangerous one.  There is no
# per-run lock anywhere in this harness: two m3_run.py processes on the same
# (pulsar, tag) would write one chain directory and corrupt it.  m4_supervise.sh
# guarded only the POOL DRIVER (`alive "m3_campaign.sh noise"`).  If a driver
# died and left orphaned workers -- exactly what a session disruption produces --
# the guard passed and a second pool launched on top of live samplers.  Here the
# guard is tag-aware: a pool is relaunched only when neither its driver NOR any
# m3_run.py worker carrying its tag is alive.
#
#   bash scripts/m5_supervise.sh
# Env: N_NOISE N_SW N_FL N_TAB THREADS_SW THREADS_TAB MAX_ROUNDS SLEEP_S
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
mkdir -p logs/m5 results/m4

STATE=results/m4/CAMPAIGN_STATE.json
DONE=results/m4/CAMPAIGN_COMPLETE.json

gated () { grep -l '"gate_met": true' results/m3/*_$1.summary.json 2>/dev/null | wc -l; }

# any process whose command line contains $1
alive () {
  for d in /proc/[0-9]*; do
    c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
    case "$c" in (*$1*) return 0;; esac
  done
  return 1
}

# any m3_run.py SAMPLER carrying tag $1 (n1/t1/f1/s1).  This is the guard that
# m4_supervise.sh lacked.
worker_on_tag () {
  for d in /proc/[0-9]*; do
    c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
    case "$c" in
      (*m3_run.py*"--tag $1"*) return 0;;
    esac
  done
  return 1
}

write_state () {  # $1=round $2=reason
  cat > "$STATE" <<JSON
{
  "written_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "round": $1,
  "reason": "$2",
  "pid": $$,
  "coverage": {"noise": $n, "swwide": $s, "fl": $f, "table": $t},
  "targets":  {"noise": 83, "swwide": 26, "fl": 83, "table": 83},
  "workers_alive": $w
}
JSON
}

MAX_ROUNDS=${MAX_ROUNDS:-4000}
SLEEP_S=${SLEEP_S:-300}
final="max_rounds_exhausted"

for round in $(seq 1 "$MAX_ROUNDS"); do
  n=$(gated noise_n1); s=$(gated swwide_s1)
  f=$(gated fl_f1);    t=$(gated table_t1)
  w=$(pgrep -fc "[m]3_run.py" 2>/dev/null || true); w=${w:-0}
  echo "[$(date -u +%H:%M:%SZ) round $round] noise $n/83  swwide $s/26  fl $f/83  table $t/83  workers $w"
  write_state "$round" "running"

  if [ "$n" -lt 83 ] && ! alive "m3_campaign.sh noise" && ! worker_on_tag n1; then
    echo "  -> relaunching noise"
    setsid nohup bash -c "GATE_RULE=relative NPROC=${N_NOISE:-12} THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh noise # M4POOL=noise" >> logs/m5/pool_noise.log 2>&1 &
  fi
  if [ "$s" -lt 26 ] && ! alive "m4_swwide.sh" && ! worker_on_tag s1; then
    echo "  -> relaunching swwide"
    setsid nohup bash -c "NPROC=${N_SW:-6} THREADS=${THREADS_SW:-1} CHUNK_MIN=5 bash scripts/m4_swwide.sh # M4POOL=swwide" >> logs/m5/pool_swwide.log 2>&1 &
  fi
  if [ "$f" -lt 83 ] && ! alive "m3_campaign.sh fl" && ! worker_on_tag f1; then
    echo "  -> relaunching fl"
    setsid nohup bash -c "GATE_RULE=relative NPROC=${N_FL:-8} THREADS=1 CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh fl # M4POOL=fl" >> logs/m5/pool_fl.log 2>&1 &
  fi
  if [ "$t" -lt 83 ] && ! alive "m3_campaign.sh table" && ! worker_on_tag t1; then
    echo "  -> relaunching table"
    setsid nohup bash -c "GATE_RULE=relative NPROC=${N_TAB:-4} THREADS=${THREADS_TAB:-1} CHUNK_MIN=5 ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh table # M4POOL=table" >> logs/m5/pool_table.log 2>&1 &
  fi

  if [ "$n" -ge 83 ] && [ "$s" -ge 26 ] && [ "$f" -ge 83 ] && [ "$t" -ge 83 ]; then
    final="all_targets_met"
    write_state "$round" "$final"
    cp "$STATE" "$DONE"
    echo "ALL TARGETS MET -> $DONE"
    break
  fi
  sleep "$SLEEP_S"
done

write_state "${round:-0}" "$final"
echo "supervisor exiting: $final"
