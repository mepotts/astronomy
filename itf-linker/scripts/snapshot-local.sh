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
# WHERE IT COMMITS. Git runs in a dedicated archive clone ($ARCHIVE), never in the
# development checkout. Until 2026-08-06 this script ran `git checkout main` in the shared
# tree whenever that tree was clean: commit your work on a feature branch, leave it clean
# overnight, and the task moved you to main and pushed from it. The dirty-tree guard only
# ever protected *uncommitted* work. The archive now owns its own clone, so the state of
# the development tree cannot affect it and it cannot affect the development tree.
#
# ORDER MATTERS. The key set is published BEFORE any git work and independently of it. It
# is the artefact that makes the NEXT delta computable, and it used to sit after the
# commit/push block -- so a dirty tree, an unchanged ITF, or a failed push each skipped it
# silently. That is why the newest published key set was 08-04 while the archive on disk
# had reached 08-06.
#
# Safe to run repeatedly. If the ITF has not been regenerated since the last snapshot the
# archive is already current and nothing is committed.

set -uo pipefail

REPO="c:/Users/matth/projects/astronomy"              # development checkout; snapshot data lives here
ARCHIVE="c:/Users/matth/projects/astronomy-archive"   # clone this task commits from; nothing human in it
PROJ="$REPO/itf-linker"
PY="$PROJ/.venv/Scripts/python.exe"
LOG="$PROJ/data/snapshot-local.log"
BRANCH=main
GH_REPO="mepotts/astronomy"

# Generations of key set retained as release assets. More than one so that a corrupt or
# half-finished upload can never be the only copy in existence; see "no single generation".
KEYSET_KEEP=4

exec >>"$LOG" 2>&1
echo "=============================================================="
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] starting"

# Non-zero if any step failed. The scheduled task's LastTaskResult is the only signal a
# human checks (docs/archive-operations.md section 1), so a partial run must not exit 0.
RC=0

# ---------------------------------------------------------------- 1. archive the pull

cd "$PROJ" || { echo "FATAL: cannot cd to $PROJ"; exit 1; }
[ -x "$PY" ] || { echo "FATAL: no interpreter at $PY"; exit 1; }

echo "--- fetching and archiving"
if ! "$PY" -m itf_linker.cli snapshot --refetch; then
  echo "FATAL: snapshot command failed (MPC unreachable, or a real error above)"
  exit 1
fi

SID=$(ls -1 data/snapshots | sort | tail -1)
if [ -z "$SID" ]; then
  echo "FATAL: no snapshot directory after a successful snapshot run"
  exit 1
fi
echo "--- newest snapshot: $SID"

SNAP_REL="itf-linker/data/snapshots/$SID"
SNAP_DIR="$REPO/$SNAP_REL"

# ------------------------------------------------- 2. publish the key set (before git)

KEYSET="$SNAP_DIR/observations.parquet"
ASSET="observations-$SID.parquet"
STAGED="$SNAP_DIR/$ASSET"

if [ ! -f "$KEYSET" ]; then
  # Pruned by the rolling window (FULL_KEEP), i.e. this SID is not the newest full
  # snapshot. Nothing to publish and nothing wrong.
  echo "--- no key set on disk for $SID; skipping publish"
elif gh release view itf-state --repo "$GH_REPO" >/dev/null 2>&1; then
  # gh names an asset after the file's BASENAME -- the `file#label` suffix sets only a
  # display label. So the per-snapshot name has to come from a per-snapshot filename.
  # Hardlink where the filesystem allows it; a 170 MB copy is the fallback, not the plan.
  rm -f "$STAGED"
  if ! ln "$KEYSET" "$STAGED" 2>/dev/null && ! cp "$KEYSET" "$STAGED"; then
    echo "FATAL: could not stage key set as $ASSET -- not published"
    echo "       the NEXT run will have no parent key set to diff against"
    RC=1
  else
    published=0
    for attempt in 1 2 3; do
      # --clobber deletes the existing asset BEFORE uploading, and gh documents that a
      # failed upload loses the original. That is survivable only because the name carries
      # $SID: it can clobber a half-uploaded file of this generation, never an older one.
      if gh release upload itf-state "$STAGED" --repo "$GH_REPO" --clobber; then
        echo "--- published key set for $SID as $ASSET (attempt $attempt)"
        published=1
        break
      fi
      echo "WARN: key set upload attempt $attempt failed"
      sleep 20
    done
    rm -f "$STAGED"

    if [ "$published" = "1" ]; then
      # Prune only after a confirmed upload, so pruning can never run in a state where the
      # newest generation is missing. The pre-2026-08-06 asset is named
      # `observations.parquet` with no SID, so this glob never matches it and the last
      # single-copy generation is left alone.
      mapfile -t assets < <(gh release view itf-state --repo "$GH_REPO" \
        --json assets -q '.assets[].name | select(startswith("observations-"))' | sort)
      drop=$(( ${#assets[@]} - KEYSET_KEEP ))
      if [ "$drop" -gt 0 ]; then
        for old in "${assets[@]:0:$drop}"; do
          if gh release delete-asset itf-state "$old" --repo "$GH_REPO" --yes; then
            echo "--- pruned old key set $old"
          else
            echo "WARN: could not prune $old (harmless; it only costs storage)"
          fi
        done
      fi
    else
      # The one unrecoverable consequence in this script: without this asset the next run
      # has no parent key set and its delta is unmeasurable.
      echo "FATAL: key set for $SID could not be published after 3 attempts"
      echo "       the NEXT run will have no parent key set to diff against"
      RC=1
    fi
  fi
else
  echo "FATAL: release itf-state not found on $GH_REPO -- key set not published"
  RC=1
fi

# --------------------------------------------------- 3. commit the permanent record

MAN="$SNAP_DIR/manifest.json"
DELTA="$SNAP_DIR/delta.parquet"

for f in "$MAN" "$DELTA"; do
  [ -f "$f" ] || { echo "FATAL: expected artefact missing: $f"; exit 1; }
done

if [ ! -d "$ARCHIVE/.git" ]; then
  echo "FATAL: no archive clone at $ARCHIVE"
  echo "       create it once with:"
  echo "         git clone https://github.com/$GH_REPO.git '$ARCHIVE'"
  exit 1
fi

cd "$ARCHIVE" || { echo "FATAL: cannot cd to $ARCHIVE"; exit 1; }

# A stale index can only come from a previous failed run of this script; nothing human is
# ever edited here. Unstage it (mixed reset -- never --hard, which is how an agent's work
# was destroyed on 2026-08-06 back when this ran in the shared tree).
git reset -q

if ! git fetch -q origin; then
  echo "FATAL: fetch failed in archive clone"; exit 1
fi
if ! git checkout -q "$BRANCH"; then
  echo "FATAL: cannot check out $BRANCH in archive clone"; exit 1
fi
if ! git merge -q --ff-only "origin/$BRANCH"; then
  echo "FATAL: $BRANCH in archive clone is not fast-forwardable from origin"
  echo "       someone committed there by hand; resolve before the next run"
  exit 1
fi

# Stage EVERY snapshot record on disk, not just the newest. A run that dies or is skipped
# at the commit step would otherwise orphan that day's permanent record forever, because no
# later run ever looked back. That is not hypothetical: the 2026-07-29 baseline pair and
# 20260806T122651Z sat uncommitted on the laptop for days, and the 08-07 run walked straight
# past all three. Restaging is free -- git stages only what actually differs.
for dir in "$REPO/itf-linker/data/snapshots"/*/; do
  sid=$(basename "$dir")
  # A pruned snapshot keeps its manifest and delta forever; anything missing them is a
  # half-written directory, not a record.
  [ -f "$dir/manifest.json" ] && [ -f "$dir/delta.parquet" ] || continue

  rel="itf-linker/data/snapshots/$sid"
  mkdir -p "$ARCHIVE/$rel" || { echo "FATAL: cannot create $rel"; exit 1; }
  if ! cp -f "$dir/manifest.json" "$dir/delta.parquet" "$ARCHIVE/$rel/"; then
    echo "FATAL: could not copy artefacts for $sid into the archive clone"; exit 1
  fi

  # /data/ is gitignored wholesale so a stray working directory can never be committed by
  # accident; these two files are the deliberate exception, hence -f.
  #
  # No 2>/dev/null here. Discarding this error meant a failed add fell through to the
  # "nothing new" success message below -- an unmeasurable state reported as a measured
  # null, which is the exact shape docs/archive-operations.md section 4 was written about.
  if ! git add -f "$rel/manifest.json" "$rel/delta.parquet"; then
    echo "FATAL: git add failed for $sid"; exit 1
  fi

  # Prove both paths reached the index. Only then does an empty diff genuinely mean
  # "already committed", rather than "nothing was ever staged".
  if ! git ls-files --error-unmatch -- "$rel/manifest.json" "$rel/delta.parquet" >/dev/null; then
    echo "FATAL: artefacts for $sid are not in the index after a successful add"; exit 1
  fi
done

if git diff --cached --quiet; then
  echo "DONE: nothing new -- every snapshot record on disk is already committed"
  exit "$RC"
fi

mapfile -t committing < <(git diff --cached --name-only | awk -F/ '{print $(NF-1)}' | sort -u)
if [ "${#committing[@]}" -eq 1 ]; then
  MSG="ITF snapshot ${committing[0]} [skip ci]"
else
  MSG="ITF snapshots: ${committing[*]} [skip ci]"
fi
echo "--- committing ${#committing[@]} record(s): ${committing[*]}"

if ! git -c user.name="itf-snapshot (local)" \
        -c user.email="matthew.e.potts@gmail.com" \
        commit -q -m "$MSG"; then
  echo "FATAL: commit failed"; exit 1
fi

if ! git push -q origin "$BRANCH"; then
  echo "WARN: push failed -- commit is local in the archive clone, goes out with the next run"
  echo "      (the key set for $SID was published independently, above)"
  RC=1
else
  echo "DONE: committed and pushed $SID"
fi

exit "$RC"
