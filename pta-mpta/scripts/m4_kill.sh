#!/usr/bin/env bash
# M4 pool stopper.  Keyed on the run TAG (n1 noise / t1 table / f1 fl /
# s1 swwide), because the swwide variant runs `--variant noise` with a
# different tag and M3's variant-keyed killer would take it down with the
# noise pool.
#
# SIGTERM first: the harness installs a handler that aborts at once and still
# writes the summary (M2 H1/H3), so a stopped run keeps its checkpoint and its
# inventory record.  SIGKILL only for anything still alive after the grace
# period.
#
#   bash scripts/m4_kill.sh f1          # stop the fl workers + their driver
#   bash scripts/m4_kill.sh t1 table    # ... and the rolling loop for `table`
set -uo pipefail
TAG=${1:?usage: m4_kill.sh <tag n1|t1|f1|s1> [rolling-variant]}
ROLL=${2:-}

match () {  # $1 = pattern, echoes matching pids
  for d in /proc/[0-9]*; do
    p=${d#/proc/}
    c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
    case "$c" in (*$1*) echo "$p";; esac
  done
}

# 1. the rolling loop and the campaign driver, so nothing relaunches
if [ -n "$ROLL" ]; then
  for p in $(match "m3_rolling.sh $ROLL"); do kill -9 "$p" 2>/dev/null; done
fi
for p in $(match "M4POOL=$ROLL"); do kill -9 "$p" 2>/dev/null; done

# 2. the workers, politely
pids=$(match "m3_run.py.*--tag $TAG")
pids=$(for d in /proc/[0-9]*; do
  p=${d#/proc/}
  c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
  case "$c" in (*m3_run.py*"--tag $TAG"*) echo "$p";; esac
done)
n=0
for p in $pids; do kill -TERM "$p" 2>/dev/null && n=$((n+1)); done
echo "SIGTERM sent to $n workers with --tag $TAG"
sleep 20
left=0
for d in /proc/[0-9]*; do
  p=${d#/proc/}
  c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
  case "$c" in (*m3_run.py*"--tag $TAG"*) kill -9 "$p" 2>/dev/null; left=$((left+1));; esac
done
echo "SIGKILL to $left stragglers"
