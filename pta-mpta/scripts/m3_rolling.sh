#!/usr/bin/env bash
# M3: keep sweeping one dependent variant until every gated noise run has it.
set -uo pipefail
cd /mnt/c/Users/matth/projects/astronomy/pta-mpta
V=$1
TAG=$2
while true; do
  NPROC=${NPROC:-3} THREADS=1 CHUNK_MIN=${CHUNK_MIN:-5} ORDER_FILE=logs/m3/order_priority.txt bash scripts/m3_campaign.sh "$V" > /dev/null 2>&1
  n=$(grep -l "\"gate_met\": true" results/m3/*_${V}_${TAG}.summary.json 2>/dev/null | wc -l)
  g=$(grep -l "\"gate_met\": true" results/m3/*_noise_n1.summary.json 2>/dev/null | wc -l)
  echo "[$V] gated=$n of noise-gated=$g at $(date -u +%H:%M:%SZ)"
  if [ "$n" -ge 83 ]; then break; fi
  sleep 180
done
