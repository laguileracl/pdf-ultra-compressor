#!/usr/bin/env bash
set -euo pipefail

# Sync docs/wiki/*.md to the GitHub Wiki repository.
# Requirements: git, network access, write access to the repo wiki.

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

ORIGIN_URL=$(git config --get remote.origin.url || true)
if [[ -z "${ORIGIN_URL}" ]]; then
  echo "No git remote 'origin' found. Run inside a cloned repo." >&2
  exit 1
fi

# Extract slug owner/repo from various origin URL formats
# Supports: https://github.com/owner/repo(.git) and git@github.com:owner/repo(.git)
SLUG=$(printf '%s' "$ORIGIN_URL" | sed -E 's#^.*github.com[:/]+([^/]+)/([^/.]+)(\.git)?$#\1/\2#')
if [[ -z "${SLUG}" || "${SLUG}" == "$ORIGIN_URL" ]]; then
  echo "Could not parse GitHub slug from origin: $ORIGIN_URL" >&2
  exit 1
fi

WIKI_URL="https://github.com/${SLUG}.wiki.git"
WIKI_DIR=".wiki-tmp"

echo "Wiki URL: $WIKI_URL"
rm -rf "$WIKI_DIR"
git clone "$WIKI_URL" "$WIKI_DIR"

cp -f docs/wiki/*.md "$WIKI_DIR"/

pushd "$WIKI_DIR" >/dev/null
if [[ -n "$(git status --porcelain)" ]]; then
  git add .
  git commit -m "Sync wiki pages from docs/wiki"
  # Detect current default branch (often 'master' on wikis)
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  echo "Pushing to wiki branch: $BRANCH"
  git push origin "HEAD:${BRANCH}"
else
  echo "Wiki already up to date."
fi
popd >/dev/null

echo "Wiki sync complete."
