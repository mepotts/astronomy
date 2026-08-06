#!/usr/bin/env bash
#
# Daily ITF snapshot, run locally instead of on GitHub Actions.
#
# WHY THIS EXISTS. The archive originally ran as a GitHub Actions cron. That stopped
# working after 2026-08-04: the MPC is unreachable from Actions runners, with the TCP
# connection timing out rather than being refused, which is what an IP-range block looks
# like. The same request completes in ~0.1 s from this machine. Small free scientific
# services block datacenter ranges routinely and that is their call to make -- the fix is
# to fetch from somewhere legitimate, not to route around them.
#
# WHAT IT COSTS. This machine is not always on, so days will be missed. That is strictly
# better than the previous state, where every day was missed. The delta chain tolerates
# gaps: each snapshot records its own parent, so a missing day widens one interval rather
# than corrupting the series.
#
# Safe to run repeatedly. If the ITF has not been regenerated since the last snapshot the
# archive is already current and nothing is committed.

set -uo pipefail

REPO="c:/Users/matth/projects/astronomy"
PROJ="$REPO/itf-linker"
PY="$PROJ/.venv/Scripts/python.exe"
LOG="$PROJ/data/snapshot-local.log"
BRANCH=main

exec >>"$LOG" 2>&1
echo "=============================================================="
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] starting"

cd "$REPO" || { echo "FATAL: cannot cd to $REPO"; exit 1; }

# Never clobber work in progress. reset --hard here would discard uncommitted edits in a
# shared working tree -- which is exactly how an agent's work was destroyed on 2026-08-06.
if [ -n "$(git status --porcelain -- itf-linker/data/snapshots)" ]; then
  echo "NOTE: uncommitted changes already under data/snapshots; continuing"
fi

git fetch -q origin || { echo "FATAL: fetch failed"; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
  echo "SKIP: working tree dirty -- refusing to move branches under in-flight work"
  echo "      (snapshot itself still runs; commit/push skipped)"
  DIRTY=1
else
  DIRTY=0
  git checkout -q "$BRANCH" && git merge -q --ff-only origin/"$BRANCH" || true
fi

cd "$PROJ" || exit 1
echo "--- fetching and archiving"
if ! "$PY" -m itf_linker.cli snapshot --refetch; then
  echo "FATAL: snapshot command failed (MPC unreachable, or a real error above)"
  exit 1
fi

SID=$(ls -1 data/snapshots | sort | tail -1)
echo "--- newest snapshot: $SID"

if [ "$DIRTY" = "1" ]; then
  echo "DONE (archived locally; commit/push skipped because the tree was dirty)"
  exit 0
fi

cd "$REPO" || exit 1
# /data/ is gitignored wholesale so a stray working directory can never be committed by
# accident; these two files are the deliberate exception, hence -f.
git add -f "itf-linker/data/snapshots/$SID/manifest.json" \
           "itf-linker/data/snapshots/$SID/delta.parquet" 2>/dev/null

if git diff --cached --quiet; then
  echo "DONE: nothing new -- the ITF has not changed since the last snapshot"
  exit 0
fi

git -c user.name="itf-snapshot (local)" \
    -c user.email="matthew.e.potts@gmail.com" \
    commit -q -m "ITF snapshot $SID [skip ci]" || { echo "FATAL: commit failed"; exit 1; }

if ! git push -q origin "$BRANCH"; then
  echo "WARN: push failed -- commit is local, will go out with the next run"
  exit 0
fi

# The full key set is what makes the NEXT delta possible. It lives as a release asset
# rather than in git: ~178 MB/day of near-identical binaries would be ~60 GB/year of
# history, and GitHub hard-rejects files over 100 MB anyway.
if gh release view itf-state >/dev/null 2>&1; then
  gh release upload itf-state "$PROJ/data/snapshots/$SID/observations.parquet" --clobber \
    && echo "--- published key set for $SID" \
    || echo "WARN: release upload failed -- next run will diff against an older parent"
fi

echo "DONE: committed and pushed $SID"
