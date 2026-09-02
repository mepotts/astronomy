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
# WHERE IT RUNS AND COMMITS. The scheduled task invokes this script from a pinned
# operations checkout. Snapshot state is selected independently with ITF_DATA_DIR, and
# Git commits from a second archive clone ($ARCHIVE). A development branch switch therefore
# cannot change retention policy, prune the archive, or move the task's Git checkout.
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

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || exit 1
PROJ=$(cd -- "$SCRIPT_DIR/.." && pwd -P) || exit 1

# Runtime locations are explicit scheduler inputs. Defaults keep interactive/manual use
# convenient, but production sets all three so code, state, and commit checkout are
# separate failure domains.
ITF_DATA_DIR="${ITF_DATA_DIR:-$PROJ/data}"
ARCHIVE="${ITF_ARCHIVE_CLONE:-c:/Users/matth/projects/astronomy-archive}"
PY="${ITF_PYTHON:-$PROJ/.venv/Scripts/python.exe}"
LOG="${ITF_SNAPSHOT_LOG:-$ITF_DATA_DIR/snapshot-local.log}"
BRANCH="${ITF_ARCHIVE_BRANCH:-main}"
GH_REPO="${ITF_GH_REPO:-mepotts/astronomy}"
SNAPSHOT_DATA="$ITF_DATA_DIR/snapshots"

# A reused development venv may contain an editable install pointing at another checkout.
# This task needs no inherited module search path, so replace it completely. A POSIX ':'
# list is invalid to native Windows Python, whose separator is ';'.
export ITF_DATA_DIR
export PYTHONPATH="$PROJ/src"
if command -v cygpath >/dev/null 2>&1; then
  ITF_EXPECTED_PROJECT_ROOT=$(cygpath -w "$PROJ")
else
  ITF_EXPECTED_PROJECT_ROOT="$PROJ"
fi
export ITF_EXPECTED_PROJECT_ROOT

# Generations of key set retained as release assets. More than one so that a corrupt or
# half-finished upload can never be the only copy in existence; see "no single generation".
#
# Raised 4 -> 14 to match snapshot.py's FULL_KEEP, which went 3 -> 14 for the same reason:
# a three-day window cost M11 a silently wrong interval and M12 a permanent hole in the
# series (2026-08-13's delta could not be computed at all), and the MPC serves only the
# current ITF, so neither is repairable at any price. Keep the two in step -- the local
# window is what makes the next delta computable, the release mirror is what lets an old
# one be recovered.
KEYSET_KEEP=14

# The production task supplies a stable log path separately from ITF_DATA_DIR, so even a
# mistyped state path leaves a diagnostic in the established log. Do not create a new log
# parent implicitly in unattended mode: that would make a typo look valid.
LOG_PARENT=$(dirname -- "$LOG")
if [ ! -d "$LOG_PARENT" ]; then
  if [ "${ITF_ALLOW_BOOTSTRAP:-0}" = "1" ]; then
    mkdir -p "$LOG_PARENT" || { echo "FATAL: cannot create log directory $LOG_PARENT"; exit 1; }
  else
    echo "FATAL: log directory does not exist: $LOG_PARENT"
    exit 1
  fi
fi
exec >>"$LOG" 2>&1
echo "=============================================================="
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] starting"
echo "--- code: $PROJ"
echo "--- state: $ITF_DATA_DIR"
echo "--- interpreter: $PY"

# Non-zero if any step failed. The scheduled task's LastTaskResult is the only signal a
# human checks (docs/archive-operations.md section 1), so a partial run must not exit 0.
RC=0

# ---------------------------------------------------------------- 1. archive the pull

cd "$PROJ" || { echo "FATAL: cannot cd to $PROJ"; exit 1; }
[ -x "$PY" ] || { echo "FATAL: no interpreter at $PY"; exit 1; }

# Refuse to run if the selected interpreter resolves a different data directory or an old
# retention policy. This turns a future path/configuration regression into a failed task,
# rather than an unattended prune.
if ! "$PY" -c \
  "import os; from pathlib import Path; from itf_linker import config; assert config.PROJECT_ROOT == Path(os.environ['ITF_EXPECTED_PROJECT_ROOT']).resolve(), (config.PROJECT_ROOT, os.environ['ITF_EXPECTED_PROJECT_ROOT']); assert config.DATA_DIR == Path(os.environ['ITF_DATA_DIR']).resolve(), (config.DATA_DIR, os.environ['ITF_DATA_DIR'])"; then
  echo "FATAL: interpreter did not resolve the pinned code/state directories"
  exit 1
fi
if [ "${ITF_ALLOW_BOOTSTRAP:-0}" = "1" ]; then
  mkdir -p "$ITF_DATA_DIR" || { echo "FATAL: cannot bootstrap data directory $ITF_DATA_DIR"; exit 1; }
  echo "WARN: explicit archive bootstrap enabled; no continuity check was possible"
else
  if ! CHAIN_COUNTS=$("$PY" -c \
    "from itf_linker.config import validate_existing_snapshot_chain; print(*validate_existing_snapshot_chain())"); then
    echo "FATAL: ITF_DATA_DIR is not an established snapshot chain; refusing a new baseline"
    exit 1
  fi
  echo "--- existing chain: $(echo "$CHAIN_COUNTS" | awk '{print $1}') records, $(echo "$CHAIN_COUNTS" | awk '{print $2}') retained key sets"
fi
RUNTIME_FULL_KEEP=$("$PY" -c "from itf_linker.snapshot import FULL_KEEP; print(FULL_KEEP)") || {
  echo "FATAL: cannot read FULL_KEEP from the selected runtime"
  exit 1
}
if ! [[ "$RUNTIME_FULL_KEEP" =~ ^[0-9]+$ ]]; then
  echo "FATAL: selected runtime returned a non-integer FULL_KEEP: $RUNTIME_FULL_KEEP"
  exit 1
fi
if [ "$RUNTIME_FULL_KEEP" -lt 14 ] || [ "$KEYSET_KEEP" -lt "$RUNTIME_FULL_KEEP" ]; then
  echo "FATAL: unsafe retention: runtime FULL_KEEP=$RUNTIME_FULL_KEEP release KEYSET_KEEP=$KEYSET_KEEP"
  exit 1
fi
echo "--- retention: local=$RUNTIME_FULL_KEEP release=$KEYSET_KEEP"

# Prove the publication clone is a separate, pinned checkout before preflight can report
# success. Merely checking for `.git` later would accept the shared development repo and
# silently recreate the branch-switching failure this operations layout exists to remove.
if ! ARCHIVE_ROOT=$(cd -- "$ARCHIVE" 2>/dev/null && pwd -P); then
  echo "FATAL: archive clone does not exist: $ARCHIVE"
  exit 1
fi
if [ ! -d "$ARCHIVE_ROOT/.git" ]; then
  echo "FATAL: archive path is not a standalone Git clone: $ARCHIVE_ROOT"
  exit 1
fi
if ! DATA_ROOT=$(cd -- "$ITF_DATA_DIR" 2>/dev/null && pwd -P); then
  echo "FATAL: cannot resolve archive state directory: $ITF_DATA_DIR"
  exit 1
fi
proj_norm=${PROJ,,}
data_norm=${DATA_ROOT,,}
archive_norm=${ARCHIVE_ROOT,,}
if [[ "$proj_norm" == "$archive_norm" || "$proj_norm" == "$archive_norm"/* ||
      "$archive_norm" == "$proj_norm"/* || "$data_norm" == "$archive_norm" ||
      "$data_norm" == "$archive_norm"/* || "$archive_norm" == "$data_norm"/* ]]; then
  echo "FATAL: archive clone must be separate from the code and state directories"
  echo "       code=$PROJ state=$DATA_ROOT archive=$ARCHIVE_ROOT"
  exit 1
fi
ARCHIVE_REMOTE=$(git -C "$ARCHIVE_ROOT" remote get-url origin 2>/dev/null) || {
  echo "FATAL: archive clone has no readable origin remote: $ARCHIVE_ROOT"
  exit 1
}
case "$ARCHIVE_REMOTE" in
  "https://github.com/$GH_REPO"|"https://github.com/$GH_REPO.git"|\
  "git@github.com:$GH_REPO"|"git@github.com:$GH_REPO.git") ;;
  *)
    echo "FATAL: archive clone origin is not github.com/$GH_REPO: $ARCHIVE_REMOTE"
    exit 1
    ;;
esac
if ! git -C "$ARCHIVE_ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "FATAL: archive clone has no local $BRANCH branch: $ARCHIVE_ROOT"
  exit 1
fi
# All later shell paths remain stable across `cd` even if an interactive caller supplied
# a relative path. (The scheduled task uses absolute paths, but the manual interface is
# deliberately safe too.)
ARCHIVE="$ARCHIVE_ROOT"
SNAPSHOT_DATA="$DATA_ROOT/snapshots"
echo "--- publication clone: $ARCHIVE_ROOT ($ARCHIVE_REMOTE, branch $BRANCH)"

if [ "${ITF_PREFLIGHT_ONLY:-0}" = "1" ]; then
  echo "DONE: preflight only; no network, archive, release, or git mutation attempted"
  exit 0
fi

echo "--- fetching and archiving"
if ! SNAPSHOT_RESULT=$("$PY" -m itf_linker.cli snapshot --refetch); then
  printf '%s\n' "$SNAPSHOT_RESULT"
  echo "FATAL: snapshot command failed (MPC unreachable, or a real error above)"
  exit 1
fi
printf '%s\n' "$SNAPSHOT_RESULT"

if ! SID=$(printf '%s\n' "$SNAPSHOT_RESULT" | "$PY" -c \
  'import json, re, sys; value = json.load(sys.stdin).get("snapshot_id"); re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", value or "") or sys.exit("missing/invalid snapshot_id in command result"); print(value)'); then
  echo "FATAL: successful snapshot command did not return one valid snapshot id"
  exit 1
fi
echo "--- snapshot returned by command: $SID"

SNAP_DIR="$SNAPSHOT_DATA/$SID"

# Never infer the generation from a lexical directory listing. A stray future-named
# recovery directory could otherwise pin publication forever. Revalidate the whole chain
# after the write and require this exact command result to be a complete record with its
# full key set before any release or archive mutation.
if ! ITF_SELECTED_SNAPSHOT="$SID" "$PY" -c \
  'import os; from itf_linker.config import validate_existing_snapshot_chain; validate_existing_snapshot_chain(required_full_snapshot=os.environ["ITF_SELECTED_SNAPSHOT"])'; then
  echo "FATAL: snapshot returned by this run is not a validated full archive record: $SID"
  exit 1
fi

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

cd "$ARCHIVE_ROOT" || { echo "FATAL: cannot cd to $ARCHIVE_ROOT"; exit 1; }

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
for dir in "$SNAPSHOT_DATA"/*/; do
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
  # A prior run may have committed successfully and then lost the network during push.
  # An unchanged MPC snapshot must still retry that durable-but-unpublished commit; waiting
  # for some later data change could otherwise strand the archive record indefinitely.
  if ! AHEAD=$(git rev-list --count "origin/$BRANCH..$BRANCH"); then
    echo "FATAL: cannot determine whether the archive branch is ahead of origin"; exit 1
  fi
  if [ "$AHEAD" -gt 0 ]; then
    echo "--- retrying push of $AHEAD previously unpushed archive commit(s)"
    if ! git push -q origin "$BRANCH"; then
      echo "WARN: retry push failed -- $AHEAD archive commit(s) remain local"
      RC=1
    else
      echo "DONE: pushed $AHEAD previously unpushed archive commit(s); snapshot unchanged"
    fi
  else
    echo "DONE: nothing new -- every snapshot record on disk is committed and published"
  fi
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
