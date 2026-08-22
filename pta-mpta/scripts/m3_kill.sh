#!/usr/bin/env bash
# usage: m3_kill.sh <variant>   -- kills the campaign driver AND its workers
V=$1
n=0
for d in /proc/[0-9]*; do
  p=${d#/proc/}
  c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
  case "$c" in
    *m3_campaign.sh*" $V"*) kill -9 "$p" 2>/dev/null && n=$((n+1));;
  esac
done
for d in /proc/[0-9]*; do
  p=${d#/proc/}
  c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null) || continue
  case "$c" in
    *m3_run.py*"variant $V"*) kill -9 "$p" 2>/dev/null && n=$((n+1));;
  esac
done
echo "killed=$n"
