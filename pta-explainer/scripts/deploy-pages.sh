#!/usr/bin/env bash
# Deploy the built pta-explainer to its PUBLIC GitHub Pages repo.
#
# The source of truth lives in the private "astronomy" monorepo. GitHub Pages
# won't serve from a private repo on a free plan, so this pushes ONLY the
# compiled dist/ to a separate public repo (single commit, force-pushed —
# generated artifacts, so throwaway history keeps the mirror tiny).
#
# Usage:  npm run deploy         (from the pta-explainer/ dir)
# Config: override via env, e.g. PAGES_REPO_URL=... npm run deploy
set -euo pipefail

REPO_URL="${PAGES_REPO_URL:-https://github.com/mepotts/pta-explainer.git}"
BRANCH="${PAGES_BRANCH:-main}"
LIVE_URL="${PAGES_LIVE_URL:-https://mepotts.github.io/pta-explainer/}"

# Resolve the project root (this script's parent dir) regardless of CWD.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

echo "==> Building production bundle (base=/pta-explainer/)"
npm run build:pages

echo "==> Publishing dist/ -> $REPO_URL ($BRANCH)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -r dist/. "$tmp/"
touch "$tmp/.nojekyll"   # tell Pages to serve files as-is (no Jekyll build)
(
  cd "$tmp"
  git init -q -b "$BRANCH"
  git add -A
  git -c user.name="pta-explainer deploy" \
      -c user.email="deploy@localhost" \
      commit -q -m "Deploy pta-explainer site"
  git push -f -q "$REPO_URL" "$BRANCH"
)

echo "==> Done. Live at $LIVE_URL"
echo "    (first deploy can take 1-2 min for Pages to build)"
